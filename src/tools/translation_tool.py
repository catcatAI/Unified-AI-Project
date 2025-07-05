import json
import os
import re
from datetime import datetime

# Define paths relative to the project root
# Assuming this script is in src/tools/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DICTIONARY_PATH = os.path.join(PROJECT_ROOT, "src/tools/translation_model/data/translation_dictionary.json")

_translation_dictionary = None

def _load_dictionary():
    """Loads the translation dictionary from the JSON file."""
    global _translation_dictionary
    if _translation_dictionary is None:
        print("Loading translation dictionary for the first time...")
        try:
            with open(DICTIONARY_PATH, 'r', encoding='utf-8') as f:
                _translation_dictionary = json.load(f)
            print("Translation dictionary loaded successfully.")
        except FileNotFoundError:
            print(f"Error: Translation dictionary not found at {DICTIONARY_PATH}")
            _translation_dictionary = {"zh_to_en": {}, "en_to_zh": {}} # Empty dict to prevent repeated load attempts
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {DICTIONARY_PATH}")
            _translation_dictionary = {"zh_to_en": {}, "en_to_zh": {}}
        except Exception as e:
            print(f"An unexpected error occurred loading the dictionary: {e}")
            _translation_dictionary = {"zh_to_en": {}, "en_to_zh": {}}
    return _translation_dictionary

def _detect_language(text: str) -> str | None:
    """
    Very basic language detection.
    Returns 'zh' for Chinese (if Chinese characters are found), 'en' for English.
    Could be expanded or replaced with a more robust library.
    """
    # Check for Chinese characters (Unicode range for common CJK characters)
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    # Basic check for common English characters / structure (very naive)
    # This is not robust, as many languages use Latin characters.
    # A proper lang detect library would be better for production.
    if re.search(r'[A-Za-z]', text) and not re.search(r'[\u00c0-\u024f]', text): # No accented Latin chars for simplicity
        return 'en'
    return None # Cannot determine or mixed

def translate(text: str, target_language: str, source_language: str = None) -> str:
    """
    Translates text using a dictionary-based approach.
    Args:
        text (str): The text to translate.
        target_language (str): The target language code (e.g., 'en', 'zh').
        source_language (str, optional): The source language code. If None, attempts to detect.
    Returns:
        str: The translated text, or an error message/original text if translation fails.
    """
    dictionary = _load_dictionary()

    if source_language is None:
        source_language = _detect_language(text)
        if source_language is None:
            request_model_upgrade(f"Language detection failed for input: {text[:50]}...")
            return f"Could not determine source language for '{text}'. Translation unavailable."
        print(f"Detected source language: {source_language}")

    source_language = source_language.lower()
    target_language = target_language.lower()

    if source_language == target_language:
        return text # No translation needed

    translation_map_key = f"{source_language}_to_{target_language}" # e.g., "zh_to_en"

    if translation_map_key in dictionary:
        translation = dictionary[translation_map_key].get(text)
        if translation:
            return translation
        else:
            # Try case-insensitive match for English source
            if source_language == 'en':
                for k, v in dictionary[translation_map_key].items():
                    if k.lower() == text.lower():
                        return v
            request_model_upgrade(f"No translation found for '{text}' from {source_language} to {target_language}.")
            return f"Translation not available for '{text}' from {source_language} to {target_language}."
    else:
        request_model_upgrade(f"Unsupported translation direction: {source_language} to {target_language}.")
        return f"Translation from {source_language} to {target_language} is not supported."

def request_model_upgrade(details: str):
    """
    Conceptual hook for Fragmenta or a meta-learning system.
    In v0.1, this just prints a message.
    In a full system, this could log to a database, trigger an alert,
    or initiate an automated process to find/train a better model.
    """
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] MODEL_UPGRADE_REQUEST: {details}")
    # Future: Log this request to a system that Fragmenta can monitor.
    # Example: db.log_upgrade_request("translation_model", details, {"current_vocab_size": len(_translation_dictionary)})

if __name__ == '__main__':
    print("--- Translation Tool Example Usage ---")

    # Ensure dictionary is loaded for standalone test
    _load_dictionary()
    if not _translation_dictionary or not _translation_dictionary.get("zh_to_en"):
         print("Dictionary seems empty or not loaded correctly. Test results might be inaccurate.")


    tests = [
        ("你好", "en", "Hello"),
        ("Hello", "zh", "你好"),
        ("谢谢", "en", "Thank you"),
        ("Thank you", "zh", "谢谢"),
        ("猫", "en", "Cat"),
        ("Dog", "zh", "狗"),
        ("未知词", "en", "Translation not available for '未知词' from zh to en."),
        ("Unknown word", "zh", "Translation not available for 'Unknown word' from en to zh."),
        ("你好", "es", "Translation from zh to es is not supported."), # Test unsupported target
        ("Hello", "en", "Hello"), # Test same source/target
        (" ayuda ", "en", None) # Test language detection (should detect 'es' or fail) - current basic detect might fail
    ]

    for text, target_lang, expected in tests:
        print(f"\nInput: '{text}', Target: '{target_lang}'")
        # Test auto-detection for some cases
        if text == " ayuda ": # Spanish word, our basic detection will likely fail
            translation = translate(text, target_lang) # Rely on auto-detect
        else:
            translation = translate(text, target_lang) # Rely on auto-detect, or pass source_lang if needed

        print(f"  -> Got: '{translation}'")
        if expected is not None: # For cases where we have a clear expected output
            if translation == expected:
                print("  Result: PASS")
            else:
                print(f"  Result: FAIL (Expected: '{expected}')")
        else: # For cases like language detection failure, just observe
            print("  Result: OBSERVE (e.g. lang detection outcome)")

    print("\n--- Testing upgrade request ---")
    request_model_upgrade("User requested translation for a very rare dialect.")

    print("\nTranslation Tool script execution finished.")
