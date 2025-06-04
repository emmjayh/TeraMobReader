import json
import os
from indexer import load_all_xml_data, build_inverted_index, tokenize_text
from translator import translate_to_korean, is_korean, translate_to_english

class SearchEngine:
    def __init__(self, xml_directory: str):
        """
        Initializes the SearchEngine by loading data and building the index.
        """
        print("Initializing Search Engine...") # Should be visible
        # Adjust xml_directory path if it's relative to the project root
        if not os.path.isabs(xml_directory) and xml_directory.startswith("../"):
            base_dir = os.path.dirname(__file__) # src directory
            xml_directory = os.path.normpath(os.path.join(base_dir, xml_directory))

        self.all_npc_data = load_all_xml_data(xml_directory)
        if not self.all_npc_data:
            print("Warning: No NPC data loaded. Search will yield no results.")
            self.inverted_index_en = {}
        else:
            print(f"Loaded {len(self.all_npc_data)} NPC entries.")
            self.inverted_index_en = build_inverted_index(self.all_npc_data)
            print("Inverted index for English names/items built.")
        print("Search Engine initialized.")

    def search(self, english_query: str) -> list:
        """
        Searches for NPCs based on an English query.
        The search considers:
        1. English query tokens against an inverted index of English NPC/item names.
        2. The English query translated to Korean, then tokenized and matched against
           original Korean NPC/item names.
        """
        matching_npc_ids = set()

        # A. English Keyword Search (using Inverted Index)
        if english_query and isinstance(english_query, str) and english_query.strip():
            english_query_tokens = tokenize_text(english_query)
            # print(f"DEBUG: English query tokens: {english_query_tokens}")
            for token in english_query_tokens:
                if token in self.inverted_index_en:
                    # print(f"DEBUG: Token '{token}' found in English index, NPC IDs: {self.inverted_index_en[token]}")
                    matching_npc_ids.update(self.inverted_index_en[token])

        # B. Korean Name Search (direct iteration and translation)
        # Translate the input query to Korean. If it's already Korean, it should remain similar.
        korean_for_search = ""
        if english_query and isinstance(english_query, str) and english_query.strip():
             korean_for_search = translate_to_korean(english_query, text_type="search query")

        # print(f"DEBUG: Query '{english_query}' translated for Korean search part as: '{korean_for_search}'")

        if korean_for_search: # Proceed if there's a valid string for Korean search
            korean_query_tokens = tokenize_text(korean_for_search)
            # print(f"DEBUG: Tokens for Korean part search: {korean_query_tokens}")

            if korean_query_tokens: # Only iterate if there are tokens to search for
                for npc_id, npc_entry in enumerate(self.all_npc_data):
                    # Check NPC Name (Original Korean)
                    original_npc_name = npc_entry.get('npcName', {}).get('original', '')
                    if original_npc_name and is_korean(original_npc_name): # Check original is Korean
                        tokenized_original_npc_name = tokenize_text(original_npc_name)
                        if any(kq_token in tokenized_original_npc_name for kq_token in korean_query_tokens):
                            # print(f"DEBUG: Match on Korean NPC name '{original_npc_name}' for query token from '{korean_for_search}'")
                            matching_npc_ids.add(npc_id)
                            # No continue here, allow item check too if desired, though set handles duplicates.

                    # Check Item Names (Original Korean)
                    # Only proceed if NPC not already added by name match for this Korean query part,
                    # or if you want items to also contribute independently (set handles duplicates).
                    for item in npc_entry.get('items', []):
                        original_item_name = item.get('name', {}).get('original', '')
                        if original_item_name and is_korean(original_item_name): # Check original is Korean
                            tokenized_original_item_name = tokenize_text(original_item_name)
                            if any(kq_token in tokenized_original_item_name for kq_token in korean_query_tokens):
                                # print(f"DEBUG: Match on Korean item name '{original_item_name}' for query token from '{korean_for_search}'")
                                matching_npc_ids.add(npc_id)
                                break # Found a matching item for this NPC for this Korean query part

        # C. Retrieve Full NPC Data
        results = [self.all_npc_data[npc_id] for npc_id in matching_npc_ids]
        return results

    def index_single_file(self, xml_file_path: str):
        """
        Reloads data from a single XML file and rebuilds the search index.
        """
        if not os.path.isabs(xml_file_path): # Ensure path is absolute or correctly resolved
            base_dir = os.path.dirname(__file__) # src directory
            # Assuming xml_file_path might be relative to project root or src.
            # For simplicity, let's assume it's already a full path or correctly relative to where SearchEngine expects it.
            # If it's just a filename, it should be in the SearchEngine's base xml_directory.
            # This path logic might need to be more robust depending on how xml_file_path is provided.
            # For now, let's assume xml_file_path is the full, correct path.

        print(f"Re-indexing file: {xml_file_path}")

        # 1. Remove old entries from this file
        initial_count = len(self.all_npc_data)
        self.all_npc_data = [npc_entry for npc_entry in self.all_npc_data
                             if npc_entry.get('source_file') != xml_file_path]
        removed_count = initial_count - len(self.all_npc_data)
        if removed_count > 0:
            print(f"Removed {removed_count} old entries from '{os.path.basename(xml_file_path)}'.")
        else:
            print(f"No existing entries found for '{os.path.basename(xml_file_path)}' to remove (this is okay if it's a new file or was not loaded).")

        # 2. Parse the updated file and add its data
        # We need parse_compensation_data from xml_parser
        # Ensure it's imported: from xml_parser import parse_compensation_data
        # (Assuming it's already imported at the module level of search_engine.py)

        # To avoid error if SearchEngine did not import it at top level:
        try:
            from xml_parser import parse_compensation_data as pc_data # Local import for safety
        except ImportError:
            print("Error: Could not import parse_compensation_data. Re-indexing aborted.")
            # Potentially re-add the removed items if aborting, or handle more gracefully
            # For now, this is a critical error.
            return

        updated_npc_data_from_file = pc_data(xml_file_path)

        if updated_npc_data_from_file is not None: # parse_compensation_data returns None on error
            self.all_npc_data.extend(updated_npc_data_from_file)
            print(f"Added/updated {len(updated_npc_data_from_file)} entries from '{os.path.basename(xml_file_path)}'.")
        else:
            print(f"Warning: Could not parse '{os.path.basename(xml_file_path)}' during re-indexing. File might be corrupted or empty.")
            # Depending on desired behavior, one might re-add the 'removed_count' items
            # or leave them out if the file is truly problematic.

        # 3. Rebuild the entire index
        # Ensure build_inverted_index is imported: from indexer import build_inverted_index
        # (Assuming it's already imported at the module level of search_engine.py)
        try:
            from indexer import build_inverted_index as bi_index # Local import for safety
        except ImportError:
            print("Error: Could not import build_inverted_index. Index not rebuilt.")
            return

        print("Rebuilding search index...")
        self.inverted_index_en = bi_index(self.all_npc_data)
        print(f"Search index rebuilt. Total NPCs indexed: {len(self.all_npc_data)}")


