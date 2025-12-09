"""
Load a custom Parquet sales dataset into the app database.

Defaults:
- INPUT:  /Users/Glebazzz/MMS/Data/merged_cleaned_sales_clean.parquet
- OUTPUT: duckdb:///tmp/mms_data.duckdb (table: sales_aggregated)

Environment overrides:
- SALES_DATA_PATH  -> path to parquet/csv
- DATABASE_URL     -> duckdb:///path/to.db or postgres://...
"""

from __future__ import annotations

from pathlib import Path
import os
import pandas as pd

from backend.tools.db_loader import DatabaseLoaderTool


DEFAULT_INPUT = Path("/Users/Glebazzz/MMS/Data/merged_cleaned_sales_clean.parquet")
DEFAULT_DB_URL = "duckdb:///tmp/mms_data.duckdb"
TARGET_TABLE = "sales_aggregated"


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map the custom dataset columns into the expected schema:
    - date, channel, department, sales_value, margin_value, units, promo_flag, discount_pct
    """
    if df.empty:
        return df

    rename_map = {
        "sales_qty": "units",
    }
    df = df.rename(columns=rename_map)

    # Required columns
    required = ["date", "channel", "department", "sales_value", "margin_value"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Units
    if "units" not in df.columns:
        df["units"] = 0

    # Discount
    if "discount_pct" not in df.columns:
        df["discount_pct"] = 0.0

    # Promo flag from explicit column or code_promo
    if "promo_flag" not in df.columns:
        if "code_promo" in df.columns:
            df["promo_flag"] = df["code_promo"].notna() & (df["code_promo"] != "")
        else:
            df["promo_flag"] = False

    # Normalize types
    df["date"] = pd.to_datetime(df["date"])
    df["channel"] = df["channel"].astype(str).str.lower()
    df["department"] = df["department"].astype(str).str.upper()
    df["promo_flag"] = df["promo_flag"].astype(bool)

    # Keep only expected columns
    columns = [
        "date",
        "channel",
        "department",
        "promo_flag",
        "discount_pct",
        "sales_value",
        "margin_value",
        "units",
    ]
    df = df[[col for col in columns if col in df.columns]]
    return df


def load_custom_sales(
    source_path: Path | str | None = None,
    database_url: str | None = None,
    table_name: str = TARGET_TABLE,
) -> dict:
    path = Path(source_path or os.getenv("SALES_DATA_PATH") or DEFAULT_INPUT)
    db_url = database_url or os.getenv("DATABASE_URL") or DEFAULT_DB_URL

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_parquet(path)
    df = _normalize_dataframe(df)

    if df.empty:
        return {"success": False, "message": "Input dataset is empty after normalization", "rows_inserted": 0}

    loader = DatabaseLoaderTool(database_url=db_url)
    try:
        result = loader.load_dataframe(df, table_name=table_name, if_exists="replace")
    finally:
        loader.close()
    return result


if __name__ == "__main__":
    res = load_custom_sales()
    print(res)
