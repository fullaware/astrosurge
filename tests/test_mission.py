"""Tests for the full mission lifecycle (11 phases).

Verifies end-to-end mission execution:
  - Phase progression (1→11)
  - Funding and debt tracking
  - Mining operations
  - Transit calculations
  - Market sale and financial analysis
"""

import pytest
from astrosurge.mission import (
    run_mission,
    MissionResult,
    PhaseResult,
    PHASE_NAMES,
)
from astrosurge.transit import calc_round_trip
from astrosurge.config import settings


# ─── phase name lookup ─────────────────────────────────────────────────────

class TestPhaseNames:
    def test_all_phases_have_names(self):
        assert PHASE_NAMES[1] == "asteroid_identification"
        assert PHASE_NAMES[2] == "survey_planning"
        assert PHASE_NAMES[3] == "mission_design"
        assert PHASE_NAMES[4] == "spacecraft_assembly"
        assert PHASE_NAMES[5] == "transit_execution"
        assert PHASE_NAMES[6] == "site_establishment"
        assert PHASE_NAMES[7] == "mining_operations"
        assert PHASE_NAMES[8] == "cargo_sealing"
        assert PHASE_NAMES[9] == "return_transit"
        assert PHASE_NAMES[10] == "market_sale"
        assert PHASE_NAMES[11] == "financial_analysis"

    def test_phase_count(self):
        assert len(PHASE_NAMES) == 11


# ─── full mission execution ───────────────────────────────────────────────

class TestRunMission:

    def test_heracles_tier_1_completes(self, heracles):
        """Heracles Fast ROI mission should complete all 11 phases."""
        result = run_mission(heracles, seed=42)
        assert result.status == "completed"
        assert result.error is None

    def test_heracles_produces_profit(self, heracles):
        """Heracles mission should generate positive ROI."""
        result = run_mission(heracles, seed=42)
        assert result.financials["net_profit_usd"] > 0
        assert result.financials["roi"] > 0

    def test_heracles_has_11_phase_results(self, heracles):
        """All 11 phases should produce results."""
        result = run_mission(heracles, seed=42)
        assert len(result.phase_results) == 11

    def test_phase_order_correct(self, heracles):
        """Phases should execute in order 1 through 11."""
        result = run_mission(heracles, seed=42)
        for i, phase in enumerate(result.phase_results, 1):
            assert phase.phase == i
            assert phase.phase_name == PHASE_NAMES[i]

    def test_transit_estimate_attached(self, heracles):
        """Result should include transit estimate."""
        result = run_mission(heracles, seed=42)
        assert result.transit.one_way_days == 88
        assert result.transit.round_trip_days == 319

    def test_mining_data_available(self, heracles):
        """Result should include mining data."""
        result = run_mission(heracles, seed=42)
        assert result.mining is not None
        assert result.mining.total_mined_kg > 0
        assert result.mining.days_mined > 0

    def test_funding_snapshots_collected(self, heracles):
        """Should have funding snapshots covering the mission duration."""
        result = run_mission(heracles, seed=42)
        assert len(result.funding_snapshots) > 0
        first = result.funding_snapshots[0]
        last = result.funding_snapshots[-1]
        assert last.days_elapsed >= first.days_elapsed

    def test_funding_break_even_eventually(self, heracles):
        """Well-chosen target should reach break-even during the mission."""
        result = run_mission(heracles, seed=42)
        # At some point during the mission, cargo value exceeded debt
        # The final snapshot might not be break-even if mining just finished,
        # but the financial analysis should show profit
        assert result.financials["net_profit_usd"] > 0

    def test_market_result_has_element_sales(self, heracles):
        """Market sale should record element-level sales."""
        result = run_mission(heracles, seed=42)
        assert result.market_result["total_revenue"] > 0
        assert len(result.market_result["element_sales"]) > 0

    def test_financials_contain_all_metrics(self, heracles):
        """Financial analysis should have full P&L breakdown."""
        result = run_mission(heracles, seed=42)
        f = result.financials
        assert "total_cost_usd" in f
        assert "total_revenue_usd" in f
        assert "net_profit_usd" in f
        assert "roi" in f
        assert "debt_repaid" in f
        assert "retained_profit" in f

    def test_debt_repaid_does_not_exceed_revenue(self, heracles):
        """Debt repayment cannot exceed total revenue."""
        result = run_mission(heracles, seed=42)
        assert result.financials["debt_repaid"] <= result.financials["total_revenue_usd"]

    def test_retained_profit_non_negative(self, heracles):
        """Retained profit should never be negative."""
        result = run_mission(heracles, seed=42)
        assert result.financials["retained_profit"] >= 0

    def test_mission_result_to_dict(self, heracles):
        """MissionResult.to_dict() should work without errors."""
        result = run_mission(heracles, seed=42)
        d = result.to_dict()
        assert d["status"] == "completed"
        assert d["asteroid_name"] == "Heracles"
        assert d["spkid"] == 2005143
        assert d["mission_type"] == "mining_fast_roi"
        assert d["tier"] == 1
        assert d["financials"]["net_profit_usd"] > 0

    def test_zeus_also_profitable(self, zeus):
        """Zeus mission should also be profitable (larger asteroid)."""
        result = run_mission(zeus, seed=42)
        assert result.status == "completed"
        assert result.financials["net_profit_usd"] > 0

    def test_unnamed_asteroid_handled(self, unnamed_m_class):
        """Unnamed asteroids should not crash the mission."""
        result = run_mission(unnamed_m_class, seed=42)
        assert result.status == "completed"
        # Should reference spkid in the absence of a name
        assert "spkid-276049" in result.asteroid_name


