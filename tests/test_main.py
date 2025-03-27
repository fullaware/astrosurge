import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from main import manage_missions, manage_mining

# filepath: /home/fullaware/projects/beryl/test_main.py

class TestMain(unittest.TestCase):

    @patch("main.get_missions")
    @patch("main.execute_mission")
    @patch("main.deposit_cargo")
    def test_manage_missions_execute(self, mock_deposit_cargo, mock_execute_mission, mock_get_missions):
        user_id = ObjectId()
        mock_get_missions.return_value = [
            MagicMock(id=ObjectId(), asteroid_name="Asteroid A", status=MagicMock(name="FUNDED")),
        ]
        mock_execute_mission.return_value = None
        mock_deposit_cargo.return_value = None

        with patch("builtins.input", side_effect=["4", "1"]):  # Execute mission, select first mission
            manage_missions(user_id)

        mock_execute_mission.assert_called_once()
        mock_deposit_cargo.assert_called_once()

    @patch("main.get_ship")
    @patch("main.get_current_cargo_mass")
    @patch("main.mine_hourly")
    @patch("main.update_ship_cargo")
    def test_manage_mining(self, mock_update_ship_cargo, mock_mine_hourly, mock_get_current_cargo_mass, mock_get_ship):
        user_id = ObjectId()
        ship_id = ObjectId()
        asteroid_name = "Asteroid B"

        mock_get_ship.return_value = {"capacity": 50000, "mining_power": 100}
        mock_get_current_cargo_mass.return_value = 1000
        mock_mine_hourly.return_value = ([{"name": "gold", "mass_kg": 50}], False)
        mock_update_ship_cargo.return_value = None

        manage_mining(user_id, ship_id, asteroid_name)

        mock_mine_hourly.assert_called_once_with(
            asteroid_name=asteroid_name,
            extraction_rate=100,
            user_id=user_id,
            ship_capacity=50000,
            current_cargo_mass=1000,
        )
        mock_update_ship_cargo.assert_called_once_with(ship_id, [{"name": "gold", "mass_kg": 50}])

    @patch("main.get_missions")
    def test_manage_missions_no_missions(self, mock_get_missions):
        user_id = ObjectId()
        mock_get_missions.return_value = []

        with patch("builtins.input", side_effect=["4"]):  # Execute mission
            manage_missions(user_id)

        mock_get_missions.assert_called_once()

    @patch("main.mine_hourly")
    def test_manage_mining_no_elements(self, mock_mine_hourly):
        user_id = ObjectId()
        ship_id = ObjectId()
        asteroid_name = "Asteroid C"

        mock_mine_hourly.return_value = ([], False)

        with patch("main.update_ship_cargo") as mock_update_ship_cargo:
            manage_mining(user_id, ship_id, asteroid_name)

        mock_mine_hourly.assert_called_once()
        mock_update_ship_cargo.assert_not_called()

if __name__ == "__main__":
    unittest.main()