"""
Tests for Economic Analytics Service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.economic_analytics import EconomicAnalyticsService


class TestEconomicAnalyticsService:
    """Test suite for EconomicAnalyticsService"""
    
    @pytest.fixture
    def mock_mongodb(self):
        """Mock MongoDB connection"""
        with patch('src.services.economic_analytics.MongoClient') as mock_client:
            mock_db = Mock()
            mock_client.return_value = Mock(
                admin=Mock(command=Mock(return_value=True)),
                asteroids=mock_db
            )
            yield mock_db
    
    @pytest.fixture
    def analytics_service(self, mock_mongodb):
        """Create analytics service with mocked MongoDB"""
        with patch.dict('os.environ', {'MONGODB_URI': 'mongodb://localhost:27017/test'}):
            service = EconomicAnalyticsService()
            service.db = mock_mongodb
            return service
    
    @pytest.mark.asyncio
    async def test_get_historical_mission_performance_empty(self, analytics_service):
        """Test historical performance with no missions"""
        analytics_service.missions.find.return_value = []
        
        result = await analytics_service.get_historical_mission_performance()
        
        assert result["total_missions"] == 0
        assert result["total_revenue"] == 0
        assert result["total_costs"] == 0
    
    @pytest.mark.asyncio
    async def test_get_profit_loss_trends_empty(self, analytics_service):
        """Test profit/loss trends with no missions"""
        analytics_service.missions.find.return_value = []
        
        result = await analytics_service.get_profit_loss_trends()
        
        assert result["weekly_trend"] == []
        assert result["monthly_trend"] == []
    
    @pytest.mark.asyncio
    async def test_get_commodity_price_history(self, analytics_service):
        """Test commodity price history retrieval"""
        analytics_service.market_prices.find.return_value = []
        
        result = await analytics_service.get_commodity_price_history()
        
        assert "commodities" in result
        assert "Gold" in result["commodities"]
        assert "current_price" in result["commodities"]["Gold"]
    
    @pytest.mark.asyncio
    async def test_get_roi_analysis_empty(self, analytics_service):
        """Test ROI analysis with no missions"""
        analytics_service.missions.find.return_value = []
        
        result = await analytics_service.get_roi_analysis()
        
        assert result["total_missions"] == 0
        assert result["average_roi"] == 0
    
    @pytest.mark.asyncio
    async def test_get_economic_dashboard_data(self, analytics_service):
        """Test comprehensive dashboard data retrieval"""
        analytics_service.missions.find.return_value = []
        analytics_service.market_prices.find.return_value = []
        
        result = await analytics_service.get_economic_dashboard_data()
        
        assert "historical_performance" in result
        assert "profit_loss_trends" in result
        assert "commodity_price_history" in result
        assert "roi_analysis" in result

