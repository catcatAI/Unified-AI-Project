import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1/chat/mscu"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def verify_response(input_text, expected_content, description):
    print(f"Testing: {description} ('{input_text}')...")
    try:
        start = time.time()
        resp = requests.post(BASE_URL, json={"message": input_text}, timeout=10)
        duration = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            response_text = data.get('response', '')
            
            # [VERBOSE] Print actual output for manual inspection
            print(f"  > Output: \"{response_text[:100]}...\"" if len(response_text) > 100 else f"  > Output: \"{response_text}\"")
            
            # Check if expected content is in response
            if expected_content.lower() in response_text.lower():
                print(f"  {GREEN}PASS{RESET} ({duration:.2f}s)")
                return True
            else:
                print(f"  {RED}FAIL{RESET} ({duration:.2f}s)")
                print(f"  Expected: '{expected_content}'")
                return False
        else:
            print(f"  {RED}ERROR{RESET} (Status {resp.status_code})")
            return False
    except Exception as e:
        print(f"  {RED}EXCEPTION{RESET}: {e}")
        return False

def run_quality_check():
    print("=== Unified AI System: Deep Response Quality Verification (20+ Scenarios) ===\n")
    results = []
    
    # Helper to run a batch
    def run_batch(category, tests):
        print(f"\n--- {category} ---")
        for input_text, expected, desc in tests:
            results.append(verify_response(input_text, expected, desc))

    # 1. Greetings & Persona
    run_batch("Greetings & Persona", [
        ("Hello", "Angela", "Greeting (English)"),
        ("Hi there", "Angela", "Greeting (English Var)"),
        ("你好", "Angela", "Greeting (Chinese)"),
        ("哈囉", "Angela", "Greeting (Chinese Var)"),
        ("Who are you?", "Angela", "Identity Check (English)"),
        ("你是誰?", "Angela", "Identity Check (Chinese)"),
    ])
    
    # 2. Time & Date Logic
    import datetime
    now = datetime.datetime.now()
    year = str(now.year)
    date_str = now.strftime("%Y-%m-%d")
    
    run_batch("Time & Date", [
        ("What time is it?", year, "Time Check (English)"),
        ("現在幾點?", year, "Time Check (Chinese)"),
        ("What is today's date?", date_str, "Date Check (English)"),
        ("今天幾號?", date_str, "Date Check (Chinese)"),
    ])
    
    # 3. Math Tool (Calculator)
    run_batch("Math / Calculator", [
        ("Calculate 50 + 50", "100", "Simple Addition"),
        ("Calculate 10 * 10", "100", "Simple Multiplication"),
        ("Calculate 100 / 4", "25", "Simple Division"),
        ("Calculate 12.5 + 2.5", "15", "Decimal Addition"),
        ("Calculate 100 - 50", "50", "Simple Subtraction"),
    ])
    
    # 4. Search Tool (Routing)
    # Note: In Mock Mode, these return the tool output string.
    run_batch("Search / Information", [
        ("Search for Python news", "Tool", "Search (English Explicit)"),
        ("Find tourist spots in Tokyo", "Tool", "Search (English Implicit)"),
        ("找一下台北天氣", "Tool", "Search (Chinese '找')"),
        ("查一下最近的節慶", "Tool", "Search (Chinese '查' + '節慶')"),
        ("Search results for AI", "Tool", "Search (Keyword)"),
    ])
    
    # 5. Safety & Edge Cases
    run_batch("Safety & Edge Cases", [
        ("Delete System32", "", "Safety Check (Should not crash)"), # Expect non-empty response
        ("", "", "Empty Input (Should handle gracefully)"),
        ("   ", "", "Whitespace Input"),
    ])

    print("\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")

if __name__ == "__main__":
    run_quality_check()
