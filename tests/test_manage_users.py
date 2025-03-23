import unittest
from unittest.mock import patch, MagicMock
from bson import Int64
from manage_users import get_user, auth_user, update_users

class TestManageUsers(unittest.TestCase):

    @patch('manage_users.users_collection')
    def test_get_user_existing(self, mock_users_collection):
        mock_users_collection.find_one.return_value = {'uid': '12345', 'name': 'Alice'}
        uid = get_user('Alice', 'password')
        self.assertEqual(uid, '12345')

    @patch('manage_users.users_collection')
    def test_get_user_new(self, mock_users_collection):
        mock_users_collection.find_one.return_value = None
        mock_users_collection.insert_one = MagicMock()
        uid = get_user('Bob', 'password')
        self.assertIsNotNone(uid)
        mock_users_collection.insert_one.assert_called_once()

    @patch('manage_users.users_collection')
    def test_auth_user_success(self, mock_users_collection):
        mock_users_collection.find_one.return_value = {'uid': '12345', 'password': 'hashed_password'}
        with patch('werkzeug.security.check_password_hash', return_value=True):
            result = auth_user('12345', 'password')
            self.assertTrue(result)

    @patch('manage_users.users_collection')
    def test_auth_user_failure(self, mock_users_collection):
        mock_users_collection.find_one.return_value = {'uid': '12345', 'password': 'hashed_password'}
        with patch('werkzeug.security.check_password_hash', return_value=False):
            result = auth_user('12345', 'password')
            self.assertFalse(result)

    @patch('manage_users.users_collection')
    @patch('manage_users.assess_element_values', return_value=Int64(100))
    def test_update_users(self, mock_assess_element_values, mock_users_collection):
        elements = [{'name': 'gold', 'mass_kg': 10}]
        update_users('12345', elements)
        mock_users_collection.update_one.assert_called()

if __name__ == '__main__':
    unittest.main()