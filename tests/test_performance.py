"""
Performance and load tests
"""
import pytest
import time
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


@pytest.mark.slow
@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints"""
    
    @patch('api.get_db')
    def test_health_check_performance(self, mock_get_db):
        """Test health check response time"""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.1  # Should respond in under 100ms
    
    @patch('api.get_db')
    def test_asteroids_endpoint_performance(self, mock_get_db):
        """Test asteroids endpoint response time"""
        mock_db = Mock()
        mock_db.get_asteroids = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        start = time.time()
        response = client.get("/api/asteroids?limit=100")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5  # Should respond in under 500ms
    
    @patch('api.get_db')
    def test_missions_endpoint_performance(self, mock_get_db):
        """Test missions endpoint response time"""
        mock_db = Mock()
        mock_db.get_missions = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        start = time.time()
        response = client.get("/api/missions")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5  # Should respond in under 500ms
    
    @patch('api.CommodityPricingService')
    def test_commodity_prices_performance(self, mock_pricing):
        """Test commodity prices endpoint response time"""
        mock_service = Mock()
        mock_service.get_commodity_prices_per_kg = Mock(return_value={
            "Gold": 70548.0,
            "Platinum": 35274.0
        })
        mock_pricing.return_value = mock_service
        
        start = time.time()
        response = client.get("/api/commodity-prices")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in under 1 second (includes API call)
    
    @patch('api.get_db')
    def test_concurrent_requests(self, mock_get_db):
        """Test handling concurrent requests"""
        mock_db = Mock()
        mock_db.get_asteroids = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        import threading
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.get("/api/asteroids?limit=10")
                results.append(response.status_code == 200)
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert all(results)


@pytest.mark.slow
@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database operations"""
    
    @patch('api.get_db')
    def test_pagination_performance(self, mock_get_db):
        """Test pagination query performance"""
        mock_db = Mock()
        mock_db.get_asteroids = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        # Test different page sizes
        for limit in [10, 50, 100, 500]:
            start = time.time()
            response = client.get(f"/api/asteroids?limit={limit}&skip=0")
            elapsed = time.time() - start
            
            assert response.status_code == 200
            # Larger pages should take slightly longer, but still reasonable
            assert elapsed < 1.0
    
    @patch('api.get_db')
    def test_query_optimization(self, mock_get_db):
        """Test that queries are optimized"""
        mock_db = Mock()
        mock_db.get_asteroids = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        # Test that get_asteroids is called with correct parameters
        response = client.get("/api/asteroids?limit=50&skip=100")
        mock_db.get_asteroids.assert_called_once_with(50, 100)

