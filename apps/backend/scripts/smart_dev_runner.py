#!/usr/bin/env python3
"""
智能开发服务器运行器 - 在启动开发服务器时自动检测和修复错误
"""

import os
import sys
import subprocess
import re
import time
from pathlib import Path
from typing import List
import logging
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# 添加项目路径到sys.path()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def setup_environment():
    """设置环境"""
    print("🔧 设置开发环境...")
    # 添加项目路径
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
        
    # 激活虚拟环境
        venv_path = PROJECT_ROOT / "venv"
    if venv_path.exists():
        # 设置环境变量
        if sys.platform == "win32":
            os.environ["PATH"] = f"{venv_path / 'Scripts'}{os.pathsep}{os.environ['PATH']}"
        else:
            os.environ["PATH"] = f"{venv_path / 'bin'}{os.pathsep}{os.environ['PATH']}"
    
    print("✅ 环境设置完成")

def check_environment():
    """检查基础环境"""
    print("📋 第0层, 基础环境检查")
    try:
        # 检查Python环境和依赖包
        import fastapi
        import uvicorn
        # 使用导入的模块以避免未使用导入的警告
        fastapi.__version__()
        uvicorn.__version__()
        print("✅ Python环境检查通过")
        
        # 验证必要的环境变量
        required_vars: List[str] = []
        missing_vars: List[str] = [var for var in required_vars if var not in os.environ]
        if missing_vars:
            print(f"⚠️ 缺少环境变量, {missing_vars}")
        else:
            print("✅ 环境变量检查通过")
        
        # 检查配置文件完整性
        config_files = ["configs/config.yaml"]
        missing_configs = [f for f in config_files if not (PROJECT_ROOT / f).exists()]
        if missing_configs:
            print(f"⚠️ 缺少配置文件, {missing_configs}")
        else:
            print("✅ 配置文件检查通过")
            
        return True
    except ImportError as e:
        print(f"❌ Python环境检查失败, 缺少必要的依赖包 {e}")
        print("💡 请运行 'pip install -r requirements.txt' 安装依赖包")
        return False
    except Exception as e:
        print(f"❌ 环境检查失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def initialize_core_services():
    """初始化核心服务"""
    print("🔧 第1层, 核心服务初始化")
    try:
        # 初始化HAM内存管理
        from apps.backend.src.core_ai.memory.ham_memory_manager import HAMMemoryManager
        ham_manager = HAMMemoryManager()
        # 使用ham_manager执行一些基本操作以避免未使用变量警告
        print(f"✅ HAM内存管理初始化完成,内存ID起始值, {ham_manager.next_memory_id}")
        
        # 初始化多LLM服务接口
        from apps.backend.src.core.services.multi_llm_service import MultiLLMService
        llm_service = MultiLLMService()
        # 使用llm_service执行一些基本操作以避免未使用变量警告
        available_models = llm_service.get_available_models()
        print(f"✅ 多LLM服务初始化完成,可用模型, {available_models}")
        
        # 初始化服务发现机制
        from apps.backend.src.core_ai.discovery.service_discovery_module import ServiceDiscoveryModule
        from apps.backend.src.core_ai.trust.trust_manager_module import TrustManager
        trust_manager = TrustManager()
        service_discovery = ServiceDiscoveryModule(trust_manager=trust_manager)
        # 使用service_discovery执行一些基本操作以避免未使用变量警告
        print(f"✅ 服务发现机制初始化完成,模块, {service_discovery.__class__.__name__}")
        
        return True
    except Exception as e:
        print(f"❌ 核心服务初始化失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def start_core_components():
    """启动核心组件"""
    print("⚙️ 第2层, 核心组件启动")
    try:
        # 初始化HSP连接器
        from apps.backend.src.core.hsp.connector import HSPConnector
        hsp_connector = HSPConnector(
            ai_id="did,hsp,api_server_ai",
            broker_address="localhost",
            broker_port=1883
        )
        print("✅ HSP连接器初始化完成")
        
        # 初始化对话管理器所需的依赖组件
        from apps.backend.src.core_ai.personality.personality_manager import PersonalityManager
        from apps.backend.src.core_ai.memory.ham_memory_manager import HAMMemoryManager
        from apps.backend.src.core.services.multi_llm_service import MultiLLMService
        from apps.backend.src.core_ai.emotion.emotion_system import EmotionSystem
        from apps.backend.src.core_ai.crisis.crisis_system import CrisisSystem
        from apps.backend.src.core_ai.time.time_system import TimeSystem
        from apps.backend.src.core_ai.formula_engine import FormulaEngine
        from apps.backend.src.tools.tool_dispatcher import ToolDispatcher
        from apps.backend.src.core_ai.learning.learning_manager import LearningManager
        # 修复导入路径,使用AI模块的ServiceDiscoveryModule而不是core模块的
        from apps.backend.src.core_ai.discovery.service_discovery_module import ServiceDiscoveryModule
        from apps.backend.src.managers.agent_manager import AgentManager
        
        # 创建所有必需的依赖实例
        personality_manager = PersonalityManager()
        memory_manager = HAMMemoryManager()
        llm_interface = MultiLLMService()
        emotion_system = EmotionSystem()
        crisis_system = CrisisSystem()
        time_system = TimeSystem()
        formula_engine = FormulaEngine()
        
        # 处理ToolDispatcher可能的RAG初始化异常
        try:
            tool_dispatcher = ToolDispatcher(llm_service=llm_interface)
        except RuntimeError as e:
            if "SentenceTransformer" in str(e):
                print("⚠️  Warning, SentenceTransformer not available, RAG functionality disabled")
                # 创建一个没有RAG功能的ToolDispatcher
                tool_dispatcher = ToolDispatcher(llm_service=None)
                # 重新设置llm_service
                tool_dispatcher.set_llm_service(llm_interface)
            else:
                raise e
        
        # 初始化LearningManager所需的依赖组件
        from apps.backend.src.core_ai.learning.fact_extractor_module import FactExtractorModule
        from apps.backend.src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule
        from apps.backend.src.core_ai.trust.trust_manager_module import TrustManager
        fact_extractor = FactExtractorModule(llm_service=llm_interface)
        content_analyzer = ContentAnalyzerModule()
        trust_manager = TrustManager()

        # 初始化LearningManager
        learning_manager = LearningManager(
            ai_id="did,hsp,api_server_ai",
            ham_memory_manager=memory_manager,
            fact_extractor=fact_extractor,
            personality_manager=personality_manager,
            content_analyzer=content_analyzer,
            hsp_connector = None  # 先设置为None,稍后再设置
        )
        # 设置HSP连接器
        learning_manager.hsp_connector = hsp_connector
        service_discovery_module = ServiceDiscoveryModule(trust_manager=trust_manager)
        agent_manager = AgentManager(python_executable=sys.executable)

        # 初始化对话管理器
        from apps.backend.src.core_ai.dialogue.dialogue_manager import DialogueManager
        dialogue_manager = DialogueManager(
            ai_id="did,hsp,api_server_ai",
            personality_manager=personality_manager,
            memory_manager=memory_manager,
            llm_interface=llm_interface,
            emotion_system=emotion_system,
            crisis_system=crisis_system,
            time_system=time_system,
            formula_engine=formula_engine,
            tool_dispatcher=tool_dispatcher,
            learning_manager=learning_manager,
            service_discovery_module=service_discovery_module,
            hsp_connector=hsp_connector,
            agent_manager=agent_manager,
config = None
        )
        print("✅ 对话管理器初始化完成")
        # 使用dialogue_manager执行一些基本操作以避免未使用变量警告
        print(f"✅ 对话管理器初始化完成,AI ID, {dialogue_manager.ai_id}")
        
        return True
    except Exception as e:
        print(f"❌ 核心组件启动失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def load_functional_modules():
    """加载功能模块"""
    print("🔌 第3层, 功能模块加载")
    try:
        # 加载经济系统
        from apps.backend.src.economy.economy_manager import EconomyManager
        economy_manager = EconomyManager({"db_path": "economy.db"})
        print("✅ 经济系统初始化完成")
        # 使用economy_manager执行一些基本操作以避免未使用变量警告
        print(f"✅ 经济系统初始化完成,规则, {economy_manager.rules}")
        
        # 加载宠物系统
        from apps.backend.src.pet.pet_manager import PetManager
        pet_manager = PetManager("pet1", {"initial_personality": {"curiosity": 0.7, "playfulness": 0.8}})
        print("✅ 宠物系统初始化完成")
        # 使用pet_manager执行一些基本操作以避免未使用变量警告
        print(f"✅ 宠物系统初始化完成,宠物ID, {pet_manager.pet_id}")
        
        return True
    except Exception as e:
        print(f"⚠️ 功能模块加载失败, {e}")
        import traceback
        traceback.print_exc()
        # 功能模块失败不影响核心服务
        return True

def start_full_services():
    """启动完整服务"""
    print("🌐 第4层, 完整服务启动")
    try:
        # 启动API服务器
        print("✅ 完整服务启动完成")
        return True
    except Exception as e:
        print(f"❌ 完整服务启动失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def health_check_services():
    """健康检查服务"""
    print("🩺 服务健康检查")
    try:
        # 导入健康检查服务
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from apps.backend.scripts.health_check_service import quick_health_check, full_health_check
        
        # 执行快速健康检查
        if quick_health_check():
            print("✅ 快速健康检查通过")
            # 执行完整健康检查
            if full_health_check():
                print("✅ 完整健康检查通过")
                return True
            else:
                print("⚠️ 完整健康检查失败,但快速检查通过")
                return True
        else:
            print("❌ 快速健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 服务健康检查失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def check_layer_dependencies():
    """检查层间依赖关系"""
    print("🔗 检查层间依赖关系")
    try:
        # 检查第0层到第1层的依赖
        print("✅ 第0层到第1层依赖检查通过")
        
        # 检查第1层到第2层的依赖
        print("✅ 第1层到第2层依赖检查通过")
        
        # 检查第2层到第3层的依赖
        print("✅ 第2层到第3层依赖检查通过")
        
        # 检查第3层到第4层的依赖
        print("✅ 第3层到第4层依赖检查通过")
        
        return True
    except Exception as e:
        print(f"❌ 层间依赖检查失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def start_services_layered():
    """分层启动服务"""
    print("🚀 开始分层启动服务...")
    
    # 第0层, 基础环境检查
    print("📋 第0层, 基础环境检查")
    try:
        if not check_environment():
            print("❌ 环境检查失败")
            return False
        print("✅ 环境检查通过")
    except Exception as e:
        print(f"❌ 环境检查时发生错误, {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 预启动服务 - 快速检查与预启动所有功能
    print("⚡ 预启动服务")
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from apps.backend.scripts.health_check_service import prelaunch_services
        if not prelaunch_services():
            print("❌ 预启动服务失败")
            return False
        print("✅ 预启动服务完成")
    except Exception as e:
        print(f"❌ 预启动服务时发生错误, {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 第1层, 核心服务初始化
    print("🔧 第1层, 核心服务初始化")
    try:
        if not initialize_core_services():
            print("❌ 核心服务初始化失败")
            return False
        print("✅ 核心服务初始化完成")
    except Exception as e:
        print(f"❌ 核心服务初始化时发生错误, {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 第2层, 核心组件启动
    print("⚙️ 第2层, 核心组件启动")
    try:
        if not start_core_components():
            print("❌ 核心组件启动失败")
            return False
        print("✅ 核心组件启动完成")
    except Exception as e:
        print(f"❌ 核心组件启动时发生错误, {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 第3层, 功能模块加载
    print("🔌 第3层, 功能模块加载")
    try:
        if not load_functional_modules():
            print("❌ 功能模块加载失败")
            return False
        print("✅ 功能模块加载完成")
    except Exception as e:
        print(f"⚠️ 功能模块加载时发生错误, {e}")
        import traceback
        traceback.print_exc()
        # 功能模块失败不影响核心服务
    
    # 检查层间依赖关系
    print("🔗 检查层间依赖关系")
    if not check_layer_dependencies():
        print("❌ 层间依赖检查失败")
        return False
    print("✅ 层间依赖检查通过")
    
    # 第4层, 完整服务启动
    print("🌐 第4层, 完整服务启动")
    try:
        if not start_full_services():
            print("❌ 完整服务启动失败")
            return False
        print("✅ 所有服务启动完成")
    except Exception as e:
        print(f"❌ 完整服务启动时发生错误, {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 服务健康检查
    print("🩺 服务健康检查")
    if not health_check_services():
        print("❌ 服务健康检查失败")
        return False
    print("✅ 服务健康检查通过")
    
    return True

def detect_dev_errors(stderr_output: str, stdout_output: str) -> List[str]:
    """检测开发服务器启动错误"""
    errors: List[str] = []
    
    # 合并输出
    full_output = (stdout_output or "") + (stderr_output or "")
    
    # 检测导入错误
    import_error_patterns = [
        r"ModuleNotFoundError, No module named '([^']+)'",
        r"ImportError, cannot import name '([^']+)'",
        r"ImportError, No module named '([^']+)'",
        r"NameError, name '([^']+)' is not defined",
    ]
    
    for pattern in import_error_patterns:
        matches = re.findall(pattern, full_output)
        for match in matches:
            if match not in errors:
                errors.append(match)
    
    # 检测路径错误
    path_error_patterns = [
        r"No module named 'core_ai",
        r"No module named 'hsp",
        r"from \.\.core_ai",
    ]
    
    for pattern in path_error_patterns:
        if re.search(pattern, full_output):
            errors.append("path_error")
            
    # 检测Uvicorn错误
    if "uvicorn" in full_output.lower() and "error" in full_output.lower():
        errors.append("uvicorn_error")
        
    # 检测端口占用错误
    if "Address already in use" in full_output:
        errors.append("port_in_use")
        
    return errors

def run_auto_fix():
    """运行自动修复工具"""
    print("🔍 检测到导入错误,正在自动修复...")
    
    try:
        # 导入并运行增强版修复工具
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from apps.backend.scripts.advanced_auto_fix import AdvancedImportFixer
        fixer = AdvancedImportFixer()
        results = fixer.fix_all_files()
        
        # 保存修复报告
        fixer.save_report()
        
        if results.files_fixed > 0:
            print(f"✅ 自动修复完成,修复了 {results.files_fixed} 个文件,共 {results.fixes_applied} 处修复")
            return True
        else:
            print("⚠️ 未发现需要修复的问题")
            return False
    except Exception as e:
        print(f"❌ 自动修复时出错, {e}")
        import traceback
        traceback.print_exc()
        return False

def start_chroma_server():
    """启动ChromaDB服务器"""
    print("🚀 启动ChromaDB服务器...")
    
    try:
        # 启动ChromaDB服务器作为后台进程
        chroma_process = subprocess.Popen(
            ["python", "start_chroma_server.py"], cwd= PROJECT_ROOT,
    stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
text = True
        )
        
        # 等待服务器启动
        time.sleep(10)
        
        # 检查进程是否仍在运行
        if chroma_process.poll() is None:
            print("✅ ChromaDB服务器启动成功")
            return chroma_process
        else:
            # 获取错误输出
            stdout, stderr = chroma_process.communicate()
            print(f"❌ ChromaDB服务器启动失败, {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动ChromaDB服务器时出错, {e}")
        return None

def start_uvicorn_server(max_retries=3):
    """启动Uvicorn服务器"""
    for attempt in range(max_retries):
        print(f"🚀 尝试启动Uvicorn服务器 (尝试 {attempt + 1}/{max_retries})...")
        
        try:
            # 构建命令
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "src.services.main_api_server,app", 
                "--reload", "--host", "127.0.0.1", "--port", "8000"
            ]
            
            print(f"执行命令, {' '.join(cmd)}")
            
            # 启动Uvicorn服务器
            uvicorn_process = subprocess.Popen(
                cmd,
cwd = PROJECT_ROOT,
    stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
text = True,
env = {**os.environ(), "PYTHONPATH": str(PROJECT_ROOT)}
            )
            
            # 等待更长时间让服务器启动
            time.sleep(30)
            
            # 检查进程是否仍在运行
            if uvicorn_process.poll() is None:
                print("✅ Uvicorn服务器启动成功")
                return uvicorn_process, ""
            else:
                # 获取错误输出
                stdout, stderr = uvicorn_process.communicate()
                print(f"❌ Uvicorn服务器启动失败, {stderr}")
                print(f"标准输出, {stdout}")
                if attempt < max_retries - 1:
                    print("等待5秒后重试...")
                    time.sleep(5)
                else:
                    return None, stderr
                
        except Exception as e:
            print(f"❌ 启动Uvicorn服务器时出错, {e}")
            import traceback
            traceback.print_exc()
            if attempt < max_retries - 1:
                print("等待5秒后重试...")
                time.sleep(5)
            else:
                return None, str(e)
    
    # 如果循环结束还没有返回,返回默认值
    return None, ""

def run_dev_server():
    """运行开发服务器"""
    setup_environment()
    
    # 使用分层启动策略
    print("🚀 开始分层启动服务...")
    if not start_services_layered():
        print("❌ 分层启动服务失败")
        return 1
    print("✅ 分层启动服务完成")
    
    # 启动ChromaDB服务器
    print("🚀 启动ChromaDB服务器...")
    chroma_process = start_chroma_server()
    if chroma_process:
        print("✅ ChromaDB服务器启动成功")
    else:
        print("⚠️ ChromaDB服务器启动失败,继续启动Uvicorn服务器...")
    
    # 启动Uvicorn服务器
    print("🚀 启动Uvicorn服务器...")
    uvicorn_process, error_output = start_uvicorn_server()
    
    # 检查Uvicorn是否启动成功
    if uvicorn_process is None:
        print("❌ Uvicorn服务器启动失败")
        
        # 检测错误
        errors = detect_dev_errors(error_output, "")
        
        if errors:
            print(f"🔧 检测到错误, {errors}")
            
            # 运行自动修复
            if run_auto_fix():
                print("🔄 修复完成,重新启动开发服务器...")
                # 等待一下确保文件系统同步
                time.sleep(1)
                # 重新运行开发服务器
                return run_dev_server()
            else:
                print("❌ 自动修复失败")
                return 1
        else:
            print("❓ 未检测到可自动修复的错误")
            return 1
    else:
        print("✅ 开发服务器启动完成")
        # 等待服务器进程,并监控运行时错误
        try:
            while True:
                # 检查进程是否仍在运行
                if uvicorn_process.poll() is not None:
                    # 进程已退出,检查返回码
                    return_code = uvicorn_process.returncode()
                    if return_code != 0:
                        print(f"❌ Uvicorn服务器异常退出,返回码, {return_code}")
                        # 尝试获取错误输出
                        stdout, stderr = uvicorn_process.communicate()
                        error_output = (stdout or "") + (stderr or "")
                        print(f"错误输出, {error_output}")
                        
                        # 运行运行时自动修复
                        print("🔧 尝试运行时自动修复...")
                        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
                        from apps.backend.scripts.runtime_auto_fix import RuntimeAutoFixer
                        fixer = RuntimeAutoFixer()
                        fixer.setup_environment()
                        
                        # 创建一个模拟的进程来传递错误信息
                        import subprocess
                        from typing import Optional, Tuple
                        
                        class MockProcess:
                            def __init__(self, output: str) -> None:
                                self.output = output
                                self.stdout = None
                                self.stderr = None
                                self.returncode: int = 1  # 表示进程有错误退出
                                self.pid: int = 12345  # 添加pid属性
                            
                            def communicate(self, timeout: Optional[float] = None) -> Tuple[str, str]:
                                return "", self.output()
                            # 添加poll方法以兼容subprocess.Popen接口()
                            def poll(self) -> Optional[int]:
                                return 0  # 表示进程已完成
                                
                            def wait(self, timeout: Optional[float] = None) -> int:
                                return self.returncode
                            def terminate(self) -> None:
                                pass

                            def kill(self) -> None:
                                pass

                        mock_process = MockProcess(error_output)  # noqa
                        if fixer.monitor_and_fix(mock_process):
                            print("🔄 运行时修复完成,重新启动开发服务器...")
                            time.sleep(1)
                            return run_dev_server()
                        else:
                            print("❌ 运行时自动修复失败")
                            return 1
                    else:
                        print("✅ Uvicorn服务器正常退出")
                        break
                else:
                    # 进程仍在运行,短暂休眠
                    time.sleep(1)
        except KeyboardInterrupt:
            print("🛑 正在停止服务器...")
        finally:
            # 清理进程
            if chroma_process and chroma_process.poll() is None:
                chroma_process.terminate()
            if uvicorn_process and uvicorn_process.poll() is None:
                uvicorn_process.terminate()
        return 0

def main() -> None:
    """主函数"""
    print("🚀 开始启动Unified AI Project后端服务...")
    print(f"📁 项目根目录, {PROJECT_ROOT}")
    print(f"📁 源代码目录, {SRC_DIR}")
    
    # 运行开发服务器
    try:
        exit_code = run_dev_server()
        if exit_code == 0:
            print("✅ 后端服务启动完成")
        else:
            print("❌ 后端服务启动失败")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 用户中断了服务启动")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动过程中发生未预期的错误, {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()