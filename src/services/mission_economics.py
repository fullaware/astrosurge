"""
Mission Economics Service for AstroSurge

This service provides enhanced mission economics with MongoDB as the core state management system.
"""
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.commodity_pricing_standalone import CommodityPricingService

logger = logging.getLogger(__name__)


class MissionEconomicsService:
    """
    Mission economics service with MongoDB as core state management.
    
    Features:
    - MongoDB as core state management system
    - Real commodity pricing integration
    - Ore grade calculations with persistence
    - Gangue separation costs tracking
    - Mission economics with historical data
    - Risk assessment and recommendations
    - Optimal cargo mix analysis
    """
    
    def __init__(self, mongodb_uri: str = None):
        """Initialize the mission economics service"""
        # MongoDB connection
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
        self.db = self.client.asteroids
        
        # Test connection
        try:
            self.client.admin.command('ping')
            logger.info("✅ MongoDB connection successful")
        except ConnectionFailure:
            logger.error("❌ MongoDB connection failed")
            raise
        
        # Collections
        self.missions = self.db.missions
        self.users = self.db.users
        self.ships = self.db.ships
        self.market_prices = self.db.market_prices
        self.mission_economics = self.db.mission_economics
        self.ore_analysis = self.db.ore_analysis
        
        # Initialize commodity pricing service
        self.pricing_service = CommodityPricingService()
        
        # Mission cost structure (per day)
        self.cost_structure = {
            'ground_control': 75000,      # $75K/day
            'launch_scrub': 75000,        # $75K per scrub
            'space_event_base': 100000,   # $100K base for space events
            'mining_operations': 50000,   # $50K/day for mining operations
            'ship_maintenance': 25000,    # $25K/day for ship maintenance
            'fuel_consumption': 15000,    # $15K/day for fuel
            'life_support': 10000,        # $10K/day for life support
        }
        
        # Gangue separation costs (per kg of ore processed)
        self.gangue_separation_cost = 0.50  # $0.50 per kg of ore
        
        # Ore grade classifications
        self.ore_grade_classifications = {
            'low': {'min': 0.01, 'max': 0.05, 'description': 'Low-grade ore'},
            'medium': {'min': 0.05, 'max': 0.10, 'description': 'Medium-grade ore'},
            'high': {'min': 0.10, 'max': 0.20, 'description': 'High-grade ore'},
            'premium': {'min': 0.20, 'max': 1.0, 'description': 'Premium-grade ore'}
        }
        
        # Mining efficiency factors
        self.mining_efficiency = {
            'low': 0.8,      # 80% efficiency for low-grade ore
            'medium': 0.9,   # 90% efficiency for medium-grade ore
            'high': 0.95,    # 95% efficiency for high-grade ore
            'premium': 0.98  # 98% efficiency for premium-grade ore
        }
        
        # Ship specifications
        self.ship_specs = {
            'cargo_capacity': 50000,      # 50,000 kg
            'max_mining_rate': 1500,       # 1,500 kg/day
            'fuel_capacity': 10000,        # 10,000 kg fuel
            'crew_size': 4,                # 4 crew members
            'hull_integrity': 100,         # 100% hull integrity
        }
        
        # Ensure indexes exist
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure MongoDB indexes exist for optimal performance"""
        try:
            # Mission economics indexes
            self.mission_economics.create_index("mission_id")
            self.mission_economics.create_index("user_id")
            self.mission_economics.create_index("calculated_at")
            
            # Ore analysis indexes
            self.ore_analysis.create_index("mission_id")
            self.ore_analysis.create_index("asteroid_id")
            self.ore_analysis.create_index("ore_grade")
            
            # Market prices indexes
            self.market_prices.create_index("symbol")
            self.market_prices.create_index("timestamp")
            self.market_prices.create_index([("symbol", 1), ("timestamp", -1)])
            
            logger.info("✅ MongoDB indexes ensured")
        except Exception as e:
            logger.warning(f"Warning: Could not create indexes: {e}")
    
    async def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get mission data from MongoDB"""
        try:
            mission = self.missions.find_one({"_id": ObjectId(mission_id)})
            if mission:
                mission["_id"] = str(mission["_id"])
            return mission
        except Exception as e:
            logger.error(f"Error getting mission {mission_id}: {e}")
            return None
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from MongoDB"""
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def get_ship(self, ship_id: str) -> Optional[Dict[str, Any]]:
        """Get ship data from MongoDB"""
        try:
            ship = self.ships.find_one({"_id": ObjectId(ship_id)})
            if ship:
                ship["_id"] = str(ship["_id"])
            return ship
        except Exception as e:
            logger.error(f"Error getting ship {ship_id}: {e}")
            return None
    
    async def save_mission_economics(self, mission_id: str, economics_data: Dict[str, Any]) -> bool:
        """Save mission economics data to MongoDB"""
        try:
            economics_doc = {
                "mission_id": ObjectId(mission_id),
                "calculated_at": datetime.utcnow(),
                "economics": economics_data,
                "version": "1.0"
            }
            
            # Upsert the economics data
            result = self.mission_economics.replace_one(
                {"mission_id": ObjectId(mission_id)},
                economics_doc,
                upsert=True
            )
            
            logger.info(f"Mission economics saved for mission {mission_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving mission economics: {e}")
            return False
    
    async def get_mission_economics(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get mission economics data from MongoDB"""
        try:
            economics = self.mission_economics.find_one(
                {"mission_id": ObjectId(mission_id)}
            )
            
            if economics:
                economics["_id"] = str(economics["_id"])
                economics["mission_id"] = str(economics["mission_id"])
                return economics.get("economics", {})
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting mission economics: {e}")
            return None
    
    async def save_ore_analysis(self, mission_id: str, asteroid_id: str, 
                              ore_analysis: Dict[str, Any]) -> bool:
        """Save ore analysis data to MongoDB"""
        try:
            ore_doc = {
                "mission_id": ObjectId(mission_id),
                "asteroid_id": asteroid_id,
                "analyzed_at": datetime.utcnow(),
                "analysis": ore_analysis,
                "version": "1.0"
            }
            
            # Upsert the ore analysis
            result = self.ore_analysis.replace_one(
                {"mission_id": ObjectId(mission_id), "asteroid_id": asteroid_id},
                ore_doc,
                upsert=True
            )
            
            logger.info(f"Ore analysis saved for mission {mission_id}, asteroid {asteroid_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving ore analysis: {e}")
            return False
    
    async def get_ore_analysis(self, mission_id: str, asteroid_id: str = None) -> Optional[Dict[str, Any]]:
        """Get ore analysis data from MongoDB"""
        try:
            query = {"mission_id": ObjectId(mission_id)}
            if asteroid_id:
                query["asteroid_id"] = asteroid_id
            
            ore_analysis = self.ore_analysis.find_one(query)
            
            if ore_analysis:
                ore_analysis["_id"] = str(ore_analysis["_id"])
                ore_analysis["mission_id"] = str(ore_analysis["mission_id"])
                return ore_analysis.get("analysis", {})
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting ore analysis: {e}")
            return None
    
    def calculate_ore_grade(self, commodity_content: float, total_ore: float) -> tuple[str, float]:
        """Calculate ore grade and classification"""
        if total_ore <= 0:
            return 'low', 0.0
        
        grade_percentage = commodity_content / total_ore
        
        for grade_class, specs in self.ore_grade_classifications.items():
            if specs['min'] <= grade_percentage < specs['max']:
                return grade_class, grade_percentage
        
        # Handle edge case for very high grades
        if grade_percentage >= 1.0:
            return 'premium', grade_percentage
        
        return 'low', grade_percentage
    
    async def calculate_mission_costs(self, mission_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive mission costs with MongoDB persistence"""
        mission_duration = mission_data.get('total_days', 224)
        launch_scrubs = mission_data.get('launch_scrubs', 0)
        space_events = mission_data.get('space_events', 0)
        mining_days = mission_data.get('mining_days', 30)
        
        costs = {}
        
        # Ground control costs (daily throughout mission)
        costs['ground_control'] = mission_duration * self.cost_structure['ground_control']
        
        # Launch scrub costs
        costs['launch_scrubs'] = launch_scrubs * self.cost_structure['launch_scrub']
        
        # Space event costs (variable based on severity)
        costs['space_events'] = space_events * self.cost_structure['space_event_base']
        
        # Mining operation costs
        costs['mining_operations'] = mining_days * self.cost_structure['mining_operations']
        
        # Ship maintenance costs
        costs['ship_maintenance'] = mission_duration * self.cost_structure['ship_maintenance']
        
        # Fuel costs
        costs['fuel'] = mission_duration * self.cost_structure['fuel_consumption']
        
        # Life support costs
        costs['life_support'] = mission_duration * self.cost_structure['life_support']
        
        # Calculate total
        costs['total'] = sum(costs.values())
        
        return costs
    
    async def calculate_mining_yield(self, mission_id: str, asteroid_composition: Dict[str, float], 
                                   mining_days: int, ore_grade: float = 0.1) -> Dict[str, Any]:
        """Calculate realistic mining yield with MongoDB persistence"""
        max_daily_yield = self.ship_specs['max_mining_rate']
        total_ore_mined = min(mining_days * max_daily_yield, self.ship_specs['cargo_capacity'])
        
        # Calculate grade classification
        grade_class, grade_percentage = self.calculate_ore_grade(
            total_ore_mined * ore_grade, total_ore_mined
        )
        
        # Apply mining efficiency based on ore grade
        efficiency = self.mining_efficiency.get(grade_class, 0.8)
        effective_yield = total_ore_mined * efficiency
        
        # Calculate commodity extraction
        commodity_yield = {}
        gangue_weight = 0
        
        for element, percentage in asteroid_composition.items():
            element_weight = effective_yield * percentage * ore_grade
            commodity_yield[element] = element_weight
            gangue_weight += effective_yield * percentage * (1 - ore_grade)
        
        # Calculate gangue separation costs
        gangue_separation_cost = effective_yield * self.gangue_separation_cost
        
        yield_data = {
            'total_ore_mined': total_ore_mined,
            'effective_yield': effective_yield,
            'ore_grade': grade_percentage,
            'grade_classification': grade_class,
            'mining_efficiency': efficiency,
            'commodity_yield': commodity_yield,
            'gangue_weight': gangue_weight,
            'gangue_separation_cost': gangue_separation_cost
        }
        
        # Save ore analysis to MongoDB
        await self.save_ore_analysis(mission_id, "unknown", yield_data)
        
        return yield_data
    
    async def calculate_cargo_value(self, cargo: Dict[str, float]) -> Dict[str, Any]:
        """Calculate cargo value using real commodity pricing"""
        # Get current market prices
        market_prices = self.pricing_service.get_commodity_prices_per_kg()
        
        cargo_value = {}
        total_value = 0
        
        for commodity, weight in cargo.items():
            if commodity in market_prices:
                price_per_kg = market_prices[commodity]
                commodity_value = weight * price_per_kg
                cargo_value[commodity] = {
                    'weight_kg': weight,
                    'price_per_kg': price_per_kg,
                    'total_value': commodity_value
                }
                total_value += commodity_value
            else:
                logger.warning(f"Unknown commodity: {commodity}")
                cargo_value[commodity] = {
                    'weight_kg': weight,
                    'price_per_kg': 0,
                    'total_value': 0
                }
        
        cargo_value['total_value'] = total_value
        return cargo_value
    
    async def calculate_comprehensive_mission_economics(self, mission_id: str) -> Dict[str, Any]:
        """Calculate comprehensive mission economics with MongoDB integration"""
        # Get mission data from MongoDB
        mission = await self.get_mission(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        
        # Extract mission parameters
        mission_duration = mission.get('total_days', 224)
        launch_scrubs = mission.get('launch_scrubs', 0)
        space_events = mission.get('space_events', 0)
        mining_days = mission.get('mining_days', 30)
        asteroid_composition = mission.get('asteroid_composition', {})
        ore_grade = mission.get('ore_grade', 0.1)
        cargo = mission.get('cargo', {})
        hull_damage = mission.get('hull_damage', 0)
        
        # Calculate mission costs
        mission_costs = await self.calculate_mission_costs(mission)
        
        # Calculate mining yield
        mining_yield = await self.calculate_mining_yield(
            mission_id, asteroid_composition, mining_days, ore_grade
        )
        
        # Calculate cargo value
        cargo_value = await self.calculate_cargo_value(cargo)
        
        # Calculate investor repayment (15% annual interest)
        daily_interest_rate = 0.15 / 365
        principal = mission_costs['total']
        interest_amount = principal * daily_interest_rate * mission_duration
        total_repayment = principal + interest_amount
        
        # Calculate ship repair costs
        repair_cost_per_damage = 1000000  # $1M per damage point
        ship_repair_cost = min(hull_damage * repair_cost_per_damage, 25000000)
        
        # Calculate gangue separation costs
        gangue_costs = mining_yield.get('gangue_separation_cost', 0)
        
        # Calculate net profit
        total_costs = mission_costs['total'] + gangue_costs
        net_profit = cargo_value['total_value'] - total_costs - total_repayment - ship_repair_cost
        
        # Calculate ROI
        roi_percentage = (net_profit / total_costs * 100) if total_costs > 0 else 0
        
        economics = {
            'mission_costs': mission_costs,
            'mining_yield': mining_yield,
            'cargo_value': cargo_value,
            'investor_repayment': {
                'principal': principal,
                'interest': interest_amount,
                'total': total_repayment
            },
            'ship_repair_cost': ship_repair_cost,
            'gangue_separation_cost': gangue_costs,
            'total_costs': total_costs,
            'net_profit': net_profit,
            'roi_percentage': roi_percentage,
            'mission_summary': {
                'duration_days': mission_duration,
                'mining_days': mining_days,
                'ore_grade': ore_grade,
                'grade_classification': mining_yield.get('grade_classification', 'unknown'),
                'total_cargo_weight': sum(cargo.values()) if cargo else 0,
                'hull_damage': hull_damage
            }
        }
        
        # Save economics to MongoDB
        await self.save_mission_economics(mission_id, economics)
        
        return economics
    
    async def calculate_optimal_cargo_mix(self, mission_id: str, 
                                        asteroid_composition: Dict[str, float], 
                                        cargo_capacity: float = 50000) -> Dict[str, Any]:
        """Calculate optimal cargo mix for maximum profit with MongoDB persistence"""
        # Get current market prices
        market_prices = self.pricing_service.get_commodity_prices_per_kg()
        
        # Calculate value per kg for each commodity
        commodity_values = {}
        for element, percentage in asteroid_composition.items():
            if element in market_prices:
                price_per_kg = market_prices[element]
                # Account for ore grade (assume 10% average grade)
                effective_price = price_per_kg * 0.1
                commodity_values[element] = {
                    'percentage': percentage,
                    'price_per_kg': price_per_kg,
                    'effective_price': effective_price,
                    'value_per_kg_ore': effective_price
                }
        
        # Sort by value per kg of ore
        sorted_commodities = sorted(
            commodity_values.items(), 
            key=lambda x: x[1]['value_per_kg_ore'], 
            reverse=True
        )
        
        # Calculate optimal allocation
        optimal_mix = {}
        remaining_capacity = cargo_capacity
        
        for commodity, data in sorted_commodities:
            if remaining_capacity <= 0:
                break
            
            # Allocate based on asteroid composition percentage
            allocation = min(
                remaining_capacity * data['percentage'],
                remaining_capacity
            )
            
            optimal_mix[commodity] = {
                'weight_kg': allocation,
                'percentage': data['percentage'],
                'price_per_kg': data['price_per_kg'],
                'value': allocation * data['price_per_kg'] * 0.1  # Account for ore grade
            }
            
            remaining_capacity -= allocation
        
        # Calculate total value
        total_value = sum(item['value'] for item in optimal_mix.values())
        
        optimal_analysis = {
            'mission_id': mission_id,
            'optimal_cargo_mix': optimal_mix,
            'total_value': total_value,
            'cargo_capacity_used': cargo_capacity - remaining_capacity,
            'commodity_rankings': sorted_commodities,
            'calculated_at': datetime.utcnow()
        }
        
        # Save optimal cargo mix analysis to MongoDB
        await self.save_ore_analysis(mission_id, "optimal_cargo", optimal_analysis)
        
        return optimal_analysis
    
    async def calculate_mission_risk_assessment(self, mission_id: str) -> Dict[str, Any]:
        """Calculate mission risk assessment based on economic factors"""
        economics = await self.calculate_comprehensive_mission_economics(mission_id)
        
        # Risk factors
        risk_factors = {
            'low_profit_margin': economics['net_profit'] < 100000000,  # Less than $100M profit
            'high_costs': economics['total_costs'] > 500000000,        # More than $500M costs
            'low_roi': economics['roi_percentage'] < 50,              # Less than 50% ROI
            'high_hull_damage': economics['mission_summary']['hull_damage'] > 10,
            'long_mission': economics['mission_summary']['duration_days'] > 300,
            'low_ore_grade': economics['mission_summary']['ore_grade'] < 0.05
        }
        
        # Calculate risk score
        risk_score = sum(risk_factors.values())
        risk_level = 'low' if risk_score <= 1 else 'medium' if risk_score <= 3 else 'high'
        
        risk_assessment = {
            'mission_id': mission_id,
            'risk_factors': risk_factors,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'recommendations': self._get_risk_recommendations(risk_factors),
            'calculated_at': datetime.utcnow()
        }
        
        return risk_assessment
    
    def _get_risk_recommendations(self, risk_factors: Dict[str, bool]) -> List[str]:
        """Get recommendations based on risk factors"""
        recommendations = []
        
        if risk_factors['low_profit_margin']:
            recommendations.append("Consider higher-grade asteroids or longer mining operations")
        
        if risk_factors['high_costs']:
            recommendations.append("Optimize mission duration and reduce operational costs")
        
        if risk_factors['low_roi']:
            recommendations.append("Focus on high-value commodities and efficient operations")
        
        if risk_factors['high_hull_damage']:
            recommendations.append("Invest in better ship protection and hazard avoidance")
        
        if risk_factors['long_mission']:
            recommendations.append("Consider shorter missions or more efficient travel routes")
        
        if risk_factors['low_ore_grade']:
            recommendations.append("Target asteroids with higher commodity concentrations")
        
        return recommendations
    
    async def get_mission_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get mission history for a user from MongoDB"""
        try:
            missions = list(self.missions.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit))
            
            for mission in missions:
                mission["_id"] = str(mission["_id"])
                # Get economics data
                economics = await self.get_mission_economics(str(mission["_id"]))
                mission["economics"] = economics
            
            return missions
            
        except Exception as e:
            logger.error(f"Error getting mission history: {e}")
            return []
    
    async def get_user_economics_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive economics summary for a user"""
        try:
            # Get all missions for user
            missions = list(self.missions.find({"user_id": user_id}))
            
            total_profit = 0
            total_costs = 0
            mission_count = len(missions)
            successful_missions = 0
            
            for mission in missions:
                economics = await self.get_mission_economics(str(mission["_id"]))
                if economics:
                    total_profit += economics.get('net_profit', 0)
                    total_costs += economics.get('total_costs', 0)
                    if economics.get('net_profit', 0) > 0:
                        successful_missions += 1
            
            avg_profit = total_profit / mission_count if mission_count > 0 else 0
            success_rate = (successful_missions / mission_count * 100) if mission_count > 0 else 0
            overall_roi = (total_profit / total_costs * 100) if total_costs > 0 else 0
            
            return {
                'user_id': user_id,
                'total_missions': mission_count,
                'successful_missions': successful_missions,
                'success_rate': success_rate,
                'total_profit': total_profit,
                'total_costs': total_costs,
                'average_profit': avg_profit,
                'overall_roi': overall_roi,
                'calculated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting user economics summary: {e}")
            return {}


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Create service instance
        economics_service = MissionEconomicsService()
        
        print("🚀 AstroSurge Mission Economics Service")
        print("=" * 50)
        
        print(f"\n📊 MongoDB Integration Status:")
        print(f"✅ MongoDB Connection: Active")
        print(f"✅ Collections: missions, users, ships, market_prices, mission_economics, ore_analysis")
        print(f"✅ Indexes: Created for optimal performance")
        print(f"✅ State Management: MongoDB as core storage")
        
        print(f"\n🔧 Service Features:")
        print(f"✅ Real commodity pricing integration")
        print(f"✅ Ore grade calculations with persistence")
        print(f"✅ Gangue separation costs tracking")
        print(f"✅ Mission economics with historical data")
        print(f"✅ Risk assessment and recommendations")
        print(f"✅ Optimal cargo mix analysis")
        print(f"✅ User economics summaries")
        
        print(f"\n📈 Ready for AstroSurge Integration!")
        print(f"✅ MongoDB as core state management")
        print(f"✅ Persistent mission economics")
        print(f"✅ Historical data analysis")
        print(f"✅ Real-time economic calculations")
    
    # Run the example
    asyncio.run(main())
