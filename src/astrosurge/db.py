"""MongoDB connection and operations for AstroSurge.

Provides:
  - Database class for connecting to MongoDB
  - Query methods for asteroids collection
  - Persistence for missions, ships, events
"""

from pymongo import MongoClient
from typing import Optional

from .config import settings
from .models import Asteroid, Element


class Database:
    """MongoDB database connection and operations."""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.asteroids_db = None
        self.asteroids_collection = None
        self.astrosurge_db = None
        self.missions_collection = None
        self.ships_collection = None
        self.ship_events_collection = None

    def connect(self) -> "Database":
        """Connect to MongoDB."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.asteroids_db = self.client["asteroids"]
        self.asteroids_collection = self.asteroids_db.asteroids
        self.astrosurge_db = self.client[settings.MONGODB_DATABASE]
        self.missions_collection = self.astrosurge_db.missions
        self.ships_collection = self.astrosurge_db.ships
        self.ship_events_collection = self.astrosurge_db.ship_events
        return self

    def close(self):
        """Close the MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ─── Asteroid queries ────────────────────────────────────────────────

    def find_asteroid_by_spkid(self, spkid: int) -> Optional[dict]:
        """Find an asteroid by its SPK ID."""
        return self.asteroids_collection.find_one({"spkid": spkid})

    def find_asteroids(self, query: dict, limit: int = 100) -> list[dict]:
        """Query asteroids with optional filters."""
        cursor = self.asteroids_collection.find(query).limit(limit)
        return list(cursor)

    def find_fast_roi_candidates(self, max_moid: float = 0.10,
                                  min_diameter: float = 3.0,
                                  classes: tuple = ("M",),
                                  limit: int = 50) -> list[dict]:
        """Find candidate asteroids for Fast ROI (Tier 1) missions."""
        query = {
            "moid": {"$lte": max_moid, "$gt": 0},
            "diameter": {"$gte": min_diameter},
            "class": {"$in": list(classes)},
        }
        cursor = self.asteroids_collection.find(query).sort("moid", 1).limit(limit)
        return list(cursor)

    def count_asteroids(self, query: dict) -> int:
        """Count asteroids matching a query."""
        return self.asteroids_collection.count_documents(query)

    # ─── Serialization helpers ───────────────────────────────────────────

    @staticmethod
    def doc_to_asteroid(doc: dict) -> Asteroid:
        """Convert a MongoDB document to an Asteroid model."""
        elements = [
            Element(
                name=e.get("name", "Unknown"),
                mass_kg=float(e.get("mass_kg", 0)),
                number=e.get("number", 0),
            )
            for e in doc.get("elements", [])
        ]
        return Asteroid(
            source_id=doc["_id"],
            name=doc.get("name"),
            pdes=doc.get("pdes", ""),
            spkid=int(doc.get("spkid", 0)),
            class_=doc.get("class", "U"),
            diameter=float(doc.get("diameter", 0)),
            moid=float(doc.get("moid", 0)),
            moid_days=int(doc.get("moid_days", 0)),
            neo=bool(doc.get("neo", False)),
            hazard=bool(doc.get("hazard", False)),
            elements=elements,
        )


# Singleton instance
db = Database()


def get_db() -> Database:
    """Get the database singleton."""
    return db
