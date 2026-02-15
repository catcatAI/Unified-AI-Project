#!/usr/bin/env python
# coding: utf-8
"""
Automated Test Syntax Fixer

Fixes common syntax errors in test files:
- try, → try:
- :: → :
- == → = (in assignments)
- coding, utf-8 → coding: utf-8
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


class TestSyntaxFixer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fixes_applied = []
        self.errors = []
        
        self.patterns = [
            (r'\btry\s*,', 'try:', 'try, → try:'),
            (r'^(\s*)(class\s+\w+)\s*,\s*$', r'\1\2:', 'class Name, → class Name:'),
            (r'^(\s*)(def\s+\w+\s*\([^)]*\))\s*,\s*$', r'\1\2:', 'def func(), → def func():'),
            (r'^(\s*)(def|class)\s+\w+.*::$', r'\1\2 \3:', ':: → :'),
            (r'^(\s*)(\w+)\s*==\s*([^=])', r'\1\2 = \3', '== → = (assignment)'),
            (r'\bwait\s+asyncio\.', 'await asyncio.', 'wait asyncio → await asyncio'),
            (r'#\s*-\*-\s*coding\s*,\s*utf-8\s*-\*-', '# -*- coding: utf-8 -*-', 'coding, utf-8 → coding: utf-8'),
            (r'#\s*coding\s*,\s*utf-8', '# coding: utf-8', 'coding, utf-8 → coding: utf-8')
        ]

    def fix_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    original_content = f.read()
            except Exception as e:
                self.errors.append(f"Error reading {file_path}: {e}")
                return False, []
        except Exception as e:
            self.errors.append(f"Error reading {file_path}: {e}")
            return False, []

        modified_content = original_content
        applied_fixes = []

        lines = modified_content.split('\n')
        for i, line in enumerate(lines):
            for pattern, replacement, description in self.patterns:
                if re.search(pattern, line, re.MULTILINE):
                    new_line = re.sub(pattern, replacement, line)
                    if new_line != line:
                        lines[i] = new_line
                        applied_fixes.append(f"Line {i+1}: {description}")

        modified_content = '\n'.join(lines)

        if modified_content != original_content:
            if not self.dry_run:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                except Exception as e:
                    self.errors.append(f"Error writing {file_path}: {e}")
                    return False, []
            
            self.fixes_applied.append((str(file_path), applied_fixes))
            return True, applied_fixes
        
        return False, []

    def process_directory(self, directory: Path, sample: int = None) -> None:
        test_files = sorted(directory.rglob('*.py'))
        
        if sample and sample > 0:
            import random
            test_files = random.sample(test_files, min(sample, len(test_files)))
        
        print(f"Processing {len(test_files)} files...")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print()

        fixed_count = 0
        for file_path in test_files:
            modified, fixes = self.fix_file(file_path)
            if modified:
                fixed_count += 1
                print(f"✓ Fixed: {file_path}")
                for fix in fixes:
                    print(f"  - {fix}")
        
        print()
        print("=" * 80)
        print(f"Summary:")
        print(f"  Files processed: {len(test_files)}")
        print(f"  Files modified: {fixed_count}")
        print(f"  Errors: {len(self.errors)}")
        
        if self.errors:
            print()
            print("Errors encountered:")
            for error in self.errors:
                print(f"  - {error}")

    def generate_report(self, output_path: Path = None) -> str:
        report = []
        report.append("Test Syntax Fix Report")
        report.append("=" * 80)
        report.append(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        report.append(f"Files fixed: {len(self.fixes_applied)}")
        report.append()
        
        for file_path, fixes in self.fixes_applied:
            report.append(f"\n{file_path}:")
            for fix in fixes:
                report.append(f"  - {fix}")
        
        if self.errors:
            report.append("\n\nErrors:")
            for error in self.errors:
                report.append(f"  - {error}")
        
        report_text = '\n'.join(report)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\nReport saved to: {output_path}")
        
        return report_text


def main():
    parser = argparse.ArgumentParser(description='Fix common test syntax errors')
    parser.add_argument('path', type=str, help='Path to test directory or file')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--sample', type=int, help='Process only N random files (for testing)')
    parser.add_argument('--report', type=str, help='Save report to file')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)
    
    fixer = TestSyntaxFixer(dry_run=args.dry_run)
    
    if path.is_file():
        modified, fixes = fixer.fix_file(path)
        if modified:
            print(f"✓ Fixed: {path}")
            for fix in fixes:
                print(f"  - {fix}")
        else:
            print(f"No fixes needed for {path}")
    else:
        fixer.process_directory(path, sample=args.sample)
    
    if args.report:
        fixer.generate_report(Path(args.report))
    
    sys.exit(0 if not fixer.errors else 1)


if __name__ == '__main__':
    main()
