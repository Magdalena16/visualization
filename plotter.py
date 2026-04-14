import tkinter as tk
import matplotlib.pyplot as plt
import mplcursors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


def clear_plot_frame(plot_frame):
    for widget in plot_frame.winfo_children():
        widget.destroy()

def draw_scatter_plot(
    plot_frame,
    x,
    y,
    values,
    x_col,
    y_col,
    val_col,
    hover_data=None,
    point_size=5,
    controller=None,
    xlim=None,
    ylim=None
):

    clear_plot_frame(plot_frame)
   # plt.close("all")

    toolbar_frame = tk.Frame(plot_frame)
    toolbar_frame.pack(fill="x")

    canvas_frame = tk.Frame(plot_frame)
    canvas_frame.pack(fill="both", expand=True)

    fig, ax = plt.subplots()
    sc = ax.scatter(x, y, c=values, s=point_size)

    if xlim is not None and ylim is not None:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    fig.colorbar(sc, ax=ax)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(val_col)
    ax.set_aspect("equal", adjustable="box")

    if xlim is not None and ylim is not None:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    if hover_data is not None:
        cursor = mplcursors.cursor(sc, hover=True)

        @cursor.connect("add")
        def on_add(sel):
            i = sel.index
            lines = []

            for col in hover_data.columns:
                lines.append(f"{col}: {hover_data.iloc[i][col]}")

            sel.annotation.set_text("\n".join(lines))

        fig._cursor = cursor

    if controller is not None:
        def on_mouse_release(event):
            if event.inaxes != ax:
                return

            # nur reagieren, wenn wirklich gezoomt / gepannt wurde
            new_xlim = ax.get_xlim()
            new_ylim = ax.get_ylim()
            
            old_limits = getattr(controller, "current_view_limits", None)
            if old_limits is not None:
                old_xlim, old_ylim = old_limits
                if old_xlim == new_xlim and old_ylim == new_ylim:
                    return

            # kleines Delay, damit Matplotlib intern fertig ist
            canvas.get_tk_widget().after(
                100,
                lambda: controller.replot_current_view(new_xlim, new_ylim)
            )

        canvas.mpl_connect("button_release_event", on_mouse_release)

    canvas.draw()

    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()

    return fig, ax, canvas