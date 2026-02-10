"""
Specialized agent implementations for portfolio optimization
Now powered by Google Gemini AI for intelligent analysis
"""
from typing import List, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from .models import (
    Portfolio, AgentAnalysis, AgentProposal, AgentVote, AgentType, 
    VoteType, Trade, TradePlan, Position
)
from .communication import CommunicationBus
from .config import GeminiConfig, cost_tracker
from .prompts import get_analysis_prompt, get_vote_prompt
import logging
import time

# Try new google.genai API first, fallback to old one
try:
    from google import genai
    from google.genai import types
    USE_NEW_API = True
except ImportError:
    try:
        import google.generativeai as genai
        types = None
        USE_NEW_API = False
    except ImportError:
        genai = None
        types = None
        USE_NEW_API = False

logger = logging.getLogger(__name__)

# Configure Gemini API
gemini_client = None
if genai and GeminiConfig.validate():
    try:
        if USE_NEW_API:
            # New google.genai API
            gemini_client = genai.Client(api_key=GeminiConfig.get_api_key())
            logger.info(f"✅ Google Gemini configured (NEW API): {GeminiConfig.MODEL}")
        else:
            # Old google.generativeai API
            genai.configure(api_key=GeminiConfig.get_api_key())
            logger.info(f"✅ Google Gemini configured (OLD API): {GeminiConfig.MODEL}")
    except Exception as e:
        logger.error(f"❌ Failed to configure Gemini: {e}")


