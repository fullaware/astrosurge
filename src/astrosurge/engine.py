"""Stateful mission engine — persists ships, missions, events, and market state to MongoDB."""

from datetime import datetime, timezone
from typing import Optional

from .db import Database
from .models import (
    Ship, ShipEvent, Mission, MissionMetrics, UpgradeModule,
    SHIP_CLASSES, SHIP_STATUSES, PHASE_NAMES,
    MISSION_TYPES, MISSION_TYPE_TIER, UPGRADE_MODULES, TIER_REQUIREMENTS,
)
from .mission import run_mission, MissionResult
from .market import MarketState, sell_cargo
from .config import settings
from .transit import calc_round_trip


class Engine:
    """Orchestrates stateful missions with MongoDB persistence."""

    def __init__(self, db: Database):
        self.db = db

    # ─── Ship Management ─────────────────────────────────────────────

    def build_ship(self, name: str, class_: str = "mining_transport") -> Ship:
        """Create a new ship and persist it."""
        ship_id = self.db.get_next_ship_id()
        ship = Ship(
            ship_id=ship_id,
            name=name,
            class_=class_,
            status="in_port",
            tier=1,
        )
        self.db.create_ship(ship)
        self.db.record_event(ShipEvent(
            ship_id=ship_id, mission_id=None,
            event_type="built",
            data={"name": name, "class": class_},
        ))
        return ship

    def get_ship(self, ship_id: str) -> Optional[Ship]:
        """Load a ship from the database."""
        doc = self.db.get_ship(ship_id)
        if doc:
            return self.db.doc_to_ship(doc)
        return None

    def install_upgrade(self, ship_id: str, module_id: str) -> tuple[bool, str]:
        """Install an upgrade module on a ship. Deducts cost from retained earnings.

        Returns (success, message).
        """
        ship = self.get_ship(ship_id)
        if not ship:
            return False, "Ship not found"

        if ship.status != "in_port":
            return False, "Ship must be in port to upgrade"

        if module_id not in UPGRADE_MODULES:
            return False, f"Unknown module: {module_id}"

        if ship.has_upgrade(module_id):
            return False, f"Module {module_id} already installed"

        module_def = UPGRADE_MODULES[module_id]
        cost = module_def["cost"]

        # ── Deduct cost from retained earnings ──────────────────────
        if ship.retained_earnings < cost:
            shortfall = cost - ship.retained_earnings
            return False, (
                f"Need ${shortfall:,.0f} more in retained earnings. "
                f"Current: ${ship.retained_earnings:,.0f}, "
                f"Cost: ${cost:,.0f}"
            )

        module = UpgradeModule(
            module_id=module_id,
            tier=module_def["tier"],
        )

        new_earnings = ship.retained_earnings - cost
        new_spend = ship.total_upgrade_spend + cost

        upgrades = [u.to_dict() for u in ship.upgrades]
        upgrades.append(module.to_dict())

        # Recompute tier from installed upgrades
        new_tier = ship.tier
        for t, reqs in sorted(TIER_REQUIREMENTS.items()):
            if all(any(u["module_id"] == r for u in upgrades) for r in reqs):
                new_tier = max(new_tier, t)

        self.db.update_ship(ship_id, {
            "upgrades": upgrades,
            "tier": new_tier,
            "retained_earnings": new_earnings,
            "total_upgrade_spend": new_spend,
        })
        self.db.record_event(ShipEvent(
            ship_id=ship_id, mission_id=None,
            event_type="upgraded",
            data={
                "module_id": module_id,
                "tier": module_def["tier"],
                "cost": cost,
                "retained_earnings_after": new_earnings,
            },
        ))
        return True, f"Installed {module_def['name']} (Tier {module_def['tier']}) — cost ${cost:,.0f}"

    def _auto_install_upgrades(
        self, ship: Ship, required_tier: int
    ) -> tuple[bool, str, list[str]]:
        """Auto-install missing upgrades needed to reach required_tier.

        Returns (success, message_or_detail, list_of_installed_module_ids).
        Deducts costs from ship.retained_earnings.
        """
        installed_ids = [u.module_id for u in ship.upgrades]
        missing_modules: list[tuple[str, int]] = []  # (module_id, cost)

        for tier in range(ship.tier + 1, required_tier + 1):
            reqs = TIER_REQUIREMENTS.get(tier, [])
            for mod_id in reqs:
                if mod_id not in installed_ids:
                    missing_modules.append((mod_id, UPGRADE_MODULES[mod_id]["cost"]))

        if not missing_modules:
            return True, "No upgrades needed", []

        total_cost = sum(cost for _, cost in missing_modules)

        if ship.retained_earnings < total_cost:
            shortfall = total_cost - ship.retained_earnings
            details = "; ".join(
                f"{UPGRADE_MODULES[mid]['name']} (${cost:,})"
                for mid, cost in missing_modules
            )
            return False, (
                f"Need ${shortfall:,.0f} more retained earnings to auto-install "
                f"required upgrades for Tier {required_tier}. "
                f"Current: ${ship.retained_earnings:,.0f}, Total cost: ${total_cost:,.0f}. "
                f"Required: {details}"
            ), []

        # Install each missing module
        new_earnings = ship.retained_earnings
        new_spend = ship.total_upgrade_spend
        installed_now = []
        for mod_id, cost in missing_modules:
            new_earnings -= cost
            new_spend += cost
            installed_now.append(mod_id)

        # Build the complete upgrades list
        upgrades = [u.to_dict() for u in ship.upgrades]
        for mod_id in installed_now:
            module_def = UPGRADE_MODULES[mod_id]
            upgrades.append({
                "module_id": mod_id,
                "tier": module_def["tier"],
                "installed_at": datetime.now(timezone.utc).isoformat(),
            })

        # Recompute tier
        new_tier = ship.tier
        for t, reqs in sorted(TIER_REQUIREMENTS.items()):
            if all(any(u["module_id"] == r for u in upgrades) for r in reqs):
                new_tier = max(new_tier, t)

        self.db.update_ship(ship.ship_id, {
            "upgrades": upgrades,
            "tier": new_tier,
            "retained_earnings": new_earnings,
            "total_upgrade_spend": new_spend,
        })

        for mod_id in installed_now:
            self.db.record_event(ShipEvent(
                ship_id=ship.ship_id, mission_id=None,
                event_type="auto_upgraded",
                data={
                    "module_id": mod_id,
                    "cost": UPGRADE_MODULES[mod_id]["cost"],
                    "retained_earnings_after": new_earnings,
                },
            ))

        names = [UPGRADE_MODULES[mid]["name"] for mid in installed_now]
        return True, f"Auto-installed: {', '.join(names)} (cost ${total_cost:,})", installed_now

    # ─── Mission Lifecycle ───────────────────────────────────────────

    def launch_mission(
        self,
        ship_id: str,
        spkid: int,
        mission_type: str = "mining_fast_roi",
        reusable: bool = True,
        refinery: bool = False,
        seed: Optional[int] = None,
    ) -> Mission:
        """Launch a mission: validate ship, auto-install upgrades if needed,
        create mission doc, run simulation, persist, accumulate earnings."""
        ship = self.get_ship(ship_id)
        if not ship:
            raise ValueError(f"Ship {ship_id} not found")

        if ship.status != "in_port":
            raise ValueError(f"Ship {ship_id} is {ship.status}, not in_port")

        asteroid_doc = self.db.find_asteroid_by_spkid(spkid)
        if not asteroid_doc:
            raise ValueError(f"Asteroid spkid={spkid} not found")

        asteroid = self.db.doc_to_asteroid(asteroid_doc)

        # ── Auto-install missing upgrades ──────────────────────────
        required_tier = MISSION_TYPE_TIER.get(mission_type, 1)
        auto_installed = []
        if ship.tier < required_tier:
            ok, msg, auto_installed = self._auto_install_upgrades(ship, required_tier)
            if not ok:
                raise ValueError(msg)
            # Reload ship after upgrades
            ship = self.get_ship(ship_id)

        # Create mission document
        mission_id = self.db.get_next_mission_id()
        transit = calc_round_trip(asteroid.moid)

        mission = Mission(
            mission_id=mission_id,
            ship_id=ship_id,
            asteroid_source_id=asteroid.source_id,
            asteroid_name=asteroid.name or f"spkid-{asteroid.spkid}",
            spkid=spkid,
            mission_type=mission_type,
            tier=ship.tier,
            phase=1,
            phase_name="asteroid_identification",
            status="active",
            moid_au=asteroid.moid,
            transit_time_days_one_way=transit.one_way_days,
            round_trip_days=transit.round_trip_days,
        )
        self.db.create_mission(mission)

        # Mark ship as active
        self.db.update_ship(ship_id, {
            "status": "active",
            "last_mission_id": mission_id,
        })
        self.db.record_event(ShipEvent(
            ship_id=ship_id, mission_id=mission_id,
            event_type="launched",
            data={"spkid": spkid, "mission_type": mission_type},
        ))

        # Cap mining days so total mission doesn't exceed 365 days
        fixed_days = (transit.one_way_days * 2) + transit.setup_days + transit.prep_days
        max_mining = max(0, 365 - fixed_days)
        capped_mining = min(transit.mining_days, max_mining)

        # Run the simulation
        result = run_mission(
            asteroid=asteroid,
            ship_cost=settings.LAUNCH_COST_REUSABLE if reusable else settings.LAUNCH_COST_EXPENDABLE,
            launch_cost=None,
            daily_ops=None,
            mining_days=capped_mining,
            previous_mission_profit=0.0,
            seed=seed,
            reusable=reusable,
            refinery=refinery,
        )

        # Persist phase results
        phase_results = []
        for pr in result.phase_results:
            phase_results.append({
                "phase": pr.phase,
                "phase_name": pr.phase_name,
                "status": pr.status,
                "data": pr.data,
            })

        # Update mission with results
        fin = result.financials
        metrics = MissionMetrics(
            total_cost_usd=fin.get("total_cost_usd", 0),
            total_revenue_usd=fin.get("total_revenue_usd", 0),
            net_profit_usd=fin.get("net_profit_usd", 0),
            roi=fin.get("roi", 0),
            total_yield_kg=result.mining.total_ore_kg if result.mining else 0,
            time_to_value_days=result.transit.round_trip_days,
        )

        # ── Track auto-installed upgrades in mission metadata ──────
        mission_meta = {
            "status": result.status,
            "phase": 11,
            "phase_name": "financial_analysis",
            "metrics": metrics.to_dict(),
            "phase_results": phase_results,
            "error": result.error,
        }
        if auto_installed:
            mission_meta["auto_upgraded_modules"] = [
                {
                    "module_id": mid,
                    "name": UPGRADE_MODULES[mid]["name"],
                    "cost": UPGRADE_MODULES[mid]["cost"],
                }
                for mid in auto_installed
            ]

        self.db.update_mission(mission_id, mission_meta)

        # Record events for each phase
        for pr in result.phase_results:
            self.db.record_event(ShipEvent(
                ship_id=ship_id, mission_id=mission_id,
                event_type=pr.phase_name,
                data={"phase": pr.phase, "status": pr.status},
            ))

        self.db.record_event(ShipEvent(
            ship_id=ship_id, mission_id=mission_id,
            event_type="mission_complete" if result.status == "completed" else "disabled",
            data={"status": result.status, "revenue": fin.get("total_revenue_usd", 0)},
        ))

        # Persist daily ticks
        ticks = self._build_ticks(result, mission_id)
        self.db.persist_ticks(mission_id, ticks)

        # Apply market price changes from cargo sale
        if result.market_result and result.market_result.get("price_changes"):
            current_prices = self.db.get_market_state()
            for elem, change in result.market_result["price_changes"].items():
                current_prices[elem] = change["new_price"]
            self.db.save_market_state(current_prices)

        # ── Update ship: back to port + add retained earnings + cargo value ──
        net_profit = fin.get("net_profit_usd", 0)
        total_revenue = fin.get("total_revenue_usd", 0)
        retained_earnings_before = ship.retained_earnings
        new_retained = retained_earnings_before + net_profit
        new_cargo_sold = (ship.total_cargo_value_sold or 0) + total_revenue

        self.db.update_ship(ship_id, {
            "status": "in_port",
            "mission_count": ship.mission_count + 1,
            "veteran_status": (ship.mission_count + 1) >= 5,
            "retained_earnings": new_retained,
            "total_cargo_value_sold": new_cargo_sold,
        })

        self.db.record_event(ShipEvent(
            ship_id=ship_id, mission_id=mission_id,
            event_type="earnings_updated",
            data={
                "net_profit": net_profit,
                "total_revenue": total_revenue,
                "retained_earnings_before": retained_earnings_before,
                "retained_earnings_after": new_retained,
                "total_cargo_value_sold": new_cargo_sold,
            },
        ))

        # Reload from DB to return actual persisted state
        return self.db.get_mission(mission_id)

    def relaunch_ship(
        self,
        ship_id: str,
        spkid: Optional[int] = None,
        mission_type: str = "mining_fast_roi",
        seed: Optional[int] = None,
        reusable: bool = True,
        refinery: bool = False,
    ) -> Mission:
        """Relaunch a ship on a new mission — optionally auto-select an asteroid.

        If spkid is not provided, auto-selects a suitable asteroid.
        """
        ship = self.get_ship(ship_id)
        if not ship:
            raise ValueError(f"Ship {ship_id} not found")

        if ship.status != "in_port":
            raise ValueError(f"Ship {ship_id} is {ship.status}, not in_port")

        if spkid is None:
            spkid = self._select_asteroid_for_relaunch(ship)

        return self.launch_mission(
            ship_id=ship_id,
            spkid=spkid,
            mission_type=mission_type,
            reusable=reusable,
            refinery=refinery,
            seed=seed,
        )

    def _select_asteroid_for_relaunch(self, ship: Ship) -> int:
        """Auto-select a suitable asteroid for a relaunch mission.

        Preferences: NEO → Class M → Largest diameter → Not recently targeted.
        """
        # Get the ship's recently targeted spkids (last 3 missions)
        recent_spkids: set[int] = set()
        missions_cursor = self.db.astrosurge_db.missions.find(
            {"ship_id": ship.ship_id},
            {"spkid": 1, "_id": 0},
        ).sort("_id", -1).limit(3)
        for m in missions_cursor:
            if "spkid" in m:
                recent_spkids.add(m["spkid"])

        # Query for a suitable asteroid (must fit within 365-day mission)
        pipeline = [
            {"$match": {
                "neo": True,
                "moid": {"$gt": 0, "$lte": 0.10},
                "spkid": {"$nin": list(recent_spkids)},
            }},
            {"$sort": {"diameter": -1}},
            {"$limit": 10},
        ]
        candidates = list(self.db.asteroids_collection.aggregate(pipeline))

        if not candidates:
            # Fallback: any asteroid within range, not recently targeted
            pipeline[0]["$match"].pop("neo", None)
            candidates = list(self.db.asteroids_collection.aggregate(pipeline))

        if not candidates:
            raise ValueError("No suitable asteroid found for relaunch")

        # Pick the largest M-class, or largest overall
        m_class = [c for c in candidates if c.get("class") == "M"]
        pick = m_class[0] if m_class else candidates[0]
        return pick["spkid"]

    def _build_ticks(self, result: MissionResult, mission_id: str) -> list[dict]:
        """Build daily tick records from mission result — with events for all phases."""
        from .events import generate_events

        # Phase mapping by sequential day counter
        phase_at_day = {}
        day_counter = 0
        transit_ow = result.transit.one_way_days if result.transit else 0
        setup_d = result.transit.setup_days if result.transit else 3
        mining_d = len(result.mining.daily_yields) if result.mining else 0

        # Offset mining yield days by transit + setup duration
        mining_offset = transit_ow + setup_d
        yield_by_day = {}
        if result.mining:
            for yd in result.mining.daily_yields:
                yield_by_day[yd.day + mining_offset] = yd
        prep_d = result.transit.prep_days if result.transit else 1
        return_d = transit_ow

        est_moid = max(0, (transit_ow - 30) / 1000) if transit_ow > 30 else 0.01

        # Phase 5: Transit outbound
        for d in range(transit_ow):
            day_counter += 1
            phase_at_day[day_counter] = (5, "transit_execution", "🛸")
        # Phase 6: Site setup
        for d in range(setup_d):
            day_counter += 1
            phase_at_day[day_counter] = (6, "site_establishment", "🏗️")
        # Phase 7: Mining
        for d in range(mining_d):
            day_counter += 1
            phase_at_day[day_counter] = (7, "mining_operations", "⛏️")
        # Phase 8: Cargo prep
        for d in range(prep_d):
            day_counter += 1
            phase_at_day[day_counter] = (8, "cargo_sealing", "📦")
        # Phase 9: Return
        for d in range(return_d):
            day_counter += 1
            phase_at_day[day_counter] = (9, "return_transit", "🏠")

        ticks = []
        for snap in result.funding_snapshots:
            day = snap.days_elapsed
            phase_num, phase_name, phase_icon = phase_at_day.get(day, (0, "unknown", "❓"))

            tick = {
                "mission_id": mission_id,
                "day": day,
                "phase": phase_num,
                "phase_name": phase_name,
                "phase_icon": phase_icon,
                "funding_remaining": round(snap.funding_remaining, 2),
                "funding_pool": round(snap.funding_pool, 2),
                "debt_owed": round(snap.debt_owed, 2),
                "cargo_value": round(snap.cargo_value, 2),
                "daily_roi": round(snap.daily_roi, 4),
                "is_break_even": snap.is_break_even,
                "cumulative_ops": round(snap.cumulative_ops_cost, 2),
                "events": [],
                "repositioning": False,
            }

            # Generate phase-specific events for non-mining days
            if phase_num in (5, 6, 8, 9):
                tick["events"] = generate_events(phase_num, day, moid_au=est_moid)

            # Merge mining yield if this was a mining day
            yd = yield_by_day.get(day)
            if yd:
                tick["mined_kg"] = round(yd.total_mined_kg, 2)
                tick["daily_revenue"] = round(yd.daily_revenue, 2)
                top_elems = sorted(
                    yd.element_breakdown.items(),
                    key=lambda x: -x[1]["value"],
                )[:3]
                tick["top_elements"] = [
                    {"name": e, "value": v["value"], "mass_kg": v["mass_kg"]}
                    for e, v in top_elems
                ]
                tick["events"].extend(yd.events)

                if yd.total_mined_kg == 0 and len(yd.events) > 0:
                    tick["repositioning"] = True
                    for ev in yd.events:
                        if "reposition" in ev.get("type", "").lower():
                            tick["phase_name"] = "repositioning"
                            tick["phase_icon"] = "🚚"
                            break

            ticks.append(tick)

        return ticks

    def get_mission(self, mission_id: str) -> Optional[dict]:
        """Get a mission with its events."""
        doc = self.db.get_mission(mission_id)
        if not doc:
            return None
        events = self.db.get_mission_events(mission_id)
        doc["events"] = events
        return doc
