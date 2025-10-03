#!/usr/bin/env python3
"""
User Acceptance Test Script
Automated script to perform user acceptance testing for the Unified AI Project
"""

import sys
import time
import json
import subprocess
import requests
from pathlib import Path
# Add the backend src directory to the path
backend_src = Path(__file__).parent.parent / "apps" / "backend" / "src"
_ = sys.path.insert(0, str(backend_src))

class UserAcceptanceTest:
    """User Acceptance Test runner"""

    def __init__(self) -> None:
    self.base_url = "http://localhost:8000"
    self.api_endpoint = f"{self.base_url}/api"
    self.results = {
            "test_scenarios": [],
            "overall_status": "not_started",
            "start_time": None,
            "end_time": None,
            "issues": []
    }

    def log_result(self, scenario: str, status: str, details: str = "", execution_time: float = 0)
    """Log test result"""
    self.results["test_scenarios"].append({
            "scenario": scenario,
            "status": status,
            "details": details,
            "execution_time": execution_time,
            _ = "timestamp": time.time()
    })
    _ = print(f"[{status.upper()}] {scenario}: {details} (Time: {execution_time:.2f}s)")

    def log_issue(self, severity: str, description: str, scenario: str = "")
    """Log an issue found during testing"""
    issue = {
            "severity": severity,
            "description": description,
            "scenario": scenario,
            _ = "timestamp": time.time()
    }
    _ = self.results["issues"].append(issue)
    _ = print(f"[ISSUE-{severity.upper()}] {description}")

    def check_system_health(self) -> bool:
        """Check if the system is running and healthy""":
    try:

    response = requests.get(f"{self.api_endpoint}/health", timeout=10)
            if response.status_code == 200:

    data = response.json()
                return data.get("status") == "healthy"
            return False
        except Exception as e:

            _ = self.log_issue("high", f"System health check failed: {e}")
            return False

    def test_creative_writing(self) -> bool:
    """Test creative writing functionality"""
    start_time = time.time()
        try:
            # Test health check first
            if not self.check_system_health()

    _ = self.log_result("Creative Writing", "failed", "System not healthy", time.time() - start_time)
                return False

            # Submit a creative writing task
            payload = {
                "task": "Write a short story about a robot learning to paint",
                "parameters": {
                    "style": "sci-fi",
                    "length": "short"
                }
            }

            response = requests.post(
                f"{self.api_endpoint}/agents/creative-writing-agent/task",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:


    data = response.json()
                task_id = data.get("task_id")
                if task_id:
                    # Check task status
                    time.sleep(2)  # Wait a moment for processing
    status_response = requests.get(
                        f"{self.api_endpoint}/agents/creative-writing-agent/task/{task_id}",
                        timeout=30
                    )

                    if status_response.status_code == 200:


    status_data = status_response.json()
                        if status_data.get("status") in ["completed", "submitted"]:

    execution_time = time.time() - start_time
                            _ = self.log_result("Creative Writing", "passed", "Successfully generated content", execution_time)
                            return True
                        else:

                            _ = self.log_result("Creative Writing", "failed", f"Task status: {status_data.get('status')}", time.time() - start_time)
                            return False
                    else:

                        _ = self.log_result("Creative Writing", "failed", f"Status check failed: {status_response.status_code}", time.time() - start_time)
                        return False
                else:

                    _ = self.log_result("Creative Writing", "failed", "No task ID returned", time.time() - start_time)
                    return False
            else:

                _ = self.log_result("Creative Writing", "failed", f"Task submission failed: {response.status_code}", time.time() - start_time)
                return False

        except Exception as e:


            execution_time = time.time() - start_time
            _ = self.log_result("Creative Writing", "failed", f"Exception: {e}", execution_time)
            _ = self.log_issue("medium", f"Creative writing test failed: {e}", "Creative Writing")
            return False

    def test_image_generation(self) -> bool:
    """Test image generation functionality"""
    start_time = time.time()
        try:
            # Test health check first
            if not self.check_system_health()

    _ = self.log_result("Image Generation", "failed", "System not healthy", time.time() - start_time)
                return False

            # Submit an image generation task
            payload = {
                "task": "A futuristic cityscape at sunset with flying cars",
                "parameters": {
                    "size": "256x256"
                }
            }

            response = requests.post(
                f"{self.api_endpoint}/agents/image-generation-agent/task",
                json=payload,
                timeout=60  # Longer timeout for image generation
            )

            if response.status_code == 200:


    data = response.json()
                task_id = data.get("task_id")
                if task_id:
                    # Check task status
                    time.sleep(5)  # Wait longer for image generation
    status_response = requests.get(
                        f"{self.api_endpoint}/agents/image-generation-agent/task/{task_id}",
                        timeout=30
                    )

                    if status_response.status_code == 200:


    status_data = status_response.json()
                        if status_data.get("status") in ["completed", "submitted"]:

    execution_time = time.time() - start_time
                            _ = self.log_result("Image Generation", "passed", "Successfully generated image", execution_time)
                            return True
                        else:

                            _ = self.log_result("Image Generation", "failed", f"Task status: {status_data.get('status')}", time.time() - start_time)
                            return False
                    else:

                        _ = self.log_result("Image Generation", "failed", f"Status check failed: {status_response.status_code}", time.time() - start_time)
                        return False
                else:

                    _ = self.log_result("Image Generation", "failed", "No task ID returned", time.time() - start_time)
                    return False
            else:

                _ = self.log_result("Image Generation", "failed", f"Task submission failed: {response.status_code}", time.time() - start_time)
                return False

        except Exception as e:


            execution_time = time.time() - start_time
            _ = self.log_result("Image Generation", "failed", f"Exception: {e}", execution_time)
            _ = self.log_issue("medium", f"Image generation test failed: {e}", "Image Generation")
            return False

    def test_web_search(self) -> bool:
    """Test web search functionality"""
    start_time = time.time()
        try:
            # Test health check first
            if not self.check_system_health()

    _ = self.log_result("Web Search", "failed", "System not healthy", time.time() - start_time)
                return False

            # Submit a web search task
            payload = {
                "task": "Latest developments in artificial intelligence 2025",
                "parameters": {}
            }

            response = requests.post(
                f"{self.api_endpoint}/agents/web-search-agent/task",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:


    data = response.json()
                task_id = data.get("task_id")
                if task_id:
                    # Check task status
                    time.sleep(3)  # Wait for search to complete
    status_response = requests.get(
                        f"{self.api_endpoint}/agents/web-search-agent/task/{task_id}",
                        timeout=30
                    )

                    if status_response.status_code == 200:


    status_data = status_response.json()
                        if status_data.get("status") in ["completed", "submitted"]:

    execution_time = time.time() - start_time
                            _ = self.log_result("Web Search", "passed", "Successfully performed web search", execution_time)
                            return True
                        else:

                            _ = self.log_result("Web Search", "failed", f"Task status: {status_data.get('status')}", time.time() - start_time)
                            return False
                    else:

                        _ = self.log_result("Web Search", "failed", f"Status check failed: {status_response.status_code}", time.time() - start_time)
                        return False
                else:

                    _ = self.log_result("Web Search", "failed", "No task ID returned", time.time() - start_time)
                    return False
            else:

                _ = self.log_result("Web Search", "failed", f"Task submission failed: {response.status_code}", time.time() - start_time)
                return False

        except Exception as e:


            execution_time = time.time() - start_time
            _ = self.log_result("Web Search", "failed", f"Exception: {e}", execution_time)
            _ = self.log_issue("medium", f"Web search test failed: {e}", "Web Search")
            return False

    def test_cli_tools(self) -> bool:
    """Test CLI tools functionality"""
    start_time = time.time()
        try:
            # Test health check command
            result = subprocess.run(
                ["python", "-m", "cli.commands.main", "health"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:


    execution_time = time.time() - start_time
                _ = self.log_result("CLI Tools", "passed", "Health check command successful", execution_time)
                return True
            else:

                execution_time = time.time() - start_time
                _ = self.log_result("CLI Tools", "failed", f"Health check failed: {result.stderr}", execution_time)
                _ = self.log_issue("low", f"CLI health check failed: {result.stderr}", "CLI Tools")
                return False

        except subprocess.TimeoutExpired:


            execution_time = time.time() - start_time
            _ = self.log_result("CLI Tools", "failed", "Command timed out", execution_time)
            _ = self.log_issue("medium", "CLI health check timed out", "CLI Tools")
            return False
        except Exception as e:

            execution_time = time.time() - start_time
            _ = self.log_result("CLI Tools", "failed", f"Exception: {e}", execution_time)
            _ = self.log_issue("medium", f"CLI tools test failed: {e}", "CLI Tools")
            return False

    def test_system_monitoring(self) -> bool:
    """Test system monitoring functionality"""
    start_time = time.time()
        try:
            # Test health check first
            if not self.check_system_health()

    _ = self.log_result("System Monitoring", "failed", "System not healthy", time.time() - start_time)
                return False

            # Get system metrics
            response = requests.get(f"{self.api_endpoint}/monitoring/metrics", timeout=10)

            if response.status_code == 200:


    data = response.json()
                if "cpu_usage" in data and "memory_usage" in data:

    execution_time = time.time() - start_time
                    _ = self.log_result("System Monitoring", "passed", "Successfully retrieved system metrics", execution_time)
                    return True
                else:

                    _ = self.log_result("System Monitoring", "failed", "Incomplete metrics data", time.time() - start_time)
                    return False
            else:

                _ = self.log_result("System Monitoring", "failed", f"Metrics retrieval failed: {response.status_code}", time.time() - start_time)
                return False

        except Exception as e:


            execution_time = time.time() - start_time
            _ = self.log_result("System Monitoring", "failed", f"Exception: {e}", execution_time)
            _ = self.log_issue("medium", f"System monitoring test failed: {e}", "System Monitoring")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
    """Run all user acceptance tests"""
    _ = print("Starting User Acceptance Tests...")
    print("=" * 50)

    self.results["start_time"] = time.time()

    # Test scenarios in order of dependency
    test_scenarios = [
            _ = ("System Health", self.check_system_health),
            _ = ("Creative Writing", self.test_creative_writing),
            _ = ("Image Generation", self.test_image_generation),
            _ = ("Web Search", self.test_web_search),
            _ = ("CLI Tools", self.test_cli_tools),
            _ = ("System Monitoring", self.test_system_monitoring)
    ]

    passed_tests = 0
    total_tests = len(test_scenarios)

        for scenario_name, test_func in test_scenarios:


    _ = print(f"\nRunning {scenario_name} test...")
            try:

                result = test_func()
                if result:

    passed_tests += 1
            except Exception as e:

                _ = self.log_issue("high", f"Test {scenario_name} crashed: {e}", scenario_name)
                _ = print(f"[ERROR] {scenario_name} test crashed: {e}")

    self.results["end_time"] = time.time()

    # Calculate overall status
        if passed_tests == total_tests:

    self.results["overall_status"] = "passed"
        elif passed_tests >= total_tests * 0.8:

    self.results["overall_status"] = "partially_passed"
        else:

            self.results["overall_status"] = "failed"

    # Print summary
    print("\n" + "=" * 50)
    _ = print("USER ACCEPTANCE TEST SUMMARY")
    print("=" * 50)
    _ = print(f"Tests Passed: {passed_tests}/{total_tests}")
    _ = print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    _ = print(f"Overall Status: {self.results['overall_status'].upper()}")
    _ = print(f"Total Execution Time: {self.results['end_time'] - self.results['start_time']:.2f}s")

        if self.results["issues"]:


    _ = print(f"\nIssues Found: {len(self.results['issues'])}")
            for issue in self.results["issues"]:

    _ = print(f"  - [{issue['severity'].upper()}] {issue['description']}")

    return self.results

    def save_results(self, filename: str = "uat_results.json")
    """Save test results to file"""
    results_file = Path(__file__).parent.parent / "reports" / filename
    results_file.parent.mkdir(exist_ok=True)

    # Convert to JSON-serializable format
    serializable_results = self._make_serializable(self.results)

    with open(results_file, 'w', encoding='utf-8') as f:
    json.dump(serializable_results, f, indent=2, ensure_ascii=False)

    _ = print(f"\nResults saved to: {results_file}")

    def _make_serializable(self, obj)
    """Convert object to JSON-serializable format"""
        if isinstance(obj, dict)

    return {key: self._make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list)

    return [self._make_serializable(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool)) or obj is None:

    return obj
        else:

            return str(obj)

def main() -> None:
    """Main function"""
    # Check if system is running
    print("Checking if system is running...")
    try:

    response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code != 200:

    _ = print("ERROR: System is not running. Please start the development environment first.")
            _ = print("Run: unified-ai.bat -> Start Development -> Start Full Development Environment")
            _ = sys.exit(1)
    except requests.exceptions.ConnectionError:

    _ = print("ERROR: Cannot connect to system. Please start the development environment first.")
    _ = print("Run: unified-ai.bat -> Start Development -> Start Full Development Environment")
    _ = sys.exit(1)
    except Exception as e:

    _ = print(f"ERROR: Unexpected error checking system status: {e}")
    _ = sys.exit(1)

    # Run tests
    tester = UserAcceptanceTest()
    results = tester.run_all_tests()
    _ = tester.save_results()

    # Exit with appropriate code
    if results["overall_status"] == "passed":

    _ = print("\n🎉 All user acceptance tests passed!")
    _ = sys.exit(0)
    elif results["overall_status"] == "partially_passed":

    _ = print("\n⚠️  Some tests passed, but issues were found. Please review results.")
    _ = sys.exit(1)
    else:

    _ = print("\n❌ User acceptance tests failed. Please review results and fix issues.")
    _ = sys.exit(1)

if __name__ == "__main__":


    _ = main()