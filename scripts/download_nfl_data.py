import nflreadpy as nfl
import pandas as pd
import os

def download_nfl_data(seasons=None):
    """
    Downloads NFL schedules and team data, merges them, and returns analysis-ready DataFrame.
    """
    if seasons is None:
        seasons = list(range(2000, 2025))

    os.makedirs('data', exist_ok=True)

    print(f"Downloading schedules for {len(seasons)} seasons...")
    schedules = nfl.load_schedules(seasons)
    
    print("Downloading team info...")
    teams = nfl.load_teams()

    # --- CRITICAL FIX: Convert Polars/Arrow objects to Pandas ---
    if hasattr(schedules, 'to_pandas'):
        schedules = schedules.to_pandas()
        
    if hasattr(teams, 'to_pandas'):
        teams = teams.to_pandas()
    # ------------------------------------------------------------

    try:
        # Now this works because we guaranteed it is a pandas DataFrame
        analysis_data = schedules.copy()

        # Merge team names
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

        # Metrics
        analysis_data['total_points'] = analysis_data['home_score'] + analysis_data['away_score']
        analysis_data['point_differential'] = analysis_data['home_score'] - analysis_data['away_score']
        analysis_data['home_win'] = (analysis_data['point_differential'] > 0).astype(int)

        # Save
        analysis_data.to_csv('data/analysis_ready.csv', index=False)
        print("Successfully saved data/analysis_ready.csv")

        return analysis_data
        
    except Exception as e:
        raise Exception(f"Error creating merged dataset: {e}")