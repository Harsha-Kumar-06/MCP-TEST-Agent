# 🤖 Google Gemini AI Integration Setup Guide

Your Portfolio Swarm agents are now powered by **Google Gemini AI**! 🚀

This guide will help you get everything set up in **under 5 minutes**.

---

## ✅ What Was Integrated

All 5 specialized agents now use Google Gemini for intelligent analysis:

1. **🔍 Market Analysis Agent** - Valuation & sector trend analysis
2. **⚖️ Risk Assessment Agent** - Compliance & risk management  
3. **💰 Tax Strategy Agent** - Tax optimization & capital gains
4. **🌱 ESG Compliance Agent** - Environmental & social governance
5. **⚡ Algorithmic Trading Agent** - Execution feasibility & liquidity

**New Features:**
- ✅ AI-powered portfolio analysis
- ✅ Intelligent voting on trade proposals
- ✅ Cost tracking (API usage & expenses)
- ✅ Error handling with automatic retries
- ✅ Response parsing from natural language to structured data
- ✅ Configurable prompts for each agent

---

## 🚀 Quick Start (5 Steps)

### **Step 1: Get Your Free Gemini API Key**

1. Go to **[Google AI Studio](https://makersuite.google.com/app/apikey)**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your API key (starts with `AIza...`)

> 💡 **Free Tier:** Google Gemini 1.5 Flash gives you **15 requests/minute** and **1M tokens/day** for FREE!

---

### **Step 2: Create `.env` File**

Copy the example file and add your API key:

```bash
# Copy template
copy .env.example .env

# On Mac/Linux:
# cp .env.example .env
```

Open `.env` in a text editor and replace `your_api_key_here` with your actual key:

```bash
GEMINI_API_KEY=AIzaSyC...YOUR_ACTUAL_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.5
GEMINI_MAX_TOKENS=4096
ENABLE_COST_TRACKING=true
ENABLE_DEBUG_LOGGING=false
```

---

### **Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

This installs:
- `google-genai` - **New** Gemini SDK (replaces deprecated google-generativeai)
- `python-dotenv` - Environment variable management
- `Flask` - Web framework
- `pyyaml` - File parsing support

> ⚠️ **Important:** Use `google-genai` NOT `google-generativeai` (deprecated)

---

### **Step 4: Run the System**

```bash
python flask_ui.py
```

You should see:
```
✅ Using new google.genai API
✅ Google Gemini configured: gemini-2.5-flash
🌐 Open your browser and go to: http://localhost:5000
```

---

### **Step 5: Test with Sample Portfolio**

1. Open **http://localhost:5000** in your browser
2. Click **"Load Sample Portfolio"** button
3. Wait 5 seconds (countdown timer)
4. See AI agents analyze and vote! 🤖
5. Check terminal for cost summary:
   ```
   💰 AI API Usage Cost:
      Total Requests: 15
      Total Tokens: 12,450
      Total Cost: $0.000937
   ```

---

## 📊 Understanding Costs

### **Pricing (Google Gemini 1.5 Flash)**

| Model | Input Tokens | Output Tokens |
|-------|--------------|---------------|
| **Gemini 1.5 Flash** | $0.075 / 1M tokens | $0.30 / 1M tokens |

### **Typical Costs Per Optimization**

| Scenario | Agents | API Calls | Tokens | Cost |
|----------|--------|-----------|--------|------|
| **Small Portfolio** (5 positions) | 5 agents | 10-15 | ~10K | **$0.001** |
| **Medium Portfolio** (20 positions) | 5 agents | 15-20 | ~25K | **$0.003** |
| **Large Portfolio** (50 positions) | 5 agents | 20-30 | ~50K | **$0.006** |

> 💡 **Real-world example:** Optimizing a $10M portfolio with 20 positions costs **less than 1 cent**!

---

## 🎛️ Configuration Options

### **Model Selection**

Edit `.env` to choose different Gemini models:

```bash
# Fast & cheap (recommended)
GEMINI_MODEL=gemini-1.5-flash

# More powerful (costs 5x more)
GEMINI_MODEL=gemini-1.5-pro

# Legacy model
GEMINI_MODEL=gemini-pro
```

### **Temperature (Creativity)**

Control how deterministic vs creative the AI is:

```bash
# Very deterministic (recommended for finance)
GEMINI_TEMPERATURE=0.1

# Balanced (default)
GEMINI_TEMPERATURE=0.3

# More creative
GEMINI_TEMPERATURE=0.7
```

### **Max Tokens (Response Length)**

```bash
# Shorter responses (faster, cheaper)
GEMINI_MAX_TOKENS=1024

# Balanced (default)
GEMINI_MAX_TOKENS=2048

# Longer responses (more detailed analysis)
GEMINI_MAX_TOKENS=4096
```

---

## 🔍 How It Works

### **Analysis Phase**

Each agent uses specialized prompts to analyze the portfolio:

```python
# Example: Market Analysis Agent
PROMPT: "Analyze this $10M portfolio with 70% tech allocation.
         Identify overvalued sectors..."

AI RESPONSE: 
FINDINGS: Technology sector at 70% exceeds historical norms (P/E 32x vs 24x avg)
RECOMMENDATION: Reduce tech exposure to 50%, rotate to healthcare
CONVICTION: 8
CONCERNS: Apple overweight at 15%, Nvidia elevated valuation
```

### **Voting Phase (Rule-Based + Iteration-Aware)**

Voting now uses **rule-based logic** (no AI calls) with **iteration-aware thresholds**:

```python
# Example: Tax Strategy Agent voting
# Base threshold: 15% tax liability
# Iteration adjustment: +3% per iteration

# Iteration 1: threshold 15%, REJECT if tax > 15%
# Iteration 3: threshold 21%, REJECT if tax > 21%
# Iteration 5: threshold 27%, REJECT if tax > 27%

# This encourages consensus in later iterations
vote_rationale = f"Iter {iteration}: threshold {threshold}%, tax={tax_pct:.1f}%"
```

Each agent adjusts thresholds progressively:
| Agent | Base | Adjustment |
|-------|------|------------|
| Market Analysis | 30% bad trades | +5%/iter |
| Risk Assessment | 3 violations | +1/iter |
| Tax Strategy | 15% liability | +3%/iter |
| ESG Compliance | ESG avg 60 | -3/iter |
| Algorithmic Trading | 50 bps cost | +10 bps/iter |

### **Cost Tracking**

Every API call is tracked:

```python
# Automatically logged
cost_tracker.add_usage(
    agent_type="MARKET_ANALYSIS",
    input_tokens=1850,
    output_tokens=320
)

# View summary after optimization
cost_tracker.print_summary()
```

---

## 💡 Prompt Engineering

All agent prompts are in **`portfolio_swarm/prompts.py`**

### **Customizing Prompts**

Want agents to focus on specific criteria? Edit the prompts:

```python
# Example: Make Risk Agent more conservative
RISK_ASSESSMENT_SYSTEM_PROMPT = """
You are an EXTREMELY CONSERVATIVE Risk Assessment Agent.
Your risk tolerance is LOW. Flag any portfolio beta > 1.0 as concerning.
Concentration limits should be 20% maximum per sector.
...
"""
```

### **Agent-Specific Expertise**

Each agent has 3 prompts:
1. **System Prompt** - Defines agent's role and expertise
2. **Analysis Prompt** - Template for portfolio analysis
3. **Vote Prompt** - Template for voting on proposals

---

## 🐛 Troubleshooting

### **Error: "GEMINI_API_KEY not configured"**

**Solution:** Create `.env` file with your API key (see Step 2)

---

### **Error: "API quota exceeded"**

**Solution:** You hit the free tier limit (15 requests/min). Wait 1 minute and try again.

Or upgrade to paid tier: **[Google Cloud Console](https://console.cloud.google.com)**

---

### **Error: "Module 'google.generativeai' not found"**

**Solution:** Install dependencies:
```bash
pip install google-generativeai python-dotenv
```

---

### **Agents returning generic responses**

**Problem:** AI might be struggling with prompt format

**Solutions:**
1. Check `GEMINI_TEMPERATURE` isn't too low (<0.1)
2. Increase `GEMINI_MAX_TOKENS` to allow longer responses
3. Review prompts in `prompts.py` for clarity

---

### **High costs**

**Optimizations:**
1. Use `gemini-1.5-flash` (not `gemini-1.5-pro`)
2. Reduce `GEMINI_MAX_TOKENS` to limit response length
3. Set `ENABLE_COST_TRACKING=true` to monitor usage
4. Implement caching for repeated portfolio analyses

---

## 🚀 Next Steps

### **1. Test with Your Portfolio**

- **Text Input:** Paste your holdings in natural language
- **File Upload:** Upload CSV with columns: `ticker, shares, price, sector, esg_score`
- **Complex Scenario:** Try the crisis hedge fund example (see `samples/`)

### **2. Customize Agent Behavior**

Edit `portfolio_swarm/prompts.py`:
- Make agents more/less conservative
- Add industry-specific knowledge
- Adjust conviction thresholds

### **3. Monitor Costs**

Check terminal after each optimization:
```
💰 AI API Usage Cost:
   Total Cost: $0.002456
```

Set budget alerts in Google Cloud Console if needed.

### **4. Switch to Alternative LLMs (Optional)**

The architecture supports other LLMs:
- **OpenAI GPT-4:** `pip install openai`
- **Anthropic Claude:** `pip install anthropic`
- **Azure OpenAI:** Use OpenAI SDK with Azure endpoint

Example integration in `config.py` (pattern already set up for Gemini).

---

## 📚 Additional Resources

- **Gemini API Docs:** https://ai.google.dev/docs
- **Pricing Calculator:** https://ai.google.dev/pricing
- **Prompt Engineering Guide:** https://ai.google.dev/docs/prompt_best_practices
- **Rate Limits:** https://ai.google.dev/docs/quota

---

## ✅ Success Checklist

- [ ] Created `.env` file with API key
- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Started Flask server (`python flask_ui.py`)
- [ ] Saw "✅ Google Gemini configured" message
- [ ] Loaded sample portfolio and got AI analysis
- [ ] Checked cost summary in terminal
- [ ] All 5 agents provided intelligent votes

---

## 🎉 You're All Set!

Your portfolio swarm is now powered by Google Gemini AI. 

**Try it out:**
```bash
python flask_ui.py
```

Open **http://localhost:5000** and watch the agents collaborate! 🤖💼

---

**Questions?** Check the [ARCHITECTURE.md](ARCHITECTURE.md) for system details or [QUICKSTART.md](QUICKSTART.md) for usage examples.

**Cost concerns?** With Gemini 1.5 Flash, you can run **1,000+ optimizations** for less than **$1**! 💰
