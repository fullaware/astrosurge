# AstroSurge Product Requirements Document

> **Version**: 2.0  
> **Status**: Aspirational Design Document  
> **Purpose**: Complete accounting of what the simulator should do before coding begins

---

## Overview

AstroSurge is an agentic asteroid mining simulation system that models the complete lifecycle of asteroid mining operations using MongoDB for data persistence and the Pensive agentic memory system for autonomous decision-making.

### The AstroSurge Strategy

**Fast ROI Priority**: The first mission must maximize return on investment to fund all subsequent operations. The key metric is **MOID** (Minimum Orbit Intersection Distance) — lower MOID = faster transit = better ROI.

**Mission Type Progression**: Mission types are not all available from the start. Each tier unlocks the next through ship upgrades funded by previous mission revenue:

```
Tier 1: Fast ROI (PGM Strike) ──[ship upgrade]──→ Tier 2: Ice Farming
                                                       │
                                               [ship upgrade]
                                                       ↓
                                              Tier 3: Hazard Hunter
                                                       │
                                               [ship upgrade]
                                                       ↓
                                              Tier 4: Precision Extraction
```

| Tier | Mission Type | Target Class | Requirement | Est. Duration | Est. ROI |
|------|-------------|--------------|-------------|---------------|----------|
| **1** | Fast ROI (PGM Strike) | M-class | Base mining ship | ~10-14 months | 5-8x |
| **2** | Ice Farming | C-class | Add water extraction + tankage | ~12-16 months | 3-5x |
| **3** | Hazard Hunter | PHA (any) | Add propulsion manufacturing bay | ~24-48 months | 1-3x + planetary defense value |
| **4** | Precision Extraction | M-class (high-grade) | Add advanced ore refinement + swarm AI | ~8-12 months | 10-20x |

**Mining Target Categories**:

1. **M-Class (PGM/Gold)**: Platinum-group metals, trace gold
   - Fastest ROI: Low MOID (<0.1 AU) metallic asteroids
   - Example targets: Heracles, Zeus, Midas

2. **C-Class (Ice/Water)**: Water ice, volatiles, organics
   - Strategic value: LEO refueling, life support, radiation shielding
   - Example targets: Toutatis, Phaethon, Cuyo

3. **Hazard Hunters**: Potentially Hazardous Asteroids (PHAs)
   - Mission: Intercept, characterize, alter trajectory
   - Propulsion: In-space manufactured nuclear thermal/fusion
   - Goal: Planetary defense + resource access

**Target Selection Criteria** (Fast ROI Focus):
- **MOID < 0.1 AU**: Maximum practical round-trip transit time
- **Diameter > 3km**: Sufficient mass for economic return
- **Class M/C**: High-value metals or volatiles
- **Hazard Status**: PHAs offer strategic mission value (Tier 3+)

---

### Transit Time Model

AstroSurge uses a **MOID-based heuristic** to estimate transit time. Since the asteroid database contains no orbital elements (semi-major axis, eccentricity, inclination), a simplified model is used:

```
transit_days_one_way = 30 + (moid_au × 1000)
round_trip_days = (transit_days_one_way × 2) + 3 (setup) + mining_days + 1 (prep)
```

This produces realistic transit times across all MOID ranges without requiring full orbital mechanics:

| MOID Range | One-Way Transit | Example Target | Transit |
|-----------|-----------------|----------------|---------|
| < 0.01 AU | ~30-40 days | Midas (0.0036) | ~34 days |
| 0.01-0.03 AU | ~40-60 days | Toutatis (0.0066) | ~37 days |
| 0.03-0.06 AU | ~60-90 days | Heracles (0.058) | ~88 days |
| 0.06-0.10 AU | ~90-130 days | Zeus (0.071) | ~101 days |
| > 0.10 AU | > 130 days | Eros (0.149) | ~179 days |

**Note**: Actual transit times vary based on launch window alignment, propulsion type, and trajectory design. This model provides a reasonable approximation for simulation purposes.

---

### The NEO Profile (Ideal Fast ROI Target)

An ideal first-strike target has the following characteristics:
- **Diameter**: > 3km (sufficient mass for economic return)
- **Class**: M-type (platinum-group metals)
- **MOID**: < 0.10 AU (fast transit)
- **Hazard Status**: Non-hazardous preferred (simpler mission profile)
- **Composition**: High PGM content (est. based on M-class spectral signature)
- **Rotation**: Slow enough for stable surface operations

Real targets meeting these criteria: **Heracles** (4.8km, MOID: 0.058 AU, M-class, non-hazardous) and **Zeus** (5.2km, MOID: 0.071 AU, M-class, non-hazardous).

---

## Mission Phases

AstroSurge operates through **11 distinct phases** that model the complete asteroid mining lifecycle. All 11 phases share the same structure regardless of mission type, with mission-type-specific enhancements noted in each phase.

### Phase 1: Asteroid Identification

**Purpose**: Initial analysis and selection of viable mining targets

**Activities**:
- Scan asteroid database for candidate targets
- Filter by mission type requirements (MOID, class, diameter, hazard status)
- Analyze element composition
- Calculate estimated market value
- Estimate transit time and round-trip duration
- Identify risk factors (radiation, thermal cycling, orbital stability)
- Recommend target elements for extraction

**Mission Type Enhancements**:

| Tier | Enhancement |
|------|-------------|
| Fast ROI | Score by `(estimated_value - total_cost) / transit_days` |
| Ice Farming | Filter for C-class, prioritize water ice content |
| Hazard Hunter | Filter for PHAs, score by MOID proximity + diameter |
| Precision Extraction | **Gold Concentration Threshold**: Minimum 500 ppm gold |
| Precision Extraction | **Gravity Well Factor**: Surface gravity ≥ 0.0001 m/s² |
| Precision Extraction | **Market Impact Score**: Predicts global market disruption |
| Precision Extraction | **Drone Deployability**: Time-to-first-return for swarms |

**Output**: Ranked candidate list with analysis summary, recommended elements, transit time, and confidence score.

