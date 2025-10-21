import sys
sys.path.append('apps/backend/src')
from ai.token.token_validator import TokenValidator, validate_token_generation_real
import asyncio

async def quick_test():
    validator = TokenValidator()
    result = await validate_token_generation_real('Hello', 'World test', 'test_model')
    print(f'✓ Token验证成功,生成了 {result.total_tokens} 个token')

asyncio.run(quick_test())