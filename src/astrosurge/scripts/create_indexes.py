#!/usr/bin/env python3
"""Create MongoDB indexes for AstroSurge collections.

Usage:
    python -m astrosurge.scripts.create_indexes

This creates the following indexes:

    asteroids.asteroids:
        - spkid_1                     (unique asteroid lookup)
        - class_1_moid_1_diameter_-1  (Fast ROI candidate search)
        - neo_1                       (NEO count)
        - hazard_1                    (hazard count)

    astrosurge.missions:
        - spkid_1                     (mission lookup by asteroid)
        - ship_id_1                   (mission lookup by ship)
        - status_1_created_at_-1      (active mission listing)

    astrosurge.ship_events:
        - ship_id_1_timestamp_-1      (ship event timeline)
        - timestamp_-1                (global event timeline)
"""

from ..db import Database


def main():
    db = Database()
    try:
        print("[astrosurge] Connecting to MongoDB...")
        db.connect()
        print("[astrosurge] Creating indexes...")
        db.ensure_indexes()
        print("[astrosurge] Done!")
    except Exception as e:
        print(f"[astrosurge] Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
