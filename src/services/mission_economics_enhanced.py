"""
Enhanced Mission Economics Service for AstroSurge

This service enhances mission cost calculations with real commodity pricing,
ore grade calculations, gangue separation costs, and realistic profit/loss calculations.
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.commodity_pricing_standalone import CommodityPricingService

logger = logging.getLogger(__name__)


class MissionEconomicsService:
    """
    Enhanced mission economics service with realistic calculations.
    
    Features:
    - Real commodity pricing integration
    - Ore grade calculations (10% grade = high grade)
    - Gangue separation costs
    - Realistic profit/loss calculations
    - Mission cost breakdown
    - ROI analysis
    """
    
    def __init__(self):
        """Initialize the mission economics service"""
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
    
    def calculate_mission_costs(self, mission_duration_days: int, 
                              launch_scrubs: int = 0, 
                              space_events: int = 0,
                              mining_days: int = 0) -> Dict[str, float]:
        """
        Calculate comprehensive mission costs.
        
        Args:
            mission_duration_days: Total mission duration in days
            launch_scrubs: Number of launch scrub events
            space_events: Number of space events
            mining_days: Number of days spent mining
            
        Returns:
            Dictionary with detailed cost breakdown
        """
        costs = {}
        
        # Ground control costs (daily throughout mission)
        costs['ground_control'] = mission_duration_days * self.cost_structure['ground_control']
        
        # Launch scrub costs
        costs['launch_scrubs'] = launch_scrubs * self.cost_structure['launch_scrub']
        
        # Space event costs (variable based on severity)
        costs['space_events'] = space_events * self.cost_structure['space_event_base']
        
        # Mining operation costs
        costs['mining_operations'] = mining_days * self.cost_structure['mining_operations']
        
        # Ship maintenance costs
        costs['ship_maintenance'] = mission_duration_days * self.cost_structure['ship_maintenance']
        
        # Fuel costs
        costs['fuel'] = mission_duration_days * self.cost_structure['fuel_consumption']
        
        # Life support costs
        costs['life_support'] = mission_duration_days * self.cost_structure['life_support']
        
        # Calculate total
        costs['total'] = sum(costs.values())
        
        return costs
    
    def calculate_ore_grade(self, commodity_content: float, total_ore: float) -> Tuple[str, float]:
        """
        Calculate ore grade and classification.
        
        Args:
            commodity_content: Weight of commodity in kg
            total_ore: Total ore weight in kg
            
        Returns:
            Tuple of (grade_classification, grade_percentage)
        """
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
    
    def calculate_mining_yield(self, asteroid_composition: Dict[str, float], 
                             mining_days: int, 
                             ore_grade: float = 0.1) -> Dict[str, Dict[str, float]]:
        """
        Calculate realistic mining yield based on asteroid composition and ore grade.
        
        Args:
            asteroid_composition: Dictionary of elements and their percentages
            mining_days: Number of days spent mining
            ore_grade: Ore grade (0.1 = 10% commodity content)
            
        Returns:
            Dictionary with mining yield calculations
        """
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
        
        return {
            'total_ore_mined': total_ore_mined,
            'effective_yield': effective_yield,
            'ore_grade': grade_percentage,
            'grade_classification': grade_class,
            'mining_efficiency': efficiency,
            'commodity_yield': commodity_yield,
            'gangue_weight': gangue_weight,
            'gangue_separation_cost': gangue_separation_cost
        }
    
    def calculate_cargo_value(self, cargo: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate cargo value using real commodity pricing.
        
        Args:
            cargo: Dictionary of commodities and their weights in kg
            
        Returns:
            Dictionary with cargo value calculations
        """
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
    
    def calculate_mission_economics(self, mission_data: Dict) -> Dict[str, any]:
        """
        Calculate comprehensive mission economics.
        
        Args:
            mission_data: Dictionary containing mission parameters
            
        Returns:
            Dictionary with complete economic analysis
        """
        # Extract mission parameters
        mission_duration = mission_data.get('total_days', 224)
        launch_scrubs = mission_data.get('launch_scrubs', 0)
        space_events = mission_data.get('space_events', 0)
        mining_days = mission_data.get('mining_days', 30)
        asteroid_composition = mission_data.get('asteroid_composition', {})
        ore_grade = mission_data.get('ore_grade', 0.1)
        cargo = mission_data.get('cargo', {})
        
        # Calculate mission costs
        mission_costs = self.calculate_mission_costs(
            mission_duration, launch_scrubs, space_events, mining_days
        )
        
        # Calculate mining yield
        mining_yield = self.calculate_mining_yield(
            asteroid_composition, mining_days, ore_grade
        )
        
        # Calculate cargo value
        cargo_value = self.calculate_cargo_value(cargo)
        
        # Calculate investor repayment (15% annual interest)
        daily_interest_rate = 0.15 / 365
        principal = mission_costs['total']
        interest_amount = principal * daily_interest_rate * mission_duration
        total_repayment = principal + interest_amount
        
        # Calculate ship repair costs
        hull_damage = mission_data.get('hull_damage', 0)
        repair_cost_per_damage = 1000000  # $1M per damage point
        ship_repair_cost = min(hull_damage * repair_cost_per_damage, 25000000)
        
        # Calculate gangue separation costs
        gangue_costs = mining_yield.get('gangue_separation_cost', 0)
        
        # Calculate net profit
        total_costs = mission_costs['total'] + gangue_costs
        net_profit = cargo_value['total_value'] - total_costs - total_repayment - ship_repair_cost
        
        # Calculate ROI
        roi_percentage = (net_profit / total_costs * 100) if total_costs > 0 else 0
        
        return {
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
    
    def calculate_optimal_cargo_mix(self, asteroid_composition: Dict[str, float], 
                                  cargo_capacity: float = 50000) -> Dict[str, any]:
        """
        Calculate optimal cargo mix for maximum profit.
        
        Args:
            asteroid_composition: Dictionary of elements and their percentages
            cargo_capacity: Maximum cargo capacity in kg
            
        Returns:
            Dictionary with optimal cargo mix analysis
        """
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
        
        return {
            'optimal_cargo_mix': optimal_mix,
            'total_value': total_value,
            'cargo_capacity_used': cargo_capacity - remaining_capacity,
            'commodity_rankings': sorted_commodities
        }
    
    def calculate_mission_risk_assessment(self, mission_data: Dict) -> Dict[str, any]:
        """
        Calculate mission risk assessment based on economic factors.
        
        Args:
            mission_data: Dictionary containing mission parameters
            
        Returns:
            Dictionary with risk assessment
        """
        economics = self.calculate_mission_economics(mission_data)
        
        # Risk factors
        risk_factors = {
            'low_profit_margin': economics['net_profit'] < 100000000,  # Less than $100M profit
            'high_costs': economics['total_costs'] > 500000000,        # More than $500M costs
            'low_roi': economics['roi_percentage'] < 50,              # Less than 50% ROI
            'high_hull_damage': mission_data.get('hull_damage', 0) > 10,
            'long_mission': mission_data.get('total_days', 0) > 300,
            'low_ore_grade': mission_data.get('ore_grade', 0.1) < 0.05
        }
        
        # Calculate risk score
        risk_score = sum(risk_factors.values())
        risk_level = 'low' if risk_score <= 1 else 'medium' if risk_score <= 3 else 'high'
        
        return {
            'risk_factors': risk_factors,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'recommendations': self._get_risk_recommendations(risk_factors)
        }
    
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


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create service instance
    economics_service = MissionEconomicsService()
    
    print("🚀 AstroSurge Enhanced Mission Economics Service")
    print("=" * 60)
    
    # Example mission data
    mission_data = {
        'total_days': 224,
        'launch_scrubs': 2,
        'space_events': 3,
        'mining_days': 30,
        'asteroid_composition': {
            'Platinum': 0.4,    # 40% Platinum
            'Gold': 0.3,        # 30% Gold
            'Silver': 0.2,      # 20% Silver
            'Copper': 0.1       # 10% Copper
        },
        'ore_grade': 0.1,       # 10% grade
        'cargo': {
            'Platinum': 20000,  # 20,000 kg Platinum
            'Gold': 15000,      # 15,000 kg Gold
            'Silver': 10000,    # 10,000 kg Silver
            'Copper': 5000      # 5,000 kg Copper
        },
        'hull_damage': 5
    }
    
    # Calculate mission economics
    print("\n📊 Mission Economics Analysis:")
    print("-" * 60)
    
    economics = economics_service.calculate_mission_economics(mission_data)
    
    print(f"Mission Duration: {economics['mission_summary']['duration_days']} days")
    print(f"Mining Days: {economics['mission_summary']['mining_days']} days")
    print(f"Ore Grade: {economics['mission_summary']['ore_grade']:.1%}")
    print(f"Grade Classification: {economics['mission_summary']['grade_classification']}")
    print(f"Hull Damage: {economics['mission_summary']['hull_damage']} points")
    
    print(f"\n💰 Cost Breakdown:")
    for cost_type, amount in economics['mission_costs'].items():
        if cost_type != 'total':
            print(f"  {cost_type.replace('_', ' ').title()}: ${amount:,.0f}")
    print(f"  Total Mission Costs: ${economics['mission_costs']['total']:,.0f}")
    print(f"  Gangue Separation: ${economics['gangue_separation_cost']:,.0f}")
    print(f"  Ship Repair: ${economics['ship_repair_cost']:,.0f}")
    
    print(f"\n💎 Cargo Value:")
    for commodity, data in economics['cargo_value'].items():
        if commodity != 'total_value':
            print(f"  {commodity}: {data['weight_kg']:,} kg × ${data['price_per_kg']:,.0f}/kg = ${data['total_value']:,.0f}")
    print(f"  Total Cargo Value: ${economics['cargo_value']['total_value']:,.0f}")
    
    print(f"\n🏦 Investor Repayment:")
    print(f"  Principal: ${economics['investor_repayment']['principal']:,.0f}")
    print(f"  Interest: ${economics['investor_repayment']['interest']:,.0f}")
    print(f"  Total Repayment: ${economics['investor_repayment']['total']:,.0f}")
    
    print(f"\n📈 Mission Results:")
    print(f"  Net Profit: ${economics['net_profit']:,.0f}")
    print(f"  ROI: {economics['roi_percentage']:.1f}%")
    
    # Risk assessment
    print(f"\n⚠️  Risk Assessment:")
    risk_assessment = economics_service.calculate_mission_risk_assessment(mission_data)
    print(f"  Risk Level: {risk_assessment['risk_level'].upper()}")
    print(f"  Risk Score: {risk_assessment['risk_score']}/6")
    
    if risk_assessment['recommendations']:
        print(f"  Recommendations:")
        for rec in risk_assessment['recommendations']:
            print(f"    • {rec}")
    
    # Optimal cargo mix
    print(f"\n🎯 Optimal Cargo Mix Analysis:")
    optimal_mix = economics_service.calculate_optimal_cargo_mix(
        mission_data['asteroid_composition']
    )
    
    print(f"  Total Value: ${optimal_mix['total_value']:,.0f}")
    print(f"  Capacity Used: {optimal_mix['cargo_capacity_used']:,} kg")
    
    print(f"\n✅ Enhanced Mission Economics Service Ready!")
    print(f"✅ Real commodity pricing integrated")
    print(f"✅ Ore grade calculations implemented")
    print(f"✅ Gangue separation costs included")
    print(f"✅ Comprehensive profit/loss calculations")
    print(f"✅ Risk assessment and recommendations")
    print(f"✅ Optimal cargo mix analysis")
