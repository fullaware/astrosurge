"""Mining operations simulation with site degradation and repositioning.

Daily extraction at 36 000 kg/day throughput.
Ore grade degrades over time. Site stability decreases.
Repositioning may be required when site becomes unstable or ore depleted.
Multiple events can occur per day.
"""

from dataclasses import dataclass, field
from typing import Optional
import random
import math

from .models import Asteroid, Element, DailyYield
from .config import settings
from .events import repositioning_event, _mining_extras


# ─── precious metals for on-site refining ────────────────────────────────

PRECIOUS_METALS: set[str] = {
    "Gold", "Platinum", "Palladium", "Iridium",
    "Rhodium", "Ruthenium", "Osmium", "Silver",
}


# ─── mining state ──────────────────────────────────────────────────────────

@dataclass
class MiningState:
    """Track mining progress over a mission."""
    asteroid: Asteroid
    daily_rate_kg: float = settings.MINING_RATE_KG_PER_DAY
    cargo_capacity_kg: float = settings.CARGO_CAPACITY_KG

    # Ore grade
    ore_grade_pct: float = 0.0        # current grade (degrades over time)
    base_ore_grade: float = 0.0       # initial grade at current site
    grade_degradation_rate: float = 0.005  # fraction lost per mining day

    # Site stability
    site_stability: float = 1.0       # 1.0 = stable, 0.0 = unusable
    stability_decay_rate: float = 0.02  # lost per mining day

    # Repositioning
    repositioning_days: int = 0       # >0 = currently repositioning
    repositioning_total: int = 0      # total days for current repositioning
    total_repositions: int = 0        # count of repositioning events

    # Counters
    days_mined: int = 0
    total_mined_kg: float = 0.0
    total_ore_kg: float = 0.0
    total_revenue: float = 0.0
    refinery_enabled: bool = False

    # Daily records
    daily_yields: list[DailyYield] = field(default_factory=list)

    def is_container_full(self) -> bool:
        return self.total_ore_kg >= self.cargo_capacity_kg

    def days_to_fill_container(self) -> int:
        """Estimate days needed to fill cargo at current rate/grade."""
        if self.ore_grade_pct <= 0:
            return 999_999
        if self.refinery_enabled:
            daily_pgm = self.daily_rate_kg * self.ore_grade_pct * 0.15
            if daily_pgm <= 0:
                return 999_999
            remaining = self.cargo_capacity_kg - self.total_ore_kg
            return max(0, int(remaining / daily_pgm)) + 1
        daily_ore = self.daily_rate_kg * self.ore_grade_pct
        if daily_ore <= 0:
            return 999_999
        remaining = self.cargo_capacity_kg - self.total_ore_kg
        return max(0, int(remaining / daily_ore)) + 1

    def needs_repositioning(self) -> bool:
        """Check if the current site requires repositioning."""
        if self.site_stability < 0.3:
            return True
        if self.base_ore_grade > 0 and (self.ore_grade_pct / self.base_ore_grade) < 0.25:
            return True
        return False


# ─── element value lookup ──────────────────────────────────────────────────

ELEMENT_PRICES: dict[str, float] = {
    "Gold":      135_614.87,
    "Silver":      2_119.05,
    "Platinum":   54_720.49,
    "Palladium":  41_345.80,
    "Rhodium":   234_442.90,
    "Iridium":   186_474.06,
    "Ruthenium":  15_110.83,
    "Osmium":    385_808.40,
    "Copper":      12.89,
    "Zinc":         1.98,
    "Lead":         1.98,
    "Tin":         50.44,
    "Nickel":      15.20,
    "Cobalt":      25.40,
    "Lithium":     12.00,
    "Iron":         0.10,
    "Silicon":      2.00,
    "Magnesium":    2.50,
    "Aluminum":     3.45,
    "Titanium":    30.00,
}


def get_element_price(element_name: str) -> float:
    """Price per kg for a given element. Falls back to 5.00 USD."""
    return ELEMENT_PRICES.get(element_name, 5.00)


# ─── ore grade estimation ─────────────────────────────────────────────────

