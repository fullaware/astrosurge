"""Event generation for each mission phase — multiple events per day possible."""

import random


def generate_events(phase: int, day: int, **context) -> list[dict]:
    """Generate 0-3 events for a given day in a given phase.

    Args:
        phase: Mission phase number (5=transit, 6=setup, 7=mining, 8=prep, 9=return)
        day: Day number within the mission
        context: Extra context (moid_au, hazard, class, etc.)

    Returns:
        List of event dicts, each with: type, description, severity
    """
    if phase == 5:
        return _transit_events(day, is_outbound=True, **context)
    elif phase == 6:
        return _setup_events(day, **context)
    elif phase == 7:
        return _mining_extras(day, **context)  # mining.py handles its own primary events
    elif phase == 8:
        return _prep_events(day, **context)
    elif phase == 9:
        return _transit_events(day, is_outbound=False, **context)
    return []


# ─── Transit Events (Phases 5 & 9) ──────────────────────────────────────

TRANSIT_EVENTS = [
    # (weight, event_type, description, severity)
    (15, "nominal_burn", "Course correction burn — nominal delta-v", "info"),
    (10, "debris_avoidance", "Debris field detected — trajectory adjusted", "warning"),
    (8, "comms_delay", "Communication lag — telemetry delayed 14 seconds", "info"),
    (7, "solar_flare", "Solar flare detected — radiation shielding activated", "warning"),
    (6, "thruster_calibration", "Thruster recalibration — efficiency improved 0.3%", "info"),
    (5, "fuel_trim", "Fuel burn trim adjustment — slight variance corrected", "info"),
    (4, "heat_flux", "Thermal flux anomaly — radiator adjustment", "warning"),
    (3, "trajectory_check", "Scheduled trajectory verification — on course", "info"),
    (2, "star_tracker", "Star tracker recalibration — attitude corrected", "info"),
    (1, "nav_hazard", "Navigation hazard warning — uncatalogued object nearby", "critical"),
]


def _transit_events(day: int, is_outbound: bool = True, **kw) -> list[dict]:
    """Generate 0-2 transit events per day."""
    events = []
    rolls = random.random()
    # 70% chance of 0 events, 20% chance of 1, 10% chance of 2
    num_events = 0
    if rolls < 0.30:
        num_events = 1
    if rolls < 0.10:
        num_events = 2

    for _ in range(num_events):
        ev = _pick_weighted(TRANSIT_EVENTS)
        # Customize description with day number
        direction = "outbound" if is_outbound else "return"
        events.append({
            "type": ev[1],
            "description": f"[Day {day} {direction}] {ev[2]}",
            "severity": ev[3],
        })
    return events


# ─── Site Setup Events (Phase 6) ────────────────────────────────────────

SETUP_EVENTS = [
    (15, "approach_burn", "Approach burn initiated — orbital insertion", "info"),
    (12, "surface_scan", "Surface scan complete — viable mining zone identified", "info"),
    (10, "touchdown", "Touchdown confirmed — landing gear deployed", "info"),
    (8, "anchoring", "Anchoring system deployed — hull secured to surface", "info"),
    (7, "equip_deploy", "Mining equipment deployed — drill assembly online", "info"),
    (6, "site_survey", "Site survey — optimal extraction point marked", "info"),
    (5, "regolith_test", "Regolith sample analysis — composition confirmed", "info"),
    (4, "stabilization", "Surface stabilization — terrain compensation active", "info"),
    (3, "power_grid", "Power grid online — reactor synchronization nominal", "info"),
    (2, "comm_relay", "Communication relay established — Earth link nominal", "info"),
    (1, "hazard_assessment", "Hazard assessment — local terrain evaluated", "warning"),
]


def _setup_events(day: int, **kw) -> list[dict]:
    """Generate 1-2 setup events per day."""
    events = []
    num_events = 2 if random.random() < 0.5 else 1
    for _ in range(num_events):
        ev = _pick_weighted(SETUP_EVENTS)
        events.append({
            "type": ev[1],
            "description": f"[Setup Day {day}] {ev[2]}",
            "severity": ev[3],
        })
    return events


