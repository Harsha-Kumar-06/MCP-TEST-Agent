"""
Natural Language Portfolio Parser
Extracts portfolio information from text descriptions
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

try:
    from .models import Portfolio, Position
except ImportError:
    from portfolio_swarm.models import Portfolio, Position


def parse_portfolio_text(text: str) -> Portfolio:
    """
    Parse portfolio from natural language text using contextual understanding.
    
    Strategy:
    1. Find all ticker references (Company (TICKER))
    2. Extract surrounding context for each ticker  
    3. Use semantic keywords to find shares, purchase price, current price
    4. Fall back to pattern matching if contextual parsing insufficient
    
    Args:
        text: Natural language description of portfolio
        
    Returns:
        Portfolio object
        
    Examples:
        "I own 10,000 AAPL at $185 (bought at $150), cash $500k"
        "Portfolio: AAPL 10k shares, current $185, basis $150"
    """
    positions = []
    cash = 100000.0  # Default
    policy_limits = {}
    
    # Clean and normalize text
    original_text = text
    
    # First, extract company name-to-ticker mappings
    company_ticker_map = {}
    company_patterns = [
        r'(\d+)\s+(Microsoft|Apple|NVIDIA|Alphabet|Google|Meta|Tesla|Amazon|JPMorgan|Johnson\s+&\s+Johnson|UnitedHealth|Visa|Coca-Cola|Procter\s+&\s+Gamble|ExxonMobil|Chevron|Alibaba|Taiwan\s+Semi(?:conductor)?)\s+(?:\(([A-Z]{2,5})\)|shares?)',
        r'(Microsoft|Apple|NVIDIA|Alphabet|Google|Meta|Tesla|Amazon|JPMorgan|Johnson\s+&\s+Johnson|UnitedHealth|Visa|Coca-Cola|Procter\s+&\s+Gamble|ExxonMobil|Chevron|Alibaba|Taiwan\s+Semi(?:conductor)?)\s+\(([A-Z]{2,5})\)',
    ]
    
    # Known company name to ticker mapping
    known_companies = {
        'microsoft': 'MSFT',
        'apple': 'AAPL',
        'nvidia': 'NVDA',
        'alphabet': 'GOOGL',
        'google': 'GOOGL',
        'meta': 'META',
        'tesla': 'TSLA',
        'amazon': 'AMZN',
        'jpmorgan': 'JPM',
        'johnson & johnson': 'JNJ',
        'unitedhealth': 'UNH', 
        'visa': 'V',
        'coca-cola': 'KO',
        'procter & gamble': 'PG',
        'exxonmobil': 'XOM',
        'chevron': 'CVX',
        'alibaba': 'BABA',
        'taiwan semi': 'TSM',
        'taiwan semiconductor': 'TSM',
    }
    
    # Replace company names with tickers in the text for easier parsing
    for company, ticker in known_companies.items():
        # Look for \"X CompanyName\" patterns and convert to \"X TICKER\"
        text = re.sub(rf'\\b(\\d+)\\s+{company}\\b', rf'\\1 {ticker}', text, flags=re.IGNORECASE)
        # Look for \"CompanyName at\" patterns  
        text = re.sub(rf'\\b{company}\\s+(at|@)', rf'{ticker} \\1', text, flags=re.IGNORECASE)        # Look for "X shares of CompanyName" patterns
        text = re.sub(rf'(\d+)\s+shares\s+of\s+{company}\b', rf'\1 {ticker} shares', text, flags=re.IGNORECASE)
        # Look for "CompanyName shares" patterns
        text = re.sub(rf'\b{company}\s+shares', rf'{ticker} shares', text, flags=re.IGNORECASE)    
    text = text.replace(',', '')  # Remove commas from numbers
    text = text.replace('$', ' ')  # Space out dollar signs
    
    # Extract cash balance
    cash_patterns = [
        r'(\d+\.?\d*)[kKmM]\s+cash',  # "2M cash" or "500k cash"
        r'cash[:\s]+(\d+\.?\d*)[kKmM]?',
        r'(\d+\.?\d*)[kKmM]?\s+in cash',
        r'cash balance[:\s]+(\d+\.?\d*)[kKmM]?',
        r'available[:\s]+(\d+\.?\d*)[kKmM]?'
    ]
    
    for pattern in cash_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cash_str = match.group(1)
            cash = parse_number(cash_str)
            # Check for k/m/b suffix
            if 'k' in match.group(0).lower():
                cash *= 1000
            elif 'm' in match.group(0).lower():
                cash *= 1000000
            break
    
    # Extract policy limits
    tech_limit_match = re.search(r'tech(?:nology)?\s+(?:under|below|limit|max)?\s*(\d+)%?', text, re.IGNORECASE)
    if tech_limit_match:
        policy_limits['technology_limit'] = float(tech_limit_match.group(1))
    
    esg_min_match = re.search(r'(?:minimum|min)\s+esg\s+(?:score)?\s*[:\s]*(\d+)', text, re.IGNORECASE)
    if esg_min_match:
        policy_limits['esg_minimum'] = int(esg_min_match.group(1))
    
    # === CONTEXTUAL PARSING APPROACH ===
    # Step 1: Find all ticker references and their context
    seen_tickers = set()
    
    # Multiple ticker patterns to catch different formats - EXPANDED
    ticker_patterns = [
        (r'(?:Position\s+\d+:.*?)?\(([A-Z]{2,5})\)', 1),  # Company (TICKER) - priority 1
        (r'-\s+([A-Z]{2,5}):\s+', 2),  # - TICKER: format - priority 2
        (r'\b(\d+)\s+([A-Z]{2,5})\s+(?:shares?|at|@)', 3),  # "500 MSFT shares" or "500 MSFT at" - priority 3
        (r'\b([A-Z]{2,5})\s+(?:at|@)\s+\$?\d+', 4),  # "MSFT at $420" - priority 4
        (r'\b([A-Z]{2,5})\s+[A-Z][a-z]+\s+at', 5),  # "MSFT Microsoft at" - priority 5
    ]
    
    ticker_info = []  # (position, ticker, priority)
    for pattern, priority in ticker_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Handle patterns with 2 groups (shares + ticker)
            if len(match.groups()) >= 2:
                ticker = match.group(2).upper()
            else:
                ticker = match.group(1).upper()
            
            # Filter out invalid tickers and common words - COMPREHENSIVE
            invalid_tickers = ['NOW', 'AT', 'THE', 'AND', 'FOR', 'WITH', 'FROM', 'TO', 'IN', 
                              'OF', 'ON', 'PER', 'SHARE', 'BOUGHT', 'SOLD', 'PRICE', 'COST',
                              'ALSO', 'PLUS', 'HAVE', 'OWN', 'OWNS', 'HELD', 'HOLDS', 'MY',
                              'WHICH', 'THAT', 'THIS', 'THESE', 'THOSE', 'THEM', 'THEIR',
                              'CASH', 'TOTAL', 'VALUE', 'BASIS', 'PAID', 'STOCK', 'STOCKS']
            
            # Valid ticker: 2-5 chars, not in invalid list, contains at least one consonant
            if (2 <= len(ticker) <= 5 and 
                ticker not in invalid_tickers and
                any(c in ticker for c in 'BCDFGHJKLMNPQRSTVWXYZ')):  # Has consonant
                ticker_info.append((match.start(), ticker, priority))
    
    # Sort by position, then by priority (lower priority number = higher priority)
    ticker_info.sort(key=lambda x: (x[0], x[2]))
    
    # Remove duplicates keeping first occurrence
    seen_positions = {}
    unique_tickers = []
    for pos, ticker, priority in ticker_info:
        if ticker not in seen_positions:
            seen_positions[ticker] = pos
            unique_tickers.append((pos, ticker))
    
    for start_pos, ticker in unique_tickers:
        if ticker in seen_tickers:
            continue
        
        # Extract context - for dash format use line, otherwise use ~600 chars
        # Check if this is dash format by looking at text around ticker
        is_dash_format = text[max(0, start_pos-2):start_pos+10].strip().startswith('-')
        
        if is_dash_format:
            # For dash format, extract just this line
            line_start = text.rfind('\n', 0, start_pos) + 1
            line_end = text.find('\n', start_pos)
            if line_end == -1:
                line_end = len(text)
            context = text[line_start:line_end]
        else:
            # For other formats, use wider context window
            end_pos = min(start_pos + 600, len(text))
            context = text[start_pos:end_pos]
        
        # Step 2: Extract shares using contextual verbs (more flexible patterns)
        shares = None
        share_patterns = [
            r'(\d+[,\d]*)\s+shares',  # Most common format with commas
            r'(?:purchased|bought|own|holding|hold|have)\s+(\d+[,\d]*)',
            r'(\d+[,\d]*)\s+' + re.escape(ticker),  # "500 MSFT"
            ticker + r'[^\d]+(\d+[,\d]*)\s+shares',  # "MSFT 500 shares"
        ]
        for pattern in share_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                shares_str = match.group(1).replace(',', '')
                shares = int(shares_str)
                break
        
        if not shares:
            continue
        
        # Step 3: Extract prices using IMPROVED semantic analysis
        cost_basis = None
        current_price = None
        
        # Find ALL numbers that could be prices with their positions
        price_matches = list(re.finditer(r'\$?(\d+\.?\d*)', context))
        all_prices = []
        for m in price_matches:
            try:
                p = float(m.group(1))
                if 0.01 < p < 10000:  # Reasonable stock price range
                    all_prices.append((p, m.start(), m.end()))
            except:
                continue
        
        # Strategy: Look for specific patterns FIRST, then fallback
        # Pattern 1: "at X bought/purchased at/for Y" - X is current, Y is cost
        pattern1 = re.search(r'(?:at|@)\s+\$?(\d+\.?\d*).*?(?:bought|purchased).*?(?:at|for)\s+\$?(\d+\.?\d*)', context, re.IGNORECASE)
        if pattern1:
            current_price = float(pattern1.group(1))
            cost_basis = float(pattern1.group(2))
        
        # Pattern 2: "bought/purchased at X, currently/now Y" - X is cost, Y is current
        if not current_price:
            pattern2 = re.search(r'(?:bought|purchased).*?(?:at|for)\s+\$?(\d+\.?\d*).*?(?:currently|now|trading).*?(?:at)?\s+\$?(\d+\.?\d*)', context, re.IGNORECASE)
            if pattern2:
                cost_basis = float(pattern2.group(1))
                current_price = float(pattern2.group(2))
        
        # Pattern 3: "at X, bought/paid Y" or "at X, cost Y" - X is current, Y is cost
        if not current_price:
            pattern3 = re.search(r'(?:at|@)\s+\$?(\d+\.?\d*)[,;].*?(?:bought|purchased|paid|cost)\s+(?:for)?\s*\$?(\d+\.?\d*)', context, re.IGNORECASE)
            if pattern3:
                current_price = float(pattern3.group(1))
                cost_basis = float(pattern3.group(2))
        
        # Only if no patterns matched, use keyword extraction
        if not cost_basis:
            cost_patterns = [
                r'(?:bought|purchased)\s+(?:at|for)\s+\$?(\d+\.?\d*)',
                r'(?:cost|paid)\s+(?:basis)?\s*\$?(\d+\.?\d*)',
                r'basis\s+\$?(\d+\.?\d*)',
            ]
            for pattern in cost_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    cost_basis = float(match.group(1))
                    break
        
        if not current_price:
            current_patterns = [
                r'(?:currently|now)\s+(?:trading\s+)?(?:at\s+)?\$?(\d+\.?\d*)',
                r'current(?:ly)?\s+(?:price\s+)?\s*\$?(\d+\.?\d*)',
                r'trading\s+at\s+\$?(\d+\.?\d*)',
            ]
            for pattern in current_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    current_price = float(match.group(1))
                    break
        
        # Last resort: if we have just "at X" without buy keywords, it's probably current
        if not current_price and not cost_basis and len(all_prices) >= 1:
            at_match = re.search(r'(?:at|@)\s+\$?(\d+\.?\d*)', context, re.IGNORECASE)
            if at_match:
                current_price = float(at_match.group(1))
                # Find another price for cost
                for p, start, end in all_prices:
                    if abs(p - current_price) > 1:
                        cost_basis = p
                        break
        
        # Final fallback: use same price for both
        if current_price and not cost_basis:
            cost_basis = current_price
        elif cost_basis and not current_price:
            current_price = cost_basis
        elif not current_price and not cost_basis and len(all_prices) >= 1:
            # Just use first price for both
            current_price = cost_basis = all_prices[0][0]
            
        if not shares or not current_price:
            continue
        
        # Step 4: Extract acquisition date from phrases like "320 days ago", "45 days ago"
        acquisition_date = None
        date_patterns = [
            r'(\d+)\s+days\s+ago',
            r'just\s+(\d+)\s+days\s+ago',
            r'(\d+)\s+months?\s+ago',
            r'(\d+)\s+years?\s+ago',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                days = int(match.group(1))
                if 'month' in pattern:
                    days *= 30
                elif 'year' in pattern:
                    days *= 365
                from datetime import datetime, timedelta
                acquisition_date = datetime.now() - timedelta(days=days)
                break
        
        # Step 5: Extract metadata (sector, ESG, beta)
        sector = "Unknown"
        esg_score = 0
        beta = 1.0
        
        # Extract sector - try with and without "sector" keyword
        sector_keywords = r'(Technology|Healthcare|Finance|Financial|Energy|Consumer|Auto|Tobacco|Automotive)'
        sector_match = re.search(sector_keywords + r'\s+sector', context, re.IGNORECASE)
        if not sector_match:
            # Try without "sector" keyword - look for sector name followed by comma or ESG
            sector_match = re.search(sector_keywords + r'[\s,]+(?:ESG|esg|$)', context, re.IGNORECASE)
        if sector_match:
            sector_name = sector_match.group(1).capitalize()
            # Normalize variants
            if sector_name in ['Financial', 'Finance']:
                sector = 'Finance'
            elif sector_name in ['Automotive', 'Auto']:
                sector = 'Auto'
            else:
                sector = sector_name
        
        # Extract ESG score
        esg_match = re.search(r'ESG\s+(?:score\s+)?(?:is\s+)?(?:only\s+)?(\d+)', context, re.IGNORECASE)
        if esg_match:
            esg_score = int(esg_match.group(1))
        
        # Extract beta
        beta_match = re.search(r'beta\s+(\d+\.?\d*)', context, re.IGNORECASE)
        if beta_match:
            beta = float(beta_match.group(1))
        
        # Create position with all metadata
        positions.append(Position(
            ticker=ticker,
            shares=shares,
            cost_basis=cost_basis,
            current_price=current_price,
            acquisition_date=acquisition_date,
            sector=sector,
            esg_score=esg_score,
            beta=beta
        ))
        seen_tickers.add(ticker)
    
    # If contextual parsing found positions, return them (no minimum threshold)
    # Contextual parser is more accurate than pattern fallback
    if len(positions) > 0:
        return Portfolio(positions=positions, cash=cash, policy_limits=policy_limits)
    
    # === FALLBACK TO PATTERN MATCHING (only if contextual found nothing) ===
    positions = []
    seen_tickers = set()
    
    # Extract positions - multiple patterns (ordered by specificity)
    position_patterns = [
        # NEW: "Bought X AAPL shares...at Y...currently trading at Z" (use lazy .*? and skip intermediate numbers)
        r'[Bb]ought\s+(\d+)\s+([A-Z]{2,5})\s+shares.*?at.*?(\d+\.?\d*).*?(?:currently trading|trading).*?(\d+\.?\d*)',
        
        # NEW: "Own X META shares purchased...at Y...now at Z"  
        r'[Oo]wn\s+(\d+)\s+([A-Z]{2,5})\s+shares.*?at.*?(\d+\.?\d*).*?now.*?(\d+\.?\d*)',
        
        # "Position X: Company (TICKER)\n...purchased/bought X shares...at $Y...Current/currently/now...at/to $Z"
        r'Position\s+\d+:.*?\(([A-Z]{2,5})\).*?(?:purchased|bought)\s+([\d,]+)\s+shares[^\d]*(?:at|for)[^\d]*(\d+\.?\d*)[^\d]*(?:[Cc]urrent|currently|now)[^\d]*(?:at|to)[^\d]*(\d+\.?\d*)',
        
        # Pattern 1: "(NVDA)\nI purchased 25000 shares...at 420 per share...Current price...to 875"
        r'\(([A-Z]{2,5})\).*?purchased\s+([\d,]+)\s+shares.*?(\d+\.?\d*)\s+per\s+share.*?[Cc]urrent\s+price.*?(\d+\.?\d*)',
        
        # Pattern 2: "Bought 18,000 AAPL shares at $165, currently trading at $185"
        r'[Bb]ought\s+([\d,]+)\s+([A-Z]{2,5})\s+shares[^\d]*(\d+\.?\d*)[^\d]*currently\s+trading[^\d]*(\d+\.?\d*)',
        
        # Pattern 3: "Own 12,000 META shares purchased at $485, now at $512"
        r'[Oo]wn\s+([\d,]+)\s+([A-Z]{2,5})\s+shares\s+purchased[^\d]*(\d+\.?\d*)[^\d]*now[^\d]*(\d+\.?\d*)',
        
        # Pattern 4: "(TSLA)\n5,000 shares bought at $280, currently $245"
        r'\(([A-Z]{2,5})\)[^\d]+([\d,]+)\s+shares\s+bought[^\d]*(\d+\.?\d*)[^\d]*currently[^\d]*(\d+\.?\d*)',
        
        # Pattern 5: "Purchased 8,000 JPM shares at $140, currently $185"
        r'[Pp]urchased\s+([\d,]+)\s+([A-Z]{2,5})\s+shares[^\d]*(\d+\.?\d*)[^\d]*currently[^\d]*(\d+\.?\d*)',
        
        # Pattern 6: "(XOM)\nBought 15,000 XOM shares at $95, currently trading at $108"
        r'\(([A-Z]{2,5})\)[^\d]*[Bb]ought\s+([\d,]+)\s+([A-Z]{2,5})\s+shares[^\d]*(\d+\.?\d*)[^\d]*currently\s+trading[^\d]*(\d+\.?\d*)',
        
        # Pattern 7: "(MO)\nOwn 10,000 shares purchased at $42, now at $48"
        r'\(([A-Z]{2,5})\)[^\d]*[Oo]wn\s+([\d,]+)\s+shares\s+purchased[^\d]*(\d+\.?\d*)[^\d]*now[^\d]*(\d+\.?\d*)',
        
        # Pattern 8: "(JNJ)\n...Bought 12,000 shares at $155, currently trading at $162"
        r'\(([A-Z]{2,5})\)[^\d]*[Bb]ought\s+([\d,]+)\s+shares[^\d]*(\d+\.?\d*)[^\d]*currently\s+trading[^\d]*(\d+\.?\d*)',
        
        # Pattern 9: "(PFE)\nOwn 25,000 shares purchased at $35, currently trading at $28.50"
        r'\(([A-Z]{2,5})\)[^\d]*[Oo]wn\s+([\d,]+)\s+shares\s+purchased[^\d]*(\d+\.?\d*)[^\d]*currently\s+trading[^\d]*(\d+\.?\d*)',
        
        # Pattern 10: "(COIN)\n...Bought 3,000 shares at $180, currently trading at $95"
        r'\(([A-Z]{2,5})\)[^\d]*[Bb]ought\s+([\d,]+)\s+shares[^\d]*(\d+\.?\d*)[^\d]*currently\s+trading[^\d]*(\d+\.?\d*)',
        
        # SIMPLE FORMATS BELOW
        
        # Pattern 11: "I own 10000 shares of Apple (AAPL) bought at $150, now at $185"
        r'[Oo]wn\s+([\d,]+)\s+shares\s+of\s+\w+\s+\(([A-Z]{2,5})\)\s+bought[^\d]*(\d+\.?\d*)[^\d]+now[^\d]*(\d+\.?\d*)',
        
        # Pattern 12: "5000 Microsoft (MSFT) shares, cost basis $350, current price $410"
        r'([\d,]+)\s+\w+\s+\(([A-Z]{2,5})\)\s+shares[^\d]*cost\s+basis[^\d]*(\d+\.?\d*)[^\d]*current\s+price[^\d]*(\d+\.?\d*)',
        
        # Pattern 13: "AAPL: 10k shares, purchased at $150, currently $185"
        r'([A-Z]{2,5}):\s*([\d,]+[kKmM]?)\s+shares[^\d]*purchased[^\d]+(\d+\.?\d*)[^\d]+currently[^\d]*(\d+\.?\d*)',
        
        # Pattern 14: "MSFT: 5k shares, cost $350, now $410"
        r'([A-Z]{2,5}):\s*([\d,]+[kKmM]?)\s+shares[^\d]*cost[^\d]+(\d+\.?\d*)[^\d]+now[^\d]*(\d+\.?\d*)',
        
        # Pattern 15: "JNJ: 8000 shares, basis $155, price $162"
        r'([A-Z]{2,5}):\s*([\d,]+[kKmM]?)\s+shares[^\d]*basis[^\d]+(\d+\.?\d*)[^\d]+price[^\d]*(\d+\.?\d*)',
        
        # Pattern 16: "15000 AAPL @ $185 (bought for $140)"
        r'([\d,]+[kKmM]?)\s+([A-Z]{2,5})\s+@[^\d]*(\d+\.?\d*)\s*\([^\d$]*\$?(\d+\.?\d*)\)',
        
        # Pattern 17: "8000 MSFT shares at $410, paid $305" (comma is stripped by preprocessing)
        r'([\d,]+[kKmM]?)\s+([A-Z]{2,5})\s+shares\s+at[^\d]+(\d+\.?\d*)[^\d]*paid[^\d]+(\d+\.?\d*)',
        
        # Pattern 18: "3000 Tesla at $245" (no cost basis, must not be followed by comma/paid)
        r'([\d,]+[kKmM]?)\s+([A-Z][A-Za-z]{1,4})\s+at[^\d]+(\d+\.?\d*)(?![^\n]*paid)',
    ]
    
    # Keep track of what we've seen to avoid duplicates
    seen_tickers = set()
    
    for pattern in position_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        match_list = list(matches)
        for match in match_list:
            try:
                groups = match.groups()
                matched_text = match.group(0).lower()
                
                # Parse based on pattern - check which has ticker first
                if re.match(r'[A-Z]', groups[0]):  # Ticker is first group
                    ticker = groups[0]
                    shares_str = groups[1]
                    # Determine if pattern has 4 or 5 groups (pattern 6 has extra ticker)
                    if len(groups) == 5:  # Pattern 6: (XOM) Bought 15000 XOM shares...
                        cost_basis_str = groups[3]
                        current_price_str = groups[4]
                    else:
                        # For ticker-first patterns: cost basis then current price
                        cost_basis_str = groups[2]
                        current_price_str = groups[3] if len(groups) > 3 else groups[2]
                else:  # Shares is first group
                    shares_str = groups[0]
                    ticker = groups[1]
                    
                    # Skip common words that aren't valid tickers
                    if ticker.upper() in ['NOW', 'AT', 'THE', 'AND', 'FOR', 'WITH', 'FROM', 'TO', 'IN', 'OF', 'ON']:
                        continue
                    
                    # Determine price order based on keywords in matched text
                    # If "bought...currently" or "purchased...currently" → cost first, current second
                    # If "@ $...bought" or "at $...paid" → current first, cost second
                    if re.search(r'(bought|purchased).*?(currently|now)', matched_text):
                        # Pattern: "bought at $150...currently $185" → groups[2]=cost, groups[3]=current
                        cost_basis_str = groups[2]
                        current_price_str = groups[3] if len(groups) > 3 else groups[2]
                    elif re.search(r'@.*?\(.*?bought|at.*?paid', matched_text):
                        # Pattern: "@ $185 (bought $140)" or "at $410, paid $305" → groups[2]=current, groups[3]=cost
                        current_price_str = groups[2]
                        cost_basis_str = groups[3] if len(groups) > 3 else groups[2]
                    elif 'cost' in matched_text and ('current' in matched_text or 'now' in matched_text):
                        # Pattern: "cost basis $350, current price $410" → groups[2]=cost, groups[3]=current
                        cost_basis_str = groups[2]
                        current_price_str = groups[3] if len(groups) > 3 else groups[2]
                    else:
                        # Default: current price then cost basis
                        current_price_str = groups[2]
                        cost_basis_str = groups[3] if len(groups) > 3 else groups[2]
                
                # Skip if we've already processed this ticker
                if ticker.upper() in seen_tickers:
                    continue
                
                # Parse numbers safely
                shares = int(parse_number(shares_str))
                current_price = float(parse_number(current_price_str))
                cost_basis = float(parse_number(cost_basis_str)) if cost_basis_str and cost_basis_str.strip() else current_price
                
                # Skip if invalid
                if shares <= 0 or current_price <= 0:
                    continue
                
                # Try to extract additional info for this ticker
                sector = extract_sector(text, ticker)
                esg_score = extract_esg(text, ticker)
                acquisition_date = extract_date(text, ticker)
                
                # Create position
                position = Position(
                    ticker=ticker.upper(),
                    shares=shares,
                    current_price=current_price,
                    cost_basis=cost_basis,
                    acquisition_date=acquisition_date,
                    sector=sector,
                    esg_score=esg_score,
                    beta=1.0  # Default
                )
                
                positions.append(position)
                seen_tickers.add(ticker.upper())
                
            except (ValueError, IndexError) as e:
                # Skip this match if parsing fails
                continue
    
    if not positions:
        raise ValueError("Could not find any stock positions in the text. Please include ticker symbols and prices.")
    
    return Portfolio(
        positions=positions,
        cash=cash,
        policy_limits=policy_limits
    )


def parse_number(s: str) -> float:
    """Parse number with k/m/b suffixes and commas"""
    if not s or not s.strip():
        return 0.0
    
    s = s.strip().lower().replace(',', '')  # Remove commas
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


def extract_sector(text: str, ticker: str) -> str:
    """Try to extract sector for a ticker from text"""
    sectors = ['Technology', 'Healthcare', 'Finance', 'Financials', 'Energy', 
               'Consumer', 'Industrials', 'Utilities', 'Real Estate', 'Materials']
    
    # Look for sector near the ticker
    ticker_pos = text.upper().find(ticker.upper())
    if ticker_pos >= 0:
        # Check 100 chars before and after ticker
        context = text[max(0, ticker_pos-100):min(len(text), ticker_pos+100)]
        for sector in sectors:
            if sector.lower() in context.lower():
                return sector
    
    # Default based on common tickers
    tech_tickers = ['AAPL', 'MSFT', 'GOOGL', 'GOOG', 'META', 'NVDA', 'AMD', 'INTC', 'TSLA']
    health_tickers = ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'LLY']
    finance_tickers = ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C']
    energy_tickers = ['XOM', 'CVX', 'COP', 'SLB']
    
    if ticker.upper() in tech_tickers:
        return 'Technology'
    elif ticker.upper() in health_tickers:
        return 'Healthcare'
    elif ticker.upper() in finance_tickers:
        return 'Financials'
    elif ticker.upper() in energy_tickers:
        return 'Energy'
    
    return 'Other'


def extract_esg(text: str, ticker: str) -> int:
    """Try to extract ESG score for a ticker from text"""
    # Look for "AAPL ESG 75" or "ESG 75" near ticker
    patterns = [
        rf'{ticker}\s+ESG[:\s]+(\d+)',
        rf'ESG[:\s]+(\d+)\s+{ticker}',
        rf'{ticker}[^\d]*ESG[^\d]*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 0 <= score <= 100:
                return score
    
    return 70  # Default


def extract_date(text: str, ticker: str) -> datetime:
    """Try to extract acquisition date for a ticker from text"""
    # Look for dates near ticker
    date_patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # 2023-06-15
        r'(\d{2})/(\d{2})/(\d{4})',  # 06/15/2023
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',  # June 2023
        r'bought\s+(\d+)\s+days?\s+ago',
        r'purchased\s+(\d+)\s+months?\s+ago',
    ]
    
    ticker_pos = text.upper().find(ticker.upper())
    if ticker_pos >= 0:
        context = text[max(0, ticker_pos-100):min(len(text), ticker_pos+100)]
        
        for pattern in date_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                if 'ago' in pattern:
                    days = int(match.group(1))
                    if 'month' in pattern:
                        days *= 30
                    return datetime.now() - timedelta(days=days)
                elif len(match.groups()) == 3:
                    try:
                        if '-' in pattern:
                            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                        else:
                            return datetime(int(match.group(3)), int(match.group(1)), int(match.group(2)))
                    except:
                        pass
    
    # Default to 1 year ago
    return datetime.now() - timedelta(days=365)


# Example usage
if __name__ == "__main__":
    # Test examples
    examples = [
        """
        I own 10000 shares of Apple (AAPL) bought at $150, now at $185.
        Also have 5000 Microsoft (MSFT) shares, cost basis $350, current price $410.
        Cash balance: $500000
        """,
        
        """
        Portfolio:
        - AAPL: 10k shares, purchased at $150, currently $185, Technology, ESG 75
        - MSFT: 5k shares, cost $350, now $410, Tech sector, ESG 82
        - JNJ: 8000 shares, basis $155, price $162, Healthcare, ESG 72
        
        Cash: $1m
        Keep technology under 30%
        Minimum ESG score: 65
        """,
        
        """
        My tech portfolio: 
        15000 AAPL @ $185 (bought for $140)
        8000 MSFT shares at $410, paid $305
        3000 Tesla at $245
        $2M cash
        Tech limit 35%
        """
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{'='*60}")
        print(f"EXAMPLE {i}")
        print(f"{'='*60}")
        print(f"Input:\n{example}")
        
        try:
            portfolio = parse_portfolio_text(example)
            print(f"\n✅ Parsed successfully!")
            print(f"Positions: {len(portfolio.positions)}")
            print(f"Cash: ${portfolio.cash:,.0f}")
            print(f"Policy limits: {portfolio.policy_limits}")
            print(f"\nPositions:")
            for pos in portfolio.positions:
                print(f"  - {pos.ticker}: {pos.shares:,} shares @ ${pos.current_price:.2f} "
                      f"(cost: ${pos.cost_basis:.2f}, sector: {pos.sector})")
        except Exception as e:
            print(f"\n❌ Error: {e}")
