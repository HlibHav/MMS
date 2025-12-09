"""
Data Analyst Agent

Wraps data tools for ETL with basic validation, storage helpers, and seed-data ingest.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
from pandas import DataFrame

from models.schemas import QualityReport, StorageResult, AnalysisDataset
from tools.xlsb_reader import XLSBReaderTool
from tools.data_cleaner import DataCleaningTool
from tools.data_merger import DataMergerTool
from tools.data_validator import DataValidationTool
from tools.db_loader import DatabaseLoaderTool
from middleware.observability import trace_context

try:
    from tools.data_ingest import DataIngestTool, IngestSummary
except ImportError:  # fall back if optional ingest tool is absent
    IngestSummary = Dict[str, Any]  # type: ignore

    class DataIngestTool:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.data_dir = Path(kwargs.get("data_dir", "")) if kwargs else Path(".")

        def run(self, *args, **kwargs):
            raise ImportError("tools.data_ingest is not available in this environment")


class DataAnalystAgent:
    """Agent for data processing, cleaning, and ETL operations."""
    
    def __init__(
        self,
        xlsb_reader: Optional[XLSBReaderTool] = None,
        data_cleaner: Optional[DataCleaningTool] = None,
        data_merger: Optional[DataMergerTool] = None,
        data_validator: Optional[DataValidationTool] = None,
        db_loader: Optional[DatabaseLoaderTool] = None,
    ):
        self.xlsb_reader = xlsb_reader or XLSBReaderTool()
        self.data_cleaner = data_cleaner or DataCleaningTool()
        self.data_merger = data_merger or DataMergerTool()
        self.data_validator = data_validator or DataValidationTool()

        if db_loader is None:
            default_db = Path(__file__).resolve().parents[1] / "mms.db"
            self.db_loader = DatabaseLoaderTool(f"sqlite:///{default_db}")
        else:
            self.db_loader = db_loader

        self.data_ingest = DataIngestTool()
        self.logger = logging.getLogger(__name__)
    
    def load_xlsb_files(
        self,
        file_paths: List[str]
    ) -> DataFrame:
        """Load and parse XLSB files."""
        with trace_context("data.load_xlsb", {"count": len(file_paths)}):
            results = self.xlsb_reader.read_multiple_files(file_paths)
            frames = [df for df in results.values() if df is not None and not df.empty]
            if not frames:
                return DataFrame()
            return pd.concat(frames, ignore_index=True)
    
    def clean_dataframe(
        self,
        df: DataFrame,
        schema: Optional[Dict[str, Any]] = None
    ) -> DataFrame:
        """Clean and standardize data formats."""
        with trace_context("data.clean", {}):
            return self.data_cleaner.clean_dataframe(df, schema=schema)
    
    def merge_files(
        self,
        files: List[DataFrame],
        merge_strategy: Optional[str] = None
    ) -> DataFrame:
        """Merge multiple data files by date ranges."""
        if not files:
            return pd.DataFrame()
        with trace_context("data.merge", {"count": len(files)}):
            # DataMergerTool expects a dict of dataframes keyed by name
            df_map = {f"df_{idx}": frame for idx, frame in enumerate(files)}
            return self.data_merger.merge_files(df_map, merge_strategy=merge_strategy or "union")
    
    def validate_data_quality(
        self,
        df: DataFrame
    ) -> QualityReport:
        """Validate data quality and detect issues."""
        with trace_context("data.validate", {"rows": len(df)}):
            return self.data_validator.validate_data_quality(df)
    
    def store_to_database(
        self,
        df: DataFrame,
        table_name: str
    ) -> StorageResult:
        """Store processed data in database."""
        with trace_context("data.store", {"table": table_name, "rows": len(df)}):
            result = self.db_loader.load_dataframe(
                df,
                table_name=table_name,
                if_exists="append",
                upsert=True,
                conflict_keys=["date", "channel", "department"] if "department" in df.columns else None,
            )

            return StorageResult(
                success=result.get("success", False),
                rows_inserted=result.get("rows_inserted", 0),
                table_name=result.get("table_name", table_name),
                errors=[result["message"]] if not result.get("success") else None,
            )
    
    def prepare_analysis_dataset(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> AnalysisDataset:
        """Prepare dataset for analysis by other agents."""
        # Minimal implementation: allow passing a dataframe via filters for downstream use.
        df = filters.get("dataframe") if filters else None  # type: ignore
        metadata = {"filters": filters or {}, "rows": len(df) if df is not None else 0}
        return AnalysisDataset(data={"dataframe": df}, metadata=metadata, filters_applied=filters or {})

    def ingest_seed_data(
        self,
        data_dir: Optional[str] = None,
        db_path: Optional[str] = None,
        dry_run: bool = False,
    ) -> IngestSummary:
        """
        Run the XLSB ingest pipeline end-to-end and return a summary.
        """
        with trace_context(
            "data.ingest_seed",
            {"data_dir": data_dir or str(self.data_ingest.data_dir)},
        ):
            return self.data_ingest.run(
                data_dir=data_dir,
                db_path=db_path,
                dry_run=dry_run,
            )
