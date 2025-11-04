"""
Test suite for AstroSurge Visualization Service
"""
import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.visualization import AstroSurgeVisualizationService


class TestAstroSurgeVisualizationService:
    """Test cases for visualization service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('src.services.visualization.OrbitalMechanicsService') as mock_orbital, \
             patch('src.services.visualization.MissionEconomicsService') as mock_economics, \
             patch('src.services.visualization.CommodityPricingService') as mock_pricing:
            
            # Mock the services
            self.mock_orbital = Mock()
            self.mock_economics = Mock()
            self.mock_pricing = Mock()
            
            mock_orbital.return_value = self.mock_orbital
            mock_economics.return_value = self.mock_economics
            mock_pricing.return_value = self.mock_pricing
            
            # Create the visualization service
            self.viz_service = AstroSurgeVisualizationService()
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        assert self.viz_service.orbital_service is not None
        assert self.viz_service.economics_service is not None
        assert self.viz_service.pricing_service is not None
        assert self.viz_service.refresh_interval == 30
        assert self.viz_service.max_missions_display == 10
        assert self.viz_service.max_asteroids_display == 20
        assert len(self.viz_service.chart_colors) == 6
    
    def test_get_dashboard_data(self):
        """Test getting comprehensive dashboard data"""
        dashboard_data = self.viz_service.get_dashboard_data()
        
        # Check basic structure
        required_keys = [
            'timestamp', 'overview', 'missions', 'asteroids', 'fleet',
            'economics', 'orbital_mechanics', 'risk_assessment', 'market_data',
            'alerts', 'charts'
        ]
        
        for key in required_keys:
            assert key in dashboard_data
        
        # Check overview metrics
        overview = dashboard_data['overview']
        assert 'total_missions' in overview
        assert 'active_missions' in overview
        assert 'fleet_size' in overview
        assert 'total_revenue' in overview
        assert 'net_profit' in overview
        assert 'success_rate' in overview
    
    def test_get_dashboard_data_with_user_id(self):
        """Test getting dashboard data with user filter"""
        dashboard_data = self.viz_service.get_dashboard_data('user123')
        
        # Should still return all data structure
        assert 'overview' in dashboard_data
        assert 'missions' in dashboard_data
        assert 'fleet' in dashboard_data
    
    def test_get_overview_metrics(self):
        """Test overview metrics generation"""
        metrics = self.viz_service._get_overview_metrics()
        
        # Check required metrics
        required_metrics = [
            'total_missions', 'active_missions', 'completed_missions',
            'total_asteroids', 'fleet_size', 'active_ships',
            'total_revenue', 'total_costs', 'net_profit',
            'success_rate', 'average_mission_duration', 'fuel_efficiency'
        ]
        
        for metric in required_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
            assert metrics[metric] >= 0
    
    def test_get_mission_data(self):
        """Test mission data generation"""
        mission_data = self.viz_service._get_mission_data()
        
        # Check structure
        assert 'missions' in mission_data
        assert 'status_counts' in mission_data
        
        # Check missions
        missions = mission_data['missions']
        assert isinstance(missions, list)
        assert len(missions) > 0
        
        # Check first mission structure
        if missions:
            mission = missions[0]
            required_fields = [
                'id', 'name', 'asteroid', 'status', 'progress',
                'start_date', 'estimated_completion', 'crew_size',
                'ship', 'distance_au', 'fuel_remaining', 'cargo_loaded',
                'risk_level', 'estimated_revenue', 'current_costs'
            ]
            
            for field in required_fields:
                assert field in mission
        
        # Check status counts
        status_counts = mission_data['status_counts']
        expected_statuses = ['planning', 'active', 'returning', 'completed']
        for status in expected_statuses:
            assert status in status_counts
            assert isinstance(status_counts[status], int)
    
    def test_get_asteroid_data(self):
        """Test asteroid data generation"""
        asteroid_data = self.viz_service._get_asteroid_data()
        
        # Check structure
        assert 'asteroids' in asteroid_data
        assert 'total_count' in asteroid_data
        assert 'by_difficulty' in asteroid_data
        assert 'by_risk' in asteroid_data
        
        # Check asteroids
        asteroids = asteroid_data['asteroids']
        assert isinstance(asteroids, list)
        assert len(asteroids) > 0
        
        # Check first asteroid structure
        if asteroids:
            asteroid = asteroids[0]
            required_fields = [
                'name', 'moid_au', 'size_km', 'composition',
                'mining_difficulty', 'estimated_value', 'travel_time_days',
                'risk_level', 'discovered', 'last_surveyed'
            ]
            
            for field in required_fields:
                assert field in asteroid
        
        # Check difficulty counts
        by_difficulty = asteroid_data['by_difficulty']
        expected_difficulties = ['easy', 'medium', 'hard']
        for difficulty in expected_difficulties:
            assert difficulty in by_difficulty
            assert isinstance(by_difficulty[difficulty], int)
        
        # Check risk counts
        by_risk = asteroid_data['by_risk']
        expected_risks = ['low', 'medium', 'high']
        for risk in expected_risks:
            assert risk in by_risk
            assert isinstance(by_risk[risk], int)
    
    def test_get_fleet_data(self):
        """Test fleet data generation"""
        fleet_data = self.viz_service._get_fleet_data()
        
        # Check structure
        assert 'ships' in fleet_data
        assert 'total_ships' in fleet_data
        assert 'status_counts' in fleet_data
        assert 'type_counts' in fleet_data
        
        # Check ships
        ships = fleet_data['ships']
        assert isinstance(ships, list)
        assert len(ships) > 0
        
        # Check first ship structure
        if ships:
            ship = ships[0]
            required_fields = [
                'id', 'name', 'type', 'status', 'location',
                'capacity_kg', 'current_cargo_kg', 'fuel_percentage',
                'hull_integrity', 'shield_strength', 'mining_power',
                'crew_size', 'mission_id', 'last_maintenance', 'next_maintenance'
            ]
            
            for field in required_fields:
                assert field in ship
        
        # Check status counts
        status_counts = fleet_data['status_counts']
        expected_statuses = ['active', 'docked', 'returning', 'maintenance']
        for status in expected_statuses:
            assert status in status_counts
            assert isinstance(status_counts[status], int)
    
    def test_get_economic_data(self):
        """Test economic data generation"""
        # Mock the pricing service
        self.mock_pricing.get_commodity_prices.return_value = {
            'Gold': 2000.0,
            'Platinum': 950.0,
            'Silver': 25.0,
            'Copper': 4.0,
            'Palladium': 1000.0
        }
        
        economic_data = self.viz_service._get_economic_data()
        
        # Check structure
        assert 'revenue' in economic_data
        assert 'costs' in economic_data
        assert 'profit' in economic_data
        assert 'commodity_prices' in economic_data
        assert 'market_trends' in economic_data
        
        # Check revenue data
        revenue = economic_data['revenue']
        required_revenue_fields = ['total', 'this_month', 'last_month', 'projected_annual']
        for field in required_revenue_fields:
            assert field in revenue
            assert isinstance(revenue[field], (int, float))
        
        # Check commodity prices
        commodity_prices = economic_data['commodity_prices']
        expected_commodities = ['Gold', 'Platinum', 'Silver', 'Copper', 'Palladium']
        for commodity in expected_commodities:
            assert commodity in commodity_prices
            assert isinstance(commodity_prices[commodity], (int, float))
    
    def test_get_orbital_data(self):
        """Test orbital mechanics data generation"""
        orbital_data = self.viz_service._get_orbital_data()
        
        # Check structure
        assert 'current_positions' in orbital_data
        assert 'trajectories' in orbital_data
        assert 'orbital_mechanics' in orbital_data
        
        # Check current positions
        positions = orbital_data['current_positions']
        expected_bodies = ['earth', 'ceres', 'pallas', 'juno']
        for body in expected_bodies:
            assert body in positions
            assert 'x' in positions[body]
            assert 'y' in positions[body]
            assert 'z' in positions[body]
        
        # Check trajectories
        trajectories = orbital_data['trajectories']
        assert isinstance(trajectories, list)
        if trajectories:
            trajectory = trajectories[0]
            required_fields = ['mission_id', 'start', 'end', 'progress', 'estimated_arrival']
            for field in required_fields:
                assert field in trajectory
    
    def test_get_risk_data(self):
        """Test risk assessment data generation"""
        risk_data = self.viz_service._get_risk_data()
        
        # Check structure
        assert 'overall_risk_level' in risk_data
        assert 'risk_factors' in risk_data
        assert 'mission_risks' in risk_data
        assert 'mitigation_strategies' in risk_data
        
        # Check risk factors
        risk_factors = risk_data['risk_factors']
        expected_factors = [
            'radiation_exposure', 'communication_delay', 'fuel_shortage',
            'equipment_failure', 'navigation_errors'
        ]
        for factor in expected_factors:
            assert factor in risk_factors
            assert 0 <= risk_factors[factor] <= 1
        
        # Check mission risks
        mission_risks = risk_data['mission_risks']
        assert isinstance(mission_risks, list)
        if mission_risks:
            mission_risk = mission_risks[0]
            required_fields = ['mission_id', 'risk_level', 'risk_score', 'primary_concerns']
            for field in required_fields:
                assert field in mission_risk
    
    def test_get_market_data(self):
        """Test market data generation"""
        market_data = self.viz_service._get_market_data()
        
        # Check structure
        assert 'commodity_prices' in market_data
        assert 'market_indicators' in market_data
        assert 'price_history' in market_data
        
        # Check commodity prices
        commodity_prices = market_data['commodity_prices']
        expected_commodities = ['Gold', 'Platinum', 'Silver', 'Copper', 'Palladium']
        for commodity in expected_commodities:
            assert commodity in commodity_prices
            price_data = commodity_prices[commodity]
            assert 'price' in price_data
            assert 'change' in price_data
            assert 'trend' in price_data
    
    def test_get_alert_data(self):
        """Test alert data generation"""
        alert_data = self.viz_service._get_alert_data()
        
        # Check structure
        assert isinstance(alert_data, list)
        if alert_data:
            alert = alert_data[0]
            required_fields = ['id', 'type', 'title', 'message', 'timestamp', 'priority']
            for field in required_fields:
                assert field in alert
    
    def test_get_chart_data(self):
        """Test chart data generation"""
        chart_data = self.viz_service._get_chart_data()
        
        # Check structure
        expected_charts = [
            'revenue_trend', 'mission_status', 'fleet_utilization',
            'risk_distribution', 'commodity_prices'
        ]
        
        for chart_name in expected_charts:
            assert chart_name in chart_data
            chart = chart_data[chart_name]
            assert 'labels' in chart
            assert 'data' in chart
            assert 'type' in chart
            assert isinstance(chart['labels'], list)
            assert isinstance(chart['data'], list)
            assert len(chart['labels']) == len(chart['data'])
    
    def test_get_mission_details(self):
        """Test mission details generation"""
        mission_details = self.viz_service.get_mission_details('M001')
        
        # Check structure
        required_fields = [
            'id', 'name', 'asteroid', 'status', 'progress',
            'timeline', 'crew', 'resources', 'orbital_mechanics', 'economics'
        ]
        
        for field in required_fields:
            assert field in mission_details
        
        # Check timeline
        timeline = mission_details['timeline']
        assert isinstance(timeline, list)
        if timeline:
            phase = timeline[0]
            required_phase_fields = ['phase', 'start', 'end', 'status']
            for field in required_phase_fields:
                assert field in phase
        
        # Check crew
        crew = mission_details['crew']
        assert isinstance(crew, list)
        if crew:
            crew_member = crew[0]
            required_crew_fields = ['name', 'role', 'status']
            for field in required_crew_fields:
                assert field in crew_member
    
    def test_get_asteroid_analysis(self):
        """Test asteroid analysis generation"""
        asteroid_analysis = self.viz_service.get_asteroid_analysis('Ceres')
        
        # Check structure
        required_fields = [
            'name', 'moid_au', 'size_km', 'composition',
            'mining_analysis', 'orbital_mechanics', 'risk_assessment', 'economic_analysis'
        ]
        
        for field in required_fields:
            assert field in asteroid_analysis
        
        # Check composition
        composition = asteroid_analysis['composition']
        assert isinstance(composition, dict)
        total_composition = sum(composition.values())
        assert abs(total_composition - 1.0) < 0.01  # Should sum to 1.0
        
        # Check mining analysis
        mining_analysis = asteroid_analysis['mining_analysis']
        required_mining_fields = ['difficulty', 'estimated_yield', 'mining_time_days', 'equipment_required']
        for field in required_mining_fields:
            assert field in mining_analysis
    
    def test_chart_colors(self):
        """Test chart color configuration"""
        colors = self.viz_service.chart_colors
        
        expected_colors = ['primary', 'secondary', 'success', 'warning', 'danger', 'info']
        for color in expected_colors:
            assert color in colors
            assert colors[color].startswith('#')
            assert len(colors[color]) == 7  # #RRGGBB format
    
    def test_refresh_interval(self):
        """Test refresh interval configuration"""
        assert self.viz_service.refresh_interval == 30
        assert isinstance(self.viz_service.refresh_interval, int)
        assert self.viz_service.refresh_interval > 0
    
    def test_display_limits(self):
        """Test display limits configuration"""
        assert self.viz_service.max_missions_display == 10
        assert self.viz_service.max_asteroids_display == 20
        assert isinstance(self.viz_service.max_missions_display, int)
        assert isinstance(self.viz_service.max_asteroids_display, int)
        assert self.viz_service.max_missions_display > 0
        assert self.viz_service.max_asteroids_display > 0


if __name__ == "__main__":
    pytest.main([__file__])
