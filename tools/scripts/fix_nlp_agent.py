#!/usr/bin/env python3
"""
修复NLP处理代理文件的语法错误
"""

import re
from pathlib import Path

def fix_nlp_agent_file():
    """修复NLP处理代理文件"""
    file_path = Path("apps/backend/src/ai/agents/specialized/nlp_processing_agent.py")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复各种语法错误
        # 1. 修复类定义后的缩进问题
        content = re.sub(r'class NLPProcessingAgent\(BaseAgent\):\s*\n\s*"""', 
                        'class NLPProcessingAgent(BaseAgent):\n    """', content)
        
        # 2. 修复__init__方法的缩进和语法
        content = re.sub(r'def __init__\(self, agent_id: str\) -> None:\s*\n\s*capabilities', 
                        'def __init__(self, agent_id: str) -> None:\n        capabilities', content)
        
        # 3. 修复参数定义中的语法错误
        content = content.replace('"required" False', '"required": False')
        content = content.replace('"description" "Desired summary length', '"description": "Desired summary length')
        
        # 4. 修复字典和列表定义中的语法错误
        content = content.replace(':\n                ],', ',\n                ],')
        content = content.replace('::\n    async def handle_task_request', ':\n    async def handle_task_request')
        content = content.replace(':\n        logging.info', ':\n        logging.info')
        content = content.replace('::\n            if "text_summarization"', ':\n            if "text_summarization"')
        content = content.replace('::\n            elif "sentiment_analysis"', ':\n            elif "sentiment_analysis"')
        content = content.replace('::\n            elif "entity_extraction"', ':\n            elif "entity_extraction"')
        content = content.replace('::\n            elif "language_detection"', ':\n            elif "language_detection"')
        content = content.replace('::\n            else:', ':\n            else:')
        content = content.replace('::\n        except Exception as e:', ':\n        except Exception as e:')
        content = content.replace(':\n            logging.info', ':\n            logging.info')
        content = content.replace('::\n    def _generate_text_summary', ':\n    def _generate_text_summary')
        content = content.replace(':\n    summary_length', ':\n        summary_length')
        content = content.replace('::\n            raise ValueError', ':\n            raise ValueError')
        content = content.replace('::\n        if not sentences', ':\n        if not sentences')
        content = content.replace('::\n            return', ':\n            return')
        content = content.replace('::\n        if summary_length', ':\n        if summary_length')
        content = content.replace('::\n            num_sentences', ':\n            num_sentences')
        content = content.replace('::\n        else:', ':\n        else:')
        content = content.replace('::\n    def _perform_sentiment_analysis', ':\n    def _perform_sentiment_analysis')
        content = content.replace('::\n        if not text', ':\n        if not text')
        content = content.replace('::\n        positive_count', ':\n        positive_count')
        content = content.replace('::\n        negative_count', ':\n        negative_count')
        content = content.replace('::\n        neutral_count', ':\n        neutral_count')
        content = content.replace('::\n        if total_sentiment_words', ':\n        if total_sentiment_words')
        content = content.replace('::\n            polarity', ':\n            polarity')
        content = content.replace('::\n            overall_sentiment', ':\n            overall_sentiment')
        content = content.replace('::\n        elif polarity', ':\n        elif polarity')
        content = content.replace('::\n        else:', ':\n        else:')
        content = content.replace('::\n    def _extract_entities', ':\n    def _extract_entities')
        content = content.replace('::\n        if not text', ':\n        if not text')
        content = content.replace('::\n        persons', ':\n        persons')
        content = content.replace('::\n        organizations', ':\n        organizations')
        content = content.replace('::\n        locations', ':\n        locations')
        content = content.replace('::\n    def _detect_language', ':\n    def _detect_language')
        content = content.replace('::\n        if not text', ':\n        if not text')
        content = content.replace('::\n        if total_chars', ':\n        if total_chars')
        content = content.replace('::\n    char_scores', ':\n        char_scores')
        content = content.replace('::\n    detected_language', ':\n        detected_language')
        content = content.replace('::\n        if confidence', ':\n        if confidence')
        content = content.replace('::\n            common_english_words', ':\n            common_english_words')
        content = content.replace('::\n            english_word_count', ':\n            english_word_count')
        content = content.replace('::\n    if __name__', ':\n\nif __name__')
        content = content.replace('::\n    async def main', ':\n    async def main')
        content = content.replace('::\n    try:', ':\n    try:')
        content = content.replace('::\n    except KeyboardInterrupt', ':\n    except KeyboardInterrupt')
        
        # 修复函数参数定义
        content = re.sub(r'def _generate_text_summary\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        'def _generate_text_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _perform_sentiment_analysis\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        'def _perform_sentiment_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _extract_entities\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        'def _extract_entities(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _detect_language\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        'def _detect_language(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        
        # 修复文本中的语法错误
        content = content.replace('text summarization,:', 'text summarization:')
        content = content.replace('{"name": "summary_length", "type": "string", "required" False, "description" "Desired summary length (short, medium, long)"}', 
                                '{"name": "summary_length", "type": "string", "required": False, "description": "Desired summary length (short, medium, long)"}')
        
        # 修复多余的冒号
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for sentiment analysis"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for sentiment analysis"}')
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for entity extraction"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for entity extraction"}')
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for language detection"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for language detection"}')
        
        # 修复缩进问题
        content = content.replace('logging.info(f"[{self.agent_id}] NLPProcessingAgent initialized with capabilities: {[cap[\'name\'] for cap in capabilities]}")::', 
                                '        logging.info(f"[{self.agent_id}] NLPProcessingAgent initialized with capabilities: {[cap[\'name\'] for cap in capabilities]}")')
        
        # 修复main函数部分
        content = content.replace('async def main() -> None:\s*\n\s*agent_id', 
                                'async def main() -> None:\n        agent_id')
        content = content.replace('agent = NLPProcessingAgent(agent_id=agent_id)\s*\n\s*await agent.start()', 
                                '        agent = NLPProcessingAgent(agent_id=agent_id)\n        await agent.start()')
        content = content.replace('try:\s*\n\s*asyncio.run(main())', 
                                '    try:\n        asyncio.run(main())')
        content = content.replace('except KeyboardInterrupt:\s*\n\s*print', 
                                '    except KeyboardInterrupt:\n        print')
        
        # 添加缺失的return语句
        content = re.sub(r'(def _create_success_payload.*?\n\s*HSPTaskResultPayload\(.*?\n\s*\))\s*\n', 
                        r'\1\n        return \1\n', content)
        content = re.sub(r'(def _create_failure_payload.*?\n\s*HSPTaskResultPayload\(.*?\n\s*\))\s*\n', 
                        r'\1\n        return \1\n', content)
        
        # 修复函数定义中的语法错误
        content = re.sub(r'def _generate_text_summary\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        'def _generate_text_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✓ 成功修复NLP处理代理文件: {file_path}")
        return True
    except Exception as e:
        print(f"✗ 修复NLP处理代理文件时出错: {file_path} - {e}")
        return False

def main():
    """主函数"""
    print("开始修复NLP处理代理文件...")
    print("=" * 50)
    
    if fix_nlp_agent_file():
        print("\n" + "=" * 50)
        print("✓ NLP处理代理文件修复完成!")
    else:
        print("\n" + "=" * 50)
        print("✗ NLP处理代理文件修复失败!")
    
    return 0

if __name__ == "__main__":
    exit(main())