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
                npc_name_dict['en'] = translate_to_english(original_npc_name)

            items = []
            # Find ItemBag elements directly under Compensation
            for item_bag_elem in compensation_elem.findall('ItemBag'):
                for item_elem in item_bag_elem.findall('Item'):
                    original_item_name = item_elem.get('name')
                    item_template_id = item_elem.get('templateId')

                    item_name_dict = {'original': original_item_name, 'en': original_item_name}
                    if is_korean(original_item_name):
                        item_name_dict['en'] = translate_to_english(original_item_name)

                    # Extract additional attributes
                    itembag_probability = float(item_bag_elem.get('probability', 0.0))
                    item_probability = float(item_elem.get('probability', 0.0))
                    min_quantity = int(item_elem.get('min', 1))
                    max_quantity = int(item_elem.get('max', 1))

                    items.append({
                        'name': item_name_dict,
                        'templateId': item_template_id,
                        'itembag_probability': itembag_probability,
                        'item_probability': item_probability,
                        'min_quantity': min_quantity,
                        'max_quantity': max_quantity
                    })

            # Find ItemBag elements under ClassItemBag
            for class_item_bag_elem in compensation_elem.findall('ClassItemBag'):
                for item_bag_elem in class_item_bag_elem.findall('ItemBag'):
                    # Extract ItemBag probability
                    itembag_probability_class = float(item_bag_elem.get('probability', 0.0))
                    for item_elem in item_bag_elem.findall('Item'):
                        original_item_name = item_elem.get('name')
                        item_template_id = item_elem.get('templateId')

                        item_name_dict = {'original': original_item_name, 'en': original_item_name}
                        if is_korean(original_item_name):
                            item_name_dict['en'] = translate_to_english(original_item_name)

                        # Extract additional attributes
                        item_probability_class = float(item_elem.get('probability', 0.0))
                        min_quantity_class = int(item_elem.get('min', 1))
                        max_quantity_class = int(item_elem.get('max', 1))

                        items.append({
                            'name': item_name_dict,
                            'templateId': item_template_id,
                            'itembag_probability': itembag_probability_class,
                            'item_probability': item_probability_class,
                            'min_quantity': min_quantity_class,
                            'max_quantity': max_quantity_class
                        })

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
                    print(f"    ItemBag Probability: {item.get('itembag_probability', 'N/A')}")
                    print(f"    Item Probability: {item.get('item_probability', 'N/A')}")
                    print(f"    Min Quantity: {item.get('min_quantity', 'N/A')}")
                    print(f"    Max Quantity: {item.get('max_quantity', 'N/A')}")
            else:
                print("  - No items found for this NPC.")
            print("-" * 20)


def update_compensation_data(xml_file_path: str, npc_template_id: str, updated_items_data: list) -> bool:
    """
    Updates the compensation data for a specific NPC in an XML file.

    Args:
        xml_file_path (str): Path to the XML file.
        npc_template_id (str): The templateId of the NPC to update.
        updated_items_data (list): A list of dictionaries, where each dictionary
                                   represents an item and its new attributes.
                                   Example item_data: {
                                       'templateId': str,
                                       'name': {'original': str, 'en': str},
                                       'itembag_probability': float,
                                       'item_probability': float,
                                       'min_quantity': int,
                                       'max_quantity': int
                                   }
    Returns:
        bool: True if update was successful, False otherwise.
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        npc_element_found = None

        for compensation_elem in root.findall('Compensation'):
            if compensation_elem.get('npcTemplateId') == npc_template_id:
                npc_element_found = compensation_elem
                break

        if npc_element_found is None:
            print(f"Error: NPC with templateId '{npc_template_id}' not found in '{xml_file_path}'.")
            return False

        # Clear existing ItemBag and ClassItemBag elements for this NPC
        for item_bag in list(npc_element_found.findall('ItemBag')): # Iterate over a copy for safe removal
            npc_element_found.remove(item_bag)
        for class_item_bag in list(npc_element_found.findall('ClassItemBag')): # Iterate over a copy
            npc_element_found.remove(class_item_bag)

        # Re-add items based on updated_items_data
        # This simplified version creates one ItemBag per Item.
        for item_data in updated_items_data:
            new_item_bag = ET.Element('ItemBag')
            new_item_bag.set('probability', str(item_data.get('itembag_probability', 0.0)))

            new_item = ET.Element('Item')
            new_item.set('templateId', str(item_data.get('templateId', '')))

            # Ensure 'name' and 'original' keys exist, default to empty string if not
            name_dict = item_data.get('name', {})
            original_name = name_dict.get('original', '')
            new_item.set('name', original_name)

            new_item.set('min', str(item_data.get('min_quantity', 1)))
            new_item.set('max', str(item_data.get('max_quantity', 1)))
            new_item.set('probability', str(item_data.get('item_probability', 0.0)))

            new_item_bag.append(new_item)
            npc_element_found.append(new_item_bag)

        # Write changes back to the XML file
        # To preserve the XML declaration and potentially other formatting,
        # it's often better to write to a temporary file then replace,
        # or use lxml which has better pretty print and write options.
        # For now, ET's default tree.write is used.
        tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)
        return True

    except FileNotFoundError:
        print(f"Error: XML file not found at '{xml_file_path}'.")
        return False
    except ET.ParseError as e:
        print(f"Error parsing XML file '{xml_file_path}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred in update_compensation_data: {e}")
        import traceback
        traceback.print_exc()
        return False