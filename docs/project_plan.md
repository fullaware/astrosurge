# Asteroid Mining Operation Simulator Project Plan

## Vision
Players mine asteroids for profit with AI-driven fleets. Longer missions increase risk—more days in space mean more chances for micrometeorite hits or delays. Target: ~50,000 kg yielding $1.5B+ revenue, set via `config`.

## Folder Structure
- **`models/`**: Pydantic models.
  - `models.py`: `UserModel`, `AsteroidModel`, `ElementModel`, `MissionModel`, `ShipModel`.
- **`amos/`**: Core logic.
  - `mine_asteroid.py`: Mining sim, revenue/profit calc, MongoDB updates.
- **`config/`**: Configuration.
  - `__init__.py`: `from .logging_config import LoggingConfig; from .mongodb_config import MongoDBConfig`.
  - `logging_config.py`: `INFO`-level logging, optional file output (`YYYY-MM-DD_HH-MM-SS-beryl.log`).
  - `mongodb_config.py`: MongoDB client with `MONGODB_URI` from `.env`, database `asteroids`.
- **Root**:
  - `.env`: `MONGODB_URI`.
  - `main.py` (TBD): Simulator entry.

## Features

### AI Management
- AIs manage ships (`ShipModel`), mine asteroids, update `MissionModel.elements`.
- Feedback via `MissionModel.events` (e.g., "Microparticle hit").

### Mining Simulation
- **Logic**: `amos/mine_asteroid.py`.
- **Yield**: `MissionModel.elements`, targets `config.target_yield_kg` (50,000 kg), 600-1,000 kg/hour.
- **Difficulty**: Scales with `total_duration_days`—more event rolls (5% hit chance/day).

### Company Management
- **Model**: `UserModel`.
- **Ranking**: Leaderboard by `MissionModel.profit`.

### Mission Planning
- **Model**: `MissionModel`.
- **Duration**: `travel_days_allocated + mining_days_allocated + events.delay_days`.
- **Events**: Stored in `MissionModel.events`.

### Funding
- **Logic**: `mine_asteroid.py` updates `cost`, `revenue`, `profit`, `penalties`.

## Data Model
- **Users**: `UserModel` (as per your schema).
- **Asteroids**: `AsteroidModel` (as per your schema).
- **Missions**: `MissionModel` (updated to match your schema).
- **Config**: Simplified:
  - `id: str = Field(alias="_id")`
  - `name: str`
  - `variables: dict`
  - `updated_at: datetime`

## Tasks
1. **Verify `models/models.py`**:
   - Ensure `MissionModel` aligns with MongoDB schema.
2. **Update `amos/mine_asteroid.py`**:
   - Use `MongoDBConfig.get_database()`, `LoggingConfig.setup_logging()`.
   - Match `MissionModel` fields (e.g., `travel_days_allocated`).
3. **Test**:
   - Confirm 50,000 kg yields ~$1.5B with your MongoDB (`asteroids` database).
4. **Next**:
   - Build `main.py`.
   - Add FastAPI endpoints (e.g., `/missions/run`).

## Config Details
- **`config/logging_config.py`**: `LoggingConfig.setup_logging(log_to_file=False)`—console logs, optional file.
- **`config/mongodb_config.py`**: `MongoDBConfig.get_database()`—connects to `asteroids` database via `.env`.

## Notes
- Database: `asteroids` (not `asteroid_mining` as I assumed—adjusted below).