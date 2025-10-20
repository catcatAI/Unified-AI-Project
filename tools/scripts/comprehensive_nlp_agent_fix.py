#!/usr/bin/env python3
"""
全面修复NLP处理代理文件的语法错误
"""

import re
from pathlib import Path

def fix_nlp_agent_comprehensive():
    """全面修复NLP处理代理文件"""
    file_path = Path("apps/backend/src/ai/agents/specialized/nlp_processing_agent.py")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复类定义后的缩进
        content = re.sub(r'class NLPProcessingAgent\(BaseAgent\):\s*\n\s*"""', 
                        'class NLPProcessingAgent(BaseAgent):\n    """', content)
        
        # 修复__init__方法
        content = re.sub(r'def __init__\(self, agent_id: str\) -> None:\s*\n\s*capabilities = \[', 
                        'def __init__(self, agent_id: str) -> None:\n        capabilities = [', content)
        
        # 修复capabilities列表的缩进
        content = re.sub(r'\s*]\s*\n\s*super\(\).__init__\(agent_id=agent_id, capabilities=capabilities\)', 
                        '\n        ]\n        super().__init__(agent_id=agent_id, capabilities=capabilities)', content)
        
        # 修复logging语句的缩进
        content = re.sub(r'\s*logging.info\(f"\[\{self.agent_id\}\] NLPProcessingAgent initialized with capabilities: \{\[cap\[\'name\'\] for cap in capabilities\]\}"\):', 
                        '\n        logging.info(f"[{self.agent_id}] NLPProcessingAgent initialized with capabilities: {[cap[\'name\'] for cap in capabilities]}")', content)
        
        # 修复handle_task_request方法
        content = re.sub(r'async def handle_task_request\(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope\):\s*\n\s*request_id', 
                        '    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):\n        request_id', content)
        
        # 修复参数定义中的语法错误
        content = content.replace('"required" False', '"required": False')
        content = content.replace('"description" "Desired summary length', '"description": "Desired summary length')
        
        # 修复字典和列表定义中的语法错误
        content = content.replace('{"name": "summary_length", "type": "string", "required" False, "description" "Desired summary length (short, medium, long)"}', 
                                '{"name": "summary_length", "type": "string", "required": False, "description": "Desired summary length (short, medium, long)"}')
        
        # 修复多余的冒号
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for sentiment analysis"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for sentiment analysis"}')
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for entity extraction"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for entity extraction"}')
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for language detection"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for language detection"}')
        
        # 修复条件语句中的语法错误
        content = content.replace('if "text_summarization" in capability_id::', '            if "text_summarization" in capability_id:')
        content = content.replace('elif "sentiment_analysis" in capability_id::', '            elif "sentiment_analysis" in capability_id:')
        content = content.replace('elif "entity_extraction" in capability_id::', '            elif "entity_extraction" in capability_id:')
        content = content.replace('elif "language_detection" in capability_id::', '            elif "language_detection" in capability_id:')
        content = content.replace('else:', '            else:')
        content = content.replace('except Exception as e::', '        except Exception as e:')
        
        # 修复文本中的语法错误
        content = content.replace('text summarization,:', 'text summarization:')
        
        # 修复函数定义
        content = re.sub(r'def _generate_text_summary\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        '    def _generate_text_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _perform_sentiment_analysis\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        '    def _perform_sentiment_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _extract_entities\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        '    def _extract_entities(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _detect_language\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        '    def _detect_language(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        
        # 修复函数体内的缩进
        content = re.sub(r'\s*text = params.get\(\'text\', \'\'\):\s*\n\s*summary_length', 
                        '\n        text = params.get(\'text\', \'\')\n        summary_length', content)
        content = re.sub(r'\s*text = params.get\(\'text\', \'\'\):\s*\n\s*if not text', 
                        '\n        text = params.get(\'text\', \'\')\n        if not text', content)
        
        # 修复if语句
        content = content.replace('if not text::', '        if not text:')
        content = content.replace('if not sentences::', '        if not sentences:')
        content = content.replace('if summary_length == \'short\'::', '        if summary_length == \'short\':')
        content = content.replace('elif summary_length == \'long\'::', '        elif summary_length == \'long\':')
        content = content.replace('else:  # medium::', '        else:  # medium')
        content = content.replace('if total_sentiment_words == 0::', '        if total_sentiment_words == 0:')
        content = content.replace('if polarity > 0.1::', '        if polarity > 0.1:')
        content = content.replace('elif polarity < -0.1::', '        elif polarity < -0.1:')
        content = content.replace('else::', '        else:')
        content = content.replace('if total_chars == 0::', '        if total_chars == 0:')
        content = content.replace('if confidence < 0.3::', '        if confidence < 0.3:')
        
        # 修复循环语句
        content = content.replace('for sentence in sentences::', '        for sentence in sentences:')
        content = content.replace('positive_count = sum(1 for word in words if word in positive_words)::', 
                                '        positive_count = sum(1 for word in words if word in positive_words)')
        content = content.replace('negative_count = sum(1 for word in words if word in negative_words)::', 
                                '        negative_count = sum(1 for word in words if word in negative_words)')
        content = content.replace('neutral_count = sum(1 for word in words if word in neutral_words)::', 
                                '        neutral_count = sum(1 for word in words if word in neutral_words)')
        content = content.replace('persons = [p for p in persons if len(p) > 1 and p.lower() not in {\'The\', \'This\', \'That\', \'These\', \'Those\'}]::', 
                                '        persons = [p for p in persons if len(p) > 1 and p.lower() not in {\'The\', \'This\', \'That\', \'These\', \'Those\'}]')
        content = content.replace('organizations = [o for o in organizations if len(o) > 2 and o not in persons]::', 
                                '        organizations = [o for o in organizations if len(o) > 2 and o not in persons]')
        content = content.replace('locations = [l for l in locations if len(l) > 2]::', 
                                '        locations = [l for l in locations if len(l) > 2]')
        
        # 修复return语句
        content = content.replace('return {"summary": "", "original_length": len(text), "summary_length": 0}::', 
                                '            return {"summary": "", "original_length": len(text), "summary_length": 0}')
        content = content.replace('summary = \'. \'.join([s[0] for s in top_sentences]) + \'.\':', 
                                '        summary = \'. \'.join([s[0] for s in top_sentences]) + \'.\'')
        content = content.replace('sentiment_words_ratio: round(total_sentiment_words / len(words), 3) if len(words) > 0 else 0:', 
                                'sentiment_words_ratio: round(total_sentiment_words / len(words), 3) if len(words) > 0 else 0')
        
        # 修复main函数部分
        content = re.sub(r'if __name__ == \'__main__\'::\s*\n\s*async def main\(\) -> None:', 
                        'if __name__ == \'__main__\':\n    async def main() -> None:', content)
        content = re.sub(r'agent_id = f"did:hsp:nlp_processing_agent_\{uuid.uuid4\(\).hex\[:6\]\}"\s*\n\s*agent = NLPProcessingAgent\(agent_id=agent_id\)\s*\n\s*await agent.start\(\)', 
                        '        agent_id = f"did:hsp:nlp_processing_agent_{uuid.uuid4().hex[:6]}"\n        agent = NLPProcessingAgent(agent_id=agent_id)\n        await agent.start()', content)
        content = re.sub(r'try:\s*\n\s*asyncio.run\(main\(\)\)', 
                        '    try:\n        asyncio.run(main())', content)
        content = re.sub(r'except KeyboardInterrupt::\s*\n\s*print', 
                        '    except KeyboardInterrupt:\n        print', content)
        
        # 修复多余的冒号和语法错误
        content = content.replace('::\n', ':\n')
        content = content.replace(':\n\n', ':\n')
        
        # 修复函数返回类型声明
        content = re.sub(r'(def _create_success_payload.*?->).*?:', r'\1 HSPTaskResultPayload:', content)
        content = re.sub(r'(def _create_failure_payload.*?->).*?:', r'\1 HSPTaskResultPayload:', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✓ 成功全面修复NLP处理代理文件: {file_path}")
        return True
    except Exception as e:
        print(f"✗ 全面修复NLP处理代理文件时出错: {file_path} - {e}")
        return False

def main():
    """主函数"""
    print("开始全面修复NLP处理代理文件...")
    print("=" * 50)
    
    if fix_nlp_agent_comprehensive():
        print("\n" + "=" * 50)
        print("✓ NLP处理代理文件全面修复完成!")
    else:
        print("\n" + "=" * 50)
        print("✗ NLP处理代理文件全面修复失败!")
    
    return 0

if __name__ == "__main__":
    exit(main())#!/usr/bin/env python3
"""
全面修复NLP处理代理文件的语法错误
"""


def fix_nlp_agent_comprehensive():
    """全面修复NLP处理代理文件"""
    file_path = Path("apps/backend/src/ai/agents/specialized/nlp_processing_agent.py")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复类定义后的缩进
        content = re.sub(r'class NLPProcessingAgent\(BaseAgent\):\s*\n\s*"""', 
                        'class NLPProcessingAgent(BaseAgent):\n    """', content)
        
        # 修复__init__方法
        content = re.sub(r'def __init__\(self, agent_id: str\) -> None:\s*\n\s*capabilities = \[', 
                        'def __init__(self, agent_id: str) -> None:\n        capabilities = [', content)
        
        # 修复capabilities列表的缩进
        content = re.sub(r'\s*]\s*\n\s*super\(\).__init__\(agent_id=agent_id, capabilities=capabilities\)', 
                        '\n        ]\n        super().__init__(agent_id=agent_id, capabilities=capabilities)', content)
        
        # 修复logging语句的缩进
        content = re.sub(r'\s*logging.info\(f"\[\{self.agent_id\}\] NLPProcessingAgent initialized with capabilities: \{\[cap\[\'name\'\] for cap in capabilities\]\}"\):', 
                        '\n        logging.info(f"[{self.agent_id}] NLPProcessingAgent initialized with capabilities: {[cap[\'name\'] for cap in capabilities]}")', content)
        
        # 修复handle_task_request方法
        content = re.sub(r'async def handle_task_request\(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope\):\s*\n\s*request_id', 
                        '    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):\n        request_id', content)
        
        # 修复参数定义中的语法错误
        content = content.replace('"required" False', '"required": False')
        content = content.replace('"description" "Desired summary length', '"description": "Desired summary length')
        
        # 修复字典和列表定义中的语法错误
        content = content.replace('{"name": "summary_length", "type": "string", "required" False, "description" "Desired summary length (short, medium, long)"}', 
                                '{"name": "summary_length", "type": "string", "required": False, "description": "Desired summary length (short, medium, long)"}')
        
        # 修复多余的冒号
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for sentiment analysis"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for sentiment analysis"}')
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for entity extraction"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for entity extraction"}')
        content = content.replace('{"name": "text", "type": "string", "required": True, "description": "Text content for language detection"}:', 
                                '{"name": "text", "type": "string", "required": True, "description": "Text content for language detection"}')
        
        # 修复条件语句中的语法错误
        content = content.replace('if "text_summarization" in capability_id::', '            if "text_summarization" in capability_id:')
        content = content.replace('elif "sentiment_analysis" in capability_id::', '            elif "sentiment_analysis" in capability_id:')
        content = content.replace('elif "entity_extraction" in capability_id::', '            elif "entity_extraction" in capability_id:')
        content = content.replace('elif "language_detection" in capability_id::', '            elif "language_detection" in capability_id:')
        content = content.replace('else:', '            else:')
        content = content.replace('except Exception as e::', '        except Exception as e:')
        
        # 修复文本中的语法错误
        content = content.replace('text summarization,:', 'text summarization:')
        
        # 修复函数定义
        content = re.sub(r'def _generate_text_summary\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        '    def _generate_text_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _perform_sentiment_analysis\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        '    def _perform_sentiment_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _extract_entities\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        '    def _extract_entities(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        content = re.sub(r'def _detect_language\(self, params: Dict\[.*?\]\s*\n\s*"""', 
                        '    def _detect_language(self, params: Dict[str, Any]) -> Dict[str, Any]:\n        """', content)
        
        # 修复函数体内的缩进
        content = re.sub(r'\s*text = params.get\(\'text\', \'\'\):\s*\n\s*summary_length', 
                        '\n        text = params.get(\'text\', \'\')\n        summary_length', content)
        content = re.sub(r'\s*text = params.get\(\'text\', \'\'\):\s*\n\s*if not text', 
                        '\n        text = params.get(\'text\', \'\')\n        if not text', content)
        
        # 修复if语句
        content = content.replace('if not text::', '        if not text:')
        content = content.replace('if not sentences::', '        if not sentences:')
        content = content.replace('if summary_length == \'short\'::', '        if summary_length == \'short\':')
        content = content.replace('elif summary_length == \'long\'::', '        elif summary_length == \'long\':')
        content = content.replace('else:  # medium::', '        else:  # medium')
        content = content.replace('if total_sentiment_words == 0::', '        if total_sentiment_words == 0:')
        content = content.replace('if polarity > 0.1::', '        if polarity > 0.1:')
        content = content.replace('elif polarity < -0.1::', '        elif polarity < -0.1:')
        content = content.replace('else::', '        else:')
        content = content.replace('if total_chars == 0::', '        if total_chars == 0:')
        content = content.replace('if confidence < 0.3::', '        if confidence < 0.3:')
        
        # 修复循环语句
        content = content.replace('for sentence in sentences::', '        for sentence in sentences:')
        content = content.replace('positive_count = sum(1 for word in words if word in positive_words)::', 
                                '        positive_count = sum(1 for word in words if word in positive_words)')
        content = content.replace('negative_count = sum(1 for word in words if word in negative_words)::', 
                                '        negative_count = sum(1 for word in words if word in negative_words)')
        content = content.replace('neutral_count = sum(1 for word in words if word in neutral_words)::', 
                                '        neutral_count = sum(1 for word in words if word in neutral_words)')
        content = content.replace('persons = [p for p in persons if len(p) > 1 and p.lower() not in {\'The\', \'This\', \'That\', \'These\', \'Those\'}]::', 
                                '        persons = [p for p in persons if len(p) > 1 and p.lower() not in {\'The\', \'This\', \'That\', \'These\', \'Those\'}]')
        content = content.replace('organizations = [o for o in organizations if len(o) > 2 and o not in persons]::', 
                                '        organizations = [o for o in organizations if len(o) > 2 and o not in persons]')
        content = content.replace('locations = [l for l in locations if len(l) > 2]::', 
                                '        locations = [l for l in locations if len(l) > 2]')
        
        # 修复return语句
        content = content.replace('return {"summary": "", "original_length": len(text), "summary_length": 0}::', 
                                '            return {"summary": "", "original_length": len(text), "summary_length": 0}')
        content = content.replace('summary = \'. \'.join([s[0] for s in top_sentences]) + \'.\':', 
                                '        summary = \'. \'.join([s[0] for s in top_sentences]) + \'.\'')
        content = content.replace('sentiment_words_ratio: round(total_sentiment_words / len(words), 3) if len(words) > 0 else 0:', 
                                'sentiment_words_ratio: round(total_sentiment_words / len(words), 3) if len(words) > 0 else 0')
        
        # 修复main函数部分
        content = re.sub(r'if __name__ == \'__main__\'::\s*\n\s*async def main\(\) -> None:', 
                        'if __name__ == \'__main__\':\n    async def main() -> None:', content)
        content = re.sub(r'agent_id = f"did:hsp:nlp_processing_agent_\{uuid.uuid4\(\).hex\[:6\]\}"\s*\n\s*agent = NLPProcessingAgent\(agent_id=agent_id\)\s*\n\s*await agent.start\(\)', 
                        '        agent_id = f"did:hsp:nlp_processing_agent_{uuid.uuid4().hex[:6]}"\n        agent = NLPProcessingAgent(agent_id=agent_id)\n        await agent.start()', content)
        content = re.sub(r'try:\s*\n\s*asyncio.run\(main\(\)\)', 
                        '    try:\n        asyncio.run(main())', content)
        content = re.sub(r'except KeyboardInterrupt::\s*\n\s*print', 
                        '    except KeyboardInterrupt:\n        print', content)
        
        # 修复多余的冒号和语法错误
        content = content.replace('::\n', ':\n')
        content = content.replace(':\n\n', ':\n')
        
        # 修复函数返回类型声明
        content = re.sub(r'(def _create_success_payload.*?->).*?:', r'\1 HSPTaskResultPayload:', content)
        content = re.sub(r'(def _create_failure_payload.*?->).*?:', r'\1 HSPTaskResultPayload:', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✓ 成功全面修复NLP处理代理文件: {file_path}")
        return True
    except Exception as e:
        print(f"✗ 全面修复NLP处理代理文件时出错: {file_path} - {e}")
        return False

def main():
    """主函数"""
    print("开始全面修复NLP处理代理文件...")
    print("=" * 50)
    
    if fix_nlp_agent_comprehensive():
        print("\n" + "=" * 50)
        print("✓ NLP处理代理文件全面修复完成!")
    else:
        print("\n" + "=" * 50)
        print("✗ NLP处理代理文件全面修复失败!")
    
    return 0

if __name__ == "__main__":
    exit(main())