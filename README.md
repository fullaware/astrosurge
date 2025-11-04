# AstroSurge

## Overview

**AstroSurge** is a simulation designed to manage asteroid mining operations, resource extraction, and economic decision-making. The project allows users to plan missions, mine asteroids, manage ships, and sell their valuable resources. It combines elements of resource management, logistics, and strategy to create a dynamic and engaging experience.

## Current Status ✅ **December 2024**

AstroSurge now features a **complete FastAPI backend** with MongoDB integration and a **comprehensive Control Center** for fleet management. The system supports multiple ships, real-time mission tracking, and estimated payoff calculations.

### 🚀 **New Features**
- **FastAPI Backend**: Complete REST API with MongoDB integration
- **Control Center**: Fleet-wide dashboard showing all ships, locations, and missions
- **Multi-ship Operations**: Create and manage multiple mining vessels
- **Real-time Status**: Live updates on ship locations and mission progress
- **Estimated Payoffs**: Calculate potential revenue for active missions
- **Unified Entrypoint**: Single `run.py` script to launch both backend and frontend

## Quick Start

### Single Command Launch

The easiest way to start AstroSurge is using the unified entrypoint:

```bash
python3 run.py
```

This will start both:
- **FastAPI Backend** on `http://localhost:8000` (API endpoints and documentation)
- **Flask Web UI** on `http://localhost:5000` (Dashboard and visualization)

### Environment Variables

Create a `.env` file in the project root with:

```bash
MONGODB_URI=mongodb://localhost:27017/asteroids
API_PORT=8000
WEB_PORT=5000
```

### Manual Service Launch

If you prefer to run services separately:

**Backend API:**
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

**Frontend Dashboard:**
```bash
python3 webapp.py
```

## Purpose

The primary goal of the AstroSurge is to simulate the complexities of asteroid mining and resource management in a futuristic setting. It aims to:
- **Explore the potential of asteroid mining** as a sustainable source of rare and valuable materials.
- **Simulate economic and logistical challenges** involved in space exploration and resource extraction.
- **Provide a framework for decision-making** in resource allocation, mission planning, and ship management.

## Key Features

1. **Asteroid Mining:**
   - Locate and assess the value of asteroids based on their composition and proximity to Earth.
   - Mine valuable elements like gold, platinum, and rare earth metals.
   - Manage mined resources and update asteroid data dynamically.

2. **Ship Management:**
   - Build and manage a fleet of mining ships with customizable attributes like capacity, mining power, and hull integrity.
   - Track ship locations, missions, and cargo.
   - Repair and maintain ships to ensure operational efficiency.

3. **Mission Planning:**
   - Plan and execute mining missions to maximize resource extraction and minimize costs.
   - Track mission progress, including projected and actual costs, durations, and outcomes.
   - Handle unexpected challenges like ship damage or resource depletion.

4. **Resource Trading and Distribution:**
   - Sell mined resources to generate revenue.
   - Distribute resources for industrial, medical, and other uses.
   - Update user accounts with the value of mined resources and manage economic growth.

5. **Fleet Control Center:**
   - **Comprehensive fleet overview** with all ships and their current status
   - **Real-time location tracking** showing ships on Earth, in space, or at asteroids
   - **Mission monitoring** with progress updates and estimated completion times
   - **Estimated payoff calculations** for active missions based on cargo and costs
   - **Ship selection and detailed inspection** for operational management

## Architecture

### Backend (FastAPI)
- **API Server**: Running on http://localhost:8000
- **Database**: MongoDB with 958K+ asteroid records
- **Endpoints**: Complete REST API for ships, missions, asteroids, and fleet management

### Frontend (Next.js)
- **Web Interface**: Running on http://localhost:3000
- **Components**: Fleet status, mission planning, turn management, mission history
- **NEW**: Control Center for comprehensive fleet management

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB running locally or accessible via connection string

### 1. Clone the repository:
```sh
git clone https://github.com/fullaware/astrosurge.git
cd astrosurge
```

### 2. Install Python dependencies:
```sh
python3.13 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
```

