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
    asteroid_name: str = Field(..., description="Target asteroid")
    asteroid_moid_days: int = Field(..., description="Days to reach asteroid")
    budget: float = Field(..., description="Mission budget")

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
        
        # Check for events based on phase
        phase_events = [e for e in self.events if e['phase'] == phase]
        
        for event in phase_events:
            if random.random() < event['probability']:
                await self.apply_event_to_mission(mission_id, event, day)
        
        # Update mission progress based on phase
        await self.update_mission_progress(mission_id, day, phase)
    
    async def apply_event_to_mission(self, mission_id, event, day):
        """Apply an event to a mission"""
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
        elif phase == "mining":
            # Mining operations on asteroid
            await self.progress_mining_phase(mission_id, day)
        elif phase == "returning":
            # Return journey to Earth
            await self.progress_return_phase(mission_id, day)
        
        # Update mission timestamp
        await self.db.update_mission_timestamp(mission_id)
    
    async def check_launch_conditions(self, mission_id):
        """Check if launch conditions are met"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        # For now, automatically launch after 3 days in launch_ready phase
        # In a real system, this would check weather, technical readiness, etc.
        if mission['current_day'] >= 3:
            await self.db.update_mission_phase(mission_id, "launched", 0)
            print(f"   🚀 Mission {mission_id} launched successfully!")
    
    async def progress_travel_phase(self, mission_id, day):
        """Progress the travel phase of a mission"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        current_day = mission['current_day']
        asteroid_moid_days = mission['asteroid_moid_days']
        
        # After first day of launch, transition to traveling phase
        if current_day == 1 and mission['current_phase'] == 'launched':
            await self.db.update_mission_phase(mission_id, "traveling", current_day)
            print(f"   🚀 Mission {mission_id} transitioned to traveling phase")
        
        # Check if arrived at asteroid
        if current_day >= asteroid_moid_days:
            # Arrived at asteroid, switch to mining phase
            await self.db.update_mission_phase(mission_id, "mining", 0)
            print(f"   🚀 Mission {mission_id} arrived at asteroid, switching to mining phase")
    
    async def progress_mining_phase(self, mission_id, day):
        """Progress the mining phase of a mission"""
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
        
        # Calculate daily mining output (max 1500kg per day)
        daily_mining_capacity = 1500  # kg per day
        current_cargo = mission.get('cargo', {})
        total_cargo_weight = sum(current_cargo.values()) if current_cargo else 0
        ship_capacity = 50000  # kg
        
        if total_cargo_weight >= ship_capacity:
            # Ship is full, switch to return phase
            await self.db.update_mission_phase(mission_id, "returning", 0)
            print(f"   ⛏️  Mission {mission_id} cargo full ({total_cargo_weight}kg), switching to return phase")
            return
        
        # Calculate today's mining output based on asteroid composition
        # The asteroid data uses 'elements' array with 'name' and 'mass_kg' fields
        available_elements = asteroid.get('elements', [])
        if not available_elements:
            print(f"   ❌ Asteroid {asteroid_id} has no elements data")
            return
        
        # Calculate mining output for this day
        daily_output = {}
        remaining_capacity = min(daily_mining_capacity, ship_capacity - total_cargo_weight)
        
        if remaining_capacity > 0:
            # Focus on valuable elements for mining (Gold, Platinum, Palladium, Silver, Copper, Lithium, Cobalt)
            valuable_elements = ['Gold', 'Platinum', 'Palladium', 'Silver', 'Copper', 'Lithium', 'Cobalt']
            
            # Filter available elements to only valuable ones
            valuable_available = [e for e in available_elements if e.get('name') in valuable_elements]
            
            if valuable_available:
                # Distribute mining output across valuable elements
                per_element = remaining_capacity / len(valuable_available)
                for element in valuable_available:
                    element_name = element['name']
                    daily_output[element_name] = per_element
                
                # Update mission cargo
                new_cargo = current_cargo.copy()
                for element, amount in daily_output.items():
                    new_cargo[element] = new_cargo.get(element, 0) + amount
                
                # Update mission with new cargo
                await self.db.update_mission_cargo(mission_id, new_cargo)
                
                print(f"   ⛏️  Mission {mission_id} mined {remaining_capacity:.1f}kg of valuable elements (Total: {sum(new_cargo.values()):.1f}kg)")
            else:
                print(f"   ⚠️  Mission {mission_id} - No valuable elements found on asteroid")
        
        # Increment mission day counter for mining phase
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
        """Calculate final mission results including investor repayment and ship repair"""
        mission = await self.db.get_mission(mission_id)
        if not mission:
            return
        
        # Get mission costs
        total_costs = mission.get('costs', {}).get('total', 0)
        
        # Calculate investor repayment with interest (15% annual rate)
        # Convert to daily rate: 15% / 365 = 0.0411% per day
        daily_interest_rate = 0.15 / 365
        mission_duration_days = mission.get('total_days', 0) or 224  # Default to typical mission length
        
        # Calculate interest: Principal × Rate × Time
        interest_amount = total_costs * daily_interest_rate * mission_duration_days
        total_repayment = total_costs + interest_amount
        
        # Calculate ship repair costs based on hull damage
        # Hull damage accumulates during the mission from events
        hull_damage = mission.get('hull_damage', 0) or 0
        repair_cost_per_damage = 1000000  # $1M per damage point
        ship_repair_cost = min(hull_damage * repair_cost_per_damage, 25000000)  # Max $25M
        
        # Calculate cargo value
        cargo = mission.get('cargo', {})
        cargo_value = self.calculate_cargo_value(cargo)
        
        # Calculate net profit
        net_profit = cargo_value - total_costs - total_repayment - ship_repair_cost
        
        # Update mission with final results
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
        
        print(f"   💰 Mission {mission_id} results calculated:")
        print(f"      Total Costs: ${total_costs:,.2f}")
        print(f"      Investor Repayment: ${total_repayment:,.2f} (including ${interest_amount:,.2f} interest)")
        print(f"      Ship Repair: ${ship_repair_cost:,.2f}")
        print(f"      Cargo Value: ${cargo_value:,.2f}")
        print(f"      Net Profit: ${net_profit:,.2f}")
        print(f"      ROI: {final_results['roi_percentage']:.1f}%")
    
    def calculate_cargo_value(self, cargo):
        """Calculate the market value of cargo"""
        # Market prices per kg (realistic commodity prices)
        market_prices = {
            'Gold': 60000,        # $60,000/kg
            'Platinum': 30000,    # $30,000/kg
            'Palladium': 40000,   # $40,000/kg
            'Silver': 800,        # $800/kg
            'Silver': 800,        # $800/kg
            'Copper': 8,          # $8/kg
            'Lithium': 15,        # $15/kg
            'Cobalt': 80          # $80/kg
        }
        
        total_value = 0
        for element, amount in cargo.items():
            price = market_prices.get(element, 0)
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
            
            for ship in ships:
                ship["_id"] = str(ship["_id"])
            return ships
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
            return ship
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
            
            for mission in missions:
                mission["_id"] = str(mission["_id"])
            return missions
        except Exception as e:
            print(f"Error getting missions: {e}")
            return []
    
    async def create_mission(self, mission_data: MissionCreate) -> Dict[str, Any]:
        """Create a new mission"""
        try:
            mission_dict = mission_data.model_dump()
            mission_dict["created_at"] = datetime.now(timezone.utc)
            mission_dict["updated_at"] = datetime.now(timezone.utc)
            mission_dict["status"] = "planning"
            mission_dict["current_phase"] = "planning"
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
            
            result = self.db.missions.insert_one(mission_dict)
            mission_dict["_id"] = str(result.inserted_id)
            return mission_dict
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