### Phase 2: Survey Planning

**Purpose**: Plan detailed reconnaissance and hazard mapping

**Activities**:
- Select instrument suite (basic/advanced)
- Configure hazard tolerance levels
- Map hazard zones on asteroid surface
- Estimate recovery rate adjustments
- Analyze element concentrations

**Mission Type Enhancements**:

| Tier | Enhancement |
|------|-------------|
| Fast ROI | Standard survey (surface composition, hazard mapping) |
| Ice Farming | Volatile detection (neutron spectroscopy for H₂O/OH) |
| Hazard Hunter | Rotation stability analysis, trajectory characterization |
| Precision Extraction | Gold deposit mapping (gamma-ray spectroscopy), gravity field mapping |

**Output**: Survey plan, hazard map, instrument configuration.

### Phase 3: Mission Design

**Purpose**: Design spacecraft and transit profile

**Activities**:
- Select propulsion system (nuclear_thermal default, upgradeable to ion or exotic)
- Design mission profile (direct/gravity assist)
- Calculate travel time and launch windows
- Determine delta-v budget
- Calculate fuel savings opportunities

**Mission Type Enhancements**:

| Tier | Enhancement |
|------|-------------|
| Fast ROI | Direct intercept, minimal transit |
| Ice Farming | Higher cargo mass budget (water is heavy) |
| Hazard Hunter | Continuous thrust trajectory, station-keeping |
| Precision Extraction | Swarm deployment, rapid-response insertion |

**Output**: Mission profile, travel duration, propulsion specs.

### Phase 4: Spacecraft Assembly

**Purpose**: Build and configure mining spacecraft

**Activities**:
- Select shielding strategy (passive/active/SITU)
- Design cargo container system
- Calculate mass budget (ship + equipment + shielding)
- Validate mass constraints
- Configure mining equipment

**Ship Upgrade System**: Between missions, ships can be upgraded to unlock new mission types:

| Upgrade | Cost | Unlocks |
|---------|------|---------|
| Water extraction + cryotankage | $X M | Tier 2: Ice Farming |
| Propulsion manufacturing bay | $Y M | Tier 3: Hazard Hunter |
| Advanced ore refinement + swarm AI | $Z M | Tier 4: Precision Extraction |

**Secure Funding**: Before launch, the mission requires capital. The system generates a mission pitch based on:
- Target asteroid (class, diameter, MOID, estimated value)
- Mission type and risk profile
- Ship configuration and veteran status
- Expected ROI and time-to-value
- Previous mission track record (if any)

Funding sources include previous mission profits, investor capital, or corporate backing. The secured amount must cover ship cost + launch costs + daily operations for the entire mission duration. If insufficient funding is secured, the mission cannot proceed. During the mission, the funding balance decreases each day as operational costs are deducted.

**Output**: Spacecraft BOM, mass budget, configuration, funding approval.

### Phase 5: Transit Execution

**Purpose**: Execute outbound journey

**Activities**:
- Monitor transit progress
- Execute course corrections
- Manage AI quorum operations
- Track daily operational costs
- Maintain communication systems

**Duration**: `30 + (moid_au × 1000)` days one-way (see Transit Time Model)

**Output**: Transit log, course correction records.

### Phase 6: Site Establishment

**Purpose**: Land on asteroid and establish autonomous mining base

**Activities**:
- Complete surface survey
- Select optimal mining site
- Deploy mining and anchoring equipment
- Establish base operations
- Configure daily operational systems

**Asteroid Naming**: If the target asteroid has no name (identified by spkid only), the player names it upon first landing. Named asteroids persist in the database for future missions.

**Output**: Landing report, site selection, equipment status.

### Phase 7: Mining Operations

**Purpose**: Execute extraction

**Activities**:
- Daily ore extraction (36,000 kg/day throughput)
- Process ore into extractable elements
- Track cumulative yield and revenue
- Monitor container filling status
- Update daily revenue calculations

**Mission Type Enhancements**:

| Tier | Enhancement |
|------|-------------|
| Fast ROI | PGM-specific separation (M-class), fast-track extraction |
| Ice Farming | Ice/water processing for LEO refueling |
| Hazard Hunter | Continuous thrust propulsion, trajectory alteration |
| Precision Extraction | High-grade ore refinement, autonomous swarm coordination |

**Output**: Daily yield reports, revenue tracking, container status.

### Phase 8: Cargo Sealing

**Purpose**: Seal cargo for return

**Activities**:
- Seal cargo containers
- Final quality verification
- Trajectory correction for return
- Prepare docking systems
- Configure cargo transfer systems

**Output**: Sealing report, departure readiness, cargo certification.

### Phase 9: Return Transit

**Purpose**: Return to Earth

**Activities**:
- Execute return trajectory
- Perform course corrections
- Prepare for re-entry
- Complete cargo transfer preparations
- Monitor return systems

**Duration**: Same as outbound transit (see Transit Time Model)

**Output**: Return transit log, re-entry readiness.

### Phase 10: Market Sale

**Purpose**: Execute market sale

**Activities**:
- Calculate total elements sold
- **Adjust market prices** based on quantity sold (price elasticity model)
- Apply market impact to future missions (prices persist at adjusted levels)
- Account for market impact (price dilution)
- Adjust revenue for market conditions
- Break down revenue by element
- Generate sales report

**Output**: Sales report, revenue breakdown, market impact analysis.

### Phase 11: Financial Analysis

**Purpose**: Evaluate mission

**Activities**:
- Calculate total mission cost (development + operations)
- Calculate total revenue from sales
- Determine net profit/loss
- Calculate ROI
- Estimate break-even price per kg
- Document time-to-value metrics
- Calculate re-tooling cost for next mission tier
- Plan ship upgrade for next mission type

**Output**: Final financial report, ROI, profitability analysis, capital recovery timeline, upgrade budget.

---

## Simulation Flow

