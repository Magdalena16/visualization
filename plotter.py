import tkinter as tk

import matplotlib.pyplot as plt
import mplcursors
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


# --- toolbar ---

class CustomToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, window, controller=None):
        self.controller = controller
        super().__init__(canvas, window)

    def home(self, *args):
        super().home(*args)
        if self.controller is not None:
            self.controller.reset_view()


# --- frame helpers ---

def clear_plot_frame(plot_frame):
    for widget in plot_frame.winfo_children():
        widget.destroy()


def _reset_controller_plot_refs(controller):
    if controller is None:
        return

    controller.plot_canvas = None
    controller.plot_toolbar = None
    controller.plot_canvas_widget = None
    controller.plot_toolbar_frame = None
    controller.plot_canvas_frame = None


def _setup_plot_frames(plot_frame, controller):
    if controller is not None and controller.plot_toolbar_frame is None:
        clear_plot_frame(plot_frame)

        controller.plot_toolbar_frame = tk.Frame(plot_frame)
        controller.plot_toolbar_frame.pack(fill="x")

        controller.plot_canvas_frame = tk.Frame(plot_frame)
        controller.plot_canvas_frame.pack(fill="both", expand=True)

    if controller is not None:
        return controller.plot_toolbar_frame, controller.plot_canvas_frame

    toolbar_frame = tk.Frame(plot_frame)
    toolbar_frame.pack(fill="x")

    canvas_frame = tk.Frame(plot_frame)
    canvas_frame.pack(fill="both", expand=True)

    return toolbar_frame, canvas_frame


def _clear_frame_children(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def _store_plot_refs(controller, canvas, toolbar):
    if controller is None:
        return

    controller.plot_canvas = canvas
    controller.plot_toolbar = toolbar
    controller.plot_canvas_widget = canvas.get_tk_widget()


# --- hover ---

def _attach_hover(scatter, hover_data):
    if hover_data is None:
        return

    cursor = mplcursors.cursor(scatter, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        i = sel.index
        lines = [f"{col}: {hover_data.iloc[i][col]}" for col in hover_data.columns]
        sel.annotation.set_text("\n".join(lines))

    return cursor


# --- zoom / replot ---

def _attach_auto_replot(canvas, ax, controller):
    if controller is None:
        return

    pending_job = {"id": None}

    def trigger_replot():
        if getattr(controller, "_is_replotting_view", False):
            return

        new_xlim = ax.get_xlim()
        new_ylim = ax.get_ylim()

        old_limits = getattr(controller, "current_view_limits", None)
        if old_limits == (new_xlim, new_ylim):
            return

        controller.current_view_limits = (new_xlim, new_ylim)
        controller.replot_current_view(new_xlim, new_ylim)

    def schedule_auto_refresh(delay=250):
        if getattr(controller, "_is_replotting_view", False):
            return

        widget = canvas.get_tk_widget()

        if pending_job["id"] is not None:
            try:
                widget.after_cancel(pending_job["id"])
            except Exception:
                pass

        pending_job["id"] = widget.after(delay, trigger_replot)

    def on_mouse_release(event):
        if event.inaxes != ax:
            return
        schedule_auto_refresh(delay=350)

    def on_scroll(event):
        if event.inaxes != ax:
            return

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()

        xdata, ydata = event.xdata, event.ydata
        if xdata is None or ydata is None:
            return

        scale_factor = 0.8 if event.button == "up" else 1.25

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

        canvas.draw_idle()
        schedule_auto_refresh(delay=450)

    canvas.mpl_connect("button_release_event", on_mouse_release)
    canvas.mpl_connect("scroll_event", on_scroll)


# --- 2d plot ---

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
    if controller is not None and controller.plot_canvas is not None:
        try:
            plt.close(controller.plot_canvas.figure)
        except Exception:
            pass

    toolbar_frame, canvas_frame = _setup_plot_frames(plot_frame, controller)

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.subplots_adjust(left=0.12, right=0.88, bottom=0.12, top=0.90)

    scatter = ax.scatter(
        x,
        y,
        c=values,
        s=point_size,
        vmin=vmin,
        vmax=vmax,
        cmap="turbo"
    )

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(val_col)
    ax.set_box_aspect(1)
    ax.set_aspect("equal", adjustable="datalim")

    if xlim is not None and ylim is not None:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

    cbar_ax = fig.add_axes([0.88, 0.12, 0.03, 0.80])
    fig.colorbar(scatter, cax=cbar_ax)

    _clear_frame_children(canvas_frame)
    _clear_frame_children(toolbar_frame)

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    toolbar = CustomToolbar(canvas, toolbar_frame, controller=controller)
    toolbar.update()

    _store_plot_refs(controller, canvas, toolbar)

    cursor = _attach_hover(scatter, hover_data)
    if cursor is not None:
        fig._cursor = cursor

    _attach_auto_replot(canvas, ax, controller)

    return fig, ax, canvas


# --- 3d plot ---

def draw_3d_layers(
    plot_frame,
    layer_dfs,
    x_col,
    y_col,
    val_col,
    step,
    point_size=5,
    controller=None
):
    clear_plot_frame(plot_frame)
    plt.close("all")
    _reset_controller_plot_refs(controller)

    toolbar_frame = tk.Frame(plot_frame)
    toolbar_frame.pack(fill="x")

    canvas_frame = tk.Frame(plot_frame)
    canvas_frame.pack(fill="both", expand=True)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")

    plotted_any = False
    z_positions = []
    z_labels = []

    layer_spacing = 1.0
    step = max(1, int(step)) if step else 1

    for layer_idx, (filename, df) in enumerate(sorted(layer_dfs.items())):
        needed = [x_col, y_col, val_col]
        if not all(col in df.columns for col in needed):
            continue

        df_plot = df[needed].copy()
        df_plot = df_plot.apply(pd.to_numeric, errors="coerce").dropna()
        df_plot = df_plot.iloc[::step]

        if df_plot.empty:
            continue

        ax.scatter(
            df_plot[x_col],
            df_plot[y_col],
            [layer_idx * layer_spacing] * len(df_plot),
            c=df_plot[val_col],
            s=point_size,
            cmap="turbo"
        )

        z_positions.append(layer_idx * layer_spacing)
        z_labels.append(filename)
        plotted_any = True

    if not plotted_any:
        print("Keine passenden Layer-Daten für 3D")
        return

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_zlabel("Layer")
    ax.set_title(val_col)

    ax.set_zticks(z_positions)
    ax.set_zticklabels(z_labels)

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    toolbar = CustomToolbar(canvas, toolbar_frame, controller=None)
    toolbar.update()

    _store_plot_refs(controller, canvas, toolbar)