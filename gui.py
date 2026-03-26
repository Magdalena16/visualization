
import tkinter as tk
import os
from csv_reader import load_csv
import matplotlib.pyplot as plt
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def on_load_click(plot_frame, x_combo, y_combo, value_combo, step_entry):
    import os
    import tkinter as tk
    from csv_reader import load_csv
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import mplcursors

    data_folder = "data"
    files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]

    if not files:
        print("Keine CSV-Dateien gefunden")
        return

    path = os.path.join(data_folder, files[0])
    df = load_csv(path)
    step = int(step_entry.get())
    if step < 1:
        step = 1

    df = df.iloc[::step]
    columns = list(df.columns)
    x_combo["values"] = columns
    y_combo["values"] = columns
    value_combo["values"] = columns

    x_col = x_combo.get()
    y_col = y_combo.get()
    val_col = value_combo.get()

    x = df[x_col]
    y = df[y_col]
    values = df[val_col]

    # alten Plot löschen
    for widget in plot_frame.winfo_children():
        widget.destroy()

    # Unterframes für Toolbar und Plot
    toolbar_frame = tk.Frame(plot_frame)
    toolbar_frame.pack(fill="x")

    canvas_frame = tk.Frame(plot_frame)
    canvas_frame.pack(fill="both", expand=True)

    # Plot erstellen
    fig, ax = plt.subplots()
    sc = ax.scatter(x, y, c=values, s=3)

    cursor = mplcursors.cursor(sc, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        i = sel.index
        sel.annotation.set_text(
            f"X: {x.iloc[i]:.3f}\n"
            f"Y: {y.iloc[i]:.3f}\n"
            f"Value: {values.iloc[i]:.2f}"
        )

    plt.colorbar(sc, ax=ax)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(val_col)

    # Canvas in GUI einbetten
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Toolbar
    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()
        
def on_close(root):
    root.quit()
    root.destroy()

def start_gui():
    root = tk.Tk()
    root.title("CSV Visualisierung")
    root.geometry("900x700")

    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))

    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)

    tk.Label(control_frame, text="Jeder n-te Punkt:").grid(row=0, column=6, padx=5)
    step_entry = tk.Entry(control_frame, width=8)
    step_entry.grid(row=0, column=7, padx=5)
    step_entry.insert(0, "200")

    tk.Label(control_frame, text="X:").grid(row=0, column=0, padx=5)
    x_combo = ttk.Combobox(control_frame, values=[
        "Field Commanded X [mm]", "Time [s]"
    ])
    x_combo.grid(row=0, column=1, padx=5)
    x_combo.set("Field Commanded X [mm]")

    tk.Label(control_frame, text="Y:").grid(row=0, column=2, padx=5)
    y_combo = ttk.Combobox(control_frame, values=[
        "Field Commanded Y [mm]", "Time [s]"
    ])
    y_combo.grid(row=0, column=3, padx=5)
    y_combo.set("Field Commanded Y [mm]")

    tk.Label(control_frame, text="Wert:").grid(row=0, column=4, padx=5)
    value_combo = ttk.Combobox(control_frame, values=[
        "ADC B:0", "ADC B:1", "ADC B:2", "ADC B:3"
    ])
    value_combo.grid(row=0, column=5, padx=5)
    value_combo.set("ADC B:0")

    button = tk.Button(root, text="CSV laden")
    button.pack(pady=10)
    button.config(command=lambda: on_load_click(plot_frame, x_combo, y_combo, value_combo, step_entry))

    plot_frame = tk.Frame(root)
    plot_frame.pack(fill="both", expand=True)

    data_folder = "data"
    files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]

    if files:
        path = os.path.join(data_folder, files[0])
        df = load_csv(path)
        columns = list(df.columns)

        x_combo["values"] = columns
        y_combo["values"] = columns
        value_combo["values"] = columns

    if "Field Commanded X [mm]" in columns:
        x_combo.set("Field Commanded X [mm]")

    if "Field Commanded Y [mm]" in columns:
        y_combo.set("Field Commanded Y [mm]")

    if "ADC B:0" in columns:
        value_combo.set("ADC B:0")

    root.mainloop()

