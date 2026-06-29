"""Market pricing and price elasticity for asteroid mining outputs.

Prices are adjusted based on quantity sold using a price elasticity model.
Price adjustments persist across all subsequent missions.
"""

from dataclasses import dataclass, field
from typing import Optional

from .mining import ELEMENT_PRICES, get_element_price


# ─── default elasticity coefficient ────────────────────────────────────────

# Price elasticity: -0.3 means a 10% increase in supply → 3% price drop.
DEFAULT_ELASTICITY = -0.3


# ─── market state ──────────────────────────────────────────────────────────

@dataclass
class MarketState:
    """Tracks current market prices and historical sales."""
    prices: dict[str, float] = field(default_factory=lambda: dict(ELEMENT_PRICES))
    total_sold_kg: dict[str, float] = field(default_factory=dict)
    elasticity: float = DEFAULT_ELASTICITY


# ─── price adjustment ─────────────────────────────────────────────────────

def adjust_price(
    base_price: float,
    quantity_sold_kg: float,
    total_market_volume_kg: float = 1_000_000.0,
    elasticity: float = DEFAULT_ELASTICITY,
) -> float:
    """Apply price elasticity to compute new market price.

    Args:
        base_price: Current price per kg.
        quantity_sold_kg: Amount being sold in this transaction.
        total_market_volume_kg: Reference market volume.
        elasticity: Price elasticity coefficient (negative).

    Returns:
        Adjusted price per kg.
    """
    if total_market_volume_kg <= 0:
        return base_price
    supply_change = quantity_sold_kg / total_market_volume_kg
    price_change_pct = elasticity * supply_change
    return base_price * (1.0 + price_change_pct)


def record_sale(state: MarketState, element_name: str, quantity_kg: float) -> float:
    """Record a sale and return the adjusted price.

    Updates the market state with the new price after elasticity adjustment.
    """
    current_price = state.prices.get(element_name, get_element_price(element_name))
    new_price = adjust_price(current_price, quantity_kg)

    state.prices[element_name] = new_price
    state.total_sold_kg[element_name] = (
        state.total_sold_kg.get(element_name, 0.0) + quantity_kg
    )
    return new_price


def sell_cargo(market_state: MarketState, element_breakdown: dict[str, dict]) -> dict:
    """Execute market sale of all elements in the cargo.

    Args:
        market_state: Current market state (mutated in place).
        element_breakdown: {element_name: {"mass_kg": float, ...}}

    Returns:
        dict with per-element and total revenue, plus new prices.
    """
    result: dict = {
        "element_sales": [],
        "total_revenue": 0.0,
        "price_changes": {},
    }

    for elem_name, data in element_breakdown.items():
        mass = data.get("mass_kg", 0.0)
        if mass <= 0:
            continue

        old_price = market_state.prices.get(elem_name, get_element_price(elem_name))
        new_price = record_sale(market_state, elem_name, mass)
        revenue = mass * new_price

        result["element_sales"].append({
            "element": elem_name,
            "mass_kg": round(mass, 4),
            "price_per_kg": round(new_price, 2),
            "revenue": round(revenue, 2),
        })
        result["price_changes"][elem_name] = {
            "old_price": round(old_price, 2),
            "new_price": round(new_price, 2),
            "change_pct": round(((new_price - old_price) / old_price) * 100, 4),
        }
        result["total_revenue"] += revenue

    result["total_revenue"] = round(result["total_revenue"], 2)
    return result
