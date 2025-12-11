"""
Data Processing API Routes

Endpoints for data processing and ETL operations.
"""

import os
import uuid
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends, Response
from typing import List, Dict, Any
from datetime import date

from middleware.rate_limit import get_rate_limit
from middleware.auth import get_current_user, require_promo_lead
from middleware.errors import ProcessingError, ValidationError
from backend.api.utils.pagination import paginate_list
from middleware.observability import trace_function

from engines.forecast_baseline_engine import ForecastBaselineEngine
from tools.sales_data_tool import SalesDataTool
from tools.targets_config_tool import TargetsConfigTool
from models.schemas import QualityReport, StorageResult, BaselineForecast

router = APIRouter()

sales_tool = SalesDataTool()
targets_tool = TargetsConfigTool()
baseline_engine = ForecastBaselineEngine(sales_data_tool=sales_tool, targets_tool=targets_tool)

# Lightweight in-memory job tracking for data processing
_JOBS: Dict[str, Dict[str, Any]] = {}



@router.post("/process-xlsb")
@get_rate_limit("data_processing")
@trace_function(name="data.process_xlsb")
async def process_xlsb_files(
    files: List[UploadFile] = File(...),
    request: Request = None,
    current_user = Depends(require_promo_lead)
) -> dict:
    """
    Process XLSB files and load into database.
    
    Args:
        files: List of XLSB files to process
    
    Returns:
        Processing result dictionary
    """
    from tools.xlsb_reader import XLSBReaderTool
    from tools.data_cleaner import DataCleaningTool
    from tools.data_merger import DataMergerTool
    from tools.data_validator import DataValidationTool
    from tools.db_loader import DatabaseLoaderTool
    from models.schemas import StorageResult
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    job_id = f"job_{uuid.uuid4().hex}"
    _JOBS[job_id] = {
        "status": "processing",
        "processed_files": [],
        "storage_result": None,
        "total_rows": 0,
    }

    try:
        # Initialize tools
        xlsb_reader = XLSBReaderTool()
        data_cleaner = DataCleaningTool()
        data_merger = DataMergerTool()
        data_validator = DataValidationTool()
        
        # Get database URL from environment or use default
        database_url = os.getenv("DATABASE_URL", "duckdb:///tmp/mms_data.duckdb")
        db_loader = DatabaseLoaderTool(database_url=database_url)
        
        # Process each file
        processed_files = []
        dataframes = {}
        temp_files = []
        
        for file in files:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsb") as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
                temp_files.append(tmp_file_path)
            
            try:
                # Read XLSB file
                df_raw = xlsb_reader.read_file(tmp_file_path)
                
                # Clean data
                df_clean = data_cleaner.clean_dataframe(df_raw)
                
                # Validate data
                quality_report = data_validator.validate_data_quality(df_clean)
                quality_report["sample_rows"] = df_clean.head(5).to_dict(orient="records")
                
                dataframes[file.filename] = df_clean
                
                processed_files.append({
                    "filename": file.filename,
                    "rows": len(df_clean),
                    "quality_score": quality_report.get("overall_score", 0.0),
                    "issues_count": len(quality_report.get("issues", []))
                })
                _JOBS[job_id]["processed_files"].append(
                    {
                        "filename": file.filename,
                        "rows": len(df_clean),
                        "quality": quality_report,
                    }
                )
            except Exception as e:
                processed_files.append({
                    "filename": file.filename,
                    "error": str(e),
                    "success": False
                })
        
        # Merge dataframes if multiple files
        merged_df = None
        if dataframes:
            if len(dataframes) == 1:
                merged_df = list(dataframes.values())[0]
            else:
                merged_df = data_merger.merge_files(dataframes, merge_strategy="union")
        
        # Load to database
        storage_result = None
        if merged_df is not None and not merged_df.empty:
            load_result = db_loader.load_dataframe(merged_df, table_name="sales_aggregated", if_exists="append")
            storage_result = StorageResult(
                success=load_result["success"],
                rows_inserted=load_result.get("rows_inserted", 0),
                table_name=load_result.get("table_name", "sales_aggregated"),
                errors=[load_result["message"]] if not load_result["success"] else None
            )
            _JOBS[job_id]["storage_result"] = storage_result.model_dump()
        
        # Cleanup temp files
        for tmp_file in temp_files:
            try:
                os.unlink(tmp_file)
            except:
                pass
        
        db_loader.close()
        total_rows = len(merged_df) if merged_df is not None else 0
        _JOBS[job_id]["status"] = "completed"
        _JOBS[job_id]["total_rows"] = total_rows
        _JOBS[job_id]["storage_result"] = storage_result.model_dump() if storage_result else None

        return {
            "job_id": job_id,
            "processed_files": processed_files,
            "total_rows": total_rows,
            "storage_result": storage_result.model_dump() if storage_result else None
        }
    except Exception as exc:  # noqa: BLE001
        _JOBS[job_id]["status"] = "failed"
        _JOBS[job_id]["error"] = str(exc)
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(exc)}") from exc


