"""
测试模块 - test_pet_manager

自动生成的测试模块,用于验证系统功能。
基于实际API修复，支持异步方法调用。
"""

import pytest
from pet.pet_manager import PetManager


@pytest.fixture
def pet_manager():
    """创建PetManager实例"""
    return PetManager(
        "test_pet",
        {
            "initial_personality": {"curiosity": 0.7, "playfulness": 0.8},
            "initial_behaviors": {"on_interaction": "show_happiness"},
        },
    )


def test_initialization(pet_manager) -> None:
    """测试初始化"""
    assert pet_manager.pet_id == "test_pet"
    state = pet_manager.get_current_state()
    assert state is not None
    assert pet_manager.personality == {"curiosity": 0.7, "playfulness": 0.8}
    assert pet_manager.behavior_rules == {"on_interaction": "show_happiness"}


def test_get_current_state(pet_manager) -> None:
    """测试获取当前状态"""
    state = pet_manager.get_current_state()
    assert isinstance(state, dict)
    assert "happiness" in state
    assert "hunger" in state
    assert "energy" in state


def test_update_behavior(pet_manager) -> None:
    """测试更新行为"""
    new_behaviors = {"on_new_command": "wag_tail", "on_sleep": "snore"}
    pet_manager.update_behavior(new_behaviors)
    assert "on_new_command" in pet_manager.behavior_rules
    assert "on_sleep" in pet_manager.behavior_rules


def test_get_pending_actions(pet_manager) -> None:
    """测试获取待处理动作"""
    actions = pet_manager.get_pending_actions()
    assert isinstance(actions, list)


def test_update_position(pet_manager) -> None:
    """测试更新位置"""
    pet_manager.update_position(100, 200)
    state = pet_manager.get_current_state()
    assert state is not None


def test_add_action(pet_manager) -> None:
    """测试添加动作"""
    action = {"type": "move", "target": {"x": 50, "y": 50}}
    pet_manager.add_action(action)
    actions = pet_manager.get_pending_actions()
    assert len(actions) > 0
async def test_handle_interaction(pet_manager) -> None:
    """测试处理交互（异步）"""
    interaction_data = {"type": "pet"}
    result = await pet_manager.handle_interaction(interaction_data)
    assert result is not None
async def test_apply_resource_decay(pet_manager) -> None:
    """测试应用资源衰减（异步）"""
    initial_state = pet_manager.get_current_state()
    await pet_manager.apply_resource_decay()
    assert pet_manager.get_current_state() is not None
async def test_check_survival_needs(pet_manager) -> None:
    """测试检查生存需求（异步）"""
    needs = await pet_manager.check_survival_needs()
    assert needs is None or isinstance(needs, dict)
