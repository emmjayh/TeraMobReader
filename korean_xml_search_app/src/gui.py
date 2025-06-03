import tkinter as tk
from tkinter import ttk  # For themed widgets, optional
from tkinter import scrolledtext
import os
from search_engine import SearchEngine # Assuming search_engine.py is in the same directory (src)

class SearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Korean XML Search")

        # Initialize SearchEngine
        # Correctly determine xml_dir relative to this script (gui.py in src)
        # os.path.dirname(__file__) gives the directory of the current script (src)
        # Then go up one level ('..') to the project root, then into 'data/xmls'
        current_script_dir = os.path.dirname(__file__)
        xml_dir = os.path.normpath(os.path.join(current_script_dir, '..', 'data', 'xmls'))

        print(f"GUI: Initializing SearchEngine with XML directory: {xml_dir}")
        self.search_engine = SearchEngine(xml_directory=xml_dir)
        print("GUI: SearchEngine initialized.")

        # --- UI Elements ---
        # Search Frame
        search_frame = ttk.Frame(root, padding="10")
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(search_frame, text="Enter English Query:").pack(side=tk.LEFT, padx=(0, 5))

        self.query_entry = ttk.Entry(search_frame, width=50)
        self.query_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.query_entry.bind("<Return>", self.perform_search_event) # Bind Enter key

        self.search_button = ttk.Button(search_frame, text="Search", command=self.perform_search)
        self.search_button.pack(side=tk.LEFT, padx=(5, 0))

        # Results Display
        self.results_text = scrolledtext.ScrolledText(root, width=100, height=30, wrap=tk.WORD, state=tk.DISABLED)
        self.results_text.pack(padx=10, pady=(0,10), expand=True, fill=tk.BOTH)

        # Add a status bar (optional)
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready. Translator TEST_MODE is ON.")


    def perform_search_event(self, event=None): # Added event=None for binding
        self.perform_search()

    def perform_search(self):
        query = self.query_entry.get()
        if not query.strip():
            self.status_var.set("Please enter a search query.")
            return

        self.status_var.set(f"Searching for '{query}'...")
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)

        try:
            results = self.search_engine.search(query)

            if results:
                self.results_text.insert(tk.END, f"Found {len(results)} NPC(s) matching '{query}':\n\n")
                for npc in results:
                    npc_name_en = npc.get('npcName', {}).get('en', 'N/A')
                    npc_name_orig = npc.get('npcName', {}).get('original', 'N/A')
                    npc_id_val = npc.get('npcTemplateId', 'N/A') # Renamed to avoid conflict with npc_id var
                    source_file = os.path.basename(npc.get('source_file', 'N/A'))

                    display_name = npc_name_en
                    if npc_name_en != npc_name_orig and npc_name_orig != 'N/A':
                        display_name += f" (Original: {npc_name_orig})"

                    self.results_text.insert(tk.END, f"NPC: {display_name}\n")
                    self.results_text.insert(tk.END, f"  ID: {npc_id_val}\n")
                    self.results_text.insert(tk.END, f"  File: {source_file}\n")
                    self.results_text.insert(tk.END, "  Items:\n")

                    if npc.get('items'):
                        for item_idx, item in enumerate(npc['items']):
                            if item_idx < 10: # Limit displayed items per NPC for very long lists
                                item_name_en = item.get('name', {}).get('en', 'N/A')
                                item_name_orig = item.get('name', {}).get('original', 'N/A')
                                item_id_val = item.get('templateId', 'N/A') # Renamed

                                item_display_name = item_name_en
                                if item_name_en != item_name_orig and item_name_orig != 'N/A':
                                    item_display_name += f" (Original: {item_name_orig})"

                                self.results_text.insert(tk.END, f"    - {item_display_name} (ID: {item_id_val})\n")
                            elif item_idx == 10:
                                self.results_text.insert(tk.END, f"    ... and {len(npc['items']) - 10} more items.\n")
                                break
                    else:
                        self.results_text.insert(tk.END, "    - No items listed for this NPC.\n")
                    self.results_text.insert(tk.END, "\n")
                self.status_var.set(f"Search complete. Found {len(results)} NPC(s).")
            else:
                self.results_text.insert(tk.END, "No results found.\n")
                self.status_var.set("Search complete. No results found.")
        except Exception as e:
            self.results_text.insert(tk.END, f"An error occurred during search: {e}\n")
            self.status_var.set("Error during search.")
            print(f"Error during search: {e}") # Also print to console for debugging
            import traceback
            traceback.print_exc()


        self.results_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    print("GUI Script Started.")
    # Check if running in an environment that supports GUIs
    # For sandboxed environments, this might not work or might need Xvfb
    try:
        root = tk.Tk()
        app = SearchApp(root)
        print("Tkinter root window created and SearchApp initialized.")
        root.mainloop()
        print("Tkinter mainloop finished.")
    except tk.TclError as e:
        print(f"Could not initialize Tkinter GUI: {e}")
        print("This might be because the environment does not support GUIs (e.g., a headless server or sandbox without X11 forwarding).")
        print("The backend logic (SearchEngine, parsing, indexing) should still be functional and testable via scripts.")
        # Fallback for headless environment: print a success message if SearchEngine initialized
        if 'app' in locals() and app.search_engine and app.search_engine.all_npc_data:
             print("SearchEngine initialized successfully in headless fallback.")
        else:
             print("SearchEngine did not initialize successfully in headless fallback.")
    except Exception as e:
        print(f"An unexpected error occurred while trying to start the GUI: {e}")
        import traceback
        traceback.print_exc()
