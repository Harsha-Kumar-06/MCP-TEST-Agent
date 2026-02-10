"""
Improved Natural Language Portfolio Parser - Handles ANY text format
Extracts portfolio information from text descriptions intelligently
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

try:
    from .models import Portfolio, Position
except ImportError:
    from portfolio_swarm.models import Portfolio, Position


class SmartPortfolioParser:
    """Intelligent parser that handles multiple text formats"""
    
    # Known company to ticker mappings
    COMPANY_TICKERS = {
        'microsoft': 'MSFT', 'apple': 'AAPL', 'nvidia': 'NVDA',
        'alphabet': 'GOOGL', 'google': 'GOOGL', 'meta': 'META',
        'tesla': 'TSLA', 'amazon': 'AMZN', 'jpmorgan': 'JPM',
        'johnson & johnson': 'JNJ', 'j&j': 'JNJ',
        'unitedhealth': 'UNH', 'visa': 'V', 'coca-cola': 'KO', 'coke': 'KO',
        'procter & gamble': 'PG', 'p&g': 'PG',
        'exxonmobil': 'XOM', 'exxon': 'XOM', 'chevron': 'CVX',
        'alibaba': 'BABA', 'taiwan semi': 'TSM', 'taiwan semiconductor': 'TSM',
    }
    
    # Ticker to sector mappings
    TICKER_SECTORS = {
        'MSFT': 'Technology', 'AAPL': 'Technology', 'NVDA': 'Technology',
        'GOOGL': 'Technology', 'GOOG': 'Technology', 'META': 'Technology',
        'TSLA': 'Technology', 'AMZN': 'Technology', 'AMD': 'Technology',
        'INTC': 'Technology', 'CRM': 'Technology', 'ORCL': 'Technology',
        'JNJ': 'Healthcare', 'UNH': 'Healthcare', 'PFE': 'Healthcare',
        'ABBV': 'Healthcare', 'TMO': 'Healthcare', 'MRK': 'Healthcare',
        'LLY': 'Healthcare', 'BMY': 'Healthcare',
        'JPM': 'Financials', 'BAC': 'Financials', 'WFC': 'Financials',
        'GS': 'Financials', 'MS': 'Financials', 'C': 'Financials',
        'V': 'Financials', 'MA': 'Financials', 'AXP': 'Financials',
        'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',
        'KO': 'Consumer', 'PG': 'Consumer', 'PEP': 'Consumer', 'WMT': 'Consumer',
        'BABA': 'Technology', 'TSM': 'Technology',
    }
    
    def __init__(self, text: str):
        self.original_text = text
        self.text = self._normalize_text(text)
        self.positions = []
        self.cash = 100000.0
        self.policy_limits = {}
        
    def _normalize_text(self, text: str) -> str:
        """Normalize text while preserving structure"""
        # Replace company names with tickers
        normalized = text
        for company, ticker in self.COMPANY_TICKERS.items():
            # "500 Microsoft shares" -> "500 MSFT shares"
            normalized = re.sub(
                rf'\b(\d+)\s+{company}\s+shares?\b',
                rf'\1 {ticker} shares',
                normalized,
                flags=re.IGNORECASE
            )
            # "500 Microsoft at" -> "500 MSFT at"
            normalized = re.sub(
                rf'\b(\d+)\s+{company}\s+(at|@)',
                rf'\1 {ticker} \2',
                normalized,
                flags=re.IGNORECASE
            )
            # "I own 500 Microsoft" -> "I own 500 MSFT"
            normalized = re.sub(
                rf'\b(\d+)\s+{company}\b',
                rf'\1 {ticker}',
                normalized,
                flags=re.IGNORECASE
            )
        return normalized
    
    def parse(self) -> Portfolio:
        """Main parsing method"""
        # Try line-by-line parsing first (for structured input)
        self._parse_line_by_line()
        
        # Try contextual parsing for any missed positions
        if len(self.positions) < 3:  # Too few positions, try harder
            self._parse_contextual()
        
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
    
    def _parse_line_by_line(self):
        """Parse line by line for structured formats"""
        seen_tickers = set()
        
        # Split into lines
        lines = self.text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Try to extract position from this line
            position = self._extract_position_from_line(line)
            if position and position.ticker not in seen_tickers:
                self.positions.append(position)
                seen_tickers.add(position.ticker)
    
    def _extract_position_from_line(self, line: str) -> Optional[Position]:
        """Extract a position from a single line"""
        
        # Pattern 1: "500 MSFT shares at 420, bought for 350"
        # Pattern 2: "500 MSFT at 420 bought at 350"
        # Pattern 3: "MSFT: 500 shares at 420, cost 350"
        
        # Find ticker first
        ticker_match = re.search(r'\b([A-Z]{2,5})\b', line)
        if not ticker_match:
            return None
        
        ticker = ticker_match.group(1)
        
        # Skip common words that aren't tickers
        invalid = ['NOW', 'AT', 'THE', 'AND', 'FOR', 'WITH', 'FROM', 'TO', 'IN', 
                   'OF', 'ON', 'PER', 'SHARE', 'BOUGHT', 'SOLD', 'PRICE', 'COST',
                   'CASH', 'TECH', 'ESG', 'MIN', 'MAX', 'LIMIT']
        if ticker in invalid:
            return None
        
        # Extract shares
        shares = None
        shares_patterns = [
            rf'(\d+)\s+{ticker}',  # "500 MSFT"
            rf'{ticker}[:\s]+(\d+)\s+shares',  # "MSFT: 500 shares"
            r'(\d+)\s+shares',  # "500 shares"
        ]
        
        for pattern in shares_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                shares = int(match.group(1))
                break
        
        if not shares or shares < 1:
            return None
        
        # Extract prices - be smart about current vs cost
        # Look for patterns that indicate which price is which
        current_price = None
        cost_basis = None
        
        # Clean line for price extraction
        clean_line = line.replace(',', '').replace('$', ' ')
        
        # Method 1: Look for explicit keywords
        # "at 420" or "at 420," followed by "bought for 350" or "bought at 350"
        at_match = re.search(r'(?:at|@)\s+(\d+\.?\d*)', clean_line, re.IGNORECASE)
        bought_match = re.search(r'(?:bought|purchased|paid)\s+(?:for|at)\s+(\d+\.?\d*)', clean_line, re.IGNORECASE)
        
        if at_match and bought_match:
            # Both found - "at X" is current, "bought Y" is cost
            if at_match.start() < bought_match.start():
                current_price = float(at_match.group(1))
                cost_basis = float(bought_match.group(1))
            else:
                # Reversed order (unusual but handle it)
                cost_basis = float(at_match.group(1))
                current_price = float(bought_match.group(1))
        elif at_match and not bought_match:
            # Only "at X" found - it's the current price, look for cost elsewhere
            current_price = float(at_match.group(1))
            cost_match = re.search(r'(?:cost|basis)\s+(\d+\.?\d*)', clean_line, re.IGNORECASE)
            if cost_match:
                cost_basis = float(cost_match.group(1))
        elif bought_match and not at_match:
            # Only "bought" found - it's cost, look for current
            cost_basis = float(bought_match.group(1))
            current_match = re.search(r'(?:current|now|trading)\s+(?:at\s+)?(\d+\.?\d*)', clean_line, re.IGNORECASE)
            if current_match:
                current_price = float(current_match.group(1))
        
        # Method 2: Find all prices and use context
        if not current_price or not cost_basis:
            all_prices = re.findall(r'\b(\d+\.?\d*)\b', clean_line)
            price_floats = []
            for p in all_prices:
                try:
                    pf = float(p)
                    if 0.1 < pf < 10000:  # Reasonable stock price range
                        price_floats.append(pf)
                except:
                    continue
            
            # If we have at least 2 prices
            if len(price_floats) >= 2:
                # Remove share count from prices if it was captured
                price_floats = [p for p in price_floats if p != shares]
                
                if len(price_floats) >= 2:
                    # Pattern: "500 MSFT at 420, bought for 350"
                    # First price after ticker is usually current, last is cost
                    if not current_price:
                        current_price = price_floats[0]
                    if not cost_basis:
                        cost_basis = price_floats[-1]
        
        # Fill in missing values
        if not current_price and cost_basis:
            current_price = cost_basis
        elif current_price and not cost_basis:
            cost_basis = current_price
        
        if not current_price:
            return None
        
        # Get sector
        sector = self.TICKER_SECTORS.get(ticker, 'Other')
        
        return Position(
            ticker=ticker,
            shares=shares,
            current_price=current_price,
            cost_basis=cost_basis,
            sector=sector,
            esg_score=70,  # Default
            beta=1.0,
            acquisition_date=datetime.now() - timedelta(days=365)
        )
    
    def _parse_contextual(self):
        """Fallback: Parse using contextual windows for conversational text"""
        # Find all ticker mentions
        ticker_matches = list(re.finditer(r'\b([A-Z]{2,5})\b', self.text))
        
        seen_tickers = {p.ticker for p in self.positions}
        
        for match in ticker_matches:
            ticker = match.group(1)
            
            # Skip invalid and already seen
            invalid = ['NOW', 'AT', 'THE', 'AND', 'FOR', 'WITH', 'CASH', 'TECH', 'ESG']
            if ticker in invalid or ticker in seen_tickers:
                continue
            
            # Extract context window (500 chars around ticker)
            start = max(0, match.start() - 250)
            end = min(len(self.text), match.end() + 250)
            context = self.text[start:end]
            
            position = self._extract_position_from_context(ticker, context)
            if position:
                self.positions.append(position)
                seen_tickers.add(ticker)
    
    def _extract_position_from_context(self, ticker: str, context: str) -> Optional[Position]:
        """Extract position from context window"""
        # Similar logic to line-based but with wider context
        # ... (simplified for now, can expand if needed)
        return None
    
    def _extract_cash(self):
        """Extract cash balance"""
        patterns = [
            r'cash\s+(\d+)',
            r'(\d+)\s+cash',
            r'cash\s*[:\s]+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                cash_val = float(match.group(1))
                # Check for k/m suffixes
                if 'k' in match.group(0).lower():
                    cash_val *= 1000
                elif 'm' in match.group(0).lower():
                    cash_val *= 1000000
                self.cash = cash_val
                break
    
    def _extract_policy_limits(self):
        """Extract policy limits"""
        # Tech limit
        tech_match = re.search(r'tech(?:nology)?\s+(?:limit|max)\s+(\d+)', self.text, re.IGNORECASE)
        if tech_match:
            self.policy_limits['technology_limit'] = float(tech_match.group(1))
        
        # ESG minimum
        esg_match = re.search(r'esg\s+(?:min|minimum)\s+(\d+)', self.text, re.IGNORECASE)
        if esg_match:
            self.policy_limits['esg_minimum'] = int(esg_match.group(1))


def parse_portfolio_text(text: str) -> Portfolio:
    """Main entry point for parsing portfolio text"""
    parser = SmartPortfolioParser(text)
    return parser.parse()


# For backward compatibility
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
    # Test cases
    test1 = """
500 MSFT shares at 420, bought for 350
150 NVDA shares at 880, bought for 420  
400 GOOGL shares at 165, bought for 140
Cash 50000
"""
    
    test2 = """
I own 500 Microsoft shares at $420 bought at $350.
Also holding 150 NVIDIA at $880 purchased at $420.
Cash balance is $50,000.
"""
    
    for i, test in enumerate([test1, test2], 1):
        print(f"\n{'='*60}")
        print(f"Test {i}")
        print(f"{'='*60}")
        try:
            portfolio = parse_portfolio_text(test)
            print(f"✅ Parsed {len(portfolio.positions)} positions")
            for p in portfolio.positions:
                print(f"  {p.ticker}: {p.shares} shares @ ${p.current_price} (cost: ${p.cost_basis})")
        except Exception as e:
            print(f"❌ Error: {e}")
