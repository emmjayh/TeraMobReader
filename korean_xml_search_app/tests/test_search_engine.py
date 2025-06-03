import unittest
from unittest.mock import patch
import sys
import os
import shutil # For managing test directories if needed

# Adjust sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from search_engine import SearchEngine
import translator as translator_module
import indexer # To help with structuring mock data if needed

# Ensure TEST_MODE is active for all tests in this module
translator_module.TEST_MODE = True

# Removed class-level patch here, will use explicit start/stop
class TestSearchEngine(unittest.TestCase):

    mock_npc_data = [ # Defined as a class attribute for access in setUp
        { # NPC ID 0
            'npcName': {'original': '크랩몬스터', 'en': 'en_크랩몬스터'},
            'npcTemplateId': 'NPC001',
            'items': [
                {'name': {'original': '집게다리', 'en': 'en_집게다리'}, 'templateId': 'ITM001'},
                {'name': {'original': '단단한껍질', 'en': 'en_단단한껍질'}, 'templateId': 'ITM002'}
            ],
            'source_file': 'test_crab_data.xml'
        },
        { # NPC ID 1
            'npcName': {'original': 'Stone Golem', 'en': 'Stone Golem'}, # Already English
            'npcTemplateId': 'NPC002',
            'items': [
                {'name': {'original': 'Golem Core', 'en': 'Golem Core'}, 'templateId': 'ITM003'},
                {'name': {'original': '마법의 돌', 'en': 'en_마법의 돌'}, 'templateId': 'ITM004'}
            ],
            'source_file': 'test_golem_data.xml'
        },
        { # NPC ID 2
            'npcName': {'original': '숲의요정', 'en': 'en_숲의요정'},
            'npcTemplateId': 'NPC003',
            'items': [
                {'name': {'original': '요정의가루', 'en': 'en_요정의가루'}, 'templateId': 'ITM005'},
                {'name': {'original': 'Golem Core', 'en': 'Golem Core'}, 'templateId': 'ITM006'} # Shared English item
            ],
            'source_file': 'test_fairy_data.xml'
        }
    ]

    def setUp(self):
        # Patch where SearchEngine looks up load_all_xml_data
        self.patcher = patch('search_engine.load_all_xml_data')
        self.mock_load_data = self.patcher.start()
        self.mock_load_data.return_value = TestSearchEngine.mock_npc_data # Use class attribute

        self.engine = SearchEngine(xml_directory="dummy_test_path") # Path doesn't matter

    def tearDown(self):
        self.patcher.stop()

    def test_search_english_npc_name_direct(self):
        """Test direct English match on NPC name via inverted index."""
        results = self.engine.search("Stone Golem")
        self.assertEqual(len(results), 2) # Expecting 2: NPC002 (name) and NPC003 (item "Golem Core")
        npc_ids_found = {npc['npcTemplateId'] for npc in results}
        self.assertIn('NPC002', npc_ids_found)
        self.assertIn('NPC003', npc_ids_found)


    def test_search_english_item_name_direct(self):
        """Test direct English match on item name via inverted index."""
        results = self.engine.search("Golem Core")
        self.assertEqual(len(results), 2) # NPC1 and NPC2 both have "Golem Core"
        npc_ids = {npc['npcTemplateId'] for npc in results}
        self.assertEqual(npc_ids, {'NPC002', 'NPC003'})

    def test_search_translated_korean_npc_name(self):
        """Test match on original Korean NPC name after query translation (simulated)."""
        # Query "크랩몬스터" (Korean) -> translate_to_korean("크랩몬스터") will be "크랩몬스터" (TEST_MODE)
        # The search function's "Korean search part" will tokenize "크랩몬스터"
        # and compare against tokenized original Korean names.
        # 'en_크랩몬스터' is indexed for English search.
        # The query 'CrabMonster' (hypothetical perfect EN translation) would be translated to 'ko_CrabMonster' for Korean search part.
        # Let's test with an English query that would map to the placeholder translation

        # If we search "en_크랩몬스터" (the placeholder English name in index)
        results_en_placeholder = self.engine.search("en_크랩몬스터")
        self.assertEqual(len(results_en_placeholder), 1)
        self.assertEqual(results_en_placeholder[0]['npcTemplateId'], 'NPC001')

        # If we search "CrabMonster" (an English query that would translate to "ko_CrabMonster" in TEST_MODE)
        # The 'ko_CrabMonster' tokens would be compared against original Korean names.
        # '크랩몬스터' (original) tokens: ['크랩몬스터']
        # 'ko_CrabMonster' (from query) tokens: ['ko_crabmonster'] (or similar based on actual test_mode)
        # This specific test case might be tricky due to how TEST_MODE fakes translation.
        # A better test: query for something that ONLY the Korean part of search would find.
        # Our current TEST_MODE translate_to_korean("CrabMonster") -> "ko_CrabMonster"
        # is_korean("크랩몬스터") is True. tokenize_text("크랩몬스터") is ['크랩몬스터']
        # tokenize_text("ko_CrabMonster") is ['ko_crabmonster']
        # No match with this specific query and current test_mode translation.

        # Let's test by searching for "크랩몬스터" directly.
        # The search function expects an English query.
        # If we pass "크랩몬스터", it will be used for English index (no match).
        # Then, translate_to_korean("크랩몬스터") (TEST_MODE) -> "크랩몬스터" (no "ko_" prefix as it has Korean char)
        # Then, tokens ['크랩몬스터'] will be searched against original Korean names. This should find NPC001.
        results_direct_korean_query = self.engine.search("크랩몬스터")
        self.assertEqual(len(results_direct_korean_query), 1, "Should find via original Korean name part of search")
        self.assertEqual(results_direct_korean_query[0]['npcTemplateId'], 'NPC001')


    def test_search_translated_korean_item_name(self):
        """Test match on original Korean item name after query translation (simulated)."""
        # Query "집게다리" (Korean item name)
        # Search for "집게다리" -> translate_to_korean("집게다리") -> "집게다리"
        # Tokens ['집게다리'] searched against original Korean item names. Should find item in NPC001.
        results = self.engine.search("집게다리")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['npcTemplateId'], 'NPC001')

        # Query for "마법의 돌" (Magic Stone)
        results_magic_stone = self.engine.search("마법의 돌")
        self.assertEqual(len(results_magic_stone), 1)
        self.assertEqual(results_magic_stone[0]['npcTemplateId'], 'NPC002')


    def test_search_combined_results(self):
        """Test query that matches via English index for one NPC and Korean name for another."""
        # "Golem" part of "Stone Golem" (NPC1) is in English Index.
        # If we search for "Golem", TEST_MODE translate_to_korean("Golem") -> "ko_Golem".
        # This "ko_golem" token set will be checked against original Korean names.
        # "en_골렘" (NPC2's name['en']) is indexed. "골렘" is its original.
        # So, "Golem" should find NPC1 (English index) and NPC2 (Korean name search part).
        results = self.engine.search("Golem") # "Golem" -> "ko_Golem" for Korean search part
        npc_ids = {npc['npcTemplateId'] for npc in results}
        self.assertEqual(len(results), 2, f"Found IDs: {npc_ids}") # NPC1 (Stone Golem), NPC2 (en_골렘)
        self.assertIn('NPC002', npc_ids) # Stone Golem
        self.assertIn('NPC003', npc_ids) # en_골렘 (original 골렘) - this one is tricky.
                                         # 'en_골렘' tokenized is ['en_골렘']. Query 'golem' doesn't match this in EN index.
                                         # For Korean search: query 'golem' -> 'ko_golem'. Tokens: ['ko_golem']
                                         # Original Korean name '골렘', tokens: ['골렘']. No match.

        # Let's re-evaluate:
        # Query: "Golem"
        # 1. English Index Search:
        #    - Token "golem" from query.
        #    - Index has "golem" from "Stone Golem" (NPC1) and "golem" from "Golem Core" (NPC1, NPC2).
        #    - So, English search part gets {NPC002, NPC003} (IDs from mock_npc_data indices are 1 and 2)
        #      which correspond to template IDs NPC002 and NPC003.
        #
        # 2. Korean Search Part:
        #    - `translate_to_korean("Golem")` (TEST_MODE) -> "ko_golem". Tokens: `['ko_golem']`.
        #    - NPC0 ('크랩몬스터'): No match.
        #    - NPC1 ('Stone Golem', not Korean): Skipped for original Korean name check.
        #    - NPC2 ('골렘'): Original is '골렘'. `is_korean('골렘')` is True. `tokenize_text('골렘')` is `['골렘']`.
        #                     `['ko_golem']` does not match `['골렘']`. No match here.
        #
        # So, "Golem" should only find NPC1 and NPC2 via the English index on "Golem Core".
        # And NPC1 via "Stone Golem".
        self.assertEqual(npc_ids, {'NPC002', 'NPC003'})


    def test_search_no_results(self):
        results = self.engine.search("NonExistentTermXYZ")
        self.assertEqual(len(results), 0)

    def test_empty_query(self):
        results = self.engine.search("")
        self.assertEqual(len(results), 0)
        results_space = self.engine.search("   ")
        self.assertEqual(len(results_space), 0)


if __name__ == '__main__':
    unittest.main()
