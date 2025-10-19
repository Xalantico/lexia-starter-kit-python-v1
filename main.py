"""
Lexia AI Agent Starter Kit
==========================

A production-ready starter kit for building AI agents that integrate with the Lexia platform.
This demonstrates best practices for creating AI agents with proper memory management,
streaming responses, file processing, and function calling capabilities.

Key Features:
- Clean, maintainable architecture with separation of concerns
- Built-in conversation memory and thread management
- Support for PDF text extraction and image analysis
- Real-time response streaming via Lexia's infrastructure
- Function calling with DALL-E 3 image generation
- Robust error handling and comprehensive logging
- Inherited endpoints from Lexia package for consistency
- Dev mode for local development without Centrifugo

Architecture:
- Main processing logic in process_message() function
- Memory management via ConversationManager class
- Utility functions for OpenAI integration
- Standard Lexia endpoints inherited from package

Usage:
    python main.py              # Production mode (Centrifugo)
    python main.py --dev        # Dev mode (no Centrifugo)
    python main.py --prod       # Force production mode
    
    # Or with environment variable:
    LEXIA_DEV_MODE=true python main.py

The server will start on http://localhost:8005 with the following endpoints:
- POST /api/v1/send_message - Main chat endpoint
- GET /api/v1/health - Health check
- GET /api/v1/ - Root information
- GET /api/v1/docs - Interactive API documentation
- GET /api/v1/stream/{channel} - SSE stream (dev mode only)
- GET /api/v1/poll/{channel} - Polling endpoint (dev mode only)

Author: Lexia Team
License: MIT
"""

import sys
import logging
from openai import OpenAI
import os
import requests
import tiktoken
import PyPDF2
import io

# Configure logging with informative format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AI agent components
from memory import ConversationManager
from lexia import (
    LexiaHandler, 
    ChatResponse, 
    ChatMessage, 
    Variable, 
    create_success_response,
    create_lexia_app,
    add_standard_endpoints,
    Variables
)
from agent_utils import format_system_prompt, format_messages_for_openai
from function_handler import get_available_functions, process_function_calls

# Determine dev/prod mode from CLI flags or env var (default: prod)
dev_mode_flag = None
if '--dev' in sys.argv:
    dev_mode_flag = True
    print("🔧 Dev mode enabled via --dev flag")
elif '--prod' in sys.argv:
    dev_mode_flag = False
    print("🚀 Production mode enabled via --prod flag")
else:
    env_val = os.environ.get('LEXIA_DEV_MODE', 'false').lower()
    dev_mode_flag = env_val in ('true', '1', 'yes', 'y', 'on')
    if dev_mode_flag:
        print("🔧 Dev mode enabled via LEXIA_DEV_MODE environment variable")

# Initialize core services
conversation_manager = ConversationManager(max_history=10)  # Keep last 10 messages per thread
lexia = LexiaHandler(dev_mode=dev_mode_flag)

# Create the FastAPI app using Lexia's web utilities
app = create_lexia_app(
    title="Lexia AI Agent Starter Kit",
    version="1.0.0",
    description="Production-ready AI agent starter kit with Lexia integration"
)

