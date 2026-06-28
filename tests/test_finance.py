"""Tests for funding, cost tracking, and ROI calculations.

Funding model (PRD v2.0):
  - First mission: $150M investor funding
  - Funding pool = ship + launch + daily_ops × total_days
  - Debt owed increases each day
  - Break-even: cargo_value >= debt_owed
  - Funding exhausted = mission failure
"""

import pytest
from astrosurge.finance import (
    MissionFinances,
    FundingSnapshot,
    estimate_minimum_funding,
)
from astrosurge.config import settings


class TestMissionFinances:

    def test_initial_state(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        snapshot = mf.advance_day(0)[-1] if mf.advance_day(0) else None
        # 0 days advanced → debt is 0
        mf2 = MissionFinances(total_days_estimated=319)
        mf2.secure_funding()
        snaps = mf2.advance_day(1)
        assert len(snaps) == 1
        assert snaps[0].debt_owed == settings.DAILY_OPS_COST

    def test_secure_funding_first_mission(self):
        """First mission gets baseline investor funding."""
        mf = MissionFinances(
            ship_cost=0,
            launch_cost=settings.LAUNCH_COST_EXPENDABLE,
            daily_ops_cost=settings.DAILY_OPS_COST,
            total_days_estimated=319,
        )
        pool = mf.secure_funding()
        expected = settings.LAUNCH_COST_EXPENDABLE + (settings.DAILY_OPS_COST * 319)
        assert pool == pytest.approx(expected)

    def test_secure_funding_subsequent_with_profit(self):
        """Subsequent mission funded from retained profit first."""
        mf = MissionFinances(
            ship_cost=50_000_000,
            launch_cost=settings.LAUNCH_COST_EXPENDABLE,
            daily_ops_cost=settings.DAILY_OPS_COST,
            total_days_estimated=319,
        )
        mf._previous_mission_profit = 200_000_000  # Previous profit
        pool = mf.secure_funding()
        # Pool should be at least what's needed
        assert pool >= mf.ship_cost + mf.launch_cost + (mf.daily_ops_cost * mf.total_days_estimated)

    def test_advance_one_day(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        snapshots = mf.advance_day(1)
        assert len(snapshots) == 1
        snap = snapshots[0]
        assert snap.days_elapsed == 1
        assert snap.debt_owed == settings.DAILY_OPS_COST
        assert snap.cumulative_ops_cost == settings.DAILY_OPS_COST

    def test_advance_multiple_days(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        snapshots = mf.advance_day(10)
        assert len(snapshots) == 10
        assert snapshots[-1].days_elapsed == 10
        assert snapshots[-1].debt_owed == settings.DAILY_OPS_COST * 10

    def test_funding_remaining_decreases(self):
        mf = MissionFinances(total_days_estimated=319)
        pool = mf.secure_funding()
        snapshots = mf.advance_day(5)
        remaining = snapshots[-1].funding_remaining
        assert remaining < pool
        assert remaining == pytest.approx(pool - (settings.DAILY_OPS_COST * 5))

    def test_cargo_value_updates_roi(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        mf.advance_day(100)
        debt = mf._debt_owed
        mf.update_cargo_value(debt * 2)  # Cargo worth twice debt
        snap = mf._compute_snapshot()
        assert snap.is_break_even is True
        assert snap.daily_roi == pytest.approx(1.0)  # (2x - 1x) / 1x = 1.0

    def test_cargo_value_below_debt(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        mf.advance_day(100)
        mf.update_cargo_value(mf._debt_owed * 0.5)  # Cargo worth half debt
        snap = mf._compute_snapshot()
        assert snap.is_break_even is False
        assert snap.daily_roi < 0

    def test_break_even_exact(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        mf.advance_day(100)
        mf.update_cargo_value(mf._debt_owed)  # Exactly break-even
        snap = mf._compute_snapshot()
        assert snap.is_break_even is True
        assert snap.daily_roi == pytest.approx(0.0)

    def test_funding_critical(self):
        mf = MissionFinances(total_days_estimated=319)
        pool = mf.secure_funding()
        # Advance most of the funding
        days_to_critical = int((pool * 0.95) / settings.DAILY_OPS_COST)
        mf.advance_day(days_to_critical)
        assert mf.is_funding_critical(threshold_pct=0.10) is True

    def test_funding_not_critical_early(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        mf.advance_day(1)
        assert mf.is_funding_critical(threshold_pct=0.10) is False

    def test_has_funding_run_out_after_exhaustion(self):
        mf = MissionFinances(ship_cost=0, launch_cost=1_000,
                              daily_ops_cost=100, total_days_estimated=100)
        mf.secure_funding()
        mf.advance_day(15)
        assert mf.has_funding_run_out() is False
        # After depleting all funding
        mf.advance_day(100)
        assert mf.has_funding_run_out() is True

    def test_finalize_successful_mission(self):
        mf = MissionFinances(
            ship_cost=50_000_000,
            launch_cost=settings.LAUNCH_COST_EXPENDABLE,
            daily_ops_cost=settings.DAILY_OPS_COST,
            total_days_estimated=319,
        )
        mf.secure_funding()
        mf.advance_day(200)

        result = mf.finalize(total_revenue=500_000_000)
        assert result["total_cost_usd"] > 0
        assert result["total_revenue_usd"] == 500_000_000
        assert result["net_profit_usd"] == result["total_revenue_usd"] - result["total_cost_usd"]
        assert result["roi"] > 0
        assert result["debt_repaid"] > 0
        assert result["retained_profit"] > 0

    def test_finalize_losing_mission(self):
        mf = MissionFinances(
            ship_cost=50_000_000,
            launch_cost=settings.LAUNCH_COST_EXPENDABLE,
            daily_ops_cost=settings.DAILY_OPS_COST,
            total_days_estimated=319,
        )
        mf.secure_funding()
        mf.advance_day(200)

        result = mf.finalize(total_revenue=10_000_000)
        assert result["net_profit_usd"] < 0
        assert result["roi"] < 0
        # All revenue goes to debt repayment, nothing retained
        assert result["retained_profit"] >= 0

    def test_daily_roi_negative_when_underwater(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        mf.advance_day(100)
        mf.update_cargo_value(1_000)  # Tiny cargo value
        snap = mf._compute_snapshot()
        assert snap.daily_roi < 0

    def test_daily_roi_positive_when_ahead(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        mf.advance_day(100)
        giant_cargo = mf._debt_owed * 5  # 5x debt
        mf.update_cargo_value(giant_cargo)
        snap = mf._compute_snapshot()
        assert snap.daily_roi > 0

    def test_snapshot_to_dict(self):
        mf = MissionFinances(total_days_estimated=319)
        mf.secure_funding()
        mf.advance_day(1)
        snap = mf._compute_snapshot()
        d = snap.to_dict()
        assert "funding_pool" in d
        assert "debt_owed" in d
        assert "cargo_value" in d
        assert "daily_roi" in d
        assert "is_break_even" in d
        assert "days_elapsed" in d


class TestEstimateMinimumFunding:

    def test_typical_funding(self):
        """Typical Tier 1 Fast ROI mission estimate."""
        funding = estimate_minimum_funding(
            ship_cost=0,
            launch_cost=settings.LAUNCH_COST_EXPENDABLE,
            total_days=319,
        )
        expected = settings.LAUNCH_COST_EXPENDABLE + (settings.DAILY_OPS_COST * 319)
        assert funding == pytest.approx(expected)

    def test_with_ship_cost(self):
        funding = estimate_minimum_funding(
            ship_cost=50_000_000,
            launch_cost=settings.LAUNCH_COST_EXPENDABLE,
            total_days=319,
        )
        expected = 50_000_000 + settings.LAUNCH_COST_EXPENDABLE + (settings.DAILY_OPS_COST * 319)
        assert funding == pytest.approx(expected)

    def test_shorter_mission_less_funding(self):
        long_mission = estimate_minimum_funding(ship_cost=0, total_days=400)
        short_mission = estimate_minimum_funding(ship_cost=0, total_days=200)
        assert short_mission < long_mission
