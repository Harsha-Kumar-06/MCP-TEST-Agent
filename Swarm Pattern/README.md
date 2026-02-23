# Financial Portfolio Optimization - Swarm Pattern

Multi-agent collaborative system for portfolio rebalancing using the swarm pattern, powered by **Google Gemini AI**.

## Overview

This system implements a **swarm pattern** where 5 specialized AI agents collaborate to optimize investment portfolios. Agents analyze, debate, propose solutions, and vote on trade plans to reach consensus.

## ✨ Features

- 🤖 **5 Specialized AI Agents** - Market, Risk, Tax, ESG, Trading
- 🌐 **Web UI** - Beautiful Flask-based interface at `localhost:5000`
- 💬 **Natural Language Input** - Describe your portfolio in plain text
- 📁 **File Upload** - Support for CSV, JSON, YAML formats
- 🔄 **Real-time Progress** - Watch agents debate in real-time
- 📊 **Consensus Voting** - Transparent decision-making process
- 💡 **AI Recommendations** - Smart threshold suggestions based on portfolio
- 🔒 **Input Locking** - Prevents changes during optimization
- 🎯 **Strategy Selection** - 10 optimization strategies with 1-5 star ratings
- ⭐ **Portfolio-Adaptive Ratings** - Strategies rated based on YOUR portfolio's beta, ESG, sectors
- 📈 **Sector Pie Chart** - Visual sector allocation breakdown
- 🗳️ **Iteration-Aware Voting** - Agents debate properly, adjusting thresholds each iteration

## 📁 Project Structure

```
Swarm Pattern/
├── 📁 portfolio_swarm/      # Core package
│   ├── agents.py            # 5 specialized AI agents
│   ├── orchestrator.py      # Swarm coordination
│   ├── models.py            # Data models
│   ├── config.py            # Gemini API configuration
│   ├── text_parser.py       # Natural language parser
│   └── ...
│
├── 📁 templates/            # HTML templates
│   └── index.html           # Web UI template
│
├── 📁 docs/                 # Documentation (18 files)
├── 📁 tests/                # Test files (17 files)
├── 📁 samples/              # Sample portfolios & templates
├── 📁 backups/              # Old/debug files
│
├── 🚀 flask_ui.py           # Main Web UI (recommended)
├── 🚀 cli_interface.py      # Command Line Interface
├── 🚀 demo.py               # Demo with $50M portfolio
├── 🚀 web_ui.py             # Streamlit UI (alternative)
│
├── 📜 run_web.bat           # Double-click to start Web UI
├── 📜 run_cli.bat           # Double-click to start CLI
├── 📜 run_demo.bat          # Double-click to run demo
│
├── 📄 requirements.txt      # Python dependencies
├── 📄 .env                  # API keys (create from .env.example)
└── 📄 .env.example          # Template for environment variables
```

## 🚀 Quick Start

### 1. Activate Virtual Environment

Before running any commands, activate the virtual environment:

**Windows (Command Prompt):**
```bash
# Replace <YOUR_USERNAME> with your Windows username
C:/Users/<YOUR_USERNAME>/Desktop/DRAVYN/Agents/Swarm Pattern/venv/Scripts/activate.bat
```

**Windows (PowerShell):**
```powershell
# Replace <YOUR_USERNAME> with your Windows username
& "C:/Users/<YOUR_USERNAME>/Desktop/DRAVYN/Agents/Swarm Pattern/venv/Scripts/Activate.ps1"
```

**From the project directory:**
```bash
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Important:** Uses `google-genai` package (NOT the deprecated `google-generativeai`)

### 3. Set Up API Key

Create a `.env` file with your Google Gemini API key:

```env
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.5
GEMINI_MAX_TOKENS=4096
```

Get a free API key at: https://makersuite.google.com/app/apikey

### 4. Run the Application

**Option A: Double-click batch file (Windows)**
- `run_web.bat` → Web UI at http://localhost:5000

**Option B: Command line**
```bash
python flask_ui.py
```

Then open http://localhost:5000 in your browser.

## 🎯 How to Use

### Web UI (Recommended)

1. **Load Portfolio** - Choose one of three methods:
   - 📊 **Sample Portfolio** - Load pre-built $50M demo
   - 📝 **Text Description** - Describe in natural language
   - 📁 **File Upload** - Upload CSV/JSON/YAML

2. **Configure Settings** (Optional):
   - Max Iterations (1-20)
   - Consensus Threshold (50-100%)
   - Enable/disable specific agents

3. **Run Optimization** - Click "Run Optimization" and watch:
   - Real-time progress bar
   - Agent analysis phases
   - Vote tallying

4. **Review Results**:
   - Agent votes with rationales
   - Approved trade plan
   - Tax implications
   - Execution timeline

### Text Input Example

```
My Investment Portfolio:

I have $50,000 invested in Apple (AAPL) bought at $150, now at $185.
Also 200 shares of Microsoft (MSFT) at $280, currently $420.
100 Tesla (TSLA) shares at $200, now $175.
$25,000 in Amazon (AMZN) at $130, now $178.
500 NVIDIA (NVDA) shares at $450, currently $890.

