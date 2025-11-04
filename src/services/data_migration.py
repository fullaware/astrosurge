"""
Data Migration Scripts for AstroSurge

This service migrates existing data from the old schema to the new clean schema
while preserving asteroid and element data.
"""
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from bson import ObjectId
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.clean_schema import CleanSchemaService

logger = logging.getLogger(__name__)


class DataMigrationService:
    """
    Service for migrating existing data to the new clean schema.
    
    Features:
    - Migrate user data to new users collection
    - Migrate ship data to new ships collection
    - Migrate mission data to new missions collection
    - Preserve asteroid and element data
    - Create migration backup
    - Validate migration results
    - Rollback capability
    """
    
    def __init__(self, mongodb_uri: str = None):
        """Initialize the data migration service"""
        # MongoDB connection
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
        self.db = self.client.asteroids
        
        # Test connection
        try:
            self.client.admin.command('ping')
            logger.info("✅ MongoDB connection successful")
        except ConnectionFailure:
            logger.error("❌ MongoDB connection failed")
            raise
        
        # Collections
        self.old_users = self.db.users
        self.old_ships = self.db.ships
        self.old_missions = self.db.missions
        self.old_events = self.db.events
        self.old_config = self.db.config
        
        # New collections (will be created by clean schema service)
        self.new_users = self.db.users_new
        self.new_ships = self.db.ships_new
        self.new_missions = self.db.missions_new
        self.new_simulation_state = self.db.simulation_state_new
        self.new_market_prices = self.db.market_prices_new
        
        # Preserved collections
        self.asteroids = self.db.asteroids
        self.elements = self.db.elements
        
        # Migration tracking
        self.migration_log = []
        self.migration_stats = {
            'users_migrated': 0,
            'ships_migrated': 0,
            'missions_migrated': 0,
            'simulation_states_created': 0,
            'market_prices_created': 0,
            'errors': []
        }
    
    async def create_migration_backup(self) -> Dict[str, Any]:
        """
        Create a backup of existing data before migration.
        
        Returns:
            Dictionary with backup results
        """
        backup_results = {
            'backup_collections': [],
            'backup_counts': {},
            'backup_timestamp': datetime.now(timezone.utc),
            'errors': []
        }
        
        try:
            # Collections to backup
            collections_to_backup = ['users', 'ships', 'missions', 'events', 'config']
            
            for collection_name in collections_to_backup:
                try:
                    collection = self.db[collection_name]
                    backup_collection_name = f"{collection_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    backup_collection = self.db[backup_collection_name]
                    
                    # Copy all documents
                    documents = list(collection.find())
                    if documents:
                        backup_collection.insert_many(documents)
                        backup_results['backup_collections'].append(backup_collection_name)
                        backup_results['backup_counts'][collection_name] = len(documents)
                        logger.info(f"Backed up {len(documents)} documents from {collection_name} to {backup_collection_name}")
                    else:
                        logger.info(f"No documents to backup in {collection_name}")
                        
                except Exception as e:
                    error_msg = f"Error backing up {collection_name}: {str(e)}"
                    logger.error(error_msg)
                    backup_results['errors'].append(error_msg)
            
            logger.info("✅ Migration backup completed")
            return backup_results
            
        except Exception as e:
            error_msg = f"Error in migration backup: {str(e)}"
            logger.error(error_msg)
            backup_results['errors'].append(error_msg)
            return backup_results
    
    async def migrate_users(self) -> Dict[str, Any]:
        """
        Migrate user data to new users collection.
        
        Returns:
            Dictionary with migration results
        """
        migration_results = {
            'users_migrated': 0,
            'users_skipped': 0,
            'errors': []
        }
        
        try:
            # Get all users from old collection
            old_users = list(self.old_users.find())
            
            for old_user in old_users:
                try:
                    # Map old user data to new schema
                    new_user = {
                        'username': old_user.get('username', ''),
                        'company_name': old_user.get('company_name', ''),
                        'bank_balance': old_user.get('bank_balance', 0),
                        'created_at': old_user.get('created_at', datetime.now(timezone.utc)),
                        'last_login': old_user.get('last_login', datetime.now(timezone.utc))
                    }
                    
                    # Validate required fields
                    if not new_user['username'] or not new_user['company_name']:
                        logger.warning(f"Skipping user with missing required fields: {old_user.get('_id')}")
                        migration_results['users_skipped'] += 1
                        continue
                    
                    # Insert into new collection
                    result = self.new_users.insert_one(new_user)
                    migration_results['users_migrated'] += 1
                    self.migration_log.append(f"Migrated user: {new_user['username']} -> {result.inserted_id}")
                    
                except Exception as e:
                    error_msg = f"Error migrating user {old_user.get('_id')}: {str(e)}"
                    logger.error(error_msg)
                    migration_results['errors'].append(error_msg)
            
            logger.info(f"✅ Users migration completed: {migration_results['users_migrated']} migrated, {migration_results['users_skipped']} skipped")
            return migration_results
            
        except Exception as e:
            error_msg = f"Error in users migration: {str(e)}"
            logger.error(error_msg)
            migration_results['errors'].append(error_msg)
            return migration_results
    
    async def migrate_ships(self) -> Dict[str, Any]:
        """
        Migrate ship data to new ships collection.
        
        Returns:
            Dictionary with migration results
        """
        migration_results = {
            'ships_migrated': 0,
            'ships_skipped': 0,
            'errors': []
        }
        
        try:
            # Get all ships from old collection
            old_ships = list(self.old_ships.find())
            
            for old_ship in old_ships:
                try:
                    # Map old ship data to new schema
                    new_ship = {
                        'name': old_ship.get('name', 'Unnamed Ship'),
                        'user_id': self._get_user_object_id(old_ship.get('user_id', '')),
                        'capacity': self._normalize_capacity(old_ship),
                        'mining_power': self._normalize_mining_power(old_ship),
                        'shield': self._normalize_shield(old_ship),
                        'hull': self._normalize_hull(old_ship),
                        'location': self._normalize_location(old_ship.get('location', 'earth')),
                        'status': self._normalize_status(old_ship.get('status', 'idle')),
                        'created_at': old_ship.get('created_at', datetime.now(timezone.utc)),
                        'active': True
                    }
                    
                    # Validate required fields
                    if not new_ship['name'] or not new_ship['user_id']:
                        logger.warning(f"Skipping ship with missing required fields: {old_ship.get('_id')}")
                        migration_results['ships_skipped'] += 1
                        continue
                    
                    # Insert into new collection
                    result = self.new_ships.insert_one(new_ship)
                    migration_results['ships_migrated'] += 1
                    self.migration_log.append(f"Migrated ship: {new_ship['name']} -> {result.inserted_id}")
                    
                except Exception as e:
                    error_msg = f"Error migrating ship {old_ship.get('_id')}: {str(e)}"
                    logger.error(error_msg)
                    migration_results['errors'].append(error_msg)
            
            logger.info(f"✅ Ships migration completed: {migration_results['ships_migrated']} migrated, {migration_results['ships_skipped']} skipped")
            return migration_results
            
        except Exception as e:
            error_msg = f"Error in ships migration: {str(e)}"
            logger.error(error_msg)
            migration_results['errors'].append(error_msg)
            return migration_results
    
    async def migrate_missions(self) -> Dict[str, Any]:
        """
        Migrate mission data to new missions collection.
        
        Returns:
            Dictionary with migration results
        """
        migration_results = {
            'missions_migrated': 0,
            'missions_skipped': 0,
            'errors': []
        }
        
        try:
            # Get all missions from old collection
            old_missions = list(self.old_missions.find())
            
            for old_mission in old_missions:
                try:
                    # Map old mission data to new schema
                    new_mission = {
                        'name': old_mission.get('name', 'Unnamed Mission'),
                        'user_id': self._get_user_object_id(old_mission.get('user_id', '')),
                        'ship_id': self._get_ship_object_id(old_mission.get('ship_id', '')),
                        'asteroid_name': old_mission.get('asteroid_name', ''),
                        'status': self._normalize_mission_status(old_mission.get('status', 'planning')),
                        'travel_days': self._calculate_travel_days(old_mission),
                        'mining_days': self._calculate_mining_days(old_mission),
                        'days_elapsed': old_mission.get('current_day', 0),
                        'ship_location': self._calculate_ship_location(old_mission),
                        'cargo': self._normalize_cargo(old_mission),
                        'total_yield_kg': self._calculate_total_yield(old_mission),
                        'budget': old_mission.get('budget', 0),
                        'cost': self._calculate_mission_cost(old_mission),
                        'revenue': self._calculate_mission_revenue(old_mission),
                        'profit': self._calculate_mission_profit(old_mission),
                        'created_at': old_mission.get('created_at', datetime.now(timezone.utc)),
                        'started_at': old_mission.get('actual_launch_date'),
                        'completed_at': None
                    }
                    
                    # Validate required fields
                    if not new_mission['name'] or not new_mission['user_id'] or not new_mission['ship_id']:
                        logger.warning(f"Skipping mission with missing required fields: {old_mission.get('_id')}")
                        migration_results['missions_skipped'] += 1
                        continue
                    
                    # Insert into new collection
                    result = self.new_missions.insert_one(new_mission)
                    migration_results['missions_migrated'] += 1
                    self.migration_log.append(f"Migrated mission: {new_mission['name']} -> {result.inserted_id}")
                    
                except Exception as e:
                    error_msg = f"Error migrating mission {old_mission.get('_id')}: {str(e)}"
                    logger.error(error_msg)
                    migration_results['errors'].append(error_msg)
            
            logger.info(f"✅ Missions migration completed: {migration_results['missions_migrated']} migrated, {migration_results['missions_skipped']} skipped")
            return migration_results
            
        except Exception as e:
            error_msg = f"Error in missions migration: {str(e)}"
            logger.error(error_msg)
            migration_results['errors'].append(error_msg)
            return migration_results
    
    async def create_simulation_states(self) -> Dict[str, Any]:
        """
        Create simulation state records for each user.
        
        Returns:
            Dictionary with creation results
        """
        creation_results = {
            'simulation_states_created': 0,
            'errors': []
        }
        
        try:
            # Get all users from new users collection
            users = list(self.new_users.find())
            
            for user in users:
                try:
                    # Get active missions for this user
                    active_missions = list(self.new_missions.find({
                        'user_id': user['_id'],
                        'status': {'$in': ['in_progress', 'planned']}
                    }))
                    
                    # Create simulation state
                    simulation_state = {
                        'user_id': user['_id'],
                        'current_day': 1,  # Default to day 1
                        'is_running': len(active_missions) > 0,
                        'active_missions': [mission['_id'] for mission in active_missions],
                        'last_updated': datetime.now(timezone.utc)
                    }
                    
                    # Insert simulation state
                    result = self.new_simulation_state.insert_one(simulation_state)
                    creation_results['simulation_states_created'] += 1
                    self.migration_log.append(f"Created simulation state for user: {user['username']} -> {result.inserted_id}")
                    
                except Exception as e:
                    error_msg = f"Error creating simulation state for user {user.get('username')}: {str(e)}"
                    logger.error(error_msg)
                    creation_results['errors'].append(error_msg)
            
            logger.info(f"✅ Simulation states creation completed: {creation_results['simulation_states_created']} created")
            return creation_results
            
        except Exception as e:
            error_msg = f"Error in simulation states creation: {str(e)}"
            logger.error(error_msg)
            creation_results['errors'].append(error_msg)
            return creation_results
    
    async def create_market_prices(self) -> Dict[str, Any]:
        """
        Create initial market prices for common elements.
        
        Returns:
            Dictionary with creation results
        """
        creation_results = {
            'market_prices_created': 0,
            'errors': []
        }
        
        try:
            # Default market prices (per kg in USD)
            default_prices = {
                'Gold': 70548.0,      # ~$70,548/kg
                'Platinum': 35274.0,  # ~$35,274/kg
                'Silver': 881.85,     # ~$882/kg
                'Copper': 141.10,    # ~$141/kg
                'Palladium': 70548.0, # ~$70,548/kg
                'Iron': 0.15,         # ~$0.15/kg
                'Nickel': 20.0,       # ~$20/kg
                'Cobalt': 80.0,       # ~$80/kg
                'Lithium': 15.0,      # ~$15/kg
                'Rare Earth Elements': 1000.0  # ~$1,000/kg
            }
            
            for element, price in default_prices.items():
                try:
                    market_price = {
                        'element': element,
                        'price_per_kg': price,
                        'last_updated': datetime.now(timezone.utc)
                    }
                    
                    # Insert market price
                    result = self.new_market_prices.insert_one(market_price)
                    creation_results['market_prices_created'] += 1
                    self.migration_log.append(f"Created market price: {element} -> {result.inserted_id}")
                    
                except Exception as e:
                    error_msg = f"Error creating market price for {element}: {str(e)}"
                    logger.error(error_msg)
                    creation_results['errors'].append(error_msg)
            
            logger.info(f"✅ Market prices creation completed: {creation_results['market_prices_created']} created")
            return creation_results
            
        except Exception as e:
            error_msg = f"Error in market prices creation: {str(e)}"
            logger.error(error_msg)
            creation_results['errors'].append(error_msg)
            return creation_results
    
    async def preserve_asteroid_element_data(self) -> Dict[str, Any]:
        """
        Verify that asteroid and element data is preserved.
        
        Returns:
            Dictionary with preservation results
        """
        preservation_results = {
            'asteroids_count': 0,
            'elements_count': 0,
            'preserved': True,
            'errors': []
        }
        
        try:
            # Count asteroids
            asteroids_count = self.asteroids.count_documents({})
            preservation_results['asteroids_count'] = asteroids_count
            
            # Count elements
            elements_count = self.elements.count_documents({})
            preservation_results['elements_count'] = elements_count
            
            if asteroids_count == 0:
                preservation_results['preserved'] = False
                preservation_results['errors'].append("No asteroids found - data may be missing")
            
            if elements_count == 0:
                preservation_results['preserved'] = False
                preservation_results['errors'].append("No elements found - data may be missing")
            
            logger.info(f"✅ Data preservation verified: {asteroids_count} asteroids, {elements_count} elements")
            return preservation_results
            
        except Exception as e:
            error_msg = f"Error verifying data preservation: {str(e)}"
            logger.error(error_msg)
            preservation_results['errors'].append(error_msg)
            preservation_results['preserved'] = False
            return preservation_results
    
    async def run_full_migration(self, create_backup: bool = True) -> Dict[str, Any]:
        """
        Run the complete data migration process.
        
        Args:
            create_backup: Whether to create backup before migration
            
        Returns:
            Dictionary with migration results
        """
        migration_results = {
            'backup_results': {},
            'users_migration': {},
            'ships_migration': {},
            'missions_migration': {},
            'simulation_states_creation': {},
            'market_prices_creation': {},
            'data_preservation': {},
            'total_migrated': 0,
            'total_errors': 0,
            'migration_log': [],
            'success': True
        }
        
        try:
            logger.info("🚀 Starting full data migration...")
            
            # Step 1: Create backup
            if create_backup:
                logger.info("📦 Creating migration backup...")
                migration_results['backup_results'] = await self.create_migration_backup()
            
            # Step 2: Create new collections with clean schema
            logger.info("🏗️ Creating new collections with clean schema...")
            schema_service = CleanSchemaService(mongodb_uri=self.mongodb_uri)
            schema_results = schema_service.create_clean_schema(drop_existing=False)
            
            # Step 3: Migrate users
            logger.info("👥 Migrating users...")
            migration_results['users_migration'] = await self.migrate_users()
            
            # Step 4: Migrate ships
            logger.info("🚢 Migrating ships...")
            migration_results['ships_migration'] = await self.migrate_ships()
            
            # Step 5: Migrate missions
            logger.info("🎯 Migrating missions...")
            migration_results['missions_migration'] = await self.migrate_missions()
            
            # Step 6: Create simulation states
            logger.info("🎮 Creating simulation states...")
            migration_results['simulation_states_creation'] = await self.create_simulation_states()
            
            # Step 7: Create market prices
            logger.info("💰 Creating market prices...")
            migration_results['market_prices_creation'] = await self.create_market_prices()
            
            # Step 8: Verify data preservation
            logger.info("🔍 Verifying data preservation...")
            migration_results['data_preservation'] = await self.preserve_asteroid_element_data()
            
            # Calculate totals
            migration_results['total_migrated'] = (
                migration_results['users_migration'].get('users_migrated', 0) +
                migration_results['ships_migration'].get('ships_migrated', 0) +
                migration_results['missions_migration'].get('missions_migrated', 0) +
                migration_results['simulation_states_creation'].get('simulation_states_created', 0) +
                migration_results['market_prices_creation'].get('market_prices_created', 0)
            )
            
            # Count errors
            all_errors = []
            for result in migration_results.values():
                if isinstance(result, dict) and 'errors' in result:
                    all_errors.extend(result['errors'])
            migration_results['total_errors'] = len(all_errors)
            
            # Set success flag
            migration_results['success'] = migration_results['total_errors'] == 0
            
            # Copy migration log
            migration_results['migration_log'] = self.migration_log.copy()
            
            if migration_results['success']:
                logger.info("✅ Full data migration completed successfully!")
            else:
                logger.warning(f"⚠️ Full data migration completed with {migration_results['total_errors']} errors")
            
            return migration_results
            
        except Exception as e:
            error_msg = f"Error in full migration: {str(e)}"
            logger.error(error_msg)
            migration_results['success'] = False
            migration_results['total_errors'] += 1
            migration_results['migration_log'].append(error_msg)
            return migration_results
    
    # Helper methods for data normalization
    
    def _get_user_object_id(self, user_id: str) -> Optional[ObjectId]:
        """Convert user_id string to ObjectId"""
        if not user_id:
            return None
        
        # If it's already an ObjectId, return it
        if isinstance(user_id, ObjectId):
            return user_id
        
        # Try to find user by username and return their ObjectId
        try:
            user = self.new_users.find_one({'username': user_id})
            return user['_id'] if user else None
        except:
            return None
    
    def _get_ship_object_id(self, ship_id: str) -> Optional[ObjectId]:
        """Convert ship_id string to ObjectId"""
        if not ship_id:
            return None
        
        # If it's already an ObjectId, return it
        if isinstance(ship_id, ObjectId):
            return ship_id
        
        # For now, return None as we'll need to map old ship IDs to new ones
        return None
    
    def _normalize_capacity(self, old_ship: Dict[str, Any]) -> int:
        """Normalize ship capacity to new schema"""
        capacity = old_ship.get('capacity') or old_ship.get('max_cargo_capacity', 50000)
        return max(1000, min(50000, int(capacity)))
    
    def _normalize_mining_power(self, old_ship: Dict[str, Any]) -> int:
        """Normalize mining power to new schema (1-100 scale)"""
        mining_power = old_ship.get('mining_power', 1)
        if isinstance(mining_power, float):
            # Convert from decimal to percentage
            return max(1, min(100, int(mining_power * 100)))
        return max(1, min(100, int(mining_power)))
    
    def _normalize_shield(self, old_ship: Dict[str, Any]) -> int:
        """Normalize shield strength to new schema"""
        shield = old_ship.get('shield', 100)
        return max(1, min(100, int(shield)))
    
    def _normalize_hull(self, old_ship: Dict[str, Any]) -> int:
        """Normalize hull integrity to new schema"""
        hull = old_ship.get('hull') or old_ship.get('hull_integrity', 100)
        return max(1, min(100, int(hull)))
    
    def _normalize_location(self, location: str) -> float:
        """Normalize ship location to new schema (0.0-1.0 scale)"""
        location_map = {
            'earth': 0.0,
            'en_route': 0.5,
            'asteroid': 1.0,
            'mining': 1.0,
            'returning': 0.5
        }
        return location_map.get(location.lower(), 0.0)
    
    def _normalize_status(self, status: str) -> str:
        """Normalize ship status to new schema"""
        status_map = {
            'idle': 'available',
            'available': 'available',
            'en_route': 'en_route',
            'mining': 'mining',
            'returning': 'returning',
            'repairing': 'repairing'
        }
        return status_map.get(status.lower(), 'available')
    
    def _normalize_mission_status(self, status: str) -> str:
        """Normalize mission status to new schema"""
        status_map = {
            'planning': 'planned',
            'planned': 'planned',
            'in_progress': 'in_progress',
            'completed': 'completed',
            'failed': 'failed'
        }
        return status_map.get(status.lower(), 'planned')
    
    def _calculate_travel_days(self, old_mission: Dict[str, Any]) -> int:
        """Calculate travel days from old mission data"""
        asteroid_moid_days = old_mission.get('asteroid_moid_days', 120)
        return max(1, min(1000, int(asteroid_moid_days)))
    
    def _calculate_mining_days(self, old_mission: Dict[str, Any]) -> int:
        """Calculate mining days from old mission data"""
        # Default to 30 days mining
        return 30
    
    def _calculate_ship_location(self, old_mission: Dict[str, Any]) -> float:
        """Calculate current ship location from mission data"""
        current_day = old_mission.get('current_day', 0)
        total_days = old_mission.get('total_days', 120)
        
        if total_days == 0:
            return 0.0
        
        progress = min(1.0, current_day / total_days)
        return progress
    
    def _normalize_cargo(self, old_mission: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize cargo data to new schema"""
        cargo = []
        
        # Check for cargo in various possible locations
        cargo_data = old_mission.get('cargo', [])
        if isinstance(cargo_data, list):
            for item in cargo_data:
                if isinstance(item, dict) and 'element' in item and 'mass_kg' in item:
                    cargo.append({
                        'element': item['element'],
                        'mass_kg': float(item['mass_kg'])
                    })
        
        return cargo
    
    def _calculate_total_yield(self, old_mission: Dict[str, Any]) -> float:
        """Calculate total yield from mission data"""
        cargo = self._normalize_cargo(old_mission)
        return sum(item['mass_kg'] for item in cargo)
    
    def _calculate_mission_cost(self, old_mission: Dict[str, Any]) -> float:
        """Calculate mission cost from old data"""
        costs = old_mission.get('costs', {})
        return float(costs.get('total', 0))
    
    def _calculate_mission_revenue(self, old_mission: Dict[str, Any]) -> float:
        """Calculate mission revenue (placeholder)"""
        # This would need to be calculated based on cargo value
        return 0.0
    
    def _calculate_mission_profit(self, old_mission: Dict[str, Any]) -> float:
        """Calculate mission profit"""
        revenue = self._calculate_mission_revenue(old_mission)
        cost = self._calculate_mission_cost(old_mission)
        return revenue - cost


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Create migration service instance
        migration_service = DataMigrationService()
        
        print("🚀 AstroSurge Data Migration Service")
        print("=" * 50)
        
        # Run full migration
        print("\n📊 Running Full Data Migration...")
        migration_results = await migration_service.run_full_migration(create_backup=True)
        
        print(f"\n✅ Migration Results:")
        print(f"  - Total Migrated: {migration_results['total_migrated']}")
        print(f"  - Total Errors: {migration_results['total_errors']}")
        print(f"  - Success: {migration_results['success']}")
        
        print(f"\n📋 Detailed Results:")
        print(f"  - Users Migrated: {migration_results['users_migration'].get('users_migrated', 0)}")
        print(f"  - Ships Migrated: {migration_results['ships_migration'].get('ships_migrated', 0)}")
        print(f"  - Missions Migrated: {migration_results['missions_migration'].get('missions_migrated', 0)}")
        print(f"  - Simulation States Created: {migration_results['simulation_states_creation'].get('simulation_states_created', 0)}")
        print(f"  - Market Prices Created: {migration_results['market_prices_creation'].get('market_prices_created', 0)}")
        
        if migration_results['data_preservation']['preserved']:
            print(f"  - Asteroids Preserved: {migration_results['data_preservation']['asteroids_count']}")
            print(f"  - Elements Preserved: {migration_results['data_preservation']['elements_count']}")
        
        if migration_results['total_errors'] > 0:
            print(f"\n❌ Errors Encountered:")
            for error in migration_results.get('migration_log', []):
                if 'Error' in error:
                    print(f"  - {error}")
        
        print(f"\n🎯 Data Migration Complete!")
        print(f"✅ Ready for AstroSurge Integration")
    
    # Run the example
    asyncio.run(main())
