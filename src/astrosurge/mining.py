"""Mining operations simulation.

Daily extraction at 36 000 kg/day throughput.
Ore grade and element distribution determine yield composition.
"""

from dataclasses import dataclass, field
from typing import Optional
import random

from .models import Asteroid, Element, DailyYield
from .config import settings


# ─── precious metals for on-site refining ────────────────────────────────

# Metals targeted by the on-site refinery (high-value per kg)
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
    ore_grade_pct: float = 0.0  # fraction of mined mass that is valuable ore
    days_mined: int = 0
    total_mined_kg: float = 0.0
    total_ore_kg: float = 0.0  # valuable ore extracted (into container)
    total_revenue: float = 0.0
    refinery_enabled: bool = False  # on-site PGM separation
    daily_yields: list[DailyYield] = field(default_factory=list)

    def is_container_full(self) -> bool:
        return self.total_ore_kg >= self.cargo_capacity_kg

    def days_to_fill_container(self) -> int:
        """Estimate days needed to fill cargo at current rate/grade."""
        if self.ore_grade_pct <= 0:
            return 999_999
        if self.refinery_enabled:
            # With refinery, only PGMs go into the container,
            # so fill rate depends on the PGM fraction of the ore
            daily_pgm = self.daily_rate_kg * self.ore_grade_pct * 0.15  # ~15% of ore is PGM
            if daily_pgm <= 0:
                return 999_999
            remaining = self.cargo_capacity_kg - self.total_ore_kg
            return max(0, int(remaining / daily_pgm)) + 1
        daily_ore = self.daily_rate_kg * self.ore_grade_pct
        if daily_ore <= 0:
            return 999_999
        remaining = self.cargo_capacity_kg - self.total_ore_kg
        return max(0, int(remaining / daily_ore)) + 1


# ─── element value lookup ──────────────────────────────────────────────────

# Current market prices (USD per kg) — June 2026 reference
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


# ─── daily simulation ─────────────────────────────────────────────────────

def estimate_ore_grade(asteroid: Asteroid) -> float:
    """Estimate the ore grade (valuable fraction) for an asteroid.

    M-class asteroids tend to have higher PGM content.
    Returns a fraction (0.0–1.0).
    """
    if asteroid.class_ == "M":
        # Rich M-class: 1–5% ore grade
        return random.uniform(0.01, 0.05)
    elif asteroid.class_ == "C":
        # C-class: lower grade, water/volatiles
        return random.uniform(0.005, 0.02)
    else:
        return random.uniform(0.002, 0.01)


def simulate_mining_day(state: MiningState) -> DailyYield:
    """Advance mining by one day and return the yield record."""
    state.days_mined += 1

    # Determine ore grade for this asteroid if not set
    if state.ore_grade_pct == 0.0:
        state.ore_grade_pct = estimate_ore_grade(state.asteroid)

    raw_mass = state.daily_rate_kg
    ore_mass = raw_mass * state.ore_grade_pct
    gangue_mass = raw_mass - ore_mass

    # Distribute ore mass among elements proportional to their composition
    elements = state.asteroid.elements
    total_elem_mass = sum(e.mass_kg for e in elements)
    element_breakdown: dict[str, dict] = {}
    daily_revenue = 0.0

    if total_elem_mass > 0 and elements:
        # Only process top 15 elements by mass
        sorted_elems = sorted(elements, key=lambda e: -e.mass_kg)[:15]
        for elem in sorted_elems:
            fraction = elem.mass_kg / total_elem_mass
            elem_in_ore = ore_mass * fraction
            if elem_in_ore < 0.001:
                continue
            price = get_element_price(elem.name)
            value = elem_in_ore * price
            element_breakdown[elem.name] = {
                "mass_kg": round(elem_in_ore, 4),
                "value": round(value, 2),
            }
            daily_revenue += value

    state.total_mined_kg += raw_mass

    # On-site refinery: filter to precious metals only, discard base metals
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

    yield_record = DailyYield(
        day=state.days_mined,
        total_mined_kg=raw_mass,
        element_breakdown=element_breakdown,
        daily_revenue=round(daily_revenue, 2),
    )

    # Decide whether to add a random event (10% chance per day)
    if random.random() < 0.10:
        event_types = [
            ("micrometeoroid", "Micrometeoroid impact — minor hull damage"),
            ("thermal", "Thermal fluctuation — efficiency dip"),
            ("sensor", "Sensor malfunction — recalibrated"),
            ("power_spike", "Power spike — systems stabilized"),
        ]
        evt_type, desc = random.choice(event_types)
        yield_record.event = {"type": evt_type, "description": desc}

    state.daily_yields.append(yield_record)
    return yield_record


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
