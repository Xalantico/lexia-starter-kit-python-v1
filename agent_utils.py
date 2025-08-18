"""
AI Agent Utilities
=================

Utility functions for the AI agent's OpenAI integration.
These functions handle the formatting and preparation of data for OpenAI API calls,
making it easy to customize system prompts and message formatting.

Features:
- System prompt formatting with project context
- OpenAI message format conversion
- Clean separation of prompt logic from main processing
- Easy customization for different use cases

Example:
    # Format system prompt with project context
    system_prompt = format_system_prompt(
        system_message="You are a helpful AI assistant.",
        project_system_message="This project is about customer support."
    )
    
    # Format messages for OpenAI API
    messages = format_messages_for_openai(
        system_prompt=system_prompt,
        conversation_history=history,
        current_message="How can I help you?"
    )
"""

from typing import List, Dict, Any


def format_system_prompt(system_message: str = None, project_system_message: str = None) -> str:
    """
    Format system prompt for OpenAI from agent's configuration.
    
    This function combines the base system message with optional project-specific
    context to create a comprehensive system prompt for the AI model.
    
    Args:
        system_message: Base system message defining the AI's role and behavior.
                       If None, uses a default helpful assistant prompt.
        project_system_message: Additional project-specific context or instructions.
                               This is appended to the base system message.
    
    Returns:
        Formatted system prompt string ready for OpenAI API
        
    Example:
        # Basic usage with default prompt
        prompt = format_system_prompt()
        # Returns: "You are a helpful AI assistant."
        
        # With custom system message
        prompt = format_system_prompt("You are a coding expert.")
        # Returns: "You are a coding expert."
        
        # With both system and project context
        prompt = format_system_prompt(
            "You are a helpful AI assistant.",
            "This project is about customer support for a tech company."
        )
        # Returns: "You are a helpful AI assistant.\n\nProject Context: This project is about customer support for a tech company."
    """
    base_prompt = "You are a helpful AI assistant."
    
    if system_message:
        base_prompt = system_message
    
    if project_system_message:
        base_prompt += f"\n\nProject Context: {project_system_message}"
    
    return base_prompt


def format_messages_for_openai(
    system_prompt: str, 
    conversation_history: List[Dict[str, str]], 
    current_message: str
) -> List[Dict[str, str]]:
    """
    Format conversation history and current message for OpenAI API.
    
    This function takes the system prompt, conversation history, and current
    user message to create the proper message format expected by OpenAI's
    chat completion API.
    
    Args:
        system_prompt: The formatted system prompt defining AI behavior
        conversation_history: List of previous conversation messages, each containing:
                            - role: "user" or "assistant"
                            - content: The message text
                            - timestamp: Message timestamp (not used by OpenAI)
        current_message: The current user message to process
    
    Returns:
        List of message dictionaries in OpenAI API format:
        - role: "system", "user", or "assistant"
        - content: The message content
        
    Example:
        # Format messages for OpenAI
        messages = format_messages_for_openai(
            system_prompt="You are a helpful assistant.",
            conversation_history=[
                {"role": "user", "content": "Hello", "timestamp": "..."},
                {"role": "assistant", "content": "Hi there!", "timestamp": "..."}
            ],
            current_message="How are you today?"
        )
        
        # Result:
        # [
        #     {"role": "system", "content": "You are a helpful assistant."},
        #     {"role": "user", "content": "Hello"},
        #     {"role": "assistant", "content": "Hi there!"},
        #     {"role": "user", "content": "How are you today?"}
        # ]
        
    Note:
        The timestamp field from conversation history is ignored as OpenAI
        doesn't use it. Only role and content are included in the API request.
    """
    # Start with system prompt
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (excluding timestamp)
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Add current user message
    messages.append({"role": "user", "content": current_message})
    
    return messages
