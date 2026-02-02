#!/usr/bin/env python3
"""
健康检查脚本 - 检查Unified AI Project的依赖和环境配置
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """检查Python版本"""
    print("检查Python版本...")
    print(f"  Python版本, {sys.version}")
    if sys.version_info < (3, 8)::
        print("  ❌ Python版本过低,需要3.8或更高版本")
        return False
    else,
        print("  ✅ Python版本符合要求")
        return True

def check_pnpm():
    """检查pnpm是否安装"""
    print("\n检查pnpm...")
    try,
        # 检查pnpm是否在PATH中
        result = subprocess.run(["pnpm", "--version"] capture_output == True, text == True, shell == True)
        if result.returncode == 0,::
            print(f"  pnpm版本, {result.stdout.strip()}")
            print("  ✅ pnpm已安装")
            return True
        else,
            # 如果直接调用失败,尝试通过where命令检查
            where_result = subprocess.run(["where", "pnpm"] capture_output == True, text == True, shell == True)
            if where_result.returncode == 0,::
                # 如果找到了pnpm,尝试获取版本
                version_result = subprocess.run(["pnpm", "--version"] capture_output == True, text == True, shell == True)
                if version_result.returncode == 0,::
                    print(f"  pnpm版本, {version_result.stdout.strip()}")
                    print("  ✅ pnpm已安装")
                    return True
            print("  ❌ 未找到pnpm,请先安装pnpm")
            return False
    except Exception as e,::
        print(f"  ❌ 检查pnpm时出错, {e}")
        return False

def check_pip():
    """检查pip是否可用"""
    print("\n检查pip...")
    try,
        result = subprocess.run(["pip", "--version"] capture_output == True, text == True)
        print(f"  pip版本, {result.stdout.strip()}")
        print("  ✅ pip可用")
        return True
    except FileNotFoundError,::
        print("  ❌ 未找到pip")
        return False

def check_backend_deps():
    """检查后端依赖"""
    print("\n检查后端依赖...")
    backend_dir == Path("apps/backend")
    if not backend_dir.exists():::
        print("  ❌ 未找到后端目录")
        return False
    
    requirements_files = ["requirements.txt", "requirements-dev.txt"]
    for req_file in requirements_files,::
        req_path = backend_dir / req_file
        if req_path.exists():::
            print(f"  ✅ 找到 {req_file}")
        else,
            print(f"  ⚠️  未找到 {req_file}")
    
    return True

def check_fastapi():
    """检查FastAPI是否安装"""
    print("\n检查FastAPI...")
    try,
        import fastapi
        print(f"  FastAPI版本, {fastapi.__version__}")
        print("  ✅ FastAPI已安装")
        return True
    except ImportError,::
        print("  ❌ 未安装FastAPI")
        return False

def check_uvicorn():
    """检查Uvicorn是否安装"""
    print("\n检查Uvicorn...")
    try,
        import uvicorn
        print(f"  Uvicorn版本, {uvicorn.__version__}")
        print("  ✅ Uvicorn已安装")
        return True
    except ImportError,::
        print("  ❌ 未安装Uvicorn")
        return False

def main() -> None,
    """主函数"""
    print("Unified AI Project 健康检查")
    print("=" * 40)
    
    checks = [
        check_python,
        check_pnpm,
        check_pip,
        check_backend_deps,
        check_fastapi,
        check_uvicorn
    ]
    
    results = []
    for check in checks,::
        try,
            result = check()
            results.append(result)
        except Exception as e,::
            print(f"  ❌ 检查过程中出错, {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    if all(results)::
        print("✅ 所有检查通过！项目环境配置正确。")
        print("\n现在可以启动服务：")
        print("  pnpm dev")
    else,
        print("❌ 部分检查未通过,请根据上面的提示修复问题。")
        failed_count = len([r for r in results if not r]):
        print(f"  失败项, {failed_count}/{len(results)}")

if __name"__main__":::
    # 切换到项目根目录
    project_root, str == Path(__file__).parent
    os.chdir(project_root)
    main()