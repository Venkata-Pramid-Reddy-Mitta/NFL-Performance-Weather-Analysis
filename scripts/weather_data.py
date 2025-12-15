import pandas as pd
import os
import numpy as np
from typing import Optional
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
import pytz
import time
from meteostat import Point, Hourly

# Configure polite defaults for Meteostat enrichment
_GEOCODER_USER_AGENT = "nfl-weather-enricher"
_GEOCODER_TIMEOUT = 10
_GEOCODE_SLEEP = 1.0  # seconds between geocoding calls
_FETCH_WINDOW_HOURS = 1  # +/- hours around kickoff to average


def collect_weather_data(nfl_data):
    """
    Processes existing NFL data to extract weather-specific subsets.
    
    Parameters:
    -----------
    nfl_data : pd.DataFrame
        The dataframe returned by download_nfl_data()

    Returns:
    --------
    tuple
        (all_games_df, outdoor_games_df)
    """
    if not os.path.exists('data'):
        os.makedirs('data')

    # We use the data passed in, rather than downloading again
    df = nfl_data.copy()

    # Columns relevant for weather analysis
    cols = ['game_id', 'season', 'week', 'gameday', 'weekday',
            'home_team', 'away_team', 'home_score', 'away_score',
            'temp', 'wind', 'roof', 'surface', 'stadium', 
            'total_points', 'point_differential', 'home_win']

    # Add gametime if available
    if 'gametime' in df.columns:
        cols.append('gametime')

    all_games = df[cols].copy()

    # Filter for outdoor games (where temp is not null)
    outdoor = all_games[all_games['temp'].notna()].copy()
    
    return all_games, outdoor


def add_gametime_from_nfl_data(games_df, nfl_data):
    """
    Merge gametime from nfl_data into games_df by matching game_id.
    """
    if 'gametime' in games_df.columns:
        return games_df  # Already has gametime

    # Efficient pandas merge instead of manual logic
    return games_df.merge(nfl_data[['game_id', 'gametime']], on='game_id', how='left')


def enrich_games_with_meteostat(
    all_games: pd.DataFrame,
    stadium_col: str = "stadium",
    gameday_col: str = "gameday",
    gametime_col: Optional[str] = "gametime",
    city_col: Optional[str] = None,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Enrich `all_games` DataFrame with Meteostat weather fields.
    """
    df = all_games.copy().reset_index(drop=True)
    if max_rows is not None:
        df = df.iloc[:max_rows].copy()

    geolocator = Nominatim(user_agent=_GEOCODER_USER_AGENT, timeout=_GEOCODER_TIMEOUT)
    tf = TimezoneFinder()

    # caches
    latlon_cache = {}
    weather_cache = {}
    out_rows = []

    print(f"Starting enrichment for {len(df)} games...")

    for idx, row in df.iterrows():
        # Feedback every 100 rows
        if idx > 0 and idx % 100 == 0:
            print(f"Processed {idx} games...")
            
        stadium = str(row.get(stadium_col, "") or "")
        city = str(row.get(city_col, "") or "") if city_col else ""
        place = f"{stadium}, {city}".strip(", ")

        # 1) geocode (cached)
        if place in latlon_cache:
            lat, lon = latlon_cache[place]
        else:
            lat, lon = _geocode_place(place, geolocator)
            if (lat is None or lon is None) and stadium:
                lat, lon = _geocode_place(stadium, geolocator)
            latlon_cache[place] = (lat, lon)
            time.sleep(_GEOCODE_SLEEP)

        # default outputs
        default_out = {
            "met_lat": np.nan, "met_lon": np.nan, "met_temp_C": np.nan,
            "met_prcp_mm": np.nan, "met_windspeed_mps": np.nan, 
            "met_source_time_utc": pd.NaT,
        }

        if lat is None or lon is None:
            out_rows.append(default_out)
            continue

        # 2) parse gameday + gametime -> target UTC
        gameday = pd.to_datetime(row[gameday_col])
        
        # Parse gametime safely
        hour, minute = 13, 0
        if gametime_col and gametime_col in row.index and pd.notna(row[gametime_col]):
            try:
                gametime_str = str(row[gametime_col])
                if ':' in gametime_str:
                    parts = gametime_str.split(':')
                    hour, minute = int(parts[0]), int(parts[1])
            except:
                pass

        kickoff_local = gameday.replace(hour=hour, minute=minute)
        
        # Simple timezone handling
        try:
            tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
            tz = pytz.timezone(tz_name)
            kickoff_localized = tz.localize(kickoff_local)
            kickoff_utc = kickoff_localized.astimezone(pytz.UTC)
        except:
            kickoff_utc = kickoff_local.tz_localize(pytz.UTC)

        # 3) check cache for weather
        cache_key = (round(lat, 4), round(lon, 4), kickoff_utc.strftime("%Y-%m-%dT%H"))
        if cache_key in weather_cache:
            features = weather_cache[cache_key]
        else:
            features = _fetch_meteostat_for_point(lat, lon, kickoff_utc)
            weather_cache[cache_key] = features

        if features is None:
            out_rows.append(default_out)
        else:
            out_rows.append({
                "met_lat": lat,
                "met_lon": lon,
                "met_temp_C": features.get("temp_mean_C", np.nan),
                "met_prcp_mm": features.get("prcp_mean_mm", np.nan),
                "met_windspeed_mps": features.get("wspd_mean_mps", np.nan),
                "met_source_time_utc": features.get("source_time_utc", pd.NaT),
            })

    return pd.concat([df, pd.DataFrame(out_rows)], axis=1)


# ---------- helper functions ----------

def _geocode_place(place, geolocator):
    if not place: return None, None
    try:
        loc = geolocator.geocode(place, addressdetails=False, timeout=10)
        return (float(loc.latitude), float(loc.longitude)) if loc else (None, None)
    except:
        return None, None

def _fetch_meteostat_for_point(lat, lon, kickoff_utc):
    try:
        # Convert to naive datetime for Meteostat
        start = (kickoff_utc - timedelta(hours=_FETCH_WINDOW_HOURS)).replace(tzinfo=None)
        end = (kickoff_utc + timedelta(hours=_FETCH_WINDOW_HOURS)).replace(tzinfo=None)

        data = Hourly(Point(lat, lon), start, end).fetch()
        
        if data is None or data.empty:
            return None

        return {
            "temp_mean_C": float(data["temp"].mean()) if "temp" in data else np.nan,
            "prcp_mean_mm": float(data["prcp"].mean()) if "prcp" in data else np.nan,
            "wspd_mean_mps": float(data["wspd"].mean()) if "wspd" in data else np.nan,
            "source_time_utc": kickoff_utc
        }
    except:
        return None