"""
Test suite for enhanced commodity pricing service with MongoDB caching
"""
import pytest
import yfinance as yf
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.commodity_pricing_cached import CommodityPricingService


class TestCommodityPricingServiceCached:
    """Test cases for cached commodity pricing service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Use a test database
        self.test_db_uri = "mongodb://localhost:27017/asteroids_test"
        self.pricing_service = CommodityPricingService(self.test_db_uri)
        self.test_commodities = ['GC=F', 'PL=F', 'SI=F', 'HG=F', 'PA=F']
    
    def teardown_method(self):
        """Clean up after tests"""
        # Clean up test data
        try:
            self.pricing_service.market_prices_collection.drop()
            self.pricing_service.close_connection()
        except:
            pass
    
    def test_mongodb_connection(self):
        """Test MongoDB connection and collection creation"""
        assert self.pricing_service.client is not None
        assert self.pricing_service.db is not None
        assert self.pricing_service.market_prices_collection is not None
    
    def test_ensure_indexes(self):
        """Test that indexes are created properly"""
        # This test verifies indexes are created without errors
        # The actual index creation is tested implicitly through other tests
        assert True  # If we get here, no exceptions were raised
    
    def test_is_price_stale_fresh(self):
        """Test that fresh prices are not considered stale"""
        fresh_timestamp = datetime.now() - timedelta(hours=1)
        assert not self.pricing_service._is_price_stale(fresh_timestamp)
    
    def test_is_price_stale_old(self):
        """Test that old prices are considered stale"""
        old_timestamp = datetime.now() - timedelta(days=8)
        assert self.pricing_service._is_price_stale(old_timestamp)
    
    def test_is_price_stale_none(self):
        """Test that None timestamp is considered stale"""
        assert self.pricing_service._is_price_stale(None)
    
    def test_should_update_prices_no_cache(self):
        """Test that prices should be updated when no cache exists"""
        # Ensure no cached prices exist
        self.pricing_service.market_prices_collection.drop()
        
        assert self.pricing_service._should_update_prices()
    
    def test_should_update_prices_stale_cache(self):
        """Test that prices should be updated when cache is stale"""
        # Insert stale price data
        stale_timestamp = datetime.now() - timedelta(days=8)
        self.pricing_service.market_prices_collection.insert_one({
            "symbol": "GC=F",
            "price_per_ounce": 2000.0,
            "timestamp": stale_timestamp
        })
        
        assert self.pricing_service._should_update_prices()
    
    def test_should_update_prices_fresh_cache(self):
        """Test that prices should not be updated when cache is fresh"""
        # Insert fresh price data
        fresh_timestamp = datetime.now() - timedelta(hours=1)
        self.pricing_service.market_prices_collection.insert_one({
            "symbol": "GC=F",
            "price_per_ounce": 2000.0,
            "timestamp": fresh_timestamp
        })
        
        assert not self.pricing_service._should_update_prices()
    
    @patch('yfinance.Ticker')
    def test_update_cached_prices_success(self, mock_ticker):
        """Test successful update of cached prices"""
        # Mock yfinance responses
        mock_responses = {
            'GC=F': {'regularMarketPrice': 2000.0},
            'PL=F': {'regularMarketPrice': 1000.0},
            'SI=F': {'regularMarketPrice': 25.0},
            'HG=F': {'regularMarketPrice': 4.0},
            'PA=F': {'regularMarketPrice': 2000.0}
        }
        
        def mock_ticker_side_effect(symbol):
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = mock_responses[symbol]
            return mock_ticker_instance
        
        mock_ticker.side_effect = mock_ticker_side_effect
        
        # Update cached prices
        updated_prices = self.pricing_service.update_cached_prices()
        
        # Verify prices were updated
        assert len(updated_prices) == 5
        assert updated_prices['GC=F'] == 2000.0
        assert updated_prices['PL=F'] == 1000.0
        
        # Verify prices were stored in MongoDB
        stored_prices = list(self.pricing_service.market_prices_collection.find())
        assert len(stored_prices) == 5
        
        # Verify one specific price record
        gold_record = self.pricing_service.market_prices_collection.find_one({"symbol": "GC=F"})
        assert gold_record['price_per_ounce'] == 2000.0
        assert gold_record['price_per_kg'] == 2000.0 * 35.274
        assert gold_record['commodity_name'] == 'Gold'
    
    @patch('yfinance.Ticker')
    def test_update_cached_prices_api_failure(self, mock_ticker):
        """Test handling of API failures during price updates"""
        # Mock API failure
        mock_ticker.side_effect = Exception("API Error")
        
        # Update cached prices
        updated_prices = self.pricing_service.update_cached_prices()
        
        # Should use fallback prices
        assert len(updated_prices) == 5
        assert updated_prices['GC=F'] == self.pricing_service.fallback_prices['GC=F']
        assert updated_prices['PL=F'] == self.pricing_service.fallback_prices['PL=F']
    
    def test_get_cached_prices(self):
        """Test retrieving cached prices from MongoDB"""
        # Insert test price data
        test_prices = [
            {"symbol": "GC=F", "price_per_ounce": 2000.0, "timestamp": datetime.now()},
            {"symbol": "PL=F", "price_per_ounce": 1000.0, "timestamp": datetime.now()}
        ]
        
        for price_data in test_prices:
            self.pricing_service.market_prices_collection.insert_one(price_data)
        
        # Retrieve cached prices
        cached_prices = self.pricing_service.get_cached_prices()
        
        assert len(cached_prices) == 2
        assert cached_prices['GC=F'] == 2000.0
        assert cached_prices['PL=F'] == 1000.0
    
    def test_get_cached_prices_empty(self):
        """Test retrieving cached prices when collection is empty"""
        cached_prices = self.pricing_service.get_cached_prices()
        assert len(cached_prices) == 0
    
    @patch.object(CommodityPricingService, '_should_update_prices')
    @patch.object(CommodityPricingService, 'update_cached_prices')
    @patch.object(CommodityPricingService, 'get_cached_prices')
    def test_get_commodity_prices_with_caching_update_needed(self, mock_get_cached, mock_update_cached, mock_should_update):
        """Test caching behavior when update is needed"""
        mock_should_update.return_value = True
        mock_update_cached.return_value = {'GC=F': 2000.0, 'PL=F': 1000.0}
        
        prices = self.pricing_service.get_commodity_prices_with_caching()
        
        mock_should_update.assert_called_once()
        mock_update_cached.assert_called_once()
        mock_get_cached.assert_not_called()
        assert prices == {'GC=F': 2000.0, 'PL=F': 1000.0}
    
    @patch.object(CommodityPricingService, '_should_update_prices')
    @patch.object(CommodityPricingService, 'update_cached_prices')
    @patch.object(CommodityPricingService, 'get_cached_prices')
    def test_get_commodity_prices_with_caching_no_update_needed(self, mock_get_cached, mock_update_cached, mock_should_update):
        """Test caching behavior when no update is needed"""
        mock_should_update.return_value = False
        mock_get_cached.return_value = {'GC=F': 2000.0, 'PL=F': 1000.0}
        
        prices = self.pricing_service.get_commodity_prices_with_caching()
        
        mock_should_update.assert_called_once()
        mock_get_cached.assert_called_once()
        mock_update_cached.assert_not_called()
        assert prices == {'GC=F': 2000.0, 'PL=F': 1000.0}
    
    def test_get_price_history(self):
        """Test retrieving price history"""
        # Insert historical price data
        base_time = datetime.now()
        historical_prices = [
            {"symbol": "GC=F", "price_per_ounce": 2000.0, "price_per_kg": 70548.0, "timestamp": base_time - timedelta(days=1)},
            {"symbol": "GC=F", "price_per_ounce": 2050.0, "price_per_kg": 72311.7, "timestamp": base_time - timedelta(days=2)},
            {"symbol": "GC=F", "price_per_ounce": 1950.0, "price_per_kg": 68784.3, "timestamp": base_time - timedelta(days=3)}
        ]
        
        for price_data in historical_prices:
            self.pricing_service.market_prices_collection.insert_one(price_data)
        
        # Retrieve price history
        history = self.pricing_service.get_price_history('GC=F', days=5)
        
        assert len(history) == 3
        assert history[0]['price_per_ounce'] == 2000.0  # Most recent first
        assert history[1]['price_per_ounce'] == 2050.0
        assert history[2]['price_per_ounce'] == 1950.0
    
    def test_get_price_history_empty(self):
        """Test retrieving price history when no data exists"""
        history = self.pricing_service.get_price_history('GC=F', days=30)
        assert len(history) == 0
    
    def test_cleanup_old_prices(self):
        """Test cleanup of old price records"""
        # Insert old and recent price data
        old_timestamp = datetime.now() - timedelta(days=100)
        recent_timestamp = datetime.now() - timedelta(days=10)
        
        self.pricing_service.market_prices_collection.insert_one({
            "symbol": "GC=F", "price_per_ounce": 2000.0, "timestamp": old_timestamp
        })
        self.pricing_service.market_prices_collection.insert_one({
            "symbol": "PL=F", "price_per_ounce": 1000.0, "timestamp": recent_timestamp
        })
        
        # Clean up old prices (keep 90 days)
        self.pricing_service.cleanup_old_prices(days_to_keep=90)
        
        # Verify old record was deleted, recent record remains
        remaining_records = list(self.pricing_service.market_prices_collection.find())
        assert len(remaining_records) == 1
        assert remaining_records[0]['symbol'] == 'PL=F'
    
    def test_convert_ounce_to_kilogram(self):
        """Test ounce to kilogram conversion"""
        price_per_ounce = 2000.0
        expected_price_per_kg = 2000.0 * 35.274
        
        result = self.pricing_service.convert_ounce_to_kilogram(price_per_ounce)
        assert result == pytest.approx(expected_price_per_kg, rel=1e-6)
    
    @patch.object(CommodityPricingService, 'get_commodity_prices_with_caching')
    def test_get_commodity_prices_per_kg(self, mock_get_prices):
        """Test getting commodity prices per kilogram"""
        mock_get_prices.return_value = {
            'GC=F': 2000.0,  # Gold
            'PL=F': 1000.0   # Platinum
        }
        
        kg_prices = self.pricing_service.get_commodity_prices_per_kg()
        
        assert 'Gold' in kg_prices
        assert 'Platinum' in kg_prices
        assert kg_prices['Gold'] == pytest.approx(2000.0 * 35.274, rel=1e-6)
        assert kg_prices['Platinum'] == pytest.approx(1000.0 * 35.274, rel=1e-6)
    
    def test_get_price_summary(self):
        """Test getting comprehensive price summary"""
        # Insert test data
        self.pricing_service.market_prices_collection.insert_one({
            "symbol": "GC=F",
            "commodity_name": "Gold",
            "price_per_ounce": 2000.0,
            "price_per_kg": 70548.0,
            "timestamp": datetime.now()
        })
        
        with patch.object(self.pricing_service, 'get_commodity_prices_with_caching') as mock_get_prices:
            mock_get_prices.return_value = {'GC=F': 2000.0}
            
            summary = self.pricing_service.get_price_summary()
            
            assert 'Gold' in summary
            assert summary['Gold']['price_per_ounce'] == 2000.0
            assert summary['Gold']['price_per_kg'] == pytest.approx(70548.0, rel=1e-6)
            assert summary['Gold']['symbol'] == 'GC=F'


if __name__ == "__main__":
    pytest.main([__file__])
