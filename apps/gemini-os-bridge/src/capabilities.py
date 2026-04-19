import pyautogui
import pyperclip
import psutil
import pygetwindow as gw
from PIL import Image
import os
import time
from datetime import datetime

class OSCapabilities:
    def __init__(self, workspace_dir="context_storage"):
        self.workspace = workspace_dir
        if not os.path.exists(self.workspace):
            os.makedirs(self.workspace)
        pyautogui.FAILSAFE = True
        self._clipboard_backup = None

    def scrub_workspace(self):
        """Cleans up old screenshots to prevent context pollution."""
        for f in os.listdir(self.workspace):
            if f.endswith(".png") or f.endswith(".jpg"):
                try:
                    os.remove(os.path.join(self.workspace, f))
                except Exception:
                    pass
        print("    [System] Workspace scrubbed.")

    def __enter__(self):
        """Standard setup for a safe OS task session."""
        self.backup_clipboard()
        self.cleanup_save_dialogs()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures system state is restored regardless of task success."""
        self.restore_clipboard()
        self.focus_terminal()
        if exc_type:
            print(f"    [Guard] Task aborted due to error: {exc_val}")
            self.take_screenshot("fatal_error_state.png")
        return False # Propagate error

    def backup_clipboard(self):
        """Backs up the current clipboard content."""
        self._clipboard_backup = pyperclip.paste()

    def restore_clipboard(self):
        """Restores the backed-up clipboard content."""
        if self._clipboard_backup is not None:
            pyperclip.copy(self._clipboard_backup)

    def focus_window(self, title_substring):
        """Finds and focuses a window containing the title_substring."""
        try:
            windows = gw.getWindowsWithTitle(title_substring)
            if windows:
                win = windows[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                return True
        except Exception:
            pass
        return False

    def wait_for_window(self, title_substring, timeout=20):
        """Polls until a window with the title appears."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.focus_window(title_substring):
                return True
            time.sleep(1)
        return False

    def close_tab(self):
        """Closes the current browser tab."""
        pyautogui.hotkey('ctrl', 'w')
        return True

    def focus_terminal(self):
        """Attempts to find and focus the terminal running this script."""
        terminals = ["PowerShell", "Command Prompt", "cmd.exe", "Windows Terminal", "Gemini"]
        for t in terminals:
            if self.focus_window(t):
                return True
        return False

    def clean_text(self, text):
        """Removes noise, excessive whitespace, and non-informative lines."""
        import re
        if not text:
            return ""
        
        # Remove navigation noise lines (common in web captures)
        lines = text.split('\n')
        cleaned_lines = []
        noise_keywords = ["跳至主內容", "無障礙說明", "意見回饋", "Privacy", "Terms", "Sign in", "Log in"]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if any(keyword in line for keyword in noise_keywords):
                continue
            cleaned_lines.append(line)
            
        # Join and collapse multiple newlines
        content = "\n".join(cleaned_lines)
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content

    def cleanup_save_dialogs(self):
        """Finds and closes any lingering 'Save As' or '儲存圖片' windows."""
        save_titles = ["Save As", "另存新檔", "儲存圖片", "另存影像", "儲存檔案"]
        for title in gw.getAllTitles():
            if any(keyword in title for keyword in save_titles):
                try:
                    win = gw.getWindowsWithTitle(title)[0]
                    win.close()
                    print(f"    [Cleanup] Closed lingering dialog: {title}")
                except Exception:
                    pass
        return True

    def handle_save_as_dialog(self, target_path, timeout=15):
        """Waits for Save As dialog with expanded title support."""
        import time
        start = time.time()
        # Common titles for "Save As" across languages/browsers
        save_titles = ["Save As", "另存新檔", "儲存圖片", "另存影像", "儲存檔案"]
        
        print(f"    [Capability] Waiting for save dialog (Timeout: {timeout}s)...")
        while time.time() - start < timeout:
            all_windows = gw.getAllTitles()
            for title in all_windows:
                if any(keyword in title for keyword in save_titles):
                    print(f"    [Capability] Detected Dialog: {title}")
                    try:
                        win = gw.getWindowsWithTitle(title)[0]
                        win.activate()
                        time.sleep(1.5)
                        pyperclip.copy(target_path)
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(1)
                        pyautogui.press('enter')
                        return True
                    except Exception as e:
                        print(f"    [Capability] Error focusing dialog: {e}")
            time.sleep(1)
        
        # Diagnostic step: return currently open titles if failed
        return {"error": "Dialog not found", "open_titles": [t for t in gw.getAllTitles() if t]}

    def take_screenshot(self, filename=None):
        """Captures the current screen and saves it."""
        if filename is None:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(self.workspace, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        return path

    def get_clipboard(self):
        """Returns the current content of the clipboard."""
        return pyperclip.paste()

    def set_clipboard(self, text):
        """Sets the content of the clipboard."""
        pyperclip.copy(text)
        return True

    def cleanup_redundant_tabs(self, browser_title_part, task_keywords, max_tabs=20):
        """Cycles through tabs and closes those matching task_keywords if they are duplicates."""
        if not self.focus_window(browser_title_part):
            return "Browser not found"
        
        seen_titles = []
        closed_count = 0
        task_found_count = {} # Track how many times each task keyword is seen
        
        print(f"    [Cleanup] Starting tab scan (Max: {max_tabs})...")
        
        for _ in range(max_tabs):
            time.sleep(1)
            current_title = gw.getActiveWindowTitle()
            
            # Stop if we've cycled back to a title we've processed (or if title is empty)
            if not current_title or current_title in seen_titles:
                break
            
            is_task_tab = False
            for kw in task_keywords:
                if kw.lower() in current_title.lower():
                    task_found_count[kw] = task_found_count.get(kw, 0) + 1
                    # If this is the 2nd or more time we see this task topic, close it
                    if task_found_count[kw] > 1:
                        print(f"    [Cleanup] Closing redundant tab: {current_title}")
                        self.close_tab()
                        closed_count += 1
                        is_task_tab = True
                        break # Tab is closed, don't add to seen_titles yet
            
            if not is_task_tab:
                seen_titles.append(current_title)
                # Move to next tab
                pyautogui.hotkey('ctrl', 'tab')
        
        return {"scanned": len(seen_titles) + closed_count, "closed": closed_count}

    def get_all_window_titles(self):
        """Returns a list of all currently open window titles."""
        return [t for t in gw.getAllTitles() if t.strip()]

    def is_content_open(self, substring):
        """Checks if any open window title contains the substring."""
        titles = self.get_all_window_titles()
        return any(substring.lower() in t.lower() for t in titles)

    def list_active_windows(self):
        """Lists names of currently active/open windows (basic implementation)."""
        processes = []
        for proc in psutil.process_iter(['name']):
            try:
                processes.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return list(set(processes))

    def open_app(self, app_path_or_name):
        """Attempts to open an application."""
        try:
            os.startfile(app_path_or_name)
            return True
        except Exception as e:
            return str(e)

    def type_text(self, text, interval=0.01):
        """Simulates typing text."""
        pyautogui.write(text, interval=interval)
        return True

    def press_key(self, key):
        """Simulates a key press (e.g., 'enter', 'esc', 'ctrl')."""
        pyautogui.press(key)
        return True

    def move_mouse(self, x, y):
        """Moves the mouse to a specific coordinate."""
        pyautogui.moveTo(x, y)
        return True

    def scroll(self, amount):
        """Scrolls up (positive) or down (negative)."""
        pyautogui.scroll(amount)
        return True

    def click(self, x, y, clicks=1):
        """Clicks at a specific coordinate."""
        pyautogui.click(x, y, clicks=clicks)
        return True

    def click_image(self, template_path, confidence=0.8):
        """Finds an image on screen and clicks it (requires opencv-python)."""
        try:
            location = pyautogui.locateOnScreen(template_path, confidence=confidence)
            if location:
                pyautogui.click(location)
                return True
        except Exception as e:
            return str(e)
        return False

    def click_text(self, target_text, occurrence=1):
        """Finds text on screen and clicks its center coordinate."""
        import pytesseract
        from pytesseract import Output
        try:
            screenshot = pyautogui.screenshot()
            # Get detailed OCR data including bounding boxes
            data = pytesseract.image_to_data(screenshot, lang=OCR_LANG, output_type=Output.DICT)
            
            count = 0
            for i in range(len(data['text'])):
                if target_text.lower() in data['text'][i].lower():
                    count += 1
                    if count == occurrence:
                        # Calculate center of the text bounding box
                        x = data['left'][i] + data['width'][i] // 2
                        y = data['top'][i] + data['height'][i] // 2
                        print(f"    [Vision] Found '{target_text}' at ({x}, {y}). Clicking...")
                        pyautogui.click(x, y)
                        return True
            print(f"    [Vision] Text '{target_text}' not found on screen.")
            return False
        except Exception as e:
            return f"OCR Click Error: {str(e)}"

    def ocr_screenshot(self, region=None):
        """Extracts text from a screenshot or specific region (requires Tesseract)."""
        import pytesseract
        # Note: In Windows, you might need to specify the tesseract_cmd path
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        try:
            screenshot = pyautogui.screenshot(region=region)
            text = pytesseract.image_to_string(screenshot, lang='chi_tra+eng')
            return text
        except Exception as e:
            return f"OCR Error: {str(e)} (Ensure Tesseract-OCR is installed on OS)"

if __name__ == "__main__":
    os_cap = OSCapabilities()
    print("--- Gemini OS Bridge Initialized ---")
    print(f"Clipboard Content: {os_cap.get_clipboard()[:50]}...")
    # screenshot_path = os_cap.take_screenshot("test_init.png")
    # print(f"Test screenshot saved to: {screenshot_path}")