The simulation operates in a continuous loop driven by user input and autonomous execution:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MISSION LOOP                                  │
│                                                                         │
│  [USER INPUT]   [FUNDING]   [AUTO-EXECUTE: daily ticks]   [POST-MISSION]│
│  ┌──────────┐  ┌────────┐  ┌──────────────────────────┐  ┌──────────┐  │
│  │Identify  │  │Pitch   │  │ Launch                   │  │ Repair   │  │
│  │ asteroid │  │investors│  │  ↓ (daily progress)      │  │ Upgrade  │  │
│  │Mission   │──→│Secure  │──→│ Travel (course corrections) │──→│ Retrofit │  │
│  │type      │  │capital │  │  ↓                       │  │ Plan next│  │
│  │Ship      │  │        │  │ Site setup               │  │          │  │
│  │config    │  │        │  │  ↓                       │  └────┬─────┘  │
│  └──────────┘  └────────┘  │ Mining (daily yield)     │       │        │
│                              │  ↓                       │       │        │
│                              │ Return (daily transit)   │       │        │
│                              │  ↓                       │       │        │
│                              │ Sell (market adjustment) │       │        │
│                              │  ↓                       │       │        │
│                              │ Financial analysis       │       │        │
│                              └──────────────────────────┘       │        │
│                                                                  │        │
└──────────────────────────────────────────────────────────────────┘────────┘
```

### Stage 1: User Input (Phases 1-4)
The player selects the asteroid target, determines the mission type (based on unlocked tiers), designs the mission profile, and configures the spacecraft. These strategic decisions set all parameters for the mission.

### Stage 2: Secure Funding
Before launch, the mission must be funded. The system generates a mission pitch (target value, risk profile, expected ROI, track record) which determines available capital:
- **Funding source**: Investors, previous mission profits, or corporate backing
- **Funding covers everything**: Ship acquisition cost + launch vehicle + daily operational costs for the entire mission duration
- **Funding is a single pool**: The total amount is secured upfront and drawn down daily
- **Funding risk**: Higher-risk missions (hazardous targets, first-time targets) may receive less funding or demand higher returns
- **First mission**: Always gets baseline funding from investors ($150M expendable or $97M reusable) to bootstrap the operation. This creates the first **debt owed**.
- **Subsequent missions**: Funded by **previous mission profits** first. If profits from the prior mission are sufficient to cover the full funding pool, no investors are needed. If profits fall short, the remainder comes from investors (creating new debt).
- **Self-funding milestone**: After a successful first mission, the goal is to generate enough profit to fund the second mission entirely from retained earnings — breaking the dependency on external capital.
- **Insufficient funding**: If the secured amount (profits + investment) cannot cover estimated ship + launch + daily ops for the full mission duration, the mission cannot proceed

### Stage 3: Auto-Execute with Daily Ticks (Phases 5-11)
The simulation runs the mission autonomously with daily updates the player can observe:

**Each simulated day produces**:
- Transit position and distance remaining (during travel phases)
- Course corrections and fuel consumption (if any)
- Mining yield and element breakdown (during mining phase)
- Random events encountered (micrometeoroids, thermal fluctuations, equipment failures)
- Cumulative revenue and container status
- **Funding remaining** (initial funding minus ship cost, launch cost, and daily ops to date)
- **Daily ops cost deducted** from funding pool
- **Funding burn rate** (how fast the pool is being consumed)
- **Current cargo value** (cargo kg × current market price per kg for each element)
- **Debt owed** (total funding consumed to date — what must be repaid to investors)
- **Daily ROI** = `(current cargo value - debt owed) / debt owed` — updated every day

**Real-time P&L dashboard** (updates every simulated day):

| Metric | What it tells you |
|--------|-------------------|
| Cargo value | What you've recovered so far at today's prices |
| Debt owed | What you've spent that must be repaid |
| Daily ROI | Are you ahead yet? Negative = underwater, 0% = break-even, positive = profit |

The mission reaches **break-even** when `cargo value >= debt owed`. Every day after that is pure profit — assuming you make it home.

**Funding runs out = mission failure**: If the funding pool reaches zero before the ship returns and sells cargo, the mission is declared **failed**. The ship may be stranded, requiring a rescue mission (if crewed) or written off (if autonomous).

**Phases executed autonomously**:
1. **Launch** — Departure from Earth/orbit
2. **Travel** — Transit to asteroid (duration based on MOID)
3. **Site Setup** — Landing and equipment deployment
4. **Mining** — Daily extraction (36,000 kg/day) until container full or time limit
5. **Return** — Transit back to Earth
6. **Sell** — Market sale with price adjustment
7. **Financial Analysis** — Final P&L

Random events (micrometeoroids, equipment failures, thermal fluctuations) occur based on configured risk profiles and are logged each day they happen.

### Strategic Exit: Cancel or Sell a Mission

At any point during Stage 3, the player can choose to exit a mission that is not performing:

**Cancel Mission** — Return to Earth immediately with whatever cargo is onboard:
- Remaining transit time is calculated from current position
- Cargo is sold at market prices upon return (partial payload)
- Revenue goes to repay investors first (any shortfall becomes a loss)
- Ship is recovered but may take damage from early departure
- Mission status: `failed`
- Useful when: Daily ROI is deeply negative and not trending toward break-even

**Sell Mission** — Sell the entire mission (ship, cargo, asteroid rights, debt) to another business:
- Buyer performs a **discounted cash flow analysis** based on: current cargo value, estimated remaining ore, time to completion, operational costs to completion, current market prices
- **Buyer's valuation**: `present_value = (current_cargo_value + expected_future_revenue) - remaining_operational_costs - risk_discount`
  - `expected_future_revenue`: Projected yield from remaining mining × current market price
  - `remaining_operational_costs`: Daily ops from current position through return and sale
  - `risk_discount`: Scales with transit time remaining, hazard status, ship condition, market price volatility
- Buyer assumes all remaining operational costs and debt
- Ship is transferred to the buyer (player loses the ship)
- Mission status: `sold`
- Useful when: You need to cut losses but want some return, or the mission is viable but you lack the capital to finish it

**Example**: A mission 60% through mining with $80M cargo onboard, $120M debt owed, and $40M remaining operational costs. Buyer values the remaining 40% yield at $50M, applies a 25% risk discount ($12.5M), arriving at a payout of: `$80M + $50M - $40M - $12.5M = $77.5M`. After repaying the $120M debt, the player still owes $42.5M — but has avoided $40M in additional operational costs and salvaged the ship's remaining value rather than risking total loss.

### Stage 4: Post-Mission (Repay + Repair + Upgrade + Market Adjustment)
After the mission completes, revenue is distributed in order:
1. **Repay Investors**: The first dollars from cargo sales go to repay the **debt owed** (total funding consumed during the mission). This clears the books from the current mission.
2. **Retained Profit**: Everything remaining after repayment is company profit. This becomes the funding source for the next mission.
3. **Damage Assessment**: Calculate hull integrity, bot damage, system wear from mission events
4. **Repair**: Restore ship to operational condition (cost scales with damage sustained). Repair costs come from retained profit.
5. **Upgrade/Retrofit**: If sufficient retained profit remains, the player can upgrade the ship to unlock the next mission tier (add water extraction, propulsion manufacturing, or advanced refinement).
6. **Market Adjustment**: The sale of elements affects global market prices. If large quantities of a particular element were sold, its price drops for future missions (price elasticity model). This persists across all subsequent missions.
7. **Plan Next**: Player selects next target and mission type. Mission 2 is funded from retained profit first — if profit covers the full funding pool, no investors needed.
8. **Loop**: Return to Stage 1 for the next mission

### Mission Statuses
- **`active`**: Currently progressing through phases
- **`completed`**: All 11 phases finished successfully
- **`failed`**: Terminated before completion
- **`abandoned`**: Terminated due to ship loss (`ship.status == "lost"`) — wait for retrieval or start new ship
- **`sold`**: Mission sold to another business — ship transferred, debt cleared, player received payout

### Mission Output
Each mission produces:
- Daily logs (transit progress, mining yield, events encountered)
- Final financial report (cost, revenue, profit, ROI)
- Ship status post-mission (damage, remaining bots, wear)
- Upgrade recommendations and cost for next tier

---

## Simulation Visualization & Interaction

The simulation runs on a **global clock** that advances all active ships simultaneously. The player observes, pauses, and intervenes.

### Time Controls

| Control | Behavior |
|---------|----------|
| **Play** | Advances all ships by one simulation day every ~1-2 real seconds |
| **Pause** | Freezes all simulation state — ships stop, clock stops, no costs accrue |
| **1x speed** | Default: ~1-2 seconds per day — granular enough to read daily logs |
| **2x speed** | ~0.5-1 second per day — skip routine days |
| **5x speed** | ~0.2 seconds per day — fast-forward through long transits |
| **Max speed** | Runs all remaining days instantly to completion (or next event) |

### Solar System Map (Fleet View)

The primary visualization is an **orbital map** showing the inner solar system:
- **Sun** at center (scale indicator)
- **Earth** at 1 AU (reference point)
- **Orbit traces** for each active asteroid target (derived from MOID)
- **Ship icons** positioned along their transit paths, color-coded by status:
  - 🟢 Green: In transit (outbound)
  - 🟡 Yellow: Mining operations
  - 🔵 Blue: Return transit
  - 🔴 Red: Distressed / funding critical
  - ⚫ Gray: Lost
- **Hover** over any ship: tooltip shows ship name, mission, cargo value, days remaining
- **Click** any ship: opens detail panel

### Fleet Dashboard
A sidebar or top bar showing aggregate fleet metrics:
- Total ships active / in port / lost
- Total cargo value across all active missions
- Total debt owed across all missions
- Fleet-wide daily ops cost burn rate
- Retained earnings (available for next missions)
- Global market price ticker (current prices per element)

### Ship Detail Panel
Opens when clicking a ship on the map or selecting from a list:

**Mission info**: target asteroid, mission type, tier, days elapsed, days remaining

**Real-time P&L** (updates every tick):
- Current cargo value
- Debt owed
- Daily ROI
- Funding remaining
- Break-even ETA (estimated days until cargo value ≥ debt)

**Daily log**: scrollable list of every simulated day for this ship, showing:
- Day number and phase
- Position (AU from Earth)
- Mining yield and top elements (if mining)
- Events encountered
- Funding balance change
- Cargo value change

**Actions** (available when paused):
- Cancel mission
- Sell mission
- Adjust mining priorities
- Set risk tolerance

### Event Notification System
Certain events trigger an **auto-pause** and notification:

| Event | Auto-Pause? | Why |
|-------|-------------|-----|
| Micrometeoroid impact | ✅ | Requires decision: repair or continue? |
| Equipment failure | ✅ | May need reconfiguration |
| Funding critical (<10% remaining) | ✅ | Player must decide: return early or push forward? |
| Break-even milestone | ℹ️ (message only) | Cargo value ≥ debt — informational |
| Mining container full | ℹ️ (message only) | Ready to return — player can trigger return early |
| Ship lost | ✅ | Mission critical event |
| Market price shift >5% in a day | ℹ️ (message only) | Significant volatility |

Auto-paused events present the player with a brief summary of what happened and available options before they can resume the clock.

### Decision Mode (Paused)
When paused, the player can:
- **Review any ship** — inspect cargo, funding, events, trajectory
- **Change mission parameters** — adjust mining rate, risk tolerance, return timing
- **Cancel or sell** any active mission
- **Plan next mission** — select target, configure ship, secure funding
- **Queue upgrades** — set which upgrade to purchase when current mission completes
- **Adjust fleet strategy** — rebalance priorities across multiple ships

Decisions made during pause take effect on the next tick when play resumes.

### Screen Layout (Conceptual)

```
┌─────────────────────────────────────────────────────────────┐
│  [⏸] [▶] [1x] [2x] [5x] [Max]    Day 173/417  │
├──────────────────────────────┬──────────────────────────────┤
│                              │  FLEET DASHBOARD             │
│                              │  ─────────────────           │
│    SOLAR SYSTEM MAP          │  Active ships:  3            │
│                              │  Total cargo:   $142M        │
│    [Sun]──[Earth]            │  Total debt:    $312M        │
│         ● Heracles (🟢)      │  Burn rate:     $135K/day   │
│           ● Zeus (🟡)        │  Retained:      $28M        │
│              ● Cuyo (🔵)     │                              │
│                              │  SHIP DETAIL: Zeus           │
│                              │  ─────────────────           │
│                              │  Cargo: $87M  Debt: $112M    │
│                              │  ROI: -22%  ETA break-even:  │
│                              │  14 days                     │
│                              │  [Cancel] [Sell]             │
├──────────────────────────────┴──────────────────────────────┤
│  EVENT LOG: Day 112 — Zeus: Micrometeoroid impact —        │
│  hull damage 15%. Repair bots deployed.                    │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Adaptation

