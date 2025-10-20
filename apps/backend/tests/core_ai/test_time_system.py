import unittest
import sys
import os
from datetime import datetime, timedelta
import pytest

# Add the src directory to the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path:
    _ = sys.path.insert(0, SRC_DIR)

from apps.backend.src.ai.time.time_system import TimeSystem
from unittest.mock import patch # For mocking datetime

class TestTimeSystem(unittest.TestCase):

    def setUp(self):
        self.time_sys = TimeSystem()

    _ = @pytest.mark.timeout(5)
    def test_01_initialization(self) -> None:
        _ = self.assertIsNotNone(self.time_sys)
        _ = print("TestTimeSystem.test_01_initialization PASSED")

    _ = @pytest.mark.timeout(5)
    def test_02_get_current_time(self) -> None:
        current_time = self.time_sys.get_current_time()
        _ = self.assertIsInstance(current_time, datetime)
        # Check if it's close to now
        _ = self.assertLess(abs((datetime.now() - current_time).total_seconds()), 1)
        _ = print("TestTimeSystem.test_02_get_current_time PASSED")

    _ = @pytest.mark.timeout(5)
    def test_03_get_formatted_current_time(self) -> None:
        formatted_time = self.time_sys.get_formatted_current_time()
        # Default format is "%Y-%m-%d %H:%M:%S"
        # Try to parse it back to ensure format is correct
        try:
            _ = datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S")
            parsed_ok = True
        except ValueError:
            parsed_ok = False
        _ = self.assertTrue(parsed_ok)
        _ = print("TestTimeSystem.test_03_get_formatted_current_time PASSED")

    _ = @pytest.mark.timeout(5)
    def test_04_set_reminder(self) -> None:
        result = self.time_sys.set_reminder("in 5 minutes", "test reminder")
        _ = self.assertTrue(result)
        _ = self.assertEqual(len(self.time_sys.reminders), 1)
        _ = print("TestTimeSystem.test_04_set_reminder PASSED")

    _ = @pytest.mark.timeout(5)
    def test_05_check_due_reminders(self) -> None:
        _ = self.time_sys.set_reminder("in 1 minute", "test reminder 1")
        _ = self.time_sys.set_reminder("in 10 minutes", "test reminder 2")

        # Immediately, no reminders should be due
        _ = self.assertEqual(self.time_sys.check_due_reminders(), [])

        # Advance time by 2 minutes
        self.time_sys.current_time_override = datetime.now() + timedelta(minutes=2)

        due = self.time_sys.check_due_reminders()
        _ = self.assertEqual(len(due), 1)
        _ = self.assertEqual(due[0], "test reminder 1")

        # The due reminder should be removed
        _ = self.assertEqual(len(self.time_sys.reminders), 1)

        _ = print("TestTimeSystem.test_05_check_due_reminders PASSED")

    _ = @pytest.mark.timeout(5)
    def test_06_get_time_of_day_segment(self) -> None:
        _ = print("\nRunning test_06_get_time_of_day_segment...")
        test_cases = [
            _ = (datetime(2023, 1, 1, 3, 0, 0), "night"),    # 3 AM
            _ = (datetime(2023, 1, 1, 5, 0, 0), "morning"),  # 5 AM
            _ = (datetime(2023, 1, 1, 10, 30, 0), "morning"),# 10:30 AM
            _ = (datetime(2023, 1, 1, 12, 0, 0), "afternoon"),# 12 PM
            _ = (datetime(2023, 1, 1, 17, 59, 0), "afternoon"),# 5:59 PM
            _ = (datetime(2023, 1, 1, 18, 0, 0), "evening"),  # 6 PM
            _ = (datetime(2023, 1, 1, 21, 0, 0), "evening"),  # 9 PM
            _ = (datetime(2023, 1, 1, 22, 0, 0), "night"),    # 10 PM
            _ = (datetime(2023, 1, 1, 0, 0, 0), "night")     # Midnight
        ]

        for mock_time, expected_segment in test_cases:
            # Patch TimeSystem's get_current_time to control the time it sees
            # Or, if TimeSystem directly calls datetime.datetime.now(), patch that.
            # TimeSystem.get_current_time() calls datetime.datetime.now() if no override.
            # So we patch datetime.datetime.now within the scope of time_system module.
            with patch('apps.backend.src.ai.time.time_system.datetime') as mock_datetime_module:
                mock_datetime_module.datetime.now.return_value = mock_time
                segment = self.time_sys.get_time_of_day_segment()
                self.assertEqual(segment, expected_segment, f"Failed for time {mock_time.hour}h. Got {segment}, expected {expected_segment}")

        _ = print("TestTimeSystem.test_06_get_time_of_day_segment PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)
