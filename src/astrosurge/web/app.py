"""FastAPI application for AstroSurge Web UI."""

import os
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from bson import ObjectId

from ..db import Database, get_db
from ..models import Ship, SHIP_CLASSES, MISSION_TYPES, UPGRADE_MODULES, TIER_REQUIREMENTS
from ..engine import Engine
from ..asteroid_filter import rank_fast_roi_candidates, FAST_ROI_MAX_MOID_AU, FAST_ROI_MIN_DIAMETER_KM
from ..mission import run_mission
from ..mining import ELEMENT_PRICES
from ..config import settings

# ─── paths ─────────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent

# Resolve webui root: env var takes precedence (used in Docker),
# fall back to relative path from source tree (local development).
_env_webui = os.environ.get("ASTROSURGE_WEBUI_DIR")
if _env_webui:
    WEBUI_ROOT = Path(_env_webui)
else:
    # When running from source tree: /app/src/astrosurge/web/../../.. = /app
    ROOT = HERE.parent.parent.parent
    WEBUI_ROOT = ROOT / "webui"

TEMPLATES_DIR = WEBUI_ROOT / "templates"
STATIC_DIR = WEBUI_ROOT / "static"

print(f"[astrosurge] TEMPLATES_DIR={TEMPLATES_DIR} (exists={(TEMPLATES_DIR / 'index.html').exists()})")

# ─── FastAPI app ───────────────────────────────────────────────────────────

app = FastAPI(
    title="AstroSurge",
    description="Agentic asteroid mining simulation",
    version="0.3.0",
)


# ─── MongoDB document serializer ───────────────────────────────────────────