The same simulation runs on mobile with a reflowed layout designed for small screens and touch interaction.

**Layout strategy**: Single-column, full-width panels stacked vertically. A bottom tab bar switches between views.

```
┌─────────────────────────────────────────┐
│ Time: Day 173/417    [⏸][▶][1x][2x]    │  ← Slim time bar (always visible)
├─────────────────────────────────────────┤
│                                         │
│  ACTIVE SHIPS (3)                       │  ← Default view: ship cards
│  ┌─────────────────────────────────┐    │
│  │ ● Heracles  🟢  Cargo: $55M    │    │
│  │   Debt: $112M  ROI: -51%        │    │
│  │   ETA: 88 days                  │    │
│  ├─────────────────────────────────┤    │
│  │ ● Zeus      🟡  Cargo: $87M    │    │
│  │   Debt: $98M   ROI: -11%        │    │
│  │   ETA: 14 days to break-even    │    │
│  ├─────────────────────────────────┤    │
│  │ ● Cuyo      🔵  Cargo: $12M    │    │
│  │   Debt: $45M   ROI: -73%        │    │
│  │   ETA: 203 days                 │    │
│  └─────────────────────────────────┘    │
│                                         │
├─────────────────────────────────────────┤
│  [🌍 Map] [🚀 Ships] [💰 $] [📋 Log]  │  ← Bottom tab bar
└─────────────────────────────────────────┘
```

