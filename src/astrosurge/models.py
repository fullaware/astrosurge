"""Data models for AstroSurge simulation."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from bson import ObjectId


# ─── asteroid element composition ──────────────────────────────────────────

@dataclass
class Element:
    name: str
    mass_kg: float
    number: int = 0


# ─── source asteroid (from asteroids.asteroids collection) ─────────────────

@dataclass
class Asteroid:
    source_id: ObjectId
    name: Optional[str]
    pdes: str
    spkid: int
    class_: str  # 'M', 'C', 'S', etc.
    diameter: float  # km
    moid: float  # AU
    moid_days: int
    neo: bool
    hazard: bool
    elements: list[Element] = field(default_factory=list)


# ─── ship ──────────────────────────────────────────────────────────────────

@dataclass
class Ship:
    ship_id: str
    name: str
    class_: str  # mining_transport, heavy_lifter, ice_hauler, hazard_interceptor
    status: str = "in_port"  # active | in_port | reserve | disabled | lost | retired
    tier: int = 1
    mission_count: int = 0
    veteran_status: bool = False
    cargo_capacity_kg: float = 50_000
    propulsion_type: str = "chemical"
    shielding_type: str = "passive"
    repair_bots_count: int = 2
    current_cargo_kg: float = 0.0
    water_extraction: bool = False
    propulsion_manufacturing: bool = False
    advanced_refinement: bool = False
    swarm_ai: bool = False


# ─── mission ───────────────────────────────────────────────────────────────

@dataclass
class MissionMetrics:
    total_cost_usd: float = 0.0
    total_revenue_usd: float = 0.0
    net_profit_usd: float = 0.0
    roi: float = 0.0
    total_yield_kg: float = 0.0
    time_to_value_days: int = 0
    break_even_price_per_kg: float = 0.0
    daily_throughput_kg: float = 36_000


@dataclass
class Mission:
    asteroid_source_id: ObjectId
    asteroid_name: str
    spkid: int
    mission_type: str = "mining_fast_roi"  # mining_fast_roi | mining_ice | hazard_hunter | precision_extraction
    phase: int = 1
    phase_name: str = "asteroid_identification"
    status: str = "active"  # active | completed | failed | abandoned | sold
    tier: int = 1
    ship_id: Optional[str] = None
    moid_au: float = 0.0
    transit_time_days_one_way: int = 0
    round_trip_days: int = 0
    metrics: MissionMetrics = field(default_factory=MissionMetrics)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ─── daily yield record ────────────────────────────────────────────────────

@dataclass
class DailyYield:
    day: int
    total_mined_kg: float
    element_breakdown: dict  # {name: {"mass_kg": float, "value": float}}
    daily_revenue: float
    event: Optional[dict] = None


# ─── fund tracking ─────────────────────────────────────────────────────────

@dataclass
class FundingState:
    total_funding_pool: float  # upfront capital secured
    ship_cost: float
    launch_cost: float
    daily_ops_cost: float
    days_elapsed: int = 0
    cumulative_ops_cost: float = 0.0
    debt_owed: float = 0.0  # total funding consumed so far
    current_cargo_value: float = 0.0
    remaining_funding: float = 0.0
    funded_by_investors: bool = True
    previous_mission_profit: float = 0.0
