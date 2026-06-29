---
title: "AstroSurge Handoff — v0.3.0"
description: "Complete project handoff document covering architecture, API, deployment, implemented features, known issues, and next steps"
tags: [astrosurge, handoff, v0.3.0, documentation]
---

# AstroSurge — Project Handoff Document

**Generated:** 2026-06-29  
**Version:** v0.3.0  
**Status:** All core features implemented, ready for game-loop refinement

---

## Project Overview

AstroSurge is an agentic asteroid mining simulation system with a stateful
mission engine, persistent MongoDB backend, and a mobile-responsive dark-theme
web UI. Users manage a fleet of ships, run full mission progressions (Tiers 1-4),
and view day-by-day tick timelines with per-day events.

### Core Concept

```
Build Ship → Launch Mission → Mine Asteroid → Sell Cargo → Upgrade Ship → Repeat (higher tiers)
```

Missions progress through 11 phases (identification → transit → setup → mining →
prep → return → sale → analysis), each generating financial snapshots and events.

---

## Architecture

### Repository Structure (`~/projects/astrosurge`)

```
src/astrosurge/
├── __init__.py
├── config.py          # Settings: MongoDB URI, rates, costs
├── db.py              # MongoDB CRUD — ships, missions, events, ticks, market
├── engine.py          # Stateful mission orchestrator — launch, upgrade, relaunch
├── events.py          # Phase-specific event generators (transit, setup, mining, prep, return)
├── finance.py         # Funding pool + cargo value tracking per day
├── market.py          # Market state + cargo sale pricing
├── mining.py          # Mining operations, site degradation, repositioning
├── mission.py         # Full 11-phase mission runner
├── models.py          # Dataclasses: Ship, Mission, Asteroid, DailyYield, etc.
├── transit.py         # MOID-based transit time calculation
├── asteroid_filter.py # Target selection (Fast ROI criteria)
├── scripts/
│   └── create_indexes.py
└── web/
    └── app.py         # FastAPI: 18+ REST endpoints + HTML serving

webui/
├── static/
│   ├── css/style.css  # Bootstrap dark theme overrides + mobile tab bar
│   └── js/app.js      # SPA: dashboard, fleet, missions, market tabs
└── templates/
    └── index.html     # Single-page app shell + modals
```

### MongoDB Collections

| Database | Collection | Purpose | Doc Count |
|----------|-----------|---------|-----------|
| `asteroids` | `asteroids` | 958k asteroid catalog with elements | 958,000 |
| `astrosurge` | `ships` | Fleet ships with upgrades + retained earnings | ~1 |
| `astrosurge` | `missions` | Mission results with metrics | ~3 |
| `astrosurge` | `ship_events` | Event log for each ship | ~20 |
| `astrosurge` | `mission_ticks` | Day-by-day tick timeline | ~700 |
| `astrosurge` | `market_state` | Current element prices | ~20 |

### Key Data Models

**Ship:**
```python
ship_id, name, class_, status, tier, mission_count, veteran_status
cargo_capacity_kg, propulsion_type, shielding_type, repair_bots_count
current_cargo_kg, retained_earnings, total_upgrade_spend
upgrades: list[UpgradeModule]  # [{module_id, tier, installed_at}]
last_mission_id, created_at
```

**Mission:**
```python
mission_id, ship_id, asteroid_source_id, asteroid_name, spkid
mission_type, tier, status, moid_au
transit_time_days_one_way, round_trip_days
metrics: MissionMetrics  # total_cost, total_revenue, net_profit, roi, yield_kg
phase_results: list[PhaseResult]
auto_upgraded_modules: list[dict]  # modules auto-installed on launch
```

**DailyYield (per mining day):**
```python
day, total_mined_kg, element_breakdown, daily_revenue
events: list[dict]  # 0-3 events with type, description, severity
```

**Tick (per mission day):**
```python
mission_id, day, phase, phase_name, phase_icon
funding_remaining, funding_pool, debt_owed, cargo_value
daily_roi, is_break_even, cumulative_ops
events: list[dict]  # 0-N events from all phases
repositioning: bool, mined_kg, daily_revenue, top_elements
```