if __name__ == "__main__":
    print("Search Engine Script Started.") # Early print for diagnostics
    xml_dir = "../data/xmls/"  # Relative to the 'src' directory where this script is
    engine = SearchEngine(xml_dir)

    if not engine.all_npc_data:
        print("Exiting: No data loaded for search engine.")
    else:
        # Original English query list (reduced for initial testing post-timeout issues)
        queries = [
            "Redcap",
            "Potion",
            "Healing Orb",
            "Dark Fairy Noble"
        ]
        # queries = [
        #     "Redcap",
        #     "Campfire",
        #     "Potion",
        #     "Potion of Magic",
        #     "Healing Orb",      # English equivalent of "회복 구슬"
        #     "Dark Fairy Noble", # English equivalent of "어둠의 요정 귀족"
        #     "Crystal",
        #     "Sabertooth",
        #     "Lost Pixie",
        #     "Bomb",
        #     "Scroll",
        #     "Reinforcement Crystal"
        # ]

        for query in queries:
            print(f"\nSearching for: '{query}'")
            results = engine.search(query)

            print(f"Results for '{query}': ({len(results)} found)")
            if results:
                for npc in results:
                    npc_name_display = f"{npc['npcName']['en']} (Original: {npc['npcName']['original']})" \
                                       if npc['npcName']['en'] != npc['npcName']['original'] \
                                       else npc['npcName']['en']
                    print(f"  NPC: {npc_name_display} (ID: {npc['npcTemplateId']}) from {os.path.basename(npc['source_file'])}")

            else:
                print("  No results found.")
            print("-" * 30)
