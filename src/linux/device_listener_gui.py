# /src/linux/device_listener_gui.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import queue
import configparser
import evdev
from evdev import ecodes

# Safe local package resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import JoyToKeyConfigParser

class ControlToKeyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ControlToKey (Hospital Accessibility Engine)")
        self.root.geometry("900x550")
        self.root.minsize(750, 450)
        
        self.profiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
        if not os.path.exists(self.profiles_dir):
            os.makedirs(profiles_dir)
            
        self.parser = JoyToKeyConfigParser(self.profiles_dir)
        self.parser.load_all_profiles()
        self.auto_maps = self._load_auto_target_mappings()
        
        self.gui_queue = queue.Queue()
        self.active_profile_name = "Main"
        
        # Mapping labels matching standard configurations
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
        
        # Start Window Detection Watcher Engine
        self.tracking_running = True
        self.tracker_thread = threading.Thread(target=self._window_tracker_loop, daemon=True)
        self.tracker_thread.start()
        
        self.root.after(100, self._process_gui_queue)

        def _hardware_loop_worker(self):
        """Linux Gamepad Input Device Tracker Hook."""
        
        device_path = "/dev/input/by-id/usb-Logitech_Gamepad_F310_-event-joystick"
        if not os.path.exists(device_path):
            device_path = "/dev/input/event0"
            
        if not os.path.exists(device_path):
            return
            
        try:
            device = evdev.InputDevice(device_path)
            device.grab()
            for event in device.read_loop():
                if not self.tracking_running: break
                if event.type == ecodes.EV_KEY and event.code in self.btn_map:
                    btn_id = self.btn_map[event.code]
                    if event.value == 1:
                        self.gui_queue.put(("PRESS", btn_id))
                        self.process_button(btn_id, True)
                    elif event.value == 0:
                        self.gui_queue.put(("RELEASE", btn_id))
                        self.process_button(btn_id, False)
        except Exception:
            pass

    def _build_ui_layout(self):
        # Configuration Menu Management Hooks
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Profile", command=self._create_new_profile)
        file_menu.add_command(label="Link Active Window to Profile", command=self._link_current_window_target)
        file_menu.add_command(label="Refresh Profiles", command=self._refresh_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu_bar)

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # LEFT PANE: Profile Directories Management Frame
        left_pane = ttk.LabelFrame(main_frame, text=" Profiles Layout Files ", padding="5")
        left_pane.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.profile_listbox = tk.Listbox(left_pane, width=25, font=("Arial", 10))
        self.profile_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.profile_listbox.bind('<<ListboxSelect>>', self._on_profile_changed)

        left_scroll = ttk.Scrollbar(left_pane, orient=tk.VERTICAL, command=self.profile_listbox.yview)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.profile_listbox.config(yscrollcommand=left_scroll.set)

        # Profile File Action Control Strips
        btn_strip = ttk.Frame(left_pane, padding="2")
        btn_strip.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))
        ttk.Button(btn_strip, text="+ New", width=8, command=self._create_new_profile).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_strip, text="Link App", width=10, command=self._link_current_window_target).pack(side=tk.RIGHT, padx=2)

        # RIGHT PANE: Interactive Target Configuration Layout Tree Matrix
        right_pane = ttk.LabelFrame(main_frame, text=" Configured Control Assignments (Double-click Row to Edit) ", padding="5")
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        columns = ("control", "mapping", "details")
        self.mapping_tree = ttk.Treeview(right_pane, columns=columns, show="headings", selectmode="browse")
        
        self.mapping_tree.heading("control", text="Target Joystick Input Button/Axis")
        self.mapping_tree.heading("mapping", text="Mapped Command Type")
        self.mapping_tree.heading("details", text="Assigned Macro Output Matrix Target")

        self.mapping_tree.column("control", width=180, anchor=tk.W)
        self.mapping_tree.column("mapping", width=150, anchor=tk.CENTER)
        self.mapping_tree.column("details", width=300, anchor=tk.W)

        self.mapping_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.mapping_tree.bind("<Double-1>", self._on_row_double_clicked)

        right_scroll = ttk.Scrollbar(right_pane, orient=tk.VERTICAL, command=self.mapping_tree.yview)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mapping_tree.config(yscrollcommand=right_scroll.set)
        
        # Active runtime tracking status strip frame
        self.status_label = ttk.Label(self.root, text="Active Process: Monitoring standard background scopes...", relief=tk.SUNKEN, padding=2)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.mapping_tree.tag_configure('active_press', background='#cce5ff', font=('Arial', 10, 'bold'))
        self.mapping_tree.tag_configure('normal_row', background='white')

    def _populate_profiles(self):
        self.profile_listbox.delete(0, tk.END)
        if not self.parser.loaded_profiles:
            self.parser.loaded_profiles["Main"] = {"threshold": 4000, "buttons": {}, "axes": {}}
            
        for name in sorted(self.parser.loaded_profiles.keys()):
            self.profile_listbox.insert(tk.END, name)
            
        # Select active entry index baseline tracking lines
        idx = 0
        if self.active_profile_name in self.parser.loaded_profiles:
            idx = sorted(self.parser.loaded_profiles.keys()).index(self.active_profile_name)
        
        self.profile_listbox.selection_set(idx)
        self._update_mapping_tree_display()

    def _on_profile_changed(self, event):
        selection = self.profile_listbox.curselection()
        if selection:
            self.active_profile_name = self.profile_listbox.get(selection)
            self._update_mapping_tree_display()

    def _update_mapping_tree_display(self):
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)
            
        profile_data = self.parser.loaded_profiles.get(self.active_profile_name, {"buttons": {}, "axes": {}})

        for axis_key in ["axis1n", "axis1p", "axis2n", "axis2p", "axis3n", "axis3p", "axis4n", "axis4p", "pov1u", "pov1d", "pov1l", "pov1r"]:
            label = self.joytokey_labels.get(axis_key, axis_key)
            mapping = profile_data.get("axes", {}).get(axis_key)
            self._insert_row_by_mapping(axis_key, label, mapping)

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

    # ====================================================================
    # ⚙️ EXTENSION LAYER: CONFIGURATION BUILDER & SAVE ROUTINES
    # ====================================================================
    def _create_new_profile(self):
        new_name = simpledialog.askstring("New Profile", "Enter unique profile sheet layout name:", parent=self.root)
        if not new_name: return
        new_name = new_name.strip().replace(" ", "_")
        
        file_path = os.path.join(self.profiles_dir, f"{new_name}.cfg")
        if os.path.exists(file_path):
            messagebox.showerror("Error", "A configuration matching that name target already exists!")
            return
            
        # Construct template base file mapping layers
        config = configparser.ConfigParser()
        config['General'] = {'Threshold': '4000'}
        config['Joystick 1'] = {}
        
        with open(file_path, 'w') as f:
            config.write(f)
            
        self.parser.loaded_profiles[new_name] = {"threshold": 4000, "buttons": {}, "axes": {}}
        self.active_profile_name = new_name
        self._populate_profiles()

    def _on_row_double_clicked(self, event):

    """Launches an overlay configuration edit window to safely alter mappings."""\
