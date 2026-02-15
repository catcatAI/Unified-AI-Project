#!/usr/bin/env python3
"""
Angela AI - Environment Configuration Validator
环境配置验证器

验证所有必需的环境变量是否正确配置，提供清晰的错误提示。
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
logger = logging.getLogger(__name__)


class Severity(Enum):
    """问题严重程度"""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str) -> None:
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        self.info.append(message)


@dataclass
class EnvVarSpec:
    """环境变量规范"""
    name: str
    description: str
    required: bool = True
    default: Optional[str] = None
    validator: Optional[callable] = None
    allowed_values: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, env_file: Optional[Path] = None):
        self.env_file = env_file or Path.cwd() / ".env"
        self.result = ValidationResult(valid=True)
        self.specs = self._define_specs()
    
    def _define_specs(self) -> List[EnvVarSpec]:
        """定义所有环境变量规范"""
        return [
            # 应用设置
            EnvVarSpec(
                name="ANGELA_ENV",
                description="应用运行环境",
                required=True,
                default="development",
                allowed_values=["development", "production", "testing"]
            ),
            EnvVarSpec(
                name="NODE_ENV",
                description="Node.js 运行环境",
                required=True,
                default="development",
                allowed_values=["development", "production", "test"]
            ),
            
            # 后端配置
            EnvVarSpec(
                name="BACKEND_HOST",
                description="后端服务器地址",
                required=True,
                default="127.0.0.1"
            ),
            EnvVarSpec(
                name="BACKEND_PORT",
                description="后端服务器端口",
                required=True,
                default="8000",
                validator=lambda x: x.isdigit() and 1 <= int(x) <= 65535
            ),
            EnvVarSpec(
                name="BACKEND_URL",
                description="后端服务器完整 URL",
                required=True,
                default="http://127.0.0.1:8000"
            ),
            
            # 安全密钥
            EnvVarSpec(
                name="ANGELA_KEY_A",
                description="后端控制密钥",
                required=True,
                min_length=32,
                validator=lambda x: len(x) >= 32
            ),
            EnvVarSpec(
                name="ANGELA_KEY_B",
                description="移动通信密钥",
                required=True,
                min_length=32,
                validator=lambda x: len(x) >= 32
            ),
            EnvVarSpec(
                name="ANGELA_KEY_C",
                description="桌面同步密钥",
                required=True,
                min_length=32,
                validator=lambda x: len(x) >= 32
            ),
            
            # 数据库配置
            EnvVarSpec(
                name="DATABASE_URL",
                description="数据库连接 URL",
                required=True,
                default="sqlite:///./angela.db"
            ),
            
            # Live2D 配置
            EnvVarSpec(
                name="LIVE2D_MODEL_PATH",
                description="Live2D 模型路径",
                required=False
            ),
            
            # 性能设置
            EnvVarSpec(
                name="PERFORMANCE_MODE",
                description="性能模式",
                required=False,
                default="auto",
                allowed_values=["auto", "low", "medium", "high", "ultra"]
            ),
            EnvVarSpec(
                name="TARGET_FPS",
                description="目标帧率",
                required=False,
                default="60",
                validator=lambda x: x.isdigit() and 30 <= int(x) <= 144
            ),
            
            # 日志配置
            EnvVarSpec(
                name="LOG_LEVEL",
                description="日志级别",
                required=False,
                default="info",
                allowed_values=["debug", "info", "warning", "error", "critical"]
            ),
            
            # 功能开关
            EnvVarSpec(
                name="ENABLE_VOICE_RECOGNITION",
                description="启用语音识别",
                required=False,
                default="true",
                allowed_values=["true", "false"]
            ),
            EnvVarSpec(
                name="ENABLE_TTS",
                description="启用语音合成",
                required=False,
                default="true",
                allowed_values=["true", "false"]
            ),
            EnvVarSpec(
                name="ENABLE_WEBSOCKET",
                description="启用 WebSocket",
                required=False,
                default="true",
                allowed_values=["true", "false"]
            ),
        ]
    
    def _validate_value(self, spec: EnvVarSpec, value: Optional[str]) -> None:
        """验证单个环境变量值"""
        if value is None or value == "":
            if spec.required:
                self.result.add_error(
                    f"缺少必需的环境变量: {spec.name}\n"
                    f"  描述: {spec.description}"
                )
            elif spec.default:
                os.environ[spec.name] = spec.default
                self.result.add_info(
                    f"使用默认值: {spec.name} = {spec.default}"
                )
            return
        
        # 验证允许的值
        if spec.allowed_values and value not in spec.allowed_values:
            self.result.add_error(
                f"环境变量值无效: {spec.name} = {value}\n"
                f"  允许的值: {', '.join(spec.allowed_values)}"
            )
        
        # 验证长度
        if spec.min_length and len(value) < spec.min_length:
            self.result.add_error(
                f"环境变量值太短: {spec.name}\n"
                f"  当前长度: {len(value)}, 最小长度: {spec.min_length}"
            )
        
        if spec.max_length and len(value) > spec.max_length:
            self.result.add_error(
                f"环境变量值太长: {spec.name}\n"
                f"  当前长度: {len(value)}, 最大长度: {spec.max_length}"
            )
        
        # 自定义验证器
        if spec.validator and not spec.validator(value):
            self.result.add_error(
                f"环境变量值验证失败: {spec.name} = {value}"
            )
        
        # 检查默认值占位符
        if value.startswith("your_") or value.endswith("_here"):
            self.result.add_warning(
                f"环境变量可能使用默认占位符: {spec.name} = {value}\n"
                f"  请更新为实际值"
            )
    
    def _check_file_paths(self) -> None:
        """检查文件路径是否存在"""
        paths_to_check = [
            ("LIVE2D_MODEL_PATH", "Live2D 模型文件"),
        ]
        
        for var_name, description in paths_to_check:
            path = os.environ.get(var_name)
            if path:
                file_path = Path(path)
                if not file_path.exists():
                    self.result.add_warning(
                        f"{description} 不存在: {path}\n"
                        f"  环境变量: {var_name}"
                    )
    
    def _load_env_file(self) -> None:
        """加载 .env 文件"""
        if not self.env_file.exists():
            self.result.add_warning(
                f".env 文件不存在: {self.env_file}\n"
                f"  请从 .env.example 复制并配置"
            )
            return
        
        self.result.add_info(f"找到 .env 文件: {self.env_file}")
        
        # 读取并解析 .env 文件
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value
    
    def validate(self) -> ValidationResult:
        """执行完整验证"""
        self._load_env_file()
        
        # 验证所有规范的环境变量
        for spec in self.specs:
            value = os.environ.get(spec.name)
            self._validate_value(spec, value)
        
        # 检查文件路径
        self._check_file_paths()
        
        return self.result
    
    def print_report(self) -> None:
        """打印验证报告"""
        logger.info("=" * 60)
        logger.info("Angela AI - 环境配置验证报告")
        logger.info("=" * 60)
        
        if self.result.valid:
            logger.info("✓ 配置验证通过")
        else:
            logger.info("✗ 配置验证失败")
        
        logger.info()
        
        # 打印错误
        if self.result.errors:
            logger.error(f"错误 ({len(self.result.errors)}):")
            logger.info("-" * 60)
            for error in self.result.errors:
                logger.error(f"  ❌ {error}")
            logger.info()
        
        # 打印警告
        if self.result.warnings:
            logger.warning(f"警告 ({len(self.result.warnings)}):")
            logger.info("-" * 60)
            for warning in self.result.warnings:
                logger.warning(f"  ⚠️  {warning}")
            logger.info()
        
        # 打印信息
        if self.result.info:
            logger.info(f"信息 ({len(self.result.info)}):")
            logger.info("-" * 60)
            for info in self.result.info:
                logger.info(f"  ℹ️  {info}")
            logger.info()
        
        logger.info("=" * 60)
        
        # 返回退出码
        sys.exit(0 if self.result.valid else 1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="验证 Angela AI 环境配置"
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help=".env 文件路径"
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="静默模式，只输出错误"
    )
    
    args = parser.parse_args()
    
    validator = ConfigValidator(env_file=args.env_file)
    result = validator.validate()
    
    if not args.silent:
        validator.print_report()
    else:
        if not result.valid:
            for error in result.errors:
                logger.error(f"ERROR: {error}", file=sys.stderr)
        sys.exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()