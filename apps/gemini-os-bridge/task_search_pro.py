import time
import sys
import pyperclip
import pyautogui
from src.capabilities import OSCapabilities

def perform_pro_search():
    os_cap = OSCapabilities()
    
    # Check if a query was passed as an argument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Breakthroughs in LLM local deployment optimization April 2024"
    
    # 1. Focus or Open Browser
    browsers = ["Firefox", "Chrome", "Edge", "Brave"]
    target_browser = None
    
    print("[1/6] Searching for browser...")
    for b in browsers:
        if os_cap.focus_window(b):
            target_browser = b
            break
    
    if not target_browser:
        print("    No browser found. Launching default browser...")
        os_cap.open_app("https://www.google.com")
        # Wait specifically for a browser window to appear
        if os_cap.wait_for_window("Google", timeout=20):
            target_browser = "Browser"
            print("    Browser launched and focused.")
        else:
            print("    Failed to detect browser window. Aborting.")
            return

    time.sleep(2)

    # 2. Prepare and Search
    print(f"[2/6] Executing search for: {query}")
    pyperclip.copy(query)
    pyautogui.hotkey('ctrl', 't')
    time.sleep(3)
    pyautogui.hotkey('ctrl', 'l') # Focus address bar to be safe
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    pyautogui.press('enter')

    # 3. Dynamic Load Wait
    print("[3/6] Waiting for results (polling content)...")
    content = ""
    for attempt in range(3):
        time.sleep(10) # Base wait for your laptop
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(1)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(2)
        content = pyperclip.paste()
        if len(content) > 500: # Heuristic for a loaded search page
            print(f"    Content detected (Length: {len(content)}). Proceeding.")
            break
        print(f"    Attempt {attempt+1}: Page might not be loaded. Retrying...")

    # 4. Final Extraction & Analysis
    print("[4/6] Data captured.")
    
    # 5. Cleanup: Close Tab
    print("[5/6] Cleaning up (closing search tab)...")
    os_cap.close_tab()
    time.sleep(1)

    # 6. Return Focus to Gemini CLI
    print("[6/6] Task complete. Returning to Gemini CLI.")
    os_cap.focus_terminal()

    # Final Output to CLI
    print("\n" + "="*50)
    print("PRO SEARCH RESULTS:")
    print("-" * 50)
    print(content[:1000] if len(content) > 0 else "Failed to capture content.")
    print("="*50)

if __name__ == "__main__":
    perform_pro_search()
