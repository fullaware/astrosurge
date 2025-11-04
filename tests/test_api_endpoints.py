"""
Comprehensive test suite for FastAPI endpoints
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Add the project root to the Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variables before importing api
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test_asteroids")

from api import app, DatabaseManager

# Create test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test health check and status endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestConfigEndpoints:
    """Test configuration endpoints"""
    
    @patch('api.get_db')
    def test_get_config(self, mock_get_db):
        """Test getting system configuration"""
        mock_db = Mock()
        mock_db.get_config = Mock(return_value={"test": "config"})
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/config")
        assert response.status_code == 200


class TestAsteroidEndpoints:
    """Test asteroid-related endpoints"""
    
    @patch('api.get_db')
    def test_get_asteroids(self, mock_get_db):
        """Test getting asteroids list"""
        mock_db = Mock()
        mock_db.get_asteroids = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/asteroids?limit=10&skip=0")
        assert response.status_code == 200
    
    @patch('api.get_db')
    def test_get_asteroids_with_pagination(self, mock_get_db):
        """Test getting asteroids with pagination"""
        mock_db = Mock()
        mock_db.get_asteroids = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/asteroids?limit=5&skip=10")
        assert response.status_code == 200
        mock_db.get_asteroids.assert_called_once_with(5, 10)
    
    @patch('api.get_db')
    def test_get_elements(self, mock_get_db):
        """Test getting chemical elements"""
        mock_db = Mock()
        mock_db.get_elements = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/elements")
        assert response.status_code == 200


class TestUserEndpoints:
    """Test user management endpoints"""
    
    @patch('api.get_db')
    def test_get_users(self, mock_get_db):
        """Test getting all users"""
        mock_db = Mock()
        mock_db.get_users = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/users")
        assert response.status_code == 200
    
    @patch('api.get_db')
    def test_create_user(self, mock_get_db):
        """Test creating a new user"""
        mock_db = Mock()
        mock_db.create_user = Mock(return_value={
            "_id": "test_id",
            "username": "testuser",
            "company_name": "Test Co",
            "bank_balance": 1000000.0,
            "investor_debt": 0.0
        })
        mock_get_db.return_value = mock_db
        
        user_data = {
            "username": "testuser",
            "company_name": "Test Co",
            "bank_balance": 1000000.0,
            "investor_debt": 0.0
        }
        response = client.post("/api/users", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


class TestShipEndpoints:
    """Test ship management endpoints"""
    
    @patch('api.get_db')
    def test_get_ships(self, mock_get_db):
        """Test getting all ships"""
        mock_db = Mock()
        mock_db.get_ships = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/ships")
        assert response.status_code == 200
    
    @patch('api.get_db')
    def test_create_ship(self, mock_get_db):
        """Test creating a new ship"""
        mock_db = Mock()
        mock_db.create_ship = Mock(return_value={
            "_id": "ship_id",
            "user_id": "user_id",
            "name": "Test Ship",
            "capacity_kg": 50000,
            "status": "available"
        })
        mock_get_db.return_value = mock_db
        
        ship_data = {
            "user_id": "user_id",
            "name": "Test Ship",
            "capacity_kg": 50000
        }
        response = client.post("/api/ships", json=ship_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Ship"
    
    @patch('api.get_db')
    def test_mark_ship_veteran(self, mock_get_db):
        """Test marking a ship as veteran"""
        mock_db = Mock()
        mock_db.mark_ship_veteran = Mock(return_value=True)
        mock_get_db.return_value = mock_db
        
        response = client.put("/api/ships/test_ship_id/veteran")
        assert response.status_code == 200


class TestMissionEndpoints:
    """Test mission management endpoints"""
    
    @patch('api.get_db')
    def test_get_missions(self, mock_get_db):
        """Test getting all missions"""
        mock_db = Mock()
        mock_db.get_missions = Mock(return_value=[])
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/missions")
        assert response.status_code == 200
    
    @patch('api.get_db')
    @patch('api.simulation_engine')
    def test_create_mission(self, mock_engine, mock_get_db):
        """Test creating a new mission"""
        mock_db = Mock()
        mock_db.get_asteroid = Mock(return_value={
            "_id": "asteroid_id",
            "name": "Test Asteroid",
            "moid": 0.1
        })
        mock_db.create_mission = Mock(return_value={
            "_id": "mission_id",
            "user_id": "user_id",
            "ship_id": "ship_id",
            "asteroid_id": "asteroid_id",
            "status": "planning"
        })
        mock_get_db.return_value = mock_db
        
        mission_data = {
            "user_id": "user_id",
            "ship_id": "ship_id",
            "asteroid_id": "asteroid_id",
            "name": "Test Mission"
        }
        response = client.post("/api/missions", json=mission_data)
        assert response.status_code == 200
    
    @patch('api.get_db')
    def test_get_mission_results(self, mock_get_db):
        """Test getting mission results"""
        mock_db = Mock()
        mock_db.get_mission = Mock(return_value={
            "_id": "mission_id",
            "status": "completed",
            "results": {"profit": 1000000}
        })
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/missions/test_mission_id/results")
        assert response.status_code == 200


class TestCommodityEndpoints:
    """Test commodity pricing endpoints"""
    
    @patch('api.CommodityPricingService')
    def test_get_commodity_prices(self, mock_pricing_service):
        """Test getting commodity prices"""
        mock_service = Mock()
        mock_service.get_commodity_prices_per_kg = Mock(return_value={
            "Gold": 70548.0,
            "Platinum": 35274.0,
            "Silver": 881.85
        })
        mock_pricing_service.return_value = mock_service
        
        response = client.get("/api/commodity-prices")
        assert response.status_code == 200
        data = response.json()
        assert "prices_per_kg" in data


class TestOrbitalEndpoints:
    """Test orbital mechanics endpoints"""
    
    @patch('api.OrbitalMechanicsService')
    def test_get_travel_time(self, mock_orbital_service):
        """Test calculating travel time"""
        mock_service = Mock()
        mock_service.calculate_travel_time = Mock(return_value={
            "one_way_time_days": 10.5,
            "total_time_days": 21.0,
            "distance_km": 14959787.07
        })
        mock_orbital_service.return_value = mock_service
        
        response = client.get("/api/orbital/travel-time?moid_au=0.1&mission_type=round_trip")
        assert response.status_code == 200
        data = response.json()
        assert "total_time_days" in data
    
    @patch('api.OrbitalMechanicsService')
    def test_get_trajectory(self, mock_orbital_service):
        """Test getting trajectory information"""
        mock_service = Mock()
        mock_service.calculate_trajectory = Mock(return_value={
            "departure_date": "2024-01-01",
            "arrival_date": "2024-01-15",
            "return_date": "2024-02-01"
        })
        mock_orbital_service.return_value = mock_service
        
        response = client.get("/api/orbital/trajectory?moid_au=0.1&departure_date=2024-01-01")
        assert response.status_code == 200


class TestMissionAnalysisEndpoints:
    """Test mission analysis endpoints"""
    
    @patch('api.get_db')
    @patch('api.MissionEconomicsService')
    def test_get_mission_economics(self, mock_economics_service, mock_get_db):
        """Test getting mission economics analysis"""
        mock_db = Mock()
        mock_db.get_mission = Mock(return_value={
            "_id": "mission_id",
            "cargo": {"Gold": 100, "Platinum": 50}
        })
        mock_get_db.return_value = mock_db
        
        mock_service = Mock()
        mock_service.calculate_mission_economics = Mock(return_value={
            "total_value": 10000000,
            "profit": 5000000
        })
        mock_economics_service.return_value = mock_service
        
        response = client.get("/api/missions/test_mission_id/economics")
        assert response.status_code == 200
    
    @patch('api.get_db')
    @patch('api.SpaceHazardsService')
    def test_get_mission_risk(self, mock_hazards_service, mock_get_db):
        """Test getting mission risk assessment"""
        mock_db = Mock()
        mock_db.get_mission = Mock(return_value={
            "_id": "mission_id",
            "asteroid_id": "asteroid_id"
        })
        mock_get_db.return_value = mock_db
        
        mock_service = Mock()
        mock_service.assess_mission_risk = Mock(return_value={
            "overall_risk": 0.15,
            "hazards": []
        })
        mock_hazards_service.return_value = mock_service
        
        response = client.get("/api/missions/test_mission_id/risk")
        assert response.status_code == 200
    
    @patch('api.get_db')
    def test_get_mission_hazards(self, mock_get_db):
        """Test getting mission hazards"""
        mock_db = Mock()
        mock_db.get_mission = Mock(return_value={
            "_id": "mission_id",
            "hazards": []
        })
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/missions/test_mission_id/hazards")
        assert response.status_code == 200


class TestWorldSimulationEndpoints:
    """Test world simulation endpoints"""
    
    @patch('api.get_db')
    def test_get_world_status(self, mock_get_db):
        """Test getting world simulation status"""
        mock_db = Mock()
        mock_db.get_world_state = Mock(return_value={
            "current_day": 1,
            "status": "running"
        })
        mock_get_db.return_value = mock_db
        
        response = client.get("/api/world/status")
        assert response.status_code == 200
    
    @patch('api.simulation_engine')
    @patch('api.get_db')
    def test_start_world_simulation(self, mock_get_db, mock_engine):
        """Test starting world simulation"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_engine.initialize = Mock(return_value=None)
        mock_engine.start = Mock(return_value=None)
        
        response = client.post("/api/world/start")
        assert response.status_code == 200
    
    @patch('api.simulation_engine')
    def test_stop_world_simulation(self, mock_engine):
        """Test stopping world simulation"""
        mock_engine.stop = Mock(return_value=None)
        
        response = client.post("/api/world/stop")
        assert response.status_code == 200
    
    @patch('api.simulation_engine')
    @patch('api.get_db')
    def test_tick_world_simulation(self, mock_get_db, mock_engine):
        """Test ticking world simulation"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        mock_engine.tick = Mock(return_value=None)
        
        response = client.post("/api/world/tick")
        assert response.status_code == 200


class TestMiningAnalysisEndpoints:
    """Test mining analysis endpoints"""
    
    @patch('api.get_db')
    @patch('api.MiningOperationsService')
    def test_get_asteroid_mining_analysis(self, mock_mining_service, mock_get_db):
        """Test getting asteroid mining analysis"""
        mock_db = Mock()
        mock_db.get_asteroid = Mock(return_value={
            "_id": "asteroid_id",
            "name": "Test Asteroid",
            "elements": [{"name": "Gold", "percentage": 10}]
        })
        mock_get_db.return_value = mock_db
        
        mock_service = Mock()
        mock_service.analyze_mining_potential = Mock(return_value={
            "estimated_yield": 1000,
            "ore_grade": 0.1
        })
        mock_mining_service.return_value = mock_service
        
        response = client.get("/api/asteroids/test_asteroid_id/mining-analysis")
        assert response.status_code == 200

