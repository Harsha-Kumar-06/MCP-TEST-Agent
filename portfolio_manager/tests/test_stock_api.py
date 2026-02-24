"""
Stock API Tests

Unit tests for the Alpha Vantage API integration.
Run with: pytest portfolio_manager/tests/test_stock_api.py -v

Note: These tests use the 'demo' API key which has limited functionality.
For full testing, set ALPHA_VANTAGE_API_KEY environment variable.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.stock_api import (
    get_stock_quote,
    get_company_fundamentals,
    get_technical_indicators,
    search_stocks,
)


class TestStockQuote:
    """Tests for stock quote functionality."""
    
    @pytest.mark.integration
    def test_get_quote_valid_symbol(self):
        """Test getting quote for valid symbol."""
        # Note: Demo API key only works with specific symbols
        result = get_stock_quote("IBM")
        
        # Should return data or rate limit error
        if "error" not in result:
            assert "symbol" in result
            assert "price" in result
            assert result["price"] > 0
    
    def test_get_quote_response_structure(self):
        """Test that quote response has expected structure."""
        result = get_stock_quote("AAPL")
        
        # Even with errors, certain keys should exist or error key
        assert "error" in result or all(
            key in result for key in ["symbol", "price", "volume"]
        )


class TestCompanyFundamentals:
    """Tests for company fundamentals functionality."""
    
    @pytest.mark.integration
    def test_get_fundamentals_valid_symbol(self):
        """Test getting fundamentals for valid symbol."""
        result = get_company_fundamentals("IBM")
        
        if "error" not in result:
            assert "symbol" in result
            assert "name" in result
            assert "sector" in result
            assert "pe_ratio" in result


class TestTechnicalIndicators:
    """Tests for technical indicators functionality."""
    
    @pytest.mark.integration
    def test_get_rsi(self):
        """Test getting RSI indicator."""
        result = get_technical_indicators("IBM", "RSI")
        
        if "error" not in result:
            assert "indicator" in result
            assert result["indicator"] == "RSI"
            assert "signal" in result
    
    def test_invalid_indicator(self):
        """Test error with invalid indicator."""
        result = get_technical_indicators("IBM", "INVALID")
        
        assert "error" in result


class TestStockSearch:
    """Tests for stock search functionality."""
    
    @pytest.mark.integration
    def test_search_stocks(self):
        """Test stock search."""
        result = search_stocks("Apple")
        
        if "error" not in result:
            assert "results" in result
            assert "count" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])
