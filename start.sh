#!/bin/bash

# Set environment variables
export MONGODB_URI="mongodb://localhost:27017/asteroids"
export LOG_LEVEL="INFO"
export SIMULATION_SPEED="1.0"
export FRONTEND_PORT="3000"
export API_PORT="8000"

echo "Starting AstroSurge FastAPI server..."
echo "MongoDB URI: $MONGODB_URI"
echo "API Port: $API_PORT"

# Start the FastAPI server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload