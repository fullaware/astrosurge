"""Asteroid selection and scoring for mining missions.

Core Fast ROI (Tier 1) strategy:
    Score by (estimated_value - total_cost) / transit_days

Criteria:
    - MOID < 0.1 AU
    - Diameter > 3 km
    - Class M (PGM) / C (ice) depending on tier
    - Non-hazardous preferred
"""

from dataclasses import dataclass
from typing import Optional

from .models import Asteroid
from .transit import calc_one_way, calc_round_trip


# ─── configuration ─────────────────────────────────────────────────────────

FAST_ROI_MAX_MOID_AU = 0.10
FAST_ROI_MIN_DIAMETER_KM = 3.0
FAST_ROI_PREFERRED_CLASSES = ("M",)


# ─── scoring result ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ScoreCard:
    asteroid_name: Optional[str]
    spkid: int
    class_: str
    diameter: float
    moid: float
    hazard: bool
    transit_days_one_way: int
    estimated_value: float
    estimated_cost: float
    score: float  # (value - cost) / transit_days

    def to_dict(self) -> dict:
        return {
            "name": self.asteroid_name,
            "spkid": self.spkid,
            "class": self.class_,
            "diameter_km": self.diameter,
            "moid_au": self.moid,
            "hazard": self.hazard,
            "transit_days_one_way": self.transit_days_one_way,
            "estimated_value_usd": round(self.estimated_value, 2),
            "estimated_cost_usd": round(self.estimated_cost, 2),
            "score": round(self.score, 4),
        }


# ─── helpers ───────────────────────────────────────────────────────────────

def estimate_asteroid_value(asteroid: Asteroid) -> float:
    """Rough value estimate based on class, diameter, and elements.

    For M-class: PGM-rich, high value density.
    For C-class: water/volatiles, lower value per kg.
    """
    if asteroid.class_ == "M":
        # Assume ~$500M–$2B for typical 3–5 km M-class
        return asteroid.diameter ** 3 * 15_000_000  # cubic scaling
    elif asteroid.class_ == "C":
        return asteroid.diameter ** 3 * 2_000_000
    else:
        return asteroid.diameter ** 3 * 1_000_000


def estimate_mission_cost(asteroid: Asteroid, launch_cost: float = 150_000_000,
                          daily_ops: float = 45_000) -> float:
    """Rough cost estimate for a Fast ROI (Tier 1) mission."""
    one_way = calc_one_way(asteroid.moid)
    est = calc_round_trip(asteroid.moid)
    return launch_cost + (est.round_trip_days * daily_ops)


# ─── filtering ─────────────────────────────────────────────────────────────

def passes_fast_roi_filter(asteroid: Asteroid) -> bool:
    """Check if an asteroid meets Fast ROI criteria."""
    if asteroid.moid >= FAST_ROI_MAX_MOID_AU:
        return False
    if asteroid.diameter < FAST_ROI_MIN_DIAMETER_KM:
        return False
    if asteroid.class_ not in FAST_ROI_PREFERRED_CLASSES:
        return False
    return True


def score_fast_roi(asteroid: Asteroid, launch_cost: float = 150_000_000,
                   daily_ops: float = 45_000) -> Optional[ScoreCard]:
    """Score an asteroid for Fast ROI (Tier 1). Returns None if it fails filters."""
    if not passes_fast_roi_filter(asteroid):
        return None

    value = estimate_asteroid_value(asteroid)
    cost = estimate_mission_cost(asteroid, launch_cost, daily_ops)
    one_way = calc_one_way(asteroid.moid)
    score = (value - cost) / one_way if one_way > 0 else 0.0

    return ScoreCard(
        asteroid_name=asteroid.name,
        spkid=asteroid.spkid,
        class_=asteroid.class_,
        diameter=asteroid.diameter,
        moid=asteroid.moid,
        hazard=asteroid.hazard,
        transit_days_one_way=one_way,
        estimated_value=value,
        estimated_cost=cost,
        score=score,
    )


def rank_fast_roi_candidates(asteroids: list[Asteroid],
                              launch_cost: float = 150_000_000,
                              daily_ops: float = 45_000) -> list[ScoreCard]:
    """Filter and rank potential targets for Fast ROI (Tier 1)."""
    scored = []
    for ast in asteroids:
        card = score_fast_roi(ast, launch_cost, daily_ops)
        if card is not None:
            scored.append(card)
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored
