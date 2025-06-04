import xml.etree.ElementTree as ET
import os
from translator import is_korean, translate_to_english

def parse_compensation_data(xml_file_path):
    """
    Parses the XML file and extracts compensation data, including translations.

    Args:
        xml_file_path (str): The path to the XML file.

    Returns:
        list: A list of NPCs with their extracted information.
              Each element in the list is a dictionary with the following keys:
              'npcName': {'original': str, 'en': str}
              'npcTemplateId': str
              'items': A list of items, each a dictionary:
                       {'name': {'original': str, 'en': str}, 'templateId': str}
    """
    npcs_data = []
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        for compensation_elem in root.findall('Compensation'):
            original_npc_name = compensation_elem.get('npcName')
            npc_template_id = compensation_elem.get('npcTemplateId')

            npc_name_dict = {'original': original_npc_name, 'en': original_npc_name}
            if is_korean(original_npc_name):
                npc_name_dict['en'] = translate_to_english(original_npc_name, text_type="NPC name")

            items = []
            # Find ItemBag elements directly under Compensation
            for item_bag_elem in compensation_elem.findall('ItemBag'):
                for item_elem in item_bag_elem.findall('Item'):
                    original_item_name = item_elem.get('name')
                    item_template_id = item_elem.get('templateId')

                    item_name_dict = {'original': original_item_name, 'en': original_item_name}
                    if is_korean(original_item_name):
                        item_name_dict['en'] = translate_to_english(original_item_name, text_type="item name")

                    items.append({'name': item_name_dict, 'templateId': item_template_id})

            # Find ItemBag elements under ClassItemBag
            for class_item_bag_elem in compensation_elem.findall('ClassItemBag'):
                for item_bag_elem in class_item_bag_elem.findall('ItemBag'):
                    for item_elem in item_bag_elem.findall('Item'): # This loop was iterating one level too deep previously for item_name_dict
                        original_item_name = item_elem.get('name')
                        item_template_id = item_elem.get('templateId')

                        item_name_dict = {'original': original_item_name, 'en': original_item_name}
                        if is_korean(original_item_name):
                            item_name_dict['en'] = translate_to_english(original_item_name, text_type="item name")

                        items.append({'name': item_name_dict, 'templateId': item_template_id})

            npcs_data.append({
                'npcName': npc_name_dict,
                'npcTemplateId': npc_template_id,
                'items': items,
                'source_file': xml_file_path  # Add source file path
            })

    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: XML file not found at {xml_file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    return npcs_data

if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    # Navigate up one level to the 'korean_xml_search_app' directory, then into 'data/xmls'
    # Construct the path to the sample.xml file relative to this script
    # Navigate up one level to the 'korean_xml_search_app' directory, then into 'data/xmls'
    xml_file_relative_path = os.path.join('..', 'data', 'xmls', 'sample.xml')
    xml_file_abs_path = os.path.normpath(os.path.join(current_dir, xml_file_relative_path))

    extracted_data = parse_compensation_data(xml_file_abs_path)

    if extracted_data:
        for npc in extracted_data:
            print(f"NPC Name (Original): {npc['npcName']['original']}")
            if npc['npcName']['original'] != npc['npcName']['en']:
                 print(f"NPC Name (English): {npc['npcName']['en']}")
            print(f"NPC ID: {npc['npcTemplateId']}")
            print(f"Source File: {npc['source_file']}") # Print source file

            if npc['items']:
                for item in npc['items']:
                    print(f"  - Item (Original): {item['name']['original']}")
                    if item['name']['original'] != item['name']['en']:
                        print(f"    Item (English): {item['name']['en']}")
                    print(f"    Item ID: {item['templateId']}")
            else:
                print("  - No items found for this NPC.")
            print("-" * 20)
