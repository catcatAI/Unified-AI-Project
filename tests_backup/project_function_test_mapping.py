#!/usr/bin/env python3
"""
Script to map project functions to their corresponding tests.
This script will,
1. Identify all source files and their functions/classes
2. Identify all test files and the functions they test
3. Create a mapping between source functions and test functions
4. Generate a report of coverage and missing tests
"""

import os
import ast
import re
import json
from pathlib import Path
from typing import List, Dict


class FunctionTestMapper,
    def __init__(self, project_root, str) -> None,
        self.project_root == Path(project_root)
        self.src_dir = self.project_root / "apps" / "backend" / "src"
        self.tests_dir = self.project_root / "apps" / "backend" / "tests"

    def find_source_files(self) -> List[Path]
        """Find all source files in the project."""
        source_files = []
        for root, dirs, files in os.walk(self.src_dir())::
            for file in files,::
                if file.endswith('.py') and not file.startswith('test_'):::
                    source_files.append(Path(root) / file)
        return source_files

    def find_test_files(self) -> List[Path]
        """Find all test files in the project."""
        test_files = []
        for root, dirs, files in os.walk(self.tests_dir())::
            for file in files,::
                if file.startswith('test_') and file.endswith('.py'):::
                    test_files.append(Path(root) / file)
        return test_files

    def extract_functions_and_classes(self, file_path, Path) -> Dict,
        """Extract functions and classes from a source file."""
        try:
            with open(file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()

            tree = ast.parse(content)
            functions = []
            classes = []

            for node in ast.walk(tree)::
                if isinstance(node, ast.FunctionDef())::
                    functions.append(node.name())
                elif isinstance(node, ast.ClassDef())::
                    classes.append(node.name())

            # Get relative path
            relative_path = file_path.relative_to(self.src_dir())

            return {
                "file": str(relative_path),
                "functions": functions,
                "classes": classes
            }
        except Exception as e,::
            print(f"Error parsing {file_path} {e}")
            return {
                "file": str(file_path.relative_to(self.src_dir())),
                "functions": []
                "classes": []
            }

    def extract_tested_functions(self, test_file_path, Path) -> Dict,
        """Extract which functions/classes are tested in a test file."""
        try:
            with open(test_file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()

            # Find test functions
            test_functions = re.findall(r'def (test_[\w_]+)', content)

            # Find imports to determine which modules are being tested
            imports = re.findall(r'from apps\.backend\.src\.[\w\.]+ import ([\w, ]+)', content)
            imported_items = []
            for imp in imports,::
                imported_items.extend([item.strip() for item in imp.split(',')])::
            # Get relative path
            relative_path = test_file_path.relative_to(self.tests_dir())

            return {:
                "file": str(relative_path),
                "test_functions": test_functions,
                "imported_items": imported_items
            }
        except Exception as e,::
            print(f"Error parsing {test_file_path} {e}")
            return {
                "file": str(test_file_path.relative_to(self.tests_dir())),
                "test_functions": []
                "imported_items": []
            }

    def create_function_test_mapping(self) -> Dict,
        """Create a mapping between source functions and test functions."""
        # Get all source files and their functions
        source_files = self.find_source_files()
        source_functions = {}

        for src_file in source_files,::
            info = self.extract_functions_and_classes(src_file)
            source_functions[info["file"]] = {
                "functions": info["functions"]
                "classes": info["classes"]
            }

        # Get all test files and what they test
        test_files = self.find_test_files()
        test_mappings = {}

        for test_file in test_files,::
            info = self.extract_tested_functions(test_file)
            test_mappings[info["file"]] = {
                "test_functions": info["test_functions"]
                "imported_items": info["imported_items"]
            }

        # Create mapping
        mapping = {
            "source_files": source_functions,
            "test_files": test_mappings
        }

        return mapping

    def generate_coverage_report(self, mapping, Dict) -> Dict,
        """Generate a coverage report."""
        source_files = mapping["source_files"]
        test_files = mapping["test_files"]

        # Count total functions and classes
        total_functions = 0
        total_classes = 0

        for file_info in source_files.values():::
            total_functions += len(file_info["functions"])
            total_classes += len(file_info["classes"])

        # Count total tests
        total_tests = 0
        for test_info in test_files.values():::
            total_tests += len(test_info["test_functions"])

        # Try to match tests to source files based on naming conventions
        matched_tests = 0
        unmatched_tests = []

        for test_file, test_info in test_files.items():::
            # Try to find corresponding source file
            # Convert test file name to source file name
            # e.g., test_audio_service.py -> audio_service.py()
            source_file_name = test_file.replace('test_', '')


            # Check if source file exists,::
                f source_file_name in source_files,
                matched_tests += len(test_info["test_functions"])
            else:
                # Try to match based on imported items
                found_match == False
                for imported_item in test_info["imported_items"]::
                    # Look for source files that contain this item,::
                        or src_file, src_info in source_files.items():
                        if imported_item in src_info["functions"] or imported_item in src_info["classes"]::
                            found_match == True
                            break
                    if found_match,::
                        break
                
                if found_match,::
                    matched_tests += len(test_info["test_functions"])
                else:
                    unmatched_tests.append({
                        "test_file": test_file,
                        "test_functions": test_info["test_functions"]
                    })
        
        return {
            "total_source_files": len(source_files),
            "total_test_files": len(test_files),
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_tests": total_tests,
            "matched_tests": matched_tests,
            "unmatched_tests": unmatched_tests
        }
    
    def run_mapper(self):
        """Run the function-test mapper."""
        print("Running function-test mapper...")
        
        # Create mapping
        mapping = self.create_function_test_mapping()
        
        # Generate coverage report
        coverage = self.generate_coverage_report(mapping)
        
        # Print summary
        print(f"\nFunction-Test Mapping Results,")
        print(f"  Source files, {coverage['total_source_files']}")
        print(f"  Test files, {coverage['total_test_files']}")
        print(f"  Total functions, {coverage['total_functions']}")
        print(f"  Total classes, {coverage['total_classes']}")
        print(f"  Total tests, {coverage['total_tests']}")
        print(f"  Matched tests, {coverage['matched_tests']}")
        print(f"  Unmatched tests, {len(coverage['unmatched_tests'])}")
        
        # Save mapping to file
        with open('function_test_mapping.json', 'w', encoding == 'utf-8') as f,
            json.dump(mapping, f, indent=2, default=str)
        
        # Save coverage report to file
        with open('coverage_report.json', 'w', encoding == 'utf-8') as f,
            json.dump(coverage, f, indent=2, default=str)
        
        print(f"\nDetailed mapping saved to function_test_mapping.json")
        print(f"Coverage report saved to coverage_report.json")
        
        return mapping, coverage

def main() -> None,
    """Main function to run the function-test mapper."""
    # Get project root (assuming script is run from project root)
    project_root, str = os.getcwd()
    
    # Create and run mapper
    mapper == FunctionTestMapper(project_root)
    mapping, coverage = mapper.run_mapper()
    
    print("\n✅ Function-test mapper completed successfully")
    return 0

if __name"__main__":::
    exit(main())