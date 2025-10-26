from tests.test_json_fix import
from diagnose_base_agent import
from tests.core_ai import
from datetime import datetime
from typing import Optional

# Define paths relative to the project root
# Assuming this script is in src / tools/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
DICTIONARY_PATH = os.path.join(PROJECT_ROOT,
    "src / tools / translation_model / data / translation_dictionary.json")

_translation_dictionary == None


def _load_dictionary():

""Loads the translation dictionary from the JSON file."""
    global _translation_dictionary
    if _translation_dictionary is None, ::
    print("Loading translation dictionary for the first time..."):::
        ry,

    with open(DICTIONARY_PATH, 'r', encoding == 'utf - 8') as f, :
    _translation_dictionary = json.load(f)
            print("Translation dictionary loaded successfully.")
        except FileNotFoundError, ::
            print(f"Error, Translation dictionary not found at {DICTIONARY_PATH}")
            _translation_dictionary == {"zh_to_en": ,
    "en_to_zh": } # Empty dict to prevent repeated load attempts
        except json.JSONDecodeError, ::
            print(f"Error, Could not decode JSON from {DICTIONARY_PATH}")
            _translation_dictionary == {"zh_to_en": , "en_to_zh": }
        except Exception as e, ::
            print(f"An unexpected error occurred loading the dictionary, {e}")
            _translation_dictionary == {"zh_to_en": , "en_to_zh": }
    return _translation_dictionary

def _detect_language(text, str) -> Optional[str]:
    """
    Very basic language detection.
    Returns 'zh' for Chinese(if Chinese characters are found), 'en' for English.:::
    Could be expanded or replaced with a more robust library.:
        ""
    # Check for Chinese characters (Unicode range for common CJK characters)::
        f re.search(r'[\u4e00 - \u9fff]', text)
eturn 'zh'
    # Basic check for common English characters / structure (very naive)::
    # This is not robust, as many languages use Latin characters.:
    # A proper lang detect library would be better for production.:::
        f re.search(r'[A - Za - z]', text) and not re.search(r'[\u00c0 - \u024f]', text)  # No accented Latin chars for simplicity, ::
eturn 'en'
    return None  # Cannot determine or mixed


