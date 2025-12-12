"""
NFL Data Collection Script for Weather, Stadium, and Scheduling Analysis
"""

import nflreadpy as nfl
import pandas as pd
import os


def download_nfl_data(seasons=None):
    """
    Downloads NFL schedules and team data, merges them, and returns analysis-ready DataFrame.

    Parameters:
    -----------
    seasons : list, optional
        List of seasons to download (default: [2020, 2021, 2022, 2023, 2024])

    Returns:
    --------
    pd.DataFrame
        Merged dataset with schedules, team info, and calculated metrics
    """
    if seasons is None:
        seasons = [2020, 2021, 2022, 2023, 2024]

    os.makedirs('data', exist_ok=True)

    schedules = None
    teams = None

    try:
        schedules = nfl.load_schedules(seasons)
        schedules = schedules.to_pandas()
        schedules.to_csv('data/schedules.csv', index=False)
    except Exception as e:
        raise Exception(f"Error downloading schedules: {e}")

    try:
        teams = nfl.load_teams()
        teams = teams.to_pandas()
        teams.to_csv('data/teams.csv', index=False)
    except Exception as e:
        raise Exception(f"Error downloading teams: {e}")

    if schedules is None:
        raise Exception("Failed to download schedules data")

    try:
        analysis_data = schedules.copy()

        if teams is not None:
            team_cols = ['team_abbr', 'team_name']
            available_cols = [col for col in team_cols if col in teams.columns]
            if available_cols:
                analysis_data = analysis_data.merge(
                    teams[available_cols],
                    left_on='home_team',
                    right_on='team_abbr',
                    how='left'
                )

        analysis_data['point_differential'] = analysis_data['home_score'] - \
            analysis_data['away_score']
        analysis_data['home_win'] = (
            analysis_data['point_differential'] > 0).astype(int)

        analysis_data.to_csv('data/analysis_ready.csv', index=False)

        return analysis_data
    except Exception as e:
        raise Exception(f"Error creating merged dataset: {e}")
