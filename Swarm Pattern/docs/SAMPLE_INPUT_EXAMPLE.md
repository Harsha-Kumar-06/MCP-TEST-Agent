# Sample Text Input & Expected Results

This document provides a sample text description for testing the Portfolio Swarm Optimizer.

---

## Sample Text Input

Copy and paste this into the **"Enter Text Description"** input field:

```
My Investment Portfolio:

I have $50,000 invested in Apple (AAPL) which I bought at $150 per share, now worth $185.
I also hold 200 shares of Microsoft (MSFT) purchased at $280, currently trading at $420.
My Tesla (TSLA) position is 100 shares bought at $200, now at $175 (down unfortunately).
I have $25,000 in Amazon (AMZN) stock, bought at $130, now at $178.
Finally, I own 500 shares of NVIDIA (NVDA) purchased at $450, currently at $890.

My risk tolerance is moderate and I'm investing for long-term growth over 10+ years.
I prefer technology stocks but am open to diversification suggestions.
```

---

## Expected Parsed Portfolio

After clicking **"Parse Portfolio"**, you should see:

### Portfolio Metrics

| Metric | Value |
|--------|-------|
| Total Value | ~$642,281 |
| Positions | 5 |
| Portfolio Beta | ~1.4 |
| ESG Score | ~65 |

### Positions Table

| Symbol | Shares | Purchase Price | Current Price | Market Value | Sector |
|--------|--------|----------------|---------------|--------------|--------|
| AAPL | 333 | $150.00 | $185.00 | $61,605 | Technology |
| MSFT | 200 | $280.00 | $420.00 | $84,000 | Technology |
| TSLA | 100 | $200.00 | $175.00 | $17,500 | Consumer Cyclical |
| AMZN | 192 | $130.00 | $178.00 | $34,176 | Technology |
| NVDA | 500 | $450.00 | $890.00 | $445,000 | Technology |

### Sector Allocation

| Sector | Percentage |
|--------|------------|
| Technology | ~97% |
| Consumer Cyclical | ~3% |

---

## Expected Optimization Results

After running optimization, you should see analysis from 5 specialized agents:

### 1. Market Analysis Agent

```
Market Conditions Assessment:
- Current market sentiment: Cautiously Optimistic
- Interest rate environment: Elevated (5.25-5.50%)
- Tech sector outlook: Strong but valuations stretched

Key Observations:
• AI/semiconductor boom driving NVDA gains
• Mega-cap tech showing resilience
• Valuation concerns in growth stocks

Market Recommendations:
- Consider defensive positioning given high valuations
- Dollar-cost averaging into quality names
- Watch for Fed policy shifts
```

### 2. Risk Assessment Agent

```
Portfolio Risk Assessment:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Risk Level: HIGH
Volatility Score: 8.2/10
Concentration Risk: CRITICAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Risk Factors:
• 97% technology sector exposure (recommended max: 40%)
• Single position (NVDA) = 69% of portfolio
• TSLA showing unrealized losses (-12.5%)
• High correlation between holdings

Risk Metrics:
┌────────────┬─────────┬────────────┐
│ Metric     │ Current │ Target     │
├────────────┼─────────┼────────────┤
│ Beta       │ 1.4     │ 1.0-1.1    │
│ Volatility │ High    │ Moderate   │
│ Sharpe     │ 0.85    │ 1.0+       │
│ Max DD     │ -35%    │ -20%       │
└────────────┴─────────┴────────────┘

Recommendations:
1. REDUCE NVDA position to max 25% of portfolio
2. ADD defensive sectors (healthcare, utilities, staples)
3. HARVEST tax loss on TSLA position
4. MAINTAIN quality tech exposure (AAPL, MSFT)
```

### 3. Tax Strategy Agent