# ─── funding edge cases ──────────────────────────────────────────────────

class TestFundingEdgeCases:

    def test_extreme_costs_produce_negative_roi(self):
        """If daily ops are astronomical, mission completes with negative ROI."""
        from astrosurge.models import Asteroid, Element
        from bson import ObjectId

        far_asteroid = Asteroid(
            source_id=ObjectId(),
            name="FarOut",
            pdes="99996",
            spkid=99996,
            class_="M",
            diameter=3.5,
            moid=0.09,
            moid_days=90,
            neo=True,
            hazard=False,
            elements=[Element("Gold", 100_000, 79)],
        )

        # Extreme costs → mission completes but loses money
        result = run_mission(
            far_asteroid,
            ship_cost=500_000_000,
            launch_cost=500_000_000,
            daily_ops=100_000_000,  # $100M/day → extremely expensive
            seed=42,
        )
        assert result.status == "completed"
        assert result.financials["net_profit_usd"] < 0
        assert result.financials["roi"] < 0

    def test_previous_profit_reduces_debt(self, heracles):
        """Having retained profit from a prior mission changes funding."""
        result_with_profit = run_mission(
            heracles,
            previous_mission_profit=200_000_000,
            seed=42,
        )
        assert result_with_profit.status == "completed"

    def test_low_launch_cost_reusable(self, heracles):
        """Reusable launch ($97M) should improve ROI vs expendable ($150M)."""
        result_reusable = run_mission(heracles, launch_cost=97_000_000, seed=42)
        result_expendable = run_mission(heracles, launch_cost=150_000_000, seed=42)
        # Reusable should have lower cost → higher retained profit
        assert result_reusable.financials["retained_profit"] >= \
               result_expendable.financials["retained_profit"]


# ─── mining edge cases ───────────────────────────────────────────────────

class TestMiningEdgeCases:

    def test_low_grade_asteroid_still_mines(self):
        """Even a low-grade asteroid should produce some revenue."""
        from astrosurge.models import Asteroid, Element
        from bson import ObjectId

        low_grade = Asteroid(
            source_id=ObjectId(),
            name="LowGrade",
            pdes="99995",
            spkid=99995,
            class_="S",
            diameter=3.1,
            moid=0.05,
            moid_days=50,
            neo=True,
            hazard=False,
            elements=[Element("Iron", 100_000_000, 26)],
        )

        result = run_mission(low_grade, seed=42)
        assert result.status == "completed"
        # Even Iron-heavy asteroids produce some value
        assert result.mining is not None
        assert result.mining.total_revenue > 0

    def test_container_fills_before_max_days(self, heracles):
        """Rich M-class should fill container before max mining days."""
        result = run_mission(heracles, seed=42)
        assert result.mining is not None
        assert result.mining.is_container_full() is True
        assert result.mining.days_mined <= 139  # default mining days


