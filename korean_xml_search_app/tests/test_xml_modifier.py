import unittest
import xml.etree.ElementTree as ET
import os
import tempfile
import sys

# Adjust path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from xml_parser import parse_compensation_data, update_compensation_data
# Assuming translator.py is in src and TEST_MODE is True by default or handled within translator
# from translator import TEST_MODE

# Sample XML data for testing
SAMPLE_XML_CONTENT = """
<CompensationList>
    <Compensation npcName="몬스터A" npcTemplateId="101">
        <ItemBag probability="0.5">
            <Item templateId="1001" name="아이템1" min="1" max="2" probability="0.8"/>
        </ItemBag>
        <ItemBag probability="1.0">
            <Item templateId="1002" name="아이템2" probability="0.9"/> <!-- min/max missing -->
        </ItemBag>
    </Compensation>
    <Compensation npcName="몬스터B" npcTemplateId="102">
        <ItemBag probability="0.1">
            <Item templateId="2001" name="코리안아이템" min="5" max="5" probability="1.0"/>
        </ItemBag>
        <!-- NPC with no direct items, but could have ClassItemBag (not covered in this sample for simplicity) -->
    </Compensation>
    <Compensation npcName="몬스터C" npcTemplateId="103">
        <!-- No items for this NPC -->
    </Compensation>
</CompensationList>
"""

class TestParseCompensationDataNewAttributes(unittest.TestCase):

    def setUp(self):
        # Create a temporary file for parsing tests
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".xml")
        self.temp_file.write(SAMPLE_XML_CONTENT)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file_path)

    def test_parse_extracts_new_item_attributes(self):
        parsed_data = parse_compensation_data(self.temp_file_path)
        self.assertIsNotNone(parsed_data)
        self.assertEqual(len(parsed_data), 3) # 3 NPCs

        # NPC 101
        npc101 = next((npc for npc in parsed_data if npc['npcTemplateId'] == "101"), None)
        self.assertIsNotNone(npc101)
        self.assertEqual(len(npc101['items']), 2)

        item1 = npc101['items'][0]
        self.assertEqual(item1['templateId'], "1001")
        self.assertEqual(item1['name']['original'], "아이템1")
        self.assertEqual(item1['itembag_probability'], 0.5)
        self.assertEqual(item1['item_probability'], 0.8)
        self.assertEqual(item1['min_quantity'], 1)
        self.assertEqual(item1['max_quantity'], 2)

        item2 = npc101['items'][1] # Item with missing min/max
        self.assertEqual(item2['templateId'], "1002")
        self.assertEqual(item2['name']['original'], "아이템2")
        self.assertEqual(item2['itembag_probability'], 1.0)
        self.assertEqual(item2['item_probability'], 0.9)
        self.assertEqual(item2['min_quantity'], 1) # Default
        self.assertEqual(item2['max_quantity'], 1) # Default

        # NPC 102
        npc102 = next((npc for npc in parsed_data if npc['npcTemplateId'] == "102"), None)
        self.assertIsNotNone(npc102)
        self.assertEqual(len(npc102['items']), 1)
        item_ko = npc102['items'][0]
        self.assertEqual(item_ko['templateId'], "2001")
        self.assertEqual(item_ko['name']['original'], "코리안아이템")
        # Assuming TEST_MODE=True in translator.py, 'en' name will be 'en_코리안아이템'
        self.assertTrue(item_ko['name']['en'].startswith("en_"))
        self.assertEqual(item_ko['itembag_probability'], 0.1)
        self.assertEqual(item_ko['item_probability'], 1.0)
        self.assertEqual(item_ko['min_quantity'], 5)
        self.assertEqual(item_ko['max_quantity'], 5)

        # NPC 103
        npc103 = next((npc for npc in parsed_data if npc['npcTemplateId'] == "103"), None)
        self.assertIsNotNone(npc103)
        self.assertEqual(len(npc103['items']), 0)


