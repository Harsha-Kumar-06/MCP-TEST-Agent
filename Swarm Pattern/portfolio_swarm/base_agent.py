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
        
        # Analysis caching - only call AI on first iteration
        self._cached_analysis: Optional[AgentAnalysis] = None
        self._analysis_portfolio_hash: Optional[str] = None
        
        # Swarm context - set by orchestrator
        self.consensus_threshold: float = 0.6
        self.total_agents: int = 5
        self.max_iterations: int = 10
        self.votes_needed_to_pass: int = 3
        self.votes_needed_to_fail: int = 3
        
        # Rejection feedback from previous iteration - used to adapt proposals
        self.rejection_feedback: List[str] = []
        self.last_rejection_reasons: List[str] = []
        
        # Subscribe to messages
        self.comm_bus.subscribe_broadcast(self._on_message_received)
        
        logger.info(f"{self.agent_type.value} initialized")
    
    def _get_portfolio_hash(self, portfolio: Portfolio) -> str:
        """Generate hash of portfolio for cache invalidation"""
        positions_str = ",".join(f"{p.ticker}:{p.shares}" for p in sorted(portfolio.positions, key=lambda x: x.ticker))
        return f"{positions_str}:{portfolio.total_value:.0f}"
    
    def _should_use_cached_analysis(self, portfolio: Portfolio) -> bool:
        """Check if we can reuse cached analysis (same portfolio, not first iteration)"""
        if self._cached_analysis is None:
            return False
        current_hash = self._get_portfolio_hash(portfolio)
        return self._analysis_portfolio_hash == current_hash and self.current_iteration > 0
    
    def _cache_analysis(self, analysis: AgentAnalysis, portfolio: Portfolio):
        """Cache analysis result for reuse in subsequent iterations"""
        self._cached_analysis = analysis
        self._analysis_portfolio_hash = self._get_portfolio_hash(portfolio)
    
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
    
    def set_rejection_feedback(self, feedback: List[str]):
        """Set rejection feedback from previous iteration to adapt proposals"""
        self.last_rejection_reasons = feedback
        self.rejection_feedback.extend(feedback)
    
    def clear_rejection_feedback(self):
        """Clear rejection feedback for fresh optimization"""
        self.rejection_feedback = []
        self.last_rejection_reasons = []
    
    def set_swarm_context(self, consensus_threshold: float, total_agents: int, max_iterations: int):
        """Set swarm-level context for consensus awareness"""
        self.consensus_threshold = consensus_threshold
        self.total_agents = total_agents
        self.max_iterations = max_iterations
        # Calculate how many votes needed to pass/fail
        self.votes_needed_to_pass = int(total_agents * consensus_threshold) + 1
        self.votes_needed_to_fail = total_agents - self.votes_needed_to_pass + 1
    
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
