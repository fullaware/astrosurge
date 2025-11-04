"""
Orbital Mechanics Calculations for AstroSurge

This service implements realistic travel time calculations using AU distances
and realistic propulsion speeds for asteroid mining missions.
"""
import logging
import math
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class OrbitalMechanicsService:
    """
    Service for calculating realistic orbital mechanics and travel times.
    
    Features:
    - Calculate travel time based on asteroid MOID field
    - Use realistic propulsion speeds (72,537 km/hour)
    - Account for return journey with additional mass
    - Update mission planning with accurate travel estimates
    - Handle various mission phases and trajectories
    """
    
    def __init__(self):
        """Initialize the orbital mechanics service"""
        # Physical constants
        self.AU_TO_KM = 149597870.7  # 1 AU = 149,597,870.7 km
        self.EARTH_RADIUS_KM = 6371  # Earth radius in km
        
        # Propulsion characteristics
        self.PROPULSION_SPEED_KMH = 72537  # 72,537 km/hour (20.15 km/s)
        self.PROPULSION_SPEED_KMS = 20.15  # 20.15 km/s
        
        # Mission parameters
        self.MIN_TRAVEL_DISTANCE_AU = 0.1  # Minimum 0.1 AU travel distance
        self.MAX_TRAVEL_DISTANCE_AU = 10.0  # Maximum 10.0 AU travel distance
        
        # Mass factors
        self.SHIP_DRY_MASS_KG = 10000  # 10,000 kg dry ship mass
        self.FUEL_MASS_KG = 20000  # 20,000 kg fuel mass (increased for long missions)
        self.CARGO_MASS_FACTOR = 1.2  # 20% additional mass for cargo
        
        # Mission phases
        self.MISSION_PHASES = {
            'departure': 'Departure from Earth',
            'transit': 'Transit to asteroid',
            'approach': 'Approach and orbit insertion',
            'mining': 'Mining operations',
            'departure_asteroid': 'Departure from asteroid',
            'return_transit': 'Return transit to Earth',
            'approach_earth': 'Approach and Earth orbit insertion',
            'landing': 'Landing on Earth'
        }
    
    def calculate_travel_time(self, moid_au: float, mission_type: str = 'round_trip') -> Dict[str, Any]:
        """
        Calculate travel time based on asteroid MOID field.
        
        Args:
            moid_au: Minimum Orbit Intersection Distance in AU
            mission_type: Type of mission ('one_way', 'round_trip', 'mining_mission')
            
        Returns:
            Dictionary with travel time calculations
        """
        try:
            # Validate input
            if moid_au < self.MIN_TRAVEL_DISTANCE_AU:
                moid_au = self.MIN_TRAVEL_DISTANCE_AU
            elif moid_au > self.MAX_TRAVEL_DISTANCE_AU:
                moid_au = self.MAX_TRAVEL_DISTANCE_AU
            
            # Convert AU to km
            distance_km = moid_au * self.AU_TO_KM
            
            # Calculate basic travel time (one way)
            one_way_time_hours = distance_km / self.PROPULSION_SPEED_KMH
            one_way_time_days = one_way_time_hours / 24
            
            # Calculate mission-specific travel times
            if mission_type == 'one_way':
                total_time_hours = one_way_time_hours
                total_time_days = one_way_time_days
                phases = self._calculate_one_way_phases(one_way_time_days)
                
            elif mission_type == 'round_trip':
                # Account for return journey with additional mass
                return_time_hours = one_way_time_hours * self.CARGO_MASS_FACTOR
                total_time_hours = one_way_time_hours + return_time_hours
                total_time_days = total_time_hours / 24
                phases = self._calculate_round_trip_phases(one_way_time_days, return_time_hours / 24)
                
            elif mission_type == 'mining_mission':
                # Full mining mission with approach, mining, and return
                approach_time_days = max(1, one_way_time_days * 0.1)  # 10% for approach
                mining_time_days = 30  # 30 days mining
                departure_time_days = max(1, one_way_time_days * 0.1)  # 10% for departure
                return_time_days = one_way_time_days * self.CARGO_MASS_FACTOR
                
                total_time_days = one_way_time_days + approach_time_days + mining_time_days + departure_time_days + return_time_days
                total_time_hours = total_time_days * 24
                phases = self._calculate_mining_mission_phases(
                    one_way_time_days, approach_time_days, mining_time_days, 
                    departure_time_days, return_time_days
                )
            else:
                raise ValueError(f"Unknown mission type: {mission_type}")
            
            # Calculate fuel requirements
            fuel_requirements = self._calculate_fuel_requirements(distance_km, mission_type)
            
            # Calculate mission costs
            mission_costs = self._calculate_mission_costs(total_time_days, distance_km)
            
            return {
                'moid_au': moid_au,
                'distance_km': distance_km,
                'mission_type': mission_type,
                'one_way_time_hours': one_way_time_hours,
                'one_way_time_days': one_way_time_days,
                'total_time_hours': total_time_hours,
                'total_time_days': total_time_days,
                'phases': phases,
                'fuel_requirements': fuel_requirements,
                'mission_costs': mission_costs,
                'propulsion_speed_kmh': self.PROPULSION_SPEED_KMH,
                'propulsion_speed_kms': self.PROPULSION_SPEED_KMS,
                'calculated_at': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"Error calculating travel time: {str(e)}")
            raise
    
    def _calculate_one_way_phases(self, transit_time_days: float) -> List[Dict[str, Any]]:
        """Calculate phases for one-way mission"""
        phases = [
            {
                'phase': 'departure',
                'description': 'Departure from Earth',
                'duration_days': 1,
                'start_day': 0,
                'end_day': 1
            },
            {
                'phase': 'transit',
                'description': 'Transit to asteroid',
                'duration_days': transit_time_days,
                'start_day': 1,
                'end_day': 1 + transit_time_days
            },
            {
                'phase': 'approach',
                'description': 'Approach and orbit insertion',
                'duration_days': 1,
                'start_day': 1 + transit_time_days,
                'end_day': 2 + transit_time_days
            }
        ]
        return phases
    
    def _calculate_round_trip_phases(self, outbound_time_days: float, return_time_days: float) -> List[Dict[str, Any]]:
        """Calculate phases for round-trip mission"""
        phases = [
            {
                'phase': 'departure',
                'description': 'Departure from Earth',
                'duration_days': 1,
                'start_day': 0,
                'end_day': 1
            },
            {
                'phase': 'transit',
                'description': 'Transit to asteroid',
                'duration_days': outbound_time_days,
                'start_day': 1,
                'end_day': 1 + outbound_time_days
            },
            {
                'phase': 'approach',
                'description': 'Approach and orbit insertion',
                'duration_days': 1,
                'start_day': 1 + outbound_time_days,
                'end_day': 2 + outbound_time_days
            },
            {
                'phase': 'departure_asteroid',
                'description': 'Departure from asteroid',
                'duration_days': 1,
                'start_day': 2 + outbound_time_days,
                'end_day': 3 + outbound_time_days
            },
            {
                'phase': 'return_transit',
                'description': 'Return transit to Earth',
                'duration_days': return_time_days,
                'start_day': 3 + outbound_time_days,
                'end_day': 3 + outbound_time_days + return_time_days
            },
            {
                'phase': 'approach_earth',
                'description': 'Approach and Earth orbit insertion',
                'duration_days': 1,
                'start_day': 3 + outbound_time_days + return_time_days,
                'end_day': 4 + outbound_time_days + return_time_days
            }
        ]
        return phases
    
    def _calculate_mining_mission_phases(self, transit_time_days: float, approach_time_days: float, 
                                       mining_time_days: float, departure_time_days: float, 
                                       return_time_days: float) -> List[Dict[str, Any]]:
        """Calculate phases for full mining mission"""
        phases = [
            {
                'phase': 'departure',
                'description': 'Departure from Earth',
                'duration_days': 1,
                'start_day': 0,
                'end_day': 1
            },
            {
                'phase': 'transit',
                'description': 'Transit to asteroid',
                'duration_days': transit_time_days,
                'start_day': 1,
                'end_day': 1 + transit_time_days
            },
            {
                'phase': 'approach',
                'description': 'Approach and orbit insertion',
                'duration_days': approach_time_days,
                'start_day': 1 + transit_time_days,
                'end_day': 1 + transit_time_days + approach_time_days
            },
            {
                'phase': 'mining',
                'description': 'Mining operations',
                'duration_days': mining_time_days,
                'start_day': 1 + transit_time_days + approach_time_days,
                'end_day': 1 + transit_time_days + approach_time_days + mining_time_days
            },
            {
                'phase': 'departure_asteroid',
                'description': 'Departure from asteroid',
                'duration_days': departure_time_days,
                'start_day': 1 + transit_time_days + approach_time_days + mining_time_days,
                'end_day': 1 + transit_time_days + approach_time_days + mining_time_days + departure_time_days
            },
            {
                'phase': 'return_transit',
                'description': 'Return transit to Earth',
                'duration_days': return_time_days,
                'start_day': 1 + transit_time_days + approach_time_days + mining_time_days + departure_time_days,
                'end_day': 1 + transit_time_days + approach_time_days + mining_time_days + departure_time_days + return_time_days
            },
            {
                'phase': 'approach_earth',
                'description': 'Approach and Earth orbit insertion',
                'duration_days': 1,
                'start_day': 1 + transit_time_days + approach_time_days + mining_time_days + departure_time_days + return_time_days,
                'end_day': 2 + transit_time_days + approach_time_days + mining_time_days + departure_time_days + return_time_days
            }
        ]
        return phases
    
    def _calculate_fuel_requirements(self, distance_km: float, mission_type: str) -> Dict[str, Any]:
        """Calculate fuel requirements for mission"""
        # Base fuel consumption (kg per 1000 km)
        base_fuel_consumption = 0.01  # 0.01 kg per 1000 km (ultra-efficient ion drive)
        
        # Calculate fuel for outbound journey
        outbound_fuel = (distance_km / 1000) * base_fuel_consumption
        
        if mission_type == 'one_way':
            total_fuel = outbound_fuel
        elif mission_type == 'round_trip':
            # Return journey requires more fuel due to cargo mass
            return_fuel = outbound_fuel * self.CARGO_MASS_FACTOR
            total_fuel = outbound_fuel + return_fuel
        elif mission_type == 'mining_mission':
            # Mining mission includes approach, mining operations, and return
            approach_fuel = outbound_fuel * 0.2  # 20% for approach
            mining_fuel = 500  # 500 kg for mining operations
            return_fuel = outbound_fuel * self.CARGO_MASS_FACTOR
            total_fuel = outbound_fuel + approach_fuel + mining_fuel + return_fuel
        else:
            total_fuel = outbound_fuel
        
        return {
            'outbound_fuel_kg': outbound_fuel,
            'return_fuel_kg': total_fuel - outbound_fuel if mission_type != 'one_way' else 0,
            'total_fuel_kg': total_fuel,
            'fuel_margin_kg': total_fuel * 0.1,  # 10% safety margin
            'total_with_margin_kg': total_fuel * 1.1,
            'fuel_sufficient': total_fuel * 1.1 <= self.FUEL_MASS_KG
        }
    
    def _calculate_mission_costs(self, total_time_days: float, distance_km: float) -> Dict[str, Any]:
        """Calculate mission costs based on time and distance"""
        # Base costs per day
        base_cost_per_day = 100000  # $100,000 per day
        
        # Distance-based costs
        distance_cost_per_km = 10  # $10 per km
        
        # Calculate costs
        time_cost = total_time_days * base_cost_per_day
        distance_cost = distance_km * distance_cost_per_km
        total_cost = time_cost + distance_cost
        
        return {
            'time_cost': time_cost,
            'distance_cost': distance_cost,
            'total_cost': total_cost,
            'cost_per_day': base_cost_per_day,
            'cost_per_km': distance_cost_per_km
        }
    
    def calculate_mission_trajectory(self, moid_au: float, mission_type: str = 'mining_mission') -> Dict[str, Any]:
        """
        Calculate detailed mission trajectory including velocity changes.
        
        Args:
            moid_au: Minimum Orbit Intersection Distance in AU
            mission_type: Type of mission
            
        Returns:
            Dictionary with trajectory calculations
        """
        try:
            # Get basic travel time calculations
            travel_data = self.calculate_travel_time(moid_au, mission_type)
            
            # Calculate velocity changes
            distance_km = travel_data['distance_km']
            one_way_time_hours = travel_data['one_way_time_hours']
            
            # Calculate required delta-v for outbound journey
            # Assuming Hohmann transfer orbit
            earth_orbital_velocity = 29.78  # km/s (Earth's orbital velocity)
            asteroid_orbital_velocity = earth_orbital_velocity * math.sqrt(1 / moid_au)  # Simplified
            
            # Delta-v calculations
            departure_delta_v = 3.5  # km/s (Earth departure)
            arrival_delta_v = 1.0  # km/s (Asteroid arrival)
            departure_asteroid_delta_v = 1.0  # km/s (Asteroid departure)
            arrival_earth_delta_v = 3.5  # km/s (Earth arrival)
            
            total_delta_v = departure_delta_v + arrival_delta_v
            if mission_type != 'one_way':
                total_delta_v += departure_asteroid_delta_v + arrival_earth_delta_v
            
            # Calculate acceleration and deceleration phases
            acceleration_time_hours = 24  # 24 hours acceleration
            deceleration_time_hours = 24  # 24 hours deceleration
            
            # Calculate cruise time
            cruise_time_hours = one_way_time_hours - acceleration_time_hours - deceleration_time_hours
            
            trajectory = {
                'moid_au': moid_au,
                'distance_km': distance_km,
                'mission_type': mission_type,
                'velocity_changes': {
                    'departure_delta_v': departure_delta_v,
                    'arrival_delta_v': arrival_delta_v,
                    'departure_asteroid_delta_v': departure_asteroid_delta_v,
                    'arrival_earth_delta_v': arrival_earth_delta_v,
                    'total_delta_v': total_delta_v
                },
                'flight_phases': {
                    'acceleration_time_hours': acceleration_time_hours,
                    'cruise_time_hours': cruise_time_hours,
                    'deceleration_time_hours': deceleration_time_hours,
                    'total_time_hours': one_way_time_hours
                },
                'orbital_velocities': {
                    'earth_orbital_velocity': earth_orbital_velocity,
                    'asteroid_orbital_velocity': asteroid_orbital_velocity
                }
            }
            
            # Merge with travel data
            trajectory.update(travel_data)
            
            return trajectory
            
        except Exception as e:
            logger.error(f"Error calculating mission trajectory: {str(e)}")
            raise
    
    def calculate_mission_risk_factors(self, moid_au: float, mission_type: str = 'mining_mission') -> Dict[str, Any]:
        """
        Calculate mission risk factors based on distance and mission complexity.
        
        Args:
            moid_au: Minimum Orbit Intersection Distance in AU
            mission_type: Type of mission
            
        Returns:
            Dictionary with risk factor calculations
        """
        try:
            # Base risk factors
            distance_risk = min(1.0, moid_au / 5.0)  # Risk increases with distance
            time_risk = min(1.0, moid_au / 3.0)  # Risk increases with time
            
            # Mission complexity risk
            complexity_risk = {
                'one_way': 0.3,
                'round_trip': 0.5,
                'mining_mission': 0.7
            }.get(mission_type, 0.5)
            
            # Calculate total risk score (0-1 scale)
            total_risk = (distance_risk * 0.4 + time_risk * 0.3 + complexity_risk * 0.3)
            
            # Risk categories
            if total_risk < 0.3:
                risk_level = 'low'
            elif total_risk < 0.6:
                risk_level = 'medium'
            else:
                risk_level = 'high'
            
            # Specific risk factors
            risk_factors = {
                'radiation_exposure': min(1.0, moid_au * 0.2),
                'communication_delay': min(1.0, moid_au * 0.1),
                'fuel_shortage': min(1.0, moid_au * 0.15),
                'equipment_failure': min(1.0, moid_au * 0.1),
                'navigation_errors': min(1.0, moid_au * 0.05)
            }
            
            return {
                'moid_au': moid_au,
                'mission_type': mission_type,
                'risk_scores': {
                    'distance_risk': distance_risk,
                    'time_risk': time_risk,
                    'complexity_risk': complexity_risk,
                    'total_risk': total_risk
                },
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'recommendations': self._get_risk_recommendations(total_risk, risk_factors)
            }
            
        except Exception as e:
            logger.error(f"Error calculating mission risk factors: {str(e)}")
            raise
    
    def _get_risk_recommendations(self, total_risk: float, risk_factors: Dict[str, float]) -> List[str]:
        """Get risk mitigation recommendations"""
        recommendations = []
        
        if total_risk > 0.7:
            recommendations.append("Consider shorter mission duration or closer asteroid")
            recommendations.append("Implement redundant systems and backup plans")
            recommendations.append("Increase fuel margins and safety reserves")
        
        if risk_factors['radiation_exposure'] > 0.5:
            recommendations.append("Implement enhanced radiation shielding")
            recommendations.append("Monitor crew radiation exposure levels")
        
        if risk_factors['communication_delay'] > 0.3:
            recommendations.append("Implement autonomous operation capabilities")
            recommendations.append("Establish emergency communication protocols")
        
        if risk_factors['fuel_shortage'] > 0.4:
            recommendations.append("Increase fuel capacity or optimize trajectory")
            recommendations.append("Implement fuel-efficient propulsion systems")
        
        if risk_factors['equipment_failure'] > 0.3:
            recommendations.append("Implement redundant critical systems")
            recommendations.append("Increase maintenance and inspection frequency")
        
        return recommendations
    
    def update_mission_planning(self, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update mission planning with accurate travel estimates.
        
        Args:
            mission_data: Existing mission data
            
        Returns:
            Updated mission data with orbital mechanics calculations
        """
        try:
            # Extract asteroid information
            asteroid_name = mission_data.get('asteroid_name', '')
            moid_au = mission_data.get('moid_au', 1.0)
            mission_type = mission_data.get('mission_type', 'mining_mission')
            
            # Calculate orbital mechanics
            travel_calculations = self.calculate_travel_time(moid_au, mission_type)
            trajectory = self.calculate_mission_trajectory(moid_au, mission_type)
            risk_factors = self.calculate_mission_risk_factors(moid_au, mission_type)
            
            # Update mission data
            updated_mission = mission_data.copy()
            updated_mission.update({
                'orbital_mechanics': {
                    'travel_calculations': travel_calculations,
                    'trajectory': trajectory,
                    'risk_factors': risk_factors
                },
                'travel_days': int(travel_calculations['total_time_days']),
                'fuel_requirements': travel_calculations['fuel_requirements'],
                'mission_costs': travel_calculations['mission_costs'],
                'risk_level': risk_factors['risk_level'],
                'updated_at': datetime.now(timezone.utc)
            })
            
            return updated_mission
            
        except Exception as e:
            logger.error(f"Error updating mission planning: {str(e)}")
            raise


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    def main():
        # Create orbital mechanics service
        orbital_service = OrbitalMechanicsService()
        
        print("🚀 AstroSurge Orbital Mechanics Service")
        print("=" * 50)
        
        # Test with different asteroids
        test_asteroids = [
            {'name': 'Ceres', 'moid': 1.59478},
            {'name': 'Pallas', 'moid': 1.23429},
            {'name': 'Juno', 'moid': 1.03429},
            {'name': 'Vesta', 'moid': 1.32429}
        ]
        
        for asteroid in test_asteroids:
            print(f"\n📊 Asteroid: {asteroid['name']} (MOID: {asteroid['moid']} AU)")
            
            # Calculate travel time for mining mission
            travel_data = orbital_service.calculate_travel_time(asteroid['moid'], 'mining_mission')
            
            print(f"  - Distance: {travel_data['distance_km']:,.0f} km")
            print(f"  - Total Time: {travel_data['total_time_days']:.1f} days")
            print(f"  - Fuel Required: {travel_data['fuel_requirements']['total_fuel_kg']:,.0f} kg")
            print(f"  - Mission Cost: ${travel_data['mission_costs']['total_cost']:,.0f}")
            
            # Calculate risk factors
            risk_data = orbital_service.calculate_mission_risk_factors(asteroid['moid'], 'mining_mission')
            print(f"  - Risk Level: {risk_data['risk_level'].upper()}")
            print(f"  - Total Risk: {risk_data['risk_scores']['total_risk']:.2f}")
        
        print(f"\n🎯 Orbital Mechanics Calculations Complete!")
        print(f"✅ Realistic travel time calculations implemented")
        print(f"✅ Propulsion speeds: {orbital_service.PROPULSION_SPEED_KMH:,} km/h")
        print(f"✅ Mission planning integration ready")
    
    # Run the example
    main()