def estimate_ore_grade(asteroid: Asteroid) -> float:
    """Estimate the ore grade (valuable fraction) for an asteroid."""
    if asteroid.class_ == "M":
        return random.uniform(0.01, 0.05)
    elif asteroid.class_ == "C":
        return random.uniform(0.005, 0.02)
    else:
        return random.uniform(0.002, 0.01)


# ─── event pools for mining (base events that always can happen) ──────────

MINING_BASE_EVENTS = [
    (10, "micrometeoroid", "Micrometeoroid impact — minor hull damage", "warning"),
    (8, "power_spike", "Power spike — systems stabilized", "warning"),
    (7, "sensor_glitch", "Sensor glitch — recalibrated", "info"),
    (6, "thermal_fluctuation", "Thermal fluctuation — efficiency dip 2%", "info"),
    (5, "vibration", "Equipment vibration anomaly — dampeners engaged", "info"),
    (4, "comms_interrupt", "Communication interruption — relay restored", "info"),
    (3, "repair_bot", "Repair bot cycle — minor maintenance completed", "info"),
]


# ─── daily simulation ─────────────────────────────────────────────────────

def simulate_mining_day(state: MiningState) -> DailyYield:
    """Advance mining by one day and return the yield record.

    Handles:
      - Repositioning (no mining if repositioning_days > 0)
      - Ore grade degradation
      - Site stability decay
      - Rich ore pockets (temporary grade boost)
      - 0-3 events per day
      - Automatic repositioning trigger when site degrades
    """
    state.days_mined += 1

    # ── Initialize ore grade on first mining day ───────────────────
    if state.ore_grade_pct == 0.0:
        state.ore_grade_pct = estimate_ore_grade(state.asteroid)
        state.base_ore_grade = state.ore_grade_pct

    # ── Handle repositioning ───────────────────────────────────────
    if state.repositioning_days > 0:
        state.repositioning_days -= 1
        repo_day = state.repositioning_total - state.repositioning_days
        yield_record = DailyYield(
            day=state.days_mined,
            total_mined_kg=0.0,
            element_breakdown={},
            daily_revenue=0.0,
            events=[repositioning_event(state.days_mined, repo_day, state.repositioning_total)],
        )
        # When repositioning finishes, reset site quality
        if state.repositioning_days == 0:
            _reset_site(state)
            yield_record.events.append({
                "type": "reposition_complete",
                "description": f"[Mining Day {state.days_mined}] Repositioning complete — mining resumed at new site (grade: {state.ore_grade_pct*100:.2f}%)",
                "severity": "info",
            })
        state.daily_yields.append(yield_record)
        return yield_record

    # ── Check if repositioning is needed before mining ──────────────
    if state.needs_repositioning():
        return _trigger_repositioning(state)

    # ── Degrade ore grade ──────────────────────────────────────────
    state.ore_grade_pct *= (1.0 - state.grade_degradation_rate)
    state.site_stability -= state.stability_decay_rate

    # ── Rich ore pocket? (random grade boost) ──────────────────────
    rich_pocket = False
    if random.random() < 0.08:  # 8% chance
        state.ore_grade_pct = min(state.base_ore_grade, state.ore_grade_pct * (2.0 + random.random()))
        rich_pocket = True

    # ── Extract ore ────────────────────────────────────────────────
    raw_mass = state.daily_rate_kg
    ore_mass = raw_mass * state.ore_grade_pct
    elements = state.asteroid.elements
    total_elem_mass = sum(e.mass_kg for e in elements)
    element_breakdown: dict[str, dict] = {}
    daily_revenue = 0.0

    if total_elem_mass > 0 and elements:
        scored = []
        for e in elements:
            price = get_element_price(e.name)
            scored.append((e, price, e.mass_kg * price))
        scored.sort(key=lambda x: -x[2])
        top_scored = scored[:15]
        total_scored_mass = sum(elem.mass_kg for elem, _, _ in top_scored)
        for elem, price, _ in top_scored:
            fraction = elem.mass_kg / total_scored_mass if total_scored_mass > 0 else 0
            elem_in_ore = ore_mass * fraction
            if elem_in_ore < 0.001:
                continue
            value = elem_in_ore * price
            element_breakdown[elem.name] = {
                "mass_kg": round(elem_in_ore, 4),
                "value": round(value, 2),
            }
            daily_revenue += value

    state.total_mined_kg += raw_mass

    # ── On-site refinery ───────────────────────────────────────────
    if state.refinery_enabled:
        refined_breakdown = {
            name: data for name, data in element_breakdown.items()
            if name in PRECIOUS_METALS
        }
        refined_ore_mass = sum(d["mass_kg"] for d in refined_breakdown.values())
        refined_revenue = sum(d["value"] for d in refined_breakdown.values())
        ore_mass = refined_ore_mass
        daily_revenue = refined_revenue
        element_breakdown = refined_breakdown

    state.total_ore_kg += ore_mass
    state.total_revenue += daily_revenue

    # ── Build yield record with events ─────────────────────────────
    events: list[dict] = []

    # Base mining events (0-2 per day)
    num_base = 0
    roll = random.random()
    if roll < 0.30:
        num_base = 1
    if roll < 0.10:
        num_base = 2
    for _ in range(num_base):
        ev = _pick_weighted(MINING_BASE_EVENTS)
        events.append({
            "type": ev[1],
            "description": f"[Mining Day {state.days_mined}] {ev[2]}",
            "severity": ev[3],
        })

    # Extra events from events module (0-2 per day)
    events.extend(_mining_extras(state.days_mined))

    # Rich pocket event
    if rich_pocket:
        events.append({
            "type": "rich_pocket",
            "description": f"[Mining Day {state.days_mined}] Rich ore pocket struck — grade boosted to {state.ore_grade_pct*100:.2f}%",
            "severity": "info",
        })

    # Low stability warning
    if state.site_stability < 0.4:
        events.append({
            "type": "site_unstable",
            "description": f"[Mining Day {state.days_mined}] ⚠️ Site stability critical ({state.site_stability:.0%}) — repositioning may be required",
            "severity": "warning",
        })

    yield_record = DailyYield(
        day=state.days_mined,
        total_mined_kg=raw_mass,
        element_breakdown=element_breakdown,
        daily_revenue=round(daily_revenue, 2),
        events=events,
    )

    state.daily_yields.append(yield_record)
    return yield_record


