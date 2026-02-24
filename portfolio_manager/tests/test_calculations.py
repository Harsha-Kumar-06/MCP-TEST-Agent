"""
Portfolio Manager Tests

Unit tests for the portfolio manager tools and calculations.
Run with: pytest portfolio_manager/tests/test_calculations.py -v
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.calculations import (
    calculate_sharpe_ratio,
    calculate_portfolio_volatility,
    calculate_correlation_matrix,
    calculate_max_drawdown,
    calculate_beta,
    calculate_portfolio_return,
    calculate_var
)


class TestSharpeRatio:
    """Tests for Sharpe ratio calculation."""
    
    def test_sharpe_ratio_positive_returns(self):
        """Test Sharpe ratio with positive returns."""
        returns = [0.01, 0.02, 0.015, 0.008, 0.012, 0.018, 0.005, 0.022, 0.011, 0.009]
        result = calculate_sharpe_ratio(returns, risk_free_rate=0.05)
        
        assert "sharpe_ratio" in result
        assert result["sharpe_ratio"] > 0
        assert result["interpretation"] in ["excellent", "very_good", "good", "adequate", "poor"]
    
    def test_sharpe_ratio_negative_returns(self):
        """Test Sharpe ratio with negative returns."""
        returns = [-0.01, -0.02, -0.015, 0.005, -0.012]
        result = calculate_sharpe_ratio(returns, risk_free_rate=0.05)
        
        assert result["sharpe_ratio"] < 0
        assert result["interpretation"] == "poor"
    
    def test_sharpe_ratio_insufficient_data(self):
        """Test Sharpe ratio with insufficient data."""
        result = calculate_sharpe_ratio([0.01])
        
        assert "error" in result
        assert result["interpretation"] == "insufficient_data"


class TestPortfolioVolatility:
    """Tests for portfolio volatility calculation."""
    
    def test_volatility_calculation(self):
        """Test basic volatility calculation."""
        weights = [0.6, 0.4]
        returns_matrix = [
            [0.01, 0.02, -0.01, 0.015, 0.008],  # Stock 1
            [0.015, 0.01, -0.005, 0.02, 0.005]   # Stock 2
        ]
        
        result = calculate_portfolio_volatility(weights, returns_matrix)
        
        assert "portfolio_volatility" in result
        assert "annualized_volatility" in result
        assert result["portfolio_volatility"] > 0
    
    def test_volatility_weights_mismatch(self):
        """Test error when weights don't match returns."""
        weights = [0.5, 0.5]
        returns_matrix = [[0.01, 0.02]]  # Only one stock
        
        result = calculate_portfolio_volatility(weights, returns_matrix)
        
        assert "error" in result
    
    def test_volatility_weights_not_sum_to_one(self):
        """Test error when weights don't sum to 1."""
        weights = [0.6, 0.6]  # Sums to 1.2
        returns_matrix = [[0.01, 0.02], [0.015, 0.01]]
        
        result = calculate_portfolio_volatility(weights, returns_matrix)
        
        assert "error" in result


class TestCorrelationMatrix:
    """Tests for correlation matrix calculation."""
    
    def test_correlation_matrix_positive(self):
        """Test correlation between positively correlated stocks."""
        returns_dict = {
            "AAPL": [0.01, 0.02, 0.015, 0.008, 0.012],
            "MSFT": [0.012, 0.018, 0.014, 0.009, 0.011]
        }
        
        result = calculate_correlation_matrix(returns_dict)
        
        assert "correlations" in result
        assert "AAPL-MSFT" in result["correlations"]
        assert result["correlations"]["AAPL-MSFT"] > 0
    
    def test_correlation_diversification_score(self):
        """Test diversification score calculation."""
        returns_dict = {
            "STOCK_A": [0.01, 0.02, 0.03, 0.04, 0.05],
            "STOCK_B": [-0.01, 0.03, -0.02, 0.04, -0.03]  # Negatively correlated
        }
        
        result = calculate_correlation_matrix(returns_dict)
        
        assert "diversification_score" in result
        assert 0 <= result["diversification_score"] <= 100
    
    def test_correlation_insufficient_stocks(self):
        """Test error with single stock."""
        result = calculate_correlation_matrix({"AAPL": [0.01, 0.02, 0.03]})
        
        assert "error" in result


class TestMaxDrawdown:
    """Tests for maximum drawdown calculation."""
    
    def test_drawdown_basic(self):
        """Test basic drawdown calculation."""
        prices = [100, 110, 105, 95, 100, 90, 95, 100, 105]
        
        result = calculate_max_drawdown(prices)
        
        assert "max_drawdown" in result
        assert result["max_drawdown"] < 0  # Drawdown should be negative
        assert abs(result["max_drawdown"]) > 0
    
    def test_drawdown_interpretation(self):
        """Test drawdown risk interpretation."""
        # Large drawdown
        prices = [100, 50, 60, 55]  # 50% drawdown
        result = calculate_max_drawdown(prices)
        
        assert result["interpretation"] in ["low_risk", "moderate_risk", "high_risk", "very_high_risk"]
    
    def test_drawdown_insufficient_data(self):
        """Test error with insufficient data."""
        result = calculate_max_drawdown([100])
        
        assert "error" in result


