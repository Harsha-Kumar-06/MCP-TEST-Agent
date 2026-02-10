"""
Financial Portfolio Optimization using Swarm Pattern
Multi-agent collaborative system for portfolio rebalancing
"""

__version__ = "1.0.0"

# Core models
from .models import Portfolio, Position, AgentAnalysis, AgentProposal, AgentVote, Trade, TradePlan

# Agents
from .agents import (
    MarketAnalysisAgent,
    RiskAssessmentAgent,
    TaxStrategyAgent,
    ESGComplianceAgent,
    AlgorithmicTradingAgent
)

# Communication
from .communication import CommunicationBus, DebateFormatter

# Orchestrator
from .orchestrator import SwarmOrchestrator

# Parsers
from .input_parser import PortfolioParser
from .text_parser import GeminiEnhancedParser

# Configuration
from .config import GeminiConfig, cost_tracker

# Strategies
from .strategies import (
    OptimizationStrategy,
    StrategyType,
    get_strategy,
    create_custom_strategy,
    list_available_strategies,
    strategy_to_prompt,
    STRATEGY_TEMPLATES
)

# Logging
from .logger import SwarmLogger, get_logger, setup_logging

# Memory
from .memory import ConversationMemory, QUERY_TEMPLATES, get_query_template, list_query_templates

__all__ = [
    # Version
    "__version__",
    
    # Models
    "Portfolio",
    "Position",
    "AgentAnalysis",
    "AgentProposal",
    "AgentVote",
    "Trade",
    "TradePlan",
    
    # Agents
    "MarketAnalysisAgent",
    "RiskAssessmentAgent",
    "TaxStrategyAgent",
    "ESGComplianceAgent",
    "AlgorithmicTradingAgent",
    
    # Communication
    "CommunicationBus",
    "DebateFormatter",
    
    # Orchestrator
    "SwarmOrchestrator",
    
    # Parsers
    "PortfolioParser",
    "GeminiEnhancedParser",
    
    # Config
    "GeminiConfig",
    "cost_tracker",
    
    # Strategies
    "OptimizationStrategy",
    "StrategyType",
    "get_strategy",
    "create_custom_strategy",
    "list_available_strategies",
    "strategy_to_prompt",
    "STRATEGY_TEMPLATES",
    
    # Logging
    "SwarmLogger",
    "get_logger",
    "setup_logging",
    
    # Memory
    "ConversationMemory",
    "QUERY_TEMPLATES",
    "get_query_template",
    "list_query_templates",
]
