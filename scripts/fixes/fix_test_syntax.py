#!/usr/bin/env python3
"""
Test Syntax Fixer - Automated Test File Syntax Error Correction

Fixes common syntax errors in test files:
- try, -> try:
- except, -> except:
- :: -> :
- == -> = (in assignments)
- coding, utf-8 -> coding: utf-8
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple

# Common syntax error patterns and their fixes
SYNTAX_FIXES = [
    # Pattern: (regex_pattern, replacement, description)
    (r'\btry,', 'try:', 'Fix try statement: try, -> try:'),
    (r'\bexcept,', 'except:', 'Fix except statement: except, -> except:'),
    (r'\bif,', 'if:', 'Fix if statement: if, -> if:'),
    (r'\bdef,', 'def:', 'Fix def statement: def, -> def:'),
    (r'\bclass,', 'class:', 'Fix class statement: class, -> class:'),
    (r'\bfor,', 'for:', 'Fix for statement: for, -> for:'),
    (r'\bwhile,', 'while:', 'Fix while statement: while, -> while:'),
    (r'\belif,', 'elif:', 'Fix elif statement: elif, -> elif:'),
    (r'\belse,', 'else:', 'Fix else statement: else, -> else:'),
    (r'coding,\s*utf-8', 'coding: utf-8', 'Fix encoding declaration: coding, utf-8 -> coding: utf-8'),
    (r'coding,\s*UTF-8', 'coding: UTF-8', 'Fix encoding declaration: coding, UTF-8 -> coding: UTF-8'),
    
    # Double colon fixes (but not in slice notation)
    # This is tricky - we need to be careful not to break valid :: in slices
    # For now, focus on obvious cases like 'def func()::' or 'class Test()::' 
    (r'(\))\s*::', r'\1:', 'Fix double colon after function/class definition'),
]

class TestSyntaxFixer:
    def __init__(self, dry_run=False, verbose=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            'files_scanned': 0,
            'files_fixed': 0,
            'fixes_applied': 0,
            'errors': []
        }
    
    def scan_directory(self, directory: str) -> List[Path]:
        """Scan directory for Python test files"""
        test_files = []
        dir_path = Path(directory)
        
        if not dir_path.exists():
            print(f"Error: Directory {directory} does not exist")
            return []
        
        # Find all test_*.py files
        for pattern in ['test_*.py', '*_test.py']:
            test_files.extend(dir_path.rglob(pattern))
        
        if self.verbose:
            print(f"Found {len(test_files)} test files in {directory}")
        
        return test_files
    
    def fix_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        Fix syntax errors in a single file
        Returns: (was_modified, num_fixes)
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_count = 0
            
            # Apply each fix pattern
            for pattern, replacement, description in SYNTAX_FIXES:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    num_replacements = len(matches)
                    fixes_count += num_replacements
                    if self.verbose and num_replacements > 0:
                        print(f"  [{file_path.name}] {description}: {num_replacements} fixes")
            
            # Check if file was modified
            was_modified = content != original_content
            
            if was_modified:
                if not self.dry_run:
                    # Write fixed content back
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    if self.verbose:
                        print(f"  ✓ Fixed {file_path.name} ({fixes_count} issues)")
                else:
                    print(f"  [DRY-RUN] Would fix {file_path.name} ({fixes_count} issues)")
            
            return was_modified, fixes_count
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            self.stats['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
            return False, 0
    
    def fix_directory(self, directory: str, sample_size: int = None):
        """Fix all test files in directory"""
        test_files = self.scan_directory(directory)
        
        if sample_size:
            test_files = test_files[:sample_size]
            print(f"Processing sample of {len(test_files)} files (--sample {sample_size})")
        
        print(f"\nProcessing {len(test_files)} test files...")
        print(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}\n")
        
        for file_path in test_files:
            self.stats['files_scanned'] += 1
            was_modified, fixes_count = self.fix_file(file_path)
            
            if was_modified:
                self.stats['files_fixed'] += 1
                self.stats['fixes_applied'] += fixes_count
        
        self.print_summary()
    
    def print_summary(self):
        """Print summary of fixes"""
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Files scanned:   {self.stats['files_scanned']}")
        print(f"Files fixed:     {self.stats['files_fixed']}")
        print(f"Total fixes:     {self.stats['fixes_applied']}")
        print(f"Errors:          {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            print("\nErrors encountered:")
            for error in self.stats['errors']:
                print(f"  - {error}")
        
        if self.dry_run:
            print("\n⚠️  DRY-RUN MODE - No files were actually modified")
            print("   Run without --dry-run to apply changes")
        else:
            print(f"\n✅ Successfully fixed {self.stats['files_fixed']} files")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Automated Test Syntax Fixer for Angela AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run on tests directory (see what would be fixed)
  python fix_test_syntax.py tests/ --dry-run
  
  # Fix all test files
  python fix_test_syntax.py tests/
  
  # Fix sample of 5 files (for verification)
  python fix_test_syntax.py tests/ --sample 5 --verbose
  
  # Fix with verbose output
  python fix_test_syntax.py tests/ --verbose
        """
    )
    
    parser.add_argument('directory', help='Directory containing test files')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be fixed without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output for each file')
    parser.add_argument('--sample', type=int, metavar='N',
                        help='Process only first N files (for testing)')
    
    args = parser.parse_args()
    
    fixer = TestSyntaxFixer(dry_run=args.dry_run, verbose=args.verbose)
    fixer.fix_directory(args.directory, sample_size=args.sample)


if __name__ == '__main__':
    main()
