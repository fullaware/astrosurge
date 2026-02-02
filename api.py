#!/usr/bin/env python3
"""
AstroSurge Walkthrough API

Minimal FastAPI application that serves walkthrough and protocol feedback data.
"""

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient


app = FastAPI(
    title="AstroSurge Walkthrough API",
    description="Minimal API for the simulation walkthrough experience",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _get_state_collection():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None
    client = MongoClient(uri)
    db_name = os.getenv("MONGODB_DB", "astrosurge")
    return client[db_name]["walkthrough_state"]


def _load_persisted_state():
    collection = _get_state_collection()
    if not collection:
        return {}
    doc = collection.find_one({"_id": "default"}) or {}
    return {
        "current_step_id": doc.get("current_step_id"),
        "current_step_index": doc.get("current_step_index", 0),
        "choices": doc.get("choices", {}),
        "ai_branch_triggered": doc.get("ai_branch_triggered", False),
    }


def _save_persisted_state(payload):
    collection = _get_state_collection()
    if not collection:
        return
    update = {
        "current_step_id": payload.get("current_step_id"),
        "current_step_index": payload.get("current_step_index", 0),
        "choices": payload.get("choices", {}),
        "ai_branch_triggered": payload.get("ai_branch_triggered", False),
        "updated_at": datetime.now(timezone.utc),
    }
    collection.update_one({"_id": "default"}, {"$set": update}, upsert=True)


def _build_walkthrough_data():
    persisted = _load_persisted_state()
    return {
        "current_step_index": persisted.get("current_step_index", 0),
        "current_step_id": persisted.get("current_step_id"),
        "choices": persisted.get("choices", {}),
        "payload_target_kg": 50_000,
        "loop_funding_note": "Each 50,000 kg payload return funds the next mission.",
        "steps": [
            {
                "id": "funding_decision",
                "title": "Secure Launch Funding",
                "summary": "Convince backers with a clear first-return narrative.",
                "decision_focus": "Show how the first payload closes the financing loop.",
                "protocol_note": "Investors are betting on a single, proof-of-return mission.",
                "milestone": False,
                "next": "mission_loop",
                "choices": [
                    {
                        "id": "conservative_funding",
                        "label": "Conservative budget, longer runway",
                        "outcome": "Lower risk, slower cadence. Credibility rises with investors."
                    },
                    {
                        "id": "aggressive_funding",
                        "label": "Aggressive budget, faster launch",
                        "outcome": "Higher velocity, increased risk. Pressure builds on first return."
                    }
                ],
                "key_points": [
                    "Mission budget vs. projected revenue",
                    "Risk mitigation and readiness",
                    "Timeline to first 50,000 kg return",
                ],
                "cta": "Review financing assumptions",
            },
            {
                "id": "mission_loop",
                "title": "Run the 50,000 kg Loop",
                "summary": "Launch, mine, return, sell, reinvest.",
                "decision_focus": "Hit the payload target to fund the next mission.",
                "protocol_note": "The first successful return unlocks compounding missions.",
                "milestone": False,
                "next": "commodity_reality",
                "choices": [
                    {
                        "id": "tight_cycle",
                        "label": "Tight cycle, prioritize speed",
                        "outcome": "Faster loop completion, more wear and hazard exposure."
                    },
                    {
                        "id": "balanced_cycle",
                        "label": "Balanced cycle, prioritize safety",
                        "outcome": "Steadier output with fewer disruptions and repair costs."
                    }
                ],
                "key_points": [
                    "Launch and transit windows",
                    "Mining and gangue separation efficiency",
                    "Earth re-entry and payload sale",
                ],
                "cta": "Validate the payload plan",
            },
            {
                "id": "commodity_reality",
                "title": "Commodity Market Reality",
                "summary": "Earth markets saturate fast; prices react.",
                "decision_focus": "Throttle sales to avoid price shocks.",
                "protocol_note": "Early profits draw scrutiny as supply shocks ripple globally.",
                "milestone": False,
                "next": "space_manufacturing",
                "choices": [
                    {
                        "id": "throttle_sales",
                        "label": "Throttle sales, stabilize prices",
                        "outcome": "Markets stay calmer; revenue grows more steadily."
                    },
                    {
                        "id": "flood_market",
                        "label": "Flood market for cash",
                        "outcome": "Short-term gains, long-term price collapse risk."
                    }
                ],
                "key_points": [
                    "Commodity price volatility",
                    "Flooding risk and political blowback",
                    "Shift value to in-orbit uses",
                ],
                "cta": "Set sale pacing policy",
            },
            {
                "id": "space_manufacturing",
                "title": "Pivot to Space Manufacturing",
                "summary": "The real margin is in space-built goods.",
                "decision_focus": "Allocate revenue to orbital factories.",
                "protocol_note": "Infrastructure turns raw payloads into sustained market power.",
                "milestone": False,
                "next": "civilization_metrics",
                "choices": [
                    {
                        "id": "factory_priority",
                        "label": "Prioritize orbital factories",
                        "outcome": "Higher margins in orbit; Earth dependence drops faster."
                    },
                    {
                        "id": "mixed_investment",
                        "label": "Split investment Earth/space",
                        "outcome": "Balanced growth; slower shift to off-Earth independence."
                    }
                ],
                "key_points": [
                    "Higher margins in orbit",
                    "Infrastructure compounding effects",
                    "Long-term market independence",
                ],
                "cta": "Allocate manufacturing budget",
            },
            {
                "id": "civilization_metrics",
                "title": "Civilization Metrics",
                "summary": "Shift from cash to advancement indicators.",
                "decision_focus": "Choose which metric drives priority decisions.",
                "protocol_note": "The goal shifts from rich to advanced.",
                "milestone": False,
                "next": "ai_colonies",
                "choices": [
                    {
                        "id": "tech_index_focus",
                        "label": "Prioritize Tech Index",
                        "outcome": "Faster innovation; higher complexity and oversight needs."
                    },
                    {
                        "id": "resource_independence_focus",
                        "label": "Prioritize Resource Independence",
                        "outcome": "Earth dependence drops; political pressure eases sooner."
                    }
                ],
                "key_points": [
                    "Tech Index, Energy per Capita, Population in Space",
                    "Resource Independence, Cultural Influence, AI Sentience",
                    "Metrics replace money as the core score",
                ],
                "cta": "Set metric priority",
            },
            {
                "id": "ai_colonies",
                "title": "Autonomous AI Colonies",
                "summary": "AI runs operations; you steer ethics.",
                "decision_focus": "Set the ethical directive for AI oversight.",
                "protocol_note": "The AI begins to ask humanity-level questions.",
                "milestone": False,
                "next": "earth_transition",
                "choices": [
                    {
                        "id": "ethics_sustainability",
                        "label": "Prioritize sustainability",
                        "outcome": "Slower expansion; fewer ecological shocks."
                    },
                    {
                        "id": "ethics_welfare",
                        "label": "Maximize human welfare",
                        "outcome": "Earth stability improves; cultural influence grows."
                    },
                    {
                        "id": "ethics_expansion",
                        "label": "Pursue interstellar expansion",
                        "outcome": "Rapid growth; higher governance risk."
                    }
                ],
                "key_points": [
                    "AI manages fleets and allocation",
                    "Ethical directives steer autonomy goals",
                    "Player becomes an overseer",
                ],
                "cta": "Set AI directive",
            },
            {
                "id": "earth_transition",
                "title": "Earth's Great Transition",
                "summary": "Earth reshapes under space abundance.",
                "decision_focus": "Decide whether to rescue or leave Earth behind.",
                "protocol_note": "Earth becomes museum, sanctuary, or prison.",
                "milestone": False,
                "next": "trade_network",
                "choices": [
                    {
                        "id": "help_earth",
                        "label": "Help Earth transition",
                        "outcome": "Stability rises; resource burden slows expansion."
                    },
                    {
                        "id": "focus_space",
                        "label": "Prioritize space colonies",
                        "outcome": "Faster off-Earth growth; Earth instability grows."
                    }
                ],
                "key_points": [
                    "Energy credits replace fossil economies",
                    "Climate collapse or revival events",
                    "Population migration to space",
                ],
                "cta": "Choose Earth policy",
            },
            {
                "id": "trade_network",
                "title": "Interplanetary Trade Network",
                "summary": "Build routes across the solar economy.",
                "decision_focus": "Respond to trade tensions and supply shocks.",
                "protocol_note": "Player becomes a space economist.",
                "milestone": False,
                "next": "project_genesis",
                "choices": [
                    {
                        "id": "open_trade",
                        "label": "Open trade, shared prosperity",
                        "outcome": "Lower conflict; slower independence for colonies."
                    },
                    {
                        "id": "space_autarky",
                        "label": "Space autarky and internal supply chains",
                        "outcome": "Faster independence; Earth relations strain."
                    }
                ],
                "key_points": [
                    "Earth → Moon → Belt → Mars → Jupiter routes",
                    "Supply/demand and political tension",
                    "Energy-backed currency (Sol)",
                ],
                "cta": "Set trade policy",
            },
            {
                "id": "project_genesis",
                "title": "Interstellar Seed Mission",
                "summary": "Launch humanity beyond the Sun.",
                "decision_focus": "Commit to a no-return legacy mission.",
                "protocol_note": "Not a win condition, a legacy.",
                "milestone": False,
                "next": "humanity_logs",
                "choices": [
                    {
                        "id": "launch_genesis",
                        "label": "Launch Project Genesis",
                        "outcome": "Humanity becomes a constellation; Earth mythologizes the mission."
                    },
                    {
                        "id": "delay_genesis",
                        "label": "Delay for further preparation",
                        "outcome": "Improves mission viability; delays legacy impact."
                    }
                ],
                "key_points": [
                    "AI-piloted interstellar ark",
                    "DNA libraries and seed banks",
                    "60-year journey to Proxima b",
                ],
                "cta": "Decide on launch",
            },
            {
                "id": "humanity_logs",
                "title": "Humanity Logs",
                "summary": "Generate narrative based on your choices.",
                "decision_focus": "Shape the cultural memory of your civilization.",
                "protocol_note": "History books unlock from milestones.",
                "milestone": False,
                "next": "legacy_mode",
                "choices": [
                    {
                        "id": "celebrate_earth",
                        "label": "Celebrate Earth's heritage",
                        "outcome": "Cultural influence remains Earth-centric."
                    },
                    {
                        "id": "celebrate_space",
                        "label": "Celebrate space pioneers",
                        "outcome": "A new space-first identity emerges."
                    }
                ],
                "key_points": [
                    "Dynamic lore based on metrics",
                    "Story engine unlocks milestones",
                    "History books become the record",
                ],
                "cta": "Choose narrative framing",
            },
            {
                "id": "legacy_mode",
                "title": "Legacy Mode",
                "summary": "Export your civilization for others.",
                "decision_focus": "Decide how your legacy is shared.",
                "protocol_note": "Your civilization becomes an NPC elsewhere.",
                "milestone": False,
                "next": "bio_evolution",
                "choices": [
                    {
                        "id": "public_legacy",
                        "label": "Public legacy export",
                        "outcome": "Shared universe influence grows."
                    },
                    {
                        "id": "private_legacy",
                        "label": "Private archive only",
                        "outcome": "Legacy preserved but not shared."
                    }
                ],
                "key_points": [
                    "Shared universe progress bar",
                    "Post-mortem report generated",
                    "Legacy export JSON",
                ],
                "cta": "Set legacy policy",
            },
            {
                "id": "bio_evolution",
                "title": "Biological Evolution",
                "summary": "Humanity adapts to space environments.",
                "decision_focus": "Approve or limit genetic adaptation.",
                "protocol_note": "Ethics define what counts as human.",
                "milestone": False,
                "next": "final_review",
                "choices": [
                    {
                        "id": "approve_adaptation",
                        "label": "Approve adaptive traits",
                        "outcome": "Resilience rises; identity questions intensify."
                    },
                    {
                        "id": "limit_adaptation",
                        "label": "Limit modifications",
                        "outcome": "Cultural continuity remains; space survival is harder."
                    }
                ],
                "key_points": [
                    "Low-g adaptations and radiation traits",
                    "Neural augmentation choices",
                    "New species question",
                ],
                "cta": "Approve adaptation policy",
            },
            {
                "id": "final_review",
                "title": "Final Review",
                "summary": "Summarize outcomes and next strategic horizon.",
                "decision_focus": "Lock in the final strategic direction.",
                "protocol_note": "Your civilization’s legacy is sealed.",
                "milestone": True,
                "next": None,
                "choices": [
                    {
                        "id": "continue_simulation",
                        "label": "Continue simulation",
                        "outcome": "Extend the timeline with open-ended progression."
                    },
                    {
                        "id": "export_legacy",
                        "label": "Export legacy report",
                        "outcome": "Generate the final civilization record."
                    }
                ],
                "key_points": [
                    "Civilization metrics stabilized",
                    "Narrative logs complete",
                    "Legacy report ready",
                ],
                "cta": "Finalize trajectory",
            },
        ],
        "ai_branch": {
            "triggered": persisted.get("ai_branch_triggered", False),
            "trigger_reason": "Revenue and mission scale reached the autonomy surge threshold.",
            "event_title": "AI Autonomy Surge",
            "event_message": "Autonomous mission orchestration spikes temporarily. Prepare for human reintegration.",
            "event_recovery_note": "Human governance evolves and reasserts oversight after the surge window.",
        },
    }


def _minimal_overview():
    return {
        "total_missions": 1,
        "active_missions": 1,
        "completed_missions": 0,
        "fleet_size": 1,
        "active_ships": 1,
        "total_revenue": 0,
        "net_profit": 0,
        "success_rate": 0,
        "total_cargo_mined": 0,
        "discovered_asteroids": 0,
        "asteroids_visited": 0,
        "total_raw_material_processed": 0,
        "total_gangue_separated": 0,
        "average_ore_grade": 0,
        "top_mineral": "None",
    }


@app.get("/api/dashboard")
async def get_dashboard():
    """Minimal dashboard payload for walkthrough UI."""
    return {
        "overview": _minimal_overview(),
        "missions": {"missions": []},
        "asteroids": {"asteroids": []},
        "walkthrough": _build_walkthrough_data(),
    }


@app.post("/api/walkthrough/state")
async def save_walkthrough_state(payload: dict = Body(...)):
    """Persist walkthrough state to MongoDB when configured."""
    _save_persisted_state(payload)
    return {"ok": True}


@app.get("/api/civilization/summary")
async def get_civilization_summary():
    """Minimal civilization summary for walkthrough UI."""
    return {
        "metrics": {},
        "metrics_history": [],
        "events": [],
        "logs": [],
        "trade_routes": [],
    }


@app.get("/api/civilization/legacy-export")
async def get_civilization_legacy_export():
    """Export a JSON summary of the civilization state."""
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {},
        "events": [],
        "narrative_logs": [],
        "mission_count": 0,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "version": "1.0.0",
        "service": "walkthrough-api",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
