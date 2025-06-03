import os
import json
from xml_parser import parse_compensation_data
from translator import translate_to_korean # Although not used in indexing, good for future search

def load_all_xml_data(xml_directory: str) -> list:
    """
    Loads and parses all XML files from a given directory.

    Args:
        xml_directory (str): The path to the directory containing XML files.

    Returns:
        list: A list of all NPC data extracted from the XML files.
    """
    all_npc_data = []

    # Ensure xml_directory is an absolute path or correctly relative
    if not os.path.isabs(xml_directory):
        # Assuming this script is in src, and xml_directory is like ../data/xmls
        base_dir = os.path.dirname(__file__)
        xml_directory = os.path.normpath(os.path.join(base_dir, xml_directory))

    if not os.path.isdir(xml_directory):
        print(f"Error: Directory not found at {xml_directory}")
        return all_npc_data

    for filename in os.listdir(xml_directory):
        if filename.endswith(".xml"):
            full_file_path = os.path.join(xml_directory, filename)
            print(f"Parsing file: {full_file_path}")
            npc_data_from_file = parse_compensation_data(full_file_path)
            if npc_data_from_file:
                all_npc_data.extend(npc_data_from_file)
    return all_npc_data

def tokenize_text(text: str) -> list:
    """
    Tokenizes text: lowercase and splits by space.

    Args:
        text (str): The text to tokenize.

    Returns:
        list: A list of unique tokens.
    """
    if not text:
        return []
    return list(set(text.lower().split()))

def build_inverted_index(all_npc_data: list) -> dict:
    """
    Builds an inverted index from the provided NPC data.

    Args:
        all_npc_data (list): A list of NPC data objects.

    Returns:
        dict: The inverted index. Keys are tokens, values are lists of NPC IDs.
    """
    inverted_index = {}
    for npc_id, npc_entry in enumerate(all_npc_data):
        # Process NPC Name
        npc_name_en = npc_entry.get('npcName', {}).get('en', '')
        if npc_name_en:
            tokens = tokenize_text(npc_name_en)
            for token in tokens:
                if token not in inverted_index:
                    inverted_index[token] = set()
                inverted_index[token].add(npc_id)

        # Process Item Names
        for item in npc_entry.get('items', []):
            item_name_en = item.get('name', {}).get('en', '')
            if item_name_en:
                tokens = tokenize_text(item_name_en)
                for token in tokens:
                    if token not in inverted_index:
                        inverted_index[token] = set()
                    inverted_index[token].add(npc_id)

    # Convert sets to lists for easier display/serialization
    for token in inverted_index:
        inverted_index[token] = list(inverted_index[token])

    return inverted_index

if __name__ == "__main__":
    # Assuming indexer.py is in 'src', and data is in 'data/xmls' relative to project root
    xml_dir = "../data/xmls/"

    print(f"Loading XML data from: {xml_dir}")
    all_data = load_all_xml_data(xml_dir)

    if all_data:
        print(f"\nSuccessfully loaded {len(all_data)} NPC entries.")
        print("\nSample of loaded data (first NPC entry):")
        # Use json.dumps for pretty printing the complex dictionary
        print(json.dumps(all_data[0], indent=2, ensure_ascii=False))

        print("\nBuilding inverted index...")
        index = build_inverted_index(all_data)
        print("Inverted index built.")

        print("\nSample of Inverted Index (first 5 items):")
        sample_index = {k: index[k] for k in list(index.keys())[:5]}
        print(json.dumps(sample_index, indent=2, ensure_ascii=False))

        # Example: Print index for a specific common token if it exists
        if "potion" in index:
            print("\nIndex entry for 'potion':")
            print(json.dumps({"potion": index["potion"]}, indent=2, ensure_ascii=False))
        if "crystal" in index:
            print("\nIndex entry for 'crystal':")
            print(json.dumps({"crystal": index["crystal"]}, indent=2, ensure_ascii=False))

    else:
        print("No data loaded. Index not built.")
