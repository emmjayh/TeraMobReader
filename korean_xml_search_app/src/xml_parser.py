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

                    item_data_for_gui = {
                        'name': item_name_dict,
                        'templateId': item_template_id,
                        'itembag_probability': float(item_bag_elem.get('probability', 0.0)),
                        'item_probability': float(item_elem.get('probability', 0.0)),
                        'min_quantity': int(item_elem.get('min', 1)),
                        'max_quantity': int(item_elem.get('max', 1))
                    }
                    items.append(item_data_for_gui)

            # Find ItemBag elements under ClassItemBag
            for class_item_bag_elem in compensation_elem.findall('ClassItemBag'):
                for item_bag_elem in class_item_bag_elem.findall('ItemBag'):
                    for item_elem in item_bag_elem.findall('Item'):
                        original_item_name = item_elem.get('name')
                        item_template_id = item_elem.get('templateId')

                        item_name_dict = {'original': original_item_name, 'en': original_item_name}
                        if is_korean(original_item_name):
                            item_name_dict['en'] = translate_to_english(original_item_name, text_type="item name")

                        item_data_for_gui = {
                            'name': item_name_dict,
                            'templateId': item_template_id,
                            'itembag_probability': float(item_bag_elem.get('probability', 0.0)), # Probability of the parent ItemBag
                            'item_probability': float(item_elem.get('probability', 0.0)),    # Probability of the Item itself
                            'min_quantity': int(item_elem.get('min', 1)),
                            'max_quantity': int(item_elem.get('max', 1))
                        }
                        items.append(item_data_for_gui)

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

def _indent_xml(elem, level=0):
    """Helper function to pretty-print XML tree."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            _indent_xml(subelem, level + 1)
        if not subelem.tail or not subelem.tail.strip(): # outdent last child
            subelem.tail = i
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

def update_compensation_data(xml_file_path: str, npc_template_id: str, updated_items_data: list) -> bool:
    """
    Updates the item data for a specific NPC in an XML file.
    Each item in updated_items_data will be placed in its own ItemBag.
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: XML file not found at {xml_file_path}")
        return False
    except ET.ParseError as e:
        print(f"Error parsing XML file {xml_file_path}: {e}")
        return False

    npc_found = False
    for compensation_elem in root.findall(f".//Compensation[@npcTemplateId='{npc_template_id}']"):
        npc_found = True

        # Remove existing ItemBag and ClassItemBag elements for this NPC
        # Iterate over a copy when removing elements
        for child_tag in ['ItemBag', 'ClassItemBag']:
            for elem_to_remove in compensation_elem.findall(child_tag):
                compensation_elem.remove(elem_to_remove)

        # Add new ItemBag elements from updated_items_data
        for item_dict in updated_items_data:
            # Create a new ItemBag for each item
            # The prompt implies item_dict contains 'itembag_probability' for the ItemBag,
            # and other details for the Item itself.
            item_bag = ET.SubElement(compensation_elem, "ItemBag")
            item_bag.set("probability", str(item_dict.get('itembag_probability', "0.0"))) # Default if not present

            item_elem = ET.SubElement(item_bag, "Item")
            item_elem.set("templateId", str(item_dict.get('templateId', '')))
            # Use original name for saving, as 'name' in XML is typically the original form
            item_elem.set("name", str(item_dict.get('name', {}).get('original', 'Unknown Item')))
            item_elem.set("min", str(item_dict.get('min_quantity', '1')))
            item_elem.set("max", str(item_dict.get('max_quantity', '1')))
            item_elem.set("probability", str(item_dict.get('item_probability', '1.0')))
        break # Assuming unique npcTemplateId within a file

    if not npc_found:
        print(f"Error: NPC with templateId '{npc_template_id}' not found in {xml_file_path}")
        return False

    try:
        _indent_xml(root) # Apply pretty-printing
        # ET.indent(tree, space="  ") # Alternative for Python 3.9+

        tree.write(xml_file_path, encoding="utf-8", xml_declaration=True)
        print(f"Successfully updated NPC {npc_template_id} in {xml_file_path}")
        return True
    except Exception as e:
        print(f"Error writing updated XML to {xml_file_path}: {e}")
        return False

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
