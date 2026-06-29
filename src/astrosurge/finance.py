"""Funding, cost tracking, and ROI calculations.

Funding model (PRD v2.0):
  - First mission: baseline funding from investors ($150M expendable or $97M reusable)
  - Each mission: funding pool = ship + launch + daily_ops × total_days
  - Debt owed increases each day as ops costs are deducted
  - Break-even: cargo_value >= debt_owed
  - Funding runs out = mission failure
"""

from dataclasses import dataclass, field
from typing import Optional

from .config import settings


# ─── funding snapshot ──────────────────────────────────────────────────────

@dataclass
class FundingSnapshot:
    """Snapshot of financial state at a point in time."""
    funding_pool: float
    funding_remaining: float
    debt_owed: float
    cumulative_ops_cost: float
    cargo_value: float
    daily_roi: float  # (cargo_value - debt_owed) / debt_owed if debt > 0
    is_break_even: bool
    days_elapsed: int

    def to_dict(self) -> dict:
        return {
            "funding_pool": round(self.funding_pool, 2),
            "funding_remaining": round(self.funding_remaining, 2),
            "debt_owed": round(self.debt_owed, 2),
            "cumulative_ops_cost": round(self.cumulative_ops_cost, 2),
            "cargo_value": round(self.cargo_value, 2),
            "daily_roi": round(self.daily_roi, 4),
            "is_break_even": self.is_break_even,
            "days_elapsed": self.days_elapsed,
        }


# ─── funding calculator ────────────────────────────────────────────────────

@dataclass
class MissionFinances:
    """Tracks funding and financial state through a mission."""

    ship_cost: float = 0.0
    launch_cost: float = settings.LAUNCH_COST_EXPENDABLE
    daily_ops_cost: float = settings.DAILY_OPS_COST
    total_days_estimated: int = 0

    # Internal state
    _funding_pool: float = 0.0
    _debt_owed: float = 0.0
    _cumulative_ops: float = 0.0
    _days_elapsed: int = 0
    _cargo_value: float = 0.0
    _previous_mission_profit: float = 0.0

    def secure_funding(self) -> float:
        """Calculate and secure the total funding pool.

        First mission: baseline investor funding.
        Subsequent missions: funded from previous profit first, investors for remainder.
        """
        total_needed = self.ship_cost + self.launch_cost + (
            self.daily_ops_cost * self.total_days_estimated
        )

        # First mission (no prior profit) gets full investor funding
        if self._previous_mission_profit <= 0:
            self._funding_pool = total_needed
        else:
            # Fund from retained profit first
            self._funding_pool = max(total_needed, self._previous_mission_profit)

        self._debt_owed = 0.0
        self._cumulative_ops = 0.0
        return self._funding_pool

    def advance_day(self, days: int = 1) -> list[FundingSnapshot]:
        """Advance the mission by N days, deducting ops costs.

        Returns a snapshot for each day.
        """
        snapshots = []
        for _ in range(days):
            self._days_elapsed += 1
            self._cumulative_ops += self.daily_ops_cost
            self._debt_owed += self.daily_ops_cost

            snapshots.append(self._compute_snapshot())

        return snapshots

    def update_cargo_value(self, value: float):
        """Set the current cargo market value."""
        self._cargo_value = value

    def funding_remaining(self) -> float:
        return max(0.0, self._funding_pool - self._debt_owed)

    def is_funding_critical(self, threshold_pct: float = 0.10) -> bool:
        """Funding below threshold % of original pool."""
        if self._funding_pool <= 0:
            return True
        return self.funding_remaining() / self._funding_pool < threshold_pct

    def has_funding_run_out(self) -> bool:
        return self._debt_owed >= self._funding_pool

    def is_break_even(self) -> bool:
        return self._cargo_value >= self._debt_owed

    def _compute_snapshot(self) -> FundingSnapshot:
        debt = self._debt_owed
        remaining = max(0.0, self._funding_pool - debt)
        daily_roi = (
            (self._cargo_value - debt) / debt if debt > 0 else 0.0
        )
        return FundingSnapshot(
            funding_pool=self._funding_pool,
            funding_remaining=remaining,
            debt_owed=debt,
            cumulative_ops_cost=self._cumulative_ops,
            cargo_value=self._cargo_value,
            daily_roi=daily_roi,
            is_break_even=self._cargo_value >= debt,
            days_elapsed=self._days_elapsed,
        )

    def finalize(self, total_revenue: float) -> dict:
        """Calculate final financial metrics for a completed mission.

        Returns:
            {
                "total_cost_usd": float,
                "total_revenue_usd": float,
                "net_profit_usd": float,
                "roi": float,
                "break_even_price_per_kg": float,
                "debt_repaid": float,
                "retained_profit": float,
            }
        """
        total_cost = self.ship_cost + self.launch_cost + self._cumulative_ops
        profit = total_revenue - total_cost
        roi = profit / total_cost if total_cost > 0 else 0.0

        # Repay full investment (ship + launch + ops) first
        # remaining is retained profit for the next mission
        total_investment = self.ship_cost + self.launch_cost + self._debt_owed
        debt_repaid = min(total_revenue, total_investment)
        retained = total_revenue - debt_repaid

        return {
            "total_cost_usd": round(total_cost, 2),
            "total_revenue_usd": round(total_revenue, 2),
            "net_profit_usd": round(profit, 2),
            "roi": round(roi, 4),
            "debt_repaid": round(debt_repaid, 2),
            "retained_profit": round(retained, 2),
        }


def estimate_minimum_funding(ship_cost: float,
                              launch_cost: float = settings.LAUNCH_COST_EXPENDABLE,
                              daily_ops: float = settings.DAILY_OPS_COST,
                              total_days: int = 417) -> float:
    """Estimate the minimum funding required for a mission."""
    return ship_cost + launch_cost + (daily_ops * total_days)
