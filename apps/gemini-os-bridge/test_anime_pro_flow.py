import time
import os
import pyperclip
import pyautogui
from src.config import *
from src.capabilities import OSCapabilities
from src.runner import RobustTaskRunner

def anime_pro_mission():
    os_cap = OSCapabilities()
    runner = RobustTaskRunner()
    
    # Target Path for this mission
    save_path = os.path.join(CONTEXT_STORAGE, "kuno_final_mission.jpg")
    
    print("--- [Gemini OS] Mission: Anime High-Res Acquisition Start ---")
    
    try:
        # 1-3. Search & Content Verify
        query = "魔術師庫諾看得見一切 官方壁紙"
        print("[1/10] Starting web search...")
        raw_content = runner.run_web_search(query, focus_back=False)
        
        # 4. Image Search Mode
        print("[4/10] Navigating to Google Images...")
        img_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=isch"
        os_cap.open_app(img_url)
        time.sleep(BROWSER_LOAD_WAIT)
        
        # 5. Visual Focus
        print("[5/10] Focusing browser and selecting image...")
        os_cap.focus_window("Google")
        time.sleep(2)
        # Click a stable position for first result
        pyautogui.click(400, 400) 
        time.sleep(4)
        
        # 6. Interaction: Right-click
        print("[6/10] Invoking Context Menu...")
        # Target the expanded panel on the right
        pyautogui.rightClick(1000, 400)
        time.sleep(2)
        
        # 7. Action: Save As
        print("[7/10] Selecting 'Save Image As' (Key: v)...")
        pyautogui.press('v')
        time.sleep(3)
        
        # 8. Path Injection & Verify
        print(f"[8/10] Injecting project path: {save_path}")
        success = os_cap.handle_save_as_dialog(save_path)
        
        if success:
            print("    [Success] Path injected and saved.")
        else:
            print("    [Warning] Save dialog not detected in time.")
            os_cap.take_screenshot("mission_failure_dialog.png")

        # 9. Cleanup
        print("[9/10] Closing browser tab...")
        os_cap.close_tab()
        
        # 10. Final Focus & Report
        print("[10/10] Returning focus to Gemini CLI.")
        os_cap.focus_terminal()
        
        print("\n" + "="*50)
        print("MISSION COMPLETE: 'Kuno' Image acquired.")
        print(f"Location: {save_path}")
        print("="*50)

    except Exception as e:
        print(f"\n[!] Mission Failed: {str(e)}")
        os_cap.focus_terminal()

if __name__ == "__main__":
    anime_pro_mission()
