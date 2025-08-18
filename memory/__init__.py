"""
Memory Module for AI Agent
==========================

Handles conversation memory and history management for the AI agent.
This module provides a clean, extensible way to manage conversation state
separate from the Lexia platform.

Features:
- Thread-based conversation management
- Configurable history limits
- Timestamp tracking for messages
- Easy extension for persistent storage

Usage:
    from memory import ConversationManager
    
    # Initialize with custom history limit
    manager = ConversationManager(max_history=20)
    
    # Add messages to a thread
    manager.add_message("thread_123", "user", "Hello")
    manager.add_message("thread_123", "assistant", "Hi there!")
    
    # Get conversation history
    history = manager.get_history("thread_123")
"""

from .conversation_manager import ConversationManager

__all__ = ['ConversationManager']
