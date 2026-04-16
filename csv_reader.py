import os
import pandas as pd


def get_csv_files(folder):
    return [f for f in os.listdir(folder) if f.lower().endswith(".csv")]


def get_csv_columns(path):
    return list(pd.read_csv(path, nrows=0).columns)


def get_parquet_cache_path(csv_path):
    return csv_path + ".parquet"


def load_csv(path, usecols=None):
    return pd.read_csv(
        path,
        usecols=usecols,
        low_memory=False
    )


def load_data_fast(path, usecols=None):
    parquet_path = get_parquet_cache_path(path)

    if os.path.exists(parquet_path):
        try:
            return pd.read_parquet(parquet_path, columns=usecols)
        except Exception:
            pass

    df = pd.read_csv(path, usecols=usecols, low_memory=False)

    try:
        full_df = pd.read_csv(path, low_memory=False)
        full_df.to_parquet(parquet_path, index=False)
    except Exception:
        pass

    return df