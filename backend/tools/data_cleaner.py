"""
Data Cleaning Tool for Data Analyst Agent

Cleans and standardizes sales data formats.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class DataCleaningTool:
    """Tool for cleaning and standardizing data formats."""
    
    # Standard department mappings
    DEPARTMENT_MAPPING = {
        'tv': 'TV',
        'television': 'TV',
        'tvs': 'TV',
        'gaming': 'Gaming',
        'game': 'Gaming',
        'audio': 'Audio',
        'accessories': 'Accessories',
        'accessory': 'Accessories',
        'smartphone': 'Smartphones',
        'phone': 'Smartphones',
        'laptop': 'Computers',
        'computer': 'Computers',
    }
    
    # Standard channel mappings
    CHANNEL_MAPPING = {
        'web': 'online',
        'online': 'online',
        'store': 'offline',
        'stores': 'offline',
        'offline': 'offline',
        'retail': 'offline',
    }
    
    def __init__(self):
        self.required_columns = ['date', 'channel', 'department', 'sales_value', 'margin_value', 'units']
    
    def clean_dataframe(self, df: pd.DataFrame, schema: Optional[Dict] = None) -> pd.DataFrame:
        """
        Clean and standardize DataFrame.
        
        Args:
            df: Raw DataFrame
            schema: Optional schema mapping for column names
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return df
        
        # Apply schema mapping if provided
        if schema:
            df = df.rename(columns=schema)
        
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # Standardize column names (lowercase, strip whitespace)
        df_clean.columns = df_clean.columns.str.lower().str.strip()
        
        # Clean date column
        df_clean = self._clean_dates(df_clean)
        
        # Clean channel column
        df_clean = self._clean_channels(df_clean)
        
        # Clean department column
        df_clean = self._clean_departments(df_clean)
        
        # Clean numeric columns
        df_clean = self._clean_numeric_columns(df_clean)
        
        # Handle missing values
        df_clean = self._handle_missing_values(df_clean)
        
        # Remove duplicates
        df_clean = self._remove_duplicates(df_clean)
        
        # Validate required columns
        df_clean = self._validate_columns(df_clean)
        
        logger.info(f"Cleaned DataFrame: {len(df_clean)} rows, {len(df_clean.columns)} columns")
        return df_clean
    
    def _clean_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize date column."""
        date_columns = ['date', 'datum', 'day', 'transaction_date']
        
        for col in date_columns:
            if col in df.columns:
                # Convert to datetime
                df[col] = pd.to_datetime(df[col], errors='coerce', infer_datetime_format=True)
                # Format as ISO date string
                df[col] = df[col].dt.strftime('%Y-%m-%d')
                # Rename to 'date'
                if col != 'date':
                    df = df.rename(columns={col: 'date'})
                break
        
        # Remove rows with invalid dates
        if 'date' in df.columns:
            df = df[df['date'].notna()]
        
        return df
    
    def _clean_channels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize channel column."""
        channel_columns = ['channel', 'sales_channel', 'type']
        
        for col in channel_columns:
            if col in df.columns:
                # Normalize values
                df[col] = df[col].astype(str).str.lower().str.strip()
                # Map to standard values
                df[col] = df[col].map(self.CHANNEL_MAPPING).fillna(df[col])
                # Validate
                df[col] = df[col].apply(
                    lambda x: x if x in ['online', 'offline'] else None
                )
                # Rename to 'channel'
                if col != 'channel':
                    df = df.rename(columns={col: 'channel'})
                break
        
        return df
    
    def _clean_departments(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize department column."""
        dept_columns = ['department', 'category', 'product_category', 'dept']
        
        for col in dept_columns:
            if col in df.columns:
                # Normalize values
                df[col] = df[col].astype(str).str.strip()
                # Map common variations
                df[col] = df[col].str.lower().map(self.DEPARTMENT_MAPPING).fillna(df[col])
                # Capitalize first letter
                df[col] = df[col].str.capitalize()
                # Rename to 'department'
                if col != 'department':
                    df = df.rename(columns={col: 'department'})
                break
        
        return df
    
    def _clean_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean numeric columns (sales_value, margin_value, units, discount_pct)."""
        numeric_columns = {
            'sales_value': ['sales', 'sales_value', 'revenue', 'turnover', 'amount'],
            'margin_value': ['margin', 'margin_value', 'profit', 'gross_profit'],
            'units': ['units', 'quantity', 'qty', 'items'],
            'discount_pct': ['discount', 'discount_pct', 'discount_percent', 'discount_%']
        }
        
        for target_col, source_cols in numeric_columns.items():
            for source_col in source_cols:
                if source_col in df.columns:
                    # Convert to numeric, handling errors
                    df[target_col] = pd.to_numeric(df[source_col], errors='coerce')
                    # Remove negative values (except for margin which can be negative)
                    if target_col != 'margin_value':
                        df[target_col] = df[target_col].clip(lower=0)
                    # Rename if different
                    if source_col != target_col and target_col not in df.columns:
                        df = df.rename(columns={source_col: target_col})
                    break
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values appropriately."""
        # For required columns, drop rows with missing values
        required = ['date', 'channel', 'department', 'sales_value', 'units']
        for col in required:
            if col in df.columns:
                before = len(df)
                df = df[df[col].notna()]
                after = len(df)
                if before != after:
                    logger.warning(f"Dropped {before - after} rows with missing {col}")
        
        # For margin_value, fill with calculated value if sales_value exists
        if 'margin_value' in df.columns and 'sales_value' in df.columns:
            missing_margin = df['margin_value'].isna() & df['sales_value'].notna()
            if missing_margin.any():
                # Estimate margin as 25% of sales (default)
                df.loc[missing_margin, 'margin_value'] = df.loc[missing_margin, 'sales_value'] * 0.25
                logger.info(f"Estimated margin for {missing_margin.sum()} rows")
        
        # For discount_pct, set to 0 if missing (no promo)
        if 'discount_pct' in df.columns:
            df['discount_pct'] = df['discount_pct'].fillna(0)
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records."""
        before = len(df)
        # Remove exact duplicates
        df = df.drop_duplicates()
        after = len(df)
        
        if before != after:
            logger.info(f"Removed {before - after} duplicate rows")
        
        return df
    
    def _validate_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and ensure required columns exist."""
        missing = [col for col in self.required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        return df



