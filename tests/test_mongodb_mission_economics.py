"""
Test suite for MongoDB-integrated mission economics service
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bson import ObjectId

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.mongodb_mission_economics import MongoDBMissionEconomicsService


class TestMongoDBMissionEconomicsService:
    """Test cases for MongoDB-integrated mission economics service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock MongoDB connection to avoid actual database calls
        with patch('src.services.mongodb_mission_economics.MongoClient') as mock_client:
            mock_db = Mock()
            mock_client.return_value.admin.command.return_value = True
            mock_client.return_value.asteroids = mock_db
            
            # Mock collections
            mock_db.missions = Mock()
            mock_db.users = Mock()
            mock_db.ships = Mock()
            mock_db.market_prices = Mock()
            mock_db.mission_economics = Mock()
            mock_db.ore_analysis = Mock()
            
            # Provide a mock MongoDB URI to avoid environment variable error
            self.economics_service = MongoDBMissionEconomicsService(mongodb_uri="mongodb://test:test@localhost:27017/test")
            self.mock_db = mock_db
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        assert self.economics_service.pricing_service is not None
        assert self.economics_service.cost_structure is not None
        assert self.economics_service.ore_grade_classifications is not None
        assert self.economics_service.mining_efficiency is not None
        assert self.economics_service.ship_specs is not None
    
    @pytest.mark.asyncio
    async def test_get_mission_success(self):
        """Test successful mission retrieval"""
        mission_id = "507f1f77bcf86cd799439011"
        mock_mission = {
            "_id": ObjectId(mission_id),
            "name": "Test Mission",
            "user_id": "user123",
            "total_days": 224
        }
        
        self.mock_db.missions.find_one.return_value = mock_mission
        
        result = await self.economics_service.get_mission(mission_id)
        
        assert result is not None
        assert result["_id"] == mission_id
        assert result["name"] == "Test Mission"
        self.mock_db.missions.find_one.assert_called_once_with({"_id": ObjectId(mission_id)})
    
    @pytest.mark.asyncio
    async def test_get_mission_not_found(self):
        """Test mission retrieval when mission doesn't exist"""
        mission_id = "507f1f77bcf86cd799439011"
        self.mock_db.missions.find_one.return_value = None
        
        result = await self.economics_service.get_mission(mission_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_user_success(self):
        """Test successful user retrieval"""
        user_id = "507f1f77bcf86cd799439011"
        mock_user = {
            "_id": ObjectId(user_id),
            "username": "testuser",
            "company_name": "Test Corp",
            "bank_balance": 1000000
        }
        
        self.mock_db.users.find_one.return_value = mock_user
        
        result = await self.economics_service.get_user(user_id)
        
        assert result is not None
        assert result["_id"] == user_id
        assert result["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_save_mission_economics_success(self):
        """Test successful mission economics saving"""
        mission_id = "507f1f77bcf86cd799439011"
        economics_data = {
            "net_profit": 100000000,
            "total_costs": 50000000,
            "roi_percentage": 200
        }
        
        self.mock_db.mission_economics.replace_one.return_value = Mock(upserted_id=ObjectId())
        
        result = await self.economics_service.save_mission_economics(mission_id, economics_data)
        
        assert result is True
        self.mock_db.mission_economics.replace_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_mission_economics_success(self):
        """Test successful mission economics retrieval"""
        mission_id = "507f1f77bcf86cd799439011"
        mock_economics = {
            "_id": ObjectId(),
            "mission_id": ObjectId(mission_id),
            "economics": {
                "net_profit": 100000000,
                "total_costs": 50000000
            }
        }
        
        self.mock_db.mission_economics.find_one.return_value = mock_economics
        
        result = await self.economics_service.get_mission_economics(mission_id)
        
        assert result is not None
        assert result["net_profit"] == 100000000
        assert result["total_costs"] == 50000000
    
    @pytest.mark.asyncio
    async def test_save_ore_analysis_success(self):
        """Test successful ore analysis saving"""
        mission_id = "507f1f77bcf86cd799439011"
        asteroid_id = "asteroid123"
        ore_analysis = {
            "ore_grade": 0.1,
            "grade_classification": "high",
            "mining_efficiency": 0.95
        }
        
        self.mock_db.ore_analysis.replace_one.return_value = Mock(upserted_id=ObjectId())
        
        result = await self.economics_service.save_ore_analysis(mission_id, asteroid_id, ore_analysis)
        
        assert result is True
        self.mock_db.ore_analysis.replace_one.assert_called_once()
    
    def test_calculate_ore_grade_low(self):
        """Test ore grade calculation for low-grade ore"""
        grade_class, grade_percentage = self.economics_service.calculate_ore_grade(
            commodity_content=100,  # 100 kg commodity
            total_ore=5000           # 5000 kg total ore
        )
        
        assert grade_class == 'low'
        assert grade_percentage == 0.02  # 2%
    
    def test_calculate_ore_grade_high(self):
        """Test ore grade calculation for high-grade ore"""
        grade_class, grade_percentage = self.economics_service.calculate_ore_grade(
            commodity_content=800,  # 800 kg commodity
            total_ore=5000          # 5000 kg total ore
        )
        
        assert grade_class == 'high'
        assert grade_percentage == 0.16  # 16%
    
    @pytest.mark.asyncio
    async def test_calculate_mission_costs(self):
        """Test mission cost calculation"""
        mission_data = {
            'total_days': 100,
            'launch_scrubs': 1,
            'space_events': 2,
            'mining_days': 20
        }
        
        costs = await self.economics_service.calculate_mission_costs(mission_data)
        
        # Ground control: 100 days × $75K = $7.5M
        assert costs['ground_control'] == 100 * 75000
        
        # Launch scrubs: 1 × $75K = $75K
        assert costs['launch_scrubs'] == 1 * 75000
        
        # Space events: 2 × $100K = $200K
        assert costs['space_events'] == 2 * 100000
        
        # Mining operations: 20 days × $50K = $1M
        assert costs['mining_operations'] == 20 * 50000
        
        # Total should be sum of all costs
        expected_total = sum([
            costs['ground_control'],
            costs['launch_scrubs'],
            costs['space_events'],
            costs['mining_operations'],
            costs['ship_maintenance'],
            costs['fuel'],
            costs['life_support']
        ])
        assert costs['total'] == expected_total
    
    @pytest.mark.asyncio
    async def test_calculate_mining_yield(self):
        """Test mining yield calculation with MongoDB persistence"""
        mission_id = "507f1f77bcf86cd799439011"
        asteroid_composition = {
            'Platinum': 0.4,
            'Gold': 0.3,
            'Silver': 0.2,
            'Copper': 0.1
        }
        
        # Mock the save_ore_analysis method
        with patch.object(self.economics_service, 'save_ore_analysis', return_value=True) as mock_save:
            yield_data = await self.economics_service.calculate_mining_yield(
                mission_id, asteroid_composition, mining_days=30, ore_grade=0.1
            )
            
            # Check basic yield calculations
            assert yield_data['total_ore_mined'] == 45000  # 30 days × 1500 kg/day
            assert yield_data['ore_grade'] == 0.1
            assert yield_data['grade_classification'] == 'high'
            assert yield_data['mining_efficiency'] == 0.95  # High-grade efficiency
            
            # Check gangue separation cost
            expected_gangue_cost = yield_data['effective_yield'] * 0.50
            assert yield_data['gangue_separation_cost'] == expected_gangue_cost
            
            # Verify MongoDB save was called
            mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_cargo_value(self):
        """Test cargo value calculation"""
        # Mock pricing service
        with patch.object(self.economics_service.pricing_service, 'get_commodity_prices_per_kg') as mock_get_prices:
            mock_get_prices.return_value = {
                'Platinum': 35274.0,
                'Gold': 70548.0,
                'Silver': 881.85,
                'Copper': 141.10
            }
            
            cargo = {
                'Platinum': 20000,
                'Gold': 15000,
                'Silver': 10000,
                'Copper': 5000
            }
            
            cargo_value = await self.economics_service.calculate_cargo_value(cargo)
            
            # Check individual commodity values
            assert cargo_value['Platinum']['weight_kg'] == 20000
            assert cargo_value['Platinum']['price_per_kg'] == 35274.0
            assert cargo_value['Platinum']['total_value'] == 20000 * 35274.0
            
            assert cargo_value['Gold']['weight_kg'] == 15000
            assert cargo_value['Gold']['price_per_kg'] == 70548.0
            assert cargo_value['Gold']['total_value'] == 15000 * 70548.0
            
            # Check total value
            expected_total = sum(item['total_value'] for item in cargo_value.values() 
                               if isinstance(item, dict) and 'total_value' in item)
            assert cargo_value['total_value'] == expected_total
    
    @pytest.mark.asyncio
    async def test_calculate_comprehensive_mission_economics(self):
        """Test comprehensive mission economics calculation"""
        mission_id = "507f1f77bcf86cd799439011"
        
        # Mock mission data
        mock_mission = {
            "_id": ObjectId(mission_id),
            "total_days": 224,
            "launch_scrubs": 2,
            "space_events": 3,
            "mining_days": 30,
            "asteroid_composition": {
                "Platinum": 0.4,
                "Gold": 0.3,
                "Silver": 0.2,
                "Copper": 0.1
            },
            "ore_grade": 0.1,
            "cargo": {
                "Platinum": 20000,
                "Gold": 15000,
                "Silver": 10000,
                "Copper": 5000
            },
            "hull_damage": 5
        }
        
        # Mock the get_mission method
        with patch.object(self.economics_service, 'get_mission', return_value=mock_mission) as mock_get_mission:
            # Mock the save methods
            with patch.object(self.economics_service, 'save_mission_economics', return_value=True) as mock_save_economics:
                with patch.object(self.economics_service, 'save_ore_analysis', return_value=True) as mock_save_ore:
                    
                    economics = await self.economics_service.calculate_comprehensive_mission_economics(mission_id)
                    
                    # Check that mission was retrieved
                    mock_get_mission.assert_called_once_with(mission_id)
                    
                    # Check economics structure
                    assert 'mission_costs' in economics
                    assert 'mining_yield' in economics
                    assert 'cargo_value' in economics
                    assert 'investor_repayment' in economics
                    assert 'ship_repair_cost' in economics
                    assert 'gangue_separation_cost' in economics
                    assert 'total_costs' in economics
                    assert 'net_profit' in economics
                    assert 'roi_percentage' in economics
                    assert 'mission_summary' in economics
                    
                    # Check mission summary
                    summary = economics['mission_summary']
                    assert summary['duration_days'] == 224
                    assert summary['mining_days'] == 30
                    assert summary['ore_grade'] == 0.1
                    assert summary['hull_damage'] == 5
                    
                    # Verify MongoDB saves were called
                    mock_save_economics.assert_called_once()
                    mock_save_ore.assert_called()
    
    @pytest.mark.asyncio
    async def test_calculate_optimal_cargo_mix(self):
        """Test optimal cargo mix calculation"""
        mission_id = "507f1f77bcf86cd799439011"
        asteroid_composition = {
            'Platinum': 0.4,
            'Gold': 0.3,
            'Silver': 0.2,
            'Copper': 0.1
        }
        
        # Mock pricing service
        with patch.object(self.economics_service.pricing_service, 'get_commodity_prices_per_kg') as mock_get_prices:
            mock_get_prices.return_value = {
                'Platinum': 35274.0,
                'Gold': 70548.0,
                'Silver': 881.85,
                'Copper': 141.10
            }
            
            # Mock save method
            with patch.object(self.economics_service, 'save_ore_analysis', return_value=True) as mock_save:
                optimal_mix = await self.economics_service.calculate_optimal_cargo_mix(
                    mission_id, asteroid_composition, cargo_capacity=50000
                )
                
                # Check that commodities are sorted by value
                commodity_rankings = optimal_mix['commodity_rankings']
                assert len(commodity_rankings) == 4
                
                # Gold should be first (highest price)
                assert commodity_rankings[0][0] == 'Gold'
                assert commodity_rankings[0][1]['price_per_kg'] == 70548.0
                
                # Copper should be last (lowest price)
                assert commodity_rankings[-1][0] == 'Copper'
                assert commodity_rankings[-1][1]['price_per_kg'] == 141.10
                
                # Check optimal cargo mix
                assert 'optimal_cargo_mix' in optimal_mix
                assert 'total_value' in optimal_mix
                assert 'cargo_capacity_used' in optimal_mix
                assert optimal_mix['mission_id'] == mission_id
                
                # Verify MongoDB save was called
                mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_mission_risk_assessment(self):
        """Test mission risk assessment calculation"""
        mission_id = "507f1f77bcf86cd799439011"
        
        # Mock comprehensive economics calculation
        mock_economics = {
            'net_profit': 50000000,  # Low profit
            'total_costs': 600000000,  # High costs
            'roi_percentage': 8.3,  # Low ROI
            'mission_summary': {
                'duration_days': 400,  # Long mission
                'hull_damage': 15,  # High hull damage
                'ore_grade': 0.03  # Low ore grade
            }
        }
        
        with patch.object(self.economics_service, 'calculate_comprehensive_mission_economics', 
                         return_value=mock_economics) as mock_calc:
            
            risk_assessment = await self.economics_service.calculate_mission_risk_assessment(mission_id)
            
            assert risk_assessment['mission_id'] == mission_id
            assert risk_assessment['risk_level'] == 'high'
            assert risk_assessment['risk_score'] >= 4
            assert len(risk_assessment['recommendations']) > 0
            assert 'calculated_at' in risk_assessment
            
            # Check risk factors
            risk_factors = risk_assessment['risk_factors']
            assert risk_factors['low_profit_margin'] == True
            assert risk_factors['high_costs'] == True
            assert risk_factors['low_roi'] == True
            assert risk_factors['high_hull_damage'] == True
            assert risk_factors['long_mission'] == True
            assert risk_factors['low_ore_grade'] == True
    
    @pytest.mark.asyncio
    async def test_get_mission_history(self):
        """Test mission history retrieval"""
        user_id = "user123"
        
        # Mock missions data
        mock_missions = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "name": "Mission 1",
                "user_id": user_id,
                "created_at": datetime.utcnow()
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "name": "Mission 2",
                "user_id": user_id,
                "created_at": datetime.utcnow()
            }
        ]
        
        self.mock_db.missions.find.return_value.sort.return_value.limit.return_value = mock_missions
        
        # Mock get_mission_economics
        with patch.object(self.economics_service, 'get_mission_economics', 
                         return_value={"net_profit": 100000000}) as mock_get_economics:
            
            history = await self.economics_service.get_mission_history(user_id, limit=10)
            
            assert len(history) == 2
            assert history[0]["name"] == "Mission 1"
            assert history[1]["name"] == "Mission 2"
            
            # Check that economics were added
            for mission in history:
                assert "economics" in mission
                assert mission["economics"]["net_profit"] == 100000000
    
    @pytest.mark.asyncio
    async def test_get_user_economics_summary(self):
        """Test user economics summary calculation"""
        user_id = "user123"
        
        # Mock missions data
        mock_missions = [
            {"_id": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": ObjectId("507f1f77bcf86cd799439012")},
            {"_id": ObjectId("507f1f77bcf86cd799439013")}
        ]
        
        self.mock_db.missions.find.return_value = mock_missions
        
        # Mock get_mission_economics with different results
        economics_results = [
            {"net_profit": 100000000, "total_costs": 50000000},  # Profitable
            {"net_profit": -50000000, "total_costs": 100000000},  # Loss
            {"net_profit": 200000000, "total_costs": 80000000}   # Profitable
        ]
        
        with patch.object(self.economics_service, 'get_mission_economics', 
                         side_effect=economics_results) as mock_get_economics:
            
            summary = await self.economics_service.get_user_economics_summary(user_id)
            
            assert summary['user_id'] == user_id
            assert summary['total_missions'] == 3
            assert summary['successful_missions'] == 2  # 2 profitable missions
            assert summary['success_rate'] == pytest.approx(66.67, rel=1e-2)
            assert summary['total_profit'] == 250000000  # 100M - 50M + 200M
            assert summary['total_costs'] == 230000000  # 50M + 100M + 80M
            assert summary['overall_roi'] == pytest.approx(108.7, rel=1e-1)
            assert 'calculated_at' in summary
    
    def test_get_risk_recommendations(self):
        """Test risk recommendations generation"""
        risk_factors = {
            'low_profit_margin': True,
            'high_costs': True,
            'low_roi': False,
            'high_hull_damage': False,
            'long_mission': True,
            'low_ore_grade': False
        }
        
        recommendations = self.economics_service._get_risk_recommendations(risk_factors)
        
        assert len(recommendations) == 3
        assert "Consider higher-grade asteroids or longer mining operations" in recommendations
        assert "Optimize mission duration and reduce operational costs" in recommendations
        assert "Consider shorter missions or more efficient travel routes" in recommendations
    
    def test_cost_structure_values(self):
        """Test cost structure values"""
        costs = self.economics_service.cost_structure
        
        assert costs['ground_control'] == 75000
        assert costs['launch_scrub'] == 75000
        assert costs['space_event_base'] == 100000
        assert costs['mining_operations'] == 50000
        assert costs['ship_maintenance'] == 25000
        assert costs['fuel_consumption'] == 15000
        assert costs['life_support'] == 10000
    
    def test_ore_grade_classifications(self):
        """Test ore grade classification boundaries"""
        classifications = self.economics_service.ore_grade_classifications
        
        # Test low grade boundary
        assert classifications['low']['min'] == 0.01
        assert classifications['low']['max'] == 0.05
        
        # Test medium grade boundary
        assert classifications['medium']['min'] == 0.05
        assert classifications['medium']['max'] == 0.10
        
        # Test high grade boundary
        assert classifications['high']['min'] == 0.10
        assert classifications['high']['max'] == 0.20
        
        # Test premium grade boundary
        assert classifications['premium']['min'] == 0.20
        assert classifications['premium']['max'] == 1.0
    
    def test_mining_efficiency_values(self):
        """Test mining efficiency values"""
        efficiency = self.economics_service.mining_efficiency
        
        assert efficiency['low'] == 0.8
        assert efficiency['medium'] == 0.9
        assert efficiency['high'] == 0.95
        assert efficiency['premium'] == 0.98
    
    def test_ship_specifications(self):
        """Test ship specifications"""
        specs = self.economics_service.ship_specs
        
        assert specs['cargo_capacity'] == 50000
        assert specs['max_mining_rate'] == 1500
        assert specs['fuel_capacity'] == 10000
        assert specs['crew_size'] == 4
        assert specs['hull_integrity'] == 100


if __name__ == "__main__":
    pytest.main([__file__])
