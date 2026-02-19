"""
核心系統組件的單元測試
測試 SystemManager、CognitiveOrchestrator 等核心功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os
import logging
logger = logging.getLogger(__name__)

from core.managers.system_manager import SystemManager
from core.orchestrator import CognitiveOrchestrator
from ai.memory.ham_memory_manager import HAMMemoryManager
from ai.agent_manager import AgentManager
from game.economy_manager import EconomyManager
from game.desktop_pet import DesktopPet


class TestSystemManager:
    """SystemManager 測試類"""
    
    @pytest.fixture
    async def system_manager(self):
        """創建測試用的 SystemManager 實例"""
        sm = SystemManager()
        yield sm
        # 清理
        if sm.initialized:
            await sm.shutdown_system()
    
    @pytest.mark.asyncio
    async def test_system_manager_initialization(self, system_manager):
        """測試系統管理器初始化"""
        # Mock config path
        with patch('os.path.exists', return_value=True):
            success = await system_manager.initialize_system()
            assert success is True
            assert system_manager.initialized is True
    
    @pytest.mark.asyncio
    async def test_component_initialization(self, system_manager):
        """測試組件初始化"""
        with patch('os.path.exists', return_value=True):
            await system_manager.initialize_system()
            
            # 檢查所有組件都已初始化
            assert system_manager.cognitive_orchestrator is not None
            assert system_manager.ham_memory_manager is not None
            assert system_manager.agent_manager is not None
            assert system_manager.economy_manager is not None
            assert system_manager.desktop_pet is not None


class TestCognitiveOrchestrator:
    """CognitiveOrchestrator 測試類"""
    
    @pytest.fixture
    def orchestrator(self):
        """創建測試用的 CognitiveOrchestrator 實例"""
        with patch('requests.post') as mock_post:
            # Mock LLM response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "response": "測試回應"
            }
            
            orch = CognitiveOrchestrator(llm_available=True, available_models=["test_model"])
            yield orch
    
    @pytest.mark.asyncio
    async def test_process_user_input(self, orchestrator):
        """測試用戶輸入處理"""
        response = await orchestrator.process_user_input("你好")
        
        assert isinstance(response, dict)
        assert "response" in response
        assert "action" in response
        assert "confidence" in response
        assert response["response"] == "測試回應"
    
    def test_calculate_confidence(self, orchestrator):
        """測試置信度計算"""
        # 測試有知識的情況
        knowledge = [{"content": "測試知識"}]
        confidence = orchestrator._calculate_confidence(knowledge, "question")
        assert 0.6 <= confidence <= 1.0
        
        # 測試無知識的情況
        empty_knowledge = []
        confidence = orchestrator._calculate_confidence(empty_knowledge, "question")
        assert 0.1 <= confidence <= 0.6


class TestHAMMemoryManager:
    """HAMMemoryManager 測試類"""
    
    @pytest.fixture
    def memory_manager(self):
        """創建測試用的記憶管理器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = HAMMemoryManager(
                storage_type="simple",
                storage_path=temp_dir
            )
            yield manager
    
    @pytest.mark.asyncio
    async def test_store_memory(self, memory_manager):
        """測試記憶存儲"""
        memory_data = {
            "content": "測試記憶",
            "type": "episodic",
            "importance": 0.8
        }
        
        memory_id = await memory_manager.store_memory(memory_data)
        assert memory_id is not None
        assert len(memory_id) > 0
    
    @pytest.mark.asyncio
    async def test_retrieve_memories(self, memory_manager):
        """測試記憶檢索"""
        # 先存儲一個記憶
        memory_data = {
            "content": "測試記憶檢索",
            "type": "semantic",
            "importance": 0.9
        }
        await memory_manager.store_memory(memory_data)
        
        # 檢索相關記憶
        memories = await memory_manager.retrieve_memories("測試", limit=5)
        assert len(memories) >= 1
        assert any("測試記憶檢索" in m["content"] for m in memories)


class TestAgentManager:
    """AgentManager 測試類"""
    
    @pytest.fixture
    def agent_manager(self):
        """創建測試用的代理管理器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = AgentManager(data_path=temp_dir)
            yield manager
    
    def test_create_agent(self, agent_manager):
        """測試代理創建"""
        agent_config = {
            "name": "測試代理",
            "type": "assistant",
            "capabilities": ["conversation", "analysis"]
        }
        
        agent_id = agent_manager.create_agent(agent_config)
        assert agent_id is not None
        
        # 檢查代理是否創建成功
        agent = agent_manager.get_agent(agent_id)
        assert agent is not None
        assert agent["name"] == "測試代理"
    
    def test_list_agents(self, agent_manager):
        """測試代理列表"""
        # 創建幾個測試代理
        for i in range(3):
            agent_manager.create_agent({
                "name": f"測試代理{i}",
                "type": "assistant"
            })
        
        agents = agent_manager.list_agents()
        assert len(agents) >= 3


class TestDesktopPet:
    """DesktopPet 測試類"""
    
    @pytest.fixture
    def desktop_pet(self):
        """創建測試用的桌面寵物"""
        pet = DesktopPet(name="測試寵物", personality_type="friendly")
        return pet
    
    @pytest.mark.asyncio
    async def test_pet_initialization(self, desktop_pet):
        """測試寵物初始化"""
        assert desktop_pet.name == "測試寵物"
        assert desktop_pet.personality_type == "friendly"
        assert desktop_pet.initialized is True
    
    @pytest.mark.asyncio
    async def test_handle_user_input(self, desktop_pet):
        """測試用戶輸入處理"""
        response = await desktop_pet.handle_user_input(
            "message", 
            {"text": "你好"}
        )
        
        assert isinstance(response, dict)
        assert "pet_response" in response
        assert "emotion" in response
    
    def test_update_mood(self, desktop_pet):
        """測試情緒更新"""
        desktop_pet.update_mood("happy", 0.8)
        assert desktop_pet.current_mood == "happy"
        assert desktop_pet.mood_intensity == 0.8


class TestEconomyManager:
    """EconomyManager 測試類"""
    
    @pytest.fixture
    def economy_manager(self):
        """創建測試用的經濟管理器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_economy.db")
            manager = EconomyManager(db_path=db_path)
            yield manager
    
    @pytest.mark.asyncio
    async def test_create_user_account(self, economy_manager):
        """測試創建用戶帳戶"""
        user_id = "test_user_123"
        success = await economy_manager.create_user_account(user_id)
        assert success is True
        
        # 檢查帳戶是否創建
        balance = await economy_manager.get_user_balance(user_id)
        assert balance >= 0
    
    @pytest.mark.asyncio
    async def test_transaction(self, economy_manager):
        """測試交易功能"""
        # 創建兩個用戶
        user1 = "user1"
        user2 = "user2"
        
        await economy_manager.create_user_account(user1, initial_balance=100)
        await economy_manager.create_user_account(user2, initial_balance=50)
        
        # 進行交易
        success = await economy_manager.process_transaction(
            from_user=user1,
            to_user=user2,
            amount=30,
            description="測試交易"
        )
        
        assert success is True
        
        # 檢查餘額
        balance1 = await economy_manager.get_user_balance(user1)
        balance2 = await economy_manager.get_user_balance(user2)
        
        assert balance1 == 70
        assert balance2 == 80


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v"])