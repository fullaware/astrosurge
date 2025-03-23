import unittest
from unittest.mock import patch, MagicMock
from bson import Int64
from manage_elements import select_elements, find_elements_use, sell_elements

class TestManageElements(unittest.TestCase):

    def test_select_elements_default(self):
        result = select_elements()
        self.assertEqual(result, ["gold", "silver", "platinum", "copper", "palladium"])

    def test_select_elements_user_choice(self):
        result = select_elements(["gold", "iron", "platinum"])
        self.assertEqual(result, ["gold", "platinum"])

    @patch('manage_elements.elements_collection')
    def test_find_elements_use(self, mock_elements_collection):
        mock_elements_collection.find_one.return_value = {'name': 'gold', 'uses': ['jewelry']}
        elements = [{'name': 'gold', 'mass_kg': 10}]
        result = find_elements_use(elements, 10)
        self.assertEqual(result, [{'use': 'jewelry', 'total_mass_kg': 10}])

    def test_sell_elements(self):
        elements = [{'name': 'gold', 'mass_kg': 10}]
        commodity_values = {'gold': 50}
        result = sell_elements(50, elements, commodity_values)
        self.assertEqual(result, {'gold': Int64(250)})

if __name__ == '__main__':
    unittest.main()