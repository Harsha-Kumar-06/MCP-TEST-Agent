"""
Swarm orchestrator - coordinates multi-agent portfolio optimization
"""
from typing import List, Optional, Dict
from .models import (
    Portfolio, AgentAnalysis, AgentProposal, AgentVote, 
    ConsensusResult, TradePlan, VoteType
)
from .communication import CommunicationBus, DebateFormatter
from .base_agent import BaseAgent
from .strategies import OptimizationStrategy, StrategyType, get_strategy, strategy_to_prompt, STRATEGY_TEMPLATES
import logging

logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """Coordinates the swarm of agents to reach consensus on portfolio rebalancing"""
    
    def __init__(self, 
                 agents: List[BaseAgent],
                 max_iterations: int = 10,
                 min_iterations: int = 1,
                 consensus_threshold: float = 0.6,
                 require_unanimous: bool = False,
                 progress_callback=None,
                 strategy: Optional[OptimizationStrategy] = None):
        """
        Initialize swarm orchestrator
        
        Args:
            agents: List of specialized agents
            max_iterations: Maximum debate iterations
            min_iterations: Minimum iterations before allowing consensus (forces debate)
            consensus_threshold: Minimum approval rate (0.0-1.0)
            require_unanimous: If True, requires all agents to approve
            progress_callback: Optional callback function(iteration, phase, details)
            strategy: Optional optimization strategy to guide agent behavior
        """
        # Validate minimum agents for meaningful multi-agent debate
        if len(agents) < 2:
            raise ValueError(
                f"Multi-agent debate requires at least 2 active agents, but only {len(agents)} provided. "
                "A single agent automatically results in 100% consensus, defeating the purpose of swarm intelligence."
            )
        
        self.agents = agents
        self.max_iterations = max_iterations
        self.min_iterations = min(min_iterations, max_iterations)  # Can't exceed max
        self.consensus_threshold = consensus_threshold
        self.require_unanimous = require_unanimous
        self.comm_bus = CommunicationBus()
        self.progress_callback = progress_callback
        
        # Set optimization strategy (default to Balanced if not provided)
        self.strategy = strategy or get_strategy(StrategyType.BALANCED)
        self.strategy_prompt = strategy_to_prompt(self.strategy)
        
        # Wire agents to communication bus and strategy
        for agent in self.agents:
            agent.comm_bus = self.comm_bus
            agent.set_strategy(self.strategy)
        
        self.current_iteration = 0
        self.consensus_result: Optional[ConsensusResult] = None
        self.last_consensus: Optional[ConsensusResult] = None  # Track last voting result
        self.iteration_history = []  # Track each iteration's key events
        
        logger.info(f"Swarm initialized with {len(agents)} agents")
        logger.info(f"Strategy: {self.strategy.name}")
        logger.info(f"Iterations: min={self.min_iterations}, max={self.max_iterations}")
    
    def run_rebalancing_swarm(self, portfolio: Portfolio) -> ConsensusResult:
        """
        Execute the swarm optimization process
        
        Returns:
            ConsensusResult with approved trade plan or failure status
        """
        logger.info("=" * 80)
        logger.info("SWARM REBALANCING SESSION STARTED")
        logger.info("=" * 80)
        
        if self.progress_callback:
            self.progress_callback(0, "Initializing", "Starting multi-agent optimization")
        
        # Clear rejection feedback from any previous run
        self._last_rejection_feedback = []
        for agent in self.agents:
            if hasattr(agent, 'clear_rejection_feedback'):
                agent.clear_rejection_feedback()
        
        # Check initial compliance
        violations = portfolio.get_compliance_violations()
        if violations:
            logger.warning("Initial compliance violations detected:")
            for v in violations:
                logger.warning(f"  - {v}")
        
        # Main iteration loop
        for iteration in range(self.max_iterations):
            self.current_iteration = iteration
            logger.info(f"\n{'='*80}\nITERATION {iteration + 1}\n{'='*80}")
            
            if self.progress_callback:
                self.progress_callback(iteration + 1, "Analyzing", f"Iteration {iteration + 1}/{self.max_iterations}")
            
            # Update all agents with current iteration and pass rejection feedback
            for agent in self.agents:
                agent.set_iteration(iteration)
                agent.set_swarm_context(self.consensus_threshold, len(self.agents), self.max_iterations)
                # Pass rejection feedback from previous iteration (if any)
                if iteration > 0 and hasattr(self, '_last_rejection_feedback'):
                    agent.set_rejection_feedback(self._last_rejection_feedback)
            
            # Phase 1: All agents analyze current state
            if self.progress_callback:
                self.progress_callback(iteration + 1, "Analysis", "Agents analyzing portfolio")
            analyses = self._parallel_analysis(portfolio)
            
            # Phase 2: Agents debate and refine
            if iteration > 0:
                if self.progress_callback:
                    self.progress_callback(iteration + 1, "Debate", "Inter-agent discussion")
                self._iterative_debate(portfolio, analyses)
            
            # Phase 3: Generate proposals
            if self.progress_callback:
                self.progress_callback(iteration + 1, "Proposals", "Generating trade proposals")
            proposals = self._collect_proposals(portfolio, analyses)
            
            if not proposals:
                logger.warning("No proposals generated in iteration {iteration + 1}")
                continue
            
            # Phase 4: Vote on best proposal
            if self.progress_callback:
                self.progress_callback(iteration + 1, "Voting", "Agents voting on best proposal")
            best_proposal = self._select_best_proposal(proposals)
            consensus = self._vote_on_proposal(best_proposal, portfolio)
            
            # Save last consensus for fallback
            self.last_consensus = consensus
            
            # Collect rejection feedback for next iteration
            # This helps agents adapt their proposals to address concerns
            self._last_rejection_feedback = []
            for vote in consensus.votes:
                if vote.vote == VoteType.REJECT:
                    # Extract key reason from rationale
                    self._last_rejection_feedback.append(f"{vote.agent_type.value}: {vote.rationale}")
                    # Also add specific concerns
                    if vote.concerns:
                        self._last_rejection_feedback.extend(vote.concerns)
            
            # Track iteration history for timeline visualization
            iteration_record = {
                'iteration': iteration + 1,
                'approval_rate': consensus.approval_rate,
                'proposal': {
                    'from_agent': best_proposal.agent_type.value.replace('_', ' ').title(),
                    'conviction': best_proposal.conviction,
                    'rationale': best_proposal.rationale[:150] if len(best_proposal.rationale) > 150 else best_proposal.rationale,
                    'trades': [
                        {
                            'action': t.action,
                            'ticker': t.ticker,
                            'shares': t.shares,
                            'value': t.notional_value
                        }
                        for t in best_proposal.trade_plan.trades
                    ],
                    'total_notional': best_proposal.trade_plan.total_notional,
                    'num_trades': len(best_proposal.trade_plan.trades)
                },
                'votes': [
                    {
                        'agent': v.agent_type.value.replace('_', ' ').title(),
                        'vote': v.vote.value,
                        'rationale': v.rationale[:100] + '...' if len(v.rationale) > 100 else v.rationale
                    }
                    for v in consensus.votes
                ],
                'key_concerns': self._extract_key_concerns(consensus.votes),
                'rejection_feedback': self._last_rejection_feedback[:3] if self._last_rejection_feedback else [],
                'consensus_reached': self._check_consensus(consensus) and (iteration + 1 >= self.min_iterations)
            }
            self.iteration_history.append(iteration_record)
            
            # Check for API quota errors in votes (early stopping)
            quota_errors = sum(1 for v in consensus.votes if 'quota' in v.rationale.lower() or 'api' in v.rationale.lower())
            if quota_errors >= len(consensus.votes) * 0.6:  # If 60%+ agents hit quota errors
                logger.error(f"\n{'='*80}")
                logger.error("STOPPING EARLY: API QUOTA EXHAUSTED")
                logger.error(f"{'='*80}")
                logger.error(f"{quota_errors}/{len(consensus.votes)} agents unable to access API")
                logger.error("Consider: 1) Wait for quota reset, 2) Reduce agents/iterations, 3) Upgrade API plan")
                if self.progress_callback:
                    self.progress_callback(iteration + 1, "Stopped", f"API quota exhausted - stopping early")
                return self._fallback_strategy(portfolio)
            
            # Check for consensus
            # ALWAYS stop on 100% (unanimous) approval - no point continuing
            # Otherwise, respect min_iterations setting
            unanimous = consensus.approval_rate >= 0.99  # 100% or very close
            consensus_reached = self._check_consensus(consensus)
            past_min_iterations = iteration + 1 >= self.min_iterations
            
            if unanimous and consensus_reached:
                # 100% approval - always stop immediately
                logger.info("\n" + "="*80)
                logger.info("UNANIMOUS CONSENSUS ACHIEVED!")
                logger.info("="*80)
                self.consensus_result = consensus
                if self.progress_callback:
                    self.progress_callback(iteration + 1, "Complete", f"Unanimous consensus! ({consensus.approval_rate:.0%} approval)")
                return consensus
            elif past_min_iterations and consensus_reached:
                logger.info("\n" + "="*80)
                logger.info("CONSENSUS ACHIEVED!")
                logger.info("="*80)
                self.consensus_result = consensus
                if self.progress_callback:
                    self.progress_callback(iteration + 1, "Complete", f"Consensus reached! ({consensus.approval_rate:.0%} approval)")
                return consensus
            elif iteration + 1 < self.min_iterations:
                logger.info(f"\n⏳ Iteration {iteration + 1}/{self.min_iterations} completed (min_iterations not reached yet)")
                if self.progress_callback:
                    self.progress_callback(iteration + 1, "Continuing", f"Min iterations: {iteration + 1}/{self.min_iterations}")
        
        # Max iterations reached without consensus
        logger.warning("\n" + "="*80)
        logger.warning("MAX ITERATIONS REACHED - NO CONSENSUS")
        logger.warning("="*80)
        if self.progress_callback:
            self.progress_callback(self.max_iterations, "Fallback", "Max iterations reached, using fallback strategy")
        return self._fallback_strategy(portfolio)
    
    def _parallel_analysis(self, portfolio: Portfolio) -> List[AgentAnalysis]:
        """Phase 1: All agents analyze portfolio independently"""
        logger.info("\nPhase 1: Parallel Analysis")
        logger.info("-" * 40)
        
        analyses = []
        for agent in self.agents:
            analysis = agent.analyze(portfolio)
            agent.log_analysis(analysis)
            analyses.append(analysis)
            
            # Broadcast findings
            agent.send_message(
                content=f"FINDINGS: {analysis.findings}\nRECOMMENDATION: {analysis.recommendation}\nCONVICTION: {analysis.conviction}/10",
                message_type="analysis"
            )
            
            logger.info(f"\n{agent.agent_type.value.upper()}:")
            logger.info(f"  Conviction: {analysis.conviction}/10")
            logger.info(f"  Key finding: {analysis.findings[:100]}...")
        
        return analyses
    
    def _iterative_debate(self, portfolio: Portfolio, analyses: List[AgentAnalysis]):
        """Phase 2: Agents debate and challenge each other"""
        logger.info("\nPhase 2: Inter-Agent Debate")
        logger.info("-" * 40)
        
        # Allow agents to respond to each other's analyses
        # In a real implementation, this would use LLM to generate contextual responses
        # For now, we'll have agents flag conflicts
        
        for agent in self.agents:
            conflicts = agent.analyze(portfolio).concerns
            if conflicts:
                for concern in conflicts:
                    agent.send_message(
                        content=f"CONCERN: {concern}",
                        message_type="debate"
                    )
    
    def _collect_proposals(self, portfolio: Portfolio, analyses: List[AgentAnalysis]) -> List[AgentProposal]:
        """Phase 3: Collect trade plan proposals from agents"""
        logger.info("\nPhase 3: Proposal Collection")
        logger.info("-" * 40)
        
        proposals = []
        for agent in self.agents:
            proposal = agent.propose_solution(portfolio, analyses)
            if proposal:
                proposals.append(proposal)
                logger.info(f"\n{agent.agent_type.value.upper()} proposed:")
                logger.info(f"  Trades: {len(proposal.trade_plan.trades)}")
                logger.info(f"  Total notional: ${proposal.trade_plan.total_notional:,.0f}")
        
        return proposals
    
    def _select_best_proposal(self, proposals: List[AgentProposal]) -> AgentProposal:
        """Select the proposal with highest average conviction"""
        if not proposals:
            raise ValueError("No proposals to evaluate")
        
        # Sort by conviction score
        best = max(proposals, key=lambda p: p.conviction)
        logger.info(f"\nBest proposal from: {best.agent_type.value} (conviction: {best.conviction}/10)")
        return best
    
    def _vote_on_proposal(self, proposal: AgentProposal, portfolio: Portfolio) -> ConsensusResult:
        """Phase 4: All agents vote on the proposal"""
        logger.info("\nPhase 4: Voting on Proposal")
        logger.info("-" * 40)
        
        votes = []
        for agent in self.agents:
            vote = agent.vote_on_proposal(proposal.trade_plan, portfolio)
            votes.append(vote)
            
            vote_symbol = "✅" if vote.vote == VoteType.APPROVE else "❌" if vote.vote == VoteType.REJECT else "⚠️"
            logger.info(f"{vote_symbol} {agent.agent_type.value.upper()}: {vote.vote.value}")
            logger.info(f"   Rationale: {vote.rationale[:100]}...")
        
        # Calculate approval rate
        approve_count = sum(1 for v in votes if v.vote == VoteType.APPROVE)
        total_votes = len([v for v in votes if v.vote != VoteType.ABSTAIN])
        approval_rate = approve_count / total_votes if total_votes > 0 else 0
        
        approved = approval_rate >= self.consensus_threshold
        if self.require_unanimous:
            approved = all(v.vote == VoteType.APPROVE for v in votes)
        
        logger.info(f"\nApproval Rate: {approval_rate:.1%} (threshold: {self.consensus_threshold:.1%})")
        
        return ConsensusResult(
            approved=approved,
            trade_plan=proposal.trade_plan if approved else None,
            votes=votes,
            approval_rate=approval_rate,
            iteration=self.current_iteration
        )
    
    def _check_consensus(self, consensus: ConsensusResult) -> bool:
        """Check if consensus has been reached"""
        if self.require_unanimous:
            return consensus.unanimous
        return consensus.approved
    
    def _extract_key_concerns(self, votes) -> List[str]:
        """Extract key concerns from agent votes for timeline display"""
        concerns = []
        keywords = ['risk', 'compliance', 'tax', 'esg', 'concentration', 'beta', 'volatility', 'diversif']
        
        for vote in votes:
            if vote.vote.value != 'approve':
                rationale = vote.rationale.lower()
                for keyword in keywords:
                    if keyword in rationale:
                        # Extract a short concern phrase
                        agent_name = vote.agent_type.value.replace('_', ' ').title()
                        concerns.append(f"{agent_name}: {keyword.title()} concern")
                        break
        
        return concerns[:3]  # Return top 3 concerns
    
    def _fallback_strategy(self, portfolio: Portfolio) -> ConsensusResult:
        """Fallback if no consensus reached - return last voting results"""
        logger.warning("Executing fallback strategy: Compliance-first approach")
        
        violations = portfolio.get_compliance_violations()
        if violations:
            # Create a minimal trade plan to fix compliance
            # In real implementation, would use risk agent's recommendation
            logger.info("Creating minimal compliance fix...")
        
        # Return the last consensus result with votes, but mark as not approved
        if self.last_consensus:
            logger.info(f"Returning last voting results: {len(self.last_consensus.votes)} votes recorded")
            return ConsensusResult(
                approved=False,
                trade_plan=self.last_consensus.trade_plan,
                votes=self.last_consensus.votes,
                approval_rate=self.last_consensus.approval_rate,
                iteration=self.current_iteration
            )
        
        # No votes at all - return empty
        return ConsensusResult(
            approved=False,
            trade_plan=None,
            votes=[],
            approval_rate=0.0,
            iteration=self.current_iteration
        )
    
    def get_debate_summary(self) -> str:
        """Get formatted summary of the entire debate"""
        messages = self.comm_bus.get_conversation_history()
        return DebateFormatter.format_full_debate(messages)
    
    def get_metrics(self) -> Dict:
        """Get swarm performance metrics"""
        return {
            "iterations_used": self.current_iteration + 1,
            "max_iterations": self.max_iterations,
            "consensus_reached": self.consensus_result.approved if self.consensus_result else False,
            "total_messages": len(self.comm_bus.messages),
            "agents_count": len(self.agents)
        }
