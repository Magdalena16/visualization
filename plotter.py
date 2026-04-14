import tkinter as tk
import matplotlib.pyplot as plt
import mplcursors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def clear_plot_frame(plot_frame):
    for widget in plot_frame.winfo_children():
        widget.destroy()

def draw_scatter_plot(plot_frame, x, y, values, x_col, y_col, val_col, hover_data=None, point_size=5):
    clear_plot_frame(plot_frame)

    toolbar_frame = tk.Frame(plot_frame)
    toolbar_frame.pack(fill="x")

    canvas_frame = tk.Frame(plot_frame)
    canvas_frame.pack(fill="both", expand=True)

    fig, ax = plt.subplots()
    sc = ax.scatter(x, y, c=values, s=point_size)

    fig.colorbar(sc, ax=ax)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(val_col)
    ax.set_aspect("equal", adjustable="box")

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    if hover_data is not None and len(hover_data.columns) > 0:
        cursor = mplcursors.cursor(sc, hover=True)

        @cursor.connect("add")
        def on_add(sel):
            i = sel.index
            row = hover_data.iloc[i]

            lines = []
            for j, col in enumerate(hover_data.columns):
                lines.append(f"{col}: {row.iloc[j]}")

            sel.annotation.set_text("\n".join(lines))

        canvas._cursor = cursor
        fig._cursor = cursor

    canvas.draw_idle()

    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()

    return fig, ax, canvas


# def draw_scatter_plot(plot_frame, x, y, values, x_col, y_col, val_col, hover_data=None):
#     clear_plot_frame(plot_frame)

#     toolbar_frame = tk.Frame(plot_frame)
#     toolbar_frame.pack(fill="x")

#     canvas_frame = tk.Frame(plot_frame)
#     canvas_frame.pack(fill="both", expand=True)

#     fig, ax = plt.subplots()
#     sc = ax.scatter(x, y, c=values, s=5)

#     fig.colorbar(sc, ax=ax)
#     ax.set_xlabel(x_col)
#     ax.set_ylabel(y_col)
#     ax.set_title(val_col)
#     ax.set_aspect("equal", adjustable="box")

#     canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
#     #canvas.draw()
#     canvas.get_tk_widget().pack(fill="both", expand=True)

#     if hover_data is not None:
#         cursor = mplcursors.cursor(sc, hover=True)

#         @cursor.connect("add")
#         def on_add(sel):
#             i = sel.index

#             lines = []

#             # for col in hover_data.columns:
#             #     lines.append(f"{col}: {hover_data.iloc[i][col]}")

#             hover_cols = [col for col, var in hover_vars.items() if var.get()]
#             hover_data = controller.df[hover_cols] if hover_cols else None

#             sel.annotation.set_text("\n".join(lines))

#         fig._mplcursors_cursor = cursor

    
#     canvas.draw()

#     toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
#     toolbar.update()

#     return fig, ax, canvas