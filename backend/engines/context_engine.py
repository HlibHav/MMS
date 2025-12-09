"""
Context Engine

Builds comprehensive context for promotional planning.

Input: geo, date_range, external data
Output: PromoContext with:
- Events and holidays
- Seasonality factors
- Weather profile
- Weekend patterns
"""

from typing import Optional, Tuple
from datetime import date

from models.schemas import PromoContext, DateRange
from tools.context_data_tool import ContextDataTool
from tools.weather_tool import WeatherTool


class ContextEngine:
    """Engine for building comprehensive promotional context."""
    
    def __init__(
        self,
        context_tool: Optional[ContextDataTool] = None,
        weather_tool: Optional[WeatherTool] = None,
    ):
        """
        Initialize Context Engine.
        
        Args:
            context_tool: Context Data Tool instance
            weather_tool: Weather Tool instance
        """
        self.context_tool = context_tool
        self.weather_tool = weather_tool
    
    def build_context(
        self,
        geo: str,
        date_range: DateRange
    ) -> PromoContext:
        """
        Build comprehensive context for promotional planning.
        
        Args:
            geo: Geographic region (e.g., "DE", "UA")
            date_range: DateRange tuple (start_date, end_date)
        
        Returns:
            PromoContext with events, weather, seasonality
        """
        from tools.context_data_tool import ContextDataTool
        from tools.weather_tool import WeatherTool
        
        context_tool = self.context_tool or ContextDataTool()
        weather_tool = self.weather_tool
        
        # Get events and seasonality
        events = context_tool.get_events(geo, (date_range.start_date, date_range.end_date))
        seasonality = context_tool.get_seasonality_profile(geo)
        weekend_patterns = context_tool.get_weekend_patterns(geo)
        
        # Get weather if tool is available
        weather = None
        if weather_tool:
            try:
                weather_data = weather_tool.get_weather_forecast(
                    location=geo,
                    date_range_start=date_range.start_date,
                    date_range_end=date_range.end_date
                )
                weather = weather_data.model_dump() if hasattr(weather_data, 'model_dump') else weather_data
            except Exception:
                # Weather is optional, continue without it
                pass
        
        return PromoContext(
            geo=geo,
            date_range=date_range,
            events=events,
            weather=weather,
            seasonality=seasonality,
            weekend_patterns=weekend_patterns
        )

