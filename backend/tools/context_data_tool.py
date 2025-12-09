"""
Context Data Tool

External context data (events, holidays, seasonality).

API:
get_events(geo: str, date_range: DateRange) -> List[Event]
get_seasonality_profile(geo: str) -> SeasonalityProfile
"""

from typing import List, Optional, Tuple, Dict
from datetime import date, timedelta

from models.schemas import Event, SeasonalityProfile, DateRange


class ContextDataTool:
    """Tool for accessing external context data (events, holidays, seasonality)."""
    
    def __init__(self):
        """Initialize Context Data Tool."""
        # Static fixtures for hackathon bootstrap
        self._seasonality_defaults = SeasonalityProfile(
            geo="DEFAULT",
            monthly_factors={m: 1.0 for m in range(1, 13)},
            weekly_patterns={
                "Monday": 0.95,
                "Tuesday": 1.0,
                "Wednesday": 1.02,
                "Thursday": 1.05,
                "Friday": 1.12,
                "Saturday": 1.15,
                "Sunday": 0.85,
            },
        )
    
    def get_events(
        self,
        geo: str,
        date_range: Tuple[date, date]
    ) -> List[Event]:
        """
        Get events and holidays for a geographic region and date range.
        
        Args:
            geo: Geographic region (e.g., "DE", "UA")
            date_range: Tuple of (start_date, end_date)
        
        Returns:
            List of Event objects
        """
        start_date, end_date = date_range
        span_days = (end_date - start_date).days
        anchor = start_date + timedelta(days=min(span_days // 2, 7))
        return [
            Event(name="Payday weekend", date=anchor, type="seasonal", impact="medium"),
            Event(name="Gaming launch week", date=anchor + timedelta(days=3), type="local_event", impact="high"),
        ]
    
    def get_seasonality_profile(
        self,
        geo: str
    ) -> SeasonalityProfile:
        """
        Get seasonality profile for a geographic region.
        
        Args:
            geo: Geographic region
        
        Returns:
            SeasonalityProfile with seasonal patterns
        """
        profile = self._seasonality_defaults.model_copy()
        profile.geo = geo
        return profile
    
    def get_weekend_patterns(
        self,
        geo: str
    ) -> Dict[str, float]:
        """
        Get weekend shopping patterns for a region.
        
        Args:
            geo: Geographic region
        
        Returns:
            Dictionary with weekend pattern data
        """
        return {"Saturday": 1.15, "Sunday": 0.9}
