import os
import pandas as pd
from csv_reader import CSVReader
from plotter import draw_scatter_plot
import time

class AppController:

    # --- Initialisierung ---
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        self.reader = CSVReader()

        self.df = None
        self.layer_dfs = {}

        self.current_file = None
        self.current_plot_config = None
        self.current_view_limits = None
        self.is_updating_plot = False

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

        self.loaded_cols = []

    # --- Dateiverwaltung ---
    def get_file_list(self):
        return self.reader.get_csv_files(self.data_folder)

    def load_file(self, filename):
        path = os.path.join(self.data_folder, filename)

        t0 = time.time()

        self.current_file = filename
        self.current_file_path = path
        self.columns = self.reader.get_csv_columns(path)
        self.df = None

        self.color_limits = None
        self.filtered_df = None
        self.last_filters = None
        self.loaded_cols = []

        print(f"[Timing] CSV header load: {time.time() - t0:.3f}s")

    def load_all_files(self):
        self.layer_dfs = {}

        for filename in self.get_file_list():
            path = os.path.join(self.data_folder, filename)
            try:
                self.layer_dfs[filename] = self.reader.load_csv(path)
            except Exception as e:
                print(f"Fehler beim Laden von {filename}: {e}")

    def get_columns(self):
        return getattr(self, "columns", [])

    def load_plot_data(self, x_col, y_col, val_col, hover_cols, filters):
        hover_cols = hover_cols or []
        filters = filters or []

        filter_cols = [
            f["column"]
            for f in filters
            if isinstance(f, dict) and f.get("column")
        ]

        needed_cols = []
        for col in [x_col, y_col, val_col] + hover_cols + filter_cols:
            if col and col not in needed_cols:
                needed_cols.append(col)

        if not needed_cols or not getattr(self, "current_file_path", None):
            self.df = None
            self.loaded_cols = []
            return

        self.df = self.reader.load_data_fast(self.current_file_path, usecols=needed_cols)
        self.loaded_cols = needed_cols[:]

        self.filtered_df = None
        self.last_filters = None
        self.color_limits = None

    def _get_needed_cols(self, x_col, y_col, val_col, hover_cols, filters):
        hover_cols = hover_cols or []
        filters = filters or []

        filter_cols = [
            f["column"]
            for f in filters
            if isinstance(f, dict) and f.get("column")
        ]

        needed_cols = set()

        for col in [x_col, y_col, val_col] + hover_cols + filter_cols:
            if col:
                needed_cols.add(col)

        return needed_cols

    # --- Data Preparation Helpers ---
    def _apply_filters(self, df, filters):
        if df is None or not filters:
            return df

        filtered_df = df.copy()

        for f in filters:
            if not isinstance(f, dict):
                continue

            column = f.get("column")
            operator = f.get("operator")
            raw_value = f.get("value")

            if not column or not operator or column not in filtered_df.columns:
                continue

            series = filtered_df[column]

            try:
                typed_value = float(raw_value)
                series_numeric = pd.to_numeric(series, errors="coerce")
                is_numeric_filter = True
            except (TypeError, ValueError):
                typed_value = str(raw_value)
                is_numeric_filter = False

            try:
                if operator == "==":
                    if is_numeric_filter:
                        filtered_df = filtered_df[series_numeric == typed_value]
                    else:
                        filtered_df = filtered_df[series.astype(str) == typed_value]

                elif operator == "!=":
                    if is_numeric_filter:
                        filtered_df = filtered_df[series_numeric != typed_value]
                    else:
                        filtered_df = filtered_df[series.astype(str) != typed_value]

                elif operator == ">":
                    if is_numeric_filter:
                        filtered_df = filtered_df[series_numeric > typed_value]

                elif operator == "<":
                    if is_numeric_filter:
                        filtered_df = filtered_df[series_numeric < typed_value]

                elif operator == ">=":
                    if is_numeric_filter:
                        filtered_df = filtered_df[series_numeric >= typed_value]

                elif operator == "<=":
                    if is_numeric_filter:
                        filtered_df = filtered_df[series_numeric <= typed_value]

            except Exception as e:
                print(f"Fehler beim Anwenden des Filters {f}: {e}")

        return filtered_df


    def _prepare_dataframe_from_df(self, df, x_col, y_col, val_col, hover_cols):
        all_cols = list(dict.fromkeys([x_col, y_col, val_col] + hover_cols))

        missing = [col for col in all_cols if col not in df.columns]
        if missing:
            print(f"Fehlende Spalten: {missing}")
            return None

        df = df[all_cols].dropna()

        if df.empty:
            print("Keine Daten zum Plotten")
            return None

        return df

    def _apply_sampling(self, df, x_col, y_col, xlim, ylim, step):
        if df is None or df.empty:
            return None

        # Bei Zoom immer erst auf sichtbaren Bereich begrenzen
        if xlim is not None and ylim is not None:
            visible_df = df[
                (df[x_col] >= xlim[0]) & (df[x_col] <= xlim[1]) &
                (df[y_col] >= ylim[0]) & (df[y_col] <= ylim[1])
            ]

            if visible_df.empty:
                print("Keine sichtbaren Daten")
                return None

            target_points = 5000
            dynamic_step = max(1, len(visible_df) // target_points)
            return visible_df.iloc[::dynamic_step]

        # Ohne Zoom normales Sampling
        step = max(1, int(step)) if step else 1
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
        hover_cols = hover_cols or []
        filters = filters or []

        t0 = time.time()

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

        needed_cols = self._get_needed_cols(x_col, y_col, val_col, hover_cols, filters)

        if self.df is None or self.loaded_cols != needed_cols:
            self.load_plot_data(x_col, y_col, val_col, hover_cols, filters)

        if self.df is None:
            print("Keine Daten geladen")
            return

        if filters != self.last_filters or self.filtered_df is None:
            self.filtered_df = self._apply_filters(self.df, filters)
            self.last_filters = filters.copy()

        df_base = self.filtered_df

        df = self._prepare_dataframe_from_df(
            df_base,
            x_col,
            y_col,
            val_col,
            hover_cols
        )
        if df is None:
            return

        t1 = time.time()
        print(f"[Timing] Prepare DF: {t1 - t0:.3f}s")

        df = self._apply_sampling(df, x_col, y_col, xlim, ylim, step)
        if df is None or df.empty:
            return

        t2 = time.time()
        print(f"[Timing] Sampling: {t2 - t1:.3f}s")

        x = df[x_col]
        y = df[y_col]
        values = df[val_col]
        hover_data = df[hover_cols] if hover_cols else None

        vmin, vmax = self._get_color_limits(val_col)

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

        if preserve_limits and xlim is not None and ylim is not None:
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
            self.current_view_limits = (xlim, ylim)

        self.current_figure = fig
        self.current_ax = ax
        self.current_canvas = canvas
        self.connect_axes_events(ax)

        t3 = time.time()
        print(f"[Timing] Plot: {t3 - t2:.3f}s")
        print(f"[Timing] TOTAL: {t3 - t0:.3f}s")
        print("-" * 40)

        self.last_ax = ax

        return len(df)

    def plot_visible_data(self, xlim, ylim):
            if self.df is None or not self.current_plot_config:
                return

            if self.is_updating_plot:
                return

            self.is_updating_plot = True
            try:
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
            finally:
                self.is_updating_plot = False

    def connect_axes_events(self, ax):
            def on_release(_event):
                if self.is_updating_plot:
                    return

                try:
                    xlim = ax.get_xlim()
                    ylim = ax.get_ylim()
                    self.current_view_limits = (xlim, ylim)
                    self.plot_visible_data(xlim, ylim)
                except Exception:
                    pass

            ax.figure.canvas.mpl_connect("button_release_event", on_release)

        # --- Replot / Zoom ---

        #--- replot current view ---

    def replot_current_view(self, xlim, ylim):
            if self.df is None or not self.current_plot_config:
                return

            if self._is_replotting_view:
                return

            cfg = self.current_plot_config
            filters = cfg["filters"]

            if filters != self.last_filters or self.filtered_df is None:
                self.filtered_df = self._apply_filters(self.df, filters)
                self.last_filters = filters.copy()

            df_base = self.filtered_df

            df = self._prepare_dataframe_from_df(
                df_base,
                cfg["x_col"],
                cfg["y_col"],
                cfg["val_col"],
                cfg["hover_cols"]
            )
            if df is None or df.empty:
                return

            #--- auf sichtbaren Bereich begrenzen ---
            df = df[
                (df[cfg["x_col"]] >= xlim[0]) & (df[cfg["x_col"]] <= xlim[1]) &
                (df[cfg["y_col"]] >= ylim[0]) & (df[cfg["y_col"]] <= ylim[1])
            ]
            if df.empty:
                return

            #--- nur bei wirklich vielen sichtbaren Punkten samplen ---
            visible_points = len(df)

            max_visible_points = 10000
            if visible_points > max_visible_points:
                step = max(1, int(visible_points / max_visible_points))
                df = df.iloc[::step]

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

            return len(df), xlim, ylim

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
                point_size,
                controller=self
            )

