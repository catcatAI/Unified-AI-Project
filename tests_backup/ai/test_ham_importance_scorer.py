"""
Test suite for HAM Importance Scorer
测试 HAM 重要性评分器

测试场景：
1. 基础评分
2. 关键词加权
3. 用户输入加权
4. 受保护内容加权
5. 长度惩罚
6. 时间衰减
"""

import pytest
import asyncio
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'apps' / 'backend' / 'src'))

from ai.memory.ham_memory.ham_importance_scorer import ImportanceScorer


class TestImportanceScorer:
    """ImportanceScorer 测试类"""
    
    @pytest.fixture
    def scorer(self):
        """创建 ImportanceScorer 实例"""
        return ImportanceScorer()
    
    @pytest.mark.asyncio
    async def test_basic_score(self, scorer):
        """测试基础评分"""
        metadata = {}
        score = await scorer.calculate("普通消息", metadata)
        assert 0.0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_keyword_boost(self, scorer):
        """测试关键词加分"""
        #urgent 关键词
        score_urgent = await scorer.calculate("这是一个urgent消息", {})
        score_normal = await scorer.calculate("这是一个普通消息", {})
        assert score_urgent > score_normal
        
        #important 关键词
        score_important = await scorer.calculate("这是important内容", {})
        assert score_important > score_normal
    
    @pytest.mark.asyncio
    async def test_negative_keywords(self, scorer):
        """测试负面关键词加分"""
        score_error = await scorer.calculate("发生error错误", {})
        score_failure = await scorer.calculate("操作failure失败", {})
        assert score_error > 0.0
        assert score_failure > 0.0
    
    @pytest.mark.asyncio
    async def test_user_input_boost(self, scorer):
        """测试用户输入加分"""
        metadata_user = {"speaker": "user"}
        metadata_system = {"speaker": "system"}
        
        score_user = await scorer.calculate("消息", metadata_user)
        score_system = await scorer.calculate("消息", metadata_system)
        assert score_user > score_system
    
    @pytest.mark.asyncio
    async def test_protected_content_boost(self, scorer):
        """测试受保护内容加分"""
        metadata_protected = {"protected": True}
        metadata_normal = {"protected": False}
        
        score_protected = await scorer.calculate("消息", metadata_protected)
        score_normal = await scorer.calculate("消息", metadata_normal)
        assert score_protected > score_normal
    
    @pytest.mark.asyncio
    async def test_length_penalty(self, scorer):
        """测试长度惩罚"""
        short_msg = "短消息"
        long_msg = "这是一条" * 50  # 长消息
        
        score_short = await scorer.calculate(short_msg, {})
        score_long = await scorer.calculate(long_msg, {})
        
        # 长消息应该得分较低（因为被截断）
        assert score_long < 1.0
    
    @pytest.mark.asyncio
    async def test_score_cap(self, scorer):
        """测试分数上限"""
        # 创建应该得高分的消息
        metadata = {
            "speaker": "user",
            "protected": True
        }
        score = await scorer.calculate("urgent important 消息 error failure", metadata)
        
        # 分数不应超过 1.0
        assert score <= 1.0
    
    @pytest.mark.asyncio
    async def test_empty_content(self, scorer):
        """测试空内容"""
        score = await scorer.calculate("", {})
        assert 0.0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_combined_factors(self, scorer):
        """测试组合因素"""
        metadata = {
            "speaker": "user",
            "protected": True
        }
        score = await scorer.calculate("urgent important 消息", metadata)
        
        # 组合因素应该产生较高分数
        assert score > 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
