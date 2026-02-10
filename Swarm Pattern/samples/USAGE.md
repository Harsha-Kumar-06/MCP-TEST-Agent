# Using Sample Input Files - Quick Start

## Available Sample Files

The `samples/` directory contains pre-filled portfolio examples in multiple formats:

1. **sample_portfolio.csv** - 16 positions, $60M portfolio (CSV format)
2. **sample_portfolio.json** - 9 positions, $39M portfolio with full metadata (JSON format)  
3. **sample_portfolio.yaml** - 4 positions, $23M portfolio (YAML format)
4. **sample_questions.txt** - Complete questionnaire for manual input

## Quick Usage

### Option 1: Use File Input Demo (Easiest)

```bash
# Set Python path
set PYTHONPATH=%CD%

# Run with any sample file
python file_input_demo.py samples\sample_portfolio.csv
python file_input_demo.py samples\sample_portfolio.json
python file_input_demo.py samples\sample_portfolio.yaml

# Interactive file selector
python file_input_demo.py
```

### Option 2: Programmatic Use

```python
from portfolio_swarm.input_parser import PortfolioParser
from portfolio_swarm.orchestrator import SwarmOrchestrator
from portfolio_swarm.agents import *
from portfolio_swarm.communication import CommunicationBus

# Parse any format
parser = PortfolioParser()
portfolio = parser.parse_file("samples/sample_portfolio.json")

# Validate
warnings = parser.validate_portfolio(portfolio)
for w in warnings:
    print(f"Warning: {w}")

# Run optimization
bus = CommunicationBus()
agents = [
    MarketAnalysisAgent(bus),
    RiskAssessmentAgent(bus),
    TaxStrategyAgent(bus),
    ESGComplianceAgent(bus),
    AlgorithmicTradingAgent(bus)
]

orchestrator = SwarmOrchestrator(agents)
result = orchestrator.run_rebalancing_swarm(portfolio)

print(f"Consensus: {result.approved}")
print(f"Approval rate: {result.approval_rate:.1%}")
```

### Option 3: Create Your Own File

```bash
# Export blank templates
python -c "from portfolio_swarm.input_parser import PortfolioParser; p = PortfolioParser(); p.export_template('csv', 'my_portfolio.csv')"

# Or use interactive CLI
python cli_interface.py
```

## File Format Details

### CSV Format (samples/sample_portfolio.csv)

**Required columns:**
- `ticker` - Stock symbol (e.g., AAPL)
- `shares` - Number of shares owned
- `current_price` - Current market price per share
- `cost_basis` - Original purchase price
- `acquisition_date` - Purchase date (YYYY-MM-DD)
- `sector` - Sector classification
- `esg_score` - ESG rating (0-100)
- `beta` - Market sensitivity measure

**Example:**
```csv
ticker,shares,current_price,cost_basis,acquisition_date,sector,esg_score,beta
AAPL,15000,200.00,170.00,2023-03-20,Technology,72,1.2
MSFT,20000,400.00,350.00,2022-06-15,Technology,82,1.1
```

### JSON Format (samples/sample_portfolio.json)

**Structure:**
```json
{
  "portfolio_name": "My Portfolio",
  "cash_balance": 3000000,
  "positions": [
    {
      "ticker": "AAPL",
      "shares": 15000,
      "current_price": 200.00,
      "cost_basis": 170.00,
      "acquisition_date": "2023-03-20",
      "sector": "Technology",
      "esg_score": 72,
      "beta": 1.2
    }
  ],
  "policy_limits": {
    "technology_limit": 30.0,
    "esg_minimum": 60,
    "max_beta": 1.5
  }
}
```

### YAML Format (samples/sample_portfolio.yaml)

**Structure:**
```yaml
portfolio_name: "My Portfolio"
cash_balance: 3000000
positions:
  - ticker: "AAPL"
    shares: 15000
    current_price: 200.00
    cost_basis: 170.00
    acquisition_date: "2023-03-20"
    sector: "Technology"
    esg_score: 72
    beta: 1.2
policy_limits:
  technology_limit: 30.0
  esg_minimum: 60
```

## Testing Your File

```bash
# Test parsing only
set PYTHONPATH=%CD%
python portfolio_swarm\input_parser.py

# Full optimization
python file_input_demo.py your_portfolio.csv
```

## Common Issues

### Issue: "No module named 'portfolio_swarm'"
**Solution:** Set PYTHONPATH first:
```bash
set PYTHONPATH=%CD%
```

### Issue: "KeyError: 'ticker'"
**Solution:** Ensure CSV has proper header row with required column names

### Issue: "ValueError: invalid literal for int()"
**Solution:** Check that numeric fields (shares, prices) contain valid numbers

### Issue: YAML parsing fails
**Solution:** Install PyYAML:
```bash
pip install pyyaml
```

### Issue: Excel parsing fails
**Solution:** Install required packages:
```bash
pip install pandas openpyxl
```

## Validation

The parser automatically validates:
- ✓ Non-empty portfolio
- ✓ Positive shares and prices
- ✓ ESG scores in range 0-100
- ✓ Beta values are reasonable
- ⚠️ High sector concentration
- ⚠️ Negative cash balance

## Next Steps

1. Try running one of the sample files
2. Modify a sample file with your own data
3. Export a blank template and fill it in
4. Use the CLI interface for guided input
5. Use the web UI for visual input

## Support

- See [INPUTS_OUTPUTS.md](../INPUTS_OUTPUTS.md) for detailed field descriptions
- See [COMPLETE_GUIDE.md](../COMPLETE_GUIDE.md) for full system documentation
- See [QUICKSTART.md](../QUICKSTART.md) for basic usage

## Examples

```bash
# Compare all sample files
python file_input_demo.py
# Select option 3

# Export templates
python file_input_demo.py
# Select option 4

# Use specific file
python file_input_demo.py samples\sample_portfolio.json
```