# ─── Additional Mining Events (beyond what mining.py generates) ─────────

MINING_EVENTS = [
    (10, "vein_exhaustion", "Current vein thinning — yield decreasing", "warning"),
    (8, "ground_vibration", "Ground vibration detected — site stability affected", "warning"),
    (7, "equipment_maintenance", "Scheduled equipment maintenance — drill head serviced", "info"),
    (6, "dust_plume", "Regolith dust plume — visibility reduced temporarily", "info"),
    (5, "conveyor_jam", "Ore transporter jam — cleared by repair bot", "warning"),
    (4, "drill_bit_wear", "Drill bit wear detected — replacement scheduled", "info"),
    (3, "seismic_event", "Minor seismic event — operations paused 2 hours", "warning"),
    (2, "grade_surprise", "Unexpected high-grade streak — yield spike", "info"),
    (1, "cave_in", "Subsurface cavity collapse — equipment repositioned", "critical"),
]


def _mining_extras(day: int, **kw) -> list[dict]:
    """Generate 0-2 additional mining events per day."""
    events = []
    if random.random() < 0.25:  # 25% chance of extra mining events
        num_events = 1 if random.random() < 0.7 else 2
        for _ in range(num_events):
            ev = _pick_weighted(MINING_EVENTS)
            events.append({
                "type": ev[1],
                "description": f"[Mining Day {day}] {ev[2]}",
                "severity": ev[3],
            })
    return events


# ─── Cargo Prep Events (Phase 8) ────────────────────────────────────────

PREP_EVENTS = [
    (20, "container_seal", "Cargo container sealed — integrity check passed", "info"),
    (15, "mass_calc", "Final mass calculation — trajectory update", "info"),
    (12, "seal_verify", "Container seal verification — pressure holding", "info"),
    (10, "temp_stabilize", "Cargo temperature stabilized — within safe range", "info"),
    (8, "lock_mechanism", "Locking mechanism engaged — container secured", "info"),
    (5, "seal_leak", "Minor seal leak detected — resealed successfully", "warning"),
    (3, "redistribution", "Cargo redistribution — center of mass adjusted", "info"),
    (2, "inventory_log", "Inventory manifest uploaded — cargo certified", "info"),
]


def _prep_events(day: int, **kw) -> list[dict]:
    """Generate 1-2 prep events."""
    events = []
    num_events = 2 if random.random() < 0.6 else 1
    for _ in range(num_events):
        ev = _pick_weighted(PREP_EVENTS)
        events.append({
            "type": ev[1],
            "description": f"[Prep Day {day}] {ev[2]}",
            "severity": ev[3],
        })
    return events


# ─── Repositioning events ───────────────────────────────────────────────

REPOSITION_EVENTS = [
    (15, "reposition_start", "Mining site unstable — initiating repositioning", "warning"),
    (12, "equip_retract", "Mining equipment retracted for relocation", "info"),
    (10, "transit_new_site", "Traversing to new mining site — low speed", "info"),
    (8, "site_survey_new", "New site surveyed — viable ore confirmed", "info"),
    (7, "anchoring_new", "Anchoring at new location — stabilization in progress", "info"),
    (6, "equip_deploy_new", "Equipment redeployed at new site", "info"),
    (5, "grade_confirmation", "Ore grade confirmed at new location — mining resuming", "info"),
]


def repositioning_event(day: int, repo_day: int, total_repo: int) -> dict:
    """Generate an event for a day spent repositioning."""
    pool = REPOSITION_EVENTS
    ev = _pick_weighted(pool)
    return {
        "type": ev[1],
        "description": f"[Repo Day {repo_day}/{total_repo}] {ev[2]}",
        "severity": ev[3],
    }


# ─── Utility ─────────────────────────────────────────────────────────────

def _pick_weighted(pool: list[tuple]) -> tuple:
    """Pick an item from a weighted list."""
    total = sum(w for w, *_ in pool)
    r = random.uniform(0, total)
    upto = 0
    for w, *rest in pool:
        upto += w
        if r <= upto:
            return (w, *rest)
    return pool[-1]
