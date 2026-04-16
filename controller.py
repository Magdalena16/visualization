import os
import pandas as pd
from csv_reader import get_csv_files, load_csv
from plotter import draw_scatter_plot


class AppController:

    # --- Initialisierung ---
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder

        self.df = None
        self.layer_dfs = {}

        self.current_file = None
        self.current_plot_config = {}
        self.current_view_limits = None

        self.filtered_df = None
        self.last_filters = None

        self.color_limits = None
        self.last_ax = None

        self._is_replotting_view = False
        self.plot_canvas = None
        self.plot_toolbar = None
        self.plot_canvas_widget = None
        self.plot_toolbar_frame = None
        self.plot_canvas_frame = None

    # --- Dateiverwaltung ---
    def get_file_list(self):
        return get_csv_files(self.data_folder)

    def load_file(self, filename):
        path = os.path.join(self.data_folder, filename)
        self.df = load_csv(path)

        for col in self.df.columns:
            try:
                self.df[col] = pd.to_numeric(self.df[col])
            except (ValueError, TypeError):
                pass

        self.current_file = filename
        self.color_limits = None
        self.filtered_df = None
        self.last_filters = None

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

    # --- Data Preparation Helpers ---
    def _apply_filters(self, df, filters):
        for col, val in filters.items():
            if col in df.columns and val and val != "Alle":
                df = df[df[col].astype(str) == str(val)]
        return df

    def _prepare_dataframe(self, x_col, y_col, val_col, hover_cols, filters):
        df = self._apply_filters(self.df, filters)

        all_cols = list(dict.fromkeys([x_col, y_col, val_col] + hover_cols))

        missing = [col for col in all_cols if col not in df.columns]
        if missing:
            print(f"Fehlende Spalten: {missing}")
            return None

        df = df[all_cols].copy()

        for col in all_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna()

        if df.empty:
            print("Keine Daten zum Plotten")
            return None

        return df

    def _apply_sampling(self, df, x_col, y_col, xlim, ylim, step):
        if xlim and ylim:
            df = df[
                (df[x_col] >= xlim[0]) & (df[x_col] <= xlim[1]) &
                (df[y_col] >= ylim[0]) & (df[y_col] <= ylim[1])
            ]

            if df.empty:
                print("Keine sichtbaren Daten")
                return None

            target_points = 5000
            dynamic_step = max(1, len(df) // target_points)
            return df.iloc[::dynamic_step]

        return df.iloc[::step]

    def _get_color_limits(self, val_col):
        if self.color_limits is None:
            vmin = pd.to_numeric(self.df[val_col], errors="coerce").min()
            vmax = pd.to_numeric(self.df[val_col], errors="coerce").max()
            self.color_limits = (vmin, vmax)

        return self.color_limits

    # --- 2D Plot ---
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
        if self.df is None:
            print("Keine Daten geladen")
            return

        hover_cols = hover_cols or []
        filters = filters or {}

        if filters != self.last_filters:
            self.filtered_df = self._apply_filters(self.df, filters)
            self.last_filters = filters

        df_base = self.filtered_df

        # Config speichern
        self.current_plot_config = {
            "plot_frame": plot_frame,
            "x_col": x_col,
            "y_col": y_col,
            "val_col": val_col,
            "step": step,
            "hover_cols": hover_cols,
            "point_size": point_size,
            "filters": filters
        }

        df = self._prepare_dataframe(x_col, y_col, val_col, hover_cols, {})
        if df is None:
            return

        df = self._apply_sampling(df, x_col, y_col, xlim, ylim, step)
        if df is None:
            return

        x = df[x_col]
        y = df[y_col]
        values = df[val_col]
        hover_data = df[hover_cols] if hover_cols else None

        vmin, vmax = self._get_color_limits(val_col)

        if preserve_limits:
            self.current_view_limits = (xlim, ylim)

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
            ylim=ylim if preserve_limits else None,
            vmin=vmin,
            vmax=vmax
        )

        self.last_ax = ax

    # --- Replot / Zoom ---
    def replot_current_view(self, xlim, ylim):
        if self.df is None or not self.current_plot_config:
            return

        if self._is_replotting_view:
            return

        cfg = self.current_plot_config

        df = self._prepare_dataframe(
            cfg["x_col"],
            cfg["y_col"],
            cfg["val_col"],
            cfg["hover_cols"],
            cfg["filters"]
        )

        if df is None:
            return

        df = self._apply_sampling(df, cfg["x_col"], cfg["y_col"], xlim, ylim, step=1)
        if df is None:
            return

        x = df[cfg["x_col"]]
        y = df[cfg["y_col"]]
        values = df[cfg["val_col"]]
        hover_data = df[cfg["hover_cols"]] if cfg["hover_cols"] else None

        vmin, vmax = self.color_limits

        self._is_replotting_view = True
        try:
            fig, ax, canvas = draw_scatter_plot(
                cfg["plot_frame"],
                x,
                y,
                values,
                cfg["x_col"],
                cfg["y_col"],
                cfg["val_col"],
                hover_data=hover_data,
                point_size=cfg["point_size"],
                controller=self,
                xlim=xlim,
                ylim=ylim,
                vmin=vmin,
                vmax=vmax
            )
            self.last_ax = ax
            self.current_view_limits = (xlim, ylim)
        finally:
            self._is_replotting_view = False

    def redraw_plot(self):
        if not self.current_plot_config:
            return

        cfg = self.current_plot_config
        xlim, ylim = self.current_view_limits or (None, None)

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

    def reset_view(self):
        if not self.current_plot_config or self.df is None:
            return

        self.current_view_limits = None
        cfg = self.current_plot_config

        self.plot_current_data(
            cfg["plot_frame"],
            cfg["x_col"],
            cfg["y_col"],
            cfg["val_col"],
            cfg["step"],
            cfg["hover_cols"],
            cfg["point_size"],
            cfg["filters"]
        )

    # --- 3D Plot ---
    def plot_all_layers_3d(self, plot_frame, x_col, y_col, val_col, step, point_size=5):
        from plotter import draw_3d_layers

        if not self.layer_dfs:
            print("Keine Layer geladen")
            return

        draw_3d_layers(
            plot_frame,
            self.layer_dfs,
            x_col,
            y_col,
            val_col,
            step,
            point_size
        )

