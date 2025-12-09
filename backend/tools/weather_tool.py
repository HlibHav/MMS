"""
Weather Tool for Context Engine

Uses Open-Meteo API (free, no API key required) to fetch weather forecasts.
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class WeatherTool:
    """Tool for fetching weather forecasts from Open-Meteo API."""
    
    # Open-Meteo API base URL
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Geographic coordinates for major cities/regions
    GEO_COORDINATES = {
        "DE": {"latitude": 51.1657, "longitude": 10.4515, "name": "Germany"},
        "UA": {"latitude": 48.3794, "longitude": 31.1656, "name": "Ukraine"},
        "PL": {"latitude": 51.9194, "longitude": 19.1451, "name": "Poland"},
        "FR": {"latitude": 46.2276, "longitude": 2.2137, "name": "France"},
        "IT": {"latitude": 41.8719, "longitude": 12.5674, "name": "Italy"},
        "ES": {"latitude": 40.4637, "longitude": -3.7492, "name": "Spain"},
    }
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Weather Tool.
        
        Args:
            base_url: Optional custom API base URL (for testing)
        """
        self.base_url = base_url or self.BASE_URL
    
    def get_weather_forecast(
        self,
        location: str,
        date_range_start: date,
        date_range_end: date,
        timezone: str = "auto"
    ) -> Dict:
        """
        Get weather forecast for a location and date range.
        
        Args:
            location: Geographic code (e.g., "DE", "UA") or coordinates
            date_range_start: Start date
            date_range_end: End date
            timezone: Timezone (default: "auto")
            
        Returns:
            Dictionary with weather forecast data:
            {
                "location": str,
                "date_range": {"start": str, "end": str},
                "summary": str,
                "daily": [
                    {
                        "date": str,
                        "condition": str,
                        "temp_max": float,
                        "temp_min": float,
                        "rain_prob": float,
                        "rain_sum": float,
                        "cloud_cover": float
                    }
                ]
            }
        """
        try:
            # Get coordinates for location
            coords = self._get_coordinates(location)
            if not coords:
                raise ValueError(f"Unknown location: {location}")
            
            # Format dates
            start_str = date_range_start.strftime("%Y-%m-%d")
            end_str = date_range_end.strftime("%Y-%m-%d")
            
            # Build API request
            params = {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "start_date": start_str,
                "end_date": end_str,
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_probability_max",
                    "precipitation_sum",
                    "weather_code",
                    "cloud_cover_max"
                ],
                "timezone": timezone
            }
            
            # Make API request
            logger.info(f"Fetching weather for {location} ({start_str} to {end_str})")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response
            daily_data = data.get("daily", {})
            
            # Map weather codes to conditions
            weather_codes = daily_data.get("weather_code", [])
            dates = daily_data.get("time", [])
            temp_max = daily_data.get("temperature_2m_max", [])
            temp_min = daily_data.get("temperature_2m_min", [])
            rain_prob = daily_data.get("precipitation_probability_max", [])
            rain_sum = daily_data.get("precipitation_sum", [])
            cloud_cover = daily_data.get("cloud_cover_max", [])
            
            # Build daily forecast list
            daily_forecast = []
            for i, date_str in enumerate(dates):
                condition = self._weather_code_to_condition(
                    weather_codes[i] if i < len(weather_codes) else 0
                )
                
                daily_forecast.append({
                    "date": date_str,
                    "condition": condition,
                    "temp_max": temp_max[i] if i < len(temp_max) else None,
                    "temp_min": temp_min[i] if i < len(temp_min) else None,
                    "temp_avg": (
                        (temp_max[i] + temp_min[i]) / 2
                        if i < len(temp_max) and i < len(temp_min)
                        else None
                    ),
                    "rain_prob": rain_prob[i] if i < len(rain_prob) else 0,
                    "rain_sum": rain_sum[i] if i < len(rain_sum) else 0,
                    "cloud_cover": cloud_cover[i] if i < len(cloud_cover) else None
                })
            
            # Generate summary
            summary = self._generate_summary(daily_forecast)
            
            return {
                "location": location,
                "coordinates": coords,
                "date_range": {
                    "start": start_str,
                    "end": end_str
                },
                "summary": summary,
                "daily": daily_forecast
            }
            
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing weather data: {str(e)}")
            raise
    
    def _get_coordinates(self, location: str) -> Optional[Dict]:
        """
        Get coordinates for a location.
        
        Args:
            location: Geographic code or "lat,lon" format
            
        Returns:
            Dictionary with latitude and longitude, or None
        """
        # Check if it's already coordinates
        if "," in location:
            try:
                lat, lon = map(float, location.split(","))
                return {"latitude": lat, "longitude": lon, "name": location}
            except ValueError:
                return None
        
        # Check predefined locations
        location_upper = location.upper()
        if location_upper in self.GEO_COORDINATES:
            return self.GEO_COORDINATES[location_upper]
        
        return None
    
    def _weather_code_to_condition(self, code: int) -> str:
        """
        Convert WMO weather code to condition string.
        
        Args:
            code: WMO weather code (0-99)
            
        Returns:
            Condition string: "sun", "cloud", "rain", "snow", "storm"
        """
        # WMO Weather Code mapping
        if code == 0:
            return "sun"  # Clear sky
        elif code in [1, 2, 3]:
            return "cloud"  # Mainly clear, partly cloudy, overcast
        elif code in [45, 48]:
            return "cloud"  # Fog
        elif code in [51, 53, 55, 56, 57]:
            return "rain"  # Drizzle
        elif code in [61, 63, 65, 66, 67]:
            return "rain"  # Rain
        elif code in [71, 73, 75, 77]:
            return "snow"  # Snow
        elif code in [80, 81, 82]:
            return "rain"  # Rain showers
        elif code in [85, 86]:
            return "snow"  # Snow showers
        elif code in [95, 96, 99]:
            return "storm"  # Thunderstorm
        else:
            return "cloud"  # Default
    
    def _generate_summary(self, daily_forecast: List[Dict]) -> str:
        """
        Generate human-readable weather summary.
        
        Args:
            daily_forecast: List of daily forecast dictionaries
            
        Returns:
            Summary string
        """
        if not daily_forecast:
            return "No weather data available"
        
        # Count conditions
        conditions = [day["condition"] for day in daily_forecast]
        condition_counts = {}
        for cond in conditions:
            condition_counts[cond] = condition_counts.get(cond, 0) + 1
        
        # Find dominant condition
        dominant = max(condition_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate average temperature
        temps = [day["temp_avg"] for day in daily_forecast if day["temp_avg"] is not None]
        avg_temp = sum(temps) / len(temps) if temps else None
        
        # Check for rain
        rainy_days = sum(1 for day in daily_forecast if day["rain_prob"] > 60)
        
        # Build summary
        summary_parts = []
        
        if dominant == "rain" and rainy_days > len(daily_forecast) / 2:
            summary_parts.append("rainy")
        elif dominant == "snow":
            summary_parts.append("snowy")
        elif dominant == "sun":
            summary_parts.append("sunny")
        else:
            summary_parts.append("cloudy")
        
        if rainy_days > 0:
            summary_parts.append(f"with {rainy_days} rainy day(s)")
        
        if avg_temp is not None:
            summary_parts.append(f"avg {avg_temp:.1f}°C")
        
        return ", ".join(summary_parts)
    
    def get_historical_weather(
        self,
        location: str,
        date: date
    ) -> Dict:
        """
        Get historical weather data (for past dates).
        
        Uses Open-Meteo historical weather API.
        
        Args:
            location: Geographic code
            date: Date to get historical data for
            
        Returns:
            Historical weather data
        """
        # Open-Meteo historical API endpoint
        historical_url = "https://archive-api.open-meteo.com/v1/archive"
        
        coords = self._get_coordinates(location)
        if not coords:
            raise ValueError(f"Unknown location: {location}")
        
        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "start_date": date.strftime("%Y-%m-%d"),
            "end_date": date.strftime("%Y-%m-%d"),
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "weather_code"
            ]
        }
        
        try:
            response = requests.get(historical_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching historical weather: {str(e)}")
            raise