---

## Current State

### Deployment

| URL | Port | Access |
|-----|------|--------|
| `asteroids.apps.fullaware.com` | 443 (Traefik) | External via self-signed TLS |
| `http://10.28.28.15:8001` | 8001 (direct) | Internal / testing |
| API health: | `/api/health` | `{"version": "0.3.0"}` |

### Infrastructure

- **Host**: `studio96` (10.28.28.15) — macOS with Docker Desktop
- **Docker**: Containerized with Python 3.12-slim, FastAPI + uvicorn
- **Traefik**: File-based dynamic config at `~/projects/traefik/config/dynamic.yml`
- **TLS**: Self-signed (`tls: {}` without Let's Encrypt)
- **MongoDB**: `mongodb://archimedes:${MONGODB_PASSWORD}@host.docker.internal:27017/?authSource=admin&directConnection=true`
- **Network**: `traefik_traefik-network` (external) for Traefik communication

### Docker Operations

```bash
# On studio96:
cd ~/projects/astrosurge && git pull
D="/Applications/Docker.app/Contents/Resources/bin/docker"
$D build -t astrosurge:latest .
$D stop astrosurge; $D rm astrosurge
$D run -d --name astrosurge --restart unless-stopped \
  -p 8001:8000 --network traefik_traefik-network \
  -e MONGODB_URI="${MONGODB_URI}" \
  -e MONGODB_DATABASE=astrosurge \
  astrosurge:latest
```

**⚠️ Known issue**: `docker-credential-desktop` not in PATH. Fix:
Remove `credsStore` from `~/.docker/config.json` before `$D build`.

### Clean MongoDB Data

```bash
# From studio96:
D="/Applications/Docker.app/Contents/Resources/bin/docker"
$D exec astrosurge python3 -c "
from pymongo import MongoClient
c = MongoClient(os.environ['MONGODB_URI'])
ast = c['astrosurge']
for col in ['ships','missions','ship_events','mission_ticks','market_state']:
    ast[col].delete_many({})
c.close()
"
```

---

## REST API Reference

### Fleet Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/fleet/ships` | Build a new ship `{name, class_}` |
| `GET` | `/api/fleet/ships` | List all ships with stats |
| `GET` | `/api/fleet/ships/{id}` | Ship detail with 20 recent events |
| `POST` | `/api/fleet/ships/{id}/upgrade` | Install upgrade `{module_id}` |
| `POST` | `/api/ships/{id}/relaunch` | Relaunch (auto-select asteroid) |

### Mission Lifecycle

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/missions` | Launch mission `{ship_id, spkid, mission_type}` |
| `GET` | `/api/missions` | List all missions |
| `GET` | `/api/missions/{id}` | Mission detail + events |
| `GET` | `/api/missions/{id}/ticks` | Paginated tick timeline |

### Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/asteroids/candidates` | Filtered asteroid list for target selection |
| `GET` | `/api/asteroids/{spkid}` | Single asteroid detail with elements |
| `GET` | `/api/market` | Current element market prices |
| `GET` | `/api/stats` | Aggregate statistics |
| `GET` | `/api/health` | Health check |

---

## Implemented Features (v0.3.0)

### ✅ Enhanced Event System
- 0-3 events per day across all 11 mission phases
- Phase-specific event pools with weighted probabilities
- Event severity levels: info / warning / critical
- Events displayed with severity icons in tick timeline (ℹ️ ⚠️ 🔴)

### ✅ Site Degradation & Repositioning
- Ore grade degrades by 0.5% per mining day
- Site stability decreases by 2% per mining day
- Repositioning triggers when stability <30% or grade <25% of base
- 2-5 days to reposition (no mining during repositioning)
- Rich ore pockets (8% chance, 2x-3x grade boost)
- Each reposition slightly degrades base ore quality (8% per event)

### ✅ Ship Retained Earnings
- Ship accumulates net profit from missions in `retained_earnings`
- Upgrade costs deducted from retained earnings
- Insufficient funds returns detailed error with shortfall
- Dashboard shows total retained earnings across fleet

### ✅ Auto-Install Upgrades
- Launching a higher-tier mission auto-deducts and installs missing upgrades
- Ships less than 6 months old eligible (but installed modules count)
- Auto-installed modules tracked in `mission.auto_upgraded_modules`
- Insufficient earnings returns descriptive error listing required modules and costs

### ✅ Ship Relaunch
- `POST /api/ships/{id}/relaunch` with optional `spkid`
- Auto-selects asteroid: NEO → Class M → Largest diameter → Skip recent targets
- Relaunch button on completed mission cards in web UI

### ✅ Build Ships from UI
- "＋ Build Ship" button in Fleet tab header
- Bootstrap modal with name + class inputs
- POSTs to existing API endpoint, auto-refreshes fleet

### ✅ Ship Event Timeline
- "Show Events" button on each ship card in Fleet tab
- Fetches 30 most recent events from API
- Event icons: 🏗️ built, 🚀 launched, ⬆️ upgraded, 🤖 auto_upgraded
- ✅ mission_complete, 💰 earnings_updated

### ✅ Cache-Busting
- All static file references use `?v=N` (currently v6)
- Version badge reads from `/api/health` at runtime

---

## Upgrade Modules

| Module ID | Name | Tier | Cost |
|-----------|------|------|------|
| `water_extraction` | Water Extraction + Cryotankage | 2 | $30M |
| `propulsion_manufacturing` | Propulsion Manufacturing Bay | 3 | $50M |
| `advanced_refinement` | Advanced Ore Refinement | 4 | $50M |
| `swarm_ai` | Swarm AI Coordination | 4 | $30M |

### Tier Requirements

| Tier | Required Modules |
|------|-----------------|
| 2 | `water_extraction` |
| 3 | `propulsion_manufacturing` |
| 4 | `advanced_refinement` + `swarm_ai` |

### Mission Type → Tier Mapping

| Mission | Tier | Description |
|---------|------|-------------|
| `mining_fast_roi` | 1 | PGM Strike (M-class) |
| `mining_ice` | 2 | Ice Farming (C-class) |
| `hazard_hunter` | 3 | Hazard Hunter (PHA) |
| `precision_extraction` | 4 | Precision Extraction (M-class high-grade) |

---

## Known Issues & Quirks

1. **`docker-credential-desktop` not in PATH** — Remove `credsStore` from
   `~/.docker/config.json` on studio96 before `docker build`.

2. **Self-signed TLS** — All services at `*.apps.fullaware.com` use `tls: {}`
   without cert resolver. Browsers show warning (acceptable for dev).

3. **Mining yield on transit days was a bug (already fixed)** — The
   `yield_by_day` mapping in `engine.py` `_build_ticks()` must offset mining
   days by `transit_ow + setup_d` to avoid mining data leaking into transit ticks.

4. **Repositioning resets site stability to 1.0** — Each reset slightly degrades
   base ore grade (multiply by `max(0.5, 1.0 - total_repositions * 0.08)`).

5. **Database cleanup is manual** — No API endpoint to delete missions/ships.
   Must use `pymongo` or `mongosh` via Docker exec.

6. **Version badge** — The HTML footer has a hardcoded `v0.3.0` but the
   `init()` JS function reads from `/api/health` at runtime (overrides badge).

---

## Tested Progression (Example)

| Mission | Type | Tier | Profit | Upgrades Auto-Installed |
|---------|------|------|--------|------------------------|
| MISSION-001 | `mining_fast_roi` | 1 | $1,357,972,925 | — |
| MISSION-002 | `hazard_hunter` | 3 | $1,358,057,032 | Propulsion Manufacturing Bay ($50M) |
| MISSION-003 | `mining_fast_roi` | 3 | $1,319,773,821 | — |

Final ship state: Tier 3, $3.95B retained earnings, $80M upgrade spend,
2 upgrades, 3 missions, 20 events, 691 ticks across missions.

---

## Development Workflow

```bash
# Local dev (macOS):
cd ~/projects/astrosurge
source venv/bin/activate
cd src/astrosurge/web
uvicorn astrosurge.web.app:app --reload --port 8000

# Build + deploy (studio96):
ssh fullaware@10.28.28.15
cd ~/projects/astrosurge && git pull
D="/Applications/Docker.app/Contents/Resources/bin/docker"
$D build -t astrosurge:latest .
$D stop astrosurge; $D rm astrosurge
$D run -d --name astrosurge --restart unless-stopped \
  -p 8001:8000 --network traefik_traefik-network \
  -e MONGODB_URI="${MONGODB_URI}" \
  -e MONGODB_DATABASE=astrosurge \
  astrosurge:latest

# After deploying UI changes, bump cache bust in index.html:
# sed -i '' 's/v=N/v=N+1/' webui/templates/index.html
```

---

## Next Steps (Priority Order)

### 1. Profit/Loss Tracking Per Ship (High)
- Show `retained_earnings` and `total_upgrade_spend` vs `total_cargo_value_sold`
- Net profitability dashboard per ship

### 2. Ship Status / Health / Damage System (Medium)
- Track ship hull integrity, component wear
- Repair costs deducted from retained earnings
- Damage events during transit (solar flares, debris)

### 3. Multiple Ships Simultaneously (Medium)
- Multiple ships can be built (already supported)
- Show active missions alongside in-port ships
- Fleet dashboard with per-ship profit charts

### 4. Mission Abort / Emergency Return (Medium)
- API endpoint to abort active mission
- Loss of cargo or partial recovery
- Record as "abandoned" mission status

### 5. Market Price Volatility (Low)
- Random price fluctuations between missions
- Market timing strategy (sell when prices are high)
- Historical price chart

### 6. Visual Upgrades (Low)
- Ship status icons showing installed upgrades
- Asteroid selection map/diagram
- Mission timeline visualization (Gantt-like)

### 7. Multi-Step Tutorial (Low)
- Guided first mission for new users
- Tooltip explanations for each UI element
- Achievement badges for milestones

---

## Key Files to Reference

| File | Purpose |
|------|---------|
| `src/astrosurge/engine.py` | Mission orchestrator — `launch_mission()`, `install_upgrade()`, `relaunch_ship()` |
| `src/astrosurge/mission.py` | 11-phase mission runner — `run_mission()` |
| `src/astrosurge/mining.py` | Mining ops with site degradation + repositioning |
| `src/astrosurge/events.py` | Event generators for all phases |
| `src/astrosurge/models.py` | All dataclasses + upgrade definitions |
| `src/astrosurge/db.py` | MongoDB CRUD operations |
| `src/astrosurge/web/app.py` | FastAPI routes + Pydantic models |
| `webui/static/js/app.js` | SPA frontend logic |
| `webui/templates/index.html` | HTML template + modals |
| `Dockerfile` | Container build instructions |
| `docker-compose.yml` | Docker Compose configuration |
| `pyproject.toml` | Python dependencies |
| `PRD.md` | Full product requirements document |
| `/Users/fullaware/projects/traefik/config/dynamic.yml` | Traefik routing for `asteroids.apps.fullaware.com` |

---

## Credentials (⚠️ EXPOSED — Cannot Rotate)

The following are exposed in this document and in chat history. They must
be rotated if security is a concern:

| Service | Credential | Location |
|---------|-----------|----------|
| MongoDB | `archimedes:${MONGODB_PASSWORD}` | `.env` |
| (List other exposed credentials if applicable) |

---

## Questions for Next Session

1. **Which next step should be tackled first?** Profit tracking, damage system,
   multiple ships, abort, market volatility, tutorials?

2. **Should the upgrade system be extended?** (e.g., propulsion upgrades to
   `ion`/`exotic`, shield upgrades, bot count upgrades)

3. **Production hardening needed?** (Let's Encrypt TLS, auth, rate limiting)

4. **Should we add a database cleanup API?** (DELETE endpoints for ships/missions)

5. **Any UI preferences for the next iteration?** (Charts, maps, animations?)
