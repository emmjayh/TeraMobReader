import unittest
import sys
import os
import shutil # For cleaning up temp directories
import json

# Adjust sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from indexer import tokenize_text, load_all_xml_data, build_inverted_index
import xml_parser # To potentially mock its parse_compensation_data
import translator as translator_module

# Ensure TEST_MODE is active for all tests in this module
translator_module.TEST_MODE = True

class TestIndexer(unittest.TestCase):

    def test_tokenize_text(self):
        self.assertEqual(sorted(tokenize_text("Hello World")), sorted(["world", "hello"]))
        self.assertEqual(sorted(tokenize_text("Test  Extra Spaces")), sorted(["test", "extra", "spaces"]))
        self.assertEqual(sorted(tokenize_text("")), sorted([])) # Ensure consistent empty list comparison
        self.assertEqual(sorted(tokenize_text("MiXeD CaSe")), sorted(["mixed", "case"]))
        self.assertEqual(sorted(tokenize_text("test-item with-hyphen")), sorted(["test-item", "with-hyphen"]))


    def setUp(self):
        # Create a temporary directory for test XML files
        self.temp_dir_for_xml = os.path.join(os.path.dirname(__file__), "temp_xml_dir_indexer")
        os.makedirs(self.temp_dir_for_xml, exist_ok=True)

        # Create a dummy test XML file (can reuse content from test_xml_parser's test_data.xml)
        self.dummy_xml_path = os.path.join(self.temp_dir_for_xml, "dummy.xml")
        with open(self.dummy_xml_path, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0" encoding="utf-8"?>
<CCompensationData huntingZoneId="99">
  <Compensation npcTemplateId="T01" npcName="테스트엔피시">
    <ItemBag><Item templateId="item_k1" name="코리안아이템" /></ItemBag>
  </Compensation>
  <Compensation npcTemplateId="T02" npcName="EnglishNPC">
    <ItemBag><Item templateId="item_e1" name="EnglishItem" /></ItemBag>
    <ClassItemBag class="Any"><ItemBag><Item templateId="item_e2" name="Another English Item" /></ItemBag></ClassItemBag>
  </Compensation>
</CCompensationData>""")

    def tearDown(self):
        # Remove the temporary directory and its contents
        if os.path.exists(self.temp_dir_for_xml):
            shutil.rmtree(self.temp_dir_for_xml)

    def test_load_all_xml_data(self):
        # Test loading from the temp directory
        all_data = load_all_xml_data(self.temp_dir_for_xml)
        self.assertEqual(len(all_data), 2)

        npc_names = {entry['npcName']['original'] for entry in all_data}
        self.assertIn("테스트엔피시", npc_names)
        self.assertIn("EnglishNPC", npc_names)

        # Check source_file attribute
        for entry in all_data:
            self.assertTrue(entry['source_file'].endswith("dummy.xml"))

    def test_build_inverted_index(self):
        # Sample data (ensure it reflects TEST_MODE from translator)
        sample_npc_data = [
            { # NPC ID 0
                'npcName': {'original': '크랩', 'en': 'en_크랩'}, 'npcTemplateId': 'N1',
                'items': [{'name': {'original': '집게발', 'en': 'en_집게발'}, 'templateId': 'I10'}],
                'source_file': 'dummy1.xml'
            },
            { # NPC ID 1
                'npcName': {'original': 'Crab', 'en': 'Crab'}, 'npcTemplateId': 'N2',
                'items': [{'name': {'original': 'Pincer', 'en': 'Pincer'}, 'templateId': 'I20'}],
                'source_file': 'dummy2.xml'
            },
            { # NPC ID 2
                'npcName': {'original': '골렘', 'en': 'en_골렘'}, 'npcTemplateId': 'N3',
                'items': [
                    {'name': {'original': '돌조각', 'en': 'en_돌조각'}, 'templateId': 'I30'},
                    {'name': {'original': 'Crab Pincer', 'en': 'Crab Pincer'}, 'templateId': 'I31'} # English item name
                ],
                'source_file': 'dummy3.xml'
            }
        ]

        index = build_inverted_index(sample_npc_data)

        # Print index for debugging if needed
        # print("\nConstructed Index for test_build_inverted_index:")
        # print(json.dumps(index, indent=2, ensure_ascii=False))

        self.assertIn("en_크랩", index)
        self.assertEqual(sorted(index["en_크랩"]), [0])

        self.assertIn("crab", index)
        self.assertEqual(sorted(index["crab"]), [1, 2]) # From NPC name and item name

        self.assertIn("pincer", index)
        self.assertEqual(sorted(index["pincer"]), [1, 2])

        self.assertIn("en_집게발", index)
        self.assertEqual(sorted(index["en_집게발"]), [0])

        self.assertIn("en_골렘", index)
        self.assertEqual(sorted(index["en_골렘"]), [2])

        self.assertIn("en_돌조각", index)
        self.assertEqual(sorted(index["en_돌조각"]), [2])

        # Check that original Korean names (not translated by TEST_MODE for 'en' field unless explicitly done so)
        # are NOT in the index if they were not part of an 'en' field.
        self.assertNotIn("크랩", index)
        self.assertNotIn("집게발", index)


if __name__ == '__main__':
    unittest.main()
