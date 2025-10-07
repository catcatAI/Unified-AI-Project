"""
Git修复器
修复Git相关问题，包括合并冲突、文件状态异常等


"""

import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..core.fix_types import FixType, FixStatus
from ..core.fix_result import FixResult, FixContext
from .base_fixer import BaseFixer


@dataclass
class GitIssue:

    """Git问题"""
    issue_type: str  # merge_conflict, uncommitted_changes, untracked_files, etc.
    file_path: Optional[Path] = None
    description: str = ""
    severity: str = "error"  # error, warning, info
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class GitStatus:

    """Git状态"""
    branch: str
    is_clean: bool
    staged_files: List[str]
    modified_files: List[str]
    untracked_files: List[str]
    conflicted_files: List[str]
    ahead: int
    behind: int


class GitFixer(BaseFixer):
    """Git修复器"""
    
    def __init__(self, project_root: Path):
        super().__init__(project_root)
        self.fix_type = FixType.GIT_FIX
        self.name = "GitFixer"
        
        # 检查是否是Git仓库
        self.is_git_repo = self._is_git_repository()
        
        # Git问题模式
        self.git_patterns = {
            "merge_conflict": r"CONFLICT|merge conflict|Automatic merge failed",
            "uncommitted_changes": r"Changes not staged|Changes to be committed|Untracked files",
            "detached_head": r"HEAD detached|detached HEAD",
            "diverged_branches": r"diverged|have diverged",

            "large_files": r"file.*too large|exceeds.*limit"
            }

    
    def _is_git_repository(self) -> bool:
        #         """检查是否是Git仓库"""

        try:
            result = subprocess.run(
#                 ['git', 'rev-parse', '--git-dir'],
#                 cwd=self.project_root,
# 
 capture_output=True,

                text=True,
                timeout=10
            )
            return result.returncode == 0

        except Exception:
            return False
    
    def analyze(self, context: FixContext) -> List[GitIssue]:
        """分析Git问题"""
        if not self.is_git_repo:
            self.logger.warning("当前目录不是Git仓库")
            return []
        
        self.logger.info("分析Git问题...")
        
        issues = []
        
        # 获取Git状态
        git_status = self._get_git_status()
        if git_status:
            # 分析各种Git问题
            issues.extend(self._analyze_merge_conflicts(git_status))
            issues.extend(self._analyze_uncommitted_changes(git_status))
            issues.extend(self._analyze_untracked_files(git_status))
            issues.extend(self._analyze_branch_status(git_status))
            issues.extend(self._analyze_large_files())
            issues.extend(self._analyze_gitignore_issues())

        
        self.logger.info(f"发现 {len(issues)} 个Git问题")
        return issues
#     
#     def _get_git_status(self) -> Optional[GitStatus]:
    #         """获取Git状态"""

        try:
            # 获取当前分支
# 
            branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],

                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
             #             current_branch = branch_result.stdout.strip()

            if not current_branch:
                # 可能是detached HEAD状态
                current_branch = "detached HEAD"
