"""
NFL Data Collection Script for Weather, Stadium, and Scheduling Analysis
Run this script to download all the data you need for your project
"""

import nflreadpy as nfl
import pandas as pd
import os

os.makedirs('nfl_data', exist_ok=True)

seasons = [2020, 2021, 2022, 2023, 2024]

try:
    schedules = nfl.load_schedules(seasons)
    schedules.to_csv('nfl_data/schedules.csv', index=False)
except Exception as e:
    print(f"Error downloading schedules: {e}")

try:
    teams = nfl.load_teams()
    teams.to_csv('nfl_data/teams.csv', index=False)
except Exception as e:
    print(f"Error downloading teams: {e}")

download_pbp = input("Download play-by-play? (y/n): ").lower() == 'y'

if download_pbp:
    try:
        pbp = nfl.load_pbp(seasons)
        pbp.to_csv('nfl_data/play_by_play.csv', index=False)
    except Exception as e:
        print(f"Error downloading play-by-play: {e}")

try:
    analysis_data = schedules.merge(
        teams[['team_abbr', 'team_name', 'team_stadium',
               'team_roof', 'team_surface']],
        left_on='home_team',
        right_on='team_abbr',
        how='left'
    )

    analysis_data['point_differential'] = analysis_data['home_score'] - \
        analysis_data['away_score']
    analysis_data['home_win'] = (
        analysis_data['point_differential'] > 0).astype(int)

    analysis_data.to_csv('nfl_data/analysis_ready.csv', index=False)
except Exception as e:
    print(f"Error creating merged dataset: {e}")

print("Data download complete.")
