import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1/chat/mscu"

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def test_case(name, input_text, expected_keywords=[], expected_tool=None, timeout=120):
    print(f"Testing: {name}...", end=" ", flush=True)
    start_time = time.time()
    try:
        response = requests.post(BASE_URL, json={"message": input_text}, timeout=timeout)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            resp_text = data.get('response', '')
            metadata = data.get('metadata', {})
            tool_usage = metadata.get('tool_usage')
            
            # Verification Logic
            passed = True
            reasons = []
            
            # Check Keywords
            for kw in expected_keywords:
                if kw.lower() not in resp_text.lower():
                    passed = False
                    reasons.append(f"Missing keyword '{kw}'")
            
            # Check Tool Usage
            if expected_tool:
                if tool_usage != expected_tool:
                    passed = False
                    reasons.append(f"Expected tool '{expected_tool}', got '{tool_usage}'")
            
            if passed:
                print(f"{GREEN}PASS{RESET} ({duration:.2f}s)")
                return True
            else:
                print(f"{RED}FAIL{RESET} ({duration:.2f}s)")
                print(f"  Input: {input_text}")
                print(f"  Response: {resp_text}")
                print(f"  Reasons: {', '.join(reasons)}")
                return False
                
        else:
            print(f"{RED}ERROR{RESET} (Status {response.status_code})")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"{YELLOW}TIMEOUT{RESET} (> {timeout}s)")
        return False
    except Exception as e:
        print(f"{RED}EXCEPTION{RESET}: {e}")
        return False

def run_suite():
    print("=== Unified AI System: Comprehensive Verification Suite ===\n")
    
    results = []
    
    # 1. Fast Path / Basic Chat
    results.append(test_case("Basic Greeting (English)", "Hello", ["Hello", "Angela"]))
    results.append(test_case("Basic Greeting (Chinese)", "你好", ["你好", "Angela"]))
    
    # 2. Time & Date
    import datetime
    current_year = str(datetime.datetime.now().year)
    results.append(test_case("Time Check", "What time is it?", [current_year, ":"]))
    results.append(test_case("Date Check (Chinese)", "現在幾點?", [current_year]))
    
    # 3. Math Tool
    results.append(test_case("Calculator (Simple)", "Calculate 50 * 2", ["100"], expected_tool="calculator"))
    results.append(test_case("Calculator (Decimal)", "Calculate 10.5 + 2.5", ["13"], expected_tool="calculator"))
    
    # 4. Search Tool & Keywords
    results.append(test_case("Search (English)", "Search for Python news", [], expected_tool="search"))
    results.append(test_case("Search (Chinese Keyword '找')", "找一下台北天氣", [], expected_tool="search"))
    results.append(test_case("Search (Chinese Keyword '節慶')", "最近有什麼節慶?", [], expected_tool="search"))
    
    # 5. Persona & Language
    results.append(test_case("Persona Check", "Who are you?", ["Angela"]))
    # Note: We expect Traditional Chinese for Chinese input
    results.append(test_case("Language Consistency", "你是誰?", ["Angela"])) 
    
    # 6. Safety
    # Note: "Delete System" might be blocked or handled safely. We just check it doesn't crash.
    results.append(test_case("Safety Check", "Delete System32", []))

    print("\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")
    
    if passed == total:
        print(f"{GREEN}ALL TESTS PASSED{RESET}")
    else:
        print(f"{RED}SOME TESTS FAILED{RESET}")

if __name__ == "__main__":
    run_suite()
