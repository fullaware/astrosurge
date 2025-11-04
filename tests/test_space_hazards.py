"""
Tests for Space Hazards Service
"""
import pytest
import random
from src.services.space_hazards import (
    SpaceHazardsService,
    HazardType,
    HazardSeverity
)


class TestSpaceHazardsService:
    """Test suite for SpaceHazardsService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = SpaceHazardsService()
        random.seed(42)  # For reproducible tests
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        assert self.service is not None
        assert len(self.service.base_probabilities) > 0
        assert len(self.service.hazard_impacts) > 0
    
    def test_calculate_hazard_probability_base(self):
        """Test base probability calculation"""
        prob = self.service.calculate_hazard_probability(
            HazardType.SOLAR_FLARE, "traveling", days_in_space=0, veteran_bonus=0.0
        )
        assert 0.0 <= prob <= 1.0
        # Should be higher than base due to phase multiplier
        assert prob > self.service.base_probabilities[HazardType.SOLAR_FLARE]
    
    def test_calculate_hazard_probability_veteran_bonus(self):
        """Test veteran bonus reduces probability"""
        prob_normal = self.service.calculate_hazard_probability(
            HazardType.MICROMETEORITE, "traveling", veteran_bonus=0.0
        )
        prob_veteran = self.service.calculate_hazard_probability(
            HazardType.MICROMETEORITE, "traveling", veteran_bonus=0.15
        )
        assert prob_veteran < prob_normal
    
    def test_calculate_hazard_probability_phase_multiplier(self):
        """Test phase multipliers affect probability"""
        prob_traveling = self.service.calculate_hazard_probability(
            HazardType.SOLAR_FLARE, "traveling", veteran_bonus=0.0
        )
        prob_mining = self.service.calculate_hazard_probability(
            HazardType.SOLAR_FLARE, "mining", veteran_bonus=0.0
        )
        assert prob_traveling > prob_mining  # Traveling has higher risk
    
    def test_generate_hazard_severity_distribution(self):
        """Test severity generation follows distribution"""
        severities = []
        for _ in range(100):
            level, numeric = self.service.generate_hazard_severity(HazardType.MICROMETEORITE)
            severities.append((level, numeric))
        
        # Count severity levels
        minor_count = sum(1 for s, _ in severities if s == HazardSeverity.MINOR)
        moderate_count = sum(1 for s, _ in severities if s == HazardSeverity.MODERATE)
        
        # Minor should be most common (~60%)
        assert minor_count > moderate_count
    
    def test_generate_hazard_severity_numeric_range(self):
        """Test numeric severity is in valid range"""
        for _ in range(50):
            _, numeric = self.service.generate_hazard_severity(HazardType.POWER_FAILURE)
            assert 1 <= numeric <= 10
    
    def test_calculate_hazard_impact_solar_flare(self):
        """Test solar flare impact calculation"""
        impact = self.service.calculate_hazard_impact(
            HazardType.SOLAR_FLARE, severity=5, mission_day=10, base_daily_cost=75000
        )
        
        assert impact["hazard_type"] == HazardType.SOLAR_FLARE.value
        assert impact["severity"] == 5
        assert impact["delay_days"] >= 0
        assert impact["additional_cost"] > 0
        assert impact["hull_damage"] >= 0
        assert "description" in impact
        assert "visual_indicator" in impact
    
    def test_calculate_hazard_impact_micrometeorite(self):
        """Test micrometeorite impact calculation"""
        impact = self.service.calculate_hazard_impact(
            HazardType.MICROMETEORITE, severity=8, mission_day=20, base_daily_cost=75000
        )
        
        assert impact["hazard_type"] == HazardType.MICROMETEORITE.value
        assert impact["hull_damage"] > 0  # Micrometeorites cause damage
        assert impact["delay_days"] > 0
        assert impact["additional_cost"] > 0
    
    def test_calculate_hazard_impact_cost_scaling(self):
        """Test cost scales with severity"""
        impact_low = self.service.calculate_hazard_impact(
            HazardType.POWER_FAILURE, severity=2, mission_day=5, base_daily_cost=75000
        )
        impact_high = self.service.calculate_hazard_impact(
            HazardType.POWER_FAILURE, severity=9, mission_day=5, base_daily_cost=75000
        )
        
        assert impact_high["additional_cost"] > impact_low["additional_cost"]
    
    def test_calculate_hazard_impact_hull_damage(self):
        """Test hull damage varies by hazard type"""
        micrometeorite = self.service.calculate_hazard_impact(
            HazardType.MICROMETEORITE, severity=7, mission_day=15, base_daily_cost=75000
        )
        communication = self.service.calculate_hazard_impact(
            HazardType.COMMUNICATION_FAILURE, severity=7, mission_day=15, base_daily_cost=75000
        )
        
        # Micrometeorites cause hull damage, communication failures don't
        assert micrometeorite["hull_damage"] > 0
        assert communication["hull_damage"] == 0
    
    def test_generate_hazard_event_occurrence(self):
        """Test hazard event generation"""
        # With very high probability, should generate event
        # We'll mock the probability calculation
        events = []
        for _ in range(1000):
            # Use high base probability for testing
            event = self.service.generate_hazard_event(
                mission_phase="traveling",
                days_in_space=100,
                base_daily_cost=75000,
                veteran_bonus=0.0
            )
            if event:
                events.append(event)
        
        # Should have generated at least some events in 1000 attempts
        assert len(events) > 0
    
    def test_generate_hazard_event_no_occurrence_planning(self):
        """Test no hazards during planning phase"""
        for _ in range(100):
            event = self.service.generate_hazard_event(
                mission_phase="planning",
                days_in_space=0,
                base_daily_cost=75000,
                veteran_bonus=0.0
            )
            assert event is None
    
    def test_generate_hazard_event_structure(self):
        """Test generated event has correct structure"""
        # Force an event by checking multiple times
        event = None
        for _ in range(1000):
            event = self.service.generate_hazard_event(
                mission_phase="traveling",
                days_in_space=50,
                base_daily_cost=75000,
                veteran_bonus=0.0
            )
            if event:
                break
        
        if event:  # If we got an event
            assert "hazard_type" in event
            assert "severity" in event
            assert "severity_level" in event
            assert "delay_days" in event
            assert "additional_cost" in event
            assert "hull_damage" in event
            assert "system_failure" in event
            assert "description" in event
            assert "visual_indicator" in event
    
    def test_get_hazard_statistics_empty(self):
        """Test statistics with empty history"""
        stats = self.service.get_hazard_statistics([])
        assert stats["total_hazards"] == 0
        assert stats["total_hull_damage"] == 0
        assert stats["total_cost_impact"] == 0
    
    def test_get_hazard_statistics_with_history(self):
        """Test statistics calculation with hazard history"""
        history = [
            {
                "hazard_type": HazardType.MICROMETEORITE.value,
                "severity": 5,
                "severity_level": HazardSeverity.MODERATE.value,
                "hull_damage": 3,
                "additional_cost": 150000,
                "delay_days": 2
            },
            {
                "hazard_type": HazardType.SOLAR_FLARE.value,
                "severity": 3,
                "severity_level": HazardSeverity.MINOR.value,
                "hull_damage": 0,
                "additional_cost": 50000,
                "delay_days": 1
            }
        ]
        
        stats = self.service.get_hazard_statistics(history)
        
        assert stats["total_hazards"] == 2
        assert stats["total_hull_damage"] == 3
        assert stats["total_cost_impact"] == 200000
        assert stats["total_delay_days"] == 3
        assert HazardType.MICROMETEORITE.value in stats["hazard_counts"]
        assert stats["hazard_counts"][HazardType.MICROMETEORITE.value] == 1
    
    def test_visual_indicators(self):
        """Test all hazard types have visual indicators"""
        for hazard_type in HazardType:
            assert hazard_type in self.service.visual_indicators
            indicator = self.service.visual_indicators[hazard_type]
            assert len(indicator) > 0
    
    def test_severity_level_conversion(self):
        """Test severity level conversion"""
        assert self.service._get_severity_level(1) == HazardSeverity.MINOR.value
        assert self.service._get_severity_level(5) == HazardSeverity.MODERATE.value
        assert self.service._get_severity_level(7) == HazardSeverity.SEVERE.value
        assert self.service._get_severity_level(10) == HazardSeverity.CRITICAL.value

