import langdetect
from deep_translator import GoogleTranslator
import json # Added for caching
import os   # Added for cache file path

# Suppress langdetect warnings for short texts
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='langdetect')

# --- Test Mode Flag ---
TEST_MODE = True # Set to False for live translations
# --- End Test Mode Flag ---

# --- Translation Cache ---
CACHE_FILE = os.path.join(os.path.dirname(__file__), "translation_cache.json")
translation_cache = {}
# --- End Translation Cache ---

def load_translation_cache():
    """Loads the translation cache from CACHE_FILE if it exists."""
    global translation_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                translation_cache = json.load(f)
            # print(f"Translation cache loaded from {CACHE_FILE}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # print(f"Error loading cache file: {e}. Starting with an empty cache.")
            translation_cache = {}
    else:
        # print("Cache file not found. Starting with an empty cache.")
        translation_cache = {}

def save_translation_cache():
    """Saves the current translation_cache to CACHE_FILE."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(translation_cache, f, ensure_ascii=False, indent=2)
        # print(f"Translation cache saved to {CACHE_FILE}")
    except IOError as e:
        print(f"Error saving cache file: {e}")

def is_korean(text: str) -> bool:
    """
    Checks if the given text is Korean.
    More robustly checks for presence of Korean Unicode characters first,
    then falls back to langdetect for non-obvious cases if text is long enough.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return False

    # Primary check: Presence of Korean Unicode characters
    if any('\uAC00' <= char <= '\uD7A3' for char in text):
        return True

    # Fallback for text without obvious Korean characters but might still be Korean (e.g., mixed language)
    # Only use langdetect if text is substantial enough for it to be effective.
    # This avoids langdetect errors/misclassifications on very short non-Korean strings.
    if len(text.strip()) >= 3: # Arbitrary threshold, can be adjusted
        try:
            return langdetect.detect(text) == 'ko'
        except langdetect.lang_detect_exception.LangDetectException:
            # Langdetect failed (e.g., text too ambiguous or short in its context)
            return False
        except Exception:
            # Catch any other unexpected errors during detection
            return False

    return False # Default if no Korean characters and text is too short for langdetect

def translate_to_english(text: str) -> str:
    """
    Translates Korean text to English.

    Args:
        text (str): The Korean text to translate.

    Returns:
        str: The translated English text, or the original text if translation fails.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return text

    if TEST_MODE:
        if any('\uAC00' <= char <= '\uD7A3' for char in text):
            return f"en_{text}"
        return text

    # Live translation with caching
    stripped_text = text.strip()
    if not stripped_text:
        return text # Return original for empty or whitespace-only strings

    cache_key = f"ko_en:{stripped_text}" # Language-specific key
    if cache_key in translation_cache:
        # print(f"Cache hit for '{stripped_text}' (ko->en)")
        return translation_cache[cache_key]

    # print(f"Cache miss for '{stripped_text}' (ko->en). Calling API.")
    try:
        translated = GoogleTranslator(source='ko', target='en').translate(stripped_text)
        if translated: # Ensure translation is not None or empty
            translation_cache[cache_key] = translated
            save_translation_cache()
            return translated
        return text # Return original if translation result is empty
    except Exception as e:
        print(f"Error translating '{text}' to English using deep-translator: {e}")
        return text

def translate_to_korean(text: str) -> str:
    """
    Translates English text to Korean.

    Args:
        text (str): The English text to translate.

    Returns:
        str: The translated Korean text, or the original text if translation fails.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return text

    if TEST_MODE:
        if not any('\uAC00' <= char <= '\uD7A3' for char in text):
            return f"ko_{text}"
        return text

    # Live translation with caching
    stripped_text = text.strip()
    if not stripped_text:
        return text # Return original for empty or whitespace-only strings

    cache_key = f"en_ko:{stripped_text}" # Language-specific key
    if cache_key in translation_cache:
        # print(f"Cache hit for '{stripped_text}' (en->ko)")
        return translation_cache[cache_key]

    # print(f"Cache miss for '{stripped_text}' (en->ko). Calling API.")
    try:
        translated = GoogleTranslator(source='en', target='ko').translate(stripped_text)
        if translated: # Ensure translation is not None or empty
            translation_cache[cache_key] = translated
            save_translation_cache()
            return translated
        return text # Return original if translation result is empty
    except Exception as e:
        print(f"Error translating '{text}' to Korean using deep-translator: {e}")
        return text

# Initial load of the cache when the module is imported
load_translation_cache()

if __name__ == "__main__":
    # --- Original Test Mode Tests ---
    print("--- Running Original Test Mode Checks ---")
    sample_korean = "안녕하세요"
    sample_english = "Hello"
    print(f"'{sample_korean}' is Korean: {is_korean(sample_korean)}")
    print(f"'{sample_english}' is Korean: {is_korean(sample_english)}")

    if is_korean(sample_korean):
        translated_en = translate_to_english(sample_korean)
        print(f"Korean to English (TEST_MODE): '{sample_korean}' -> '{translated_en}'")

    translated_ko = translate_to_korean(sample_english)
    print(f"English to Korean (TEST_MODE): '{sample_english}' -> '{translated_ko}'")
    print("--- Finished Original Test Mode Checks ---\n")

    # --- Testing Live Translation & Caching ---
    # Ensure TEST_MODE = False for this specific test block, then revert
    original_test_mode_for_caching_test = TEST_MODE # Use global directly
    TEST_MODE = False # Use global directly
    print(f"--- Temporarily setting TEST_MODE to: {TEST_MODE} for Caching Test ---")

    # Clear cache for a clean test if file exists
    if os.path.exists(CACHE_FILE):
        print(f"Removing existing cache file: {CACHE_FILE}")
        os.remove(CACHE_FILE)
    load_translation_cache() # Reload empty cache

    print("\n--- Testing Live Translation & Caching ---")
    korean_text_live = "안녕하세요" # A common Korean greeting
    english_text_live = "Hello, world!"

    print(f"Translating '{korean_text_live}' to English (1st time, live):")
    translated1_en = translate_to_english(korean_text_live)
    print(f"Result: {translated1_en}")

    print(f"Translating '{korean_text_live}' to English (2nd time, should be cached):")
    translated2_en = translate_to_english(korean_text_live)
    print(f"Result: {translated2_en}")
    if translated1_en and translated1_en != f"en_{korean_text_live}": # Check if live translation likely occurred
      assert translated1_en == translated2_en

    print(f"\nTranslating '{english_text_live}' to Korean (1st time, live):")
    translated1_ko = translate_to_korean(english_text_live)
    print(f"Result: {translated1_ko}")

    print(f"Translating '{english_text_live}' to Korean (2nd time, should be cached):")
    translated2_ko = translate_to_korean(english_text_live)
    print(f"Result: {translated2_ko}")
    if translated1_ko and translated1_ko != f"ko_{english_text_live}": # Check if live translation likely occurred
      assert translated1_ko == translated2_ko

    if os.path.exists(CACHE_FILE):
        print(f"\nCache file '{CACHE_FILE}' created/updated.")
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                print("Cache content:")
                print(f.read())
        except Exception as e:
            print(f"Error reading cache file for display: {e}")
    else:
        print(f"\nCache file '{CACHE_FILE}' NOT created (problem).")

    # Revert TEST_MODE to its original state for other potential imports/tests
    TEST_MODE = original_test_mode_for_caching_test # Use global directly
    print(f"--- TEST_MODE reverted to: {TEST_MODE} ---")
