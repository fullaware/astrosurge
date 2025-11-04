"""
Tests for Mining Operations Service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.mining_operations import MiningOperationsService


class TestMiningOperationsService:
    """Test suite for MiningOperationsService"""
    
    @pytest.fixture
    def mock_mongodb(self):
        """Mock MongoDB connection"""
        with patch('src.services.mining_operations.MongoClient') as mock_client:
            mock_db = Mock()
            mock_elements = Mock()
            mock_db.elements = mock_elements
            mock_client.return_value = Mock(
                admin=Mock(command=Mock(return_value=True)),
                asteroids=mock_db
            )
            yield {'client': mock_client, 'db': mock_db, 'elements': mock_elements}
    
    @pytest.fixture
    def mining_service(self, mock_mongodb):
        """Create mining service with mocked MongoDB"""
        with patch.dict('os.environ', {'MONGODB_URI': 'mongodb://localhost:27017/test'}):
            service = MiningOperationsService()
            service.db = mock_mongodb['db']
            service.elements_collection = mock_mongodb['elements']
            return service
    
    def test_get_asteroid_class_c_type(self, mining_service):
        """Test getting asteroid class for C-type"""
        asteroid = {'class': 'C', 'name': 'Ceres'}
        assert mining_service.get_asteroid_class(asteroid) == 'C'
    
    def test_get_asteroid_class_s_type(self, mining_service):
        """Test getting asteroid class for S-type"""
        asteroid = {'class': 'S', 'name': 'Vesta'}
        assert mining_service.get_asteroid_class(asteroid) == 'S'
    
    def test_get_asteroid_class_m_type(self, mining_service):
        """Test getting asteroid class for M-type"""
        asteroid = {'class': 'M', 'name': 'Juno'}
        assert mining_service.get_asteroid_class(asteroid) == 'M'
    
    def test_get_asteroid_class_default(self, mining_service):
        """Test default class when unknown"""
        asteroid = {'class': 'X', 'name': 'Unknown'}
        assert mining_service.get_asteroid_class(asteroid) == 'C'
    
    def test_determine_ore_grade_c_type(self, mining_service):
        """Test ore grade determination for C-type asteroid"""
        grade_class, grade_percentage = mining_service.determine_ore_grade('C')
        assert grade_class in ['low', 'medium', 'high', 'premium']
        assert 0.01 <= grade_percentage <= 0.35
    
    def test_determine_ore_grade_m_type(self, mining_service):
        """Test ore grade determination for M-type asteroid (should favor higher grades)"""
        grade_class, grade_percentage = mining_service.determine_ore_grade('M')
        assert grade_class in ['low', 'medium', 'high', 'premium']
        assert 0.01 <= grade_percentage <= 0.35
    
    def test_calculate_mining_yield_basic(self, mining_service):
        """Test basic mining yield calculation"""
        asteroid = {
            'class': 'M',
            'name': 'Test Asteroid',
            'elements': [
                {'name': 'Gold', 'mass_kg': 1000000},
                {'name': 'Platinum', 'mass_kg': 500000},
                {'name': 'Silver', 'mass_kg': 200000}
            ]
        }
        
        yield_data = mining_service.calculate_mining_yield(asteroid, mining_days=10)
        
        assert 'total_ore_mined' in yield_data
        assert 'effective_yield' in yield_data
        assert 'ore_grade' in yield_data
        assert 'grade_classification' in yield_data
        assert 'commodity_yield' in yield_data
        assert yield_data['asteroid_class'] == 'M'
    
    def test_calculate_mining_yield_no_elements(self, mining_service):
        """Test mining yield with no elements"""
        asteroid = {
            'class': 'C',
            'name': 'Empty Asteroid',
            'elements': []
        }
        
        yield_data = mining_service.calculate_mining_yield(asteroid, mining_days=10)
        
        assert yield_data['total_ore_mined'] == 0
        assert yield_data['commodity_yield'] == {}
    
    def test_calculate_daily_mining_output(self, mining_service):
        """Test daily mining output calculation"""
        asteroid = {
            'class': 'S',
            'elements': [
                {'name': 'Gold', 'mass_kg': 1000000},
                {'name': 'Platinum', 'mass_kg': 500000}
            ]
        }
        
        current_cargo = {'Gold': 1000, 'Platinum': 500}
        daily_output = mining_service.calculate_daily_mining_output(
            asteroid, current_cargo, ship_capacity=50000
        )
        
        assert isinstance(daily_output, dict)
        # Should have some output if capacity allows
        if sum(current_cargo.values()) < 50000:
            assert len(daily_output) > 0
    
    def test_calculate_daily_mining_output_full_ship(self, mining_service):
        """Test daily mining output when ship is full"""
        asteroid = {
            'class': 'C',
            'elements': [{'name': 'Gold', 'mass_kg': 1000000}]
        }
        
        current_cargo = {'Gold': 50000}  # Ship is full
        daily_output = mining_service.calculate_daily_mining_output(
            asteroid, current_cargo, ship_capacity=50000
        )
        
        assert daily_output == {}
    
    @pytest.mark.asyncio
    async def test_get_element_class_probabilities(self, mining_service):
        """Test getting element class probabilities"""
        # Mock element document
        mock_element = {
            'name': 'Platinum',
            'classes': [
                {'class': 'C', 'percentage': 30},
                {'class': 'S', 'percentage': 50},
                {'class': 'M', 'percentage': 20}
            ]
        }
        
        mining_service.elements_collection.find_one = Mock(return_value=mock_element)
        
        probs = await mining_service.get_element_class_probabilities('Platinum')
        
        assert 'C' in probs
        assert 'S' in probs
        assert 'M' in probs
        assert abs(sum(probs.values()) - 1.0) < 0.01  # Should sum to ~1.0
    
    @pytest.mark.asyncio
    async def test_get_element_class_probabilities_not_found(self, mining_service):
        """Test getting probabilities for non-existent element"""
        mining_service.elements_collection.find_one = Mock(return_value=None)
        
        probs = await mining_service.get_element_class_probabilities('Unobtanium')
        
        # Should return default distribution
        assert 'C' in probs
        assert 'S' in probs
        assert 'M' in probs
    
    @pytest.mark.asyncio
    async def test_get_mining_analysis(self, mining_service):
        """Test getting comprehensive mining analysis"""
        # Mock asteroid
        mock_asteroid = {
            '_id': 'test_id',
            'name': 'Test Asteroid',
            'class': 'M',
            'elements': [
                {'name': 'Gold', 'mass_kg': 1000000},
                {'name': 'Platinum', 'mass_kg': 500000}
            ]
        }
        
        # Mock MongoDB find
        mock_find_one = Mock(return_value=mock_asteroid)
        mining_service.db.asteroids.find_one = mock_find_one
        
        # Mock element probabilities
        mock_element = {
            'name': 'Gold',
            'classes': [
                {'class': 'C', 'percentage': 30},
                {'class': 'S', 'percentage': 50},
                {'class': 'M', 'percentage': 20}
            ]
        }
        mining_service.elements_collection.find_one = Mock(return_value=mock_element)
        
        analysis = await mining_service.get_mining_analysis('test_id')
        
        assert 'asteroid_name' in analysis
        assert 'asteroid_class' in analysis
        assert 'ore_grade_distribution' in analysis
        assert 'element_analysis' in analysis
    
    def test_mining_efficiency_by_grade(self, mining_service):
        """Test mining efficiency values"""
        assert mining_service.mining_efficiency['low'] < mining_service.mining_efficiency['medium']
        assert mining_service.mining_efficiency['medium'] < mining_service.mining_efficiency['high']
        assert mining_service.mining_efficiency['high'] < mining_service.mining_efficiency['premium']
    
    def test_ore_grade_distributions(self, mining_service):
        """Test that ore grade distributions sum to 1.0"""
        for asteroid_class in ['C', 'S', 'M']:
            distribution = mining_service.ore_grade_distributions[asteroid_class]
            total = sum(distribution.values())
            assert abs(total - 1.0) < 0.01, f"Distribution for {asteroid_class} doesn't sum to 1.0"