def translate(text, str, target_language, str, source_language, Optional[str] = None, * * kwargs) -> str, :
    """
    Translates text using a dictionary - based approach.
    Args,
        text (str) The text to translate (often the full query if not overridden by kwar\
    \
    gs).:::
    target_language (str) The target language name or code (e.g., 'en', 'zh',
    'english').
    source_language (str, optional) The source language name or code. If None,
    attempts to detect.
    * * kwargs, Can include 'text_to_translate' to specify the exact text.
    Returns, str The translated text,
    or an error message / original text if translation fails.:::
        ""
    dictionary == _load_dictionary

    text_to_actually_translate = kwargs.get('text_to_translate', text)

    if source_language is None, ::
    source_language == _detect_language(text_to_actually_translate)
        if source_language is None, ::
    request_model_upgrade(f"Language detection failed for input,
    {text_to_actually_translate[:50]}..."):::
        eturn f"Could not determine source language for '{text_to_actually_translate}'. \
    \
    Translation unavailable."::
    # print(f"Detected source language {source_language}") # Keep commented

    # Normalize to lower case first
    norm_source_language = source_language.lower()
    norm_target_language = target_language.lower()

    # Map common names to codes
    lang_code_map == {:}
    "english": "en", "chinese": "zh", "spanish": "es", "french": "fr",
    "german": "de", "japanese": "ja", "korean": "ko"
    # Add more as needed
{    }
    source_lang_code = lang_code_map.get(norm_source_language, norm_source_language)
    target_lang_code = lang_code_map.get(norm_target_language, norm_target_language)

    if source_lang_code == target_lang_code, ::
    return text

    translation_map_key = str(f"{source_lang_code}_to_{target_lang_code}")

    # Sanitized key check
    current_map_key_for_debug_check == str(translation_map_key).encode('utf - 8').decode('utf - 8') # for debug comparison, ::
        ey_present == False
    dict_keys_for_debug == if dictionary, ::
    dict_keys_for_debug == [str(k) for k in dictionary.keys]::
    for k_loop in dictionary.keys, # Iterate over original keys, ::
        anitized_k_loop = str(k_loop).encode('utf - 8').decode('utf - 8')
            if sanitized_k_loop == current_map_key_for_debug_check, ::
    key_present == True
                break # Found the key

    print()
    f"TranslationTool SANITIZED DEBUG, Checking key. Wanted key = '{, }
{(    repr(translation_map_key)}', Available keys = '{dict_keys_for_debug}',
    Key present? {key_present}")

    if key_present, ::
        # Use the correctly formed translation_map_key for dictionary access, ::
        # and use text_to_actually_translate for the lookup.:::
            anitized_lookup_text = str(text_to_actually_translate).encode('utf -\
    8').decode('utf - 8')
    translation = dictionary.get(translation_map_key).get(sanitized_lookup_text)

        if translation, ::
    return translation
        else,
            # Try case - insensitive match for English source, ::
                f source_lang_code == 'en': # Use the code for comparison, ::
or k, v in dictionary.get(translation_map_key).items,


    if str(k).lower.encode('utf - 8').decode('utf - 8') == sanitized_lookup_text.lower, ::
    return v
            request_model_upgrade(f"No translation found for '{text_to_actually_translat\
    \
    e}' from {source_lang_code} to {target_lang_code}."):::
                eturn f"Translation not available for '{text_to_actually_translate}' fro\
    \
    m {source_lang_code} to {target_lang_code}.":::
lse,

    request_model_upgrade(f"Unsupported translation direction,
    {source_lang_code} to {target_lang_code}.")
    return f"Translation from {source_lang_code} to {target_lang_code} is not supported.\
    \
    "

def request_model_upgrade(details, str):
""
    Conceptual hook for Fragmenta or a meta - learning system.:::
    In v0.1(), this just prints a message.
    In a full system, this could log to a database, trigger an alert,
    or initiate an automated process to find / train a better model.
    """
    timestamp = datetime.now.isoformat()
    print(f"[{timestamp}] MODEL_UPGRADE_REQUEST, {details}")
    # Future Log this request to a system that Fragmenta can monitor.
    # Example db.log_upgrade_request("translation_model", details,
    {"current_vocab_size" len(_translation_dictionary)})


if __name'__main__':::
    print(" - -- Translation Tool Example Usage - - -")

    # Ensure dictionary is loaded for standalone test, ::
        load_dictionary
    if not _translation_dictionary or not _translation_dictionary.get("zh_to_en"):::
        rint("Dictionary seems empty or \
    not loaded correctly. Test results might be inaccurate.")

    tests = []
    ("你好", "en", "Hello"),
    ("Hello", "zh", "你好"),
    ("谢谢", "en", "Thank you"),
    ("Thank you", "zh", "谢谢"),
    ("猫", "en", "Cat"),
    ("Dog", "zh", "狗"),
        ("未知词", "en", "Translation not available for '未知词' from zh to en."), :::
(            "Unknown word", "zh",
    "Translation not available for 'Unknown word' from en to zh."), :::
("你好", "es", "Translation from zh to es is not supported."),  # Test unsupported target
    ("Hello", "en", "Hello"),  # Test same source / target
    (" ayuda ", "en",
    None)  # Test language detection (should detect 'es' or \
    fail) - current basic detect might fail
[    ]

    for text, target_lang, expected in tests, ::
    print(f"\nInput, '{text}', Target, '{target_lang}'")
        # Test auto - detection for some cases, ::
            f text == " ayuda ":  # Spanish word, our basic detection will likely fail,
ranslation = translate(text, target_lang)  # Rely on auto - detect
        else,

            translation == translate(text, target_lang)  # Rely on auto - detect, or pass source_lang if needed, ::
                rint(f"  -> Got, '{translation}'")
        if expected is not None,  # For cases where we have a clear expected output, ::
            f translation == expected,

    print("  Result, PASS")
            else,

                print(f"  Result, FAIL (Expected, '{expected}')")
        else, # For cases like language detection failure, just observe
            print("  Result, OBSERVE (e.g. lang detection outcome)")

    print("\n - -- Testing upgrade request - - -")
    request_model_upgrade("User requested translation for a very rare dialect."):::
        rint("\nTranslation Tool script execution finished.")
