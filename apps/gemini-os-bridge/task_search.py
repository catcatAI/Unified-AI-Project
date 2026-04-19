import time
import sys
from src.capabilities import OSCapabilities

def perform_search_task():
    os_cap = OSCapabilities()
    
    # 1. Identify and focus browser
    browsers = ["Chrome", "Edge", "Firefox", "Brave"]
    target_browser = None
    
    print("Searching for an open browser...")
    for b in browsers:
        if os_cap.focus_window(b):
            target_browser = b
            print(f"Found and focused: {target_browser}")
            break
    
    if not target_browser:
        print("No open browser found. Attempting to open default browser...")
        os_cap.open_app("https://www.google.com")
        time.sleep(5) # Wait for browser to open
        target_browser = "Browser" # Generic fallback

    # Give it a moment to settle
    time.sleep(2)

    # 2. Open new tab (Ctrl + T)
    print("Opening new tab...")
    os_cap.press_key('ctrl') # PyAutoGUI hold is better but press works for simple shortcuts
    import pyautogui
    pyautogui.hotkey('ctrl', 't')
    time.sleep(2)

    # 3. Type search query
    # What I want to know: "Latest developments in AI agentic workflows 2024"
    query = "Latest developments in AI agentic workflows 2024"
    print(f"Typing query: {query}")
    os_cap.type_text(query, interval=0.1) # Slow typing for performance
    time.sleep(1)
    os_cap.press_key('enter')

    # 4. Wait for results (as requested, long interval)
    print("Waiting for search results to load (10 seconds)...")
    time.sleep(10)

    # 5. Extract information
    # We'll use the 'Select All' and 'Copy' trick to get page content
    print("Extracting page content...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(2)
    
    content = os_cap.get_clipboard()
    
    print("\n--- Task Complete ---")
    print("Summary of results (First 500 chars):")
    print(content[:500])

if __name__ == "__main__":
    perform_search_task()
