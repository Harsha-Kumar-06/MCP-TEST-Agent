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

logger = logging.getLogger(__name__)

# Use ONLY the new google.genai API (deprecated google.generativeai causes issues)
try:
    from google import genai
    from google.genai import types
    USE_NEW_API = True
    logger.info("✅ Using new google.genai API")
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]
    USE_NEW_API = False
    logger.error("❌ google-genai package not installed. Run: pip install google-genai")

# Configure Gemini API
gemini_client = None
if genai and GeminiConfig.validate():
    try:
        # New google.genai API only
        gemini_client = genai.Client(api_key=GeminiConfig.get_api_key())
        logger.info(f"✅ Google Gemini configured: {GeminiConfig.MODEL}")
    except Exception as e:
        logger.error(f"❌ Failed to configure Gemini: {e}")


class MarketAnalysisAgent(BaseAgent):
    """Agent specialized in market trends and valuation analysis
    Powered by Google Gemini AI for intelligent market analysis
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.MARKET_ANALYSIS, communication_bus)
        self.gemini_client = gemini_client
        # Market data for context
        self.sector_valuations = {
            "Technology": {"pe_ratio": 32.5, "historical_avg": 24.0, "trend": "overvalued"},
            "Healthcare": {"pe_ratio": 22.0, "historical_avg": 23.0, "trend": "fair"},
            "Financials": {"pe_ratio": 12.5, "historical_avg": 14.0, "trend": "undervalued"},
        }
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic and cost tracking"""
        if not genai or not self.gemini_client or not types:
            raise RuntimeError("Gemini API not available. Install google-genai or google-generativeai package.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                # New google.genai API
                response = self.gemini_client.models.generate_content(
                    model=GeminiConfig.MODEL,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=GeminiConfig.TEMPERATURE,
                        max_output_tokens=GeminiConfig.MAX_TOKENS,
                    )
                )
                text = response.text or ""
                
                # DEBUG: Show first 300 chars of raw AI response (always on to diagnose issues)
                if text:
                    logger.info(f"🔍 RAW AI RESPONSE ({self.agent_type}): {text[:300]}...")
                
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
        raise RuntimeError("Gemini API failed")
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini into analysis components"""
        try:
            # Check for irrelevant content - use specific phrases to avoid false positives
            # Avoid single words like 'modern' which appear in valid finance terms
            irrelevant_patterns = [
                'welcome to the world', 'welcome to ai', 'step into a realm',
                'evocative image', 'sleek design', 'dall-e', 'midjourney',
                'image description', 'picture shows', 'photo of', 'logo design',
                'i cannot provide', 'i can\'t provide', 'as an ai'
            ]
            response_lower = response_text.lower()
            is_irrelevant = any(pattern in response_lower for pattern in irrelevant_patterns)
            
            if is_irrelevant:
                matched = [p for p in irrelevant_patterns if p in response_lower]
                logger.warning(f"⚠️ Received irrelevant AI response (matched: {matched}), using default analysis")
                return {
                    'findings': 'Portfolio analysis completed with default parameters',
                    'recommendation': 'Review portfolio allocation manually',
                    'conviction': 5,
                    'concerns': ['AI response required validation'],
                    'metrics': {}
                }
            
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
            
            # If no structured content was found, provide defaults
            if not result['findings']:
                result['findings'] = 'Portfolio analysis completed'
            if not result['recommendation']:
                result['recommendation'] = 'Monitor portfolio and review allocations'
            
            return result
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return {
                'findings': 'Portfolio analysis completed with default parameters',
                'recommendation': 'Review portfolio manually',
                'conviction': 5,
                'concerns': ['Parsing error encountered'],
                'metrics': {}
            }
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze market conditions and portfolio positioning using Gemini AI"""
        # Check if we can reuse cached analysis (iteration > 0 with same portfolio)
        if self._should_use_cached_analysis(portfolio) and self._cached_analysis:
            logger.info(f"📦 {self.agent_type} using cached analysis (iteration {self.current_iteration})")
            return self._cached_analysis
        
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
        
        # Add strategy context so AI knows the optimization goal
        if hasattr(self, 'strategy_context') and self.strategy_context:
            user_prompt = f"{self.strategy_context}\n\n{user_prompt}"
        
        # Call Gemini
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            
            logger.info(f"✅ {self.agent_type} analysis complete (conviction: {parsed['conviction']})")
            
            analysis = AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics']
            )
            
            # Cache for subsequent iterations
            self._cache_analysis(analysis, portfolio)
            return analysis
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
        """Propose trades based on market analysis - ADAPTS BASED ON FEEDBACK"""
        sector_alloc = portfolio.sector_allocation
        trades = []
        sell_proceeds = 0.0
        
        # ADAPTATION: Check rejection feedback
        reduce_trade_size = False
        if hasattr(self, 'last_rejection_reasons') and self.last_rejection_reasons:
            feedback_text = " ".join(self.last_rejection_reasons).lower()
            if "large" in feedback_text or "illiquid" in feedback_text or "execution" in feedback_text:
                reduce_trade_size = True
        
        # ADAPTATION: Scale trade size based on iteration
        # Start at 20%, reduce by 3% each iteration, minimum 5%
        base_sell_pct = max(0.05, 0.20 - (self.current_iteration * 0.03))
        if reduce_trade_size:
            base_sell_pct *= 0.5
        
        # Step 1: Identify overweight overvalued positions to SELL
        for position in portfolio.positions:
            if position.sector in self.sector_valuations:
                valuation = self.sector_valuations[position.sector]
                sector_pct = sector_alloc.get(position.sector, 0)
                
                if valuation["trend"] == "overvalued" and sector_pct > 25:
                    # ADAPTATION: Vary sell percentage based on iteration
                    shares_to_sell = int(position.shares * base_sell_pct)
                    trade_value = shares_to_sell * position.current_price
                    sell_proceeds += trade_value
                    if shares_to_sell > 0:
                        trades.append(Trade(
                            action="SELL",
                            ticker=position.ticker,
                            shares=shares_to_sell,
                            estimated_price=position.current_price,
                            rationale=f"Reduce overvalued {position.sector} ({base_sell_pct:.0%})"
                        ))
        
        # Step 2: Use sell proceeds to BUY undervalued positions
        if sell_proceeds > 0:
            # Find undervalued sectors to buy
            undervalued_positions = [
                p for p in portfolio.positions 
                if p.sector in self.sector_valuations 
                and self.sector_valuations[p.sector]["trend"] == "undervalued"
            ]
            
            if undervalued_positions:
                # ADAPTATION: Spread buys more on later iterations
                num_buys = min(len(undervalued_positions), 1 + self.current_iteration)
                buy_per_position = sell_proceeds / num_buys
                for position in undervalued_positions[:num_buys]:
                    shares_to_buy = int(buy_per_position / position.current_price)
                    if shares_to_buy > 0:
                        trades.append(Trade(
                            action="BUY",
                            ticker=position.ticker,
                            shares=shares_to_buy,
                            estimated_price=position.current_price,
                            rationale=f"Add to undervalued {position.sector} sector"
                        ))
            else:
                # If no undervalued positions exist, suggest buying Healthcare (fair value)
                healthcare_positions = [p for p in portfolio.positions if p.sector == "Healthcare"]
                if healthcare_positions:
                    for position in healthcare_positions[:2]:  # Buy up to 2 healthcare stocks
                        buy_amount = sell_proceeds / 2
                        shares_to_buy = int(buy_amount / position.current_price)
                        if shares_to_buy > 0:
                            trades.append(Trade(
                                action="BUY",
                                ticker=position.ticker,
                                shares=shares_to_buy,
                                estimated_price=position.current_price,
                                rationale=f"Diversify into defensive {position.sector} sector"
                            ))
        
        if not trades:
            return None
        
        # Calculate expected metrics
        projected_metrics = {
            "portfolio_beta": portfolio.portfolio_beta * 0.95,
            "tech_allocation": sector_alloc.get("Technology", 0) * 0.8
        }
        
        trade_plan = TradePlan(
            trades=trades,
            expected_tax_liability=0,
            expected_execution_cost=sum(t.notional_value * 0.0005 for t in trades),
            execution_timeline_days=2,
            projected_portfolio_metrics=projected_metrics
        )
        
        return AgentProposal(
            agent_type=self.agent_type,
            trade_plan=trade_plan,
            rationale=f"Market rebalancing (iter {self.current_iteration+1}, sell: {base_sell_pct:.0%})",
            conviction=max(6, 8 - self.current_iteration)  # Lower conviction on later iterations
        )
    
    def vote_on_proposal(self, proposal: TradePlan, portfolio: Portfolio) -> AgentVote:
        """Vote based on market analysis - DATA-DRIVEN SCORING"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal (iteration {self.current_iteration + 1})...")
        
        concerns = []
        
        # PORTFOLIO METRICS
        portfolio_beta = portfolio.portfolio_beta
        total_value = portfolio.total_value
        
        # Calculate sector concentration
        sector_values = {}
        for pos in portfolio.positions:
            sector_values[pos.sector] = sector_values.get(pos.sector, 0) + pos.market_value
        max_sector_pct = max(v / total_value * 100 for v in sector_values.values()) if sector_values else 0
        concentrated_sector = max(sector_values.keys(), key=lambda k: sector_values[k]) if sector_values else "N/A"
        
        # Analyze each trade and score it
        overvalued_sells = 0
        undervalued_buys = 0
        bad_trades = 0
        neutral_trades = 0
        improves_diversification = False
        
        for trade in proposal.trades:
            position = next((p for p in portfolio.positions if p.ticker == trade.ticker), None)
            sector = position.sector if position else "Unknown"
            valuation = self.sector_valuations.get(sector, {}).get("trend", "neutral")
            
            if trade.action == "SELL":
                if valuation == "overvalued":
                    overvalued_sells += 1
                elif valuation == "neutral":
                    neutral_trades += 1
                if position and sector == concentrated_sector and max_sector_pct > 30:
                    improves_diversification = True
            elif trade.action == "BUY":
                if valuation == "undervalued":
                    undervalued_buys += 1
                elif valuation == "overvalued":
                    bad_trades += 1
                    concerns.append(f"Buying {trade.ticker} in overvalued {sector}")
                else:
                    neutral_trades += 1
        
        # CALCULATE MARKET SCORE (0-100)
        total_trades = len(proposal.trades)
        market_score = 50  # Base score
        
        # Good trades boost score
        market_score += overvalued_sells * 10  # +10 per good sell
        market_score += undervalued_buys * 10  # +10 per good buy
        
        # Bad trades reduce score
        market_score -= bad_trades * 15  # -15 per bad trade
        
        # Portfolio improvements
        if improves_diversification:
            market_score += 15
        if portfolio_beta > 1.3 and any(t.action == "SELL" for t in proposal.trades):
            market_score += 5  # Reducing exposure in high-beta portfolio
        
        # Cap score
        market_score = max(0, min(100, market_score))
        
        # DYNAMIC THRESHOLD based on portfolio state
        base_threshold = 45
        if max_sector_pct > 35:  # Very concentrated - be stricter
            base_threshold += 10
        if portfolio_beta > 1.4:  # High beta - stricter on buys
            base_threshold += 5
        
        iteration_leniency = self.current_iteration * 3
        threshold = max(base_threshold - iteration_leniency, 30)
        
        # DECISION based on score
        late_iteration = self.current_iteration >= self.max_iterations // 2
        
        if market_score < 30:
            # Very poor proposal - reject even late
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: Market score {market_score}/100 too low. {bad_trades} bad trades, beta: {portfolio_beta:.2f}"
        elif market_score < threshold and not late_iteration:
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: Market score {market_score}/100 below {threshold}. Concentration: {max_sector_pct:.0f}% in {concentrated_sector}"
        elif market_score >= 70:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Strong market alignment ({market_score}/100). {overvalued_sells} good sells, {undervalued_buys} good buys"
        elif improves_diversification:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Score {market_score}/100, improves diversification from {max_sector_pct:.0f}% {concentrated_sector}"
        else:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Market score {market_score}/100 acceptable. Beta: {portfolio_beta:.2f}, ${total_value/1e6:.1f}M"
        
        logger.info(f"✅ {self.agent_type} voted: {vote_type} (score: {market_score}/100)")
        
        return AgentVote(
            agent_type=self.agent_type,
            vote=vote_type,
            rationale=rationale,
            concerns=concerns
        )


class RiskAssessmentAgent(BaseAgent):
    """Agent specialized in risk management and compliance
    Powered by Google Gemini AI for intelligent risk assessment
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.RISK_ASSESSMENT, communication_bus)
        self.gemini_client = gemini_client
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic"""
        if not genai or not self.gemini_client or not types:
            raise RuntimeError("Gemini API not available.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.gemini_client.models.generate_content(
                    model=GeminiConfig.MODEL,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=GeminiConfig.TEMPERATURE,
                        max_output_tokens=GeminiConfig.MAX_TOKENS,
                    )
                )
                text = response.text or ""
                
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
        raise RuntimeError("Gemini API failed")
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini"""
        try:
            # Validate response is portfolio-related - use specific phrases to avoid false positives
            irrelevant_patterns = [
                'welcome to the world', 'welcome to ai', 'step into a realm',
                'evocative image', 'sleek design', 'dall-e', 'midjourney',
                'image description', 'picture shows', 'photo of', 'logo design',
                'i cannot provide', 'i can\'t provide', 'as an ai'
            ]
            response_lower = response_text.lower()
            if any(pattern in response_lower for pattern in irrelevant_patterns):
                matched = [p for p in irrelevant_patterns if p in response_lower]
                logger.warning(f"⚠️ RiskAssessmentAgent: irrelevant response (matched: {matched})")
                return {'findings': 'Risk analysis completed with default parameters', 'recommendation': 'Review compliance manually', 'conviction': 5, 'concerns': ['AI response required validation'], 'metrics': {}}
            
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
            
            if not result['findings']:
                result['findings'] = 'Risk assessment completed'
            if not result['recommendation']:
                result['recommendation'] = 'Monitor risk metrics'
            return result
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {'findings': 'Risk analysis completed with defaults', 'recommendation': 'Review required', 'conviction': 5, 'concerns': [], 'metrics': {}}
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze portfolio risk and compliance using Gemini AI"""
        # Check if we can reuse cached analysis (iteration > 0 with same portfolio)
        if self._should_use_cached_analysis(portfolio) and self._cached_analysis:
            logger.info(f"📦 {self.agent_type} using cached analysis (iteration {self.current_iteration})")
            return self._cached_analysis
        
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
        
        # Add strategy context so AI knows the optimization goal
        if hasattr(self, 'strategy_context') and self.strategy_context:
            user_prompt = f"{self.strategy_context}\n\n{user_prompt}"
        
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            
            logger.info(f"✅ {self.agent_type} analysis complete (conviction: {parsed['conviction']})")
            
            analysis = AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics']
            )
            
            # Cache for subsequent iterations
            self._cache_analysis(analysis, portfolio)
            return analysis
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
        """Propose trades to fix compliance and reduce risk - ADAPTS BASED ON FEEDBACK"""
        violations = portfolio.get_compliance_violations()
        if not violations:
            return None
        
        trades = []
        sector_alloc = portfolio.sector_allocation
        
        # ADAPTATION: Check if previous proposals were rejected for large/illiquid trades
        reduce_trade_size = False
        spread_trades = False
        if hasattr(self, 'last_rejection_reasons') and self.last_rejection_reasons:
            feedback_text = " ".join(self.last_rejection_reasons).lower()
            if "large" in feedback_text or "illiquid" in feedback_text:
                reduce_trade_size = True
            if "concentrated" in feedback_text or "turnover" in feedback_text:
                spread_trades = True
        
        # ADAPTATION: Later iterations should be more conservative
        # Reduce trade size multiplier: 1.0 → 0.7 → 0.5 → 0.3
        size_multiplier = max(0.3, 1.0 - (self.current_iteration * 0.15))
        if reduce_trade_size:
            size_multiplier *= 0.5  # Additional reduction if feedback indicated large trades
        
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
                    
                    # ADAPTATION: Scale reduction by multiplier
                    reduction_needed = reduction_needed * size_multiplier
                    
                    # Find positions in this sector to sell
                    sector_positions = [p for p in portfolio.positions if p.sector == sector]
                    
                    # ADAPTATION: Vary which positions we sell based on iteration
                    if self.current_iteration % 2 == 1:
                        sector_positions = sorted(sector_positions, key=lambda p: p.market_value)
                    else:
                        sector_positions = sorted(sector_positions, key=lambda p: -p.market_value)
                    
                    for position in sector_positions:
                        if reduction_needed > 0:
                            # ADAPTATION: Cap per-trade size for executability
                            max_per_trade = position.market_value * 0.3 if reduce_trade_size else position.market_value * 0.5
                            shares_to_sell = min(
                                position.shares,
                                int(reduction_needed / position.current_price),
                                int(max_per_trade / position.current_price)
                            )
                            if shares_to_sell > 0:
                                trades.append(Trade(
                                    action="SELL",
                                    ticker=position.ticker,
                                    shares=shares_to_sell,
                                    estimated_price=position.current_price,
                                    rationale=f"Reduce {sector} to comply with {limit}% limit"
                                ))
                                reduction_needed -= shares_to_sell * position.current_price
        
        # Calculate proceeds from sells to allocate to BUY trades
        sell_proceeds = sum(t.notional_value for t in trades if t.action == "SELL")
        
        # Add BUY trades for underweight sectors
        if sell_proceeds > 0:
            # Find sectors that are underweight (below 15%)
            underweight_sectors = [
                sector for sector, pct in sector_alloc.items() 
                if pct < 15 and sector not in ["Technology"]  # Exclude overweight sectors
            ]
            
            if underweight_sectors:
                # ADAPTATION: Spread buys more widely on later iterations
                num_sectors = min(len(underweight_sectors), 2 + self.current_iteration)
                buy_per_sector = sell_proceeds / num_sectors
                for sector in underweight_sectors[:num_sectors]:
                    sector_positions = [p for p in portfolio.positions if p.sector == sector]
                    if sector_positions:
                        position = sector_positions[0]
                        shares_to_buy = int(buy_per_sector / position.current_price)
                        if shares_to_buy > 0:
                            trades.append(Trade(
                                action="BUY",
                                ticker=position.ticker,
                                shares=shares_to_buy,
                                estimated_price=position.current_price,
                                rationale=f"Increase {sector} allocation for diversification"
                            ))
        
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
            rationale=f"Fix compliance (iter {self.current_iteration+1}, size: {size_multiplier:.0%})",
            conviction=10
        )
    
    def vote_on_proposal(self, proposal: TradePlan, portfolio: Portfolio) -> AgentVote:
        """Vote based on risk & compliance - DATA-DRIVEN SCORING"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal (iteration {self.current_iteration + 1})...")
        
        # PORTFOLIO METRICS
        violations = portfolio.get_compliance_violations()
        beta = portfolio.portfolio_beta
        total_value = portfolio.total_value
        
        # Sector concentration
        sector_values = {}
        for pos in portfolio.positions:
            sector_values[pos.sector] = sector_values.get(pos.sector, 0) + pos.market_value
        max_sector_pct = max(v / total_value * 100 for v in sector_values.values()) if sector_values else 0
        concentrated_sector = max(sector_values.keys(), key=lambda k: sector_values[k]) if sector_values else "N/A"
        
        concerns = list(violations) if violations else []
        
        # Analyze trade impact
        fixes_violations = 0
        reduces_concentration = False
        reduces_beta = False
        increases_risk = False
        
        for trade in proposal.trades:
            pos = next((p for p in portfolio.positions if p.ticker == trade.ticker), None)
            if trade.action == "SELL" and pos:
                for v in violations:
                    if pos.sector.lower() in v.lower():
                        fixes_violations += 1
                if pos.sector == concentrated_sector:
                    reduces_concentration = True
                if pos.beta > 1.2:
                    reduces_beta = True
            elif trade.action == "BUY" and pos:
                if pos.beta > 1.3:
                    increases_risk = True
        
        # Risk factors
        high_beta = beta > 1.3
        very_concentrated = max_sector_pct > 35
        num_violations = len(violations)
        
        if high_beta:
            concerns.append(f"Beta {beta:.2f} elevated")
        if very_concentrated:
            concerns.append(f"{concentrated_sector} {max_sector_pct:.0f}%")
        
        # CALCULATE RISK SCORE (0-100, higher = safer/better)
        risk_score = 70  # Base score
        
        # Compliance
        risk_score -= num_violations * 10  # -10 per violation
        risk_score += fixes_violations * 15  # +15 per fix
        
        # Concentration
        if very_concentrated:
            risk_score -= 10
        if reduces_concentration:
            risk_score += 15
        
        # Beta
        if high_beta:
            risk_score -= 10
        if reduces_beta:
            risk_score += 10
        if increases_risk:
            risk_score -= 15
        
        # Cap score
        risk_score = max(0, min(100, risk_score))
        
        # DYNAMIC THRESHOLD
        base_threshold = 45
        if num_violations > 2:
            base_threshold += 15  # Stricter when many violations
        if high_beta and very_concentrated:
            base_threshold += 10  # Double trouble
        
        iteration_leniency = self.current_iteration * 4
        threshold = max(base_threshold - iteration_leniency, 25)
        
        # DECISION
        late_iteration = self.current_iteration >= self.max_iterations // 2
        
        if risk_score < 25:
            # Dangerous proposal - reject
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: Risk score {risk_score}/100 dangerous. {num_violations} violations, beta {beta:.2f}"
        elif risk_score < threshold and not late_iteration:
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: Risk score {risk_score}/100 below {threshold}. {num_violations} violations unfixed"
        elif risk_score >= 75:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Excellent risk profile ({risk_score}/100). {'Fixes ' + str(fixes_violations) + ' violations' if fixes_violations else 'Compliant'}"
        elif fixes_violations > 0 or reduces_concentration:
            vote_type = VoteType.APPROVE
            benefits = []
            if fixes_violations: benefits.append(f"fixes {fixes_violations}")
            if reduces_concentration: benefits.append("diversifies")
            if reduces_beta: benefits.append("lowers beta")
            rationale = f"Iter {self.current_iteration+1}: Risk score {risk_score}/100, {', '.join(benefits)}"
        else:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Manageable risk. Score: {risk_score}, ESG: {avg_esg:.0f}"
        
        logger.info(f"✅ {self.agent_type} voted: {vote_type} (iter {self.current_iteration+1})")
        
        return AgentVote(
            agent_type=self.agent_type,
            vote=vote_type,
            rationale=rationale,
            concerns=concerns
        )


