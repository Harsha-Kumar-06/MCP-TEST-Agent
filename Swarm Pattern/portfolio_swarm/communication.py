"""
Communication infrastructure for agent swarm
"""
from typing import List, Dict, Optional, Callable
from collections import defaultdict
from .models import Message, AgentType
import logging

logger = logging.getLogger(__name__)


class CommunicationBus:
    """Central message bus for agent communication"""
    
    def __init__(self):
        self.messages: List[Message] = []
        self.subscribers: Dict[AgentType, List[Callable]] = defaultdict(list)
        self.broadcast_subscribers: List[Callable] = []
    
    def subscribe(self, agent_type: AgentType, callback: Callable):
        """Subscribe an agent to receive messages"""
        self.subscribers[agent_type].append(callback)
        logger.debug(f"{agent_type.value} subscribed to messages")
    
    def subscribe_broadcast(self, callback: Callable):
        """Subscribe to all broadcast messages"""
        self.broadcast_subscribers.append(callback)
    
    def publish(self, message: Message):
        """Publish a message to the bus"""
        self.messages.append(message)
        logger.info(f"Message from {message.from_agent.value}: {message.content[:100]}...")
        
        # Deliver to specific recipient or broadcast
        if message.to_agent is None:
            # Broadcast to all
            for callback in self.broadcast_subscribers:
                callback(message)
        else:
            # Direct message
            for callback in self.subscribers[message.to_agent]:
                callback(message)
    
    def get_messages_for_agent(self, agent_type: AgentType, iteration: Optional[int] = None) -> List[Message]:
        """Retrieve messages for a specific agent"""
        messages = [
            m for m in self.messages 
            if m.to_agent == agent_type or m.to_agent is None
        ]
        
        if iteration is not None:
            messages = [m for m in messages if m.iteration == iteration]
        
        return messages
    
    def get_conversation_history(self, iteration: Optional[int] = None) -> List[Message]:
        """Get full conversation history"""
        if iteration is not None:
            return [m for m in self.messages if m.iteration == iteration]
        return self.messages.copy()
    
    def clear_history(self):
        """Clear all messages"""
        self.messages.clear()
        logger.info("Communication history cleared")


class DebateFormatter:
    """Formats agent debates into readable summaries"""
    
    @staticmethod
    def format_iteration(messages: List[Message], iteration: int) -> str:
        """Format messages from a single iteration"""
        output = [f"\n{'='*80}", f"ITERATION {iteration}", f"{'='*80}\n"]
        
        for msg in messages:
            if msg.iteration == iteration:
                header = f"{msg.from_agent.value.upper()}"
                if msg.to_agent:
                    header += f" → {msg.to_agent.value.upper()}"
                else:
                    header += " → ALL"
                
                output.append(f"\n{header}:")
                output.append(f"{msg.content}\n")
        
        return "\n".join(output)
    
    @staticmethod
    def format_full_debate(messages: List[Message]) -> str:
        """Format entire debate history"""
        if not messages:
            return "No messages in debate history"
        
        max_iteration = max(m.iteration for m in messages)
        output = []
        
        for i in range(max_iteration + 1):
            output.append(DebateFormatter.format_iteration(messages, i))
        
        return "\n".join(output)
