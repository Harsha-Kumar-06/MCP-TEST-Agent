"""
Enhanced Logging Utilities for Portfolio Swarm
Provides structured logging, agent handoff tracking, and session analytics
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
import threading


# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class AgentHandoff:
    """Record of an agent handoff event"""
    timestamp: str
    from_agent: str
    to_agent: str
    reason: str
    iteration: int
    context: Optional[str] = None


@dataclass
class SessionMetrics:
    """Metrics for a single optimization session"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    portfolio_value: float = 0.0
    positions_count: int = 0
    strategy_name: str = "Balanced"
    iterations_used: int = 0
    consensus_reached: bool = False
    approval_rate: float = 0.0
    total_messages: int = 0
    handoffs: List[AgentHandoff] = field(default_factory=list)
    agent_votes: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class SwarmLogger:
    """Enhanced logger for the swarm optimization process"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = LOGS_DIR / f"swarm_{self.session_id}.log"
        self.json_log_file = LOGS_DIR / f"swarm_{self.session_id}.json"
        
        # Configure file handler
        self.logger = logging.getLogger("SwarmAgent")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler - detailed logs
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler - info and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Session metrics
        self.current_session: Optional[SessionMetrics] = None
        self.all_sessions: List[SessionMetrics] = []
        
        # Callbacks for real-time updates
        self.callbacks: List[Callable] = []
    
    def start_session(self, portfolio_value: float = 0, positions_count: int = 0, 
                      strategy_name: str = "Balanced") -> str:
        """Start a new optimization session"""
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = SessionMetrics(
            session_id=self.session_id,
            start_time=datetime.now().isoformat(),
            portfolio_value=portfolio_value,
            positions_count=positions_count,
            strategy_name=strategy_name
        )
        
        self.logger.info(f"=" * 60)
        self.logger.info(f"SESSION STARTED: {self.session_id}")
        self.logger.info(f"Strategy: {strategy_name}")
        self.logger.info(f"Portfolio: ${portfolio_value:,.2f} ({positions_count} positions)")
        self.logger.info(f"=" * 60)
        
        self._notify_callbacks("session_start", {
            "session_id": self.session_id,
            "strategy": strategy_name
        })
        
        return self.session_id
    
    def end_session(self, consensus_reached: bool = False, approval_rate: float = 0.0,
                   iterations_used: int = 0, total_messages: int = 0):
        """End the current session"""
        if self.current_session:
            self.current_session.end_time = datetime.now().isoformat()
            self.current_session.consensus_reached = consensus_reached
            self.current_session.approval_rate = approval_rate
            self.current_session.iterations_used = iterations_used
            self.current_session.total_messages = total_messages
            
            # Save session to JSON
            self._save_session_json()
            
            self.all_sessions.append(self.current_session)
            
            self.logger.info(f"=" * 60)
            self.logger.info(f"SESSION ENDED: {self.session_id}")
            self.logger.info(f"Consensus: {'REACHED' if consensus_reached else 'NOT REACHED'}")
            self.logger.info(f"Approval Rate: {approval_rate:.1%}")
            self.logger.info(f"Iterations: {iterations_used}")
            self.logger.info(f"=" * 60)
            
            self._notify_callbacks("session_end", {
                "consensus": consensus_reached,
                "approval_rate": approval_rate
            })
    
    def log_agent_handoff(self, from_agent: str, to_agent: str, reason: str, 
                         iteration: int = 0, context: Optional[str] = None):
        """Log an agent handoff event"""
        handoff = AgentHandoff(
            timestamp=datetime.now().isoformat(),
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            iteration=iteration,
            context=context
        )
        
        if self.current_session:
            self.current_session.handoffs.append(handoff)
        
        self.logger.info(f"HANDOFF: {from_agent} -> {to_agent} | {reason}")
        
        self._notify_callbacks("handoff", {
            "from": from_agent,
            "to": to_agent,
            "reason": reason
        })
    
    def log_agent_vote(self, agent_name: str, vote: str, rationale: str):
        """Log an agent's vote"""
        if self.current_session:
            self.current_session.agent_votes[agent_name] = vote
        
        vote_symbol = "✅" if vote.lower() == "approve" else "❌" if vote.lower() == "reject" else "⚠️"
        self.logger.info(f"{vote_symbol} {agent_name}: {vote}")
        self.logger.debug(f"   Rationale: {rationale[:100]}...")
        
        self._notify_callbacks("vote", {
            "agent": agent_name,
            "vote": vote,
            "rationale": rationale[:200]
        })
    
    def log_phase(self, iteration: int, phase: str, details: str = ""):
        """Log a phase change in the optimization"""
        self.logger.info(f"[Iter {iteration}] Phase: {phase}")
        if details:
            self.logger.debug(f"   Details: {details}")
        
        self._notify_callbacks("phase", {
            "iteration": iteration,
            "phase": phase,
            "details": details
        })
    
    def log_error(self, error_message: str, exception: Optional[Exception] = None):
        """Log an error"""
        if self.current_session:
            self.current_session.errors.append(error_message)
        
        self.logger.error(f"ERROR: {error_message}")
        if exception:
            self.logger.exception(exception)
        
        self._notify_callbacks("error", {"message": error_message})
    
    def log_analysis(self, agent_name: str, conviction: int, finding: str):
        """Log agent analysis"""
        self.logger.info(f"📊 {agent_name} Analysis (Conviction: {conviction}/10)")
        self.logger.debug(f"   Finding: {finding[:150]}...")
        
        self._notify_callbacks("analysis", {
            "agent": agent_name,
            "conviction": conviction,
            "finding": finding[:200]
        })
    
    def log_trade(self, action: str, ticker: str, shares: int, value: float, rationale: str):
        """Log a proposed trade"""
        self.logger.info(f"💹 {action} {shares:,} {ticker} (${value:,.2f})")
        self.logger.debug(f"   Rationale: {rationale[:100]}...")
    
    def add_callback(self, callback: Callable):
        """Add a callback for real-time updates"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Notify all registered callbacks"""
        for callback in self.callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                self.logger.warning(f"Callback error: {e}")
    
    def _save_session_json(self):
        """Save current session to JSON file"""
        if self.current_session:
            session_dict = asdict(self.current_session)
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, indent=2, default=str)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.current_session:
            return {}
        
        return {
            "session_id": self.current_session.session_id,
            "strategy": self.current_session.strategy_name,
            "portfolio_value": f"${self.current_session.portfolio_value:,.2f}",
            "positions": self.current_session.positions_count,
            "iterations": self.current_session.iterations_used,
            "consensus": self.current_session.consensus_reached,
            "approval_rate": f"{self.current_session.approval_rate:.1%}",
            "handoffs": len(self.current_session.handoffs),
            "errors": len(self.current_session.errors)
        }
    
    def export_session_log(self, format: str = "json") -> str:
        """Export session log in specified format"""
        if not self.current_session:
            return ""
        
        if format == "json":
            return json.dumps(asdict(self.current_session), indent=2, default=str)
        elif format == "text":
            return self._session_to_text()
        elif format == "csv":
            return self._session_to_csv()
        else:
            return json.dumps(asdict(self.current_session), indent=2, default=str)
    
    def _session_to_text(self) -> str:
        """Convert session to text format"""
        if not self.current_session:
            return ""
        
        lines = [
            "=" * 60,
            f"SWARM OPTIMIZATION SESSION REPORT",
            f"Session ID: {self.current_session.session_id}",
            f"Strategy: {self.current_session.strategy_name}",
            "=" * 60,
            "",
            f"Portfolio Value: ${self.current_session.portfolio_value:,.2f}",
            f"Positions: {self.current_session.positions_count}",
            f"Iterations Used: {self.current_session.iterations_used}",
            f"Consensus Reached: {'Yes' if self.current_session.consensus_reached else 'No'}",
            f"Approval Rate: {self.current_session.approval_rate:.1%}",
            "",
            "AGENT VOTES:",
            "-" * 40,
        ]
        
        for agent, vote in self.current_session.agent_votes.items():
            symbol = "✅" if vote.lower() == "approve" else "❌"
            lines.append(f"  {symbol} {agent}: {vote}")
        
        if self.current_session.handoffs:
            lines.extend([
                "",
                "HANDOFFS:",
                "-" * 40,
            ])
            for h in self.current_session.handoffs:
                lines.append(f"  [{h.iteration}] {h.from_agent} -> {h.to_agent}: {h.reason}")
        
        if self.current_session.errors:
            lines.extend([
                "",
                "ERRORS:",
                "-" * 40,
            ])
            for err in self.current_session.errors:
                lines.append(f"  ❌ {err}")
        
        return "\n".join(lines)
    
    def _session_to_csv(self) -> str:
        """Convert session metrics to CSV format"""
        if not self.current_session:
            return ""
        
        headers = ["Metric", "Value"]
        rows = [
            ["Session ID", self.current_session.session_id],
            ["Strategy", self.current_session.strategy_name],
            ["Portfolio Value", f"${self.current_session.portfolio_value:,.2f}"],
            ["Positions", str(self.current_session.positions_count)],
            ["Iterations", str(self.current_session.iterations_used)],
            ["Consensus", "Yes" if self.current_session.consensus_reached else "No"],
            ["Approval Rate", f"{self.current_session.approval_rate:.1%}"],
            ["Handoffs", str(len(self.current_session.handoffs))],
            ["Errors", str(len(self.current_session.errors))],
        ]
        
        lines = [",".join(headers)]
        for row in rows:
            lines.append(",".join(row))
        
        return "\n".join(lines)


# Global logger instance
swarm_logger = SwarmLogger()


def get_logger() -> SwarmLogger:
    """Get the global swarm logger instance"""
    return swarm_logger


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup basic logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("SwarmAgent")
