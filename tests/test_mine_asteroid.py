import unittest
from unittest.mock import patch, MagicMock
from bson import Int64
from mine_asteroid import mine_hourly, update_mined_asteroid

class TestMineAsteroid(unittest.TestCase):

    def test_mine_hourly(self):
        asteroid = {
            'elements': [{'name': 'gold', 'mass_kg': 100}],
            'mass': 100
        }
        result_asteroid, elements_mined = mine_hourly(asteroid, 50, '12345')
        self.assertEqual(result_asteroid['mass'], 50)
        self.assertEqual(elements_mined, [{'name': 'gold', 'mass_kg': 50}])

    @patch('mine_asteroid.mined_asteroids_collection')
    def test_update_mined_asteroid(self, mock_mined_asteroids_collection):
        asteroid = {
            'full_name': 'Test Asteroid',
            'elements': [{'name': 'gold', 'mass_kg': 50}],
            'mass': 50,
            'uid': '12345'
        }
        update_mined_asteroid(asteroid, 50)
        mock_mined_asteroids_collection.update_one.assert_called()

if __name__ == '__main__':
    unittest.main()