import os
import pandas as pd
from csv_reader import get_csv_files, load_csv
from plotter import draw_scatter_plot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from plotter import clear_plot_frame
import tkinter as tk
from mpl_toolkits.mplot3d import Axes3D


class AppController:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        self.layer_dfs = {}        
        self.current_file = None
        self.last_plot_args = None
        self.current_plot_config = {}
        self.current_view_limits = None
        self.is_updating_plot = False
        self.last_ax = None
        self._is_replotting_view = False

    def get_file_list(self):
        return get_csv_files(self.data_folder)

    def load_file(self, filename):
        path = os.path.join(self.data_folder, filename)
        self.df = load_csv(path)
        self.current_file = filename
        return self.df
    
    def load_all_files(self):
        self.layer_dfs = {}

        for filename in self.get_file_list():
            path = os.path.join(self.data_folder, filename)
            try:
                self.layer_dfs[filename] = load_csv(path)
            except Exception as e:
                print(f"Fehler beim Laden von {filename}: {e}")

    def get_columns(self):
        if self.df is None:
            return []
        return list(self.df.columns)

    def get_downsampled_data(self, x_col, y_col, val_col, step):
        if self.df is None:
            print("df ist None")
            return None, None, None

        if step < 1:
            step = 1

        df_plot = self.df.iloc[::step]

        x = df_plot[x_col]
        y = df_plot[y_col]
        values = df_plot[val_col]

        return x, y, values

    def plot_all_layers(self, plot_frame, x_col, y_col, val_col, step, point_size=5):

        clear_plot_frame(plot_frame)

        toolbar_frame = tk.Frame(plot_frame)
        toolbar_frame.pack(fill="x")

        canvas_frame = tk.Frame(plot_frame)
        canvas_frame.pack(fill="both", expand=True)

        fig, ax = plt.subplots()

        for filename, df in self.layer_dfs.items():
            needed = [x_col, y_col, val_col]
            if not all(col in df.columns for col in needed):
                continue

            df_plot = df[needed].copy()
            for col in needed:
                df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")
            df_plot = df_plot.dropna()
            df_plot = df_plot.iloc[::step]

            if df_plot.empty:
                continue

            sc = ax.scatter(
                df_plot[x_col],
                df_plot[y_col],
                c=df_plot[val_col],
                s=point_size,
                label=filename
            )

        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_title(val_col)
        ax.set_aspect("equal", adjustable="box")
        ax.legend()

        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

    def plot_current_data(
        self,
        plot_frame,
        x_col,
        y_col,
        val_col,
        step,
        hover_cols=None,
        point_size=5,
        filters=None,
        xlim=None,
        ylim=None,
        preserve_limits=False
    ):

        self.current_plot_config = {
            "plot_frame": plot_frame,
            "x_col": x_col,
            "y_col": y_col,
            "val_col": val_col,
            "step": step,
            "hover_cols": hover_cols or [],
            "point_size": point_size,
            "filters": filters
        }

        if self.df is None:
            print("Keine Daten geladen")
            return

        hover_cols = hover_cols or []
        filters = filters or {}



        df_base = self.df.copy()

        # Filter anwenden
        for col, val in filters.items():
            if col in df_base.columns and val and val != "Alle":
                df_base = df_base[df_base[col].astype(str) == str(val)]

        all_cols = list(dict.fromkeys([x_col, y_col, val_col] + hover_cols))

        missing = [col for col in all_cols if col not in df_base.columns]
        if missing:
            print(f"Fehlende Spalten: {missing}")
            return

        df_plot = df_base[all_cols].copy()

        for col in all_cols:
            df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")

        df_plot = df_plot.dropna()

        if df_plot.empty:
            print("Keine Daten zum Plotten")
            return

        # Falls gezoomt: nur sichtbaren Bereich betrachten
        if xlim is not None and ylim is not None:
            df_plot = df_plot[
                (df_plot[x_col] >= xlim[0]) & (df_plot[x_col] <= xlim[1]) &
                (df_plot[y_col] >= ylim[0]) & (df_plot[y_col] <= ylim[1])
            ]

            if df_plot.empty:
                print("Keine sichtbaren Daten")
                return

            # dynamisches Resampling im sichtbaren Bereich
            target_points = 5000
            dynamic_step = max(1, len(df_plot) // target_points)
            df_plot = df_plot.iloc[::dynamic_step]
        else:
            df_plot = df_plot.iloc[::step]

        x = df_plot[x_col]
        y = df_plot[y_col]
        values = df_plot[val_col]
        hover_data = df_plot[hover_cols] if hover_cols else None

        if preserve_limits and xlim is not None and ylim is not None:
            self.current_view_limits = (xlim, ylim)

        self.is_updating_plot = True
        try:
           fig, ax, canvas = draw_scatter_plot(
                plot_frame,
                x,
                y,
                values,
                x_col,
                y_col,
                val_col,
                hover_data=hover_data,
                point_size=point_size,
                controller=self,
                xlim=xlim if preserve_limits else None,
                ylim=ylim if preserve_limits else None
            )
           self.last_ax = ax
        finally:
            self.is_updating_plot = False

    def plot_all_layers_3d(self, plot_frame, x_col, y_col, val_col, step, point_size=5):

        clear_plot_frame(plot_frame)
        plt.close("all")

        toolbar_frame = tk.Frame(plot_frame)
        toolbar_frame.pack(fill="x")

        canvas_frame = tk.Frame(plot_frame)
        canvas_frame.pack(fill="both", expand=True)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        plotted_any = False

        for layer_idx, (filename, df) in enumerate(sorted(self.layer_dfs.items())):
            needed = [x_col, y_col, val_col]
            if not all(col in df.columns for col in needed):
                continue

            df_plot = df[needed].copy()

            for col in needed:
                df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")

            df_plot = df_plot.dropna()
            df_plot = df_plot.iloc[::step]

            if df_plot.empty:
                continue

            x = df_plot[x_col]
            y = df_plot[y_col]
            z = [layer_idx] * len(df_plot)
            c = df_plot[val_col]

            ax.scatter(x, y, z, c=c, s=point_size)
            plotted_any = True

        if not plotted_any:
            print("Keine passenden Layer-Daten für 3D")
            plt.close(fig)
            return

        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.set_zlabel("Layer")
        ax.set_title(f"3D Layer-Ansicht: {val_col}")

        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        toolbar.update()

    def plot_visible_data(self, xlim, ylim):
        if self.is_updating_plot:
            return

        if not self.current_plot_config:
            return

        self.current_view_limits = (xlim, ylim)

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
            xlim=xlim,
            ylim=ylim,
            preserve_limits=True
        )

    def replot_current_view(self, xlim, ylim):
        if getattr(self, "_is_replotting_view", False):
            return

        if self.df is None or not self.current_plot_config:
            return

        cfg = self.current_plot_config
        x_col = cfg["x_col"]
        y_col = cfg["y_col"]
        val_col = cfg["val_col"]
        hover_cols = cfg["hover_cols"]
        point_size = cfg["point_size"]
        plot_frame = cfg["plot_frame"]
        filters = cfg["filters"]

        df_base = self.df.copy()

        # Filter anwenden
        for col, val in filters.items():
            if col in df_base.columns and val and val != "Alle":
                df_base = df_base[df_base[col].astype(str) == str(val)]

        all_cols = list(dict.fromkeys([x_col, y_col, val_col] + hover_cols))
        df_plot = df_base[all_cols].copy()

        for col in all_cols:
            df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")

        df_plot = df_plot.dropna()

        # nur sichtbaren Bereich nehmen
        df_plot = df_plot[
            (df_plot[x_col] >= xlim[0]) & (df_plot[x_col] <= xlim[1]) &
            (df_plot[y_col] >= ylim[0]) & (df_plot[y_col] <= ylim[1])
        ]

        if df_plot.empty:
            print("Keine sichtbaren Daten")
            return

        # dynamischer Step
        visible_count = len(df_plot)

        if visible_count > 200000:
            dynamic_step = 500
        elif visible_count > 50000:
            dynamic_step = 100
        elif visible_count > 10000:
            dynamic_step = 20
        elif visible_count > 2000:
            dynamic_step = 5
        else:
            dynamic_step = 1

        df_plot = df_plot.iloc[::dynamic_step]

        x = df_plot[x_col]
        y = df_plot[y_col]
        values = df_plot[val_col]
        hover_data = df_plot[hover_cols] if hover_cols else None

        self.current_view_limits = (xlim, ylim)

        self._is_replotting_view = True
        try:
            fig, ax, canvas = draw_scatter_plot(
                plot_frame,
                x,
                y,
                values,
                x_col,
                y_col,
                val_col,
                hover_data=hover_data,
                point_size=point_size,
                controller=self,
                xlim=xlim,
                ylim=ylim
            )
            self.last_ax = ax
        finally:
            self._is_replotting_view = False



    def redraw_plot(self):
        if not self.current_plot_config:
            return

        cfg = self.current_plot_config

        xlim = None
        ylim = None
        if self.current_view_limits is not None:
            xlim, ylim = self.current_view_limits

        self.plot_current_data(
            cfg["plot_frame"],
            cfg["x_col"],
            cfg["y_col"],
            cfg["val_col"],
            cfg["step"],
            cfg["hover_cols"],
            cfg["point_size"],
            cfg["filters"],
            xlim=xlim,
            ylim=ylim,
            preserve_limits=True
        )

    def reset_plot_view(self):
        if hasattr(self, "last_plot_args") and self.last_plot_args:
            self.redraw_plot()

    def plot_visible_data(self, xlim, ylim):
        if self.df is None or not self.current_plot_config:
            return

        if self.is_updating_plot:
            return

        self.is_updating_plot = True
        try:
            cfg = self.current_plot_config
            x_col = cfg["x_col"]
            y_col = cfg["y_col"]
            val_col = cfg["val_col"]
            hover_cols = cfg["hover_cols"] or []
            point_size = cfg["point_size"]
            plot_frame = cfg["plot_frame"]

            cols = list(dict.fromkeys([x_col, y_col, val_col] + hover_cols))
            df_plot = self.df[cols].copy()

            for col in cols:
                df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")

            df_plot = df_plot.dropna()

            df_visible = df_plot[
                (df_plot[x_col] >= xlim[0]) & (df_plot[x_col] <= xlim[1]) &
                (df_plot[y_col] >= ylim[0]) & (df_plot[y_col] <= ylim[1])
            ]

            if df_visible.empty:
                return

            target_points = 5000
            step = max(1, len(df_visible) // target_points)
            df_visible = df_visible.iloc[::step]

            x = df_visible[x_col]
            y = df_visible[y_col]
            values = df_visible[val_col]
            hover_data = df_visible[hover_cols] if hover_cols else None

            draw_scatter_plot(
                plot_frame,
                x,
                y,
                values,
                x_col,
                y_col,
                val_col,
                hover_data,
                point_size,
                controller=self
            )
        finally:
            self.is_updating_plot = False