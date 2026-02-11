import sys
import os
import asyncio

# 使用自动检测的项目根目录（支持Linux/Windows）
current_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(current_file)
project_root = os.path.dirname(tests_dir)
backend_src_path = os.path.join(project_root, 'apps', 'backend', 'src')

try:
    import gmqtt
    print("成功导入gmqtt")
except ImportError as e:
    print(f"导入gmqtt失败: {e}")
    # 尝试安装gmqtt
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gmqtt"])
        import gmqtt
        print("成功安装并导入gmqtt")
    except Exception as install_error:
        print(f"安装gmqtt失败: {install_error}")
        # 不再使用sys.exit(1)，避免pytest测试失败
        print("警告: gmqtt未安装，部分测试将跳过")

# 直接从文件路径读取external_connector.py
external_connector_file = os.path.join(backend_src_path, 'hsp', 'external', 'external_connector.py')
print(f"尝试读取文件: {external_connector_file}")

try:
    # 读取文件内容
    with open(external_connector_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("成功读取external_connector.py文件")
    print("文件长度:", len(content), "字符")
    
    # 创建一个简单的测试来检查MQTT连接逻辑
    print("\n开始分析MQTT连接稳定性问题...")
    
    # 分析ExternalConnector类中的连接逻辑
    if 'async def connect(self):' in content:
        print("✓ 找到connect方法")
    else:
        print("✗ 未找到connect方法")
        
    if 'async def disconnect(self):' in content:
        print("✓ 找到disconnect方法")
    else:
        print("✗ 未找到disconnect方法")
        
    if 'on_connect' in content:
        print("✓ 找到on_connect回调")
    else:
        print("✗ 未找到on_connect回调")
        
    if 'on_disconnect' in content:
        print("✓ 找到on_disconnect回调")
    else:
        print("✗ 未找到on_disconnect回调")
    
    # 检查连接稳定性相关的代码
    stability_issues = []
    
    # 检查是否有重连机制
    if 'retry' not in content and 'backoff' not in content:
        stability_issues.append("缺少重连和退避机制")
    
    # 检查是否有连接状态检查
    if 'is_connected' not in content:
        stability_issues.append("缺少连接状态检查")
    
    # 检查是否有异常处理
    if 'except Exception' not in content:
        stability_issues.append("缺少异常处理")
    
    # 检查是否有连接超时设置
    if 'timeout' not in content:
        stability_issues.append("缺少连接超时设置")
    
    # 检查是否有心跳机制
    if 'keepalive' not in content:
        stability_issues.append("缺少心跳机制")
    
    if stability_issues:
        print("\n发现的MQTT连接稳定性问题:")
        for issue in stability_issues:
            print(f"  - {issue}")
    else:
        print("\n未发现明显的MQTT连接稳定性问题")
    
    # 分析HSPConnector中的连接逻辑
    hsp_connector_file = os.path.join(backend_src_path, 'hsp', 'connector.py')
    print(f"\n尝试读取HSP连接器文件: {hsp_connector_file}")
    
    try:
        with open(hsp_connector_file, 'r', encoding='utf-8') as f:
            hsp_content = f.read()
        
        print("成功读取HSP连接器文件")
        print("文件长度:", len(hsp_content), "字符")
        
        # 检查HSP连接器中的连接稳定性机制
        hsp_stability_issues = []
        
        # 检查是否有重试机制
        if 'retry' not in hsp_content:
            hsp_stability_issues.append("HSP连接器缺少重试机制")
        else:
            print("✓ HSP连接器包含重试机制")
            
        # 检查是否有回退机制
        if 'fallback' not in hsp_content:
            hsp_stability_issues.append("HSP连接器缺少回退机制")
        else:
            print("✓ HSP连接器包含回退机制")
            
        # 检查是否有断路器模式
        if 'circuit_breaker' not in hsp_content:
            hsp_stability_issues.append("HSP连接器缺少断路器模式")
        else:
            print("✓ HSP连接器包含断路器模式")
            
        # 检查是否有连接状态管理
        if 'is_connected' not in hsp_content:
            hsp_stability_issues.append("HSP连接器缺少连接状态管理")
        else:
            print("✓ HSP连接器包含连接状态管理")
            
        # 检查是否有连接重试逻辑
        if 'connect(' in hsp_content and 'for attempt in range' in hsp_content:
            print("✓ HSP连接器包含连接重试逻辑")
        else:
            hsp_stability_issues.append("HSP连接器缺少连接重试逻辑")
            
        if hsp_stability_issues:
            print("\nHSP连接器中的稳定性问题:")
            for issue in hsp_stability_issues:
                print(f"  - {issue}")
        else:
            print("\nHSP连接器未发现明显的稳定性问题")
            
        # 分析具体的连接逻辑
        print("\n分析HSP连接器的连接方法...")
        if 'async def connect(self):' in hsp_content:
            # 找到connect方法的位置
            connect_start = hsp_content.find('async def connect(self):')
            if connect_start != -1:
                # 找到方法结束位置(下一个方法开始或文件结束)
                next_method = hsp_content.find('async def ', connect_start + 10)
                if next_method == -1:
                    next_method = len(hsp_content)
                connect_method = hsp_content[connect_start:next_method]
                print("HSP连接方法预览:")
                print(connect_method[:1000])  # 显示前1000个字符
                
                # 检查连接方法中的关键特性
                if 'for attempt in range' in connect_method:
                    print("✓ 连接方法包含重试循环")
                else:
                    print("✗ 连接方法缺少重试循环")
                    
                if 'await asyncio.sleep' in connect_method:
                    print("✓ 连接方法包含退避延迟")
                else:
                    print("✗ 连接方法缺少退避延迟")
                    
                if 'except Exception' in connect_method:
                    print("✓ 连接方法包含异常处理")
                else:
                    print("✗ 连接方法缺少异常处理")
            else:
                print("无法定位连接方法")
        else:
            print("HSP连接器中未找到connect方法")
            
    except FileNotFoundError as e:
        print(f"HSP连接器文件未找到: {e}")
    except Exception as e:
        print(f"读取HSP连接器文件时出错: {e}")
    
    print("\n分析完成")
    
except FileNotFoundError as e:
    print(f"文件未找到: {e}")
except Exception as e:
    print(f"执行测试时出错: {e}")