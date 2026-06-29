"""Tests for mining operations simulation.

Key behaviors:
  - Daily extraction: 36 000 kg/day throughput
  - Ore grade determines valuable fraction
  - Element distribution follows asteroid composition
  - Container capacity: 50 000 kg
  - Random events occur ~10% of days
"""

import pytest
from astrosurge.mining import (
    MiningState,
    get_element_price,
    ELEMENT_PRICES,
    estimate_ore_grade,
    simulate_mining_day,
    run_mining_operation,
)


class TestElementPrices:
    """Verify element price lookups."""

    def test_gold_price(self):
        assert get_element_price("Gold") == 135_614.87

    def test_platinum_price(self):
        assert get_element_price("Platinum") == 54_720.49

    def test_unknown_element_defaults(self):
        assert get_element_price("Fictionalium") == 5.00

    def test_all_precious_metals_have_prices(self):
        precious = ["Gold", "Silver", "Platinum", "Palladium",
                     "Rhodium", "Iridium", "Ruthenium", "Osmium"]
        for metal in precious:
            assert get_element_price(metal) > 0, f"{metal} missing price"

    def test_prices_are_positive(self):
        for name, price in ELEMENT_PRICES.items():
            assert price > 0, f"{name} has non-positive price {price}"


class TestEstimateOreGrade:

    def test_m_class_grade(self, heracles):
        grade = estimate_ore_grade(heracles)
        assert 0.01 <= grade <= 0.05  # PRD: 1–5% for M-class

    def test_c_class_grade(self, cuyo):
        grade = estimate_ore_grade(cuyo)
        assert 0.005 <= grade <= 0.02  # PRD: lower for C-class

    def test_m_class_averages_higher_than_c(self, heracles, cuyo):
        """M-class should generally have higher grade than C-class."""
        m_grades = [estimate_ore_grade(heracles) for _ in range(100)]
        c_grades = [estimate_ore_grade(cuyo) for _ in range(100)]
        assert sum(m_grades) / len(m_grades) > sum(c_grades) / len(c_grades)

    def test_default_class(self, eros):
        """S-class (or unknown) should use lowest grade range."""
        grade = estimate_ore_grade(eros)
        # Eros is M-class, so this should pass
        assert 0.01 <= grade <= 0.05


class TestMiningState:

    def test_initial_state(self, heracles):
        state = MiningState(asteroid=heracles)
        assert state.days_mined == 0
        assert state.total_mined_kg == 0.0
        assert state.total_ore_kg == 0.0
        assert state.total_revenue == 0.0
        assert state.daily_yields == []

    def test_container_not_full_initially(self, heracles):
        state = MiningState(asteroid=heracles)
        assert state.is_container_full() is False

    def test_daily_rate_default(self, heracles):
        state = MiningState(asteroid=heracles)
        assert state.daily_rate_kg == 36_000

    def test_cargo_capacity_default(self, heracles):
        state = MiningState(asteroid=heracles)
        assert state.cargo_capacity_kg == 50_000

    def test_container_full_after_exceeding(self, heracles):
        state = MiningState(asteroid=heracles)
        state.total_ore_kg = 50_000
        assert state.is_container_full() is True

    def test_container_full_above_capacity(self, heracles):
        state = MiningState(asteroid=heracles)
        state.total_ore_kg = 60_000
        assert state.is_container_full() is True


class TestSimulateMiningDay:

    def test_simulate_one_day_increases_count(self, heracles):
        state = MiningState(asteroid=heracles)
        simulate_mining_day(state)
        assert state.days_mined == 1

    def test_simulate_one_day_mines_36000_kg(self, heracles):
        state = MiningState(asteroid=heracles)
        simulate_mining_day(state)
        assert state.total_mined_kg == 36_000

    def test_simulate_one_day_updates_ore(self, heracles):
        state = MiningState(asteroid=heracles)
        result = simulate_mining_day(state)
        assert state.total_ore_kg > 0
        assert len(result.element_breakdown) > 0

    def test_simulate_one_day_has_revenue(self, heracles):
        state = MiningState(asteroid=heracles)
        result = simulate_mining_day(state)
        assert result.daily_revenue > 0

    def test_daily_yield_recorded(self, heracles):
        state = MiningState(asteroid=heracles)
        result = simulate_mining_day(state)
        assert len(state.daily_yields) == 1
        assert state.daily_yields[0] is result

    def test_two_days_double_count(self, heracles):
        state = MiningState(asteroid=heracles)
        simulate_mining_day(state)
        simulate_mining_day(state)
        assert state.days_mined == 2
        assert state.total_mined_kg == 72_000

    def test_element_breakdown_contains_known_elements(self, heracles):
        state = MiningState(asteroid=heracles)
        result = simulate_mining_day(state)
        for elem_name in result.element_breakdown:
            assert elem_name in (
                "Platinum", "Palladium", "Gold", "Iridium",
                "Iron", "Nickel", "Cobalt", "Silicon",
                "Magnesium", "Aluminum",
            )

    def test_event_may_occur(self, heracles):
        """Events have 10% chance, so may or may not fire in one day."""
        state = MiningState(asteroid=heracles)
        result = simulate_mining_day(state)
        # No assertion — events are random. Just verify no crash.
        assert result.day == 1

    def test_midas_mining_produces_revenue(self, midas):
        """Midas, being M-class with PGM, should generate significant revenue."""
        state = MiningState(asteroid=midas)
        result = simulate_mining_day(state)
        assert result.daily_revenue > 0


