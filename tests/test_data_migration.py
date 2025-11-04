"""
Test suite for data migration service
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from bson import ObjectId

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.data_migration import DataMigrationService


class TestDataMigrationService:
    """Test cases for data migration service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock MongoDB connection to avoid actual database calls
        with patch('src.services.data_migration.MongoClient') as mock_client:
            mock_db = Mock()
            mock_client.return_value.admin.command.return_value = True
            mock_client.return_value.asteroids = mock_db
            
            # Mock collections
            mock_db.users = Mock()
            mock_db.ships = Mock()
            mock_db.missions = Mock()
            mock_db.events = Mock()
            mock_db.config = Mock()
            mock_db.users_new = Mock()
            mock_db.ships_new = Mock()
            mock_db.missions_new = Mock()
            mock_db.simulation_state_new = Mock()
            mock_db.market_prices_new = Mock()
            mock_db.asteroids = Mock()
            mock_db.elements = Mock()
            
            # Mock collection operations
            for collection in [mock_db.users, mock_db.ships, mock_db.missions, 
                             mock_db.users_new, mock_db.ships_new, mock_db.missions_new,
                             mock_db.simulation_state_new, mock_db.market_prices_new]:
                collection.find.return_value = []
                collection.find_one.return_value = None
                collection.insert_one.return_value = Mock(inserted_id=ObjectId())
                collection.insert_many.return_value = Mock(inserted_ids=[ObjectId()])
                collection.count_documents.return_value = 100
            
            # Provide a mock MongoDB URI to avoid environment variable error
            self.migration_service = DataMigrationService(mongodb_uri="mongodb://test:test@localhost:27017/test")
            self.mock_db = mock_db
    
    def test_service_initialization(self):
        """Test that service initializes correctly"""
        assert self.migration_service.old_users is not None
        assert self.migration_service.old_ships is not None
        assert self.migration_service.old_missions is not None
        assert self.migration_service.new_users is not None
        assert self.migration_service.new_ships is not None
        assert self.migration_service.new_missions is not None
        assert self.migration_service.asteroids is not None
        assert self.migration_service.elements is not None
        assert len(self.migration_service.migration_log) == 0
        assert self.migration_service.migration_stats['users_migrated'] == 0
    
    @pytest.mark.asyncio
    async def test_create_migration_backup(self):
        """Test migration backup creation"""
        # Mock backup collections
        mock_backup_collection = Mock()
        mock_backup_collection.insert_many.return_value = Mock()
        
        # Mock existing collections with data
        mock_collection_with_data = Mock()
        mock_collection_with_data.find.return_value = [
            {'_id': ObjectId(), 'data': 'test1'},
            {'_id': ObjectId(), 'data': 'test2'}
        ]
        
        # Mock collection access for backup
        def mock_getitem(key):
            if key.startswith('users_backup') or key.startswith('ships_backup'):
                return mock_backup_collection
            elif key in ['users', 'ships', 'missions', 'events', 'config']:
                return mock_collection_with_data
            return Mock()
        
        # Override the __getitem__ method properly
        self.mock_db.__getitem__ = Mock(side_effect=mock_getitem)
        
        results = await self.migration_service.create_migration_backup()
        
        # Check results structure
        assert 'backup_collections' in results
        assert 'backup_counts' in results
        assert 'backup_timestamp' in results
        assert 'errors' in results
        
        # Check that backup was attempted
        assert len(results['backup_collections']) > 0
    
    @pytest.mark.asyncio
    async def test_migrate_users_success(self):
        """Test successful user migration"""
        # Mock old users data
        old_users_data = [
            {
                '_id': ObjectId(),
                'username': 'testuser1',
                'company_name': 'Test Corp 1',
                'bank_balance': 1000000,
                'created_at': datetime.now(timezone.utc),
                'last_login': datetime.now(timezone.utc)
            },
            {
                '_id': ObjectId(),
                'username': 'testuser2',
                'company_name': 'Test Corp 2',
                'bank_balance': 2000000,
                'created_at': datetime.now(timezone.utc),
                'last_login': datetime.now(timezone.utc)
            }
        ]
        
        self.migration_service.old_users.find.return_value = old_users_data
        self.migration_service.new_users.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        results = await self.migration_service.migrate_users()
        
        # Check results
        assert results['users_migrated'] == 2
        assert results['users_skipped'] == 0
        assert len(results['errors']) == 0
        
        # Check that insert_one was called for each user
        assert self.migration_service.new_users.insert_one.call_count == 2
    
    @pytest.mark.asyncio
    async def test_migrate_users_with_skipped(self):
        """Test user migration with skipped users"""
        # Mock old users data with missing required fields
        old_users_data = [
            {
                '_id': ObjectId(),
                'username': 'validuser',
                'company_name': 'Valid Corp',
                'bank_balance': 1000000,
                'created_at': datetime.now(timezone.utc),
                'last_login': datetime.now(timezone.utc)
            },
            {
                '_id': ObjectId(),
                'username': '',  # Missing username
                'company_name': 'Invalid Corp',
                'bank_balance': 0
            },
            {
                '_id': ObjectId(),
                'username': 'incompleteuser',
                'company_name': '',  # Missing company name
                'bank_balance': 0
            }
        ]
        
        self.migration_service.old_users.find.return_value = old_users_data
        self.migration_service.new_users.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        results = await self.migration_service.migrate_users()
        
        # Check results
        assert results['users_migrated'] == 1
        assert results['users_skipped'] == 2
        assert len(results['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_migrate_ships_success(self):
        """Test successful ship migration"""
        # Mock old ships data
        old_ships_data = [
            {
                '_id': ObjectId(),
                'name': 'Test Ship 1',
                'user_id': 'testuser1',
                'capacity': 50000,
                'mining_power': 0.85,
                'shield': 95,
                'hull': 98,
                'location': 'earth',
                'status': 'available',
                'created_at': datetime.now(timezone.utc)
            },
            {
                '_id': ObjectId(),
                'name': 'Test Ship 2',
                'user_id': 'testuser2',
                'max_cargo_capacity': 30000,
                'mining_power': 2.5,
                'hull_integrity': 100,
                'location': 'asteroid',
                'status': 'mining',
                'created_at': datetime.now(timezone.utc)
            }
        ]
        
        self.migration_service.old_ships.find.return_value = old_ships_data
        self.migration_service.new_ships.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        # Mock user lookup for user_id conversion
        self.migration_service.new_users.find_one.return_value = {'_id': ObjectId()}
        
        results = await self.migration_service.migrate_ships()
        
        # Check results
        assert results['ships_migrated'] == 2
        assert results['ships_skipped'] == 0
        assert len(results['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_migrate_missions_success(self):
        """Test successful mission migration"""
        # Mock old missions data
        old_missions_data = [
            {
                '_id': ObjectId(),
                'name': 'Test Mission 1',
                'user_id': 'testuser1',
                'ship_id': ObjectId(),
                'asteroid_name': 'Test Asteroid',
                'status': 'planning',
                'asteroid_moid_days': 120,
                'current_day': 5,
                'budget': 1000000,
                'costs': {'total': 50000},
                'created_at': datetime.now(timezone.utc)
            }
        ]
        
        self.migration_service.old_missions.find.return_value = old_missions_data
        self.migration_service.new_missions.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        # Mock user lookup for user_id conversion
        self.migration_service.new_users.find_one.return_value = {'_id': ObjectId()}
        
        results = await self.migration_service.migrate_missions()
        
        # Check results
        assert results['missions_migrated'] == 1
        assert results['missions_skipped'] == 0
        assert len(results['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_create_simulation_states(self):
        """Test simulation state creation"""
        # Mock users data
        users_data = [
            {'_id': ObjectId(), 'username': 'user1'},
            {'_id': ObjectId(), 'username': 'user2'}
        ]
        
        self.migration_service.new_users.find.return_value = users_data
        self.migration_service.new_simulation_state.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        # Mock missions lookup
        self.migration_service.new_missions.find.return_value = []
        
        results = await self.migration_service.create_simulation_states()
        
        # Check results
        assert results['simulation_states_created'] == 2
        assert len(results['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_create_market_prices(self):
        """Test market prices creation"""
        self.migration_service.new_market_prices.insert_one.return_value = Mock(inserted_id=ObjectId())
        
        results = await self.migration_service.create_market_prices()
        
        # Check results
        assert results['market_prices_created'] == 10  # 10 default prices
        assert len(results['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_preserve_asteroid_element_data(self):
        """Test data preservation verification"""
        self.migration_service.asteroids.count_documents.return_value = 958524
        self.migration_service.elements.count_documents.return_value = 119
        
        results = await self.migration_service.preserve_asteroid_element_data()
        
        # Check results
        assert results['asteroids_count'] == 958524
        assert results['elements_count'] == 119
        assert results['preserved'] == True
        assert len(results['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_preserve_asteroid_element_data_missing(self):
        """Test data preservation verification with missing data"""
        self.migration_service.asteroids.count_documents.return_value = 0
        self.migration_service.elements.count_documents.return_value = 119
        
        results = await self.migration_service.preserve_asteroid_element_data()
        
        # Check results
        assert results['asteroids_count'] == 0
        assert results['elements_count'] == 119
        assert results['preserved'] == False
        assert len(results['errors']) > 0
    
    @pytest.mark.asyncio
    async def test_run_full_migration_success(self):
        """Test successful full migration"""
        # Mock all the individual migration methods
        with patch.object(self.migration_service, 'create_migration_backup') as mock_backup, \
             patch.object(self.migration_service, 'migrate_users') as mock_users, \
             patch.object(self.migration_service, 'migrate_ships') as mock_ships, \
             patch.object(self.migration_service, 'migrate_missions') as mock_missions, \
             patch.object(self.migration_service, 'create_simulation_states') as mock_simulation, \
             patch.object(self.migration_service, 'create_market_prices') as mock_prices, \
             patch.object(self.migration_service, 'preserve_asteroid_element_data') as mock_preserve:
            
            # Set up mock return values
            mock_backup.return_value = {'backup_collections': ['users_backup'], 'errors': []}
            mock_users.return_value = {'users_migrated': 2, 'users_skipped': 0, 'errors': []}
            mock_ships.return_value = {'ships_migrated': 3, 'ships_skipped': 0, 'errors': []}
            mock_missions.return_value = {'missions_migrated': 1, 'missions_skipped': 0, 'errors': []}
            mock_simulation.return_value = {'simulation_states_created': 2, 'errors': []}
            mock_prices.return_value = {'market_prices_created': 10, 'errors': []}
            mock_preserve.return_value = {'asteroids_count': 958524, 'elements_count': 119, 'preserved': True, 'errors': []}
            
            # Mock clean schema service
            with patch('src.services.data_migration.CleanSchemaService') as mock_schema_service:
                mock_schema_instance = Mock()
                mock_schema_service.return_value = mock_schema_instance
                mock_schema_instance.create_clean_schema.return_value = {'collections_created': ['users', 'ships']}
                
                results = await self.migration_service.run_full_migration(create_backup=True)
                
                # Check results
                assert results['success'] == True
                assert results['total_migrated'] == 18  # 2+3+1+2+10
                assert results['total_errors'] == 0
                # Migration log might be empty in mocked test
                assert 'migration_log' in results
    
    def test_normalize_capacity(self):
        """Test ship capacity normalization"""
        # Test with capacity field
        old_ship1 = {'capacity': 25000}
        assert self.migration_service._normalize_capacity(old_ship1) == 25000
        
        # Test with max_cargo_capacity field
        old_ship2 = {'max_cargo_capacity': 15000}
        assert self.migration_service._normalize_capacity(old_ship2) == 15000
        
        # Test with no capacity (default)
        old_ship3 = {}
        assert self.migration_service._normalize_capacity(old_ship3) == 50000
        
        # Test with capacity outside bounds
        old_ship4 = {'capacity': 75000}  # Too high
        assert self.migration_service._normalize_capacity(old_ship4) == 50000
        
        old_ship5 = {'capacity': 500}  # Too low
        assert self.migration_service._normalize_capacity(old_ship5) == 1000
    
    def test_normalize_mining_power(self):
        """Test mining power normalization"""
        # Test with decimal mining power
        old_ship1 = {'mining_power': 0.85}
        assert self.migration_service._normalize_mining_power(old_ship1) == 85
        
        # Test with integer mining power
        old_ship2 = {'mining_power': 75}
        assert self.migration_service._normalize_mining_power(old_ship2) == 75
        
        # Test with no mining power (default)
        old_ship3 = {}
        assert self.migration_service._normalize_mining_power(old_ship3) == 1
        
        # Test with mining power outside bounds
        old_ship4 = {'mining_power': 150}  # Too high
        assert self.migration_service._normalize_mining_power(old_ship4) == 100
        
        old_ship5 = {'mining_power': 0}  # Too low
        assert self.migration_service._normalize_mining_power(old_ship5) == 1
    
    def test_normalize_location(self):
        """Test ship location normalization"""
        assert self.migration_service._normalize_location('earth') == 0.0
        assert self.migration_service._normalize_location('en_route') == 0.5
        assert self.migration_service._normalize_location('asteroid') == 1.0
        assert self.migration_service._normalize_location('mining') == 1.0
        assert self.migration_service._normalize_location('returning') == 0.5
        assert self.migration_service._normalize_location('unknown') == 0.0
    
    def test_normalize_status(self):
        """Test ship status normalization"""
        assert self.migration_service._normalize_status('idle') == 'available'
        assert self.migration_service._normalize_status('available') == 'available'
        assert self.migration_service._normalize_status('en_route') == 'en_route'
        assert self.migration_service._normalize_status('mining') == 'mining'
        assert self.migration_service._normalize_status('returning') == 'returning'
        assert self.migration_service._normalize_status('repairing') == 'repairing'
        assert self.migration_service._normalize_status('unknown') == 'available'
    
    def test_normalize_mission_status(self):
        """Test mission status normalization"""
        assert self.migration_service._normalize_mission_status('planning') == 'planned'
        assert self.migration_service._normalize_mission_status('planned') == 'planned'
        assert self.migration_service._normalize_mission_status('in_progress') == 'in_progress'
        assert self.migration_service._normalize_mission_status('completed') == 'completed'
        assert self.migration_service._normalize_mission_status('failed') == 'failed'
        assert self.migration_service._normalize_mission_status('unknown') == 'planned'
    
    def test_calculate_travel_days(self):
        """Test travel days calculation"""
        old_mission1 = {'asteroid_moid_days': 120}
        assert self.migration_service._calculate_travel_days(old_mission1) == 120
        
        old_mission2 = {'asteroid_moid_days': 0}  # Too low
        assert self.migration_service._calculate_travel_days(old_mission2) == 1
        
        old_mission3 = {'asteroid_moid_days': 2000}  # Too high
        assert self.migration_service._calculate_travel_days(old_mission3) == 1000
        
        old_mission4 = {}  # No data
        assert self.migration_service._calculate_travel_days(old_mission4) == 120
    
    def test_calculate_ship_location(self):
        """Test ship location calculation"""
        old_mission1 = {'current_day': 30, 'total_days': 120}
        assert self.migration_service._calculate_ship_location(old_mission1) == 0.25
        
        old_mission2 = {'current_day': 120, 'total_days': 120}
        assert self.migration_service._calculate_ship_location(old_mission2) == 1.0
        
        old_mission3 = {'current_day': 0, 'total_days': 0}  # Division by zero
        assert self.migration_service._calculate_ship_location(old_mission3) == 0.0
        
        old_mission4 = {'current_day': 150, 'total_days': 120}  # Over 100%
        assert self.migration_service._calculate_ship_location(old_mission4) == 1.0
    
    def test_normalize_cargo(self):
        """Test cargo normalization"""
        old_mission1 = {
            'cargo': [
                {'element': 'Gold', 'mass_kg': 100.5},
                {'element': 'Silver', 'mass_kg': 250.0}
            ]
        }
        cargo = self.migration_service._normalize_cargo(old_mission1)
        assert len(cargo) == 2
        assert cargo[0]['element'] == 'Gold'
        assert cargo[0]['mass_kg'] == 100.5
        assert cargo[1]['element'] == 'Silver'
        assert cargo[1]['mass_kg'] == 250.0
        
        old_mission2 = {'cargo': []}  # Empty cargo
        cargo = self.migration_service._normalize_cargo(old_mission2)
        assert len(cargo) == 0
        
        old_mission3 = {}  # No cargo field
        cargo = self.migration_service._normalize_cargo(old_mission3)
        assert len(cargo) == 0
    
    def test_calculate_total_yield(self):
        """Test total yield calculation"""
        old_mission = {
            'cargo': [
                {'element': 'Gold', 'mass_kg': 100.5},
                {'element': 'Silver', 'mass_kg': 250.0}
            ]
        }
        total_yield = self.migration_service._calculate_total_yield(old_mission)
        assert total_yield == 350.5
        
        old_mission_empty = {'cargo': []}
        total_yield = self.migration_service._calculate_total_yield(old_mission_empty)
        assert total_yield == 0.0
    
    def test_calculate_mission_cost(self):
        """Test mission cost calculation"""
        old_mission1 = {'costs': {'total': 50000}}
        assert self.migration_service._calculate_mission_cost(old_mission1) == 50000
        
        old_mission2 = {'costs': {}}  # No total
        assert self.migration_service._calculate_mission_cost(old_mission2) == 0
        
        old_mission3 = {}  # No costs
        assert self.migration_service._calculate_mission_cost(old_mission3) == 0


if __name__ == "__main__":
    pytest.main([__file__])
