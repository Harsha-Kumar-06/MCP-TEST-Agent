# 🤖 Gemini-Enhanced Dynamic Portfolio Parser

## 🚀 What's New?

Your portfolio parser now **learns and grows** using Google Gemini AI! It can handle:
- ✅ **Any company name** - even if not in the database
- ✅ **Unknown tickers** - Gemini identifies them automatically
- ✅ **Automatic sector classification** - for any stock
- ✅ **ESG score estimation** - powered by AI
- ✅ **Caching** - learned data saved for instant future lookups

---

## 🌟 Key Features

### 1. Dynamic Ticker Discovery
```
Input: "500 Snowflake shares at 150, bought for 120"

First time:
  🤖 Gemini identifies: Snowflake → SNOW
  💾 Caches mapping for future use
  
Next time:
  ⚡ Instant lookup from cache (no API call!)
```

### 2. Intelligent Sector Assignment
```
Unknown ticker: DDOG

🤖 Gemini: "Datadog is in Technology sector"
💾 Cached: DDOG → Technology

All future DDOG parses use cached data!
```

### 3. ESG Score Estimation
```
New company in portfolio?

🤖 Gemini estimates ESG score (0-100)
💾 Cached for consistency
✅ Used in policy compliance checks
```

### 4. Full Text Extraction Fallback
```
If structured parsing fails:

🤖 Gemini reads entire text
📊 Extracts ALL positions
🎯 Identifies prices, shares, metadata
✅ Returns complete portfolio
```

---

## 📊 How It Works

### Multi-Layer Approach:

```
Layer 1: Static Mappings (Instant)
  ├─ Check 80+ known companies
  ├─ Check 50+ known sectors
  └─ If found → Use immediately
  
Layer 2: Cache Lookup (Instant)
  ├─ Check learned mappings
  ├─ Check previous Gemini responses
  └─ If found → Use immediately
  
Layer 3: Gemini API (Smart)
  ├─ Ask Gemini for unknown data
  ├─ Validate response
  ├─ Cache for future
  └─ Return enriched data
  
Layer 4: Full Extraction (Powerful)
  ├─ Send entire text to Gemini
  ├─ Extract structured JSON
  ├─ Parse all positions
  └─ Return complete portfolio
```

---

## 🎯 Usage Examples

### Example 1: Emerging Tech Stocks
```
500 Palantir shares at 25, bought for 18
200 Snowflake at 150, bought for 120
150 CrowdStrike at 280, bought for 200

Cash 100000
```

**Result:**
```
✨ Learned: Palantir → PLTR (Technology)
✨ Learned: Snowflake → SNOW (Technology)
✨ Learned: CrowdStrike → CRWD (Technology)

✅ Parsed 3 positions successfully!
💾 Mappings cached in portfolio_knowledge_cache.json
```

### Example 2: Global Stocks
```
300 Sony shares at 95, bought for 80
200 SAP at 140, bought for 120
150 Taiwan Semiconductor at 145, bought for 130

Cash 50000
```

**Result:**
```
✨ Learned: Sony → SONY (Technology)
✨ Learned: SAP → SAP (Technology)
✅ Taiwan Semiconductor → TSM (cached)

✅ Parsed 3 positions successfully!
```

---

## 🔧 How to Enable

### Step 1: Test the New Parser

```bash
cd "c:\Users\Harsha Kumar\Desktop\DRAVYN\Agents\Swarm Pattern"
py -3.13 test_gemini_parser.py
```

### Step 2: Update Flask UI

**Option A - Replace the parser file:**
```bash
cd portfolio_swarm
copy text_parser.py text_parser_static_backup.py
copy text_parser_gemini.py text_parser.py
```

**Option B - Update import in flask_ui.py:**
```python
# Change this:
from portfolio_swarm.text_parser import parse_portfolio_text

# To this:
from portfolio_swarm.text_parser_gemini import parse_portfolio_text
```

### Step 3: Restart Flask

```bash
py -3.13 flask_ui.py
```

---

## 💰 Cost Efficiency

### Smart Caching Strategy:

| Parse Type | API Calls | Cost | Speed |
|------------|-----------|------|-------|
| Known company (Microsoft) | 0 | $0.00 | Instant ⚡ |
| Cached company (Snowflake) | 0 | $0.00 | Instant ⚡ |
| New company (first time) | 2-3 | ~$0.001 | 1-2s 🤖 |
| Full extraction fallback | 1 | ~$0.002 | 2-3s 🤖 |

**Example:** 
- Parse 100 known companies: **$0.00** (all cached)
- Parse 10 new companies: **~$0.01** (Gemini learns them)
- Parse those 10 again: **$0.00** (now cached!)

---

## 📁 Knowledge Cache

The parser creates `portfolio_knowledge_cache.json`:

```json
{
  "companies": {
    "snowflake": "SNOW",
    "palantir": "PLTR",
    "crowdstrike": "CRWD"
  },
  "sectors": {
    "SNOW": "Technology",
    "PLTR": "Technology",
    "CRWD": "Technology"
  },
  "esg_scores": {
    "SNOW": 72,
    "PLTR": 65,
    "CRWD": 78
  }
}
```

**Benefits:**
- ✅ Instant lookups after first use
- ✅ Consistent data across parses
- ✅ Minimal API costs
- ✅ Growing knowledge base

---

## 🎉 Benefits Summary

### Before (Static Parser):
- ❌ Only 80 companies supported
- ❌ Unknown companies fail to parse
- ❌ Manual sector assignment
- ❌ Fixed ESG scores
- ❌ Can't handle new companies

### After (Gemini-Enhanced):
- ✅ **Unlimited companies** (learns anything)
- ✅ **Unknown → Known** (automatic learning)
- ✅ **Dynamic sectors** (AI-powered)
- ✅ **Smart ESG** (AI estimation)
- ✅ **Future-proof** (grows with market)

---

## 🚀 Quick Start

1. **Test it**: `py -3.13 test_gemini_parser.py`
2. **Enable it**: Update Flask UI import
3. **Use it**: Paste ANY company names - they work!
4. **Watch it learn**: Check `portfolio_knowledge_cache.json`

**Your parser now grows smarter with every use!** 🌱→🌳
