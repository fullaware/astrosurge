"""
Test suite for standalone commodity pricing service
"""
import pytest
import yfinance as yf
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.commodity_pricing_standalone import CommodityPricingService


class TestCommodityPricingServiceStandalone:
    """Test cases for standalone commodity pricing service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.pricing_service = CommodityPricingService()
        self.test_commodities = ['GC=F', 'PL=F', 'SI=F', 'HG=F', 'PA=F']
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        assert self.pricing_service.commodity_symbols is not None
        assert len(self.pricing_service.commodity_symbols) == 5
        assert self.pricing_service.OUNCES_PER_KG == 35.274
        assert self.pricing_service.fallback_prices is not None
    
    def test_is_cache_stale_fresh(self):
        """Test that fresh cache is not considered stale"""
        self.pricing_service._cache_timestamp = datetime.now() - timedelta(minutes=30)
        assert not self.pricing_service._is_cache_stale()
    
    def test_is_cache_stale_old(self):
        """Test that old cache is considered stale"""
        self.pricing_service._cache_timestamp = datetime.now() - timedelta(hours=2)
        assert self.pricing_service._is_cache_stale()
    
    def test_is_cache_stale_none(self):
        """Test that None cache timestamp is considered stale"""
        self.pricing_service._cache_timestamp = None
        assert self.pricing_service._is_cache_stale()
    
    @patch('yfinance.Ticker')
    def test_fetch_commodity_price_success(self, mock_ticker):
        """Test successful fetching of a single commodity price"""
        # Mock the yfinance response
        mock_info = {'regularMarketPrice': 2000.0}  # $2000 per ounce
        mock_ticker.return_value.info = mock_info
        
        price = self.pricing_service.fetch_commodity_price('GC=F')
        
        assert price == 2000.0
        mock_ticker.assert_called_once_with('GC=F')
    
    @patch('yfinance.Ticker')
    def test_fetch_commodity_price_api_failure(self, mock_ticker):
        """Test handling of API failure with fallback pricing"""
        # Mock API failure
        mock_ticker.side_effect = Exception("API Error")
        
        price = self.pricing_service.fetch_commodity_price('GC=F')
        
        # Should return fallback price
        assert price == self.pricing_service.fallback_prices['GC=F']
    
    @patch('yfinance.Ticker')
    def test_fetch_all_commodity_prices_success(self, mock_ticker):
        """Test fetching all commodity prices successfully"""
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
    
    def test_convert_ounce_to_kilogram(self):
        """Test conversion from per-ounce to per-kilogram pricing"""
        price_per_ounce = 2000.0
        expected_price_per_kg = 2000.0 * 35.274
        
        result = self.pricing_service.convert_ounce_to_kilogram(price_per_ounce)
        
        assert result == pytest.approx(expected_price_per_kg, rel=1e-6)
    
    @patch.object(CommodityPricingService, 'fetch_all_commodity_prices')
    def test_get_commodity_prices_per_kg_no_cache(self, mock_fetch):
        """Test getting commodity prices per kg when no cache exists"""
        mock_fetch.return_value = {
            'GC=F': 2000.0,  # Gold
            'PL=F': 1000.0   # Platinum
        }
        
        # Clear cache
        self.pricing_service._session_cache = {}
        self.pricing_service._cache_timestamp = None
        
        kg_prices = self.pricing_service.get_commodity_prices_per_kg()
        
        assert 'Gold' in kg_prices
        assert 'Platinum' in kg_prices
        assert kg_prices['Gold'] == pytest.approx(2000.0 * 35.274, rel=1e-6)
        assert kg_prices['Platinum'] == pytest.approx(1000.0 * 35.274, rel=1e-6)
        
        # Verify cache was set
        assert self.pricing_service._session_cache == kg_prices
        assert self.pricing_service._cache_timestamp is not None
    
    @patch.object(CommodityPricingService, 'fetch_all_commodity_prices')
    def test_get_commodity_prices_per_kg_with_cache(self, mock_fetch):
        """Test getting commodity prices per kg when cache exists"""
        # Set up fresh cache
        cached_prices = {
            'Gold': 70548.0,
            'Platinum': 35274.0
        }
        self.pricing_service._session_cache = cached_prices
        self.pricing_service._cache_timestamp = datetime.now() - timedelta(minutes=30)
        
        kg_prices = self.pricing_service.get_commodity_prices_per_kg()
        
        # Should return cached prices
        assert kg_prices == cached_prices
        
        # Should not call fetch_all_commodity_prices
        mock_fetch.assert_not_called()
    
    def test_get_commodity_price_per_kg_single(self):
        """Test getting price for a single commodity"""
        with patch.object(self.pricing_service, 'fetch_commodity_price') as mock_fetch:
            mock_fetch.return_value = 2000.0
            
            price = self.pricing_service.get_commodity_price_per_kg('Gold')
            
            assert price == pytest.approx(2000.0 * 35.274, rel=1e-6)
            mock_fetch.assert_called_once_with('GC=F')
    
    def test_get_commodity_price_per_kg_unknown(self):
        """Test getting price for unknown commodity"""
        price = self.pricing_service.get_commodity_price_per_kg('Unknown')
        
        assert price == 0.0
    
    @patch.object(CommodityPricingService, 'fetch_all_commodity_prices')
    def test_get_price_summary(self, mock_fetch):
        """Test getting comprehensive price summary"""
        mock_fetch.return_value = {
            'GC=F': 2000.0,  # Gold
            'PL=F': 1000.0   # Platinum
        }
        
        summary = self.pricing_service.get_price_summary()
        
        assert 'Gold' in summary
        assert 'Platinum' in summary
        
        assert summary['Gold']['price_per_ounce'] == 2000.0
        assert summary['Gold']['price_per_kg'] == pytest.approx(70548.0, rel=1e-6)
        assert summary['Gold']['symbol'] == 'GC=F'
    
    def test_validate_price_data_valid(self):
        """Test validation of valid price data"""
        valid_prices = {
            'GC=F': 2000.0,
            'PL=F': 1000.0
        }
        
        assert self.pricing_service.validate_price_data(valid_prices)
    
    def test_validate_price_data_invalid_zero(self):
        """Test validation of invalid price data (zero price)"""
        invalid_prices = {
            'GC=F': 0.0,
            'PL=F': 1000.0
        }
        
        assert not self.pricing_service.validate_price_data(invalid_prices)
    
    def test_validate_price_data_invalid_negative(self):
        """Test validation of invalid price data (negative price)"""
        invalid_prices = {
            'GC=F': -100.0,
            'PL=F': 1000.0
        }
        
        assert not self.pricing_service.validate_price_data(invalid_prices)
    
    def test_validate_price_data_out_of_range(self):
        """Test validation of price data outside reasonable range"""
        out_of_range_prices = {
            'GC=F': 50000.0,  # Way too high
            'PL=F': 1000.0
        }
        
        assert not self.pricing_service.validate_price_data(out_of_range_prices)
    
    @patch.object(CommodityPricingService, 'get_commodity_prices_per_kg')
    def test_get_mission_economics(self, mock_get_prices):
        """Test mission economics calculation"""
        mock_get_prices.return_value = {
            'Gold': 70548.0,
            'Platinum': 35274.0
        }
        
        economics = self.pricing_service.get_mission_economics(50000)
        
        assert 'Gold' in economics
        assert 'Platinum' in economics
        
        # Test Gold economics
        gold_econ = economics['Gold']
        assert gold_econ['price_per_kg'] == 70548.0
        assert gold_econ['cargo_capacity_kg'] == 50000
        assert gold_econ['total_cargo_value'] == 70548.0 * 50000
        assert gold_econ['commodity_name'] == 'Gold'
        
        # Test Platinum economics
        platinum_econ = economics['Platinum']
        assert platinum_econ['price_per_kg'] == 35274.0
        assert platinum_econ['cargo_capacity_kg'] == 50000
        assert platinum_econ['total_cargo_value'] == 35274.0 * 50000
        assert platinum_econ['commodity_name'] == 'Platinum'
    
    @patch.object(CommodityPricingService, 'get_commodity_price_per_kg')
    def test_calculate_ore_value(self, mock_get_price):
        """Test ore value calculation with ore grade"""
        mock_get_price.return_value = 35274.0  # Platinum price per kg
        
        ore_value = self.pricing_service.calculate_ore_value('Platinum', 10000, 0.1)
        
        assert ore_value['total_ore_weight_kg'] == 10000
        assert ore_value['commodity_weight_kg'] == 1000  # 10% of 10000
        assert ore_value['gangue_weight_kg'] == 9000   # 90% of 10000
        assert ore_value['ore_grade'] == 0.1
        assert ore_value['price_per_kg'] == 35274.0
        assert ore_value['commodity_value'] == 1000 * 35274.0
        assert ore_value['total_ore_value'] == 1000 * 35274.0
    
    def test_calculate_ore_value_high_grade(self):
        """Test ore value calculation with high grade ore"""
        with patch.object(self.pricing_service, 'get_commodity_price_per_kg') as mock_get_price:
            mock_get_price.return_value = 35274.0
            
            # High grade ore (50%)
            ore_value = self.pricing_service.calculate_ore_value('Platinum', 1000, 0.5)
            
            assert ore_value['commodity_weight_kg'] == 500
            assert ore_value['gangue_weight_kg'] == 500
            assert ore_value['ore_grade'] == 0.5
            assert ore_value['commodity_value'] == 500 * 35274.0
    
    def test_clear_cache(self):
        """Test cache clearing functionality"""
        # Set up cache
        self.pricing_service._session_cache = {'Gold': 70548.0}
        self.pricing_service._cache_timestamp = datetime.now()
        
        # Clear cache
        self.pricing_service.clear_cache()
        
        assert self.pricing_service._session_cache == {}
        assert self.pricing_service._cache_timestamp is None
    
    def test_fallback_prices_are_reasonable(self):
        """Test that fallback prices are reasonable market values"""
        fallback_prices = self.pricing_service.fallback_prices
        
        # Check that fallback prices are reasonable (within expected ranges)
        assert 1000 <= fallback_prices['GC=F'] <= 3000  # Gold $1000-3000/oz
        assert 500 <= fallback_prices['PL=F'] <= 2000   # Platinum $500-2000/oz
        assert 15 <= fallback_prices['SI=F'] <= 50      # Silver $15-50/oz
        assert 2 <= fallback_prices['HG=F'] <= 10       # Copper $2-10/oz
        assert 1000 <= fallback_prices['PA=F'] <= 3000  # Palladium $1000-3000/oz
    
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
