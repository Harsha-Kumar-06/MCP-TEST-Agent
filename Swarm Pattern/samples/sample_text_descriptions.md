# Sample Portfolio Text Descriptions

Copy and paste any of these examples into the "Text Description" field in the web UI!

---

## 📝 EXAMPLE 1: Simple List

```
I own 10000 shares of Apple (AAPL) bought at $150, now trading at $185.
Also have 5000 Microsoft (MSFT) shares, cost basis $350, current price $410.
Plus 3000 Tesla (TSLA) at $245, purchased at $195.
Cash balance: $500,000
```

**What you'll get:**
- 3 positions: AAPL, MSFT, TSLA
- Automatic sector detection
- Cash: $500,000

---

## 📝 EXAMPLE 2: Detailed with ESG

```
Portfolio Overview:
- AAPL: 15,000 shares, purchased June 2023 at $150, currently $185, Technology sector, ESG score 75
- MSFT: 8,000 shares, bought September 2022 at $350, now $410, Technology, ESG 82
- JNJ: 10,000 shares, cost basis $155, current $162, Healthcare, ESG 72
- JPM: 5,000 shares at $185, bought at $140, Finance, ESG 58

Cash: $1,000,000
Technology limit: 30%
Minimum ESG score: 65
```

**What you'll get:**
- 4 positions with ESG scores
- Policy limits configured
- Sectors specified
- Cash: $1M

---

## 📝 EXAMPLE 3: Conversational Style

```
My tech-heavy portfolio includes Apple (15k shares @ $185, bought for $140), 
Microsoft (8k shares, paid $305 now worth $410), and some Tesla 
(3k shares currently at $245, cost basis $195). 

Also holding 5000 shares of JNJ in healthcare at $162 (bought at $155).

I have $2 million in cash. Want to keep technology exposure under 35%.
```

**What you'll get:**
- Natural language parsing
- Mixed notation (15k = 15,000)
- Policy limit: 35% tech
- Cash: $2M

---

## 📝 EXAMPLE 4: Short-term Positions (Tax Critical)

```
Recent purchases:
- NVDA: 5,000 shares bought 45 days ago at $450, now $875 (Technology, ESG 68)
- META: 3,000 shares bought 2 months ago at $485, currently $512 (Technology, ESG 52)
- AAPL: 10,000 shares bought 400 days ago at $170, now $185 (Technology, ESG 75)

Cash: $800,000
Tech limit: 30%
ESG minimum: 60
```

**What you'll get:**
- Recent purchase dates detected
- Short-term capital gains implications
- ESG violations flagged (META below 60)
- Tech sector over limit

---

## 📝 EXAMPLE 5: Crisis Portfolio (Multiple Violations)

```
Concentrated tech portfolio:
AAPL 20000 shares at $185 (cost $175, bought 3 months ago)
NVDA 10000 at $875 (bought at $420)
TSLA 5000 at $245 (paid $280, ESG 45)
META 8000 shares, current $512, basis $485, ESG 52

Cash: $1 million
Technology sector limit: 30%
Minimum ESG: 60
Maximum portfolio beta: 1.5
```

**What you'll get:**
- High concentration (85% tech)
- Short-term tax issues
- ESG violations (TSLA 45, META 52)
- Complex rebalancing needed

---

## 📝 EXAMPLE 6: Balanced Portfolio

```
Diversified holdings:

Technology (28%):
- AAPL 10000 @ $185 (basis $150)
- MSFT 5000 @ $410 (basis $350)

Healthcare (25%):
- JNJ 12000 @ $162 (basis $155)
- UNH 3000 @ $500 (basis $480)

Finance (20%):
- JPM 8000 @ $185 (basis $140)
- BAC 15000 @ $40 (basis $38)

Energy (12%):
- XOM 8000 @ $108 (basis $95)

Consumer Staples (15%):
- PG 10000 @ $150 (basis $145)

Cash: $3,000,000
All tech limit 30%, financials 25%, energy 15%
ESG minimum 60
```

**What you'll get:**
- Well-diversified portfolio
- Near compliance
- Minor violations only

---

## 🎯 QUICK TEST SAMPLES

### Copy-Paste Ready:

**Sample A - Simple:**
```
10000 AAPL @ $185 (cost $150), 5000 MSFT @ $410 (cost $350), cash $1m
```

**Sample B - With Limits:**
```
15000 AAPL at $185 bought at $140
8000 MSFT at $410 cost $350
5000 JNJ at $162 basis $155
Cash $2M, tech limit 25%, ESG min 70
```

**Sample C - Problem Portfolio:**
```
20k AAPL @ $185 (bought $175), 10k NVDA @ $875 (cost $450), 5k TSLA @ $245 (basis $280), cash $500k, tech max 30%
```

---

## 💡 TIPS FOR BEST RESULTS

1. **Include prices**: Current price and cost basis for tax calculations
2. **Mention sectors**: Or use common tickers (AAPL=Tech, JNJ=Healthcare)
3. **State cash balance**: Default is $100k if not specified
4. **Add limits**: "tech limit 30%", "ESG minimum 65", etc.
5. **Use k/m for thousands/millions**: "10k shares" = 10,000

---

## 🔧 WHAT GETS PARSED

✅ **Automatically detected:**
- Stock tickers (AAPL, MSFT, etc.)
- Share quantities (10000, 10k, 10,000)
- Current prices ($185, 185)
- Cost basis (bought at $150)
- Cash balance ($1m, $1,000,000)
- Policy limits (tech limit 30%)
- ESG minimums (min ESG 65)

✅ **Smart defaults:**
- Sectors: Based on ticker or text mentions
- ESG scores: 70 if not specified
- Purchase date: 1 year ago if not mentioned
- Beta: 1.0 if not specified

---

## 🚀 HOW TO USE

1. **Copy** any example above
2. Go to web UI
3. Select **"Text Description"** as Portfolio Source
4. **Paste** into text area
5. Click **"🔍 Parse Portfolio"**
6. See your portfolio loaded!
7. Go to **"Optimize"** tab
8. Click **"Run Optimization"**

---

## 🎨 SUPPORTED FORMATS

The parser understands many variations:

- "10000 AAPL at $185"
- "10k shares of Apple"
- "AAPL: 10,000 shares, current $185"
- "own 10k AAPL @ $185"
- "bought 10000 shares Apple (AAPL)"
- "15k AAPL, now $185, cost $150"

**All work equally well!** Write naturally and the AI will extract the data. 🎉
