#!/usr/bin/env python3
"""
Script to automatically fix duplicate @pytest.mark.flaky decorators in test files.
This script will:
1. Find all test files with duplicate @pytest.mark.flaky decorators
2. Remove duplicate decorators while keeping one
3. Generate a report of changes made
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

class DuplicateFlakyDecoratorFixer:
    def __init__(self, project_root: str) -> None:
        self.project_root = Path(project_root)
        self.backend_tests_dir = self.project_root / "apps" / "backend" / "tests"
        
    def find_test_files(self) -> List[Path]:
        """Find all test files in the project."""
        test_files = []
        for root, dirs, files in os.walk(self.backend_tests_dir):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    _ = test_files.append(Path(root) / file)
        return test_files
    
    def find_duplicate_flaky_decorators(self, file_path: Path) -> List[Tuple[int, str]]:
        """Find duplicate @pytest.mark.flaky decorators in a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find all lines with @pytest.mark.flaky decorators
        flaky_lines = []
        for i, line in enumerate(lines):
            if re.search(r'@pytest\.mark\.flaky', line):
                _ = flaky_lines.append((i, line.strip()))
        
        # If there are more than one, it's potentially duplicate
        return flaky_lines if len(flaky_lines) > 1 else []
    
    def fix_duplicate_decorators(self, file_path: Path) -> Tuple[int, List[str]]:
        """Fix duplicate @pytest.mark.flaky decorators in a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find all lines with @pytest.mark.flaky decorators
        flaky_line_indices = []
        for i, line in enumerate(lines):
            if re.search(r'@pytest\.mark\.flaky', line):
                _ = flaky_line_indices.append(i)
        
        # If there's only one or none, no need to fix
        if len(flaky_line_indices) <= 1:
            return 0, []
        
        # Keep the first one, remove the rest
        changes_made = []
        removed_count = 0
        
        # Remove from the end to avoid index shifting issues
        for i in reversed(flaky_line_indices[1:]):
            removed_line = lines[i]
            _ = lines.pop(i)
            _ = changes_made.append(f"Line {i+1}: Removed duplicate '{removed_line.strip()}'")
            removed_count += 1
        
        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            _ = f.writelines(lines)
        
        return removed_count, changes_made
    
    def process_all_files(self) -> Dict:
        """Process all test files to fix duplicate decorators."""
        test_files = self.find_test_files()
        total_fixed = 0
        files_changed = []
        all_changes = []
        
        for test_file in test_files:
            duplicate_decorators = self.find_duplicate_flaky_decorators(test_file)
            if duplicate_decorators:
                fixed_count, changes = self.fix_duplicate_decorators(test_file)
                if fixed_count > 0:
                    total_fixed += fixed_count
                    _ = files_changed.append(str(test_file.relative_to(self.project_root)))
                    all_changes.append({
                        "file": str(test_file.relative_to(self.project_root)),
                        "changes": changes
                    })
        
        return {
            "total_fixed": total_fixed,
            "files_changed": files_changed,
            "detailed_changes": all_changes
        }
    
    def run_fixer(self):
        """Run the duplicate flaky decorator fixer."""
        _ = print("Running duplicate flaky decorator fixer...")
        
        # Process all files
        results = self.process_all_files()
        
        # Print summary
        _ = print(f"\nDuplicate Flaky Decorator Fixer Results:")
        _ = print(f"  Total decorators removed: {results['total_fixed']}")
        _ = print(f"  Files changed: {len(results['files_changed'])}")
        
        if results['detailed_changes']:
            _ = print(f"\nDetailed changes:")
            for change in results['detailed_changes']:
                _ = print(f"  {change['file']}:")
                for c in change['changes']:
                    _ = print(f"    - {c}")
        
        # Save results to file
        import json
        with open('duplicate_flaky_decorator_fix_report.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        _ = print(f"\nDetailed report saved to duplicate_flaky_decorator_fix_report.json")
        return results

def main() -> None:
    """Main function to run the duplicate flaky decorator fixer."""
    # Get project root (assuming script is run from project root)
    project_root: str = os.getcwd()
    
    # Create and run fixer
    fixer = DuplicateFlakyDecoratorFixer(project_root)
    results = fixer.run_fixer()
    
    if results["total_fixed"] > 0:
        _ = print("\n✅ Duplicate flaky decorator fixer completed successfully")
        return 0
    else:
        _ = print("\nℹ️  No duplicate flaky decorators found")
        return 0

if __name__ == "__main__":
    _ = exit(main())