import time
import sys
import pyautogui
from src.capabilities import OSCapabilities

def capture_image_thumbnails():
    os_cap = OSCapabilities()
    query = "魔術師庫諾看得見一切 庫諾"
    # Direct Google Image Search URL
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
    
    try:
        print(f"[1/4] Launching Image Search: {search_url}")
        os_cap.open_app(search_url)
        
        # Wait for browser and images to load
        print("[2/4] Waiting for thumbnails to load (10 seconds)...")
        time.sleep(10)
        
        # Ensure browser is focused
        browsers = ["Firefox", "Chrome", "Edge"]
        for b in browsers:
            if os_cap.focus_window(b):
                break
        
        # 3. Capture a specific region (avoiding headers/ads if possible)
        # On a standard 1080p screen, the main results start around y=200
        print("[3/4] Capturing thumbnail grid...")
        screenshot_path = os_cap.take_screenshot("image_search_results.png")
        print(f"    Grid captured and saved to: {screenshot_path}")
        
    except Exception as e:
        print(f"[!] Error: {str(e)}")
    
    finally:
        print("[4/4] Returning to terminal.")
        os_cap.focus_terminal()

if __name__ == "__main__":
    capture_image_thumbnails()
