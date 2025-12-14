"""
Weather Data Collection
Research Question: How do weather conditions impact game scoring?
"""

import nflreadpy as nfl
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


def collect_weather_data(seasons=None):
    """
    Collects NFL weather data for the specified seasons.

    Parameters:
    -----------
    seasons : list, optional
        List of seasons to download (default: [2020, 2021, 2022, 2023, 2024])

    Returns:
    --------
    tuple
        (all_games_df, outdoor_games_df) - DataFrames with all games and outdoor-only games
    """
    if seasons is None:
        seasons = [2020, 2021, 2022, 2023, 2024]

    if not os.path.exists('data'):
        os.makedirs('data')

    schedules = nfl.load_schedules(seasons)
    df = schedules.to_pandas()

    cols = ['game_id', 'season', 'week', 'gameday', 'weekday',
            'home_team', 'away_team', 'home_score', 'away_score',
            'temp', 'wind', 'roof', 'surface', 'stadium']

    all_games = df[cols].copy()

    # Add gametime if available in original data
    if 'gametime' in df.columns:
        all_games['gametime'] = df['gametime']

    all_games['total_points'] = all_games['home_score'] + \
        all_games['away_score']
    all_games['point_differential'] = all_games['home_score'] - \
        all_games['away_score']
    all_games['home_win'] = (all_games['point_differential'] > 0).astype(int)

    all_games.to_csv('data/weather_data_all_games.csv', index=False)

    outdoor = all_games[all_games['temp'].notna()].copy()
    outdoor.to_csv('data/weather_data_outdoor_only.csv', index=False)

    return all_games, outdoor


def add_gametime_from_nfl_data(games_df, nfl_data):
    """
    Merge gametime from nfl_data into games_df by matching game_id.

    Parameters:
    -----------
    games_df : pd.DataFrame
        Games dataframe (all_games or outdoor_games) with game_id column
    nfl_data : pd.DataFrame
        Full NFL data with game_id and gametime columns

    Returns:
    --------
    pd.DataFrame
        games_df with gametime column added
    """
    if 'gametime' in games_df.columns:
        return games_df  # Already has gametime

    if nfl_data is None or 'gametime' not in nfl_data.columns or 'game_id' not in nfl_data.columns:
        return games_df  # Can't merge

    gametime_df = nfl_data[['game_id', 'gametime']].copy()
    result = games_df.merge(gametime_df, on='game_id', how='left')
    return result


