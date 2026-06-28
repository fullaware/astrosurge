"""Mission lifecycle — orchestrates the 11-phase asteroid mining mission.

Phases (PRD v2.0):
  1. Asteroid Identification
  2. Survey Planning
  3. Mission Design
  4. Spacecraft Assembly & Funding
  5. Transit Execution (outbound)
  6. Site Establishment
  7. Mining Operations
  8. Cargo Sealing
  9. Return Transit
 10. Market Sale
 11. Financial Analysis
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from enum import IntEnum, auto

from .models import Asteroid, Mission, MissionMetrics
from .transit import calc_round_trip, TransitEstimate
from .mining import MiningState, run_mining_operation
from .market import MarketState, sell_cargo
from .finance import MissionFinances, FundingSnapshot
from .config import settings


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


# ─── mission phase status ─────────────────────────────────────────────────

@dataclass
class PhaseResult:
    phase: int
    phase_name: str
    status: str = "completed"  # completed | in_progress | failed
    data: dict = field(default_factory=dict)


# ─── mission runner ────────────────────────────────────────────────────────

@dataclass
class MissionResult:
    """Complete output from running a mission."""
    asteroid_name: str
    spkid: int
    mission_type: str
    tier: int
    status: str
    transit: TransitEstimate
    mining: Optional[MiningState] = None
    funding_snapshots: list[FundingSnapshot] = field(default_factory=list)
    phase_results: list[PhaseResult] = field(default_factory=list)
    financials: dict = field(default_factory=dict)
    market_result: dict = field(default_factory=dict)
    error: Optional[str] = None
    reusable: bool = False
    refinery: bool = False

    def to_dict(self) -> dict:
        return {
            "asteroid_name": self.asteroid_name,
            "spkid": self.spkid,
            "mission_type": self.mission_type,
            "tier": self.tier,
            "status": self.status,
            "transit": {
                "one_way_days": self.transit.one_way_days,
                "round_trip_days": self.transit.round_trip_days,
                "setup_days": self.transit.setup_days,
                "mining_days": self.transit.mining_days,
                "prep_days": self.transit.prep_days,
            },
            "mining": {
                "days_mined": self.mining.days_mined if self.mining else 0,
                "total_mined_kg": round(self.mining.total_mined_kg, 2) if self.mining else 0,
                "total_ore_kg": round(self.mining.total_ore_kg, 2) if self.mining else 0,
                "total_revenue_at_extraction": round(self.mining.total_revenue, 2) if self.mining else 0,
            } if self.mining else None,
            "num_phase_results": len(self.phase_results),
            "is_break_even": self.funding_snapshots[-1].is_break_even if self.funding_snapshots else False,
            "financials": self.financials,
            "error": self.error,
        }


# ─── orchestrator ──────────────────────────────────────────────────────────

def run_mission(
    asteroid: Asteroid,
    ship_cost: float = 0.0,
    launch_cost: Optional[float] = None,
    daily_ops: Optional[float] = None,
    mining_days: int = 139,
    previous_mission_profit: float = 0.0,
    seed: Optional[int] = None,
    reusable: bool = False,
    refinery: bool = False,
) -> MissionResult:
    """Execute a complete Tier 1 Fast ROI mission.

    Args:
        asteroid: Target asteroid.
        ship_cost: Cost of building/acquiring the ship.
        launch_cost: Cost per launch. Auto-set to REUSABLE when reusable=True.
        daily_ops: Daily operations cost. Auto-increased when refinery=True.
        mining_days: Max mining days before departure.
        previous_mission_profit: Retained profit from prior mission.
        seed: RNG seed for deterministic results.
        reusable: If True, uses reusable launch cost ($97M vs $150M).
        refinery: If True, on-site processing extracts only PGMs.

    This runs all 11 phases in sequence and returns the full result.
    """

    # Resolve launch cost: explicit param wins, else auto-detect
    if launch_cost is None:
        launch_cost = (
            settings.LAUNCH_COST_REUSABLE if reusable
            else settings.LAUNCH_COST_EXPENDABLE
        )

    # Resolve daily ops: explicit param wins, else add refinery cost
    if daily_ops is None:
        daily_ops = settings.DAILY_OPS_COST
        if refinery:
            daily_ops += settings.REFINERY_DAILY_COST

    # ── Phase 1: Asteroid Identification ──────────────────────────────────
    transit_est = calc_round_trip(asteroid.moid)

    phase_results: list[PhaseResult] = [
        PhaseResult(1, "asteroid_identification", data={
            "target": asteroid.name or f"spkid-{asteroid.spkid}",
            "class": asteroid.class_,
            "diameter_km": asteroid.diameter,
            "moid_au": asteroid.moid,
            "hazard": asteroid.hazard,
            "transit_days_one_way": transit_est.one_way_days,
            "round_trip_days": transit_est.round_trip_days,
        }),
    ]

    # ── Phase 2: Survey Planning ──────────────────────────────────────────
    phase_results.append(PhaseResult(2, "survey_planning", data={
        "instrument_suite": "advanced",
        "hazard_tolerance": "conservative",
    }))

    # ── Phase 3: Mission Design ───────────────────────────────────────────
    phase_results.append(PhaseResult(3, "mission_design", data={
        "propulsion": "chemical",
        "mission_profile": "direct_intercept",
        "delta_v_budget_km_s": 8.5,
    }))

    # ── Phase 4: Spacecraft Assembly & Funding ────────────────────────────
    finances = MissionFinances(
        ship_cost=ship_cost,
        launch_cost=launch_cost,
        daily_ops_cost=daily_ops,
        total_days_estimated=transit_est.round_trip_days,
    )
    finances._previous_mission_profit = previous_mission_profit
    funding_pool = finances.secure_funding()

    phase_results.append(PhaseResult(4, "spacecraft_assembly", data={
        "shielding": "SITU",
        "container_capacity_kg": settings.CARGO_CAPACITY_KG,
        "funding_pool": round(funding_pool, 2),
    }))

    # ── Phase 5: Transit Execution (outbound) ─────────────────────────────
    funding_snapshots: list[FundingSnapshot] = []
    for snapshot in finances.advance_day(transit_est.one_way_days):
        funding_snapshots.append(snapshot)

    phase_results.append(PhaseResult(5, "transit_execution", data={
        "duration_days": transit_est.outbound.days,
        "funding_remaining": funding_snapshots[-1].funding_remaining,
        "debt_owed": funding_snapshots[-1].debt_owed,
    }))

    # Check for funding failure during transit
    if finances.has_funding_run_out():
        return MissionResult(
            asteroid_name=asteroid.name or f"spkid-{asteroid.spkid}",
            spkid=asteroid.spkid,
            mission_type="mining_fast_roi",
            tier=1,
            status="failed",
            transit=transit_est,
            funding_snapshots=funding_snapshots,
            phase_results=phase_results,
            financials=finances.finalize(0.0),
            error="Funding exhausted during outbound transit",
            reusable=reusable,
            refinery=refinery,
        )

    # ── Phase 6: Site Establishment ───────────────────────────────────────
    for snapshot in finances.advance_day(transit_est.setup_days):
        funding_snapshots.append(snapshot)

    phase_results.append(PhaseResult(6, "site_establishment", data={
        "duration_days": transit_est.setup_days,
        "surface_survey": True,
        "equipment_deployed": True,
    }))

    # Check funding
    if finances.has_funding_run_out():
        return MissionResult(
            asteroid_name=asteroid.name or f"spkid-{asteroid.spkid}",
            spkid=asteroid.spkid,
            mission_type="mining_fast_roi",
            tier=1,
            status="failed",
            transit=transit_est,
            funding_snapshots=funding_snapshots,
            phase_results=phase_results,
            financials=finances.finalize(0.0),
            error="Funding exhausted during site establishment",
            reusable=reusable,
            refinery=refinery,
        )

    # ── Phase 7: Mining Operations ────────────────────────────────────────
    mining_state = run_mining_operation(
        asteroid, max_days=mining_days, seed=seed, refinery=refinery,
    )

    for snapshot in finances.advance_day(mining_state.days_mined):
        # Update cargo value after each day
        finances.update_cargo_value(mining_state.total_revenue)
        funding_snapshots.append(snapshot)

    phase_results.append(PhaseResult(7, "mining_operations", data={
        "days_mined": mining_state.days_mined,
        "total_mined_kg": round(mining_state.total_mined_kg, 2),
        "total_ore_kg": round(mining_state.total_ore_kg, 2),
        "container_full": mining_state.is_container_full(),
    }))

    if finances.has_funding_run_out():
        return MissionResult(
            asteroid_name=asteroid.name or f"spkid-{asteroid.spkid}",
            spkid=asteroid.spkid,
            mission_type="mining_fast_roi",
            tier=1,
            status="failed",
            transit=transit_est,
            mining=mining_state,
            funding_snapshots=funding_snapshots,
            phase_results=phase_results,
            financials=finances.finalize(0.0),
            error="Funding exhausted during mining operations",
            reusable=reusable,
            refinery=refinery,
        )

    # ── Phase 8: Cargo Sealing ───────────────────────────────────────────
    for snapshot in finances.advance_day(transit_est.prep_days):
        funding_snapshots.append(snapshot)

    phase_results.append(PhaseResult(8, "cargo_sealing", data={
        "cargo_sealed": True,
        "trajectory_corrected": True,
    }))

    # ── Phase 9: Return Transit ───────────────────────────────────────────
    for snapshot in finances.advance_day(transit_est.return_.days):
        # Keep updating cargo value with current market estimate
        finances.update_cargo_value(mining_state.total_revenue)
        funding_snapshots.append(snapshot)

    phase_results.append(PhaseResult(9, "return_transit", data={
        "duration_days": transit_est.return_.days,
        "funding_remaining": funding_snapshots[-1].funding_remaining,
    }))

    if finances.has_funding_run_out():
        return MissionResult(
            asteroid_name=asteroid.name or f"spkid-{asteroid.spkid}",
            spkid=asteroid.spkid,
            mission_type="mining_fast_roi",
            tier=1,
            status="failed",
            transit=transit_est,
            mining=mining_state,
            funding_snapshots=funding_snapshots,
            phase_results=phase_results,
            financials=finances.finalize(0.0),
            error="Funding exhausted during return transit",
            reusable=reusable,
            refinery=refinery,
        )

    # ── Phase 10: Market Sale ─────────────────────────────────────────────
    # Aggregate element breakdown across all mining days (no double-count)
    element_breakdown: dict[str, dict] = {}
    for yd in mining_state.daily_yields:
        for elem, data in yd.element_breakdown.items():
            entry = element_breakdown.get(elem)
            if entry is None:
                element_breakdown[elem] = {"mass_kg": data["mass_kg"], "value": data["value"]}
            else:
                entry["mass_kg"] += data["mass_kg"]
                entry["value"] += data["value"]

    market_state = MarketState()
    market_result = sell_cargo(market_state, element_breakdown)

    phase_results.append(PhaseResult(10, "market_sale", data={
        "total_revenue": market_result["total_revenue"],
        "elements_sold": len(market_result["element_sales"]),
    }))

    # ── Phase 11: Financial Analysis ──────────────────────────────────────
    financials = finances.finalize(market_result["total_revenue"])

    phase_results.append(PhaseResult(11, "financial_analysis", data=financials))

    return MissionResult(
        asteroid_name=asteroid.name or f"spkid-{asteroid.spkid}",
        spkid=asteroid.spkid,
        mission_type="mining_fast_roi",
        tier=1,
        status="completed",
        transit=transit_est,
        mining=mining_state,
        funding_snapshots=funding_snapshots,
        phase_results=phase_results,
        financials=financials,
        market_result=market_result,
        reusable=reusable,
        refinery=refinery,
    )