item_id = self.mapping_tree.focus()\
if not item_id: return

current_values = self.mapping_tree.item(item_id, 'values')\
control_label = current_values[0]

# Build configuration edit dialog panel wrapper layout frame\
edit_win = tk.Toplevel(self.root)\
edit_win.title(f"Assign - {control_label}")\
edit_win.geometry("400x250")\
edit_win.transient(self.root)\
edit_win.grab_set()

ttk.Label(edit_win, text=f"Configure input rule mappings for: {control_label}", font=("Arial", 10, "bold")).pack(pady=10)

type_var = tk.StringVar(value="Disabled")

combo_frame = ttk.Frame(edit_win)\
combo_frame.pack(fill=tk.X, padx=20, pady=5)\
ttk.Label(combo_frame, text="Assignment Type: ").pack(side=tk.LEFT)\
type_combo = ttk.Combobox(combo_frame, textvariable=type_var, values=["Disabled", "Keyboard (Macro)", "Mouse Proportional", "Profile Layer Shift Chord"], state="readonly")\
type_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True)

param_frame = ttk.Frame(edit_win)\
param_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

param_entry_var = tk.StringVar()

def _update_fields_by_type(*args):\
for widget in param_frame.winfo_children(): widget.destroy()\
selected = type_var.get()\
if selected == "Keyboard (Macro)":\
ttk.Label(param_frame, text="Enter Windows Virtual Key Code Integer:\n(e.g., 65 for 'A', 13 for Enter)").pack()\
ttk.Entry(param_frame, textvariable=param_entry_var).pack(fill=tk.X, pady=5)\
elif selected == "Mouse Proportional":\
ttk.Label(param_frame, text="Enter Velocity Parameters: SpeedX, SpeedY, Wheel\n(e.g., 50, 0, 0 to move right)").pack()\
ttk.Entry(param_frame, textvariable=param_entry_var).pack(fill=tk.X, pady=5)\
elif selected == "Profile Layer Shift Chord":\
ttk.Label(param_frame, text="Enter target profile layer destination name:").pack()\
ttk.Entry(param_frame, textvariable=param_entry_var).pack(fill=tk.X, pady=5)