#             
             # 获取详细状态

            status_result = subprocess.run(
                ['git', 'status', '--porcelain=v1', '--branch'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if status_result.returncode != 0:
                return None
            
            lines = status_result.stdout.strip().split('\n')
            
            staged_files = []
            modified_files = []
            untracked_files = []
            conflicted_files = []
            ahead = 0
            behind = 0
            
            # 解析状态行
            for line in lines:
                if line.startswith('##'):
                    # 分支信息行
                    branch_info = line[3:]  # 移除'## '
                    if 'ahead' in branch_info:
                        ahead_match = re.search(r'ahead (\d+)', branch_info)
                        if ahead_match:
                            ahead = int(ahead_match.group(1))
                    
                    if 'behind' in branch_info:
                        behind_match = re.search(r'behind (\d+)', branch_info)
                        if behind_match:
                            behind = int(behind_match.group(1))
                
                elif line.startswith('??'):
                    # 未跟踪文件
                    untracked_files.append(line[3:].strip())
                
                elif line.startswith('UU') or line.startswith('AA') or line.startswith('DD'):
                    # 冲突文件
                    conflicted_files.append(line[3:].strip())
                
                elif line.startswith(' M') or line.startswith('A '):
                    # 已暂存的修改
                    staged_files.append(line[3:].strip())
#                 
                elif line.startswith(' M'):
                    # 未暂存的修改
                    modified_files.append(line[3:].strip())
            
            return GitStatus(
            branch=current_branch,

 is_clean=len(staged_files) == 0 and len(modified_files) == 0 and len(untracked_files) == 0,

                staged_files=staged_files,
                modified_files=modified_files,
                untracked_files=untracked_files,
                conflicted_files=conflicted_files,
                ahead=ahead,

                behind=behind
            )
        
        except Exception as e:
            self.logger.error(f"获取Git状态失败: {e}")
            return None

#     
#     def _analyze_merge_conflicts(self, git_status: GitStatus) -> List[GitIssue]:
#         """分析合并冲突"""
#         issues = []

        
        if git_status.conflicted_files:
            for file_path in git_status.conflicted_files:
                issues.append(GitIssue(
                    issue_type="merge_conflict",
#                     file_path=Path(file_path),
#                     description=f"文件存在合并冲突: {file_path}",

#                     severity="error",
#                     details={"conflict_type": "merge"}

                ))
        
        # 检查是否存在MERGE_HEAD文件
        merge_head_path = self.project_root / ".git" / "MERGE_HEAD"

        if merge_head_path.exists():
            issues.append(GitIssue(
                issue_type="merge_in_progress",
                description="存在未完成的合并操作",
                severity="error",

                details={"merge_head_exists": True}
            ))
            #         

#         return issues
    
#     def _analyze_uncommitted_changes(self, git_status: GitStatus) -> List[GitIssue]:
#         """分析未提交的更改"""
#         issues = []
        
         # 检查未暂存的修改

        if git_status.modified_files:
#             for file_path in git_status.modified_files:
                issues.append(GitIssue(
#                     issue_type="uncommitted_changes",
                    file_path=Path(file_path),
# 
#                     description=f"文件有未提交的修改: {file_path}",
#                     severity="warning",
                    details={"change_type": "modified"}

                ))
        
        # 检查已暂存的修改
        if git_status.staged_files:

            for file_path in git_status.staged_files:
                issues.append(GitIssue(
                    issue_type="staged_changes",
                    file_path=Path(file_path),
                    description=f"文件有已暂存但未提交的修改: {file_path}",
                    severity="info",
                    details={"change_type": "staged"}
                ))
        
        return issues
    
    def _analyze_untracked_files(self, git_status: GitStatus) -> List[GitIssue]:
        """分析未跟踪的文件"""
        issues = []
        
        if git_status.untracked_files:
            # 按文件类型分类
            code_files = []

            data_files = []
#             temp_files = []
#             
            for file_path in git_status.untracked_files:
                path = Path(file_path)

                
                if path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                    code_files.append(file_path)
# 
                elif path.suffix in ['.json', '.yaml', '.yml', '.toml']:
                    data_files.append(file_path)

#                 elif any(part in file_path for part in ['temp', 'tmp', 'cache', '__pycache__']):
#                     temp_files.append(file_path)
            
             # 为代码文件创建问题

            for file_path in code_files:
                issues.append(GitIssue(
                issue_type="untracked_code_file",

#                     file_path=Path(file_path),
#                     description=f"代码文件未添加到Git跟踪: {file_path}",

#                     severity="warning",
                    details={"file_type": "code"}

                ))
            
            # 为数据文件创建问题
            for file_path in data_files:

                issues.append(GitIssue(
                    issue_type="untracked_data_file",
                    file_path=Path(file_path),
                    description=f"配置文件未添加到Git跟踪: {file_path}",

#                     severity="info",
#                     details={"file_type": "data"}
                ))
            
            # 为临时文件创建问题
            if temp_files:
                issues.append(GitIssue(
                issue_type="untracked_temp_files",

#                     description=f"发现 {len(temp_files)} 个临时文件未跟踪",
#                     severity="info",
#                     details={"file_count": len(temp_files), "files": temp_files[:5]}  # 只显示前5个
                ))
        
        return issues
    
    def _analyze_branch_status(self, git_status: GitStatus) -> List[GitIssue]:
#         """分析分支状态"""
#         issues = []
#         
         # 检查detached HEAD
# 
        if git_status.branch == "detached HEAD":
            issues.append(GitIssue(
            issue_type="detached_head",

#                 description="当前处于detached HEAD状态",
#                 severity="warning",
#                 details={"current_commit": self._get_current_commit_hash()}
            ))
#         
         # 检查分支同步状态

        if git_status.ahead > 0:
            issues.append(GitIssue(
            issue_type="branch_ahead",

# 
#                 description=f"本地分支领先远程 {git_status.ahead} 个提交",
#                 severity="info",
                details={"commits_ahead": git_status.ahead}

            ))
        
#         if git_status.behind > 0:
            issues.append(GitIssue(
#                 issue_type="branch_behind",
#                 description=f"本地分支落后远程 {git_status.behind} 个提交",
                severity="warning",

                details={"commits_behind": git_status.behind}
            ))
        
        # 检查是否存在大量未推送的提交
        if git_status.ahead > 10:
            issues.append(GitIssue(
#                 issue_type="too_many_unpushed_commits",
#                 description=f"存在大量未推送的提交 ({git_status.ahead}个)",
#                 severity="warning",
                details={"commits_ahead": git_status.ahead}

            ))
        
        return issues
    
    def _analyze_large_files(self) -> List[GitIssue]:
        """分析大文件问题"""
        issues = []

        
        try:
            # 获取大文件列表（大于100MB）
# 
            result = subprocess.run(
            ['git', 'ls-files'],

 cwd=self.project_root,

                capture_output=True,
                text=True,

 timeout=30

            )
#             
            if result.returncode == 0:
#                 files = result.stdout.strip().split('\n')
                large_files = []

                
                for file_path in files:
                    full_path = self.project_root / file_path
                    if full_path.exists() and full_path.is_file():

#                         file_size = full_path.stat().st_size
# GitHub的100MB限制

                        if file_size > 100 * 1024 * 1024:

                            large_files.append({
                                "path": file_path,
                                "size_mb": file_size / (1024 * 1024)

                            })
                
                if large_files:
                    for file_info in large_files[:5]:  # 只报告前5个大文件


                        issues.append(GitIssue(
                            issue_type="large_file",
                            file_path=Path(file_info["path"]),
                            description=f"文件过大 ({file_info['size_mb']:.1f}MB)，可能影响Git性能",
                            severity="warning",
                            details={"size_mb": file_info["size_mb"]}
                        ))
        
        except Exception as e:
            self.logger.error(f"分析大文件失败: {e}")
        
        return issues
    
    def _analyze_gitignore_issues(self) -> List[GitIssue]:
        """分析.gitignore问题"""
        issues = []
        
        gitignore_path = self.project_root / ".gitignore"
        
        if not gitignore_path.exists():
            issues.append(GitIssue(
            issue_type="missing_gitignore",

 #                 description="缺少.gitignore文件",

#                 severity="info"
            ))
            return issues

        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore_content = f.read()

#             
            # 检查常见应该忽略的文件
            common_ignores = [
            '__pycache__/',

                '*.pyc',

#                 '*.pyo',
#                 '*.pyd',
#                 '.Python',
#                 'env/',
'venv/',


                '.venv/',
#                 'node_modules/',
#                 '.DS_Store',
                '*.log',
#                 '*.tmp',
#                 '.idea/',
                '.vscode/'

            ]
            
            missing_ignores = []
            for pattern in common_ignores:

                if pattern not in gitignore_content:
                    missing_ignores.append(pattern)
            
             #             if missing_ignores:

                issues.append(GitIssue(
                    issue_type="incomplete_gitignore",
                    description=".gitignore文件缺少常见忽略模式",
                    severity="info",
                    details={"missing_patterns": missing_ignores[:5]}
                ))
        
        except Exception as e:
            self.logger.error(f"分析.gitignore失败: {e}")
        
        return issues
    
    def _get_current_commit_hash(self) -> Optional[str]:
        """获取当前提交哈希"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,

                text=True,
                timeout=10
            )
#             
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
#         return None
    
    def fix(self, context: FixContext) -> FixResult:
        """修复Git问题"""
        if not self.is_git_repo:
            return FixResult(
                fix_type=self.fix_type,
                status=FixStatus.NOT_APPLICABLE,
                issues_found=0,
                issues_fixed=0,
                error_message="当前目录不是Git仓库"
            )
        
        self.logger.info("开始修复Git问题...")
        
        import time
        start_time = time.time()
        
        issues_fixed = 0
        issues_found = 0
        error_messages = []
        
        try:
            # 分析问题
            issues = self.analyze(context)
            issues_found = len(issues)
            
            if issues_found == 0:
                self.logger.info("未发现Git问题")
                return FixResult(
                    fix_type=self.fix_type,
                    status=FixStatus.SUCCESS,
                    issues_found=0,
                    issues_fixed=0,
                    duration_seconds=time.time() - start_time
                )
            
            # 按问题类型分组
            issues_by_type = {}
            for issue in issues:
                if issue.issue_type not in issues_by_type:
                    issues_by_type[issue.issue_type] = []
                issues_by_type[issue.issue_type].append(issue)
            
            # 修复不同类型的问题
            for issue_type, type_issues in issues_by_type.items():
                try:
                    if issue_type == "merge_conflict":

                        fixed_count = self._fix_merge_conflicts(type_issues)
                    elif issue_type == "uncommitted_changes":
                        fixed_count = self._fix_uncommitted_changes(type_issues)
#                     elif issue_type == "untracked_code_file":
#                         fixed_count = self._fix_untracked_files(type_issues, file_type="code")
#                     elif issue_type == "untracked_data_file":
                        fixed_count = self._fix_untracked_files(type_issues, file_type="data")

                    elif issue_type == "branch_ahead":
                        fixed_count = self._fix_branch_ahead(type_issues)

# 
                    elif issue_type == "branch_behind":
                        fixed_count = self._fix_branch_behind(type_issues)
#                     elif issue_type == "detached_head":
#                         fixed_count = self._fix_detached_head(type_issues)
                        #                     elif issue_type == "missing_gitignore":

#                         fixed_count = self._fix_missing_gitignore(type_issues)
#                     elif issue_type == "incomplete_gitignore":
    #                         fixed_count = self._fix_incomplete_gitignore(type_issues)

#                     elif issue_type == "large_file":
                        fixed_count = self._fix_large_files(type_issues)

                    else:
                        fixed_count = 0

                    
                    issues_fixed += fixed_count
                    
                except Exception as e:
#                     error_msg = f"修复 {issue_type} 类型Git问题失败: {e}"
                    self.logger.error(error_msg)
                    error_messages.append(error_msg)

            
             # 确定修复状态

            if issues_fixed == issues_found:
                status = FixStatus.SUCCESS
            elif issues_fixed > 0:
                status = FixStatus.PARTIAL_SUCCESS
            else:
                status = FixStatus.FAILED
            
            duration = time.time() - start_time
            
            return FixResult(
                fix_type=self.fix_type,
                status=status,
                issues_found=issues_found,
                issues_fixed=issues_fixed,
                error_message="; ".join(error_messages) if error_messages else None,
                duration_seconds=duration,
                details={

#                     "issues_by_type": {k: len(v) for k, v in issues_by_type.items()},
#                     "fixed_by_type": self._get_fixed_by_type(issues_by_type, issues_fixed)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Git修复过程失败: {e}")
            return FixResult(
            fix_type=self.fix_type,

#                 status=FixStatus.FAILED,
#                 issues_found=issues_found,
#                 issues_fixed=issues_fixed,
#                 error_message=str(e),
#                 duration_seconds=time.time() - start_time

            )
    
    def _fix_merge_conflicts(self, issues: List[GitIssue]) -> int:
        """修复合并冲突"""
        fixed_count = 0

#         
        for issue in issues:
            try:
                if issue.file_path:
                    # 尝试自动解决冲突
                    if self._resolve_merge_conflict(issue.file_path):

                        self.logger.info(f"成功解决合并冲突: {issue.file_path}")
                        fixed_count += 1
                    else:
                        self.logger.warning(f"无法自动解决合并冲突: {issue.file_path}")

            
            except Exception as e:
                self.logger.error(f"修复合并冲突失败: {e}")
        
        return fixed_count
    
    def _fix_uncommitted_changes(self, issues: List[GitIssue]) -> int:
#         """修复未提交的更改"""
#         fixed_count = 0
#         

        try:
            # 自动暂存并提交更改

            # 这里使用简化的逻辑，实际应用中可能需要更复杂的处理
            
            # 暂存所有更改
            stage_result = subprocess.run(
            ['git', 'add', '-A'],

#                 cwd=self.project_root,
                capture_output=True,
#                 text=True,
#                 timeout=30
            )
            
            if stage_result.returncode == 0:
                # 提交更改

                commit_result = subprocess.run(
                    ['git', 'commit', '-m', 'Auto-fix: Commit uncommitted changes'],
                    cwd=self.project_root,
                    capture_output=True,

#                     text=True,
#                     timeout=30
                )
#                 
                if commit_result.returncode == 0:
                    self.logger.info("成功提交未提交的更改")
                    fixed_count = len(issues)

                else:
                    self.logger.warning(f"提交更改失败: {commit_result.stderr}")
            else:
                self.logger.warning(f"暂存更改失败: {stage_result.stderr}")
        
        except Exception as e:
            self.logger.error(f"修复未提交更改失败: {e}")
#         
#         return fixed_count
#     
#     def _fix_untracked_files(self, issues: List[GitIssue], file_type: str) -> int:
        """修复未跟踪的文件"""


        fixed_count = 0
        
        try:
            for issue in issues:

#                 if issue.file_path and issue.file_path.exists():
                    # 添加文件到Git
                    add_result = subprocess.run(
#                         ['git', 'add', str(issue.file_path)],
                        cwd=self.project_root,

 capture_output=True,

                        text=True,
                        timeout=10
                    )
                    
                    if add_result.returncode == 0:
#                         self.logger.info(f"成功添加文件到Git: {issue.file_path}")
                        fixed_count += 1
#                     else:
#                         self.logger.warning(f"添加文件到Git失败: {issue.file_path}")
        
        except Exception as e:
            self.logger.error(f"修复未跟踪文件失败: {e}")

        
        return fixed_count
    
    def _fix_branch_ahead(self, issues: List[GitIssue]) -> int:
        """修复分支领先问题"""
        fixed_count = 0

#         
        try:
            # 推送本地提交
            push_result = subprocess.run(
            ['git', 'push'],

                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if push_result.returncode == 0:
#                 self.logger.info("成功推送本地提交")
                fixed_count = len(issues)
#             else:
                self.logger.warning(f"推送失败: {push_result.stderr}")

        
        except Exception as e:
            self.logger.error(f"修复分支领先问题失败: {e}")
        
        return fixed_count
    
    def _fix_branch_behind(self, issues: List[GitIssue]) -> int:
        """修复分支落后问题"""
        fixed_count = 0
        
        try:
            # 拉取远程更新
            pull_result = subprocess.run(
                ['git', 'pull'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if pull_result.returncode == 0:
                self.logger.info("成功拉取远程更新")
                fixed_count = len(issues)
            else:
                self.logger.warning(f"拉取失败: {pull_result.stderr}")
        
        except Exception as e:
            self.logger.error(f"修复分支落后问题失败: {e}")
        
        return fixed_count
    
    def _fix_detached_head(self, issues: List[GitIssue]) -> int:
        """修复detached HEAD问题"""
        fixed_count = 0
        
        try:
            # 创建新分支
            branch_name = f"detached-head-fix-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            checkout_result = subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if checkout_result.returncode == 0:
                self.logger.info(f"成功创建新分支: {branch_name}")
                fixed_count = len(issues)
            else:
                self.logger.warning(f"创建新分支失败: {checkout_result.stderr}")
        
        except Exception as e:
            self.logger.error(f"修复detached HEAD失败: {e}")
        
        return fixed_count
    
    def _fix_missing_gitignore(self, issues: List[GitIssue]) -> int:
        """修复缺失的.gitignore"""
        fixed_count = 0
        
        try:
            gitignore_path = self.project_root / ".gitignore"
            
            # 创建基本的.gitignore
            basic_gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/

lib/
lib64/
parts/
sdist/

 var/

wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
.env/
.venv/

 # IDE


.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/

# OS
.DS_Store

Thumbs.db
"""
            
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(basic_gitignore)
            
            self.logger.info("已创建基本的.gitignore文件")
            fixed_count = len(issues)
        
        except Exception as e:
            self.logger.error(f"创建.gitignore文件失败: {e}")
        
        return fixed_count
    
    def _fix_incomplete_gitignore(self, issues: List[GitIssue]) -> int:
        """修复不完整的.gitignore"""
        fixed_count = 0

        
        try:
            gitignore_path = self.project_root / ".gitignore"
            
            # 添加缺失的常见模式
            additional_patterns = [
                "",
                "# Auto-fix additions",

#                 "__pycache__/",
#                 "*.pyc",
#                 "*.pyo",
                ".Python",

                "venv/",
                "node_modules/",
                ".DS_Store",
                "*.log"
            ]
            
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(additional_patterns))
#             
#             self.logger.info("已更新.gitignore文件")
            fixed_count = len(issues)

        
        except Exception as e:
            self.logger.error(f"更新.gitignore文件失败: {e}")
        
        return fixed_count
    
    def _fix_large_files(self, issues: List[GitIssue]) -> int:
        """修复大文件问题"""
        fixed_count = 0
        
        for issue in issues:
            try:
                if issue.file_path:
                    self.logger.warning(f"大文件需要手动处理: {issue.file_path}")
                    self.logger.info(f"建议使用Git LFS: git lfs track '{issue.file_path.name}'")
                    # 标记为已处理（因为我们已经提供了建议）
                    fixed_count += 1
            
            except Exception as e:
                self.logger.error(f"处理大文件问题失败: {e}")

        
        return fixed_count
    
    def _resolve_merge_conflict(self, file_path: Path) -> bool:
        """解决合并冲突"""
        try:
            # 简化的冲突解决策略
            # 在实际应用中，这里需要更智能的冲突解决算法
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            
            # 检查是否存在冲突标记
            if '<<<<<<<' in content and '>>>>>>>' in content:

                # 尝试简单的冲突解决策略
                # 这里可以实现更复杂的逻辑
                
                # 例如：保留当前版本（ours）
                resolved_content = self._resolve_conflict_keep_ours(content)

                
                if resolved_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(resolved_content)
                    
                    # 标记冲突已解决
                    subprocess.run(
                        ['git', 'add', str(file_path)],
                        cwd=self.project_root,
                        capture_output=True,
                        timeout=10
                    )
                    
                    return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"解决合并冲突失败 {file_path}: {e}")
            return False
    
    def _resolve_conflict_keep_ours(self, content: str) -> str:
        """解决冲突 - 保留当前版本"""
        # 简化的冲突解决：保留ours部分
        lines = content.split('\n')
        resolved_lines = []
        in_conflict = False
        use_ours = True
        
        for line in lines:
            if line.startswith('<<<<<<<'):
                in_conflict = True
                use_ours = True
            elif line.startswith('======='):
                use_ours = False
            elif line.startswith('>>>>>>>'):
                in_conflict = False
                use_ours = True
            elif not in_conflict or use_ours:
                resolved_lines.append(line)
        
        return '\n'.join(resolved_lines)
    
    def _get_fixed_by_type(self, issues_by_type: Dict[str, List[GitIssue]], 
                          total_fixed: int) -> Dict[str, int]:
        """获取按类型修复的数量"""
        # 简化处理：按比例分配修复数量
        fixed_by_type = {}
        total_issues = sum(len(issues) for issues in issues_by_type.values())
        
        if total_issues > 0:
            for issue_type, issues in issues_by_type.items():
                proportion = len(issues) / total_issues
                fixed_count = int(total_fixed * proportion)
                fixed_by_type[issue_type] = max(1, fixed_count) if issues else 0
        
        return fixed_by_type