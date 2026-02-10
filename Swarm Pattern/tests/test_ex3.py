from portfolio_swarm.text_parser import parse_portfolio_text

text = '''My tech portfolio:
15000 AAPL @ $185 (bought for $140)
8000 MSFT shares at $410, paid $305
3000 Tesla at $245
$2M cash
Tech limit 35%'''

print(f"Input:\n{text}\n")

portfolio = parse_portfolio_text(text)

print(f"Result: {len(portfolio.positions)} positions, ${portfolio.cash:,.0f} cash")
for pos in portfolio.positions:
    print(f"  {pos.ticker}: {pos.shares} shares @ ${pos.current_price} (cost ${pos.cost_basis})")
