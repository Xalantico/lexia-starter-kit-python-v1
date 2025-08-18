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

Architecture:
- Main processing logic in process_message() function
- Memory management via ConversationManager class
- Utility functions for OpenAI integration
- Standard Lexia endpoints inherited from package

Usage:
    python main.py

The server will start on http://localhost:8000 with the following endpoints:
- POST /api/v1/send_message - Main chat endpoint
- GET /api/v1/health - Health check
- GET /api/v1/ - Root information
- GET /api/v1/docs - Interactive API documentation

Author: Lexia Team
License: MIT
"""

import asyncio
import logging
from openai import OpenAI
import os
import requests
import tiktoken
import PyPDF2
import io
import time

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
    add_standard_endpoints
)
from agent_utils import format_system_prompt, format_messages_for_openai
from lexia.utils import set_env_variables, get_openai_api_key

# Initialize core services
conversation_manager = ConversationManager(max_history=10)  # Keep last 10 messages per thread
lexia = LexiaHandler()

# Create the FastAPI app using Lexia's web utilities
app = create_lexia_app(
    title="Lexia AI Agent Starter Kit",
    version="1.0.0",
    description="Production-ready AI agent starter kit with Lexia integration"
)

async def generate_image_with_dalle(
    prompt: str, 
    size: str = "1024x1024", 
    quality: str = "standard", 
    style: str = "vivid"
) -> str:
    """
    Generate an image using OpenAI's DALL-E 3 model.
    
    This function demonstrates how to integrate external AI services with your agent.
    You can extend this pattern to add other AI capabilities like speech synthesis,
    video generation, or custom ML model inference.
    
    Args:
        prompt: Detailed text description of the image to generate
        size: Image dimensions - "1024x1024" (square), "1792x1024" (landscape), or "1024x1792" (portrait)
        quality: Image quality - "standard" or "hd" (higher cost but better quality)
        style: Image style - "vivid" (dramatic) or "natural" (realistic)
    
    Returns:
        str: URL of the generated image
        
    Raises:
        Exception: If image generation fails or API key is missing
        
    Example:
        >>> image_url = await generate_image_with_dalle("A serene mountain landscape at sunset")
        >>> print(f"Generated image: {image_url}")
    """
    try:
        # Get OpenAI API key from environment variables
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        logger.info(f"🎨 Generating image with DALL-E 3: {prompt}")
        
        # Generate image using DALL-E 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1
        )
        
        image_url = response.data[0].url
        logger.info(f"✅ Image generated successfully: {image_url}")
        
        return image_url
        
    except Exception as e:
        error_msg = f"Error generating image with DALL-E: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg)

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
        
        # Set environment variables and get OpenAI API key
        set_env_variables(data.variables)
        openai_api_key = get_openai_api_key(data.variables)
        if not openai_api_key:
            error_msg = "OpenAI API key not found in variables"
            logger.error(error_msg)
            lexia.send_error(data, error_msg)
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
        
        # Define available functions for the AI (extend this list for custom capabilities)
        available_functions = [
            {
                "type": "function",
                "function": {
                    "name": "generate_image",
                    "description": "Generate an image using DALL-E 3 based on a text description",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "A detailed description of the image you want to generate. Be specific about style, colors, composition, and mood."
                            },
                            "size": {
                                "type": "string",
                                "enum": ["1024x1024", "1792x1024", "1024x1792"],
                                "description": "The size of the generated image. 1024x1024 is square, 1792x1024 is landscape, 1024x1792 is portrait."
                            },
                            "quality": {
                                "type": "string",
                                "enum": ["standard", "hd"],
                                "description": "Image quality. HD is higher quality but costs more."
                            },
                            "style": {
                                "type": "string",
                                "enum": ["vivid", "natural"],
                                "description": "Image style. Vivid is more dramatic, natural is more realistic."
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            }
        ]
        
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
        
        # Process streaming response
        full_response = ""
        usage_info = None
        function_calls = []
        generated_image_url = None
        
        logger.info("📡 Streaming response from OpenAI...")
        
        for chunk in stream:
            # Handle content chunks
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                # Stream chunk to Lexia via Centrifugo
                lexia.stream_chunk(data, content)
            
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
                        
                        # Accumulate function arguments
                        if tool_call.function.arguments:
                            function_calls[tool_call.index]["function"]["arguments"] += tool_call.function.arguments
                            logger.info(f"🔧 Accumulated arguments for function {tool_call.index}: {tool_call.function.arguments}")
            
            # Capture usage information from the last chunk
            if chunk.usage:
                usage_info = chunk.usage
                logger.info(f"📊 Usage info captured: {usage_info}")
        
        logger.info(f"✅ OpenAI response complete. Length: {len(full_response)} characters")
        
        # Process function calls if any were made
        if function_calls:
            logger.info(f"🔧 Processing {len(function_calls)} function calls...")
            logger.info(f"🔧 Function calls details: {function_calls}")
            
            for function_call in function_calls:
                try:
                    logger.info(f"🔧 Processing function: {function_call['function']['name']}")
                    
                    if function_call["function"]["name"] == "generate_image":
                        import json
                        args = json.loads(function_call["function"]["arguments"])
                        
                        logger.info(f"🎨 Executing DALL-E image generation with args: {args}")
                        
                        # Generate the image using our DALL-E function
                        image_url = await generate_image_with_dalle(
                            prompt=args.get("prompt"),
                            size=args.get("size", "1024x1024"),
                            quality=args.get("quality", "standard"),
                            style=args.get("style", "vivid")
                        )
                        
                        logger.info(f"✅ DALL-E image generated: {image_url}")
                        
                        # Store the image URL for inclusion in the final response
                        generated_image_url = image_url
                        logger.info(f"🖼️ Set generated_image_url to: {generated_image_url}")
                        
                        # Add image generation result to response
                        image_result = f"\n\n🎨 **Image Generated Successfully!**\n\n**Prompt:** {args.get('prompt')}\n**Image URL:** {image_url}\n\n*Image created with DALL-E 3*"
                        full_response += image_result
                        
                        # Stream the image result to Lexia
                        lexia.stream_chunk(data, image_result)
                        
                        logger.info(f"✅ Image generation completed: {image_url}")
                        
                except Exception as e:
                    error_msg = f"Error executing function {function_call['function']['name']}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    function_error = f"\n\n❌ **Function Execution Error:** {error_msg}"
                    full_response += function_error
                    lexia.stream_chunk(data, function_error)
        else:
            logger.info("🔧 No function calls to process")
        
        logger.info(f"🖼️ Final generated_image_url value: {generated_image_url}")
        
        # Store response in conversation memory
        conversation_manager.add_message(data.thread_id, "assistant", full_response)
        
        # Send complete response to Lexia with full data structure
        logger.info("📤 Sending complete response to Lexia...")
        
        # Include generated image in the response if one was created
        if generated_image_url:
            logger.info(f"🖼️ Including generated image in API call: {generated_image_url}")
            # Use the complete_response method that includes the file field
            lexia.complete_response(data, full_response, usage_info, file_url=generated_image_url)
        else:
            # Normal response without image
            lexia.complete_response(data, full_response, usage_info)
        
        logger.info(f"🎉 Message processing completed successfully for thread {data.thread_id}")
            
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg, exc_info=True)
        lexia.send_error(data, error_msg)


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
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/api/v1/health")
    print("💬 Chat Endpoint: http://localhost:8000/api/v1/send_message")
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
    print("\n🔧 Customize the process_message() function to add your AI logic!")
    print("=" * 60)
    
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000)
