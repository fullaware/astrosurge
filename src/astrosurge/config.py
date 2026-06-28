"""Configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings."""

    # MongoDB
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "astrosurge")

    # Mining constants (from Full Aware / PRD v2.0)
    LAUNCH_COST_EXPENDABLE: float = 150_000_000
    LAUNCH_COST_REUSABLE: float = 97_000_000
    REFURBISHMENT_COST: float = 2_000_000  # Refurbishment between reusable launches
    CARGO_CAPACITY_KG: float = 50_000
    DAILY_OPS_COST: float = 45_000
    REFINERY_DAILY_COST: float = 15_000  # Extra daily ops when on-site refinery active
    MINING_RATE_KG_PER_DAY: float = 36_000

    # Market prices (USD per kg, June 2026 reference)
    GOLD_PRICE_PER_KG: float = 135_614.87
    SILVER_PRICE_PER_KG: float = 2_119.05
    PLATINUM_PRICE_PER_KG: float = 54_720.49
    PALLADIUM_PRICE_PER_KG: float = 41_345.80
    RHODIUM_PRICE_PER_KG: float = 234_442.90
    IRIDIUM_PRICE_PER_KG: float = 186_474.06
    RUTHENIUM_PRICE_PER_KG: float = 15_110.83
    OSMIUM_PRICE_PER_KG: float = 385_808.40

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()
