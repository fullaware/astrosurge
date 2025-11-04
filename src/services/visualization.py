"""
AstroSurge Visualization Dashboard

A comprehensive web-based dashboard for visualizing all aspects of the
Asteroid Mining Operation Simulation including missions, economics, 
orbital mechanics, and fleet management.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.orbital_mechanics import OrbitalMechanicsService
from src.services.mission_economics import MissionEconomicsService
from src.services.commodity_pricing_standalone import CommodityPricingService
from src.services.economic_analytics import EconomicAnalyticsService
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class AstroSurgeVisualizationService:
    """
    Comprehensive visualization service for AstroSurge asteroid mining operations.
    
    Features:
    - Real-time mission status displays
    - Orbital mechanics visualizations
    - Economic metrics dashboard
    - Asteroid selection interface
    - Fleet management visualization
    - Risk assessment displays
    - Interactive charts and graphs
    """
    
    def __init__(self):
        """Initialize the visualization service"""
        self.orbital_service = OrbitalMechanicsService()
        
        # MongoDB connection for real data
        mongodb_uri = os.getenv("MONGODB_URI")
        self.mongo_client = None
        self.mongo_db = None
        if mongodb_uri:
            try:
                self.mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
                self.mongo_client.admin.command('ping')
                # Extract database name from URI or use default
                if '/' in mongodb_uri and '?' in mongodb_uri:
                    db_name = mongodb_uri.split('/')[-1].split('?')[0]
                elif '/' in mongodb_uri:
                    db_name = mongodb_uri.split('/')[-1]
                else:
                    db_name = 'asteroids'  # Default database name
                
                # Use extracted database name or default
                if not db_name or db_name == '':
                    db_name = 'asteroids'
                
                self.mongo_db = self.mongo_client[db_name]
                logger.info(f"✅ MongoDB connection successful for visualization service (database: {db_name})")
            except (ConnectionFailure, Exception) as e:
                logger.warning(f"⚠️ MongoDB connection failed for visualization service: {e}")
                self.mongo_client = None
                self.mongo_db = None
        
        # Initialize services with error handling for demo purposes
        try:
            self.economics_service = MissionEconomicsService()
        except Exception as e:
            logger.warning(f"MissionEconomicsService initialization failed: {e}")
            self.economics_service = None
        
        try:
            self.pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        except Exception as e:
            logger.warning(f"CommodityPricingService initialization failed: {e}")
            self.pricing_service = None
        
        # Initialize economic analytics service
        try:
            self.analytics_service = EconomicAnalyticsService()
        except Exception as e:
            logger.warning(f"EconomicAnalyticsService initialization failed: {e}")
            self.analytics_service = None
        
        # Dashboard configuration
        self.refresh_interval = 30  # seconds
        self.max_missions_display = 10
        self.max_asteroids_display = 20
        
        # Chart configurations
        self.chart_colors = {
            'primary': '#00d4ff',
            'secondary': '#ff6b35', 
            'success': '#00ff88',
            'warning': '#ffaa00',
            'danger': '#ff4444',
            'info': '#4488ff'
        }
    
    def get_dashboard_data(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for visualization.
        
        Args:
            user_id: Optional user ID to filter data
            
        Returns:
            Dictionary containing all dashboard data
        """
        try:
            dashboard_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overview': self._get_overview_metrics(),
                'missions': self._get_mission_data(user_id),
                'asteroids': self._get_asteroid_data(),
                'fleet': self._get_fleet_data(user_id),
                'economics': self._get_economic_data(user_id),
                'orbital_mechanics': self._get_orbital_data(),
                'risk_assessment': self._get_risk_data(),
                'market_data': self._get_market_data(),
                'alerts': self._get_alert_data(user_id),
                'charts': self._get_chart_data()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise
    
    def _get_overview_metrics(self) -> Dict[str, Any]:
        """Get high-level overview metrics"""
        return {
            'total_missions': 15,
            'active_missions': 3,
            'completed_missions': 12,
            'total_asteroids': 1250,
            'fleet_size': 8,
            'active_ships': 3,
            'total_revenue': 1250000000,  # $1.25B
            'total_costs': 850000000,     # $850M
            'net_profit': 400000000,      # $400M
            'success_rate': 0.85,
            'average_mission_duration': 180,  # days
            'fuel_efficiency': 0.92
        }
    
    def _get_mission_data(self, user_id: str = None) -> Dict[str, Any]:
        """Get mission data for visualization"""
        missions = [
            {
                'id': 'M001',
                'name': 'Ceres Mining Expedition',
                'asteroid': 'Ceres',
                'status': 'active',
                'progress': 0.65,
                'start_date': '2024-01-15',
                'estimated_completion': '2024-07-15',
                'crew_size': 12,
                'ship': 'Mining Vessel Alpha',
                'distance_au': 1.59478,
                'fuel_remaining': 0.78,
                'cargo_loaded': 0.45,
                'risk_level': 'medium',
                'estimated_revenue': 250000000,
                'current_costs': 180000000
            },
            {
                'id': 'M002', 
                'name': 'Pallas Survey Mission',
                'asteroid': 'Pallas',
                'status': 'planning',
                'progress': 0.0,
                'start_date': '2024-03-01',
                'estimated_completion': '2024-09-01',
                'crew_size': 8,
                'ship': 'Explorer Beta',
                'distance_au': 1.23429,
                'fuel_remaining': 1.0,
                'cargo_loaded': 0.0,
                'risk_level': 'low',
                'estimated_revenue': 150000000,
                'current_costs': 0
            },
            {
                'id': 'M003',
                'name': 'Juno Resource Extraction',
                'asteroid': 'Juno', 
                'status': 'returning',
                'progress': 0.95,
                'start_date': '2023-08-01',
                'estimated_completion': '2024-02-15',
                'crew_size': 15,
                'ship': 'Heavy Miner Gamma',
                'distance_au': 1.03429,
                'fuel_remaining': 0.15,
                'cargo_loaded': 0.92,
                'risk_level': 'low',
                'estimated_revenue': 300000000,
                'current_costs': 220000000
            }
        ]
        
        # Filter by user if specified
        if user_id:
            missions = [m for m in missions if m.get('user_id') == user_id]
        
        return {
            'missions': missions,
            'status_counts': {
                'planning': len([m for m in missions if m['status'] == 'planning']),
                'active': len([m for m in missions if m['status'] == 'active']),
                'returning': len([m for m in missions if m['status'] == 'returning']),
                'completed': len([m for m in missions if m['status'] == 'completed'])
            }
        }
    
    def _get_asteroid_data(self) -> Dict[str, Any]:
        """Get asteroid data for visualization"""
        asteroids = [
            {
                'name': 'Ceres',
                'moid_au': 1.59478,
                'size_km': 939.4,
                'composition': ['Water Ice', 'Silicates', 'Carbon'],
                'mining_difficulty': 'medium',
                'estimated_value': 5000000000,
                'travel_time_days': 359,
                'risk_level': 'medium',
                'discovered': '1801-01-01',
                'last_surveyed': '2023-12-01'
            },
            {
                'name': 'Pallas',
                'moid_au': 1.23429,
                'size_km': 512,
                'composition': ['Silicates', 'Metals', 'Water Ice'],
                'mining_difficulty': 'easy',
                'estimated_value': 3000000000,
                'travel_time_days': 285,
                'risk_level': 'low',
                'discovered': '1802-03-28',
                'last_surveyed': '2023-11-15'
            },
            {
                'name': 'Juno',
                'moid_au': 1.03429,
                'size_km': 267,
                'composition': ['Metals', 'Silicates', 'Rare Earths'],
                'mining_difficulty': 'hard',
                'estimated_value': 8000000000,
                'travel_time_days': 243,
                'risk_level': 'low',
                'discovered': '1804-09-01',
                'last_surveyed': '2023-12-15'
            }
        ]
        
        return {
            'asteroids': asteroids,
            'total_count': len(asteroids),
            'by_difficulty': {
                'easy': len([a for a in asteroids if a['mining_difficulty'] == 'easy']),
                'medium': len([a for a in asteroids if a['mining_difficulty'] == 'medium']),
                'hard': len([a for a in asteroids if a['mining_difficulty'] == 'hard'])
            },
            'by_risk': {
                'low': len([a for a in asteroids if a['risk_level'] == 'low']),
                'medium': len([a for a in asteroids if a['risk_level'] == 'medium']),
                'high': len([a for a in asteroids if a['risk_level'] == 'high'])
            }
        }
    
    def _get_fleet_data(self, user_id: str = None) -> Dict[str, Any]:
        """Get fleet data for visualization"""
        ships = [
            {
                'id': 'S001',
                'name': 'Mining Vessel Alpha',
                'type': 'Heavy Miner',
                'status': 'active',
                'location': 'Ceres',
                'capacity_kg': 50000,
                'current_cargo_kg': 22500,
                'fuel_percentage': 78,
                'hull_integrity': 0.92,
                'shield_strength': 0.85,
                'mining_power': 85,
                'crew_size': 12,
                'mission_id': 'M001',
                'last_maintenance': '2024-01-01',
                'next_maintenance': '2024-04-01'
            },
            {
                'id': 'S002',
                'name': 'Explorer Beta',
                'type': 'Survey Ship',
                'status': 'docked',
                'location': 'Earth',
                'capacity_kg': 25000,
                'current_cargo_kg': 0,
                'fuel_percentage': 100,
                'hull_integrity': 0.98,
                'shield_strength': 0.95,
                'mining_power': 45,
                'crew_size': 8,
                'mission_id': None,
                'last_maintenance': '2024-01-15',
                'next_maintenance': '2024-04-15'
            },
            {
                'id': 'S003',
                'name': 'Heavy Miner Gamma',
                'type': 'Heavy Miner',
                'status': 'returning',
                'location': 'Juno',
                'capacity_kg': 50000,
                'current_cargo_kg': 46000,
                'fuel_percentage': 15,
                'hull_integrity': 0.88,
                'shield_strength': 0.75,
                'mining_power': 95,
                'crew_size': 15,
                'mission_id': 'M003',
                'last_maintenance': '2023-12-01',
                'next_maintenance': '2024-03-01'
            }
        ]
        
        # Filter by user if specified
        if user_id:
            ships = [s for s in ships if s.get('user_id') == user_id]
        
        return {
            'ships': ships,
            'total_ships': len(ships),
            'status_counts': {
                'active': len([s for s in ships if s['status'] == 'active']),
                'docked': len([s for s in ships if s['status'] == 'docked']),
                'returning': len([s for s in ships if s['status'] == 'returning']),
                'maintenance': len([s for s in ships if s['status'] == 'maintenance'])
            },
            'type_counts': {
                'Heavy Miner': len([s for s in ships if s['type'] == 'Heavy Miner']),
                'Survey Ship': len([s for s in ships if s['type'] == 'Survey Ship']),
                'Transport': len([s for s in ships if s['type'] == 'Transport'])
            }
        }
    
    def _get_economic_data(self, user_id: str = None) -> Dict[str, Any]:
        """Get economic data for visualization using real analytics"""
        # Try to get real data from analytics service
        if self.analytics_service:
            try:
                import asyncio
                analytics_data = asyncio.run(self.analytics_service.get_economic_dashboard_data(user_id))
                
                # Extract data from analytics
                historical = analytics_data.get('historical_performance', {})
                trends = analytics_data.get('profit_loss_trends', {})
                price_history = analytics_data.get('commodity_price_history', {})
                roi_analysis = analytics_data.get('roi_analysis', {})
                
        # Get current commodity prices
                if self.pricing_service:
                    try:
                        prices_per_kg = self.pricing_service.get_commodity_prices_per_kg()
                        # Convert to per-ounce for display if needed
                        prices = prices_per_kg
                    except:
                        prices = {
                            'Gold': 2000.0,
                            'Platinum': 950.0,
                            'Silver': 25.0,
                            'Copper': 4.0,
                            'Palladium': 1000.0
                        }
                else:
                    prices = {
                        'Gold': 2000.0,
                        'Platinum': 950.0,
                        'Silver': 25.0,
                        'Copper': 4.0,
                        'Palladium': 1000.0
                    }
                
                # Calculate monthly trends
                monthly_trend = trends.get('monthly_trend', [])
                this_month_profit = monthly_trend[-1]['profit'] if monthly_trend else 0
                last_month_profit = monthly_trend[-2]['profit'] if len(monthly_trend) >= 2 else 0
                
                return {
                    'revenue': {
                        'total': historical.get('total_revenue', 0),
                        'this_month': trends.get('monthly_trend', [{}])[-1].get('revenue', 0) if trends.get('monthly_trend') else 0,
                        'last_month': trends.get('monthly_trend', [{}])[-2].get('revenue', 0) if len(trends.get('monthly_trend', [])) >= 2 else 0,
                        'projected_annual': historical.get('total_revenue', 0) * 12 if historical.get('total_missions', 0) > 0 else 0
                    },
                    'costs': {
                        'total': historical.get('total_costs', 0),
                        'this_month': trends.get('monthly_trend', [{}])[-1].get('costs', 0) if trends.get('monthly_trend') else 0,
                        'last_month': trends.get('monthly_trend', [{}])[-2].get('costs', 0) if len(trends.get('monthly_trend', [])) >= 2 else 0,
                        'projected_annual': historical.get('total_costs', 0) * 12 if historical.get('total_missions', 0) > 0 else 0
                    },
                    'profit': {
                        'total': historical.get('total_profit', 0),
                        'this_month': this_month_profit,
                        'last_month': last_month_profit,
                        'projected_annual': historical.get('total_profit', 0) * 12 if historical.get('total_missions', 0) > 0 else 0
                    },
                    'commodity_prices': prices,
                    'price_history': price_history,
                    'profit_loss_trends': trends,
                    'roi_analysis': roi_analysis,
                    'historical_performance': historical,
                    'market_trends': price_history.get('price_changes', {})
                }
                
            except Exception as e:
                logger.warning(f"Error getting analytics data, using fallback: {e}")
        
        # Fallback to demo data
        if self.pricing_service:
            try:
                prices = self.pricing_service.get_commodity_prices_per_kg()
            except:
                prices = {
                    'Gold': 2000.0,
                    'Platinum': 950.0,
                    'Silver': 25.0,
                    'Copper': 4.0,
                    'Palladium': 1000.0
                }
        else:
            prices = {
                'Gold': 2000.0,
                'Platinum': 950.0,
                'Silver': 25.0,
                'Copper': 4.0,
                'Palladium': 1000.0
            }
        
        return {
            'revenue': {
                'total': 1250000000,
                'this_month': 150000000,
                'last_month': 120000000,
                'projected_annual': 1800000000
            },
            'costs': {
                'total': 850000000,
                'this_month': 95000000,
                'last_month': 80000000,
                'projected_annual': 1100000000
            },
            'profit': {
                'total': 400000000,
                'this_month': 55000000,
                'last_month': 40000000,
                'projected_annual': 700000000
            },
            'commodity_prices': prices,
            'market_trends': {
                'gold_trend': '+5.2%',
                'platinum_trend': '-2.1%',
                'silver_trend': '+8.7%',
                'copper_trend': '+3.4%',
                'palladium_trend': '+1.9%'
            }
        }
    
    def _get_orbital_data(self) -> Dict[str, Any]:
        """Get orbital mechanics data for visualization"""
        return {
            'current_positions': {
                'earth': {'x': 0, 'y': 0, 'z': 0},
                'ceres': {'x': 1.59478, 'y': 0, 'z': 0},
                'pallas': {'x': 1.23429, 'y': 0, 'z': 0},
                'juno': {'x': 1.03429, 'y': 0, 'z': 0}
            },
            'trajectories': [
                {
                    'mission_id': 'M001',
                    'start': 'Earth',
                    'end': 'Ceres',
                    'progress': 0.65,
                    'estimated_arrival': '2024-07-15'
                },
                {
                    'mission_id': 'M003',
                    'start': 'Juno',
                    'end': 'Earth',
                    'progress': 0.95,
                    'estimated_arrival': '2024-02-15'
                }
            ],
            'orbital_mechanics': {
                'propulsion_speed_kmh': 72537,
                'average_travel_time_days': 295,
                'fuel_efficiency': 0.92,
                'delta_v_capability': 15.5
            }
        }
    
    def _get_risk_data(self) -> Dict[str, Any]:
        """Get risk assessment data for visualization"""
        return {
            'overall_risk_level': 'medium',
            'risk_factors': {
                'radiation_exposure': 0.3,
                'communication_delay': 0.2,
                'fuel_shortage': 0.4,
                'equipment_failure': 0.25,
                'navigation_errors': 0.15
            },
            'mission_risks': [
                {
                    'mission_id': 'M001',
                    'risk_level': 'medium',
                    'risk_score': 0.5,
                    'primary_concerns': ['fuel_shortage', 'equipment_failure']
                },
                {
                    'mission_id': 'M002',
                    'risk_level': 'low',
                    'risk_score': 0.3,
                    'primary_concerns': ['communication_delay']
                },
                {
                    'mission_id': 'M003',
                    'risk_level': 'low',
                    'risk_score': 0.4,
                    'primary_concerns': ['fuel_shortage']
                }
            ],
            'mitigation_strategies': [
                'Enhanced radiation shielding',
                'Redundant communication systems',
                'Increased fuel margins',
                'Preventive maintenance protocols'
            ]
        }
    
    def _get_market_data(self) -> Dict[str, Any]:
        """Get market data for visualization"""
        return {
            'commodity_prices': {
                'Gold': {'price': 2000.0, 'change': '+5.2%', 'trend': 'up'},
                'Platinum': {'price': 950.0, 'change': '-2.1%', 'trend': 'down'},
                'Silver': {'price': 25.0, 'change': '+8.7%', 'trend': 'up'},
                'Copper': {'price': 4.0, 'change': '+3.4%', 'trend': 'up'},
                'Palladium': {'price': 1000.0, 'change': '+1.9%', 'trend': 'up'}
            },
            'market_indicators': {
                'volatility': 'medium',
                'trend': 'bullish',
                'confidence': 0.75
            },
            'price_history': {
                'gold': [1950, 1980, 2000, 2020, 2000],
                'platinum': [980, 960, 950, 940, 950],
                'silver': [22, 23, 24, 25, 25],
                'copper': [3.8, 3.9, 4.0, 4.1, 4.0],
                'palladium': [980, 990, 1000, 1010, 1000]
            }
        }
    
    def _get_alert_data(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get alert data for visualization"""
        alerts = [
            {
                'id': 'A001',
                'type': 'warning',
                'title': 'Low Fuel Warning',
                'message': 'Mining Vessel Alpha fuel below 20%',
                'timestamp': '2024-01-15T10:30:00Z',
                'mission_id': 'M001',
                'priority': 'high'
            },
            {
                'id': 'A002',
                'type': 'info',
                'title': 'Mission Update',
                'message': 'Juno mission 95% complete',
                'timestamp': '2024-01-15T09:15:00Z',
                'mission_id': 'M003',
                'priority': 'medium'
            },
            {
                'id': 'A003',
                'type': 'success',
                'title': 'Mission Completed',
                'message': 'Vesta survey mission successful',
                'timestamp': '2024-01-14T16:45:00Z',
                'mission_id': 'M004',
                'priority': 'low'
            }
        ]
        
        # Filter by user if specified
        if user_id:
            alerts = [a for a in alerts if a.get('user_id') == user_id]
        
        return alerts
    
    def _get_chart_data(self) -> Dict[str, Any]:
        """Get chart data for visualization"""
        return {
            'revenue_trend': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'data': [100, 120, 110, 140, 130, 150],
                'type': 'line'
            },
            'mission_status': {
                'labels': ['Planning', 'Active', 'Returning', 'Completed'],
                'data': [2, 3, 1, 12],
                'type': 'doughnut'
            },
            'fleet_utilization': {
                'labels': ['Active', 'Docked', 'Maintenance'],
                'data': [3, 4, 1],
                'type': 'pie'
            },
            'risk_distribution': {
                'labels': ['Low', 'Medium', 'High'],
                'data': [8, 5, 2],
                'type': 'bar'
            },
            'commodity_prices': {
                'labels': ['Gold', 'Platinum', 'Silver', 'Copper', 'Palladium'],
                'data': [2000, 950, 25, 4, 1000],
                'type': 'bar'
            }
        }
    
    def get_mission_details(self, mission_id: str) -> Dict[str, Any]:
        """Get detailed mission information for visualization"""
        # This would typically fetch from database
        mission_details = {
            'id': mission_id,
            'name': 'Ceres Mining Expedition',
            'asteroid': 'Ceres',
            'status': 'active',
            'progress': 0.65,
            'timeline': [
                {'phase': 'departure', 'start': '2024-01-15', 'end': '2024-01-16', 'status': 'completed'},
                {'phase': 'transit', 'start': '2024-01-16', 'end': '2024-07-10', 'status': 'in_progress'},
                {'phase': 'mining', 'start': '2024-07-10', 'end': '2024-08-10', 'status': 'pending'},
                {'phase': 'return', 'start': '2024-08-10', 'end': '2024-12-15', 'status': 'pending'}
            ],
            'crew': [
                {'name': 'Captain Sarah Chen', 'role': 'Mission Commander', 'status': 'active'},
                {'name': 'Dr. Marcus Rodriguez', 'role': 'Chief Engineer', 'status': 'active'},
                {'name': 'Lt. Alex Kim', 'role': 'Navigation Officer', 'status': 'active'}
            ],
            'resources': {
                'fuel_remaining': 0.78,
                'food_supplies': 0.85,
                'water_supplies': 0.90,
                'spare_parts': 0.70
            },
            'orbital_mechanics': self.orbital_service.calculate_travel_time(1.59478, 'mining_mission'),
            'economics': {
                'estimated_revenue': 250000000,
                'current_costs': 180000000,
                'projected_profit': 70000000
            }
        }
        
        return mission_details
    
    def get_asteroid_analysis(self, asteroid_name: str) -> Dict[str, Any]:
        """Get detailed asteroid analysis for visualization"""
        # This would typically fetch from database
        asteroid_data = {
            'name': asteroid_name,
            'moid_au': 1.59478,
            'size_km': 939.4,
            'composition': {
                'water_ice': 0.25,
                'silicates': 0.45,
                'metals': 0.20,
                'carbon': 0.10
            },
            'mining_analysis': {
                'difficulty': 'medium',
                'estimated_yield': 50000000,  # kg
                'mining_time_days': 30,
                'equipment_required': ['Heavy Mining Drills', 'Ore Processors', 'Cargo Holds']
            },
            'orbital_mechanics': self.orbital_service.calculate_travel_time(1.59478, 'mining_mission'),
            'risk_assessment': self.orbital_service.calculate_mission_risk_factors(1.59478, 'mining_mission'),
            'economic_analysis': {
                'estimated_value': 5000000000,
                'mining_costs': 200000000,
                'transport_costs': 50000000,
                'net_value': 4750000000
            }
        }
        
        return asteroid_data
    
    def _get_mining_data(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get real mining operations data from MongoDB.
        
        Args:
            user_id: Optional user ID to filter missions
            
        Returns:
            Dictionary containing active mining missions with detailed data
        """
        if not self.mongo_db:
            logger.warning("MongoDB not available, returning empty mining data")
            return {
                'active_mining_missions': [],
                'total_active': 0,
                'total_cargo': 0
            }
        
        try:
            missions_collection = self.mongo_db.missions
            asteroids_collection = self.mongo_db.asteroids
            
            # Query for missions in mining phase
            query = {"current_phase": "mining"}
            if user_id:
                query["user_id"] = user_id
            
            mining_missions = list(missions_collection.find(query))
            
            active_mining_missions = []
            total_cargo = 0
            
            for mission in mining_missions:
                try:
                    mission_id = str(mission.get('_id', ''))
                    mission_name = mission.get('name', 'Unnamed Mission')
                    asteroid_name = mission.get('asteroid_name', 'Unknown')
                    asteroid_id = mission.get('asteroid_id')
                    
                    # Get cargo data (dictionary format: {element_name: weight_kg})
                    cargo = mission.get('cargo', {})
                    if isinstance(cargo, list):
                        # Convert list format to dict if needed
                        cargo_dict = {}
                        for item in cargo:
                            if isinstance(item, dict):
                                element = item.get('element') or item.get('name')
                                mass = item.get('mass_kg') or item.get('weight', 0)
                                if element:
                                    cargo_dict[element] = mass
                        cargo = cargo_dict
                    
                    # Calculate total cargo weight
                    current_cargo_kg = sum(cargo.values()) if cargo else 0
                    total_cargo += current_cargo_kg
                    
                    # Get ship capacity (default 50000kg)
                    ship_capacity_kg = mission.get('ship_capacity', 50000)
                    
                    # Calculate progress percentage
                    progress_percentage = (current_cargo_kg / ship_capacity_kg * 100) if ship_capacity_kg > 0 else 0
                    
                    # Get mining days (current_day in mining phase)
                    mining_days = mission.get('current_day', 0)
                    
                    # Get asteroid class
                    asteroid_class = None
                    if asteroid_id:
                        try:
                            from bson import ObjectId
                            if isinstance(asteroid_id, str) and len(asteroid_id) == 24:
                                asteroid_obj = asteroids_collection.find_one({"_id": ObjectId(asteroid_id)})
                            else:
                                asteroid_obj = asteroids_collection.find_one({"name": asteroid_name})
                            
                            if asteroid_obj:
                                asteroid_class = asteroid_obj.get('class', 'C')
                        except Exception as e:
                            logger.warning(f"Error getting asteroid class: {e}")
                    
                    # If asteroid_class not found, default to 'C'
                    if not asteroid_class:
                        asteroid_class = 'C'
                    
                    # Calculate daily yield (approximate)
                    daily_yield = current_cargo_kg / max(mining_days, 1) if mining_days > 0 else 0
                    
                    # Format cargo breakdown
                    cargo_breakdown = {}
                    for element, weight in cargo.items():
                        if weight > 0:
                            cargo_breakdown[element] = round(weight, 2)
                    
                    mission_data = {
                        'mission_id': mission_id,
                        'name': mission_name,
                        'asteroid_name': asteroid_name,
                        'asteroid_class': asteroid_class,
                        'current_cargo_kg': round(current_cargo_kg, 2),
                        'ship_capacity_kg': ship_capacity_kg,
                        'progress_percentage': round(progress_percentage, 2),
                        'mining_days': mining_days,
                        'cargo_breakdown': cargo_breakdown,
                        'daily_yield': round(daily_yield, 2)
                    }
                    
                    active_mining_missions.append(mission_data)
                    
                except Exception as e:
                    logger.error(f"Error processing mining mission {mission.get('_id', 'unknown')}: {e}")
                    continue
            
            return {
                'active_mining_missions': active_mining_missions,
                'total_active': len(active_mining_missions),
                'total_cargo': round(total_cargo, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting mining data from MongoDB: {e}")
            return {
                'active_mining_missions': [],
                'total_active': 0,
                'total_cargo': 0
            }


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    def main():
        # Create visualization service
        viz_service = AstroSurgeVisualizationService()
        
        print("🚀 AstroSurge Visualization Dashboard")
        print("=" * 50)
        
        # Get dashboard data
        dashboard = viz_service.get_dashboard_data()
        
        print(f"\n📊 Dashboard Overview:")
        print(f"  - Total Missions: {dashboard['overview']['total_missions']}")
        print(f"  - Active Missions: {dashboard['overview']['active_missions']}")
        print(f"  - Fleet Size: {dashboard['overview']['fleet_size']}")
        print(f"  - Total Revenue: ${dashboard['overview']['total_revenue']:,}")
        print(f"  - Net Profit: ${dashboard['overview']['net_profit']:,}")
        
        print(f"\n🚀 Active Missions:")
        for mission in dashboard['missions']['missions']:
            if mission['status'] == 'active':
                print(f"  - {mission['name']}: {mission['progress']*100:.0f}% complete")
        
        print(f"\n🛸 Fleet Status:")
        for ship in dashboard['fleet']['ships']:
            print(f"  - {ship['name']}: {ship['status']} ({ship['fuel_percentage']}% fuel)")
        
        print(f"\n💰 Economic Overview:")
        print(f"  - This Month Revenue: ${dashboard['economics']['revenue']['this_month']:,}")
        print(f"  - This Month Costs: ${dashboard['economics']['costs']['this_month']:,}")
        print(f"  - This Month Profit: ${dashboard['economics']['profit']['this_month']:,}")
        
        print(f"\n⚠️  Risk Assessment:")
        print(f"  - Overall Risk Level: {dashboard['risk_assessment']['overall_risk_level'].upper()}")
        print(f"  - Primary Concerns: {', '.join(dashboard['risk_assessment']['risk_factors'].keys())}")
        
        print(f"\n✅ Visualization Dashboard Ready!")
        print(f"✅ Real-time data updates every {viz_service.refresh_interval} seconds")
        print(f"✅ Comprehensive metrics and visualizations available")
    
    # Run the example
    main()
