#! / usr / bin / env python3
"""
增量学习管理器
实现增量数据识别、增量模型训练、智能训练触发和自动模型整理功能
"""

from system_test import
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enhanced_realtime_monitoring import
# TODO: Fix import - module 'threading' not found
from collections import defaultdict
# TODO: Fix import - module 'hashlib' not found

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
backend_path, str = project_root / "apps" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))

# 导入项目模块
try,
    DATA_DIR,
    TRAINING_DIR,
    MODELS_DIR,
    get_data_path,
    resolve_path
(    )
except ImportError, ::
    # 如果路径配置模块不可用, 使用默认路径处理
    PROJECT_ROOT = project_root
    DATA_DIR == PROJECT_ROOT / "data"
    TRAINING_DIR == PROJECT_ROOT / "training"
    MODELS_DIR == TRAINING_DIR / "models"

# 导入数据管理器和模型训练器
from training.data_manager import DataManager
from training.train_model import ModelTrainer

# 配置日志
logging.basicConfig()
    level = logging.INFO(),
    format, str = '%(asctime)s - %(levelname)s - %(message)s',
    handlers = []
    logging.FileHandler(TRAINING_DIR / 'incremental_learning.log'),
    logging.StreamHandler()
[    ]
()
logger, Any = logging.getLogger(__name__)


