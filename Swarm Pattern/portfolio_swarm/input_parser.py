"""
Universal Portfolio Input Parser
Supports CSV, JSON, YAML, Excel, and plain text formats
"""
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pathlib import Path
from portfolio_swarm.models import Portfolio, Position


class PortfolioParser:
    """
    Universal parser for portfolio data in multiple formats
    
    Supported formats:
    - CSV (.csv)
    - JSON (.json)
    - YAML (.yaml, .yml)
    - Excel (.xlsx, .xls)
    - Text Q&A (.txt)
    """
    
    def __init__(self):
        self.supported_formats = ['.csv', '.json', '.yaml', '.yml', '.xlsx', '.xls', '.txt']
    
    def parse_file(self, file_path: str) -> Portfolio:
        """
        Parse portfolio from any supported file format
        
        Args:
            file_path: Path to input file
            
        Returns:
            Portfolio object
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            return self.parse_csv(file_path)
        elif suffix == '.json':
            return self.parse_json(file_path)
        elif suffix in ['.yaml', '.yml']:
            return self.parse_yaml(file_path)
        elif suffix in ['.xlsx', '.xls']:
            return self.parse_excel(file_path)
        elif suffix == '.txt':
            return self.parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    
    def parse_csv(self, file_path: str) -> Portfolio:
        """Parse CSV file with position data"""
        positions = []
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                position = self._create_position_from_dict(row)
                positions.append(position)
        
        # Use defaults for cash and limits
        return Portfolio(
            positions=positions,
            cash=1000000.0,  # Default $1M cash
            policy_limits={"technology_limit": 30.0}
        )
    
    def parse_json(self, file_path: str) -> Portfolio:
        """Parse JSON file with complete portfolio data"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Parse positions
        positions = []
        for pos_data in data.get('positions', []):
            position = self._create_position_from_dict(pos_data)
            positions.append(position)
        
        # Parse cash and limits
        cash = data.get('cash_balance', data.get('cash', 1000000.0))
        policy_limits = data.get('policy_limits', {})
        
        return Portfolio(
            positions=positions,
            cash=float(cash),
            policy_limits=policy_limits
        )
    
    def parse_yaml(self, file_path: str) -> Portfolio:
        """Parse YAML file with portfolio data"""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML not installed. Run: pip install pyyaml")
        
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse positions
        positions = []
        for pos_data in data.get('positions', []):
            position = self._create_position_from_dict(pos_data)
            positions.append(position)
        
        # Parse cash and limits
        cash = data.get('cash_balance', data.get('cash', 1000000.0))
        policy_limits = data.get('policy_limits', {})
        
        return Portfolio(
            positions=positions,
            cash=float(cash),
            policy_limits=policy_limits
        )
    
    def parse_excel(self, file_path: str) -> Portfolio:
        """Parse Excel file with portfolio data"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas not installed. Run: pip install pandas openpyxl")
        
        # Read positions sheet
        df = pd.read_excel(file_path, sheet_name='Positions')
        
        positions = []
        for _, row in df.iterrows():
            position = self._create_position_from_dict(row.to_dict())
            positions.append(position)
        
        # Try to read config sheet
        try:
            config_df = pd.read_excel(file_path, sheet_name='Config')
            cash = float(config_df[config_df['Parameter'] == 'Cash']['Value'].iloc[0])
        except:
            cash = 1000000.0
        
        return Portfolio(
            positions=positions,
            cash=cash,
            policy_limits={"technology_limit": 30.0}
        )
    
    def parse_text(self, file_path: str) -> Portfolio:
        """Parse text file with natural language descriptions"""
        from portfolio_swarm.text_parser import parse_portfolio_text
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use the advanced text parser to extract portfolio data
        return parse_portfolio_text(content)
    
    def _create_position_from_dict(self, data: Dict) -> Position:
        """
        Create Position object from dictionary data
        Handles various field name variations
        """
        # Extract ticker
        ticker = data.get('ticker') or data.get('symbol') or data.get('Ticker')
        
        # Extract shares
        shares = int(data.get('shares') or data.get('quantity') or data.get('Shares') or 0)
        
        # Extract prices
        current_price = float(data.get('current_price') or data.get('price') or 
                            data.get('Current Price') or 0)
        cost_basis = float(data.get('cost_basis') or data.get('purchase_price') or 
                          data.get('Cost Basis') or current_price)
        
        # Extract date
        acq_date_str = data.get('acquisition_date') or data.get('purchase_date') or \
                       data.get('Acquisition Date')
        if acq_date_str:
            if isinstance(acq_date_str, str):
                try:
                    acquisition_date = datetime.strptime(acq_date_str, '%Y-%m-%d')
                except:
                    # Try other formats
                    try:
                        acquisition_date = datetime.strptime(acq_date_str, '%m/%d/%Y')
                    except:
                        acquisition_date = datetime.now() - timedelta(days=365)
            else:
                acquisition_date = acq_date_str
        else:
            acquisition_date = datetime.now() - timedelta(days=365)
        
        # Extract sector
        sector = data.get('sector') or data.get('Sector') or 'Unknown'
        
        # Extract ESG score
        esg_score = int(data.get('esg_score') or data.get('ESG Score') or 70)
        
        # Extract beta
        beta = float(data.get('beta') or data.get('Beta') or 1.0)
        
        return Position(
            ticker=ticker,
            shares=shares,
            current_price=current_price,
            cost_basis=cost_basis,
            acquisition_date=acquisition_date,
            sector=sector,
            esg_score=esg_score,
            beta=beta
        )
    
    def validate_portfolio(self, portfolio: Portfolio) -> List[str]:
        """
        Validate portfolio data and return list of warnings/errors
        
        Returns:
            List of validation messages (empty if all valid)
        """
        warnings = []
        
        # Check for empty portfolio
        if not portfolio.positions:
            warnings.append("ERROR: Portfolio has no positions")
        
        # Check each position
        for i, pos in enumerate(portfolio.positions, 1):
            if pos.shares <= 0:
                warnings.append(f"WARNING: Position {i} ({pos.ticker}) has invalid shares: {pos.shares}")
            
            if pos.current_price <= 0:
                warnings.append(f"WARNING: Position {i} ({pos.ticker}) has invalid price: {pos.current_price}")
            
            if pos.esg_score < 0 or pos.esg_score > 100:
                warnings.append(f"WARNING: Position {i} ({pos.ticker}) has invalid ESG score: {pos.esg_score}")
            
            if pos.beta < 0.1 or pos.beta > 3.0:
                warnings.append(f"INFO: Position {i} ({pos.ticker}) has unusual beta: {pos.beta}")
        
        # Check cash
        if portfolio.cash < 0:
            warnings.append("WARNING: Negative cash balance")
        
        # Check for extreme concentration
        sector_alloc = portfolio.sector_allocation
        for sector, pct in sector_alloc.items():
            if pct > 50:
                warnings.append(f"WARNING: High concentration in {sector}: {pct:.1f}%")
        
        return warnings
    
    def export_template(self, format: str, output_path: str):
        """
        Export an empty template in specified format
        
        Args:
            format: 'csv', 'json', 'yaml', or 'excel'
            output_path: Where to save the template
        """
        if format == 'csv':
            self._export_csv_template(output_path)
        elif format == 'json':
            self._export_json_template(output_path)
        elif format == 'yaml':
            self._export_yaml_template(output_path)
        elif format == 'excel':
            self._export_excel_template(output_path)
    
    def _export_csv_template(self, output_path: str):
        """Export CSV template"""
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ticker', 'shares', 'current_price', 'cost_basis', 
                'acquisition_date', 'sector', 'esg_score', 'beta'
            ])
            writer.writerow([
                'AAPL', '1000', '150.00', '140.00', 
                '2023-01-15', 'Technology', '72', '1.2'
            ])
    
    def _export_json_template(self, output_path: str):
        """Export JSON template"""
        template = {
            "portfolio_name": "My Portfolio",
            "cash_balance": 1000000,
            "positions": [
                {
                    "ticker": "AAPL",
                    "shares": 1000,
                    "current_price": 150.00,
                    "cost_basis": 140.00,
                    "acquisition_date": "2023-01-15",
                    "sector": "Technology",
                    "esg_score": 72,
                    "beta": 1.2
                }
            ],
            "policy_limits": {
                "technology_limit": 30.0,
                "esg_minimum": 60
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(template, f, indent=2)
    
    def _export_yaml_template(self, output_path: str):
        """Export YAML template"""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML not installed")
        
        template = {
            "portfolio_name": "My Portfolio",
            "cash_balance": 1000000,
            "positions": [
                {
                    "ticker": "AAPL",
                    "shares": 1000,
                    "current_price": 150.00,
                    "cost_basis": 140.00,
                    "acquisition_date": "2023-01-15",
                    "sector": "Technology",
                    "esg_score": 72,
                    "beta": 1.2
                }
            ],
            "policy_limits": {
                "technology_limit": 30.0,
                "esg_minimum": 60
            }
        }
        
        with open(output_path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False)
    
    def _export_excel_template(self, output_path: str):
        """Export Excel template"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas not installed")
        
        # Positions sheet
        positions_data = {
            'ticker': ['AAPL'],
            'shares': [1000],
            'current_price': [150.00],
            'cost_basis': [140.00],
            'acquisition_date': ['2023-01-15'],
            'sector': ['Technology'],
            'esg_score': [72],
            'beta': [1.2]
        }
        
        # Config sheet
        config_data = {
            'Parameter': ['Cash', 'Tech Limit', 'ESG Min'],
            'Value': [1000000, 30, 60]
        }
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            pd.DataFrame(positions_data).to_excel(writer, sheet_name='Positions', index=False)
            pd.DataFrame(config_data).to_excel(writer, sheet_name='Config', index=False)


