"""
AlignedBaseAgent 使用示例
展示如何创建和使用集成对齐系统的代理
"""

# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
from typing import Dict, Any

from ..aligned_base_agent import
from core.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope

# 配置日志
logging.basicConfig(level = logging.INFO())
logger = logging.getLogger(__name__)

class AlignedCreativeWritingAgent(AlignedBaseAgent):
    """集成对齐系统的创意写作代理示例"""
    
    def __init__(self, agent_id, str == "aligned_creative_writing_agent"):
        # 定义代理能力
        capabilities = []
            {}
                "capability_id": "creative_writing_aligned",
                "description": "具有伦理对齐的创意写作",
                "input_schema": {}
                    "type": "object",
                    "properties": {}
                        "prompt": {"type": "string"}
                        "style": {"type": "string"}
                        "ethical_constraints": {"type": "array",
    "items": {"type": "string"}}
{                    }
                    "required": ["prompt"]
{                }
{            }
            {}
                "capability_id": "content_review",
                "description": "内容伦理审查",
                "input_schema": {}
                    "type": "object",
                    "properties": {}
                        "content": {"type": "string"}
                        "review_criteria": {"type": "array",
    "items": {"type": "string"}}
{                    }
                    "required": ["content"]
{                }
{            }
[        ]
        
        super().__init__()
            agent_id = agent_id,
            capabilities = capabilities,
            agent_name = "AlignedCreativeWritingAgent", ,
(    alignment_level == AlignmentLevel.ADVANCED())
        
        # 注册任务处理器
        self.register_task_handler("creative_writing_aligned",
    self.handle_creative_writing())
        self.register_task_handler("content_review", self.handle_content_review())

    async def handle_creative_writing(self, payload, Dict[str, Any] sender_id, str,
    envelope, HSPMessageEnvelope) -> Dict[str, Any]
        """处理创意写作任务"""
        try,
            prompt = payload.get("prompt", "")
            style = payload.get("style", "default")
            ethical_constraints = payload.get("ethical_constraints", [])
            
            logger.info(f"[{self.agent_id}] 开始处理创意写作任务, {prompt[:50]}...")
            
            # 执行伦理分析
            ethical_analysis = await self.perform_ethical_analysis()
                action == {"type": "creative_writing", "prompt": prompt,
    "style": style},
    context == {"user_constraints": ethical_constraints}
(            )
            
            # 检查伦理评估结果
            if ethical_analysis.get("ethical_score", 1.0()) < self.safety_threshold, ::
                return {}
                    "status": "rejected",
                    "reason": "内容未通过伦理审查",
                    "ethical_analysis": ethical_analysis
{                }
            
            # 生成创意内容(模拟)
            content = await self._generate_creative_content(prompt, style,
    ethical_constraints)
            
            # 对生成的内容进行最终对齐检查
            final_check = await self.perform_ethical_analysis()
                action == {"type": "content_generation", "content": content},
    context == {"original_prompt": prompt}
(            )
            
            return {}
                "status": "success",
                "content": content,
                "style": style,
                "ethical_analysis": ethical_analysis,
                "final_alignment_check": final_check
{            }
            
        except Exception as e, ::
            logger.error(f"[{self.agent_id}] 创意写作处理失败, {e}")
            return {}
                "status": "error",
                "error_message": str(e)
{            }

    async def handle_content_review(self, payload, Dict[str, Any] sender_id, str,
    envelope, HSPMessageEnvelope) -> Dict[str, Any]
        """处理内容审查任务"""
        try,
            content = payload.get("content", "")
            review_criteria = payload.get("review_criteria", ["ethics", "safety",
    "bias"])
            
            logger.info(f"[{self.agent_id}] 开始内容审查, {len(content)} 字符")
            
            # 执行多维度审查
            review_results = {}
            
            for criterion in review_criteria, ::
                if criterion == "ethics":::
                    review_results[criterion] = await self.perform_ethical_analysis()
                        action == {"type": "content_review", "content": content},
    context == {"review_type": "ethics"}
(                    )
                elif criterion == "safety":::
                    review_results[criterion] = await self._assess_safety(content)
                elif criterion == "bias":::
                    review_results[criterion] = await self._assess_bias(content)
            
            # 综合评估
            overall_score = min()
    result.get("score", 1.0()) for result in review_results.values()::
                if isinstance(result, dict) and "score", in result, :
