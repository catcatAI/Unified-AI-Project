"""
测试模块 - test_pet_manager

自动生成的测试模块,用于验证系统功能。
"""

import pytest
from pet.pet_manager import PetManager

@pytest.fixture
def pet_manager():
    """创建PetManager实例"""
    return PetManager("test_pet", {})

@pytest.mark.asyncio
async def test_initialization(pet_manager) -> None:
    """测试初始化"""
    assert pet_manager.pet_id == "test_pet"
    state = pet_manager.get_current_state()
    assert state is not None

def test_get_current_state(pet_manager) -> None:
    """测试获取当前状态"""
    state = pet_manager.get_current_state()
    assert isinstance(state, dict)

@pytest.mark.asyncio
async def test_handle_interaction(pet_manager) -> None:
    """测试处理交互"""
    interaction_data = {"type": "pet"}
    result = await pet_manager.handle_interaction(interaction_data)
    assert result is not None

def test_update_behavior(pet_manager) -> None:
    """测试更新行为"""
    new_behaviors = {"on_interaction": "wave"}
    pet_manager.update_behavior(new_behaviors)
    assert pet_manager.behavior_rules is not None

def test_get_pending_actions(pet_manager) -> None:
    """测试获取待处理动作"""
    actions = pet_manager.get_pending_actions()
    assert isinstance(actions, list)

@pytest.mark.asyncio
async def test_apply_resource_decay(pet_manager) -> None:
    """测试应用资源衰减"""
    await pet_manager.apply_resource_decay()
    state = pet_manager.get_current_state()
    assert state is not None

@pytest.mark.asyncio
async def test_check_survival_needs(pet_manager) -> None:
    """测试检查生存需求"""
    # check_survival_needs 需要economy_manager，这里只测试不会崩溃
    needs = await pet_manager.check_survival_needs()
    # 如果没有economy_manager，返回None是正常的
    assert needs is None or isinstance(needs, dict)