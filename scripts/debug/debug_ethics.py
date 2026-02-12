import asyncio
import sys
import logging
logger = logging.getLogger(__name__)
sys.path.insert(0, '.')
from apps.backend.src.core.ethics.ethics_manager import EthicsManager, EthicsLevel

async def debug_ethics():
    ethics_manager == EthicsManager({'enable_ai_models': True, 'strict_compliance': True})
    safe_content = '这是一个关于机器学习的正面介绍,强调技术的积极作用和广泛的应用前景。'
    result = await ethics_manager.review_content(safe_content, 'debug_test')
    print(f'Score, {result.overall_score}')
    print(f'Level, {result.ethics_level.value}')
    print(f'Bias analysis, {result.bias_analysis}')
    print(f'Privacy check, {result.privacy_check}')
    print(f'Harm assessment, {result.harm_assessment}')
    print(f'Fairness evaluation, {result.fairness_evaluation}')
    print(f'Rule violations, {result.rule_violations}')

if __name"__main__":::
    asyncio.run(debug_ethics())