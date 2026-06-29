"""Tests for market pricing and price elasticity model.

Price elasticity:
  - Selling large quantities depresses prices
  - Price adjustments persist across missions
  - Default elasticity coefficient: -0.3
"""

import pytest
from astrosurge.market import (
    MarketState,
    adjust_price,
    record_sale,
    sell_cargo,
    DEFAULT_ELASTICITY,
)
from astrosurge.mining import ELEMENT_PRICES


class TestAdjustPrice:

    def test_no_sale_no_change(self):
        """Zero quantity sold → no price change."""
        new_price = adjust_price(1000.0, 0.0)
        assert new_price == 1000.0

    def test_small_sale_small_drop(self):
        """Small quantity → negligible price drop."""
        new_price = adjust_price(1000.0, 100.0, total_market_volume_kg=1_000_000.0)
        # supply_change = 100/1_000_000 = 0.0001
        # price_change_pct = -0.3 * 0.0001 = -0.00003
        # new_price = 1000 * 0.99997 = 999.97
        assert new_price == pytest.approx(999.97, rel=1e-4)

    def test_large_sale_large_drop(self):
        """Large quantity → noticeable price drop."""
        new_price = adjust_price(1000.0, 100_000.0, total_market_volume_kg=1_000_000.0)
        # supply_change = 0.10
        # price_change_pct = -0.3 * 0.10 = -0.03
        # new_price = 1000 * 0.97 = 970
        assert new_price == pytest.approx(970.0)

    def test_custom_elasticity(self):
        """More elastic market → bigger price drops."""
        new_price = adjust_price(1000.0, 100_000.0,
                                  total_market_volume_kg=1_000_000.0,
                                  elasticity=-1.0)
        # price_change_pct = -1.0 * 0.10 = -0.10
        # new_price = 1000 * 0.90 = 900
        assert new_price == pytest.approx(900.0)

    def test_inelastic_market(self):
        """Inelastic market → small price drops."""
        new_price = adjust_price(1000.0, 100_000.0,
                                  total_market_volume_kg=1_000_000.0,
                                  elasticity=-0.05)
        # price_change_pct = -0.05 * 0.10 = -0.005
        # new_price = 1000 * 0.995 = 995
        assert new_price == pytest.approx(995.0)

    def very_large_sale(self):
        """Extremely large sale relative to market volume → big drop."""
        new_price = adjust_price(1000.0, 500_000.0,
                                  total_market_volume_kg=1_000_000.0)
        # supply_change = 0.50
        # price_change_pct = -0.3 * 0.50 = -0.15
        # new_price = 1000 * 0.85 = 850
        assert new_price == pytest.approx(850.0)

    def test_zero_market_volume(self):
        """Zero market volume → no change (avoid division by zero)."""
        new_price = adjust_price(1000.0, 100.0, total_market_volume_kg=0.0)
        assert new_price == 1000.0

    def test_default_elasticity_constant(self):
        assert DEFAULT_ELASTICITY == -0.3


class TestRecordSale:

    def test_records_sale_updates_price(self):
        state = MarketState()
        initial = state.prices["Gold"]
        new_price = record_sale(state, "Gold", 10_000.0)
        assert new_price < initial  # Price dropped
        assert state.prices["Gold"] == new_price

    def test_tracks_total_sold(self):
        state = MarketState()
        record_sale(state, "Gold", 10_000.0)
        assert state.total_sold_kg["Gold"] == 10_000.0

    def test_multiple_sales_accumulate(self):
        state = MarketState()
        record_sale(state, "Gold", 5_000.0)
        record_sale(state, "Gold", 3_000.0)
        assert state.total_sold_kg["Gold"] == 8_000.0

    def test_multiple_sales_further_depress_price(self):
        state = MarketState()
        p1 = record_sale(state, "Gold", 10_000.0)
        p2 = record_sale(state, "Gold", 10_000.0)
        assert p2 < p1  # Second sale at lower price

    def test_multiple_elements_independent(self):
        state = MarketState()
        gold_price = record_sale(state, "Gold", 10_000.0)
        plat_price = record_sale(state, "Platinum", 10_000.0)
        assert state.total_sold_kg["Gold"] == 10_000.0
        assert state.total_sold_kg["Platinum"] == 10_000.0
        # Prices should be different (different base prices)
        assert gold_price != plat_price

    def test_unknown_element(self):
        state = MarketState()
        price = record_sale(state, "Fictionalium", 100.0)
        assert price == pytest.approx(5.0 * (1 + DEFAULT_ELASTICITY * (100 / 1_000_000)))


class TestSellCargo:

    def test_sell_single_element(self):
        state = MarketState()
        breakdown = {"Gold": {"mass_kg": 5_000.0, "value": 5_000 * 135_614.87}}
        result = sell_cargo(state, breakdown)
        assert result["total_revenue"] > 0
        assert len(result["element_sales"]) == 1
        assert len(result["price_changes"]) == 1

    def test_sell_multiple_elements(self):
        state = MarketState()
        breakdown = {
            "Gold": {"mass_kg": 5_000.0, "value": 0},
            "Platinum": {"mass_kg": 3_000.0, "value": 0},
            "Silver": {"mass_kg": 10_000.0, "value": 0},
        }
        result = sell_cargo(state, breakdown)
        assert result["total_revenue"] > 0
        assert len(result["element_sales"]) == 3

    def test_price_changes_recorded(self):
        state = MarketState()
        initial_gold = state.prices["Gold"]
        breakdown = {"Gold": {"mass_kg": 10_000.0, "value": 0}}
        result = sell_cargo(state, breakdown)
        pc = result["price_changes"]["Gold"]
        assert pc["old_price"] == initial_gold
        assert pc["new_price"] < initial_gold
        assert pc["change_pct"] < 0

    def test_zero_mass_skipped(self):
        state = MarketState()
        breakdown = {"Gold": {"mass_kg": 0.0, "value": 0}}
        result = sell_cargo(state, breakdown)
        assert result["total_revenue"] == 0.0
        assert len(result["element_sales"]) == 0

    def test_empty_breakdown(self):
        state = MarketState()
        result = sell_cargo(state, {})
        assert result["total_revenue"] == 0.0

    def test_market_state_persists_after_sale(self, heracles):
        """Market state should track sales for future missions."""
        state = MarketState()
        breakdown_1 = {"Gold": {"mass_kg": 5_000.0, "value": 0}}
        result_1 = sell_cargo(state, breakdown_1)
        assert state.total_sold_kg["Gold"] == 5_000.0

        # Second mission sells more
        breakdown_2 = {"Gold": {"mass_kg": 5_000.0, "value": 0}}
        result_2 = sell_cargo(state, breakdown_2)
        assert state.total_sold_kg["Gold"] == 10_000.0
        # Price dropped further
        assert result_2["price_changes"]["Gold"]["new_price"] < \
               result_1["price_changes"]["Gold"]["new_price"]
