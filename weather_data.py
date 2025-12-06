"""
Weather Data Collection
Team: [Your names]
Research Question: How do weather conditions impact game scoring?
"""

import nflreadpy as nfl
import pandas as pd
import os

def collect_weather_data(seasons):
    """Gets NFL weather data for the specified seasons"""
    
    print("Collecting weather data...")
    print(f"Seasons: {seasons}\n")
    
    # make sure directory exists
    if not os.path.exists('nfl_data'):
        os.makedirs('nfl_data')
    
    # download schedules using nflreadpy
    print("Downloading schedules from NFLverse...")
    schedules = nfl.load_schedules(seasons)
    df = schedules.to_pandas()
    print(f"Got {len(df)} games total")
    
    # we only want outdoor games because indoor games don't have weather
    print("\nFiltering for outdoor games...")
    outdoor = df[df['temp'].notna()].copy()
    print(f"Found {len(outdoor)} outdoor games with weather data")
    
    # pick the columns we need for weather analysis
    cols = ['game_id', 'season', 'week', 'gameday', 'weekday',
            'home_team', 'away_team', 'home_score', 'away_score',
            'temp', 'wind', 'roof', 'surface', 'stadium']
    
    weather_df = outdoor[cols].copy()
    
    # add some useful calculated columns
    weather_df['total_points'] = weather_df['home_score'] + weather_df['away_score']
    weather_df['point_differential'] = weather_df['home_score'] - weather_df['away_score']
    weather_df['home_win'] = (weather_df['point_differential'] > 0).astype(int)
    
    # save it
    weather_df.to_csv('nfl_data/weather_data.csv', index=False)
    print("\nSaved to nfl_data/weather_data.csv")
    
    # print some basic stats
    print("\n--- Summary ---")
    print(f"Total games: {len(weather_df)}")
    print(f"Seasons covered: {weather_df['season'].min()} to {weather_df['season'].max()}")
    print(f"Temp range: {weather_df['temp'].min():.0f}F to {weather_df['temp'].max():.0f}F")
    print(f"Wind range: {weather_df['wind'].min():.0f} to {weather_df['wind'].max():.0f} mph")
    print(f"Average points per game: {weather_df['total_points'].mean():.1f}")
    print("\nDone!")
    
    return weather_df


# run it
if __name__ == "__main__":
    # get data for last 5 seasons
    seasons = [2020, 2021, 2022, 2023, 2024]
    data = collect_weather_data(seasons)
    print(f"\nCollected {len(data)} games for analysis")