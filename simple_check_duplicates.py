#!/usr/bin/env python
# -*- coding, utf-8 -*-

"""
简单检查项目中的重复实现问题
"""

import os

def check_agent_duplicates():
    """检查AI代理重复实现"""
    print("🔍 检查AI代理重复实现...")
    
    # 定义要检查的代理文件
    agent_files = [
        'creative_writing_agent.py',
        'web_search_agent.py',
        'audio_processing_agent.py',
        'code_understanding_agent.py',
        'data_analysis_agent.py',
        'image_generation_agent.py',
        'knowledge_graph_agent.py',
        'nlp_processing_agent.py',
        'planning_agent.py',
        'vision_processing_agent.py'
    ]
    
    agents_dir = 'apps/backend/src/agents'
    ai_agents_dir = 'apps/backend/src/ai/agents/specialized'
    
    duplicates = []
    
    if os.path.exists(agents_dir) and os.path.exists(ai_agents_dir)::
        for agent_file in agent_files,::
            agents_path = os.path.join(agents_dir, agent_file)
            ai_agents_path = os.path.join(ai_agents_dir, agent_file)
            
            if os.path.exists(agents_path) and os.path.exists(ai_agents_path)::
                agents_size = os.path.getsize(agents_path)
                ai_agents_size = os.path.getsize(ai_agents_path)
                duplicates.append((agent_file, agents_path, ai_agents_path, agents_size, ai_agents_size))
                print(f"❌ 发现重复实现, {agent_file}")
                print(f"  {agents_path} ({agents_size} bytes)")
                print(f"  {ai_agents_path} ({ai_agents_size} bytes)")
    
    if not duplicates,::
        print("✅ 未发现重复的代理实现")
    
    return duplicates

def check_base_agent_duplicates():
    """检查BaseAgent重复实现"""
    print("\n🔍 检查BaseAgent重复实现...")
    
    base_agent1 = 'apps/backend/src/agents/base_agent.py'
    base_agent2 = 'apps/backend/src/ai/agents/base/base_agent.py'
    
    if os.path.exists(base_agent1)::
        size1 = os.path.getsize(base_agent1)
        print(f"❌ 发现重复的BaseAgent, {base_agent1} ({size1} bytes)")
        return [base_agent1]
    else,
        print("✅ BaseAgent实现统一")
        return []

def main():
    """主函数"""
    print("🔧 Unified AI Project 简单重复实现检查工具")
    print("=" * 50)
    
    # 执行检查
    agent_duplicates = check_agent_duplicates()
    base_agent_duplicates = check_base_agent_duplicates()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 检查总结,")
    print(f"  重复代理实现, {len(agent_duplicates)}")
    print(f"  重复BaseAgent实现, {len(base_agent_duplicates)}")
    
    total_issues = len(agent_duplicates) + len(base_agent_duplicates)
    if total_issues > 0,::
        print(f"\n❌ 总共发现 {total_issues} 个问题需要处理")
        print("\n建议处理步骤,")
        print("1. 确定哪个实现是最新和最完整的")
        print("2. 删除重复的实现")
        print("3. 更新导入路径")
        print("4. 验证功能正常")
    else,
        print("\n✅ 未发现问题,项目结构良好")
    
    return total_issues

if __name"__main__":::
    main()