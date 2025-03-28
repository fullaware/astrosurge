# Progress Checklist

## Phase 1: Functional API
### Project Setup
- [x] Create folder structure (`api/`, `services/`, `config/`, `docs/`).
- [x] Add `main.py` as the FastAPI app entry point.
- [x] Configure `.env` for environment variables (`MONGODB_URI`, etc.).
- [x] Add `logging_config.py` for logging setup.
- [x] Add `mongodb_config.py` for MongoDB configuration.

### API Routes
- [x] `asteroid_routes.py`: Endpoints for asteroid-related operations.
- [x] `ship_routes.py`: Endpoints for ship-related operations.
- [x] `mission_routes.py`: Endpoints for mission-related operations.
- [ ] `simulation_routes.py`: Endpoints for running mining simulations.
- [x] `user_routes.py`: Endpoints for user authentication and updates.
- [x] `element_routes.py`: Endpoints for element selection and selling.

### Services
- [x] `manage_asteroids.py`: Logic for asteroid-related operations.
- [x] `manage_ships.py`: Logic for ship-related operations.
- [x] `manage_mission.py`: Logic for mission-related operations.
- [x] `manage_elements.py`: Logic for element-related operations.
- [x] `manage_users.py`: Logic for user authentication and updates.
- [x] `mine_asteroid.py`: Logic for simulating asteroid mining.

### Documentation
- [x] `project_plan.md`: High-level project plan.
- [x] `progress_checklist.md`: Checklist for tracking progress.
- [ ] Add API documentation:
  - [ ] Document all API endpoints with request/response examples.
  - [ ] Include Swagger UI instructions.
- [ ] Add deployment documentation:
  - [ ] Document environment setup.
  - [ ] Document deployment steps.

### Features
- [x] Mining simulation with hourly granularity.
- [x] Mission planning with risk/reward balancing.
- [x] Funding and investment system.
- [ ] Leaderboard for ranking companies:
  - [ ] Design leaderboard schema in MongoDB.
  - [ ] Create API endpoint to retrieve leaderboard data.
  - [ ] Implement sorting and ranking logic.

### Testing
- [ ] Test all API endpoints using Swagger UI or Postman.
- [ ] Test MongoDB queries for all services.
- [ ] Verify logging to stdout and file.

### Deployment
- [ ] Add deployment instructions to `docs/`.
- [ ] Ensure `.env` is properly configured for production.
- [ ] Test deployment on a staging server.

---

## Phase 2: AI Integration
### Features
- [ ] AI decision-making for mission planning and mining:
  - [ ] Log AI decisions during simulations.
  - [ ] Create API endpoint to retrieve decision logs.
  - [ ] Display explanations in the user interface.
- [ ] Market trends for strategy adjustments:
  - [ ] Design schema for market trends in MongoDB.
  - [ ] Create API endpoint to retrieve market trends.
  - [ ] Integrate trends into mission planning and element selling.

