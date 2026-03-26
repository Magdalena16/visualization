from csv_reader import load_csv
from plotter import plot_data
import os

data_folder = "data"
files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]
first_file = files[0]
path = os.path.join(data_folder, first_file)

print("Lade Datei:", first_file)

df = load_csv(path)

print(df.head())
print(df.columns)


from gui import start_gui

start_gui()