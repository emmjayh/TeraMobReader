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

        # NPC Selection Dropdown (initially hidden) - Placed within search_frame for simpler layout management here
        self.npc_selection_label = ttk.Label(search_frame, text="Select NPC:")
        self.npc_select_var = tk.StringVar()
        self.npc_combobox = ttk.Combobox(search_frame, textvariable=self.npc_select_var, state='readonly', width=47) # Adjusted width
        self.npc_combobox.bind('<<ComboboxSelected>>', self.display_selected_npc_details)

        # Initial hiding - will be managed by pack/pack_forget in perform_search
        # No need to pack them here if we pack_forget immediately after (or just don't pack yet)
        # For simplicity in this step, we'll add them to search_frame and then forget.
        # A more complex layout might use a dedicated frame for these that's managed.
        self.npc_selection_label.pack(side=tk.LEFT, padx=(10, 5)) # Add some padding to separate from search button
        self.npc_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.npc_selection_label.pack_forget()
        self.npc_combobox.pack_forget()


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

    def _display_npc_details_in_text_widget(self, npc_data):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END) # Clear before displaying new selection

        npc_name_en = npc_data.get('npcName', {}).get('en', 'N/A')
        npc_name_orig = npc_data.get('npcName', {}).get('original', 'N/A')
        npc_id_val = npc_data.get('npcTemplateId', 'N/A')
        source_file = os.path.basename(npc_data.get('source_file', 'N/A'))

        display_name = npc_name_en
        if npc_name_en != npc_name_orig and npc_name_orig != 'N/A':
            display_name += f" (Original: {npc_name_orig})"

        self.results_text.insert(tk.END, f"NPC: {display_name}\n")
        self.results_text.insert(tk.END, f"  ID: {npc_id_val}\n")
        self.results_text.insert(tk.END, f"  File: {source_file}\n")
        self.results_text.insert(tk.END, "  Items:\n")

        if npc_data.get('items'):
            for item_idx, item in enumerate(npc_data['items']):
                if item_idx < 10: # Limit displayed items per NPC
                    item_name_en = item.get('name', {}).get('en', 'N/A')
                    item_name_orig = item.get('name', {}).get('original', 'N/A')
                    item_id_val_item = item.get('templateId', 'N/A') # Unique var name

                    item_display_name = item_name_en
                    if item_name_en != item_name_orig and item_name_orig != 'N/A':
                        item_display_name += f" (Original: {item_name_orig})"
                    self.results_text.insert(tk.END, f"    - {item_display_name} (ID: {item_id_val_item})\n")
                elif item_idx == 10:
                    self.results_text.insert(tk.END, f"    ... and {len(npc_data['items']) - 10} more items.\n")
                    break
        else:
            self.results_text.insert(tk.END, "    - No items listed for this NPC.\n")
        self.results_text.insert(tk.END, "\n")
        self.results_text.config(state=tk.DISABLED)

    def display_selected_npc_details(self, event=None):
        selected_display_name = self.npc_select_var.get()
        selected_npc_data = None

        if not self.current_search_results or not selected_display_name:
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete('1.0', tk.END)
            self.results_text.insert(tk.END, "Please perform a search or select an NPC.\n")
            self.results_text.config(state=tk.DISABLED)
            return

        for npc_data_iter in self.current_search_results:
            iter_display_name = f"{npc_data_iter['npcName']['en']} (ID: {npc_data_iter['npcTemplateId']})"
            if iter_display_name == selected_display_name:
                selected_npc_data = npc_data_iter
                break

        if selected_npc_data:
            self._display_npc_details_in_text_widget(selected_npc_data)
            self.status_var.set(f"Displaying details for {selected_npc_data['npcName']['en']}.")
        else: # Should not happen if combobox values are correctly populated
            self.results_text.config(state=tk.NORMAL)
            self.results_text.delete('1.0', tk.END)
            self.results_text.insert(tk.END, f"Could not find details for: {selected_display_name}\n")
            self.results_text.config(state=tk.DISABLED)
            self.status_var.set(f"Error: Could not find details for selected NPC.")


    def perform_search(self):
        query = self.query_entry.get()
        if not query.strip():
            self.status_var.set("Please enter a search query.")
            return

        self.status_var.set(f"Searching for '{query}'...")
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)

        try:
            self.current_search_results = self.search_engine.search(query) # Store results
            results = self.current_search_results # Use local variable for clarity

            if len(results) > 1:
                self.results_text.insert(tk.END, f"{len(results)} NPCs found. Please select one from the dropdown.\n\n")
                npc_display_names = []
                for npc_data in results:
                    display_name = f"{npc_data['npcName']['en']} (ID: {npc_data['npcTemplateId']})"
                    npc_display_names.append(display_name)

                self.npc_combobox['values'] = npc_display_names
                self.npc_combobox.set('')

                # Ensure visibility using pack (assuming they were forgotten or not initially packed here)
                self.npc_selection_label.pack(side=tk.LEFT, padx=(10,5), before=self.npc_combobox) # Pack label before combobox
                self.npc_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)

                self.npc_combobox.current(0) # Select first item
                self.display_selected_npc_details() # Display its details
                self.status_var.set(f"Multiple results: {len(results)}. Select an NPC.")

            elif len(results) == 1:
                self.npc_selection_label.pack_forget()
                self.npc_combobox.pack_forget()
                self.npc_select_var.set('')

                self._display_npc_details_in_text_widget(results[0])
                self.status_var.set(f"Search complete. Found 1 NPC.")
            else: # No results
                self.npc_selection_label.pack_forget()
                self.npc_combobox.pack_forget()
                self.npc_select_var.set('')
                self.results_text.insert(tk.END, "No results found.\n")
                self.status_var.set("Search complete. No results found.")

        except Exception as e:
            self.results_text.insert(tk.END, f"An error occurred during search: {e}\n")
            self.status_var.set("Error during search.")
            print(f"Error during search: {e}")
            import traceback
            traceback.print_exc()

        self.results_text.config(state=tk.DISABLED) # Ensure it's disabled at the end

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
