"""
Clean Database Schema Implementation for AstroSurge

This service implements the new clean database schema from schema_design.md
with proper indexes, validation, and constraints.
"""
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from bson import ObjectId
import sys

logger = logging.getLogger(__name__)


class CleanSchemaService:
    """
    Service for implementing the clean database schema for AstroSurge.
    
    Features:
    - Create new collections with clean schema
    - Implement proper indexes for performance
    - Add data validation and constraints
    - Maintain read-only collections (asteroids, elements)
    - Schema validation and testing
    """
    
    def __init__(self, mongodb_uri: str = None):
        """Initialize the clean schema service"""
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
        
        # Collections to keep (read-only)
        self.readonly_collections = ['asteroids', 'elements']
        
        # New collections to create
        self.new_collections = {
            'users': self._get_users_schema(),
            'ships': self._get_ships_schema(),
            'missions': self._get_missions_schema(),
            'simulation_state': self._get_simulation_state_schema(),
            'market_prices': self._get_market_prices_schema()
        }
    
    def _get_users_schema(self) -> Dict[str, Any]:
        """Get users collection schema"""
        return {
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['username', 'company_name', 'bank_balance', 'created_at'],
                    'properties': {
                        'username': {
                            'bsonType': 'string',
                            'minLength': 3,
                            'maxLength': 50,
                            'pattern': '^[a-zA-Z0-9_]+$',
                            'description': 'Unique username (3-50 chars, alphanumeric + underscore)'
                        },
                        'company_name': {
                            'bsonType': 'string',
                            'minLength': 1,
                            'maxLength': 100,
                            'description': 'Company name (1-100 chars)'
                        },
                        'bank_balance': {
                            'bsonType': 'number',
                            'minimum': 0,
                            'description': 'Current balance in dollars (non-negative)'
                        },
                        'created_at': {
                            'bsonType': 'date',
                            'description': 'Account creation date'
                        },
                        'last_login': {
                            'bsonType': 'date',
                            'description': 'Last login timestamp'
                        }
                    }
                }
            },
            'indexes': [
                {'keys': [('username', ASCENDING)], 'options': {'unique': True}},
                {'keys': [('company_name', ASCENDING)]},
                {'keys': [('created_at', DESCENDING)]}
            ]
        }
    
    def _get_ships_schema(self) -> Dict[str, Any]:
        """Get ships collection schema"""
        return {
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['name', 'user_id', 'capacity', 'mining_power', 'shield', 'hull', 'location', 'status', 'created_at', 'active'],
                    'properties': {
                        'name': {
                            'bsonType': 'string',
                            'minLength': 1,
                            'maxLength': 100,
                            'description': 'Ship name (1-100 chars)'
                        },
                        'user_id': {
                            'bsonType': 'objectId',
                            'description': 'Reference to user'
                        },
                        'capacity': {
                            'bsonType': 'number',
                            'minimum': 1000,
                            'maximum': 50000,
                            'description': 'Cargo capacity in kg (1,000-50,000)'
                        },
                        'mining_power': {
                            'bsonType': 'number',
                            'minimum': 1,
                            'maximum': 100,
                            'description': 'Mining efficiency (1-100)'
                        },
                        'shield': {
                            'bsonType': 'number',
                            'minimum': 1,
                            'maximum': 100,
                            'description': 'Shield strength (1-100)'
                        },
                        'hull': {
                            'bsonType': 'number',
                            'minimum': 1,
                            'maximum': 100,
                            'description': 'Hull integrity (1-100)'
                        },
                        'location': {
                            'bsonType': 'number',
                            'minimum': 0.0,
                            'maximum': 1.0,
                            'description': 'Ship location (0.0=Earth, 1.0=Asteroid)'
                        },
                        'status': {
                            'bsonType': 'string',
                            'enum': ['available', 'en_route', 'mining', 'returning', 'repairing'],
                            'description': 'Ship status'
                        },
                        'created_at': {
                            'bsonType': 'date',
                            'description': 'Ship creation date'
                        },
                        'active': {
                            'bsonType': 'bool',
                            'description': 'Whether ship is operational'
                        }
                    }
                }
            },
            'indexes': [
                {'keys': [('user_id', ASCENDING)]},
                {'keys': [('status', ASCENDING)]},
                {'keys': [('active', ASCENDING)]},
                {'keys': [('created_at', DESCENDING)]}
            ]
        }
    
    def _get_missions_schema(self) -> Dict[str, Any]:
        """Get missions collection schema"""
        return {
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['name', 'user_id', 'ship_id', 'asteroid_name', 'status', 'travel_days', 'mining_days', 'days_elapsed', 'ship_location', 'cargo', 'total_yield_kg', 'budget', 'cost', 'revenue', 'profit', 'created_at'],
                    'properties': {
                        'name': {
                            'bsonType': 'string',
                            'minLength': 1,
                            'maxLength': 100,
                            'description': 'Mission name (1-100 chars)'
                        },
                        'user_id': {
                            'bsonType': 'objectId',
                            'description': 'Reference to user'
                        },
                        'ship_id': {
                            'bsonType': 'objectId',
                            'description': 'Reference to ship'
                        },
                        'asteroid_name': {
                            'bsonType': 'string',
                            'minLength': 1,
                            'maxLength': 200,
                            'description': 'Target asteroid name'
                        },
                        'status': {
                            'bsonType': 'string',
                            'enum': ['planned', 'in_progress', 'completed', 'failed'],
                            'description': 'Mission status'
                        },
                        'travel_days': {
                            'bsonType': 'number',
                            'minimum': 1,
                            'maximum': 1000,
                            'description': 'Days to reach asteroid (1-1000)'
                        },
                        'mining_days': {
                            'bsonType': 'number',
                            'minimum': 1,
                            'maximum': 365,
                            'description': 'Days allocated for mining (1-365)'
                        },
                        'days_elapsed': {
                            'bsonType': 'number',
                            'minimum': 0,
                            'description': 'Current day in mission (non-negative)'
                        },
                        'ship_location': {
                            'bsonType': 'number',
                            'minimum': 0.0,
                            'maximum': 1.0,
                            'description': 'Current ship location (0.0-1.0)'
                        },
                        'cargo': {
                            'bsonType': 'array',
                            'items': {
                                'bsonType': 'object',
                                'required': ['element', 'mass_kg'],
                                'properties': {
                                    'element': {
                                        'bsonType': 'string',
                                        'description': 'Element name'
                                    },
                                    'mass_kg': {
                                        'bsonType': 'number',
                                        'minimum': 0,
                                        'description': 'Mass in kg (non-negative)'
                                    }
                                }
                            },
                            'description': 'Current cargo array'
                        },
                        'total_yield_kg': {
                            'bsonType': 'number',
                            'minimum': 0,
                            'description': 'Total extracted mass (non-negative)'
                        },
                        'budget': {
                            'bsonType': 'number',
                            'minimum': 0,
                            'description': 'Mission budget in dollars (non-negative)'
                        },
                        'cost': {
                            'bsonType': 'number',
                            'minimum': 0,
                            'description': 'Current mission cost (non-negative)'
                        },
                        'revenue': {
                            'bsonType': 'number',
                            'minimum': 0,
                            'description': 'Expected revenue (non-negative)'
                        },
                        'profit': {
                            'bsonType': 'number',
                            'description': 'Expected profit (can be negative)'
                        },
                        'created_at': {
                            'bsonType': 'date',
                            'description': 'Mission creation date'
                        },
                        'started_at': {
                            'bsonType': 'date',
                            'description': 'Mission start date'
                        },
                        'completed_at': {
                            'bsonType': 'date',
                            'description': 'Mission completion date'
                        }
                    }
                }
            },
            'indexes': [
                {'keys': [('user_id', ASCENDING)]},
                {'keys': [('ship_id', ASCENDING)]},
                {'keys': [('status', ASCENDING)]},
                {'keys': [('created_at', DESCENDING)]},
                {'keys': [('asteroid_name', ASCENDING)]}
            ]
        }
    
    def _get_simulation_state_schema(self) -> Dict[str, Any]:
        """Get simulation state collection schema"""
        return {
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['user_id', 'current_day', 'is_running', 'active_missions', 'last_updated'],
                    'properties': {
                        'user_id': {
                            'bsonType': 'objectId',
                            'description': 'Reference to user'
                        },
                        'current_day': {
                            'bsonType': 'number',
                            'minimum': 0,
                            'description': 'Current simulation day (non-negative)'
                        },
                        'is_running': {
                            'bsonType': 'bool',
                            'description': 'Whether simulation is active'
                        },
                        'active_missions': {
                            'bsonType': 'array',
                            'items': {
                                'bsonType': 'objectId'
                            },
                            'description': 'Array of active mission IDs'
                        },
                        'last_updated': {
                            'bsonType': 'date',
                            'description': 'Last simulation update'
                        }
                    }
                }
            },
            'indexes': [
                {'keys': [('user_id', ASCENDING)], 'options': {'unique': True}},
                {'keys': [('is_running', ASCENDING)]},
                {'keys': [('last_updated', DESCENDING)]}
            ]
        }
    
    def _get_market_prices_schema(self) -> Dict[str, Any]:
        """Get market prices collection schema"""
        return {
            'validator': {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'required': ['element', 'price_per_kg', 'last_updated'],
                    'properties': {
                        'element': {
                            'bsonType': 'string',
                            'minLength': 1,
                            'maxLength': 50,
                            'description': 'Element name (1-50 chars)'
                        },
                        'price_per_kg': {
                            'bsonType': 'number',
                            'minimum': 0,
                            'description': 'Price per kg in dollars (non-negative)'
                        },
                        'last_updated': {
                            'bsonType': 'date',
                            'description': 'Last price update'
                        }
                    }
                }
            },
            'indexes': [
                {'keys': [('element', ASCENDING)], 'options': {'unique': True}},
                {'keys': [('last_updated', DESCENDING)]}
            ]
        }
    
    async def create_clean_schema(self, drop_existing: bool = False) -> Dict[str, Any]:
        """
        Create the clean database schema.
        
        Args:
            drop_existing: Whether to drop existing collections first
            
        Returns:
            Dictionary with creation results
        """
        results = {
            'collections_created': [],
            'collections_dropped': [],
            'indexes_created': [],
            'errors': [],
            'readonly_collections': self.readonly_collections
        }
        
        try:
            # Drop existing collections if requested
            if drop_existing:
                await self._drop_existing_collections(results)
            
            # Create new collections
            for collection_name, schema in self.new_collections.items():
                try:
                    await self._create_collection(collection_name, schema, results)
                except Exception as e:
                    error_msg = f"Error creating collection {collection_name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Verify readonly collections exist
            await self._verify_readonly_collections(results)
            
            logger.info("✅ Clean schema implementation completed")
            return results
            
        except Exception as e:
            error_msg = f"Error in clean schema implementation: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            return results
    
    async def _drop_existing_collections(self, results: Dict[str, Any]):
        """Drop existing collections (except readonly ones)"""
        existing_collections = self.db.list_collection_names()
        
        for collection_name in existing_collections:
            if collection_name not in self.readonly_collections:
                try:
                    self.db.drop_collection(collection_name)
                    results['collections_dropped'].append(collection_name)
                    logger.info(f"Dropped collection: {collection_name}")
                except Exception as e:
                    error_msg = f"Error dropping collection {collection_name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
    
    async def _create_collection(self, collection_name: str, schema: Dict[str, Any], results: Dict[str, Any]):
        """Create a collection with schema validation and indexes"""
        try:
            # Create collection with validation
            collection = self.db.create_collection(
                collection_name,
                validator=schema['validator']
            )
            
            results['collections_created'].append(collection_name)
            logger.info(f"Created collection: {collection_name}")
            
            # Create indexes
            for index_spec in schema['indexes']:
                try:
                    keys = index_spec['keys']
                    options = index_spec.get('options', {})
                    
                    collection.create_index(keys, **options)
                    index_name = '_'.join([f"{field}_{direction}" for field, direction in keys])
                    results['indexes_created'].append(f"{collection_name}.{index_name}")
                    logger.info(f"Created index: {collection_name}.{index_name}")
                    
                except Exception as e:
                    error_msg = f"Error creating index for {collection_name}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
        except Exception as e:
            error_msg = f"Error creating collection {collection_name}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
    
    async def _verify_readonly_collections(self, results: Dict[str, Any]):
        """Verify that readonly collections exist"""
        existing_collections = self.db.list_collection_names()
        
        for collection_name in self.readonly_collections:
            if collection_name in existing_collections:
                logger.info(f"✅ Readonly collection exists: {collection_name}")
            else:
                error_msg = f"Warning: Readonly collection missing: {collection_name}"
                logger.warning(error_msg)
                results['errors'].append(error_msg)
    
    async def validate_schema(self) -> Dict[str, Any]:
        """
        Validate the clean schema implementation.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'collections_validated': [],
            'indexes_validated': [],
            'errors': [],
            'summary': {}
        }
        
        try:
            # Check collections exist
            existing_collections = self.db.list_collection_names()
            
            for collection_name in self.new_collections.keys():
                if collection_name in existing_collections:
                    validation_results['collections_validated'].append(collection_name)
                    
                    # Validate indexes
                    collection = self.db[collection_name]
                    indexes = collection.list_indexes()
                    
                    schema_indexes = self.new_collections[collection_name]['indexes']
                    for schema_index in schema_indexes:
                        index_found = False
                        for existing_index in indexes:
                            if existing_index['key'] == dict(schema_index['keys']):
                                validation_results['indexes_validated'].append(f"{collection_name}.{existing_index['name']}")
                                index_found = True
                                break
                        
                        if not index_found:
                            error_msg = f"Missing index for {collection_name}: {schema_index['keys']}"
                            validation_results['errors'].append(error_msg)
                else:
                    error_msg = f"Missing collection: {collection_name}"
                    validation_results['errors'].append(error_msg)
            
            # Check readonly collections
            for collection_name in self.readonly_collections:
                if collection_name in existing_collections:
                    validation_results['collections_validated'].append(f"{collection_name} (readonly)")
                else:
                    error_msg = f"Missing readonly collection: {collection_name}"
                    validation_results['errors'].append(error_msg)
            
            # Summary
            validation_results['summary'] = {
                'total_collections': len(existing_collections),
                'new_collections': len(self.new_collections),
                'readonly_collections': len(self.readonly_collections),
                'collections_validated': len(validation_results['collections_validated']),
                'indexes_validated': len(validation_results['indexes_validated']),
                'errors': len(validation_results['errors'])
            }
            
            logger.info("✅ Schema validation completed")
            return validation_results
            
        except Exception as e:
            error_msg = f"Error in schema validation: {str(e)}"
            logger.error(error_msg)
            validation_results['errors'].append(error_msg)
            return validation_results
    
    async def test_crud_operations(self) -> Dict[str, Any]:
        """
        Test basic CRUD operations on the new schema.
        
        Returns:
            Dictionary with test results
        """
        test_results = {
            'tests_passed': [],
            'tests_failed': [],
            'errors': []
        }
        
        try:
            # Test users collection
            await self._test_users_crud(test_results)
            
            # Test ships collection
            await self._test_ships_crud(test_results)
            
            # Test missions collection
            await self._test_missions_crud(test_results)
            
            # Test simulation_state collection
            await self._test_simulation_state_crud(test_results)
            
            # Test market_prices collection
            await self._test_market_prices_crud(test_results)
            
            logger.info("✅ CRUD operations testing completed")
            return test_results
            
        except Exception as e:
            error_msg = f"Error in CRUD testing: {str(e)}"
            logger.error(error_msg)
            test_results['errors'].append(error_msg)
            return test_results
    
    async def _test_users_crud(self, test_results: Dict[str, Any]):
        """Test users collection CRUD operations"""
        try:
            users_collection = self.db.users
            
            # Create test user
            test_user = {
                'username': 'testuser_schema',
                'company_name': 'Test Corp',
                'bank_balance': 1000000,
                'created_at': datetime.now(timezone.utc),
                'last_login': datetime.now(timezone.utc)
            }
            
            result = users_collection.insert_one(test_user)
            user_id = result.inserted_id
            test_results['tests_passed'].append('users.create')
            
            # Read test user
            found_user = users_collection.find_one({'_id': user_id})
            if found_user:
                test_results['tests_passed'].append('users.read')
            else:
                test_results['tests_failed'].append('users.read')
            
            # Update test user
            users_collection.update_one(
                {'_id': user_id},
                {'$set': {'bank_balance': 2000000}}
            )
            test_results['tests_passed'].append('users.update')
            
            # Delete test user
            users_collection.delete_one({'_id': user_id})
            test_results['tests_passed'].append('users.delete')
            
        except Exception as e:
            test_results['tests_failed'].append('users.crud')
            test_results['errors'].append(f"Users CRUD test failed: {str(e)}")
    
    async def _test_ships_crud(self, test_results: Dict[str, Any]):
        """Test ships collection CRUD operations"""
        try:
            ships_collection = self.db.ships
            
            # Create test ship
            test_ship = {
                'name': 'Test Ship',
                'user_id': ObjectId(),
                'capacity': 50000,
                'mining_power': 80,
                'shield': 90,
                'hull': 100,
                'location': 0.0,
                'status': 'available',
                'created_at': datetime.now(timezone.utc),
                'active': True
            }
            
            result = ships_collection.insert_one(test_ship)
            ship_id = result.inserted_id
            test_results['tests_passed'].append('ships.create')
            
            # Read test ship
            found_ship = ships_collection.find_one({'_id': ship_id})
            if found_ship:
                test_results['tests_passed'].append('ships.read')
            else:
                test_results['tests_failed'].append('ships.read')
            
            # Update test ship
            ships_collection.update_one(
                {'_id': ship_id},
                {'$set': {'status': 'mining'}}
            )
            test_results['tests_passed'].append('ships.update')
            
            # Delete test ship
            ships_collection.delete_one({'_id': ship_id})
            test_results['tests_passed'].append('ships.delete')
            
        except Exception as e:
            test_results['tests_failed'].append('ships.crud')
            test_results['errors'].append(f"Ships CRUD test failed: {str(e)}")
    
    async def _test_missions_crud(self, test_results: Dict[str, Any]):
        """Test missions collection CRUD operations"""
        try:
            missions_collection = self.db.missions
            
            # Create test mission
            test_mission = {
                'name': 'Test Mission',
                'user_id': ObjectId(),
                'ship_id': ObjectId(),
                'asteroid_name': 'Test Asteroid',
                'status': 'planned',
                'travel_days': 30,
                'mining_days': 10,
                'days_elapsed': 0,
                'ship_location': 0.0,
                'cargo': [],
                'total_yield_kg': 0,
                'budget': 1000000,
                'cost': 0,
                'revenue': 0,
                'profit': 0,
                'created_at': datetime.now(timezone.utc)
            }
            
            result = missions_collection.insert_one(test_mission)
            mission_id = result.inserted_id
            test_results['tests_passed'].append('missions.create')
            
            # Read test mission
            found_mission = missions_collection.find_one({'_id': mission_id})
            if found_mission:
                test_results['tests_passed'].append('missions.read')
            else:
                test_results['tests_failed'].append('missions.read')
            
            # Update test mission
            missions_collection.update_one(
                {'_id': mission_id},
                {'$set': {'status': 'in_progress'}}
            )
            test_results['tests_passed'].append('missions.update')
            
            # Delete test mission
            missions_collection.delete_one({'_id': mission_id})
            test_results['tests_passed'].append('missions.delete')
            
        except Exception as e:
            test_results['tests_failed'].append('missions.crud')
            test_results['errors'].append(f"Missions CRUD test failed: {str(e)}")
    
    async def _test_simulation_state_crud(self, test_results: Dict[str, Any]):
        """Test simulation_state collection CRUD operations"""
        try:
            simulation_collection = self.db.simulation_state
            
            # Create test simulation state
            test_state = {
                'user_id': ObjectId(),
                'current_day': 1,
                'is_running': True,
                'active_missions': [],
                'last_updated': datetime.now(timezone.utc)
            }
            
            result = simulation_collection.insert_one(test_state)
            state_id = result.inserted_id
            test_results['tests_passed'].append('simulation_state.create')
            
            # Read test state
            found_state = simulation_collection.find_one({'_id': state_id})
            if found_state:
                test_results['tests_passed'].append('simulation_state.read')
            else:
                test_results['tests_failed'].append('simulation_state.read')
            
            # Update test state
            simulation_collection.update_one(
                {'_id': state_id},
                {'$set': {'current_day': 2}}
            )
            test_results['tests_passed'].append('simulation_state.update')
            
            # Delete test state
            simulation_collection.delete_one({'_id': state_id})
            test_results['tests_passed'].append('simulation_state.delete')
            
        except Exception as e:
            test_results['tests_failed'].append('simulation_state.crud')
            test_results['errors'].append(f"Simulation state CRUD test failed: {str(e)}")
    
    async def _test_market_prices_crud(self, test_results: Dict[str, Any]):
        """Test market_prices collection CRUD operations"""
        try:
            prices_collection = self.db.market_prices
            
            # Create test price
            test_price = {
                'element': 'TestElement',
                'price_per_kg': 1000.0,
                'last_updated': datetime.now(timezone.utc)
            }
            
            result = prices_collection.insert_one(test_price)
            price_id = result.inserted_id
            test_results['tests_passed'].append('market_prices.create')
            
            # Read test price
            found_price = prices_collection.find_one({'_id': price_id})
            if found_price:
                test_results['tests_passed'].append('market_prices.read')
            else:
                test_results['tests_failed'].append('market_prices.read')
            
            # Update test price
            prices_collection.update_one(
                {'_id': price_id},
                {'$set': {'price_per_kg': 1500.0}}
            )
            test_results['tests_passed'].append('market_prices.update')
            
            # Delete test price
            prices_collection.delete_one({'_id': price_id})
            test_results['tests_passed'].append('market_prices.delete')
            
        except Exception as e:
            test_results['tests_failed'].append('market_prices.crud')
            test_results['errors'].append(f"Market prices CRUD test failed: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Create service instance
        schema_service = CleanSchemaService()
        
        print("🚀 AstroSurge Clean Schema Implementation Service")
        print("=" * 60)
        
        # Create clean schema
        print("\n📊 Creating Clean Schema...")
        creation_results = await schema_service.create_clean_schema(drop_existing=True)
        
        print(f"\n✅ Collections Created: {len(creation_results['collections_created'])}")
        for collection in creation_results['collections_created']:
            print(f"  - {collection}")
        
        print(f"\n✅ Indexes Created: {len(creation_results['indexes_created'])}")
        for index in creation_results['indexes_created']:
            print(f"  - {index}")
        
        if creation_results['errors']:
            print(f"\n❌ Errors: {len(creation_results['errors'])}")
            for error in creation_results['errors']:
                print(f"  - {error}")
        
        # Validate schema
        print(f"\n🔍 Validating Schema...")
        validation_results = await schema_service.validate_schema()
        
        print(f"\n✅ Collections Validated: {validation_results['summary']['collections_validated']}")
        print(f"✅ Indexes Validated: {validation_results['summary']['indexes_validated']}")
        
        if validation_results['errors']:
            print(f"\n❌ Validation Errors: {len(validation_results['errors'])}")
            for error in validation_results['errors']:
                print(f"  - {error}")
        
        # Test CRUD operations
        print(f"\n🧪 Testing CRUD Operations...")
        crud_results = await schema_service.test_crud_operations()
        
        print(f"\n✅ Tests Passed: {len(crud_results['tests_passed'])}")
        for test in crud_results['tests_passed']:
            print(f"  - {test}")
        
        if crud_results['tests_failed']:
            print(f"\n❌ Tests Failed: {len(crud_results['tests_failed'])}")
            for test in crud_results['tests_failed']:
                print(f"  - {test}")
        
        print(f"\n🎯 Clean Schema Implementation Complete!")
        print(f"✅ New collections created with validation")
        print(f"✅ Performance indexes implemented")
        print(f"✅ Readonly collections preserved")
        print(f"✅ CRUD operations tested")
    
    # Run the example
    asyncio.run(main())
