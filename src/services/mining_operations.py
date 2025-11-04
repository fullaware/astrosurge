"""
Mining Operations Service for AstroSurge

Implements class-based mining probabilities and realistic mining yields
based on asteroid classification (C, S, M types).
"""
import logging
import random
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MiningOperationsService:
    """
    Service for realistic mining operations based on asteroid classification.
    
    Features:
    - Class-based mining probabilities (C, S, M types)
    - Element probability based on asteroid class
    - Ore grade variations (low, medium, high, premium)
    - Mining efficiency calculations
    - Realistic yield calculations
    """
    
    def __init__(self, mongodb_uri: str = None):
        """Initialize the mining operations service"""
        # MongoDB connection
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
        self.db = self.client.asteroids
        
        # Test connection
        try:
            self.client.admin.command('ping')
            logger.info("✅ MongoDB connection successful for Mining Operations")
        except ConnectionFailure:
            logger.error("❌ MongoDB connection failed for Mining Operations")
            raise
        
        # Collections
        self.elements_collection = self.db.elements
        
        # Mining configuration
        self.max_daily_mining_rate = 1500  # kg per day
        self.max_cargo_capacity = 50000  # kg
        
        # Ore grade probability distribution (based on asteroid class)
        self.ore_grade_distributions = {
            'C': {
                'low': 0.40,      # 40% chance of low-grade
                'medium': 0.35,   # 35% chance of medium-grade
                'high': 0.20,     # 20% chance of high-grade
                'premium': 0.05   # 5% chance of premium-grade
            },
            'S': {
                'low': 0.30,
                'medium': 0.40,
                'high': 0.25,
                'premium': 0.05
            },
            'M': {
                'low': 0.25,
                'medium': 0.35,
                'high': 0.30,
                'premium': 0.10   # Metallic asteroids have higher premium chance
            }
        }
        
        # Ore grade values (percentage of commodity in ore)
        self.ore_grade_values = {
            'low': (0.01, 0.05),      # 1-5% commodity
            'medium': (0.05, 0.10),   # 5-10% commodity
            'high': (0.10, 0.20),     # 10-20% commodity
            'premium': (0.20, 0.35)   # 20-35% commodity
        }
        
        # Mining efficiency by ore grade
        self.mining_efficiency = {
            'low': 0.75,      # 75% efficiency for low-grade
            'medium': 0.85,   # 85% efficiency for medium-grade
            'high': 0.92,     # 92% efficiency for high-grade
            'premium': 0.98   # 98% efficiency for premium-grade
        }
        
        # Valuable elements to prioritize
        self.valuable_elements = ['Gold', 'Platinum', 'Palladium', 'Silver', 'Copper', 'Lithium', 'Cobalt']
    
    def get_asteroid_class(self, asteroid: Dict[str, Any]) -> str:
        """
        Get asteroid classification (C, S, or M).
        
        Args:
            asteroid: Asteroid document from database
            
        Returns:
            Asteroid class ('C', 'S', or 'M')
        """
        asteroid_class = asteroid.get('class', 'C')
        
        # Validate class
        if asteroid_class not in ['C', 'S', 'M']:
            logger.warning(f"Unknown asteroid class '{asteroid_class}', defaulting to 'C'")
            asteroid_class = 'C'
        
        return asteroid_class
    
    async def get_element_class_probabilities(self, element_name: str) -> Dict[str, float]:
        """
        Get the probability distribution of an element across asteroid classes.
        
        Args:
            element_name: Name of the element
            
        Returns:
            Dictionary with class probabilities (C, S, M percentages)
        """
        try:
            element = self.elements_collection.find_one({"name": element_name})
            
            if not element:
                logger.warning(f"Element '{element_name}' not found in database")
                # Default distribution (equal probability)
                return {'C': 0.33, 'S': 0.33, 'M': 0.34}
            
            # Extract class percentages from element document
            classes = element.get('classes', [])
            if not classes:
                # Default distribution if no class data
                return {'C': 0.33, 'S': 0.33, 'M': 0.34}
            
            # Convert to dictionary
            class_probs = {}
            total = 0
            for class_data in classes:
                class_name = class_data.get('class')
                percentage = class_data.get('percentage', 0)
                if class_name in ['C', 'S', 'M']:
                    class_probs[class_name] = percentage / 100.0  # Convert to decimal
                    total += percentage
            
            # Normalize if total doesn't equal 100
            if total > 0 and abs(total - 100) > 0.01:
                for class_name in class_probs:
                    class_probs[class_name] = class_probs[class_name] / (total / 100.0)
            
            # Ensure all classes are present
            for class_name in ['C', 'S', 'M']:
                if class_name not in class_probs:
                    class_probs[class_name] = 0.0
            
            return class_probs
            
        except Exception as e:
            logger.error(f"Error getting element class probabilities: {e}")
            return {'C': 0.33, 'S': 0.33, 'M': 0.34}
    
    def calculate_element_mining_probability(self, element_name: str, asteroid_class: str, 
                                            available_elements: List[Dict[str, Any]]) -> float:
        """
        Calculate the probability of mining a specific element from an asteroid.
        
        Args:
            element_name: Name of the element
            asteroid_class: Asteroid class (C, S, or M)
            available_elements: List of available elements on the asteroid
            
        Returns:
            Probability (0.0 to 1.0) of finding this element
        """
        # Find element in asteroid composition
        element_data = next((e for e in available_elements if e.get('name') == element_name), None)
        if not element_data:
            return 0.0
        
        # Get element's class probability for this asteroid class
        # This would be async, so we'll use a synchronous approximation
        # For now, use element abundance on asteroid as base probability
        total_mass = sum(e.get('mass_kg', 0) for e in available_elements)
        if total_mass == 0:
            return 0.0
        
        element_mass = element_data.get('mass_kg', 0)
        base_probability = element_mass / total_mass if total_mass > 0 else 0.0
        
        # Adjust based on asteroid class (simplified - in real implementation would use element class data)
        class_multipliers = {
            'C': 1.0,  # Carbonaceous asteroids favor all elements equally
            'S': 1.2,  # Silicate asteroids favor certain elements
            'M': 1.5   # Metallic asteroids have higher concentrations
        }
        
        multiplier = class_multipliers.get(asteroid_class, 1.0)
        
        # For valuable elements, increase probability
        if element_name in self.valuable_elements:
            multiplier *= 1.5
        
        return min(base_probability * multiplier, 1.0)
    
    def determine_ore_grade(self, asteroid_class: str) -> Tuple[str, float]:
        """
        Determine ore grade based on asteroid class.
        
        Args:
            asteroid_class: Asteroid class (C, S, or M)
            
        Returns:
            Tuple of (grade_class, grade_percentage)
        """
        distribution = self.ore_grade_distributions.get(asteroid_class, self.ore_grade_distributions['C'])
        
        # Roll for grade
        rand = random.random()
        cumulative = 0.0
        
        for grade, probability in distribution.items():
            cumulative += probability
            if rand <= cumulative:
                # Get grade value range
                min_val, max_val = self.ore_grade_values[grade]
                grade_percentage = random.uniform(min_val, max_val)
                return grade, grade_percentage
        
        # Fallback to medium grade
        min_val, max_val = self.ore_grade_values['medium']
        return 'medium', random.uniform(min_val, max_val)
    
    def calculate_mining_yield(self, asteroid: Dict[str, Any], 
                               mining_days: int,
                               ship_capacity: int = 50000) -> Dict[str, Any]:
        """
        Calculate realistic mining yield based on asteroid class and composition.
        
        Args:
            asteroid: Asteroid document
            mining_days: Number of days spent mining
            ship_capacity: Maximum cargo capacity in kg
            
        Returns:
            Dictionary with mining yield calculations
        """
        asteroid_class = self.get_asteroid_class(asteroid)
        available_elements = asteroid.get('elements', [])
        
        if not available_elements:
            logger.warning(f"Asteroid {asteroid.get('name', 'Unknown')} has no elements data")
            return {
                'total_ore_mined': 0,
                'effective_yield': 0,
                'ore_grade': 0.0,
                'grade_classification': 'low',
                'mining_efficiency': 0.75,
                'commodity_yield': {},
                'gangue_weight': 0
            }
        
        # Determine ore grade for this mining operation
        grade_class, ore_grade = self.determine_ore_grade(asteroid_class)
        efficiency = self.mining_efficiency.get(grade_class, 0.75)
        
        # Calculate total ore that could be mined
        max_ore_mined = min(
            mining_days * self.max_daily_mining_rate,
            ship_capacity
        )
        
        # Apply efficiency
        effective_yield = max_ore_mined * efficiency
        
        # Calculate commodity extraction based on element probabilities
        commodity_yield = {}
        total_commodity_weight = 0
        
        # Filter to valuable elements
        valuable_available = [
            e for e in available_elements 
            if e.get('name') in self.valuable_elements
        ]
        
        if valuable_available:
            # Calculate total mass of valuable elements
            total_valuable_mass = sum(e.get('mass_kg', 0) for e in valuable_available)
            
            if total_valuable_mass > 0:
                # Distribute mining based on element abundance and class probability
                for element in valuable_available:
                    element_name = element['name']
                    element_mass = element.get('mass_kg', 0)
                    
                    # Base probability from abundance
                    abundance_ratio = element_mass / total_valuable_mass
                    
                    # Adjust for asteroid class (simplified)
                    class_multiplier = {
                        'C': 0.9,  # Carbonaceous asteroids have lower concentrations
                        'S': 1.0,  # Silicate asteroids have average concentrations
                        'M': 1.3   # Metallic asteroids have higher concentrations
                    }.get(asteroid_class, 1.0)
                    
                    # Calculate element yield
                    element_ratio = abundance_ratio * class_multiplier
                    element_ore = effective_yield * element_ratio
                    
                    # Extract commodity (ore grade * ore weight)
                    commodity_weight = element_ore * ore_grade
                    commodity_yield[element_name] = commodity_weight
                    total_commodity_weight += commodity_weight
                
                # Normalize to ensure we don't exceed effective yield
                if total_commodity_weight > effective_yield * ore_grade:
                    scale_factor = (effective_yield * ore_grade) / total_commodity_weight
                    for element_name in commodity_yield:
                        commodity_yield[element_name] *= scale_factor
        
        # Calculate gangue (non-commodity material)
        gangue_weight = effective_yield * (1 - ore_grade)
        
        return {
            'total_ore_mined': max_ore_mined,
            'effective_yield': effective_yield,
            'ore_grade': ore_grade,
            'grade_classification': grade_class,
            'mining_efficiency': efficiency,
            'commodity_yield': commodity_yield,
            'gangue_weight': gangue_weight,
            'asteroid_class': asteroid_class
        }
    
    def calculate_daily_mining_output(self, asteroid: Dict[str, Any],
                                     current_cargo: Dict[str, float],
                                     ship_capacity: int = 50000) -> Dict[str, float]:
        """
        Calculate daily mining output for a mission.
        
        Args:
            asteroid: Asteroid document
            current_cargo: Current cargo dictionary
            ship_capacity: Maximum cargo capacity
            
        Returns:
            Dictionary of daily mining output (element_name -> kg)
        """
        asteroid_class = self.get_asteroid_class(asteroid)
        available_elements = asteroid.get('elements', [])
        
        # Calculate current cargo weight
        total_cargo_weight = sum(current_cargo.values()) if current_cargo else 0
        remaining_capacity = ship_capacity - total_cargo_weight
        
        if remaining_capacity <= 0:
            return {}  # Ship is full
        
        # Determine ore grade for today
        grade_class, ore_grade = self.determine_ore_grade(asteroid_class)
        efficiency = self.mining_efficiency.get(grade_class, 0.75)
        
        # Calculate daily mining capacity
        daily_ore_mined = min(
            self.max_daily_mining_rate * efficiency,
            remaining_capacity
        )
        
        if daily_ore_mined <= 0:
            return {}
        
        # Calculate commodity output
        daily_output = {}
        
        # Filter to valuable elements
        valuable_available = [
            e for e in available_elements 
            if e.get('name') in self.valuable_elements
        ]
        
        if not valuable_available:
            return {}
        
        # Calculate total mass of valuable elements for probability distribution
        total_valuable_mass = sum(e.get('mass_kg', 0) for e in valuable_available)
        
        if total_valuable_mass == 0:
            return {}
        
        # Distribute daily mining based on element abundance and class
        for element in valuable_available:
            element_name = element['name']
            element_mass = element.get('mass_kg', 0)
            
            # Base probability from abundance
            abundance_ratio = element_mass / total_valuable_mass
            
            # Class-based multiplier
            class_multiplier = {
                'C': 0.9,
                'S': 1.0,
                'M': 1.3
            }.get(asteroid_class, 1.0)
            
            # Calculate element ore mined today
            element_ore = daily_ore_mined * abundance_ratio * class_multiplier
            
            # Extract commodity (ore grade determines purity)
            commodity_weight = element_ore * ore_grade
            
            if commodity_weight > 0.1:  # Only include if > 0.1kg
                daily_output[element_name] = commodity_weight
        
        # Normalize to ensure total doesn't exceed daily capacity
        total_output = sum(daily_output.values())
        if total_output > daily_ore_mined * ore_grade:
            scale_factor = (daily_ore_mined * ore_grade) / total_output
            for element_name in daily_output:
                daily_output[element_name] *= scale_factor
        
        return daily_output
    
    async def get_mining_analysis(self, asteroid_id: str, asteroid_class: str = None) -> Dict[str, Any]:
        """
        Get comprehensive mining analysis for an asteroid.
        
        Args:
            asteroid_id: Asteroid ID or name
            asteroid_class: Optional asteroid class (if not provided, will fetch)
            
        Returns:
            Dictionary with mining analysis
        """
        try:
            # Try to get asteroid by ID or name
            asteroid = None
            if isinstance(asteroid_id, str) and len(asteroid_id) == 24:
                from bson import ObjectId
                asteroid = self.db.asteroids.find_one({"_id": ObjectId(asteroid_id)})
            else:
                asteroid = self.db.asteroids.find_one({"name": asteroid_id})
            
            if not asteroid:
                logger.warning(f"Asteroid {asteroid_id} not found")
                return {}
            
            asteroid_class = asteroid_class or self.get_asteroid_class(asteroid)
            available_elements = asteroid.get('elements', [])
            
            # Analyze element probabilities
            element_analysis = {}
            valuable_available = [
                e for e in available_elements 
                if e.get('name') in self.valuable_elements
            ]
            
            total_valuable_mass = sum(e.get('mass_kg', 0) for e in valuable_available)
            
            for element in valuable_available:
                element_name = element['name']
                element_mass = element.get('mass_kg', 0)
                
                # Get element class probabilities
                class_probs = await self.get_element_class_probabilities(element_name)
                asteroid_class_prob = class_probs.get(asteroid_class, 0.0)
                
                # Calculate expected yield probability
                abundance_ratio = element_mass / total_valuable_mass if total_valuable_mass > 0 else 0
                expected_probability = abundance_ratio * asteroid_class_prob
                
                element_analysis[element_name] = {
                    'abundance_ratio': abundance_ratio,
                    'class_probability': asteroid_class_prob,
                    'expected_probability': expected_probability,
                    'mass_kg': element_mass
                }
            
            # Get ore grade distribution for this asteroid class
            grade_distribution = self.ore_grade_distributions.get(asteroid_class, {})
            
            return {
                'asteroid_id': str(asteroid.get('_id')),
                'asteroid_name': asteroid.get('name', 'Unknown'),
                'asteroid_class': asteroid_class,
                'ore_grade_distribution': grade_distribution,
                'element_analysis': element_analysis,
                'mining_efficiency_by_grade': self.mining_efficiency,
                'max_daily_mining_rate': self.max_daily_mining_rate
            }
            
        except Exception as e:
            logger.error(f"Error getting mining analysis: {e}")
            return {}

