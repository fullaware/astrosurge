"""Shared test fixtures for AstroSurge.

All tests use synthetic data — no live MongoDB required.
"""

import pytest
from bson import ObjectId

from astrosurge.models import Asteroid, Element, Ship
from astrosurge.transit import calc_one_way
from astrosurge.mining import ELEMENT_PRICES
from astrosurge.config import settings


# ─── sample asteroids ──────────────────────────────────────────────────────

@pytest.fixture
def heracles() -> Asteroid:
    """Heracles — the ideal first Fast ROI target.

    spkid=2005143, M-class, 4.84km, MOID=0.0584 AU, non-hazardous.
    """
    return Asteroid(
        source_id=ObjectId("663f1a2b3c4d5e6f7a8b9c01"),
        name="Heracles",
        pdes="5143",
        spkid=2005143,
        class_="M",
        diameter=4.84,
        moid=0.0584,
        moid_days=58,
        neo=True,
        hazard=False,
        elements=[
            Element("Platinum", 5.0e6, 78),
            Element("Palladium", 3.0e6, 46),
            Element("Gold", 2.5e6, 79),
            Element("Iridium", 1.0e6, 77),
            Element("Iron", 8.0e7, 26),
            Element("Nickel", 5.0e7, 28),
            Element("Cobalt", 2.0e6, 27),
            Element("Silicon", 3.0e7, 14),
            Element("Magnesium", 1.5e7, 12),
            Element("Aluminum", 1.0e7, 13),
        ],
    )


@pytest.fixture
def zeus() -> Asteroid:
    """Zeus — larger M-class, slightly longer transit.

    spkid=2005732, M-class, 5.23km, MOID=0.0707 AU, non-hazardous.
    """
    return Asteroid(
        source_id=ObjectId("663f1a2b3c4d5e6f7a8b9c02"),
        name="Zeus",
        pdes="5732",
        spkid=2005732,
        class_="M",
        diameter=5.23,
        moid=0.0707,
        moid_days=71,
        neo=True,
        hazard=False,
        elements=[
            Element("Platinum", 8.0e6, 78),
            Element("Gold", 4.0e6, 79),
            Element("Palladium", 2.0e6, 46),
            Element("Rhodium", 5.0e5, 45),
            Element("Iron", 1.2e8, 26),
            Element("Nickel", 7.0e7, 28),
        ],
    )


@pytest.fixture
def midas() -> Asteroid:
    """Midas — fastest transit but hazardous.

    spkid=2001981, M-class, 3.4km, MOID=0.0036 AU, hazardous.
    """
    return Asteroid(
        source_id=ObjectId("663f1a2b3c4d5e6f7a8b9c03"),
        name="Midas",
        pdes="1981",
        spkid=2001981,
        class_="M",
        diameter=3.4,
        moid=0.0036,
        moid_days=4,
        neo=True,
        hazard=True,
        elements=[
            Element("Platinum", 1.0e6, 78),
            Element("Gold", 8.0e5, 79),
            Element("Iron", 4.0e7, 26),
        ],
    )


@pytest.fixture
def eros() -> Asteroid:
    """Eros — largest M-class NEO but long transit.

    spkid=2000433, M-class, 16.84km, MOID=0.1486 AU, non-hazardous.
    """
    return Asteroid(
        source_id=ObjectId("663f1a2b3c4d5e6f7a8b9c04"),
        name="Eros",
        pdes="433",
        spkid=2000433,
        class_="M",
        diameter=16.84,
        moid=0.1486,
        moid_days=149,
        neo=True,
        hazard=False,
        elements=[
            Element("Gold", 2.0e7, 79),
            Element("Platinum", 1.5e7, 78),
            Element("Iron", 5.0e8, 26),
        ],
    )


@pytest.fixture
def toutatis() -> Asteroid:
    """Toutatis — C-class, closest, hazardous.

    spkid=2004179, C-class, 5.4km, MOID=0.0066 AU, hazardous.
    """
    return Asteroid(
        source_id=ObjectId("663f1a2b3c4d5e6f7a8b9c05"),
        name="Toutatis",
        pdes="4179",
        spkid=2004179,
        class_="C",
        diameter=5.4,
        moid=0.0066,
        moid_days=7,
        neo=True,
        hazard=True,
        elements=[
            Element("Water", 3.0e7, 0),
            Element("Carbon", 5.0e7, 6),
            Element("Iron", 2.0e7, 26),
            Element("Magnesium", 1.0e7, 12),
            Element("Silicon", 8.0e6, 14),
        ],
    )


@pytest.fixture
def cuyo() -> Asteroid:
    """Cuyo — best safe C-class target.

    spkid=2003753, C-class, 5.7km, MOID=0.0727 AU, non-hazardous.
    """
    return Asteroid(
        source_id=ObjectId("663f1a2b3c4d5e6f7a8b9c06"),
        name="Cuyo",
        pdes="3753",
        spkid=2003753,
        class_="C",
        diameter=5.7,
        moid=0.0727,
        moid_days=73,
        neo=True,
        hazard=False,
        elements=[
            Element("Water", 5.0e7, 0),
            Element("Carbon", 6.0e7, 6),
            Element("Iron", 1.5e7, 26),
        ],
    )


@pytest.fixture
def unnamed_m_class() -> Asteroid:
    """Unnamed M-class asteroid (spkid 276049). Will receive name on landing."""
    return Asteroid(
        source_id=ObjectId("663f1a2b3c4d5e6f7a8b9c07"),
        name=None,
        pdes="276049",
        spkid=276049,
        class_="M",
        diameter=3.5,
        moid=0.0974,
        moid_days=97,
        neo=True,
        hazard=False,
        elements=[
            Element("Platinum", 1.2e6, 78),
            Element("Gold", 6.0e5, 79),
        ],
    )


# ─── sample ship ──────────────────────────────────────────────────────────

@pytest.fixture
def base_mining_ship() -> Ship:
    """A fresh Tier 1 mining ship."""
    return Ship(
        ship_id="SHIP-001",
        name="GoldRush-1",
        class_="mining_transport",
        tier=1,
        cargo_capacity_kg=50_000,
    )


# ─── real expected values (from PRD) ──────────────────────────────────────

@pytest.fixture
def expected_transit_values() -> dict:
    """Expected transit times from PRD v2.0 Transit Time Model table."""
    return {
        "Midas":    {"moid": 0.0036, "one_way": 34, "source": "PRD table"},
        "Toutatis": {"moid": 0.0066, "one_way": 37, "source": "PRD table"},
        "Heracles": {"moid": 0.0584, "one_way": 88, "source": "PRD table"},
        "Zeus":     {"moid": 0.0707, "one_way": 101, "source": "PRD table"},
        "Eros":     {"moid": 0.1486, "one_way": 179, "source": "PRD table"},
    }
