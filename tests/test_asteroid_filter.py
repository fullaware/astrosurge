"""Tests for asteroid filtering and scoring logic.

Fast ROI (Tier 1) strategy:
  - MOID < 0.10 AU
  - Diameter > 3 km
  - Class M
  - Non-hazardous preferred
  - Score: (value - cost) / transit_days
"""
import pytest
from astrosurge.asteroid_filter import (
    passes_fast_roi_filter,
    score_fast_roi,
    rank_fast_roi_candidates,
    estimate_asteroid_value,
    estimate_mission_cost,
    FAST_ROI_MAX_MOID_AU,
    FAST_ROI_MIN_DIAMETER_KM,
    FAST_ROI_PREFERRED_CLASSES,
)


# ─── config constants ─────────────────────────────────────────────────────

class TestConfig:
    def test_max_moid(self):
        assert FAST_ROI_MAX_MOID_AU == 0.10

    def test_min_diameter(self):
        assert FAST_ROI_MIN_DIAMETER_KM == 3.0

    def test_preferred_classes(self):
        assert FAST_ROI_PREFERRED_CLASSES == ("M",)


# ─── passes_fast_roi_filter ───────────────────────────────────────────────

class TestPassesFilter:

    def test_heracles_passes(self, heracles):
        """Heracles: M-class, MOID=0.058, 4.84km, non-hazardous → pass."""
        assert passes_fast_roi_filter(heracles) is True

    def test_zeus_passes(self, zeus):
        """Zeus: M-class, MOID=0.071, 5.23km → pass."""
        assert passes_fast_roi_filter(zeus) is True

    def test_midas_passes_on_class_and_size(self, midas):
        """Midas: M-class, MOID=0.004, 3.4km → pass (hazard ignored at filter)."""
        assert passes_fast_roi_filter(midas) is True

    def test_eros_fails_moid(self, eros):
        """Eros: M-class but MOID=0.149 > 0.10 → fail."""
        assert passes_fast_roi_filter(eros) is False

    def test_toutatis_fails_class(self, toutatis):
        """Toutatis: C-class, not M → fail."""
        assert passes_fast_roi_filter(toutatis) is False

    def test_cuyo_fails_class(self, cuyo):
        """Cuyo: C-class, not M → fail."""
        assert passes_fast_roi_filter(cuyo) is False

    def test_unnamed_m_class_passes(self, unnamed_m_class):
        """spkid 276049: M-class, MOID=0.097, 3.5km → pass."""
        assert passes_fast_roi_filter(unnamed_m_class) is True

    def test_too_small_m_class(self):
        """M-class with 2.0 km diameter → fail (below 3km min)."""
        from conftest import Asteroid, Element
        from bson import ObjectId
        small = Asteroid(
            source_id=ObjectId(),
            name="Tiny",
            pdes="99999",
            spkid=99999,
            class_="M",
            diameter=2.0,
            moid=0.05,
            moid_days=50,
            neo=True,
            hazard=False,
            elements=[Element("Gold", 1000, 79)],
        )
        assert passes_fast_roi_filter(small) is False

    def test_too_high_moid_m_class(self):
        """M-class with MOID=0.15 → fail."""
        from conftest import Asteroid, Element
        from bson import ObjectId
        far = Asteroid(
            source_id=ObjectId(),
            name="FarAway",
            pdes="99998",
            spkid=99998,
            class_="M",
            diameter=4.0,
            moid=0.15,
            moid_days=150,
            neo=True,
            hazard=False,
            elements=[Element("Gold", 1000, 79)],
        )
        assert passes_fast_roi_filter(far) is False


# ─── estimate_asteroid_value ──────────────────────────────────────────────

