#!/usr/bin/env python3
"""
AstroSurge - Complete Mission Lifecycle System
Asteroid Mining Operation Simulator

This is a complete rebuild implementing:
- World simulation with daily clock ticks
- Complete mission lifecycle (planning → launch → travel → mining → return)
- Ship management with realistic costs ($150M ship, $25M max repair)
- Asteroid integration with real data
- Economic modeling with investor funding
"""

import os
import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Import enhanced services
from src.services.commodity_pricing_standalone import CommodityPricingService
from src.services.mission_economics import MissionEconomicsService
from src.services.orbital_mechanics import OrbitalMechanicsService
from src.services.space_hazards import SpaceHazardsService, HazardType
from src.services.mining_operations import MiningOperationsService

# Environment configuration
from dotenv import load_dotenv
load_dotenv()

# MongoDB connection string
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable not set")

# Pydantic Models for Complete System
class UserBase(BaseModel):
    username: str = Field(..., description="Unique username")
    company_name: str = Field(..., description="Company name")
    bank_balance: float = Field(..., description="Current balance in dollars")
    investor_debt: float = Field(default=0, description="Current debt to investors")

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: str = Field(..., alias="_id")
    created_at: datetime
    last_login: datetime

    class Config:
        allow_population_by_field_name = True

class ShipBase(BaseModel):
    name: str = Field(..., description="Ship name")
    user_id: str = Field(..., description="Owner username")
    capacity: float = Field(..., description="Cargo capacity in kg")
    mining_power: float = Field(..., description="Mining efficiency")
    shield: float = Field(..., ge=0, le=100, description="Shield strength")
    hull: float = Field(..., ge=0, le=100, description="Hull integrity")
    power_systems: float = Field(..., ge=0, le=100, description="Power system health")

class ShipCreate(ShipBase):
    pass

class Ship(ShipBase):
    id: str = Field(..., alias="_id")
    status: str = Field(..., description="Ship status")
    location: str = Field(..., description="Current location")
    current_cargo: float = Field(default=0, description="Current cargo weight")
    cargo_composition: Dict[str, float] = Field(default_factory=dict, description="Cargo breakdown")
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True

class MissionEvent(BaseModel):
    day: int = Field(..., description="Day event occurred")
    event_type: str = Field(..., description="Type of event")
    description: str = Field(..., description="Event description")
    impact_days: int = Field(..., description="Days of delay")
    cost: float = Field(..., description="Additional cost")

class MissionCosts(BaseModel):
    ground_control: float = Field(default=0, description="Ground control costs")
    launch_scrubs: float = Field(default=0, description="Launch scrub costs")
    space_events: float = Field(default=0, description="Space event costs")
    total: float = Field(default=0, description="Total mission cost")

class MissionBase(BaseModel):
    name: str = Field(..., description="Mission name")
    user_id: str = Field(..., description="Owner username")
    ship_id: str = Field(..., description="Ship ObjectId")
    asteroid_id: str = Field(..., description="Target asteroid ID")
    asteroid_name: Optional[str] = Field(None, description="Target asteroid name")
    asteroid_moid_days: Optional[float] = Field(None, description="Days to reach asteroid")
    budget: Optional[float] = Field(None, description="Mission budget")
    loan_id: Optional[str] = Field(None, description="Linked loan ID")
    description: Optional[str] = Field(None, description="Mission description")

class MissionCreate(MissionBase):
    pass

class Mission(MissionBase):
    id: str = Field(..., alias="_id")
    status: str = Field(..., description="Mission status")
    launch_date: datetime = Field(..., description="Scheduled launch date")
    actual_launch_date: Optional[datetime] = Field(None, description="Actual launch date")
    current_phase: str = Field(..., description="Current mission phase")
    current_day: int = Field(..., description="Days into current phase")
    total_days: int = Field(..., description="Total mission days")
    costs: MissionCosts = Field(default_factory=MissionCosts)
    events: List[MissionEvent] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True

class ConfigBase(BaseModel):
    ground_control_cost_per_day: float = Field(..., description="Daily ground control cost")
    launch_scrub_cost: float = Field(..., description="Cost when launch is scrubbed")
    base_ship_cost: float = Field(..., description="Base cost for new mining ship")
    ship_repair_cost_max: float = Field(..., description="Maximum ship repair cost")
    ship_cargo_capacity: float = Field(..., description="Standard ship cargo capacity")
    investor_interest_rate: float = Field(..., description="Annual interest rate for loans")
    mining_efficiency_base: float = Field(..., description="Base mining efficiency")
    asteroid_yield_multiplier: float = Field(..., description="Asteroid resource yield multiplier")

class EventBase(BaseModel):
    event_name: str = Field(..., description="Event identifier")
    event_type: str = Field(..., description="Event type")
    phase: str = Field(..., description="Mission phase")
    probability: float = Field(..., ge=0.0, le=1.0, description="Daily probability")
    impact_days: int = Field(..., description="Days of delay/impact")
    cost_multiplier: float = Field(..., description="Cost impact multiplier")
    description: str = Field(..., description="Event description")
    min_severity: int = Field(..., ge=1, le=10, description="Minimum severity")
    max_severity: int = Field(..., ge=1, le=10, description="Maximum severity")

class WorldStateBase(BaseModel):
    simulation_id: str = Field(..., description="Unique simulation identifier")
    current_day: int = Field(..., description="Current simulation day")
    status: str = Field(..., description="Simulation status")
    total_cost: float = Field(..., description="Accumulated costs")
    total_revenue: float = Field(..., description="Total revenue")
    active_missions: int = Field(..., description="Active missions")
    total_ships: int = Field(..., description="Total ships")