@router.get("/jobs/{job_id}")
async def get_processing_job(job_id: str) -> dict:
    """Return status/details for a processing job."""
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}


@router.get("/quality")
@trace_function(name="data.quality")
async def get_quality_report(
    dataset_id: str | None = None,
    job_id: str | None = None
) -> QualityReport:
    """
    Get data quality report for a dataset.
    
    Args:
        dataset_id: Dataset identifier (table name or file path)
    
    Returns:
        QualityReport object
    """
    from tools.data_validator import DataValidationTool
    from tools.sales_data_tool import SalesDataTool
    import pandas as pd
    from datetime import date, timedelta
    
    try:
        # Reuse quality data from a completed job when provided
        if job_id and job_id in _JOBS:
            job = _JOBS[job_id]
            files = job.get("processed_files", [])
            if files:
                q = files[0].get("quality", {})
                return QualityReport(
                    completeness=q.get("completeness", 0.0),
                    accuracy=q.get("accuracy", 0.0),
                    consistency=q.get("consistency", 0.0),
                    timeliness=q.get("timeliness", 0.0),
                    issues=[issue.get("message", str(issue)) for issue in q.get("issues", [])],
                    recommendations=q.get("recommendations", []),
                    sample_rows=q.get("sample_rows"),
                )

        data_validator = DataValidationTool()
        
        # For MVP: load data from sales tool or database
        sales_tool = SalesDataTool()
        
        # Get recent data (last 90 days) as sample
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        
        df = sales_tool.get_aggregated_sales(
            date_range=(start_date, end_date),
            grain=["date", "channel", "department"]
        )
        
        # Validate data quality
        quality_data = data_validator.validate_data_quality(df)
        
        # Convert to QualityReport schema
        issues_list = [issue.get("message", str(issue)) for issue in quality_data.get("issues", [])]
        recommendations = []
        
        if quality_data.get("completeness", 1.0) < 0.9:
            recommendations.append("Address missing values in critical columns")
        if quality_data.get("accuracy", 1.0) < 0.9:
            recommendations.append("Review data accuracy and validate ranges")
        if quality_data.get("consistency", 1.0) < 0.9:
            recommendations.append("Check data consistency across records")
        if quality_data.get("timeliness", 1.0) < 0.9:
            recommendations.append("Ensure data is up-to-date and timely")
        
        sample_rows = df.head(5).to_dict(orient="records") if not df.empty else []
        
        return QualityReport(
            completeness=quality_data.get("completeness", 0.0),
            accuracy=quality_data.get("accuracy", 0.0),
            consistency=quality_data.get("consistency", 0.0),
            timeliness=quality_data.get("timeliness", 0.0),
            issues=issues_list,
            recommendations=recommendations,
            sample_rows=sample_rows,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error generating quality report: {str(exc)}") from exc


@router.get("/baseline")
async def get_baseline(
    start_date: date,
    end_date: date,
    department: str | None = None,
    channel: str | None = None
) -> BaselineForecast:
    """Get baseline forecast for the requested date range."""
    try:
        df_filters = {"department": department, "channel": channel}
        baseline = baseline_engine.calculate_baseline((start_date, end_date))
        if department or channel:
            agg = sales_tool.get_aggregated_sales(
                date_range=(start_date, end_date),
                grain=["date"],
                filters=df_filters
            )
            if not agg.empty:
                baseline.total_sales = float(agg["sales_value"].sum())
                baseline.total_margin = float(agg["margin_value"].sum())
                baseline.total_units = float(agg["units"].sum())
        return baseline
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/segments")
async def get_segments(
    page: int = 1,
    page_size: int = 20,
    response: Response = None,
) -> dict:
    """Return demo CDP segments."""
    segments = [
        {
            "segment_id": "LOYAL_HIGH_VALUE",
            "name": "Loyal High Value",
            "share_of_customers": 0.18,
            "description": "High frequency, high AOV customers",
        },
        {
            "segment_id": "PRICE_SENSITIVE",
            "name": "Price Sensitive",
            "share_of_customers": 0.32,
            "description": "Promotion responsive shoppers",
        },
        {
            "segment_id": "NEW_CUSTOMERS",
            "name": "New Customers",
            "share_of_customers": 0.12,
            "description": "Acquired in last 90 days",
        },
    ]
    paged, meta = paginate_list(segments, page=page, page_size=page_size)
    if response is not None:
        response.headers["X-Pagination-Page"] = str(meta["page"])
        response.headers["X-Pagination-Page-Size"] = str(meta["page_size"])
        response.headers["X-Pagination-Total"] = str(meta["total"])
        response.headers["X-Pagination-Total-Pages"] = str(meta["total_pages"])
    return {"segments": paged, "pagination": meta}


@router.get("/uplift-model")
async def get_uplift_model(
    department: str | None = None,
    channel: str | None = None
) -> dict:
    """Return a lightweight uplift model snapshot."""
    coefficients = {
        "TV": {"online": 0.18, "store": 0.12},
        "GAMING": {"online": 0.22, "store": 0.15},
        "AUDIO": {"online": 0.14, "store": 0.1},
    }
    filtered = coefficients
    if department:
        dep_key = department.upper()
        filtered = {dep_key: coefficients.get(dep_key, {"online": 0.1, "store": 0.1})}
    if channel:
        channel_key = channel.lower()
        filtered = {
            dep: {channel_key: vals.get(channel_key, 0.1)} for dep, vals in filtered.items()
        }
    return {
        "department": department,
        "channel": channel,
        "coefficients": filtered,
        "version": "demo-1",
    }


@router.post("/store")
async def store_data(
    table_name: str,
    data: dict
) -> StorageResult:
    """
    Store processed data in database.
    
    Args:
        table_name: Target table name
        data: Data to store (should be a DataFrame-like structure)
    
    Returns:
        StorageResult object
    """
    import pandas as pd
    from tools.db_loader import DatabaseLoaderTool
    
    try:
        # Convert data dict to DataFrame
        if isinstance(data, dict) and "data" in data:
            df = pd.DataFrame(data["data"])
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError("Invalid data format")
        
        # Get database URL
        database_url = os.getenv("DATABASE_URL", "duckdb:///tmp/mms_data.duckdb")
        db_loader = DatabaseLoaderTool(database_url=database_url)
        
        # Load data
        load_result = db_loader.load_dataframe(df, table_name=table_name, if_exists="append")
        
        db_loader.close()
        
        return StorageResult(
            success=load_result["success"],
            rows_inserted=load_result.get("rows_inserted", 0),
            table_name=load_result.get("table_name", table_name),
            errors=[load_result["message"]] if not load_result["success"] else None
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error storing data: {str(exc)}") from exc
