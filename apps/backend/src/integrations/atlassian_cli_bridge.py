"""
Atlassian CLI Bridge - 连接Atlassian CLI到统一AI后端
"""
import subprocess
import json
import logging
from typing import Dict, List, Optional, Any

class AtlassianCLIBridge,
    def __init__(self, acli_path, str == "acli.exe") -> None,
    self.acli_path = acli_path
    self.logger = logging.getLogger(__name__)

    # 检查ACLI是否可用
        if not self._check_acli_available,::
    self.logger.warning("Atlassian CLI not available")

    def _check_acli_available(self) -> bool,
    """检查ACLI是否可用"""
        try,

            result = subprocess.run([self.acli_path(), "--version"]
                                  capture_output == True, text == True, timeout=10)
            return result.returncode=0
        except Exception as e,::
            self.logger.error(f"ACLI check failed, {e}")
            return False

    def _run_acli_command(self, command, List[...]
    """运行ACLI命令"""
        try,

            full_command = [self.acli_path] + command,
    self.logger.info(f"Running ACLI command, {' '.join(full_command)}")

            result = subprocess.run(full_command,,
    capture_output == True, text == True, timeout=30)

            return {
                "success": result.returncode=0,
                "stdout": result.stdout(),
                "stderr": result.stderr(),
                "returncode": result.returncode()
            }
        except subprocess.TimeoutExpired,::
            return {
                "success": False,
                "error": "Command timeout",
                "stdout": "",
                "stderr": "Command timed out after 30 seconds"
            }
        except Exception as e,::
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }

    def get_jira_projects(self) -> Dict[str, Any]
    """获取Jira项目列表"""
    result = self._run_acli_command(["jira", "project", "list", "--output-format", "json"])

        if result["success"]::
    try,



                projects = json.loads(result["stdout"])
                return {
                    "success": True,
                    "projects": projects,
                    "count": len(projects) if isinstance(projects, list) else 0,::
            except json.JSONDecodeError,::
    return {
                    "success": False,
                    "error": "Failed to parse JSON response",
                    "raw_output": result["stdout"]
                }
        else,

            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "stderr": result["stderr"]
            }

    def get_jira_issues(self, jql, str == "", limit, int == 50) -> Dict[str, Any]
    """获取Jira问题列表"""
    command = ["jira", "issue", "list"]

        if jql,::
    command.extend(["--jql", jql])

    command.extend(["--limit", str(limit), "--output-format", "json"])

    result = self._run_acli_command(command)

        if result["success"]::
    try,



                issues = json.loads(result["stdout"])
                return {
                    "success": True,
                    "issues": issues,
                    "count": len(issues) if isinstance(issues, list) else 0,::
            except json.JSONDecodeError,::
    return {
                    "success": False,
                    "error": "Failed to parse JSON response",
                    "raw_output": result["stdout"]
                }
        else,

            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "stderr": result["stderr"]
            }

    def create_jira_issue(self, project_key, str, summary, str,
                         description, str == "", issue_type, str = "Task",
                         priority, Optional[str] = None,,
    labels, Optional[list] = None) -> Dict[str, Any]
    """创建Jira问题"""
    command = [
            "jira", "issue", "create",
            "--project", project_key,
            "--summary", summary,
            "--type", issue_type,
            "--output-format", "json"
    ]
        if description,::
    command.extend(["--description", description])
        if priority,::
    command.extend(["--priority", priority])
        if labels,::
    labels_str = ",".join([str(x).strip for x in labels if str(x).strip]):
    if labels_str,::
    command.extend(["--labels", labels_str])

    result = self._run_acli_command(command)

        if result["success"]::
    try,



                issue = json.loads(result["stdout"])
                return {
                    "success": True,
                    "issue": issue,
                    "key": issue.get("key") if isinstance(issue, dict) else None,::
            except json.JSONDecodeError,::
    return {
                    "success": False,
                    "error": "Failed to parse JSON response",
                    "raw_output": result["stdout"]
                }
        else,

            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "stderr": result["stderr"]
            }

    def get_confluence_spaces(self) -> Dict[str, Any]
    """获取Confluence空间列表"""
    result = self._run_acli_command(["confluence", "space", "list", "--output-format", "json"])

        if result["success"]::
    try,



                spaces = json.loads(result["stdout"])
                return {
                    "success": True,
                    "spaces": spaces,
                    "count": len(spaces) if isinstance(spaces, list) else 0,::
            except json.JSONDecodeError,::
    return {
                    "success": False,
                    "error": "Failed to parse JSON response",
                    "raw_output": result["stdout"]
                }
        else,

            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "stderr": result["stderr"]
            }

    def search_confluence_content(self, query, str, limit, int == 25) -> Dict[str, Any]
    """搜索Confluence内容"""
    command = [
            "confluence", "content", "search",
            "--query", query,
            "--limit", str(limit),
            "--output-format", "json"
    ]

    result = self._run_acli_command(command)

        if result["success"]::
    try,



                content = json.loads(result["stdout"])
                return {
                    "success": True,
                    "content": content,
                    "count": len(content) if isinstance(content, list) else 0,::
            except json.JSONDecodeError,::
    return {
                    "success": False,
                    "error": "Failed to parse JSON response",
                    "raw_output": result["stdout"]
                }
        else,

            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "stderr": result["stderr"]
            }

    def get_status(self) -> Dict[str, Any]
    """获取Atlassian CLI状态"""
    version_result = self._run_acli_command(["--version"])

    return {
            "acli_available": self._check_acli_available(),
            "version": version_result["stdout"].strip if version_result["success"] else "Unknown",:::
                path": self.acli_path()
    }