import time
import pyperclip
import pyautogui
from src.config import *
from src.capabilities import OSCapabilities

class RobustTaskRunner:
    def __init__(self):
        self.os_cap = OSCapabilities()

    def run_web_search(self, query, focus_back=True):
        """
        Executes a web search with state awareness and multi-layered verification.
        """
        try:
            print(f"[Runner] Task: Web Search for '{query}'")

            # 0. Cleanup and State Check
            self.os_cap.cleanup_save_dialogs()

            # Check if we already have a window related to this query
            if self.os_cap.is_content_open(query.split()[0]): # Check for first keyword
                print(f"[Runner] Detected existing window for '{query}'. Focusing instead of opening new.")
                self.os_cap.focus_window(query.split()[0])
                time.sleep(GLOBAL_DELAY)
            else:
                # 1. Focus Browser
                browsers = ["Firefox", "Chrome", "Edge", "Brave"]
                target = None
                for b in browsers:
                    if self.os_cap.focus_window(b):
                        target = b
                        break

                if not target:
                    self.os_cap.open_app("https://www.google.com")
                    self.os_cap.wait_for_window("Google", timeout=WINDOW_WAIT_TIMEOUT)

                # 2. Search
                pyperclip.copy(query)
                pyautogui.hotkey('ctrl', 't')
                time.sleep(GLOBAL_DELAY * 2)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(GLOBAL_DELAY)
                pyautogui.press('enter')

            # 3. Layered Verification
 (Dynamic wait)
            print(f"[Runner] Waiting {BROWSER_LOAD_WAIT}s for stability...")
            time.sleep(BROWSER_LOAD_WAIT)
            
            # Action: Capture content
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(GLOBAL_DELAY)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(GLOBAL_DELAY * 2)
            
            final_content = pyperclip.paste()
            
            # Check if content changed/loaded
            if len(final_content) < 500 or final_content == query:
                print("[Runner] Primary verification failed. Attempting vision check...")
                err_path = self.os_cap.take_screenshot("search_verification_fail.png")
                raise Exception(f"Stability check failed: Content too short. Proof: {err_path}")

            # 4. Success & Cleanup
            print(f"[Runner] Search successful (Captured {len(final_content)} chars). Cleaning up...")
            self.os_cap.close_tab()
            
            if focus_back:
                self.os_cap.focus_terminal()
            
            return self.os_cap.clean_text(final_content)[:MAX_CAPTURE_CHARS]

        except Exception as e:
            print(f"[Runner] FATAL ERROR: {str(e)}")
            if focus_back:
                self.os_cap.focus_terminal()
            return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test run
    runner = RobustTaskRunner()
    result = runner.run_web_search("Current status of Gemini CLI OS integration")
    print(f"\nFinal Result Preview:\n{result[:500]}...")
