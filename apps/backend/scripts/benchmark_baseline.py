"""
Angela AI - Benchmark Baseline Runner
Runs key benchmarks and saves results as baseline.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime


def run_benchmark(name, func, iterations=100):
    """Run a benchmark and return results."""
    times = []

    for _ in range(iterations):
        start = time.time()
        try:
            func()
        except Exception as e:
            return {"name": name, "error": str(e)}
        elapsed = time.time() - start
        times.append(elapsed)

    return {
        "name": name,
        "iterations": iterations,
        "min_time": min(times),
        "max_time": max(times),
        "avg_time": sum(times) / len(times),
        "p50_time": sorted(times)[len(times) // 2],
        "p95_time": sorted(times)[int(len(times) * 0.95)],
        "p99_time": sorted(times)[int(len(times) * 0.99)],
    }


def benchmark_ed3n():
    """Benchmark ED3N engine."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend" / "src"))
        from ai.ed3n.ed3n_engine import ED3NEngine

        engine = ED3NEngine()

        def run():
            engine.process({"input": "test input", "context": {}})

        return run_benchmark("ED3N Process", run)
    except Exception as e:
        return {"name": "ED3N Process", "error": str(e)}


def benchmark_garden():
    """Benchmark GARDEN engine."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend" / "src"))
        from ai.garden.garden_engine import GARDENEngine

        engine = GARDENEngine()

        def run():
            engine.process({"input": "test input", "context": {}})

        return run_benchmark("GARDEN Process", run)
    except Exception as e:
        return {"name": "GARDEN Process", "error": str(e)}


def benchmark_classifier():
    """Benchmark classifier."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend" / "src"))
        from ai.core.classifier import QueryClassifier

        classifier = QueryClassifier()

        def run():
            classifier.classify("What is the weather?")

        return run_benchmark("Classifier", run)
    except Exception as e:
        return {"name": "Classifier", "error": str(e)}


def main():
    print("Running benchmarks...")
    print("=" * 60)

    results = []

    # Run benchmarks
    benchmarks = [
        ("ED3N", benchmark_ed3n),
        ("GARDEN", benchmark_garden),
        ("Classifier", benchmark_classifier),
    ]

    for name, func in benchmarks:
        print(f"Running {name} benchmark...")
        result = func()
        results.append(result)
        if "error" in result:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Avg: {result['avg_time']*1000:.2f}ms")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "benchmarks": results,
    }

    output_path = Path(".benchmarks/baseline.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nBaseline saved to: {output_path}")


if __name__ == "__main__":
    main()
