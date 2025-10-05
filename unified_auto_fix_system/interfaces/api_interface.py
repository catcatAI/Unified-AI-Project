"""
API接口
为外部系统提供RESTful API接口
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict
from datetime import datetime

from ..core.unified_fix_engine import UnifiedFixEngine
from ..core.fix_types import FixType, FixScope, FixPriority
from ..core.fix_result import FixContext, FixReport


class APIFixInterface:
    """API修复接口"""
    
    def __init__(self, project_root: Path, config_path: Optional[Path] = None):
        self.project_root = Path(project_root).resolve()
        self.config_path = config_path
        
        # 初始化统一修复引擎
        self.fix_engine = UnifiedFixEngine(self.project_root, config_path)
        
        # 设置API专用日志
        self.logger = logging.getLogger(f"{__name__}.APIFixInterface")
        
        # API统计
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "request_types": {}
        }
    
    def handle_request(self, method: str, path: str, 
                      query_params: Optional[Dict[str, Any]] = None,
                      body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理API请求"""
        self.api_stats["total_requests"] += 1
        
        try:
            self.logger.info(f"处理API请求: {method} {path}")
            
            # 路由分发
            if method == "GET":
                response = self._handle_get_request(path, query_params)
            elif method == "POST":
                response = self._handle_post_request(path, body)
            elif method == "PUT":
                response = self._handle_put_request(path, body)
            elif method == "DELETE":
                response = self._handle_delete_request(path)
            else:
                response = self._error_response(405, "Method not allowed")
            
            self.api_stats["successful_requests"] += 1
            self._update_request_stats(path)
            
            return response
        
        except Exception as e:
            self.api_stats["failed_requests"] += 1
            self.logger.error(f"API请求处理失败: {e}")
            return self._error_response(500, str(e))
    
    def _handle_get_request(self, path: str, 
                           query_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """处理GET请求"""
        path_parts = path.strip("/").split("/")
        
        if path_parts[0] == "status":
            return self._get_status()
        elif path_parts[0] == "health":
            return self._get_health()
        elif path_parts[0] == "config":
            return self._get_config()
        elif path_parts[0] == "analysis" and len(path_parts) > 1:
            return self._get_analysis_result(path_parts[1])
        elif path_parts[0] == "reports":
            return self._list_reports()
        elif path_parts[0] == "reports" and len(path_parts) > 1:
            return self._get_report(path_parts[1])
        elif path_parts[0] == "modules":
            return self._get_modules()
        elif path_parts[0] == "statistics":
            return self._get_statistics()
        else:
            return self._error_response(404, "Endpoint not found")
    
    def _handle_post_request(self, path: str, 
                            body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """处理POST请求"""
        if not body:
            return self._error_response(400, "Request body is required")
        
        path_parts = path.strip("/").split("/")
        
        if path_parts[0] == "analyze":
            return self._start_analysis(body)
        elif path_parts[0] == "fix":
            return self._start_fix(body)
        elif path_parts[0] == "config":
            return self._update_config(body)
        else:
            return self._error_response(404, "Endpoint not found")
    
    def _handle_put_request(self, path: str, 
                           body: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """处理PUT请求"""
        return self._error_response(405, "PUT method not supported for this endpoint")
    
    def _handle_delete_request(self, path: str) -> Dict[str, Any]:
        """处理DELETE请求"""
        return self._error_response(405, "DELETE method not supported for this endpoint")
    
    def _get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        module_status = self.fix_engine.get_module_status()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.fix_engine.project_root),
            "engine_status": {
                "modules_enabled": len([m for m in module_status.values() if m == "enabled"]),
                "total_fixes": self.fix_engine.stats["total_fixes"],
                "successful_fixes": self.fix_engine.stats["successful_fixes"],
                "failed_fixes": self.fix_engine.stats["failed_fixes"]
            },
            "api_stats": self.api_stats
        }
    
    def _get_health(self) -> Dict[str, Any]:
        """获取健康检查"""
        try:
            # 快速状态检查
            module_status = self.fix_engine.get_module_status()
            
            # 计算健康度
            enabled_modules = sum(1 for status in module_status.values() if status == "enabled")
            total_modules = len(module_status)
            
            health_score = (enabled_modules / total_modules) * 100 if total_modules > 0 else 0
            
            return {
                "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "unhealthy",
                "health_score": health_score,
                "checks": {
                    "engine": "ok" if self.fix_engine else "failed",
                    "modules": "ok" if enabled_modules > 0 else "failed"
                },
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "health_score": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return {
            "config": self.fix_engine.config,
            "available_modules": [ft.value for ft in FixType],
            "available_scopes": [fs.value for fs in FixScope],
            "available_priorities": [fp.value for fp in FixPriority]
        }
    
    def _update_config(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """更新配置"""
        try:
            if "config" not in body:
                return self._error_response(400, "Missing 'config' in request body")
            
            new_config = body["config"]
            
            # 验证配置
            self._validate_config(new_config)
            
            # 更新配置
            self.fix_engine.config.update(new_config)
            self.fix_engine.save_config()
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "config": self.fix_engine.config
            }
        
        except ValueError as e:
            return self._error_response(400, str(e))
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _validate_config(self, config: Dict[str, Any]):
        """验证配置"""
        # 验证修复类型
        if "enabled_modules" in config:
            for module in config["enabled_modules"]:
                if module not in [ft.value for ft in FixType]:
                    raise ValueError(f"Invalid fix type: {module}")
        
        # 验证布尔值
        bool_fields = ["backup_enabled", "dry_run", "ai_assisted", "parallel_fixing"]
        for field in bool_fields:
            if field in config and not isinstance(config[field], bool):
                raise ValueError(f"Field '{field}' must be a boolean")
        
        # 验证整数
        int_fields = ["max_fix_attempts"]
        for field in int_fields:
            if field in config and not isinstance(config[field], int):
                raise ValueError(f"Field '{field}' must be an integer")
    
    def _start_analysis(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """开始分析"""
        try:
            # 创建上下文
            context = self._create_context_from_body(body)
            
            # 执行分析
            result = self.fix_engine.analyze_project(context)
            
            # 生成分析ID
            analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return {
                "success": True,
                "message": "Analysis started successfully",
                "analysis_id": analysis_id,
                "result": result
            }
        
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _start_fix(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """开始修复"""
        try:
            # 创建上下文
            context = self._create_context_from_body(body)
            
            # 解析修复类型
            fix_types = body.get("fix_types")
            
            # 执行修复
            report = self.fix_engine.fix_issues(context, fix_types)
            
            # 生成修复ID
            fix_id = f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return {
                "success": True,
                "message": "Fix started successfully",
                "fix_id": fix_id,
                "report": asdict(report)
            }
        
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _create_context_from_body(self, body: Dict[str, Any]) -> FixContext:
        """从请求体创建修复上下文"""
        # 解析目标路径
        target_path = None
        if "target_path" in body:
            target_path = Path(body["target_path"])
            if not target_path.is_absolute():
                target_path = self.project_root / target_path
        
        # 解析范围
        scope = FixScope(body.get("scope", "project"))
        
        # 解析优先级
        priority = FixPriority(body.get("priority", "normal"))
        
        # 解析修复类型
        fix_types = None
        if "fix_types" in body:
            fix_types = []
            for ft_str in body["fix_types"]:
                try:
                    fix_type = FixType(ft_str)
                    fix_types.append(fix_type)
                except ValueError:
                    self.logger.warning(f"Unknown fix type: {ft_str}")
        
        # 创建上下文
        context = FixContext(
            project_root=self.project_root,
            target_path=target_path,
            scope=scope,
            priority=priority,
            backup_enabled=body.get("backup_enabled", True),
            dry_run=body.get("dry_run", False),
            ai_assisted=body.get("ai_assisted", False),
            custom_rules=body.get("custom_rules", {})
        )
        
        return context
    
    def _get_modules(self) -> Dict[str, Any]:
        """获取模块信息"""
        module_status = self.fix_engine.get_module_status()
        
        modules_info = {}
        for fix_type in FixType:
            modules_info[fix_type.value] = {
                "status": module_status.get(fix_type.value, "disabled"),
                "description": self._get_module_description(fix_type)
            }
        
        return {
            "modules": modules_info,
            "total_enabled": len([m for m in module_status.values() if m == "enabled"])
        }
    
    def _get_module_description(self, fix_type: FixType) -> str:
        """获取模块描述"""
        descriptions = {
            FixType.SYNTAX_FIX: "Fix Python syntax errors",
            FixType.IMPORT_FIX: "Fix import path issues",
            FixType.DEPENDENCY_FIX: "Fix dependency problems",
            FixType.GIT_FIX: "Fix Git-related issues",
            FixType.ENVIRONMENT_FIX: "Fix environment configuration issues",
            FixType.SECURITY_FIX: "Fix security vulnerabilities",
            FixType.CODE_STYLE_FIX: "Fix code style issues",
            FixType.PATH_FIX: "Fix file path issues",
            FixType.CONFIGURATION_FIX: "Fix configuration file issues",
            FixType.PERFORMANCE_FIX: "Optimize code performance",
            FixType.COMPATIBILITY_FIX: "Fix compatibility issues",
            FixType.TYPE_HINT_FIX: "Fix type hint issues"
        }
        
        return descriptions.get(fix_type, "Unknown module")
    
    def _get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "engine_statistics": self.fix_engine.stats,
            "api_statistics": self.api_stats,
            "project_info": {
                "root_path": str(self.fix_engine.project_root),
                "config_path": str(self.fix_engine.config_path)
            }
        }
    
    def _list_reports(self) -> Dict[str, Any]:
        """列出修复报告"""
        reports_dir = self.project_root / "unified_fix_reports"
        
        if not reports_dir.exists():
            return {
                "reports": [],
                "total": 0
            }
        
        try:
            report_files = []
            for report_file in reports_dir.glob("fix_report_*.json"):
                stat = report_file.stat()
                report_files.append({
                    "filename": report_file.name,
                    "path": str(report_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # 按修改时间排序
            report_files.sort(key=lambda x: x["modified"], reverse=True)
            
            return {
                "reports": report_files,
                "total": len(report_files)
            }
        
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _get_report(self, report_id: str) -> Dict[str, Any]:
        """获取修复报告"""
        reports_dir = self.project_root / "unified_fix_reports"
        report_file = reports_dir / report_id
        
        if not report_file.exists():
            return self._error_response(404, "Report not found")
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            return {
                "success": True,
                "report": report_data
            }
        
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _get_analysis_result(self, analysis_id: str) -> Dict[str, Any]:
        """获取分析结果"""
        # 这里可以实现分析结果的缓存和检索
        # 简化版本：返回最新分析结果
        try:
            context = FixContext(project_root=self.project_root)
            result = self.fix_engine.analyze_project(context)
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "result": result
            }
        
        except Exception as e:
            return self._error_response(500, str(e))
    
    def _update_request_stats(self, path: str):
        """更新请求统计"""
        endpoint = path.strip("/").split("/")[0]
        
        if endpoint not in self.api_stats["request_types"]:
            self.api_stats["request_types"][endpoint] = 0
        
        self.api_stats["request_types"][endpoint] += 1
    
    def _error_response(self, status_code: int, message: str) -> Dict[str, Any]:
        """错误响应"""
        return {
            "success": False,
            "error": {
                "code": status_code,
                "message": message
            },
            "timestamp": datetime.now().isoformat()
        }