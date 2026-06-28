"""Tests for transit time model.

PRD formula:
    transit_days_one_way = 30 + (moid_au × 1000)
    round_trip_days = (transit_days_one_way × 2) + setup_days + mining_days + prep_days
"""

import pytest
from astrosurge.transit import (
    calc_one_way,
    calc_round_trip,
    TransitEstimate,
    days_remaining,
    DEFAULT_SETUP_DAYS,
    DEFAULT_MINING_DAYS_TO_FILL,
    DEFAULT_PREP_DAYS,
)


# ─── calc_one_way ──────────────────────────────────────────────────────────

class TestCalcOneWay:
    """Verify the MOID-based transit time formula."""

    def test_heracles(self):
        """Heracles MOID=0.0584 → ~88 days (PRD table)."""
        assert calc_one_way(0.0584) == 88

    def test_zeus(self):
        """Zeus MOID=0.0707 → ~101 days (PRD table)."""
        assert calc_one_way(0.0707) == 101

    def test_midas(self):
        """Midas MOID=0.0036 → ~34 days (PRD table)."""
        assert calc_one_way(0.0036) == 34

    def test_toutatis(self):
        """Toutatis MOID=0.0066 → ~37 days (PRD table)."""
        assert calc_one_way(0.0066) == 37

    def test_eros(self):
        """Eros MOID=0.1486 → ~179 days (PRD table)."""
        assert calc_one_way(0.1486) == 179

    def test_cuyo(self):
        """Cuyo MOID=0.0727 → ~103 days (PRD table)."""
        assert calc_one_way(0.0727) == 103

    def test_zero_moid(self):
        """MOID=0 → minimum 30 days."""
        assert calc_one_way(0.0) == 30

    def test_very_small_moid(self):
        """Extremely small MOID should floor at 30."""
        assert calc_one_way(0.0001) == 30

    def test_very_large_moid(self):
        """Large MOID should produce correspondingly large transit."""
        assert calc_one_way(0.5) == 530  # 30 + 500

    def test_moid_edge_at_half(self):
        """MOID=0.0005 → 30.5 → rounds to 30 (Python 3 banker's rounding)."""
        assert calc_one_way(0.0005) == 30

    def test_negative_moid_not_allowed(self):
        """MOID should never be negative; function still handles gracefully."""
        result = calc_one_way(-0.01)
        assert result >= 30  # floor should still be 30

    @pytest.mark.parametrize("moid,expected", [
        (0.001, 31),
        (0.01, 40),
        (0.05, 80),
        (0.10, 130),
        (0.15, 180),
        (0.20, 230),
        (0.25, 280),
        (0.30, 330),
    ])
    def test_various_moid_values(self, moid, expected):
        """Parametrized check of formula across MOID range."""
        assert calc_one_way(moid) == expected

    def test_same_as_prd_table(self, expected_transit_values):
        """Verify all entries match the PRD v2.0 Transit Time Model table."""
        for name, row in expected_transit_values.items():
            assert calc_one_way(row["moid"]) == row["one_way"], (
                f"{name}: MOID={row['moid']} expected {row['one_way']} days "
                f"per PRD table, got {calc_one_way(row['moid'])}"
            )


# ─── calc_round_trip ──────────────────────────────────────────────────────

class TestCalcRoundTrip:
    """Verify round-trip calculations and TransitEstimate structure."""

    def test_heracles_round_trip(self):
        """Heracles: 88 days one-way.
        round_trip = (88 × 2) + 3 + 139 + 1 = 319
        (PRD v2.0 Fast ROI table: 319 days round trip)
        """
        est = calc_round_trip(0.0584)
        assert est.one_way_days == 88
        assert est.round_trip_days == 319  # 176 + 3 + 139 + 1
        assert est.setup_days == 3
        assert est.mining_days == 139
        assert est.prep_days == 1

    def test_midas_round_trip(self):
        """Midas: 34 days one-way.
        round_trip = (34 × 2) + 3 + 139 + 1 = 211
        (PRD table: 211 days)
        """
        est = calc_round_trip(0.0036)
        assert est.one_way_days == 34
        assert est.round_trip_days == 211

    def test_zeus_round_trip(self):
        """Zeus: 101 days one-way.
        round_trip = (101 × 2) + 3 + 139 + 1 = 345
        (PRD table: 345 days)
        """
        est = calc_round_trip(0.0707)
        assert est.one_way_days == 101
        assert est.round_trip_days == 345

    def test_return_leg_matches_outbound(self):
        """Return leg should have same duration as outbound."""
        for moid in (0.0584, 0.0036, 0.0707, 0.1486):
            est = calc_round_trip(moid)
            assert est.outbound.days == est.return_.days, f"moid={moid}"
            assert est.outbound.moid_au == est.return_.moid_au, f"moid={moid}"

    def test_custom_durations(self):
        """Allow overriding setup, mining, and prep days."""
        est = calc_round_trip(0.0584, setup_days=5, mining_days=100, prep_days=2)
        assert est.setup_days == 5
        assert est.mining_days == 100
        assert est.prep_days == 2
        assert est.round_trip_days == (88 * 2) + 5 + 100 + 2  # 283

    def test_transit_estimate_is_frozen(self):
        """TransitEstimate should be immutable (frozen dataclass)."""
        est = calc_round_trip(0.0584)
        with pytest.raises(AttributeError):
            est.one_way_days = 999

    def test_transit_leg_is_frozen(self):
        """TransitLeg should be immutable (frozen dataclass)."""
        est = calc_round_trip(0.0584)
        with pytest.raises(AttributeError):
            est.outbound.days = 999


# ─── days_remaining ───────────────────────────────────────────────────────

class TestDaysRemaining:
    """Verify the days_remaining helper."""

    def test_at_start(self):
        assert days_remaining(319, 0) == 319

    def test_halfway(self):
        assert days_remaining(319, 160) == 159

    def test_complete(self):
        assert days_remaining(319, 319) == 0

    def test_over_complete(self):
        assert days_remaining(319, 400) == 0

    def test_single_day(self):
        assert days_remaining(1, 0) == 1
        assert days_remaining(1, 1) == 0


# ─── defaults ─────────────────────────────────────────────────────────────

class TestDefaults:
    """Verify default constants match expectations."""

    def test_setup_days(self):
        # From PRD: 3 days for site establishment
        assert DEFAULT_SETUP_DAYS == 3

    def test_mining_days_to_fill(self):
        # 50 000 kg / 36 000 kg/day ≈ 1.39 → but PRD says 139
        # This is likely a mission design constant, not a literal calc
        assert DEFAULT_MINING_DAYS_TO_FILL == 139

    def test_prep_days(self):
        assert DEFAULT_PREP_DAYS == 1
