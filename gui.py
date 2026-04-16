import os
import tkinter as tk
from tkinter import ttk

from controller import AppController


class AppGUI:
    def __init__(self, data_folder="data"):
        self.controller = AppController(data_folder=data_folder)
        self.data_folder = data_folder

        self.root = tk.Tk()
        self.root.title("CSV Visualisierung")
        self.root.geometry("1200x800")

        self.hover_vars = {}
        self.known_files = set()

        self._create_widgets()
        self._bind_events()
        self._initialize()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_widgets(self):
        self._create_main_frames()
        self._create_status_label()
        self._create_scrollable_hover_area()
        self._create_settings_widgets()
        self._create_option_widgets()
        self._create_filter_widgets()

    def _create_main_frames(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=8)

        self.settings_frame = tk.LabelFrame(top_frame, text="Plot-Einstellungen")
        self.settings_frame.pack(fill="x", pady=5)

        self.options_frame = tk.LabelFrame(top_frame, text="Optionen")
        self.options_frame.pack(fill="x", pady=5)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        self.hover_frame = tk.LabelFrame(bottom_frame, text="Hover-Werte")
        self.hover_frame.pack(side="left", fill="both", padx=5)

        self.filter_frame = tk.LabelFrame(bottom_frame, text="Filter")
        self.filter_frame.pack(side="left", fill="both", padx=5)

        self.plot_frame = tk.Frame(self.root, bd=1, relief="sunken")
        self.plot_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_status_label(self):
        self.status_label = tk.Label(self.options_frame, text="", fg="red")
        self.status_label.grid(row=1, column=0, columnspan=10, sticky="w", padx=5)

    def _create_scrollable_hover_area(self):
        self.hover_canvas = tk.Canvas(self.hover_frame, height=100, width=200)
        self.hover_scrollbar = tk.Scrollbar(
            self.hover_frame,
            orient="vertical",
            command=self.hover_canvas.yview
        )
        self.hover_inner_frame = tk.Frame(self.hover_canvas)

        self.hover_inner_frame.bind(
            "<Configure>",
            lambda e: self.hover_canvas.configure(scrollregion=self.hover_canvas.bbox("all"))
        )

        self.hover_canvas.create_window((0, 0), window=self.hover_inner_frame, anchor="nw")
        self.hover_canvas.configure(yscrollcommand=self.hover_scrollbar.set)

        self.hover_canvas.bind("<Enter>", self._bind_mousewheel)
        self.hover_canvas.bind("<Leave>", self._unbind_mousewheel)

        self.hover_canvas.pack(side="left", fill="both", expand=True)
        self.hover_scrollbar.pack(side="right", fill="y")

    def _create_settings_widgets(self):
        tk.Label(self.settings_frame, text="Datei:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.file_combo = ttk.Combobox(self.settings_frame, width=25, state="readonly")
        self.file_combo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.settings_frame, text="X:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.x_combo = ttk.Combobox(self.settings_frame, width=22, state="readonly")
        self.x_combo.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(self.settings_frame, text="Y:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.y_combo = ttk.Combobox(self.settings_frame, width=22, state="readonly")
        self.y_combo.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(self.settings_frame, text="Wert:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.value_combo = ttk.Combobox(self.settings_frame, width=22, state="readonly")
        self.value_combo.grid(row=0, column=7, padx=5, pady=5)

        tk.Label(self.settings_frame, text="Modus:").grid(row=0, column=8, padx=5, pady=5, sticky="w")
        self.view_mode_var = tk.StringVar(value="2D")
        self.view_mode_combo = ttk.Combobox(
            self.settings_frame,
            textvariable=self.view_mode_var,
            values=["2D", "3D"],
            width=8,
            state="readonly"
        )
        self.view_mode_combo.grid(row=0, column=9, padx=5, pady=5)

    def _create_option_widgets(self):
        tk.Label(self.options_frame, text="Jeder n-te Punkt:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.step_entry = tk.Entry(self.options_frame, width=8)
        self.step_entry.grid(row=0, column=1, padx=5, pady=5)
        self.step_entry.insert(0, "500")

        tk.Label(self.options_frame, text="Punktgröße:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.point_size_entry = tk.Entry(self.options_frame, width=8)
        self.point_size_entry.grid(row=0, column=3, padx=5, pady=5)
        self.point_size_entry.insert(0, "5")

        self.auto_reload_var = tk.BooleanVar(value=False)
        self.auto_reload_cb = tk.Checkbutton(
            self.options_frame,
            text="Auto-Reload",
            variable=self.auto_reload_var
        )
        self.auto_reload_cb.grid(row=0, column=4, padx=10, pady=5)

        self.plot_button = tk.Button(self.options_frame, text="Plotten", command=self.plot_selected_data)
        self.plot_button.grid(row=0, column=6, padx=5, pady=5)

        self.reset_button = tk.Button(self.options_frame, text="Ansicht zurücksetzen", command=self.reset_view)
        self.reset_button.grid(row=0, column=7, padx=5, pady=5)

    def _create_filter_widgets(self):
        tk.Label(self.filter_frame, text="Tag:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tag_combo = ttk.Combobox(self.filter_frame, width=20, state="readonly")
        self.tag_combo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.filter_frame, text="Outline:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.outline_combo = ttk.Combobox(self.filter_frame, width=20, state="readonly")
        self.outline_combo.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.filter_frame, text="Bauteil:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.part_combo = ttk.Combobox(self.filter_frame, width=20, state="readonly")
        self.part_combo.grid(row=2, column=1, padx=5, pady=5)

    def _bind_mousewheel(self, _event):
        self.hover_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        self.hover_canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.hover_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_events(self):
        self.tag_combo.bind("<<ComboboxSelected>>", lambda e: self.plot_selected_data())
        self.outline_combo.bind("<<ComboboxSelected>>", lambda e: self.plot_selected_data())
        self.part_combo.bind("<<ComboboxSelected>>", lambda e: self.plot_selected_data())
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)

    def _initialize(self):
        self._set_combo_values(self.tag_combo, ["Alle"], "Alle")
        self._set_combo_values(self.outline_combo, ["Alle"], "Alle")
        self._set_combo_values(self.part_combo, ["Alle"], "Alle")

        self.known_files = set(self.fill_file_list())
        self.load_selected_file()
        self.check_for_new_files()

    def _set_combo_values(self, combo, values, default="Alle"):
        combo["values"] = values
        combo.set(default)

    def _get_int_entry(self, entry, default):
        try:
            return int(entry.get())
        except ValueError:
            entry.delete(0, tk.END)
            entry.insert(0, str(default))
            return default

    def _get_float_entry(self, entry, default):
        try:
            return float(entry.get())
        except ValueError:
            entry.delete(0, tk.END)
            entry.insert(0, str(default))
            return default

    def _set_preferred_or_fallback(self, combo, columns, preferred_name, fallback_index):
        if preferred_name in columns:
            combo.set(preferred_name)
        elif len(columns) > fallback_index:
            combo.set(columns[fallback_index])

    def _get_plot_config(self):
        return {
            "x_col": self.x_combo.get(),
            "y_col": self.y_combo.get(),
            "val_col": self.value_combo.get(),
            "step": self._get_int_entry(self.step_entry, 200),
            "point_size": self._get_float_entry(self.point_size_entry, 5),
            "hover_cols": self.get_selected_hover_columns(),
            "filters": self.get_filters(),
            "mode": self.view_mode_var.get(),
        }

    def fill_file_list(self):
        files = sorted(self.controller.get_file_list())
        self.file_combo["values"] = files

        if files and not self.file_combo.get():
            self.file_combo.set(files[0])

        return files

    def set_filter_values(self, combo, column_name):
        if self.controller.df is not None and column_name in self.controller.df.columns:
            vals = sorted(self.controller.df[column_name].dropna().astype(str).unique().tolist())
            self._set_combo_values(combo, ["Alle"] + vals, "Alle")
        else:
            self._set_combo_values(combo, ["Alle"], "Alle")

    def file_is_ready(self, filename):
        path = os.path.join(self.data_folder, filename)
        try:
            size1 = os.path.getsize(path)
            with open(path, "rb") as f:
                f.read(1)
            size2 = os.path.getsize(path)
            return size1 == size2
        except (PermissionError, OSError, FileNotFoundError):
            return False

    def clear_hover_checkboxes(self):
        for widget in self.hover_inner_frame.winfo_children():
            widget.destroy()
        self.hover_vars.clear()

    def create_hover_checkboxes(self, columns):
        self.clear_hover_checkboxes()

        for col in columns:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                self.hover_inner_frame,
                text=col,
                variable=var,
                command=self.plot_selected_data
            )
            cb.pack(anchor="w")
            self.hover_vars[col] = var

    def set_default_plot_columns(self, columns):
        self.x_combo["values"] = columns
        self.y_combo["values"] = columns
        self.value_combo["values"] = columns

        self._set_preferred_or_fallback(
            self.x_combo, columns, "Field Commanded X [mm]", 0
        )
        self._set_preferred_or_fallback(
            self.y_combo, columns, "Field Commanded Y [mm]", 1
        )
        self._set_preferred_or_fallback(
            self.value_combo, columns, "ADC B:0", 2
        )

    def load_selected_file(self):
        filename = self.file_combo.get()
        if not filename:
            return

        self.controller.load_file(filename)
        columns = self.controller.get_columns()

        self.set_default_plot_columns(columns)
        self.create_hover_checkboxes(columns)

        self.set_filter_values(self.tag_combo, "tag")
        self.set_filter_values(self.outline_combo, "outline")
        self.set_filter_values(self.part_combo, "bauteil")

    def get_selected_hover_columns(self):
        return [col for col, var in self.hover_vars.items() if var.get()]

    def get_filters(self):
        return {
            "tag": self.tag_combo.get(),
            "outline": self.outline_combo.get(),
            "bauteil": self.part_combo.get(),
        }

    def plot_selected_data(self):
        self.status_label.config(text="Lade Plot...")
        self.root.update_idletasks()
        
        if self.controller.df is None:
            self.load_selected_file()

        config = self._get_plot_config()

        if not config["x_col"] or not config["y_col"] or not config["val_col"]:
            print("Spaltenauswahl fehlt")
            return

        if config["mode"] == "2D":
            self._plot_2d(config)
        else:
            self._plot_3d(config)

        self.status_label.config(text="")

    def _plot_2d(self, config):
        self.controller.plot_current_data(
            self.plot_frame,
            config["x_col"],
            config["y_col"],
            config["val_col"],
            config["step"],
            config["hover_cols"],
            config["point_size"],
            config["filters"]
        )

    def _plot_3d(self, config):
        self.controller.load_all_files()
        self.controller.plot_all_layers_3d(
            self.plot_frame,
            config["x_col"],
            config["y_col"],
            config["val_col"],
            config["step"],
            config["point_size"]
        )

    def reset_view(self):
        self.controller.reset_view()

    def _handle_new_file_in_2d(self, newest_file, current_files):
        self.known_files = current_files
        print(f"Neue Datei erkannt (2D, nicht automatisch geladen): {newest_file}")
        self.status_label.config(text=f"Neue Datei verfügbar: {newest_file}")

    def _handle_new_file_in_3d(self, newest_file, current_files):
        try:
            self.controller.load_all_files()
            self.plot_selected_data()
            self.known_files = current_files
            print(f"Neue Datei in 3D geladen: {newest_file}")
            self.status_label.config(text="")
        except PermissionError:
            print(f"Datei noch gesperrt: {newest_file}")

    def check_for_new_files(self):
        if self.auto_reload_var.get():
            files = self.fill_file_list()
            current_files = set(files)
            new_files = current_files - self.known_files

            if new_files:
                newest_file = sorted(new_files)[-1]

                if self.file_is_ready(newest_file):
                    if self.view_mode_var.get() == "2D":
                        self._handle_new_file_in_2d(newest_file, current_files)
                    else:
                        self._handle_new_file_in_3d(newest_file, current_files)
                else:
                    print(f"Datei noch nicht fertig: {newest_file}")
            else:
                self.known_files = current_files

        self.root.after(2000, self.check_for_new_files)

    def on_file_selected(self, _event=None):
        self.load_selected_file()
        self.plot_selected_data()

    def on_close(self):
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass

        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def start_gui():
    app = AppGUI(data_folder="data")
    app.run()
