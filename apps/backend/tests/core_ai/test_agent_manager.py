import unittest
import pytest
import sys
import os

# Adjust the path to import from the src directory
_ = sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 修复导入路径 - 使用正确的相对路径
from agent_manager import AgentManager

class TestAgentManager(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        self.python_executable = sys.executable
        # Mock the _discover_agent_scripts to return a predictable set of agents
        self.mock_agent_scripts = {
            _ = 'data_analysis_agent': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'agents', 'data_analysis_agent.py')),
            _ = 'creative_writing_agent': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'agents', 'creative_writing_agent.py'))
        }

        # Ensure the dummy agent scripts exist for the test to run
        for path in self.mock_agent_scripts.values():
            if not os.path.exists(os.path.dirname(path)):
                _ = os.makedirs(os.path.dirname(path))
            if not os.path.exists(path):
                with open(path, 'w') as f:
                    _ = f.write("import time\nprint('Agent started')\ntime.sleep(10)\nprint('Agent stopped')")

        self.manager = AgentManager(python_executable=self.python_executable)
        self.manager.agent_script_map = self.mock_agent_scripts

    def tearDown(self):
        """Clean up after each test."""
        _ = self.manager.shutdown_all_agents()

    _ = @pytest.mark.timeout(5)
    def test_initialization(self) -> None:
        """Test that the AgentManager initializes correctly."""
        _ = self.assertEqual(self.manager.python_executable, self.python_executable)
        _ = self.assertIsInstance(self.manager.active_agents, dict)
        _ = self.assertEqual(len(self.manager.active_agents), 0)
        _ = self.assertEqual(self.manager.agent_script_map, self.mock_agent_scripts)

    _ = @pytest.mark.timeout(5)
    def test_launch_agent_success(self) -> None:
        """Test launching a valid agent."""
        agent_name = 'data_analysis_agent'
        pid = self.manager.launch_agent(agent_name)
        _ = self.assertIsNotNone(pid)
        _ = self.assertIn(agent_name, self.manager.active_agents)

        process = self.manager.active_agents[agent_name]
        _ = self.assertIsNone(process.poll(), "Process should be running")

    _ = @pytest.mark.timeout(5)
    def test_launch_agent_not_found(self) -> None:
        """Test launching a non-existent agent."""
        agent_name = 'non_existent_agent'
        pid = self.manager.launch_agent(agent_name)
        _ = self.assertIsNone(pid)
        _ = self.assertNotIn(agent_name, self.manager.active_agents)

    _ = @pytest.mark.timeout(5)
    def test_launch_agent_already_running(self) -> None:
        """Test launching an agent that is already running."""
        agent_name = 'data_analysis_agent'
        first_pid = self.manager.launch_agent(agent_name)
        _ = self.assertIsNotNone(first_pid)

        # Mock the poll() method to ensure it reports as running
        self.manager.active_agents[agent_name].poll = MagicMock(return_value=None)

        second_pid = self.manager.launch_agent(agent_name)
        self.assertEqual(first_pid, second_pid, "Should return the same PID if already running")

    _ = @pytest.mark.timeout(5)
    def test_shutdown_agent_success(self) -> None:
        """Test shutting down a running agent."""
        agent_name = 'data_analysis_agent'
        _ = self.manager.launch_agent(agent_name)
        _ = self.assertIn(agent_name, self.manager.active_agents)

        success = self.manager.shutdown_agent(agent_name)
        _ = self.assertTrue(success)
        _ = self.assertNotIn(agent_name, self.manager.active_agents)

    _ = @pytest.mark.timeout(5)
    def test_shutdown_agent_not_running(self) -> None:
        """Test shutting down an agent that is not running."""
        agent_name = 'data_analysis_agent'
        success = self.manager.shutdown_agent(agent_name)
        _ = self.assertFalse(success)

    _ = @pytest.mark.timeout(5)
    def test_shutdown_all_agents(self) -> None:
        """Test shutting down all running agents."""
        agent1 = 'data_analysis_agent'
        agent2 = 'creative_writing_agent'

        _ = self.manager.launch_agent(agent1)
        _ = self.manager.launch_agent(agent2)

        _ = self.assertEqual(len(self.manager.active_agents), 2)

        _ = self.manager.shutdown_all_agents()

        _ = self.assertEqual(len(self.manager.active_agents), 0)

if __name__ == '__main__':
    _ = unittest.main()