#!/bin/bash

# AstroSurge Docker Compose Test Script
# This script tests the Docker Compose setup

set -e

echo "🚀 AstroSurge Docker Compose Test Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    cp env.example .env
    print_warning "Please edit .env file with your MongoDB URI before continuing"
    print_warning "Example: MONGODB_URI=mongodb://username:password@host:port/database"
    exit 1
fi

# Check if MONGODB_URI is set
if ! grep -q "MONGODB_URI=" .env || grep -q "MONGODB_URI=mongodb://username:password@host:port/database" .env; then
    print_error "MONGODB_URI not configured in .env file"
    print_warning "Please set your MongoDB connection string in .env file"
    exit 1
fi

print_status "Environment configuration found"

# Test Docker Compose syntax
echo "🔍 Testing Docker Compose syntax..."
if docker-compose config > /dev/null 2>&1; then
    print_status "Docker Compose syntax is valid"
else
    print_error "Docker Compose syntax error"
    docker-compose config
    exit 1
fi

# Build images
echo "🔨 Building Docker images..."
if docker-compose build; then
    print_status "Docker images built successfully"
else
    print_error "Failed to build Docker images"
    exit 1
fi

# Test services startup
echo "🚀 Testing services startup..."
if docker-compose up -d; then
    print_status "Services started successfully"
else
    print_error "Failed to start services"
    docker-compose logs
    exit 1
fi

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check main app
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "Main application is healthy"
else
    print_warning "Main application health check failed"
fi

# Check dashboard
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    print_status "Dashboard API is healthy"
else
    print_warning "Dashboard API health check failed"
fi

# Check nginx
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_status "Nginx proxy is healthy"
else
    print_warning "Nginx proxy health check failed"
fi

# Show service status
echo "📊 Service Status:"
docker-compose ps

# Show logs
echo "📋 Recent logs:"
docker-compose logs --tail=20

# Test cleanup
echo "🧹 Testing cleanup..."
if docker-compose down; then
    print_status "Services stopped successfully"
else
    print_error "Failed to stop services"
    exit 1
fi

print_status "Docker Compose test completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Configure your MongoDB URI in .env file"
echo "2. Run: docker-compose up -d"
echo "3. Access application at: http://localhost:8000"
echo "4. Access dashboard at: http://localhost:5000"
echo "5. Run tests: docker-compose --profile testing up test-runner"