```
Tax Optimization Analysis:
═══════════════════════════════════════════

TAX-LOSS HARVESTING OPPORTUNITIES:
┌─────────┬───────────────┬──────────────────┐
│ Symbol  │ Unrealized    │ Tax Savings      │
├─────────┼───────────────┼──────────────────┤
│ TSLA    │ -$2,500       │ $625 - $925      │
└─────────┴───────────────┴──────────────────┘

CAPITAL GAINS SUMMARY:
┌─────────┬───────────────┬──────────────────┐
│ Symbol  │ Gain/Loss     │ Type             │
├─────────┼───────────────┼──────────────────┤
│ AAPL    │ +$11,655      │ Check holding    │
│ MSFT    │ +$28,000      │ Check holding    │
│ TSLA    │ -$2,500       │ Harvestable      │
│ AMZN    │ +$9,216       │ Check holding    │
│ NVDA    │ +$220,000     │ Check holding    │
└─────────┴───────────────┴──────────────────┘

Total Unrealized Gains: $266,371
Estimated Tax Liability: $40,000 - $55,000

RECOMMENDATIONS:
1. Sell TSLA to harvest $2,500 loss
   - Offsets gains from other positions
   - Wait 31 days before repurchasing (wash sale rule)
   
2. Consider qualified dividends
   - AAPL, MSFT pay qualified dividends (15% rate)
   
3. Hold winners for long-term treatment
   - If held >1 year: 15-20% rate vs 22-37% short-term
```

### 4. ESG Compliance Agent

```
ESG Analysis Report:
═══════════════════════════════════════════

OVERALL ESG SCORE: 65/100 (Above Average)

INDIVIDUAL SCORES:
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ Symbol  │ E Score │ S Score │ G Score │ Total   │
├─────────┼─────────┼─────────┼─────────┼─────────┤
│ AAPL    │ 72      │ 68      │ 75      │ 72      │
│ MSFT    │ 85      │ 78      │ 82      │ 82      │
│ TSLA    │ 80      │ 45      │ 40      │ 55      │
│ AMZN    │ 55      │ 52      │ 65      │ 57      │
│ NVDA    │ 70      │ 72      │ 78      │ 73      │
└─────────┴─────────┴─────────┴─────────┴─────────┘

CONCERNS:
⚠️ TSLA - Governance issues (board independence)
⚠️ AMZN - Labor practices concerns
✓ MSFT - Industry leader in sustainability

RECOMMENDATIONS:
- Portfolio meets most ESG criteria
- Consider replacing TSLA with higher ESG alternatives
- MSFT is strongest ESG holding - maintain position
```

### 5. Algorithmic Trading Agent

```
Trade Execution Plan:
═══════════════════════════════════════════

PROPOSED TRADES:

SELL ORDERS:
┌─────────┬─────────┬──────────┬───────────────┐
│ Symbol  │ Shares  │ Price    │ Proceeds      │
├─────────┼─────────┼──────────┼───────────────┤
│ NVDA    │ 285     │ $890.00  │ $253,650      │
│ TSLA    │ 100     │ $175.00  │ $17,500       │
└─────────┴─────────┴──────────┴───────────────┘
Total Sell Proceeds: $271,150

BUY ORDERS (Diversification):
┌─────────┬─────────┬──────────┬───────────────┐
│ Symbol  │ Shares  │ Price    │ Cost          │
├─────────┼─────────┼──────────┼───────────────┤
│ JNJ     │ 250     │ $160.00  │ $40,000       │
│ UNH     │ 80      │ $525.00  │ $42,000       │
│ JPM     │ 200     │ $195.00  │ $39,000       │
│ V       │ 140     │ $280.00  │ $39,200       │
│ PG      │ 200     │ $165.00  │ $33,000       │
│ COST    │ 50      │ $740.00  │ $37,000       │
└─────────┴─────────┴──────────┴───────────────┘
Total Buy Cost: $230,200

EXECUTION STRATEGY:
- Use VWAP algorithm for large NVDA sale
- Execute over 3-5 trading days
- Set limit orders 0.5% below market for buys

TRANSACTION COSTS:
- Estimated commission: $0 (most brokers)
- Market impact (NVDA): ~$500
- Spread costs: ~$300
- Total estimated cost: $800
```

