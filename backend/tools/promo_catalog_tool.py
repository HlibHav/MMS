"""
Promo Catalog Tool

Access to historical promotional campaigns.
Supports reading from XLSB files and database.
"""

from typing import List, Optional, Dict, Any
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PromoCampaign:
    """Promotional campaign data structure."""
    
    def __init__(self, data: Dict):
        self.id = data.get('id')
        self.promo_name = data.get('promo_name')
        self.date_start = data.get('date_start')
        self.date_end = data.get('date_end')
        self.departments = data.get('departments', [])
        self.channels = data.get('channels', [])
        self.avg_discount_pct = data.get('avg_discount_pct')
        self.mechanics = data.get('mechanics', {})
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'promo_name': self.promo_name,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'departments': self.departments,
            'channels': self.channels,
            'avg_discount_pct': self.avg_discount_pct,
            'mechanics': self.mechanics
        }


class PromoCatalogTool:
    """Tool for accessing historical promotional campaigns."""
    
    def __init__(self, db_connection=None, xlsb_reader=None):
        """
        Initialize Promo Catalog Tool.
        
        Args:
            db_connection: Database connection object
            xlsb_reader: XLSBReaderTool instance for reading XLSB files
        """
        self.db_connection = db_connection
        self.xlsb_reader = xlsb_reader
        self._promo_cache = None
    
    def load_from_xlsb(self, file_path: str) -> pd.DataFrame:
        """
        Load promotional data from XLSB file.
        
        Args:
            file_path: Path to XLSB file
            
        Returns:
            DataFrame with promo data
        """
        if self.xlsb_reader is None:
            from .xlsb_reader import XLSBReaderTool
            self.xlsb_reader = XLSBReaderTool()
        
        logger.info(f"Loading promo data from {file_path}")
        df = self.xlsb_reader.read_file(file_path)
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.strip()
        
        return df
    
    def process_promo_dataframe(self, df: pd.DataFrame) -> List[PromoCampaign]:
        """
        Process promo DataFrame and extract campaign information.
        
        Args:
            df: DataFrame with promo data
            
        Returns:
            List of PromoCampaign objects
        """
        if df.empty:
            return []
        
        campaigns = []
        
        # Try to identify promo campaigns from the data
        # This depends on the structure of the XLSB file
        
        # Option 1: If there's a promo_name or campaign column
        if 'promo_name' in df.columns or 'campaign' in df.columns:
            promo_col = 'promo_name' if 'promo_name' in df.columns else 'campaign'
            grouped = df.groupby(promo_col)
            
            for promo_name, group in grouped:
                # Get date range
                if 'date' in group.columns:
                    date_start = pd.to_datetime(group['date']).min().date()
                    date_end = pd.to_datetime(group['date']).max().date()
                else:
                    date_start = None
                    date_end = None
                
                # Get departments
                departments = []
                if 'department' in group.columns:
                    departments = group['department'].unique().tolist()
                
                # Get channels
                channels = []
                if 'channel' in group.columns:
                    channels = group['channel'].unique().tolist()
                
                # Get average discount
                avg_discount = None
                if 'discount_pct' in group.columns:
                    avg_discount = group['discount_pct'].mean()
                
                campaign = PromoCampaign({
                    'id': f"promo_{promo_name}_{date_start}",
                    'promo_name': promo_name,
                    'date_start': str(date_start) if date_start else None,
                    'date_end': str(date_end) if date_end else None,
                    'departments': departments,
                    'channels': channels,
                    'avg_discount_pct': float(avg_discount) if avg_discount else None,
                    'mechanics': {}
                })
                campaigns.append(campaign)
        
        # Option 2: Group by date ranges with discounts
        elif 'date' in df.columns and 'discount_pct' in df.columns:
            # Group consecutive days with discounts as campaigns
            df_sorted = df.sort_values('date')
            df_sorted['date'] = pd.to_datetime(df_sorted['date'])
            df_sorted['has_discount'] = df_sorted['discount_pct'] > 0
            
            # Find promo periods (consecutive days with discounts)
            promo_periods = []
            current_period = None
            
            for idx, row in df_sorted.iterrows():
                if row['has_discount']:
                    if current_period is None:
                        current_period = {
                            'start': row['date'],
                            'end': row['date'],
                            'rows': [row]
                        }
                    else:
                        # Check if consecutive day
                        if (row['date'] - current_period['end']).days <= 1:
                            current_period['end'] = row['date']
                            current_period['rows'].append(row)
                        else:
                            # Save current period and start new one
                            promo_periods.append(current_period)
                            current_period = {
                                'start': row['date'],
                                'end': row['date'],
                                'rows': [row]
                            }
                else:
                    if current_period is not None:
                        promo_periods.append(current_period)
                        current_period = None
            
            if current_period is not None:
                promo_periods.append(current_period)
            
            # Create campaigns from periods
            for i, period in enumerate(promo_periods):
                period_df = pd.DataFrame(period['rows'])
                
                departments = []
                if 'department' in period_df.columns:
                    departments = period_df['department'].unique().tolist()
                
                channels = []
                if 'channel' in period_df.columns:
                    channels = period_df['channel'].unique().tolist()
                
                avg_discount = period_df['discount_pct'].mean() if 'discount_pct' in period_df.columns else None
                
                campaign = PromoCampaign({
                    'id': f"promo_period_{i+1}_{period['start'].date()}",
                    'promo_name': f"Promo Period {i+1}",
                    'date_start': str(period['start'].date()),
                    'date_end': str(period['end'].date()),
                    'departments': departments,
                    'channels': channels,
                    'avg_discount_pct': float(avg_discount) if avg_discount else None,
                    'mechanics': {}
                })
                campaigns.append(campaign)
        
        logger.info(f"Extracted {len(campaigns)} promotional campaigns")
        return campaigns
    
    def get_past_promos(
        self,
        filters: Optional[Dict[str, Any]] = None,
        xlsb_file_path: Optional[str] = None
    ) -> List[PromoCampaign]:
        """
        Get past promotional campaigns.
        
        Args:
            filters: Optional dictionary of filters:
                - date_start: Start date
                - date_end: End date
                - channel: Filter by channel
                - department: Filter by department
            xlsb_file_path: Optional path to XLSB file to load from
        
        Returns:
            List of PromoCampaign objects
        """
        campaigns = []
        
        # Load from XLSB file if provided
        if xlsb_file_path:
            df = self.load_from_xlsb(xlsb_file_path)
            campaigns = self.process_promo_dataframe(df)
        elif self._promo_cache is not None:
            campaigns = self._promo_cache
        else:
            # Try to load from database
            if self.db_connection:
                campaigns = self._load_from_database()
            else:
                logger.warning("No data source available for promo catalog")
                return []
        
        # Apply filters
        if filters:
            campaigns = self._apply_filters(campaigns, filters)
        
        return campaigns
    
    def _load_from_database(self) -> List[PromoCampaign]:
        """Load campaigns from database."""
        # TODO: Implement database loading
        logger.warning("Database loading not yet implemented")
        return []
    
    def _apply_filters(
        self,
        campaigns: List[PromoCampaign],
        filters: Dict[str, Any]
    ) -> List[PromoCampaign]:
        """Apply filters to campaigns."""
        filtered = campaigns
        
        if 'date_start' in filters:
            date_start = pd.to_datetime(filters['date_start']).date()
            filtered = [c for c in filtered if c.date_start and pd.to_datetime(c.date_start).date() >= date_start]
        
        if 'date_end' in filters:
            date_end = pd.to_datetime(filters['date_end']).date()
            filtered = [c for c in filtered if c.date_end and pd.to_datetime(c.date_end).date() <= date_end]
        
        if 'channel' in filters:
            channel = filters['channel']
            filtered = [c for c in filtered if channel in c.channels or not c.channels]
        
        if 'department' in filters:
            department = filters['department']
            filtered = [c for c in filtered if department in c.departments or not c.departments]
        
        return filtered
    
    def get_promo_by_id(
        self,
        promo_id: str
    ) -> Optional[PromoCampaign]:
        """
        Get specific promotional campaign by ID.
        
        Args:
            promo_id: Campaign ID
        
        Returns:
            PromoCampaign object or None
        """
        # Load all campaigns if not cached
        if self._promo_cache is None:
            self._promo_cache = self.get_past_promos()
        
        for campaign in self._promo_cache:
            if campaign.id == promo_id:
                return campaign
        
        return None
    
    def cache_promos(self, campaigns: List[PromoCampaign]):
        """Cache promotional campaigns."""
        self._promo_cache = campaigns