class DataTracker, :
    """数据跟踪器, 负责跟踪和管理训练数据状态"""

    def __init__(self, tracking_file, str == None, config_file, str == None) -> None, :
    self.data_dir == DATA_DIR
        self.tracking_file == Path(tracking_file) if tracking_file else TRAINING_DIR /\
    "data_tracking.json":::
    self.config_file == Path(config_file) if config_file else TRAINING_DIR / "configs" /\
    \
    "performance_config.json":::
    self.processed_files = {}
    self.new_files = set()
    self.max_scan_files = 5000  # 默认值
    self.scan_file_types = []  # 要扫描的文件类型
    self.enable_file_type_filtering == True  # 是否启用文件类型过滤
    self.progress_log_interval = 5000  # 进度日志间隔
    self.max_workers = 8  # 并行处理工作进程数
    self.enable_parallel_scanning == True  # 是否启用并行扫描
    self.error_handler = global_error_handler  # 错误处理器
    self._load_performance_config()
    self._load_tracking_data()

    def _load_performance_config(self):
        ""加载性能配置"""
    context == ErrorContext("DataTracker", "_load_performance_config")
        try,

            if self.config_file.exists():::
                ith open(self.config_file(), 'r', encoding == 'utf - 8') as f,
    config = json.load(f)
                    data_scanning_config = config.get('data_scanning', {})
                    self.max_scan_files = data_scanning_config.get('max_files_per_scan',
    5000)
                    self.scan_file_types = data_scanning_config.get('file_types_to_scan'\
    \
    , [])
                    self.enable_file_type_filtering = data_scanning_config.get('enable_f\
    \
    ile_type_filtering', True)
                    self.progress_log_interval = data_scanning_config.get('progress_log_\
    \
    interval', 5000)
                    self.max_workers = data_scanning_config.get('max_workers', 8)
                    self.enable_parallel_scanning = data_scanning_config.get('enable_par\
    \
    allel_scanning', True)
                logger.info(f"✅ 加载性能配置, {self.config_file}")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 加载性能配置失败, {e}")

    def _load_tracking_data(self):
        ""加载数据跟踪信息"""
    context == ErrorContext("DataTracker", "_load_tracking_data")
        try,

            if self.tracking_file.exists():::
                ith open(self.tracking_file(), 'r', encoding == 'utf - 8') as f,
    data = json.load(f)
                    self.processed_files == {"k": datetime.fromisoformat(v) for k,
    v in data.get('processed_files', {}).items()}::
    logger.info(f"✅ 加载数据跟踪信息, {self.tracking_file}")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 加载数据跟踪信息失败, {e}")

    def _save_tracking_data(self):
        ""保存数据跟踪信息"""
    context == ErrorContext("DataTracker", "_save_tracking_data")
        try,

            data = {}
                'processed_files': {"k": v.isoformat() for k,
    v in self.processed_files.items()}:
    'updated_at': datetime.now().isoformat()
{            }
            with open(self.tracking_file(), 'w', encoding == 'utf - 8') as f, :
    json.dump(data, f, ensure_ascii == False, indent = 2)
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 保存数据跟踪信息失败, {e}")

    def _calculate_file_hash(self, file_path, Path) -> str, :
    """计算文件哈希值"""
    context == ErrorContext("DataTracker", "_calculate_file_hash",
    {"file_path": str(file_path)})
    hash_md5 = hashlib.md5()
        try,

            with open(file_path, "rb") as f, :
    for chunk in iter(lambda, f.read(4096), b""):::
    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 计算文件哈希失败 {file_path} {e}")
            return ""

    def scan_for_new_data(self) -> List[Dict[str, Any]]:
    """扫描新增数据"""
    logger.info("🔍 开始扫描新增数据...")
    context == ErrorContext("DataTracker", "scan_for_new_data")

    # 根据配置选择使用并行或串行扫描器
        try,

            if self.enable_parallel_scanning, ::
                # 使用并行优化的数据扫描器
                from training.parallel_optimized_data_scanner import ParallelOptimizedDa\
    \
    taScanner
                scanner == ParallelOptimizedDataScanner(self.data_dir(),
    self.tracking_file(), self.config_file())
                logger.info("🔄 使用并行优化的数据扫描器")
            else,
                # 使用串行优化的数据扫描器
                from training.optimized_data_scanner import OptimizedDataScanner
                scanner == OptimizedDataScanner(self.data_dir(), self.tracking_file(),
    self.config_file())
                logger.info("🔄 使用串行优化的数据扫描器")

            # 获取要扫描的文件类型
            file_types == self.scan_file_types if self.enable_file_type_filtering else N\
    one, :
            # 查找新增文件
            new_data_files = scanner.find_new_files()
    max_files = self.max_scan_files(),
                file_types = file_types
(            )

            logger.info(f"✅ 扫描完成, 发现 {len(new_data_files)} 个新增 / 修改文件")
            return new_data_files

        except ImportError as e, ::
            # 如果优化的扫描器不可用, 使用原始方法
            self.error_handler.handle_error(e, context,
    ErrorRecoveryStrategy.FALLBACK())
            logger.warning(f"⚠️  优化的数据扫描器不可用, 使用原始扫描方法, {e}")
            return self._scan_for_new_data_original()
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 扫描新增数据时出错, {e}")
            return []

    def _scan_for_new_data_original(self) -> List[Dict[str, Any]]:
    """原始数据扫描方法(备用)"""
    context == ErrorContext("DataTracker", "_scan_for_new_data_original")
        try,
            # 使用DataManager扫描数据, 但限制文件数量
            data_manager == DataManager()
            data_catalog = data_manager.scan_data()

            # 如果指定了要扫描的文件类型, 进行过滤
            if self.scan_file_types and self.enable_file_type_filtering, ::
    filtered_catalog = {}
                for file_path, file_info in data_catalog.items():::
                    f file_info.get('type') in self.scan_file_types,


    filtered_catalog[file_path] = file_info
                data_catalog = filtered_catalog
                logger.info(f"📋 根据配置过滤文件类型, 剩余 {len(data_catalog)} 个文件")

            # 如果文件数量过多, 只处理最近修改的文件
            if len(data_catalog) > self.max_scan_files, ::
    logger.warning(f"⚠️  发现 {len(data_catalog)} 个文件, 超过限制 {self.max_scan_files} 个,
    将只处理最近修改的文件")
                # 按修改时间排序, 取最新的文件
                sorted_files == sorted(data_catalog.items(), key = lambda x,
    x[1]['modified_time'] reverse == True)
                data_catalog == dict(sorted_files[:self.max_scan_files])

            new_data_files = []
            processed_count = 0

            # 检查每个文件是否为新增或修改的
            for file_path, file_info in data_catalog.items():::
                ull_path == Path(file_info['path'])

                # 检查文件是否已处理
                file_hash = self._calculate_file_hash(full_path)
                if not file_hash, ::
    continue

                # 检查文件修改时间
                modified_time = datetime.fromtimestamp(file_info['modified_time'])

                # 如果文件未处理过或已修改, 则标记为新增
                if file_hash not in self.processed_files or \
    self.processed_files[file_hash] < modified_time, ::
    new_data_files.append({)}
                        'path': str(full_path),
                        'relative_path': file_path,
                        'hash': file_hash,
                        'modified_time': modified_time.isoformat(),
                        'size': file_info['size']
                        'type': file_info['type']
{(                    })
                    logger.debug(f"   发现新增 / 修改文件, {file_path}")

                processed_count += 1
                # 每处理指定数量的文件输出一次进度
                if processed_count % self.progress_log_interval == 0, ::
    logger.info(f"   已处理 {processed_count} 个文件...")

            logger.info(f"✅ 扫描完成, 发现 {len(new_data_files)} 个新增 / 修改文件 (总共检查 {processed_count} 个文件)")
            return new_data_files
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 原始数据扫描方法失败, {e}")
            return []

    def mark_as_processed(self, file_hash, str):
        ""标记文件为已处理"""
    context == ErrorContext("DataTracker", "mark_as_processed",
    {"file_hash": file_hash})
        try,

            self.processed_files[file_hash] = datetime.now()
            self._save_tracking_data()
            logger.debug(f"✅ 标记文件为已处理, {file_hash}")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 标记文件为已处理失败, {e}")


