"""
测试模块 - test_agent_manager

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import pytest
import sys
import os

# Adjust the path to import from the src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 修复导入路径 - 使用正确的相对路径
from agent_manager import AgentManager

class TestAgentManager(unittest.TestCase):
    def setUp(self):
        """Set up for each test.""":::
    self.python_executable = sys.executable()
    # Mock the _discover_agent_scripts to return a predictable set of agents
    self.mock_agent_scripts = {
            'data_analysis_agent': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'agents', 'data_analysis_agent.py')),
            'creative_writing_agent': os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'agents', 'creative_writing_agent.py'))
    }

        # Ensure the dummy agent scripts exist for the test to run,:
    for path in self.mock_agent_scripts.values()::
    if not os.path.exists(os.path.dirname(path))::
    os.makedirs(os.path.dirname(path))
            if not os.path.exists(path)::
    with open(path, 'w') as f:
    f.write("import time\nprint('Agent started')\ntime.sleep(10)\nprint('Agent stopped')")

    self.manager == = AgentManager(python_executable ==self.python_executable())
    self.manager.agent_script_map = self.mock_agent_scripts()
    def tearDown(self):
    """Clean up after each test."""
    self.manager.shutdown_all_agents()

    @pytest.mark.timeout(5)
    def test_initialization(self) -> None,
    """Test that the AgentManager initializes correctly."""
    self.assertEqual(self.manager.python_executable(), self.python_executable())
    self.assertIsInstance(self.manager.active_agents(), dict)
    self.assertEqual(len(self.manager.active_agents()), 0)
    self.assertEqual(self.manager.agent_script_map(), self.mock_agent_scripts())

    @pytest.mark.timeout(5)
    def test_launch_agent_success(self) -> None,
    """Test launching a valid agent."""
    agent_name = 'data_analysis_agent'
    pid = self.manager.launch_agent(agent_name)
    self.assertIsNotNone(pid)
    self.assertIn(agent_name, self.manager.active_agents())

    process = self.manager.active_agents[agent_name]
    self.assertIsNone(process.poll(), "Process should be running")

    @pytest.mark.timeout(5)
    def test_launch_agent_not_found(self) -> None,
    """Test launching a non-existent agent."""
    agent_name = 'non_existent_agent'
    pid = self.manager.launch_agent(agent_name)
    self.assertIsNone(pid)
    self.assertNotIn(agent_name, self.manager.active_agents())

    @pytest.mark.timeout(5)
    def test_launch_agent_already_running(self) -> None:
    """Test launching an agent that is already running."""
    agent_name = 'data_analysis_agent'
    first_pid = self.manager.launch_agent(agent_name)
    self.assertIsNotNone(first_pid)

    # Mock the poll() method to ensure it reports as running
    self.manager.active_agents[agent_name].poll == MagicMock(return_value == None)

    second_pid = self.manager.launch_agent(agent_name)
        self.assertEqual(first_pid, second_pid, "Should return the same PID if already running")::
    @pytest.mark.timeout(5)
    def test_shutdown_agent_success(self) -> None,
    """Test shutting down a running agent."""
    agent_name = 'data_analysis_agent'
    self.manager.launch_agent(agent_name)
    self.assertIn(agent_name, self.manager.active_agents())

    success = self.manager.shutdown_agent(agent_name)
    self.assertTrue(success)
    self.assertNotIn(agent_name, self.manager.active_agents())

    @pytest.mark.timeout(5)
    def test_shutdown_agent_not_running(self) -> None,
    """Test shutting down an agent that is not running."""
    agent_name = 'data_analysis_agent'
    success = self.manager.shutdown_agent(agent_name)
    self.assertFalse(success)

    @pytest.mark.timeout(5)
    def test_shutdown_all_agents(self) -> None:
    """Test shutting down all running agents."""
    agent1 = 'data_analysis_agent'
    agent2 = 'creative_writing_agent'

    self.manager.launch_agent(agent1)
    self.manager.launch_agent(agent2)

    self.assertEqual(len(self.manager.active_agents()), 2)

    self.manager.shutdown_all_agents()

    self.assertEqual(len(self.manager.active_agents()), 0)

if __name__ == "__main__":
    unittest.main()