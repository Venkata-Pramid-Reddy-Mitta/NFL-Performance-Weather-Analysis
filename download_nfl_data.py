"""
NFL Data Collection Script for Weather, Stadium, and Scheduling Analysis
Run this script to download all the data you need for your project
"""

# Step 1: Install the required package (run this in your terminal first)
# pip install nflreadpy

import nflreadpy as nfl
import pandas as pd
import os

# Create data directory if it doesn't exist
os.makedirs('nfl_data', exist_ok=True)

print("Starting NFL data download...")
print("=" * 60)

# Define which seasons you want to analyze (adjust as needed)
seasons = [2020, 2021, 2022, 2023, 2024]

# ============================================================================
# DATASET 1: SCHEDULES (Contains weather, scores, venue info)
# ============================================================================
print("\n1. Downloading NFL schedules (includes weather data)...")
try:
    schedules = nfl.load_schedules(seasons)
    schedules.to_csv('nfl_data/schedules.csv', index=False)
    print(f"   ✓ Schedules downloaded: {len(schedules)} games")
    print(f"   Columns include: {', '.join(schedules.columns[:10].tolist())}...")
except Exception as e:
    print(f"   ✗ Error downloading schedules: {e}")

# ============================================================================
# DATASET 2: TEAMS (Contains stadium characteristics)
# ============================================================================
print("\n2. Downloading team information (stadium details)...")
try:
    teams = nfl.load_teams()
    teams.to_csv('nfl_data/teams.csv', index=False)
    print(f"   ✓ Teams downloaded: {len(teams)} teams")
    print(f"   Columns include: {', '.join(teams.columns.tolist())}")
except Exception as e:
    print(f"   ✗ Error downloading teams: {e}")

# ============================================================================
# DATASET 3: PLAY-BY-PLAY (Optional - for detailed game analysis)
# ============================================================================
print("\n3. Downloading play-by-play data (this may take a few minutes)...")
print("   Note: This is a large dataset. You may skip this if you only need game-level stats.")
download_pbp = input("   Download play-by-play? (y/n): ").lower() == 'y'

if download_pbp:
    try:
        pbp = nfl.load_pbp(seasons)
        pbp.to_csv('nfl_data/play_by_play.csv', index=False)
        print(f"   ✓ Play-by-play downloaded: {len(pbp)} plays")
    except Exception as e:
        print(f"   ✗ Error downloading play-by-play: {e}")
else:
    print("   ⊘ Skipped play-by-play download")

# ============================================================================
# PREVIEW THE DATA
# ============================================================================
print("\n" + "=" * 60)
print("DATA PREVIEW")
print("=" * 60)

# Preview schedules
print("\n📊 SCHEDULES DATA (first 3 rows):")
print(schedules.head(3))
print(f"\nTotal columns: {len(schedules.columns)}")
print(f"Key columns for your analysis:")
print("  - Weather: temp, wind, weather")
print("  - Scores: home_score, away_score")
print("  - Teams: home_team, away_team")
print("  - Venue: stadium, roof")
print("  - Schedule: gameday, weekday")

# Preview teams
print("\n🏟️  TEAMS DATA (first 3 rows):")
print(teams.head(3))
print(f"\nTotal teams: {len(teams)}")
print(f"Key columns for stadium analysis:")
print("  - team_abbr, team_name")
print("  - team_stadium")
print("  - team_roof (dome/outdoor/retractable)")
print("  - team_surface (grass/turf)")

# ============================================================================
# CREATE MERGED DATASET FOR EASY ANALYSIS
# ============================================================================
print("\n" + "=" * 60)
print("CREATING ANALYSIS-READY DATASETS")
print("=" * 60)

# Merge schedules with team stadium info
print("\n4. Creating merged dataset with stadium characteristics...")
try:
    # Merge for home team stadium info
    analysis_data = schedules.merge(
        teams[['team_abbr', 'team_name', 'team_stadium', 'team_roof', 'team_surface']],
        left_on='home_team',
        right_on='team_abbr',
        how='left'
    )
    
    # Calculate point differential
    analysis_data['point_differential'] = analysis_data['home_score'] - analysis_data['away_score']
    analysis_data['home_win'] = (analysis_data['point_differential'] > 0).astype(int)
    
    # Save the merged dataset
    analysis_data.to_csv('nfl_data/analysis_ready.csv', index=False)
    print(f"   ✓ Analysis dataset created: {len(analysis_data)} games")
except Exception as e:
    print(f"   ✗ Error creating merged dataset: {e}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 60)
print("QUICK STATISTICS")
print("=" * 60)

print(f"\n📈 Seasons covered: {schedules['season'].min()} - {schedules['season'].max()}")
print(f"📈 Total games: {len(schedules)}")
print(f"📈 Games with weather data: {schedules['temp'].notna().sum()}")
print(f"📈 Unique stadiums: {schedules['stadium'].nunique()}")

# Weather statistics
print(f"\n🌡️  WEATHER STATS:")
print(f"   Average temperature: {schedules['temp'].mean():.1f}°F")
print(f"   Average wind speed: {schedules['wind'].mean():.1f} mph")
print(f"   Games with precipitation: {schedules['weather'].str.contains('rain|snow', case=False, na=False).sum()}")

# Roof type distribution
print(f"\n🏟️  ROOF TYPE DISTRIBUTION:")
roof_counts = schedules['roof'].value_counts()
for roof_type, count in roof_counts.items():
    print(f"   {roof_type}: {count} games ({count/len(schedules)*100:.1f}%)")

# Home field advantage
print(f"\n🏠 HOME FIELD ADVANTAGE:")
home_wins = analysis_data['home_win'].sum()
total_games = len(analysis_data[analysis_data['home_score'].notna()])
print(f"   Home team wins: {home_wins}/{total_games} ({home_wins/total_games*100:.1f}%)")

print("\n" + "=" * 60)
print("✅ DATA COLLECTION COMPLETE!")
print("=" * 60)
print("\nYour data is saved in the 'nfl_data' folder:")
print("  • schedules.csv - Game schedules with weather")
print("  • teams.csv - Team and stadium information")
print("  • analysis_ready.csv - Merged dataset for analysis")
if download_pbp:
    print("  • play_by_play.csv - Play-by-play data")

print("\n🚀 NEXT STEPS:")
print("1. Explore the data in Excel or Jupyter notebook")
print("2. Start with 'analysis_ready.csv' for your visualizations")
print("3. Use the column names above to filter and analyze specific questions")
print("\n📖 For data dictionary and column descriptions, visit:")
print("   https://nflreadr.nflverse.com/articles/dictionary_schedules.html")