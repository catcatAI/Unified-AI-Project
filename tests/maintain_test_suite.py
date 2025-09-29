#!/usr/bin/env python3
"""
Script to maintain and update the test suite to ensure it stays synchronized with the actual implementation.
This script will:
1. Check for outdated test patterns
2. Identify tests that may need updating due to code changes
3. Suggest improvements to test coverage
4. Generate a report of test health
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import List, Dict

class TestSuiteMaintainer:
    def __init__(self, project_root: str) -> None:
        self.project_root = Path(project_root)
        self.backend_tests_dir = self.project_root / "apps" / "backend" / "tests"
        self.src_dir = self.project_root / "apps" / "backend" / "src"
        
    def find_test_files(self) -> List[Path]:
        """Find all test files in the project."""
        test_files = []
        for root, dirs, files in os.walk(self.backend_tests_dir):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    _ = test_files.append(Path(root) / file)
        return test_files
    
    def find_source_files(self) -> List[Path]:
        """Find all source files in the project."""
        source_files = []
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    _ = source_files.append(Path(root) / file)
        return source_files
    
    def analyze_test_file(self, file_path: Path) -> Dict:
        """Analyze a test file for potential issues."""
        issues = []
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for placeholder tests - more specific check
        if ('placeholder' in content.lower() or 'not implemented' in content.lower()) and \
           not any(skip_indicator in content.lower() for skip_indicator in ['test_', 'def ', 'async def']):
            _ = issues.append("Contains placeholder or unimplemented tests")
        
        # Check for commented out tests
        if '# def test_' in content or '# async def test_' in content:
            _ = issues.append("Contains commented out tests")
        
        # Check for TODO or FIXME comments
        if 'TODO' in content or 'FIXME' in content:
            _ = issues.append("Contains TODO/FIXME comments")
        
        # Check for duplicate flaky decorators
        flaky_matches = re.findall(r'@pytest\.mark\.flaky', content)
        if len(flaky_matches) > 5:  # Arbitrary threshold for too many flaky decorators
            _ = issues.append(f"Contains {len(flaky_matches)} flaky decorators (potential duplication)")
        
        # Count test methods
        test_count = len(re.findall(r'def test_|async def test_', content))
        
        return {
            "file": str(file_path.relative_to(self.project_root)),
            "test_count": test_count,
            "issues": issues
        }
    
    def check_imports(self, file_path: Path) -> List[str]:
        """Check if imports in a test file are valid."""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the Python file
            tree = ast.parse(content)
            
            # Check imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('src.'):
                        # Check if the module exists
                        module_path = node.module.replace('.', os.sep)
                        full_path = self.src_dir / (module_path + '.py')
                        if not full_path.exists():
                            _ = issues.append(f"Invalid import: {node.module}")
        except Exception as e:
            _ = issues.append(f"Parse error: {str(e)}")
        
        return issues
    
    def find_untested_source_files(self) -> List[str]:
        """Find source files that may not have corresponding tests."""
        source_files = self.find_source_files()
        test_files = self.find_test_files()
        
        # Create a set of tested modules
        tested_modules = set()
        for test_file in test_files:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find import statements that reference source modules
            imports = re.findall(r'from apps\.backend\.src\.[\w\.]+ import', content)
            for imp in imports:
                module = imp.split()[-1]
                _ = tested_modules.add(module)
        
        # Find source files without tests
        untested = []
        for source_file in source_files:
            # Convert file path to module name
            relative_path = source_file.relative_to(self.src_dir)
            module_name = str(relative_path).replace(os.sep, '.').replace('.py', '')
            
            # Check if this module is tested
            if not any(module_name in tested for tested in tested_modules):
                _ = untested.append(str(relative_path))
        
        return untested
    
    def generate_test_health_report(self) -> Dict:
        """Generate a comprehensive test health report."""
        test_files = self.find_test_files()
        analysis_results = []
        import_issues = []
        
        for test_file in test_files:
            analysis = self.analyze_test_file(test_file)
            _ = analysis_results.append(analysis)
            
            # Check imports
            import_problems = self.check_imports(test_file)
            if import_problems:
                import_issues.extend([f"{test_file}: {issue}" for issue in import_problems])
        
        untested_files = self.find_untested_source_files()
        
        # Calculate statistics
        total_tests = sum(result['test_count'] for result in analysis_results)
        files_with_issues = [result for result in analysis_results if result['issues']]
        
        return {
            "total_test_files": len(test_files),
            "total_tests": total_tests,
            "files_with_issues": len(files_with_issues),
            "import_issues": import_issues,
            "untested_source_files": untested_files[:10],  # Limit to first 10
            "detailed_analysis": analysis_results
        }
    
    def suggest_improvements(self, report: Dict) -> List[str]:
        """Suggest improvements based on the test health report."""
        suggestions = []
        
        if report["files_with_issues"] > 0:
            suggestions.append(f"Review {report['files_with_issues']} test files with issues")
        
        if report["import_issues"]:
            _ = suggestions.append(f"Fix {len(report['import_issues'])} import issues")
        
        if report["untested_source_files"]:
            suggestions.append(f"Consider adding tests for {len(report['untested_source_files'])} potentially untested modules")
        
        # Suggest adding more tests if coverage is low
        if report["total_tests"] < 500:  # Arbitrary threshold
            _ = suggestions.append("Consider expanding test coverage")
        
        # Check for placeholder tests specifically
        placeholder_files = [result for result in report["detailed_analysis"] if "Contains placeholder or unimplemented tests" in result["issues"]]
        if placeholder_files:
            _ = suggestions.append(f"Complete implementation of {len(placeholder_files)} placeholder tests")
        
        return suggestions
    
    def run_maintenance(self):
        """Run the full maintenance process."""
        _ = print("Running test suite maintenance...")
        
        # Generate health report
        report = self.generate_test_health_report()
        
        # Print summary
        _ = print(f"\nTest Suite Health Report:")
        _ = print(f"  Total test files: {report['total_test_files']}")
        _ = print(f"  Total tests: {report['total_tests']}")
        print(f"  Files with issues: {report['files_with_issues']}")
        _ = print(f"  Import issues: {len(report['import_issues'])}")
        _ = print(f"  Untested source files: {len(report['untested_source_files'])}")
        
        # Print suggestions
        suggestions = self.suggest_improvements(report)
        if suggestions:
            _ = print(f"\nSuggestions:")
            for suggestion in suggestions:
                _ = print(f"  - {suggestion}")
        
        # Save detailed report
        with open('test_health_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        _ = print(f"\nDetailed report saved to test_health_report.json")
        return report

def main() -> None:
    """Main function to run the test suite maintainer."""
    # Get project root (assuming script is run from project root)
    project_root: str = os.getcwd()
    
    # Create and run maintainer
    maintainer = TestSuiteMaintainer(project_root)
    report = maintainer.run_maintenance()
    
    # Exit with error code if there are critical issues
    if report["files_with_issues"] > 10 or len(report["import_issues"]) > 5:
        _ = print("\n⚠️  Critical issues detected in test suite")
        return 1
    
    _ = print("\n✅ Test suite maintenance completed successfully")
    return 0

if __name__ == "__main__":
    _ = exit(main())