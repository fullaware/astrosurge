"""Transit time model for asteroid mining missions.

Uses a MOID-based heuristic since the asteroid database contains
no orbital elements (semi-major axis, eccentricity, inclination).

Formula (PRD v2.0):
    transit_days_one_way = 30 + (moid_au × 1000)
    round_trip_days = (transit_days_one_way × 2) + setup_days + mining_days + prep_days
"""

from dataclasses import dataclass


# Default phase durations (from PRD / Full Aware article)
DEFAULT_SETUP_DAYS = 3
DEFAULT_MINING_DAYS_TO_FILL = 139   # 50 000 kg ÷ 36 000 kg/day ≈ 1.39 → rounded to 139
DEFAULT_PREP_DAYS = 1


@dataclass(frozen=True)
class TransitLeg:
    """Result for one leg (outbound or return)."""
    days: int
    moid_au: float


@dataclass(frozen=True)
class TransitEstimate:
    """Complete round-trip transit estimate."""
    one_way_days: int
    round_trip_days: int
    setup_days: int
    mining_days: int
    prep_days: int
    outbound: TransitLeg
    return_: TransitLeg


def calc_one_way(moid_au: float) -> int:
    """Calculate one-way transit days from MOID.

    >>> calc_one_way(0.0584)   # Heracles
    88
    >>> calc_one_way(0.0036)   # Midas
    34
    >>> calc_one_way(0.1486)   # Eros
    179
    >>> calc_one_way(0.0)      # minimum
    30
    """
    return max(30, int(round(30 + (moid_au * 1000))))


def calc_round_trip(
    moid_au: float,
    setup_days: int = DEFAULT_SETUP_DAYS,
    mining_days: int = DEFAULT_MINING_DAYS_TO_FILL,
    prep_days: int = DEFAULT_PREP_DAYS,
) -> TransitEstimate:
    """Calculate complete round-trip estimate.

    round_trip_days = (one_way × 2) + setup + mining + prep

    Returns a realistic (uncapped) estimate. The caller may cap the actual
    mining days during execution to enforce a maximum mission duration.
    """
    one_way = calc_one_way(moid_au)
    outbound = TransitLeg(days=one_way, moid_au=moid_au)
    return_ = TransitLeg(days=one_way, moid_au=moid_au)

    round_trip = (one_way * 2) + setup_days + mining_days + prep_days

    return TransitEstimate(
        one_way_days=one_way,
        round_trip_days=round_trip,
        setup_days=setup_days,
        mining_days=mining_days,
        prep_days=prep_days,
        outbound=outbound,
        return_=return_,
    )


def days_remaining(estimated_total_days: int, days_elapsed: int) -> int:
    """Return remaining days at a point in the mission."""
    return max(0, estimated_total_days - days_elapsed)