async def process_message(data: ChatMessage) -> None:
    """
    Process incoming chat messages using OpenAI and send responses via Lexia.
    
    This is the core AI processing function that you can customize for your specific use case.
    The function handles:
    1. Message validation and logging
    2. Environment variable setup
    3. OpenAI API communication
    4. File processing (PDFs, images)
    5. Function calling and execution
    6. Response streaming and completion
    
    Args:
        data: ChatMessage object containing the incoming message and metadata
        
    Returns:
        None: Responses are sent via Lexia's streaming and completion APIs
        
    Raises:
        Exception: If message processing fails (errors are sent to Lexia)
        
    Customization Points:
        - Modify system prompts and context
        - Adjust OpenAI model parameters
        - Add custom function calling capabilities
        - Implement specialized file processing
        - Customize error handling and logging
    """
    try:
        # Log comprehensive request information for debugging
        logger.info("=" * 80)
        logger.info("📥 FULL REQUEST BODY RECEIVED:")
        logger.info("=" * 80)
        logger.info(f"Thread ID: {data.thread_id}")
        logger.info(f"Message: {data.message}")
        logger.info(f"Response UUID: {data.response_uuid}")
        logger.info(f"Model: {data.model}")
        logger.info(f"System Message: {data.system_message}")
        logger.info(f"Project System Message: {data.project_system_message}")
        logger.info(f"Variables: {data.variables}")
        logger.info(f"Stream URL: {getattr(data, 'stream_url', 'Not provided')}")
        logger.info(f"Stream Token: {getattr(data, 'stream_token', 'Not provided')}")
        logger.info(f"Full data object: {data}")
        logger.info("=" * 80)
        
        # Log key processing information
        logger.info(f"🚀 Processing message for thread {data.thread_id}")
        logger.info(f"📝 Message: {data.message[:100]}...")
        logger.info(f"🔑 Response UUID: {data.response_uuid}")
        
        # Get OpenAI API key using Variables helper class
        vars = Variables(data.variables)
        openai_api_key = vars.get("OPENAI_API_KEY")
        if not openai_api_key:
            missing_key_msg = "Sorry, the OpenAI API key is missing or empty. From menu right go to admin mode, then agents and edit the agent in last section you can set the openai key."
            logger.error("OpenAI API key not found or empty in variables")
            lexia.stream_chunk(data, missing_key_msg)
            lexia.complete_response(data, missing_key_msg)
            return
        
        # Initialize OpenAI client and conversation management
        client = OpenAI(api_key=openai_api_key)
        conversation_manager.add_message(data.thread_id, "user", data.message)
        thread_history = conversation_manager.get_history(data.thread_id)
        
        # Format system prompt and messages for OpenAI
        system_prompt = format_system_prompt(data.system_message, data.project_system_message)
        messages = format_messages_for_openai(system_prompt, thread_history, data.message)
        
        # Process PDF files if present
        if hasattr(data, 'file_type') and data.file_type == 'pdf' and hasattr(data, 'file_url') and data.file_url:
            logger.info(f"📄 PDF detected: {data.file_url}")
            
            try:
                # Download and process PDF content
                logger.info("📥 Downloading PDF...")
                response = requests.get(data.file_url)
                response.raise_for_status()
                
                # Extract text from PDF using PyPDF2
                logger.info("📖 Extracting text from PDF...")
                pdf_file = io.BytesIO(response.content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() + "\n"
                
                logger.info(f"📄 PDF text extracted. Length: {len(pdf_text)} characters")
                
                # Count tokens using tiktoken to prevent API overload
                logger.info("🔢 Counting tokens with tiktoken...")
                tokenizer = tiktoken.get_encoding("gpt2")
                tokens = tokenizer.encode(pdf_text)
                token_count = len(tokens)
                
                logger.info(f"🔢 Token count: {token_count}")
                

                
                # Add PDF content to the message for context
                if messages and messages[-1]['role'] == 'user':
                    combined_content = f"{data.message}\n\nPDF Content:\n{pdf_text}"
                    messages[-1]['content'] = combined_content
                    
                    logger.info(f"📤 PDF content added to OpenAI request. Total tokens: {token_count}")
                    

                
            except Exception as e:
                error_msg = f"Error processing PDF: {str(e)}"
                logger.error(error_msg, exc_info=True)
                # Continue without PDF content if there's an error
        
        # Process image files if present
        elif hasattr(data, 'file_type') and data.file_type == 'image' and hasattr(data, 'file_url') and data.file_url:
            logger.info(f"🖼️ Image detected: {data.file_url}")
            # Add image to the last user message for vision analysis
            if messages and messages[-1]['role'] == 'user':
                messages[-1]['content'] = [
                    {"type": "text", "text": messages[-1]['content']},
                    {"type": "image_url", "image_url": {"url": data.file_url}}
                ]
                logger.info("🖼️ Image added to OpenAI request for vision analysis")
        
        # Log OpenAI request details
        logger.info(f"🤖 Sending to OpenAI model: {data.model}")
        logger.info(f"💬 System prompt: {system_prompt[:100]}...")
        logger.info(f"📤 Messages being sent to OpenAI: {messages}")
        
        # Get available functions from function handler
        available_functions = get_available_functions()
        
        # Stream response from OpenAI with function calling support
        stream = client.chat.completions.create(
            model=data.model,
            messages=messages,
            tools=available_functions,
            tool_choice="auto",
            max_tokens=1000,
            temperature=0.7,
            stream=True
        )
        
        # Begin a Lexia session (aggregates + streams)
        session = lexia.begin(data)
        
        # Process streaming response
        usage_info = None
        function_calls = []
        generated_image_url = None
        
        logger.info("📡 Streaming response from OpenAI...")
        
        for chunk in stream:
            # Handle content chunks
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                # Stream chunk to Lexia (handles dev/prod mode internally) and aggregate
                session.stream(content)
            
            # Handle function call chunks
            if chunk.choices[0].delta.tool_calls:
                logger.info(f"🔧 Tool call chunk detected: {chunk.choices[0].delta.tool_calls}")
                for tool_call in chunk.choices[0].delta.tool_calls:
                    if tool_call.function:
                        # Initialize function call if it's new
                        if len(function_calls) <= tool_call.index:
                            function_calls.append({
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": ""
                                }
                            })
                            logger.info(f"🔧 New function call initialized: {tool_call.function.name}")
                            
                            # Stream function call announcement to Lexia
                            function_msg = f"\n🔧 **Calling function:** {tool_call.function.name}"
                            session.stream(function_msg)
                        
                        # Accumulate function arguments
                        if tool_call.function.arguments:
                            function_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
                            logger.info(f"🔧 Accumulated arguments for function {tool_call.index}: {tool_call.function.arguments}")
                            
                            # Stream function execution progress to Lexia
                            try:
                                import json
                                current_args = function_calls[tool_call.index]["function"]["arguments"]
                                # Try to parse as JSON to show progress
                                if current_args.endswith('"') or current_args.endswith('}') or current_args.endswith(']'):
                                    parsed_args = json.loads(current_args)
                                    progress_msg = f"\n⚙️ **Function parameters:** {json.dumps(parsed_args, indent=2)}"
                                    session.stream(progress_msg)
                            except json.JSONDecodeError:
                                # JSON not complete yet, don't stream partial data
                                pass
            
            # Capture usage information from the last chunk
            if chunk.usage:
                usage_info = chunk.usage
                logger.info(f"📊 Usage info captured: {usage_info}")
        
        logger.info("✅ OpenAI response stream complete")
        
        # Process function calls if any were made using the function handler
        function_result, generated_image_url = await process_function_calls(function_calls, lexia, data)
        if function_result:
            session.stream(function_result)
        
        logger.info(f"🖼️ Final generated_image_url value: {generated_image_url}")
        
        # Finalize via session (aggregated). Include file_url if available
        final_text = lexia.close(data, usage_info, file_url=generated_image_url)
        
        # Store response in conversation memory
        conversation_manager.add_message(data.thread_id, "assistant", final_text)
        
        logger.info(f"🎉 Message processing completed successfully for thread {data.thread_id}")
            
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg, exc_info=True)
        lexia.send_error(data, error_msg, exception=e) 


