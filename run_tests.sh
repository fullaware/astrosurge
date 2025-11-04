#!/bin/bash
# Test runner script for AstroSurge

set -e

echo "🧪 AstroSurge Test Suite"
echo "========================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Warning: Virtual environment not detected${NC}"
    echo "   Consider activating your virtual environment first"
    echo ""
fi

# Run tests with coverage
echo "📊 Running tests with coverage..."
echo ""

# Run unit tests
echo "🔬 Unit Tests:"
pytest tests/ -m "not integration and not slow and not performance" -v --tb=short

# Run integration tests (if not skipped)
if [ "$1" != "--unit-only" ]; then
    echo ""
    echo "🔗 Integration Tests:"
    pytest tests/ -m integration -v --tb=short
fi

# Run performance tests (if not skipped)
if [ "$1" != "--unit-only" ] && [ "$1" != "--no-performance" ]; then
    echo ""
    echo "⚡ Performance Tests:"
    pytest tests/ -m performance -v --tb=short
fi

# Generate coverage report
echo ""
echo "📈 Generating coverage report..."
pytest tests/ --cov=src --cov=api --cov=webapp --cov-report=html --cov-report=term-missing --cov-report=term:skip-covered

echo ""
echo -e "${GREEN}✅ Test suite completed!${NC}"
echo ""
echo "📊 Coverage report available at: htmlcov/index.html"
echo ""

