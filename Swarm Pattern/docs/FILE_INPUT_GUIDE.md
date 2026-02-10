# File Input System - Summary

## What Was Created

I've created a comprehensive input file system that allows you to provide portfolio data in **multiple formats**:

### 📁 Sample Files (in `samples/` directory)

1. **sample_portfolio.csv** - CSV format with 16 positions ($60M)
2. **sample_portfolio.json** - JSON format with 9 positions + full metadata ($39M)
3. **sample_portfolio.yaml** - YAML format with 4 positions ($23M)
4. **sample_questions.txt** - Complete questionnaire guide
5. **USAGE.md** - Detailed usage instructions
6. **README.md** - Overview of sample files

### 🔧 New Components

**portfolio_swarm/input_parser.py** (400+ lines)
- Universal parser supporting CSV, JSON, YAML, Excel formats
- Automatic field name detection (handles variations like "ticker" vs "symbol")
- Built-in validation with warnings
- Template export functionality
- Smart date parsing

**file_input_demo.py** (210+ lines)
- Complete example showing how to use any input format
- Runs full swarm optimization from file input
- Interactive file selector
- Comparison mode for multiple files
- Template generation

## How to Use

### Quick Start

```bash
# Set Python path (required on Windows)
cd "c:\Users\Harsha Kumar\Desktop\DRAVYN\Agents\Swarm Pattern"
set PYTHONPATH=%CD%

# Run with any sample file
python file_input_demo.py samples\sample_portfolio.csv
python file_input_demo.py samples\sample_portfolio.json  
python file_input_demo.py samples\sample_portfolio.yaml

# Interactive mode
python file_input_demo.py
```

### Just Tested - Working!

```
Loading portfolio from: samples\sample_portfolio.csv
Portfolio loaded successfully!
  - Positions: 16
  - Total value: $59,670,000
  - Cash: $1,000,000
  
OPTIMIZATION RESULTS
Consensus reached: YES
Iterations: 1
Approval rate: 80.0%

Recommended trades: 4
  SELL  3000 shares of AAPL @ $200.00
  SELL  4000 shares of MSFT @ $400.00
  SELL  2000 shares of NVDA @ $500.00
  SELL  1600 shares of GOOGL @ $140.00

Agent votes:
  market_analysis: APPROVED  
  risk_assessment: APPROVED
  tax_strategy: APPROVED
  esg_compliance: REJECTED
  algorithmic_trading: APPROVED
```

## Supported Input Formats

### 1. CSV Format (Simplest)

**Create:** Excel → Save As → CSV
**Required columns:**
- ticker, shares, current_price, cost_basis, acquisition_date, sector, esg_score, beta

**Example:**
```csv
ticker,shares,current_price,cost_basis,acquisition_date,sector,esg_score,beta
AAPL,15000,200.00,170.00,2023-03-20,Technology,72,1.2
MSFT,20000,400.00,350.00,2022-06-15,Technology,82,1.1
```

### 2. JSON Format (Most Features)

**Create:** Any text editor
**Includes:** Portfolio metadata, policy limits, investment objectives

```json
{
  "cash_balance": 3000000,
  "positions": [...],
  "policy_limits": {
    "technology_limit": 30.0,
    "esg_minimum": 60
  }
}
```

### 3. YAML Format (Readable)

**Create:** Any text editor  
**Best for:** Human-readable configuration

```yaml
cash_balance: 3000000
positions:
  - ticker: "AAPL"
    shares: 15000
    current_price: 200.00
```

### 4. Excel Format (Advanced)

**Requires:** `pip install pandas openpyxl`
**Sheets:** "Positions" (holdings) + "Config" (settings)

## Required Fields

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| ticker | Text | AAPL | Stock symbol |
| shares | Integer | 15000 | Number of shares |
| current_price | Decimal | 200.00 | Current market price |
| cost_basis | Decimal | 170.00 | Purchase price |
| acquisition_date | Date | 2023-03-20 | When purchased |
| sector | Text | Technology | Sector classification |
| esg_score | Integer | 72 | ESG rating (0-100) |
| beta | Decimal | 1.2 | Market sensitivity |

## Optional Fields (JSON/YAML only)

