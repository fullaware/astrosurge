"""Deterministic asteroid element composition generation.

Generates realistic element distributions based on asteroid taxonomic class
(M, C, S) using SPK ID as a deterministic seed. Each asteroid gets a unique
but class-appropriate composition that stays consistent across queries.
"""

import hashlib
import math
import random
from typing import Optional

from .models import Element


# ─── Element composition templates ─────────────────────────────────────────
# Each entry: (name, min_weight_pct, max_weight_pct)
# Values are weight percentages of total mass, normalized to 100%

M_CLASS_ELEMENTS: list[tuple[str, float, float]] = [
    # Major metals
    ("Iron",         35.0, 55.0),
    ("Nickel",       10.0, 22.0),
    ("Cobalt",        1.5,  5.0),
    # Minor metals
    ("Chromium",      0.5,  3.0),
    ("Manganese",     0.3,  1.5),
    ("Titanium",      0.1,  1.0),
    ("Copper",        0.1,  0.8),
    ("Zinc",          0.05, 0.3),
    ("Tin",           0.01, 0.1),
    # Precious metals (PGMs)
    ("Platinum",      0.05, 2.0),
    ("Palladium",     0.05, 1.5),
    ("Rhodium",       0.01, 1.0),
    ("Iridium",       0.01, 0.6),
    ("Osmium",        0.01, 0.6),
    ("Ruthenium",     0.01, 0.4),
    ("Gold",          0.005, 0.3),
    ("Silver",        0.01, 0.2),
    # Light elements (minor)
    ("Silicon",       0.5,  4.0),
    ("Magnesium",     0.3,  2.0),
    ("Aluminum",      0.2,  1.5),
    ("Sulfur",        1.0,  4.0),
    ("Phosphorus",    0.05, 0.3),
    ("Carbon",        0.05, 0.5),
    ("Oxygen",        0.2,  2.0),
]

C_CLASS_ELEMENTS: list[tuple[str, float, float]] = [
    # Carbon and water
    ("Carbon",       15.0, 35.0),
    ("Oxygen",       10.0, 25.0),  # bound in water, carbonates, silicates
    ("Hydrogen",      5.0, 15.0),  # water ice, hydrocarbons
    ("Nitrogen",      0.5,  3.0),  # organics
    # Rock-forming elements
    ("Silicon",       8.0, 18.0),
    ("Magnesium",     5.0, 12.0),
    ("Iron",          8.0, 18.0),
    ("Aluminum",      1.0,  4.0),
    ("Calcium",       0.5,  3.0),
    ("Sodium",        0.3,  1.5),
    ("Potassium",     0.1,  0.8),
    ("Phosphorus",    0.1,  0.5),
    ("Sulfur",        1.0,  5.0),
    # Minor metals
    ("Nickel",        0.5,  3.0),
    ("Chromium",      0.1,  0.8),
    ("Manganese",     0.1,  0.5),
    ("Titanium",      0.1,  0.5),
    # Trace elements
    ("Zinc",          0.01, 0.1),
    ("Copper",        0.01, 0.1),
    # PGMs (very low in C-class)
    ("Platinum",      0.001, 0.05),
    ("Palladium",     0.001, 0.03),
    ("Iridium",       0.0005, 0.02),
]

S_CLASS_ELEMENTS: list[tuple[str, float, float]] = [
    # Silicates (dominant)
    ("Oxygen",       30.0, 45.0),
    ("Silicon",      15.0, 25.0),
    ("Magnesium",     8.0, 18.0),
    ("Iron",          8.0, 18.0),
    ("Aluminum",      2.0,  6.0),
    ("Calcium",       0.5,  3.0),
    ("Sodium",        0.5,  2.0),
    ("Potassium",     0.1,  0.8),
    ("Titanium",      0.1,  0.8),
    ("Chromium",      0.1,  0.5),
    ("Manganese",     0.1,  0.3),
    # Metals
    ("Nickel",        0.5,  3.0),
    ("Cobalt",        0.05, 0.5),
    ("Copper",        0.01, 0.1),
    ("Zinc",          0.01, 0.1),
    # Light elements
    ("Carbon",        0.1,  1.0),
    ("Phosphorus",    0.05, 0.3),
    ("Sulfur",        0.5,  3.0),
    # Trace PGMs (very low in S-class)
    ("Platinum",      0.001, 0.03),
    ("Palladium",     0.001, 0.02),
    ("Gold",          0.0005, 0.01),
    ("Silver",        0.001, 0.02),
]