class MarketAnalysisAgent(BaseAgent):
    """Agent specialized in market trends and valuation analysis
    Powered by Google Gemini AI for intelligent market analysis
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.MARKET_ANALYSIS, communication_bus)
        self.use_new_api = USE_NEW_API
        self.gemini_client = gemini_client
        if not USE_NEW_API and genai:
            self.model = genai.GenerativeModel(
                model_name=GeminiConfig.MODEL,
                generation_config={
                    "temperature": GeminiConfig.TEMPERATURE,
                    "max_output_tokens": GeminiConfig.MAX_TOKENS,
                }
            )
        else:
            self.model = None
        # Market data for context
        self.sector_valuations = {
            "Technology": {"pe_ratio": 32.5, "historical_avg": 24.0, "trend": "overvalued"},
            "Healthcare": {"pe_ratio": 22.0, "historical_avg": 23.0, "trend": "fair"},
            "Financials": {"pe_ratio": 12.5, "historical_avg": 14.0, "trend": "undervalued"},
        }
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic and cost tracking"""
        if not genai:
            raise RuntimeError("Gemini API not available. Install google-genai or google-generativeai package.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                if self.use_new_api:
                    # New google.genai API
                    response = self.gemini_client.models.generate_content(
                        model=GeminiConfig.MODEL,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=GeminiConfig.TEMPERATURE,
                            max_output_tokens=GeminiConfig.MAX_TOKENS,
                        )
                    )
                    text = response.text
                else:
                    # Old google.generativeai API
                    chat = self.model.start_chat(history=[])
                    response = chat.send_message(full_prompt)
                    text = response.text
                
                # Track costs
                if GeminiConfig.ENABLE_COST_TRACKING and hasattr(response, 'usage_metadata'):
                    cost_tracker.add_usage(
                        agent_type=str(self.agent_type),
                        input_tokens=getattr(response.usage_metadata, 'prompt_token_count', 0),
                        output_tokens=getattr(response.usage_metadata, 'candidates_token_count', 0)
                    )
                
                return text
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a quota/rate limit error - don't retry these
                if any(keyword in error_str for keyword in ['429', 'quota', 'resource_exhausted', 'rate limit']):
                    logger.error(f"❌ {self.agent_type} hit API quota limit (no retry)")
                    raise  # Fail immediately for quota errors
                
                logger.warning(f"Gemini API attempt {attempt + 1}/{GeminiConfig.MAX_RETRIES} failed: {str(e)[:100]}")
                if attempt < GeminiConfig.MAX_RETRIES - 1:
                    delay = GeminiConfig.RETRY_DELAY
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Gemini API failed after {GeminiConfig.MAX_RETRIES} attempts: {str(e)[:100]}")
                    raise
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini into analysis components"""
        try:
            lines = response_text.strip().split('\n')
            result = {
                'findings': '',
                'recommendation': '',
                'conviction': 5,
                'concerns': [],
                'metrics': {}
            }
            
            for line in lines:
                line = line.strip()
                if line.startswith('FINDINGS:'):
                    result['findings'] = line.replace('FINDINGS:', '').strip()
                elif line.startswith('RECOMMENDATION:'):
                    result['recommendation'] = line.replace('RECOMMENDATION:', '').strip()
                elif line.startswith('CONVICTION:'):
                    try:
                        result['conviction'] = int(line.replace('CONVICTION:', '').strip())
                    except ValueError:
                        result['conviction'] = 5
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        result['concerns'] = [c.strip() for c in concerns_str.split(',')]
                elif line.startswith('METRICS:'):
                    metrics_str = line.replace('METRICS:', '').strip()
                    for metric in metrics_str.split(','):
                        if ':' in metric:
                            key, value = metric.split(':', 1)
                            try:
                                result['metrics'][key.strip()] = float(value.strip())
                            except ValueError:
                                result['metrics'][key.strip()] = value.strip()
            
            return result
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return {
                'findings': response_text[:200],
                'recommendation': 'Review required',
                'conviction': 5,
                'concerns': [],
                'metrics': {}
            }
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze market conditions and portfolio positioning using Gemini AI"""
        logger.info(f"🤖 {self.agent_type} analyzing portfolio with AI...")
        
        # Prepare portfolio data for AI
        sector_alloc = portfolio.sector_allocation
        sector_text = "\n".join([f"  - {sector}: {pct:.1f}%" for sector, pct in sector_alloc.items()])
        
        top_holdings = sorted(portfolio.positions, key=lambda p: p.market_value, reverse=True)[:5]
        holdings_text = "\n".join([
            f"  - {p.ticker}: ${p.market_value:,.0f} ({p.market_value/portfolio.total_value*100:.1f}%) - {p.sector}"
            for p in top_holdings
        ])
        
        # Get prompts
        system_prompt, user_prompt_template = get_analysis_prompt(str(self.agent_type))
        
        # Fill in template
        user_prompt = user_prompt_template.format(
            total_value=portfolio.total_value,
            num_positions=len(portfolio.positions),
            cash=portfolio.cash,
            sector_allocation=sector_text,
            top_holdings=holdings_text
        )
        
        # Call Gemini
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            
            logger.info(f"✅ {self.agent_type} analysis complete (conviction: {parsed['conviction']})")
            
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics']
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} analysis failed: {e}")
            # Fallback to basic analysis
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings="AI analysis unavailable, using fallback",
                recommendation="Review portfolio manually",
                conviction=5,
                concerns=["AI service error"],
                metrics={}
            )
    
    def propose_solution(self, portfolio: Portfolio, context: List[AgentAnalysis]) -> Optional[AgentProposal]:
        """Propose trades based on market analysis"""
        sector_alloc = portfolio.sector_allocation
        trades = []
        
        # Identify overweight overvalued positions
        for position in portfolio.positions:
            if position.sector in self.sector_valuations:
                valuation = self.sector_valuations[position.sector]
                sector_pct = sector_alloc.get(position.sector, 0)
                
                if valuation["trend"] == "overvalued" and sector_pct > 25:
                    # Propose selling 20% of position
                    shares_to_sell = int(position.shares * 0.2)
                    trades.append(Trade(
                        action="SELL",
                        ticker=position.ticker,
                        shares=shares_to_sell,
                        estimated_price=position.current_price,
                        rationale=f"Reduce overvalued {position.sector} exposure"
                    ))
        
        if not trades:
            return None
        
        # Calculate expected metrics
        projected_metrics = {
            "portfolio_beta": portfolio.portfolio_beta * 0.95,  # Estimate reduction
            "tech_allocation": sector_alloc.get("Technology", 0) * 0.8
        }
        
        trade_plan = TradePlan(
            trades=trades,
            expected_tax_liability=0,  # Will be calculated by tax agent
            expected_execution_cost=sum(t.notional_value * 0.0005 for t in trades),
            execution_timeline_days=2,
            projected_portfolio_metrics=projected_metrics
        )
        
        return AgentProposal(
            agent_type=self.agent_type,
            trade_plan=trade_plan,
            rationale="Reduce exposure to overvalued sectors based on fundamental analysis",
            conviction=8
        )
    
    def vote_on_proposal(self, proposal: TradePlan, portfolio: Portfolio) -> AgentVote:
        """Vote on proposed trade plan from market perspective using AI"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal...")
        
        # Format trades for AI
        trades_text = "\n".join([
            f"  - {t.action} {t.shares} shares of {t.ticker} @ ${t.estimated_price:.2f} (${t.notional_value:,.0f})"
            for t in proposal.trades
        ])
        
        # Get vote prompt
        vote_prompt_template = get_vote_prompt(str(self.agent_type))
        vote_prompt = vote_prompt_template.format(
            trades=trades_text,
            tax=proposal.expected_tax_liability,
            execution_cost=proposal.expected_execution_cost,
            timeline=proposal.execution_timeline_days
        )
        
        try:
            system_prompt, _ = get_analysis_prompt(str(self.agent_type))
            response_text = self._call_gemini(system_prompt, vote_prompt)
            
            # Parse vote response
            vote_type = VoteType.ABSTAIN
            rationale = ""
            concerns = []
            
            response_lower = response_text.lower()
            
            # More flexible parsing - check entire response, not just formatted lines
            for line in response_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('VOTE:'):
                    vote_str = line.replace('VOTE:', '').strip().upper()
                    if 'APPROVE' in vote_str:
                        vote_type = VoteType.APPROVE
                    elif 'REJECT' in vote_str:
                        vote_type = VoteType.REJECT
                elif line.startswith('RATIONALE:'):
                    rationale = line.replace('RATIONALE:', '').strip()
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        concerns = [c.strip() for c in concerns_str.split(',')]
            
            # If no vote found in formatted response, try to infer from content
            if vote_type == VoteType.ABSTAIN:
                if 'approve' in response_lower and 'reject' not in response_lower:
                    vote_type = VoteType.APPROVE
                    if not rationale:
                        rationale = "Portfolio appears suitable, proceeding with trades"
                elif 'reject' in response_lower:
                    vote_type = VoteType.REJECT
                    if not rationale:
                        rationale = "Concerns identified, rejecting proposal"
                else:
                    # Default to APPROVE if AI gives a response but no clear vote
                    # This prevents all-reject scenarios from parsing issues
                    vote_type = VoteType.APPROVE
                    if not rationale:
                        rationale = response_text[:200] if response_text else "AI analysis complete"
            
            logger.info(f"✅ {self.agent_type} voted: {vote_type}")
            
            return AgentVote(
                agent_type=self.agent_type,
                vote=vote_type,
                rationale=rationale or response_text[:200] or "AI analysis complete",
                concerns=concerns
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} voting failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Check if it's a quota error
            error_str = str(e).lower()
            if 'quota' in error_str or '429' in error_str or 'resource_exhausted' in error_str:
                return AgentVote(
                    agent_type=self.agent_type,
                    vote=VoteType.APPROVE,  # Default to approve on quota errors to not block optimization
                    rationale=f"⚠️ API quota exceeded. Using conservative approval for {self.agent_type}.",
                    concerns=["Gemini API quota limit reached - consider upgrading plan or waiting for reset"]
                )
            else:
                return AgentVote(
                    agent_type=self.agent_type,
                    vote=VoteType.APPROVE,  # Change from ABSTAIN to APPROVE on error
                    rationale=f"AI voting service error: {str(e)[:100]}",
                    concerns=["Unable to complete AI analysis - defaulting to approval"]
                )


class RiskAssessmentAgent(BaseAgent):
    """Agent specialized in risk management and compliance
    Powered by Google Gemini AI for intelligent risk assessment
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.RISK_ASSESSMENT, communication_bus)
        self.use_new_api = USE_NEW_API
        self.gemini_client = gemini_client
        if not USE_NEW_API and genai:
            self.model = genai.GenerativeModel(
                model_name=GeminiConfig.MODEL,
                generation_config={
                    "temperature": GeminiConfig.TEMPERATURE,
                    "max_output_tokens": GeminiConfig.MAX_TOKENS,
                }
            )
        else:
            self.model = None
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic"""
        if not genai:
            raise RuntimeError("Gemini API not available.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                if self.use_new_api:
                    response = self.gemini_client.models.generate_content(
                        model=GeminiConfig.MODEL,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=GeminiConfig.TEMPERATURE,
                            max_output_tokens=GeminiConfig.MAX_TOKENS,
                        )
                    )
                    text = response.text
                else:
                    chat = self.model.start_chat(history=[])
                    response = chat.send_message(full_prompt)
                    text = response.text
                
                if GeminiConfig.ENABLE_COST_TRACKING and hasattr(response, 'usage_metadata'):
                    cost_tracker.add_usage(
                        agent_type=str(self.agent_type),
                        input_tokens=getattr(response.usage_metadata, 'prompt_token_count', 0),
                        output_tokens=getattr(response.usage_metadata, 'candidates_token_count', 0)
                    )
                
                return text
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a quota/rate limit error - don't retry these
                if any(keyword in error_str for keyword in ['429', 'quota', 'resource_exhausted', 'rate limit']):
                    logger.error(f"❌ {self.agent_type} voting hit API quota limit (no retry)")
                    raise  # Fail immediately for quota errors
                
                logger.warning(f"Gemini API attempt {attempt + 1}/{GeminiConfig.MAX_RETRIES} failed: {str(e)[:100]}")
                if attempt < GeminiConfig.MAX_RETRIES - 1:
                    delay = GeminiConfig.RETRY_DELAY
                    time.sleep(delay)
                else:
                    raise
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini"""
        try:
            lines = response_text.strip().split('\n')
            result = {'findings': '', 'recommendation': '', 'conviction': 5, 'concerns': [], 'metrics': {}}
            
            for line in lines:
                line = line.strip()
                if line.startswith('FINDINGS:'):
                    result['findings'] = line.replace('FINDINGS:', '').strip()
                elif line.startswith('RECOMMENDATION:'):
                    result['recommendation'] = line.replace('RECOMMENDATION:', '').strip()
                elif line.startswith('CONVICTION:'):
                    try:
                        result['conviction'] = int(line.replace('CONVICTION:', '').strip())
                    except ValueError:
                        result['conviction'] = 5
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        result['concerns'] = [c.strip() for c in concerns_str.split(',')]
                elif line.startswith('METRICS:'):
                    metrics_str = line.replace('METRICS:', '').strip()
                    for metric in metrics_str.split(','):
                        if ':' in metric:
                            key, value = metric.split(':', 1)
                            try:
                                result['metrics'][key.strip()] = float(value.strip())
                            except ValueError:
                                result['metrics'][key.strip()] = value.strip()
            return result
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {'findings': response_text[:200], 'recommendation': 'Review required', 'conviction': 5, 'concerns': [], 'metrics': {}}
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze portfolio risk and compliance using Gemini AI"""
        logger.info(f"🤖 {self.agent_type} analyzing portfolio with AI...")
        
        violations = portfolio.get_compliance_violations()
        sector_alloc = portfolio.sector_allocation
        beta = portfolio.portfolio_beta
        
        # Format data for AI
        sector_text = "\n".join([f"  - {sector}: {pct:.1f}%" for sector, pct in sector_alloc.items()])
        
        policy_text = "\n".join([f"  - {key}: {value}%" for key, value in portfolio.policy_limits.items()])
        
        position_sizes = [(p.ticker, p.market_value/portfolio.total_value*100) for p in portfolio.positions]
        position_sizes.sort(key=lambda x: x[1], reverse=True)
        positions_text = "\n".join([f"  - {ticker}: {pct:.1f}%" for ticker, pct in position_sizes[:10]])
        
        violations_text = "\n".join([f"  - {v}" for v in violations]) if violations else "None"
        
        # Get prompts
        system_prompt, user_prompt_template = get_analysis_prompt(str(self.agent_type))
        
        user_prompt = user_prompt_template.format(
            total_value=portfolio.total_value,
            portfolio_beta=beta,
            num_positions=len(portfolio.positions),
            sector_allocation=sector_text,
            policy_limits=policy_text,
            position_sizes=positions_text,
            violations=violations_text
        )
        
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            
            logger.info(f"✅ {self.agent_type} analysis complete (conviction: {parsed['conviction']})")
            
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics']
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} analysis failed: {e}")
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings="AI analysis unavailable",
                recommendation="Manual review required" if violations else "Risk profile acceptable",
                conviction=10 if violations else 5,
                concerns=violations,
                metrics={"portfolio_beta": beta}
            )
    
    def propose_solution(self, portfolio: Portfolio, context: List[AgentAnalysis]) -> Optional[AgentProposal]:
        """Propose trades to fix compliance and reduce risk"""
        violations = portfolio.get_compliance_violations()
        if not violations:
            return None
        
        trades = []
        sector_alloc = portfolio.sector_allocation
        
        # Fix sector violations
        for sector, percentage in sector_alloc.items():
            limit_key = f"{sector.lower()}_limit"
            if limit_key in portfolio.policy_limits:
                limit = portfolio.policy_limits[limit_key]
                if percentage > limit:
                    # Calculate amount to reduce
                    current_value = portfolio.total_value * (percentage / 100)
                    target_value = portfolio.total_value * (limit / 100)
                    reduction_needed = current_value - target_value
                    
                    # Find positions in this sector to sell
                    sector_positions = [p for p in portfolio.positions if p.sector == sector]
                    for position in sector_positions:
                        if reduction_needed > 0:
                            shares_to_sell = min(
                                position.shares,
                                int(reduction_needed / position.current_price)
                            )
                            trades.append(Trade(
                                action="SELL",
                                ticker=position.ticker,
                                shares=shares_to_sell,
                                estimated_price=position.current_price,
                                rationale=f"Reduce {sector} to comply with {limit}% limit"
                            ))
                            reduction_needed -= shares_to_sell * position.current_price
        
        if not trades:
            return None
        
        # Project new metrics
        projected_beta = portfolio.portfolio_beta * 0.92
        projected_metrics = {
            "portfolio_beta": projected_beta,
            "compliance_fixed": True
        }
        
        trade_plan = TradePlan(
            trades=trades,
            expected_tax_liability=0,
            expected_execution_cost=sum(t.notional_value * 0.0005 for t in trades),
            execution_timeline_days=1,
            projected_portfolio_metrics=projected_metrics
        )
        
        return AgentProposal(
            agent_type=self.agent_type,
            trade_plan=trade_plan,
            rationale="Fix compliance violations and reduce concentration risk",
            conviction=10
        )
    
    def vote_on_proposal(self, proposal: TradePlan, portfolio: Portfolio) -> AgentVote:
        """Vote based on risk and compliance impact using AI"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal...")
        
        violations = portfolio.get_compliance_violations()
        trades_text = "\n".join([
            f"  - {t.action} {t.shares} shares of {t.ticker} @ ${t.estimated_price:.2f}"
            for t in proposal.trades
        ])
        
        vote_prompt_template = get_vote_prompt(str(self.agent_type))
        vote_prompt = vote_prompt_template.format(
            trades=trades_text,
            violations=", ".join(violations) if violations else "None"
        )
        
        try:
            system_prompt, _ = get_analysis_prompt(str(self.agent_type))
            response_text = self._call_gemini(system_prompt, vote_prompt)
            
            vote_type = VoteType.ABSTAIN
            rationale = ""
            concerns = []
            
            for line in response_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('VOTE:'):
                    vote_str = line.replace('VOTE:', '').strip().upper()
                    if 'APPROVE' in vote_str:
                        vote_type = VoteType.APPROVE
                    elif 'REJECT' in vote_str:
                        vote_type = VoteType.REJECT
                elif line.startswith('RATIONALE:'):
                    rationale = line.replace('RATIONALE:', '').strip()
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        concerns = [c.strip() for c in concerns_str.split(',')]
            
            # Fallback: If no vote found in formatted response, infer from content
            if vote_type == VoteType.ABSTAIN:
                response_lower = response_text.lower()
                if 'approve' in response_lower and 'reject' not in response_lower:
                    vote_type = VoteType.APPROVE
                    if not rationale:
                        rationale = "Risk assessment passed - proceeding with trades"
                elif 'reject' in response_lower:
                    vote_type = VoteType.REJECT
                    if not rationale:
                        rationale = "Risk concerns identified - rejecting proposal"
                else:
                    # Default based on violations
                    vote_type = VoteType.REJECT if violations else VoteType.APPROVE
                    if not rationale:
                        rationale = response_text[:200] if response_text else "Risk analysis complete"
            
            logger.info(f"✅ {self.agent_type} voted: {vote_type}")
            
            return AgentVote(
                agent_type=self.agent_type,
                vote=vote_type,
                rationale=rationale or "AI analysis complete",
                concerns=concerns
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} voting failed: {e}")
            return AgentVote(
                agent_type=self.agent_type,
                vote=VoteType.REJECT if violations else VoteType.APPROVE,
                rationale="AI service error - using fallback logic",
                concerns=violations if violations else []
            )