Risk tolerance: moderate
Goal: long-term growth
```

## 🤖 Specialized Agents

| Agent | Role | Focus |
|-------|------|-------|
| **Market Analysis** | Trends & Valuations | Market sentiment, P/E ratios, sector outlook |
| **Risk Assessment** | Compliance & Risk | Concentration, beta, policy limits |
| **Tax Strategy** | Tax Optimization | Capital gains, loss harvesting, holding periods |
| **ESG Compliance** | Sustainability | Environmental, social, governance scores |
| **Algorithmic Trading** | Execution | Trade timing, costs, market impact |

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Required
GEMINI_API_KEY=your-api-key

# Optional (defaults shown)
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.5
GEMINI_MAX_TOKENS=4096
ENABLE_COST_TRACKING=true
ENABLE_DEBUG_LOGGING=false
```

### Consensus Settings

| Setting | Range | Description |
|---------|-------|-------------|
| Min Iterations | 1-10 | Minimum debate rounds before consensus |
| Max Iterations | 1-20 | Maximum debate rounds before stopping |
| Consensus Threshold | 0.5-1.0 | Required approval rate (60% = 3/5 agents) |

## ⚡ Performance Optimizations

The system includes several optimizations to reduce API costs:

| Feature | Benefit |
|---------|---------|
| **Rule-Based Voting** | 50% less API calls - voting uses logic, not AI |
| **Analysis Caching** | Eliminates redundant AI calls across iterations |
| **Smart Model** | Uses gemini-2.5-flash with 4096 tokens |

See [CHANGELOG.md](docs/CHANGELOG.md) for details.

## 📊 Sample Files

Located in `samples/` folder:

- `sample_portfolio.csv` - CSV format example
- `sample_portfolio.json` - JSON format example
- `sample_portfolio.yaml` - YAML format example
- `sample_text_descriptions.md` - Natural language examples
- `crisis_portfolio.txt` - Crisis scenario example
- `template.csv` - Empty template for your data

## 📚 Documentation

All documentation is in the `docs/` folder:

| Document | Description |
|----------|-------------|
| `SETUP_GUIDE.md` | **Complete setup & project guide** ⭐ |
| `QUICKSTART_2MIN.md` | 2-minute setup guide |
| `GEMINI_SETUP.md` | API key configuration |
| `SAMPLE_INPUT_EXAMPLE.md` | Input/output examples |
| `ARCHITECTURE.md` | System design details |
| `COMPLETE_GUIDE.md` | Full user guide |
| `FILE_INPUT_GUIDE.md` | File format specifications |

### 📊 Architecture Diagrams

Visual diagrams in `docs/diagrams/`:

| Diagram | Description |
|---------|-------------|
| `architecture.svg` | System architecture overview |
| `flowchart.svg` | Optimization process flow |
| `agent-interaction.svg` | Agent communication model |
| `data-flow.svg` | Data transformation pipeline |

## 🧪 Running Tests

```bash
cd tests
python -m pytest test_agents_api.py -v
```

## 🔧 Troubleshooting

### "No module named 'flask'"
```bash
pip install flask werkzeug
```

### API Quota Exceeded
- Reduce number of active agents (uncheck 2-3 in sidebar)
- Lower max iterations to 3-5
- Wait for daily quota reset

### Import Errors
Ensure you're using the correct Python:
```bash
C:\Python313\python.exe flask_ui.py
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web UI (Flask)                        │
├─────────────────────────────────────────────────────────┤
│                  Swarm Orchestrator                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  │ Market  │ │  Risk   │ │   Tax   │ │   ESG   │ │ Trading │
│  │ Agent   │ │ Agent   │ │ Agent   │ │ Agent   │ │ Agent   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
│       └──────────┴──────────┴──────────┴──────────┘
│                    Communication Bus                      │
├─────────────────────────────────────────────────────────┤
│                  Google Gemini AI API                    │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Workflow

1. **Input** → Portfolio data (text/file/sample)
2. **Parse** → Convert to structured Portfolio object
3. **Analyze** → Each agent analyzes independently
4. **Debate** → Agents exchange concerns/recommendations
5. **Propose** → Generate trade plan
6. **Vote** → All agents vote with rationale
7. **Consensus** → Check if threshold reached
8. **Output** → Approved trades + execution plan

## 🆕 Recent Updates

### Latest (Feb 2026 - v2.1.0)
- ✅ **10 Strategies** - Added Momentum Trading and Value Investing
- ✅ **Star Ratings** - 1-5 ⭐ ratings with effectiveness labels
- ✅ **Portfolio-Adaptive** - Ratings adjust ±2 stars based on portfolio characteristics
- ✅ **Iteration-Aware Voting** - Agents adjust thresholds to encourage consensus
- ✅ **Improved Filters** - Fixed irrelevant content detection (phrase-based)
- ✅ **BUY Trades** - Added proper BUY trade generation

### Previous (v2.0.0)
- ✅ **Strategy Selection Tab** - Choose strategy AFTER loading portfolio
- ✅ **Sector Allocation Pie Chart** - Visual breakdown using Chart.js
- ✅ **Fixed Agent Voting** - All 5 agents now vote properly (no abstains)
- ✅ **BEST FIT Badge** - Top-rated strategy highlighted
- ✅ **API Migration** - google-genai package (from deprecated google-generativeai)
- ✅ **Organized project structure** (docs/, tests/, samples/, backups/)

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

## 📞 Support

For issues or questions:
- Check `docs/` folder for guides
- Review `samples/` for examples
- Open a GitHub issue
