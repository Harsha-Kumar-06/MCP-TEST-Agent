"""
Gemini-Enhanced Portfolio Parser
Dynamically learns new tickers and sectors using Google Gemini API
"""
import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    USE_NEW_API = True
except ImportError:
    GEMINI_AVAILABLE = False
    USE_NEW_API = False
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

try:
    from .models import Portfolio, Position
    from .config import GeminiConfig
except ImportError:
    from portfolio_swarm.models import Portfolio, Position
    from portfolio_swarm.config import GeminiConfig

logger = logging.getLogger(__name__)


class DynamicKnowledgeBase:
    """Learns and caches ticker/sector mappings using Gemini"""
    
    def __init__(self, cache_file: str = "portfolio_knowledge_cache.json"):
        self.cache_file = cache_file
        self.company_tickers = self._load_base_mappings()
        self.ticker_sectors = self._load_base_sectors()
        self.learned_data = self._load_cache()
        self.gemini_client = None
        
        if GEMINI_AVAILABLE and GeminiConfig.validate() and genai:
            # New google.genai API
            self.gemini_client = genai.Client(api_key=GeminiConfig.get_api_key())
    
    def _call_gemini(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """Call Gemini API with the new google.genai package"""
        if not self.gemini_client or not types:
            return None
        try:
            response = self.gemini_client.models.generate_content(
                model=GeminiConfig.MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=max_tokens,
                )
            )
            return response.text
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")
            return None
    
    def _load_base_mappings(self) -> Dict[str, str]:
        """Load base company to ticker mappings"""
        return {
            'microsoft': 'MSFT', 'apple': 'AAPL', 'nvidia': 'NVDA',
            'alphabet': 'GOOGL', 'google': 'GOOGL', 'meta': 'META',
            'tesla': 'TSLA', 'amazon': 'AMZN', 'jpmorgan': 'JPM',
            'johnson & johnson': 'JNJ', 'j&j': 'JNJ',
            'unitedhealth': 'UNH', 'visa': 'V', 'coca-cola': 'KO', 'coke': 'KO',
            'procter & gamble': 'PG', 'p&g': 'PG',
            'exxonmobil': 'XOM', 'exxon': 'XOM', 'chevron': 'CVX',
            'alibaba': 'BABA', 'taiwan semi': 'TSM', 'taiwan semiconductor': 'TSM',
            'berkshire hathaway': 'BRK.B', 'walmart': 'WMT', 'pepsi': 'PEP',
            'netflix': 'NFLX', 'adobe': 'ADBE', 'salesforce': 'CRM',
            'oracle': 'ORCL', 'intel': 'INTC', 'amd': 'AMD',
            'qualcomm': 'QCOM', 'broadcom': 'AVGO', 'paypal': 'PYPL',
            'mastercard': 'MA', 'american express': 'AXP',
            'bank of america': 'BAC', 'wells fargo': 'WFC', 'goldman sachs': 'GS',
            'morgan stanley': 'MS', 'citigroup': 'C',
            'pfizer': 'PFE', 'merck': 'MRK', 'eli lilly': 'LLY',
            'abbvie': 'ABBV', 'bristol myers': 'BMY',
        }
    
    def _load_base_sectors(self) -> Dict[str, str]:
        """Load base ticker to sector mappings"""
        return {
            'MSFT': 'Technology', 'AAPL': 'Technology', 'NVDA': 'Technology',
            'GOOGL': 'Technology', 'GOOG': 'Technology', 'META': 'Technology',
            'TSLA': 'Technology', 'AMZN': 'Technology', 'AMD': 'Technology',
            'INTC': 'Technology', 'CRM': 'Technology', 'ORCL': 'Technology',
            'NFLX': 'Technology', 'ADBE': 'Technology', 'QCOM': 'Technology',
            'AVGO': 'Technology', 'PYPL': 'Technology',
            'JNJ': 'Healthcare', 'UNH': 'Healthcare', 'PFE': 'Healthcare',
            'ABBV': 'Healthcare', 'TMO': 'Healthcare', 'MRK': 'Healthcare',
            'LLY': 'Healthcare', 'BMY': 'Healthcare',
            'JPM': 'Financials', 'BAC': 'Financials', 'WFC': 'Financials',
            'GS': 'Financials', 'MS': 'Financials', 'C': 'Financials',
            'V': 'Financials', 'MA': 'Financials', 'AXP': 'Financials',
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',
            'KO': 'Consumer', 'PG': 'Consumer', 'PEP': 'Consumer', 'WMT': 'Consumer',
            'BABA': 'Technology', 'TSM': 'Technology',
            'BRK.B': 'Financials', 'BRK.A': 'Financials',
        }
    
    def _load_cache(self) -> Dict:
        """Load learned data from cache file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'companies': {}, 'sectors': {}, 'esg_scores': {}}
    
    def _save_cache(self):
        """Save learned data to cache file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.learned_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save knowledge cache: {e}")
    
    def get_ticker_from_company(self, company_name: str) -> Optional[str]:
        """Get ticker symbol from company name, using Gemini if needed"""
        company_lower = company_name.lower().strip()
        
        # Check static mappings first
        if company_lower in self.company_tickers:
            return self.company_tickers[company_lower]
        
        # Check learned cache
        if company_lower in self.learned_data['companies']:
            return self.learned_data['companies'][company_lower]
        
        # Use Gemini to learn new ticker
        if self.gemini_client:
            ticker = self._ask_gemini_for_ticker(company_name)
            if ticker:
                # Cache the learned mapping
                self.learned_data['companies'][company_lower] = ticker
                self.company_tickers[company_lower] = ticker
                self._save_cache()
                logger.info(f"✨ Learned: {company_name} → {ticker}")
                return ticker
        
        return None
    
    def get_sector_for_ticker(self, ticker: str) -> str:
        """Get sector for ticker, using Gemini if needed"""
        ticker_upper = ticker.upper()
        
        # Check static mappings first
        if ticker_upper in self.ticker_sectors:
            return self.ticker_sectors[ticker_upper]
        
        # Check learned cache
        if ticker_upper in self.learned_data['sectors']:
            return self.learned_data['sectors'][ticker_upper]
        
        # Use Gemini to learn new sector
        if self.gemini_client:
            sector = self._ask_gemini_for_sector(ticker)
            if sector:
                # Cache the learned mapping
                self.learned_data['sectors'][ticker_upper] = sector
                self.ticker_sectors[ticker_upper] = sector
                self._save_cache()
                logger.info(f"✨ Learned: {ticker} → {sector} sector")
                return sector
        
        return 'Other'
    
    def get_esg_score(self, ticker: str) -> int:
        """Get estimated ESG score for ticker using Gemini"""
        ticker_upper = ticker.upper()
        
        # Check cache first
        if ticker_upper in self.learned_data['esg_scores']:
            return self.learned_data['esg_scores'][ticker_upper]
        
        # Use Gemini to estimate ESG
        if self.gemini_client:
            esg = self._ask_gemini_for_esg(ticker)
            if esg:
                self.learned_data['esg_scores'][ticker_upper] = esg
                self._save_cache()
                return esg
        
        return 70  # Default
    
    def _ask_gemini_for_ticker(self, company_name: str) -> Optional[str]:
        """Ask Gemini for ticker symbol"""
        try:
            prompt = f"""What is the stock ticker symbol for: {company_name}

Return ONLY the ticker symbol in uppercase (e.g., AAPL, MSFT, GOOGL).
If the company is not publicly traded or you're unsure, return "UNKNOWN".
No explanation needed, just the ticker."""

            response_text = self._call_gemini(prompt, max_tokens=20)
            if not response_text:
                return None
            
            ticker = response_text.strip().upper()
            
            # Validate ticker format
            if ticker and ticker != "UNKNOWN" and 1 <= len(ticker) <= 5 and ticker.replace('.', '').isalpha():
                return ticker
            
        except Exception as e:
            logger.warning(f"Gemini ticker lookup failed for '{company_name}': {e}")
        
        return None
    
    def _ask_gemini_for_sector(self, ticker: str) -> Optional[str]:
        """Ask Gemini for sector classification"""
        try:
            prompt = f"""What sector does the stock ticker {ticker} belong to?

Choose ONE from: Technology, Healthcare, Financials, Energy, Consumer, Industrials, Materials, Utilities, Real Estate, Other

Return ONLY the sector name, no explanation."""

            response_text = self._call_gemini(prompt, max_tokens=20)
            if not response_text:
                return None
            
            sector = response_text.strip()
            
            # Validate sector
            valid_sectors = ['Technology', 'Healthcare', 'Financials', 'Energy', 
                           'Consumer', 'Industrials', 'Materials', 'Utilities', 
                           'Real Estate', 'Other']
            
            if sector in valid_sectors:
                return sector
            
        except Exception as e:
            logger.warning(f"Gemini sector lookup failed for '{ticker}': {e}")
        
        return None
        
        return None
    
    def _ask_gemini_for_esg(self, ticker: str) -> Optional[int]:
        """Ask Gemini for ESG score estimate"""
        try:
            prompt = f"""What is the approximate ESG (Environmental, Social, Governance) score for {ticker}?

Return ONLY a number between 0-100 representing the ESG score.
Higher is better. No explanation needed."""

            response_text = self._call_gemini(prompt, max_tokens=10)
            if not response_text:
                return None
            
            score_text = response_text.strip()
            match = re.search(r'\d+', score_text)
            if not match:
                return None
            score = int(match.group())
            
            if 0 <= score <= 100:
                return score
            
        except Exception as e:
            logger.warning(f"Gemini ESG lookup failed for '{ticker}': {e}")
        
        return None
    
    def extract_all_from_text(self, text: str) -> Dict:
        """Use Gemini to extract ALL portfolio data from free-form text"""
        if not self.gemini_client:
            return {}
        
        try:
            prompt = f"""Extract stock portfolio positions from this text:

{text}

Return a JSON object with this exact format:
{{
  "positions": [
    {{
      "ticker": "MSFT",
      "company": "Microsoft",
      "shares": 500,
      "current_price": 420,
      "cost_basis": 350,
      "sector": "Technology"
    }}
  ],
  "cash": 50000,
  "tech_limit": 40,
  "esg_minimum": 55
}}

Extract ALL positions you can find. For prices, "current_price" is what it's "at" or "trading at" now. "cost_basis" is what was "bought" or "purchased" for.
Return ONLY valid JSON, no markdown or explanation."""

            response_text = self._call_gemini(prompt, max_tokens=2048)
            if not response_text:
                return {}
            
            # Extract JSON from response
            json_text = response_text.strip()
            
            # Remove markdown code blocks if present
            json_text = re.sub(r'```json\s*', '', json_text)
            json_text = re.sub(r'```\s*', '', json_text)
            
            data = json.loads(json_text)
            return data
            
        except Exception as e:
            logger.warning(f"Gemini full extraction failed: {e}")
        
        return {}


