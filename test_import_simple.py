print('测试导入...')
try:
    from apps.backend.src.ai.reasoning.real_causal_reasoning_engine import RealCausalReasoningEngine
    print('✅ 导入成功')
except Exception as e:
    print(f'❌ 导入失败: {e}')
    import traceback
    traceback.print_exc()