### 3. Install Frontend dependencies:
```sh
cd frontend
npm install
cd ..
```

### 4. Start the FastAPI backend:
```sh
# Option 1: Use the startup script
chmod +x start.sh
./start.sh

# Option 2: Manual startup
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start the frontend (in a new terminal):
```sh
cd frontend
npm run dev
```

### 6. Access the application:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Docker Compose Deployment

For containerized deployment, use Docker Compose:

### 1. Configure environment:
```sh
cp env.example .env
# Edit .env with your MongoDB URI
```

### 2. Deploy with Docker Compose:
```sh
# Start both services (API and WebApp)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Access services:
- **API Backend**: http://localhost:8000
  - API Docs: http://localhost:8000/docs
  - Health Check: http://localhost:8000/health
- **Web Dashboard**: http://localhost:5000
  - Dashboard: http://localhost:5000/

### 4. Build individual services:
```sh
# Build API only
docker-compose build api

# Build WebApp only
docker-compose build webapp

# Rebuild without cache
docker-compose build --no-cache
```

### 4. Service management:
```sh
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Check status
docker-compose ps
```

## Testing

### Running Tests

The project includes comprehensive test coverage:

```sh
# Run all tests with coverage
./run_tests.sh

# Run only unit tests
./run_tests.sh --unit-only

# Run without performance tests
./run_tests.sh --no-performance

# Run specific test file
pytest tests/test_api_endpoints.py -v

# Run with coverage report
pytest tests/ --cov=src --cov=api --cov-report=html
```

### Test Coverage

The test suite includes:
- ✅ **Unit Tests**: All business logic services (13 test files)
- ✅ **API Endpoint Tests**: Complete FastAPI endpoint coverage
- ✅ **Integration Tests**: End-to-end workflow testing
- ✅ **Performance Tests**: Response time and load testing

### Test Structure

```
tests/
├── test_api_endpoints.py      # API endpoint tests
├── test_integration.py        # Integration tests
├── test_performance.py        # Performance tests
├── test_commodity_pricing*.py # Pricing service tests
├── test_mission_economics*.py # Economics service tests
├── test_orbital_mechanics.py  # Orbital mechanics tests
├── test_mining_operations.py  # Mining operations tests
└── ...                        # Other service tests
```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /api/asteroids` - List asteroids with filtering
- `GET /api/ships/user/{user_id}` - Get user's ships
- `POST /api/ships` - Create new ship
- `GET /api/missions/user/{user_id}` - Get user's missions
- `POST /api/missions` - Create new mission
- `GET /api/fleet/status/{user_id}` - Get comprehensive fleet status

### Fleet Management
- **Multi-ship operations**: Create and manage multiple vessels
- **Mission coordination**: Plan and execute missions across the fleet
- **Real-time status**: Live updates on ship locations and mission progress
- **Performance tracking**: Monitor fleet efficiency and profitability

## Control Center Features

The new Control Center provides a **comprehensive fleet management dashboard**:

- **🚀 Fleet Overview**: Total ships, active ships, ships in space, total cargo capacity
- **📊 Ship Grid**: Visual representation of all ships with status indicators
- **📍 Location Tracking**: Real-time ship positions (Earth, En Route, Asteroid)
- **🎯 Mission Info**: Target asteroids, duration, budget, and estimated payoffs
- **💰 Payoff Calculations**: Real-time revenue estimates for active missions
- **📦 Cargo Status**: Current cargo contents and mass for each ship
- **🔍 Ship Details**: Detailed inspection and technical specifications

## Database Schema

The system uses a **validated MongoDB schema** with:

- **958K+ asteroid records** with SPK-ID, NEO classification, and element composition
- **119 chemical elements** with properties and asteroid class distributions
- **Comprehensive mission tracking** with 41 fields for detailed analysis
- **Ship management** with status, location, and cargo tracking
- **User and company management** for multi-user support

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to suggest improvements.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

Ethical AI use provided via feedback score and comment. [3 Laws of Kindness](https://www.fullaware.com/posts/aigoldenrule/)