# Add standard Lexia endpoints including the inherited send_message endpoint
# This provides all the standard functionality without additional code
add_standard_endpoints(
    app, 
    conversation_manager=conversation_manager,
    lexia_handler=lexia,
    process_message_func=process_message
)

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Lexia AI Agent Starter Kit...")
    print("=" * 60)
    
    # Display mode
    if getattr(lexia, 'dev_mode', False):
        print("🔧 DEV MODE ACTIVE - No Centrifugo required!")
        print("   Use --prod flag or LEXIA_DEV_MODE=false for production")
    else:
        print("🟢 PRODUCTION MODE - Centrifugo/WebSocket streaming")
        print("   Use --dev flag or LEXIA_DEV_MODE=true for local development")
    
    print("=" * 60)
    print("📖 API Documentation: http://localhost:8005/docs")
    print("🔍 Health Check: http://localhost:8005/api/v1/health")
    print("💬 Chat Endpoint: http://localhost:8005/api/v1/send_message")
    
    if getattr(lexia, 'dev_mode', False):
        print("📡 SSE Stream: http://localhost:8005/api/v1/stream/{channel}")
        print("📊 Poll Stream: http://localhost:8005/api/v1/poll/{channel}")
    
    print("=" * 60)
    print("\n✨ This starter kit demonstrates:")
    print("   - Clean integration with Lexia package")
    print("   - Inherited endpoints for common functionality")
    print("   - Customizable AI message processing")
    print("   - Conversation memory management")
    print("   - File processing (PDFs, images)")
    print("   - Function calling with DALL-E 3")
    print("   - Proper data structure for Lexia communication")
    print("   - Comprehensive error handling and logging")
    
    if getattr(lexia, 'dev_mode', False):
        print("   - Dev mode streaming (SSE, no Centrifugo)")
    else:
        print("   - Production streaming (Centrifugo/WebSocket)")
    
    print("\n🔧 Customize the process_message() function to add your AI logic!")
    print("\n💡 Mode Selection:")
    print("   python main.py --dev   # Local development (SSE streaming)")
    print("   python main.py --prod  # Production (Centrifugo)")
    print("=" * 60)
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=5001)
