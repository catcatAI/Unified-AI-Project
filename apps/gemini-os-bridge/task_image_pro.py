import time
import sys
import pyautogui
import pygetwindow as gw
from src.capabilities import OSCapabilities

def pro_image_acquisition():
    os_cap = OSCapabilities()
    
    try:
        print("[1/6] Finding and Activating Browser...")
        target_browser = None
        browsers = ["Firefox", "Chrome", "Edge", "Brave"]
        
        # Robust activation loop
        for b in browsers:
            wins = gw.getWindowsWithTitle(b)
            if wins:
                win = wins[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(3) # Wait for OS to switch focus
                target_browser = win
                print(f"    Active Window: {win.title}")
                break
        
        if not target_browser:
            print("    [!] ERROR: No browser window detected.")
            return

        # 2. Get window dimensions for dynamic clicking
        left, top, width, height = target_browser.left, target_browser.top, target_browser.width, target_browser.height
        print(f"[2/6] Window Geometry: {width}x{height} at ({left}, {top})")

        # 3. Scroll Down
        print("[3/6] Scrolling down...")
        # Move mouse to center of browser first to ensure scroll hits the right area
        center_x = left + (width // 2)
        center_y = top + (height // 2)
        pyautogui.moveTo(center_x, center_y)
        time.sleep(1)
        os_cap.scroll(-800) 
        time.sleep(6) # Wait for images to load on slow performance laptop

        # 4. Precision Click (Dynamic)
        # Target an area where thumbnails usually reside (middle-left area of the window)
        target_x = left + (width // 3)
        target_y = top + (height // 2)
        print(f"[4/6] Clicking dynamic target at ({target_x}, {target_y})...")
        pyautogui.click(target_x, target_y)
        time.sleep(6) # Wait for expansion

        # 5. Verification
        print("[5/6] Capturing verification...")
        verify_path = os_cap.take_screenshot("final_verification.png")
        print(f"    Verification saved: {verify_path}")

    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("[6/6] Returning to terminal.")
        os_cap.focus_terminal()

if __name__ == "__main__":
    pro_image_acquisition()