class GeminiEnhancedParser:
    """Parser with dynamic Gemini-powered learning"""
    
    def __init__(self, text: str):
        self.original_text = text
        self.text = text
        self.positions = []
        self.cash = 100000.0
        self.policy_limits = {}
        self.knowledge = DynamicKnowledgeBase()
        
    def parse(self) -> Portfolio:
        """Parse with fallback to Gemini"""
        # First try traditional parsing
        self._normalize_text()
        self._parse_line_by_line()
        
        # If we got very few positions, try Gemini full extraction
        if len(self.positions) < 2 and self.knowledge.gemini_client:
            logger.info("🤖 Using Gemini to extract portfolio data...")
            gemini_data = self.knowledge.extract_all_from_text(self.original_text)
            
            if gemini_data.get('positions'):
                self._create_positions_from_gemini(gemini_data)
        
        # Extract metadata
        self._extract_cash()
        self._extract_policy_limits()
        
        if not self.positions:
            raise ValueError("Could not find any stock positions in the text. Please include ticker symbols and prices.")
        
        return Portfolio(
            positions=self.positions,
            cash=self.cash,
            policy_limits=self.policy_limits
        )
    
    def _normalize_text(self):
        """Normalize company names to tickers"""
        # Try to normalize known companies
        for company in list(self.knowledge.company_tickers.keys()):
            ticker = self.knowledge.company_tickers[company]
            # Replace company names with tickers
            self.text = re.sub(
                rf'\b(\d+)\s+{company}\s+(shares?|at|@)',
                rf'\1 {ticker} \2',
                self.text,
                flags=re.IGNORECASE
            )
    
    def _parse_line_by_line(self):
        """Parse structured line format"""
        seen_tickers = set()
        lines = self.text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue
            
            position = self._extract_position_from_line(line)
            if position and position.ticker not in seen_tickers:
                self.positions.append(position)
                seen_tickers.add(position.ticker)
    
    def _extract_position_from_line(self, line: str) -> Optional[Position]:
        """Extract position with Gemini-enhanced data"""
        # Find ticker
        ticker_match = re.search(r'\b([A-Z]{2,5})\b', line)
        if not ticker_match:
            return None
        
        ticker = ticker_match.group(1)
        
        invalid = ['NOW', 'AT', 'THE', 'AND', 'FOR', 'WITH', 'FROM', 'TO', 'IN',
                   'OF', 'ON', 'PER', 'SHARE', 'BOUGHT', 'SOLD', 'PRICE', 'COST',
                   'CASH', 'TECH', 'ESG', 'MIN', 'MAX', 'LIMIT']
        if ticker in invalid:
            return None
        
        # Extract shares
        shares = None
        shares_patterns = [
            rf'(\d+)\s+{ticker}',
            rf'{ticker}[:\s]+(\d+)\s+shares',
            r'(\d+)\s+shares',
        ]
        
        for pattern in shares_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                shares = int(match.group(1))
                break
        
        if not shares or shares < 1:
            return None
        
        # Extract prices
        clean_line = line.replace(',', '').replace('$', ' ')
        
        at_match = re.search(r'(?:at|@)\s+(\d+\.?\d*)', clean_line, re.IGNORECASE)
        bought_match = re.search(r'(?:bought|purchased|paid)\s+(?:for|at)\s+(\d+\.?\d*)', clean_line, re.IGNORECASE)
        
        current_price = None
        cost_basis = None
        
        if at_match and bought_match:
            if at_match.start() < bought_match.start():
                current_price = float(at_match.group(1))
                cost_basis = float(bought_match.group(1))
            else:
                cost_basis = float(at_match.group(1))
                current_price = float(bought_match.group(1))
        elif at_match:
            current_price = float(at_match.group(1))
            cost_match = re.search(r'(?:cost|basis)\s+(\d+\.?\d*)', clean_line, re.IGNORECASE)
            if cost_match:
                cost_basis = float(cost_match.group(1))
        
        if not current_price:
            return None
        
        if not cost_basis:
            cost_basis = current_price
        
        # Get sector using Gemini if needed
        sector = self.knowledge.get_sector_for_ticker(ticker)
        
        # Get ESG score using Gemini if needed  
        esg_score = self.knowledge.get_esg_score(ticker)
        
        return Position(
            ticker=ticker,
            shares=shares,
            current_price=current_price,
            cost_basis=cost_basis,
            sector=sector,
            esg_score=esg_score,
            beta=1.0,
            acquisition_date=datetime.now() - timedelta(days=365)
        )
    
    def _create_positions_from_gemini(self, gemini_data: Dict):
        """Create positions from Gemini extraction"""
        for pos_data in gemini_data.get('positions', []):
            try:
                ticker = pos_data['ticker'].upper()
                sector = pos_data.get('sector', self.knowledge.get_sector_for_ticker(ticker))
                
                position = Position(
                    ticker=ticker,
                    shares=int(pos_data['shares']),
                    current_price=float(pos_data['current_price']),
                    cost_basis=float(pos_data.get('cost_basis', pos_data['current_price'])),
                    sector=sector,
                    esg_score=self.knowledge.get_esg_score(ticker),
                    beta=1.0,
                    acquisition_date=datetime.now() - timedelta(days=365)
                )
                
                self.positions.append(position)
                
            except Exception as e:
                logger.warning(f"Failed to create position from Gemini data: {e}")
        
        # Extract cash and limits
        if 'cash' in gemini_data:
            self.cash = float(gemini_data['cash'])
        if 'tech_limit' in gemini_data:
            self.policy_limits['technology_limit'] = float(gemini_data['tech_limit'])
        if 'esg_minimum' in gemini_data:
            self.policy_limits['esg_minimum'] = int(gemini_data['esg_minimum'])
    
    def _extract_cash(self):
        """Extract cash from text"""
        patterns = [
            r'cash\s+(\d+)',
            r'(\d+)\s+cash',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                self.cash = float(match.group(1))
                if 'k' in match.group(0).lower():
                    self.cash *= 1000
                elif 'm' in match.group(0).lower():
                    self.cash *= 1000000
                break
    
    def _extract_policy_limits(self):
        """Extract policy limits"""
        tech_match = re.search(r'tech(?:nology)?\s+(?:limit|max)\s+(\d+)', self.text, re.IGNORECASE)
        if tech_match:
            self.policy_limits['technology_limit'] = float(tech_match.group(1))
        
        esg_match = re.search(r'esg\s+(?:min|minimum)\s+(\d+)', self.text, re.IGNORECASE)
        if esg_match:
            self.policy_limits['esg_minimum'] = int(esg_match.group(1))


def parse_portfolio_text(text: str) -> Portfolio:
    """Main entry point - uses Gemini-enhanced parser"""
    parser = GeminiEnhancedParser(text)
    return parser.parse()


# Backward compatibility
def parse_number(s: str) -> float:
    """Parse number with k/m/b suffixes"""
    if not s or not s.strip():
        return 0.0
    
    s = s.strip().lower().replace(',', '')
    multiplier = 1.0
    
    if s.endswith('k'):
        multiplier = 1000
        s = s[:-1]
    elif s.endswith('m'):
        multiplier = 1000000
        s = s[:-1]
    elif s.endswith('b'):
        multiplier = 1000000000
        s = s[:-1]
    
    return float(s) * multiplier


if __name__ == "__main__":
    # Test with unknown companies
    test = """
500 Snowflake shares at 150, bought for 120
200 Palantir at 25, bought for 18
150 CrowdStrike at 280, bought for 200
Cash 100000
Tech limit 40
"""
    
    print("Testing Gemini-Enhanced Parser")
    print("="*70)
    
    try:
        portfolio = parse_portfolio_text(test)
        print(f"✅ Parsed {len(portfolio.positions)} positions\n")
        
        for p in portfolio.positions:
            print(f"{p.ticker}: {p.shares} shares @ ${p.current_price} (cost: ${p.cost_basis})")
            print(f"  Sector: {p.sector}, ESG: {p.esg_score}")
        
        print(f"\nCash: ${portfolio.cash:,.0f}")
        print(f"Policy Limits: {portfolio.policy_limits}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
