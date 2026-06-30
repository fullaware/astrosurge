"""MongoDB connection and operations for AstroSurge.

Provides:
  - Database class for connecting to MongoDB
  - Query methods for asteroids collection
  - Persistence for missions, ships, events
"""

from datetime import datetime, timezone
from typing import Optional

from pymongo import MongoClient

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
        self.mission_ticks_collection = self.astrosurge_db.mission_ticks
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
                                  min_diameter: float = 1.0,
                                  classes: tuple = ("M", "C"),
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

        # ─── Index management ────────────────────────────────────────────────

    # Known index names we want on asteroids.asteroids (excluding _id_)
    ASTEROID_INDEXES = {
        "spkid_1",
        "class_1_moid_1_diameter_-1",
        "neo_1",
        "hazard_1",
    }

    # Known index names for astrosurge collections
    MISSIONS_INDEXES = {"spkid_1", "ship_id_1", "status_1_created_at_-1"}
    MISSIONS_TICKS_INDEXES = {"mission_id_1_day_1"}
    SHIP_EVENTS_INDEXES = {"ship_id_1_timestamp_-1", "timestamp_-1"}

    def ensure_indexes(self, drop_unused: bool = False):
        """Create indexes for asteroid and astrosurge collections.

        Args:
            drop_unused: If True, removes any index not in the known set.

        Run this once after connecting to improve query performance.
        """
        # — asteroids.asteroids —
        # Primary lookup by SPK ID (used in detail view and simulation)
        self.asteroids_collection.create_index("spkid", name="spkid_1")

        # Fast ROI candidate search: filter by class, moid range, diameter, sort by moid
        # Equality on class first, then sort key (moid), then range filter (diameter)
        self.asteroids_collection.create_index(
            [("class", 1), ("moid", 1), ("diameter", -1)],
            name="class_1_moid_1_diameter_-1",
        )

        # Stats queries: individual field counts
        self.asteroids_collection.create_index("neo", name="neo_1")
        self.asteroids_collection.create_index("hazard", name="hazard_1")

        # — astrosurge collections —
        # Missions lookup by spkid
        self.missions_collection.create_index("spkid", name="spkid_1")
        self.missions_collection.create_index("ship_id", name="ship_id_1")
        self.missions_collection.create_index(
            [("status", 1), ("created_at", -1)],
            name="status_1_created_at_-1",
        )

        # Mission ticks (daily timeline)
        self.mission_ticks_collection.create_index(
            [("mission_id", 1), ("day", 1)],
            name="mission_id_1_day_1",
            unique=True,
        )

        # Ship events timeline
        self.ship_events_collection.create_index(
            [("ship_id", 1), ("timestamp", -1)],
            name="ship_id_1_timestamp_-1",
        )
        self.ship_events_collection.create_index(
            [("timestamp", -1)],
            name="timestamp_-1",
        )

        # Drop unused indexes if requested
        if drop_unused:
            self._drop_unused_indexes(
                self.asteroids_collection, self.ASTEROID_INDEXES, "asteroids.asteroids",
            )
            self._drop_unused_indexes(
                self.missions_collection, self.MISSIONS_INDEXES, "astrosurge.missions",
            )
            self._drop_unused_indexes(
                self.ship_events_collection, self.SHIP_EVENTS_INDEXES, "astrosurge.ship_events",
            )

        print("[astrosurge] Indexes ensured on asteroids.asteroids and astrosurge collections")

    @staticmethod
    def _drop_unused_indexes(collection, known_names: set, label: str):
        """Drop any indexes in the collection not in the known set."""
        for idx in collection.list_indexes():
            name = idx["name"]
            if name == "_id_":
                continue
            if name not in known_names:
                print(f"[astrosurge] Dropping unused index {label}.{name}")
                collection.drop_index(name)


    # ─── Ship persistence ─────────────────────────────────────────────

    def create_ship(self, ship: 'Ship') -> str:
        """Insert a new ship document. Returns ship_id."""
        self.ships_collection.insert_one(ship.to_dict())
        return ship.ship_id

    def get_ship(self, ship_id: str) -> Optional[dict]:
        """Get a ship by ship_id."""
        return self.ships_collection.find_one({"ship_id": ship_id})

    def list_ships(self, status: Optional[str] = None) -> list[dict]:
        """List all ships, optionally filtered by status."""
        query = {"status": status} if status else {}
        cursor = self.ships_collection.find(query).sort("created_at", -1)
        return list(cursor)

    def update_ship(self, ship_id: str, updates: dict):
        """Update fields on a ship document."""
        self.ships_collection.update_one(
            {"ship_id": ship_id},
            {"$set": updates},
        )

    def delete_ship(self, ship_id: str):
        """Permanently delete a ship document."""
        self.ships_collection.delete_one({"ship_id": ship_id})

    def get_next_ship_id(self) -> str:
        """Generate the next ship ID (SHIP-XXX)."""
        last = self.ships_collection.find_one(
            {"ship_id": {"$regex": r"^SHIP-"}},
            sort=[("ship_id", -1)],
        )
        if last:
            num = int(last["ship_id"].split("-")[1]) + 1
        else:
            num = 1
        return f"SHIP-{num:03d}"

    # ─── Mission persistence ────────────────────────────────────────────

    def create_mission(self, mission: 'Mission') -> str:
        """Insert a new mission document. Returns mission_id."""
        self.missions_collection.insert_one(mission.to_dict())
        return mission.mission_id

    def get_mission(self, mission_id: str) -> Optional[dict]:
        """Get a mission by mission_id."""
        return self.missions_collection.find_one({"mission_id": mission_id})

    def list_missions(self, status: Optional[str] = None,
                      limit: int = 50) -> list[dict]:
        """List missions, optionally filtered by status."""
        query = {"status": status} if status else {}
        cursor = self.missions_collection.find(query).sort("created_at", -1).limit(limit)
        return list(cursor)

    def update_mission(self, mission_id: str, updates: dict):
        """Update fields on a mission document."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.missions_collection.update_one(
            {"mission_id": mission_id},
            {"$set": updates},
        )

    def get_next_mission_id(self) -> str:
        """Generate the next mission ID (MISSION-XXX)."""
        last = self.missions_collection.find_one(
            {"mission_id": {"$regex": r"^MISSION-"}},
            sort=[("mission_id", -1)],
        )
        if last:
            num = int(last["mission_id"].split("-")[1]) + 1
        else:
            num = 1
        return f"MISSION-{num:03d}"

    # ─── Ship Events persistence ────────────────────────────────────────

    def record_event(self, event: 'ShipEvent') -> str:
        """Record a ship event. Returns the inserted ID."""
        result = self.ship_events_collection.insert_one(event.to_dict())
        return str(result.inserted_id)

    def get_ship_events(self, ship_id: str, limit: int = 100) -> list[dict]:
        """Get events for a ship, most recent first."""
        cursor = self.ship_events_collection.find(
            {"ship_id": ship_id},
        ).sort("timestamp", -1).limit(limit)
        return list(cursor)

    def get_mission_events(self, mission_id: str) -> list[dict]:
        """Get events for a mission."""
        cursor = self.ship_events_collection.find(
            {"mission_id": mission_id},
        ).sort("timestamp", 1)
        return list(cursor)

    # ─── Market State persistence ───────────────────────────────────────

    def get_market_state(self) -> dict:
        """Load the persistent market state document."""
        doc = self.astrosurge_db["market_state"].find_one({"_id": "global"})
        if doc:
            return doc.get("prices", {})
        return {}

    def save_market_state(self, prices: dict):
        """Save market prices to the persistent market state."""
        self.astrosurge_db["market_state"].update_one(
            {"_id": "global"},
            {"$set": {"prices": prices}},
            upsert=True,
        )

    # ─── Mission Ticks (daily timeline) ──────────────────────────────

    def persist_ticks(self, mission_id: str, ticks: list[dict]):
        """Batch insert daily tick records for a mission."""
        if not ticks:
            return
        for t in ticks:
            t["mission_id"] = mission_id
        self.mission_ticks_collection.insert_many(ticks, ordered=False)

    def get_mission_ticks(self, mission_id: str, page: int = 1,
                          per_page: int = 50) -> dict:
        """Get paginated daily ticks for a mission."""
        total = self.mission_ticks_collection.count_documents(
            {"mission_id": mission_id}
        )
        cursor = self.mission_ticks_collection.find(
            {"mission_id": mission_id},
        ).sort("day", 1).skip((page - 1) * per_page).limit(per_page)
        return {
            "ticks": list(cursor),
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }


    # ─── Serialization helpers ───────────────────────────────────────────

    def doc_to_ship(self, doc: dict) -> 'Ship':
        """Convert a MongoDB document to a Ship model."""
        from .models import Ship, UpgradeModule
        upgrades = [
            UpgradeModule(
                module_id=u["module_id"],
                tier=u.get("tier", 0),
                installed_at=datetime.fromisoformat(u["installed_at"]) if isinstance(u.get("installed_at"), str) else u.get("installed_at", datetime.now(timezone.utc)),
            )
            for u in doc.get("upgrades", [])
        ]
        return Ship(
            ship_id=doc["ship_id"],
            name=doc.get("name", ""),
            class_=doc.get("class", "mining_transport"),
            status=doc.get("status", "in_port"),
            tier=doc.get("tier", 1),
            mission_count=doc.get("mission_count", 0),
            veteran_status=doc.get("veteran_status", False),
            cargo_capacity_kg=doc.get("cargo_capacity_kg", 50_000),
            propulsion_type=doc.get("propulsion_type", "nuclear_thermal"),
            shielding_type=doc.get("shielding_type", "passive"),
            repair_bots_count=doc.get("repair_bots_count", 2),
            current_cargo_kg=doc.get("current_cargo_kg", 0.0),
            retained_earnings=doc.get("retained_earnings", 0.0),
            total_upgrade_spend=doc.get("total_upgrade_spend", 0.0),
            total_cargo_value_sold=doc.get("total_cargo_value_sold", 0.0),
            upgrades=upgrades,
            last_mission_id=doc.get("last_mission_id"),
        )

    def doc_to_mission(self, doc: dict) -> 'Mission':
        """Convert a MongoDB document to a Mission model."""
        from .models import Mission, MissionMetrics
        metrics = MissionMetrics(
            total_cost_usd=doc.get("metrics", {}).get("total_cost_usd", 0),
            total_revenue_usd=doc.get("metrics", {}).get("total_revenue_usd", 0),
            net_profit_usd=doc.get("metrics", {}).get("net_profit_usd", 0),
            roi=doc.get("metrics", {}).get("roi", 0),
            total_yield_kg=doc.get("metrics", {}).get("total_yield_kg", 0),
            time_to_value_days=doc.get("metrics", {}).get("time_to_value_days", 0),
            break_even_price_per_kg=doc.get("metrics", {}).get("break_even_price_per_kg", 0),
            daily_throughput_kg=doc.get("metrics", {}).get("daily_throughput_kg", 36_000),
        )
        return Mission(
            mission_id=doc["mission_id"],
            ship_id=doc["ship_id"],
            asteroid_source_id=doc["asteroid_source_id"],
            asteroid_name=doc.get("asteroid_name", ""),
            spkid=doc.get("spkid", 0),
            mission_type=doc.get("mission_type", "mining_fast_roi"),
            tier=doc.get("tier", 1),
            phase=doc.get("phase", 1),
            phase_name=doc.get("phase_name", "asteroid_identification"),
            status=doc.get("status", "active"),
            moid_au=doc.get("moid_au", 0),
            transit_time_days_one_way=doc.get("transit_time_days_one_way", 0),
            round_trip_days=doc.get("round_trip_days", 0),
            metrics=metrics,
            phase_results=doc.get("phase_results", []),
            error=doc.get("error"),
            created_at=datetime.fromisoformat(doc["created_at"]) if isinstance(doc.get("created_at"), str) else doc.get("created_at", datetime.now(timezone.utc)),
            updated_at=datetime.fromisoformat(doc["updated_at"]) if isinstance(doc.get("updated_at"), str) else doc.get("updated_at", datetime.now(timezone.utc)),
        )


    @staticmethod
    def doc_to_asteroid(doc: dict) -> Asteroid:
        """Convert a MongoDB document to an Asteroid model.

        Elements are generated deterministically from SPK ID and class,
        not from MongoDB data, to give class-appropriate composition.
        """
        from .composition import generate_elements

        spkid = int(doc.get("spkid", 0))
        class_ = doc.get("class", "U")
        diameter = float(doc.get("diameter", 0))

        elements = generate_elements(
            spkid=spkid,
            class_=class_,
            diameter_km=diameter,
        )
        return Asteroid(
            source_id=doc["_id"],
            name=doc.get("name"),
            pdes=doc.get("pdes", ""),
            spkid=spkid,
            class_=class_,
            diameter=diameter,
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
