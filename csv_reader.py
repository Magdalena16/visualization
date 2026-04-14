import os
import pandas as pd

def get_csv_files(folder):
    return [f for f in os.listdir(folder) if f.endswith(".csv")]

def load_csv(path):
    return pd.read_csv(path)