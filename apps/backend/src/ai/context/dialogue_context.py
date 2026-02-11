"""对话上下文子系统"""
# Angela Matrix: [L2:MEM] [L4:CTX] Dialogue context subsystem

import logging
import re
# from tests.tools.test_tool_dispatcher_logging import  # Commented out - incomplete import
# from tests.core_ai import  # Commented out - incomplete import
from datetime import datetime
from typing import Any, Dict, List, Optional
# from .manager import  # Commented out - incomplete import
# from .storage.base import  # Commented out - incomplete import

logger = logging.getLogger(__name__)


class Message:
    """消息"""

    def __init__(self, sender: str, content: str, message_type: str = "text") -> None:
        self.message_id = f"msg_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        self.sender = sender
        self.content = content
        self.timestamp = datetime.now()
        self.message_type = message_type
        self.metadata: Dict[str, Any] = {}


class Conversation:
    """对话"""

    def __init__(self, conversation_id: str, participants: List[str]) -> None:
        self.conversation_id = conversation_id
        self.participants = participants
        self.messages: List[Message] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.context_summary: Optional['ContextSummary'] = None

    def add_message(self, message: Message):
        """添加消息"""
        self.messages.append(message)

    def complete(self):
        """完成对话"""
        self.end_time = datetime.now()


class ContextSummary:
    """上下文摘要"""

    def __init__(self) -> None:
        self.key_points: List[str] = []
        self.entities: List[str] = []
        self.intents: List[str] = []
        self.sentiment: str = "neutral"
        self.relevance_score: float = 0.0


