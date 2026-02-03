"""
Tests for the context system, including various context managers.
"""

import pytest
import tempfile
import shutil
import sys
import os

# Add project root to path to allow absolute imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, PROJECT_ROOT)


# Corrected import paths
from apps.backend.src.core_ai.context.context_system import ContextManager, ContextType
from apps.backend.src.core_ai.context.storage.memory import MemoryStorage
from apps.backend.src.core_ai.context.storage.disk import DiskStorage
from apps.backend.src.core_ai.context.tool_context import ToolContextManager
from apps.backend.src.core_ai.context.model_context import ModelContextManager, AgentContextManager
from apps.backend.src.core_ai.context.dialogue_context import DialogueContextManager
from apps.backend.src.core_ai.context.memory_context import MemoryContextManager

@pytest.fixture
def temp_dir_fixture():
    """Create a temporary directory for tests that need disk storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def context_manager_fixture(temp_dir_fixture):
    """Provides a ContextManager instance with a disk storage path."""
    return ContextManager(disk_storage_path=temp_dir_fixture)

def test_context_manager_initialization(context_manager_fixture):
    """Test ContextManager initialization."""
    assert context_manager_fixture is not None
    assert isinstance(context_manager_fixture.memory_storage, MemoryStorage)
    assert isinstance(context_manager_fixture.disk_storage, DiskStorage)

def test_create_and_get_context(context_manager_fixture):
    """Test creating and retrieving a context."""
    context_id = context_manager_fixture.create_context(
        ContextType.TOOL,
        {"test": "data"}
    )
    assert context_id is not None
    
    context = context_manager_fixture.get_context(context_id)
    assert context is not None
    assert context.context_id == context_id
    assert context.context_type == ContextType.TOOL
    assert context.content == {"test": "data"}

def test_tool_context_manager(context_manager_fixture):
    """Test basic functionality of the ToolContextManager."""
    tool_manager = ToolContextManager(context_manager_fixture)
    
    assert tool_manager.create_tool_category("cat_001", "Test Category", "A category for testing.")
    assert tool_manager.register_tool("tool_001", "Test Tool", "A tool for testing.", "cat_001")
    
    tool_context = tool_manager.get_tool_context("tool_001")
    assert tool_context is not None
    assert tool_context.content['name'] == "Test Tool"