type_var.trace_add("write", _update_fields_by_type)\
type_combo.set("Keyboard (Macro)") # Default option fallback block triggers

def _commit_save_to_disk():\
chosen_type = type_var.get()\
raw_input = param_entry_var.get().strip()

# Map parameters to JoyToKey specifications\
if chosen_type == "Disabled":\
out_str = ""\
elif chosen_type == "Keyboard (Macro)":\
out_str = f"1, {raw_input}" if raw_input else ""\
elif chosen_type == "Mouse Proportional":\
out_str = f"2, {raw_input}" if raw_input else ""\
elif chosen_type == "Profile Layer Shift Chord":\
out_str = f"3, "{raw_input}"" if raw_input else ""

self._write_mapping_entry_to_ini(item_id, out_str)\
edit_win.destroy()\
self._refresh_all()

ttk.Button(edit_win, text="Save Mapping Rule", command=_commit_save_to_disk).pack(side=tk.BOTTOM, pady=15)

def _write_mapping_entry_to_ini(self, target_key, config_value_string):\
"""Rewrites INI values directly to preserve external profile compatibility."""\
file_path = os.path.join(self.profiles_dir, f"{self.active_profile_name}.cfg")\
config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))\
config.read(file_path)

if 'Joystick 1' not in config:\
config['Joystick 1'] = {}

ini_key = f"button{int(target_key):02d}" if target_key.isdigit() else target_key

if config_value_string == "":\
if ini_key in config['Joystick 1']:\
config.remove_option('Joystick 1', ini_key)\
else:\
config['Joystick 1'][ini_key] = config_value_string

with open(file_path, 'w') as f:\
config.write(f)

# ====================================================================\
# 🔍 EXTENSION LAYER: PROCESS MONITORING & AUTO-MAPPING ENGINES\
# ====================================================================\
def _load_auto_target_mappings(self):\
"""Loads configuration maps from a shared tracking template layout file."""\
map_path = os.path.join(self.profiles_dir, "auto_targets.map")\
maps = {}\
if os.path.exists(map_path):\
with open(map_path, 'r') as f:\
for line in f:\
if '=' in line and not line.startswith(('#', ';')):\
proc, prof = line.split('=', 1)\
maps[proc.strip().lower()] = prof.strip()\
return maps