class ModelManager, :
    """模型管理器, 负责模型版本管理和增量更新"""

    def __init__(self, models_dir, str == None) -> None, :
        self.models_dir == Path(models_dir) if models_dir else MODELS_DIR, ::
    self.model_versions = {}
    self.error_handler = global_error_handler  # 错误处理器
    self.version_controller == VersionControlManager(models_dir)  # 版本控制器
    self._load_model_versions()

    def _load_model_versions(self):
        ""加载模型版本信息"""
    context == ErrorContext("ModelManager", "_load_model_versions")
        try,

            version_file = self.models_dir / "model_versions.json"
            if version_file.exists():::
                ith open(version_file, 'r', encoding == 'utf - 8') as f,
    self.model_versions = json.load(f)
                logger.info(f"✅ 加载模型版本信息, {version_file}")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 加载模型版本信息失败, {e}")

    def _save_model_versions(self):
        ""保存模型版本信息"""
    context == ErrorContext("ModelManager", "_save_model_versions")
        try,

            version_file = self.models_dir / "model_versions.json"
            with open(version_file, 'w', encoding == 'utf - 8') as f, :
    json.dump(self.model_versions(), f, ensure_ascii == False, indent = 2)
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 保存模型版本信息失败, {e}")

    def get_latest_model(self, model_name, str) -> Optional[Path]:
    """获取最新版本的模型"""
    context == ErrorContext("ModelManager", "get_latest_model",
    {"model_name": model_name})
        try,

            if model_name in self.model_versions, ::
    latest_version = self.model_versions[model_name].get('latest')
                if latest_version, ::
    model_path = self.models_dir / latest_version
                    if model_path.exists():::
                        eturn model_path
            return None
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取最新模型失败, {e}")
            return None

    def save_incremental_model(self, model_name, str, model_path, Path, metrics,
    Dict[str, Any]):
        ""保存增量更新的模型(集成版本控制)"""
    context == ErrorContext("ModelManager", "save_incremental_model", {)}
            "model_name": model_name,
            "model_path": str(model_path)
{(    })
        try,
            # 使用版本控制器创建新版本
            metadata = {}
                'performance_metrics': metrics,
                'training_data': {}
                'change_log': f'Incremental update for {model_name}', :::
                    tags': ['incremental', 'auto - generated']
{            }

            # 根据性能指标自动标记版本类型
            accuracy = metrics.get('accuracy', 0)
            version_type = "alpha"  # 默认为alpha版本
            if accuracy >= 0.95, ::
    version_type = "release"
                metadata['tags'].append('stable')
            elif accuracy >= 0.85, ::
    version_type = "beta"
                metadata['tags'].append('testing')

            # 创建版本
            version_name = self.version_controller.create_version()
(    model_name, model_path, metadata, version_type)

            if version_name, ::
                # 更新本地版本信息以保持兼容性
                version_path = self.models_dir / version_name
                if model_name not in self.model_versions, ::
    self.model_versions[model_name] = {}
                        'versions': []
                        'latest': version_name,
                        'created_at': datetime.now().isoformat()
{                    }

                self.model_versions[model_name]['versions'].append({)}
                    'version': version_name,
                    'path': str(version_path),
                    'created_at': datetime.now().isoformat(),
                    'metrics': metrics
{(                })
                self.model_versions[model_name]['latest'] = version_name
                self.model_versions[model_name]['updated_at'] = datetime.now().isoformat\
    \
    ()

                # 保存版本信息
                self._save_model_versions()

                logger.info(f"✅ 保存增量模型, {version_name} (类型, {version_type})")
                return version_path
            else,

                logger.error(f"❌ 使用版本控制器创建版本失败")
                return None
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 保存增量模型失败, {e}")
            return None

    def cleanup_old_models(self, model_name, str, keep_versions, int == 5):
        ""清理旧版本模型"""
    context == ErrorContext("ModelManager", "cleanup_old_models", {)}
            "model_name": model_name,
            "keep_versions": keep_versions
{(    })
        try,

            if model_name in self.model_versions, ::
    versions = self.model_versions[model_name].get('versions', [])
                if len(versions) > keep_versions, ::
                    # 按创建时间排序, 保留最新的几个版本
                    versions.sort(key == lambda x, x['created_at'] reverse == True)
                    old_versions == versions[keep_versions, ]

                    # 删除旧版本文件
                    for version_info in old_versions, ::
    version_path == Path(version_info['path'])
                        if version_path.exists():::
                            ry,


                                version_path.unlink()
                                logger.info(f"🗑️  删除旧版本模型, {version_path.name}")
                            except Exception as e, ::
                                self.error_handler.handle_error(e, context)
                                logger.error(f"❌ 删除旧版本模型失败 {version_path.name} {e}")

                    # 更新版本列表
                    self.model_versions[model_name]['versions'] = versions[:keep_version\
    \
    s]
                    self._save_model_versions()
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 清理旧版本模型失败, {e}")

    def auto_cleanup_models(self, keep_versions, int == 5):
        ""自动清理所有模型的旧版本"""
    context == ErrorContext("ModelManager", "auto_cleanup_models", {)}
            "keep_versions": keep_versions
{(    })
        try,

            for model_name in self.model_versions.keys():::
= self.cleanup_old_models(model_name, keep_versions)
            logger.info(f"✅ 自动清理完成, 每个模型保留最新 {keep_versions} 个版本")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 自动清理模型失败, {e}")

    def rollback_to_latest_stable_version(self, model_name, str) -> bool, :
    """一键回滚到最新的稳定版本"""
    context == ErrorContext("ModelManager", "rollback_to_latest_stable_version",
    {"model_name": model_name})
        try,
            # 使用版本控制器查找最新的稳定版本
            stable_versions = self.version_controller.get_versions_by_tag(model_name,
    "stable")
            if not stable_versions, ::
    logger.warning(f"⚠️  模型 {model_name} 没有标记为稳定版本的版本")
                return False

            # 按创建时间排序, 获取最新的稳定版本
            stable_versions.sort(key == lambda x, x['created_at'] reverse == True)
            latest_stable_version = stable_versions[0]['version']

            # 执行回滚
            success = self.version_controller.rollback_to_version(model_name,
    latest_stable_version)
            if success, ::
    logger.info(f"✅ 模型 {model_name} 已回滚到最新稳定版本, {latest_stable_version}")
            else,

                logger.error(f"❌ 模型 {model_name} 回滚到稳定版本失败")

            return success
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 一键回滚到稳定版本失败, {e}")
            return False

    def rollback_to_previous_version(self, model_name, str) -> bool, :
    """一键回滚到上一个版本"""
    context == ErrorContext("ModelManager", "rollback_to_previous_version",
    {"model_name": model_name})
        try,
            # 获取版本历史
            version_history = self.version_controller.get_version_history(model_name)
            if len(version_history) < 2, ::
    logger.warning(f"⚠️  模型 {model_name} 没有足够的版本历史进行回滚")
                return False

            # 按创建时间排序
            version_history.sort(key == lambda x, x['created_at'] reverse == True)
            previous_version = version_history[1]['version']

            # 执行回滚
            success = self.version_controller.rollback_to_version(model_name,
    previous_version)
            if success, ::
    logger.info(f"✅ 模型 {model_name} 已回滚到上一个版本, {previous_version}")
            else,

                logger.error(f"❌ 模型 {model_name} 回滚到上一个版本失败")

            return success
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 一键回滚到上一个版本失败, {e}")
            return False


class TrainingScheduler, :
    """训练调度器, 负责训练任务的调度和执行"""

    def __init__(self) -> None, :
    self.pending_tasks = []
    self.is_idle == True
    self.idle_threshold = 0.3  # CPU使用率阈值
    self.idle_duration = 0
    self.idle_check_interval = 60  # 检查间隔(秒)
    self.min_idle_duration = 300  # 最小空闲持续时间(秒)
    self.failed_tasks = []  # 存储失败的任务
    self.max_retry_attempts = 3  # 最大重试次数
    self.resource_manager == None  # 资源管理器
    self.error_handler = global_error_handler  # 错误处理器
    self._init_resource_manager()

    def _init_resource_manager(self):
        ""初始化资源管理器"""
    context == ErrorContext("TrainingScheduler", "_init_resource_manager")
        try,

            from training.resource_manager import ResourceManager
            self.resource_manager == ResourceManager()
            logger.info("✅ 资源管理器初始化成功")
        except Exception as e, ::
            self.error_handler.handle_error(e, context,
    ErrorRecoveryStrategy.FALLBACK())
            logger.warning(f"⚠️  资源管理器初始化失败, {e}")

    def is_system_idle(self) -> bool, :
    """检查系统是否空闲"""
    context == ErrorContext("TrainingScheduler", "is_system_idle")
        try,

