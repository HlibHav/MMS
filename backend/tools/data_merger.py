"""
Data Merger Tool for Data Analyst Agent

Merges multiple data files handling overlaps and date ranges.
"""

import pandas as pd
from typing import List, Dict, Optional, Literal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataMergerTool:
    """Tool for merging multiple data files."""
    
    def __init__(self):
        pass
    
    def merge_files(
        self,
        dataframes: Dict[str, pd.DataFrame],
        merge_strategy: Literal['union', 'intersect', 'overwrite'] = 'union'
    ) -> pd.DataFrame:
        """
        Merge multiple DataFrames.
        
        Args:
            dataframes: Dictionary mapping file paths to DataFrames
            merge_strategy: How to handle overlapping data
                - 'union': Combine all, keep all records
                - 'intersect': Keep only records present in all files
                - 'overwrite': Later files overwrite earlier ones
        
        Returns:
            Merged DataFrame
        """
        if not dataframes:
            raise ValueError("No dataframes provided")
        
        # Filter out None values
        valid_dfs = {k: v for k, v in dataframes.items() if v is not None and not v.empty}
        
        if not valid_dfs:
            raise ValueError("No valid dataframes to merge")
        
        if len(valid_dfs) == 1:
            return list(valid_dfs.values())[0]
        
        # Ensure all have required columns
        required_cols = ['date', 'channel', 'department']
        for path, df in valid_dfs.items():
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                raise ValueError(f"DataFrame from {path} missing columns: {missing}")
        
        # Sort by file name (assumes chronological order in filename)
        sorted_paths = sorted(valid_dfs.keys())
        
        if merge_strategy == 'union':
            return self._merge_union([valid_dfs[path] for path in sorted_paths])
        elif merge_strategy == 'intersect':
            return self._merge_intersect([valid_dfs[path] for path in sorted_paths])
        elif merge_strategy == 'overwrite':
            return self._merge_overwrite([valid_dfs[path] for path in sorted_paths])
        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")
    
    def _merge_union(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Merge keeping all records, removing duplicates."""
        merged = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates based on date, channel, department
        key_cols = ['date', 'channel', 'department']
        before = len(merged)
        merged = merged.drop_duplicates(subset=key_cols, keep='last')
        after = len(merged)
        
        if before != after:
            logger.info(f"Removed {before - after} duplicate records in union merge")
        
        return merged.sort_values('date').reset_index(drop=True)
    
    def _merge_intersect(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Merge keeping only records present in all DataFrames."""
        if len(dfs) == 1:
            return dfs[0]
        
        # Find intersection of date/channel/department combinations
        key_cols = ['date', 'channel', 'department']
        
        # Get all unique combinations from first DataFrame
        intersection = set(
            dfs[0][key_cols].apply(tuple, axis=1)
        )
        
        # Intersect with all other DataFrames
        for df in dfs[1:]:
            combinations = set(df[key_cols].apply(tuple, axis=1))
            intersection = intersection & combinations
        
        # Filter all DataFrames to intersection
        filtered_dfs = []
        for df in dfs:
            mask = df[key_cols].apply(tuple, axis=1).isin(intersection)
            filtered_dfs.append(df[mask])
        
        # Merge filtered DataFrames
        merged = pd.concat(filtered_dfs, ignore_index=True)
        merged = merged.drop_duplicates(subset=key_cols, keep='last')
        
        logger.info(f"Intersect merge: {len(merged)} records from {len(intersection)} unique combinations")
        return merged.sort_values('date').reset_index(drop=True)
    
    def _merge_overwrite(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Merge with later files overwriting earlier ones."""
        merged = pd.concat(dfs, ignore_index=True)
        
        # Keep last occurrence for each date/channel/department combination
        key_cols = ['date', 'channel', 'department']
        merged = merged.drop_duplicates(subset=key_cols, keep='last')
        
        logger.info(f"Overwrite merge: {len(merged)} records (later files overwrite earlier)")
        return merged.sort_values('date').reset_index(drop=True)
    
    def detect_overlaps(self, dfs: Dict[str, pd.DataFrame]) -> Dict:
        """
        Detect date range overlaps between DataFrames.
        
        Returns:
            Dictionary with overlap information
        """
        overlaps = []
        
        file_list = list(dfs.items())
        for i, (path1, df1) in enumerate(file_list):
            if df1 is None or df1.empty or 'date' not in df1.columns:
                continue
            
            date_range1 = (df1['date'].min(), df1['date'].max())
            
            for j, (path2, df2) in enumerate(file_list[i+1:], start=i+1):
                if df2 is None or df2.empty or 'date' not in df2.columns:
                    continue
                
                date_range2 = (df2['date'].min(), df2['date'].max())
                
                # Check for overlap
                if date_range1[0] <= date_range2[1] and date_range2[0] <= date_range1[1]:
                    overlap_start = max(date_range1[0], date_range2[0])
                    overlap_end = min(date_range1[1], date_range2[1])
                    
                    overlaps.append({
                        'file1': path1,
                        'file2': path2,
                        'overlap_start': overlap_start,
                        'overlap_end': overlap_end,
                        'overlap_days': (pd.to_datetime(overlap_end) - pd.to_datetime(overlap_start)).days + 1
                    })
        
        return {
            'has_overlaps': len(overlaps) > 0,
            'overlaps': overlaps
        }



