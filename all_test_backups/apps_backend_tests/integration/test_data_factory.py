"""
测试数据工厂
提供各种测试数据的生成和管理
"""

import uuid
from typing import Dict, Any, List


class TestDataFactory:
    """测试数据工厂类"""
    
    @staticmethod
    def create_agent_config(
        agent_id: str = None,
        agent_type: str = "base_agent",
        capabilities: List[str] = None,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        创建代理配置数据
        
        Args:
            agent_id: 代理ID
            agent_type: 代理类型
            capabilities: 代理能力列表
            config: 配置参数
            
        Returns:
            Dict: 代理配置
        """
        if agent_id is None:
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        if capabilities is None:
            capabilities = ["text_generation", "data_analysis"]
            
        if config is None:
            config = {
                "max_concurrent_tasks": 5,
                "timeout": 30,
                "retry_attempts": 3
            }
            
        return {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "config": config,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    @staticmethod
    def create_hsp_message(
        message_id: str = None,
        message_type: str = "fact",
        content: str = "Test message content",
        source: str = "test_source",
        target: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        创建HSP消息数据
        
        Args:
            message_id: 消息ID
            message_type: 消息类型 (fact, opinion, request, response)
            content: 消息内容
            source: 消息来源
            target: 消息目标
            metadata: 元数据
            
        Returns:
            Dict: HSP消息
        """
        if message_id is None:
            message_id = f"msg_{uuid.uuid4().hex[:8]}"
            
        if metadata is None:
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "priority": "normal",
                "ttl": 3600
            }
            
        return {
            "id": message_id,
            "type": message_type,
            "content": content,
            "source": source,
            "target": target,
            "metadata": metadata
        }
    
    @staticmethod
    def create_memory_item(
        memory_id: str = None,
        content: str = "Test memory content",
        memory_type: str = "fact",
        importance_score: float = 0.5,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        创建记忆项数据
        
        Args:
            memory_id: 记忆ID
            content: 记忆内容
            memory_type: 记忆类型
            importance_score: 重要性评分
            tags: 标签列表
            metadata: 元数据
            
        Returns:
            Dict: 记忆项
        """
        if memory_id is None:
            memory_id = f"mem_{uuid.uuid4().hex[:8]}"
            
        if tags is None:
            tags = ["test", "integration"]
            
        if metadata is None:
            metadata = {
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 1
            }
            
        return {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "importance_score": importance_score,
            "tags": tags,
            "metadata": metadata
        }
    
    @staticmethod
    def create_training_data(
        data_id: str = None,
        input_data: str = "Test input data",
        expected_output: str = "Test expected output",
        data_type: str = "text",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        创建训练数据
        
        Args:
            data_id: 数据ID
            input_data: 输入数据
            expected_output: 期望输出
            data_type: 数据类型
            metadata: 元数据
            
        Returns:
            Dict: 训练数据
        """
        if data_id is None:
            data_id = f"train_{uuid.uuid4().hex[:8]}"
            
        if metadata is None:
            metadata = {
                "created_at": datetime.now().isoformat(),
                "source": "integration_test",
                "quality_score": 0.8
            }
            
        return {
            "id": data_id,
            "input": input_data,
            "expected_output": expected_output,
            "type": data_type,
            "metadata": metadata
        }
    
    @staticmethod
    def create_dialogue_context(
        context_id: str = None,
        user_id: str = "test_user",
        session_id: str = None,
        history: List[Dict] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        创建对话上下文数据
        
        Args:
            context_id: 上下文ID
            user_id: 用户ID
            session_id: 会话ID
            history: 对话历史
            metadata: 元数据
            
        Returns:
            Dict: 对话上下文
        """
        if context_id is None:
            context_id = f"context_{uuid.uuid4().hex[:8]}"
            
        if session_id is None:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            
        if history is None:
            history = []
            
        if metadata is None:
            metadata = {
                "created_at": datetime.now().isoformat(),
                "language": "en",
                "timezone": "UTC"
            }
            
        return {
            "id": context_id,
            "user_id": user_id,
            "session_id": session_id,
            "history": history,
            "metadata": metadata
        }
    
    @staticmethod
    def create_test_scenario(
        scenario_id: str = None,
        name: str = "Test Scenario",
        description: str = "Test scenario for integration testing",
        steps: List[Dict] = None,
        expected_results: List[str] = None
    ) -> Dict[str, Any]:
        """
        创建测试场景数据
        
        Args:
            scenario_id: 场景ID
            name: 场景名称
            description: 场景描述
            steps: 测试步骤
            expected_results: 期望结果
            
        Returns:
            Dict: 测试场景
        """
        if scenario_id is None:
            scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
            
        if steps is None:
            steps = [
                {
                    "step": 1,
                    "action": "Initialize system",
                    "description": "Start all core services"
                }
            ]
            
        if expected_results is None:
            expected_results = ["System initializes successfully"]
            
        return {
            "id": scenario_id,
            "name": name,
            "description": description,
            "steps": steps,
            "expected_results": expected_results,
            "created_at": datetime.now().isoformat()
        }


class TestDataSet:
    """测试数据集类"""
    
    def __init__(self) -> None:
        self.factory = TestDataFactory()
        self.data_sets = {}
    
    def create_standard_test_data(self) -> Dict[str, Any]:
        """
        创建标准测试数据集
        
        Returns:
            Dict: 标准测试数据集
        """
        return {
            "agents": [
                self.factory.create_agent_config(
                    agent_id="writer_agent_001",
                    agent_type="creative_writing",
                    capabilities=["text_generation", "story_creation"]
                ),
                self.factory.create_agent_config(
                    agent_id="analyst_agent_001",
                    agent_type="data_analysis",
                    capabilities=["data_processing", "insight_extraction"]
                )
            ],
            "messages": [
                self.factory.create_hsp_message(
                    message_id="msg_001",
                    message_type="request",
                    content="Please analyze this dataset",
                    source="writer_agent_001",
                    target="analyst_agent_001"
                ),
                self.factory.create_hsp_message(
                    message_id="msg_002",
                    message_type="response",
                    content="Analysis complete. Key insights: ...",
                    source="analyst_agent_001",
                    target="writer_agent_001"
                )
            ],
            "memories": [
                self.factory.create_memory_item(
                    memory_id="mem_001",
                    content="User prefers concise responses",
                    memory_type="preference",
                    importance_score=0.8,
                    tags=["user_preference", "communication_style"]
                )
            ],
            "training_data": [
                self.factory.create_training_data(
                    data_id="train_001",
                    input_data="Write a short story about technology",
                    expected_output="A brief story exploring the impact of technology on society",
                    data_type="creative_writing"
                )
            ]
        }
    
    def get_data_set(self, name: str) -> Dict[str, Any]:
        """
        获取指定名称的数据集
        
        Args:
            name: 数据集名称
            
        Returns:
            Dict: 数据集
        """
        if name not in self.data_sets:
            if name == "standard":
                self.data_sets[name] = self.create_standard_test_data()
            else:
                raise ValueError(f"Unknown dataset: {name}")
                
        return self.data_sets[name]

# 添加pytest标记，防止被误认为测试类
TestDataSet.__test__ = False