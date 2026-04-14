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
        draw_scatter_plot(plot_frame, x, y, values, x_col, y_col, val_col, hover_data, point_size)

    def reset_plot_view(self):
        if hasattr(self, "last_plot_args") and self.last_plot_args:
            self.plot_current_data(*self.last_plot_args)