def _save_auto_target_mappings(self):\
map_path = os.path.join(self.profiles_dir, "auto_targets.map")\
with open(map_path, 'w') as f:\
f.write("# ControlToKey Process Automation Profile Mapping Registry\n")\
for proc, prof in self.auto_maps.items():\
f.write(f"{proc}={prof}\n")

def _link_current_window_target(self):\
"""Links the active background software process directly to a layout file."""\
active_app = self._get_active_window_process_name()\
if "Unknown" in active_app or not active_app:\
messagebox.showwarning("Target Error", "Could not safely resolve active foreground window process handle coordinates.")\
return

confirm = messagebox.askyesno("Link Profile", f"Automate mapping configurations?\nLink process: [{active_app}]\nTo profile sheet: [{self.active_profile_name}]")\
if confirm:\
self.auto_maps[active_app.lower()] = self.active_profile_name\
self._save_auto_target_mappings()\
messagebox.showinfo("Success", f"Mapping route registered successfully for application instance: {active_app}")

def _get_active_window_process_name(self):\
"""Cross-platform active window process detection hook."""\
if sys.platform.startswith('linux'):\
try:\
# Queries xdotool to grab the active window process name on Linux systems\
import subprocess\
window_id = subprocess.check_output(["xdotool", "getactivewindow"]).decode().strip()\
pid = subprocess.check_output(["xdotool", "getwindowpid", window_id]).decode().strip()\
comm_path = f"/proc/{pid}/comm"\
if os.path.exists(comm_path):\
with open(comm_path, 'r') as f:\
return f.read().strip()\
except Exception:\
pass\
elif sys.platform.startswith('win'):\
try:\
# Queries native Win32 API functions to get the active window process on Windows systems\
import ctypes\
hwnd = ctypes.windll.user32.GetForegroundWindow()\
pid = ctypes.wintypes.DWORD()\
ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

# Retrieve process metadata from the process identifier\
PROCESS_QUERY_INFORMATION = 0x0400\
PROCESS_VM_READ = 0x0010\
h_process = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)

buf = ctypes.create_unicode_buffer(260)\
size = ctypes.wintypes.DWORD(260)\
ctypes.windll.psapi.GetModuleBaseNameW(h_process, None, buf, size)\
ctypes.windll.kernel32.CloseHandle(h_process)\
if buf.value: return buf.value\
except Exception:\
pass\
return "UnknownWorkspaceApp"

def _window_tracker_loop(self):\
"""Asynchronous tracking framework loop engine."""\
last_app = ""\
while self.tracking_running:\
active_app = self._get_active_window_process_name().lower()\
if active_app != last_app:\
last_app = active_app\
if active_app in self.auto_maps:\
target_profile = self.auto_maps[active_app]\
# Pipe automation triggers safely down to the execution queue\
self.gui_queue.put(("AUTO_SWITCH", (active_app, target_profile)))\
else:\
self.gui_queue.put(("UPDATE_STATUS", active_app))\
time.sleep(1.0)

def _process_gui_queue(self):\
try:\
while True:\
msg_type, data = self.gui_queue.get_nowait()\
if msg_type == "AUTO_SWITCH":\
app_name, profile_target = data\
self.status_label.config(text=f"AutoTarget Match Found! Process: [{app_name}] -> Swapped to Layout Profile: [{profile_target}]")\
if self.active_profile_name != profile_target and profile_target in self.parser.loaded_profiles:\
self.active_profile_name = profile_target\
self._populate_profiles()\
elif msg_type == "UPDATE_STATUS":\
self.status_label.config(text=f"Active Process: [{data}] (No explicit routing profile mapped).")\
self.gui_queue.task_done()\
except queue.Empty:\
pass\
self.root.after(100, self._process_gui_queue)

def _refresh_all(self):\
self.parser.load_all_profiles()\
self.auto_maps = self._load_auto_target_mappings()\
self._populate_profiles()

if **name** == "**main**":\
root = tk.Tk()\
app = ControlToKeyGUI(root)\
root.mainloop()