---

## Final Consensus Summary

```
═══════════════════════════════════════════════════════════════
              PORTFOLIO OPTIMIZATION CONSENSUS
═══════════════════════════════════════════════════════════════

AGENT VOTES:
┌─────────────────────┬─────────┬────────────────────────────┐
│ Agent               │ Vote    │ Rationale                  │
├─────────────────────┼─────────┼────────────────────────────┤
│ Market Analysis     │ APPROVE │ Diversification needed     │
│ Risk Assessment     │ APPROVE │ Reduces concentration risk │
│ Tax Strategy        │ APPROVE │ Tax-loss harvesting value  │
│ ESG Compliance      │ APPROVE │ Improves ESG score         │
│ Algorithmic Trading │ APPROVE │ Executable trade plan      │
└─────────────────────┴─────────┴────────────────────────────┘

CONSENSUS: 5/5 APPROVE (100%)
STATUS: ✅ CONSENSUS REACHED

═══════════════════════════════════════════════════════════════
                    RECOMMENDED ACTIONS
═══════════════════════════════════════════════════════════════

IMMEDIATE (Priority 1):
🔴 SELL 285 shares NVDA @ $890 (reduce from 69% to 25%)
🔴 SELL 100 shares TSLA @ $175 (tax-loss harvest)

REBALANCING (Priority 2):
🟢 BUY Healthcare: JNJ (250), UNH (80)
🟢 BUY Financials: JPM (200), V (140)
🟢 BUY Consumer: PG (200), COST (50)

HOLD (No Action):
🟡 AAPL - 333 shares (strong performer)
🟡 MSFT - 200 shares (quality holding)
🟡 AMZN - 192 shares (growth potential)
🟡 NVDA - 215 shares (retain partial position)

═══════════════════════════════════════════════════════════════
                  PORTFOLIO TRANSFORMATION
═══════════════════════════════════════════════════════════════

BEFORE → AFTER COMPARISON:
┌─────────────────┬──────────┬──────────┬─────────────────────┐
│ Metric          │ Before   │ After    │ Change              │
├─────────────────┼──────────┼──────────┼─────────────────────┤
│ Total Value     │ $642,281 │ $642,281 │ No change           │
│ # Positions     │ 5        │ 10       │ +5 (diversified)    │
│ Tech Exposure   │ 97%      │ 45%      │ -52% (safer)        │
│ Healthcare      │ 0%       │ 13%      │ +13% (defensive)    │
│ Financials      │ 0%       │ 12%      │ +12% (value)        │
│ Consumer        │ 3%       │ 14%      │ +11% (staples)      │
│ Portfolio Beta  │ 1.40     │ 1.05     │ -0.35 (lower risk)  │
│ ESG Score       │ 65       │ 72       │ +7 (improved)       │
│ Concentration   │ 69%      │ 30%      │ -39% (diversified)  │
└─────────────────┴──────────┴──────────┴─────────────────────┘

RISK REDUCTION:        HIGH → MODERATE
EXPECTED VOLATILITY:   -35%
DIVERSIFICATION:       2/10 → 8/10
TAX SAVINGS:           ~$925 (from TSLA loss harvest)

═══════════════════════════════════════════════════════════════
```

---

## How to Run the Test

1. Start the Flask server:
   ```bash
   C:\Python313\python.exe flask_ui.py
   ```

2. Open browser to `http://localhost:5000`

3. Click **"Enter Text Description"** button

4. Paste the sample text from above

5. Click **"Parse Portfolio"**

6. Review the parsed portfolio data

7. Click **"Optimize Portfolio"** or wait for auto-start

8. View results in the **Results** tab

---

## Notes

- Results will vary based on the AI model's analysis
- Actual stock prices differ from examples
- The optimization uses Google Gemini AI for analysis
- 5 specialized agents collaborate to reach consensus
- Consensus threshold and iterations can be adjusted in sidebar
