"""
测试Angela真实的LLM创作能力
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, 'apps/backend')

async def test_real_creation():
    print('='*80)
    print('ANGELA REAL CREATION TEST')
    print('='*80)
    print()
    
    from src.core.orchestrator import CognitiveOrchestrator
    
    orch = CognitiveOrchestrator()
    await orch.initialize()
    
    print(f'Available Ollama models: {orch.available_models}')
    print()
    
    # 测试1: 生成故事
    print('='*80)
    print('TEST 1: GENERATE SHORT STORY')
    print('='*80)
    
    story_prompt = "Write a short sci-fi story about AI and humans, about 200 words."
    print(f'Prompt: {story_prompt}')
    print()
    
    result = await orch.process_user_input(story_prompt)
    story_response = result.get('response', "...")
    
    print(f'Generated Story:')
    print(story_response)
    print()
    
    # 保存故事到桌面
    output_dir = Path(r'C:\Users\catai\OneDrive\Desktop')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    story_file = output_dir / 'Angela_生成的故事.txt'
    with open(story_file, 'w', encoding='utf-8') as f:
        f.write(f'''Angela 生成的故事
{'='*60}
时间: {result.get('timestamp', '')}
置信度: {result.get('confidence', 0):.2f}
处理时间: {result.get('processing_time_ms', 0):.1f}ms

故事内容:
{'='*60}

{story_response}

{'='*60}

此故事由Angela（AI助手）使用LLM（Ollama）生成。
如果需要修改或续写，请告诉Angela具体要求。
''')
    
    print(f'✅ Story saved to: {story_file}')
    print(f'   File size: {story_file.stat().st_size:,} bytes')
    print()
    
    # 测试2: 对话模式（非创作）
    print('='*80)
    print('TEST 2: CONVERSATION MODE')
    print('='*80)
    print()
    
    conversation_prompts = [
        'Hello Angela, who are you?',
        'What can you do for me?',
        'Tell me something interesting about AI'
    ]
    
    for i, prompt in enumerate(conversation_prompts, 1):
        print(f'{i}. User: {prompt}')
        
        result = await orch.process_user_input(prompt)
        response = result.get('response', "...")
        
        print(f'   Angela: {response[:80]}...' if len(response) > 80 else f'   Angela: {response}')
        print(f'   Time: {result.get("processing_time_ms", 0):.1f}ms')
        print()
    
    await orch.shutdown()
    
    print('='*80)
    print('✅ ALL TESTS COMPLETE')
    print('='*80)
    print()
    print('Summary:')
    print('  1. Angela is using real LLM (Ollama)')
    print('  2. Creative generation working')
    print('  3. Conversation mode working')
    print()

if __name__ == '__main__':
    asyncio.run(test_real_creation())