**Bottom tab bar** (5 tabs):

| Tab | Shows |
|-----|-------|
| **🌍 Map** | Simplified solar system. Pinch to zoom. Tap a ship to open its bottom sheet. Sun and Earth as fixed references, ship icons positioned proportionally. |
| **🚀 Ships** | Card list of all ships with key metrics (name, status icon, cargo value, debt, ROI, ETA). Tap a card to open the ship detail sheet. |
| **💰 $** | Fleet financial dashboard: retained earnings, total debt, burn rate, global market prices, mission cost breakdown. |
| **📋 Log** | Chronological event log for all ships. Filterable by ship, event type, or date range. Auto-pause events are highlighted. |
| **🔧 Actions** | Pending decisions (auto-paused events), ship upgrades available, new mission planning. Badge count shows number of pending actions. |

**Ship detail bottom sheet** (slides up from bottom when tapping a ship):

```
┌─────────────────────────────────────────┐
│  Zeus  🟡 Mining                      │
│  Heracles · Tier 1 · Day 112/417       │
│─────────────────────────────────────────│
│  CARGO: $87M     DEBT: $98M            │
│  ROI: -11%       BREAK-EVEN: 14 days   │
│  FUNDING LEFT: $38M  BURN: $45K/day    │
│─────────────────────────────────────────│
│  Recent events:                         │
│  Day 112: Micrometeoroid — repaired    │
│  Day 108: Power spike — no damage      │
│  Day 101: Thermal fluctuation — -15%   │
│─────────────────────────────────────────│
│  [Cancel Mission]  [Sell Mission]       │
└─────────────────────────────────────────┘
```

The bottom sheet covers ~60% of the screen, leaving the time bar visible at the top. Swipe down or tap outside to dismiss. All ship detail and decision actions are accessible from this sheet.

**Mobile-specific behaviors**:
- **Portrait only** (landscape shows the desktop layout on tablets)
- **Pull-to-refresh** on Ships and Log tabs to force a tick catch-up
- **Haptic feedback** on auto-pause events
- **Offline resilience**: if connection drops, the last known state is cached and re-synced on reconnect
- **Notification badge** on the Actions tab when decisions are pending
- **Swipe to dismiss** bottom sheets and notification cards

---

## Data Model

### Source Data Collection

Asteroid source data lives in the existing `asteroids.asteroids` collection (958,524 asteroids). Key fields:

| Field | Type | Notes |
|-------|------|-------|
| `_id` | ObjectId | Unique identifier |
| `name` | string | IAU designation (may be null for unnamed asteroids) |
| `pdes` | string | Permanent designation (e.g., "5143" for Heracles) |
| `spkid` | int | SPK ID (e.g., 2005143) |
| `class` | string | Spectral class (M, C, S, etc.) |
| `diameter` | float | Estimated diameter in km |
| `moid` | float | Minimum Orbit Intersection Distance in AU |
| `moid_days` | int | MOID bucket classification (1-80) |
| `neo` | bool | Near-Earth Object flag |
| `hazard` | bool | Potentially Hazardous Asteroid flag |
| `elements` | array | Element composition (name, mass_kg, number) |
| `mass` | Int64 | Estimated mass (⚠️ often hits Int64 max — unreliable) |
| `value` | Int64 | Estimated value (⚠️ often hits Int64 max — unreliable) |

### Asteroid Missions Collection (`astrosurge.missions`)

