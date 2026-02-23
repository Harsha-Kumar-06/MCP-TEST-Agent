"""
Configuration management for Portfolio Swarm AI agents
Handles API keys, model settings, retry logic, and cost tracking
"""
import os
from typing import Optional
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiConfig:
    """Configuration for Google Gemini API integration"""
    
    # API Configuration
    API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # Current stable model (Feb 2026)
    TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))
    MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
    
    # Retry Configuration
    MAX_RETRIES: int = 2  # Reduced from 3 to speed up failure detection
    RETRY_DELAY: float = 1.0  # Reduced from 2.0 seconds
    TIMEOUT: int = 30  # seconds
    
    # Cost Tracking (approximate pricing as of 2024)
    # Gemini 1.5 Flash pricing
    COST_PER_1K_INPUT_TOKENS: float = 0.000075  # $0.075 per 1M tokens
    COST_PER_1K_OUTPUT_TOKENS: float = 0.0003   # $0.30 per 1M tokens
    ENABLE_COST_TRACKING: bool = os.getenv("ENABLE_COST_TRACKING", "true").lower() == "true"
    
    # Debug Settings
    ENABLE_DEBUG_LOGGING: bool = os.getenv("ENABLE_DEBUG_LOGGING", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that API key is configured"""
        if not cls.API_KEY or cls.API_KEY == "your_api_key_here":
            logger.error("❌ GEMINI_API_KEY not configured. Please set it in .env file")
            logger.error("   Get your API key from: https://makersuite.google.com/app/apikey")
            return False
        return True
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get API key with validation"""
        if not cls.validate():
            raise ValueError("Gemini API key not configured. Please set GEMINI_API_KEY in .env file")
        return cls.API_KEY


class CostTracker:
    """Track API usage costs across all agent calls"""
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        self.agent_costs = {}  # Track costs per agent type
    
    def add_usage(self, agent_type: str, input_tokens: int, output_tokens: int):
        """Record token usage for a specific agent"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1
        
        if agent_type not in self.agent_costs:
            self.agent_costs[agent_type] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "requests": 0
            }
        
        self.agent_costs[agent_type]["input_tokens"] += input_tokens
        self.agent_costs[agent_type]["output_tokens"] += output_tokens
        self.agent_costs[agent_type]["requests"] += 1
    
    def get_total_cost(self) -> float:
        """Calculate total cost in USD"""
        input_cost = (self.total_input_tokens / 1000) * GeminiConfig.COST_PER_1K_INPUT_TOKENS
        output_cost = (self.total_output_tokens / 1000) * GeminiConfig.COST_PER_1K_OUTPUT_TOKENS
        return input_cost + output_cost
    
    def get_agent_cost(self, agent_type: str) -> float:
        """Calculate cost for specific agent"""
        if agent_type not in self.agent_costs:
            return 0.0
        
        data = self.agent_costs[agent_type]
        input_cost = (data["input_tokens"] / 1000) * GeminiConfig.COST_PER_1K_INPUT_TOKENS
        output_cost = (data["output_tokens"] / 1000) * GeminiConfig.COST_PER_1K_OUTPUT_TOKENS
        return input_cost + output_cost
    
    def get_summary(self) -> dict:
        """Get detailed cost summary"""
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.get_total_cost(), 6),
            "agent_breakdown": {
                agent: {
                    "requests": data["requests"],
                    "tokens": data["input_tokens"] + data["output_tokens"],
                    "cost_usd": round(self.get_agent_cost(agent), 6)
                }
                for agent, data in self.agent_costs.items()
            }
        }
    
    def print_summary(self):
        """Print formatted cost summary"""
        summary = self.get_summary()
        print("\n" + "="*60)
        print("📊 AI API USAGE SUMMARY")
        print("="*60)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Tokens: {summary['total_tokens']:,} ({summary['total_input_tokens']:,} in + {summary['total_output_tokens']:,} out)")
        print(f"Total Cost: ${summary['total_cost_usd']:.6f}")
        print("\n" + "-"*60)
        print("Per-Agent Breakdown:")
        print("-"*60)
        for agent, data in summary['agent_breakdown'].items():
            print(f"  {agent:20s} | {data['requests']:2d} calls | {data['tokens']:6,} tokens | ${data['cost_usd']:.6f}")
        print("="*60 + "\n")


# Global cost tracker instance
cost_tracker = CostTracker()
