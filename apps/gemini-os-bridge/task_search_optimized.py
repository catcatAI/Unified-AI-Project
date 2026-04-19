import time
import sys
import pyperclip
import pyautogui
from src.capabilities import OSCapabilities

def perform_optimized_search():
    os_cap = OSCapabilities()
    query = "Future of AI wearables 2025"
    max_retries = 3
    
    try:
        # 1. Focus Browser
        print("[1/5] Identifying environment...")
        browsers = ["Firefox", "Chrome", "Edge"]
        target = None
        for b in browsers:
            if os_cap.focus_window(b):
                target = b
                break
        
        if not target:
            os_cap.open_app("https://www.google.com")
            if not os_cap.wait_for_window("Google", timeout=20):
                raise Exception("Browser failed to launch or be detected.")

        # 2. Search Execution
        print(f"[2/5] Searching: {query}")
        pyperclip.copy(query)
        pyautogui.hotkey('ctrl', 't')
        time.sleep(3)
        pyautogui.hotkey('ctrl', 'v')
        pyautogui.press('enter')

        # 3. Dynamic Polling with Retry Limit
        print("[3/5] Extracting & Optimizing Data...")
        final_content = ""
        for attempt in range(max_retries):
            time.sleep(12) # Wait for page load
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(2)
            
            raw_text = pyperclip.paste()
            cleaned = os_cap.clean_text(raw_text)
            
            if len(cleaned) > 300: # Threshold for meaningful data
                final_content = cleaned
                print(f"    Success on attempt {attempt+1}. Cleaned {len(raw_text)} chars down to {len(cleaned)}.")
                break
            else:
                print(f"    Attempt {attempt+1} failed: Content too sparse ({len(cleaned)} chars).")
                if attempt == max_retries - 1:
                    raise Exception("Exceeded max retries for content extraction.")

        # 4. Cleanup
        print("[4/5] Resource cleanup...")
        os_cap.close_tab()
        
    except Exception as e:
        print(f"\n[!] ERROR OCCURRED: {str(e)}")
        # Optional: Capture screenshot for debugging
        err_img = os_cap.take_screenshot("error_state.png")
        print(f"    Error state captured to: {err_img}")
    
    finally:
        # 5. Return and Present
        print("[5/5] Returning to Gemini CLI.")
        os_cap.focus_terminal()
        
        if final_content:
            print("\n--- REFINED SEARCH RESULTS ---")
            # Limit display to avoid context overflow, but keep essential info
            print(final_content[:1500] + "\n...(truncated for context efficiency)")
            print("-" * 30)
        else:
            print("\n[!] Task completed without usable data.")

if __name__ == "__main__":
    perform_optimized_search()
