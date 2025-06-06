# Version: 20240524.140000
import tkinter as tk
from tkinter import ttk, messagebox
import os
import traceback # For detailed error logging
from search_engine import SearchEngine
import xml_parser # For saving changes

class SearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Korean XML Search - Editor Mode")
        self.root.geometry("950x750") # Adjusted size for more columns

        current_script_dir = os.path.dirname(__file__)
        xml_dir = os.path.normpath(os.path.join(current_script_dir, '..', 'data', 'xmls'))

        self.search_engine = SearchEngine(xml_directory=xml_dir)

        # Internal state
        self.current_npc_items = []
        self.current_treeview_item_to_idx_map = {}
        self.current_npc_template_id = None
        self.current_npc_source_file = None
        self.current_npc_display_name_for_status = None # For status bar
        self.current_search_results = []
        self.active_edit_entry = None

        # --- Main UI Frames ---
        top_frame = ttk.Frame(root, padding="5")
        top_frame.pack(fill=tk.X, side=tk.TOP, pady=(0,5))

        self.search_frame = ttk.Frame(top_frame, padding="5")
        self.search_frame.pack(fill=tk.X)

        middle_frame = ttk.Frame(root, padding="5")
        middle_frame.pack(expand=True, fill=tk.BOTH)

        bottom_frame = ttk.Frame(root, padding="5")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5,0))

        # --- Search Controls ---
        ttk.Label(self.search_frame, text="English Query:").pack(side=tk.LEFT, padx=(0, 5))
        self.query_entry = ttk.Entry(self.search_frame, width=30)
        self.query_entry.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=5) # Don't expand entry too much
        self.query_entry.bind("<Return>", self.perform_search_event)

        self.search_button = ttk.Button(self.search_frame, text="Search", command=self.perform_search)
        self.search_button.pack(side=tk.LEFT, padx=(5, 10))

        self.npc_selection_label = ttk.Label(self.search_frame, text="Select NPC:")
        self.npc_selection_label.pack(side=tk.LEFT, padx=(0, 2))

        self.npc_select_var = tk.StringVar()
        self.npc_combobox = ttk.Combobox(self.search_frame, textvariable=self.npc_select_var, state='readonly', width=40)
        self.npc_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.npc_combobox.bind('<<ComboboxSelected>>', self.handle_npc_selection_change)

        self.npc_selection_label.pack_forget()
        self.npc_combobox.pack_forget()

        # --- Treeview for Items ---
        self.columns_config = {
            "item_id": {"heading": "Item ID", "width": 80, "data_key": "templateId", "type": str, "editable": False},
            "en_name": {"heading": "English Name", "width": 200, "data_key": "name.en", "type": str, "editable": False},
            "ko_name": {"heading": "Original Name", "width": 200, "data_key": "name.original", "type": str, "editable": False},
            "itembag_prob": {"heading": "Bag Prob.", "width": 80, "data_key": "itembag_probability", "type": float, "editable": True},
            "item_prob": {"heading": "Item Prob.", "width": 80, "data_key": "item_probability", "type": float, "editable": True},
            "min_qty": {"heading": "Min", "width": 60, "data_key": "min_quantity", "type": int, "editable": True},
            "max_qty": {"heading": "Max", "width": 60, "data_key": "max_quantity", "type": int, "editable": True}
        }
        column_ids = list(self.columns_config.keys())

        self.items_treeview = ttk.Treeview(middle_frame, columns=column_ids, show="headings", selectmode="browse")

        for col_id, col_info in self.columns_config.items():
            self.items_treeview.heading(col_id, text=col_info["heading"])
            self.items_treeview.column(col_id, width=col_info["width"], anchor=tk.W if col_info["type"] == str else tk.CENTER)

        tree_scrollbar_y = ttk.Scrollbar(middle_frame, orient="vertical", command=self.items_treeview.yview)
        self.items_treeview.configure(yscrollcommand=tree_scrollbar_y.set)
        tree_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scrollbar_x = ttk.Scrollbar(middle_frame, orient="horizontal", command=self.items_treeview.xview)
        self.items_treeview.configure(xscrollcommand=tree_scrollbar_x.set)
        tree_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.items_treeview.pack(expand=True, fill=tk.BOTH)
        self.items_treeview.bind("<Double-1>", self.on_treeview_double_click)

        # --- Action Buttons ---
        self.save_button = ttk.Button(bottom_frame, text="Save Changes to XML", command=self.save_changes_to_xml, state=tk.DISABLED)
        self.save_button.pack(side=tk.RIGHT, padx=5)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready. Translator TEST_MODE is ON.")

    def perform_search_event(self, event=None):
        self.perform_search()

    def perform_search(self):
        query = self.query_entry.get()
        if not query.strip():
            self.status_var.set("Please enter a search query.")
            return
        self.status_var.set(f"Searching for '{query}'...")

        self._clear_npc_data_display()

        self.current_search_results = self.search_engine.search(query)
        results = self.current_search_results

        if len(results) > 1:
            try:
                self.npc_selection_label.pack(side=tk.LEFT, padx=(10, 2))
                self.npc_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.search_frame.update_idletasks()

                npc_display_names = [f"{r['npcName']['en']} (ID: {r['npcTemplateId']})" for r in self.current_search_results]
                self.npc_combobox['values'] = npc_display_names

                if npc_display_names:
                    self.npc_combobox.current(0)
                    self.handle_npc_selection_change() # Loads first NPC, also updates status bar
                    # Update status bar for multi-result context *after* first NPC is loaded
                    self.status_var.set(f"{len(self.current_search_results)} NPCs found. Showing: '{self.current_npc_display_name_for_status}'. Use dropdown for others.")
                else:
                    self.npc_combobox.set('')
                    self._clear_npc_data_display()
                    self.status_var.set("Multiple results found, but an issue occurred populating dropdown.")
            except Exception as e:
                self.status_var.set("Error processing multiple NPC results. Check console.")
                print("Error occurred in multi-result processing block of perform_search:")
                traceback.print_exc()
                self.npc_selection_label.pack_forget()
                self.npc_combobox.pack_forget()
                self.npc_select_var.set('')
                self._clear_npc_data_display()
        elif len(results) == 1:
            self.npc_selection_label.pack_forget()
            self.npc_combobox.pack_forget()
            self.npc_select_var.set('')
            self._load_npc_data_into_gui(results[0])
        else:
            self.npc_selection_label.pack_forget()
            self.npc_combobox.pack_forget()
            self.npc_select_var.set('')
            self.status_var.set("No results found.")
            self._clear_npc_data_display()

    def handle_npc_selection_change(self, event=None):
        selected_display_name = self.npc_select_var.get()
        selected_npc_data = None
        if not self.current_search_results or not selected_display_name: return

        for npc_data_iter in self.current_search_results:
            iter_display_name = f"{npc_data_iter['npcName']['en']} (ID: {npc_data_iter['npcTemplateId']})"
            if iter_display_name == selected_display_name:
                selected_npc_data = npc_data_iter
                break
        if selected_npc_data:
            self._load_npc_data_into_gui(selected_npc_data)

    def _clear_npc_data_display(self):
        if self.active_edit_entry:
            self.active_edit_entry.destroy()
            self.active_edit_entry = None
        for i in self.items_treeview.get_children():
            self.items_treeview.delete(i)
        self.current_npc_items.clear()
        self.current_treeview_item_to_idx_map.clear()
        self.current_npc_template_id = None
        self.current_npc_source_file = None
        self.current_npc_display_name_for_status = None
        self.save_button.config(state=tk.DISABLED)
        # Do not clear results_text here as perform_search uses it for count message

    def _load_npc_data_into_gui(self, npc_data):
        # Clear previous NPC's items and state, but not the general results_text area
        if self.active_edit_entry: self.active_edit_entry.destroy(); self.active_edit_entry = None
        for i in self.items_treeview.get_children(): self.items_treeview.delete(i)
        self.current_npc_items.clear()
        self.current_treeview_item_to_idx_map.clear()

        self.current_npc_template_id = npc_data.get('npcTemplateId')
        self.current_npc_source_file = npc_data.get('source_file')
        self.current_npc_display_name_for_status = npc_data.get('npcName', {}).get('en', 'N/A')

        raw_items = npc_data.get('items', [])
        for item_data in raw_items:
            self.current_npc_items.append(dict(item_data))

        for idx, item_dict in enumerate(self.current_npc_items):
            values = []
            for col_id_key in self.columns_config: # Iterate in defined order
                col_info = self.columns_config[col_id_key]
                data_key = col_info["data_key"]
                val = None
                if "." in data_key:
                    key1, key2 = data_key.split(".")
                    val = item_dict.get(key1, {}).get(key2, '') # Default to empty string for display
                else:
                    val = item_dict.get(data_key, '')

                if col_info["type"] == float and isinstance(val, (float, int)):
                    val = f"{val:.4f}"
                elif val is None: # Ensure no None values are passed to Treeview
                    val = ''
                values.append(val)

            tree_item_id = self.items_treeview.insert("", tk.END, values=tuple(values))
            self.current_treeview_item_to_idx_map[tree_item_id] = idx

        status_msg = f"Displaying: {self.current_npc_display_name_for_status} (ID: {self.current_npc_template_id})"
        if self.current_npc_source_file:
            status_msg += f" from {os.path.basename(self.current_npc_source_file)}"
        self.status_var.set(status_msg)

        if self.current_npc_source_file and self.current_npc_template_id:
             self.save_button.config(state=tk.NORMAL)
        else:
             self.save_button.config(state=tk.DISABLED)


    def on_treeview_double_click(self, event):
        if self.active_edit_entry: self.active_edit_entry.destroy(); self.active_edit_entry = None

        tree_item_id = self.items_treeview.focus()
        if not tree_item_id: return

        column_id_str = self.items_treeview.identify_column(event.x)

        col_idx = int(column_id_str.replace('#','')) -1
        if 0 <= col_idx < len(self.columns_config):
            col_key_name = list(self.columns_config.keys())[col_idx]
            col_info = self.columns_config[col_key_name]

            if not col_info.get("editable", False):
                 self.status_var.set(f"Column '{col_info['heading']}' is not editable.")
                 return
        else:
            return

        x, y, width, height = self.items_treeview.bbox(tree_item_id, column_id_str)
        current_value = self.items_treeview.set(tree_item_id, column=column_id_str)

        self.active_edit_entry = ttk.Entry(self.items_treeview)
        self.active_edit_entry.place(x=x, y=y, width=width, height=height)
        self.active_edit_entry.insert(0, current_value)
        self.active_edit_entry.focus_set()
        self.active_edit_entry.bind("<Return>", lambda ev: self.save_cell_edit(ev, tree_item_id, col_key_name, self.active_edit_entry))
        self.active_edit_entry.bind("<FocusOut>", lambda ev: self.save_cell_edit(ev, tree_item_id, col_key_name, self.active_edit_entry))
        self.active_edit_entry.bind("<Escape>", lambda ev, ed=self.active_edit_entry: ed.destroy())


    def save_cell_edit(self, event, tree_item_id, column_key_name, entry_widget):
        if entry_widget != self.active_edit_entry:
            entry_widget.destroy() # Destroy if it's a stale call
            return

        new_value_str = entry_widget.get()
        entry_widget.destroy() # Destroy immediately after getting value
        self.active_edit_entry = None

        list_idx = self.current_treeview_item_to_idx_map.get(tree_item_id)
        if list_idx is None or list_idx >= len(self.current_npc_items):
            self.status_var.set("Error: Item reference lost during edit.")
            return

        col_info = self.columns_config[column_key_name]
        data_key = col_info["data_key"]
        expected_type = col_info["type"]
        validated_value = None

        try:
            if expected_type == int:
                validated_value = int(new_value_str)
                if validated_value < 0: raise ValueError("Quantity cannot be negative.")
                if data_key == "max_quantity":
                    min_val = self.current_npc_items[list_idx].get("min_quantity", 0)
                    if validated_value < min_val: raise ValueError("Max quantity < min.")
            elif expected_type == float:
                validated_value = float(new_value_str)
                if not (0.0 <= validated_value <= 1.0):
                     raise ValueError("Probability must be 0.0-1.0.")
            else:
                validated_value = new_value_str
        except ValueError as ve:
            self.status_var.set(f"Invalid value for {col_info['heading']}: {ve}")
            messagebox.showerror("Validation Error", f"Invalid value for {col_info['heading']}:\n{ve}\nOriginal value restored.")
            # Re-populate the cell with original value if validation fails by re-setting it from internal store
            original_value = self.current_npc_items[list_idx].get(data_key)
            if "." in data_key: # Handle nested for original value retrieval
                key1, key2 = data_key.split(".")
                original_value = self.current_npc_items[list_idx].get(key1, {}).get(key2, '')
            display_value = f"{original_value:.4f}" if expected_type == float and isinstance(original_value, (float,int)) else str(original_value if original_value is not None else '')
            self.items_treeview.set(tree_item_id, column=column_key_name, value=display_value)
            return

        display_value = f"{validated_value:.4f}" if expected_type == float else str(validated_value)
        self.items_treeview.set(tree_item_id, column=column_key_name, value=display_value)

        if "." in data_key:
            key1, key2 = data_key.split(".")
            if key1 not in self.current_npc_items[list_idx]: self.current_npc_items[list_idx][key1] = {}
            self.current_npc_items[list_idx][key1][key2] = validated_value
        else:
            self.current_npc_items[list_idx][data_key] = validated_value

        self.status_var.set(f"Updated {col_info['heading']} for item ID {self.current_npc_items[list_idx]['templateId']}.")


    def save_changes_to_xml(self):
        if not self.current_npc_source_file or self.current_npc_template_id is None:
            messagebox.showerror("Error", "No NPC data loaded or source file unknown to save to.")
            self.status_var.set("Save failed: No NPC data loaded.")
            return

        self.status_var.set(f"Saving changes for NPC ID {self.current_npc_template_id} to {os.path.basename(self.current_npc_source_file)}...")
        try:
            items_to_save = []
            for item_gui_data in self.current_npc_items:
                item_to_save = {
                    'templateId': item_gui_data.get('templateId'),
                    'name': {'original': item_gui_data.get('name',{}).get('original')},
                    'itembag_probability': item_gui_data.get('itembag_probability'),
                    'item_probability': item_gui_data.get('item_probability'),
                    'min_quantity': item_gui_data.get('min_quantity'),
                    'max_quantity': item_gui_data.get('max_quantity')
                }
                items_to_save.append(item_to_save)

            success = xml_parser.update_compensation_data(
                self.current_npc_source_file,
                self.current_npc_template_id,
                items_to_save
            )

            if success:
                self.search_engine.index_single_file(self.current_npc_source_file)
                self.status_var.set(f"Changes saved to {os.path.basename(self.current_npc_source_file)} and index updated.")
                messagebox.showinfo("Success", "Changes saved and index updated.")
            else:
                self.status_var.set("Error saving changes to XML. Check console.")
                messagebox.showerror("Error", "Failed to save changes to XML. See console for details.")
        except Exception as e:
            self.status_var.set(f"Exception during save: {e}")
            messagebox.showerror("Save Error", f"An unexpected error occurred: {e}")
            print(f"Exception during save_changes_to_xml: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    print("GUI Script Started.")
    try:
        root = tk.Tk()
        app = SearchApp(root)
        print("Tkinter root window created and SearchApp initialized.")
        root.mainloop()
        print("Tkinter mainloop finished.")
    except tk.TclError as e:
        print(f"Could not initialize Tkinter GUI: {e}")
        print("This might be because the environment does not support GUIs.")
        if 'app' in locals() and hasattr(app, 'search_engine') and app.search_engine and app.search_engine.all_npc_data:
             print("SearchEngine initialized successfully in headless fallback.")
        else:
             print("SearchEngine did not initialize successfully in headless fallback.")
    except Exception as e:
        print(f"An unexpected error occurred while trying to start the GUI: {e}")
        traceback.print_exc()
