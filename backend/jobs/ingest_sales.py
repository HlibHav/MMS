"""
Sales ingestion job.

Run via cron or scheduler to ingest daily sales CSV/XLSB into the database.
"""

import os
from pathlib import Path
from tools.xlsb_reader import XLSBReaderTool
from tools.data_cleaner import DataCleaningTool
from tools.data_merger import DataMergerTool
from tools.db_loader import DatabaseLoaderTool

DATA_DIR = Path(os.getenv("SALES_DATA_DIR", "./data"))
DATABASE_URL = os.getenv("DATABASE_URL", "duckdb:///tmp/mms_data.duckdb")
TABLE_NAME = os.getenv("SALES_TABLE", "sales_aggregated")


def ingest():
    reader = XLSBReaderTool()
    cleaner = DataCleaningTool()
    merger = DataMergerTool()
    loader = DatabaseLoaderTool(database_url=DATABASE_URL)

    files = list(DATA_DIR.glob("*.xlsb")) + list(DATA_DIR.glob("*.xlsx")) + list(DATA_DIR.glob("*.csv"))
    if not files:
        print("No sales files found")
        return

    dataframes = {}
    for file in files:
        try:
            if file.suffix.lower() == ".csv":
                import pandas as pd
                df_raw = pd.read_csv(file, parse_dates=["date"])
            else:
                df_raw = reader.read_file(str(file))
            df_clean = cleaner.clean_dataframe(df_raw)
            dataframes[str(file)] = df_clean
        except Exception as e:
            print(f"Failed to process {file}: {e}")

    merged = merger.merge_files(dataframes, merge_strategy="overwrite")
    result = loader.load_dataframe(merged, table_name=TABLE_NAME, upsert=True, conflict_keys=["date", "channel", "department", "promo_flag"])
    print(result)


if __name__ == "__main__":
    ingest()

