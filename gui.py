
import tkinter as tk
from tkinter import ttk
from controller import AppController


def start_gui():
    controller = AppController(data_folder="data")

    root = tk.Tk()
    root.title("CSV Visualisierung")
    root.geometry("1000x700")

    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)

    tk.Label(control_frame, text="Datei:").grid(row=0, column=0, padx=5)
    file_combo = ttk.Combobox(control_frame, width=20)
    file_combo.grid(row=0, column=1, padx=5)

    tk.Label(control_frame, text="X:").grid(row=0, column=2, padx=5)
    x_combo = ttk.Combobox(control_frame, width=20)
    x_combo.grid(row=0, column=3, padx=5)

    tk.Label(control_frame, text="Y:").grid(row=0, column=4, padx=5)
    y_combo = ttk.Combobox(control_frame, width=20)
    y_combo.grid(row=0, column=5, padx=5)

    tk.Label(control_frame, text="Wert:").grid(row=0, column=6, padx=5)
    value_combo = ttk.Combobox(control_frame, width=20)
    value_combo.grid(row=0, column=7, padx=5)

    tk.Label(control_frame, text="Jeder n-te Punkt:").grid(row=0, column=8, padx=5)
    step_entry = tk.Entry(control_frame, width=8)
    step_entry.grid(row=0, column=9, padx=5)
    step_entry.insert(0, "200")

    plot_frame = tk.Frame(root)
    plot_frame.pack(fill="both", expand=True)

    hover_frame = tk.LabelFrame(root, text="Hover-Werte")
    hover_frame.pack(fill="x", padx=10, pady=5)

    hover_vars = {}

    def fill_file_list():
        files = controller.get_file_list()
        file_combo["values"] = files
        if files and not file_combo.get():
            file_combo.set(files[0])

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

        for widget in hover_frame.winfo_children():
            widget.destroy()

        hover_vars.clear()

        for col in columns:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                hover_frame,
                text=col,
                variable=var,
                command=plot_selected_data
            )
            cb.pack(side="left")
            hover_vars[col] = var

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

        hover_cols = [col for col, var in hover_vars.items() if var.get()]
        #hover_cols = [col for col in hover_cols if col not in [x_col, y_col, val_col]]

        controller.plot_current_data(plot_frame, x_col, y_col, val_col, step, hover_cols)

    load_file_button = tk.Button(control_frame, text="Datei laden", command=load_selected_file)
    load_file_button.grid(row=0, column=10, padx=5)

    plot_button = tk.Button(control_frame, text="Plotten", command=plot_selected_data)
    plot_button.grid(row=0, column=11, padx=5)

    fill_file_list()
    load_selected_file()

    def on_close():
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