class TestBeta:
    """Tests for beta calculation."""
    
    def test_beta_market_aligned(self):
        """Test beta for stock aligned with market."""
        stock_returns = [0.01, 0.02, -0.01, 0.015, 0.008]
        market_returns = [0.008, 0.015, -0.008, 0.012, 0.006]
        
        result = calculate_beta(stock_returns, market_returns)
        
        assert "beta" in result
        assert result["beta"] > 0
    
    def test_beta_interpretation(self):
        """Test beta interpretation."""
        stock_returns = [0.02, 0.03, -0.02, 0.025]
        market_returns = [0.01, 0.015, -0.01, 0.012]
        
        result = calculate_beta(stock_returns, market_returns)
        
        assert result["interpretation"] in ["defensive", "conservative", "moderate", "aggressive"]


class TestPortfolioReturn:
    """Tests for portfolio return calculation."""
    
    def test_return_calculation(self):
        """Test weighted return calculation."""
        weights = [0.6, 0.4]
        returns = [0.10, 0.05]  # 10% and 5%
        
        result = calculate_portfolio_return(weights, returns)
        
        assert "portfolio_return" in result
        # 0.6 * 0.10 + 0.4 * 0.05 = 0.08 (8%)
        assert abs(result["portfolio_return"] - 0.08) < 0.001
    
    def test_return_contributions(self):
        """Test contribution breakdown."""
        weights = [0.5, 0.5]
        returns = [0.10, 0.02]
        
        result = calculate_portfolio_return(weights, returns)
        
        assert "contributions" in result
        assert len(result["contributions"]) == 2


class TestValueAtRisk:
    """Tests for Value at Risk calculation."""
    
    def test_var_calculation(self):
        """Test basic VaR calculation."""
        returns = [0.01, -0.02, 0.015, -0.03, 0.02, -0.01, 0.008, -0.025, 0.012, -0.015]
        
        result = calculate_var(returns, confidence_level=0.95, portfolio_value=10000)
        
        assert "var_percent" in result
        assert "var_dollar" in result
        assert result["var_percent"] < 0  # VaR should be negative (loss)
    
    def test_var_insufficient_data(self):
        """Test error with insufficient data."""
        result = calculate_var([0.01, 0.02, 0.03], confidence_level=0.95, portfolio_value=10000)
        
        assert "error" in result


# Integration test for portfolio workflow
class TestPortfolioWorkflow:
    """Integration tests for portfolio construction workflow."""
    
    def test_full_calculation_workflow(self):
        """Test a complete calculation workflow."""
        # Simulate portfolio data
        holdings = {
            "AAPL": {"weight": 0.30, "returns": [0.01, 0.02, -0.01, 0.015, 0.008] * 10},
            "MSFT": {"weight": 0.25, "returns": [0.012, 0.018, -0.008, 0.014, 0.009] * 10},
            "GOOGL": {"weight": 0.25, "returns": [0.015, 0.01, -0.005, 0.02, 0.005] * 10},
            "JNJ": {"weight": 0.20, "returns": [0.005, 0.008, 0.002, 0.006, 0.004] * 10}
        }
        
        # Calculate correlation
        returns_dict = {symbol: data["returns"] for symbol, data in holdings.items()}
        correlation_result = calculate_correlation_matrix(returns_dict)
        
        assert "diversification_score" in correlation_result
        
        # Calculate portfolio volatility
        weights = [data["weight"] for data in holdings.values()]
        returns_matrix = [data["returns"] for data in holdings.values()]
        vol_result = calculate_portfolio_volatility(weights, returns_matrix)
        
        assert "annualized_volatility" in vol_result
        
        # Calculate Sharpe ratio using portfolio returns
        portfolio_returns = []
        for i in range(len(list(holdings.values())[0]["returns"])):
            period_return = sum(
                holdings[symbol]["weight"] * holdings[symbol]["returns"][i]
                for symbol in holdings
            )
            portfolio_returns.append(period_return)
        
        sharpe_result = calculate_sharpe_ratio(portfolio_returns)
        
        assert "sharpe_ratio" in sharpe_result
        print(f"Portfolio Sharpe Ratio: {sharpe_result['sharpe_ratio']}")
        print(f"Portfolio Volatility: {vol_result['annualized_volatility']:.2%}")
        print(f"Diversification Score: {correlation_result['diversification_score']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
