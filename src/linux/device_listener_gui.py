# /src/linux/device_listener_gui.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue

# Safe local package resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import JoyToKeyConfigParser

class ControlToKeyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ControlToKey (Hospital Accessibility Engine)")
        self.root.geometry("850x500")
        self.root.minsize(700, 400)
        
        # Load and manage profiles path structures
        self.profiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
        self.parser = JoyToKeyConfigParser(self.profiles_dir)
        self.parser.load_all_profiles()
        
        # Safe cross-thread queue communication channel
        self.gui_queue = queue.Queue()
        self.active_profile_name = "Main"
        
        # Direct Translation Array matching JoyToKey display logic
        self.joytokey_labels = {
            "axis1n": "Stick1: Left", "axis1p": "Stick1: Right",
            "axis2n": "Stick1: Up",   "axis2p": "Stick1: Down",
            "axis3n": "Stick2: Left", "axis3p": "Stick2: Right",
            "axis4n": "Stick2: Up",   "axis4p": "Stick2: Down",
            "pov1u": "POV: Up",       "pov1d": "POV: Down",
            "pov1l": "POV: Left",     "pov1r": "POV: Right",
            1: "Button 1 (A)",        2: "Button 2 (B)",
            3: "Button 3 (X)",        4: "Button 4 (Y)",
            5: "Button 5 (LB)",       6: "Button 6 (RB)",
            7: "Button 7 (LT)",       8: "Button 8 (RT)",
            9: "Button 9 (Back)",     10: "Button 10 (Start)",
            11: "Button 11 (L3)",     12: "Button 12 (R3)"
        }

        self._build_ui_layout()
        self._populate_profiles()
        self._start_hardware_polling()
        self.root.after(100, self._process_gui_queue)

    def _build_ui_layout(self):
        """Generates the classic JoyToKey Dual-Pane Split Interface Layout."""
        # Top Menu Control Matrix Bar
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Refresh Profiles", command=self._refresh_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu_bar)

        # Base Master Main Window Frame container 
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ----------------------------------------------------
        # LEFT PANE: Profiles Selection Matrix List
        # ----------------------------------------------------
        left_pane = ttk.LabelFrame(main_frame, text=" Profiles Layout Files ", padding="5")
        left_pane.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.profile_listbox = tk.Listbox(left_pane, width=25, font=("Arial", 10))
        self.profile_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.profile_listbox.bind('<<ListboxSelect>>', self._on_profile_changed)

        left_scroll = ttk.Scrollbar(left_pane, orient=tk.VERTICAL, command=self.profile_listbox.yview)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.profile_listbox.config(yscrollcommand=left_scroll.set)

        # ----------------------------------------------------
        # RIGHT PANE: Button & Macro Assignments Map View Grid
        # ----------------------------------------------------
        right_pane = ttk.LabelFrame(main_frame, text=" Configured Control Assignments ", padding="5")
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Configure columns inside the Treeview grid container system
        columns = ("control", "mapping", "details")
        self.mapping_tree = ttk.Treeview(right_pane, columns=columns, show="headings", selectmode="browse")
        
        self.mapping_tree.heading("control", text="Target Joystick Input Button/Axis")
        self.mapping_tree.heading("mapping", text="Mapped Command Type")
        self.mapping_tree.heading("details", text="Assigned Macro Output Matrix Target")

        self.mapping_tree.column("control", width=180, anchor=tk.W)
        self.mapping_tree.column("mapping", width=150, anchor=tk.CENTER)
        self.mapping_tree.column("details", width=300, anchor=tk.W)

        self.mapping_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        right_scroll = ttk.Scrollbar(right_pane, orient=tk.VERTICAL, command=self.mapping_tree.yview)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mapping_tree.config(yscrollcommand=right_scroll.set)
        
        # Configure Row Highlighting Tags matching JoyToKey's active state highlights
        self.mapping_tree.tag_configure('active_press', background='#cce5ff', font=('Arial', 10, 'bold'))
        self.mapping_tree.tag_configure('normal_row', background='white')

    def _populate_profiles(self):
        self.profile_listbox.delete(0, tk.END)
        if not self.parser.loaded_profiles:
            # Inject structural safety placeholder fallback block arrays
            self.parser.loaded_profiles["Main"] = {"threshold": 4000, "buttons": {}, "axes": {}}
            
        for name in sorted(self.parser.loaded_profiles.keys()):
            self.profile_listbox.insert(tk.END, name)
            
        # Select primary entry by default baseline execution setup
        self.profile_listbox.selection_set(0)
        self.active_profile_name = self.profile_listbox.get(0)
        self._update_mapping_tree_display()

    def _on_profile_changed(self, event):
        selection = self.profile_listbox.curselection()
        if selection:
            self.active_profile_name = self.profile_listbox.get(selection[0])
            self._update_mapping_tree_display()

    def _update_mapping_tree_display(self):
        """Clears and re-draws the mapping grid rows to match the active .cfg profile."""
        # Clear existing elements securely
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)
            
        profile_data = self.parser.loaded_profiles.get(self.active_profile_name, {"buttons": {}, "axes": {}})

        # Standard JoyToKey initialization baseline loop sequence
        # First layout sequence: structural axes processing tracking loops
        for axis_key in ["axis1n", "axis1p", "axis2n", "axis2p", "axis3n", "axis3p", "axis4n", "axis4p", "pov1u", "pov1d", "pov1l", "pov1r"]:
            label = self.joytokey_labels.get(axis_key, axis_key)
            mapping = profile_data.get("axes", {}).get(axis_key)
            self._insert_row_by_mapping(axis_key, label, mapping)

        # Second layout sequence: discrete face button structural lines maps tracking
        for btn_id in range(1, 13):
            label = self.joytokey_labels.get(btn_id, f"Button {btn_id}")
            mapping = profile_data.get("buttons", {}).get(btn_id)
            self._insert_row_by_mapping(btn_id, label, mapping)

    def _insert_row_by_mapping(self, item_id, label, mapping):
        if not mapping:
            self.mapping_tree.insert("", tk.END, iid=str(item_id), values=(label, "Disabled", "None"), tags=('normal_row',))
            return
            
        map_type = mapping.get("type", "UNKNOWN")
        if map_type == "KEYBOARD":
            keys_str = ", ".join([f"VK({k})" for k in mapping.get("keys", [])])
            self.mapping_tree.insert("", tk.END, iid=str(item_id), values=(label, "Keyboard (Macro)", keys_str), tags=('normal_row',))
        elif map_type == "MOUSE":
            details = f"X: {mapping.get('x',0)} | Y: {mapping.get('y',0)} | Wheel: {mapping.get('wheel',0)}"
            self.mapping_tree.insert("", tk.END, iid=str(item_id), values=(label, "Mouse Speed Proportional", details), tags=('normal_row',))
        elif map_type == "PROFILE_SHIFT":
            details = f"Hold to Switch -> [{mapping.get('target','')}]"
            self.mapping_tree.insert("", tk.END, iid=str(item_id), values=(label, "Profile Layer Shift Chord", details), tags=('normal_row',))
        else:
            self.mapping_tree.insert("", tk.END, iid=str(item_id), values=(label, "Disabled", "None"), tags=('normal_row',))

    def _start_hardware_polling(self):
        """Spins up an independent runtime thread worker to pull inputs off hardware."""
        self.polling_thread = threading.Thread(target=self._hardware_loop_worker, daemon=True)
        self.polling_thread.start()

    def _hardware_loop_worker(self):
        """Headless background tracking framework loops routing events directly to the UI."""
        # Note: In a production build, your evdev logic runs here.
        # Instead of directly processing inputs into the OS blindly, we pipe states to the GUI queue:
        # e.g., self.gui_queue.put(("PRESS", btn_id)) or self.gui_queue.put(("RELEASE", btn_id))
        pass

    def _process_gui_queue(self):
        """Pulls raw peripheral data off the thread queue to dynamically paint row highlights."""
        try:
            while True:
                event_type, target_id = self.gui_queue.get_nowait()
                if self.mapping_tree.exists(str(target_id)):
                    if event_type == "PRESS":
                        self.mapping_tree.item(str(target_id), tags=('active_press',))
                    else:
                        self.mapping_tree.item(str(target_id), tags=('normal_row',))
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        self.root.after(50, self._process_gui_queue)

    def _refresh_all(self):
        self.parser.load_all_profiles()
        self._populate_profiles()
        messagebox.showinfo("ControlToKey Engine", "Hospital configurations re-indexed and successfully refreshed!")

if __name__ == "__main__":
    root = tk.Tk()
app = ControlToKeyGUI(root)
root.mainloop()

---

### 🔀 Connecting the GUI Module to Your Platform Entry Scripts

To make this GUI display your configurations on startup, you must update your direct platform execution entry point scripts to wrap this interface context around your application layout handlers.

Update your **`/src/linux/main.py`** (and mirror this structure for your future `/src/windows/main.py` file) to initialize the interface layout lifecycle:

```python
# /src/linux/main.py
import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from device_listener_gui import ControlToKeyGUI

def main():
    print("[*] ControlToKey UI Subsystem Active. Booting display frame wrappers...")
    
    # Initialize the Tkinter frame execution loop engine
    root = tk.Tk()
    app = ControlToKeyGUI(root)
    
    # Run the window graphics rendering lifecycle
    root.mainloop()

if __name__ == "__main__":
    main()