# TODO: Fix import - module 'psutil' not found
            # 检查CPU使用率
            cpu_percent = psutil.cpu_percent(interval = 1)
            return cpu_percent < self.idle_threshold * 100
        except ImportError, ::
            # 如果没有psutil, 使用简化的方法
            self.error_handler.handle_error(Exception("psutil not available"), context,
    ErrorRecoveryStrategy.FALLBACK())
            logger.warning("⚠️  无法检测系统资源使用情况, 假设系统空闲")
            return True
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 检查系统空闲状态时出错, {e}")
            return False

    def _get_available_resources(self) -> Dict[str, Any]:
    """获取可用系统资源"""
    context == ErrorContext("TrainingScheduler", "_get_available_resources")
    # 默认资源信息
    resources = {}
            'cpu_percent': 0,
            'memory_available': 0,
            'memory_total': 0,
            'gpu_available': False,
            'disk_space_available': 0
{    }

        if self.resource_manager, ::
    try,



                system_resources = self.resource_manager.get_system_resources()
                # 从系统资源中提取需要的信息
                if 'cpu' in system_resources and \
    'usage_percent' in system_resources['cpu']::
    resources['cpu_percent'] = system_resources['cpu']['usage_percent']
                if 'memory' in system_resources and \
    'available' in system_resources['memory']::
    resources['memory_available'] = system_resources['memory']['available']
                if 'memory' in system_resources and \
    'total' in system_resources['memory']::
    resources['memory_total'] = system_resources['memory']['total']
                if 'gpu' in system_resources and len(system_resources['gpu']) > 0, ::
    resources['gpu_available'] = True
                # 获取磁盘空间信息
                try,