class TestUpdateCompensationData(unittest.TestCase):

    def setUp(self):
        # Create a temporary XML file for update tests
        self.temp_file_fd, self.temp_xml_path = tempfile.mkstemp(suffix=".xml", text=True)
        with open(self.temp_xml_path, "w", encoding="utf-8") as f:
            f.write(SAMPLE_XML_CONTENT)
        # print(f"Test XML created at: {self.temp_xml_path}")


    def tearDown(self):
        os.close(self.temp_file_fd)
        os.unlink(self.temp_xml_path)
        # print(f"Test XML deleted: {self.temp_xml_path}")

    def test_update_modifies_items_correctly(self):
        npc_id_to_update = "101"
        updated_items_data = [
            {
                'templateId': "1001", 'name': {'original': "아이템1_수정됨", 'en': "Item1_Modified"},
                'itembag_probability': 0.75, 'item_probability': 0.85,
                'min_quantity': 3, 'max_quantity': 4
            },
            {
                'templateId': "NEW001", 'name': {'original': "새로운아이템", 'en': "NewItem"},
                'itembag_probability': 0.25, 'item_probability': 0.95,
                'min_quantity': 1, 'max_quantity': 1
            }
        ]

        success = update_compensation_data(self.temp_xml_path, npc_id_to_update, updated_items_data)
        self.assertTrue(success)

        tree = ET.parse(self.temp_xml_path)
        root = tree.getroot()
        npc_element = None
        for comp_elem in root.findall('Compensation'):
            if comp_elem.get('npcTemplateId') == npc_id_to_update:
                npc_element = comp_elem
                break

        self.assertIsNotNone(npc_element)
        item_bags = npc_element.findall('ItemBag')
        self.assertEqual(len(item_bags), len(updated_items_data))

        # Verify first updated item
        item_bag1 = item_bags[0]
        self.assertEqual(item_bag1.get('probability'), str(updated_items_data[0]['itembag_probability']))
        item1 = item_bag1.find('Item')
        self.assertIsNotNone(item1)
        self.assertEqual(item1.get('templateId'), updated_items_data[0]['templateId'])
        self.assertEqual(item1.get('name'), updated_items_data[0]['name']['original'])
        self.assertEqual(item1.get('min'), str(updated_items_data[0]['min_quantity']))
        self.assertEqual(item1.get('max'), str(updated_items_data[0]['max_quantity']))
        self.assertEqual(item1.get('probability'), str(updated_items_data[0]['item_probability']))

        # Verify second (new) item
        item_bag2 = item_bags[1]
        self.assertEqual(item_bag2.get('probability'), str(updated_items_data[1]['itembag_probability']))
        item2 = item_bag2.find('Item')
        self.assertIsNotNone(item2)
        self.assertEqual(item2.get('templateId'), updated_items_data[1]['templateId'])
        self.assertEqual(item2.get('name'), updated_items_data[1]['name']['original'])
        self.assertEqual(item2.get('min'), str(updated_items_data[1]['min_quantity']))
        self.assertEqual(item2.get('max'), str(updated_items_data[1]['max_quantity']))
        self.assertEqual(item2.get('probability'), str(updated_items_data[1]['item_probability']))

    def test_update_preserves_original_item_name(self):
        npc_id_to_update = "102"
        korean_name = "코리안아이템_수정"
        updated_items_data = [
            {
                'templateId': "2001", 'name': {'original': korean_name, 'en': "KoreanItem_Modified"},
                'itembag_probability': 0.15, 'item_probability': 0.75,
                'min_quantity': 1, 'max_quantity': 2
            }
        ]
        success = update_compensation_data(self.temp_xml_path, npc_id_to_update, updated_items_data)
        self.assertTrue(success)

        tree = ET.parse(self.temp_xml_path)
        root = tree.getroot()
        npc_element = next(c for c in root.findall('Compensation') if c.get('npcTemplateId') == npc_id_to_update)
        item = npc_element.find('ItemBag/Item')
        self.assertEqual(item.get('name'), korean_name)

    def test_update_clears_items_for_npc(self):
        npc_id_to_update = "101" # This NPC has 2 items initially
        updated_items_data = [] # Empty list to clear items

        success = update_compensation_data(self.temp_xml_path, npc_id_to_update, updated_items_data)
        self.assertTrue(success)

        tree = ET.parse(self.temp_xml_path)
        root = tree.getroot()
        npc_element = next(c for c in root.findall('Compensation') if c.get('npcTemplateId') == npc_id_to_update)
        item_bags = npc_element.findall('ItemBag')
        self.assertEqual(len(item_bags), 0)


    def test_update_handles_nonexistent_npc(self):
        success = update_compensation_data(self.temp_xml_path, "nonexistent_npc_id", [])
        self.assertFalse(success)
        # Could also check if file content remains unchanged by reading it before and after

    def test_update_handles_bad_xml_path(self):
        success = update_compensation_data("bad/path/to/nonexistent_file.xml", "101", [])
        self.assertFalse(success)

if __name__ == '__main__':
    # If translator.TEST_MODE needs to be set for xml_parser's import,
    # it should be done before xml_parser is imported by the tests.
    # However, `update_compensation_data` itself doesn't use translation.
    # `parse_compensation_data` does, but its tests are self-contained with temp files.
    # So, direct manipulation of TEST_MODE might not be needed here if it's True by default.
    # print(f"Translator TEST_MODE is currently: {TEST_MODE}")
    unittest.main()