@app.get("/api/missions/{mission_id}/results")
async def get_mission_results(mission_id: str, db: DatabaseManager = Depends(get_db)):
    """Get detailed mission results including economic analysis"""
    mission = await db.get_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Get final results if mission is completed
    final_results = mission.get('final_results', {})
    
    # Calculate current mission status and costs
    current_costs = mission.get('costs', {})
    current_phase = mission.get('current_phase', 'unknown')
    
    # Prepare comprehensive mission report
    mission_report = {
        'mission_id': mission_id,
        'name': mission.get('name', 'Unknown Mission'),
        'status': mission.get('status', 'unknown'),
        'current_phase': current_phase,
        'current_day': mission.get('current_day', 0),
        'total_days': mission.get('total_days', 0),
        'asteroid_name': mission.get('asteroid_name', 'Unknown'),
        'ship_name': mission.get('ship_name', 'Unknown Ship'),
        'cargo': mission.get('cargo', {}),
        'cargo_weight': sum(mission.get('cargo', {}).values()),
        'costs': current_costs,
        'events': mission.get('events', []),
        'final_results': final_results,
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

# Asteroid and Element Data
@app.get("/api/asteroids")
async def get_asteroids(limit: int = 10, skip: int = 0, db: DatabaseManager = Depends(get_db)):
    """Get asteroids from the database"""
    return await db.get_asteroids(limit, skip)

@app.get("/api/elements")
async def get_elements(db: DatabaseManager = Depends(get_db)):
    """Get chemical elements from the database"""
    return await db.get_elements()

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