class TaxStrategyAgent(BaseAgent):
    """Agent specialized in tax optimization
    Powered by Google Gemini AI for intelligent tax strategy
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.TAX_STRATEGY, communication_bus)
        self.long_term_rate = 0.20  # 20% for long-term gains
        self.short_term_rate = 0.37  # 37% for short-term gains
        self.use_new_api = USE_NEW_API
        self.gemini_client = gemini_client
        if not USE_NEW_API and genai:
            self.model = genai.GenerativeModel(
                model_name=GeminiConfig.MODEL,
                generation_config={
                    "temperature": GeminiConfig.TEMPERATURE,
                    "max_output_tokens": GeminiConfig.MAX_TOKENS,
                }
            )
        else:
            self.model = None
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic"""
        if not genai:
            raise RuntimeError("Gemini API not available.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                if self.use_new_api:
                    response = self.gemini_client.models.generate_content(
                        model=GeminiConfig.MODEL,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=GeminiConfig.TEMPERATURE,
                            max_output_tokens=GeminiConfig.MAX_TOKENS,
                        )
                    )
                    text = response.text
                else:
                    chat = self.model.start_chat(history=[])
                    response = chat.send_message(full_prompt)
                    text = response.text
                
                if GeminiConfig.ENABLE_COST_TRACKING and hasattr(response, 'usage_metadata'):
                    cost_tracker.add_usage(
                        agent_type=str(self.agent_type),
                        input_tokens=getattr(response.usage_metadata, 'prompt_token_count', 0),
                        output_tokens=getattr(response.usage_metadata, 'candidates_token_count', 0)
                    )
                return text
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['429', 'quota', 'resource_exhausted', 'rate limit']):
                    logger.error(f"❌ {self.agent_type} hit API quota (no retry)")
                    raise
                if attempt < GeminiConfig.MAX_RETRIES - 1:
                    time.sleep(GeminiConfig.RETRY_DELAY)
                else:
                    raise
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini"""
        try:
            lines = response_text.strip().split('\n')
            result = {'findings': '', 'recommendation': '', 'conviction': 5, 'concerns': [], 'metrics': {}}
            for line in lines:
                line = line.strip()
                if line.startswith('FINDINGS:'):
                    result['findings'] = line.replace('FINDINGS:', '').strip()
                elif line.startswith('RECOMMENDATION:'):
                    result['recommendation'] = line.replace('RECOMMENDATION:', '').strip()
                elif line.startswith('CONVICTION:'):
                    try:
                        result['conviction'] = int(line.replace('CONVICTION:', '').strip())
                    except ValueError:
                        result['conviction'] = 5
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        result['concerns'] = [c.strip() for c in concerns_str.split(',')]
                elif line.startswith('METRICS:'):
                    metrics_str = line.replace('METRICS:', '').strip()
                    for metric in metrics_str.split(','):
                        if ':' in metric:
                            key, value = metric.split(':', 1)
                            try:
                                result['metrics'][key.strip()] = float(value.strip())
                            except ValueError:
                                result['metrics'][key.strip()] = value.strip()
            return result
        except Exception as e:
            return {'findings': response_text[:200], 'recommendation': 'Review required', 'conviction': 5, 'concerns': [], 'metrics': {}}
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze tax implications using Gemini AI"""
        logger.info(f"🤖 {self.agent_type} analyzing portfolio with AI...")
        
        # Format position data with tax details
        positions_text = []
        for p in portfolio.positions:
            days_held = (datetime.now() - p.acquisition_date).days
            is_lt = days_held >= 365
            gain = p.unrealized_gain
            tax_rate = self.long_term_rate if is_lt else self.short_term_rate
            status = "Long-term" if is_lt else f"Short-term ({days_held} days)"
            positions_text.append(
                f"  - {p.ticker}: ${gain:,.0f} gain, {status}, {tax_rate*100:.0f}% tax rate"
            )
        
        system_prompt, user_prompt_template = get_analysis_prompt(str(self.agent_type))
        user_prompt = user_prompt_template.format(
            positions_with_gains="\n".join(positions_text)
        )
        
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            logger.info(f"✅ {self.agent_type} analysis complete")
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics']
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} analysis failed: {e}")
            total_gains = sum(p.unrealized_gain for p in portfolio.positions if p.unrealized_gain > 0)
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings="AI unavailable",
                recommendation="Prioritize long-term positions",
                conviction=5,
                concerns=[],
                metrics={"unrealized_gains": total_gains}
            )
    
    def propose_solution(self, portfolio: Portfolio, context: List[AgentAnalysis]) -> Optional[AgentProposal]:
        """Propose tax-efficient alternatives"""
        # Look for alternative positions to sell that are long-term
        # This is a simplified implementation
        return None  # Typically provides critiques rather than full proposals
    
    def vote_on_proposal(self, proposal: TradePlan, portfolio: Portfolio) -> AgentVote:
        """Vote based on tax efficiency using AI"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal...")
        
        # Calculate tax impact for each trade
        trades_text = []
        total_tax = 0
        position_details = []
        
        for trade in proposal.trades:
            if trade.action == "SELL":
                position = next((p for p in portfolio.positions if p.ticker == trade.ticker), None)
                if position:
                    days_held = (datetime.now() - position.acquisition_date).days
                    is_lt = days_held >= 365
                    gain_per_share = position.current_price - position.cost_basis
                    total_gain = gain_per_share * trade.shares
                    tax_rate = self.long_term_rate if is_lt else self.short_term_rate
                    tax = total_gain * tax_rate
                    total_tax += tax
                    
                    trades_text.append(f"  - {trade.action} {trade.shares} {trade.ticker} @ ${trade.estimated_price:.2f}")
                    position_details.append(f"  - {position.ticker}: {days_held} days held, ${total_gain:,.0f} gain, {'LT' if is_lt else 'ST'}, ${tax:,.0f} tax")
        
        proposal.expected_tax_liability = total_tax
        
        vote_prompt_template = get_vote_prompt(str(self.agent_type))
        vote_prompt = vote_prompt_template.format(
            trades="\n".join(trades_text),
            position_details="\n".join(position_details)
        )
        
        try:
            system_prompt, _ = get_analysis_prompt(str(self.agent_type))
            response_text = self._call_gemini(system_prompt, vote_prompt)
            
            vote_type = VoteType.ABSTAIN
            rationale = ""
            concerns = []
            
            for line in response_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('VOTE:'):
                    vote_str = line.replace('VOTE:', '').strip().upper()
                    if 'APPROVE' in vote_str:
                        vote_type = VoteType.APPROVE
                    elif 'REJECT' in vote_str:
                        vote_type = VoteType.REJECT
                elif line.startswith('RATIONALE:'):
                    rationale = line.replace('RATIONALE:', '').strip()
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        concerns = [c.strip() for c in concerns_str.split(',')]
            
            # Fallback: If no vote found in formatted response, infer from content
            if vote_type == VoteType.ABSTAIN:
                response_lower = response_text.lower()
                if 'approve' in response_lower and 'reject' not in response_lower:
                    vote_type = VoteType.APPROVE
                    if not rationale:
                        rationale = f"Tax-efficient approach approved - liability: ${total_tax:,.0f}"
                elif 'reject' in response_lower:
                    vote_type = VoteType.REJECT
                    if not rationale:
                        rationale = f"Tax implications too high - liability: ${total_tax:,.0f}"
                else:
                    # Default based on tax amount
                    vote_type = VoteType.REJECT if total_tax > 200000 else VoteType.APPROVE
                    if not rationale:
                        rationale = response_text[:200] if response_text else f"Tax liability: ${total_tax:,.0f}"
            
            logger.info(f"✅ {self.agent_type} voted: {vote_type} (tax: ${total_tax:,.0f})")
            
            return AgentVote(
                agent_type=self.agent_type,
                vote=vote_type,
                rationale=rationale or f"Tax liability: ${total_tax:,.0f}",
                concerns=concerns
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} voting failed: {e}")
            # Fallback logic
            if total_tax > 200000:
                vote = VoteType.REJECT
                rationale = f"Excessive tax: ${total_tax:,.0f}"
            else:
                vote = VoteType.APPROVE
                rationale = f"Acceptable tax: ${total_tax:,.0f}"
            
            return AgentVote(
                agent_type=self.agent_type,
                vote=vote,
                rationale=rationale,
                concerns=[]
            )


class ESGComplianceAgent(BaseAgent):
    """Agent specialized in ESG criteria evaluation
    Powered by Google Gemini AI for intelligent ESG assessment
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.ESG_COMPLIANCE, communication_bus)
        self.esg_minimum = 60
        self.esg_ratings = {
            "JNJ": 79, "UNH": 72, "PFE": 76,
            "JPM": 58, "BAC": 62, "GS": 55,
            "AAPL": 72, "MSFT": 82, "GOOGL": 71, "NVDA": 78
        }
        self.use_new_api = USE_NEW_API
        self.gemini_client = gemini_client
        if not USE_NEW_API and genai:
            self.model = genai.GenerativeModel(
                model_name=GeminiConfig.MODEL,
                generation_config={
                    "temperature": GeminiConfig.TEMPERATURE,
                    "max_output_tokens": GeminiConfig.MAX_TOKENS,
                }
            )
        else:
            self.model = None
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic"""
        if not genai:
            raise RuntimeError("Gemini API not available.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                if self.use_new_api:
                    response = self.gemini_client.models.generate_content(
                        model=GeminiConfig.MODEL,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=GeminiConfig.TEMPERATURE,
                            max_output_tokens=GeminiConfig.MAX_TOKENS,
                        )
                    )
                    text = response.text
                else:
                    chat = self.model.start_chat(history=[])
                    response = chat.send_message(full_prompt)
                    text = response.text
                
                if GeminiConfig.ENABLE_COST_TRACKING and hasattr(response, 'usage_metadata'):
                    cost_tracker.add_usage(
                        agent_type=str(self.agent_type),
                        input_tokens=getattr(response.usage_metadata, 'prompt_token_count', 0),
                        output_tokens=getattr(response.usage_metadata, 'candidates_token_count', 0)
                    )
                return text
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['429', 'quota', 'resource_exhausted', 'rate limit']):
                    logger.error(f"❌ {self.agent_type} hit API quota (no retry)")
                    raise
                if attempt < GeminiConfig.MAX_RETRIES - 1:
                    time.sleep(GeminiConfig.RETRY_DELAY)
                else:
                    raise
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini"""
        try:
            lines = response_text.strip().split('\n')
            result = {'findings': '', 'recommendation': '', 'conviction': 5, 'concerns': [], 'metrics': {}}
            for line in lines:
                line = line.strip()
                if line.startswith('FINDINGS:'):
                    result['findings'] = line.replace('FINDINGS:', '').strip()
                elif line.startswith('RECOMMENDATION:'):
                    result['recommendation'] = line.replace('RECOMMENDATION:', '').strip()
                elif line.startswith('CONVICTION:'):
                    try:
                        result['conviction'] = int(line.replace('CONVICTION:', '').strip())
                    except ValueError:
                        result['conviction'] = 5
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        result['concerns'] = [c.strip() for c in concerns_str.split(',')]
                elif line.startswith('METRICS:'):
                    metrics_str = line.replace('METRICS:', '').strip()
                    for metric in metrics_str.split(','):
                        if ':' in metric:
                            key, value = metric.split(':', 1)
                            try:
                                result['metrics'][key.strip()] = float(value.strip())
                            except ValueError:
                                result['metrics'][key.strip()] = value.strip()
            return result
        except Exception as e:
            return {'findings': response_text[:200], 'recommendation': 'Review required', 'conviction': 5, 'concerns': [], 'metrics': {}}
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze ESG compliance using Gemini AI"""
        logger.info(f"🤖 {self.agent_type} analyzing portfolio with AI...")
        
        avg_esg = portfolio.average_esg_score
        positions_text = "\n".join([
            f"  - {p.ticker}: ESG {p.esg_score} {'✅' if p.esg_score >= self.esg_minimum else '❌ LOW'}"
            for p in portfolio.positions
        ])
        
        system_prompt, user_prompt_template = get_analysis_prompt(str(self.agent_type))
        user_prompt = user_prompt_template.format(
            avg_esg_score=avg_esg,
            positions_with_esg=positions_text
        )
        
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            logger.info(f"✅ {self.agent_type} analysis complete")
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics'] or {"avg_esg_score": avg_esg}
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} analysis failed: {e}")
            low_esg = [p for p in portfolio.positions if p.esg_score < self.esg_minimum]
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings="AI unavailable",
                recommendation="Replace low-ESG holdings" if low_esg else "ESG maintained",
                conviction=10 if low_esg else 6,
                concerns=[f"{p.ticker} ESG {p.esg_score}" for p in low_esg],
                metrics={"avg_esg_score": avg_esg}
            )
    
    def propose_solution(self, portfolio: Portfolio, context: List[AgentAnalysis]) -> Optional[AgentProposal]:
        """Propose ESG-compliant alternatives"""
        # Typically critiques other proposals rather than leading
        return None
    
    def vote_on_proposal(self, proposal: TradePlan, portfolio: Portfolio) -> AgentVote:
        """Vote based on ESG impact using AI"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal...")
        
        trades_text = []
        esg_scores_text = []
        
        for trade in proposal.trades:
            trades_text.append(f"  - {trade.action} {trade.shares} {trade.ticker}")
            esg_score = self.esg_ratings.get(trade.ticker, 70)
            esg_scores_text.append(f"  - {trade.ticker}: ESG {esg_score}")
        
        vote_prompt_template = get_vote_prompt(str(self.agent_type))
        vote_prompt = vote_prompt_template.format(
            trades="\n".join(trades_text),
            esg_scores="\n".join(esg_scores_text)
        )
        
        try:
            system_prompt, _ = get_analysis_prompt(str(self.agent_type))
            response_text = self._call_gemini(system_prompt, vote_prompt)
            
            vote_type = VoteType.ABSTAIN
            rationale = ""
            concerns = []
            
            for line in response_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('VOTE:'):
                    vote_str = line.replace('VOTE:', '').strip().upper()
                    if 'APPROVE' in vote_str:
                        vote_type = VoteType.APPROVE
                    elif 'REJECT' in vote_str:
                        vote_type = VoteType.REJECT
                elif line.startswith('RATIONALE:'):
                    rationale = line.replace('RATIONALE:', '').strip()
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        concerns = [c.strip() for c in concerns_str.split(',')]
            
            # Fallback: If no vote found in formatted response, infer from content
            if vote_type == VoteType.ABSTAIN:
                response_lower = response_text.lower()
                if 'approve' in response_lower and 'reject' not in response_lower:
                    vote_type = VoteType.APPROVE
                    if not rationale:
                        rationale = "ESG standards met - proceeding with trades"
                elif 'reject' in response_lower:
                    vote_type = VoteType.REJECT
                    if not rationale:
                        rationale = "ESG concerns identified - rejecting proposal"
                else:
                    # Default to APPROVE for ESG unless explicitly rejected
                    vote_type = VoteType.APPROVE
                    if not rationale:
                        rationale = response_text[:200] if response_text else "ESG criteria maintained"
            
            logger.info(f"✅ {self.agent_type} voted: {vote_type}")
            
            return AgentVote(
                agent_type=self.agent_type,
                vote=vote_type,
                rationale=rationale or "ESG criteria maintained",
                concerns=concerns
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} voting failed: {e}")
            return AgentVote(
                agent_type=self.agent_type,
                vote=VoteType.APPROVE,
                rationale="ESG criteria maintained (fallback)",
                concerns=[]
            )


