#!/usr/bin/env python
"""
Convert a large CSV sales file to Parquet using DuckDB (streaming, low memory).

Usage:
  SALES_CSV_PATH=data/raw/merged_cleaned_sales.csv \
  SALES_PARQUET_PATH=data/raw/merged_cleaned_sales.parquet \
  python scripts/convert_sales_to_parquet.py
"""

import os
import duckdb


def main() -> None:
    csv_path = os.getenv("SALES_CSV_PATH", "data/raw/merged_cleaned_sales.csv")
    parquet_path = os.getenv("SALES_PARQUET_PATH", "data/raw/merged_cleaned_sales.parquet")

    # Use DuckDB COPY for efficient, streaming conversion.
    duckdb.sql(
        f"""
        COPY (
          SELECT * FROM read_csv_auto('{csv_path}', SAMPLE_SIZE=-1)
        ) TO '{parquet_path}' (FORMAT PARQUET);
        """
    )
    print(f"Converted {csv_path} -> {parquet_path}")


if __name__ == "__main__":
    main()
