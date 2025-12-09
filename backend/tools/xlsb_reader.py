"""
XLSB Reader Tool for Data Analyst Agent

Reads and parses XLSB (Excel Binary) files containing sales data.
"""

import pandas as pd
from pyxlsb import open_workbook
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class XLSBReaderTool:
    """Tool for reading XLSB files and converting to DataFrames."""
    
    def __init__(self):
        self.supported_formats = ['.xlsb', '.xlsx', '.csv']
    
    def read_file(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Read XLSB file and return as DataFrame.
        
        Args:
            file_path: Path to XLSB file
            sheet_name: Optional sheet name (uses first sheet if None)
            
        Returns:
            DataFrame with data from the file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        ext = Path(file_path).suffix.lower()
        if ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format. Expected one of {self.supported_formats}, got {file_path}")

        # Fast paths for demo: CSV/XLSX via pandas
        if ext in [".csv", ".xlsx"]:
            df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)
            logger.info(f"Read {len(df)} rows from {file_path}")
            return df
        
        try:
            # Read XLSB file
            with open_workbook(file_path) as wb:
                # Get sheet name
                if sheet_name is None:
                    sheet_name = wb.sheets[0].name
                
                # Read sheet
                with wb.get_sheet(sheet_name) as sheet:
                    # Read all rows
                    rows = []
                    for row in sheet.rows():
                        rows.append([cell.v for cell in row])
                    
                    # Convert to DataFrame
                    if rows:
                        # First row as header
                        df = pd.DataFrame(rows[1:], columns=rows[0])
                        logger.info(f"Read {len(df)} rows from {file_path}")
                        return df
                    else:
                        logger.warning(f"Empty file: {file_path}")
                        return pd.DataFrame()
                        
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            raise
    
    def inspect_file(self, file_path: str) -> Dict:
        """
        Inspect XLSB file structure without reading all data.
        
        Args:
            file_path: Path to XLSB file
            
        Returns:
            Dictionary with file metadata:
            - sheets: List of sheet names
            - columns: Column names from first sheet
            - row_count: Estimated row count
        """
        try:
            with open_workbook(file_path) as wb:
                sheets = [sheet.name for sheet in wb.sheets]
                
                # Get columns from first sheet
                with wb.get_sheet(sheets[0]) as sheet:
                    # Read first row for headers
                    first_row = next(sheet.rows())
                    columns = [cell.v for cell in first_row]
                    
                    # Estimate row count (approximate)
                    row_count = sum(1 for _ in sheet.rows())
                
                return {
                    "file_path": file_path,
                    "sheets": sheets,
                    "columns": columns,
                    "row_count": row_count,
                    "file_size_mb": round(pd.io.common.file_size(file_path) / (1024 * 1024), 2)
                }
        except Exception as e:
            logger.error(f"Error inspecting {file_path}: {str(e)}")
            raise
    
    def read_multiple_files(self, file_paths: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Read multiple XLSB files.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Dictionary mapping file paths to DataFrames
        """
        results = {}
        for file_path in file_paths:
            try:
                df = self.read_file(file_path)
                results[file_path] = df
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {str(e)}")
                results[file_path] = None
        
        return results


