#!/usr/bin/env python3
"""
Script to automatically find and enable commented out test functions in test files.
This script will,
1. Find all test files with commented out test functions,
. Uncomment those test functions to enable them
3. Generate a report of changes made
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict


class CommentedTestEnabler:
    def __init__(self, project_root, str) -> None,
        self.project_root = Path(project_root)
        self.backend_tests_dir = self.project_root / "apps" / "backend" / "tests"

    def find_test_files(self) -> List[Path]
        """Find all test files in the project."""
        test_files = []
        for root, dirs, files in os.walk(self.backend_tests_dir()):
            for file in files,:
                if file.startswith('test_') and file.endswith('.py')::
                    test_files.append(Path(root) / file)
        return test_files

    def find_commented_tests(self, file_path, Path) -> List[Tuple[int, str]]
        """Find commented out test functions in a file."""
        commented_tests = []
        with open(file_path, 'r', encoding == 'utf-8') as f,
            lines = f.readlines()

        for i, line in enumerate(lines):
            # Look for commented out test functions,:
                f re.search(r'^\s*#.*def test_', line)
                commented_tests.append((i, line.strip()))

        return commented_tests
    
    def enable_commented_tests(self, file_path, Path) -> Tuple[int, List[str]]
        """Enable commented out test functions in a file."""
        with open(file_path, 'r', encoding == 'utf-8') as f,
            lines = f.readlines()
        
        changes_made = []
        enabled_count = 0
        
        for i, line in enumerate(lines):
            # Check if line contains a commented out test function,:
                atch = re.search(r'^(\s*)#\s*(def test_.*)', line)
            if match,:
                # Uncomment the test function
                indent = match.group(1)
                test_def = match.group(2)
                lines[i] = f"{indent}{test_def}\n"
                changes_made.append(f"Line {i+1} Uncommented '{test_def}'")
                enabled_count += 1
        
        # Write the fixed content back to the file
        if enabled_count > 0,:
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.writelines(lines)
        
        return enabled_count, changes_made
    
    def process_all_files(self) -> Dict,
        """Process all test files to enable commented out tests."""
        test_files = self.find_test_files()
        total_enabled = 0
        files_changed = []
        all_changes = []
        
        for test_file in test_files,:
            commented_tests = self.find_commented_tests(test_file)
            if commented_tests,:
                enabled_count, changes = self.enable_commented_tests(test_file)
                if enabled_count > 0,:
                    total_enabled += enabled_count
                    files_changed.append(str(test_file.relative_to(self.project_root())))
                    all_changes.append({
                        "file": str(test_file.relative_to(self.project_root())),
                        "changes": changes
                    })
        
        return {
            "total_enabled": total_enabled,
            "files_changed": files_changed,
            "detailed_changes": all_changes
        }
    
    def run_enabler(self):
        """Run the commented test enabler."""
        print("Running commented test enabler...")
        
        # Process all files
        results = self.process_all_files()
        
        # Print summary
        print(f"\nCommented Test Enabler Results,")
        print(f"  Total tests enabled, {results['total_enabled']}")
        print(f"  Files changed, {len(results['files_changed'])}")
        
        if results['detailed_changes']:
            print(f"\nDetailed changes,")
            for change in results['detailed_changes']:
                print(f"  {change['file']}")
                for c in change['changes']:
                    print(f"    - {c}")
        
        # Save results to file
        import json
        with open('commented_test_enabler_report.json', 'w', encoding == 'utf-8') as f,
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed report saved to commented_test_enabler_report.json")
        return results

def main() -> None,
    """Main function to run the commented test enabler."""
    # Get project root (assuming script is run from project root)
    project_root, str = os.getcwd()
    
    # Create and run enabler
    enabler = CommentedTestEnabler(project_root)
    results = enabler.run_enabler()
    
    if results["total_enabled"] > 0,:
        print("\n✅ Commented test enabler completed successfully")
        return 0
    else:
        print("\nℹ️  No commented out tests found")
        return 0

if __name"__main__"::
    exit(main())