class TaxStrategyAgent(BaseAgent):
    """Agent specialized in tax optimization
    Powered by Google Gemini AI for intelligent tax strategy
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.TAX_STRATEGY, communication_bus)
        self.long_term_rate = 0.20  # 20% for long-term gains
        self.short_term_rate = 0.37  # 37% for short-term gains
        self.gemini_client = gemini_client
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic"""
        if not genai or not self.gemini_client or not types:
            raise RuntimeError("Gemini API not available.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.gemini_client.models.generate_content(
                    model=GeminiConfig.MODEL,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=GeminiConfig.TEMPERATURE,
                        max_output_tokens=GeminiConfig.MAX_TOKENS,
                    )
                )
                text = response.text or ""
                
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
        raise RuntimeError("Gemini API failed")
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini"""
        try:
            # Validate response is portfolio-related - use specific phrases to avoid false positives
            irrelevant_patterns = [
                'welcome to the world', 'welcome to ai', 'step into a realm',
                'evocative image', 'sleek design', 'dall-e', 'midjourney',
                'image description', 'picture shows', 'photo of', 'logo design',
                'i cannot provide', 'i can\'t provide', 'as an ai'
            ]
            response_lower = response_text.lower()
            if any(pattern in response_lower for pattern in irrelevant_patterns):
                matched = [p for p in irrelevant_patterns if p in response_lower]
                logger.warning(f"⚠️ TaxOptimizationAgent: irrelevant response (matched: {matched})")
                return {'findings': 'Tax analysis completed with default parameters', 'recommendation': 'Review tax implications manually', 'conviction': 5, 'concerns': ['AI response required validation'], 'metrics': {}}
            
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
            
            if not result['findings']:
                result['findings'] = 'Tax assessment completed'
            if not result['recommendation']:
                result['recommendation'] = 'Monitor tax implications'
            return result
        except Exception as e:
            return {'findings': 'Tax analysis completed with defaults', 'recommendation': 'Review required', 'conviction': 5, 'concerns': [], 'metrics': {}}
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze tax implications using Gemini AI"""
        # Check if we can reuse cached analysis (iteration > 0 with same portfolio)
        if self._should_use_cached_analysis(portfolio) and self._cached_analysis:
            logger.info(f"📦 {self.agent_type} using cached analysis (iteration {self.current_iteration})")
            return self._cached_analysis
        
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
        
        # Add strategy context so AI knows the optimization goal
        if hasattr(self, 'strategy_context') and self.strategy_context:
            user_prompt = f"{self.strategy_context}\n\n{user_prompt}"
        
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            logger.info(f"✅ {self.agent_type} analysis complete")
            analysis = AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics']
            )
            
            # Cache for subsequent iterations
            self._cache_analysis(analysis, portfolio)
            return analysis
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
        """Vote based on tax efficiency - PORTFOLIO & CONSENSUS AWARE"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal (iteration {self.current_iteration + 1})...")
        
        # PORTFOLIO ANALYSIS - Get full context
        total_value = portfolio.total_value
        portfolio_beta = portfolio.portfolio_beta
        avg_esg = portfolio.average_esg_score
        
        concerns = []
        total_tax = 0
        short_term_sales = 0
        loss_harvesting_opportunities = 0
        positions_near_long_term = []  # Within 60 days of going long-term
        
        for trade in proposal.trades:
            if trade.action == "SELL":
                position = next((p for p in portfolio.positions if p.ticker == trade.ticker), None)
                if position:
                    days_held = (datetime.now() - position.acquisition_date).days
                    days_to_lt = 365 - days_held
                    is_lt = days_held >= 365
                    gain_per_share = position.current_price - position.cost_basis
                    total_gain = gain_per_share * trade.shares
                    
                    if total_gain < 0:
                        loss_harvesting_opportunities += 1  # Tax loss harvesting
                    else:
                        tax_rate = self.long_term_rate if is_lt else self.short_term_rate
                        tax = total_gain * tax_rate
                        total_tax += tax
                        
                        if not is_lt and total_gain > 0:
                            short_term_sales += 1
                            if 0 < days_to_lt <= 60:
                                positions_near_long_term.append(f"{trade.ticker} ({days_to_lt}d to LT)")
                                concerns.append(f"{trade.ticker}: {days_to_lt} days from long-term rate")
                            else:
                                concerns.append(f"{trade.ticker}: ST gain taxed at {tax_rate*100:.0f}%")
        
        proposal.expected_tax_liability = total_tax
        tax_pct = (total_tax / total_value * 100) if total_value > 0 else 0
        
        # CONSENSUS AWARENESS
        votes_to_pass = self.votes_needed_to_pass
        late_iteration = self.current_iteration >= self.max_iterations // 2
        high_threshold = self.consensus_threshold >= 0.8
        
        # Iteration-aware thresholds
        base_tax_pct = 2.0
        iteration_leniency = self.current_iteration * 0.5
        tax_pct_threshold = min(base_tax_pct + iteration_leniency, 5.0)
        
        # Large portfolios can tolerate more absolute tax
        large_portfolio = total_value > 10000000  # $10M+
        absolute_tax_threshold = 300000 if large_portfolio else 200000
        
        # CALCULATE TAX SCORE (0-100, higher = more tax-efficient)
        tax_score = 80  # Base score
        
        # Tax burden impact
        if tax_pct > 3.0:
            tax_score -= 30  # Heavy tax hit
        elif tax_pct > 2.0:
            tax_score -= 20
        elif tax_pct > 1.0:
            tax_score -= 10
        
        # Short-term penalties
        tax_score -= short_term_sales * 8  # -8 per ST sale
        
        # Near long-term concerns (could wait)
        tax_score -= len(positions_near_long_term) * 12  # -12 per position close to LT
        
        # Loss harvesting bonus
        tax_score += loss_harvesting_opportunities * 10  # +10 per harvest opportunity
        
        # Cap score
        tax_score = max(0, min(100, tax_score))
        
        # DYNAMIC THRESHOLD based on portfolio
        base_threshold = 40
        if total_value > 20000000:  # Large portfolio - stricter on taxes
            base_threshold += 10
        if len(positions_near_long_term) > 0:  # Could easily improve
            base_threshold += 10
        
        iteration_leniency = self.current_iteration * 5
        threshold = max(base_threshold - iteration_leniency, 25)
        
        # DECISION
        late_iteration = self.current_iteration >= self.max_iterations // 2
        has_loss_harvesting = loss_harvesting_opportunities > 0
        
        if tax_score < 25 and total_tax > 100000:
            # Very expensive - reject even late
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: Tax score {tax_score}/100, ${total_tax:,.0f} too high for ${total_value/1e6:.1f}M portfolio"
        elif tax_score < threshold and not late_iteration:
            vote_type = VoteType.REJECT
            reason = f"Score {tax_score}/100 below {threshold}"
            if positions_near_long_term:
                reason += f". Wait for: {', '.join(positions_near_long_term)}"
            rationale = f"Iter {self.current_iteration+1}: Tax inefficient - {reason}"
        elif tax_score >= 70:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Tax-efficient ({tax_score}/100). ${total_tax:,.0f} ({tax_pct:.1f}%)"
        elif has_loss_harvesting:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Tax score {tax_score}/100 with {loss_harvesting_opportunities} harvest opportunities"
        else:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Tax score {tax_score}/100 acceptable. ${total_tax:,.0f}, {short_term_sales} ST sales"
        
        logger.info(f"✅ {self.agent_type} voted: {vote_type} (iter {self.current_iteration+1}, tax: ${total_tax:,.0f})")
        
        return AgentVote(
            agent_type=self.agent_type,
            vote=vote_type,
            rationale=rationale,
            concerns=concerns
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
        self.gemini_client = gemini_client
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic"""
        if not genai or not self.gemini_client or not types:
            raise RuntimeError("Gemini API not available.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.gemini_client.models.generate_content(
                    model=GeminiConfig.MODEL,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=GeminiConfig.TEMPERATURE,
                        max_output_tokens=GeminiConfig.MAX_TOKENS,
                    )
                )
                text = response.text or ""
                
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
        raise RuntimeError("Gemini API failed")
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini"""
        try:
            # Validate response is portfolio-related - use specific phrases to avoid false positives
            irrelevant_patterns = [
                'welcome to the world', 'welcome to ai', 'step into a realm',
                'evocative image', 'sleek design', 'dall-e', 'midjourney',
                'image description', 'picture shows', 'photo of', 'logo design',
                'i cannot provide', 'i can\'t provide', 'as an ai'
            ]
            response_lower = response_text.lower()
            if any(pattern in response_lower for pattern in irrelevant_patterns):
                matched = [p for p in irrelevant_patterns if p in response_lower]
                logger.warning(f"⚠️ ESGComplianceAgent: irrelevant response (matched: {matched})")
                return {'findings': 'ESG analysis completed with default parameters', 'recommendation': 'Review ESG compliance manually', 'conviction': 5, 'concerns': ['AI response required validation'], 'metrics': {}}
            
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
            
            if not result['findings']:
                result['findings'] = 'ESG assessment completed'
            if not result['recommendation']:
                result['recommendation'] = 'Monitor ESG scores'
            return result
        except Exception as e:
            return {'findings': 'ESG analysis completed with defaults', 'recommendation': 'Review required', 'conviction': 5, 'concerns': [], 'metrics': {}}
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze ESG compliance using Gemini AI"""
        # Check if we can reuse cached analysis (iteration > 0 with same portfolio)
        if self._should_use_cached_analysis(portfolio) and self._cached_analysis:
            logger.info(f"📦 {self.agent_type} using cached analysis (iteration {self.current_iteration})")
            return self._cached_analysis
        
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
        
        # Add strategy context so AI knows the optimization goal
        if hasattr(self, 'strategy_context') and self.strategy_context:
            user_prompt = f"{self.strategy_context}\n\n{user_prompt}"
        
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            logger.info(f"✅ {self.agent_type} analysis complete")
            analysis = AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics'] or {"avg_esg_score": avg_esg}
            )
            
            # Cache for subsequent iterations
            self._cache_analysis(analysis, portfolio)
            return analysis
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
        """Vote based on actual ESG impact - genuinely portfolio-aware"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal (iteration {self.current_iteration + 1})...")
        
        concerns = []
        
        # Calculate ACTUAL portfolio ESG metrics
        current_avg_esg = portfolio.average_esg_score
        total_value = portfolio.total_value
        
        # Calculate proposed changes impact on ESG
        esg_impact = 0.0
        low_esg_issues = []
        high_esg_benefits = []
        
        for trade in proposal.trades:
            trade_esg = self.esg_ratings.get(trade.ticker, 70)
            trade_value = trade.notional_value
            trade_weight = trade_value / total_value if total_value > 0 else 0
            
            if trade.action == "BUY":
                esg_impact += trade_weight * (trade_esg - current_avg_esg)
                if trade_esg < self.esg_minimum:
                    low_esg_issues.append(f"{trade.ticker} (ESG:{trade_esg})")
            elif trade.action == "SELL":
                esg_impact -= trade_weight * (trade_esg - current_avg_esg)
                if trade_esg >= 75:
                    high_esg_benefits.append(f"{trade.ticker} (ESG:{trade_esg})")
        
        # Calculate projected ESG after trades
        projected_esg = current_avg_esg + (esg_impact * 10)
        esg_change = projected_esg - current_avg_esg
        
        # DYNAMIC thresholds based on iteration AND portfolio state
        base_threshold = self.esg_minimum  # 65 default
        iteration_leniency = self.current_iteration * 5  # More lenient each iteration
        
        # Portfolio-adaptive: be stricter if portfolio ESG is already low
        if current_avg_esg < 60:
            strictness_modifier = 5  # More strict for low-ESG portfolios
        elif current_avg_esg > 75:
            strictness_modifier = -10  # More lenient for high-ESG portfolios
        else:
            strictness_modifier = 0
        
        adjusted_threshold = max(base_threshold - iteration_leniency + strictness_modifier, 45)
        
        # Calculate ESG "score" for this proposal (0-100)
        num_issues = len(low_esg_issues)
        num_benefits = len(high_esg_benefits)
        proposal_esg_score = 70  # Base score
        proposal_esg_score -= num_issues * 15  # -15 per low-ESG buy
        proposal_esg_score += num_benefits * 5  # +5 per high-ESG involved
        if esg_change > 0:
            proposal_esg_score += 10  # Bonus for improving ESG
        elif esg_change < -2:
            proposal_esg_score -= 10  # Penalty for significantly hurting ESG
        
        # DECISION: Based on proposal score vs dynamic threshold
        # This creates natural variation - some proposals pass, some don't
        late_iteration = self.current_iteration >= self.max_iterations // 2
        
        if proposal_esg_score < 40 and not late_iteration:
            # Severe ESG problems - reject unless late
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: ESG score {proposal_esg_score}/100 too low. Issues: {', '.join(low_esg_issues) if low_esg_issues else 'negative impact'}"
            concerns = low_esg_issues if low_esg_issues else [f"ESG change: {esg_change:+.1f}"]
        elif proposal_esg_score < 55 and current_avg_esg < adjusted_threshold:
            # Mediocre proposal when portfolio needs improvement
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: Portfolio ESG {current_avg_esg:.0f} below {adjusted_threshold:.0f}, proposal score {proposal_esg_score}/100 insufficient"
            concerns.append(f"Need ESG improvement, got score {proposal_esg_score}")
        elif proposal_esg_score >= 70 or esg_change > 0:
            # Good proposal or positive impact
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: ESG score {proposal_esg_score}/100. Portfolio: {current_avg_esg:.0f} → {projected_esg:.0f} ({esg_change:+.1f})"
        elif late_iteration:
            # Late iteration - accept mediocre for consensus
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: ESG score {proposal_esg_score}/100 acceptable for consensus ({self.votes_needed_to_pass}/{self.total_agents} needed)"
        else:
            # Default: approve if not clearly bad
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: ESG acceptable. Score: {proposal_esg_score}/100, portfolio avg: {current_avg_esg:.0f}"
        
        logger.info(f"✅ {self.agent_type} voted: {vote_type} (iter {self.current_iteration+1})")
        
        return AgentVote(
            agent_type=self.agent_type,
            vote=vote_type,
            rationale=rationale,
            concerns=concerns
        )


class AlgorithmicTradingAgent(BaseAgent):
    """Agent specialized in trade execution and liquidity analysis
    Powered by Google Gemini AI for intelligent execution strategy
    """
    
    def __init__(self, communication_bus: CommunicationBus):
        super().__init__(AgentType.ALGORITHMIC_TRADING, communication_bus)
        self.typical_slippage = 0.0005  # 5 basis points
        self.gemini_client = gemini_client
    
    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Call Gemini API with retry logic"""
        if not genai or not self.gemini_client or not types:
            raise RuntimeError("Gemini API not available.")
        
        for attempt in range(GeminiConfig.MAX_RETRIES):
            try:
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.gemini_client.models.generate_content(
                    model=GeminiConfig.MODEL,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=GeminiConfig.TEMPERATURE,
                        max_output_tokens=GeminiConfig.MAX_TOKENS,
                    )
                )
                text = response.text or ""
                
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
        raise RuntimeError("Gemini API failed")
    
    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse structured response from Gemini"""
        try:
            # Validate response is portfolio-related - use specific phrases to avoid false positives
            irrelevant_patterns = [
                'welcome to the world', 'welcome to ai', 'step into a realm',
                'evocative image', 'sleek design', 'dall-e', 'midjourney',
                'image description', 'picture shows', 'photo of', 'logo design',
                'i cannot provide', 'i can\'t provide', 'as an ai'
            ]
            response_lower = response_text.lower()
            if any(pattern in response_lower for pattern in irrelevant_patterns):
                matched = [p for p in irrelevant_patterns if p in response_lower]
                logger.warning(f"⚠️ ExecutionStrategyAgent: irrelevant response (matched: {matched})")
                return {'findings': 'Trading analysis completed with default parameters', 'recommendation': 'Review execution plan manually', 'conviction': 5, 'concerns': ['AI response required validation'], 'metrics': {}}
            
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
            
            if not result['findings']:
                result['findings'] = 'Trading analysis completed'
            if not result['recommendation']:
                result['recommendation'] = 'Execute trades as planned'
            return result
        except Exception as e:
            return {'findings': 'Trading analysis completed with defaults', 'recommendation': 'Review required', 'conviction': 5, 'concerns': [], 'metrics': {}}
    
    def analyze(self, portfolio: Portfolio) -> AgentAnalysis:
        """Analyze execution feasibility using Gemini AI"""
        # Check if we can reuse cached analysis (iteration > 0 with same portfolio)
        if self._should_use_cached_analysis(portfolio) and self._cached_analysis:
            logger.info(f"📦 {self.agent_type} using cached analysis (iteration {self.current_iteration})")
            return self._cached_analysis
        
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
        
        # Add strategy context so AI knows the optimization goal
        if hasattr(self, 'strategy_context') and self.strategy_context:
            user_prompt = f"{self.strategy_context}\n\n{user_prompt}"
        
        try:
            response_text = self._call_gemini(system_prompt, user_prompt)
            parsed = self._parse_analysis_response(response_text)
            logger.info(f"✅ {self.agent_type} analysis complete")
            analysis = AgentAnalysis(
                agent_type=self.agent_type,
                findings=parsed['findings'],
                recommendation=parsed['recommendation'],
                conviction=parsed['conviction'],
                concerns=parsed['concerns'],
                metrics=parsed['metrics'] or {"typical_slippage_bps": 5}
            )
            
            # Cache for subsequent iterations
            self._cache_analysis(analysis, portfolio)
            return analysis
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
        """Vote based on execution feasibility - PORTFOLIO & CONSENSUS AWARE"""
        logger.info(f"🗳️  {self.agent_type} voting on proposal (iteration {self.current_iteration + 1})...")
        
        # PORTFOLIO ANALYSIS - Get full context
        total_value = portfolio.total_value
        portfolio_beta = portfolio.portfolio_beta
        num_positions = len(portfolio.positions)
        avg_esg = portfolio.average_esg_score
        
        total_notional = proposal.total_notional
        trade_pct_of_portfolio = (total_notional / total_value * 100) if total_value > 0 else 0
        execution_cost = total_notional * self.typical_slippage
        proposal.expected_execution_cost = execution_cost
        
        concerns = []
        large_trades = 0
        illiquid_trades = 0
        
        for trade in proposal.trades:
            position = next((p for p in portfolio.positions if p.ticker == trade.ticker), None)
            trade_value = trade.notional_value
            
            # Flag large single trades relative to portfolio
            if trade_value > total_value * 0.05:  # >5% of portfolio
                large_trades += 1
                concerns.append(f"{trade.ticker}: ${trade_value/1e6:.1f}M ({trade_value/total_value*100:.1f}% of portfolio)")
            
            # Flag large absolute trades
            if trade_value > 2000000:  # >$2M
                illiquid_trades += 1
        
        # Recommend timeline for large rebalances
        if total_notional > 5000000 or trade_pct_of_portfolio > 10:
            recommended_days = max(2, min(5, int(total_notional / 2000000)))
            proposal.execution_timeline_days = recommended_days
            concerns.append(f"Recommend {recommended_days}-day execution ({trade_pct_of_portfolio:.0f}% turnover)")
        
        # CONSENSUS AWARENESS
        votes_to_pass = self.votes_needed_to_pass
        late_iteration = self.current_iteration >= self.max_iterations // 2
        
        # Iteration-aware thresholds
        cost_bps = (execution_cost / total_notional * 10000) if total_notional > 0 else 0
        base_bps_threshold = 50
        iteration_leniency = self.current_iteration * 10
        bps_threshold = base_bps_threshold + iteration_leniency
        
        # Adjust for portfolio size - larger portfolios have better execution
        if total_value > 50000000:  # $50M+
            bps_threshold += 20  # More tolerant
        
        # CALCULATE EXECUTION SCORE (0-100, higher = easier to execute)
        exec_score = 80  # Base score
        
        # Cost impact
        if cost_bps > 75:
            exec_score -= 30  # Very expensive
        elif cost_bps > 50:
            exec_score -= 15
        elif cost_bps > 30:
            exec_score -= 5
        
        # Large trades are harder
        exec_score -= large_trades * 8  # -8 per large trade
        exec_score -= illiquid_trades * 10  # -10 per illiquid
        
        # Turnover impact
        if trade_pct_of_portfolio > 25:
            exec_score -= 20  # High turnover
        elif trade_pct_of_portfolio > 15:
            exec_score -= 10
        
        # Portfolio size bonus (better execution)
        if total_value > 50000000:
            exec_score += 10
        
        # Cap score
        exec_score = max(0, min(100, exec_score))
        
        # DYNAMIC THRESHOLD
        base_threshold = 40
        if illiquid_trades > 2:
            base_threshold += 15  # Stricter with illiquid trades
        if trade_pct_of_portfolio > 20:
            base_threshold += 10
        
        iteration_leniency = self.current_iteration * 4
        threshold = max(base_threshold - iteration_leniency, 25)
        
        # DECISION
        late_iteration = self.current_iteration >= self.max_iterations // 2
        total_trades = len(proposal.trades)
        
        if exec_score < 20:
            # Very difficult execution - reject
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: Execution score {exec_score}/100 too risky. {large_trades} large, {illiquid_trades} illiquid trades"
        elif exec_score < threshold and not late_iteration:
            vote_type = VoteType.REJECT
            rationale = f"Iter {self.current_iteration+1}: Exec score {exec_score}/100 below {threshold}. Cost {cost_bps:.0f} bps, {trade_pct_of_portfolio:.0f}% turnover"
        elif exec_score >= 70:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Easy execution ({exec_score}/100). ${execution_cost:,.0f} cost, {total_trades} trades"
        elif trade_pct_of_portfolio < 15:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Exec score {exec_score}/100, manageable {trade_pct_of_portfolio:.0f}% turnover"
        else:
            vote_type = VoteType.APPROVE
            rationale = f"Iter {self.current_iteration+1}: Exec score {exec_score}/100 acceptable. ${execution_cost:,.0f} ({cost_bps:.0f} bps)"
        
        logger.info(f"✅ {self.agent_type} voted: {vote_type} (iter {self.current_iteration+1}, cost: ${execution_cost:,.0f})")
        
        return AgentVote(
            agent_type=self.agent_type,
            vote=vote_type,
            rationale=rationale,
            concerns=concerns
        )

