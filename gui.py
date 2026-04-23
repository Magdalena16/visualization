import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time

from controller import AppController


class AppGUI:
    def __init__(self, data_folder="data"):
        self.controller = AppController(data_folder=data_folder)
        self.data_folder = data_folder

        self.root = tk.Tk()
        self.root.title("CSV Visualisierung")
        self.root.state("zoomed")

        self.hover_vars = {}
        self.known_files = set()

        self._create_widgets()
        self._bind_events()
        self._initialize()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_widgets(self):
        self._create_main_frames()
        self._create_settings_widgets()
        self._create_option_widgets()
        self._create_toolbar()
        self._create_filter_widgets()
        self._create_scrollable_hover_area()
        self._create_statusbar()
        self._create_status_label()

        for col in [1, 3, 5, 7]:
            self.settings_frame.grid_columnconfigure(col, weight=1)

    def _create_main_frames(self):
        #self.root.state("zoomed")

        self.top_container = tk.Frame(self.root)
        self.top_container.pack(fill="x", padx=10, pady=8)

        self.top_row = tk.Frame(self.top_container)
        self.top_row.pack(fill="x")

        self.settings_frame = tk.LabelFrame(self.top_row, text="Plot-Einstellungen")
        self.settings_frame.pack(fill="x", pady=5)

        self.options_frame = tk.LabelFrame(self.top_container, text="Optionen")
        self.options_frame.pack(fill="x", pady=5)

        self.toolbar_frame = tk.Frame(self.top_container)
        self.toolbar_frame.pack(fill="x", pady=(0, 5))

        self.middle_container = tk.Frame(self.root)
        self.middle_container.pack(fill="x", padx=10, pady=5)

        self.hover_frame = tk.LabelFrame(self.middle_container, text="Hover-Werte")
        self.hover_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.filter_frame = tk.LabelFrame(self.middle_container, text="Filter")
        self.filter_frame.pack(side="left", fill="y", padx=(5, 0))

        self.bottom_container = tk.Frame(self.root)
        self.bottom_container.pack(fill="x", side="bottom", padx=10, pady=(0, 5))

        self.plot_frame = tk.Frame(self.root, bd=1, relief="sunken")
        self.plot_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_toolbar(self):
        self.toolbar_plot_button = tk.Button(
            self.toolbar_frame,
            text="Plotten",
            command=self.plot_selected_data,
            state="disabled"
        )
        self.toolbar_plot_button.pack(side="left", padx=2)

        self.toolbar_reset_button = tk.Button(
            self.toolbar_frame,
            text="Reset View",
            command=self.reset_view,
            state="disabled"
        )
        self.toolbar_reset_button.pack(side="left", padx=2)

        self.toolbar_clear_filters_button = tk.Button(
            self.toolbar_frame,
            text="Filter löschen",
            command=self.clear_filters,
            state="disabled"
        )
        self.toolbar_clear_filters_button.pack(side="left", padx=2)

        self.toolbar_toggle_button = tk.Button(
            self.toolbar_frame,
            text="2D/3D",
            command=self.toggle_dimension,
            state="disabled"
        )
        self.toolbar_toggle_button.pack(side="left", padx=2)

        self.toolbar_export_button = tk.Button(
            self.toolbar_frame,
            text="Export PNG",
            command=self.export_current_plot,
            state="disabled"
        )
        self.toolbar_export_button.pack(side="left", padx=2)

        self.sampling_var = tk.BooleanVar(value=True)
        self.toolbar_sampling_cb = tk.Checkbutton(
            self.toolbar_frame,
            text="Sampling",
            variable=self.sampling_var,
            state="disabled"
        )
        self.toolbar_sampling_cb.pack(side="left", padx=10)

    def _set_plot_controls_state(self, enabled):
        state = "normal" if enabled else "disabled"

        for name in [
            "toolbar_plot_button",
            "toolbar_reset_button",
            "toolbar_clear_filters_button",
            "toolbar_toggle_button",
            "toolbar_export_button",
            "toolbar_sampling_cb",
        ]:
            widget = getattr(self, name, None)
            if widget is not None:
                widget.config(state=state)
        
            # def _set_plot_controls_state(self, enabled):
            # state = "normal" if enabled else "disabled"

            # self.toolbar_plot_button.config(state=state)
            # self.toolbar_reset_button.config(state=state)
            # self.toolbar_clear_filters_button.config(state=state)
            # self.toolbar_toggle_button.config(state=state)
            # self.toolbar_export_button.config(state=state)
            # self.toolbar_sampling_cb.config(state=state)

    def _create_statusbar(self):
        statusbar = ttk.Frame(self.bottom_container)
        statusbar.pack(fill="x", side="bottom", padx=10, pady=3)

        self.file_status_label = ttk.Label(statusbar, text="Keine Datei geladen")
        self.file_status_label.pack(side="left")

        self.view_status_label = ttk.Label(statusbar, text="")
        self.view_status_label.pack(side="right", padx=(0, 15))

        self.plot_time_label = ttk.Label(statusbar, text="")
        self.plot_time_label.pack(side="right", padx=(0, 15))

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

    def _create_filter_widgets(self):
        self.filter_rows = []

        self.filter_frame = tk.LabelFrame(self.bottom_container, text="Filter")
        self.filter_frame.pack(fill="x", padx=10, pady=5)

        top_row = tk.Frame(self.filter_frame)
        top_row.pack(fill="x", padx=5, pady=5)

        tk.Button(
            top_row,
            text="Filter hinzufügen",
            command=self.add_filter_row
        ).pack(side="left")

        tk.Button(
            top_row,
            text="Filter löschen",
            command=self.clear_filters
        ).pack(side="left", padx=5)

        self.filters_container = tk.Frame(self.filter_frame)
        self.filters_container.pack(fill="x", padx=5, pady=5)
        self.add_filter_row()

    def add_filter_row(self):
        row_frame = tk.Frame(self.filters_container)
        row_frame.pack(fill="x", pady=2)

        column_var = tk.StringVar()
        operator_var = tk.StringVar(value="==")
        value_var = tk.StringVar()

        tk.Label(row_frame, text="Spalte").pack(side="left", padx=(0, 5))

        column_box = ttk.Combobox(
            row_frame,
            textvariable=column_var,
            state="readonly",
            width=25
        )
        column_box["values"] = self.controller.get_columns() if self.controller.df is not None else []
        column_box.pack(side="left", padx=5)

        tk.Label(row_frame, text="Operator").pack(side="left", padx=(10, 5))

        operator_box = ttk.Combobox(
            row_frame,
            textvariable=operator_var,
            state="readonly",
            width=8,
            values=["==", "!=", ">", "<", ">=", "<="]
        )
        operator_box.pack(side="left", padx=5)

        tk.Label(row_frame, text="Wert").pack(side="left", padx=(10, 5))

        value_entry = tk.Entry(row_frame, textvariable=value_var, width=20)
        value_entry.pack(side="left", padx=5)

        tk.Button(
            row_frame,
            text="X",
            command=lambda: self.remove_filter_row(row_frame)
        ).pack(side="left", padx=10)

        self.filter_rows.append({
            "frame": row_frame,
            "column_var": column_var,
            "operator_var": operator_var,
            "value_var": value_var,
            "column_box": column_box,
        })

    def remove_filter_row(self, row_frame):
        for row in self.filter_rows:
            if row["frame"] == row_frame:
                row["frame"].destroy()
                self.filter_rows.remove(row)
                break

    def get_active_filters(self):
        filters = []

        for row in self.filter_rows:
            column = row["column_var"].get().strip()
            operator = row["operator_var"].get().strip()
            value = row["value_var"].get().strip()

            if column and operator and value:
                filters.append({
                    "column": column,
                    "operator": operator,
                    "value": value
                })

        return filters

    def update_filter_column_options(self):
        columns = list(self.controller.df.columns) if self.controller.df is not None else []

        for row in self.filter_rows:
            row["column_box"]["values"] = columns

    def _bind_mousewheel(self, _event):
        self.hover_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        self.hover_canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.hover_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_events(self):
        #self.tag_combo.bind("<<ComboboxSelected>>", lambda e: self.plot_selected_data())
        #self.outline_combo.bind("<<ComboboxSelected>>", lambda e: self.plot_selected_data())
        #self.part_combo.bind("<<ComboboxSelected>>", lambda e: self.plot_selected_data())
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_selected)

    def _initialize(self):
        #self._set_combo_values(self.tag_combo, ["Alle"], "Alle")
        #self._set_combo_values(self.outline_combo, ["Alle"], "Alle")
        #self._set_combo_values(self.part_combo, ["Alle"], "Alle")

        self.known_files = set(self.fill_file_list())

        # self._build_layout()
        # self._create_widgets()
        # self._create_toolbar()
        # self._bind_events()
        
        self.load_selected_file()
        self.plot_selected_data()
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
        step = self._get_int_entry(self.step_entry, 200)

        if self.controller.df is not None:
            total_rows = len(self.controller.df)

            if total_rows > 200000:
                step = max(step, 10)
            if total_rows > 500000:
                step = max(step, 20)
            if total_rows > 1000000:
                step = max(step, 50)

        return {
            "x_col": self.x_combo.get(),
            "y_col": self.y_combo.get(),
            "val_col": self.value_combo.get(),
            "step": step,
            "point_size": self._get_float_entry(self.point_size_entry, 5),
            "hover_cols": self.get_selected_hover_columns(),
            "filters": self.get_active_filters(),
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

        self.update_filter_column_options()

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

        #self.set_filter_values(self.tag_combo, "tag")
        #self.set_filter_values(self.outline_combo, "outline")
        #self.set_filter_values(self.part_combo, "bauteil")
        self._set_plot_controls_state(True)

        self.file_status_label.config(text=f"Datei: {filename}")

        if hasattr(self, "file_status_label"):
            self.file_status_label.config(text=f"Datei: {filename}")

    def get_selected_hover_columns(self):
        return [col for col, var in self.hover_vars.items() if var.get()]

    # def get_filters(self):
    #     return {
    #         "tag": self.tag_combo.get(),
    #         "outline": self.outline_combo.get(),
    #         "bauteil": self.part_combo.get(),
    #     }

    #--- filter reset ---

    def clear_filters(self):
        for row in self.filter_rows[:]:
            row["frame"].destroy()
        self.filter_rows.clear()

    #--- plot selected data ---

    def plot_selected_data(self):
        self.status_label.config(text="Lade Plot...")
        self.root.update_idletasks()

        start_time = time.perf_counter()

        if self.controller.df is None:
            self.load_selected_file()

        config = self._get_plot_config()

        if hasattr(self, "sampling_var") and not self.sampling_var.get():
            config["step"] = 1

        if not config["x_col"] or not config["y_col"] or not config["val_col"]:
            print("Spaltenauswahl fehlt")
            self.status_label.config(text="")
            return

        # aktuellen Ausschnitt merken
        xlim = None
        ylim = None
        preserve_limits = False

        if getattr(self.controller, "current_view_limits", None) is not None:
            xlim, ylim = self.controller.current_view_limits
            preserve_limits = True

        num_points = None

        if config["mode"] == "2D":
            num_points = self.controller.plot_current_data(
                self.plot_frame,
                config["x_col"],
                config["y_col"],
                config["val_col"],
                config["step"],
                config["hover_cols"],
                config["point_size"],
                config["filters"],
                xlim=xlim,
                ylim=ylim,
                preserve_limits=preserve_limits
            )
        else:
            self._plot_3d(config)

        end_time = time.perf_counter()
        duration = end_time - start_time

        if hasattr(self, "plot_time_label"):
            self.plot_time_label.config(text=f"Plotzeit: {duration:.2f}s")

        if num_points is not None and hasattr(self, "view_status_label"):
            if getattr(self.controller, "current_view_limits", None) is not None:
                xlim, ylim = self.controller.current_view_limits
                self.view_status_label.config(
                    text=f"Punkte: {num_points}    X: [{xlim[0]:.2f}, {xlim[1]:.2f}]  Y: [{ylim[0]:.2f}, {ylim[1]:.2f}]"
                )
            else:
                self.view_status_label.config(text=f"Punkte: {num_points}")

        self.status_label.config(text="")

    def _plot_2d(self, config):
        df = self.controller.df
        num_points = 0

        if df is not None:
            filtered_df = self.controller._apply_filters(df, config["filters"])

            if filtered_df is not None and not filtered_df.empty:
                step = max(1, int(config["step"]))
                num_points = len(filtered_df.iloc[::step])

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

        if hasattr(self, "plot_time_label"):
            self.plot_time_label.config(text=f"Punkte: {num_points}")

        if hasattr(self.controller, "current_view_limits") and self.controller.current_view_limits is not None:
            xlim, ylim = self.controller.current_view_limits
            self.view_status_label.config(
                text=f"X: [{xlim[0]:.2f}, {xlim[1]:.2f}]  Y: [{ylim[0]:.2f}, {ylim[1]:.2f}]"
            )

        return num_points

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

    #--- toggle dimension ---

    def toggle_dimension(self):
        current = self.view_mode_var.get()

        if current == "2D":
            self.view_mode_var.set("3D")
        else:
            self.view_mode_var.set("2D")

        self.plot_selected_data()

    #--- reset view ---

    def reset_view(self):
        self.current_view_limits = None

        if hasattr(self, "current_plot_config") and self.current_plot_config:
            cfg = self.current_plot_config

            self.plot_current_data(
                cfg["plot_frame"],
                cfg["x_col"],
                cfg["y_col"],
                cfg["val_col"],
                cfg["step"],
                cfg["hover_cols"],
                cfg["point_size"],
                cfg["filters"],
                xlim=None,
                ylim=None,
                preserve_limits=False
            )

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
                    mode = self.view_mode_var.get()

                    if mode == "2D":
                        try:
                            self.file_combo.set(newest_file)
                            self.load_selected_file()
                            self.plot_selected_data()

                            self.known_files = current_files
                            print(f"Neue Datei automatisch geladen (2D): {newest_file}")
                            self.status_label.config(text="")
                        except PermissionError:
                            print(f"Datei noch gesperrt: {newest_file}")

                    else:
                        try:
                            self.controller.load_all_files()
                            self.plot_selected_data()

                            self.known_files = current_files
                            print(f"Neue Datei in 3D geladen: {newest_file}")
                            self.status_label.config(text="")
                        except PermissionError:
                            print(f"Datei noch gesperrt: {newest_file}")
                else:
                    print(f"Datei noch nicht fertig: {newest_file}")
            else:
                self.known_files = current_files

        self.root.after(2000, self.check_for_new_files)

    def on_file_selected(self, _event=None):
        self.load_selected_file()
        self.plot_selected_data()

    #--- export current plot ---

    def export_current_plot(self):
        if not hasattr(self.controller, "current_figure") or self.controller.current_figure is None:
            print("Kein Plot zum Exportieren vorhanden")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")]
        )
        if not file_path:
            return

        self.controller.current_figure.savefig(file_path, dpi=300, bbox_inches="tight")

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
