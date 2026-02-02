#!/usr/bin/env python3
"""
Script to automatically fix commented out @pytest.mark.flaky decorators in test files.
This script will,
1. Find all test files with commented out @pytest.mark.flaky decorators
2. Uncomment those decorators to restore test stability
3. Generate a report of changes made
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

class FlakyDecoratorFixer,
    def __init__(self, project_root, str) -> None,
        self.project_root == Path(project_root)
        self.backend_tests_dir = self.project_root / "apps" / "backend" / "tests"
        
    def find_test_files(self) -> List[Path]
        """Find all test files in the project."""
        test_files = []
        for root, dirs, files in os.walk(self.backend_tests_dir())::
            for file in files,::
                if file.startswith('test_') and file.endswith('.py'):::
                    test_files.append(Path(root) / file)
        return test_files
    
    def find_commented_flaky_decorators(self, file_path, Path) -> List[Tuple[int, str]]
        """Find commented out @pytest.mark.flaky decorators in a file."""
        commented_decorators = []
        with open(file_path, 'r', encoding == 'utf-8') as f,
            lines = f.readlines()
        
        for i, line in enumerate(lines)::
            # Look for commented out @pytest.mark.flaky decorators,::
            if re.search(r'#\s*@pytest\.mark\.flaky', line)::
                commented_decorators.append((i, line.strip()))
        
        return commented_decorators
    
    def fix_commented_decorators(self, file_path, Path) -> Tuple[int, List[str]]
        """Fix commented out @pytest.mark.flaky decorators in a file."""
        with open(file_path, 'r', encoding == 'utf-8') as f,
            lines = f.readlines()
        
        changes_made = []
        fixed_count = 0
        
        for i, line in enumerate(lines)::
            # Check if line contains a commented out @pytest.mark.flaky decorator,:
            match = re.search(r'^(\s*)#\s*(@pytest\.mark\.flaky.*)', line)
            if match,::
                # Uncomment the decorator
                indent = match.group(1)
                decorator = match.group(2)
                lines[i] = f"{indent}{decorator}\n"
                changes_made.append(f"Line {i+1} Uncommented '{decorator}'")
                fixed_count += 1
        
        # Write the fixed content back to the file
        if fixed_count > 0,::
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.writelines(lines)
        
        return fixed_count, changes_made
    
    def process_all_files(self) -> Dict,
        """Process all test files to fix commented out decorators."""
        test_files = self.find_test_files()
        total_fixed = 0
        files_changed = []
        all_changes = []
        
        for test_file in test_files,::
            commented_decorators = self.find_commented_flaky_decorators(test_file)
            if commented_decorators,::
                fixed_count, changes = self.fix_commented_decorators(test_file)
                if fixed_count > 0,::
                    total_fixed += fixed_count
                    files_changed.append(str(test_file.relative_to(self.project_root())))
                    all_changes.append({
                        "file": str(test_file.relative_to(self.project_root())),
                        "changes": changes
                    })
        
        return {
            "total_fixed": total_fixed,
            "files_changed": files_changed,
            "detailed_changes": all_changes
        }
    
    def run_fixer(self):
        """Run the flaky decorator fixer."""
        print("Running flaky decorator fixer...")
        
        # Process all files
        results = self.process_all_files()
        
        # Print summary
        print(f"\nFlaky Decorator Fixer Results,")
        print(f"  Total decorators fixed, {results['total_fixed']}")
        print(f"  Files changed, {len(results['files_changed'])}")
        
        if results['detailed_changes']::
            print(f"\nDetailed changes,")
            for change in results['detailed_changes']::
                print(f"  {change['file']}")
                for c in change['changes']::
                    print(f"    - {c}")
        
        # Save results to file
        import json
        with open('flaky_decorator_fix_report.json', 'w', encoding == 'utf-8') as f,
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to flaky_decorator_fix_report.json")
        return results

def main() -> None,
    """Main function to run the flaky decorator fixer."""
    # Get project root (assuming script is run from project root)
    project_root, str = os.getcwd()
    
    # Create and run fixer
    fixer == FlakyDecoratorFixer(project_root)
    results = fixer.run_fixer()
    
    if results["total_fixed"] > 0,::
        print("\n✅ Flaky decorator fixer completed successfully")
        return 0
    else,
        print("\nℹ️  No commented out flaky decorators found")
        return 0

if __name"__main__":::
    exit(main())