def _trigger_repositioning(state: MiningState) -> DailyYield:
    """Begin repositioning to a new mining site."""
    state.total_repositions += 1
    state.repositioning_total = random.randint(2, 5)
    state.repositioning_days = state.repositioning_total
    # Day 1 of repositioning
    state.repositioning_days -= 1
    yield_record = DailyYield(
        day=state.days_mined,
        total_mined_kg=0.0,
        element_breakdown={},
        daily_revenue=0.0,
        events=[repositioning_event(state.days_mined, 1, state.repositioning_total)],
    )
    state.daily_yields.append(yield_record)
    return yield_record


def _reset_site(state: MiningState):
    """Reset site quality after repositioning."""
    state.ore_grade_pct = estimate_ore_grade(state.asteroid)
    state.base_ore_grade = state.ore_grade_pct
    state.site_stability = 1.0
    # Slight degradation each time you reposition (site gets worse)
    state.base_ore_grade *= max(0.5, 1.0 - (state.total_repositions * 0.08))
    state.ore_grade_pct = state.base_ore_grade


# ─── weighted pick ───────────────────────────────────────────────────────

def _pick_weighted(pool: list[tuple]) -> tuple:
    """Pick an item from a weighted list."""
    total = sum(w for w, *_ in pool)
    r = random.uniform(0, total)
    upto = 0
    for w, *rest in pool:
        upto += w
        if r <= upto:
            return (w, *rest)
    return pool[-1]


# ─── run full mining operation ──────────────────────────────────────────

def run_mining_operation(asteroid: Asteroid,
                         max_days: int = 200,
                         seed: Optional[int] = None,
                         refinery: bool = False) -> MiningState:
    """Run a full mining operation up to max_days or until container full.

    Args:
        asteroid: The asteroid to mine.
        max_days: Maximum days to mine before stopping.
        seed: RNG seed for deterministic results.
        refinery: If True, on-site processing extracts only PGMs.
    """
    if seed is not None:
        random.seed(seed)

    state = MiningState(asteroid=asteroid, refinery_enabled=refinery)

    for _ in range(max_days):
        simulate_mining_day(state)
        if state.is_container_full():
            break

    return state
