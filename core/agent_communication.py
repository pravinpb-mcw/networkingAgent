"""
Inter-Agent Communication Module

This module provides utilities for agents to communicate with each other,
log their interactions, and broadcast messages to the web dashboard.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import threading
from queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent_communication")


class MessageType(Enum):
    """Types of inter-agent messages"""
    QUERY = "query"
    RESPONSE = "response"
    ALERT = "alert"
    STATUS = "status"
    INSIGHT = "insight"
    ACTION = "action"
    ERROR = "error"


@dataclass
class AgentMessage:
    """Represents a message between agents"""
    id: str
    timestamp: str
    sender: str
    receiver: str
    message_type: MessageType
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata or {}
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class CommunicationBus:
    """
    Central communication bus for inter-agent messaging.
    Maintains message history and broadcasts to WebSocket clients.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._message_counter = 0
        self._message_history: List[AgentMessage] = []
        self._subscribers: Dict[str, List[Callable]] = {}
        self._websocket_clients: List[Any] = []
        self._ws_manager = None
        self._message_queue: Queue = Queue()
        self._max_history = 1000
        
        logger.info("CommunicationBus initialized")
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID"""
        self._message_counter += 1
        return f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._message_counter}"
    
    def send_message(
        self,
        sender: str,
        receiver: str,
        message_type: MessageType,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        """
        Send a message from one agent to another.
        
        Args:
            sender: Name of the sending agent
            receiver: Name of the receiving agent
            message_type: Type of message
            content: Message content
            metadata: Optional additional metadata
            
        Returns:
            The created AgentMessage
        """
        message = AgentMessage(
            id=self._generate_message_id(),
            timestamp=datetime.now().isoformat(),
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            content=content,
            metadata=metadata
        )
        
        # Add to history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]
        
        # Log the message
        logger.info(f"[{message_type.value.upper()}] {sender} -> {receiver}: {str(content)[:200]}")
        
        # Notify subscribers
        self._notify_subscribers(receiver, message)
        
        # Queue for WebSocket broadcast
        self._message_queue.put(message)
        
        return message
    
    def _notify_subscribers(self, agent_name: str, message: AgentMessage):
        """Notify subscribers of a new message"""
        if agent_name in self._subscribers:
            for callback in self._subscribers[agent_name]:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {e}")
    
    def subscribe(self, agent_name: str, callback: Callable[[AgentMessage], None]):
        """Subscribe to messages for a specific agent"""
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(callback)
        logger.info(f"Agent '{agent_name}' subscribed to messages")
    
    def unsubscribe(self, agent_name: str, callback: Callable):
        """Unsubscribe from messages"""
        if agent_name in self._subscribers:
            self._subscribers[agent_name].remove(callback)
    
    def get_message_history(
        self,
        limit: int = 100,
        sender: Optional[str] = None,
        receiver: Optional[str] = None,
        message_type: Optional[MessageType] = None
    ) -> List[AgentMessage]:
        """
        Get message history with optional filters.
        
        Args:
            limit: Maximum number of messages to return
            sender: Filter by sender agent
            receiver: Filter by receiver agent
            message_type: Filter by message type
            
        Returns:
            List of matching messages
        """
        messages = self._message_history.copy()
        
        if sender:
            messages = [m for m in messages if m.sender == sender]
        if receiver:
            messages = [m for m in messages if m.receiver == receiver]
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        
        return messages[-limit:]
    
    def get_pending_messages(self) -> List[AgentMessage]:
        """Get all pending messages from the queue"""
        messages = []
        while not self._message_queue.empty():
            messages.append(self._message_queue.get_nowait())
        return messages
    
    def clear_history(self):
        """Clear message history"""
        self._message_history.clear()
        logger.info("Message history cleared")
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about agent communications"""
        stats = {
            "total_messages": len(self._message_history),
            "by_sender": {},
            "by_receiver": {},
            "by_type": {},
        }
        
        for msg in self._message_history:
            stats["by_sender"][msg.sender] = stats["by_sender"].get(msg.sender, 0) + 1
            stats["by_receiver"][msg.receiver] = stats["by_receiver"].get(msg.receiver, 0) + 1
            stats["by_type"][msg.message_type.value] = stats["by_type"].get(msg.message_type.value, 0) + 1
        
        return stats


# Global communication bus instance
comm_bus = CommunicationBus()


def send_agent_message(
    sender: str,
    receiver: str,
    message_type: MessageType,
    content: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> AgentMessage:
    """Convenience function to send a message via the global bus"""
    return comm_bus.send_message(sender, receiver, message_type, content, metadata)


def get_message_history(limit: int = 100) -> List[Dict[str, Any]]:
    """Get message history as a list of dictionaries"""
    return [m.to_dict() for m in comm_bus.get_message_history(limit)]
