import tkinter as tk
from tkinter import ttk  # For themed widgets, optional
from tkinter import scrolledtext
import os
from search_engine import SearchEngine # Assuming search_engine.py is in the same directory (src)
import xml_parser # For saving changes

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

        self.current_npc_items = [] # To store items of the currently displayed NPC
        self.current_treeview_item_to_idx_map = {} # To map treeview item id to list index
        self.active_edit_entry = None # To keep track of any active editing entry
        self.current_npc_template_id = None # To store the templateId of the currently displayed NPC
        self.current_npc_source_file = None # To store the source_file of the currently displayed NPC

        # Define editable columns and their mapping to data keys
        self.editable_columns_map = {
            "Bag Prob.": {"key": "itembag_probability", "type": float},
            "Item Prob.": {"key": "item_probability", "type": float},
            "Min": {"key": "min_quantity", "type": int},
            "Max": {"key": "max_quantity", "type": int}
        }
        self.editable_column_headings = list(self.editable_columns_map.keys())


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

        # Results Display - Changed to ttk.Treeview
        columns = ("item_id", "en_name", "ko_name", "itembag_prob", "item_prob", "min_qty", "max_qty")
        self.results_text = ttk.Treeview(root, columns=columns, show="headings")

        self.results_text.heading("item_id", text="Item ID")
        self.results_text.heading("en_name", text="English Name")
        self.results_text.heading("ko_name", text="Korean Name")
        self.results_text.heading("itembag_prob", text="Bag Prob.")
        self.results_text.heading("item_prob", text="Item Prob.")
        self.results_text.heading("min_qty", text="Min")
        self.results_text.heading("max_qty", text="Max")

        # Adjust column widths (example widths, can be fine-tuned)
        self.results_text.column("item_id", width=70, anchor=tk.W)
        self.results_text.column("en_name", width=200, anchor=tk.W)
        self.results_text.column("ko_name", width=200, anchor=tk.W)
        self.results_text.column("itembag_prob", width=70, anchor=tk.E)
        self.results_text.column("item_prob", width=70, anchor=tk.E)
        self.results_text.column("min_qty", width=50, anchor=tk.E)
        self.results_text.column("max_qty", width=50, anchor=tk.E)

        # Scrollbar for Treeview
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(padx=(10,0), pady=(0,10), expand=True, fill=tk.BOTH, side=tk.LEFT)
        scrollbar.pack(padx=(0,10), pady=(0,10), fill=tk.Y, side=tk.RIGHT)

        # Save Button
        self.save_button = ttk.Button(root, text="Save Changes", command=self.save_changes_to_xml)
        # Place it appropriately, e.g., below the treeview or in its own frame
        # For simplicity, packing it below the status bar for now, but a dedicated frame is better.
        self.save_button.pack(side=tk.BOTTOM, pady=5)

        # Add a status bar (optional)
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready. Translator TEST_MODE is ON.")

        # Context Menu for Treeview
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Copy Selected Rows", command=self.copy_selected_items)

        self.results_text.bind("<Button-3>", self.show_context_menu)
        self.results_text.bind("<Double-1>", self.on_treeview_double_click)


    def on_treeview_double_click(self, event):
        """Handle double-click events on the Treeview for cell editing."""
        if self.active_edit_entry: # If an edit is already active, destroy it
            self.active_edit_entry.destroy()
            self.active_edit_entry = None

        region = self.results_text.identify_region(event.x, event.y)
        if region != "cell":
            return

        tree_item_id = self.results_text.identify_row(event.y)
        column_idx_str = self.results_text.identify_column(event.x) # Returns '#col_num'
        column_idx = int(column_idx_str.replace('#', '')) - 1 # Convert to 0-based index

        # Get column heading to check if it's editable
        # Treeview columns are 1-indexed in some contexts, 0-indexed in others for values.
        # self.results_text.heading gets info about the column definition.
        # We need the actual column name as defined in 'columns' tuple during Treeview creation.
        actual_column_key = self.results_text['columns'][column_idx]
        # Now get the display heading for this key
        column_heading = self.results_text.heading(actual_column_key, "text")


        if column_heading in self.editable_column_headings:
            x, y, width, height = self.results_text.bbox(tree_item_id, column_idx_str)

            current_value = self.results_text.item(tree_item_id, "values")[column_idx]

            entry_var = tk.StringVar(value=current_value)
            entry = ttk.Entry(self.root, textvariable=entry_var)
            entry.place(x=x, y=y, width=width, height=height, anchor='nw')
            entry.focus_set()
            self.active_edit_entry = entry # Track the active entry

            # Pass tree_item_id (Treeview's internal ID), actual_column_key (data key), and entry widget
            entry.bind("<Return>", lambda e, ti=tree_item_id, ck=actual_column_key, ew=entry: \
                       self.save_cell_edit(e, ti, ck, ew))
            entry.bind("<FocusOut>", lambda e, ti=tree_item_id, ck=actual_column_key, ew=entry: \
                       self.save_cell_edit(e, ti, ck, ew))
            entry.bind("<Escape>", lambda e, ew=entry: ew.destroy()) # Allow Esc to cancel

    def save_cell_edit(self, event, tree_item_id, column_key, entry_widget):
        """Save the edited cell value."""
        if entry_widget is None or not entry_widget.winfo_exists(): # Check if widget still exists
            return

        new_value_str = entry_widget.get()
        entry_widget.destroy()
        self.active_edit_entry = None


        # Determine the data key and type for validation from the actual_column_key
        # This requires mapping the actual_column_key (e.g., 'itembag_prob') back to the display name
        # or directly using the actual_column_key if we adjust self.editable_columns_map structure.
        # For now, let's find the display name for actual_column_key
        column_heading_to_find = ""
        for k_idx, c_key in enumerate(self.results_text['columns']):
            if c_key == column_key:
                column_heading_to_find = self.results_text.heading(c_key, "text")
                break

        if not column_heading_to_find or column_heading_to_find not in self.editable_columns_map:
            self.status_var.set(f"Error: Column '{column_heading_to_find}' not configured for editing.")
            return

        edit_info = self.editable_columns_map[column_heading_to_find]
        data_key = edit_info["key"]
        expected_type = edit_info["type"]
        validated_value = None

        try:
            if expected_type == float:
                validated_value = float(new_value_str)
                # Optional: Add specific range validation for probabilities (e.g., 0.0 to 1.0)
            elif expected_type == int:
                validated_value = int(new_value_str)
                if validated_value < 0: # Quantities should generally be non-negative
                    raise ValueError("Quantity cannot be negative.")
            else: # Should not happen if map is correctly defined
                raise TypeError(f"Unsupported data type for column {column_heading_to_find}")

        except ValueError as ve:
            self.status_var.set(f"Invalid input for {column_heading_to_find}: {new_value_str}. Error: {ve}")
            print(f"Validation Error for {data_key}: {ve}")
            return
        except TypeError as te: # Should not happen
            self.status_var.set(f"Configuration error: {te}")
            print(f"Type Error: {te}")
            return

        # Update Treeview
        # Find the column index for Treeview.set
        col_idx_for_set = -1
        for idx, key_name in enumerate(self.results_text['columns']):
            if key_name == column_key:
                col_idx_for_set = idx
                break

        if col_idx_for_set != -1:
             # For probabilities, format them back to string with precision
            if expected_type == float:
                self.results_text.set(tree_item_id, column=f"#{col_idx_for_set + 1}", value=f"{validated_value:.4f}")
            else:
                self.results_text.set(tree_item_id, column=f"#{col_idx_for_set + 1}", value=validated_value)


        # Update in-memory data (self.current_npc_items)
        # This assumes tree_item_id directly maps to the index in self.current_npc_items
        # This needs to be ensured during perform_search when populating the tree.
        try:
            # If tree_item_id is the list index (after ensuring it's int)
            list_idx = self.current_treeview_item_to_idx_map.get(tree_item_id)
            if list_idx is not None and 0 <= list_idx < len(self.current_npc_items):
                self.current_npc_items[list_idx][data_key] = validated_value
                self.status_var.set(f"Updated {column_heading_to_find} for item.")
                # print(f"Updated in-memory: self.current_npc_items[{list_idx}][{data_key}] = {validated_value}")
            else:
                self.status_var.set(f"Error updating in-memory data: Invalid item identifier '{tree_item_id}'.")
                # print(f"Error: Could not find item with tree_item_id {tree_item_id} in map or current_npc_items.")

        except Exception as e:
            self.status_var.set(f"Error updating in-memory store: {e}")
            print(f"Error updating self.current_npc_items: {e}")
            import traceback
            traceback.print_exc()


    def show_context_menu(self, event):
        """Display the context menu on right-click."""
        # Select row under mouse if not already selected
        iid = self.results_text.identify_row(event.y)
        if iid:
            if not self.results_text.selection(): # If no selection, select the item under cursor
                 self.results_text.selection_set(iid)
            elif iid not in self.results_text.selection(): # If item under cursor is not part of current selection, clear and select
                self.results_text.selection_set(iid)

        self.context_menu.tk_popup(event.x_root, event.y_root)

    def copy_selected_items(self, event=None):
        """Copy selected items in the Treeview to the clipboard, tab-separated."""
        selected_ids = self.results_text.selection()
        if not selected_ids:
            self.status_var.set("No items selected to copy.")
            return

        clipboard_data = []
        for item_id in selected_ids:
            row_values = self.results_text.item(item_id, 'values')
            clipboard_data.append("\t".join(map(str, row_values)))

        if clipboard_data:
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(clipboard_data))
            self.status_var.set(f"Copied {len(selected_ids)} item(s) to clipboard.")
        else:
            self.status_var.set("No data to copy for selected items.")


    def perform_search_event(self, event=None): # Added event=None for binding
        self.perform_search()

    def perform_search(self):
        query = self.query_entry.get()
        if not query.strip():
            self.status_var.set("Please enter a search query.")
            return

        self.status_var.set(f"Searching for '{query}'...")
        # Clear previous results from Treeview and internal data stores
        for i in self.results_text.get_children():
            self.results_text.delete(i)
        self.current_npc_items.clear()
        self.current_treeview_item_to_idx_map.clear()
        self.current_npc_template_id = None # Reset current NPC info
        self.current_npc_source_file = None


        try:
            results = self.search_engine.search(query) # This should return a list of dicts

            if results:
                first_npc_original_data = results[0] # Focus on the first NPC

                # Store details of the NPC whose items are being displayed
                self.current_npc_template_id = first_npc_original_data.get('npcTemplateId')
                # Ensure source_file is the full path for saving
                self.current_npc_source_file = first_npc_original_data.get('source_file')

                # Make a deep copy for local editing if necessary, or ensure search_engine provides mutable copies
                # For this subtask, we'll assume items can be directly used or search_engine handles copy
                # However, for safety, let's make a shallow copy of the item list for now.
                # A proper deepcopy might be needed if item dicts contain mutable structures like other dicts/lists.
                # from copy import deepcopy
                # self.current_npc_items = deepcopy(first_npc_original_data.get('items', []))

                # Store items from the first NPC
                # We need a list of dictionaries.
                original_items = first_npc_original_data.get('items', [])
                self.current_npc_items = [dict(item) for item in original_items] # Create shallow copies of item dicts


                npc_name_en = first_npc_original_data.get('npcName', {}).get('en', 'N/A')
                npc_name_orig = first_npc_original_data.get('npcName', {}).get('original', 'N/A')
                npc_id_val = self.current_npc_template_id # Use stored ID

                # Display basename in GUI, but use full path for saving
                source_file_display = os.path.basename(self.current_npc_source_file) if self.current_npc_source_file else 'N/A'


                display_name = npc_name_en
                if npc_name_en != npc_name_orig and npc_name_orig != 'N/A':
                    display_name += f" (Original: {npc_name_orig})"

                status_message = f"Displaying items for NPC: {display_name} (ID: {npc_id_val}) from {source_file_display}."
                if len(results) > 1:
                    status_message += f" Found {len(results)} NPCs in total. Showing items for the first one."

                self.status_var.set(status_message)

                if self.current_npc_items:
                    for list_idx, item_data in enumerate(self.current_npc_items):
                        # Use list_idx as the iid for the Treeview row for easy mapping
                        tree_item_id = str(list_idx) # Treeview iid must be a string if not numeric
                        self.current_treeview_item_to_idx_map[tree_item_id] = list_idx

                        item_id_val = item_data.get('templateId', 'N/A')
                        en_name = item_data.get('name', {}).get('en', 'N/A')
                        ko_name = item_data.get('name', {}).get('original', 'N/A')
                        itembag_prob = item_data.get('itembag_probability', 0.0)
                        item_prob = item_data.get('item_probability', 0.0)
                        min_qty = item_data.get('min_quantity', 1)
                        max_qty = item_data.get('max_quantity', 1)

                        self.results_text.insert("", tk.END, iid=tree_item_id, values=(
                            item_id_val, en_name, ko_name,
                            f"{itembag_prob:.4f}", f"{item_prob:.4f}", # Format probabilities
                            min_qty, max_qty
                        ))
                else:
                    # Insert a placeholder or update status if no items for the first NPC
                    self.results_text.insert("", tk.END, values=("N/A", "No items listed for this NPC.", "", "", "", "", ""))
                    self.status_var.set(f"{status_message} This NPC has no items listed.")
            else:
                self.status_var.set("Search complete. No results found.")
        except Exception as e:
            self.status_var.set(f"An error occurred: {e}")
            print(f"Error during search: {e}") # Also print to console for debugging
            import traceback
            traceback.print_exc()

    def save_changes_to_xml(self):
        if not self.current_npc_template_id or not self.current_npc_source_file:
            self.status_var.set("No NPC data loaded to save.")
            return

        if not self.current_npc_items:
            self.status_var.set("No items to save for the current NPC.")
            # Optionally, consider if saving an empty item list should clear it in XML.
            # For now, requiring items to be present.
            # Or, allow saving to clear items:
            # print("Warning: Saving an empty item list for NPC.")
            pass # Allow proceeding to save an empty list if desired by xml_parser logic

        try:
            # Ensure current_npc_source_file is the absolute path
            # It should be already from how it's stored from search_engine results
            success = xml_parser.update_compensation_data(
                self.current_npc_source_file,
                self.current_npc_template_id,
                self.current_npc_items
            )
            if success:
                # Refresh search engine data for the modified file
                self.search_engine.index_single_file(self.current_npc_source_file)
                self.status_var.set(f"Changes saved to {os.path.basename(self.current_npc_source_file)} and index updated.")
            else:
                self.status_var.set("Error saving changes to XML.")
        except Exception as e:
            self.status_var.set(f"Failed to save changes: {e}")
            print(f"Error calling update_compensation_data or re-indexing: {e}")
            import traceback
            traceback.print_exc()


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
