"""
Conversation Manager for AI Agent Memory
=======================================

Manages conversation history and thread management for the AI agent.
This class provides a simple, in-memory conversation store that can be
easily extended to use databases, files, or other persistent storage.

Features:
- Thread-based conversation organization
- Configurable history limits per thread
- Automatic timestamp tracking
- Memory-efficient storage with automatic cleanup
- Easy extension for custom storage backends

Example:
    # Initialize with 20 message history limit
    manager = ConversationManager(max_history=20)
    
    # Add messages to different threads
    manager.add_message("user_123", "user", "Hello, how are you?")
    manager.add_message("user_123", "assistant", "I'm doing well, thank you!")
    manager.add_message("user_456", "user", "What's the weather like?")
    
    # Get conversation history
    history = manager.get_history("user_123")
    # Returns: [{"role": "user", "content": "Hello, how are you?", "timestamp": "..."}, ...]
    
    # Check thread status
    active_threads = manager.get_all_threads()
    thread_count = manager.get_thread_count()
"""

from typing import List, Dict, Any
from collections import defaultdict


class ConversationManager:
    """
    Manages conversation history and threading for the AI agent.
    
    This class provides an in-memory conversation store that automatically
    manages conversation history per thread. It's designed to be simple
    to use while providing all the functionality needed for basic
    conversation management.
    
    Attributes:
        max_history (int): Maximum number of messages to keep per thread
        conversations (Dict): Internal storage of conversation data
        
    Example:
        # Create manager with 15 message history limit
        manager = ConversationManager(max_history=15)
        
        # Add messages to a conversation thread
        manager.add_message("thread_1", "user", "What's 2+2?")
        manager.add_message("thread_1", "assistant", "2+2 equals 4")
        
        # Retrieve conversation history
        history = manager.get_history("thread_1")
        print(f"Thread has {len(history)} messages")
    """
    
    def __init__(self, max_history: int = 10):
        """
        Initialize the conversation manager.
        
        Args:
            max_history: Maximum number of messages to keep per thread.
                        Older messages are automatically removed when this limit is exceeded.
        """
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    
    def add_message(self, thread_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
        This method automatically manages the conversation history by:
        - Adding the new message with a timestamp
        - Removing old messages if the thread exceeds max_history
        - Creating the thread if it doesn't exist
        
        Args:
            thread_id: Unique identifier for the conversation thread
            role: Role of the message sender ("user" or "assistant")
            content: The message content/text
            
        Example:
            manager.add_message("user_123", "user", "Hello there!")
            manager.add_message("user_123", "assistant", "Hi! How can I help you?")
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': self._get_timestamp()
        }
        
        self.conversations[thread_id].append(message)
        
        # Maintain max history limit by removing oldest messages
        if len(self.conversations[thread_id]) > self.max_history:
            self.conversations[thread_id].pop(0)
    
    def get_history(self, thread_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a specific thread.
        
        Args:
            thread_id: The thread identifier to retrieve history for
            
        Returns:
            List of message dictionaries, each containing:
            - role: "user" or "assistant"
            - content: The message text
            - timestamp: ISO format timestamp
            
        Example:
            history = manager.get_history("user_123")
            for msg in history:
                print(f"{msg['role']}: {msg['content']}")
        """
        return self.conversations.get(thread_id, [])
    
    def clear_history(self, thread_id: str) -> None:
        """
        Clear conversation history for a specific thread.
        
        This completely removes all messages for the specified thread.
        Useful for privacy concerns or starting fresh conversations.
        
        Args:
            thread_id: The thread identifier to clear
            
        Example:
            manager.clear_history("user_123")  # Removes all messages for user_123
        """
        if thread_id in self.conversations:
            del self.conversations[thread_id]
    
    def get_all_threads(self) -> List[str]:
        """
        Get all active conversation thread IDs.
        
        Returns:
            List of all thread identifiers that currently have messages
            
        Example:
            active_threads = manager.get_all_threads()
            print(f"Active conversations: {len(active_threads)}")
            for thread_id in active_threads:
                history = manager.get_history(thread_id)
                print(f"Thread {thread_id}: {len(history)} messages")
        """
        return list(self.conversations.keys())
    
    def get_thread_count(self) -> int:
        """
        Get the count of active threads.
        
        Returns:
            Number of threads that currently have conversation history
            
        Example:
            count = manager.get_thread_count()
            print(f"Managing {count} conversation threads")
        """
        return len(self.conversations)
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp for message tracking.
        
        Returns:
            ISO format timestamp string
            
        Note:
            This is a private method used internally for timestamp generation.
            Override this method if you need custom timestamp formatting.
        """
        from datetime import datetime
        return datetime.now().isoformat()