**Standard Fields**:
- `asteroid_name`: Name of target asteroid (or player-assigned name if unnamed)
- `asteroid_source_id`: ObjectId from `asteroids.asteroids`
- `spkid`: SPK ID of the target asteroid
- `phase`: Current phase number (1-11)
- `phase_name`: Current phase identifier (snake_case)
- `status`: `active | completed | failed | abandoned`
- `mission_type`: `mining_fast_roi | mining_ice | mining_pgm | hazard_hunter | precision_extraction`
- `user_choices`: Player-selected options per phase
- `ai_recommendation`: AI-provided suggestions
- `metrics`: Mission-wide KPIs (cost, yield, ROI, etc.)
- `phase_N_result`: Detailed results from each completed phase

**Ship Reference Fields**:
- `ship_id`: Reference to the mining ship executing the mission
- `ship_name`: Ship designation
- `ship_class`: Ship class
- `ship_status_at_launch`: Status when mission began
- `ship_mission_count_at_launch`: Total missions ship had completed before this mission
- `cargo_capacity_kg`: Ship's cargo capacity
- `propulsion_type`: Ship's propulsion system
- `shielding_type`: Ship's shielding
- `repair_bots_count`: Number of onboard repair drones

**Transit & Navigation Fields**:
- `moid_au`: Target MOID (AU)
- `transit_time_days_one_way`: Calculated one-way transit time
- `round_trip_days`: Estimated total mission duration

**Mission Outcome Fields**:
- `mission_outcome`: `success | partial_success | abandoned | failed | sold | in_progress`
- `disabled_event`: Details of any disabling incident (null if none)
- `lost_event`: Details of ship loss event (null if none)
- `salvage_recovered_kg`: Cargo recovered from lost ships (0 if none)

**Metrics Sub-document**:
```json
{
  "total_cost_usd": 0,
  "total_revenue_usd": 0,
  "net_profit_usd": 0,
  "roi": 0.0,
  "total_yield_kg": 0,
  "time_to_value_days": 0,
  "break_even_price_per_kg": 0.0,
  "daily_throughput_kg": 36000
}
```

**Fast ROI/Progression Enhancements**:
- `ice_mining`: Boolean (true for C-class ice operations)
- `pgm_mining`: Boolean (true for M-class PGM operations)
- `tier`: Integer (1-4, maps to Mission Type Progression)
- `next_tier_plan`: Upgrade path for next mission

**Hazard Hunter Enhancements**:
- `hazard_mission`: Boolean for trajectory modification missions
- `propulsion_type`: `nuclear_thermal | ion | fusion | solar_electric` (exotic upgrades beyond base nuclear_thermal)
- `thrust_newtons`: Continuous thrust capability (N)
- `delta_v_budget`: Total available delta-v (m/s)
- `trajectory_change_mps`: Accumulated velocity change
- `planetary_defense_score`: Mission success metric (0-100)

### Ships Collection (`astrosurge.ships`)

**Status Enum**: `active | in_port | reserve | disabled | lost | retired`

**Core Fields**:
- `ship_id`: Unique identifier (e.g., `SHIP-001`)
- `name`: Ship designation (e.g., "GoldRush-1")
- `class`: `mining_transport | heavy_lifter | ice_hauler | hazard_interceptor`
- `status`: One of the status enum values
- `mission_count`: Total missions completed
- `veteran_status`: Boolean (true if 5+ successful missions)
- `tier`: Current upgrade tier (1-4)
- `last_mission_id`: Reference to most recent mission
- `next_mission_id`: Reference to upcoming mission (if assigned)
- `current_cargo_kg`: Current cargo load (0 when in_port)
- `last_event_id`: Reference to most recent event in ship_events

**Technical Specifications**:
- `cargo_capacity_kg`: Maximum cargo weight
- `propulsion_type`: `nuclear_thermal` (default, upgradable to `ion | solar_electric`)
- `fuel_capacity_kg`: Propellant capacity
- `max_transit_days`: Maximum one-way transit capability
- `shielding_type`: `passive | active | situ`
- `repair_bots_count`: Number of repair drones
- `last_service_date`: Last maintenance timestamp

**Upgrades** (modules installed between missions):
- `upgrades`: Array of installed upgrade modules
  - `module_id`: String — one of `water_extraction`, `propulsion_manufacturing`, `advanced_refinement`, `swarm_ai`
  - `installed_at`: ISO date of installation
  - `tier`: Integer — unlock tier (2-4)

  **Query examples**:
  - All ships with a capability: `{ upgrades: { $elemMatch: { module_id: "water_extraction" } } }`
  - All ships upgraded after a date: `{ upgrades: { $elemMatch: { installed_at: { $gte: ISODate("...") } } } }`

### Ship Events Collection (`astrosurge.ship_events`)

Immutable event log for all ships:

- `_id`: ObjectId
- `ship_id`: Reference to ship
- `event_type`: `build | named | launched | in_flight | locate_and_setup_mining_site | mine_resources | fill_cargo | in_flight_home | land | empty_cargo | repair_or_upgrade | relaunched | disabled | lost | retired | salvage_recovered`
- `timestamp`: UTC datetime
- `mission_id`: Associated mission (if any)
- `location_au`: [x, y, z] AU coordinates at time of event
- `event_data`: Event-specific details (JSON)

**Indexes**: `{ ship_id: 1, timestamp: -1 }` for ship history, `{ timestamp: -1 }` for timeline view.

### Walkthrough State (`astrosurge.walkthrough_state`)

- `current_step_id`: Current phase identifier
- `current_step_index`: Current phase number (1-11)
- `choices`: Global configuration choices
- `ai_branch_triggered`: AI autonomy status
- `mission_type`: `mining_fast_roi | mining_ice | mining_pgm | hazard_hunter | precision_extraction`
- `moid_threshold_au`: Target MOID threshold for target selection

---

## Real Asteroid Target Database

Verified from the `asteroids.asteroids` collection (22,895 NEOs):

### M-Class (PGM/Gold) — Tier 1 Fast ROI

