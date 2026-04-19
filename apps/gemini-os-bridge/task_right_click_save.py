import time
import sys
import pyautogui
import pygetwindow as gw
from src.capabilities import OSCapabilities

def pro_right_click_acquisition():
    os_cap = OSCapabilities()
    
    try:
        print("[1/6] Restoring Browser to Image Search...")
        # Re-open the specific search to be sure we are on the right page
        query = "魔術師庫諾看得見一切 庫諾"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
        os_cap.open_app(search_url)
        time.sleep(8)

        # 2. Get window dimensions
        wins = gw.getWindowsWithTitle("Google")
        if not wins:
            print("    [!] ERROR: Browser not found.")
            return
        win = wins[0]
        win.activate()
        left, top, width, height = win.left, win.top, win.width, win.height

        # 3. Click a thumbnail to open the side panel
        # Target: Middle of the first row
        thumb_x = left + (width // 4)
        thumb_y = top + (height // 2)
        print(f"[2/6] Clicking thumbnail at ({thumb_x}, {thumb_y})...")
        pyautogui.click(thumb_x, thumb_y)
        time.sleep(5) # Wait for side panel

        # 4. Right-click on the expanded image in the side panel
        # Usually, the expansion panel is on the right half of the screen
        panel_img_x = left + int(width * 0.75)
        panel_img_y = top + (height // 2)
        print(f"[3/6] Right-clicking expanded image at ({panel_img_x}, {panel_img_y})...")
        pyautogui.rightClick(panel_img_x, panel_img_y)
        time.sleep(2)

        # 5. Select "Save image as..." 
        # In most browsers, 'v' is the shortcut for "Save image as" in the context menu
        print("[4/6] Sending 'v' to save image...")
        pyautogui.press('v')
        time.sleep(3)

        # 6. Handle the Save As Dialog (Basic ENTER to save in default folder)
        print("[5/6] Confirming Save As dialog...")
        pyautogui.press('enter')
        time.sleep(3)
        
        # 7. Final Verification Screenshot
        print("[6/6] Verification...")
        os_cap.take_screenshot("right_click_save_result.png")
        
    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
    
    finally:
        os_cap.focus_terminal()

if __name__ == "__main__":
    pro_right_click_acquisition()
