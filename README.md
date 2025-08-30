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

## Testing the API

Run the comprehensive test suite to validate all endpoints:

```sh
python test_api.py
```

This will test:
- ✅ Health check and API connectivity
- ✅ Asteroid data retrieval
- ✅ Multi-ship creation and management
- ✅ Mission planning and execution
- ✅ Fleet status and coordination
- ✅ Mission progress tracking

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