| Target | spkid | Dia (km) | MOID (AU) | Transit* | Hazard | Notes |
|--------|-------|----------|-----------|----------|--------|-------|
| **Heracles** | 2005143 | 4.84 | 0.0584 | ~88 days | ✅ Safe | ⭐ Best first target, M-class, non-hazardous |
| **Zeus** | 2005732 | 5.23 | 0.0707 | ~101 days | ✅ Safe | Larger diameter, slightly longer transit |
| **Midas** | 2001981 | 3.4 | 0.0036 | ~34 days | ⚠️ Hazardous | Fastest ROI, requires deflection capability |
| **276049** | — | 3.5 | 0.0974 | ~127 days | ✅ Safe | **Unnamed** (named on landing), M-class |
| **153249** | — | 3.16 | 0.0573 | ~87 days | ✅ Safe | **Unnamed** (named on landing), M-class |
| **Eros** | 2000433 | 16.84 | 0.1486 | ~179 days | ✅ Safe | Largest M-class NEO but long transit |

### C-Class (Ice/Water) — Tier 2

| Target | spkid | Dia (km) | MOID (AU) | Transit* | Hazard | Notes |
|--------|-------|----------|-----------|----------|--------|-------|
| **Toutatis** | 2004179 | 5.4 | 0.0066 | ~37 days | ⚠️ Hazardous | Closest C-class, fastest transit |
| **Phaethon** | 2003200 | 6.25 | 0.0194 | ~49 days | ⚠️ Hazardous | Largest C-class NEO |
| **Cuyo** | 2003753 | 5.7 | 0.0727 | ~103 days | ✅ Safe | ⭐ Best safe C-class target |
| **Alinda** | 2000887 | 4.2 | 0.0822 | ~112 days | ✅ Safe | Safe, moderate transit |
| **Florence** | 2003122 | 4.9 | 0.0453 | ~75 days | ⚠️ Hazardous | Medium MOID, hazardous |
| **53319** | 53319 | 7.0 | 0.0247 | ~55 days | ⚠️ Hazardous | **Unnamed** (named on landing), largest C-class |
| **Cuno** | 2004183 | 3.65 | 0.0283 | ~58 days | ⚠️ Hazardous | Fast transit, hazardous |

\* Transit = one-way in days using `30 + (moid × 1000)` formula

### Asteroid Naming Convention

Asteroids without a `name` field in the database are identified by `spkid`. Upon first landing (Phase 6), the player assigns a name. Named asteroids are tracked in the mission record and the name persists for future missions.

Examples of unnamed targets that will receive player-assigned names:
- **spkid 53319** → 7.0km C-type PHA (will be named on landing)
- **spkid 276049** → 3.5km M-type (will be named on landing)
- **spkid 153249** → 3.16km M-type (will be named on landing)

---

## Ship Lifecycle Management

Ships are the workhorse of the AstroSurge model. Ships are upgraded between missions to unlock new capabilities and mission types. Some ships accumulate veteran status (5+ successful missions) but eventually must be retired.

### Ship Lifecycle Events

| Event | Description |
|-------|-------------|
| `build` | Initial construction and assembly |
| `named` | Ship receives official designation |
| `launched` | First launch from Earth or orbital facility |
| `in_flight` | Transit to mining target |
| `locate_and_setup_mining_site` | Arrive at asteroid, establish position |
| `mine_resources` | Execute mining operations |
| `fill_cargo` | Load extracted resources into cargo hold |
| `in_flight_home` | Return transit to Earth/Moon |
| `land` | Successful landing and cargo unloading |
| `empty_cargo` | Cargo transferred to storage/facility |
| `repair_or_upgrade` | Maintenance, repairs, or system upgrades |
| `relaunched` | Ship returns to service on new mission |
| `disabled` | Critical failure leading to permanent ship loss |
| `lost` | Ship permanently lost in space |
| `retired` | Permanent decommissioning |

### Ship Status Enum

```
active    — Currently on a mission
in_port   — Docked for repairs/upgrades
reserve   — Available but not assigned
disabled  — Critical failure, ship will be lost
lost      — Permanently lost in space
retired   — Permanently decommissioned
```

### Ship Loss Scenario

**Loss Triggers**:
- Hull integrity below critical threshold (shielding destroyed)
- Propulsion system total failure with no recovery
- Radiation damage exceeding safe operational limits
- Complete system cascade failure

**Loss Workflow**:
1. **Disabling Event**: Ship experiences critical failure
2. **Loss Declaration**: System marks ship as `lost`
3. **Mission Termination**: Mission status set to `abandoned`
4. **Event Log**: Record final location and cause
5. **Cargo Recovery**: Nearby ships may recover remaining cargo
6. **Ship Retired**: Ship removed from active fleet

**Cargo Recovery**:
- Nearby ships (active missions) can divert to recover cargo
- Recovered cargo is added to rescuing ship's cargo hold
- Cargo value is credited to the rescuing ship's next mission
- Recovery operation adds time to rescuing ship's transit
- Only ships with available cargo capacity can recover
- Cargo is marked as `"salvaged"` in the system

### Fleet Status Map

The system provides a real-time view of all ships:

**Fleet Overview**:
- Total ships
- Active ships: currently on missions
- In port: undergoing maintenance
- Lost: permanently decommissioned

**Per-Ship Metrics**:
- `current_cargo_kg`: Current cargo weight
- `cargo_value_usd`: Estimated cargo value at current market prices
- `status`: One of ship status enum
- `location_au`: Current 3D position (AU coordinates)
- `mission_progress`: Percentage complete (0-100%)
- `days_remaining`: Estimated days until return
- `shielding_integrity`: Shielding health (0-100%)

**Map Visualization**:
- Plot ships on 3D solar system map
- Color-coded by status (green=active, yellow=in_port, red=lost)
- Hover tooltip shows ship name, status, cargo value, and destination
- Filter by class, status, or location range

---

### Example: Lost Ship