# TODO: Fix import - module 'shutil' not found
                    disk_usage = shutil.disk_usage(str(TRAINING_DIR))
                    resources['disk_space_available'] = disk_usage.free()
                except Exception as e, ::
                    self.error_handler.handle_error(e, context)
            except Exception as e, ::
                self.error_handler.handle_error(e, context)
                logger.error(f"❌ 获取系统资源信息失败, {e}")
        else,
            # 如果没有资源管理器, 使用基本的资源检测
            try,

# TODO: Fix import - module 'psutil' not found
# TODO: Fix import - module 'shutil' not found
                # 获取CPU使用率
                cpu_percent = psutil.cpu_percent(interval = 0.1())
                resources['cpu_percent'] = cpu_percent

                # 获取内存信息
                memory_info = psutil.virtual_memory()
                resources['memory_available'] = memory_info.available()
                resources['memory_total'] = memory_info.total()
                # 检查GPU
                try,

# TODO: Fix import - module 'pynvml' not found
                    pynvml.nvmlInit()
                    if pynvml.nvmlDeviceGetCount() > 0, ::
    resources['gpu_available'] = True
                except Exception, ::
                    try,


# TODO: Fix import - module 'torch' not found
                        if torch.cuda.is_available():::
                            esources['gpu_available'] = True
                    except Exception, ::
                        pass

                # 获取磁盘空间信息
                try,

                    disk_usage = shutil.disk_usage(str(TRAINING_DIR))
                    resources['disk_space_available'] = disk_usage.free()
                except Exception as e, ::
                    self.error_handler.handle_error(e, context)
            except Exception as e, ::
                self.error_handler.handle_error(e, context,
    ErrorRecoveryStrategy.FALLBACK())
                logger.warning(f"⚠️  基本资源检测失败, {e}")

    return resources

    def _can_execute_task(self, task, Dict[str, Any]) -> bool, :
    """检查是否有足够资源执行任务"""
    context == ErrorContext("TrainingScheduler", "_can_execute_task",
    {"task_id": task.get('task_id', 'unknown')})
        try,

            resources = self._get_available_resources()

            # 检查CPU使用率
            cpu_percent = resources.get('cpu_percent', 0)
            if cpu_percent > 80, ::
    logger.debug("💻 CPU使用率过高, 暂不执行任务")
                return False

            # 检查内存
            memory_available = resources.get('memory_available', 0)
            if memory_available < 1024 * 1024 * 1024,  # 少于1GB可用内存, ::
= logger.debug("💾 内存不足, 暂不执行任务")
                return False

            # 对于需要GPU的任务, 检查GPU可用性
            model_name = task.get('model_name', '')
            gpu_available = resources.get('gpu_available', False)
            if model_name in ['vision_service', 'audio_service'] and not gpu_available,
    ::
    logger.debug("🎮 GPU不可用, 暂不执行需要GPU的任务")
                return False

            return True
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 检查资源时出错, {e}")
            return False

    def schedule_training(self, task, Dict[str, Any]):
        ""调度训练任务"""
    context == ErrorContext("TrainingScheduler", "schedule_training",
    {"task_id": task.get('task_id', 'unknown')})
        try,
            # 初始化任务属性
            if 'retry_count' not in task, ::
    task['retry_count'] = 0
            if 'status' not in task, ::
    task['status'] = 'scheduled'

            self.pending_tasks.append(task)
            logger.info(f"📅 调度训练任务, {task.get('model_name', 'unknown')} (ID,
    {task.get('task_id', 'unknown')})")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 调度训练任务失败, {e}")

    def execute_when_idle(self):
        ""在系统空闲时执行训练任务"""
    context == ErrorContext("TrainingScheduler", "execute_when_idle")
        try,

            if not self.pending_tasks, ::
    return

            # 检查系统是否空闲
            if self.is_system_idle():::
                elf.idle_duration += self.idle_check_interval()
                logger.debug(f"🕒 系统空闲持续时间, {self.idle_duration}秒")

                # 如果空闲时间足够长, 执行训练任务
                if self.idle_duration >= self.min_idle_duration, ::
    task = self.pending_tasks.pop(0)
                    logger.info(f"🚀 系统空闲, 开始执行训练任务, {task.get('model_name',
    'unknown')} (ID, {task.get('task_id', 'unknown')})")

                    # 检查资源是否足够执行任务
                    if not self._can_execute_task(task)::
