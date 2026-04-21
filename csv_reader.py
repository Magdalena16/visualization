import os
import pandas as pd


class CSVReader:
    @staticmethod
    def get_csv_files(folder):
        return [f for f in os.listdir(folder) if f.lower().endswith(".csv")]

    @staticmethod
    def get_csv_columns(path):
        return list(pd.read_csv(path, nrows=0).columns)

    @staticmethod
    def get_parquet_cache_path(csv_path):
        return csv_path + ".parquet"

    @staticmethod
    def load_csv(path, usecols=None):
        return pd.read_csv(
            path,
            usecols=usecols,
            low_memory=False
        )

    @staticmethod
    def load_data_fast(path, usecols=None):
        parquet_path = CSVReader.get_parquet_cache_path(path)

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