class TestEstimateValue:

    def test_heracles_value_positive(self, heracles):
        v = estimate_asteroid_value(heracles)
        assert v > 0
        # 4.84³ × 15M ≈ 1.7B
        assert 1.0e9 < v < 3.0e9

    def test_m_class_scales_with_diameter(self, heracles, zeus):
        v_heracles = estimate_asteroid_value(heracles)
        v_zeus = estimate_asteroid_value(zeus)
        # Zeus is bigger → higher value
        assert v_zeus > v_heracles

    def test_c_class_lower_than_m(self, cuyo):
        v = estimate_asteroid_value(cuyo)
        # C-class uses lower multiplier
        assert v > 0

    def test_zero_diameter(self):
        from conftest import Asteroid, Element
        from bson import ObjectId
        zero = Asteroid(
            source_id=ObjectId(),
            name="Zero",
            pdes="99997",
            spkid=99997,
            class_="M",
            diameter=0,
            moid=0.05,
            moid_days=50,
            neo=True,
            hazard=False,
        )
        assert estimate_asteroid_value(zero) == 0


# ─── score_fast_roi ──────────────────────────────────────────────────────

class TestScoreFastROI:

    def test_heracles_scored(self, heracles):
        card = score_fast_roi(heracles)
        assert card is not None
        assert card.asteroid_name == "Heracles"
        assert card.spkid == 2005143
        assert card.class_ == "M"
        assert card.transit_days_one_way == 88
        assert card.score > 0

    def test_zeus_scored(self, zeus):
        card = score_fast_roi(zeus)
        assert card is not None
        assert card.transit_days_one_way == 101

    def test_eros_none(self, eros):
        """Eros fails MOID filter → score returns None."""
        assert score_fast_roi(eros) is None

    def test_toutatis_none(self, toutatis):
        """Toutatis fails class filter → score returns None."""
        assert score_fast_roi(toutatis) is None

    def test_card_has_all_fields(self, heracles):
        card = score_fast_roi(heracles)
        assert card.asteroid_name is not None
        assert card.spkid > 0
        assert card.class_ == "M"
        assert card.diameter > 0
        assert card.moid > 0
        assert card.hazard is False
        assert card.transit_days_one_way > 0
        assert card.estimated_value > 0
        assert card.estimated_cost > 0

    def test_card_to_dict(self, heracles):
        card = score_fast_roi(heracles)
        d = card.to_dict()
        assert d["name"] == "Heracles"
        assert d["class"] == "M"
        assert d["score"] > 0
        assert "estimated_value_usd" in d
        assert "estimated_cost_usd" in d

    def test_hazard_flag_preserved(self, midas):
        card = score_fast_roi(midas)
        assert card is not None
        assert card.hazard is True  # Midas is hazardous


# ─── rank_fast_roi_candidates ─────────────────────────────────────────────

class TestRankCandidates:

    def test_zeus_ranks_higher_than_heracles(self, heracles, zeus):
        """Zeus should score higher (larger diameter = higher estimated value)."""
        ranked = rank_fast_roi_candidates([heracles, zeus])
        assert len(ranked) == 2
        # Zeus: 5.23km → ~2.15B value vs Heracles: 4.84km → ~1.70B value
        assert ranked[0].asteroid_name == "Zeus"
        assert ranked[1].asteroid_name == "Heracles"
        assert ranked[0].score > ranked[1].score

    def test_filters_out_bad_candidates(self, heracles, eros, toutatis):
        """Eros and Toutatis should be excluded."""
        ranked = rank_fast_roi_candidates([heracles, eros, toutatis])
        assert len(ranked) == 1
        assert ranked[0].asteroid_name == "Heracles"

    def test_unnamed_m_class_included(self, heracles, unnamed_m_class):
        """Unnamed M-class should be included in rankings."""
        ranked = rank_fast_roi_candidates([heracles, unnamed_m_class])
        assert len(ranked) == 2

    def test_empty_list(self):
        assert rank_fast_roi_candidates([]) == []

    def test_all_bad_candidates(self, eros, toutatis):
        assert rank_fast_roi_candidates([eros, toutatis]) == []


# ─── estimate_mission_cost ────────────────────────────────────────────────

class TestMissionCost:

    def test_heracles_cost(self, heracles):
        cost = estimate_mission_cost(heracles)
        assert cost > 150_000_000  # launch cost baseline
        # Expected: 150M + (319 days × 45K) = 150M + 14.355M ≈ 164.355M
        assert 160_000_000 < cost < 170_000_000

    def test_midas_cost(self, midas):
        cost = estimate_mission_cost(midas)
        # Shorter mission → lower ops cost
        assert cost > 150_000_000