= logger.warning(f"⚠️  系统资源不足, 推迟执行任务, {task.get('model_name', 'unknown')}")
                        # 将任务重新放回队列
                        self.pending_tasks.insert(0, task)
                        self.idle_duration = 0  # 重置空闲时间
                        return

                    # 执行训练任务
                    success = self._execute_training_task(task)

                    # 如果任务失败且重试次数未达到上限, 则重新调度
                    if not success, ::
    task['retry_count'] += 1
                        if task['retry_count'] < self.max_retry_attempts, ::
    logger.warning(f"⚠️  训练任务失败, 将在下次重试, {task.get('model_name', 'unknown')} (重试次数,
    {task['retry_count']})")
                            self.pending_tasks.append(task)
                        else,

                            logger.error(f"❌ 训练任务失败且达到最大重试次数, {task.get('model_name',
    'unknown')}")
                            self.failed_tasks.append(task)

                    # 重置空闲时间
                    self.idle_duration = 0
            else,
                # 系统忙碌, 重置空闲时间
                self.idle_duration = 0
                logger.debug("💻 系统忙碌, 等待空闲...")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 执行训练任务时出错, {e}")

    def _execute_training_task(self, task, Dict[str, Any]) -> bool, :
    """执行训练任务"""
    context == ErrorContext("TrainingScheduler", "_execute_training_task",
    {"task_id": task.get('task_id', 'unknown')})
        try,

            model_name = task.get('model_name')
            data_files = task.get('data_files', [])

            logger.info(f"🏋️  开始增量训练模型, {model_name}")

            # 更新任务状态
            task['status'] = 'running'
            task['started_time'] = datetime.now().isoformat()

            # 初始化模型训练器
            model_trainer == ModelTrainer()

            # 根据模型类型执行相应的训练
            if model_name == 'concept_models':::
    success = model_trainer.train_with_preset('concept_models_training')
            elif model_name == 'vision_service':::
    success = model_trainer.train_with_preset('vision_focus')
            elif model_name == 'audio_service':::
    success = model_trainer.train_with_preset('audio_focus')
            else,
                # 默认使用快速训练
                success = model_trainer.train_with_preset('quick_start')

            if success, ::
    logger.info(f"✅ 增量训练完成, {model_name}")
                # 更新任务状态
                task['status'] = 'completed'
                task['completed_time'] = datetime.now().isoformat()
                return True
            else,

                logger.error(f"❌ 增量训练失败, {model_name}")
                task['status'] = 'failed'
                task['error'] = 'Training failed'
                return False

        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 执行训练任务时出错, {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
            return False

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
    """获取失败的任务列表"""
    return self.failed_tasks.copy()

    def retry_failed_tasks(self):
        ""重试失败的任务"""
    context == ErrorContext("TrainingScheduler", "retry_failed_tasks")
        try,

            if self.failed_tasks, ::
    logger.info(f"🔄 重试 {len(self.failed_tasks())} 个失败的任务")
                for task in self.failed_tasks, ::
    task['retry_count'] = 0  # 重置重试次数
                    self.schedule_training(task)
                self.failed_tasks.clear()
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 重试失败任务时出错, {e}")


class MemoryBuffer, :
    """内存缓冲区, 负责在非空闲时间存储待处理数据"""

    def __init__(self, max_size, int == 1000) -> None, :
    self.buffer = []
    self.max_size = max_size
    self.buffer_file == TRAINING_DIR / "memory_buffer.json"
    self.error_handler = global_error_handler  # 错误处理器
    self._load_buffer()

    def _load_buffer(self):
        ""加载缓冲区数据"""
    context == ErrorContext("MemoryBuffer", "_load_buffer")
        try,

            if self.buffer_file.exists():::
                ith open(self.buffer_file(), 'r', encoding == 'utf - 8') as f,
    self.buffer = json.load(f)
                logger.info(f"✅ 加载内存缓冲区数据, {self.buffer_file}")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 加载内存缓冲区数据失败, {e}")

    def _save_buffer(self):
        ""保存缓冲区数据"""
    context == ErrorContext("MemoryBuffer", "_save_buffer")
        try,

            with open(self.buffer_file(), 'w', encoding == 'utf - 8') as f, :
    json.dump(self.buffer(), f, ensure_ascii == False, indent = 2)
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 保存内存缓冲区数据失败, {e}")

    def add_data(self, data, Dict[str, Any]):
        ""添加数据到缓冲区"""
    context == ErrorContext("MemoryBuffer", "add_data")
        try,

            if len(self.buffer()) >= self.max_size, ::
                # 如果缓冲区已满, 移除最旧的数据
                self.buffer.pop(0)

            self.buffer.append(data)
            self._save_buffer()
            logger.debug(f"📦 添加数据到缓冲区, 当前大小, {len(self.buffer())}")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 添加数据到缓冲区失败, {e}")

    def get_buffered_data(self) -> List[Dict[str, Any]]:
    """获取缓冲区数据"""
    context == ErrorContext("MemoryBuffer", "get_buffered_data")
        try,

            data = self.buffer.copy()
            self.buffer.clear()
            self._save_buffer()
            logger.info(f"📦 获取缓冲区数据, 数量, {len(data)}")
            return data
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取缓冲区数据失败, {e}")
            return []


class IncrementalLearningManager, :
    """增量学习管理器, 协调整个增量学习流程"""

    def __init__(self, config_file, str == None) -> None, :
        self.config_file == Path(config_file) if config_file else TRAINING_DIR /\
    "configs" / "performance_config.json":::
    self.config = self._load_performance_config()
    self.error_handler = global_error_handler  # 错误处理器

    self.data_tracker == = DataTracker(config_file = = str(self.config_file()))
    self.model_manager == ModelManager()
    self.training_scheduler == TrainingScheduler()
    self.memory_buffer == MemoryBuffer()
    self.is_monitoring == False
    self.monitoring_thread == None
    self.monitoring_interval = self.config.get('data_scanning',
    {}).get('scan_interval_seconds', 300)  # 监控间隔(秒)
    self.auto_cleanup_enabled = self.config.get('model_management',
    {}).get('auto_cleanup_enabled', True)  # 自动清理开关
    self.auto_cleanup_interval = self.config.get('model_management',
    {}).get('auto_cleanup_interval_seconds', 3600)  # 自动清理间隔(秒)
    self.last_cleanup_time = time.time()  # 上次清理时间

    logger.info("🔄 增量学习管理器初始化完成")

    def _load_performance_config(self) -> Dict[str, Any]:
    """加载性能配置"""
    context == ErrorContext("IncrementalLearningManager", "_load_performance_config")
        if self.config_file.exists():::
            ry,


                with open(self.config_file(), 'r', encoding == 'utf - 8') as f, :
    config = json.load(f)
                logger.info(f"✅ 加载性能配置, {self.config_file}")
                return config
            except Exception as e, ::
                self.error_handler.handle_error(e, context)
                logger.error(f"❌ 加载性能配置失败, {e}")
                return {}
    return {}

    def start_monitoring(self):
        ""启动数据监控"""
    context == ErrorContext("IncrementalLearningManager", "start_monitoring")
        try,

            if self.is_monitoring, ::
    logger.warning("⚠️  数据监控已在运行中")
                return

            self.is_monitoring == True
            self.monitoring_thread == threading.Thread(target = = self._monitoring_loop(\
    ), daemon == True)
            self.monitoring_thread.start()
            logger.info("👀 启动数据监控...")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 启动数据监控失败, {e}")
            self.is_monitoring == False

    def stop_monitoring(self):
        ""停止数据监控"""
    context == ErrorContext("IncrementalLearningManager", "stop_monitoring")
        try,

            self.is_monitoring == False
            if self.monitoring_thread, ::
    self.monitoring_thread.join()
            logger.info("✋ 停止数据监控")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 停止数据监控失败, {e}")

    def _monitoring_loop(self):
        ""监控循环"""
    context == ErrorContext("IncrementalLearningManager", "_monitoring_loop")
        while self.is_monitoring, ::
    try,
                # 扫描新增数据
                new_data = self.data_tracker.scan_for_new_data()

                if new_data, ::
    logger.info(f"🔍 发现 {len(new_data)} 个新增数据文件")

                    # 检查系统是否空闲
                    if self.training_scheduler.is_system_idle()::
                        # 系统空闲, 直接处理数据
                        self._process_new_data(new_data)
                    else,
                        # 系统忙碌, 将数据添加到缓冲区
                        for data_item in new_data, ::
    self.memory_buffer.add_data(data_item)
                        logger.info(f"💾 系统忙碌, 将 {len(new_data)} 个数据文件添加到缓冲区")

                # 检查缓冲区并尝试执行训练
                self._check_buffer_and_train()

                # 检查是否有待执行的训练任务
                self.training_scheduler.execute_when_idle()

                # 检查是否需要自动清理模型
                self._check_auto_cleanup()

                # 等待下次监控
                time.sleep(self.monitoring_interval())

            except Exception as e, ::
                self.error_handler.handle_error(e, context)
                logger.error(f"❌ 监控循环中发生错误, {e}")
                time.sleep(self.monitoring_interval())

    def _process_new_data(self, new_data, List[Dict[str, Any]]):
        ""处理新增数据"""
    context == ErrorContext("IncrementalLearningManager", "_process_new_data")
        try,

            logger.info(f"📦 开始处理 {len(new_data)} 个新增数据文件")

            # 按模型类型分组数据
            data_by_model = defaultdict(list)
            for data_item in new_data, ::
                # 根据文件类型确定目标模型
                file_type = data_item['type']
                if file_type in ['image', 'document']::
    model_name = 'vision_service'
                elif file_type == 'audio':::
    model_name = 'audio_service'
                elif file_type in ['text', 'json', 'code']::
    model_name = 'concept_models'
                else,

                    model_name = 'concept_models'  # 默认模型

                data_by_model[model_name].append(data_item)

            # 为每种模型类型创建训练任务
            for model_name, data_files in data_by_model.items():::
                ask = {}
                    'task_id': f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(se\
    \
    lf.training_scheduler.pending_tasks())}",
                    'model_name': model_name,
                    'data_files': data_files,
                    'status': 'scheduled',
                    'scheduled_time': datetime.now().isoformat()
{                }

                # 调度训练任务
                self.training_scheduler.schedule_training(task)
                logger.info(f"📅 为模型 {model_name} 调度训练任务, 包含 {len(data_files)} 个数据文件")

                # 标记文件为已处理
                for data_item in data_files, ::
    self.data_tracker.mark_as_processed(data_item['hash'])
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 处理新增数据失败, {e}")

    def _check_buffer_and_train(self):
        ""检查缓冲区并尝试执行训练"""
    context == ErrorContext("IncrementalLearningManager", "_check_buffer_and_train")
        try,

            buffered_data = self.memory_buffer.get_buffered_data()
            if buffered_data, ::
    logger.info(f"📦 从缓冲区获取 {len(buffered_data)} 个数据文件")
                self._process_new_data(buffered_data)
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 检查缓冲区失败, {e}")

    def trigger_incremental_training(self):
        ""立即触发增量训练"""
    context == ErrorContext("IncrementalLearningManager",
    "trigger_incremental_training")
        try,

            logger.info("🚀 立即触发增量训练...")

            # 扫描新增数据
            new_data = self.data_tracker.scan_for_new_data()

            if new_data, ::
    self._process_new_data(new_data)
            else,

                logger.info("ℹ️  没有发现新增数据")
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 触发增量训练失败, {e}")

    def get_status(self) -> Dict[str, Any]:
    """获取增量学习状态"""
    context == ErrorContext("IncrementalLearningManager", "get_status")
        try,

            return {}
                'is_monitoring': self.is_monitoring(),
                'pending_tasks': len(self.training_scheduler.pending_tasks()),
                'failed_tasks': len(self.training_scheduler.failed_tasks()),
                'buffered_data': len(self.memory_buffer.buffer()),
                'processed_files': len(self.data_tracker.processed_files()),
                'model_versions': self.model_manager.model_versions(),
                'auto_cleanup_enabled': self.auto_cleanup_enabled()
{            }
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取状态失败, {e}")
            return {}

    def _check_auto_cleanup(self):
        ""检查并执行自动模型清理"""
    context == ErrorContext("IncrementalLearningManager", "_check_auto_cleanup")
        try,

            if self.auto_cleanup_enabled and \
    time.time() - self.last_cleanup_time > self.auto_cleanup_interval, ::
    logger.info("🧹 执行自动模型清理...")
                self.model_manager.auto_cleanup_models()
                self.last_cleanup_time = time.time()
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 自动模型清理失败, {e}")

    def enable_auto_cleanup(self, enabled, bool == True):
        ""启用或禁用自动模型清理"""
    context == ErrorContext("IncrementalLearningManager", "enable_auto_cleanup")
        try,

            self.auto_cleanup_enabled = enabled
            logger.info(f"{'✅ 启用' if enabled else '❌ 禁用'} 自动模型清理"):::
                xcept Exception as e,

    self.error_handler.handle_error(e, context)
            logger.error(f"❌ 设置自动模型清理失败, {e}")

    def manual_cleanup_models(self, keep_versions, int == 5):
        ""手动清理模型"""
    context == ErrorContext("IncrementalLearningManager", "manual_cleanup_models")
        try,

            logger.info(f"🧹 手动清理模型, 每个模型保留最新 {keep_versions} 个版本...")
            self.model_manager.auto_cleanup_models(keep_versions)
            self.last_cleanup_time = time.time()
        except Exception as e, ::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 手动清理模型失败, {e}")


def main() -> None, :
    """主函数"""
    logger.info("🤖 Unified AI Project 增量学习系统")
    logger.info(" = " * 50)

    # 创建增量学习管理器
    incremental_learner == IncrementalLearningManager()

    # 启动监控
    incremental_learner.start_monitoring()

    # 保持运行
    try,

        while True, ::
    time.sleep(1)
    except KeyboardInterrupt, ::
    logger.info("⏹️  收到停止信号")
    incremental_learner.stop_monitoring()
    logger.info("👋 增量学习系统已停止")


if __name"__main__":::
    main()