- `cash_balance` - Available cash
- `policy_limits` - Sector limits, ESG minimums
- `investment_objectives` - Risk tolerance, time horizon
- `constraints` - Trading restrictions

## Features

### ✅ Automatic Validation

The parser automatically checks for:
- Empty portfolios
- Invalid share counts or prices
- ESG scores out of range (0-100)
- Unusual beta values
- High sector concentration
- Negative cash

### ✅ Flexible Field Names

Parser accepts variations:
- `ticker` OR `symbol` OR `Ticker`
- `shares` OR `quantity` OR `Shares`
- `current_price` OR `price` OR `Current Price`
- `cost_basis` OR `purchase_price` OR `Cost Basis`

### ✅ Smart Date Parsing

Handles multiple date formats:
- `2023-03-20` (ISO format)
- `03/20/2023` (US format)
- Falls back to 1 year ago if missing

### ✅ Template Generation

```python
from portfolio_swarm.input_parser import PortfolioParser

parser = PortfolioParser()
parser.export_template('csv', 'my_template.csv')
parser.export_template('json', 'my_template.json')
parser.export_template('yaml', 'my_template.yaml')
```

## Programmatic Usage

```python
from portfolio_swarm.input_parser import PortfolioParser
from portfolio_swarm.orchestrator import SwarmOrchestrator
from portfolio_swarm.agents import *
from portfolio_swarm.communication import CommunicationBus

# 1. Parse file (any format)
parser = PortfolioParser()
portfolio = parser.parse_file("my_portfolio.csv")

# 2. Validate
warnings = parser.validate_portfolio(portfolio)
for w in warnings:
    print(f"Warning: {w}")

# 3. Run swarm
bus = CommunicationBus()
agents = [
    MarketAnalysisAgent(bus),
    RiskAssessmentAgent(bus),
    TaxStrategyAgent(bus),
    ESGComplianceAgent(bus),
    AlgorithmicTradingAgent(bus)
]

orchestrator = SwarmOrchestrator(agents, max_iterations=10)
result = orchestrator.run_rebalancing_swarm(portfolio)

# 4. Get results
print(f"Consensus: {result.approved}")
print(f"Trades: {len(result.trade_plan.trades)}")
```

## Next Steps

1. **Try the samples:**
   ```bash
   python file_input_demo.py samples\sample_portfolio.csv
   ```

2. **Create your own file:**
   - Copy a sample file
   - Edit with your portfolio data
   - Run the demo

3. **Export a template:**
   ```bash
   python file_input_demo.py
   # Select option 4
   ```

4. **Integrate into your workflow:**
   - Use CSV for simple spreadsheet data
   - Use JSON for API integration
   - Use YAML for configuration files
   - Use Excel for complex multi-sheet data

## Files Summary

```
samples/
  ├── README.md                    # Overview
  ├── USAGE.md                     # Detailed usage guide
  ├── sample_portfolio.csv         # CSV example (16 positions)
  ├── sample_portfolio.json        # JSON example (9 positions)
  ├── sample_portfolio.yaml        # YAML example (4 positions)
  ├── sample_questions.txt         # Q&A guide
  ├── template.csv                 # Blank CSV template
  └── template.json                # Blank JSON template

portfolio_swarm/
  └── input_parser.py              # Universal parser (400+ lines)

file_input_demo.py                 # Complete working demo (210+ lines)
```

## Troubleshooting

**"No module named 'portfolio_swarm'"**
→ Run: `set PYTHONPATH=%CD%`

**"PyYAML not installed"** (for YAML files)
→ Run: `pip install pyyaml`

**"Pandas not installed"** (for Excel files)
→ Run: `pip install pandas openpyxl`

**"KeyError: 'ticker'"**
→ Check CSV has header row with correct column names

**Unicode errors on Windows**
→ Fixed in latest version (uses ASCII characters)

## Success!

The system now supports **any input format** you prefer! You can:
- ✅ Load from CSV, JSON, YAML, or Excel
- ✅ Validate automatically
- ✅ Generate blank templates
- ✅ Compare multiple files
- ✅ Run full optimization from files

All tested and working on your Windows system!
