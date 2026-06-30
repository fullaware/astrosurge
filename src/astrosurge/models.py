"""Data models for AstroSurge simulation."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
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


# ─── upgrade module ──────────────────────────────────────────────────────

UPGRADE_MODULES = {
    "water_extraction":      {"name": "Water Extraction + Cryotankage",     "tier": 2, "cost": 30_000_000},
    "propulsion_manufacturing": {"name": "Propulsion Manufacturing Bay",   "tier": 3, "cost": 50_000_000},
    "advanced_refinement":  {"name": "Advanced Ore Refinement",            "tier": 4, "cost": 50_000_000},
    "swarm_ai":             {"name": "Swarm AI Coordination",              "tier": 4, "cost": 30_000_000},
}

TIER_REQUIREMENTS = {
    2: ["water_extraction"],
    3: ["propulsion_manufacturing"],
    4: ["advanced_refinement", "swarm_ai"],
}

MISSION_TYPE_TIER = {
    "mining_fast_roi":   1,
    "mining_ice":       2,
    "hazard_hunter":    3,
    "precision_extraction": 4,
}


@dataclass
class UpgradeModule:
    module_id: str
    installed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tier: int = 0

    def to_dict(self) -> dict:
        return {
            "module_id": self.module_id,
            "installed_at": self.installed_at.isoformat(),
            "tier": self.tier,
        }


# ─── ship ──────────────────────────────────────────────────────────────────

SHIP_CLASSES = ("mining_transport", "heavy_lifter", "ice_hauler", "hazard_interceptor")
SHIP_STATUSES = ("active", "in_port", "reserve", "disabled", "lost", "retired")


@dataclass
class Ship:
    ship_id: str
    name: str
    class_: str = "mining_transport"
    status: str = "in_port"
    tier: int = 1
    mission_count: int = 0
    veteran_status: bool = False
    cargo_capacity_kg: float = 50_000
    propulsion_type: str = "nuclear_thermal"
    shielding_type: str = "passive"
    repair_bots_count: int = 2
    current_cargo_kg: float = 0.0
    retained_earnings: float = 0.0
    total_upgrade_spend: float = 0.0
    total_cargo_value_sold: float = 0.0
    upgrades: list[UpgradeModule] = field(default_factory=list)
    last_mission_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_upgrade(self, module_id: str) -> bool:
        return any(u.module_id == module_id for u in self.upgrades)

    def can_do_mission_type(self, mission_type: str) -> bool:
        """Check if ship has upgrades for a mission type."""
        required_tier = MISSION_TYPE_TIER.get(mission_type, 1)
        if required_tier <= self.tier:
            return True
        # Check if we can reach this tier via installed upgrades
        for req_module in TIER_REQUIREMENTS.get(required_tier, []):
            if not self.has_upgrade(req_module):
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "ship_id": self.ship_id,
            "name": self.name,
            "class": self.class_,
            "status": self.status,
            "tier": self.tier,
            "mission_count": self.mission_count,
            "veteran_status": self.veteran_status,
            "cargo_capacity_kg": self.cargo_capacity_kg,
            "propulsion_type": self.propulsion_type,
            "shielding_type": self.shielding_type,
            "repair_bots_count": self.repair_bots_count,
            "current_cargo_kg": self.current_cargo_kg,
            "retained_earnings": self.retained_earnings,
            "total_upgrade_spend": self.total_upgrade_spend,
            "total_cargo_value_sold": self.total_cargo_value_sold,
            "upgrades": [u.to_dict() for u in self.upgrades],
            "last_mission_id": self.last_mission_id,
            "created_at": self.created_at.isoformat(),
        }


# ─── mission ───────────────────────────────────────────────────────────────

MISSION_STATUSES = ("active", "completed", "failed", "abandoned", "sold")
MISSION_TYPES = ("mining_fast_roi", "mining_ice", "hazard_hunter", "precision_extraction")

PHASE_NAMES = {
    1: "asteroid_identification",
    2: "survey_planning",
    3: "mission_design",
    4: "spacecraft_assembly",
    5: "transit_execution",
    6: "site_establishment",
    7: "mining_operations",
    8: "cargo_sealing",
    9: "return_transit",
    10: "market_sale",
    11: "financial_analysis",
}


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

    def to_dict(self) -> dict:
        return {
            "total_cost_usd": round(self.total_cost_usd, 2),
            "total_revenue_usd": round(self.total_revenue_usd, 2),
            "net_profit_usd": round(self.net_profit_usd, 2),
            "roi": round(self.roi, 4),
            "total_yield_kg": round(self.total_yield_kg, 2),
            "time_to_value_days": self.time_to_value_days,
            "break_even_price_per_kg": round(self.break_even_price_per_kg, 2),
            "daily_throughput_kg": self.daily_throughput_kg,
        }


@dataclass
class Mission:
    mission_id: str
    ship_id: str
    asteroid_source_id: ObjectId
    asteroid_name: str
    spkid: int
    mission_type: str = "mining_fast_roi"
    tier: int = 1
    phase: int = 1
    phase_name: str = "asteroid_identification"
    status: str = "active"
    moid_au: float = 0.0
    transit_time_days_one_way: int = 0
    round_trip_days: int = 0
    metrics: MissionMetrics = field(default_factory=MissionMetrics)
    phase_results: list[dict] = field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "ship_id": self.ship_id,
            "asteroid_name": self.asteroid_name,
            "spkid": self.spkid,
            "mission_type": self.mission_type,
            "tier": self.tier,
            "phase": self.phase,
            "phase_name": self.phase_name,
            "status": self.status,
            "moid_au": self.moid_au,
            "transit_time_days_one_way": self.transit_time_days_one_way,
            "round_trip_days": self.round_trip_days,
            "metrics": self.metrics.to_dict(),
            "num_phases_completed": len(self.phase_results),
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ─── ship event ──────────────────────────────────────────────────────────

EVENT_TYPES = (
    "built", "named", "launched", "in_flight", "site_setup",
    "mining", "cargo_filled", "return_flight", "landed",
    "cargo_sold", "mission_complete", "upgraded",
    "disabled", "lost", "retired", "salvage_recovered",
)


@dataclass
class ShipEvent:
    ship_id: str
    mission_id: Optional[str]
    event_type: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ship_id": self.ship_id,
            "mission_id": self.mission_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


# ─── daily yield record ────────────────────────────────────────────────────

@dataclass
class DailyYield:
    day: int
    total_mined_kg: float
    element_breakdown: dict  # {name: {"mass_kg": float, "value": float}}
    daily_revenue: float
    events: list[dict] = field(default_factory=list)  # 0-N events per day


# ─── fund tracking ─────────────────────────────────────────────────────────

@dataclass
class FundingState:
    total_funding_pool: float
    ship_cost: float
    launch_cost: float
    daily_ops_cost: float
    days_elapsed: int = 0
    cumulative_ops_cost: float = 0.0
    debt_owed: float = 0.0
    current_cargo_value: float = 0.0
    remaining_funding: float = 0.0
    funded_by_investors: bool = True
    previous_mission_profit: float = 0.0
