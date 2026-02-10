"""
Base agent class for all specialized agents
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from .models import (
    Portfolio, AgentAnalysis, AgentProposal, AgentVote, 
    Message, AgentType, VoteType, TradePlan
)
from .communication import CommunicationBus
import logging

if TYPE_CHECKING:
    from .strategies import OptimizationStrategy

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the swarm"""
    
    def __init__(self, agent_type: AgentType, communication_bus: CommunicationBus):
        self.agent_type = agent_type
        self.comm_bus = communication_bus
        self.current_iteration = 0
        self.analysis_history: List[AgentAnalysis] = []
        self.strategy: Optional['OptimizationStrategy'] = None
        self.strategy_context: str = ""
        
        # Subscribe to messages
        self.comm_bus.subscribe_broadcast(self._on_message_received)
        
        logger.info(f"{self.agent_type.value} initialized")
    
    @abstractmethod
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze portfolio and generate findings"""
        pass
    
    @abstractmethod
    def propose_solution(self, portfolio: Portfolio, context: List[AgentAnalysis]) -> Optional[AgentProposal]:
        """Propose a trade plan based on analysis and context from other agents"""
        pass
    
    @abstractmethod
    def vote_on_proposal(self, proposal: TradePlan, portfolio: Portfolio) -> AgentVote:
        """Vote on a proposed trade plan"""
        pass
    
    def send_message(self, content: str, to_agent: Optional[AgentType] = None, 
                     message_type: str = "debate"):
        """Send a message to another agent or broadcast"""
        message = Message(
            from_agent=self.agent_type,
            to_agent=to_agent,
            content=content,
            iteration=self.current_iteration,
            message_type=message_type
        )
        self.comm_bus.publish(message)
    
    def _on_message_received(self, message: Message):
        """Callback when a message is received"""
        # Filter out own messages
        if message.from_agent == self.agent_type:
            return
        
        # Only process messages for current iteration
        if message.iteration == self.current_iteration:
            self._process_message(message)
    
    def _process_message(self, message: Message):
        """Process incoming message - can be overridden by subclasses"""
        logger.debug(f"{self.agent_type.value} received message from {message.from_agent.value}")
    
    def set_iteration(self, iteration: int):
        """Update current iteration"""
        self.current_iteration = iteration
    
    def set_strategy(self, strategy: 'OptimizationStrategy'):
        """Set the optimization strategy for this agent"""
        from .strategies import strategy_to_prompt
        self.strategy = strategy
        self.strategy_context = strategy_to_prompt(strategy)
        logger.info(f"{self.agent_type.value} strategy set to: {strategy.name}")
    
    def get_strategy_context(self) -> str:
        """Get strategy context for prompts"""
        return self.strategy_context if self.strategy_context else ""
    
    def get_recent_messages(self) -> List[Message]:
        """Get messages from current iteration"""
        return self.comm_bus.get_messages_for_agent(
            self.agent_type, 
            self.current_iteration
        )
    
    def log_analysis(self, analysis: AgentAnalysis):
        """Store analysis for history"""
        self.analysis_history.append(analysis)
