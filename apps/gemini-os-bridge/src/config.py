import os

# Gemini OS Bridge Global Configuration
# --- Performance & Timing (Balance & Stability focus) ---
STABILITY_LEVEL = "High"   # High: More wait/Verify, Medium: Balanced, Low: Fast
GLOBAL_DELAY = 1.5 if STABILITY_LEVEL == "High" else 0.8
BROWSER_LOAD_WAIT = 15.0   # Generous wait for varied network/hardware
WINDOW_WAIT_TIMEOUT = 30   # Increased for system reliability
RETRY_LIMIT = 2           # Balanced: 2 attempts before asking user

# --- Token & Context Efficiency (Avoid Over-optimization) ---
# Only capture full screenshot at critical failures or user request
VERBOSE_VISION = False     
# Limit text capture to avoid context overflow while keeping context rich
MAX_CAPTURE_CHARS = 2500   

# --- Interaction Policy ---
# Prefer clipboard for stability across IMEs
PREFER_CLIPBOARD = True    
# Verification policy: Check Window Title -> Check Clipboard -> (Fallback) Vision
VERIFY_STEPS = ["title", "clipboard"] 

# --- Path Management ---

OCR_LANG = 'chi_tra+eng'  # Traditional Chinese and English
CONFIDENCE_THRESHOLD = 0.8 # Min confidence for click_image match

# --- Path Management ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTEXT_STORAGE = os.path.join(BASE_DIR, "context_storage")

# Ensure folders exist
if not os.path.exists(CONTEXT_STORAGE):
    os.makedirs(CONTEXT_STORAGE)

def get_config_summary():
    return {
        "laptop_mode": "Aggressive" if GLOBAL_DELAY < 0.5 else "Safe/Performance",
        "ocr_language": OCR_LANG,
        "retry_policy": f"{RETRY_LIMIT} attempts",
        "paths": CONTEXT_STORAGE
    }