# World Simulation Engine with Mission Management
class WorldSimulationEngine:
    """Complete world simulation engine with mission lifecycle"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.config = None
        self.events = []
        self.world_state = None
        
        # Initialize enhanced services
        # Initialize pricing service with MongoDB caching
        mongodb_uri = os.getenv("MONGODB_URI")
        self.pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        self.economics_service = MissionEconomicsService()
        self.orbital_service = OrbitalMechanicsService()
        self.hazards_service = SpaceHazardsService()
        self.mining_service = MiningOperationsService(mongodb_uri=mongodb_uri)
    
    async def initialize(self):
        """Initialize the simulation engine"""
        # Load configuration
        self.config = await self.db.get_config()
        
        # Load events
        self.events = await self.db.get_events()
        
        # Load world state
        self.world_state = await self.db.get_world_state()
        
        print(f"✅ World Simulation Engine initialized")
        print(f"   - Config loaded: {len(self.config)} parameters")
        print(f"   - Events loaded: {len(self.events)} event types")
        print(f"   - World state: Day {self.world_state['current_day']}")
    
    async def process_daily_tick(self):
        """Process one simulation day"""
        if self.world_state['status'] != 'running':
            return
        
        current_day = self.world_state['current_day']
        print(f"🌍 Processing simulation day {current_day}")
        
        # Process all missions (including planning phase)
        all_missions = await self.db.get_missions()
        print(f"   📋 Processing {len(all_missions)} missions")
        
        for mission in all_missions:
            # Skip missions with auto_progress disabled
            if not mission.get('auto_progress', True):
                print(f"   ⏸️  Skipping mission: {mission['name']} (auto-progress paused)")
                continue
            
            print(f"   🚀 Processing mission: {mission['name']} (Phase: {mission['current_phase']}, Day: {mission['current_day']})")
            await self.process_mission_day(mission, current_day)
        
        # Update world state
        self.world_state['current_day'] += 1
        self.world_state['last_updated'] = datetime.now(timezone.utc)
        await self.db.update_world_state(self.world_state)
        
        print(f"✅ Day {current_day} processed")
    
    async def process_mission_day(self, mission, day):
        """Process one day for a specific mission"""
        mission_id = mission['_id']
        phase = mission['current_phase']
        
        # Check if mission has auto_progress disabled
        if not mission.get('auto_progress', True):
            print(f"   ⏸️  Mission {mission_id} is paused (auto_progress: false)")
            return
        
        # Use enhanced space hazards service for realistic hazard generation
        base_daily_cost = self.config.get('ground_control_cost_per_day', 75000)
        days_in_space = mission.get('total_days', 0) - mission.get('current_day', 0)
        
        # Get veteran bonus for ship
        veteran_bonus = 0.0
        if mission.get('ship_id'):
            ship = await self.db.get_ship(mission['ship_id'])
            if ship and ship.get('veteran_status', False):
                veteran_bonus = 0.15
        
        # Generate enhanced hazard event
        hazard_event = self.hazards_service.generate_hazard_event(
            mission_phase=phase,
            days_in_space=days_in_space,
            base_daily_cost=base_daily_cost,
            veteran_bonus=veteran_bonus
        )
        
        if hazard_event:
            await self.apply_enhanced_hazard_to_mission(mission_id, hazard_event, day)
        
        # Also check for legacy events (for backwards compatibility)
        phase_events = [e for e in self.events if e['phase'] == phase]
        for event in phase_events:
            if random.random() < event['probability']:
                await self.apply_event_to_mission(mission_id, event, day)
        
        # Update mission progress based on phase
        await self.update_mission_progress(mission_id, day, phase)
    
    async def apply_enhanced_hazard_to_mission(self, mission_id, hazard_event, day):
        """Apply an enhanced hazard event to a mission"""
        # Get mission for updates
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        # Create mission event from hazard
        mission_event = MissionEvent(
            day=day,
            event_type=hazard_event['hazard_type'],
            description=hazard_event['description'],
            impact_days=hazard_event['delay_days'],
            cost=hazard_event['additional_cost']
        )
        
        # Update mission with event
        await self.db.add_mission_event(mission_id, mission_event)
        
        # Update hull damage if applicable
        if hazard_event['hull_damage'] > 0:
            current_damage = mission.get('hull_damage', 0) or 0
            new_damage = current_damage + hazard_event['hull_damage']
            
            # Update mission with new hull damage
            from bson import ObjectId
            try:
                self.db.db.missions.update_one(
                    {"_id": ObjectId(mission_id)},
                    {"$set": {"hull_damage": new_damage}}
                )
            except Exception as e:
                print(f"   ⚠️  Error updating hull damage: {e}")
        
        # Update mission costs
        current_costs = mission.get('costs', {})
        new_space_event_cost = current_costs.get('space_events', 0) + hazard_event['additional_cost']
        new_total_cost = current_costs.get('total', 0) + hazard_event['additional_cost']
        
        # Update costs in database
        from bson import ObjectId
        try:
            self.db.db.missions.update_one(
                {"_id": ObjectId(mission_id)},
                {"$set": {
                    "costs.space_events": new_space_event_cost,
                    "costs.total": new_total_cost
                }}
            )
        except Exception as e:
            print(f"   ⚠️  Error updating mission costs: {e}")
        
        # Print hazard information
        indicator = hazard_event.get('visual_indicator', '⚠️')
        print(f"   {indicator} Mission {mission_id}: {hazard_event['hazard_type']} ({hazard_event['severity_level']})")
        print(f"      Impact: {hazard_event['delay_days']} days delay, Cost: ${hazard_event['additional_cost']:,.2f}")
        if hazard_event['hull_damage'] > 0:
            print(f"      Hull Damage: +{hazard_event['hull_damage']} points")
        if hazard_event['system_failure']:
            print(f"      System Failure: Critical system affected")
    
    async def apply_event_to_mission(self, mission_id, event, day):
        """Apply a legacy event to a mission (backwards compatibility)"""
        severity = random.randint(event['min_severity'], event['max_severity'])
        impact_days = event['impact_days'] * (severity / 5.0)  # Scale by severity
        additional_cost = self.config['ground_control_cost_per_day'] * impact_days * event['cost_multiplier']
        
        # Check if ship has veteran status for bonus
        mission = await self.db.get_mission(mission_id)
        veteran_bonus = 0.0
        if mission and mission.get('ship_id'):
            ship = await self.db.get_ship(mission['ship_id'])
            if ship and ship.get('veteran_status', False):
                veteran_bonus = 0.15  # 15% bonus for veteran ships
                # Reduce negative impact by veteran bonus
                impact_days = max(0, impact_days * (1 - veteran_bonus))
                additional_cost = max(0, additional_cost * (1 - veteran_bonus))
                print(f"      🏆 Veteran ship bonus applied: {veteran_bonus*100:.0f}% reduction")
        
        # Create mission event
        mission_event = MissionEvent(
            day=day,
            event_type=event['event_type'],
            description=f"{event['description']} (Severity: {severity})",
            impact_days=int(impact_days),
            cost=additional_cost
        )
        
        # Update mission with event
        await self.db.add_mission_event(mission_id, mission_event)
        
        print(f"   ⚠️  Mission {mission_id}: {event['event_name']} (Severity {severity})")
        print(f"      Impact: {int(impact_days)} days, Cost: ${additional_cost:,.2f}")
    
    async def update_mission_progress(self, mission_id, day, phase):
        """Update mission progress based on current phase"""
        print(f"      🔄 Updating mission {mission_id} progress (Phase: {phase})")
        
        if phase == "planning":
            # Check if mission is ready to launch (after planning phase)
            mission = await self.db.get_mission(mission_id)
            print(f"      📋 Mission {mission_id} in planning phase, current_day: {mission['current_day'] if mission else 'None'}")
            
            if mission and mission['current_day'] >= 7:  # Planning phase takes 7 days
                await self.db.update_mission_phase(mission_id, "launch_ready", 0)
                print(f"   📋 Mission {mission_id} planning complete, ready for launch")
            else:
                # Increment mission day counter
                print(f"      📅 Incrementing mission {mission_id} day from {mission['current_day'] if mission else 'None'}")
                result = await self.db.increment_mission_day(mission_id)
                print(f"      ✅ Mission day increment result: {result}")
        elif phase == "launch_ready":
            # Check if launch conditions are met
            await self.check_launch_conditions(mission_id)
            # Increment mission day counter for launch phase
            await self.db.increment_mission_day(mission_id)
        elif phase == "launched":
            # Mission is in transit to asteroid
            await self.progress_travel_phase(mission_id, day)
            # Increment mission day counter for travel phase
            await self.db.increment_mission_day(mission_id)
        elif phase == "traveling":
            # Continue travel to asteroid
            await self.progress_travel_phase(mission_id, day)
            # Increment mission day counter for travel phase
            await self.db.increment_mission_day(mission_id)
        elif phase == "mining_setup":
            # Mining site establishment phase
            await self.progress_mining_setup_phase(mission_id, day)
        elif phase == "mining":
            # Mining operations on asteroid
            await self.progress_mining_phase(mission_id, day)
        elif phase == "cargo_loading":
            # Cargo loading and return preparation
            await self.progress_cargo_loading_phase(mission_id, day)
        elif phase == "returning":
            # Return journey to Earth
            await self.progress_return_phase(mission_id, day)
        
        # Update mission timestamp
        await self.db.update_mission_timestamp(mission_id)
    
    async def check_launch_conditions(self, mission_id):
        """Check if launch conditions are met with realistic weather and technical checks"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        current_day = mission.get('current_day', 0)
        launch_scrubs = mission.get('launch_scrubs', 0)
        
        # Check launch conditions daily
        weather_clear = random.random() < 0.70  # 70% chance of clear weather
        technical_ready = random.random() < 0.92  # 92% chance of technical readiness
        range_available = random.random() < 0.93  # 93% chance of range availability
        
        if not weather_clear:
            # Weather scrub - increment scrub count and cost
            launch_scrubs += 1
            scrub_cost = self.config.get('launch_scrub_cost', 75000)
            
            # Update mission with scrub event
            from bson import ObjectId
            try:
                self.db.db.missions.update_one(
                    {"_id": ObjectId(mission_id)},
                    {"$set": {
                        "launch_scrubs": launch_scrubs,
                        "costs.launch_scrubs": launch_scrubs * scrub_cost,
                        "costs.total": mission.get('costs', {}).get('total', 0) + scrub_cost
                    }}
                )
            except Exception as e:
                print(f"   ⚠️  Error updating launch scrub: {e}")
            
            # Add event
            event = MissionEvent(
                day=current_day,
                event_type="launch_scrub",
                description="Launch scrubbed due to weather conditions",
                impact_days=1,
                cost=scrub_cost
            )
            await self.db.add_mission_event(mission_id, event)
            
            print(f"   ⛈️  Mission {mission_id}: Launch scrubbed due to weather (Scrub #{launch_scrubs})")
            return
        
        if not technical_ready:
            # Technical scrub
            launch_scrubs += 1
            scrub_cost = self.config.get('launch_scrub_cost', 75000)
            
            from bson import ObjectId
            try:
                self.db.db.missions.update_one(
                    {"_id": ObjectId(mission_id)},
                    {"$set": {
                        "launch_scrubs": launch_scrubs,
                        "costs.launch_scrubs": launch_scrubs * scrub_cost,
                        "costs.total": mission.get('costs', {}).get('total', 0) + scrub_cost
                    }}
                )
            except Exception as e:
                print(f"   ⚠️  Error updating launch scrub: {e}")
            
            event = MissionEvent(
                day=current_day,
                event_type="launch_scrub",
                description="Launch scrubbed due to technical issues",
                impact_days=1,
                cost=scrub_cost
            )
            await self.db.add_mission_event(mission_id, event)
            
            print(f"   🔧 Mission {mission_id}: Launch scrubbed due to technical issues (Scrub #{launch_scrubs})")
            return
        
        if not range_available:
            # Range conflict scrub
            launch_scrubs += 1
            scrub_cost = self.config.get('launch_scrub_cost', 75000)
            
            from bson import ObjectId
            try:
                self.db.db.missions.update_one(
                    {"_id": ObjectId(mission_id)},
                    {"$set": {
                        "launch_scrubs": launch_scrubs,
                        "costs.launch_scrubs": launch_scrubs * scrub_cost,
                        "costs.total": mission.get('costs', {}).get('total', 0) + scrub_cost
                    }}
                )
            except Exception as e:
                print(f"   ⚠️  Error updating launch scrub: {e}")
            
            event = MissionEvent(
                day=current_day,
                event_type="launch_scrub",
                description="Launch scrubbed due to range conflict",
                impact_days=1,
                cost=scrub_cost
            )
            await self.db.add_mission_event(mission_id, event)
            
            print(f"   🚫 Mission {mission_id}: Launch scrubbed due to range conflict (Scrub #{launch_scrubs})")
            return
        
        # All conditions met - launch!
        from datetime import datetime, timezone
        await self.db.update_mission_phase(mission_id, "launched", 0)
        
        # Update actual launch date
        from bson import ObjectId
        try:
            self.db.db.missions.update_one(
                {"_id": ObjectId(mission_id)},
                {"$set": {"actual_launch_date": datetime.now(timezone.utc)}}
            )
        except Exception as e:
            print(f"   ⚠️  Error updating launch date: {e}")
        
        print(f"   🚀 Mission {mission_id} launched successfully! (After {launch_scrubs} scrubs)")
    
    async def progress_travel_phase(self, mission_id, day):
        """Progress the travel phase of a mission using orbital mechanics"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        current_day = mission['current_day']
        
        # Get asteroid MOID for realistic travel calculations
        asteroid_id = mission.get('asteroid_id')
        asteroid_moid_days = mission.get('asteroid_moid_days', 90)  # Fallback
        
        # Use orbital mechanics service for accurate travel time if asteroid data available
        if asteroid_id:
            try:
                asteroid = await self.db.get_asteroid(asteroid_id)
                if asteroid and 'moid' in asteroid:
                    moid_au = float(asteroid.get('moid', 1.0))
                    travel_calc = self.orbital_service.calculate_travel_time(moid_au, 'round_trip')
                    asteroid_moid_days = int(travel_calc['one_way_time_days'])
                    
                    # Update mission with accurate travel time if not already set
                    if 'asteroid_moid_days' not in mission or mission['asteroid_moid_days'] != asteroid_moid_days:
                        from bson import ObjectId
                        try:
                            self.db.db.missions.update_one(
                                {"_id": ObjectId(mission_id)},
                                {"$set": {"asteroid_moid_days": asteroid_moid_days}}
                            )
                        except Exception as update_error:
                            print(f"   ⚠️  Error updating mission travel time: {update_error}")
            except Exception as e:
                print(f"   ⚠️  Error calculating travel time with orbital mechanics: {e}")
                # Continue with existing asteroid_moid_days value
        
        # After first day of launch, transition to traveling phase
        if current_day == 1 and mission['current_phase'] == 'launched':
            await self.db.update_mission_phase(mission_id, "traveling", current_day)
            print(f"   🚀 Mission {mission_id} transitioned to traveling phase")
        
        # Check if arrived at asteroid
        if current_day >= asteroid_moid_days:
            # Arrived at asteroid, switch to mining site establishment phase
            await self.db.update_mission_phase(mission_id, "mining_setup", 0)
            print(f"   🚀 Mission {mission_id} arrived at asteroid, beginning mining site establishment")
    
    async def progress_mining_phase(self, mission_id, day):
        """Progress the mining phase of a mission using class-based mining probabilities"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        # Get asteroid data for mining calculations
        asteroid_id = mission.get('asteroid_id')
        if not asteroid_id:
            print(f"   ❌ Mission {mission_id} has no asteroid assigned")
            return
        
        # Get asteroid composition for mining calculations
        asteroid = await self.db.get_asteroid(asteroid_id)
        if not asteroid:
            print(f"   ❌ Asteroid {asteroid_id} not found for mission {mission_id}")
            return
        
        # Get current cargo
        current_cargo = mission.get('cargo', {})
        total_cargo_weight = sum(current_cargo.values()) if current_cargo else 0
        
        # Get ship capacity from mission or default
        ship_capacity = mission.get('ship_capacity', 50000)  # kg
        
        if total_cargo_weight >= ship_capacity:
            # Ship is full, switch to cargo loading phase
            await self.db.update_mission_phase(mission_id, "cargo_loading", 0)
            print(f"   ⛏️  Mission {mission_id} cargo full ({total_cargo_weight}kg), beginning cargo loading and return preparation")
            return
        
        # Use enhanced mining service for class-based mining
        try:
            daily_output = self.mining_service.calculate_daily_mining_output(
                asteroid=asteroid,
                current_cargo=current_cargo,
                ship_capacity=ship_capacity
            )
            
            if daily_output:
                # Update mission cargo
                new_cargo = current_cargo.copy()
                for element, amount in daily_output.items():
                    new_cargo[element] = new_cargo.get(element, 0) + amount
                
                # Update mission with new cargo
                await self.db.update_mission_cargo(mission_id, new_cargo)
                
                # Get asteroid class for logging
                asteroid_class = self.mining_service.get_asteroid_class(asteroid)
                total_mined = sum(daily_output.values())
                
                print(f"   ⛏️  Mission {mission_id} mined {total_mined:.1f}kg from {asteroid_class}-type asteroid (Total: {sum(new_cargo.values()):.1f}kg)")
                print(f"      Elements: {', '.join([f'{k}: {v:.1f}kg' for k, v in daily_output.items()])}")
            else:
                print(f"   ⚠️  Mission {mission_id} - No mining output (ship may be full or no valuable elements)")
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in enhanced mining calculation: {e}")
            # Fallback to basic mining
            print(f"   ⚠️  Mission {mission_id} - Using fallback mining calculation")
            daily_mining_capacity = 1500
            remaining_capacity = min(daily_mining_capacity, ship_capacity - total_cargo_weight)
            
            if remaining_capacity > 0:
                available_elements = asteroid.get('elements', [])
                valuable_elements = ['Gold', 'Platinum', 'Palladium', 'Silver', 'Copper', 'Lithium', 'Cobalt']
                valuable_available = [e for e in available_elements if e.get('name') in valuable_elements]
                
                if valuable_available:
                    per_element = remaining_capacity / len(valuable_available)
                    new_cargo = current_cargo.copy()
                    for element in valuable_available:
                        element_name = element['name']
                        new_cargo[element_name] = new_cargo.get(element_name, 0) + per_element
                    
                    await self.db.update_mission_cargo(mission_id, new_cargo)
                    print(f"   ⛏️  Mission {mission_id} mined {remaining_capacity:.1f}kg (fallback mode)")
        
        # Increment mission day counter for mining phase
        await self.db.increment_mission_day(mission_id)
    
    async def progress_mining_setup_phase(self, mission_id, day):
        """Progress the mining site establishment phase"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        current_day = mission.get('current_day', 0)
        setup_days_required = 2  # 2 days to establish mining site
        
        if current_day == 0:
            print(f"   🔧 Mission {mission_id}: Beginning mining site establishment...")
        
        # Check for site establishment delays (10% chance per day)
        if random.random() < 0.10:
            delay_days = 1
            additional_cost = self.config.get('ground_control_cost_per_day', 75000) * delay_days
            
            # Add delay event
            event = MissionEvent(
                day=day,
                event_type="mining_setup_delay",
                description="Mining site establishment delayed due to equipment issues",
                impact_days=delay_days,
                cost=additional_cost
            )
            await self.db.add_mission_event(mission_id, event)
            
            # Update costs
            from bson import ObjectId
            try:
                current_costs = mission.get('costs', {})
                self.db.db.missions.update_one(
                    {"_id": ObjectId(mission_id)},
                    {"$set": {
                        "costs.total": current_costs.get('total', 0) + additional_cost
                    }}
                )
            except Exception as e:
                print(f"   ⚠️  Error updating setup delay costs: {e}")
            
            print(f"   ⚠️  Mission {mission_id}: Mining site setup delayed by {delay_days} day(s)")
            await self.db.increment_mission_day(mission_id)
            return
        
        if current_day >= setup_days_required:
            # Site establishment complete, switch to mining phase
            await self.db.update_mission_phase(mission_id, "mining", 0)
            print(f"   ✅ Mission {mission_id}: Mining site established, beginning extraction operations")
        else:
            # Continue site establishment
            await self.db.increment_mission_day(mission_id)
    
    async def progress_cargo_loading_phase(self, mission_id, day):
        """Progress the cargo loading and return preparation phase"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        current_day = mission.get('current_day', 0)
        loading_days_required = 2  # 2 days to load cargo and prepare for return
        
        if current_day == 0:
            cargo_weight = sum(mission.get('cargo', {}).values())
            print(f"   📦 Mission {mission_id}: Beginning cargo loading ({cargo_weight:.1f}kg)...")
        
        # Check for loading delays (8% chance per day)
        if random.random() < 0.08:
            delay_days = 1
            additional_cost = self.config.get('ground_control_cost_per_day', 75000) * delay_days
            
            # Add delay event
            event = MissionEvent(
                day=day,
                event_type="cargo_loading_delay",
                description="Cargo loading delayed due to securing operations",
                impact_days=delay_days,
                cost=additional_cost
            )
            await self.db.add_mission_event(mission_id, event)
            
            # Update costs
            from bson import ObjectId
            try:
                current_costs = mission.get('costs', {})
                self.db.db.missions.update_one(
                    {"_id": ObjectId(mission_id)},
                    {"$set": {
                        "costs.total": current_costs.get('total', 0) + additional_cost
                    }}
                )
            except Exception as e:
                print(f"   ⚠️  Error updating loading delay costs: {e}")
            
            print(f"   ⚠️  Mission {mission_id}: Cargo loading delayed by {delay_days} day(s)")
            await self.db.increment_mission_day(mission_id)
            return
        
        if current_day >= loading_days_required:
            # Cargo loading complete, switch to return phase
            await self.db.update_mission_phase(mission_id, "returning", 0)
            print(f"   ✅ Mission {mission_id}: Cargo secured and return trajectory planned, beginning return journey")
        else:
            # Continue cargo loading
            await self.db.increment_mission_day(mission_id)
    
    async def progress_return_phase(self, mission_id, day):
        """Progress the return phase of a mission"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        # For now, return takes a fixed number of days
        # In a real system, this would depend on asteroid distance
        return_days = 90  # Fixed for now
        
        if mission['current_day'] >= return_days:
            # Return complete, mission finished
            await self.db.update_mission_phase(mission_id, "completed", 0)
            print(f"   🌍 Mission {mission_id} returned to Earth successfully!")
            
            # Calculate final mission results
            await self.calculate_mission_results(mission_id)
        else:
            # Continue return journey
            await self.db.increment_mission_day(mission_id)
    
    async def calculate_mission_results(self, mission_id):
        """Calculate final mission results using enhanced economics service with detailed settlement"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        # Use enhanced mission economics service for comprehensive calculations
        try:
            economics = await self.economics_service.calculate_comprehensive_mission_economics(mission_id)
            
            # Calculate detailed investor repayment breakdown
            total_costs = economics.get('total_costs', 0)
            mission_duration_days = mission.get('total_days', 0) or mission.get('current_day', 0)
            daily_interest_rate = self.config.get('investor_interest_rate', 0.15) / 365
            interest_amount = total_costs * daily_interest_rate * mission_duration_days
            principal_amount = total_costs
            total_repayment = principal_amount + interest_amount
            
            # Get user for balance update
            user_id = mission.get('user_id')
            user = None
            if user_id:
                users = await self.db.get_users()
                user = next((u for u in users if u.get('username') == user_id or str(u.get('_id')) == user_id), None)
            
            # Update mission with final results
            final_results = {
                'mission_complete': True,
                'settlement_date': datetime.now(timezone.utc).isoformat(),
                'total_costs': total_costs,
                'investor_repayment': total_repayment,
                'principal_amount': principal_amount,
                'interest_paid': interest_amount,
                'interest_rate': self.config.get('investor_interest_rate', 0.15),
                'mission_duration_days': mission_duration_days,
                'ship_repair_cost': economics.get('ship_repair_cost', 0),
                'hull_damage': mission.get('hull_damage', 0) or 0,
                'cargo_value': economics.get('cargo_value', {}).get('total_value', 0),
                'net_profit': economics.get('net_profit', 0),
                'roi_percentage': economics.get('roi_percentage', 0),
                'economics_details': economics,
                'settlement_details': {
                    'cargo_sold': True,
                    'investor_repaid': True,
                    'ship_repaired': economics.get('ship_repair_cost', 0) > 0,
                    'user_balance_before': user.get('bank_balance', 0) if user else 0,
                    'user_balance_after': (user.get('bank_balance', 0) + economics.get('net_profit', 0)) if user else 0
                }
            }
            
            await self.db.update_mission_results(mission_id, final_results)
            
            # Update user balance if user exists
            if user:
                new_balance = user.get('bank_balance', 0) + economics.get('net_profit', 0)
                try:
                    from bson import ObjectId
                    self.db.db.users.update_one(
                        {"_id": ObjectId(user['_id'])},
                        {"$set": {"bank_balance": new_balance}}
                    )
                    print(f"   💳 User {user_id} balance updated: ${user.get('bank_balance', 0):,.2f} → ${new_balance:,.2f}")
                except Exception as e:
                    print(f"   ⚠️  Error updating user balance: {e}")
            
            # Add settlement event
            settlement_event = MissionEvent(
                day=mission.get('current_day', 0),
                event_type="economic_settlement",
                description=f"Mission completed: Cargo sold, investors repaid (${total_repayment:,.2f}), net profit: ${economics.get('net_profit', 0):,.2f}",
                impact_days=0,
                cost=0
            )
            await self.db.add_mission_event(mission_id, settlement_event)
            
            print(f"   💰 Mission {mission_id} economic settlement complete:")
            print(f"      Total Costs: ${final_results['total_costs']:,.2f}")
            print(f"      Principal: ${principal_amount:,.2f}")
            print(f"      Interest ({final_results['interest_rate']*100:.1f}%): ${interest_amount:,.2f}")
            print(f"      Total Repayment: ${total_repayment:,.2f}")
            print(f"      Ship Repair: ${final_results['ship_repair_cost']:,.2f}")
            print(f"      Cargo Value: ${final_results['cargo_value']:,.2f}")
            print(f"      Net Profit: ${final_results['net_profit']:,.2f}")
            print(f"      ROI: {final_results['roi_percentage']:.1f}%")
            
        except Exception as e:
            print(f"   ⚠️  Error using enhanced economics service, falling back to basic calculation: {e}")
            # Fallback to basic calculation if enhanced service fails
            total_costs = mission.get('costs', {}).get('total', 0)
            daily_interest_rate = 0.15 / 365
            mission_duration_days = mission.get('total_days', 0) or 224
            interest_amount = total_costs * daily_interest_rate * mission_duration_days
            total_repayment = total_costs + interest_amount
            
            hull_damage = mission.get('hull_damage', 0) or 0
            ship_repair_cost = min(hull_damage * 1000000, 25000000)
            
            cargo = mission.get('cargo', {})
            cargo_value = self.calculate_cargo_value(cargo)
            net_profit = cargo_value - total_costs - total_repayment - ship_repair_cost
            
            final_results = {
                'mission_complete': True,
                'total_costs': total_costs,
                'investor_repayment': total_repayment,
                'interest_paid': interest_amount,
                'ship_repair_cost': ship_repair_cost,
                'hull_damage': hull_damage,
                'cargo_value': cargo_value,
                'net_profit': net_profit,
                'roi_percentage': (net_profit / total_costs * 100) if total_costs > 0 else 0
            }
            
            await self.db.update_mission_results(mission_id, final_results)
    
    def calculate_cargo_value(self, cargo):
        """Calculate the market value of cargo using real commodity pricing"""
        total_value = 0
        
        # Use commodity pricing service for real market prices
        prices_per_kg = self.pricing_service.get_commodity_prices_per_kg()
        
        # Fallback prices for elements not in pricing service
        fallback_prices = {
            'Lithium': 15,        # $15/kg
            'Cobalt': 80          # $80/kg
        }
        
        for element, amount in cargo.items():
            # Try to get price from pricing service
            price = prices_per_kg.get(element, 0)
            
            # If not found, try fallback
            if price == 0:
                price = fallback_prices.get(element, 0)
            
            total_value += amount * price
        
        return total_value

