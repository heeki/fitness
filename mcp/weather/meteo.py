import openmeteo_requests
import json
import pandas as pd
import requests_cache
from datetime import datetime
from retry_requests import retry
from typing import List, Dict, Any, Optional

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

class Meteo:
    def __init__(self):
        # Setup the OpenMeteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        self.meteo_client = openmeteo_requests.Client(session = retry_session)
        self.historical_url = "https://historical-forecast-api.open-meteo.com/v1/forecast"

    def get_hourly_data(self, latitude: float, longitude: float, start_date: str, end_date: str, timezone: str) -> List[Dict[str, Any]]:
        historical_params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone,
            "hourly": "temperature_2m",
            "wind_speed_unit": "mph",
            "temperature_unit": "fahrenheit",
            "precipitation_unit": "inch"
        }
        print(json.dumps(historical_params, cls=DateTimeEncoder))
        responses = self.meteo_client.weather_api(self.historical_url, params=historical_params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
        # print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
        # print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

        # Process hourly data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}

        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["date"] = hourly_data["date"].tz_convert(historical_params["timezone"])
        hourly_dataframe = pd.DataFrame(data = hourly_data)
        print(hourly_dataframe)
        response = hourly_dataframe.to_dict(orient="records")
        return response

if __name__ == "__main__":
    meteo = Meteo()
    latitude = 40.459742
    longitude = -74.452375
    start_date = "2025-07-22"
    end_date = "2025-07-22"
    timezone = "America/New_York"
    print(meteo.get_hourly_data(latitude, longitude, start_date, end_date, timezone))