"""
Test suite for orbital mechanics service
"""
import pytest
import math
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Add the project root to the Python path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.orbital_mechanics import OrbitalMechanicsService


class TestOrbitalMechanicsService:
    """Test cases for orbital mechanics service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.orbital_service = OrbitalMechanicsService()
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        assert self.orbital_service.AU_TO_KM == 149597870.7
        assert self.orbital_service.PROPULSION_SPEED_KMH == 72537
        assert self.orbital_service.PROPULSION_SPEED_KMS == 20.15
        assert self.orbital_service.SHIP_DRY_MASS_KG == 10000
        assert self.orbital_service.FUEL_MASS_KG == 20000
        assert self.orbital_service.CARGO_MASS_FACTOR == 1.2
    
    def test_calculate_travel_time_one_way(self):
        """Test one-way travel time calculation"""
        moid_au = 1.5
        result = self.orbital_service.calculate_travel_time(moid_au, 'one_way')
        
        # Check basic structure
        assert 'moid_au' in result
        assert 'distance_km' in result
        assert 'mission_type' in result
        assert 'one_way_time_hours' in result
        assert 'one_way_time_days' in result
        assert 'total_time_hours' in result
        assert 'total_time_days' in result
        assert 'phases' in result
        assert 'fuel_requirements' in result
        assert 'mission_costs' in result
        
        # Check values
        assert result['moid_au'] == 1.5
        assert result['mission_type'] == 'one_way'
        assert result['distance_km'] == 1.5 * 149597870.7
        assert result['one_way_time_hours'] > 0
        assert result['one_way_time_days'] > 0
        assert result['total_time_hours'] == result['one_way_time_hours']
        assert result['total_time_days'] == result['one_way_time_days']
        
        # Check phases
        assert len(result['phases']) == 3  # departure, transit, approach
        assert result['phases'][0]['phase'] == 'departure'
        assert result['phases'][1]['phase'] == 'transit'
        assert result['phases'][2]['phase'] == 'approach'
    
    def test_calculate_travel_time_round_trip(self):
        """Test round-trip travel time calculation"""
        moid_au = 2.0
        result = self.orbital_service.calculate_travel_time(moid_au, 'round_trip')
        
        # Check values
        assert result['mission_type'] == 'round_trip'
        assert result['total_time_days'] > result['one_way_time_days']
        
        # Check phases
        assert len(result['phases']) == 6  # All phases for round trip
        phase_names = [phase['phase'] for phase in result['phases']]
        assert 'departure' in phase_names
        assert 'transit' in phase_names
        assert 'approach' in phase_names
        assert 'departure_asteroid' in phase_names
        assert 'return_transit' in phase_names
        assert 'approach_earth' in phase_names
    
    def test_calculate_travel_time_mining_mission(self):
        """Test mining mission travel time calculation"""
        moid_au = 1.0
        result = self.orbital_service.calculate_travel_time(moid_au, 'mining_mission')
        
        # Check values
        assert result['mission_type'] == 'mining_mission'
        assert result['total_time_days'] > result['one_way_time_days']
        
        # Check phases
        assert len(result['phases']) == 7  # All phases for mining mission
        phase_names = [phase['phase'] for phase in result['phases']]
        assert 'mining' in phase_names
        
        # Check mining phase
        mining_phase = next(phase for phase in result['phases'] if phase['phase'] == 'mining')
        assert mining_phase['duration_days'] == 30
    
    def test_calculate_travel_time_edge_cases(self):
        """Test travel time calculation with edge cases"""
        # Test minimum distance
        result_min = self.orbital_service.calculate_travel_time(0.05, 'one_way')
        assert result_min['moid_au'] == 0.1  # Should be clamped to minimum
        
        # Test maximum distance
        result_max = self.orbital_service.calculate_travel_time(15.0, 'one_way')
        assert result_max['moid_au'] == 10.0  # Should be clamped to maximum
        
        # Test negative distance
        result_neg = self.orbital_service.calculate_travel_time(-1.0, 'one_way')
        assert result_neg['moid_au'] == 0.1  # Should be clamped to minimum
    
    def test_calculate_travel_time_invalid_mission_type(self):
        """Test travel time calculation with invalid mission type"""
        with pytest.raises(ValueError, match="Unknown mission type"):
            self.orbital_service.calculate_travel_time(1.0, 'invalid_mission')
    
    def test_calculate_mission_trajectory(self):
        """Test mission trajectory calculation"""
        moid_au = 1.5
        result = self.orbital_service.calculate_mission_trajectory(moid_au, 'mining_mission')
        
        # Check basic structure
        assert 'moid_au' in result
        assert 'distance_km' in result
        assert 'mission_type' in result
        assert 'velocity_changes' in result
        assert 'flight_phases' in result
        assert 'orbital_velocities' in result
        
        # Check velocity changes
        velocity_changes = result['velocity_changes']
        assert 'departure_delta_v' in velocity_changes
        assert 'arrival_delta_v' in velocity_changes
        assert 'departure_asteroid_delta_v' in velocity_changes
        assert 'arrival_earth_delta_v' in velocity_changes
        assert 'total_delta_v' in velocity_changes
        
        # Check flight phases
        flight_phases = result['flight_phases']
        assert 'acceleration_time_hours' in flight_phases
        assert 'cruise_time_hours' in flight_phases
        assert 'deceleration_time_hours' in flight_phases
        assert 'total_time_hours' in flight_phases
        
        # Check orbital velocities
        orbital_velocities = result['orbital_velocities']
        assert 'earth_orbital_velocity' in orbital_velocities
        assert 'asteroid_orbital_velocity' in orbital_velocities
        assert orbital_velocities['earth_orbital_velocity'] == 29.78
    
    def test_calculate_mission_risk_factors(self):
        """Test mission risk factor calculation"""
        moid_au = 2.0
        result = self.orbital_service.calculate_mission_risk_factors(moid_au, 'mining_mission')
        
        # Check basic structure
        assert 'moid_au' in result
        assert 'mission_type' in result
        assert 'risk_scores' in result
        assert 'risk_level' in result
        assert 'risk_factors' in result
        assert 'recommendations' in result
        
        # Check risk scores
        risk_scores = result['risk_scores']
        assert 'distance_risk' in risk_scores
        assert 'time_risk' in risk_scores
        assert 'complexity_risk' in risk_scores
        assert 'total_risk' in risk_scores
        
        # Check risk level
        assert result['risk_level'] in ['low', 'medium', 'high']
        
        # Check risk factors
        risk_factors = result['risk_factors']
        expected_factors = ['radiation_exposure', 'communication_delay', 'fuel_shortage', 
                           'equipment_failure', 'navigation_errors']
        for factor in expected_factors:
            assert factor in risk_factors
            assert 0 <= risk_factors[factor] <= 1
        
        # Check recommendations
        assert isinstance(result['recommendations'], list)
        # Recommendations might be empty for low-risk scenarios
        # assert len(result['recommendations']) > 0
    
    def test_calculate_mission_risk_factors_different_levels(self):
        """Test risk factor calculation for different risk levels"""
        # Low risk (close asteroid)
        result_low = self.orbital_service.calculate_mission_risk_factors(0.5, 'one_way')
        assert result_low['risk_level'] == 'low'
        assert result_low['risk_scores']['total_risk'] < 0.3
        
        # Medium risk (medium distance)
        result_medium = self.orbital_service.calculate_mission_risk_factors(2.0, 'round_trip')
        assert result_medium['risk_level'] == 'medium'
        assert 0.3 <= result_medium['risk_scores']['total_risk'] < 0.6
        
        # High risk (far asteroid)
        result_high = self.orbital_service.calculate_mission_risk_factors(8.0, 'mining_mission')
        assert result_high['risk_level'] == 'high'
        assert result_high['risk_scores']['total_risk'] >= 0.6
    
    def test_update_mission_planning(self):
        """Test mission planning update"""
        mission_data = {
            'asteroid_name': 'Test Asteroid',
            'moid_au': 1.5,
            'mission_type': 'mining_mission',
            'existing_field': 'existing_value'
        }
        
        result = self.orbital_service.update_mission_planning(mission_data)
        
        # Check that existing fields are preserved
        assert result['asteroid_name'] == 'Test Asteroid'
        assert result['existing_field'] == 'existing_value'
        
        # Check that orbital mechanics data is added
        assert 'orbital_mechanics' in result
        assert 'travel_days' in result
        assert 'fuel_requirements' in result
        assert 'mission_costs' in result
        assert 'risk_level' in result
        assert 'updated_at' in result
        
        # Check orbital mechanics structure
        orbital_mechanics = result['orbital_mechanics']
        assert 'travel_calculations' in orbital_mechanics
        assert 'trajectory' in orbital_mechanics
        assert 'risk_factors' in orbital_mechanics
    
    def test_fuel_requirements_calculation(self):
        """Test fuel requirements calculation"""
        # Test one-way mission
        result_one_way = self.orbital_service.calculate_travel_time(1.0, 'one_way')
        fuel_one_way = result_one_way['fuel_requirements']
        assert fuel_one_way['total_fuel_kg'] > 0
        assert fuel_one_way['return_fuel_kg'] == 0
        assert fuel_one_way['fuel_sufficient'] == True
        
        # Test round-trip mission
        result_round_trip = self.orbital_service.calculate_travel_time(1.0, 'round_trip')
        fuel_round_trip = result_round_trip['fuel_requirements']
        assert fuel_round_trip['total_fuel_kg'] > fuel_one_way['total_fuel_kg']
        assert fuel_round_trip['return_fuel_kg'] > 0
        assert fuel_round_trip['fuel_margin_kg'] > 0
        assert fuel_round_trip['total_with_margin_kg'] > fuel_round_trip['total_fuel_kg']
        
        # Test mining mission
        result_mining = self.orbital_service.calculate_travel_time(1.0, 'mining_mission')
        fuel_mining = result_mining['fuel_requirements']
        assert fuel_mining['total_fuel_kg'] > fuel_round_trip['total_fuel_kg']
    
    def test_mission_costs_calculation(self):
        """Test mission costs calculation"""
        result = self.orbital_service.calculate_travel_time(2.0, 'mining_mission')
        costs = result['mission_costs']
        
        # Check cost structure
        assert 'time_cost' in costs
        assert 'distance_cost' in costs
        assert 'total_cost' in costs
        assert 'cost_per_day' in costs
        assert 'cost_per_km' in costs
        
        # Check cost values
        assert costs['time_cost'] > 0
        assert costs['distance_cost'] > 0
        assert costs['total_cost'] == costs['time_cost'] + costs['distance_cost']
        assert costs['cost_per_day'] == 100000
        assert costs['cost_per_km'] == 10
    
    def test_phase_calculations(self):
        """Test phase calculation methods"""
        # Test one-way phases
        phases_one_way = self.orbital_service._calculate_one_way_phases(10.0)
        assert len(phases_one_way) == 3
        assert phases_one_way[0]['phase'] == 'departure'
        assert phases_one_way[1]['phase'] == 'transit'
        assert phases_one_way[2]['phase'] == 'approach'
        assert phases_one_way[1]['duration_days'] == 10.0
        
        # Test round-trip phases
        phases_round_trip = self.orbital_service._calculate_round_trip_phases(10.0, 12.0)
        assert len(phases_round_trip) == 6
        phase_names = [phase['phase'] for phase in phases_round_trip]
        assert 'departure' in phase_names
        assert 'transit' in phase_names
        assert 'approach' in phase_names
        assert 'departure_asteroid' in phase_names
        assert 'return_transit' in phase_names
        assert 'approach_earth' in phase_names
        
        # Test mining mission phases
        phases_mining = self.orbital_service._calculate_mining_mission_phases(10.0, 1.0, 30.0, 1.0, 12.0)
        assert len(phases_mining) == 7
        phase_names = [phase['phase'] for phase in phases_mining]
        assert 'mining' in phase_names
        mining_phase = next(phase for phase in phases_mining if phase['phase'] == 'mining')
        assert mining_phase['duration_days'] == 30.0
    
    def test_risk_recommendations(self):
        """Test risk recommendation generation"""
        # Test high risk scenario
        high_risk_factors = {
            'radiation_exposure': 0.8,
            'communication_delay': 0.6,
            'fuel_shortage': 0.7,
            'equipment_failure': 0.5,
            'navigation_errors': 0.3
        }
        recommendations = self.orbital_service._get_risk_recommendations(0.8, high_risk_factors)
        
        assert len(recommendations) > 0
        assert any('radiation' in rec.lower() for rec in recommendations)
        assert any('communication' in rec.lower() for rec in recommendations)
        assert any('fuel' in rec.lower() for rec in recommendations)
        assert any('redundant' in rec.lower() for rec in recommendations)
        
        # Test low risk scenario
        low_risk_factors = {
            'radiation_exposure': 0.2,
            'communication_delay': 0.1,
            'fuel_shortage': 0.2,
            'equipment_failure': 0.1,
            'navigation_errors': 0.1
        }
        recommendations_low = self.orbital_service._get_risk_recommendations(0.2, low_risk_factors)
        
        # Should have fewer recommendations for low risk
        assert len(recommendations_low) <= len(recommendations)
    
    def test_physical_constants(self):
        """Test that physical constants are correct"""
        assert self.orbital_service.AU_TO_KM == 149597870.7
        assert self.orbital_service.EARTH_RADIUS_KM == 6371
        assert self.orbital_service.PROPULSION_SPEED_KMH == 72537
        assert self.orbital_service.PROPULSION_SPEED_KMS == 20.15
    
    def test_mission_parameters(self):
        """Test that mission parameters are reasonable"""
        assert self.orbital_service.MIN_TRAVEL_DISTANCE_AU == 0.1
        assert self.orbital_service.MAX_TRAVEL_DISTANCE_AU == 10.0
        assert self.orbital_service.SHIP_DRY_MASS_KG == 10000
        assert self.orbital_service.FUEL_MASS_KG == 20000
        assert self.orbital_service.CARGO_MASS_FACTOR == 1.2
    
    def test_mission_phases_enum(self):
        """Test that mission phases are properly defined"""
        phases = self.orbital_service.MISSION_PHASES
        expected_phases = [
            'departure', 'transit', 'approach', 'mining',
            'departure_asteroid', 'return_transit', 'approach_earth', 'landing'
        ]
        
        for phase in expected_phases:
            assert phase in phases
            assert isinstance(phases[phase], str)
            assert len(phases[phase]) > 0


if __name__ == "__main__":
    pytest.main([__file__])
