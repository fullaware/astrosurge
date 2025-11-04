"""
Test suite for clean database schema implementation service
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bson import ObjectId

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.clean_schema import CleanSchemaService


class TestCleanSchemaService:
    """Test cases for clean schema implementation service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock MongoDB connection to avoid actual database calls
        with patch('src.services.clean_schema.MongoClient') as mock_client:
            mock_db = Mock()
            mock_client.return_value.admin.command.return_value = True
            mock_client.return_value.asteroids = mock_db
            
            # Mock collections
            mock_db.list_collection_names.return_value = ['asteroids', 'elements', 'old_users', 'old_ships']
            mock_db.drop_collection = Mock()
            mock_db.create_collection = Mock()
            
            # Mock collection access for validation and CRUD tests
            mock_collection = Mock()
            mock_collection.list_indexes.return_value = [
                {'name': 'username_1', 'key': {'username': 1}},
                {'name': 'company_name_1', 'key': {'company_name': 1}},
                {'name': 'created_at_-1', 'key': {'created_at': -1}}
            ]
            mock_collection.insert_one = Mock(return_value=Mock(inserted_id=ObjectId()))
            mock_collection.find_one = Mock(return_value={'_id': ObjectId()})
            mock_collection.update_one = Mock()
            mock_collection.delete_one = Mock()
            
            # Mock collection access
            mock_db.__getitem__ = Mock(return_value=mock_collection)
            
            # Provide a mock MongoDB URI to avoid environment variable error
            self.schema_service = CleanSchemaService(mongodb_uri="mongodb://test:test@localhost:27017/test")
            self.mock_db = mock_db
            self.mock_collection = mock_collection
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        assert self.schema_service.readonly_collections == ['asteroids', 'elements']
        assert len(self.schema_service.new_collections) == 5
        assert 'users' in self.schema_service.new_collections
        assert 'ships' in self.schema_service.new_collections
        assert 'missions' in self.schema_service.new_collections
        assert 'simulation_state' in self.schema_service.new_collections
        assert 'market_prices' in self.schema_service.new_collections
    
    def test_users_schema_structure(self):
        """Test users collection schema structure"""
        users_schema = self.schema_service._get_users_schema()
        
        # Check validator exists
        assert 'validator' in users_schema
        assert '$jsonSchema' in users_schema['validator']
        
        # Check required fields
        required_fields = users_schema['validator']['$jsonSchema']['required']
        assert 'username' in required_fields
        assert 'company_name' in required_fields
        assert 'bank_balance' in required_fields
        assert 'created_at' in required_fields
        
        # Check properties
        properties = users_schema['validator']['$jsonSchema']['properties']
        assert 'username' in properties
        assert 'company_name' in properties
        assert 'bank_balance' in properties
        assert 'created_at' in properties
        assert 'last_login' in properties
        
        # Check indexes
        assert 'indexes' in users_schema
        assert len(users_schema['indexes']) == 3
        
        # Check unique index on username
        username_index = users_schema['indexes'][0]
        assert username_index['keys'] == [('username', 1)]
        assert username_index['options']['unique'] == True
    
    def test_ships_schema_structure(self):
        """Test ships collection schema structure"""
        ships_schema = self.schema_service._get_ships_schema()
        
        # Check required fields
        required_fields = ships_schema['validator']['$jsonSchema']['required']
        assert 'name' in required_fields
        assert 'user_id' in required_fields
        assert 'capacity' in required_fields
        assert 'mining_power' in required_fields
        assert 'shield' in required_fields
        assert 'hull' in required_fields
        assert 'location' in required_fields
        assert 'status' in required_fields
        assert 'created_at' in required_fields
        assert 'active' in required_fields
        
        # Check status enum
        status_property = ships_schema['validator']['$jsonSchema']['properties']['status']
        assert 'enum' in status_property
        assert 'available' in status_property['enum']
        assert 'en_route' in status_property['enum']
        assert 'mining' in status_property['enum']
        assert 'returning' in status_property['enum']
        assert 'repairing' in status_property['enum']
        
        # Check numeric constraints
        capacity_property = ships_schema['validator']['$jsonSchema']['properties']['capacity']
        assert capacity_property['minimum'] == 1000
        assert capacity_property['maximum'] == 100000
        
        mining_power_property = ships_schema['validator']['$jsonSchema']['properties']['mining_power']
        assert mining_power_property['minimum'] == 1
        assert mining_power_property['maximum'] == 100
        
        # Check indexes
        assert len(ships_schema['indexes']) == 4
    
    def test_missions_schema_structure(self):
        """Test missions collection schema structure"""
        missions_schema = self.schema_service._get_missions_schema()
        
        # Check required fields
        required_fields = missions_schema['validator']['$jsonSchema']['required']
        assert 'name' in required_fields
        assert 'user_id' in required_fields
        assert 'ship_id' in required_fields
        assert 'asteroid_name' in required_fields
        assert 'status' in required_fields
        assert 'travel_days' in required_fields
        assert 'mining_days' in required_fields
        assert 'days_elapsed' in required_fields
        assert 'ship_location' in required_fields
        assert 'cargo' in required_fields
        assert 'total_yield_kg' in required_fields
        assert 'budget' in required_fields
        assert 'cost' in required_fields
        assert 'revenue' in required_fields
        assert 'profit' in required_fields
        assert 'created_at' in required_fields
        
        # Check status enum
        status_property = missions_schema['validator']['$jsonSchema']['properties']['status']
        assert 'enum' in status_property
        assert 'planned' in status_property['enum']
        assert 'in_progress' in status_property['enum']
        assert 'completed' in status_property['enum']
        assert 'failed' in status_property['enum']
        
        # Check cargo array structure
        cargo_property = missions_schema['validator']['$jsonSchema']['properties']['cargo']
        assert cargo_property['bsonType'] == 'array'
        assert 'items' in cargo_property
        assert 'element' in cargo_property['items']['required']
        assert 'mass_kg' in cargo_property['items']['required']
        
        # Check numeric constraints
        travel_days_property = missions_schema['validator']['$jsonSchema']['properties']['travel_days']
        assert travel_days_property['minimum'] == 1
        assert travel_days_property['maximum'] == 1000
        
        mining_days_property = missions_schema['validator']['$jsonSchema']['properties']['mining_days']
        assert mining_days_property['minimum'] == 1
        assert mining_days_property['maximum'] == 365
        
        # Check indexes
        assert len(missions_schema['indexes']) == 5
    
    def test_simulation_state_schema_structure(self):
        """Test simulation state collection schema structure"""
        simulation_schema = self.schema_service._get_simulation_state_schema()
        
        # Check required fields
        required_fields = simulation_schema['validator']['$jsonSchema']['required']
        assert 'user_id' in required_fields
        assert 'current_day' in required_fields
        assert 'is_running' in required_fields
        assert 'active_missions' in required_fields
        assert 'last_updated' in required_fields
        
        # Check active_missions array
        active_missions_property = simulation_schema['validator']['$jsonSchema']['properties']['active_missions']
        assert active_missions_property['bsonType'] == 'array'
        assert active_missions_property['items']['bsonType'] == 'objectId'
        
        # Check numeric constraints
        current_day_property = simulation_schema['validator']['$jsonSchema']['properties']['current_day']
        assert current_day_property['minimum'] == 0
        
        # Check indexes
        assert len(simulation_schema['indexes']) == 3
        
        # Check unique index on user_id
        user_id_index = simulation_schema['indexes'][0]
        assert user_id_index['keys'] == [('user_id', 1)]
        assert user_id_index['options']['unique'] == True
    
    def test_market_prices_schema_structure(self):
        """Test market prices collection schema structure"""
        prices_schema = self.schema_service._get_market_prices_schema()
        
        # Check required fields
        required_fields = prices_schema['validator']['$jsonSchema']['required']
        assert 'element' in required_fields
        assert 'price_per_kg' in required_fields
        assert 'last_updated' in required_fields
        
        # Check numeric constraints
        price_property = prices_schema['validator']['$jsonSchema']['properties']['price_per_kg']
        assert price_property['minimum'] == 0
        
        # Check string constraints
        element_property = prices_schema['validator']['$jsonSchema']['properties']['element']
        assert element_property['minLength'] == 1
        assert element_property['maxLength'] == 50
        
        # Check indexes
        assert len(prices_schema['indexes']) == 2
        
        # Check unique index on element
        element_index = prices_schema['indexes'][0]
        assert element_index['keys'] == [('element', 1)]
        assert element_index['options']['unique'] == True
    
    @pytest.mark.asyncio
    async def test_create_clean_schema_success(self):
        """Test successful clean schema creation"""
        # Mock collection creation
        mock_collection = Mock()
        mock_collection.create_index = Mock()
        self.mock_db.create_collection.return_value = mock_collection
        
        results = await self.schema_service.create_clean_schema(drop_existing=True)
        
        # Check results structure
        assert 'collections_created' in results
        assert 'collections_dropped' in results
        assert 'indexes_created' in results
        assert 'errors' in results
        assert 'readonly_collections' in results
        
        # Check readonly collections
        assert results['readonly_collections'] == ['asteroids', 'elements']
        
        # Check that drop_collection was called for old collections
        assert self.mock_db.drop_collection.call_count >= 2
        
        # Check that create_collection was called for new collections
        assert self.mock_db.create_collection.call_count == 5
    
    @pytest.mark.asyncio
    async def test_create_clean_schema_without_drop(self):
        """Test clean schema creation without dropping existing collections"""
        # Mock collection creation
        mock_collection = Mock()
        mock_collection.create_index = Mock()
        self.mock_db.create_collection.return_value = mock_collection
        
        results = await self.schema_service.create_clean_schema(drop_existing=False)
        
        # Check that drop_collection was not called
        self.mock_db.drop_collection.assert_not_called()
        
        # Check that create_collection was called for new collections
        assert self.mock_db.create_collection.call_count == 5
    
    @pytest.mark.asyncio
    async def test_validate_schema_success(self):
        """Test successful schema validation"""
        # Mock existing collections
        self.mock_db.list_collection_names.return_value = [
            'asteroids', 'elements', 'users', 'ships', 'missions', 
            'simulation_state', 'market_prices'
        ]
        
        results = await self.schema_service.validate_schema()
        
        # Check results structure
        assert 'collections_validated' in results
        assert 'indexes_validated' in results
        assert 'errors' in results
        assert 'summary' in results
        
        # Check summary
        summary = results['summary']
        assert 'total_collections' in summary
        assert 'new_collections' in summary
        assert 'readonly_collections' in summary
        assert 'collections_validated' in summary
        assert 'indexes_validated' in summary
        assert 'errors' in summary
    
    @pytest.mark.asyncio
    async def test_validate_schema_missing_collections(self):
        """Test schema validation with missing collections"""
        # Mock missing collections
        self.mock_db.list_collection_names.return_value = ['asteroids', 'elements']
        
        results = await self.schema_service.validate_schema()
        
        # Check that errors were recorded for missing collections
        assert len(results['errors']) > 0
        assert any('Missing collection' in error for error in results['errors'])
    
    @pytest.mark.asyncio
    async def test_test_crud_operations_success(self):
        """Test successful CRUD operations testing"""
        results = await self.schema_service.test_crud_operations()
        
        # Check results structure
        assert 'tests_passed' in results
        assert 'tests_failed' in results
        assert 'errors' in results
        
        # Check that tests were run
        assert len(results['tests_passed']) > 0
        
        # Check specific test categories
        test_categories = ['users', 'ships', 'missions', 'simulation_state', 'market_prices']
        for category in test_categories:
            category_tests = [test for test in results['tests_passed'] if test.startswith(category)]
            assert len(category_tests) >= 4  # create, read, update, delete
    
    @pytest.mark.asyncio
    async def test_test_crud_operations_failure(self):
        """Test CRUD operations testing with failures"""
        # Create a new schema service with failing mock
        with patch('src.services.clean_schema.MongoClient') as mock_client:
            mock_db = Mock()
            mock_client.return_value.admin.command.return_value = True
            mock_client.return_value.asteroids = mock_db
            
            # Mock collection operations that fail
            mock_collection = Mock()
            mock_collection.insert_one = Mock(side_effect=Exception("Database error"))
            mock_collection.find_one = Mock(side_effect=Exception("Database error"))
            mock_collection.update_one = Mock(side_effect=Exception("Database error"))
            mock_collection.delete_one = Mock(side_effect=Exception("Database error"))
            
            # Mock collection access
            mock_db.__getitem__ = Mock(return_value=mock_collection)
            
            # Create service with failing mock
            failing_service = CleanSchemaService(mongodb_uri="mongodb://test:test@localhost:27017/test")
            failing_service.db = mock_db
            
            results = await failing_service.test_crud_operations()
            
            # Check that failures were recorded
            assert len(results['tests_failed']) > 0
            assert len(results['errors']) > 0
    
    def test_readonly_collections_property(self):
        """Test readonly collections property"""
        readonly = self.schema_service.readonly_collections
        assert isinstance(readonly, list)
        assert 'asteroids' in readonly
        assert 'elements' in readonly
        assert len(readonly) == 2
    
    def test_new_collections_property(self):
        """Test new collections property"""
        new_collections = self.schema_service.new_collections
        assert isinstance(new_collections, dict)
        assert len(new_collections) == 5
        
        expected_collections = ['users', 'ships', 'missions', 'simulation_state', 'market_prices']
        for collection in expected_collections:
            assert collection in new_collections
            assert 'validator' in new_collections[collection]
            assert 'indexes' in new_collections[collection]
    
    def test_schema_validation_constraints(self):
        """Test schema validation constraints"""
        # Test users schema constraints
        users_schema = self.schema_service._get_users_schema()
        username_prop = users_schema['validator']['$jsonSchema']['properties']['username']
        assert username_prop['minLength'] == 3
        assert username_prop['maxLength'] == 50
        assert 'pattern' in username_prop
        
        bank_balance_prop = users_schema['validator']['$jsonSchema']['properties']['bank_balance']
        assert bank_balance_prop['minimum'] == 0
        
        # Test ships schema constraints
        ships_schema = self.schema_service._get_ships_schema()
        capacity_prop = ships_schema['validator']['$jsonSchema']['properties']['capacity']
        assert capacity_prop['minimum'] == 1000
        assert capacity_prop['maximum'] == 100000
        
        location_prop = ships_schema['validator']['$jsonSchema']['properties']['location']
        assert location_prop['minimum'] == 0.0
        assert location_prop['maximum'] == 1.0
        
        # Test missions schema constraints
        missions_schema = self.schema_service._get_missions_schema()
        travel_days_prop = missions_schema['validator']['$jsonSchema']['properties']['travel_days']
        assert travel_days_prop['minimum'] == 1
        assert travel_days_prop['maximum'] == 1000
        
        mining_days_prop = missions_schema['validator']['$jsonSchema']['properties']['mining_days']
        assert mining_days_prop['minimum'] == 1
        assert mining_days_prop['maximum'] == 365
    
    def test_index_specifications(self):
        """Test index specifications"""
        # Test users indexes
        users_schema = self.schema_service._get_users_schema()
        users_indexes = users_schema['indexes']
        
        # Check username unique index
        username_index = users_indexes[0]
        assert username_index['keys'] == [('username', 1)]
        assert username_index['options']['unique'] == True
        
        # Check company_name index
        company_index = users_indexes[1]
        assert company_index['keys'] == [('company_name', 1)]
        
        # Check created_at index
        created_index = users_indexes[2]
        assert created_index['keys'] == [('created_at', -1)]
        
        # Test ships indexes
        ships_schema = self.schema_service._get_ships_schema()
        ships_indexes = ships_schema['indexes']
        assert len(ships_indexes) == 4
        
        # Test missions indexes
        missions_schema = self.schema_service._get_missions_schema()
        missions_indexes = missions_schema['indexes']
        assert len(missions_indexes) == 5
        
        # Test simulation_state indexes
        simulation_schema = self.schema_service._get_simulation_state_schema()
        simulation_indexes = simulation_schema['indexes']
        assert len(simulation_indexes) == 3
        
        # Check user_id unique index
        user_id_index = simulation_indexes[0]
        assert user_id_index['keys'] == [('user_id', 1)]
        assert user_id_index['options']['unique'] == True
        
        # Test market_prices indexes
        prices_schema = self.schema_service._get_market_prices_schema()
        prices_indexes = prices_schema['indexes']
        assert len(prices_indexes) == 2
        
        # Check element unique index
        element_index = prices_indexes[0]
        assert element_index['keys'] == [('element', 1)]
        assert element_index['options']['unique'] == True


if __name__ == "__main__":
    pytest.main([__file__])
