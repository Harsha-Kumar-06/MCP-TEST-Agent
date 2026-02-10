# 🚀 Quick Start Guide (2 Minutes!)

Get the Portfolio Swarm Optimizer running in under 2 minutes!

---

## Step 1: Get Your FREE Google Gemini API Key (30 seconds)

1. Go to: **https://makersuite.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"** → **"Create API key in new project"**
4. Copy the key (starts with `AIza...`)

---

## Step 2: Add API Key to .env (15 seconds)

Create/edit the `.env` file in the project root:

```env
GEMINI_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Step 3: Install Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

---

## Step 4: Run the Web UI (5 seconds)

### Windows - Double-click:
```
run_web.bat
```

### Or use command line:
```bash
python flask_ui.py
```

**Look for:**
```
✅ Google Gemini configured: gemini-2.5-flash
🌐 Open your browser: http://localhost:5000
```

---

## Step 5: Test It! (30 seconds)

1. Open **http://localhost:5000** in your browser
2. Click **"Load Sample Portfolio ($50M)"**
3. Go to **Strategy** tab → Pick a strategy (see ⭐ ratings!)
4. Click **"Run Optimization"** and watch agents debate!

**Pro tip:** Pick a low-rated (⭐⭐☆☆☆) strategy to trigger multiple iterations!

---

## 🎉 Done!

You now have a working AI-powered portfolio optimization system!

---

## 📁 Project Structure

```
Swarm Pattern/
├── flask_ui.py          # Main app (run this)
├── run_web.bat          # Double-click to start
├── portfolio_swarm/     # Core AI agents
├── templates/           # Web UI
├── docs/                # Documentation
├── tests/               # Test files
├── samples/             # Example portfolios
└── .env                 # Your API key
```

---

## 💡 Quick Troubleshooting

### ❌ "No module named 'flask'"
```bash
pip install flask werkzeug
```

### ❌ "GEMINI_API_KEY not configured"
Check your `.env` file has the correct key

### ❌ API Quota Exceeded
- Uncheck 2-3 agents in the sidebar
- Set max iterations to 3-5
- Wait for daily quota reset

---

## 🎯 What Can You Do?

### Input Methods
- **Sample Portfolio** - Pre-built $50M demo
- **Text Description** - Describe in plain English
- **File Upload** - CSV, JSON, or YAML

### Example Text Input
```
I own 500 shares of Apple at $150, now $185.
200 Microsoft shares bought at $300, current $420.
$50,000 in cash.
Risk tolerance: moderate.
```

---

## 📚 More Documentation

- Full guide: `docs/COMPLETE_GUIDE.md`
- API setup: `docs/GEMINI_SETUP.md`
- Examples: `docs/SAMPLE_INPUT_EXAMPLE.md`
- Architecture: `docs/ARCHITECTURE.md`

---

## 🆘 Need Help?

1. Check the `docs/` folder
2. Review `samples/` for examples
3. Open a GitHub issue
