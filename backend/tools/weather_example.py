"""
Example usage of Weather Tool with Open-Meteo API.
"""

from weather_tool import WeatherTool
from datetime import date, timedelta

def example_weather_forecast():
    """Example of fetching weather forecast."""
    
    # Initialize tool
    weather = WeatherTool()
    
    # Get forecast for Germany, next 7 days
    start_date = date.today()
    end_date = start_date + timedelta(days=7)
    
    print("Fetching weather forecast...")
    forecast = weather.get_weather_forecast(
        location="DE",
        date_range_start=start_date,
        date_range_end=end_date
    )
    
    print(f"\nLocation: {forecast['location']}")
    print(f"Date Range: {forecast['date_range']['start']} to {forecast['date_range']['end']}")
    print(f"Summary: {forecast['summary']}")
    print("\nDaily Forecast:")
    print("-" * 60)
    
    for day in forecast['daily']:
        print(f"\n{day['date']}:")
        print(f"  Condition: {day['condition']}")
        print(f"  Temperature: {day['temp_min']:.1f}°C - {day['temp_max']:.1f}°C")
        print(f"  Rain Probability: {day['rain_prob']:.0f}%")
        if day['rain_sum'] > 0:
            print(f"  Rain Amount: {day['rain_sum']:.1f}mm")
        print(f"  Cloud Cover: {day['cloud_cover']:.0f}%")

if __name__ == "__main__":
    example_weather_forecast()



