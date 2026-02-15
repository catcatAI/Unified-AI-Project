#!/usr/bin/env python
# coding: utf-8
"""
Import Performance Profiler

Measures module import times and identifies blocking operations.
Helps optimize slow module initialization and identify lazy loading opportunities.
"""

import argparse
import importlib
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple


class ImportProfiler:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []
        self.total_time = 0

    def profile_import(self, module_path: Path) -> Tuple[float, str]:
        import_name = self._path_to_module(module_path)
        
        if not import_name:
            return 0.0, f"Could not convert path to module: {module_path}"
        
        if self.verbose:
            print(f"Profiling: {import_name}")
        
        start_time = time.perf_counter()
        error_msg = None
        
        try:
            if import_name in sys.modules:
                del sys.modules[import_name]
            
            importlib.import_module(import_name)
            
        except Exception as e:
            error_msg = str(e)
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        return elapsed, error_msg

    def _path_to_module(self, file_path: Path) -> str:
        try:
            abs_path = file_path.resolve()
            cwd = Path.cwd().resolve()
            
            if abs_path.is_relative_to(cwd):
                rel_path = abs_path.relative_to(cwd)
            else:
                rel_path = abs_path
            
            module_parts = list(rel_path.parts)
            
            if module_parts[-1].endswith('.py'):
                module_parts[-1] = module_parts[-1][:-3]
            
            if module_parts[-1] == '__init__':
                module_parts = module_parts[:-1]
            
            return '.'.join(module_parts)
        
        except Exception as e:
            if self.verbose:
                print(f"Error converting path to module: {e}")
            return None

    def profile_module(self, module_path: Path) -> Dict:
        elapsed, error = self.profile_import(module_path)
        
        result = {
            'module': str(module_path),
            'import_name': self._path_to_module(module_path),
            'time': elapsed,
            'time_ms': round(elapsed * 1000, 2),
            'error': error
        }
        
        self.results.append(result)
        self.total_time += elapsed
        
        return result

    def profile_directory(self, directory: Path, pattern: str = '*.py') -> None:
        modules = sorted(directory.rglob(pattern))
        
        print(f"Profiling {len(modules)} modules in {directory}")
        print("=" * 80)
        print()
        
        for module_path in modules:
            if '__pycache__' in str(module_path):
                continue
            
            result = self.profile_module(module_path)
            
            status = "✗ ERROR" if result['error'] else "✓"
            print(f"{status} {result['import_name']}: {result['time_ms']}ms")
            
            if result['error'] and self.verbose:
                print(f"   Error: {result['error']}")

    def generate_report(self, top_n: int = 20) -> str:
        sorted_results = sorted(self.results, key=lambda x: x['time'], reverse=True)
        
        report = []
        report.append("Import Performance Profile Report")
        report.append("=" * 80)
        report.append(f"Total modules: {len(self.results)}")
        report.append(f"Total import time: {round(self.total_time, 2)}s ({round(self.total_time * 1000, 2)}ms)")
        report.append(f"Average import time: {round(self.total_time / len(self.results) * 1000, 2)}ms")
        report.append()
        
        report.append(f"Top {top_n} Slowest Modules:")
        report.append("-" * 80)
        
        for i, result in enumerate(sorted_results[:top_n], 1):
            status = "ERROR" if result['error'] else "OK"
            report.append(f"{i:2}. {result['time_ms']:8.2f}ms [{status:5}] {result['import_name']}")
            if result['error']:
                report.append(f"    Error: {result['error']}")
        
        report.append()
        report.append("Modules with Errors:")
        report.append("-" * 80)
        
        error_modules = [r for r in self.results if r['error']]
        if error_modules:
            for result in error_modules:
                report.append(f"  - {result['import_name']}")
                report.append(f"    Error: {result['error']}")
        else:
            report.append("  None")
        
        report.append()
        report.append("Recommendations:")
        report.append("-" * 80)
        
        slow_modules = [r for r in sorted_results if r['time'] > 1.0 and not r['error']]
        if slow_modules:
            report.append("Consider lazy loading for these slow modules:")
            for result in slow_modules[:10]:
                report.append(f"  - {result['import_name']} ({result['time_ms']}ms)")
        else:
            report.append("  No modules taking >1s to import")
        
        return '\n'.join(report)

    def save_json(self, output_path: Path) -> None:
        data = {
            'total_modules': len(self.results),
            'total_time': self.total_time,
            'average_time': self.total_time / len(self.results) if self.results else 0,
            'results': sorted(self.results, key=lambda x: x['time'], reverse=True)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"JSON report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Profile module import performance')
    parser.add_argument('path', type=str, help='Path to module file or directory')
    parser.add_argument('--pattern', type=str, default='*.py', help='File pattern (for directories)')
    parser.add_argument('--top', type=int, default=20, help='Show top N slowest modules')
    parser.add_argument('--json', type=str, help='Save JSON report to file')
    parser.add_argument('--report', type=str, help='Save text report to file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)
    
    profiler = ImportProfiler(verbose=args.verbose)
    
    try:
        if path.is_file():
            result = profiler.profile_module(path)
            print(f"Import time: {result['time_ms']}ms")
            if result['error']:
                print(f"Error: {result['error']}")
        else:
            profiler.profile_directory(path, pattern=args.pattern)
        
        print()
        report = profiler.generate_report(top_n=args.top)
        print(report)
        
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nText report saved to: {args.report}")
        
        if args.json:
            profiler.save_json(Path(args.json))
    
    except KeyboardInterrupt:
        print("\n\nProfiling interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during profiling: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
