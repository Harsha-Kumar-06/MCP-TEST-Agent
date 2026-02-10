# Portfolio Input Samples

This directory contains sample portfolio data in various formats that can be used as input to the swarm system.

## Available Formats

1. **CSV** - `sample_portfolio.csv`
2. **JSON** - `sample_portfolio.json`
3. **Excel** - `sample_portfolio.xlsx` (template)
4. **YAML** - `sample_portfolio.yaml`
5. **Text Q&A** - `sample_questions.txt`

## How to Use

```python
from portfolio_swarm.input_parser import PortfolioParser

# Parse any format
parser = PortfolioParser()
portfolio = parser.parse_file("samples/sample_portfolio.csv")
# or
portfolio = parser.parse_file("samples/sample_portfolio.json")
```

## CSV Format

```csv
ticker,shares,current_price,cost_basis,acquisition_date,sector,esg_score,beta
AAPL,1000,150.00,140.00,2023-01-15,Technology,72,1.2
```

## JSON Format

```json
{
  "positions": [...],
  "cash": 1000000,
  "policy_limits": {...}
}
```

See individual files for complete examples.