def main():
    """Example usage of the parser"""
    parser = PortfolioParser()
    
    print("="*80)
    print("PORTFOLIO INPUT PARSER - EXAMPLES")
    print("="*80)
    
    # Example 1: Parse CSV
    print("\n1. Parsing CSV file...")
    try:
        portfolio = parser.parse_file("samples/sample_portfolio.csv")
        print(f"   ✓ Loaded {len(portfolio.positions)} positions")
        print(f"   ✓ Total value: ${portfolio.total_value:,.0f}")
        
        # Validate
        warnings = parser.validate_portfolio(portfolio)
        if warnings:
            print("\n   Validation warnings:")
            for w in warnings:
                print(f"     - {w}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Example 2: Parse JSON
    print("\n2. Parsing JSON file...")
    try:
        portfolio = parser.parse_file("samples/sample_portfolio.json")
        print(f"   ✓ Loaded {len(portfolio.positions)} positions")
        print(f"   ✓ Total value: ${portfolio.total_value:,.0f}")
        print(f"   ✓ Policy limits: {portfolio.policy_limits}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Example 3: Parse YAML
    print("\n3. Parsing YAML file...")
    try:
        portfolio = parser.parse_file("samples/sample_portfolio.yaml")
        print(f"   ✓ Loaded {len(portfolio.positions)} positions")
        print(f"   ✓ Total value: ${portfolio.total_value:,.0f}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Example 4: Export templates
    print("\n4. Exporting templates...")
    try:
        parser.export_template('csv', 'samples/template.csv')
        print("   ✓ CSV template exported")
    except Exception as e:
        print(f"   ✗ CSV template error: {e}")
    
    try:
        parser.export_template('json', 'samples/template.json')
        print("   ✓ JSON template exported")
    except Exception as e:
        print(f"   ✗ JSON template error: {e}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