# Database Manager for Complete System
class DatabaseManager:
    """Database manager for complete asteroid mining system"""
    
    def __init__(self):
        self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        self.db = self.client.asteroids
        
        # Test connection
        try:
            self.client.admin.command('ping')
            print("✅ MongoDB connection successful")
        except ConnectionFailure:
            print("❌ MongoDB connection failed")
            raise
        
        # Initialize loans collection indexes
        try:
            self.db.loans.create_index([("mission_id", 1)])
            self.db.loans.create_index([("user_id", 1)])
            self.db.loans.create_index([("status", 1)])
            print("✅ Loans collection indexes created")
        except Exception as e:
            print(f"⚠️  Warning: Could not create loans indexes: {e}")
    
    # Configuration and Events
    async def get_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        try:
            config = self.db.config.find_one()
            if config:
                config["_id"] = str(config["_id"])
                return config
            else:
                raise HTTPException(status_code=500, detail="System configuration not found")
        except Exception as e:
            print(f"Error getting config: {e}")
            raise HTTPException(status_code=500, detail="Failed to get configuration")
    
    async def get_events(self) -> List[Dict[str, Any]]:
        """Get all simulation events"""
        try:
            events = list(self.db.events.find())
            for event in events:
                event["_id"] = str(event["_id"])
            return events
        except Exception as e:
            print(f"Error getting events: {e}")
            return []
    
    # World State Management
    async def get_world_state(self) -> Dict[str, Any]:
        """Get world simulation state"""
        try:
            state = self.db.world_state.find_one()
            if state:
                state["_id"] = str(state["_id"])
                return state
            else:
                raise HTTPException(status_code=500, detail="World state not found")
        except Exception as e:
            print(f"Error getting world state: {e}")
            raise HTTPException(status_code=500, detail="Failed to get world state")
    
    async def update_world_state(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update world simulation state"""
        try:
            update_data = {k: v for k, v in state_data.items() if k != "_id"}
            update_data["last_updated"] = datetime.now(timezone.utc)
            
            result = self.db.world_state.update_one(
                {"simulation_id": state_data["simulation_id"]},
                {"$set": update_data},
                upsert=True
            )
            
            if result.upserted_id:
                state_data["_id"] = str(result.upserted_id)
            
            return state_data
        except Exception as e:
            print(f"Error updating world state: {e}")
            raise HTTPException(status_code=500, detail="Failed to update world state")
    
    # User Management
    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            users = list(self.db.users.find())
            for user in users:
                user["_id"] = str(user["_id"])
            return users
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user"""
        try:
            user_dict = user_data.dict()
            user_dict["created_at"] = datetime.now(timezone.utc)
            user_dict["last_login"] = datetime.now(timezone.utc)
            
            result = self.db.users.insert_one(user_dict)
            user_dict["_id"] = str(result.inserted_id)
            return user_dict
        except Exception as e:
            print(f"Error creating user: {e}")
            raise HTTPException(status_code=500, detail="Failed to create user")
    
    # Ship Management
    async def get_ships(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get ships, optionally filtered by user"""
        try:
            filter_query = {"user_id": user_id} if user_id else {}
            ships = list(self.db.ships.find(filter_query))
            
            normalized_ships = []
            for ship in ships:
                ship["_id"] = str(ship["_id"])
                
                # Normalize ship data to match Ship model schema
                normalized_ship = {
                    "_id": ship["_id"],
                    "name": ship.get("name", "Unnamed Ship"),
                    "user_id": ship.get("user_id", ""),
                    "capacity": ship.get("max_cargo_capacity", ship.get("capacity", ship.get("capacity_kg", 50000))),
                    "capacity_kg": ship.get("max_cargo_capacity", ship.get("capacity", ship.get("capacity_kg", 50000))),
                    "mining_power": ship.get("mining_power", 50),
                    "shield": ship.get("shield", 100),
                    "hull": ship.get("hull_integrity", ship.get("hull", 100)),
                    "power_systems": ship.get("power_systems", 100),
                    "status": "available" if ship.get("status") in ["idle", "available"] else ship.get("status", "available"),
                    "location": ship.get("location", "earth"),
                    "current_cargo": ship.get("current_cargo_mass", ship.get("current_cargo", 0)),
                    "cargo_composition": ship.get("cargo_composition") or (ship.get("cargo", {}) if isinstance(ship.get("cargo"), dict) else {}),
                    "created_at": ship.get("created_at", datetime.now(timezone.utc)),
                    "updated_at": ship.get("updated_at", datetime.now(timezone.utc))
                }
                
                # Scale mining_power if it's less than 10 (likely stored as 0-10 instead of 0-100)
                if normalized_ship["mining_power"] < 10:
                    normalized_ship["mining_power"] = normalized_ship["mining_power"] * 10
                
                normalized_ships.append(normalized_ship)
            
            return normalized_ships
        except Exception as e:
            print(f"Error getting ships: {e}")
            return []
    
    async def get_ship(self, ship_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific ship"""
        try:
            from bson import ObjectId
            ship = self.db.ships.find_one({"_id": ObjectId(ship_id)})
            if ship:
                ship["_id"] = str(ship["_id"])
                
                # Normalize ship data to match Ship model schema
                normalized_ship = {
                    "_id": ship["_id"],
                    "name": ship.get("name", "Unnamed Ship"),
                    "user_id": ship.get("user_id", ""),
                    "capacity": ship.get("max_cargo_capacity", ship.get("capacity", ship.get("capacity_kg", 50000))),
                    "capacity_kg": ship.get("max_cargo_capacity", ship.get("capacity", ship.get("capacity_kg", 50000))),
                    "mining_power": ship.get("mining_power", 50),
                    "shield": ship.get("shield", 100),
                    "hull": ship.get("hull_integrity", ship.get("hull", 100)),
                    "power_systems": ship.get("power_systems", 100),
                    "status": "available" if ship.get("status") in ["idle", "available"] else ship.get("status", "available"),
                    "location": ship.get("location", "earth"),
                    "current_cargo": ship.get("current_cargo_mass", ship.get("current_cargo", 0)),
                    "cargo_composition": ship.get("cargo_composition") or (ship.get("cargo", {}) if isinstance(ship.get("cargo"), dict) else {}),
                    "created_at": ship.get("created_at", datetime.now(timezone.utc)),
                    "updated_at": ship.get("updated_at", datetime.now(timezone.utc))
                }
                
                # Scale mining_power if it's less than 10
                if normalized_ship["mining_power"] < 10:
                    normalized_ship["mining_power"] = normalized_ship["mining_power"] * 10
                
                return normalized_ship
            return None
        except Exception as e:
            print(f"Error getting ship: {e}")
            return None
    
    async def update_ship_veteran_status(self, ship_id: str, veteran_status: bool) -> bool:
        """Update ship veteran status and bonus"""
        try:
            from bson import ObjectId
            veteran_bonus = 0.15 if veteran_status else 0.0
            result = self.db.ships.update_one(
                {"_id": ObjectId(ship_id)},
                {"$set": {
                    "veteran_status": veteran_status,
                    "veteran_bonus": veteran_bonus,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating ship veteran status: {e}")
            return False
    
    async def create_ship(self, ship_data: ShipCreate) -> Dict[str, Any]:
        """Create a new ship"""
        try:
            ship_dict = ship_data.dict()
            ship_dict["created_at"] = datetime.now(timezone.utc)
            ship_dict["updated_at"] = datetime.now(timezone.utc)
            ship_dict["status"] = "available"
            ship_dict["location"] = "earth"
            ship_dict["current_cargo"] = 0
            ship_dict["cargo_composition"] = {}
            ship_dict["missions_completed"] = 0
            ship_dict["total_distance_traveled"] = 0
            ship_dict["hull_damage"] = 0
            ship_dict["last_maintenance"] = datetime.now(timezone.utc)
            ship_dict["veteran_status"] = False
            ship_dict["veteran_bonus"] = 0.0  # 15% bonus for veteran ships
            
            result = self.db.ships.insert_one(ship_dict)
            ship_dict["_id"] = str(result.inserted_id)
            return ship_dict
        except Exception as e:
            print(f"Error creating ship: {e}")
            raise HTTPException(status_code=500, detail="Failed to create ship")
    
    # Mission Management
    async def get_missions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get missions, optionally filtered by user"""
        try:
            filter_query = {"user_id": user_id} if user_id else {}
            missions = list(self.db.missions.find(filter_query))
            
            normalized_missions = []
            for mission in missions:
                mission["_id"] = str(mission["_id"])
                
                # Normalize mission data to match Mission Pydantic model
                moid_days = mission.get("asteroid_moid_days", mission.get("travel_days", 0))
                # Convert to float if it's a number
                if isinstance(moid_days, (int, float)):
                    moid_days = float(moid_days)
                else:
                    moid_days = 0.0
                
                normalized = {
                    "_id": mission["_id"],
                    "name": mission.get("name", "Unnamed Mission"),
                    "user_id": mission.get("user_id", ""),
                    "ship_id": mission.get("ship_id", ""),
                    "asteroid_id": mission.get("asteroid_id", mission.get("target_asteroid_id", "")),
                    "asteroid_name": mission.get("asteroid_name", mission.get("target_asteroid_name", "")),
                    "asteroid_moid_days": moid_days,
                    "budget": mission.get("budget", 0),
                    "loan_id": mission.get("loan_id"),
                    "description": mission.get("description"),
                    "status": mission.get("status", "planning"),
                    "launch_date": mission.get("launch_date", datetime.now(timezone.utc)),
                    "actual_launch_date": mission.get("actual_launch_date"),
                    "current_phase": mission.get("current_phase", "planning"),
                    "current_day": mission.get("current_day", 0),
                    "total_days": mission.get("total_days", 0),
                    "costs": mission.get("costs", {"ground_control": 0, "launch_scrubs": 0, "space_events": 0, "total": 0}),
                    "events": mission.get("events", []),
                    "created_at": mission.get("created_at", datetime.now(timezone.utc)),
                    "updated_at": mission.get("updated_at", datetime.now(timezone.utc))
                }
                normalized_missions.append(normalized)
            
            return normalized_missions
        except Exception as e:
            print(f"Error getting missions: {e}")
            return []
    
    async def create_mission(self, mission_data: MissionCreate) -> Dict[str, Any]:
        """Create a new mission"""
        try:
            mission_dict = mission_data.model_dump(exclude_none=True)
            
            # Get asteroid details if asteroid_id is provided
            if mission_dict.get('asteroid_id') and not mission_dict.get('asteroid_name'):
                asteroid = await self.get_asteroid(mission_dict['asteroid_id'])
                if asteroid:
                    mission_dict['asteroid_name'] = asteroid.get('name', 'Unknown')
                    moid_au = asteroid.get('moid', 0.1)
                    # Calculate travel time for moid_days
                    from src.services.orbital_mechanics import OrbitalMechanicsService
                    orbital_service = OrbitalMechanicsService()
                    travel_data = orbital_service.calculate_travel_time(moid_au, 'mining_mission')
                    mission_dict['asteroid_moid_days'] = travel_data.get('total_time_days', 0)
            
            mission_dict["created_at"] = datetime.now(timezone.utc)
            mission_dict["updated_at"] = datetime.now(timezone.utc)
            mission_dict["status"] = "planning"
            mission_dict["current_phase"] = "planning"
            mission_dict["auto_progress"] = True  # Default to auto-progress
            mission_dict["current_day"] = 0
            mission_dict["total_days"] = 0
            mission_dict["launch_date"] = datetime.now(timezone.utc) + timedelta(days=7)  # Default launch in 7 days
            mission_dict["actual_launch_date"] = None
            mission_dict["costs"] = {
                "ground_control": 0,
                "launch_scrubs": 0,
                "space_events": 0,
                "total": 0
            }
            mission_dict["events"] = []
            mission_dict["launch_scrubs"] = 0  # Track number of launch scrubs
            
            result = self.db.missions.insert_one(mission_dict)
            mission_id = str(result.inserted_id)
            
            # Return normalized mission matching Pydantic model
            moid_days = mission_dict.get("asteroid_moid_days")
            if moid_days is not None:
                moid_days = float(moid_days) if isinstance(moid_days, (int, float)) else 0.0
            else:
                moid_days = 0.0
            
            return {
                "_id": mission_id,
                "name": mission_dict.get("name", "Unnamed Mission"),
                "user_id": mission_dict.get("user_id", ""),
                "ship_id": mission_dict.get("ship_id", ""),
                "asteroid_id": mission_dict.get("asteroid_id", ""),
                "asteroid_name": mission_dict.get("asteroid_name", ""),
                "asteroid_moid_days": moid_days,
                "budget": mission_dict.get("budget", 0),
                "loan_id": mission_dict.get("loan_id"),
                "description": mission_dict.get("description"),
                "status": mission_dict.get("status", "planning"),
                "launch_date": mission_dict.get("launch_date"),
                "actual_launch_date": mission_dict.get("actual_launch_date"),
                "current_phase": mission_dict.get("current_phase", "planning"),
                "current_day": mission_dict.get("current_day", 0),
                "total_days": mission_dict.get("total_days", 0),
                "costs": mission_dict.get("costs", {"ground_control": 0, "launch_scrubs": 0, "space_events": 0, "total": 0}),
                "events": mission_dict.get("events", []),
                "created_at": mission_dict.get("created_at"),
                "updated_at": mission_dict.get("updated_at")
            }
        except Exception as e:
            print(f"Error creating mission: {e}")
            raise HTTPException(status_code=500, detail="Failed to create mission")
    
    async def get_active_missions(self) -> List[Dict[str, Any]]:
        """Get all active missions"""
        try:
            missions = list(self.db.missions.find({"status": {"$in": ["launched", "traveling", "mining", "returning"]}}))
            for mission in missions:
                mission["_id"] = str(mission["_id"])
            return missions
        except Exception as e:
            print(f"Error getting active missions: {e}")
            return []
    
    async def get_mission(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific mission"""
        try:
            from bson import ObjectId
            mission = self.db.missions.find_one({"_id": ObjectId(mission_id)})
            if mission:
                mission["_id"] = str(mission["_id"])
            return mission
        except Exception as e:
            print(f"Error getting mission: {e}")
            return None
    
    async def add_mission_event(self, mission_id: str, event: MissionEvent) -> bool:
        """Add an event to a mission"""
        try:
            event_dict = event.dict()
            result = self.db.missions.update_one(
                {"_id": mission_id},
                {"$push": {"events": event_dict}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding mission event: {e}")
            return False
    
    async def update_mission_timestamp(self, mission_id: str) -> bool:
        """Update mission timestamp"""
        try:
            result = self.db.missions.update_one(
                {"_id": mission_id},
                {"$set": {"updated_at": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating mission timestamp: {e}")
            return False
    
    async def update_mission_phase(self, mission_id: str, new_phase: str, reset_day: int = 0) -> bool:
        """Update mission phase"""
        try:
            from bson import ObjectId
            result = self.db.missions.update_one(
                {"_id": ObjectId(mission_id)},
                {"$set": {
                    "current_phase": new_phase,
                    "current_day": reset_day,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            print(f"      🔄 Phase update result: {result.modified_count} documents modified")
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating mission phase: {e}")
            return False
    
    async def complete_mission(self, mission_id: str) -> bool:
        """Mark mission as completed"""
        try:
            result = self.db.missions.update_one(
                {"_id": mission_id},
                {"$set": {
                    "status": "completed",
                    "current_phase": "completed",
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error completing mission: {e}")
            return False
    
    async def increment_mission_day(self, mission_id: str) -> bool:
        """Increment the current day counter for a mission"""
        try:
            from bson import ObjectId
            result = self.db.missions.update_one(
                {"_id": ObjectId(mission_id)},
                {"$inc": {"current_day": 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error incrementing mission day: {e}")
            return False
    
    async def update_mission_cargo(self, mission_id: str, cargo: Dict[str, float]) -> bool:
        """Update mission cargo"""
        try:
            from bson import ObjectId
            result = self.db.missions.update_one(
                {"_id": ObjectId(mission_id)},
                {"$set": {"cargo": cargo}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating mission cargo: {e}")
            return False
    
    async def update_mission_results(self, mission_id: str, results: Dict[str, Any]) -> bool:
        """Update mission with final results"""
        try:
            from bson import ObjectId
            result = self.db.missions.update_one(
                {"_id": ObjectId(mission_id)},
                {"$set": {"final_results": results}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating mission results: {e}")
            return False

    async def update_mission_fields(self, mission_id: str, fields: Dict[str, Any]) -> bool:
        """Generic mission field updater (uses $set)"""
        try:
            from bson import ObjectId
            update_doc = {"$set": {**fields, "updated_at": datetime.now(timezone.utc)}}
            result = self.db.missions.update_one({"_id": ObjectId(mission_id)}, update_doc)
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating mission fields: {e}")
            return False
    
    async def get_asteroid(self, asteroid_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific asteroid"""
        try:
            from bson import ObjectId
            asteroid = self.db.asteroids.find_one({"_id": ObjectId(asteroid_id)})
            if asteroid:
                asteroid["_id"] = str(asteroid["_id"])
            return asteroid
        except Exception as e:
            print(f"Error getting asteroid: {e}")
            return None
    
    # Asteroid and Element Data
    async def get_asteroids(self, limit: int = 10, skip: int = 0) -> Dict[str, Any]:
        """Get asteroids from the database"""
        try:
            total = self.db.asteroids.count_documents({})
            asteroids = list(self.db.asteroids.find().skip(skip).limit(limit))
            
            # Convert ObjectIds to strings
            for asteroid in asteroids:
                asteroid["_id"] = str(asteroid["_id"])
            
            return {
                "asteroids": asteroids,
                "total": total,
                "limit": limit,
                "skip": skip
            }
        except Exception as e:
            print(f"Error getting asteroids: {e}")
            return {"asteroids": [], "total": 0, "limit": limit, "skip": skip}
    
    async def get_elements(self) -> Dict[str, Any]:
        """Get chemical elements from the database"""
        try:
            elements = list(self.db.elements.find())
            total = len(elements)
            
            # Convert ObjectIds to strings
            for element in elements:
                element["_id"] = str(element["_id"])
            
            return {
                "elements": elements,
                "total": total
            }
        except Exception as e:
            print(f"Error getting elements: {e}")
            return {"elements": [], "total": 0}

# FastAPI App
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    print("🚀 Starting AstroSurge Complete Mission Lifecycle System...")
    yield
    print("🛑 Shutting down AstroSurge Complete Mission Lifecycle System...")

app = FastAPI(
    title="AstroSurge Complete Mission Lifecycle API",
    description="Asteroid Mining Operation Simulator - Complete Mission Lifecycle System",
    version="4.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global simulation engine
simulation_engine = None

# Database dependency
async def get_db() -> DatabaseManager:
    return DatabaseManager()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "4.0.0",
        "database": "connected",
        "simulation_engine": "initialized" if simulation_engine else "not_initialized"
    }

# Configuration and Events
@app.get("/api/config")
async def get_config(db: DatabaseManager = Depends(get_db)):
    """Get system configuration"""
    return await db.get_config()

@app.get("/api/events")
async def get_events(db: DatabaseManager = Depends(get_db)):
    """Get all simulation events"""
    return await db.get_events()

# World Simulation Control
@app.get("/api/world/status")
async def get_world_status(db: DatabaseManager = Depends(get_db)):
    """Get world simulation status"""
    return await db.get_world_state()

@app.post("/api/world/start")
async def start_world_simulation(background_tasks: BackgroundTasks, db: DatabaseManager = Depends(get_db)):
    """Start the world simulation"""
    global simulation_engine
    
    try:
        # Initialize simulation engine if not already done
        if not simulation_engine:
            simulation_engine = WorldSimulationEngine(db)
            await simulation_engine.initialize()
        
        # Update world state to running
        world_state = await db.get_world_state()
        world_state["status"] = "running"
        await db.update_world_state(world_state)
        
        # Start background simulation loop
        background_tasks.add_task(run_simulation_loop, db)
        
        return {"status": "started", "message": "World simulation started successfully"}
    except Exception as e:
        print(f"Error starting world simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start world simulation")

@app.post("/api/world/stop")
async def stop_world_simulation(db: DatabaseManager = Depends(get_db)):
    """Stop the world simulation"""
    try:
        world_state = await db.get_world_state()
        world_state["status"] = "stopped"
        await db.update_world_state(world_state)
        
        return {"status": "stopped", "message": "World simulation stopped successfully"}
    except Exception as e:
        print(f"Error stopping world simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop world simulation")

@app.post("/api/world/tick")
async def advance_one_day(db: DatabaseManager = Depends(get_db)):
    """Advance simulation by one day"""
    global simulation_engine
    
    try:
        if not simulation_engine:
            simulation_engine = WorldSimulationEngine(db)
            await simulation_engine.initialize()
        
        await simulation_engine.process_daily_tick()
        
        return {"status": "advanced", "message": "Simulation advanced by one day"}
    except Exception as e:
        print(f"Error advancing simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to advance simulation")

# User Management
@app.get("/api/users", response_model=List[User])
async def get_users(db: DatabaseManager = Depends(get_db)):
    """Get all users"""
    users = await db.get_users()
    return users

@app.post("/api/users", response_model=User)
async def create_user(user: UserCreate, db: DatabaseManager = Depends(get_db)):
    """Create a new user"""
    new_user = await db.create_user(user)
    return new_user

# Ship Management
@app.get("/api/ships", response_model=List[Ship])
async def get_ships(user_id: Optional[str] = None, db: DatabaseManager = Depends(get_db)):
    """Get ships, optionally filtered by user"""
    ships = await db.get_ships(user_id)
    return ships

@app.post("/api/ships", response_model=Ship)
async def create_ship(ship: ShipCreate, db: DatabaseManager = Depends(get_db)):
    """Create a new ship"""
    new_ship = await db.create_ship(ship)
    return new_ship

@app.put("/api/ships/{ship_id}/veteran")
async def update_ship_veteran_status(ship_id: str, veteran_status: bool, db: DatabaseManager = Depends(get_db)):
    """Update ship veteran status"""
    success = await db.update_ship_veteran_status(ship_id, veteran_status)
    if not success:
        raise HTTPException(status_code=404, detail="Ship not found or update failed")
    return {"message": f"Ship veteran status updated to {veteran_status}"}

@app.get("/api/ships/catalog")
async def get_ship_catalog():
    """Get predefined ship catalog models"""
    return [
        {
            "name": "Mining Vessel Alpha",
            "capacity": 50000,
            "mining_power": 75,
            "shield": 100,
            "hull": 100,
            "power_systems": 100,
            "base_cost": 150000000,
            "description": "Standard mining vessel with good capacity and efficiency"
        },
        {
            "name": "Heavy Miner Gamma",
            "capacity": 75000,
            "mining_power": 85,
            "shield": 100,
            "hull": 100,
            "power_systems": 100,
            "base_cost": 250000000,
            "description": "High-capacity mining vessel with superior efficiency"
        },
        {
            "name": "Explorer Beta",
            "capacity": 35000,
            "mining_power": 60,
            "shield": 100,
            "hull": 100,
            "power_systems": 100,
            "base_cost": 100000000,
            "description": "Lightweight explorer vessel for shorter missions"
        },
        {
            "name": "Industrial Miner Omega",
            "capacity": 100000,
            "mining_power": 90,
            "shield": 100,
            "hull": 100,
            "power_systems": 100,
            "base_cost": 400000000,
            "description": "Maximum capacity industrial mining vessel"
        }
    ]

@app.post("/api/ships/purchase")
async def purchase_ship(ship_data: ShipCreate, db: DatabaseManager = Depends(get_db)):
    """Purchase a new ship from catalog"""
    try:
        ship = await db.create_ship(ship_data)
        return ship
    except Exception as e:
        print(f"Error purchasing ship: {e}")
        raise HTTPException(status_code=500, detail="Failed to purchase ship")

# Financing Models
class LoanBase(BaseModel):
    principal: float = Field(..., description="Loan principal amount")
    apr: float = Field(..., description="Annual percentage rate")
    term_days: int = Field(..., description="Loan term in days")
    user_id: str = Field(..., description="User ID")
    mission_id: Optional[str] = Field(None, description="Linked mission ID")

class LoanCreate(LoanBase):
    pass

class Loan(LoanBase):
    id: str = Field(..., alias="_id")
    status: str = Field(..., description="Loan status: open, repaid, defaulted")
    payoff_amount: float = Field(..., description="Total payoff amount")
    created_at: datetime
    repaid_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True

@app.get("/api/financing/options")
async def get_financing_options():
    """Get default financing options and constraints"""
    return {
        "default_apr": 8.0,
        "min_principal": 1000,
        "max_principal": 1000000000,
        "min_apr": 0.0,
        "max_apr": 100.0,
        "min_term_days": 1,
        "max_term_days": 3650
    }

@app.get("/api/financing/calculate")
async def calculate_financing_needs(
    ship_id: Optional[str] = None,
    ship_to_purchase: Optional[str] = None,
    asteroid_id: Optional[str] = None,
    db: DatabaseManager = Depends(get_db)
):
    """Calculate financing needs based on mission costs, ship costs, repairs, and estimated profit"""
    try:
        from src.services.orbital_mechanics import OrbitalMechanicsService
        from src.services.commodity_pricing_standalone import CommodityPricingService
        import os
        
        # Get ship information
        ship_cost = 0
        ship = None
        if ship_to_purchase:
            # Parse ship catalog data if provided as JSON string
            try:
                import json
                ship_data = json.loads(ship_to_purchase) if isinstance(ship_to_purchase, str) else ship_to_purchase
                ship_cost = ship_data.get('base_cost', 0)
            except:
                pass
        elif ship_id:
            ship = await db.get_ship(ship_id)
            if not ship:
                raise HTTPException(status_code=404, detail="Ship not found")
        
        # Get asteroid information
        if not asteroid_id:
            raise HTTPException(status_code=400, detail="asteroid_id is required")
        
        asteroid = await db.get_asteroid(asteroid_id)
        if not asteroid:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        # Calculate travel time
        moid_au = asteroid.get('moid', 0.1)
        orbital_service = OrbitalMechanicsService()
        travel_data = orbital_service.calculate_travel_time(moid_au, 'mining_mission')
        total_travel_days = travel_data.get('total_time_days', 0)
        
        # Estimate mining time (34 days to fill capacity)
        ship_capacity = ship.get('capacity', ship.get('capacity_kg', 50000)) if ship else 50000
        mining_days = min(34, int(ship_capacity / 1500))  # 1500 kg/day max
        
        # Total mission duration
        total_mission_days = total_travel_days + mining_days
        
        # Calculate mission operational costs
        config = await db.get_config()
        ground_control_cost_per_day = config.get('ground_control_cost_per_day', 75000)
        operations_cost_per_day = config.get('operation_cost_per_day', 50000)
        launch_scrub_cost = config.get('launch_scrub_cost', 500000)
        
        # Estimate some launch scrubs (1-3 scrubs on average)
        estimated_scrubs = 1.5
        launch_scrub_costs = launch_scrub_cost * estimated_scrubs
        
        ground_control_costs = ground_control_cost_per_day * total_mission_days
        operations_costs = operations_cost_per_day * total_mission_days
        mission_operational_costs = ground_control_costs + operations_costs + launch_scrub_costs
        
        # Estimate ship repair costs (average 10-15% hull damage, max $25M)
        # Use average of 12% damage = 12 damage points = $12M, capped at $25M
        estimated_hull_damage = 12  # Average damage points
        repair_cost_per_damage = 1000000  # $1M per damage point
        estimated_repair_cost = min(estimated_hull_damage * repair_cost_per_damage, 25000000)
        
        # Calculate estimated cargo value
        mongodb_uri = os.getenv("MONGODB_URI")
        pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        prices_per_kg = pricing_service.get_commodity_prices_per_kg()
        
        # Estimate cargo composition based on asteroid class
        asteroid_class = asteroid.get('class', 'C')
        estimated_cargo_kg = ship_capacity * 0.7  # Assume 70% capacity fill
        
        # Estimate revenue based on asteroid class
        estimated_revenue = 0
        if asteroid_class == 'C':
            # C-type: mostly common elements
            avg_price = prices_per_kg.get('Copper', 9.0) * 0.5 + prices_per_kg.get('Iron', 0.1) * 0.3
            estimated_revenue = estimated_cargo_kg * avg_price
        elif asteroid_class == 'S':
            # S-type: more valuable elements
            avg_price = prices_per_kg.get('Silver', 881.85) * 0.3 + prices_per_kg.get('Copper', 9.0) * 0.4
            estimated_revenue = estimated_cargo_kg * avg_price
        elif asteroid_class == 'M':
            # M-type: most valuable
            avg_price = prices_per_kg.get('Platinum', 35274.0) * 0.2 + prices_per_kg.get('Gold', 70548.0) * 0.15
            estimated_revenue = estimated_cargo_kg * avg_price
        else:
            # Default fallback
            avg_price = sum(prices_per_kg.values()) / len(prices_per_kg) if prices_per_kg else 20000
            estimated_revenue = estimated_cargo_kg * avg_price * 0.5
        
        # Calculate total costs
        total_costs = ship_cost + mission_operational_costs + estimated_repair_cost
        
        # Calculate financing need
        financing_need = total_costs - estimated_revenue
        needs_financing = financing_need > 0
        loan_principal = max(0, financing_need) if needs_financing else 0
        
        # Get default APR
        default_apr = 8.0
        
        # Calculate loan payoff if financing is needed
        loan_payoff = 0
        loan_interest = 0
        if loan_principal > 0:
            loan_interest = loan_principal * (default_apr / 100) * (total_mission_days / 365)
            loan_payoff = loan_principal + loan_interest
        
        return {
            "ship_cost": ship_cost,
            "mission_operational_costs": mission_operational_costs,
            "estimated_repair_cost": estimated_repair_cost,
            "total_costs": total_costs,
            "estimated_revenue": estimated_revenue,
            "estimated_profit": estimated_revenue - total_costs,
            "needs_financing": needs_financing,
            "loan_principal": loan_principal,
            "loan_apr": default_apr,
            "loan_term_days": total_mission_days,
            "loan_interest": loan_interest,
            "loan_payoff": loan_payoff,
            "mission_duration_days": total_mission_days,
            "breakdown": {
                "ground_control": ground_control_costs,
                "operations": operations_costs,
                "launch_scrubs": launch_scrub_costs,
                "ship_repair": estimated_repair_cost
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error calculating financing needs: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate financing needs")

@app.post("/api/financing/loans", response_model=Loan)
async def create_loan(loan_data: LoanCreate, db: DatabaseManager = Depends(get_db)):
    """Create a new loan"""
    try:
        from bson import ObjectId
        from datetime import datetime, timezone
        
        # Calculate payoff amount using simple interest: payoff = principal * (1 + apr * term_days/365)
        payoff_amount = loan_data.principal * (1 + (loan_data.apr / 100) * (loan_data.term_days / 365))
        
        loan_dict = {
            "principal": loan_data.principal,
            "apr": loan_data.apr,
            "term_days": loan_data.term_days,
            "user_id": loan_data.user_id,
            "mission_id": loan_data.mission_id,
            "status": "open",
            "payoff_amount": payoff_amount,
            "created_at": datetime.now(timezone.utc),
            "repaid_at": None
        }
        
        result = db.db.loans.insert_one(loan_dict)
        loan_dict["_id"] = str(result.inserted_id)
        return loan_dict
    except Exception as e:
        print(f"Error creating loan: {e}")
        raise HTTPException(status_code=500, detail="Failed to create loan")

@app.patch("/api/financing/loans/{loan_id}/link-mission")
async def link_loan_to_mission(loan_id: str, body: dict, db: DatabaseManager = Depends(get_db)):
    """Link a loan to a mission"""
    try:
        from bson import ObjectId
        from datetime import datetime, timezone
        
        mission_id = body.get("mission_id")
        if not mission_id:
            raise HTTPException(status_code=400, detail="mission_id is required")
        
        result = db.db.loans.update_one(
            {"_id": ObjectId(loan_id)},
            {"$set": {"mission_id": mission_id, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        return {"status": "linked", "message": "Loan linked to mission"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error linking loan: {e}")
        raise HTTPException(status_code=500, detail="Failed to link loan to mission")

# Mission Management
@app.get("/api/missions", response_model=List[Mission])
async def get_missions(user_id: Optional[str] = None, db: DatabaseManager = Depends(get_db)):
    """Get missions, optionally filtered by user"""
    missions = await db.get_missions(user_id)
    return missions

@app.post("/api/missions", response_model=Mission)
async def create_mission(mission: MissionCreate, db: DatabaseManager = Depends(get_db)):
    """Create a new mission"""
    new_mission = await db.create_mission(mission)
    return new_mission

@app.get("/api/missions/budget-estimate")
async def get_budget_estimate(ship_id: str, asteroid_id: str, db: DatabaseManager = Depends(get_db)):
    """Calculate estimated budget and ROI for a mission"""
    try:
        # Get ship and asteroid
        ship = await db.get_ship(ship_id)
        asteroid = await db.get_asteroid(asteroid_id)
        
        if not ship or not asteroid:
            raise HTTPException(status_code=404, detail="Ship or asteroid not found")
        
        # Calculate travel time
        moid_au = asteroid.get('moid', 0.1)
        orbital_service = OrbitalMechanicsService()
        travel_data = orbital_service.calculate_travel_time(moid_au, 'mining_mission')
        
        # Ensure travel time is at least 1 day (round trip)
        total_travel_days = max(1, travel_data.get('total_time_days', 1))
        
        # Mining site setup time: 1-5 days (randomized)
        import random
        mining_setup_days = random.randint(1, 5)
        
        # Estimate mining time (34 days to fill capacity)
        ship_capacity = ship.get('capacity_kg', ship.get('capacity', 50000))
        mining_days = min(34, int(ship_capacity / 1500))  # 1500 kg/day max
        
        # Total mission duration includes: travel + setup + mining
        total_days = total_travel_days + mining_setup_days + mining_days
        
        # Estimate costs - use $45K per day minimum for operational costs
        config = await db.get_config()
        ground_control_cost_per_day = config.get('ground_control_cost_per_day', 75000)
        operations_cost_per_day = max(45000, config.get('operation_cost_per_day', 50000))  # Minimum $45K/day
        
        estimated_costs = {
            'ground_control': ground_control_cost_per_day * total_days,
            'operations': operations_cost_per_day * total_days,
            'total': (ground_control_cost_per_day + operations_cost_per_day) * total_days
        }
        
        # Estimate revenue (using commodity prices based on asteroid class)
        mongodb_uri = os.getenv("MONGODB_URI")
        pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        prices_per_kg = pricing_service.get_commodity_prices_per_kg()
        
        # Estimate cargo composition based on asteroid class
        asteroid_class = asteroid.get('class', 'C')
        estimated_cargo_kg = ship_capacity * 0.7  # Assume 70% capacity fill
        
        # Calculate estimated revenue based on asteroid class
        estimated_revenue = 0
        if asteroid_class == 'C':
            # C-type: mostly common elements
            avg_price = prices_per_kg.get('Copper', 9.0) * 0.5 + prices_per_kg.get('Iron', 0.1) * 0.3
            estimated_revenue = estimated_cargo_kg * avg_price
        elif asteroid_class == 'S':
            # S-type: more valuable elements
            avg_price = prices_per_kg.get('Silver', 881.85) * 0.3 + prices_per_kg.get('Copper', 9.0) * 0.4
            estimated_revenue = estimated_cargo_kg * avg_price
        elif asteroid_class == 'M':
            # M-type: most valuable
            avg_price = prices_per_kg.get('Platinum', 35274.0) * 0.2 + prices_per_kg.get('Gold', 70548.0) * 0.15
            estimated_revenue = estimated_cargo_kg * avg_price
        else:
            # Default fallback
            avg_price = sum(prices_per_kg.values()) / len(prices_per_kg) if prices_per_kg else 20000
            estimated_revenue = estimated_cargo_kg * avg_price * 0.5
        
        estimated_profit = estimated_revenue - estimated_costs['total']
        estimated_roi = (estimated_profit / estimated_costs['total'] * 100) if estimated_costs['total'] > 0 else 0
        
        return {
            'ship_id': ship_id,
            'asteroid_id': asteroid_id,
            'ship_capacity': ship_capacity,
            'travel_time_days': total_travel_days,
            'mining_setup_days': mining_setup_days,
            'mining_time_days': mining_days,
            'total_days': total_days,
            'estimated_costs': estimated_costs,
            'estimated_revenue': estimated_revenue,
            'estimated_profit': estimated_profit,
            'estimated_roi': estimated_roi
        }
    except Exception as e:
        print(f"Error calculating budget estimate: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate budget estimate")

@app.get("/api/missions/readiness")
async def check_mission_readiness(ship_id: str, asteroid_id: str, db: DatabaseManager = Depends(get_db)):
    """Check if mission is ready to launch"""
    try:
        ship = await db.get_ship(ship_id)
        asteroid = await db.get_asteroid(asteroid_id)
        
        return {
            'ship_available': ship is not None and ship.get('status') == 'available',
            'asteroid_accessible': asteroid is not None,
            'budget_sufficient': True  # TODO: Check user balance
        }
    except Exception as e:
        print(f"Error checking readiness: {e}")
        raise HTTPException(status_code=500, detail="Failed to check readiness")

@app.get("/api/missions/{mission_id}/results")
async def get_mission_results(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Get detailed mission results including daily events, phase history, and cargo/cost timelines"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Get final results if mission is completed
    final_results = mission.get('final_results', {})
    
    # Calculate current mission status and costs
    current_costs = mission.get('costs', {})
    current_phase = mission.get('current_phase', 'unknown')
    
    # Get all events and group by day
    events = mission.get('events', [])
    
    # Build phase history from events
    phase_history = []
    phase_transitions = []
    for event in events:
        if event.get('event_type') == 'phase_transition':
            phase_transitions.append({
                'day': event.get('current_day', event.get('day', 0)),
                'phase': event.get('description', '').split(' to ')[-1] if ' to ' in event.get('description', '') else current_phase,
                'timestamp': event.get('timestamp', mission.get('created_at'))
            })
    
    # Build cargo accumulation timeline from events
    cargo_timeline = []
    cargo_history = {}
    for event in events:
        day = event.get('current_day', event.get('day', 0))
        if 'cargo' in event or 'cargo_accumulated' in str(event.get('description', '')):
            cargo_weight = sum((event.get('cargo', {}) or {}).values())
            if cargo_weight > 0:
                cargo_history[day] = cargo_weight
                cargo_timeline.append({
                    'day': day,
                    'cargo_weight': cargo_weight,
                    'cargo_breakdown': event.get('cargo', {})
                })
    
    # Build cost accumulation timeline from events
    cost_timeline = []
    cost_history = {}
    running_total = 0
    for event in events:
        day = event.get('current_day', event.get('day', 0))
        event_cost = event.get('cost', 0) or 0
        if event_cost > 0:
            running_total += event_cost
            cost_history[day] = running_total
            cost_timeline.append({
                'day': day,
                'cost': event_cost,
                'running_total': running_total,
                'cost_type': event.get('event_type', 'unknown')
            })
    
    # Prepare comprehensive mission report
    mission_report = {
        'mission_id': mission_id,
        'name': mission.get('name', 'Unknown Mission'),
        'status': mission.get('status', 'unknown'),
        'current_phase': current_phase,
        'current_day': mission.get('current_day', 0),
        'total_days': mission.get('total_days', 0),
        'auto_progress': mission.get('auto_progress', True),
        'asteroid_name': mission.get('asteroid_name', 'Unknown'),
        'asteroid_class': mission.get('asteroid_class', 'C'),
        'ship_name': mission.get('ship_name', 'Unknown Ship'),
        'ship_capacity': mission.get('ship_capacity', 50000),
        'cargo': mission.get('cargo', {}),
        'cargo_weight': sum(mission.get('cargo', {}).values()),
        'costs': current_costs,
        'events': events,
        'daily_events': events,  # For backward compatibility
        'phase_history': phase_transitions if phase_transitions else [{'day': 0, 'phase': 'planning', 'timestamp': mission.get('created_at')}],
        'cargo_timeline': cargo_timeline,
        'cost_timeline': cost_timeline,
        'final_results': final_results,
        'created_at': mission.get('created_at'),
        'updated_at': mission.get('updated_at'),
        'economic_summary': {
            'total_investment': current_costs.get('total', 0),
            'cargo_value': final_results.get('cargo_value', 0),
            'investor_repayment': final_results.get('investor_repayment', 0),
            'interest_paid': final_results.get('interest_paid', 0),
            'ship_repair_cost': final_results.get('ship_repair_cost', 0),
            'net_profit': final_results.get('net_profit', 0),
            'roi_percentage': final_results.get('roi_percentage', 0)
        }
    }
    
    return mission_report

# Mission Control Endpoints
@app.get("/api/missions/{mission_id}/status")
async def get_mission_status(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Get current mission status with progression settings"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {
        "mission_id": mission_id,
        "status": mission.get("status"),
        "current_phase": mission.get("current_phase"),
        "current_day": mission.get("current_day", 0),
        "auto_progress": mission.get("auto_progress", True)
    }

@app.post("/api/missions/{mission_id}/launch")
async def launch_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Manually launch a mission if in launch_ready phase"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if mission.get("current_phase") not in ["launch_ready", "planning"]:
        raise HTTPException(status_code=400, detail="Mission not ready to launch")
    # Transition to launched
    await db.update_mission_phase(mission_id, "launched", 0)
    return {"status": "launched"}

@app.post("/api/missions/{mission_id}/pause")
async def pause_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Pause auto-progression for a mission"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    await db.update_mission_fields(mission_id, {"auto_progress": False})
    return {"status": "paused"}

@app.post("/api/missions/{mission_id}/resume")
async def resume_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Resume auto-progression for a mission"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    await db.update_mission_fields(mission_id, {"auto_progress": True})
    return {"status": "resumed"}

@app.post("/api/missions/{mission_id}/advance-day")
async def advance_mission_one_day(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Advance mission by one day when auto_progress is paused"""
    global simulation_engine
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if mission.get("auto_progress", True):
        raise HTTPException(status_code=400, detail="Pause mission before manual advance")
    if not simulation_engine:
        simulation_engine = WorldSimulationEngine(db)
        await simulation_engine.initialize()
    await simulation_engine.process_mission_day(mission, mission.get('current_day', 0))
    return {"status": "advanced"}

@app.post("/api/missions/{mission_id}/sell-cargo")
async def sell_mission_cargo(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Sell cargo and settle mission economics"""
    global simulation_engine
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    try:
        if not simulation_engine:
            simulation_engine = WorldSimulationEngine(db)
            await simulation_engine.initialize()
        # Calculate and persist results
        results = await simulation_engine.calculate_mission_results(mission_id)
        await db.update_mission_results(mission_id, results)
        await db.update_mission_phase(mission_id, "completed", mission.get('current_day', 0))
        return {"status": "settled", "results": results}
    except Exception as e:
        print(f"Error selling cargo: {e}")
        raise HTTPException(status_code=500, detail="Failed to sell cargo")

# Asteroid and Element Data
@app.get("/api/asteroids")
async def get_asteroids(limit: int = 10, skip: int = 0, db: DatabaseManager = Depends(get_db)):
    """Get asteroids from the database"""
    return await db.get_asteroids(limit, skip)

@app.get("/api/elements")
async def get_elements(db: DatabaseManager = Depends(get_db)):
    """Get chemical elements from the database"""
    return await db.get_elements()

# Enhanced Services API Endpoints
@app.get("/api/commodity-prices")
async def get_commodity_prices():
    """Get current commodity prices per kg using yfinance"""
    try:
        mongodb_uri = os.getenv("MONGODB_URI")
        pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        prices = pricing_service.get_commodity_prices_per_kg()
        summary = pricing_service.get_price_summary()
        return {
            "prices_per_kg": prices,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc)
        }
    except Exception as e:
        print(f"Error fetching commodity prices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch commodity prices")

@app.get("/api/asteroids/{asteroid_id}/details")
async def get_asteroid_details(asteroid_id: str, db: DatabaseManager = Depends(get_db)):
    """Get comprehensive asteroid details including estimated value"""
    try:
        from src.services.orbital_mechanics import OrbitalMechanicsService
        from src.services.commodity_pricing_standalone import CommodityPricingService
        import os
        
        asteroid = await db.get_asteroid(asteroid_id)
        if not asteroid:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        # Calculate travel time
        moid_au = asteroid.get('moid', 0.1)
        orbital_service = OrbitalMechanicsService()
        travel_data = orbital_service.calculate_travel_time(moid_au, 'mining_mission')
        
        # Get mining analysis
        engine = WorldSimulationEngine(db)
        mining_analysis = await engine.mining_service.get_mining_analysis(asteroid_id)
        
        # Calculate estimated value
        asteroid_class = asteroid.get('class', 'C')
        elements = asteroid.get('elements', [])
        
        # Get commodity prices
        mongodb_uri = os.getenv("MONGODB_URI")
        pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        prices_per_kg = pricing_service.get_commodity_prices_per_kg()
        
        # Calculate total estimated value from elements
        total_estimated_value = 0
        element_breakdown = []
        for element in elements:
            element_name = element.get('name', '')
            mass_kg = element.get('mass_kg', 0)
            price_per_kg = prices_per_kg.get(element_name, 0)
            element_value = mass_kg * price_per_kg
            total_estimated_value += element_value
            if element_value > 0:
                element_breakdown.append({
                    'name': element_name,
                    'mass_kg': mass_kg,
                    'price_per_kg': price_per_kg,
                    'value': element_value
                })
        
        # Sort by value descending
        element_breakdown.sort(key=lambda x: x['value'], reverse=True)
        
        return {
            "asteroid": {
                "_id": asteroid.get("_id"),
                "name": asteroid.get("name", asteroid.get("full_name", "Unknown")),
                "class": asteroid_class,
                "moid_au": moid_au,
                "diameter": asteroid.get("diameter", asteroid.get("size_km", 0)),
                "discovered": asteroid.get("discovered"),
                "risk_level": asteroid.get("risk_level", "medium"),
                "mining_difficulty": asteroid.get("mining_difficulty", "medium")
            },
            "travel": {
                "one_way_days": travel_data.get('one_way_time_days', 0),
                "total_days": travel_data.get('total_time_days', 0),
                "distance_au": moid_au
            },
            "mining": mining_analysis,
            "value": {
                "total_estimated_value": total_estimated_value,
                "element_breakdown": element_breakdown[:10],  # Top 10 most valuable elements
                "total_elements": len(elements)
            },
            "composition": {
                "total_mass_kg": sum(e.get('mass_kg', 0) for e in elements),
                "valuable_elements_count": len([e for e in elements if e.get('name') in prices_per_kg])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting asteroid details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get asteroid details")

@app.get("/api/asteroids/{asteroid_id}/mining-analysis")
async def get_asteroid_mining_analysis(asteroid_id: str, db: DatabaseManager = Depends(get_db)):
    """Get mining analysis for an asteroid based on its class"""
    try:
        # Get the world simulation engine's mining service
        engine = WorldSimulationEngine(db)
        analysis = await engine.mining_service.get_mining_analysis(asteroid_id)
        return analysis
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting mining analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get mining analysis: {str(e)}")

@app.get("/api/missions/{mission_id}/economics")
async def get_mission_economics(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Get comprehensive mission economics using enhanced service"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    try:
        economics_service = MissionEconomicsService()
        economics = await economics_service.calculate_comprehensive_mission_economics(mission_id)
        return economics
    except Exception as e:
        print(f"Error calculating mission economics: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate mission economics")

@app.get("/api/missions/{mission_id}/risk")
async def get_mission_risk(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Get mission risk assessment"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    try:
        economics_service = MissionEconomicsService()
        risk = await economics_service.calculate_mission_risk_assessment(mission_id)
        return risk
    except Exception as e:
        print(f"Error calculating mission risk: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate mission risk")

@app.get("/api/orbital/travel-time")
async def calculate_travel_time(moid_au: float, mission_type: str = "round_trip"):
    """Calculate travel time using orbital mechanics"""
    try:
        orbital_service = OrbitalMechanicsService()
        result = orbital_service.calculate_travel_time(moid_au, mission_type)
        return result
    except Exception as e:
        print(f"Error calculating travel time: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate travel time")

@app.get("/api/orbital/trajectory")
async def calculate_trajectory(moid_au: float, mission_type: str = "round_trip"):
    """Calculate detailed mission trajectory"""
    try:
        orbital_service = OrbitalMechanicsService()
        result = orbital_service.calculate_mission_trajectory(moid_au, mission_type)
        return result
    except Exception as e:
        print(f"Error calculating trajectory: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate trajectory")

@app.post("/api/missions/{mission_id}/launch")
async def launch_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Manually launch a mission (move from launch_ready to launched)"""
    global simulation_engine
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.get('current_phase') != 'launch_ready':
            raise HTTPException(status_code=400, detail=f"Mission is in {mission.get('current_phase')} phase, not ready to launch")
        
        # Update mission to launched phase
        await db.update_mission_phase(mission_id, "launched", 0)
        
        return {"status": "launched", "message": "Mission launched successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error launching mission: {e}")
        raise HTTPException(status_code=500, detail="Failed to launch mission")

@app.post("/api/missions/{mission_id}/pause")
async def pause_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Pause auto-progression for a mission"""
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Update mission auto_progress flag
        from bson import ObjectId
        db.db.missions.update_one(
            {"_id": ObjectId(mission_id)},
            {"$set": {"auto_progress": False}}
        )
        
        return {"status": "paused", "message": "Mission progression paused"}
    except Exception as e:
        print(f"Error pausing mission: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause mission")

@app.post("/api/missions/{mission_id}/resume")
async def resume_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Resume auto-progression for a mission"""
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Update mission auto_progress flag
        from bson import ObjectId
        db.db.missions.update_one(
            {"_id": ObjectId(mission_id)},
            {"$set": {"auto_progress": True}}
        )
        
        return {"status": "resumed", "message": "Mission progression resumed"}
    except Exception as e:
        print(f"Error resuming mission: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume mission")

@app.post("/api/missions/{mission_id}/advance-day")
async def advance_mission_day(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Manually advance a mission by one day"""
    global simulation_engine
    try:
        if not simulation_engine:
            simulation_engine = WorldSimulationEngine(db)
            await simulation_engine.initialize()
        
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.get('auto_progress', True):
            raise HTTPException(status_code=400, detail="Mission is set to auto-progress. Pause it first to advance manually.")
        
        # Process one day for this mission
        world_state = await db.get_world_state()
        await simulation_engine.process_mission_day(mission, world_state['current_day'])
        
        return {"status": "advanced", "message": "Mission advanced by one day"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error advancing mission: {e}")
        raise HTTPException(status_code=500, detail="Failed to advance mission")

@app.get("/api/missions/{mission_id}/status")
async def get_mission_status(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Get detailed mission status with progression settings"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    return {
        'mission_id': mission_id,
        'status': mission.get('status'),
        'current_phase': mission.get('current_phase'),
        'current_day': mission.get('current_day', 0),
        'auto_progress': mission.get('auto_progress', True),
        'cargo': mission.get('cargo', {}),
        'costs': mission.get('costs', {}),
        'events': mission.get('events', [])
    }

@app.post("/api/missions/{mission_id}/sell-cargo")
async def sell_mission_cargo(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Complete cargo sale and economic settlement with loan repayment"""
    global simulation_engine
    try:
        if not simulation_engine:
            simulation_engine = WorldSimulationEngine(db)
            await simulation_engine.initialize()
        
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        if mission.get('current_phase') != 'completed':
            raise HTTPException(status_code=400, detail="Mission must be completed before selling cargo")
        
        if mission.get('final_results'):
            raise HTTPException(status_code=400, detail="Cargo has already been sold")
        
        # Calculate cargo value
        cargo = mission.get('cargo', {})
        if not cargo or sum(cargo.values()) == 0:
            raise HTTPException(status_code=400, detail="No cargo to sell")
        
        mongodb_uri = os.getenv("MONGODB_URI")
        pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        prices_per_kg = pricing_service.get_commodity_prices_per_kg()
        
        cargo_value = 0
        cargo_breakdown = {}
        for element, weight_kg in cargo.items():
            price_per_kg = prices_per_kg.get(element, 0)
            element_value = weight_kg * price_per_kg
            cargo_value += element_value
            cargo_breakdown[element] = {
                'weight_kg': weight_kg,
                'price_per_kg': price_per_kg,
                'value': element_value
            }
        
        mission_costs = mission.get('costs', {}).get('total', 0)
        
        # Get and repay loans linked to this mission
        from bson import ObjectId
        from datetime import datetime, timezone
        
        loan_id = mission.get('loan_id')
        total_loan_payoff = 0
        loans_repaid = []
        
        if loan_id:
            loan = db.db.loans.find_one({"_id": ObjectId(loan_id), "status": "open"})
            if loan:
                total_loan_payoff += loan.get('payoff_amount', 0)
                loans_repaid.append(str(loan['_id']))
        
        # Also check for any other open loans linked to this mission
        other_loans = list(db.db.loans.find({"mission_id": mission_id, "status": "open"}))
        for loan in other_loans:
            if str(loan['_id']) != loan_id:
                total_loan_payoff += loan.get('payoff_amount', 0)
                loans_repaid.append(str(loan['_id']))
        
        # Calculate net profit after loan repayment
        net_profit = cargo_value - mission_costs - total_loan_payoff
        
        # Mark loans as repaid
        for loan_id_str in loans_repaid:
            try:
                db.db.loans.update_one(
                    {"_id": ObjectId(loan_id_str)},
                    {"$set": {
                        "status": "repaid",
                        "repaid_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }}
                )
            except Exception as e:
                print(f"Error marking loan {loan_id_str} as repaid: {e}")
        
        # Update mission with final results
        final_results = {
            'cargo_value': cargo_value,
            'mission_costs': mission_costs,
            'loan_payoff': total_loan_payoff,
            'net_profit': net_profit,
            'settlement_date': datetime.now(timezone.utc).isoformat(),
            'loans_repaid': loans_repaid
        }
        
        db.db.missions.update_one(
            {"_id": ObjectId(mission_id)},
            {"$set": {
                'final_results': final_results,
                'cargo_sold': True,
                'cargo_sale_date': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }}
        )
        
        # Determine if new financing is needed
        needs_financing = net_profit < 0
        suggested_loan_amount = abs(net_profit) + 100000 if needs_financing else 0
        
        return {
            'status': 'sold',
            'message': 'Cargo sold successfully',
            'cargo_value': cargo_value,
            'mission_costs': mission_costs,
            'loan_payoff': total_loan_payoff,
            'net_profit': net_profit,
            'results': final_results,
            'needs_financing': needs_financing,
            'suggested_loan_amount': suggested_loan_amount
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error selling cargo: {e}")
        raise HTTPException(status_code=500, detail="Failed to sell cargo")

@app.get("/api/missions/{mission_id}/hazards")
async def get_mission_hazards(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Get hazard statistics for a mission"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    try:
        hazards_service = SpaceHazardsService()
        hazard_history = [
            {
                "hazard_type": event.get("event_type", ""),
                "severity": event.get("description", "").split("Severity: ")[-1].split("/")[0] if "Severity:" in event.get("description", "") else 5,
                "severity_level": "moderate",  # Default, would need to parse from description
                "hull_damage": 0,  # Would need to track separately
                "additional_cost": event.get("cost", 0),
                "delay_days": event.get("impact_days", 0)
            }
            for event in mission.get("events", [])
            if event.get("event_type") in [h.value for h in HazardType]
        ]
        
        stats = hazards_service.get_hazard_statistics(hazard_history)
        return {
            "mission_id": mission_id,
            "hazard_statistics": stats,
            "recent_hazards": mission.get("events", [])[-10:] if mission.get("events") else []
        }
    except Exception as e:
        print(f"Error getting mission hazards: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mission hazards")

@app.get("/api/missions/budget-estimate")
async def get_budget_estimate(
    ship_id: str,
    asteroid_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Calculate budget estimate for a mission"""
    try:
        # Get ship and asteroid data
        ship = await db.get_ship(ship_id)
        if not ship:
            raise HTTPException(status_code=404, detail="Ship not found")
        
        asteroid = await db.get_asteroid(asteroid_id)
        if not asteroid:
            raise HTTPException(status_code=404, detail="Asteroid not found")
        
        # Calculate travel time
        orbital_service = OrbitalMechanicsService()
        moid_au = asteroid.get('moid', 1.0)
        travel_data = orbital_service.calculate_travel_time(moid_au, 'mining_mission')
        
        # Ensure travel time is at least 1 day (round trip)
        one_way_days = max(1, travel_data.get('one_way_time_days', 1))
        total_travel_days = max(1, travel_data.get('total_time_days', one_way_days * 2))
        
        # Mining site setup time: 1-5 days (randomized)
        import random
        mining_setup_days = random.randint(1, 5)
        
        # Estimate mining time (34 days to fill capacity)
        ship_capacity = ship.get('capacity_kg', ship.get('capacity', 50000))
        mining_days = min(34, int(ship_capacity / 1500))  # 1500 kg/day max
        
        # Total mission duration includes: travel + setup + mining + return travel
        total_days = total_travel_days + mining_setup_days + mining_days
        
        # Estimate costs - use $45K per day for operational costs (or config if higher)
        config = await db.get_config()
        ground_control_cost_per_day = config.get('ground_control_cost_per_day', 75000)
        operation_cost_per_day = max(45000, config.get('operation_cost_per_day', 50000))  # Minimum $45K/day
        
        ground_control_costs = ground_control_cost_per_day * total_days
        operation_costs = operation_cost_per_day * total_days
        total_costs = ground_control_costs + operation_costs
        
        # Estimate cargo value
        # ship_capacity already defined above
        mongodb_uri = os.getenv("MONGODB_URI")
        pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        prices_per_kg = pricing_service.get_commodity_prices_per_kg()
        
        # Estimate cargo composition based on asteroid class
        asteroid_class = asteroid.get('class', 'C')
        
        # Rough estimate: assume 70% capacity fill and average grade
        estimated_cargo_kg = ship_capacity * 0.7
        estimated_revenue = 0
        
        # Calculate estimated revenue based on typical element distribution
        if asteroid_class == 'C':
            # C-type: mostly common elements
            estimated_revenue = estimated_cargo_kg * prices_per_kg.get('Copper', 9.0) * 0.5
        elif asteroid_class == 'S':
            # S-type: more valuable elements
            estimated_revenue = estimated_cargo_kg * prices_per_kg.get('Silver', 881.85) * 0.3
        elif asteroid_class == 'M':
            # M-type: most valuable
            estimated_revenue = estimated_cargo_kg * prices_per_kg.get('Platinum', 35274.0) * 0.2
        
        estimated_profit = estimated_revenue - total_costs
        estimated_roi = (estimated_profit / total_costs * 100) if total_costs > 0 else 0
        
        return {
            "travel_time_days": total_travel_days,  # Round trip travel time
            "total_travel_days": total_travel_days,
            "mining_setup_days": mining_setup_days,
            "mining_time_days": mining_days,
            "total_days": total_days,
            "estimated_costs": {
                "ground_control": ground_control_costs,
                "operations": operation_costs,
                "total": total_costs
            },
            "estimated_revenue": estimated_revenue,
            "estimated_profit": estimated_profit,
            "estimated_roi": estimated_roi,
            "ship_capacity": ship_capacity
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error calculating budget estimate: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate budget estimate")

@app.get("/api/missions/readiness")
async def check_launch_readiness(
    ship_id: str,
    asteroid_id: str,
    db: DatabaseManager = Depends(get_db)
):
    """Check if mission is ready to launch"""
    try:
        # Check ship availability
        ship = await db.get_ship(ship_id)
        ship_available = ship and ship.get('status') == 'available'
        
        # Check asteroid accessibility
        asteroid = await db.get_asteroid(asteroid_id)
        asteroid_accessible = asteroid is not None
        
        # Check budget (simplified - would need user balance check)
        budget_sufficient = True  # TODO: Implement actual budget check
        
        return {
            "ship_available": ship_available,
            "asteroid_accessible": asteroid_accessible,
            "budget_sufficient": budget_sufficient,
            "ready": ship_available and asteroid_accessible and budget_sufficient
        }
    except Exception as e:
        print(f"Error checking launch readiness: {e}")
        raise HTTPException(status_code=500, detail="Failed to check launch readiness")

@app.post("/api/missions/{mission_id}/launch")
async def launch_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Manually launch a mission (move from launch_ready to launched)"""
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        current_phase = mission.get('current_phase', '')
        if current_phase != 'launch_ready':
            raise HTTPException(status_code=400, detail=f"Mission must be in 'launch_ready' phase to launch. Current phase: {current_phase}")
        
        # Update mission to launched phase
        success = await db.update_mission_phase(mission_id, "launched", 0)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update mission phase")
        
        # Update actual launch date
        from bson import ObjectId
        db.db.missions.update_one(
            {"_id": ObjectId(mission_id)},
            {"$set": {"actual_launch_date": datetime.now(timezone.utc)}}
        )
        
        return {"status": "launched", "message": "Mission launched successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error launching mission: {e}")
        raise HTTPException(status_code=500, detail="Failed to launch mission")

@app.post("/api/missions/{mission_id}/pause")
async def pause_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Pause auto-progression for a mission"""
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        from bson import ObjectId
        result = db.db.missions.update_one(
            {"_id": ObjectId(mission_id)},
            {"$set": {"auto_progress": False, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to pause mission")
        
        return {"status": "paused", "message": "Mission auto-progression paused"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error pausing mission: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause mission")

@app.post("/api/missions/{mission_id}/resume")
async def resume_mission(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Resume auto-progression for a mission"""
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        from bson import ObjectId
        result = db.db.missions.update_one(
            {"_id": ObjectId(mission_id)},
            {"$set": {"auto_progress": True, "updated_at": datetime.now(timezone.utc)}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to resume mission")
        
        return {"status": "resumed", "message": "Mission auto-progression resumed"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error resuming mission: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume mission")

@app.post("/api/missions/{mission_id}/advance-day")
async def advance_mission_day(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Manually advance a mission by one day"""
    try:
        global simulation_engine
        if not simulation_engine:
            simulation_engine = WorldSimulationEngine(db)
            await simulation_engine.initialize()
        
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Check if mission is paused
        if mission.get('auto_progress', True):
            raise HTTPException(status_code=400, detail="Mission is set to auto-progress. Pause it first to manually advance.")
        
        # Get current world day
        world_state = await db.get_world_state()
        current_world_day = world_state.get('current_day', 0)
        
        # Process one day for this mission
        await simulation_engine.process_mission_day(mission, current_world_day)
        
        return {"status": "advanced", "message": "Mission advanced by one day"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error advancing mission day: {e}")
        raise HTTPException(status_code=500, detail="Failed to advance mission day")

@app.get("/api/missions/{mission_id}/status")
async def get_mission_status(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Get detailed mission status with progression settings"""
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return {
            "mission_id": mission_id,
            "name": mission.get('name', 'Unknown'),
            "status": mission.get('status', 'unknown'),
            "current_phase": mission.get('current_phase', 'unknown'),
            "current_day": mission.get('current_day', 0),
            "total_days": mission.get('total_days', 0),
            "auto_progress": mission.get('auto_progress', True),
            "cargo": mission.get('cargo', {}),
            "cargo_weight": sum(mission.get('cargo', {}).values()),
            "costs": mission.get('costs', {}),
            "events": mission.get('events', []),
            "updated_at": mission.get('updated_at')
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting mission status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mission status")

@app.post("/api/missions/{mission_id}/sell-cargo")
async def sell_mission_cargo(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Sell cargo for a completed mission and trigger economic settlement"""
    try:
        mission = await db.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Check if mission is in a state where cargo can be sold
        current_phase = mission.get('current_phase', '')
        if current_phase not in ['completed', 'returned', 'cargo_ready']:
            raise HTTPException(status_code=400, detail=f"Cargo cannot be sold. Mission is in phase: {current_phase}")
        
        # Check if cargo has already been sold
        if mission.get('cargo_sold', False):
            raise HTTPException(status_code=400, detail="Cargo has already been sold")
        
        # Get cargo and calculate value
        cargo = mission.get('cargo', {})
        if not cargo or sum(cargo.values()) == 0:
            raise HTTPException(status_code=400, detail="No cargo to sell")
        
        # Get current commodity prices
        mongodb_uri = os.getenv("MONGODB_URI")
        pricing_service = CommodityPricingService(mongodb_uri=mongodb_uri)
        prices_per_kg = pricing_service.get_commodity_prices_per_kg()
        
        # Calculate cargo value
        cargo_value = 0
        cargo_breakdown = {}
        for element, weight_kg in cargo.items():
            price_per_kg = prices_per_kg.get(element, 0)
            element_value = weight_kg * price_per_kg
            cargo_value += element_value
            cargo_breakdown[element] = {
                'weight_kg': weight_kg,
                'price_per_kg': price_per_kg,
                'total_value': element_value
            }
        
        # Calculate economic settlement using mission economics service
        from src.services.mission_economics_enhanced import MissionEconomicsService
        economics_service = MissionEconomicsService(mongodb_uri=mongodb_uri)
        
        # Get mission budget for investor repayment calculation
        mission_budget = mission.get('budget', 0)
        
        # Calculate settlement
        settlement = economics_service.calculate_mission_results(
            mission_id=mission_id,
            total_cargo_kg=sum(cargo.values()),
            cargo_value=cargo_value,
            mission_costs=mission.get('costs', {}).get('total', 0),
            mission_budget=mission_budget
        )
        
        # Update mission with sale and settlement
        from bson import ObjectId
        from datetime import datetime, timezone
        
        update_data = {
            'cargo_sold': True,
            'cargo_sale_date': datetime.now(timezone.utc),
            'final_results': settlement,
            'updated_at': datetime.now(timezone.utc)
        }
        
        db.db.missions.update_one(
            {"_id": ObjectId(mission_id)},
            {"$set": update_data}
        )
        
        # Update user balance (if user_id is available)
        user_id = mission.get('user_id')
        if user_id:
            # Get current user balance
            user = await db.get_user(user_id)
            if user:
                current_balance = user.get('balance', 0)
                new_balance = current_balance + settlement.get('net_profit', 0)
                
                # Update user balance
                from bson import ObjectId as UserObjectId
                db.db.users.update_one(
                    {"_id": UserObjectId(user_id)},
                    {"$set": {"balance": new_balance, "updated_at": datetime.now(timezone.utc)}}
                )
        
        return {
            "status": "sold",
            "message": "Cargo sold successfully",
            "cargo_value": cargo_value,
            "cargo_breakdown": cargo_breakdown,
            "settlement": settlement
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error selling cargo: {e}")
        raise HTTPException(status_code=500, detail="Failed to sell cargo")

# Background simulation loop
async def run_simulation_loop(db: DatabaseManager):
    """Background simulation loop"""
    global simulation_engine
    
    while True:
        try:
            world_state = await db.get_world_state()
            if world_state["status"] != "running":
                break
            
            await simulation_engine.process_daily_tick()
            
            # Wait 1 second between days (for demo purposes)
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"Error in simulation loop: {e}")
            break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
