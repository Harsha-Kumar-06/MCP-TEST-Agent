from portfolio_swarm.text_parser import parse_portfolio_text
import re

text = """- AAPL: 15000 shares, purchased at 150, currently 185, Technology sector, ESG score 75
- MSFT: 8000 shares, bought at 350, now 410, Technology, ESG 82
- JNJ: 10000 shares, cost basis 155, current 162, Healthcare, ESG 72"""

# Simulate what the parser does
text_clean = text.replace(',', '').replace('$', ' ')
print("=== CLEANED TEXT ===")
print(text_clean)
print()

# Find tickers
ticker_pattern = r'-\s+([A-Z]{2,5}):\s+'
tickers = re.findall(ticker_pattern, text_clean)
print(f"=== FOUND TICKERS: {tickers} ===\n")

for ticker in tickers:
    # Find line for this ticker
    line_pattern = f'-\\s+{ticker}:.*'
    line_match = re.search(line_pattern, text_clean)
    if line_match:
        context = line_match.group(0)
        print(f"--- {ticker} ---")
        print(f"Context: {context}")
        
        # Extract shares
        shares = re.search(r'(\d+)\s+shares', context, re.I)
        print(f"Shares: {shares.group(1) if shares else 'NONE'}")
        
        # Extract cost
        cost = None
        for p in [r'purchased.*?at\s+(\d+)', r'bought.*?at\s+(\d+)', r'basis\s+(\d+)']:
            m = re.search(p, context, re.I)
            if m:
                cost = m.group(1)
                break
        print(f"Cost: {cost}")
        
        # Extract current
        current = None
        for p in [r'currently\s+(\d+)', r'now\s+(\d+)', r'current\s+(\d+)']:
            m = re.search(p, context, re.I)
            if m:
                current = m.group(1)
                break
        print(f"Current: {current}")
        
        # Extract ESG
        esg = re.search(r'ESG\s+(?:score\s+)?(\d+)', context, re.I)
        print(f"ESG: {esg.group(1) if esg else 'NONE'}")
        
        print()

print("\n=== ACTUAL PARSER RESULT ===")
portfolio = parse_portfolio_text(text)
for p in portfolio.positions:
    print(f"{p.ticker}: {p.shares} shares @ ${p.current_price} (cost ${p.cost_basis}), {p.sector}, ESG {p.esg_score}")
