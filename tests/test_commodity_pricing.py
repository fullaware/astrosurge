"""
Test suite for yfinance commodity pricing integration
"""
import pytest
import yfinance as yf
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.commodity_pricing import CommodityPricingService


class TestCommodityPricingService:
    """Test cases for commodity pricing service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.pricing_service = CommodityPricingService()
        self.test_commodities = ['GC=F', 'PL=F', 'SI=F', 'HG=F', 'PA=F']  # Gold, Platinum, Silver, Copper, Palladium
    
    def test_fetch_single_commodity_price_success(self):
        """Test successful fetching of a single commodity price"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock the yfinance response
            mock_info = {'regularMarketPrice': 2000.0}  # $2000 per ounce
            mock_ticker.return_value.info = mock_info
            
            price = self.pricing_service.fetch_commodity_price('GC=F')
            
            assert price == 2000.0
            mock_ticker.assert_called_once_with('GC=F')
    
    def test_fetch_commodity_price_api_failure(self):
        """Test handling of API failure with fallback pricing"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock API failure
            mock_ticker.side_effect = Exception("API Error")
            
            price = self.pricing_service.fetch_commodity_price('GC=F')
            
            # Should return fallback price
            assert price == self.pricing_service.fallback_prices['GC=F']
    
    def test_convert_ounce_to_kilogram(self):
        """Test conversion from per-ounce to per-kilogram pricing"""
        price_per_ounce = 2000.0
        expected_price_per_kg = 2000.0 * 35.274  # 35.274 oz per kg
        
        result = self.pricing_service.convert_ounce_to_kilogram(price_per_ounce)
        
        assert result == pytest.approx(expected_price_per_kg, rel=1e-6)
    
    def test_fetch_all_commodity_prices_success(self):
        """Test fetching all commodity prices successfully"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock responses for different commodities
            mock_responses = {
                'GC=F': {'regularMarketPrice': 2000.0},  # Gold
                'PL=F': {'regularMarketPrice': 1000.0},   # Platinum
                'SI=F': {'regularMarketPrice': 25.0},    # Silver
                'HG=F': {'regularMarketPrice': 4.0},     # Copper
                'PA=F': {'regularMarketPrice': 2000.0}   # Palladium
            }
            
            def mock_ticker_side_effect(symbol):
                mock_ticker_instance = Mock()
                mock_ticker_instance.info = mock_responses[symbol]
                return mock_ticker_instance
            
            mock_ticker.side_effect = mock_ticker_side_effect
            
            prices = self.pricing_service.fetch_all_commodity_prices()
            
            assert len(prices) == 5
            assert prices['GC=F'] == 2000.0
            assert prices['PL=F'] == 1000.0
            assert prices['SI=F'] == 25.0
            assert prices['HG=F'] == 4.0
            assert prices['PA=F'] == 2000.0
    
    def test_fetch_all_commodity_prices_partial_failure(self):
        """Test handling of partial API failures"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock partial failure - some succeed, some fail
            def mock_ticker_side_effect(symbol):
                if symbol == 'GC=F':
                    mock_ticker_instance = Mock()
                    mock_ticker_instance.info = {'regularMarketPrice': 2000.0}
                    return mock_ticker_instance
                else:
                    raise Exception("API Error")
            
            mock_ticker.side_effect = mock_ticker_side_effect
            
            prices = self.pricing_service.fetch_all_commodity_prices()
            
            # Should have fallback prices for failed commodities
            assert prices['GC=F'] == 2000.0
            assert prices['PL=F'] == self.pricing_service.fallback_prices['PL=F']
            assert prices['SI=F'] == self.pricing_service.fallback_prices['SI=F']
    
    def test_get_commodity_prices_per_kg(self):
        """Test getting commodity prices converted to per-kilogram"""
        with patch.object(self.pricing_service, 'fetch_all_commodity_prices') as mock_fetch:
            # Mock ounce prices
            mock_fetch.return_value = {
                'GC=F': 2000.0,  # Gold $2000/oz
                'PL=F': 1000.0,  # Platinum $1000/oz
                'SI=F': 25.0,    # Silver $25/oz
                'HG=F': 4.0,     # Copper $4/oz
                'PA=F': 2000.0   # Palladium $2000/oz
            }
            
            prices_per_kg = self.pricing_service.get_commodity_prices_per_kg()
            
            # Verify conversions
            assert prices_per_kg['Gold'] == pytest.approx(2000.0 * 35.274, rel=1e-6)
            assert prices_per_kg['Platinum'] == pytest.approx(1000.0 * 35.274, rel=1e-6)
            assert prices_per_kg['Silver'] == pytest.approx(25.0 * 35.274, rel=1e-6)
            assert prices_per_kg['Copper'] == pytest.approx(4.0 * 35.274, rel=1e-6)
            assert prices_per_kg['Palladium'] == pytest.approx(2000.0 * 35.274, rel=1e-6)
    
    def test_fallback_prices_are_reasonable(self):
        """Test that fallback prices are reasonable market values"""
        fallback_prices = self.pricing_service.fallback_prices
        
        # Check that fallback prices are reasonable (within expected ranges)
        assert 1000 <= fallback_prices['GC=F'] <= 3000  # Gold $1000-3000/oz
        assert 500 <= fallback_prices['PL=F'] <= 2000   # Platinum $500-2000/oz
        assert 15 <= fallback_prices['SI=F'] <= 50      # Silver $15-50/oz
        assert 2 <= fallback_prices['HG=F'] <= 10       # Copper $2-10/oz
        assert 1000 <= fallback_prices['PA=F'] <= 3000  # Palladium $1000-3000/oz
    
    def test_error_handling_invalid_symbol(self):
        """Test error handling for invalid commodity symbols"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock invalid symbol response
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {}  # Empty info (invalid symbol)
            mock_ticker.return_value = mock_ticker_instance
            
            price = self.pricing_service.fetch_commodity_price('INVALID')
            
            # Should return fallback price for invalid symbol
            assert price == self.pricing_service.fallback_prices.get('INVALID', 0)
    
    def test_price_conversion_edge_cases(self):
        """Test edge cases for price conversion"""
        # Test zero price
        assert self.pricing_service.convert_ounce_to_kilogram(0) == 0
        
        # Test negative price (should handle gracefully)
        assert self.pricing_service.convert_ounce_to_kilogram(-100) == -3527.4
        
        # Test very large price
        large_price = 1000000
        expected = large_price * 35.274
        assert self.pricing_service.convert_ounce_to_kilogram(large_price) == pytest.approx(expected, rel=1e-6)


if __name__ == "__main__":
    pytest.main([__file__])
