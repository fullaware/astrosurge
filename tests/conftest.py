"""
Pytest configuration and shared fixtures
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set default MongoDB URI for testing
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test_asteroids")


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection"""
    with patch('pymongo.MongoClient') as mock_client:
        mock_db = Mock()
        mock_client.return_value = mock_client
        mock_client.__getitem__.return_value = mock_db
        mock_client.admin.command.return_value = True
        yield mock_db


@pytest.fixture
def mock_database_manager():
    """Mock database manager"""
    mock_db = Mock()
    mock_db.get_users = Mock(return_value=[])
    mock_db.get_ships = Mock(return_value=[])
    mock_db.get_missions = Mock(return_value=[])
    mock_db.get_asteroids = Mock(return_value=[])
    mock_db.get_elements = Mock(return_value=[])
    mock_db.get_config = Mock(return_value={})
    mock_db.get_world_state = Mock(return_value={"current_day": 0, "status": "stopped"})
    return mock_db


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Clean up environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)

