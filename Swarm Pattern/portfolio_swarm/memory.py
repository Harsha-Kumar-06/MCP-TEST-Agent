"""
Conversation Memory for Portfolio Swarm
Maintains context across interactions and optimization sessions
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
import json
from pathlib import Path


@dataclass
class ConversationMessage:
    """A single message in the conversation"""
    role: str  # "user", "assistant", "agent", "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ConversationContext:
    """Context state for a conversation"""
    portfolio_summary: Optional[str] = None
    strategy_name: Optional[str] = None
    last_optimization_result: Optional[Dict] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    active_concerns: List[str] = field(default_factory=list)


class ConversationMemory:
    """
    Manages conversation history and context for the portfolio swarm system
    
    Features:
    - Windowed message history (keeps last k messages)
    - Context persistence across sessions
    - Summary generation for long conversations
    - Export/import functionality
    """
    
    def __init__(self, window_size: int = 20, persistence_path: Optional[str] = None):
        """
        Initialize conversation memory
        
        Args:
            window_size: Number of messages to keep in active memory
            persistence_path: Optional path to persist conversation data
        """
        self.window_size = window_size
        self.messages: deque = deque(maxlen=window_size)
        self.full_history: List[ConversationMessage] = []  # Complete history
        self.context = ConversationContext()
        
        if persistence_path:
            self.persistence_path = Path(persistence_path)
            self._load_from_disk()
        else:
            self.persistence_path = None
        
        # Conversation summaries for long contexts
        self.summaries: List[str] = []
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation"""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self.messages.append(message)
        self.full_history.append(message)
        
        # Update context based on message
        self._update_context(message)
        
        # Auto-save if persistence enabled
        if self.persistence_path:
            self._save_to_disk()
    
    def add_user_message(self, content: str, **kwargs):
        """Convenience method to add user message"""
        self.add_message("user", content, kwargs)
    
    def add_assistant_message(self, content: str, **kwargs):
        """Convenience method to add assistant message"""
        self.add_message("assistant", content, kwargs)
    
    def add_agent_message(self, agent_name: str, content: str, **kwargs):
        """Add a message from a specific agent"""
        metadata = {"agent_name": agent_name, **kwargs}
        self.add_message("agent", content, metadata)
    
    def add_system_message(self, content: str, **kwargs):
        """Add a system message"""
        self.add_message("system", content, kwargs)
    
    def get_messages(self, count: Optional[int] = None) -> List[ConversationMessage]:
        """Get recent messages"""
        if count is None:
            return list(self.messages)
        return list(self.messages)[-count:]
    
    def get_messages_as_dicts(self, count: Optional[int] = None) -> List[Dict]:
        """Get messages as dictionaries for API calls"""
        messages = self.get_messages(count)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]
    
    def get_context_string(self) -> str:
        """Get context as a formatted string for prompts"""
        ctx = self.context
        parts = []
        
        if ctx.portfolio_summary:
            parts.append(f"Current Portfolio: {ctx.portfolio_summary}")
        
        if ctx.strategy_name:
            parts.append(f"Selected Strategy: {ctx.strategy_name}")
        
        if ctx.user_preferences:
            prefs = ", ".join(f"{k}: {v}" for k, v in ctx.user_preferences.items())
            parts.append(f"User Preferences: {prefs}")
        
        if ctx.active_concerns:
            parts.append(f"Active Concerns: {', '.join(ctx.active_concerns)}")
        
        if ctx.last_optimization_result:
            result = ctx.last_optimization_result
            parts.append(f"Last Result: {'Consensus' if result.get('consensus') else 'No consensus'} "
                        f"({result.get('approval_rate', 0):.0%} approval)")
        
        return "\n".join(parts) if parts else "No context available"
    
    def set_portfolio_context(self, portfolio_summary: str):
        """Set portfolio summary in context"""
        self.context.portfolio_summary = portfolio_summary
    
    def set_strategy(self, strategy_name: str):
        """Set the selected strategy"""
        self.context.strategy_name = strategy_name
    
    def set_optimization_result(self, result: Dict):
        """Store optimization result in context"""
        self.context.last_optimization_result = result
    
    def add_user_preference(self, key: str, value: Any):
        """Add or update a user preference"""
        self.context.user_preferences[key] = value
    
    def add_concern(self, concern: str):
        """Add an active concern"""
        if concern not in self.context.active_concerns:
            self.context.active_concerns.append(concern)
    
    def clear_concerns(self):
        """Clear all active concerns"""
        self.context.active_concerns = []
    
    def get_summary(self) -> str:
        """Generate a summary of the conversation"""
        if not self.messages:
            return "No conversation history."
        
        user_msgs = [m for m in self.messages if m.role == "user"]
        agent_msgs = [m for m in self.messages if m.role == "agent"]
        
        summary_parts = [
            f"Conversation Summary:",
            f"- Total messages: {len(self.messages)}",
            f"- User messages: {len(user_msgs)}",
            f"- Agent messages: {len(agent_msgs)}",
        ]
        
        if self.context.strategy_name:
            summary_parts.append(f"- Strategy: {self.context.strategy_name}")
        
        if self.context.portfolio_summary:
            summary_parts.append(f"- Portfolio: {self.context.portfolio_summary[:100]}...")
        
        # Add recent topics
        if user_msgs:
            recent = user_msgs[-3:]
            topics = [m.content[:50] + "..." for m in recent]
            summary_parts.append(f"- Recent topics: {'; '.join(topics)}")
        
        return "\n".join(summary_parts)
    
    def clear(self):
        """Clear conversation history"""
        self.messages.clear()
        self.full_history.clear()
        self.context = ConversationContext()
        self.summaries.clear()
        
        if self.persistence_path:
            self._save_to_disk()
    
    def export(self, format: str = "json") -> str:
        """Export conversation in specified format"""
        if format == "json":
            data = {
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "timestamp": m.timestamp,
                        "metadata": m.metadata
                    }
                    for m in self.full_history
                ],
                "context": {
                    "portfolio_summary": self.context.portfolio_summary,
                    "strategy_name": self.context.strategy_name,
                    "user_preferences": self.context.user_preferences,
                    "active_concerns": self.context.active_concerns,
                    "last_result": self.context.last_optimization_result
                },
                "summaries": self.summaries
            }
            return json.dumps(data, indent=2, default=str)
        
        elif format == "text":
            lines = []
            for m in self.full_history:
                role_label = {
                    "user": "YOU",
                    "assistant": "ASSISTANT",
                    "agent": f"AGENT ({m.metadata.get('agent_name', 'Unknown')})",
                    "system": "SYSTEM"
                }.get(m.role, m.role.upper())
                
                lines.append(f"[{m.timestamp}] {role_label}:")
                lines.append(f"  {m.content}")
                lines.append("")
            
            return "\n".join(lines)
        
        return self.export("json")
    
    def _update_context(self, message: ConversationMessage):
        """Update context based on new message"""
        content_lower = message.content.lower()
        
        # Detect strategy mentions
        strategies = ["aggressive", "conservative", "balanced", "tax", "esg", "risk"]
        for strategy in strategies:
            if strategy in content_lower and message.role == "user":
                # User mentioned a strategy preference
                self.context.user_preferences["strategy_preference"] = strategy
        
        # Detect concern keywords
        concerns = ["risk", "loss", "tax", "esg", "compliance", "volatile"]
        for concern in concerns:
            if concern in content_lower and message.role == "user":
                self.add_concern(concern)
    
    def _save_to_disk(self):
        """Save conversation to disk"""
        if not self.persistence_path:
            return
        
        self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.export("json")
        with open(self.persistence_path, 'w', encoding='utf-8') as f:
            f.write(data)
    
    def _load_from_disk(self):
        """Load conversation from disk"""
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Restore messages
            for msg_data in data.get("messages", []):
                msg = ConversationMessage(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=msg_data.get("timestamp", ""),
                    metadata=msg_data.get("metadata", {})
                )
                self.messages.append(msg)
                self.full_history.append(msg)
            
            # Restore context
            ctx = data.get("context", {})
            self.context.portfolio_summary = ctx.get("portfolio_summary")
            self.context.strategy_name = ctx.get("strategy_name")
            self.context.user_preferences = ctx.get("user_preferences", {})
            self.context.active_concerns = ctx.get("active_concerns", [])
            self.context.last_optimization_result = ctx.get("last_result")
            
            # Restore summaries
            self.summaries = data.get("summaries", [])
            
        except Exception as e:
            print(f"Warning: Could not load conversation: {e}")


# Query templates for common operations
QUERY_TEMPLATES = {
    "optimize": "Please optimize my portfolio using the {strategy} strategy",
    "rebalance": "I need to rebalance my portfolio to meet {goal}",
    "analyze_risk": "Can you analyze the risk in my current portfolio?",
    "tax_harvest": "What tax-loss harvesting opportunities exist in my portfolio?",
    "sector_analysis": "Show me my sector allocation and any concentration risks",
    "esg_check": "How does my portfolio score on ESG metrics?",
    "reduce_position": "I want to reduce my position in {ticker}",
    "add_position": "I'm considering adding {ticker} to my portfolio",
    "compliance_check": "Are there any compliance violations in my portfolio?",
    "dividend_info": "What's the dividend yield of my portfolio?"
}


def get_query_template(template_name: str, **kwargs) -> str:
    """Get a query template with variable substitution"""
    if template_name not in QUERY_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
    
    template = QUERY_TEMPLATES[template_name]
    return template.format(**kwargs)


def list_query_templates() -> List[Dict[str, str]]:
    """Get list of available query templates"""
    return [
        {"name": name, "template": template}
        for name, template in QUERY_TEMPLATES.items()
    ]
