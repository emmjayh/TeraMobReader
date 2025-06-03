import unittest
import sys
import os
import xml.etree.ElementTree as ET

# Adjust sys.path to allow imports from the 'src' directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from xml_parser import parse_compensation_data
import translator as translator_module

# Ensure TEST_MODE is active for all tests in this module
translator_module.TEST_MODE = True

class TestXmlParser(unittest.TestCase):

    def setUp(self):
        # Define the path to the test XML file
        self.test_xml_file = os.path.join(os.path.dirname(__file__), 'test_data.xml')
        # Ensure the test file exists
        if not os.path.exists(self.test_xml_file):
            self.fail(f"Test XML file not found: {self.test_xml_file}")

    def test_parse_compensation_data(self):
        parsed_data = parse_compensation_data(self.test_xml_file)
        self.assertIsNotNone(parsed_data)
        self.assertEqual(len(parsed_data), 2) # Expecting two <Compensation> elements

        # --- Test NPC 1 (Korean Name) ---
        npc1 = parsed_data[0]
        self.assertEqual(npc1['npcName']['original'], "테스트NPC")
        self.assertEqual(npc1['npcName']['en'], "en_테스트NPC") # TEST_MODE translation
        self.assertEqual(npc1['npcTemplateId'], "1001")
        self.assertEqual(npc1['source_file'], self.test_xml_file)

        self.assertEqual(len(npc1['items']), 1)
        item1_npc1 = npc1['items'][0]
        self.assertEqual(item1_npc1['name']['original'], "테스트아이템1")
        self.assertEqual(item1_npc1['name']['en'], "en_테스트아이템1") # TEST_MODE translation
        self.assertEqual(item1_npc1['templateId'], "item01")

        # --- Test NPC 2 (English Name and ClassItemBag) ---
        npc2 = parsed_data[1]
        self.assertEqual(npc2['npcName']['original'], "TestNPC_EN")
        self.assertEqual(npc2['npcName']['en'], "TestNPC_EN") # Should remain English
        self.assertEqual(npc2['npcTemplateId'], "1002")
        self.assertEqual(npc2['source_file'], self.test_xml_file)

        self.assertEqual(len(npc2['items']), 2) # One from ItemBag, one from ClassItemBag/ItemBag

        # Item from direct ItemBag
        item1_npc2 = next((item for item in npc2['items'] if item['templateId'] == 'item02'), None)
        self.assertIsNotNone(item1_npc2)
        self.assertEqual(item1_npc2['name']['original'], "TestItem_EN")
        self.assertEqual(item1_npc2['name']['en'], "TestItem_EN") # Should remain English

        # Item from ClassItemBag
        item2_npc2 = next((item for item in npc2['items'] if item['templateId'] == 'item03'), None)
        self.assertIsNotNone(item2_npc2)
        self.assertEqual(item2_npc2['name']['original'], "전사전용템")
        self.assertEqual(item2_npc2['name']['en'], "en_전사전용템") # TEST_MODE translation

    def test_parse_non_existent_file(self):
        data = parse_compensation_data("non_existent_file.xml")
        self.assertIsNone(data) # Expecting None or appropriate error handling

    def test_parse_malformed_xml(self):
        # Create a temporary malformed XML file
        malformed_xml_path = os.path.join(os.path.dirname(__file__), "malformed_test.xml")
        with open(malformed_xml_path, "w", encoding="utf-8") as f:
            f.write("<CCompensationData><Compensation npcName='test'>Malformed</Compensation>") # Missing closing tag for CCompensationData

        data = parse_compensation_data(malformed_xml_path)
        self.assertIsNone(data) # Expecting None due to parse error

        os.remove(malformed_xml_path) # Clean up

if __name__ == '__main__':
    unittest.main()
