"""
Phase 2: HSM+CDM Core Implementation
启发式模拟机制 (HSM) + 认知配息模型 (CDM)

核心公式：
HSM = C_Gap × E_M2
CDM = Logic Unit + Memory Encoding + Dynamic Retrieval
"""
import asyncio
import hashlib
import json
import logging
import math
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CognitiveGapDetector:
    """认知缺口检测器 - C_Gap 计算"""
    
    def __init__(self):
        self.knowledge_base = {}  # 简化知识库
        self.gap_threshold = 0.7  # 缺口阈值
        
    def calculate_cognitive_gap(self, input_data: Dict[str, Any]) -> Dict[str, float]:
        """
        计算认知缺口 C_Gap = |New_Information - Existing_Structure|
        
        Returns:
            Dict with gap metrics: magnitude, confidence, complexity
        """
        try:
            # 提取输入特征
            content = input_data.get("content", "")
            context = input_data.get("context", "")
            
            # 简化的语义相似度计算
            input_features = self._extract_features(content + " " + context)
            
            # 搜索知识库中的匹配项
            max_similarity = 0.0
            for knowledge_id, knowledge in self.knowledge_base.items():
                knowledge_features = self._extract_features(knowledge["content"])
                similarity = self._cosine_similarity(input_features, knowledge_features)
                max_similarity = max(max_similarity, similarity)
            
            # 计算缺口大小
            gap_magnitude = 1.0 - max_similarity  # 相似度越低，缺口越大
            
            # 计算置信度
            gap_confidence = min(0.95, gap_magnitude * 1.2)
            
            # 计算复杂度
            gap_complexity = min(1.0, len(content.split()) / 50.0)  # 基于词数
            
            return {
                "magnitude": gap_magnitude,
                "confidence": gap_confidence, 
                "complexity": gap_complexity,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"C_Gap calculation error: {e}")
            return {"magnitude": 0.5, "confidence": 0.5, "complexity": 0.5}
    
    def _extract_features(self, text: str) -> Dict[str, float]:
        """提取文本特征向量"""
        words = text.lower().split()
        features = {}
        
        # 简化的TF-IDF特征
        total_words = len(words)
        if total_words == 0:
            return {}
            
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
            
        for word, freq in word_freq.items():
            features[word] = freq / total_words
            
        return features
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
            
        # 计算点积
        dot_product = 0.0
        for word in vec1:
            if word in vec2:
                dot_product += vec1[word] * vec2[word]
        
        # 计算向量长度
        norm1 = math.sqrt(sum(val**2 for val in vec1.values()))
        norm2 = math.sqrt(sum(val**2 for val in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def should_trigger_learning(self, gap_metrics: Dict[str, float]) -> bool:
        """判断是否应该触发学习机制"""
        magnitude = gap_metrics.get("magnitude", 0.0)
        confidence = gap_metrics.get("confidence", 0.0)
        
        # 综合判断：缺口大小超过阈值且置信度足够高
        trigger_score = magnitude * confidence
        return trigger_score > self.gap_threshold

class HeuristicSimulationMechanism:
    """启发式模拟机制 - HSM 实现"""
    
    def __init__(self):
        self.em2_factor = 0.1  # E_M2 随机探索因子
        self.temperature = 1.0  # 探索温度参数
        
    def simulate_solution(self, problem: Dict[str, Any], gap_metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        HSM = C_Gap × E_M2
        
        基于认知缺口进行启发式探索，生成解决方案
        """
        try:
            gap_magnitude = gap_metrics.get("magnitude", 0.5)
            complexity = gap_metrics.get("complexity", 0.5)
            
            # 调整探索强度
            exploration_intensity = gap_magnitude * self.em2_factor
            
            # 生成候选解决方案
            candidates = self._generate_candidates(problem, exploration_intensity, complexity)
            
            # 评估和选择最佳方案
            best_candidate = self._evaluate_candidates(candidates, problem)
            
            return {
                "solution": best_candidate,
                "hsm_score": exploration_intensity,
                "candidates_explored": len(candidates),
                "confidence": best_candidate.get("confidence", 0.5),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"HSM simulation error: {e}")
            return {
                "solution": {"content": "基础回应", "confidence": 0.3},
                "hsm_score": 0.0,
                "candidates_explored": 1,
                "confidence": 0.3
            }
    
    def _generate_candidates(self, problem: Dict[str, Any], intensity: float, complexity: float) -> List[Dict]:
        """生成候选解决方案"""
        candidates = []
        content = problem.get("content", "")
        
        # 基础候选：直接回答
        candidates.append({
            "content": f"基于'{content}'的分析回应",
            "confidence": 0.7,
            "type": "direct_response"
        })
        
        # 探索候选：基于随机探索
        if intensity > 0.05:
            candidates.append({
                "content": f"通过启发式探索对'{content}'的创新性回应",
                "confidence": 0.6 + np.random.random() * 0.2,
                "type": "exploratory_response"
            })
        
        # 复杂候选：针对复杂问题的深度回应
        if complexity > 0.7:
            candidates.append({
                "content": f"对复杂问题'{content}'的多层次深度回应",
                "confidence": 0.8 + np.random.random() * 0.1,
                "type": "complex_response"
            })
        
        return candidates
    
    def _evaluate_candidates(self, candidates: List[Dict], problem: Dict[str, Any]) -> Dict[str, Any]:
        """评估候选方案并选择最佳"""
        if not candidates:
            return {"content": "无可用方案", "confidence": 0.0}
        
        # 简化评估：选择置信度最高的方案
        best_candidate = max(candidates, key=lambda x: x.get("confidence", 0.0))
        best_candidate["evaluation_time"] = datetime.now(timezone.utc).isoformat()
        
        return best_candidate

class CognitiveDividendModel:
    """认知配息模型 - CDM 实现"""
    
    def __init__(self):
        self.logic_units = {}  # 存储逻辑单元
        self.unit_counter = 0
        self.decay_rate = 0.01  # 遗忘速率
        
    def solidify_logic_unit(self, experience: Dict[str, Any], solution: Dict[str, Any]) -> str:
        """
        将经验和解决方案固化为逻辑单元
        
        Returns:
            Logic Unit ID
        """
        try:
            # 生成逻辑单元ID
            unit_id = f"LU_{self.unit_counter:06d}"
            self.unit_counter += 1
            
            # 创建逻辑单元
            logic_unit = {
                "id": unit_id,
                "content": experience.get("content", ""),
                "solution": solution.get("solution", {}),
                "confidence": solution.get("confidence", 0.5),
                "hsm_score": solution.get("hsm_score", 0.0),
                "type": solution.get("solution", {}).get("type", "unknown"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_accessed": datetime.now(timezone.utc).isoformat(),
                "access_count": 0,
                "effectiveness": 0.5,  # 初始效果值
                "metadata": {
                    "experience": experience,
                    "gap_metrics": experience.get("gap_metrics", {}),
                    "candidates": solution.get("candidates_explored", 1)
                }
            }
            
            # 存储逻辑单元
            self.logic_units[unit_id] = logic_unit
            
            logger.info(f"CDM: Solidified logic unit {unit_id}")
            return unit_id
            
        except Exception as e:
            logger.error(f"CDM solidification error: {e}")
            return "ERROR"
    
    def retrieve_relevant_units(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """检索相关逻辑单元"""
        try:
            query_features = self._extract_features(query)
            
            # 计算相似度并排序
            scored_units = []
            for unit_id, unit in self.logic_units.items():
                unit_content = unit.get("content", "")
                unit_features = self._extract_features(unit_content)
                
                similarity = self._cosine_similarity(query_features, unit_features)
                
                # 综合评分：相似度 + 效果 + 访问频率
                access_bonus = math.log(1 + unit.get("access_count", 0)) * 0.1
                effectiveness = unit.get("effectiveness", 0.5)
                
                total_score = similarity * 0.6 + effectiveness * 0.3 + access_bonus * 0.1
                
                scored_units.append((total_score, unit))
            
            # 按评分排序并返回前N个
            scored_units.sort(key=lambda x: x[0], reverse=True)
            top_units = [unit for score, unit in scored_units[:limit]]
            
            # 更新访问统计
            for unit in top_units:
                unit["last_accessed"] = datetime.now(timezone.utc).isoformat()
                unit["access_count"] += 1
            
            return top_units
            
        except Exception as e:
            logger.error(f"CDM retrieval error: {e}")
            return []
    
    def update_effectiveness(self, unit_id: str, feedback_score: float):
        """基于反馈更新逻辑单元效果"""
        if unit_id in self.logic_units:
            unit = self.logic_units[unit_id]
            current_effectiveness = unit.get("effectiveness", 0.5)
            
            # 指数移动平均更新
            alpha = 0.2  # 学习率
            new_effectiveness = alpha * feedback_score + (1 - alpha) * current_effectiveness
            
            unit["effectiveness"] = new_effectiveness
            unit["last_updated"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"CDM: Updated unit {unit_id} effectiveness to {new_effectiveness:.3f}")
    
    def _extract_features(self, text: str) -> Dict[str, float]:
        """提取文本特征"""
        words = text.lower().split()
        features = {}
        
        total_words = len(words)
        if total_words == 0:
            return {}
            
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
            
        for word, freq in word_freq.items():
            features[word] = freq / total_words
            
        return features
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
            
        dot_product = 0.0
        for word in vec1:
            if word in vec2:
                dot_product += vec1[word] * vec2[word]
        
        norm1 = math.sqrt(sum(val**2 for val in vec1.values()))
        norm2 = math.sqrt(sum(val**2 for val in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)

class HSMCDMEngine:
    """HSM+CDM 集成引擎"""
    
    def __init__(self):
        self.gap_detector = CognitiveGapDetector()
        self.hsm = HeuristicSimulationMechanism()
        self.cdm = CognitiveDividendModel()
        
        # 性能指标
        self.metrics = {
            "total_processed": 0,
            "learning_triggered": 0,
            "units_created": 0,
            "units_retrieved": 0,
            "average_confidence": 0.0
        }
        
        logger.info("HSM+CDM Engine initialized")
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        完整的 HSM+CDM 处理流程：
        1. C_Gap 检测
        2. HSM 模拟（如需要）
        3. CDM 固化/检索
        4. 响应生成
        """
        start_time = time.time()
        self.metrics["total_processed"] += 1
        
        try:
            # Step 1: 认知缺口检测
            input_data = {"content": user_input, "context": ""}
            gap_metrics = self.gap_detector.calculate_cognitive_gap(input_data)
            
            response = None
            learned_new_unit = False
            
            # Step 2: 判断是否需要学习
            if self.gap_detector.should_trigger_learning(gap_metrics):
                logger.info(f"Triggering learning for input: {user_input[:50]}...")
                self.metrics["learning_triggered"] += 1
                
                # Step 3: HSM 启发式模拟
                problem = {"content": user_input}
                hsm_result = self.hsm.simulate_solution(problem, gap_metrics)
                
                # Step 4: CDM 固化新逻辑单元
                experience = {
                    "content": user_input,
                    "gap_metrics": gap_metrics,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                unit_id = self.cdm.solidify_logic_unit(experience, hsm_result)
                if unit_id != "ERROR":
                    self.metrics["units_created"] += 1
                    learned_new_unit = True
                
                response = hsm_result.get("solution", {}).get("content", "正在学习中...")
                
            else:
                # Step 5: 从 CDM 检索相关逻辑单元
                relevant_units = self.cdm.retrieve_relevant_units(user_input, limit=3)
                self.metrics["units_retrieved"] += len(relevant_units)
                
                if relevant_units:
                    # 使用最相关的逻辑单元生成响应
                    best_unit = relevant_units[0]
                    response = best_unit.get("solution", {}).get("content", "基于已有知识回应...")
                    
                    # 提供反馈机制
                    logger.info(f"Retrieved logic unit: {best_unit['id']}")
                else:
                    # 默认回应
                    response = f"我理解您说的：{user_input}"
            
            # Step 6: 更新平均置信度
            confidence = gap_metrics.get("confidence", 0.5)
            total_conf = self.metrics["average_confidence"] * (self.metrics["total_processed"] - 1) + confidence
            self.metrics["average_confidence"] = total_conf / self.metrics["total_processed"]
            
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "metadata": {
                    "gap_magnitude": gap_metrics.get("magnitude", 0.0),
                    "gap_confidence": gap_metrics.get("confidence", 0.0),
                    "learning_triggered": learned_new_unit,
                    "units_retrieved": len(relevant_units) if not learned_new_unit else 0,
                    "processing_time_ms": processing_time * 1000,
                    "engine": "HSM+CDM",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "metrics": self.metrics.copy()
            }
            
        except Exception as e:
            logger.error(f"HSM+CDM processing error: {e}")
            return {
                "response": f"处理过程中出现错误: {str(e)}",
                "metadata": {"error": str(e), "engine": "HSM+CDM_ERROR"},
                "metrics": self.metrics.copy()
            }
    
    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "engine": "HSM+CDM",
            "status": "active",
            "metrics": self.metrics.copy(),
            "components": {
                "gap_detector": "active",
                "hsm": "active", 
                "cdm": {
                    "total_units": len(self.cdm.logic_units),
                    "average_effectiveness": np.mean([unit.get("effectiveness", 0.5) for unit in self.cdm.logic_units.values()]) if self.cdm.logic_units else 0.0
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def provide_feedback(self, response_id: str, feedback_score: float):
        """为响应提供反馈以改进系统"""
        # 这里可以实现反馈机制来改进逻辑单元效果
        logger.info(f"Feedback provided for response {response_id}: {feedback_score}")
        
        # 可以根据反馈内容更新相关的逻辑单元
        # 这里是简化实现
        return {"status": "feedback_recorded"}

# Phase 2 测试和演示
async def demo_hsm_cdm():
    """演示 HSM+CDM 系统功能"""
    print("🚀 Phase 2: HSM+CDM 系统演示")
    print("=" * 60)
    
    engine = HSMCDMEngine()
    
    # 测试输入
    test_inputs = [
        "你好，我是新用户",
        "什么是人工智能？",
        "请解释量子计算的基本原理",
        "给我讲一个关于AI的故事",
        "量子计算在AI中的应用有哪些？",  # 应该触发已有单元检索
        "什么是认知科学？",  # 可能触发新学习
        "总结一下我们刚才的对话"  # 复杂查询
    ]
    
    print("开始处理测试输入...\n")
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"📝 测试 {i}: {user_input}")
        
        result = await engine.process_input(user_input)
        
        print(f"🤖 回应: {result['response'][:100]}...")
        print(f"📊 元数据: 学习触发={result['metadata']['learning_triggered']}, "
              f"检索单元={result['metadata']['units_retrieved']}, "
              f"处理时间={result['metadata']['processing_time_ms']:.1f}ms")
        print()
        
        # 模拟反馈
        if result['metadata']['learning_triggered']:
            feedback = 0.8  # 假设良好反馈
            engine.provide_feedback(f"response_{i}", feedback)
            print(f"🔄 提供了反馈: {feedback}")
        
        print("-" * 40)
    
    # 显示最终状态
    status = engine.get_engine_status()
    print("\n📈 HSM+CDM 系统最终状态:")
    print(f"  总处理数: {status['metrics']['total_processed']}")
    print(f"  学习触发: {status['metrics']['learning_triggered']}")
    print(f"  创建单元: {status['metrics']['units_created']}")
    print(f"  检索单元: {status['metrics']['units_retrieved']}")
    print(f"  平均置信度: {status['metrics']['average_confidence']:.3f}")
    print(f"  CDM单元总数: {status['components']['cdm']['total_units']}")
    print(f"  CDM平均效果: {status['components']['cdm']['average_effectiveness']:.3f}")
    
    return engine

if __name__ == "__main__":
    asyncio.run(demo_hsm_cdm())