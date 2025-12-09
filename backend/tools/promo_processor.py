"""
Promo Data Processor

Specialized processor for promotional catalog XLSB files.
Extends Data Analyst Agent capabilities for promo-specific data.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .xlsb_reader import XLSBReaderTool
from .data_cleaner import DataCleaningTool
from .data_validator import DataValidationTool
from .db_loader import DatabaseLoaderTool
from .promo_catalog_tool import PromoCatalogTool, PromoCampaign

logger = logging.getLogger(__name__)


class PromoProcessor:
    """Processor for promotional catalog XLSB files."""
    
    def __init__(self, database_url: str):
        """
        Initialize Promo Processor.
        
        Args:
            database_url: Database connection string
        """
        self.database_url = database_url
        self.xlsb_reader = XLSBReaderTool()
        self.data_cleaner = DataCleaningTool()
        self.data_validator = DataValidationTool()
        self.db_loader = DatabaseLoaderTool(database_url)
        self.promo_catalog = PromoCatalogTool(xlsb_reader=self.xlsb_reader)
    
    def process_promo_file(
        self,
        file_path: str,
        load_to_db: bool = True
    ) -> Dict:
        """
        Process promotional catalog XLSB file.
        
        Args:
            file_path: Path to XLSB file
            load_to_db: Whether to load to database
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing promo file: {file_path}")
        
        results = {
            "file_path": file_path,
            "success": False,
            "campaigns_extracted": 0,
            "records_processed": 0,
            "quality_report": None,
            "errors": []
        }
        
        try:
            # Step 1: Read XLSB file
            logger.info("Reading XLSB file...")
            df = self.xlsb_reader.read_file(file_path)
            results["records_processed"] = len(df)
            
            # Step 2: Clean data
            logger.info("Cleaning data...")
            df_clean = self.data_cleaner.clean_dataframe(df)
            
            # Step 3: Validate quality
            logger.info("Validating data quality...")
            quality_report = self.data_validator.validate_data_quality(df_clean)
            results["quality_report"] = quality_report
            
            # Step 4: Extract promotional campaigns
            logger.info("Extracting promotional campaigns...")
            campaigns = self.promo_catalog.process_promo_dataframe(df_clean)
            results["campaigns_extracted"] = len(campaigns)
            
            # Step 5: Load to database if requested
            if load_to_db:
                logger.info("Loading to database...")
                # Load promo data to promo_catalog table
                # Note: This might need special handling depending on schema
                # For now, we'll store the cleaned data
                db_result = self.db_loader.load_dataframe(
                    df_clean,
                    table_name='promo_catalog',
                    if_exists='append'
                )
                results["db_result"] = db_result
            
            results["success"] = True
            results["campaigns"] = [c.to_dict() for c in campaigns]
            
            logger.info(f"Successfully processed promo file: {len(campaigns)} campaigns extracted")
            
        except Exception as e:
            logger.error(f"Error processing promo file: {str(e)}")
            results["errors"].append(str(e))
            results["success"] = False
        
        return results
    
    def process_multiple_promo_files(
        self,
        file_paths: List[str],
        load_to_db: bool = True
    ) -> Dict:
        """
        Process multiple promotional catalog files.
        
        Args:
            file_paths: List of file paths
            load_to_db: Whether to load to database
            
        Returns:
            Dictionary with results for each file
        """
        results = {
            "files_processed": 0,
            "total_campaigns": 0,
            "file_results": []
        }
        
        for file_path in file_paths:
            file_result = self.process_promo_file(file_path, load_to_db)
            results["file_results"].append(file_result)
            
            if file_result["success"]:
                results["files_processed"] += 1
                results["total_campaigns"] += file_result["campaigns_extracted"]
        
        return results