def _serialize_doc(doc):
    """Recursively convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [_serialize_doc(item) for item in doc]
    if not isinstance(doc, dict):
        if isinstance(doc, ObjectId):
            return str(doc)
        if isinstance(doc, datetime):
            return doc.isoformat()
        return doc
    result = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        elif isinstance(v, dict):
            result[k] = _serialize_doc(v)
        elif isinstance(v, list):
            result[k] = [_serialize_doc(item) for item in v]
        else:
            result[k] = v
    return result

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── request/response models ──────────────────────────────────────────────

class SimulateRequest(BaseModel):
    spkid: int
    ship_cost: float = 50_000_000
    launch_cost: Optional[float] = None
    daily_ops: Optional[float] = None
    mining_days: int = 139
    previous_mission_profit: float = 0.0
    reusable: bool = False
    refinery: bool = False
    seed: Optional[int] = None


# ─── template helpers ─────────────────────────────────────────────────────

def _render_html(name: str) -> str:
    """Read an HTML template file."""
    path = TEMPLATES_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Template {name} not found")
    return path.read_text("utf-8")


# ─── startup/shutdown ──────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Connect to MongoDB on startup and ensure indexes."""
    try:
        db = get_db()
        db.connect()
        print(f"[astrosurge] Connected to MongoDB at {settings.MONGODB_URI}")
        # Build indexes in background (non-blocking)
        try:
            db.ensure_indexes()
        except Exception as idx_err:
            print(f"[astrosurge] Index creation failed (non-fatal): {idx_err}")
    except Exception as e:
        print(f"[astrosurge] Warning: MongoDB connection failed: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Close MongoDB on shutdown."""
    try:
        get_db().close()
    except Exception:
        pass


# ─── web UI routes ─────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main dashboard page."""
    return _render_html("index.html")


@app.get("/mission/{spkid}", response_class=HTMLResponse)
async def mission_page(spkid: int):
    """Serve a mission page for a specific asteroid."""
    return _render_html("index.html")


# ─── API routes ────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    db = get_db()
    mongo_ok = False
    ship_count = 0
    try:
        if db.client:
            db.client.admin.command("ping")
            mongo_ok = True
            ship_count = db.astrosurge_db["ships"].count_documents({})
    except Exception:
        pass
    return {
        "status": "ok" if mongo_ok else "degraded",
        "mongodb": mongo_ok,
        "ship_count": ship_count,
        "version": "0.3.0",
    }


@app.get("/api/asteroids/candidates")
async def candidates(
    max_moid: float = Query(FAST_ROI_MAX_MOID_AU, ge=0.001, le=1.0),
    min_diameter: float = Query(FAST_ROI_MIN_DIAMETER_KM, ge=0.1),
    limit: int = Query(20, ge=1, le=100),
):
    """Find candidate asteroids for Fast ROI (Tier 1) missions."""
    db = get_db()
    try:
        docs = db.find_fast_roi_candidates(
            max_moid=max_moid,
            min_diameter=min_diameter,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MongoDB query failed: {e}")

    asteroids = [db.doc_to_asteroid(d) for d in docs]
    ranked = rank_fast_roi_candidates(asteroids)

    return {
        "count": len(ranked),
        "filters": {
            "max_moid_au": max_moid,
            "min_diameter_km": min_diameter,
        },
        "candidates": [card.to_dict() for card in ranked],
    }


@app.get("/api/asteroids/{spkid}")
async def asteroid_detail(spkid: int):
    """Get detailed info on a specific asteroid."""
    db = get_db()
    try:
        doc = db.find_asteroid_by_spkid(spkid)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MongoDB query failed: {e}")

    if doc is None:
        raise HTTPException(status_code=404, detail=f"Asteroid spkid={spkid} not found")

    asteroid = db.doc_to_asteroid(doc)
    return {
        "spkid": asteroid.spkid,
        "name": asteroid.name or "(unnamed)",
        "class": asteroid.class_,
        "diameter_km": asteroid.diameter,
        "moid_au": asteroid.moid,
        "hazard": asteroid.hazard,
        "neo": asteroid.neo,
        "elements": [
            {"name": e.name, "mass_kg": e.mass_kg, "number": e.number}
            for e in asteroid.elements
        ],
    }


@app.post("/api/simulate")
async def simulate(req: SimulateRequest):
    """Run a complete mission simulation for an asteroid."""
    db = get_db()
    try:
        doc = db.find_asteroid_by_spkid(req.spkid)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MongoDB query failed: {e}")

    if doc is None:
        raise HTTPException(status_code=404, detail=f"Asteroid spkid={req.spkid} not found")

    asteroid = db.doc_to_asteroid(doc)

    try:
        result = run_mission(
            asteroid=asteroid,
            ship_cost=req.ship_cost,
            launch_cost=req.launch_cost,
            daily_ops=req.daily_ops,
            mining_days=req.mining_days,
            previous_mission_profit=req.previous_mission_profit,
            seed=req.seed,
            reusable=req.reusable,
            refinery=req.refinery,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")

    return result.to_dict()


@app.get("/api/simulate/{spkid}")
async def simulate_get(
    spkid: int,
    seed: Optional[int] = Query(None),
    reusable: bool = Query(False),
    refinery: bool = Query(False),
):
    """Run a quick mission simulation via GET parameters."""
    db = get_db()
    try:
        doc = db.find_asteroid_by_spkid(spkid)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MongoDB query failed: {e}")

    if doc is None:
        raise HTTPException(status_code=404, detail=f"Asteroid spkid={spkid} not found")

    asteroid = db.doc_to_asteroid(doc)

    try:
        result = run_mission(
            asteroid=asteroid,
            seed=seed,
            reusable=reusable,
            refinery=refinery,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")

    return result.to_dict()


@app.get("/api/stats")
async def stats():
    """Get database statistics."""
    db = get_db()
    try:
        total_asteroids = db.asteroids_collection.estimated_document_count()
        neo_count = db.asteroids_collection.count_documents({"neo": True})
        hazardous_count = db.asteroids_collection.count_documents({"hazard": True})
        m_class = db.asteroids_collection.count_documents({"class": "M"})
        c_class = db.asteroids_collection.count_documents({"class": "C"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"MongoDB query failed: {e}")

    return {
        "total_asteroids": total_asteroids,
        "neos": neo_count,
        "hazardous": hazardous_count,
        "class_m": m_class,
        "class_c": c_class,
    }


# ─── Pydantic models ──────────────────────────────────────────────────────

class BuildShipRequest(BaseModel):
    name: str
    class_: str = "mining_transport"

class UpgradeRequest(BaseModel):
    module_id: str

class LaunchMissionRequest(BaseModel):
    ship_id: str
    spkid: int
    mission_type: str = "mining_fast_roi"
    reusable: bool = True
    refinery: bool = False
    seed: Optional[int] = None

class RelaunchShipRequest(BaseModel):
    spkid: Optional[int] = None
    mission_type: str = "mining_fast_roi"
    reusable: bool = True
    refinery: bool = False
    seed: Optional[int] = None


# ─── Engine helper ─────────────────────────────────────────────────────────

def get_engine() -> Engine:
    return Engine(get_db())


# ─── Fleet API ────────────────────────────────────────────────────────────

@app.post("/api/fleet/ships")
def build_ship(req: BuildShipRequest):
    """Build a new ship."""
    if req.class_ not in SHIP_CLASSES:
        raise HTTPException(400, f"Invalid ship class. Must be one of: {', '.join(SHIP_CLASSES)}")
    engine = get_engine()
    ship = engine.build_ship(name=req.name, class_=req.class_)
    return {"ship_id": ship.ship_id, "name": ship.name, "class": ship.class_, "status": ship.status}


@app.get("/api/fleet/ships")
def list_ships(status: Optional[str] = Query(None)):
    """List all ships."""
    db = get_db()
    docs = db.list_ships(status=status)
    ships = [db.doc_to_ship(d).to_dict() for d in docs]
    return {"count": len(ships), "ships": _serialize_doc(ships)}


@app.get("/api/fleet/ships/{ship_id}")
def get_ship(ship_id: str):
    """Get ship detail with event history."""
    db = get_db()
    doc = db.get_ship(ship_id)
    if not doc:
        raise HTTPException(404, f"Ship {ship_id} not found")
    ship = db.doc_to_ship(doc)
    result = ship.to_dict()
    events = db.get_ship_events(ship_id, limit=20)
    result["events"] = _serialize_doc(events)
    return _serialize_doc(result)


@app.post("/api/fleet/ships/{ship_id}/upgrade")
def upgrade_ship(ship_id: str, req: UpgradeRequest):
    """Install an upgrade module on a ship."""
    if req.module_id not in UPGRADE_MODULES:
        raise HTTPException(400, f"Unknown module. Options: {', '.join(UPGRADE_MODULES.keys())}")
    engine = get_engine()
    success, msg = engine.install_upgrade(ship_id, req.module_id)
    if not success:
        raise HTTPException(400, msg)
    return {"success": True, "message": msg}


@app.post("/api/ships/{ship_id}/relaunch")
def relaunch_ship(ship_id: str, req: RelaunchShipRequest):
    """Relaunch a ship on a new mission — auto-selects asteroid if spkid not provided."""
    if req.mission_type not in MISSION_TYPES:
        raise HTTPException(400, f"Invalid mission type. Must be one of: {', '.join(MISSION_TYPES)}")
    engine = get_engine()
    try:
        mission = engine.relaunch_ship(
            ship_id=ship_id,
            spkid=req.spkid,
            mission_type=req.mission_type,
            reusable=req.reusable,
            refinery=req.refinery,
            seed=req.seed,
        )
        return _serialize_doc(mission)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Relaunch failed: {e}")


# ─── Persistent Missions API ──────────────────────────────────────────────

@app.post("/api/missions")
def launch_mission(req: LaunchMissionRequest):
    """Launch a persistent mission (creates ship + mission docs, persists everything)."""
    if req.mission_type not in MISSION_TYPES:
        raise HTTPException(400, f"Invalid mission type. Must be one of: {', '.join(MISSION_TYPES)}")

    engine = get_engine()
    try:
        mission = engine.launch_mission(
            ship_id=req.ship_id,
            spkid=req.spkid,
            mission_type=req.mission_type,
            reusable=req.reusable,
            refinery=req.refinery,
            seed=req.seed,
        )
        return _serialize_doc(mission)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Mission launch failed: {e}")


@app.get("/api/missions")
def list_missions(status: Optional[str] = Query(None)):
    """List all persistent missions."""
    db = get_db()
    docs = db.list_missions(status=status)
    return {"count": len(docs), "missions": _serialize_doc(docs)}


@app.get("/api/missions/{mission_id}")
def get_mission(mission_id: str):
    """Get mission detail with event log."""
    engine = get_engine()
    result = engine.get_mission(mission_id)
    if not result:
        raise HTTPException(404, f"Mission {mission_id} not found")
    return _serialize_doc(result)


@app.get("/api/missions/{mission_id}/ticks")
def get_mission_ticks(
    mission_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Get paginated daily ticks for a mission."""
    db = get_db()
    result = db.get_mission_ticks(mission_id, page=page, per_page=per_page)
    result["ticks"] = _serialize_doc(result["ticks"])
    return result


# ─── Market API ────────────────────────────────────────────────────────────

@app.get("/api/market")
def get_market():
    """Get current market state (prices and elasticity)."""
    db = get_db()
    persisted = db.get_market_state()
    # Merge persisted prices into defaults
    prices = dict(ELEMENT_PRICES)
    prices.update(persisted)
    return {
        "prices": prices,
        "elements": [
            {"name": k, "price_per_kg": v}
            for k, v in sorted(prices.items(), key=lambda x: -x[1])
        ],
    }
