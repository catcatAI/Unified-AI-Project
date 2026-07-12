"""
Angela AI - Unified Profiling Entry Point
Provides a single command to run various profiling modes.
"""

import argparse
import cProfile
import pstats
import sys
from pathlib import Path
from io import StringIO


def profile_imports():
    """Profile import times."""
    print("Profiling imports...")
    import importlib
    import time

    modules = [
        "ai.ed3n.ed3n_engine",
        "ai.garden.garden_engine",
        "ai.context.dialogue_context",
        "ai.agents.agent_orchestrator",
        "ai.reasoning.planning_engine",
        "security.content_filter",
        "security.safety_audit",
    ]

    results = []
    for module_name in modules:
        start = time.time()
        try:
            importlib.import_module(module_name)
            elapsed = time.time() - start
            results.append((module_name, elapsed, "OK"))
        except Exception as e:
            elapsed = time.time() - start
            results.append((module_name, elapsed, f"ERROR: {e}"))

    print("\nImport Times:")
    print("-" * 60)
    for name, elapsed, status in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"{name:50} {elapsed:6.3f}s  {status}")

    return results


def profile_function(func, *args, **kwargs):
    """Profile a specific function."""
    profiler = cProfile.Profile()
    profiler.enable()

    result = func(*args, **kwargs)

    profiler.disable()

    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(20)

    print(stream.getvalue())
    return result


def profile_memory():
    """Profile memory usage."""
    try:
        import tracemalloc

        tracemalloc.start()

        # Import key modules
        import importlib

        modules = [
            "ai.ed3n.ed3n_engine",
            "ai.garden.garden_engine",
            "ai.context.dialogue_context",
        ]

        for module_name in modules:
            try:
                importlib.import_module(module_name)
            except Exception:
                pass

        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        print("\nMemory Usage (top 10):")
        print("-" * 60)
        for stat in top_stats[:10]:
            print(stat)

        tracemalloc.stop()
        return True

    except ImportError:
        print("tracemalloc not available")
        return False


def main():
    parser = argparse.ArgumentParser(description="Angela AI Profiler")
    parser.add_argument(
        "mode",
        choices=["imports", "memory", "function"],
        help="Profiling mode",
    )
    parser.add_argument("--function", help="Function to profile (for function mode)")

    args = parser.parse_args()

    if args.mode == "imports":
        profile_imports()
    elif args.mode == "memory":
        profile_memory()
    elif args.mode == "function":
        if not args.function:
            print("Error: --function required for function mode")
            sys.exit(1)
        print(f"Profiling function: {args.function}")
        # This would need to be extended for actual use


if __name__ == "__main__":
    main()
