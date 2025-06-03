import langdetect
from googletrans import Translator

# Suppress langdetect warnings for short texts
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='langdetect')

# --- Test Mode Flag ---
TEST_MODE = True # Set to False for live translations
# --- End Test Mode Flag ---

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
        # In test mode, simulate translation without network call
        if any('\uAC00' <= char <= '\uD7A3' for char in text): # Basic check if it might be Korean
            return f"en_{text}" # Simulate English translation
        return text # Assume already English or non-translatable

    try:
        translator = Translator()
        translation = translator.translate(text, src='ko', dest='en')
        return translation.text
    except Exception as e:
        # print(f"Error translating '{text}' to English: {e}")
        return text # Return original text if translation fails

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
        # In test mode, simulate translation without network call
        # Simple check: if it doesn't have Korean chars, assume it's English or other
        if not any('\uAC00' <= char <= '\uD7A3' for char in text):
            return f"ko_{text}" # Simulate Korean translation
        return text # Assume already Korean or non-translatable

    try:
        translator = Translator()
        translation = translator.translate(text, src='en', dest='ko')
        return translation.text
    except Exception as e:
        # print(f"Error translating '{text}' to Korean: {e}")
        return text # Return original text if translation fails

if __name__ == "__main__":
    sample_korean = "안녕하세요"
    sample_english = "Hello"
    print(f"'{sample_korean}' is Korean: {is_korean(sample_korean)}")
    print(f"'{sample_english}' is Korean: {is_korean(sample_english)}")

    if is_korean(sample_korean):
        translated_en = translate_to_english(sample_korean)
        print(f"Korean to English: '{sample_korean}' -> '{translated_en}'")

    translated_ko = translate_to_korean(sample_english)
    print(f"English to Korean: '{sample_english}' -> '{translated_ko}'")

    # Test with a potentially problematic short string for langdetect
    short_text_korean = "이" # Korean character
    short_text_english = "A"

    print(f"'{short_text_korean}' is Korean: {is_korean(short_text_korean)}")
    if is_korean(short_text_korean):
            print(f"Korean to English: '{short_text_korean}' -> '{translate_to_english(short_text_korean)}'")

    print(f"'{short_text_english}' is Korean: {is_korean(short_text_english)}")
    if not is_korean(short_text_english):
            print(f"English to Korean: '{short_text_english}' -> '{translate_to_korean(short_text_english)}'")

    mixed_text_mostly_english = "Potion of Magic II" # Example from XML
    print(f"'{mixed_text_mostly_english}' is Korean: {is_korean(mixed_text_mostly_english)}")
    if is_korean(mixed_text_mostly_english):
            print(f"Korean to English: '{mixed_text_mostly_english}' -> '{translate_to_english(mixed_text_mostly_english)}'")
    else:
            print(f"Treating as English, to Korean: '{mixed_text_mostly_english}' -> '{translate_to_korean(mixed_text_mostly_english)}'")

    mixed_text_with_korean = "강화 크리스탈 - Slayer's Wrath II"
    print(f"'{mixed_text_with_korean}' is Korean: {is_korean(mixed_text_with_korean)}")
    if is_korean(mixed_text_with_korean):
            print(f"Korean to English: '{mixed_text_with_korean}' -> '{translate_to_english(mixed_text_with_korean)}'")
    else:
            print(f"Treating as English, to Korean: '{mixed_text_with_korean}' -> '{translate_to_korean(mixed_text_with_korean)}'")

    empty_string = ""
    print(f"'{empty_string}' is Korean: {is_korean(empty_string)}")
    print(f"Translate empty to English: '{translate_to_english(empty_string)}'")
    print(f"Translate empty to Korean: '{translate_to_korean(empty_string)}'")

    whitespace_string = "   "
    print(f"'{whitespace_string}' is Korean: {is_korean(whitespace_string)}")
    print(f"Translate whitespace to English: '{translate_to_english(whitespace_string)}'")
    print(f"Translate whitespace to Korean: '{translate_to_korean(whitespace_string)}'")
