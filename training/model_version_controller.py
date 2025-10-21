#!/usr/bin/env python3
"""
模型版本控制器
实现模型版本管理、比较、标记和回滚功能
"""

import json
import logging
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

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
    )
except ImportError,::
    # 如果路径配置模块不可用,使用默认路径处理
    PROJECT_ROOT = project_root
    DATA_DIR == PROJECT_ROOT / "data"
    TRAINING_DIR == PROJECT_ROOT / "training"
    MODELS_DIR == TRAINING_DIR / "models"


# 配置日志
logging.basicConfig(,
    level=logging.INFO(),
    format, str='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
    logging.FileHandler(TRAINING_DIR / 'model_version_controller.log'),
    logging.StreamHandler()
    ]
)
logger, Any = logging.getLogger(__name__)


class VersionControlManager,
    """版本控制管理器,负责模型版本管理、比较、标记和回滚操作"""

    def __init__(self, models_dir, str == None) -> None,
        self.models_dir == Path(models_dir) if models_dir else MODELS_DIR,::
    self.version_file = self.models_dir / "model_versions.json"
    self.versions = {}
    self.error_handler = global_error_handler  # 错误处理器
    self._load_versions()
    logger.info("🔄 版本控制管理器初始化完成")

    def _load_versions(self):
        ""加载版本信息"""
    context == ErrorContext("VersionControlManager", "_load_versions")
        try,

            if self.version_file.exists():::
                ith open(self.version_file(), 'r', encoding == 'utf-8') as f,
    self.versions = json.load(f)
                logger.info(f"✅ 加载版本信息, {self.version_file}")
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 加载版本信息失败, {e}")

    def _save_versions(self):
        ""保存版本信息"""
    context == ErrorContext("VersionControlManager", "_save_versions")
        try,
            # 确保模型目录存在
            self.models_dir.mkdir(parents == True, exist_ok == True)

            with open(self.version_file(), 'w', encoding == 'utf-8') as f,
    json.dump(self.versions(), f, ensure_ascii == False, indent=2, default=str)
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 保存版本信息失败, {e}")

    def _generate_version_name(self, model_name, str, version_type, str == "release") -> str,
    """
    生成版本名称

    Args,
            model_name, 模型名称
            version_type, 版本类型 (release, beta, alpha)

    Returns, str 生成的版本名称
    """
    context == ErrorContext("VersionControlManager", "_generate_version_name", {"model_name": model_name})
        try,
            # 获取当前模型的最新版本号
            major, minor, patch = 1, 0, 0
            if model_name in self.versions,::
    versions = self.versions[model_name].get('versions', [])
                if versions,::
                    # 解析最新版本号
                    latest_version = versions[-1]
                    version_str = latest_version['version'].split('_')[0]  # 获取 vX.Y.Z 部分
                    if version_str.startswith('v'):::
                        ersion_parts == version_str[1,].split('.')
                        if len(version_parts) == 3,::
    major, minor, patch = map(int, version_parts)

            # 根据版本类型递增版本号
            if version_type == "release":::
    major += 1
                minor, patch = 0, 0
            elif version_type == "beta":::
    minor += 1
                patch = 0
            else,  # alpha
                patch += 1

            # 生成版本名称
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            version_name = f"{model_name}_v{major}.{minor}.{patch}_{timestamp}.pth"

            return version_name
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 生成版本名称失败, {e}")
            # 返回默认版本名称
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"{model_name}_v1.0.0_{timestamp}.pth"

    def _calculate_file_hash(self, file_path, Path) -> str,
    """
    计算文件哈希值

    Args,
            file_path, 文件路径

    Returns, str 文件哈希值
    """
    context == ErrorContext("VersionControlManager", "_calculate_file_hash", {"file_path": str(file_path)})
        try,

            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f,
    for chunk in iter(lambda, f.read(4096), b""):::
    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 计算文件哈希失败 {file_path} {e}")
            return ""

    def create_version(self, model_name, str, model_path, Path,
                      metadata, Dict[...]
    """
    创建新版本

    Args,
            model_name, 模型名称
            model_path, 模型文件路径
            metadata, 版本元数据,
    version_type, 版本类型 (release, beta, alpha):
                eturns,
            Optional[str] 版本名称,如果创建失败则返回None
    """
    context == ErrorContext("VersionControlManager", "create_version", {
            "model_name": model_name,
            "version_type": version_type
    })
        try,

            if not model_path.exists():::
 = logger.error(f"❌ 模型文件不存在, {model_path}")
                return None

            # 生成版本名称
            version_name = self._generate_version_name(model_name, version_type)
            version_path = self.models_dir / version_name

            # 复制模型文件
            shutil.copy2(model_path, version_path)

            # 计算文件哈希
            file_hash = self._calculate_file_hash(version_path)

            # 获取文件大小
            file_size = version_path.stat().st_size

            # 准备版本信息
            version_info = {
                'version': version_name,
                'path': str(version_path),
                'created_at': datetime.now().isoformat(),
                'model_name': model_name,
                'version_type': version_type,
                'performance_metrics': metadata.get('performance_metrics', {}) if metadata else {}:
                    training_data': metadata.get('training_data', {}) if metadata else {}:
change_log': metadata.get('change_log', '') if metadata else '',:::
tags': metadata.get('tags', []) if metadata else []::
dependencies': metadata.get('dependencies', []) if metadata else []::
size_bytes': file_size,
                'hash': file_hash
            }

            # 更新版本信息
            if model_name not in self.versions,::
    self.versions[model_name] = {
                    'versions': []
                    'latest': version_name,
                    'created_at': datetime.now().isoformat()
                }

            self.versions[model_name]['versions'].append(version_info)
            self.versions[model_name]['latest'] = version_name
            self.versions[model_name]['updated_at'] = datetime.now().isoformat()

            # 保存版本信息
            self._save_versions()

            logger.info(f"✅ 创建模型版本, {version_name}")
            return version_name
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 创建模型版本失败, {e}")
            return None

    def rollback_to_version(self, model_name, str, target_version, str) -> bool,
    """
    回滚到指定版本

    Args,
            model_name, 模型名称
            target_version, 目标版本名称

    Returns, bool 回滚是否成功
    """
    context == ErrorContext("VersionControlManager", "rollback_to_version", {
            "model_name": model_name,
            "target_version": target_version
    })
        try,
            # 检查模型和版本是否存在
            if model_name not in self.versions,::
    logger.error(f"❌ 模型 {model_name} 不存在")
                return False

            # 查找目标版本
            target_version_info == None
            for version_info in self.versions[model_name]['versions']::
    if version_info['version'] == target_version,::
    target_version_info = version_info
                    break

            if not target_version_info,::
    logger.error(f"❌ 版本 {target_version} 不存在")
                return False

            target_path == Path(target_version_info['path'])
            if not target_path.exists():::
 = logger.error(f"❌ 版本文件不存在, {target_path}")
                return False

            # 备份当前版本(如果存在)
            current_version = self.versions[model_name].get('latest')
            if current_version and current_version != target_version,::
    current_version_info == None
                for version_info in self.versions[model_name]['versions']::
    if version_info['version'] == current_version,::
    current_version_info = version_info
                        break

                if current_version_info,::
    current_path == Path(current_version_info['path'])
                    if current_path.exists():::
                        ackup_name = f"{current_version}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
                        backup_path = self.models_dir / backup_name
                        shutil.copy2(current_path, backup_path)
                        logger.info(f"💾 备份当前版本到, {backup_name}")

            # 更新最新版本信息
            self.versions[model_name]['latest'] = target_version
            self.versions[model_name]['updated_at'] = datetime.now().isoformat()

            # 保存版本信息
            self._save_versions()

            logger.info(f"✅ 回滚到版本 {target_version} 成功")
            return True
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 回滚到版本 {target_version} 失败, {e}")
            return False

    def get_version_history(self, model_name, str) -> List[Dict[str, Any]]
    """
    获取模型版本历史

    Args,
            model_name, 模型名称

    Returns, List[...] 版本历史列表
    """
    context == ErrorContext("VersionControlManager", "get_version_history", {"model_name": model_name})
        try,

            if model_name in self.versions,::
    return self.versions[model_name].get('versions', [])
            return []
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取版本历史失败, {e}")
            return []

    def compare_versions(self, model_name, str, version1, str, version2, str) -> Dict[str, Any]
    """
    比较两个版本的性能指标

    Args,
            model_name, 模型名称
            version1, 第一个版本名称
            version2, 第二个版本名称

    Returns, Dict[...] 版本比较结果
    """
    context == ErrorContext("VersionControlManager", "compare_versions", {
            "model_name": model_name,
            "version1": version1,
            "version2": version2
    })
        try,

            comparison = {
                'model_name': model_name,
                'version1': version1,
                'version2': version2,
                'metrics_comparison': {}
                'improvements': []
                'degradations': []
            }

            # 获取两个版本的信息
            version1_info == None
            version2_info == None

            if model_name in self.versions,::
    for version_info in self.versions[model_name]['versions']::
    if version_info['version'] == version1,::
    version1_info = version_info
                    elif version_info['version'] == version2,::
    version2_info = version_info

            if not version1_info or not version2_info,::
    logger.error(f"❌ 无法找到要比较的版本")
                return comparison

            # 比较性能指标
            metrics1 = version1_info.get('performance_metrics', {})
            metrics2 = version2_info.get('performance_metrics', {})

            # 比较共同指标
            common_metrics = set(metrics1.keys()) & set(metrics2.keys())
            for metric in common_metrics,::
    value1 = metrics1[metric]
                value2 = metrics2[metric]
                difference = value2 - value1
                comparison['metrics_comparison'][metric] = {
                    'version1': value1,
                    'version2': value2,
                    'difference': difference,
                    'improved': difference > 0
                }

                # 记录改进和退步的指标
                if difference > 0,::
    comparison['improvements'].append({
                        'metric': metric,
                        'improvement': difference
                    })
                elif difference < 0,::
    comparison['degradations'].append({
                        'metric': metric,
                        'degradation': abs(difference)
                    })

            return comparison
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 比较版本失败, {e}")
            return {}

    def tag_version(self, model_name, str, version, str, tags, List[str]) -> bool,
    """
    为版本添加标签

    Args,
            model_name, 模型名称
            version, 版本名称
            tags, 标签列表

    Returns, bool 操作是否成功
    """
    context == ErrorContext("VersionControlManager", "tag_version", {
            "model_name": model_name,
            "version": version
    })
        try,
            # 查找指定版本
            if model_name not in self.versions,::
    logger.error(f"❌ 模型 {model_name} 不存在")
                return False

            version_found == False
            for version_info in self.versions[model_name]['versions']::
    if version_info['version'] == version,::
                    # 添加标签(去重)
                    existing_tags = set(version_info.get('tags', []))
                    new_tags = set(tags)
                    version_info['tags'] = list(existing_tags | new_tags)
                    version_found == True
                    break

            if not version_found,::
    logger.error(f"❌ 版本 {version} 不存在")
                return False

            # 保存版本信息
            self._save_versions()

            logger.info(f"✅ 为版本 {version} 添加标签, {tags}")
            return True
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 为版本添加标签失败, {e}")
            return False

    def get_versions_by_tag(self, model_name, str, tag, str) -> List[Dict[str, Any]]
    """
    根据标签获取版本

    Args,
            model_name, 模型名称
            tag, 标签

    Returns, List[...] 匹配标签的版本列表
    """
    context == ErrorContext("VersionControlManager", "get_versions_by_tag", {
            "model_name": model_name,
            "tag": tag
    })
        try,

            matching_versions = []

            if model_name in self.versions,::
    for version_info in self.versions[model_name]['versions']::
    if tag in version_info.get('tags', [])::
 = matching_versions.append(version_info)

            return matching_versions
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 根据标签获取版本失败, {e}")
            return []

    def get_latest_version(self, model_name, str) -> Optional[Dict[str, Any]]
    """
    获取模型的最新版本

    Args,
            model_name, 模型名称

    Returns,
            Optional[Dict[str, Any]] 最新版本信息,如果不存在则返回None
    """
    context == ErrorContext("VersionControlManager", "get_latest_version", {"model_name": model_name})
        try,

            if model_name in self.versions,::
    latest_version_name = self.versions[model_name].get('latest')
                if latest_version_name,::
    for version_info in self.versions[model_name]['versions']::
    if version_info['version'] == latest_version_name,::
    return version_info
            return None
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取最新版本失败, {e}")
            return None

    def delete_version(self, model_name, str, version, str) -> bool,
    """
    删除指定版本

    Args,
            model_name, 模型名称
            version, 版本名称

    Returns, bool 删除是否成功
    """
    context == ErrorContext("VersionControlManager", "delete_version", {
            "model_name": model_name,
            "version": version
    })
        try,
            # 检查模型和版本是否存在
            if model_name not in self.versions,::
    logger.error(f"❌ 模型 {model_name} 不存在")
                return False

            # 查找并删除版本信息
            version_found == False
            versions = self.versions[model_name]['versions']
            for i, version_info in enumerate(versions)::
                f version_info['version'] == version,
                    # 删除版本文件
                    version_path == Path(version_info['path'])
                    if version_path.exists():::
 = version_path.unlink()
                        logger.info(f"🗑️  删除版本文件, {version_path}")

                    # 从版本列表中移除
                    versions.pop(i)
                    version_found == True
                    break

            if not version_found,::
    logger.error(f"❌ 版本 {version} 不存在")
                return False

            # 如果删除的是最新版本,更新latest指向
            if self.versions[model_name].get('latest') == version,::
    if versions,::
    self.versions[model_name]['latest'] = versions[-1]['version']
                else,

                    self.versions[model_name]['latest'] = None

            # 保存版本信息
            self._save_versions()

            logger.info(f"✅ 删除版本 {version} 成功")
            return True
        except Exception as e,::
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 删除版本 {version} 失败, {e}")
            return False


def main() -> None,
    """主函数,用于测试版本控制管理器"""
    logger.info("🤖 Unified AI Project 模型版本控制管理器测试")
    logger.info("=" * 50)

    # 创建版本控制管理器
    version_controller == VersionControlManager()

    # 创建测试模型文件
    test_model_path == MODELS_DIR / "test_model.pth"
    test_model_path.parent.mkdir(parents == True, exist_ok == True)

    # 创建一个简单的测试文件
    with open(test_model_path, 'w') as f,
    f.write("This is a test model file for version control testing.")::
    # 测试创建版本
    logger.info("🧪 测试创建版本...")
    metadata == {:
    'performance_metrics': {
            'accuracy': 0.95(),
            'loss': 0.05(),
            'training_time': 3600
    }
    'training_data': {
            'data_count': 1000,
            'data_types': ['text', 'json']
    }
        'change_log': 'Initial version for testing',:::
            tags': ['test', 'initial']
    }

    version1 = version_controller.create_version("test_model", test_model_path, metadata, "release")
    if version1,::
    logger.info(f"✅ 创建版本成功, {version1}")
    else,

    logger.error("❌ 创建版本失败")
    return

    # 修改测试文件并创建第二个版本
    with open(test_model_path, 'w') as f,
    f.write("This is an updated test model file for version control testing."):::
        etadata2 = {
    'performance_metrics': {
            'accuracy': 0.97(),
            'loss': 0.03(),
            'training_time': 3800
    }
    'training_data': {
            'data_count': 1200,
            'data_types': ['text', 'json', 'code']
    }
    'change_log': 'Improved accuracy and added code data support',
    'tags': ['test', 'improved']
    }

    version2 = version_controller.create_version("test_model", test_model_path, metadata2, "beta")
    if version2,::
    logger.info(f"✅ 创建版本成功, {version2}")
    else,

    logger.error("❌ 创建版本失败")
    return

    # 测试版本历史查询
    logger.info("📋 测试版本历史查询...")
    history = version_controller.get_version_history("test_model")
    logger.info(f"   版本历史数量, {len(history)}")
    for version_info in history,::
    logger.info(f"   - {version_info['version']} ({version_info['version_type']})")

    # 测试版本比较
    logger.info("🔍 测试版本比较...")
    if version1 and version2,::
    comparison = version_controller.compare_versions("test_model", version1, version2)
    logger.info(f"   比较结果,")
    logger.info(f"   - 改进指标数量, {len(comparison['improvements'])}")
    logger.info(f"   - 退步指标数量, {len(comparison['degradations'])}")
        for improvement in comparison['improvements']::
    logger.info(f"     + {improvement['metric']} +{improvement['improvement'].4f}")

    # 测试标签功能
    logger.info("🏷️  测试标签功能...")
    tag_success = version_controller.tag_version("test_model", version2, ["production", "stable"])
    if tag_success,::
    logger.info("✅ 添加标签成功")
    else,

    logger.error("❌ 添加标签失败")

    # 根据标签查询版本
    production_versions = version_controller.get_versions_by_tag("test_model", "production")
    logger.info(f"   标记为'production'的版本数量, {len(production_versions)}")

    # 测试回滚功能
    logger.info("⏪ 测试回滚功能...")
    rollback_success = version_controller.rollback_to_version("test_model", version1)
    if rollback_success,::
    logger.info("✅ 回滚成功")
    else,

    logger.error("❌ 回滚失败")

    # 获取最新版本
    latest_version = version_controller.get_latest_version("test_model")
    if latest_version,::
    logger.info(f"   当前最新版本, {latest_version['version']}")

    # 清理测试文件
    try,

    test_model_path.unlink()
    logger.info("🗑️  清理测试文件完成")
    except Exception as e,::
    logger.warning(f"⚠️  清理测试文件失败, {e}")

    logger.info("✅ 模型版本控制管理器测试完成")


if __name"__main__":::
    main()