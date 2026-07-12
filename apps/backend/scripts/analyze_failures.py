"""Analyze test failure results from latest_test_results.json."""

import json
import logging

logger = logging.getLogger(__name__)


def analyze_test_failures() -> None:
    """Read test results and print summary of failures/errors."""
    try:
        with open("latest_test_results.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error("latest_test_results.json not found")
        return
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in latest_test_results.json: %s", e)
        return

    print("Test Summary,")
    print(f"  Total:  {data['summary']['total']}")
    print(f"  Passed: {data['summary']['passed']}")
    print(f"  Skipped: {data['summary']['skipped']}")
    print(f"  Failed: {data['summary']['failed']}")
    print(f"  Errors: {data['summary']['error']}")

    failed_tests = []
    error_tests = []

    if "tests" in data:
        for test in data["tests"]:
            outcome = test.get("outcome")
            if outcome == "failed":
                failed_tests.append(test)
            elif outcome == "error":
                error_tests.append(test)

    print(f"\nFailed Tests ({len(failed_tests)})")
    for test in failed_tests:
        print(f"  - {test.get('nodeid', 'Unknown')}")

    print(f"\nError Tests ({len(error_tests)})")
    for test in error_tests:
        print(f"  - {test.get('nodeid', 'Unknown')}")


if __name__ == "__main__":
    analyze_test_failures()
