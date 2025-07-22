import unittest
import pytest
import os
import sys
from datetime import datetime, timedelta

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")) #
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core_ai.time_system import TimeSystem
from unittest.mock import patch # For mocking datetime

class TestTimeSystem(unittest.TestCase):

    def setUp(self):
        self.time_sys = TimeSystem()

    @pytest.mark.timeout(5)
    def test_01_initialization(self):
        self.assertIsNotNone(self.time_sys)
        print("TestTimeSystem.test_01_initialization PASSED")

    @pytest.mark.timeout(5)
    def test_02_get_current_time(self):
        current_time = self.time_sys.get_current_time()
        self.assertIsInstance(current_time, datetime)
        # Check if it's close to now
        self.assertLess(abs((datetime.now() - current_time).total_seconds()), 1)
        print("TestTimeSystem.test_02_get_current_time PASSED")

    @pytest.mark.timeout(5)
    def test_03_get_formatted_current_time(self):
        formatted_time = self.time_sys.get_formatted_current_time()
        # Default format is "%Y-%m-%d %H:%M:%S"
        # Try to parse it back to ensure format is correct
        try:
            datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S")
            parsed_ok = True
        except ValueError:
            parsed_ok = False
        self.assertTrue(parsed_ok)
        print("TestTimeSystem.test_03_get_formatted_current_time PASSED")

    @pytest.mark.timeout(5)
    def test_04_set_reminder_placeholder(self):
        # Placeholder just returns True
        result = self.time_sys.set_reminder("in 5 minutes", "test reminder")
        self.assertTrue(result)
        print("TestTimeSystem.test_04_set_reminder_placeholder PASSED")

    @pytest.mark.timeout(5)
    def test_05_check_due_reminders_placeholder(self):
        # Placeholder just returns empty list
        reminders = self.time_sys.check_due_reminders()
        self.assertEqual(reminders, [])
        print("TestTimeSystem.test_05_check_due_reminders_placeholder PASSED")

    @pytest.mark.timeout(5)
    def test_06_get_time_of_day_segment(self):
        print("\nRunning test_06_get_time_of_day_segment...")
        test_cases = [
            (datetime(2023, 1, 1, 3, 0, 0), "night"),    # 3 AM
            (datetime(2023, 1, 1, 5, 0, 0), "morning"),  # 5 AM
            (datetime(2023, 1, 1, 10, 30, 0), "morning"),# 10:30 AM
            (datetime(2023, 1, 1, 12, 0, 0), "afternoon"),# 12 PM
            (datetime(2023, 1, 1, 17, 59, 0), "afternoon"),# 5:59 PM
            (datetime(2023, 1, 1, 18, 0, 0), "evening"),  # 6 PM
            (datetime(2023, 1, 1, 21, 0, 0), "evening"),  # 9 PM
            (datetime(2023, 1, 1, 22, 0, 0), "night"),    # 10 PM
            (datetime(2023, 1, 1, 0, 0, 0), "night")     # Midnight
        ]

        for mock_time, expected_segment in test_cases:
            # Patch TimeSystem's get_current_time to control the time it sees
            # Or, if TimeSystem directly calls datetime.datetime.now(), patch that.
            # TimeSystem.get_current_time() calls datetime.datetime.now() if no override.
            # So we patch datetime.datetime.now within the scope of time_system module.
            with patch('core_ai.time_system.datetime') as mock_datetime_module:
                mock_datetime_module.datetime.now.return_value = mock_time
                segment = self.time_sys.get_time_of_day_segment()
                self.assertEqual(segment, expected_segment, f"Failed for time {mock_time.hour}h. Got {segment}, expected {expected_segment}")

        print("TestTimeSystem.test_06_get_time_of_day_segment PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)
