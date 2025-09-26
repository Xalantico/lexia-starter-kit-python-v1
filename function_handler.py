"""
Function Handler Module
======================

This module handles all function calling capabilities for the Lexia AI Agent.
It contains the function definitions, execution logic, and related utilities.

Key Features:
- DALL-E 3 image generation function
- Function schema definitions
- Function execution and error handling
- Streaming progress updates to Lexia

Author: Lexia Team
License: MIT
"""

import asyncio
import logging
import os
import json
from openai import OpenAI
from lexia import Variables

# Configure logging
logger = logging.getLogger(__name__)

# Available functions schema for OpenAI
AVAILABLE_FUNCTIONS = [
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

async def generate_image_with_dalle(
    prompt: str, 
    variables: list = None,
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
        # Get OpenAI API key using Variables helper class
        if not variables:
            raise ValueError("Variables not provided to generate_image_with_dalle")
        
        vars = Variables(variables)
        openai_api_key = vars.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OpenAI API key not found in variables")
        
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

async def execute_function_call(
    function_call: dict, 
    lexia_handler, 
    data
) -> tuple[str, str]:
    """
    Execute a function call and return the result and any generated file URL.
    
    Args:
        function_call: The function call object from OpenAI
        lexia_handler: The Lexia handler instance for streaming updates
        data: The original chat message data
        
    Returns:
        tuple: (result_message, generated_file_url or None)
    """
    try:
        function_name = function_call['function']['name']
        logger.info(f"🔧 Processing function: {function_name}")
        
        # Stream generic function processing start to Lexia
        processing_msg = f"\n⚙️ **Processing function:** {function_name}"
        lexia_handler.stream_chunk(data, processing_msg)
        
        if function_name == "generate_image":
            return await _execute_generate_image(function_call, lexia_handler, data)
        else:
            error_msg = f"Unknown function: {function_name}"
            logger.error(error_msg)
            return f"\n\n❌ **Function Error:** {error_msg}", None
            
    except Exception as e:
        error_msg = f"Error executing function {function_call['function']['name']}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        function_error = f"\n\n❌ **Function Execution Error:** {error_msg}"
        return function_error, None

async def _execute_generate_image(
    function_call: dict, 
    lexia_handler, 
    data
) -> tuple[str, str]:
    """
    Execute the generate_image function specifically.
    
    Args:
        function_call: The function call object from OpenAI
        lexia_handler: The Lexia handler instance for streaming updates
        data: The original chat message data
        
    Returns:
        tuple: (result_message, generated_image_url)
    """
    try:
        args = json.loads(function_call["function"]["arguments"])
        logger.info(f"🎨 Executing DALL-E image generation with args: {args}")
        
        # Stream function execution start to Lexia
        execution_msg = f"\n🚀 **Executing function:** generate_image"
        lexia_handler.stream_chunk(data, execution_msg)
        
        # Generate the image using our DALL-E function
        image_url = await generate_image_with_dalle(
            prompt=args.get("prompt"),
            variables=data.variables,
            size=args.get("size", "1024x1024"),
            quality=args.get("quality", "standard"),
            style=args.get("style", "vivid")
        )
        
        logger.info(f"✅ DALL-E image generated: {image_url}")
        
        # Stream function completion to Lexia
        completion_msg = f"\n✅ **Function completed successfully:** generate_image"
        lexia_handler.stream_chunk(data, completion_msg)
        
        # Add image generation result to response
        image_result = f"\n\n🎨 **Image Generated Successfully!**\n\n**Prompt:** {args.get('prompt')}\n**Image URL:** {image_url}\n\n*Image created with DALL-E 3*"
        
        # Stream the image result to Lexia
        lexia_handler.stream_chunk(data, image_result)
        
        logger.info(f"✅ Image generation completed: {image_url}")
        
        return image_result, image_url
        
    except Exception as e:
        error_msg = f"Error executing generate_image function: {str(e)}"
        logger.error(error_msg, exc_info=True)
        function_error = f"\n\n❌ **Function Execution Error:** {error_msg}"
        return function_error, None

def get_available_functions() -> list:
    """
    Get the list of available functions for OpenAI.
    
    Returns:
        list: List of function schemas
    """
    return AVAILABLE_FUNCTIONS

async def process_function_calls(
    function_calls: list, 
    lexia_handler, 
    data
) -> tuple[str, str]:
    """
    Process a list of function calls and return the combined result.
    
    Args:
        function_calls: List of function call objects from OpenAI
        lexia_handler: The Lexia handler instance for streaming updates
        data: The original chat message data
        
    Returns:
        tuple: (combined_result_message, generated_file_url or None)
    """
    if not function_calls:
        logger.info("🔧 No function calls to process")
        return "", None
    
    logger.info(f"🔧 Processing {len(function_calls)} function calls...")
    logger.info(f"🔧 Function calls details: {function_calls}")
    
    combined_result = ""
    generated_file_url = None
    
    for function_call in function_calls:
        try:
            result, file_url = await execute_function_call(function_call, lexia_handler, data)
            combined_result += result
            
            if file_url and not generated_file_url:
                generated_file_url = file_url
                
        except Exception as e:
            error_msg = f"Error processing function call: {str(e)}"
            logger.error(error_msg, exc_info=True)
            combined_result += f"\n\n❌ **Function Processing Error:** {error_msg}"
    
    return combined_result, generated_file_url
