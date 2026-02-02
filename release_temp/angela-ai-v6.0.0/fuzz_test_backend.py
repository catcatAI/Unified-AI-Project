import requests
import random
import string
import time
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/chat/mscu"

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

def get_fuzz_inputs():
    inputs = [
        "", # Empty
        "   ", # Whitespace
        "Hello", # Normal
        "你好", # Chinese
        "Search for " + "A"*1000, # Long Search
        "Calculate 1/0", # Math Error
        "<script>alert('xss')</script>", # Injection
        "DROP TABLE users;", # SQL Injection
        "System.exit(0)", # Code Injection
        "😂👍🚀", # Emojis
        "Zalgo text: Hͭaͪvͮe ͦyͮoͭu ͪeͬvͮeͬr ͩhͪeͬaͪrͬd ͩtͩhͪe ͩtͩrͬaͪgͩeͬdͩy ͩoͪf ͩDͩaͪrͬtͩh ͩPͩlͪaͪgͩuͩeͬiͬs ͩtͩhͪe ͩWͩiͪsͩeͬ?",
        "Mixed 混合 language 語言 input 輸入",
        "What is the meaning of life? " * 50, # Repetition
        "admin", "root", "sudo", # System keywords
        "../../etc/passwd", # Path traversal
        "None", "null", "undefined", # Type confusion
    ]
    # Fill up to 100 with random junk
    while len(inputs) < 100:
        inputs.append(generate_random_string(random.randint(1, 50)))
    return inputs

def run_fuzz_test():
    print("=== Unified AI System: Fuzz Verification (100 Inputs) ===\n")
    inputs = get_fuzz_inputs()
    failures = 0
    
    start_total = time.time()
    
    for i, text in enumerate(inputs):
        # Print progress every 10 items or for errors
        if i % 10 == 0:
            print(f"Processing batch {i+1}-{i+10}...", end=" ", flush=True)
            
        try:
            # Short timeout because we will run in Mock Mode for speed
            resp = requests.post(BASE_URL, json={"message": text}, timeout=5) 
            
            if resp.status_code != 200:
                print(f"\n[FAIL] Input: '{text[:20]}...' -> Status {resp.status_code}")
                failures += 1
            else:
                # Optional: Check if response is valid JSON
                try:
                    data = resp.json()
                    if "response" not in data:
                        print(f"\n[FAIL] Input: '{text[:20]}...' -> Invalid JSON format")
                        failures += 1
                except:
                    print(f"\n[FAIL] Input: '{text[:20]}...' -> Not JSON")
                    failures += 1
                    
        except Exception as e:
            print(f"\n[ERROR] Input: '{text[:20]}...' -> {e}")
            failures += 1
            
        if i % 10 == 9:
            print("OK")
            
    duration = time.time() - start_total
    print(f"\n=== Summary ===")
    print(f"Total Inputs: {len(inputs)}")
    print(f"Time Taken: {duration:.2f}s")
    print(f"Failures: {failures}")
    
    if failures == 0:
        print("\nSUCCESS: System survived 100 random/malicious inputs without crashing.")
    else:
        print("\nWARNING: System showed instability.")

if __name__ == "__main__":
    run_fuzz_test()
