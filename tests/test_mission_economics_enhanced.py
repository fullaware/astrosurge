"""
Test suite for enhanced mission economics service
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.mission_economics_enhanced import MissionEconomicsService


class TestMissionEconomicsService:
    """Test cases for enhanced mission economics service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.economics_service = MissionEconomicsService()
        
        # Sample mission data
        self.sample_mission = {
            'total_days': 224,
            'launch_scrubs': 2,
            'space_events': 3,
            'mining_days': 30,
            'asteroid_composition': {
                'Platinum': 0.4,
                'Gold': 0.3,
                'Silver': 0.2,
                'Copper': 0.1
            },
            'ore_grade': 0.1,
            'cargo': {
                'Platinum': 20000,
                'Gold': 15000,
                'Silver': 10000,
                'Copper': 5000
            },
            'hull_damage': 5
        }
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        assert self.economics_service.pricing_service is not None
        assert self.economics_service.cost_structure is not None
        assert self.economics_service.ore_grade_classifications is not None
        assert self.economics_service.mining_efficiency is not None
        assert self.economics_service.ship_specs is not None
    
    def test_calculate_mission_costs_basic(self):
        """Test basic mission cost calculation"""
        costs = self.economics_service.calculate_mission_costs(
            mission_duration_days=100,
            launch_scrubs=1,
            space_events=2,
            mining_days=20
        )
        
        # Ground control: 100 days × $75K = $7.5M
        assert costs['ground_control'] == 100 * 75000
        
        # Launch scrubs: 1 × $75K = $75K
        assert costs['launch_scrubs'] == 1 * 75000
        
        # Space events: 2 × $100K = $200K
        assert costs['space_events'] == 2 * 100000
        
        # Mining operations: 20 days × $50K = $1M
        assert costs['mining_operations'] == 20 * 50000
        
        # Ship maintenance: 100 days × $25K = $2.5M
        assert costs['ship_maintenance'] == 100 * 25000
        
        # Fuel: 100 days × $15K = $1.5M
        assert costs['fuel'] == 100 * 15000
        
        # Life support: 100 days × $10K = $1M
        assert costs['life_support'] == 100 * 10000
        
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
    
    def test_calculate_mission_costs_zero_values(self):
        """Test mission cost calculation with zero values"""
        costs = self.economics_service.calculate_mission_costs(
            mission_duration_days=0,
            launch_scrubs=0,
            space_events=0,
            mining_days=0
        )
        
        # All costs should be zero
        for cost_type, amount in costs.items():
            assert amount == 0
    
    def test_calculate_ore_grade_low(self):
        """Test ore grade calculation for low-grade ore"""
        grade_class, grade_percentage = self.economics_service.calculate_ore_grade(
            commodity_content=100,  # 100 kg commodity
            total_ore=5000           # 5000 kg total ore
        )
        
        assert grade_class == 'low'
        assert grade_percentage == 0.02  # 2%
    
    def test_calculate_ore_grade_medium(self):
        """Test ore grade calculation for medium-grade ore"""
        grade_class, grade_percentage = self.economics_service.calculate_ore_grade(
            commodity_content=400,  # 400 kg commodity
            total_ore=5000          # 5000 kg total ore
        )
        
        assert grade_class == 'medium'
        assert grade_percentage == 0.08  # 8%
    
    def test_calculate_ore_grade_high(self):
        """Test ore grade calculation for high-grade ore"""
        grade_class, grade_percentage = self.economics_service.calculate_ore_grade(
            commodity_content=800,  # 800 kg commodity
            total_ore=5000          # 5000 kg total ore
        )
        
        assert grade_class == 'high'
        assert grade_percentage == 0.16  # 16%
    
    def test_calculate_ore_grade_premium(self):
        """Test ore grade calculation for premium-grade ore"""
        grade_class, grade_percentage = self.economics_service.calculate_ore_grade(
            commodity_content=1500,  # 1500 kg commodity
            total_ore=5000           # 5000 kg total ore
        )
        
        assert grade_class == 'premium'
        assert grade_percentage == 0.30  # 30%
    
    def test_calculate_ore_grade_zero_total(self):
        """Test ore grade calculation with zero total ore"""
        grade_class, grade_percentage = self.economics_service.calculate_ore_grade(
            commodity_content=100,
            total_ore=0
        )
        
        assert grade_class == 'low'
        assert grade_percentage == 0.0
    
    def test_calculate_mining_yield(self):
        """Test mining yield calculation"""
        # Mock pricing service on the instance
        with patch.object(self.economics_service.pricing_service, 'get_commodity_prices_per_kg') as mock_get_prices:
            mock_get_prices.return_value = {
                'Platinum': 35274.0,
                'Gold': 70548.0,
                'Silver': 881.85,
                'Copper': 141.10
            }
        
        asteroid_composition = {
            'Platinum': 0.4,
            'Gold': 0.3,
            'Silver': 0.2,
            'Copper': 0.1
        }
        
        yield_data = self.economics_service.calculate_mining_yield(
            asteroid_composition=asteroid_composition,
            mining_days=30,
            ore_grade=0.1
        )
        
        # Check basic yield calculations
        assert yield_data['total_ore_mined'] == 45000  # 30 days × 1500 kg/day
        assert yield_data['ore_grade'] == 0.1
        assert yield_data['grade_classification'] == 'high'
        assert yield_data['mining_efficiency'] == 0.95  # High-grade efficiency
        
        # Check gangue separation cost
        expected_gangue_cost = yield_data['effective_yield'] * 0.50
        assert yield_data['gangue_separation_cost'] == expected_gangue_cost
    
    def test_calculate_cargo_value(self):
        """Test cargo value calculation"""
        # Mock pricing service on the instance
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
        
        cargo_value = self.economics_service.calculate_cargo_value(cargo)
        
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
    
    def test_calculate_cargo_value_unknown_commodity(self):
        """Test cargo value calculation with unknown commodity"""
        # Mock pricing service on the instance
        with patch.object(self.economics_service.pricing_service, 'get_commodity_prices_per_kg') as mock_get_prices:
            mock_get_prices.return_value = {
                'Platinum': 35274.0
            }
        
        cargo = {
            'Platinum': 1000,
            'UnknownCommodity': 500
        }
        
        cargo_value = self.economics_service.calculate_cargo_value(cargo)
        
        # Known commodity should have value
        assert cargo_value['Platinum']['total_value'] == 1000 * 35274.0
        
        # Unknown commodity should have zero value
        assert cargo_value['UnknownCommodity']['total_value'] == 0
        assert cargo_value['UnknownCommodity']['price_per_kg'] == 0
    
    @patch.object(MissionEconomicsService, 'calculate_mission_costs')
    @patch.object(MissionEconomicsService, 'calculate_mining_yield')
    @patch.object(MissionEconomicsService, 'calculate_cargo_value')
    def test_calculate_mission_economics(self, mock_cargo_value, mock_mining_yield, mock_mission_costs):
        """Test comprehensive mission economics calculation"""
        # Mock the component methods
        mock_mission_costs.return_value = {
            'ground_control': 16800000,  # 224 days × $75K
            'launch_scrubs': 150000,     # 2 × $75K
            'space_events': 300000,      # 3 × $100K
            'mining_operations': 1500000, # 30 days × $50K
            'ship_maintenance': 5600000, # 224 days × $25K
            'fuel': 3360000,             # 224 days × $15K
            'life_support': 2240000,     # 224 days × $10K
            'total': 30000000           # Total costs
        }
        
        mock_mining_yield.return_value = {
            'total_ore_mined': 45000,
            'effective_yield': 42750,
            'ore_grade': 0.1,
            'grade_classification': 'high',
            'mining_efficiency': 0.95,
            'commodity_yield': {'Platinum': 17100, 'Gold': 12825},
            'gangue_weight': 25650,
            'gangue_separation_cost': 21375  # $0.50 per kg
        }
        
        mock_cargo_value.return_value = {
            'Platinum': {'weight_kg': 20000, 'price_per_kg': 35274.0, 'total_value': 705480000},
            'Gold': {'weight_kg': 15000, 'price_per_kg': 70548.0, 'total_value': 1058220000},
            'total_value': 1763700000
        }
        
        economics = self.economics_service.calculate_mission_economics(self.sample_mission)
        
        # Check mission costs
        assert economics['mission_costs']['total'] == 30000000
        
        # Check mining yield
        assert economics['mining_yield']['total_ore_mined'] == 45000
        
        # Check cargo value
        assert economics['cargo_value']['total_value'] == 1763700000
        
        # Check gangue separation cost
        assert economics['gangue_separation_cost'] == 21375
        
        # Check investor repayment calculation
        principal = 30000000
        daily_interest_rate = 0.15 / 365
        mission_duration = 224
        expected_interest = principal * daily_interest_rate * mission_duration
        expected_total_repayment = principal + expected_interest
        
        assert economics['investor_repayment']['principal'] == principal
        assert economics['investor_repayment']['interest'] == pytest.approx(expected_interest, rel=1e-6)
        assert economics['investor_repayment']['total'] == pytest.approx(expected_total_repayment, rel=1e-6)
        
        # Check ship repair cost
        hull_damage = 5
        expected_repair_cost = min(hull_damage * 1000000, 25000000)
        assert economics['ship_repair_cost'] == expected_repair_cost
        
        # Check net profit calculation
        total_costs = 30000000 + 21375  # mission costs + gangue separation
        expected_net_profit = 1763700000 - total_costs - expected_total_repayment - expected_repair_cost
        assert economics['net_profit'] == pytest.approx(expected_net_profit, rel=1e-6)
        
        # Check ROI calculation
        expected_roi = (expected_net_profit / total_costs * 100) if total_costs > 0 else 0
        assert economics['roi_percentage'] == pytest.approx(expected_roi, rel=1e-6)
    
    def test_calculate_optimal_cargo_mix(self):
        """Test optimal cargo mix calculation"""
        # Create a mock pricing service
        mock_pricing_service = Mock()
        mock_pricing_service.get_commodity_prices_per_kg.return_value = {
            'Platinum': 35274.0,
            'Gold': 70548.0,
            'Silver': 881.85,
            'Copper': 141.10
        }
        
        # Replace the pricing service
        original_pricing_service = self.economics_service.pricing_service
        self.economics_service.pricing_service = mock_pricing_service
        
        try:
            asteroid_composition = {
                'Platinum': 0.4,
                'Gold': 0.3,
                'Silver': 0.2,
                'Copper': 0.1
            }
            
            optimal_mix = self.economics_service.calculate_optimal_cargo_mix(
                asteroid_composition, cargo_capacity=50000
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
            
        finally:
            # Restore original pricing service
            self.economics_service.pricing_service = original_pricing_service
    
    def test_calculate_mission_risk_assessment_low_risk(self):
        """Test risk assessment for low-risk mission"""
        low_risk_mission = {
            'total_days': 200,
            'hull_damage': 2,
            'ore_grade': 0.15,
            'net_profit': 200000000,  # $200M profit
            'total_costs': 300000000,  # $300M costs
            'roi_percentage': 66.7
        }
        
        with patch.object(self.economics_service, 'calculate_mission_economics') as mock_economics:
            mock_economics.return_value = {
                'net_profit': 200000000,
                'total_costs': 300000000,
                'roi_percentage': 66.7
            }
            
            risk_assessment = self.economics_service.calculate_mission_risk_assessment(low_risk_mission)
            
            assert risk_assessment['risk_level'] == 'low'
            assert risk_assessment['risk_score'] <= 1
            assert len(risk_assessment['recommendations']) == 0
    
    def test_calculate_mission_risk_assessment_high_risk(self):
        """Test risk assessment for high-risk mission"""
        high_risk_mission = {
            'total_days': 400,
            'hull_damage': 15,
            'ore_grade': 0.03,
            'net_profit': 50000000,   # $50M profit
            'total_costs': 600000000,  # $600M costs
            'roi_percentage': 8.3
        }
        
        with patch.object(self.economics_service, 'calculate_mission_economics') as mock_economics:
            mock_economics.return_value = {
                'net_profit': 50000000,
                'total_costs': 600000000,
                'roi_percentage': 8.3
            }
            
            risk_assessment = self.economics_service.calculate_mission_risk_assessment(high_risk_mission)
            
            assert risk_assessment['risk_level'] == 'high'
            assert risk_assessment['risk_score'] >= 4
            assert len(risk_assessment['recommendations']) > 0
    
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
    
    def test_gangue_separation_cost(self):
        """Test gangue separation cost calculation"""
        assert self.economics_service.gangue_separation_cost == 0.50
        
        # Test cost calculation
        ore_weight = 1000  # kg
        expected_cost = ore_weight * 0.50
        assert expected_cost == 500.0


if __name__ == "__main__":
    pytest.main([__file__])