# ─── Template lookup ─────────────────────────────────────────────────────

_CLASS_TEMPLATES: dict[str, list[tuple[str, float, float]]] = {
    "M": M_CLASS_ELEMENTS,
    "C": C_CLASS_ELEMENTS,
    "S": S_CLASS_ELEMENTS,
}

# Fallback for unknown classes
FALLBACK_TEMPLATE = S_CLASS_ELEMENTS


def _seed_rng(spkid: int) -> random.Random:
    """Create a deterministic RNG from spkid for element composition."""
    seed_str = f"{spkid}-element-composition"
    digest = hashlib.md5(seed_str.encode()).hexdigest()
    seed = int(digest[:8], 16)
    return random.Random(seed)


def generate_elements(
    spkid: int,
    class_: str = "M",
    diameter_km: float = 3.0,
) -> list[Element]:
    """Generate deterministic, class-appropriate element composition.

    Each asteroid gets a unique composition based on its SPK ID, with
    element distributions appropriate to its taxonomic class (M, C, S).

    Args:
        spkid: SPK ID (deterministic seed).
        class_: Asteroid class ('M', 'C', 'S', or other).
        diameter_km: Diameter in km (scales absolute masses).

    Returns:
        List of Element dataclass instances.
    """
    rng = _seed_rng(spkid)
    template = _CLASS_TEMPLATES.get(class_.upper(), FALLBACK_TEMPLATE)

    # Pick a weight percentage for each element within its range
    weights: list[float] = []
    names: list[str] = []
    for name, wmin, wmax in template:
        # Use deterministic random within range for each element
        # This gives each asteroid a unique but class-appropriate mix
        w = wmin + rng.random() * (wmax - wmin)
        weights.append(w)
        names.append(name)

    # Normalise to 100%
    total_weight = sum(weights)
    fractions = [w / total_weight for w in weights]

    # Scale to absolute masses based on diameter
    # Approximate asteroid mass: (4/3)πr³ × density (~3.5 g/cm³ for M, ~2.5 for C)
    density = {"M": 3.5, "C": 2.5, "S": 2.8}.get(class_.upper(), 2.8)
    radius_km = diameter_km / 2.0
    # Mass in kg: volume (km³ → m³) × density (g/cm³ → kg/m³)
    volume_m3 = (4.0 / 3.0) * math.pi * (radius_km * 1000) ** 3
    density_kg_m3 = density * 1000  # g/cm³ → kg/m³
    total_mass_kg = volume_m3 * density_kg_m3

    elements: list[Element] = []
    for name, frac in zip(names, fractions):
        mass = total_mass_kg * frac
        # Look up atomic number from name
        atomic = _ATOMIC_NUMBERS.get(name, 0)
        elements.append(Element(name=name, mass_kg=mass, number=atomic))

    return elements


# ─── Atomic numbers for reference ──────────────────────────────────────────

_ATOMIC_NUMBERS: dict[str, int] = {
    "Hydrogen": 1, "Helium": 2, "Lithium": 3, "Beryllium": 4, "Boron": 5,
    "Carbon": 6, "Nitrogen": 7, "Oxygen": 8, "Fluorine": 9, "Neon": 10,
    "Sodium": 11, "Magnesium": 12, "Aluminum": 13, "Silicon": 14, "Phosphorus": 15,
    "Sulfur": 16, "Chlorine": 17, "Argon": 18, "Potassium": 19, "Calcium": 20,
    "Scandium": 21, "Titanium": 22, "Vanadium": 23, "Chromium": 24, "Manganese": 25,
    "Iron": 26, "Cobalt": 27, "Nickel": 28, "Copper": 29, "Zinc": 30,
    "Gold": 79, "Silver": 47, "Platinum": 78, "Palladium": 46, "Rhodium": 45,
    "Iridium": 77, "Osmium": 76, "Ruthenium": 44, "Tin": 50, "Lead": 82,
}
