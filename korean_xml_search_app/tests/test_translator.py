import unittest
import sys
import os

# Adjust sys.path to allow imports from the 'src' directory
# This assumes 'tests' is a subdirectory of the project root, and 'src' is another subdirectory.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from translator import is_korean, translate_to_english, translate_to_korean
import translator as translator_module

# Ensure TEST_MODE is active for all tests in this module
translator_module.TEST_MODE = True

class TestTranslator(unittest.TestCase):

    def test_is_korean(self):
        self.assertTrue(is_korean("안녕하세요")) # Korean
        self.assertTrue(is_korean("테스트")) # Korean
        self.assertFalse(is_korean("Hello")) # English
        self.assertFalse(is_korean("Test123")) # English + Numbers
        self.assertTrue(is_korean("테스트 Test")) # Mixed with Korean
        self.assertFalse(is_korean("これは日本語です")) # Japanese
        self.assertFalse(is_korean("")) # Empty string
        self.assertFalse(is_korean("   ")) # Whitespace
        self.assertFalse(is_korean(None)) # None input
        self.assertTrue(is_korean("이")) # Short Korean text
        self.assertFalse(is_korean("A")) # Short English text

    def test_translate_to_english_test_mode(self):
        self.assertEqual(translate_to_english("안녕하세요"), "en_안녕하세요")
        self.assertEqual(translate_to_english("테스트 아이템"), "en_테스트 아이템")
        # Non-Korean text should ideally remain unchanged or follow a specific test mode logic
        self.assertEqual(translate_to_english("Hello"), "Hello") # Assuming it returns original if not detected as Korean
        self.assertEqual(translate_to_english(""), "")
        self.assertEqual(translate_to_english("   "), "   ")
        self.assertEqual(translate_to_english(None), None)


    def test_translate_to_korean_test_mode(self):
        self.assertEqual(translate_to_korean("Hello"), "ko_Hello")
        self.assertEqual(translate_to_korean("Test Item"), "ko_Test Item")
        # Korean text should ideally remain unchanged
        self.assertEqual(translate_to_korean("안녕하세요"), "안녕하세요") # Assuming it returns original if detected as Korean
        self.assertEqual(translate_to_korean(""), "")
        self.assertEqual(translate_to_korean("   "), "   ")
        self.assertEqual(translate_to_korean(None), None)

if __name__ == '__main__':
    unittest.main()
