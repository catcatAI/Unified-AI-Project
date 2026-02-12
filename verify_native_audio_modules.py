#!/usr/bin/env python3
"""
验证 Native Audio Modules 编译状态
检查 WASAPI/PulseAudio/CoreAudio 模块是否已正确编译
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(msg):
    print(f"  [✓] {msg}")

def print_error(msg):
    print(f"  [✗] {msg}")

def print_warning(msg):
    print(f"  [!] {msg}")

def print_info(msg):
    print(f"  [i] {msg}")

def check_system_info():
    """检查系统信息"""
    print_header("系统信息")
    print_info(f"操作系统: {platform.system()}")
    print_info(f"架构: {platform.machine()}")
    print_info(f"Python版本: {platform.python_version()}")
    
    # 检查 Node.js
    try:
        result = subprocess.run(['node', '-v'], capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Node.js版本: {result.stdout.strip()}")
        else:
            print_error("Node.js 未安装")
    except FileNotFoundError:
        print_error("Node.js 未安装")

def check_native_module(module_name, module_path):
    """检查单个原生模块"""
    print_header(f"检查模块: {module_name}")
    
    if not os.path.exists(module_path):
        print_error(f"模块目录不存在: {module_path}")
        return False
    
    print_success(f"模块目录存在")
    
    # 检查 package.json
    package_json = os.path.join(module_path, 'package.json')
    if os.path.exists(package_json):
        print_success("package.json 存在")
    else:
        print_error("package.json 不存在")
        return False
    
    # 检查 binding.gyp
    binding_gyp = os.path.join(module_path, 'binding.gyp')
    if os.path.exists(binding_gyp):
        print_success("binding.gyp 存在")
    else:
        print_error("binding.gyp 不存在")
        return False
    
    # 检查 build 目录
    build_dir = os.path.join(module_path, 'build')
    if os.path.exists(build_dir):
        print_success("build 目录存在")
        
        # 检查 Release 子目录
        release_dir = os.path.join(build_dir, 'Release')
        if os.path.exists(release_dir):
            print_success("Release 目录存在")
            
            # 查找 .node 文件
            node_files = list(Path(release_dir).glob('*.node'))
            if node_files:
                for node_file in node_files:
                    size = node_file.stat().st_size
                    print_success(f"编译的模块: {node_file.name} ({size} bytes)")
                return True
            else:
                print_error("未找到编译的 .node 文件")
                return False
        else:
            print_error("Release 目录不存在")
            return False
    else:
        print_warning("build 目录不存在（模块未编译）")
        return False

def check_linux_dependencies():
    """检查 Linux 系统的依赖"""
    print_header("检查 Linux 依赖")
    
    # 检查 PulseAudio 开发库
    try:
        result = subprocess.run(['dpkg', '-l'], capture_output=True, text=True)
        if 'libpulse-dev' in result.stdout:
            print_success("libpulse-dev 已安装")
        else:
            print_error("libpulse-dev 未安装")
            print_info("安装命令: sudo apt-get install libpulse-dev libpulse-simple-dev")
    except FileNotFoundError:
        print_warning("无法检查 dpkg (非 Debian/Ubuntu 系统)")

def check_macos_dependencies():
    """检查 macOS 系统的依赖"""
    print_header("检查 macOS 依赖")
    
    # macOS 通常包含 CoreAudio 框架，无需额外安装
    print_success("CoreAudio 框架（系统自带）")

def check_windows_dependencies():
    """检查 Windows 系统的依赖"""
    print_header("检查 Windows 依赖")
    
    # Windows 通常包含 WASAPI，无需额外安装
    print_success("WASAPI（系统自带）")

def main():
    """主函数"""
    print_header("Native Audio Modules 验证")
    
    # 获取项目根目录
    script_dir = Path(__file__).parent
    native_modules_dir = script_dir / 'apps' / 'desktop-app' / 'native_modules'
    
    if not native_modules_dir.exists():
        print_error(f"Native modules 目录不存在: {native_modules_dir}")
        sys.exit(1)
    
    # 检查系统信息
    check_system_info()
    
    # 根据平台检查依赖
    system = platform.system().lower()
    if system == 'linux':
        check_linux_dependencies()
    elif system == 'darwin':
        check_macos_dependencies()
    elif system == 'windows':
        check_windows_dependencies()
    
    # 检查原生模块
    modules = {}
    
    # Windows: WASAPI
    modules['node-wasapi-capture'] = {
        'path': native_modules_dir / 'node-wasapi-capture',
        'platform': 'windows'
    }
    
    # Linux: PulseAudio
    modules['node-pulseaudio-capture'] = {
        'path': native_modules_dir / 'node-pulseaudio-capture',
        'platform': 'linux'
    }
    
    # macOS: CoreAudio
    modules['node-coreaudio-capture'] = {
        'path': native_modules_dir / 'node-coreaudio-capture',
        'platform': 'darwin'
    }
    
    results = {}
    for module_name, module_info in modules.items():
        is_current_platform = (module_info['platform'] == system.lower() or
                             (system.lower() == 'linux' and module_info['platform'] == 'linux'))
        
        if is_current_platform or True:  # 检查所有模块
            compiled = check_native_module(module_name, module_info['path'])
            results[module_name] = {
                'compiled': compiled,
                'platform': module_info['platform']
            }
    
    # 汇总结果
    print_header("验证结果汇总")
    
    for module_name, result in results.items():
        status = "已编译" if result['compiled'] else "未编译"
        icon = "[✓]" if result['compiled'] else "[✗]"
        print(f"  {icon} {module_name} ({result['platform']}): {status}")
    
    # 建议
    print_header("建议")
    
    current_module = None
    for module_name, result in results.items():
        if result['platform'] == system.lower():
            current_module = (module_name, result['compiled'])
            break
    
    if current_module:
        module_name, compiled = current_module
        if not compiled:
            print_info(f"当前平台的模块 {module_name} 尚未编译")
            print_info(f"请运行编译脚本:")
            
            module_path = modules[module_name]['path']
            if system.lower() == 'linux':
                script = module_path / 'build.sh'
                print_info(f"  bash {script}")
            elif system.lower() == 'windows':
                script = module_path / 'build.bat'
                print_info(f"  {script}")
            elif system.lower() == 'darwin':
                script = module_path / 'build.sh'
                print_info(f"  bash {script}")
        else:
            print_success(f"当前平台的模块 {module_name} 已正确编译")
    
    # 回退方案说明
    print_header("回退方案")
    print_info("如果原生模块编译失败，audio-handler.js 会自动回退到:")
    print_info("  - Web Audio API (浏览器原生音频 API)")
    print_info("  - 这意味着系统音频捕获功能可能受限")
    print_info("  - 但应用仍可正常运行，功能受限程度因模块而异")
    
    print(f"\n{'='*60}")
    print("  验证完成")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()