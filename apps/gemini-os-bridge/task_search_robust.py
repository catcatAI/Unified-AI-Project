import time
import sys
import pyperclip
import pyautogui
from src.capabilities import OSCapabilities

def perform_robust_search():
    os_cap = OSCapabilities()
    
    query = "Latest developments in AI agentic workflows April 2024"
    
    # 1. Identify and focus browser
    browsers = ["Firefox", "Chrome", "Edge", "Brave"]
    target_browser = None
    
    print("Step 1: Searching for an open browser...")
    for b in browsers:
        if os_cap.focus_window(b):
            target_browser = b
            print(f"Focused: {target_browser}")
            break
    
    if not target_browser:
        print("Opening default browser to Google...")
        os_cap.open_app("https://www.google.com")
        time.sleep(8)
        os_cap.focus_window("Google")
    
    time.sleep(3)

    # 2. Prepare Query in Clipboard (Bypasses IME)
    print(f"Step 2: Copying query to clipboard: {query}")
    pyperclip.copy(query)
    time.sleep(1)

    # 3. Open new tab (Ctrl + T)
    print("Step 3: Opening new tab...")
    pyautogui.hotkey('ctrl', 't')
    time.sleep(4) # Wait for tab to be ready

    # 4. Paste and Enter
    print("Step 4: Pasting query and searching...")
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(2)
    pyautogui.press('enter')

    # 5. Wait for results (Extra long for performance)
    print("Step 5: Waiting for search results to load (15 seconds)...")
    time.sleep(15)

    # 6. Extract information
    print("Step 6: Extracting page content...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(2)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(3)
    
    content = pyperclip.paste()
    
    if len(content) < 100 or content.strip() == query:
        print("\n[!] WARNING: Captured content seems too short or identical to query.")
        print("The search might have failed or the page didn't load.")
    else:
        print("\n--- Task Complete ---")
        print("Summary of actual captured text (First 800 chars):")
        print("-" * 30)
        print(content[:800])
        print("-" * 30)

if __name__ == "__main__":
    perform_robust_search()
