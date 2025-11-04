"""
Integration tests for complete workflows
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


@pytest.mark.integration
class TestCompleteMissionWorkflow:
    """Test complete mission lifecycle workflow"""
    
    @patch('api.get_db')
    @patch('api.simulation_engine')
    def test_complete_mission_lifecycle(self, mock_engine, mock_get_db):
        """Test creating a mission and tracking its lifecycle"""
        # Setup mocks
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock asteroid
        mock_db.get_asteroid = Mock(return_value={
            "_id": "asteroid_123",
            "name": "Test Asteroid",
            "moid": 0.1,
            "elements": [{"name": "Gold", "percentage": 10}]
        })
        
        # Mock ship
        mock_db.get_ship = Mock(return_value={
            "_id": "ship_123",
            "user_id": "user_123",
            "name": "Test Ship",
            "capacity_kg": 50000,
            "status": "available"
        })
        
        # Mock mission creation
        mock_db.create_mission = Mock(return_value={
            "_id": "mission_123",
            "user_id": "user_123",
            "ship_id": "ship_123",
            "asteroid_id": "asteroid_123",
            "status": "planning",
            "current_phase": "planning"
        })
        
        # Mock mission retrieval
        mock_db.get_mission = Mock(return_value={
            "_id": "mission_123",
            "user_id": "user_123",
            "ship_id": "ship_123",
            "asteroid_id": "asteroid_123",
            "status": "active",
            "current_phase": "mining",
            "cargo": {"Gold": 1000}
        })
        
        # Create mission
        mission_data = {
            "user_id": "user_123",
            "ship_id": "ship_123",
            "asteroid_id": "asteroid_123",
            "name": "Test Mission"
        }
        response = client.post("/api/missions", json=mission_data)
        assert response.status_code == 200
        
        # Get mission status
        response = client.get("/api/missions/mission_123/results")
        assert response.status_code == 200


@pytest.mark.integration
class TestUserFleetWorkflow:
    """Test complete user and fleet management workflow"""
    
    @patch('api.get_db')
    def test_user_fleet_creation(self, mock_get_db):
        """Test creating a user and their fleet"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Create user
        mock_db.create_user = Mock(return_value={
            "_id": "user_123",
            "username": "testuser",
            "company_name": "Test Co",
            "bank_balance": 10000000.0
        })
        
        user_data = {
            "username": "testuser",
            "company_name": "Test Co",
            "bank_balance": 10000000.0,
            "investor_debt": 0.0
        }
        response = client.post("/api/users", json=user_data)
        assert response.status_code == 200
        
        # Create ships for user
        mock_db.create_ship = Mock(return_value={
            "_id": "ship_123",
            "user_id": "user_123",
            "name": "Ship 1",
            "capacity_kg": 50000
        })
        
        ship_data = {
            "user_id": "user_123",
            "name": "Ship 1",
            "capacity_kg": 50000
        }
        response = client.post("/api/ships", json=ship_data)
        assert response.status_code == 200
        
        # Get user's ships
        mock_db.get_ships = Mock(return_value=[{
            "_id": "ship_123",
            "user_id": "user_123",
            "name": "Ship 1"
        }])
        response = client.get("/api/ships")
        assert response.status_code == 200


@pytest.mark.integration
class TestEconomicAnalysisWorkflow:
    """Test economic analysis workflow"""
    
    @patch('api.get_db')
    @patch('api.CommodityPricingService')
    @patch('api.MissionEconomicsService')
    def test_mission_economic_analysis(self, mock_economics, mock_pricing, mock_get_db):
        """Test complete economic analysis for a mission"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # Mock mission with cargo
        mock_db.get_mission = Mock(return_value={
            "_id": "mission_123",
            "cargo": {
                "Gold": 1000,
                "Platinum": 500,
                "Silver": 2000
            },
            "costs": {
                "total": 5000000
            }
        })
        
        # Mock pricing service
        mock_pricing_service = Mock()
        mock_pricing_service.get_commodity_prices_per_kg = Mock(return_value={
            "Gold": 70548.0,
            "Platinum": 35274.0,
            "Silver": 881.85
        })
        mock_pricing.return_value = mock_pricing_service
        
        # Mock economics service
        mock_economics_service = Mock()
        mock_economics_service.calculate_mission_economics = Mock(return_value={
            "total_value": 100000000,
            "profit": 95000000,
            "roi": 1900.0
        })
        mock_economics.return_value = mock_economics_service
        
        # Get commodity prices
        response = client.get("/api/commodity-prices")
        assert response.status_code == 200
        
        # Get mission economics
        response = client.get("/api/missions/mission_123/economics")
        assert response.status_code == 200


@pytest.mark.integration
class TestOrbitalMechanicsWorkflow:
    """Test orbital mechanics workflow"""
    
    @patch('api.OrbitalMechanicsService')
    def test_trajectory_planning(self, mock_orbital):
        """Test complete trajectory planning workflow"""
        mock_service = Mock()
        mock_orbital.return_value = mock_service
        
        # Calculate travel time
        mock_service.calculate_travel_time = Mock(return_value={
            "one_way_time_days": 10.5,
            "total_time_days": 21.0
        })
        response = client.get("/api/orbital/travel-time?moid_au=0.1&mission_type=round_trip")
        assert response.status_code == 200
        
        # Calculate trajectory
        mock_service.calculate_trajectory = Mock(return_value={
            "departure_date": "2024-01-01",
            "arrival_date": "2024-01-15",
            "return_date": "2024-02-01"
        })
        response = client.get("/api/orbital/trajectory?moid_au=0.1&departure_date=2024-01-01")
        assert response.status_code == 200

