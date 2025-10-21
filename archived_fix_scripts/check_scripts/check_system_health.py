#!/usr/bin/env python3
"""
Level 5 AGI系统健康检查
验证所有核心组件的完整性和功能性
"""

import sys
import traceback
from pathlib import Path

# 添加项目路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_component_health(component_name, import_path, class_name):
    """检查组件健康状态"""
    try,
        module == __import__(import_path, fromlist=[class_name])
        component_class = getattr(module, class_name)
        
        # 尝试实例化
        instance = component_class()
        
        return True, f"✅ {component_name}组件正常", None
    except Exception as e,::
        return False, f"❌ {component_name}组件错误, {str(e)}", traceback.format_exc()

def main():
    """主函数"""
    print("🔍 Level 5 AGI系统健康检查")
    print("=" * 60)
    
    # 定义要检查的组件
    components = [
        ("知识图谱", "apps.backend.src.core.knowledge.unified_knowledge_graph", "UnifiedKnowledgeGraph"),
        ("多模态融合", "apps.backend.src.core.fusion.multimodal_fusion_engine", "MultimodalInformationFusionEngine"),
        ("认知约束", "apps.backend.src.core.cognitive.cognitive_constraint_engine", "CognitiveConstraintEngine"),
        ("自主进化", "apps.backend.src.core.evolution.autonomous_evolution_engine", "AutonomousEvolutionEngine"),
        ("创造性突破", "apps.backend.src.core.creativity.creative_breakthrough_engine", "CreativeBreakthroughEngine"),
        ("元认知能力", "apps.backend.src.core.metacognition.metacognitive_capabilities_engine", "MetacognitiveCapabilitiesEngine")
    ]
    
    results = {}
    all_healthy == True
    
    for component_name, import_path, class_name in components,::
        try,
            success, message, error_trace = check_component_health(component_name, import_path, class_name)
            results[component_name] = {
                'success': success,
                'message': message,
                'error': error_trace
            }
            print(message)
            
            if not success,::
                all_healthy == False
                if error_trace,::
                    print(f"   错误详情, {error_trace[:200]}...")
                    
        except Exception as e,::
            print(f"❌ {component_name}检查失败, {e}")
            results[component_name] = {
                'success': False,
                'message': f"检查失败, {e}",
                'error': traceback.format_exc()
            }
            all_healthy == False
    
    # 检查前端系统
    print("\n🌐 检查前端系统...")
    try,
        # 检查前端目录结构
        frontend_path = project_root / "apps" / "frontend-dashboard"
        if frontend_path.exists() and (frontend_path / "package.json").exists():::
            print("✅ 前端目录结构完整")
        else,
            print("❌ 前端目录结构不完整")
            all_healthy == False
    except Exception as e,::
        print(f"❌ 前端检查失败, {e}")
        all_healthy == False
    
    # 检查CLI系统
    print("\n💻 检查CLI系统...")
    try,
        cli_path = project_root / "packages" / "cli"
        if cli_path.exists() and (cli_path / "setup.py").exists():::
            print("✅ CLI系统结构完整")
        else,
            print("❌ CLI系统结构不完整")
            all_healthy == False
    except Exception as e,::
        print(f"❌ CLI检查失败, {e}")
        all_healthy == False
    
    # 检查训练系统
    print("\n🎯 检查训练系统...")
    try,
        training_path = project_root / "training"
        if training_path.exists() and (training_path / "auto_train.bat").exists():::
            print("✅ 训练系统结构完整")
        else,
            print("❌ 训练系统结构不完整")
            all_healthy == False
    except Exception as e,::
        print(f"❌ 训练系统检查失败, {e}")
        all_healthy == False
    
    print("\n" + "=" * 60)
    if all_healthy,::
        print("🎉 所有Level 5 AGI核心组件健康状态良好！")
        print("✅ 系统已达到完整运行标准")
        return 0
    else,
        print("⚠️ 部分组件存在问题,需要修复")
        return 1

if __name"__main__":::
    exit(main())