```json
{
  "ship_id": "SHIP-007",
  "name": "GoldRush-7",
  "class": "heavy_miner",
  "status": "lost",
  "mission_count": 12,
  "veteran_status": true,
  "tier": 2,
  "last_mission_id": "MISSION-245",
  "current_cargo_kg": 12500,
  "event_log": [
    {"event": "build", "timestamp": "2025-03-15T00:00:00Z"},
    {"event": "named", "timestamp": "2025-03-20T00:00:00Z", "name": "GoldRush-7"},
    {"event": "launched", "timestamp": "2025-04-01T00:00:00Z"},
    {"event": "disabled", "timestamp": "2025-06-18T14:30:00Z", "reason": "micrometeoroid_hull_breach", "location_au": [0.45, 0.23, 0.12]},
    {"event": "lost", "timestamp": "2025-06-18T15:45:00Z", "reason": "irrecoverable_hull_failure", "final_location_au": [0.45, 0.23, 0.12]}
  ]
}
```

### Example: Salvage Recovery

```json
{
  "ship_id": "SHIP-012",
  "name": "Rescue-1",
  "class": "mining_transport",
  "status": "active",
  "mission_count": 8,
  "veteran_status": true,
  "tier": 3,
  "current_cargo_kg": 28500,
  "event_log": [
    {"event": "build", "timestamp": "2025-02-10T00:00:00Z"},
    {"event": "launched", "timestamp": "2025-03-01T00:00:00Z"},
    {"event": "salvage_recovered", "timestamp": "2025-06-19T08:30:00Z", "source_ship_id": "SHIP-007", "location_au": [0.45, 0.23, 0.12]}
  ]
}
```

---

## Data Model Relationships

```
asteroids.asteroids (source, 958,524 docs)
        │
        ▼  (selected by player/AI in Phase 1)
astrosurge.missions (one per mission)
        │
        ├──► astrosurge.ships (one per ship, referenced by mission)
        │         │
        │         ▼
        │   astrosurge.ship_events (many per ship, immutable log)
        │
        └──► astrosurge.walkthrough_state (one per session)
```

**Key Relationships**:
- Ships have status that determines location and cargo
- Lost ships have no location (decommissioned)
- Active ships have location and current cargo
- Salvage cargo is tracked on the recovering ship's current cargo
- Missions reference ships and inherit cargo state at launch
- Ships are upgraded between missions (tier increases)
- Mission type determines which asteroid classes are valid targets

---

## Technical Architecture

- **Database**: MongoDB (astrosurge database for missions/ships; asteroids database for source data)
- **Agent System**: Pensive agentic memory
- **API**: REST API at `http://localhost:8000`
- **Storage**: All mission data persisted to MongoDB
- **Transit Model**: `transit_days = 30 + (moid_au × 1000)` with no orbital elements available
- **Security**: All credentials via `.env` file (gitignored) — no hardcoded secrets

---

## Fast ROI Mission Strategy

### Tier 1: First Mission — PGM Strike

| Priority | Target | Class | Dia | MOID | One-Way | Round Trip* | Why |
|----------|--------|-------|-----|------|---------|-------------|-----|
| **1st** | **Heracles** | M | 4.84 km | 0.058 AU | ~88 days | ~319 days | Non-hazardous, M-class, closest safe PGM target |
| **2nd** | **Zeus** | M | 5.23 km | 0.071 AU | ~101 days | ~345 days | Larger diameter, non-hazardous |
| **Alt** | **Midas** | M | 3.4 km | 0.004 AU | ~34 days | ~211 days | Fastest ROI but hazardous (requires deflection) |

\* Round trip includes 3 days setup + 139 days mining + 1 day prep

### Tier 2: Second Mission — Ice Farming Infrastructure

After the PGM Strike funds the ship upgrade (add water extraction + cryotankage):

| Priority | Target | Class | Dia | MOID | One-Way | Round Trip | Why |
|----------|--------|-------|-----|------|---------|-------------|-----|
| **1st** | **Cuyo** | C | 5.7 km | 0.073 AU | ~103 days | ~349 days | Non-hazardous, largest safe C-class |
| **2nd** | **Toutatis** | C | 5.4 km | 0.007 AU | ~37 days | ~217 days | Fastest transit but hazardous |

### Tier 3: Hazard Hunter

After the Ice mission funds propulsion manufacturing upgrade:

| Priority | Target | Class | Dia | MOID | Why |
|----------|--------|-------|-----|------|-----|
| **1st** | **Toutatis** | C | 5.4 km | 0.007 AU | Closest PHA, fastest intercept |
| **2nd** | **Phaethon** | C | 6.25 km | 0.019 AU | Largest hazardous NEO |
| **3rd** | **53319** | C | 7.0 km | 0.025 AU | Unnamed, largest C-class PHA |

### Tier 4: Precision Extraction

After the Hazard Hunter mission funds advanced refinement + swarm AI:

| Priority | Target | Class | Dia | MOID | Why |
|----------|--------|-------|-----|------|-----|
| **1st** | **Heracles** (return) | M | 4.84 km | 0.058 AU | Already characterized, apply Precision Extraction enhancements |
| **2nd** | **276049** | M | 3.5 km | 0.097 AU | Unnamed M-class, fresh target |
| **3rd** | **153249** | M | 3.16 km | 0.057 AU | Unnamed M-class, fast transit |

---

## Hazard Hunter Mission Strategy

**In-Space Propulsion Chain**:
1. **Scout Mission** (3-6 months)
   - Target: Toutatis (closest hazardous, MOID: 0.0066 AU)
   - Mission: Characterize trajectory, composition, rotation
   - Propulsion: Solar-electric (ion) for station-keeping

2. **Propulsion Plant Assembly** (12-18 months)
   - Build in LEO or GEO using in-space manufacturing
   - Nuclear thermal or fusion propulsion
   - Fuel: Water ice from C-class asteroids (refueling stockpile)

3. **Trajectory Alteration** (24-36 months)
   - Deploy multiple propulsion units
   - Continuous thrust: 0.001-0.01 m/s²
   - Deflection time: 2-5 years depending on asteroid mass
   - Goal: Planetary defense + resource access