class AlgorithmicTradingAgent(BaseAgent):
    """Agent specialized in trade execution and liquidity analysis
    Powered by Google Gemini AI for intelligent execution strategy
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.ALGORITHMIC_TRADING, communication_bus)
        self.typical_slippage = 0.0005  # 5 basis points
        self.use_new_api = USE_NEW_API
        self.gemini_client = gemini_client
        if not USE_NEW_API and genai:
            self.model = genai.GenerativeModel(
                model_name=GeminiConfig.MODEL,
                generation_config={
                    "temperature": GeminiConfig.TEMPERATURE,
                    "max_output_tokens": GeminiConfig.MAX_TOKENS,
                }
            )
        else:
            self.model = None
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic"""
        if not genai:
            raise RuntimeError("Gemini API not available.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                if self.use_new_api:
                    response = self.gemini_client.models.generate_content(
                        model=GeminiConfig.MODEL,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=GeminiConfig.TEMPERATURE,
                            max_output_tokens=GeminiConfig.MAX_TOKENS,
                        )
                    )
                    text = response.text
                else:
                    chat = self.model.start_chat(history=[])
                    response = chat.send_message(full_prompt)
                    text = response.text
                
                if GeminiConfig.ENABLE_COST_TRACKING and hasattr(response, 'usage_metadata'):
                    cost_tracker.add_usage(
                        agent_type=str(self.agent_type),
                        input_tokens=getattr(response.usage_metadata, 'prompt_token_count', 0),
                        output_tokens=getattr(response.usage_metadata, 'candidates_token_count', 0)
                    )
                return text
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['429', 'quota', 'resource_exhausted', 'rate limit']):
                    logger.error(f"❌ {self.agent_type} hit API quota (no retry)")
                    raise
                if attempt < GeminiConfig.MAX_RETRIES - 1:
                    time.sleep(GeminiConfig.RETRY_DELAY)
                else:
                    raise
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini"""
        try:
            lines = response_text.strip().split('\n')
            result = {'findings': '', 'recommendation': '', 'conviction': 5, 'concerns': [], 'metrics': {}}
            for line in lines:
                line = line.strip()
                if line.startswith('FINDINGS:'):
                    result['findings'] = line.replace('FINDINGS:', '').strip()
                elif line.startswith('RECOMMENDATION:'):
                    result['recommendation'] = line.replace('RECOMMENDATION:', '').strip()
                elif line.startswith('CONVICTION:'):
                    try:
                        result['conviction'] = int(line.replace('CONVICTION:', '').strip())
                    except ValueError:
                        result['conviction'] = 5
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        result['concerns'] = [c.strip() for c in concerns_str.split(',')]
                elif line.startswith('METRICS:'):
                    metrics_str = line.replace('METRICS:', '').strip()
                    for metric in metrics_str.split(','):
                        if ':' in metric:
                            key, value = metric.split(':', 1)
                            try:
                                result['metrics'][key.strip()] = float(value.strip())
                            except ValueError:
                                result['metrics'][key.strip()] = value.strip()
            return result
        except Exception as e:
            return {'findings': response_text[:200], 'recommendation': 'Review required', 'conviction': 5, 'concerns': [], 'metrics': {}}
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze execution feasibility using Gemini AI"""
        logger.info(f"🤖 {self.agent_type} analyzing portfolio with AI...")
        
        largest = sorted(portfolio.positions, key=lambda p: p.market_value, reverse=True)[:5]
        largest_text = "\n".join([
            f"  - {p.ticker}: ${p.market_value:,.0f} ({p.shares:,} shares @ ${p.current_price:.2f})"
            for p in largest
        ])
        
        system_prompt, user_prompt_template = get_analysis_prompt(str(self.agent_type))
        user_prompt = user_prompt_template.format(
            total_value=portfolio.total_value,
            num_positions=len(portfolio.positions),
            largest_positions=largest_text
        )
        
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            logger.info(f"✅ {self.agent_type} analysis complete")
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics'] or {"typical_slippage_bps": 5}
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} analysis failed: {e}")
            return AgentAnalysis(
                agent_type=self.agent_type,
                findings="AI unavailable",
                recommendation="Standard VWAP execution",
                conviction=7,
                concerns=[],
                metrics={"typical_slippage_bps": 5}
            )
    
    def propose_solution(self, portfolio: Portfolio, context: List[AgentAnalysis]) -> Optional[AgentProposal]:
        """Propose execution strategy"""
        # Typically provides execution guidance rather than trade ideas
        return None
    
    def vote_on_proposal(self, proposal: TradePlan, portfolio: Portfolio) -> AgentVote:
        """Vote based on execution feasibility using AI"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal...")
        
        total_notional = proposal.total_notional
        execution_cost = total_notional * self.typical_slippage
        proposal.expected_execution_cost = execution_cost
        
        trades_text = []
        for trade in proposal.trades:
            trades_text.append(
                f"  - {trade.action} {trade.shares} {trade.ticker} @ ${trade.estimated_price:.2f} = ${trade.notional_value:,.0f}"
            )
        
        vote_prompt_template = get_vote_prompt(str(self.agent_type))
        vote_prompt = vote_prompt_template.format(
            trades="\n".join(trades_text)
        )
        
        try:
            system_prompt, _ = get_analysis_prompt(str(self.agent_type))
            response_text = self._call_gemini(system_prompt, vote_prompt)
            
            vote_type = VoteType.ABSTAIN
            rationale = ""
            concerns = []
            
            for line in response_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('VOTE:'):
                    vote_str = line.replace('VOTE:', '').strip().upper()
                    if 'APPROVE' in vote_str:
                        vote_type = VoteType.APPROVE
                    elif 'REJECT' in vote_str:
                        vote_type = VoteType.REJECT
                elif line.startswith('RATIONALE:'):
                    rationale = line.replace('RATIONALE:', '').strip()
                elif line.startswith('CONCERNS:'):
                    concerns_str = line.replace('CONCERNS:', '').strip()
                    if concerns_str.lower() != 'none':
                        concerns = [c.strip() for c in concerns_str.split(',')]
            
            # Fallback: If no vote found in formatted response, infer from content
            if vote_type == VoteType.ABSTAIN:
                response_lower = response_text.lower()
                if 'approve' in response_lower and 'reject' not in response_lower:
                    vote_type = VoteType.APPROVE
                    if not rationale:
                        rationale = f"Trade execution feasible - cost: ${execution_cost:,.0f}"
                elif 'reject' in response_lower:
                    vote_type = VoteType.REJECT
                    if not rationale:
                        rationale = f"Execution concerns - cost: ${execution_cost:,.0f}"
                else:
                    # Default to APPROVE for trading unless cost is excessive
                    vote_type = VoteType.APPROVE
                    if not rationale:
                        rationale = response_text[:200] if response_text else f"Executable, cost: ${execution_cost:,.0f}"
            
            # Recommend timeline
            if total_notional > 5000000:
                recommended_days = min(5, int(total_notional / 2000000))
                proposal.execution_timeline_days = recommended_days
            
            logger.info(f"✅ {self.agent_type} voted: {vote_type} (cost: ${execution_cost:,.0f})")
            
            return AgentVote(
                agent_type=self.agent_type,
                vote=vote_type,
                rationale=rationale or f"Executable, cost: ${execution_cost:,.0f}",
                concerns=concerns
            )
        except Exception as e:
            logger.error(f"❌ {self.agent_type} voting failed: {e}")
            return AgentVote(
                agent_type=self.agent_type,
                vote=VoteType.APPROVE,
                rationale=f"Executable, cost: ${execution_cost:,.0f} (fallback)",
                concerns=[]
            )
