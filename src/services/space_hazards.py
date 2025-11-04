"""
Enhanced Space Hazards Service for AstroSurge

This service provides realistic space hazard simulation with:
- Realistic probability distributions
- Detailed impact calculations
- Hull damage tracking
- System failure modeling
- Visual indicators for events
"""
import logging
import random
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class HazardType(str, Enum):
    """Types of space hazards"""
    SOLAR_FLARE = "solar_flare"
    MICROMETEORITE = "micrometeorite"
    POWER_FAILURE = "power_failure"
    COMMUNICATION_FAILURE = "communication_failure"
    RADIATION_STORM = "radiation_storm"
    DEBRIS_FIELD = "debris_field"
    ENGINE_ANOMALY = "engine_anomaly"
    LIFE_SUPPORT_ISSUE = "life_support_issue"


class HazardSeverity(str, Enum):
    """Hazard severity levels"""
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class SpaceHazardsService:
    """
    Enhanced space hazards service with realistic probability distributions.
    
    Features:
    - Realistic probability distributions (Weibull, exponential)
    - Detailed impact calculations
    - Hull damage accumulation
    - System failure modeling
    - Cost impact calculations
    - Visual indicators
    """
    
    def __init__(self):
        """Initialize the space hazards service"""
        # Hazard base probabilities (per day, can vary by phase)
        self.base_probabilities = {
            HazardType.SOLAR_FLARE: 0.05,          # 5% daily (varies with solar cycle)
            HazardType.MICROMETEORITE: 0.03,       # 3% daily
            HazardType.POWER_FAILURE: 0.06,        # 6% daily
            HazardType.COMMUNICATION_FAILURE: 0.04, # 4% daily
            HazardType.RADIATION_STORM: 0.02,      # 2% daily
            HazardType.DEBRIS_FIELD: 0.01,         # 1% daily (rare)
            HazardType.ENGINE_ANOMALY: 0.03,       # 3% daily
            HazardType.LIFE_SUPPORT_ISSUE: 0.02,   # 2% daily
        }
        
        # Phase-specific probability multipliers
        self.phase_multipliers = {
            "traveling": 1.5,      # Higher risk during travel
            "mining": 0.8,         # Lower risk during mining (stationary)
            "returning": 1.3,      # Higher risk during return (cargo affects ship)
            "launched": 1.2,       # Moderate risk during launch
            "planning": 0.0,       # No risks during planning
            "launch_ready": 0.0,   # No risks during launch prep
        }
        
        # Hazard impact parameters
        self.hazard_impacts = {
            HazardType.SOLAR_FLARE: {
                "delay_multiplier": 0.5,      # Moderate delay
                "cost_multiplier": 2.0,       # High cost (equipment protection)
                "hull_damage_range": (0, 2), # No to minor hull damage
                "system_failure_chance": 0.3, # 30% chance of system failure
                "description_template": "Solar flare detected - shielding activated"
            },
            HazardType.MICROMETEORITE: {
                "delay_multiplier": 1.0,      # Significant delay
                "cost_multiplier": 3.0,      # Very high cost (repairs)
                "hull_damage_range": (1, 5), # Moderate to significant damage
                "system_failure_chance": 0.5, # 50% chance of system failure
                "description_template": "Micrometeorite impact detected"
            },
            HazardType.POWER_FAILURE: {
                "delay_multiplier": 0.3,      # Minor delay
                "cost_multiplier": 1.5,       # Moderate cost
                "hull_damage_range": (0, 1), # No to minor damage
                "system_failure_chance": 0.8, # 80% chance (it's a power failure)
                "description_template": "Power system anomaly detected"
            },
            HazardType.COMMUNICATION_FAILURE: {
                "delay_multiplier": 0.2,      # Minor delay
                "cost_multiplier": 1.2,       # Low cost
                "hull_damage_range": (0, 0), # No damage
                "system_failure_chance": 0.4, # 40% chance
                "description_template": "Communication link interrupted"
            },
            HazardType.RADIATION_STORM: {
                "delay_multiplier": 0.4,      # Moderate delay
                "cost_multiplier": 2.5,       # High cost (shielding)
                "hull_damage_range": (0, 1), # Minor damage
                "system_failure_chance": 0.2, # 20% chance
                "description_template": "Radiation storm detected - enhanced shielding"
            },
            HazardType.DEBRIS_FIELD: {
                "delay_multiplier": 2.0,      # Major delay (navigation)
                "cost_multiplier": 4.0,       # Very high cost (avoidance maneuvers)
                "hull_damage_range": (2, 8), # Moderate to severe damage
                "system_failure_chance": 0.6, # 60% chance
                "description_template": "Debris field encountered - evasive maneuvers"
            },
            HazardType.ENGINE_ANOMALY: {
                "delay_multiplier": 0.8,      # Moderate delay
                "cost_multiplier": 2.0,       # High cost (repairs)
                "hull_damage_range": (0, 2), # No to minor damage
                "system_failure_chance": 0.7, # 70% chance
                "description_template": "Propulsion system anomaly"
            },
            HazardType.LIFE_SUPPORT_ISSUE: {
                "delay_multiplier": 0.1,      # Minor delay
                "cost_multiplier": 1.8,       # Moderate-high cost
                "hull_damage_range": (0, 0), # No damage
                "system_failure_chance": 0.9, # 90% chance (critical system)
                "description_template": "Life support system issue detected"
            },
        }
        
        # Visual indicator codes for UI
        self.visual_indicators = {
            HazardType.SOLAR_FLARE: "🌞",
            HazardType.MICROMETEORITE: "💥",
            HazardType.POWER_FAILURE: "⚡",
            HazardType.COMMUNICATION_FAILURE: "📡",
            HazardType.RADIATION_STORM: "☢️",
            HazardType.DEBRIS_FIELD: "🛸",
            HazardType.ENGINE_ANOMALY: "🚀",
            HazardType.LIFE_SUPPORT_ISSUE: "🫁",
        }
    
    def calculate_hazard_probability(self, hazard_type: HazardType, phase: str, 
                                     days_in_space: int = 0, veteran_bonus: float = 0.0) -> float:
        """
        Calculate realistic probability for a hazard occurrence.
        
        Uses Weibull distribution for cumulative risk over time.
        More days in space = higher cumulative risk.
        
        Args:
            hazard_type: Type of hazard
            phase: Current mission phase
            days_in_space: Number of days mission has been in space
            veteran_bonus: Ship veteran bonus (0.0 to 0.15)
            
        Returns:
            Adjusted probability for this day
        """
        base_prob = self.base_probabilities.get(hazard_type, 0.01)
        
        # Apply phase multiplier
        phase_mult = self.phase_multipliers.get(phase, 1.0)
        adjusted_prob = base_prob * phase_mult
        
        # Apply cumulative risk factor (Weibull-like)
        # Longer missions have slightly higher risk
        cumulative_factor = 1.0 + (days_in_space / 1000.0)  # Very gradual increase
        adjusted_prob *= cumulative_factor
        
        # Apply veteran bonus (reduces risk)
        adjusted_prob *= (1.0 - veteran_bonus)
        
        # Ensure probability stays within bounds
        return min(adjusted_prob, 1.0)
    
    def generate_hazard_severity(self, hazard_type: HazardType) -> Tuple[HazardSeverity, int]:
        """
        Generate realistic severity for a hazard.
        
        Uses weighted distribution - most hazards are minor/moderate,
        severe and critical are rare.
        
        Args:
            hazard_type: Type of hazard
            
        Returns:
            Tuple of (severity level, numeric severity 1-10)
        """
        # Weighted random selection for severity distribution
        # 60% minor, 25% moderate, 12% severe, 3% critical
        weights = [0.60, 0.25, 0.12, 0.03]
        severity_levels = [
            HazardSeverity.MINOR,
            HazardSeverity.MODERATE,
            HazardSeverity.SEVERE,
            HazardSeverity.CRITICAL
        ]
        
        severity_level = random.choices(severity_levels, weights=weights)[0]
        
        # Map severity to numeric value
        severity_map = {
            HazardSeverity.MINOR: (1, 3),
            HazardSeverity.MODERATE: (4, 6),
            HazardSeverity.SEVERE: (7, 8),
            HazardSeverity.CRITICAL: (9, 10)
        }
        
        min_sev, max_sev = severity_map[severity_level]
        numeric_severity = random.randint(min_sev, max_sev)
        
        return severity_level, numeric_severity
    
    def calculate_hazard_impact(self, hazard_type: HazardType, severity: int,
                                mission_day: int, base_daily_cost: float) -> Dict[str, Any]:
        """
        Calculate detailed impact of a hazard event.
        
        Args:
            hazard_type: Type of hazard
            severity: Numeric severity (1-10)
            mission_day: Current mission day
            base_daily_cost: Base daily mission cost
            
        Returns:
            Dictionary with impact details
        """
        impact_params = self.hazard_impacts.get(hazard_type, {})
        
        # Calculate delay days (scaled by severity)
        base_delay = impact_params.get("delay_multiplier", 1.0)
        delay_days = int(base_delay * (severity / 5.0))
        
        # Calculate additional cost (scaled by severity and base cost)
        cost_multiplier = impact_params.get("cost_multiplier", 1.0)
        additional_cost = base_daily_cost * cost_multiplier * (severity / 5.0)
        
        # Calculate hull damage (if applicable)
        damage_range = impact_params.get("hull_damage_range", (0, 0))
        if damage_range[1] > 0:
            # Scale damage by severity
            max_damage = damage_range[1]
            min_damage = damage_range[0]
            hull_damage = int(min_damage + ((max_damage - min_damage) * (severity / 10.0)))
        else:
            hull_damage = 0
        
        # Determine if system failure occurred
        failure_chance = impact_params.get("system_failure_chance", 0.0)
        system_failure = random.random() < failure_chance
        
        # Get description
        description_template = impact_params.get("description_template", "Hazard detected")
        description = f"{description_template} (Severity: {severity}/10)"
        
        # Visual indicator
        visual_indicator = self.visual_indicators.get(hazard_type, "⚠️")
        
        return {
            "hazard_type": hazard_type.value,
            "severity": severity,
            "severity_level": self._get_severity_level(severity),
            "delay_days": delay_days,
            "additional_cost": additional_cost,
            "hull_damage": hull_damage,
            "system_failure": system_failure,
            "description": description,
            "visual_indicator": visual_indicator,
            "impact_timestamp": datetime.now(timezone.utc)
        }
    
    def _get_severity_level(self, severity: int) -> str:
        """Convert numeric severity to level"""
        if severity <= 3:
            return HazardSeverity.MINOR.value
        elif severity <= 6:
            return HazardSeverity.MODERATE.value
        elif severity <= 8:
            return HazardSeverity.SEVERE.value
        else:
            return HazardSeverity.CRITICAL.value
    
    def generate_hazard_event(self, mission_phase: str, days_in_space: int,
                             base_daily_cost: float, veteran_bonus: float = 0.0) -> Optional[Dict[str, Any]]:
        """
        Generate a hazard event if probability threshold is met.
        
        This is the main entry point for hazard generation.
        
        Args:
            mission_phase: Current mission phase
            days_in_space: Days mission has been in space
            base_daily_cost: Base daily mission cost
            veteran_bonus: Ship veteran bonus
            
        Returns:
            Hazard event dictionary if one occurred, None otherwise
        """
        # Check each hazard type
        for hazard_type in HazardType:
            prob = self.calculate_hazard_probability(
                hazard_type, mission_phase, days_in_space, veteran_bonus
            )
            
            if random.random() < prob:
                # Hazard occurred!
                severity_level, severity = self.generate_hazard_severity(hazard_type)
                impact = self.calculate_hazard_impact(
                    hazard_type, severity, days_in_space, base_daily_cost
                )
                
                logger.info(f"Hazard generated: {hazard_type.value} at severity {severity}")
                return impact
        
        return None
    
    def get_hazard_statistics(self, hazard_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics from hazard history.
        
        Args:
            hazard_history: List of past hazard events
            
        Returns:
            Statistics dictionary
        """
        if not hazard_history:
            return {
                "total_hazards": 0,
                "total_hull_damage": 0,
                "total_cost_impact": 0,
                "total_delay_days": 0,
                "hazard_counts": {},
                "severity_distribution": {}
            }
        
        total_hull_damage = sum(h.get("hull_damage", 0) for h in hazard_history)
        total_cost = sum(h.get("additional_cost", 0) for h in hazard_history)
        total_delay = sum(h.get("delay_days", 0) for h in hazard_history)
        
        hazard_counts = {}
        severity_dist = {}
        
        for hazard in hazard_history:
            hazard_type = hazard.get("hazard_type", "unknown")
            hazard_counts[hazard_type] = hazard_counts.get(hazard_type, 0) + 1
            
            severity_level = hazard.get("severity_level", "unknown")
            severity_dist[severity_level] = severity_dist.get(severity_level, 0) + 1
        
        return {
            "total_hazards": len(hazard_history),
            "total_hull_damage": total_hull_damage,
            "total_cost_impact": total_cost,
            "total_delay_days": total_delay,
            "hazard_counts": hazard_counts,
            "severity_distribution": severity_dist,
            "average_severity": sum(h.get("severity", 0) for h in hazard_history) / len(hazard_history)
        }

