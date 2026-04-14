
import os
import tkinter as tk
from tkinter import ttk
from controller import AppController


def start_gui():
    controller = AppController(data_folder="data")

    root = tk.Tk()
    root.title("CSV Visualisierung")
    root.geometry("1200x800")

    # ---------- Layout-Frames ----------
    top_frame = tk.Frame(root)
    top_frame.pack(fill="x", padx=10, pady=8)

    settings_frame = tk.LabelFrame(top_frame, text="Plot-Einstellungen")
    settings_frame.pack(fill="x", pady=5)

    options_frame = tk.LabelFrame(top_frame, text="Optionen")
    options_frame.pack(fill="x", pady=5)

    bottom_frame = tk.Frame(root)
    bottom_frame.pack(fill="x", padx=10, pady=5)

    hover_frame = tk.LabelFrame(bottom_frame, text="Hover-Werte")
    hover_frame.pack(side="left", fill="both", padx=5)

    hover_canvas = tk.Canvas(hover_frame, height=100, width=200)
    hover_scrollbar = tk.Scrollbar(hover_frame, orient="vertical", command=hover_canvas.yview)
    hover_inner_frame = tk.Frame(hover_canvas)

    hover_inner_frame.bind(
        "<Configure>",
        lambda e: hover_canvas.configure(scrollregion=hover_canvas.bbox("all"))
    )

    hover_canvas.create_window((0, 0), window=hover_inner_frame, anchor="nw")
    hover_canvas.configure(yscrollcommand=hover_scrollbar.set)

    def _on_mousewheel(event):
        hover_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(_event):
        hover_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event):
        hover_canvas.unbind_all("<MouseWheel>")

    hover_canvas.bind("<Enter>", _bind_mousewheel)
    hover_canvas.bind("<Leave>", _unbind_mousewheel)

    hover_canvas.pack(side="left", fill="both", expand=True)
    hover_scrollbar.pack(side="right", fill="y")

    filter_frame = tk.LabelFrame(bottom_frame, text="Filter")
    filter_frame.pack(side="left", fill="both", padx=5)

    plot_frame = tk.Frame(root, bd=1, relief="sunken")
    plot_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- Widgets: Plot-Einstellungen ----------
    tk.Label(settings_frame, text="Datei:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    file_combo = ttk.Combobox(settings_frame, width=25, state="readonly")
    file_combo.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(settings_frame, text="X:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    x_combo = ttk.Combobox(settings_frame, width=22, state="readonly")
    x_combo.grid(row=0, column=3, padx=5, pady=5)

    tk.Label(settings_frame, text="Y:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
    y_combo = ttk.Combobox(settings_frame, width=22, state="readonly")
    y_combo.grid(row=0, column=5, padx=5, pady=5)

    tk.Label(settings_frame, text="Wert:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
    value_combo = ttk.Combobox(settings_frame, width=22, state="readonly")
    value_combo.grid(row=0, column=7, padx=5, pady=5)

    tk.Label(settings_frame, text="Modus:").grid(row=0, column=8, padx=5, pady=5, sticky="w")
    view_mode_var = tk.StringVar(value="2D")
    view_mode_combo = ttk.Combobox(
        settings_frame,
        textvariable=view_mode_var,
        values=["2D", "3D"],
        width=8,
        state="readonly"
    )
    view_mode_combo.grid(row=0, column=9, padx=5, pady=5)

    # ---------- Widgets: Optionen ----------
    tk.Label(options_frame, text="Jeder n-te Punkt:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    step_entry = tk.Entry(options_frame, width=8)
    step_entry.grid(row=0, column=1, padx=5, pady=5)
    step_entry.insert(0, "200")

    tk.Label(options_frame, text="Punktgröße:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    point_size_entry = tk.Entry(options_frame, width=8)
    point_size_entry.grid(row=0, column=3, padx=5, pady=5)
    point_size_entry.insert(0, "5")

    auto_reload_var = tk.BooleanVar(value=False)
    auto_reload_cb = tk.Checkbutton(options_frame, text="Auto-Reload", variable=auto_reload_var)
    auto_reload_cb.grid(row=0, column=4, padx=10, pady=5)

    # ---------- Widgets: Filter ----------
    tk.Label(filter_frame, text="Tag:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    tag_combo = ttk.Combobox(filter_frame, width=20, state="readonly")
    tag_combo.grid(row=0, column=1, padx=5, pady=5)
    tag_combo["values"] = ["Alle"]
    tag_combo.set("Alle")

    tk.Label(filter_frame, text="Outline:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    outline_combo = ttk.Combobox(filter_frame, width=20, state="readonly")
    outline_combo.grid(row=1, column=1, padx=5, pady=5)
    outline_combo["values"] = ["Alle"]
    outline_combo.set("Alle")

    tk.Label(filter_frame, text="Bauteil:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    part_combo = ttk.Combobox(filter_frame, width=20, state="readonly")
    part_combo.grid(row=2, column=1, padx=5, pady=5)
    part_combo["values"] = ["Alle"]
    part_combo.set("Alle")

    # ---------- Status ----------
    hover_vars = {}
    known_files = set()

    # ---------- Hilfsfunktionen ----------
    def fill_file_list():
        files = controller.get_file_list()
        file_combo["values"] = files
        if files and not file_combo.get():
            file_combo.set(files[0])
        return files

    def set_filter_values(combo, column_name):
        if controller.df is not None and column_name in controller.df.columns:
            vals = sorted(controller.df[column_name].dropna().astype(str).unique().tolist())
            combo["values"] = ["Alle"] + vals
            combo.set("Alle")
        else:
            combo["values"] = ["Alle"]
            combo.set("Alle")

    def load_selected_file():
        filename = file_combo.get()
        if not filename:
            return

        controller.load_file(filename)
        columns = controller.get_columns()

        x_combo["values"] = columns
        y_combo["values"] = columns
        value_combo["values"] = columns

        if "Field Commanded X [mm]" in columns:
            x_combo.set("Field Commanded X [mm]")
        elif columns and not x_combo.get():
            x_combo.set(columns[0])

        if "Field Commanded Y [mm]" in columns:
            y_combo.set("Field Commanded Y [mm]")
        elif len(columns) > 1 and not y_combo.get():
            y_combo.set(columns[1])

        if "ADC B:0" in columns:
            value_combo.set("ADC B:0")
        elif len(columns) > 2 and not value_combo.get():
            value_combo.set(columns[2])

        for widget in hover_inner_frame.winfo_children():
            widget.destroy()

        hover_vars.clear()

        for col in columns:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                hover_inner_frame,
                text=col,
                variable=var,
                command=plot_selected_data
            )
            cb.pack(anchor="w")
            hover_vars[col] = var

        set_filter_values(tag_combo, "tag")
        set_filter_values(outline_combo, "outline")
        set_filter_values(part_combo, "bauteil")

    def plot_selected_data():
        if controller.df is None:
            load_selected_file()

        x_col = x_combo.get()
        y_col = y_combo.get()
        val_col = value_combo.get()

        if not x_col or not y_col or not val_col:
            print("Spaltenauswahl fehlt")
            return

        try:
            step = int(step_entry.get())
        except ValueError:
            step = 200
            step_entry.delete(0, tk.END)
            step_entry.insert(0, "200")

        try:
            point_size = float(point_size_entry.get())
        except ValueError:
            point_size = 5
            point_size_entry.delete(0, tk.END)
            point_size_entry.insert(0, "5")

        hover_cols = [col for col, var in hover_vars.items() if var.get()]

        filters = {
            "tag": tag_combo.get(),
            "outline": outline_combo.get(),
            "bauteil": part_combo.get(),
        }

        mode = view_mode_var.get()

        if mode == "2D":
            controller.plot_current_data(
                plot_frame, x_col, y_col, val_col, step, hover_cols, point_size, filters
            )
        else:
            controller.load_all_files()
            controller.plot_all_layers_3d(
                plot_frame, x_col, y_col, val_col, step, point_size
            )

    def reset_view():
        controller.redraw_plot()

    def file_is_ready(filename):
        path = os.path.join("data", filename)
        try:
            size1 = os.path.getsize(path)
            with open(path, "rb") as f:
                f.read(1)
            size2 = os.path.getsize(path)
            return size1 == size2
        except (PermissionError, OSError, FileNotFoundError):
            return False

    def check_for_new_files():
        nonlocal known_files

        if auto_reload_var.get():
            files = fill_file_list()
            current_files = set(files)

            new_files = current_files - known_files
            if new_files:
                newest_file = sorted(new_files)[-1]

                if file_is_ready(newest_file):
                    file_combo.set(newest_file)
                    try:
                        load_selected_file()
                        plot_selected_data()
                        known_files = current_files
                        print(f"Neue Datei geladen: {newest_file}")
                    except PermissionError:
                        print(f"Datei noch gesperrt: {newest_file}")
                else:
                    print(f"Datei noch nicht fertig: {newest_file}")
            else:
                known_files = current_files

        root.after(2000, check_for_new_files)

    def on_close():
        try:
            import matplotlib.pyplot as plt
            plt.close("all")
        except Exception:
            pass
        root.quit()
        root.destroy()

    # ---------- Buttons ----------
    load_file_button = tk.Button(options_frame, text="Datei laden", command=load_selected_file)
    load_file_button.grid(row=0, column=5, padx=5, pady=5)

    plot_button = tk.Button(options_frame, text="Plotten", command=plot_selected_data)
    plot_button.grid(row=0, column=6, padx=5, pady=5)

    reset_button = tk.Button(options_frame, text="Ansicht zurücksetzen", command=reset_view)
    reset_button.grid(row=0, column=7, padx=5, pady=5)

    # ---------- Start ----------
    known_files = set(fill_file_list())
    load_selected_file()
    check_for_new_files()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()