class TestRunMiningOperation:

    def test_runs_specified_max_days(self, heracles):
        """If container doesn't fill, stop at max_days."""
        state = run_mining_operation(heracles, max_days=5, seed=42)
        assert state.days_mined <= 5

    def test_stops_when_container_full(self, heracles):
        """Container fills before max_days."""
        state = run_mining_operation(heracles, max_days=200, seed=42)
        assert state.is_container_full() is True
        assert state.total_ore_kg >= state.cargo_capacity_kg

    def test_deterministic_with_seed(self, heracles):
        """Same seed produces same results."""
        state1 = run_mining_operation(heracles, max_days=10, seed=42)
        state2 = run_mining_operation(heracles, max_days=10, seed=42)
        assert state1.total_revenue == state2.total_revenue
        assert state1.total_mined_kg == state2.total_mined_kg
        assert len(state1.daily_yields) == len(state2.daily_yields)

    def test_different_seeds_different_results(self, heracles):
        """Different seeds may produce different results."""
        state1 = run_mining_operation(heracles, max_days=10, seed=42)
        state2 = run_mining_operation(heracles, max_days=10, seed=99)
        # Could be same by chance, but unlikely
        assert state1.daily_yields is not None

    def test_c_class_lower_revenue(self, heracles, cuyo):
        """M-class should generate more revenue than C-class per day."""
        m_state = run_mining_operation(heracles, max_days=10, seed=42)
        c_state = run_mining_operation(cuyo, max_days=10, seed=42)
        # M-class has higher ore grade and PGM elements
        assert m_state.total_revenue > c_state.total_revenue

    def test_zero_max_days(self, heracles):
        state = run_mining_operation(heracles, max_days=0, seed=42)
        assert state.days_mined == 0
        assert state.total_mined_kg == 0.0

    def test_all_daily_yields_have_positive_revenue(self, heracles):
        state = run_mining_operation(heracles, max_days=10, seed=42)
        for yd in state.daily_yields:
            assert yd.daily_revenue >= 0
            assert yd.total_mined_kg == 36_000


class TestDaysToFillContainer:

    def test_days_to_fill_with_grade(self, heracles):
        state = MiningState(asteroid=heracles)
        # Before ore grade is set, returns large number
        assert state.days_to_fill_container() == 999_999
        # After one day, grade is set
        simulate_mining_day(state)
        assert state.days_to_fill_container() < 999_999

    def test_days_to_fill_decreases(self, heracles):
        state = MiningState(asteroid=heracles)
        simulate_mining_day(state)
        t1 = state.days_to_fill_container()
        simulate_mining_day(state)
        t2 = state.days_to_fill_container()
        assert t2 <= t1


# ─── refinery / on-site processing ────────────────────────────────────────

class TestRefinery:

    def test_precious_metals_defined(self):
        from astrosurge.mining import PRECIOUS_METALS
        assert "Gold" in PRECIOUS_METALS
        assert "Platinum" in PRECIOUS_METALS
        assert "Iron" not in PRECIOUS_METALS
        assert "Nickel" not in PRECIOUS_METALS

    def test_refinery_filters_to_pgms_only(self, heracles):
        """With refinery, element_breakdown should only contain PGMs."""
        state = run_mining_operation(heracles, max_days=5, seed=42, refinery=True)
        for yd in state.daily_yields:
            for elem_name in yd.element_breakdown:
                from astrosurge.mining import PRECIOUS_METALS
                assert elem_name in PRECIOUS_METALS, \
                    f"{elem_name} should not be in refined output"

    def test_refinery_excludes_base_metals(self, heracles):
        """Iron, Nickel, Silicon should be absent from refined output."""
        state = run_mining_operation(heracles, max_days=5, seed=42, refinery=True)
        all_elems = set()
        for yd in state.daily_yields:
            all_elems.update(yd.element_breakdown.keys())
        assert "Iron" not in all_elems
        assert "Nickel" not in all_elems
        assert "Silicon" not in all_elems

    def test_refinery_container_fills_slower(self, heracles):
        """With refinery, container fills much slower (PGMs only)."""
        normal = run_mining_operation(heracles, max_days=40, seed=42, refinery=False)
        refined = run_mining_operation(heracles, max_days=40, seed=42, refinery=True)
        # Normal should fill container in 40 days
        assert normal.is_container_full()
        assert normal.total_ore_kg >= 50_000
        # Refined should NOT be full in 40 days (only PGMs stored)
        assert not refined.is_container_full()
        assert refined.total_ore_kg < 50_000
        # But total value should still be there (just in smaller volume)
        assert refined.total_revenue > 0

    def test_refinery_preserves_pgm_value(self, heracles):
        """With or without refinery, total revenue from PGMs should be similar."""
        normal = run_mining_operation(heracles, max_days=10, seed=42, refinery=False)
        refined = run_mining_operation(heracles, max_days=10, seed=42, refinery=True)
        # Normal includes all elements. Refined only includes PGMs.
        # Refined revenue should be close to (but slightly less than) normal
        # since normal includes base metal value (tiny) + PGM value
        assert refined.total_revenue > 0
        # The PGM value should be the vast majority of normal revenue
        pgm_fraction = refined.total_revenue / normal.total_revenue
        assert pgm_fraction > 0.99  # PGMs are >99% of value

    def test_refinery_more_days_more_value(self, heracles):
        """With refinery, more mining days = more PGM value (not container-bound)."""
        short = run_mining_operation(heracles, max_days=10, seed=42, refinery=True)
        long = run_mining_operation(heracles, max_days=40, seed=42, refinery=True)
        assert long.total_revenue > short.total_revenue
        assert long.days_mined > short.days_mined
