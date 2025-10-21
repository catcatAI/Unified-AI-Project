"""
修复类型定义
定义所有支持的修复类型、状态和范围
"""

from enum import Enum
from typing import Dict, Any


class FixType(Enum):
    """修复类型枚举"""

    SYNTAX_FIX = "syntax_fix"                    # 语法错误修复
    IMPORT_FIX = "import_fix"                    # 导入路径修复
    DEPENDENCY_FIX = "dependency_fix"            # 依赖关系修复
    GIT_FIX = "git_fix"                          # Git问题修复
    ENVIRONMENT_FIX = "environment_fix"          # 环境配置修复
    SECURITY_FIX = "security_fix"                # 安全漏洞修复
    CODE_STYLE_FIX = "code_style_fix"            # 代码风格修复
    PATH_FIX = "path_fix"                        # 路径修复
    CONFIGURATION_FIX = "configuration_fix"      # 配置文件修复
    PERFORMANCE_FIX = "performance_fix"          # 性能优化修复
    COMPATIBILITY_FIX = "compatibility_fix"      # 兼容性修复
    TYPE_HINT_FIX = "type_hint_fix"              # 类型提示修复
    DECORATOR_FIX = "decorator_fix"              # 装饰器修复
    CLASS_FIX = "class_fix"                      # 类定义修复
    PARAMETER_FIX = "parameter_fix"              # 参数修复
    UNDEFINED_FIX = "undefined_fix"              # 未定义变量修复
    DATA_PROCESSING_FIX = "data_processing_fix"  # 数据处理修复
    LOGIC_GRAPH_FIX = "logic_graph_fix"          # 逻辑图谱修复
    INTELLIGENT_ITERATIVE_FIX = "intelligent_iterative_fix"  # 智能迭代修复
    AI_ASSISTED_FIX = "ai_assisted_fix"          # AI辅助修复


class FixStatus(Enum):
    """修复状态枚举"""
    PENDING = "pending"                          # 待修复
    IN_PROGRESS = "in_progress"                  # 修复中
    SUCCESS = "success"                          # 修复成功
    PARTIAL_SUCCESS = "partial_success"          # 部分成功
    FAILED = "failed"                            # 修复失败
    SKIPPED = "skipped"                          # 跳过修复
    NOT_APPLICABLE = "not_applicable"            # 不适用

    SIMULATED = "simulated"                      # 模拟修复(干运行)


class FixScope(Enum):
    """修复范围枚举"""
    PROJECT = "project"                          # 整个项目
    BACKEND = "backend"                          # 仅后端
    FRONTEND = "frontend"                        # 仅前端
    DESKTOP = "desktop"                          # 仅桌面应用
    SPECIFIC_FILE = "specific_file"              # 特定文件
    SPECIFIC_DIRECTORY = "specific_directory"    # 特定目录
    SPECIFIC_MODULE = "specific_module"          # 特定模块
    SPECIFIC_TEST = "specific_test"              # 特定测试


class FixPriority(Enum):
    """修复优先级枚举"""
    CRITICAL = "critical"                        # 关键 - 立即修复
    HIGH = "high"                                # 高 - 优先修复
    NORMAL = "normal"                            # 正常 - 常规修复
    LOW = "low"                                  # 低 - 可选修复


class FixCategory:
    """修复分类"""
