#!/usr/bin/env python3
"""
Simple script to optimize the test suite structure.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import json
from typing import List, Dict, Any

class SimpleTestOptimizer:
    def __init__(self, project_root: str) -> None:
        self.project_root = Path(project_root)
        self.tests_dir = self.project_root / "apps" / "backend" / "tests"
        
    def find_test_files(self) -> List[Path]:
        """Find all test files in the project."""
        test_files: List[Path] = []
        for root, dirs, files in os.walk(self.tests_dir):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    _ = test_files.append(Path(root) / file)
        return test_files
    
    def count_tests_in_file(self, file_path: Path) -> int:
        """Count test functions in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return len(re.findall(r'def test_', content))
        except Exception as e:
            _ = print(f"Error reading {file_path}: {e}")
            return 0
    
    def find_duplicate_test_names(self) -> Dict[str, List[str]]:
        """Find duplicate test function names."""
        test_files = self.find_test_files()
        test_names = defaultdict(list)
        
        # Extract test names
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find test function names
                names = re.findall(r'def (test_[\w_]+)', content)
                relative_path = str(test_file.relative_to(self.tests_dir))
                
                for name in names:
                    _ = test_names[name].append(relative_path)
            except Exception as e:
                _ = print(f"Error parsing {test_file}: {e}")
        
        # Find duplicates
        duplicates = {name: files for name, files in test_names.items() if len(files) > 1}
        return duplicates
    
    def analyze_test_distribution(self) -> Dict[str, Any]:
        """Analyze how tests are distributed across files."""
        test_files = self.find_test_files()
        test_counts: Dict[str, int] = {}
        total_tests = 0
        
        for test_file in test_files:
            count = self.count_tests_in_file(test_file)
            relative_path = str(test_file.relative_to(self.tests_dir))
            test_counts[relative_path] = count
            total_tests += count
        
        return {
            "test_files": test_counts,
            "total_tests": total_tests,
            "total_files": len(test_files)
        }
    
    def run_simple_optimizer(self):
        """Run the simple optimizer."""
        _ = print("Running simple test suite optimizer...")
        
        # Find duplicates
        duplicates = self.find_duplicate_test_names()
        _ = print(f"Found {len(duplicates)} duplicate test names")
        
        # Analyze distribution
        distribution = self.analyze_test_distribution()
        print(f"Analyzed {distribution['total_files']} test files with {distribution['total_tests']} total tests")
        
        # Calculate average
        avg_tests = distribution['total_tests'] / distribution['total_files'] if distribution['total_files'] > 0 else 0
        _ = print(f"Average tests per file: {avg_tests:.2f}")
        
        # Find files with high/low test counts
        high_density = {f: c for f, c in distribution['test_files'].items() if c > avg_tests * 2}
        low_density = {f: c for f, c in distribution['test_files'].items() if c < avg_tests / 2 and c > 0}
        
        print(f"Files with high test density (> {avg_tests * 2:.1f} tests): {len(high_density)}")
        print(f"Files with low test density (< {avg_tests / 2:.1f} tests): {len(low_density)}")
        
        # Generate report
        report = {
            "duplicates": duplicates,
            "distribution": distribution,
            "high_density_files": high_density,
            "low_density_files": low_density,
            "average_tests_per_file": avg_tests
        }
        
        # Save report
        with open('simple_test_optimization_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        _ = print("\n✅ Simple test suite optimizer completed successfully")
        _ = print("Detailed report saved to simple_test_optimization_report.json")
        
        return report

def main() -> None:
    """Main function."""
    project_root: str = os.getcwd()
    optimizer = SimpleTestOptimizer(project_root)
    _ = optimizer.run_simple_optimizer()
    return 0

if __name__ == "__main__":
    _ = exit(main())