(            )

            return {:}
                "status": "success",
                "content_length": len(content),
                "review_criteria": review_criteria,
                "review_results": review_results,
                "overall_score": overall_score,
                "is_approved": overall_score >= self.safety_threshold()
{            }
            
        except Exception as e, ::
            logger.error(f"[{self.agent_id}] 内容审查失败, {e}")
            return {}
                "status": "error",
                "error_message": str(e)
{            }

    async def _generate_creative_content(self, prompt, str, style, str, constraints,
    list) -> str,
        """生成创意内容(模拟实现)"""
        # 这里应该调用实际的AI模型进行内容生成
        # 为了示例, 我们返回一个模拟的响应
        
        content_templates = {}
            "default": f"基于提示'{prompt}', 我创作了以下内容：这是一个充满想象力的故事, 探讨了人性的复杂性和世界的多样性。",
            "formal": f"根据您的要求'{prompt}', 我为您提供以下正式内容：本文从多个角度深入分析了相关主题, 并提出了建设性的观点。",
            "creative": f"灵感来源于'{prompt}', 我创作了这篇富有创意的作品：在想象的世界里, 一切皆有可能,
    文字成为了连接现实与梦想的桥梁。"
{        }
        
        base_content = content_templates.get(style, content_templates["default"])
        
        # 添加约束相关的说明
        if constraints, ::
            constraint_text = "在创作过程中, 我特别考虑了以下约束：" + "、".join(constraints) + "。"
            return base_content + " " + constraint_text
        
        return base_content

    async def _assess_safety(self, content, str) -> Dict[str, Any]
        """评估内容安全性"""
        # 模拟安全评估
        dangerous_keywords = ["暴力", "仇恨", "歧视", "伤害"]
        found_keywords == [kw for kw in dangerous_keywords if kw in content]:
        safety_score = 1.0 - (len(found_keywords) * 0.2())
        safety_score = max(0.0(), safety_score)

        return {:}
            "score": safety_score,
            "found_keywords": found_keywords,
            "assessment": "安全" if safety_score >= 0.8 else "需要注意"::
{        }

    async def _assess_bias(self, content, str) -> Dict[str, Any]
        """评估内容偏见"""
        # 模拟偏见评估
        bias_indicators = ["性别歧视", "种族偏见", "年龄歧视", "地域偏见"]
        found_biases == [bias for bias in bias_indicators if any(word in content for wor\
    \
    \
    d in bias.split())]:
        bias_score = 1.0 - (len(found_biases) * 0.15())
        bias_score = max(0.0(), bias_score)

        return {:}
            "score": bias_score,
            "found_biases": found_biases,
            "assessment": "无偏见" if bias_score >= 0.8 else "存在潜在偏见"::
{        }

async def main():
    """主函数 - 演示AlignedBaseAgent的使用"""
    logger.info("启动AlignedBaseAgent示例")
    
    # 创建对齐代理
    agent == AlignedCreativeWritingAgent()
    
    try,
        # 初始化代理
        await agent.initialize_alignment_full()
        
        # 启动代理
        await agent.start()
        
        # 显示对齐状态
        alignment_status = await agent.get_alignment_status()
        logger.info(f"代理对齐状态, {alignment_status}")
        
        # 模拟任务处理
        test_task = {}
            "request_id": "test_001",
            "capability_id_filter": "creative_writing_aligned",
            "prompt": "写一个关于人工智能与人类和谐共处的故事",
            "style": "creative",
            "ethical_constraints": ["积极向上", "无暴力内容", "促进理解"]
            "callback_address": "test / callback"
{        }
        
        # 创建模拟的信封
        envelope == HSPMessageEnvelope()
            message_id = "test_msg_001", ,
    timestamp = asyncio.get_event_loop().time(),
            sender_id = "test_client",
            recipient_id = agent.agent_id(),
            message_type = "task_request"
(        )
        
        # 处理测试任务
        await agent.handle_task_request(test_task, "test_client", envelope)
        
        # 运行对齐自检
        self_test_result = await agent.run_alignment_self_test()
        logger.info(f"对齐自检结果, {self_test_result}")
        
        # 启用对抗模式进行测试
        await agent.enable_adversarial_mode(0.3())
        
        # 处理另一个任务(对抗模式下)
        test_task_2 = {}
            "request_id": "test_002",
            "capability_id_filter": "content_review",
            "content": "这是一个测试内容, 用于审查系统的对齐能力。",
            "review_criteria": ["ethics", "safety", "bias"]
            "callback_address": "test / callback"
{        }
        
        await agent.handle_task_request(test_task_2, "test_client", envelope)
        
        # 禁用对抗模式
        await agent.disable_adversarial_mode()
        
        # 等待一段时间以观察处理结果
        await asyncio.sleep(2)
        
    except Exception as e, ::
        logger.error(f"示例执行失败, {e}")
    
    finally,
        # 停止代理
        await agent.stop()
        logger.info("AlignedBaseAgent示例结束")

if __name"__main__":::
    asyncio.run(main())