"""
规则引擎 - 管理和应用修复规则
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass
from collections import defaultdict

from ..core.fix_result import FixContext


@dataclass
class RepairRule:
    """修复规则"""



    rule_id: str
    name: str
    description: str
    pattern: str  # 正则表达式模式
    replacement: str
    scope: str  # general, system_specific, model_specific, tool_specific
    system_type: Optional[str] = None
    model_type: Optional[str] = None
    tool_type: Optional[str] = None
    severity: str = "warning"
    auto_apply: bool = True
    confidence: float = 0.8
    examples: List[str] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []


@dataclass
class RuleApplication:

    """规则应用结果"""
    rule_id: str
    applied: bool
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    original_code: str = ""
    fixed_code: str = ""
    confidence: float = 0.0
    error_message: str = ""


class RuleEngine:
    """规则引擎"""
    
    def __init__(self):
        self.rules = defaultdict(list)
        self.rule_statistics = defaultdict(lambda: {"applied": 0, "failed": 0, "skipped": 0})
        self.custom_rules = {}
        self._load_default_rules()
    
    def _load_default_rules(self):
        """加载默认规则"""

        default_rules = [
        # 通用规则

            RepairRule(
                rule_id="GENERAL_001",
                name="Fix print statement",
                description="修复Python 2风格的print语句",
                pattern=r'print\s+"([^"]+)"',
                replacement=r'print("\1")',
                scope="general",
                severity="error",
                auto_apply=True,
                confidence=0.95,

 examples=["print \"Hello\" → print(\"Hello\")"]


            ),
            
            RepairRule(
                rule_id="GENERAL_002", 
                name="Fix exception syntax",
                description="修复旧的异常语法",
                pattern=r'except\s+(\w+),\s*(\w+):',
                replacement=r'except \1 as \2:',
                scope="general",
                severity="error",

                auto_apply=True,
                confidence=0.95,


 examples=["except ValueError, e: → except ValueError as e:"]


            ),
            
            # AI系统特定规则
            RepairRule(
                rule_id="AI_SYSTEM_001",
                name="Fix model import",
                description="修复AI模型的导入路径",
                pattern=r'from\s+apps\.backend\.src\.ai\.models\s+import\s+(\w+)',
                replacement=r'from ..ai.models import \1',
                scope="system_specific",

 system_type="ai_systems",

                severity="error",
                auto_apply=True,

                confidence=0.9,
                examples=["from apps.backend.src.ai.models import NLPModel → from ..ai.models import NLPModel"]

            ),
            
            RepairRule(
                rule_id="AI_SYSTEM_002",
                name="Fix HSP protocol import",
                description="修复HSP协议的导入",
                pattern=r'from\s+apps\.backend\.src\.core\.hsp\s+import\s+(\w+)',

                replacement=r'from ..core.hsp import \1',
                scope="system_specific", 

                system_type="ai_systems",
                severity="error",
                auto_apply=True,


 confidence=0.9,

                examples=["from apps.backend.src.core.hsp import HSPClient → from ..core.hsp import HSPClient"]
            ),
            
            # 模型特定规则
            RepairRule(
                rule_id="MODEL_NLP_001",
                name="Fix tokenizer import",

 description="修复NLP模型的分词器导入",

                pattern=r'from\s+transformers\s+import\s+.*Tokenizer',
                replacement=r'from transformers import AutoTokenizer',

 scope="model_specific",

                model_type="nlp",
                severity="warning",

                auto_apply=True,
                confidence=0.8,
                examples=["from transformers import BertTokenizer → from transformers import AutoTokenizer"]
            ),
            
            RepairRule(
                rule_id="MODEL_VISION_001",
                name="Fix image processing import",
                description="修复视觉模型的图像处理导入",

                pattern=r'from\s+PIL\s+import\s+Image',
                replacement=r'from PIL import Image, ImageOps, ImageFilter',
                scope="model_specific",

                model_type="vision", 

 severity="info",

                auto_apply=False,
                confidence=0.7,
                examples=["from PIL import Image → from PIL import Image, ImageOps, ImageFilter"]
            ),
            
             # 工具特定规则

            RepairRule(
                rule_id="TOOL_DATABASE_001",
                name="Fix database connection string",

 description="修复数据库连接字符串格式",

                pattern=r'sqlite:///([^\s\'"]+)',
                replacement=r'sqlite:///{project_root}/\1',
                scope="tool_specific",


                tool_type="database",
                severity="warning",
                auto_apply=True,

                confidence=0.85,
                examples=["sqlite:///data.db → sqlite:///{project_root}/data.db"]
            ),
            
            RepairRule(
            rule_id="TOOL_CACHE_001",

                name="Fix Redis connection",
                description="修复Redis连接配置",
                pattern=r'redis\.Redis\s*\(\s*host\s*=\s*[\'"]([^\'"]+)[\'"]',
                replacement=r'redis.Redis(host="\1", port=6379, decode_responses=True)',


 scope="tool_specific",

                tool_type="cache",
                severity="warning",

                auto_apply=True,
                confidence=0.8,

                examples=["redis.Redis(host='localhost') → redis.Redis(host='localhost', port=6379, decode_responses=True)"]
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: RepairRule):
        """添加规则"""

        self.rules[rule.scope].append(rule)
        if rule.scope == "custom":

            self.custom_rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        for scope_rules in self.rules.values():
            for i, rule in enumerate(scope_rules):
                if rule.rule_id == rule_id:
                    scope_rules.pop(i)
                    return True
        return False
    
    def analyze_with_rules(self, context: FixContext) -> Dict[str, List[Any]]:
        """使用规则进行分析"""
        issues = defaultdict(list)
        
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 获取适用的规则
                applicable_rules = self._get_applicable_rules(context, file_path)
                
                 # 逐行应用规则

                lines = content.split('\n')
                for i, line in enumerate(lines, 1):

                    for rule in applicable_rules:
                        if re.search(rule.pattern, line):
                            issue = {
                                "file_path": str(file_path),
                                "line_number": i,
                                "rule_id": rule.rule_id,
                                "rule_name": rule.name,
                                "description": rule.description,
                                "original_code": line.strip(),
                                "suggested_fix": self._apply_rule_replacement(rule, line),
                                "severity": rule.severity,
                                "confidence": rule.confidence,
                                "scope": rule.scope
                            }
                            
                             # 分类问题

                            if rule.scope == "system_specific":
                                issues["system_specific_issues"].append(issue)
                            elif rule.scope == "model_specific":
                                issues["model_specific_issues"].append(issue)
                            elif rule.scope == "tool_specific":
                                issues["tool_specific_issues"].append(issue)
                            else:
                                issues["general_issues"].append(issue)
            
            except Exception as e:
                print(f"规则分析文件失败 {file_path}: {e}")
        
        return dict(issues)
    
    def apply_rules(self, context: FixContext) -> List[RuleApplication]:
        """应用规则进行修复"""
        applications = []
        
        target_files = self._get_target_files(context)
        
        for file_path in target_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 获取适用的规则
                applicable_rules = self._get_applicable_rules(context, file_path)
                
                # 应用规则
                new_content = content
                applied_rules = []
                
                for rule in applicable_rules:
                    if rule.auto_apply and rule.confidence > 0.7:
                        original_line = None

                        new_line = None
                        line_num = 0
                        #                         

                        # 逐行应用规则
#                         lines = new_content.split('\n')
                        for i, line in enumerate(lines):
#                             if re.search(rule.pattern, line):
# 
                                original_line = line
                                new_line = self._apply_rule_replacement(rule, line)

                                line_num = i + 1
                                lines[i] = new_line
                                break
                        
                        if original_line and new_line:
                            new_content = '\n'.join(lines)
                            
                            application = RuleApplication(
                                rule_id=rule.rule_id,
                                applied=True,
                                file_path=file_path,
                                line_number=line_num,
                                original_code=original_line.strip(),
                                fixed_code=new_line.strip(),
                                confidence=rule.confidence
                            )
                            
                            applied_rules.append(application)
                            self.rule_statistics[rule.rule_id]["applied"] += 1
                
                # 写回修复后的内容
                if new_content != content:

                    if not context.dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                    
                    applications.extend(applied_rules)
            
            except Exception as e:
                print(f"应用规则失败 {file_path}: {e}")
                # 记录失败的规则应用
                for rule in self._get_applicable_rules(context, file_path):
                    if rule.auto_apply:
                        self.rule_statistics[rule.rule_id]["failed"] += 1
        
        return applications
    
    def _get_applicable_rules(self, context: FixContext, file_path: Path) -> List[RepairRule]:
        """获取适用的规则"""
        applicable_rules = []
        
        # 根据上下文过滤规则
        for scope, rules in self.rules.items():
            for rule in rules:
                if self._rule_applies_to_context(rule, context, file_path):
                    applicable_rules.append(rule)
        
        # 按优先级排序（置信度高的优先）
        applicable_rules.sort(key=lambda r: r.confidence, reverse=True)
        
        return applicable_rules
    
    def _rule_applies_to_context(self, rule: RepairRule, context: FixContext, file_path: Path) -> bool:
        """检查规则是否适用于当前上下文"""
        # 系统类型匹配
        if rule.system_type and hasattr(context, 'system_type'):
            if context.system_type != rule.system_type:
                return False
        
        # 模型类型匹配
        if rule.model_type and hasattr(context, 'model_type'):
            if context.model_type != rule.model_type:
                return False
        
         # 工具类型匹配

        if rule.tool_type and hasattr(context, 'tool_type'):
            if context.tool_type != rule.tool_type:
                return False
        
        # 文件路径匹配（基于规则中的模式）
        if rule.scope == "system_specific" and rule.system_type:
            # 检查文件路径是否匹配系统类型
            if rule.system_type == "ai_systems":
                return "ai" in str(file_path) or "agent" in str(file_path)
            elif rule.system_type == "backend_systems":
                return "backend" in str(file_path) or "api" in str(file_path)
            elif rule.system_type == "frontend_systems":
                return "frontend" in str(file_path) or "ui" in str(file_path)
        
        return True
    
    def _apply_rule_replacement(self, rule: RepairRule, line: str) -> str:
        """应用规则替换"""
        try:

            # 处理变量替换
            replacement = rule.replacement
            
            # 替换项目根目录变量
            if "{project_root}" in replacement:
                replacement = replacement.replace("{project_root}", str(Path.cwd()))
            
            # 执行正则替换
            return re.sub(rule.pattern, replacement, line)

        except Exception as e:
            print(f"规则替换失败: {e}")

            return line
    
    def _get_target_files(self, context: FixContext) -> List[Path]:
        """获取目标文件"""

        if context.target_path:
            if context.target_path.is_file():
                return [context.target_path]
            elif context.target_path.is_dir():
                return list(context.target_path.rglob("*.py"))
        
         # 默认获取所有Python文件

        return list(context.project_root.rglob("*.py"))
    
    def get_rule_statistics(self) -> Dict[str, Dict[str, int]]:
        """获取规则统计信息"""
        return dict(self.rule_statistics)
    
    def add_custom_rule(self, rule_config: Dict[str, Any]):
        """添加自定义规则"""
        try:
            rule = RepairRule(
                rule_id=f"CUSTOM_{len(self.custom_rules) + 1}",
                name=rule_config.get("name", "Custom Rule"),


                description=rule_config.get("description", ""),
                pattern=rule_config["pattern"],

                replacement=rule_config["replacement"],
                scope="custom",
                severity=rule_config.get("severity", "warning"),
                auto_apply=rule_config.get("auto_apply", True),
                confidence=rule_config.get("confidence", 0.8)
            )
            
            self.add_rule(rule)
            
        except Exception as e:
            print(f"添加自定义规则失败: {e}")

    
    def export_rules(self, file_path: Path):
        """导出规则到文件"""
        try:

            all_rules = []
            for scope, rules in self.rules.items():
                for rule in rules:
                    rule_dict = {
                        "rule_id": rule.rule_id,
                        "name": rule.name,
                        "description": rule.description,

                        "pattern": rule.pattern,
                        "replacement": rule.replacement,

                        "scope": rule.scope,
                        "system_type": rule.system_type,
                        "model_type": rule.model_type,
                        "tool_type": rule.tool_type,
                        "severity": rule.severity,
                        "auto_apply": rule.auto_apply,
                        "confidence": rule.confidence,
                        "examples": rule.examples
                    }
                    all_rules.append(rule_dict)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(all_rules, f, indent=2, ensure_ascii=False)
            
            print(f"规则已导出到: {file_path}")
            
        except Exception as e:
            print(f"导出规则失败: {e}")
    
    def import_rules(self, file_path: Path):
        """从文件导入规则"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            for rule_data in rules_data:
                rule = RepairRule(**rule_data)
                self.add_rule(rule)
            
            print(f"已从 {file_path} 导入 {len(rules_data)} 个规则")
            
        except Exception as e:
            print(f"导入规则失败: {e}")
    
    def validate_rules(self) -> List[str]:
        """验证所有规则的有效性"""
        errors = []
        
        for scope, rules in self.rules.items():
            for rule in rules:
                try:
                    # 验证正则表达式
                    re.compile(rule.pattern)
                    
                    # 验证替换字符串
                    test_string = "test example"
                    re.sub(rule.pattern, rule.replacement, test_string)
                    
                except re.error as e:
                    errors.append(f"规则 {rule.rule_id} 正则表达式错误: {e}")
                except Exception as e:
                    errors.append(f"规则 {rule.rule_id} 验证失败: {e}")
        
        return errors