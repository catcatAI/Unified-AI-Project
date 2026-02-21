import sys
import os
import asyncio
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.execution.execution_monitor import ExecutionMonitor, ExecutionStatus

class TestSecurityHardening(unittest.TestCase):
    def setUp(self):
        self.monitor = ExecutionMonitor()

    def test_command_injection_mitigation(self):
        # Malicious command attempting to create a file via injection
        # On Windows: whoami & echo injected > injected.txt
        
        test_file = "injected_test.txt"
        if os.path.exists(test_file):
            os.remove(test_file)
            
        # whoami is an executable (whoami.exe), so it works with shell=False list execution
        malicious_command = ["whoami", "&", "echo", "injected", ">", test_file]
        
        result = self.monitor.execute_command(malicious_command)
        
        # The file should NOT exist if injection failed
        self.assertFalse(os.path.exists(test_file), "Vulnerability: Command injection succeeded!")
        
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_string_command_auto_split(self):
        # Test that passing a string automatically gets split and run safely
        # Use an actual executable
        result = self.monitor.execute_command("whoami")
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

if __name__ == "__main__":
    unittest.main()
