import os
import pandas as pd
from csv_reader import get_csv_files, load_csv
from plotter import draw_scatter_plot


class AppController:
    def __init__(self, data_folder="data"):
        self.data_folder = data_folder
        self.df = None
        self.current_file = None
        self.last_plot_args = None
        self.current_plot_config = {}
        self.is_updating_plot = False

    def get_file_list(self):
        return get_csv_files(self.data_folder)

    def load_file(self, filename):
        path = os.path.join(self.data_folder, filename)
        self.df = load_csv(path)
        self.current_file = filename
        return self.df

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

    def plot_current_data(self, plot_frame, x_col, y_col, val_col, step, hover_cols=None, point_size=5):
        if self.is_updating_plot:
            return
        
        self.current_plot_config = {
            "plot_frame": plot_frame,
            "x_col": x_col,
            "y_col": y_col,
            "val_col": val_col,
            "step": step,
            "hover_cols": hover_cols,
            "point_size": point_size
        }

        x, y, values = self.get_downsampled_data(x_col, y_col, val_col, step)
        if x is None:
            print("Keine Daten zum Plotten")
            return

        hover_data = None
        if hover_cols:
            all_cols = list(dict.fromkeys([x_col, y_col, val_col] + hover_cols))
            df_plot = self.df[all_cols].copy()            
            df_plot = df_plot.iloc[::step]

            for col in df_plot.columns:
                df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")

            df_plot = df_plot.dropna()

            x = df_plot[x_col]
            y = df_plot[y_col]
            values = df_plot[val_col]
            hover_data = df_plot[hover_cols]

        self.last_plot_args = (plot_frame, x_col, y_col, val_col, step, hover_cols, point_size)
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

    def redraw_plot(self):
        if not self.current_plot_config:
            return

        cfg = self.current_plot_config

        self.plot_current_data(
            cfg["plot_frame"],
            cfg["x_col"],
            cfg["y_col"],
            cfg["val_col"],
            cfg["step"],
            cfg["hover_cols"],
            cfg["point_size"]
        )

    def reset_plot_view(self):
        if hasattr(self, "last_plot_args") and self.last_plot_args:
            self.redraw_plot()

    # def plot_visible_data(self, xlim, ylim):
    #     if self.is_updating_plot:
    #         return

    #     if self.df is None or not self.current_plot_config:
    #         return

    #     cfg = self.current_plot_config
    #     x_col = cfg["x_col"]
    #     y_col = cfg["y_col"]
    #     val_col = cfg["val_col"]
    #     hover_cols = cfg["hover_cols"]
    #     point_size = cfg["point_size"]
    #     plot_frame = cfg["plot_frame"]

    #     cols = list(dict.fromkeys([x_col, y_col, val_col] + (hover_cols or [])))
    #     df_plot = self.df[cols].copy()

    #     for col in cols:
    #         df_plot[col] = pd.to_numeric(df_plot[col], errors="coerce")

    #     df_plot = df_plot.dropna()

    #     # nur sichtbaren Bereich nehmen
    #     df_visible = df_plot[
    #         (df_plot[x_col] >= xlim[0]) & (df_plot[x_col] <= xlim[1]) &
    #         (df_plot[y_col] >= ylim[0]) & (df_plot[y_col] <= ylim[1])
    #     ]

    #     if df_visible.empty:
    #         print("Keine sichtbaren Daten")
    #         return

    #     # automatische Downsampling-Logik
    #     target_points = 5000
    #     step = max(1, len(df_visible) // target_points)

    #     df_visible = df_visible.iloc[::step]

    #     x = df_visible[x_col]
    #     y = df_visible[y_col]
    #     values = df_visible[val_col]
    #     hover_data = df_visible[hover_cols] if hover_cols else None

    #     self.is_updating_plot = True
    #     try:
    #         draw_scatter_plot(
    #             plot_frame,
    #             x,
    #             y,
    #             values,
    #             x_col,
    #             y_col,
    #             val_col,
    #             hover_data,
    #             point_size,
    #             controller=self
    #         )
    #     finally:
    #         self.is_updating_plot = False

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