# Configure polite defaults for Meteostat enrichment
_GEOCODER_USER_AGENT = "nfl-weather-enricher"
_GEOCODER_TIMEOUT = 10
# seconds between geocoding calls (Nominatim rate-limit friendly)
_GEOCODE_SLEEP = 1.0
_FETCH_WINDOW_HOURS = 1  # +/- hours around kickoff to average


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

    Parameters
    ----------
    all_games : pd.DataFrame
        DataFrame must contain at least game identifier index (kept as-is),
        a stadium name (stadium_col) and a gameday datetime (gameday_col).
        gameday may be naive local time — function will infer timezone from lat/lon.
    stadium_col : str
        Column name with stadium string to geocode (e.g. 'stadium' or 'stadium, city').
    gameday_col : str
        Column name with game date (string or datetime).
    gametime_col : Optional[str]
        Column name with game time (e.g. '13:00', '16:00'). If None, defaults to 13:00.
    city_col : Optional[str]
        If provided, use `"{stadium}, {city}"` when geocoding.
    max_rows : Optional[int]
        For testing: limit number of rows processed.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with new columns:
        met_temp_C, met_prcp_mm, met_windspeed_mps,
        met_lat, met_lon, met_source_time_utc
    """
    df = all_games.copy().reset_index(drop=True)
    if max_rows is not None:
        df = df.iloc[:max_rows].copy()

    geolocator = Nominatim(user_agent=_GEOCODER_USER_AGENT,
                           timeout=_GEOCODER_TIMEOUT)
    tf = TimezoneFinder()

    # caches to avoid repeated geocoding/fetches
    latlon_cache = {}
    weather_cache = {}  # key = (lat,lon, date_str) -> features

    # outputs
    out_rows = []

    for idx, row in df.iterrows():
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
            if (lat is None or lon is None) and city:
                lat, lon = _geocode_place(city, geolocator)
            latlon_cache[place] = (lat, lon)
            time.sleep(_GEOCODE_SLEEP)

        # default outputs if geocode failed
        default_out = {
            "met_lat": np.nan,
            "met_lon": np.nan,
            "met_temp_C": np.nan,
            "met_prcp_mm": np.nan,
            "met_windspeed_mps": np.nan,
            "met_source_time_utc": pd.NaT,
        }

        if lat is None or lon is None:
            out_rows.append(default_out)
            continue

        # 2) parse gameday + gametime -> target UTC
        gameday = pd.to_datetime(row[gameday_col])

        # Get gametime if available
        if gametime_col and gametime_col in row.index and pd.notna(row[gametime_col]):
            gametime_str = str(row[gametime_col])
            # Parse time (format: "13:00" or "13:00:00")
            try:
                if ':' in gametime_str:
                    time_parts = gametime_str.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                else:
                    # Try to parse as integer (hour only)
                    hour = int(gametime_str)
                    minute = 0
            except (ValueError, IndexError):
                hour, minute = 13, 0  # Default to 1 PM
        else:
            hour, minute = 13, 0  # Default to 1 PM if no gametime

        # Combine date and time
        kickoff_local = gameday.replace(
            hour=hour, minute=minute, second=0, microsecond=0)

        # If gameday is timezone-aware, convert to UTC
        if kickoff_local.tzinfo is not None and kickoff_local.tzinfo.utcoffset(kickoff_local) is not None:
            kickoff_utc = kickoff_local.astimezone(pytz.UTC)
        else:
            # infer timezone from lat/lon
            try:
                tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
            except Exception:
                tz_name = "UTC"
            try:
                tz = pytz.timezone(tz_name)
                # Convert to datetime if needed
                if isinstance(kickoff_local, pd.Timestamp):
                    kickoff_dt = kickoff_local.to_pydatetime()
                else:
                    kickoff_dt = kickoff_local
                kickoff_localized = tz.localize(kickoff_dt)
                kickoff_utc = kickoff_localized.astimezone(pytz.UTC)
            except Exception:
                # fallback - assume UTC
                if isinstance(kickoff_local, pd.Timestamp):
                    kickoff_utc = kickoff_local.tz_localize(pytz.UTC)
                else:
                    kickoff_utc = kickoff_local.replace(tzinfo=pytz.UTC)

        # 3) check cache for weather (use date key)
        cache_key = (round(lat, 4), round(lon, 4),
                     kickoff_utc.strftime("%Y-%m-%dT%H"))  # coarse key
        if cache_key in weather_cache:
            features = weather_cache[cache_key]
        else:
            features = _fetch_meteostat_for_point(lat, lon, kickoff_utc)
            weather_cache[cache_key] = features

        if features is None:
            out_rows.append(default_out)
            continue

        # attach coords and features
        features_out = {
            "met_lat": lat,
            "met_lon": lon,
            "met_temp_C": features.get("temp_mean_C", np.nan),
            "met_prcp_mm": features.get("prcp_mean_mm", np.nan),
            "met_windspeed_mps": features.get("wspd_mean_mps", np.nan),
            "met_source_time_utc": features.get("source_time_utc", pd.NaT),
        }
        out_rows.append(features_out)

    out_df = pd.DataFrame(out_rows)
    # join horizontally preserving original order
    result = pd.concat(
        [df.reset_index(drop=True), out_df.reset_index(drop=True)], axis=1)

    return result


# ---------- helper functions ----------

def _geocode_place(place: str, geolocator: Nominatim):
    """Return (lat, lon) or (None, None)."""
    if not place or place.strip() == "":
        return None, None
    try:
        loc = geolocator.geocode(place, addressdetails=False, timeout=10)
        if loc:
            return float(loc.latitude), float(loc.longitude)
    except Exception:
        return None, None
    return None, None


def _fetch_meteostat_for_point(lat: float, lon: float, kickoff_utc):
    """
    Use Meteostat Hourly to fetch a small window around kickoff_utc and produce
    single representative values (means).

    Returns dict or None.
    """
    try:
        # Ensure kickoff_utc is timezone-aware datetime in UTC
        # Convert to pandas Timestamp first for consistent handling
        if not isinstance(kickoff_utc, pd.Timestamp):
            if isinstance(kickoff_utc, datetime):
                # Convert datetime to Timestamp
                kickoff_utc = pd.Timestamp(kickoff_utc)
            else:
                kickoff_utc = pd.to_datetime(kickoff_utc)

        # Ensure timezone-aware and in UTC
        if kickoff_utc.tz is None:
            kickoff_utc = kickoff_utc.tz_localize(pytz.UTC)
        else:
            kickoff_utc = kickoff_utc.tz_convert(pytz.UTC)

        # Convert to timezone-aware datetime, then to naive UTC for Meteostat
        kickoff_utc_dt = pytz.UTC.localize(datetime(
            year=kickoff_utc.year,
            month=kickoff_utc.month,
            day=kickoff_utc.day,
            hour=kickoff_utc.hour,
            minute=kickoff_utc.minute,
            second=kickoff_utc.second,
            microsecond=kickoff_utc.microsecond
        ))

        # Calculate window and convert to naive UTC (Meteostat workaround)
        start_naive = (
            kickoff_utc_dt - timedelta(hours=_FETCH_WINDOW_HOURS)).replace(tzinfo=None)
        end_naive = (kickoff_utc_dt +
                     timedelta(hours=_FETCH_WINDOW_HOURS)).replace(tzinfo=None)

        pt = Point(lat, lon)
        data = Hourly(pt, start_naive, end_naive)
        data = data.fetch()

        if data is None or data.empty or len(data) == 0:
            return None

        # pick window average (mean) for requested fields
        out = {}

        # temp (°C)
        out["temp_mean_C"] = float(
            data["temp"].mean()) if "temp" in data.columns else np.nan
        # precipitation (mm) - provide mean
        if "prcp" in data.columns:
            out["prcp_mean_mm"] = float(data["prcp"].mean())
        else:
            out["prcp_mean_mm"] = np.nan
        # wind speed (mps)
        out["wspd_mean_mps"] = float(
            data["wspd"].mean()) if "wspd" in data.columns else np.nan
        # source time (use kickoff time)
        out["source_time_utc"] = pd.Timestamp(kickoff_utc_dt)

        return out

    except Exception:
        return None
