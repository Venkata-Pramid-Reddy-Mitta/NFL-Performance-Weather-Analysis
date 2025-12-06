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
    
    # pick the columns we need for weather analysis
    cols = ['game_id', 'season', 'week', 'gameday', 'weekday',
            'home_team', 'away_team', 'home_score', 'away_score',
            'temp', 'wind', 'roof', 'surface', 'stadium']
    
    all_games = df[cols].copy()
    
    # add calculated columns to all games
    all_games['total_points'] = all_games['home_score'] + all_games['away_score']
    all_games['point_differential'] = all_games['home_score'] - all_games['away_score']
    all_games['home_win'] = (all_games['point_differential'] > 0).astype(int)
    
    # save all games (including domes)
    all_games.to_csv('weather_data_all_games.csv', index=False)
    print(f"\nSaved all {len(all_games)} games to weather_data_all_games.csv")
    
    # now filter for outdoor games only (games with actual weather)
    print("\nFiltering for outdoor games with weather data...")
    outdoor = all_games[all_games['temp'].notna()].copy()
    print(f"Found {len(outdoor)} outdoor games")
    
    # save outdoor only
    outdoor.to_csv('weather_data_outdoor_only.csv', index=False)
    print(f"Saved to weather_data_outdoor_only.csv")
    
    # print some basic stats for outdoor games
    print("\n--- Outdoor Games Summary ---")
    print(f"Total outdoor games: {len(outdoor)}")
    print(f"Seasons covered: {outdoor['season'].min()} to {outdoor['season'].max()}")
    print(f"Temp range: {outdoor['temp'].min():.0f}F to {outdoor['temp'].max():.0f}F")
    print(f"Wind range: {outdoor['wind'].min():.0f} to {outdoor['wind'].max():.0f} mph")
    print(f"Average points per game: {outdoor['total_points'].mean():.1f}")
    
    # show roof type breakdown
    print("\n--- Roof Type Breakdown (All Games) ---")
    for roof, count in all_games['roof'].value_counts().items():
        print(f"{roof}: {count} games")
    
    print("\nDone!")
    
    return all_games, outdoor


# run it
if __name__ == "__main__":
    # get data for last 5 seasons
    seasons = [2020, 2021, 2022, 2023, 2024]
    all_data, outdoor_data = collect_weather_data(seasons)
    print(f"\nCollected {len(all_data)} total games ({len(outdoor_data)} outdoor)")