#     
     # 按严重程度分类
     # 

    SEVERITY_CATEGORIES = {
        "critical": [
        FixType.SYNTAX_FIX,

            FixType.SECURITY_FIX,
            FixType.DEPENDENCY_FIX


        ],
        "major": [
        FixType.IMPORT_FIX,

 FixType.GIT_FIX,


            FixType.ENVIRONMENT_FIX
        ],
        "minor": [
        FixType.CODE_STYLE_FIX,


            FixType.PATH_FIX,
            FixType.CONFIGURATION_FIX
        ],
        "optional": [
        FixType.PERFORMANCE_FIX,


            FixType.COMPATIBILITY_FIX,
#             FixType.TYPE_HINT_FIX
# 

        ]
        }

    
    # 按技术栈分类
    TECH_STACK_CATEGORIES = {

        "python": [
        FixType.SYNTAX_FIX,


            FixType.IMPORT_FIX,
            FixType.TYPE_HINT_FIX,

 FixType.CODE_STYLE_FIX


        ],
        "javascript": [
            FixType.SYNTAX_FIX,
            FixType.IMPORT_FIX,
            FixType.CODE_STYLE_FIX
        ],
        "git": [
        FixType.GIT_FIX


        ],
        "environment": [
            FixType.ENVIRONMENT_FIX,
            FixType.DEPENDENCY_FIX,
#             FixType.CONFIGURATION_FIX
# 

        ],
        "security": [
            FixType.SECURITY_FIX
        ]
        }

    
     # 按项目部分分类


    PROJECT_CATEGORIES = {
        "backend": [
        FixType.SYNTAX_FIX,

 FixType.IMPORT_FIX,


            FixType.DEPENDENCY_FIX,
            FixType.TYPE_HINT_FIX

        ],
        "frontend": [
        FixType.SYNTAX_FIX,


            FixType.IMPORT_FIX,
            FixType.CODE_STYLE_FIX

        ],
        "desktop": [
            FixType.SYNTAX_FIX,
            FixType.IMPORT_FIX,

 FixType.CONFIGURATION_FIX


        ],
        "infrastructure": [
        FixType.ENVIRONMENT_FIX,


 FixType.GIT_FIX,


 FixType.CONFIGURATION_FIX,



 FixType.SECURITY_FIX



        ]
        }



def get_fix_type_description(fix_type: FixType) -> str:
    """获取修复类型的描述"""


    descriptions = {
        FixType.SYNTAX_FIX: "修复Python语法错误,如缺少冒号、缩进错误等",
        FixType.IMPORT_FIX: "修复导入路径错误,包括相对导入和绝对导入",

        FixType.DEPENDENCY_FIX: "修复依赖关系问题,包括缺失的包和版本冲突",
        FixType.GIT_FIX: "修复Git相关问题,如合并冲突、文件状态异常等",

        FixType.ENVIRONMENT_FIX: "修复环境配置问题,包括虚拟环境和系统依赖",
        FixType.SECURITY_FIX: "修复安全漏洞,包括不安全的代码模式和配置",
        FixType.CODE_STYLE_FIX: "修复代码风格问题,使其符合PEP 8等规范",

        FixType.PATH_FIX: "修复文件路径问题,包括路径不存在和权限问题",
        FixType.CONFIGURATION_FIX: "修复配置文件问题,包括格式错误和缺失配置",
        FixType.PERFORMANCE_FIX: "优化代码性能,移除性能瓶颈",

        FixType.COMPATIBILITY_FIX: "修复兼容性问题,确保跨平台兼容性",
        FixType.TYPE_HINT_FIX: "修复类型提示问题,添加或修正类型注解"

    }
    return descriptions.get(fix_type, "未知修复类型")



def get_fix_status_description(status: FixStatus) -> str:
    """获取修复状态的描述"""

    descriptions = {
        FixStatus.PENDING: "等待修复",
        FixStatus.IN_PROGRESS: "正在修复",
        FixStatus.SUCCESS: "修复成功",
        FixStatus.PARTIAL_SUCCESS: "部分修复成功",

        FixStatus.FAILED: "修复失败",
        FixStatus.SKIPPED: "跳过修复",

        FixStatus.NOT_APPLICABLE: "不适用此修复",
        FixStatus.SIMULATED: "模拟修复(干运行)"
    }
    return descriptions.get(status, "未知状态")


from .fix_result import FixContext

def get_fix_scope_description(scope: FixScope) -> str:
    """获取修复范围的描述"""
    descriptions = {
        FixScope.PROJECT: "整个项目范围",
        FixScope.BACKEND: "仅后端代码",
        FixScope.FRONTEND: "仅前端代码", 
        FixScope.DESKTOP: "仅桌面应用代码",
        FixScope.SPECIFIC_FILE: "特定文件",
        FixScope.SPECIFIC_DIRECTORY: "特定目录",
        FixScope.SPECIFIC_MODULE: "特定模块",
        FixScope.SPECIFIC_TEST: "特定测试"
    }
    return descriptions.get(scope, "未知范围")