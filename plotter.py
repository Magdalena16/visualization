import tkinter as tk
import matplotlib.pyplot as plt
import mplcursors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class CustomToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, window, controller=None):
        self.controller = controller
        super().__init__(canvas, window)

    def home(self, *args):
        super().home(*args)
        if self.controller is not None:
            self.controller.reset_view()

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
    ylim=None,
    vmin=None,
    vmax=None
):

    if controller is not None and controller.plot_toolbar_frame is None:
        clear_plot_frame(plot_frame)

        controller.plot_toolbar_frame = tk.Frame(plot_frame)
        controller.plot_toolbar_frame.pack(fill="x")

        controller.plot_canvas_frame = tk.Frame(plot_frame)
        controller.plot_canvas_frame.pack(fill="both", expand=True)

    toolbar_frame = controller.plot_toolbar_frame if controller is not None else tk.Frame(plot_frame)
    canvas_frame = controller.plot_canvas_frame if controller is not None else tk.Frame(plot_frame)

    if controller is None:
        toolbar_frame.pack(fill="x")
        canvas_frame.pack(fill="both", expand=True)

    fig, ax = plt.subplots(figsize=(8,6))
    sc = ax.scatter(x, y, c=values, s=point_size, vmin=vmin, vmax=vmax, cmap="turbo")

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

    for widget in canvas_frame.winfo_children():
        widget.destroy()

    for widget in toolbar_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    toolbar = CustomToolbar(canvas, toolbar_frame, controller=controller)
    toolbar.update()

    if controller is not None:
        controller.plot_canvas = canvas
        controller.plot_toolbar = toolbar
        controller.plot_canvas_widget = canvas.get_tk_widget()

    pending_job = {"id": None}

    def schedule_auto_refresh():
        if controller is None:
            return

        if controller._is_replotting_view:
            return

        new_xlim = ax.get_xlim()
        new_ylim = ax.get_ylim()

        old_limits = getattr(controller, "current_view_limits", None)
        if old_limits is not None:
            old_xlim, old_ylim = old_limits
            if old_xlim == new_xlim and old_ylim == new_ylim:
                return

        widget = canvas.get_tk_widget()

        if pending_job["id"] is not None:
            try:
                widget.after_cancel(pending_job["id"])
            except Exception:
                pass

        pending_job["id"] = widget.after(
            400,
            lambda: controller.replot_current_view(new_xlim, new_ylim)
        )

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

    def on_scroll(event):
        if event.inaxes != ax:
            return

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        xdata = event.xdata
        ydata = event.ydata

        if xdata is None or ydata is None:
            return

        # Zoomfaktor
        scale_factor = 0.8 if event.button == "up" else 1.25

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

        canvas.draw_idle()
        schedule_auto_refresh()

    canvas.mpl_connect("scroll_event", on_scroll)

    canvas.draw()

    toolbar = CustomToolbar(canvas, toolbar_frame, controller=controller)
    toolbar.update()

    return fig, ax, canvas