class DialogueContextManager:
    """对话上下文管理器"""

    def __init__(self, context_manager) -> None:
        self.context_manager = context_manager
        self.conversations: Dict[str, Conversation] = {}

    def start_conversation(self, conversation_id: str, participants: List[str]) -> bool:
        """开始对话"""
        try:
            conversation = Conversation(conversation_id, participants)
            self.conversations[conversation_id] = conversation

            # 创建对应的上下文
            context_content = {
                "conversation": {
                    "conversation_id": conversation_id,
                    "participants": participants,
                    "start_time": conversation.start_time.isoformat(),
                    "status": "active"
                }
            }

            # context_id = self.context_manager.create_context(ContextType.DIALOGUE, context_content)  # Commented - needs proper import
            logger.info(f"Started conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start conversation {conversation_id}: {e}")
            return False

    def add_message(self, conversation_id: str, sender: str, content: str, message_type: str = "text") -> bool:
        """添加消息"""
        try:
            if conversation_id not in self.conversations:
                logger.error(f"Conversation {conversation_id} not found")
                return False

            conversation = self.conversations[conversation_id]
            message = Message(sender, content, message_type)
            conversation.add_message(message)

            # 创建对应的上下文
            context_content = {
                "message": {
                    "message_id": message.message_id,
                    "conversation_id": conversation_id,
                    "sender": sender,
                    "content": content,
                    "timestamp": message.timestamp.isoformat(),
                    "message_type": message_type
                }
            }

            # context_id = self.context_manager.create_context(ContextType.DIALOGUE, context_content)  # Commented - needs proper import
            logger.info(f"Added message to conversation {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add message to conversation {conversation_id}: {e}")
            return False

    def extract_key_points(self, text: str) -> List[str]:
        """提取关键点"""
        # 简单的关键点提取实现
        # 在实际应用中, 这可能涉及更复杂的NLP处理
        sentences = re.split(r'[.!?]+\s+', text)
        key_points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # 过滤太短的句子
                # 简单的关键词提取
                words = sentence.split()
                if len(words) > 3:  # 过滤太短的句子
                    key_points.append(sentence)

        return key_points[:5]  # 限制返回5个关键点

    def extract_entities(self, text: str) -> List[str]:
        """提取实体"""
        # 简单的实体提取实现
        # 在实际应用中, 这可能涉及NER等技术
        entities = []

        # 简单的模式匹配
        # 匹配邮箱
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        entities.extend(emails)

        # 匹配URL
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        entities.extend(urls)

        # 匹配日期
        dates = re.findall(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}', text)
        entities.extend(dates)

        return list(set(entities))  # 去重

    def analyze_sentiment(self, text: str) -> str:
        """分析情感"""
        # 简单的情感分析实现
        # 在实际应用中, 这可能涉及更复杂的情感分析模型
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disgusting', 'pathetic']

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def generate_context_summary(self, conversation_id: str) -> Optional[ContextSummary]:
        """生成上下文摘要"""
        try:
            if conversation_id not in self.conversations:
                logger.error(f"Conversation {conversation_id} not found")
                return None

            conversation = self.conversations[conversation_id]

            # 收集所有消息内容
            all_content = " ".join([msg.content for msg in conversation.messages])

            # 提取关键点
            key_points = self.extract_key_points(all_content)

            # 提取实体
            entities = self.extract_entities(all_content)

            # 分析情感
            sentiment = self.analyze_sentiment(all_content)

            # 创建摘要
            summary = ContextSummary()
            summary.key_points = key_points
            summary.entities = entities
            summary.sentiment = sentiment
            summary.relevance_score = min(1.0, len(all_content) / 1000.0)  # 简单的相关性评分

            # 保存摘要到对话
            conversation.context_summary = summary

            # 创建对应的上下文
            context_content = {
                "context_summary": {
                    "conversation_id": conversation_id,
                    "key_points": key_points,
                    "entities": entities,
                    "sentiment": sentiment,
                    "relevance_score": summary.relevance_score,
                    "generated_at": datetime.now().isoformat()
                }
            }

            # context_id = self.context_manager.create_context(ContextType.DIALOGUE, context_content)  # Commented - needs proper import
            logger.info(f"Generated context summary for conversation {conversation_id}")
            return summary
        except Exception as e:
            logger.error(f"Failed to generate context summary for conversation {conversation_id}: {e}")
            return None

    def get_conversation_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取对话上下文"""
        try:
            if conversation_id not in self.conversations:
                logger.error(f"Conversation {conversation_id} not found")
                return None

            conversation = self.conversations[conversation_id]

            # 搜索相关的上下文
            # contexts = self.context_manager.search_contexts(conversation_id, [ContextType.DIALOGUE])  # Commented - needs proper import

            # if not contexts:
            #     logger.debug(f"No context found for conversation {conversation_id}")
            #     return None

            # 返回最新的上下文
            # latest_context = max(contexts, key=lambda c: c.updated_at)
            # return {
            #     "context_id": latest_context.context_id,
            #     "content": latest_context.content,
            #     "metadata": latest_context.metadata,
            #     "updated_at": latest_context.updated_at.isoformat()
            # }
            return None
        except Exception as e:
            logger.error(f"Failed to get context for conversation {conversation_id}: {e}")
            return None

    def get_recent_conversations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近的对话"""
        try:
            # 按开始时间排序对话
            sorted_conversations = sorted(
                self.conversations.values(),
                key=lambda c: c.start_time,
                reverse=True
            )

            # 限制返回数量
            recent_conversations = sorted_conversations[:limit]

            # 转换为字典格式
            result = []
            for conv in recent_conversations:
                conv_info = {
                    "conversation_id": conv.conversation_id,
                    "participants": conv.participants,
                    "start_time": conv.start_time.isoformat(),
                    "message_count": len(conv.messages)
                }

                if conv.end_time:
                    conv_info["end_time"] = conv.end_time.isoformat()
                if conv.context_summary:
                    conv_info["summary"] = {
                        "key_points_count": len(conv.context_summary.key_points),
                        "entities_count": len(conv.context_summary.entities),
                        "sentiment": conv.context_summary.sentiment
                    }

                result.append(conv_info)

            return result
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []

    def transfer_context(self, source_conversation_id: str, target_conversation_id: str) -> bool:
        """传递对话上下文"""
        try:
            if source_conversation_id not in self.conversations:
                logger.error(f"Source conversation {source_conversation_id} not found")
                return False

            if target_conversation_id not in self.conversations:
                logger.error(f"Target conversation {target_conversation_id} not found")
                return False

            source_conv = self.conversations[source_conversation_id]
            target_conv = self.conversations[target_conversation_id]

            # 如果源对话有摘要, 将其传递给目标对话
            if source_conv.context_summary:
                target_conv.context_summary = source_conv.context_summary
                # 创建上下文记录传递
                context_content = {
                    "context_transfer": {
                        "source_conversation_id": source_conversation_id,
                        "target_conversation_id": target_conversation_id,
                        "transfer_time": datetime.now().isoformat(),
                        "summary_transferred": True
                    }
                }

                # context_id = self.context_manager.create_context(ContextType.DIALOGUE, context_content)  # Commented - needs proper import
                logger.info(f"Transferred context from {source_conversation_id} to {target_conversation_id}")
                return True

            logger.debug(f"No context summary to transfer from {source_conversation_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to transfer context from {source_conversation_id} to {target_conversation_id}: {e}")
            return False