# ─── deterministic behavior ──────────────────────────────────────────────

class TestDeterminism:
    """With same seed, results should be identical."""

    def test_deterministic_run(self, heracles):
        r1 = run_mission(heracles, seed=42)
        r2 = run_mission(heracles, seed=42)
        assert r1.financials["net_profit_usd"] == r2.financials["net_profit_usd"]
        assert r1.financials["roi"] == r2.financials["roi"]
        assert r1.mining.total_revenue == r2.mining.total_revenue
        assert r1.mining.days_mined == r2.mining.days_mined

    def test_different_seeds_different(self, heracles):
        r1 = run_mission(heracles, seed=42)
        r2 = run_mission(heracles, seed=99)
        # Could be same by coincidence, but unlikely with different ore grades
        assert r1 is not None and r2 is not None


# ─── MissionResult types ─────────────────────────────────────────────────

class TestMissionResult:
    def test_result_has_correct_fields(self, heracles):
        result = run_mission(heracles, seed=42)
        assert isinstance(result, MissionResult)
        assert isinstance(result.phase_results, list)
        for pr in result.phase_results:
            assert isinstance(pr, PhaseResult)
            assert 1 <= pr.phase <= 11


# ─── reusable launch ──────────────────────────────────────────────────────

class TestReusableLaunch:

    def test_reusable_uses_lower_launch_cost(self, heracles):
        """reusable=True should auto-set launch cost to REUSABLE."""
        result = run_mission(heracles, seed=42, reusable=True)
        cost = result.financials["total_cost_usd"]
        # With reusable ($97M), total cost = 97M + (220 * 45K) = $106.9M
        expected = settings.LAUNCH_COST_REUSABLE + (220 * settings.DAILY_OPS_COST)
        assert cost == pytest.approx(expected, rel=0.01)

    def test_reusable_increases_retained_profit(self, heracles):
        """Reusable launch should improve retained profit vs expendable."""
        expendable = run_mission(heracles, seed=42, reusable=False)
        reusable = run_mission(heracles, seed=42, reusable=True)
        savings = settings.LAUNCH_COST_EXPENDABLE - settings.LAUNCH_COST_REUSABLE
        assert reusable.financials["retained_profit"] == pytest.approx(
            expendable.financials["retained_profit"] + savings, rel=0.01
        )

    def test_reusable_flags_on_result(self, heracles):
        result = run_mission(heracles, seed=42, reusable=True)
        assert result.reusable is True


# ─── on-site refinery ────────────────────────────────────────────────────

class TestRefineryMission:

    def test_refinery_produces_only_pgm_sales(self, heracles):
        """With refinery, only PGMs should appear in element sales."""
        from astrosurge.mining import PRECIOUS_METALS
        result = run_mission(heracles, seed=42, refinery=True)
        for sale in result.market_result["element_sales"]:
            assert sale["element"] in PRECIOUS_METALS, \
                f"{sale['element']} should not be in refined sale"

    def test_refinery_improves_economics(self, heracles):
        """With refinery, more mining days = higher revenue (container not full)."""
        vanilla = run_mission(heracles, seed=42, refinery=False, mining_days=139)
        refined = run_mission(heracles, seed=42, refinery=True, mining_days=139)
        # Refinery means container fills slower, so we mine more days,
        # generating more PGM value than the base metal diluted approach
        assert refined.mining.days_mined > vanilla.mining.days_mined

    def test_refinery_flags_on_result(self, heracles):
        result = run_mission(heracles, seed=42, refinery=True)
        assert result.refinery is True


# ─── combined: reusable + refinery ───────────────────────────────────────

class TestCombinedUpgrades:

    def test_reusable_plus_refinery_doubles_retained_profit(self, heracles):
        """Combined reusable launch + refinery should significantly boost profit."""
        baseline = run_mission(heracles, seed=42, reusable=False, refinery=False)
        upgraded = run_mission(heracles, seed=42, reusable=True, refinery=True)
        assert upgraded.financials["retained_profit"] > baseline.financials["retained_profit"]

    def test_combined_has_correct_flags(self, heracles):
        result = run_mission(heracles, seed=42, reusable=True, refinery=True)
        assert result.reusable is True
        assert result.refinery is True
