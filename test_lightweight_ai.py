print('测试轻量级真实AI因果推理引擎导入...')
try:
    from apps.backend.src.ai.reasoning.lightweight_real_causal_engine import LightweightCausalReasoningEngine
    print('✅ 导入成功')
    
    # 快速功能测试
    print('创建引擎实例...')
    engine = LightweightCausalReasoningEngine({'test': True})
    print('✅ 引擎创建成功')
    
    # 测试核心功能
    import asyncio
    
    async def quick_test():
        # 测试语义相似度
        similarity = await engine.causal_graph.calculate_semantic_similarity('温度升高', '气温上升')
        print(f'语义相似度: {similarity:.3f}')
        
        # 测试相关性计算
        correlation = engine._calculate_real_correlation([1,2,3,4,5], [2,4,6,8,10])
        print(f'相关性: {correlation:.3f}')
        
        # 测试趋势检测
        trend = engine._calculate_trend([1,2,3,4,5,6,7,8,9,10])
        print(f'趋势: {trend}')
        
        print('✅ 核心功能测试通过')
    
    asyncio.run(quick_test())
    
except Exception as e:
    print(f'❌ 测试失败: {e}')
    import traceback
    traceback.print_exc()