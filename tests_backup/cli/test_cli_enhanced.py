"""
Tests for the enhanced CLI functionalities.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Corrected import path
from packages.cli.main import (
    handle_model_list, 
    handle_model_info, 
    handle_train_start, 
    handle_train_status, 
    handle_data_list, 
    handle_data_info
)

@pytest.mark.asyncio
@patch('packages.cli.main.get_services')
async def test_handle_model_list_success(mock_get_services):
    """Test model list command successfully executes."""
    mock_learning_manager = AsyncMock()
    mock_learning_manager.get_available_models.return_value = ['model1', 'model2', 'model3']
    mock_get_services.return_value = {'learning_manager': mock_learning_manager}
    
    mock_args = MagicMock()
    
    await handle_model_list(mock_args)
    
    mock_learning_manager.get_available_models.assert_called_once()

@pytest.mark.asyncio
@patch('packages.cli.main.get_services')
async def test_handle_model_list_no_learning_manager(mock_get_services):
    """Test model list command when learning manager is not available."""
    mock_get_services.return_value = {}
    mock_args = MagicMock()
    # Should not raise an exception
    await handle_model_list(mock_args)

@pytest.mark.asyncio
@patch('packages.cli.main.get_services')
async def test_handle_model_info_success(mock_get_services):
    """Test model info command successfully executes."""
    mock_learning_manager = AsyncMock()
    mock_learning_manager.get_model_info.return_value = {
        'name': 'test_model',
        'version': '1.0',
        'description': 'Test model'
    }
    mock_get_services.return_value = {'learning_manager': mock_learning_manager}
    
    mock_args = MagicMock()
    mock_args.model_name = 'test_model'
    
    await handle_model_info(mock_args)
    
    mock_learning_manager.get_model_info.assert_called_once_with('test_model')

@pytest.mark.asyncio
@patch('packages.cli.main.get_services')
async def test_handle_train_start_success(mock_get_services):
    """Test train start command successfully executes."""
    mock_learning_manager = AsyncMock()
    mock_learning_manager.start_training.return_value = {
        'status': 'started',
        'message': 'Training started successfully'
    }
    mock_get_services.return_value = {'learning_manager': mock_learning_manager}
    
    mock_args = MagicMock()
    mock_args.model_name = 'test_model'
    
    await handle_train_start(mock_args)
    
    mock_learning_manager.start_training.assert_called_once()

@pytest.mark.asyncio
@patch('packages.cli.main.get_services')
async def test_handle_train_status_success(mock_get_services):
    """Test train status command successfully executes."""
    mock_learning_manager = AsyncMock()
    mock_learning_manager.get_training_status.return_value = {
        'status': 'running',
        'progress': '50%',
        'eta': '10 minutes'
    }
    mock_get_services.return_value = {'learning_manager': mock_learning_manager}
    
    mock_args = MagicMock()
    
    await handle_train_status(mock_args)
    
    mock_learning_manager.get_training_status.assert_called_once()

@pytest.mark.asyncio
@patch('packages.cli.main.get_services')
async def test_handle_data_list_success(mock_get_services):
    """Test data list command successfully executes."""
    mock_learning_manager = AsyncMock()
    mock_learning_manager.list_datasets.return_value = ['dataset1', 'dataset2', 'dataset3']
    mock_get_services.return_value = {'learning_manager': mock_learning_manager}
    
    mock_args = MagicMock()
    
    await handle_data_list(mock_args)
    
    mock_learning_manager.list_datasets.assert_called_once()

@pytest.mark.asyncio
@patch('packages.cli.main.get_services')
async def test_handle_data_info_success(mock_get_services):
    """Test data info command successfully executes."""
    mock_learning_manager = AsyncMock()
    mock_learning_manager.get_dataset_info.return_value = {
        'name': 'test_dataset',
        'size': '1000 samples',
        'description': 'Test dataset'
    }
    mock_get_services.return_value = {'learning_manager': mock_learning_manager}
    
    mock_args = MagicMock()
    mock_args.dataset_name = 'test_dataset'
    
    await handle_data_info(mock_args)
    
    mock_learning_manager.get_dataset_info.assert_called_once_with('test_dataset')
