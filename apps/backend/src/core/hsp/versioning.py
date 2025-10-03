#!/usr/bin/env python3
"""
HSP协议版本管理模块
负责实现HSP协议的版本管理、兼容性处理和升级机制
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import semver
from dataclasses import dataclass

logger: Any = logging.getLogger(__name__)

@dataclass
class HSPVersionInfo:
    """HSP版本信息"""
    version: str
    release_date: str
    description: str
    compatible_versions: List[str]
    breaking_changes: List[str]
    deprecated_features: List[str]

@dataclass
class HSPVersionCompatibility:
    """HSP版本兼容性信息"""
    from_version: str
    to_version: str
    is_compatible: bool
    conversion_needed: bool
    conversion_handler: Optional[str] = None

class HSPVersionManager:
    """HSP版本管理器"""

    def __init__(self) -> None:
        self.current_version = "0.1.0"
        self.supported_versions = [
            "0.1.0"
        ]
        self.version_history: List[HSPVersionInfo] = []
        self.compatibility_matrix: Dict[str, Dict[str, HSPVersionCompatibility]] = {}
        self.version_converters: Dict[str, Callable] = {}

        # 初始化版本历史
        self._initialize_version_history()
        # 初始化兼容性矩阵
        self._initialize_compatibility_matrix()

        logger.info(f"HSP版本管理器初始化完成，当前版本: {self.current_version}")

    def _initialize_version_history(self):
        """初始化版本历史"""
        version_0_1_0 = HSPVersionInfo(
            version="0.1.0",
            release_date="2023-01-01",
            description="Initial release of HSP protocol",
            compatible_versions=[],
            breaking_changes=[],
            deprecated_features=[]
        )
        self.version_history.append(version_0_1_0)

    def _initialize_compatibility_matrix(self):
        """初始化兼容性矩阵"""
        # 版本0.1.0与自身兼容
        compatibility = HSPVersionCompatibility(
            from_version="0.1.0",
            to_version="0.1.0",
            is_compatible=True,
            conversion_needed=False
        )
        self._set_compatibility(compatibility)

    def register_version(self, version_info: HSPVersionInfo):
        """注册新版本"""
        self.version_history.append(version_info)
        if version_info.version not in self.supported_versions:
            self.supported_versions.append(version_info.version)
        logger.info(f"新版本已注册: {version_info.version}")

    def get_version_info(self, version: str) -> Optional[HSPVersionInfo]:
        """获取版本信息"""
        for version_info in self.version_history:
            if version_info.version == version:
                return version_info
        return None

    def is_version_supported(self, version: str) -> bool:
        """检查版本是否受支持"""
        return version in self.supported_versions

    def get_supported_versions(self) -> List[str]:
        """获取所有受支持的版本"""
        return self.supported_versions.copy()

    def _set_compatibility(self, compatibility: HSPVersionCompatibility):
        """设置版本兼容性"""
        from_ver = compatibility.from_version
        to_ver = compatibility.to_version

        if from_ver not in self.compatibility_matrix:
            self.compatibility_matrix[from_ver] = {}

        self.compatibility_matrix[from_ver][to_ver] = compatibility

    def get_compatibility(self, from_version: str, to_version: str) -> Optional[HSPVersionCompatibility]:
        """获取版本兼容性信息"""
        if from_version in self.compatibility_matrix:
            if to_version in self.compatibility_matrix[from_version]:
                return self.compatibility_matrix[from_version][to_version]
        return None

    def check_compatibility(self, from_version: str, to_version: str) -> bool:
        """检查两个版本是否兼容"""
        compatibility = self.get_compatibility(from_version, to_version)
        if compatibility:
            return compatibility.is_compatible
        return False

    def is_upgrade_needed(self, current_version: str, target_version: str) -> bool:
        """检查是否需要升级"""
        try:
            current = semver.VersionInfo.parse(current_version)
            target = semver.VersionInfo.parse(target_version)
            return target > current
        except ValueError:
            # 如果版本号不符合semver格式，进行字符串比较
            return target_version > current_version

    def register_converter(self, version_pair: str, converter: Callable):
        """注册版本转换器"""
        self.version_converters[version_pair] = converter
        logger.debug(f"版本转换器已注册: {version_pair}")

    def convert_message(self, message: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """转换消息版本"""
        # 检查是否需要转换
        compatibility = self.get_compatibility(from_version, to_version)
        if not compatibility or not compatibility.conversion_needed:
            return message

        # 查找转换器
        version_pair = f"{from_version}->{to_version}"
        converter = self.version_converters.get(version_pair)
        if not converter:
            # 尝试反向转换器
            reverse_pair = f"{to_version}->{from_version}"
            reverse_converter = self.version_converters.get(reverse_pair)
            if reverse_converter:
                # 对于反向转换器，我们需要反向应用
                logger.warning(f"使用反向转换器: {reverse_pair}")
                return message  # 简化处理，实际应该实现反向转换逻辑
            else:
                raise ValueError(f"未找到版本转换器: {version_pair}")

        # 应用转换
        try:
            converted_message = converter(message)
            logger.debug(f"消息版本转换成功: {from_version} -> {to_version}")
            return converted_message
        except Exception as e:
            logger.error(f"消息版本转换失败: {e}")
            raise

    def negotiate_version(self, client_version: str, server_version: str) -> Optional[str]:
        """协商版本"""
        # 检查客户端版本是否受支持
        if not self.is_version_supported(client_version):
            logger.warning(f"客户端版本不受支持: {client_version}")
            return None

        # 检查服务器版本是否受支持
        if not self.is_version_supported(server_version):
            logger.warning(f"服务器版本不受支持: {server_version}")
            return None

        # 检查兼容性
        if self.check_compatibility(client_version, server_version):
            # 选择较低的版本以确保兼容性
            try:
                client = semver.VersionInfo.parse(client_version)
                server = semver.VersionInfo.parse(server_version)
                return client_version if client <= server else server_version
            except ValueError:
                # 如果版本号不符合semver格式，选择客户端版本
                return client_version
        else:
            logger.warning(f"版本不兼容: {client_version} <-> {server_version}")
            return None

    def get_version_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """获取版本迁移路径"""
        # 简化实现，实际应该计算最短迁移路径
        path = [from_version]

        # 检查直接兼容性
        if self.check_compatibility(from_version, to_version):
            path.append(to_version)
            return path

        # 如果没有直接兼容性，返回空路径
        return []

    def get_deprecated_features(self, version: str) -> List[str]:
        """获取版本中的废弃特性"""
        version_info = self.get_version_info(version)
        if version_info:
            return version_info.deprecated_features
        return []

    def get_breaking_changes(self, version: str) -> List[str]:
        """获取版本中的破坏性变更"""
        version_info = self.get_version_info(version)
        if version_info:
            return version_info.breaking_changes
        return []

class HSPVersionConverter:
    """HSP版本转换器"""

    def __init__(self, version_manager: HSPVersionManager) -> None:
        self.version_manager = version_manager
        self._register_converters()

    def _register_converters(self):
        """注册版本转换器"""
        # 注册0.1.0到0.2.0的转换器（示例）
        self.version_manager.register_converter("0.1.0->0.2.0", self._convert_0_1_0_to_0_2_0)

        # 注册兼容性信息
        compatibility_0_1_0_to_0_2_0 = HSPVersionCompatibility(
            from_version="0.1.0",
            to_version="0.2.0",
            is_compatible=True,
            conversion_needed=True,
            conversion_handler="0.1.0->0.2.0"
        )
        self.version_manager._set_compatibility(compatibility_0_1_0_to_0_2_0)

    def _convert_0_1_0_to_0_2_0(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """将0.1.0版本消息转换为0.2.0版本"""
        converted = message.copy()

        # 更新协议版本
        converted["protocol_version"] = "0.2.0"

        # 转换消息信封结构（示例）
        if "hsp_envelope_version" in converted:
            converted["hsp_envelope_version"] = "0.2.0"

        # 转换载荷结构（示例）
        if "payload" in converted and isinstance(converted["payload"], dict):
            payload = converted["payload"]
            # 添加新的载荷字段
            if "metadata" not in payload:
                payload["metadata"] = {}

            # 更新时间戳格式（示例）
            if "timestamp_sent" in converted:
                # 假设新版本需要不同的时间戳格式
                pass

        logger.debug("0.1.0到0.2.0版本转换完成")
        return converted

    def convert_message_with_version_check(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """根据版本检查转换消息"""
        message_version = message.get("protocol_version", "0.1.0")
        current_version = self.version_manager.current_version

        # 如果版本相同，无需转换
        if message_version == current_version:
            return message

        # 检查是否需要升级
        if self.version_manager.is_upgrade_needed(message_version, current_version):
            # 转换到当前版本
            return self.version_manager.convert_message(message, message_version, current_version)
        else:
            # 消息版本比当前版本新，可能需要降级或其他处理
            logger.warning(f"消息版本比当前版本新: {message_version} > {current_version}")
            return message

class HSPVersionNegotiator:
    """HSP版本协商器"""

    def __init__(self, version_manager: HSPVersionManager) -> None:
        self.version_manager = version_manager

    def negotiate_with_capabilities(self, client_capabilities: List[str],
                                  server_capabilities: List[str]) -> Optional[str]:
        """基于能力协商版本"""
        # 找到共同支持的版本
        common_versions = set(client_capabilities) & set(server_capabilities)

        if not common_versions:
            logger.warning("客户端和服务器没有共同支持的版本")
            return None

        # 选择最高版本
        try:
            # 使用semver排序
            sorted_versions = sorted(common_versions, key=lambda v: semver.VersionInfo.parse(v), reverse=True)
            return sorted_versions[0]
        except ValueError:
            # 如果版本号不符合semver格式，返回第一个共同版本
            return list(common_versions)[0]

    def get_upgrade_recommendation(self, current_version: str) -> Optional[str]:
        """获取升级建议"""
        supported_versions = self.version_manager.get_supported_versions()

        try:
            current = semver.VersionInfo.parse(current_version)
            # 找到比当前版本高的最新版本
            newer_versions = [v for v in supported_versions if semver.VersionInfo.parse(v) > current]

            if newer_versions:
                # 返回最新的版本
                sorted_newer = sorted(newer_versions, key=lambda v: semver.VersionInfo.parse(v), reverse=True)
                return sorted_newer[0]
        except ValueError:
            pass

        return None

class HSPVersionedMessageHandler:
    """HSP版本化消息处理器"""

    def __init__(self, version_manager: HSPVersionManager, version_converter: HSPVersionConverter) -> None:
        self.version_manager = version_manager
        self.version_converter = version_converter

    async def handle_versioned_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理版本化消息"""
        # 1. 检查消息版本
        message_version = message.get("protocol_version", "0.1.0")

        # 2. 验证版本支持
        if not self.version_manager.is_version_supported(message_version):
            raise ValueError(f"不支持的消息版本: {message_version}")

        # 3. 转换消息到当前版本
        converted_message = self.version_converter.convert_message_with_version_check(message)

        # 4. 处理消息（这里应该是实际的消息处理逻辑）
        processed_message = await self._process_message(converted_message)

        # 5. 返回处理结果
        return processed_message

    async def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息（示例实现）"""
        # 这里应该是实际的消息处理逻辑
        # 简化实现，只是记录日志并返回原消息
        logger.info(f"处理版本化消息: {message.get('message_id', 'unknown')}")
        _ = await asyncio.sleep(0.01)  # 模拟处理时间
        return message

# 版本兼容性检查工具
class HSPCompatibilityChecker:
    """HSP兼容性检查器"""

    def __init__(self, version_manager: HSPVersionManager) -> None:
        self.version_manager = version_manager

    def check_message_compatibility(self, message: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        """检查消息与目标版本的兼容性"""
        current_version = message.get("protocol_version", "0.1.0")

        result = {
            "current_version": current_version,
            "target_version": target_version,
            "is_compatible": False,
            "conversion_needed": False,
            "issues": [],
            "recommendations": []
        }

        # 检查版本兼容性
        compatibility = self.version_manager.get_compatibility(current_version, target_version)
        if compatibility:
            result["is_compatible"] = compatibility.is_compatible
            result["conversion_needed"] = compatibility.conversion_needed

            if not compatibility.is_compatible:
                _ = result["issues"].append("版本不兼容")

            if compatibility.conversion_needed:
                _ = result["recommendations"].append("需要进行版本转换")
        else:
            _ = result["issues"].append("未找到版本兼容性信息")
            _ = result["recommendations"].append("建议升级到受支持的版本")

        return result

    def generate_compatibility_report(self, versions: List[str]) -> Dict[str, Any]:
        """生成兼容性报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "versions": versions,
            "compatibility_matrix": {},
            "issues": [],
            "summary": ""
        }

        # 生成兼容性矩阵
        for from_ver in versions:
            report["compatibility_matrix"][from_ver] = {}
            for to_ver in versions:
                compatibility = self.version_manager.get_compatibility(from_ver, to_ver)
                if compatibility:
                    report["compatibility_matrix"][from_ver][to_ver] = {
                        "compatible": compatibility.is_compatible,
                        "conversion_needed": compatibility.conversion_needed
                    }
                else:
                    report["compatibility_matrix"][from_ver][to_ver] = {
                        "compatible": False,
                        "conversion_needed": False,
                        "error": "未找到兼容性信息"
                    }

        # 生成摘要
        total_pairs = len(versions) * len(versions)
        compatible_pairs = sum(
            1 for from_ver in versions for to_ver in versions
            if report["compatibility_matrix"][from_ver][to_ver].get("compatible", False)
        )

        report["summary"] = {
            "total_version_pairs": total_pairs,
            "compatible_pairs": compatible_pairs,
            "compatibility_rate": compatible_pairs / total_pairs if total_pairs > 0 else 0,
            "supported_versions": self.version_manager.get_supported_versions()
        }

        return report

# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建版本管理器
    version_manager = HSPVersionManager()

    # 注册新版本（示例）
    version_0_2_0 = HSPVersionInfo(
        version="0.2.0",
        release_date=datetime.now().strftime("%Y-%m-%d"),
        description="HSP protocol version 0.2.0 with enhanced security",
        compatible_versions=["0.1.0"],
        breaking_changes=["Changed security parameter structure"],
        deprecated_features=["Old authentication method"]
    )
    version_manager.register_version(version_0_2_0)

    # 创建版本转换器
    version_converter = HSPVersionConverter(version_manager)

    # 创建版本协商器
    version_negotiator = HSPVersionNegotiator(version_manager)

    # 测试版本协商
    negotiated_version = version_negotiator.negotiate_with_capabilities(
        ["0.1.0", "0.2.0"],
        ["0.1.0", "0.2.0"]
    )
    print(f"协商版本: {negotiated_version}")

    # 测试版本转换
    test_message = {
        "message_id": "test_001",
        "protocol_version": "0.1.0",
        "message_type": "HSP::TestMessage_v0.1",
        "payload": {"content": "test"}
    }

    try:
        converted_message = version_converter.convert_message_with_version_check(test_message)
        print("转换后的消息:", json.dumps(converted_message, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"转换失败: {e}")

    # 生成兼容性报告
    compatibility_checker = HSPCompatibilityChecker(version_manager)
    report = compatibility_checker.generate_compatibility_report(["0.1.0", "0.2.0"])
    print("兼容性报告:", json.dumps(report, indent=2, ensure_ascii=False))