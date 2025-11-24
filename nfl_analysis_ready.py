"""
Create clean analysis-ready datasets for NFL visualization project
"""
import pandas as pd

print("Loading NFL data...")
schedules = pd.read_csv('nfl_data/schedules.csv')
teams = pd.read_csv('nfl_data/teams.csv')

print("\n" + "=" * 60)
print("CREATING ANALYSIS DATASETS")
print("=" * 60)

# ============================================================================
# DATASET 1: Full game data with all information
# ============================================================================
print("\n1. Creating complete game dataset...")

# Add calculated columns
schedules['point_differential'] = schedules['home_score'] - schedules['away_score']
schedules['home_win'] = (schedules['point_differential'] > 0).astype(int)
schedules['total_points'] = schedules['home_score'] + schedules['away_score']

# Add team names for easier reading
schedules = schedules.merge(
    teams[['team_abbr', 'team_name']], 
    left_on='home_team', 
    right_on='team_abbr',
    how='left',
    suffixes=('', '_home')
).rename(columns={'team_name': 'home_team_name'})

schedules = schedules.merge(
    teams[['team_abbr', 'team_name']], 
    left_on='away_team', 
    right_on='team_abbr',
    how='left',
    suffixes=('', '_away')
).rename(columns={'team_name': 'away_team_name'})

# Save complete dataset
schedules.to_csv('nfl_data/complete_games.csv', index=False)
print(f"   ✓ Complete dataset saved: {len(schedules)} games")

# ============================================================================
# DATASET 2: Weather analysis dataset
# ============================================================================
print("\n2. Creating weather analysis dataset...")

weather_data = schedules[[
    'game_id', 'season', 'week', 'gameday', 'weekday',
    'home_team', 'home_team_name', 'away_team', 'away_team_name',
    'home_score', 'away_score', 'total_points', 'point_differential',
    'temp', 'wind', 'roof', 'surface', 'stadium'
]].copy()

# Filter to games with weather data (outdoor games)
weather_data_outdoor = weather_data[weather_data['temp'].notna()].copy()

weather_data.to_csv('nfl_data/weather_analysis.csv', index=False)
weather_data_outdoor.to_csv('nfl_data/weather_analysis_outdoor_only.csv', index=False)

print(f"   ✓ Weather dataset (all games): {len(weather_data)} games")
print(f"   ✓ Weather dataset (outdoor only): {len(weather_data_outdoor)} games")

# ============================================================================
# DATASET 3: Stadium/Home field advantage dataset
# ============================================================================
print("\n3. Creating stadium analysis dataset...")

stadium_data = schedules[[
    'game_id', 'season', 'week', 'gameday',
    'home_team', 'home_team_name', 'away_team', 'away_team_name',
    'home_score', 'away_score', 'home_win', 'point_differential',
    'roof', 'surface', 'stadium', 'stadium_id',
    'home_rest', 'away_rest'
]].copy()

stadium_data.to_csv('nfl_data/stadium_analysis.csv', index=False)
print(f"   ✓ Stadium dataset saved: {len(stadium_data)} games")

# ============================================================================
# DATASET 4: Scheduling analysis dataset
# ============================================================================
print("\n4. Creating scheduling analysis dataset...")

scheduling_data = schedules[[
    'game_id', 'season', 'week', 'gameday', 'weekday',
    'home_team', 'home_team_name', 'away_team', 'away_team_name',
    'home_score', 'away_score', 'home_win', 'point_differential',
    'home_rest', 'away_rest', 'div_game'
]].copy()

scheduling_data.to_csv('nfl_data/scheduling_analysis.csv', index=False)
print(f"   ✓ Scheduling dataset saved: {len(scheduling_data)} games")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "=" * 60)
print("DATA SUMMARY")
print("=" * 60)

print(f"\n📊 OVERALL STATISTICS:")
print(f"   Total games: {len(schedules)}")
print(f"   Seasons: {schedules['season'].min()} - {schedules['season'].max()}")
print(f"   Unique stadiums: {schedules['stadium'].nunique()}")
print(f"   Games with weather data: {schedules['temp'].notna().sum()}")

print(f"\n🌡️  WEATHER STATISTICS:")
print(f"   Average temperature: {schedules['temp'].mean():.1f}°F")
print(f"   Temperature range: {schedules['temp'].min():.1f}°F to {schedules['temp'].max():.1f}°F")
print(f"   Average wind speed: {schedules['wind'].mean():.1f} mph")
print(f"   Max wind speed: {schedules['wind'].max():.1f} mph")

print(f"\n🏟️  ROOF TYPE DISTRIBUTION:")
roof_counts = schedules['roof'].value_counts()
for roof_type, count in roof_counts.items():
    pct = count/len(schedules)*100
    print(f"   {roof_type:15s}: {count:4d} games ({pct:5.1f}%)")

print(f"\n🌱 SURFACE TYPE DISTRIBUTION:")
surface_counts = schedules['surface'].value_counts()
for surface_type, count in surface_counts.items():
    pct = count/len(schedules)*100
    print(f"   {surface_type:15s}: {count:4d} games ({pct:5.1f}%)")

print(f"\n🏠 HOME FIELD ADVANTAGE:")
completed_games = schedules[schedules['home_score'].notna()]
home_wins = completed_games['home_win'].sum()
total_games = len(completed_games)
home_win_pct = home_wins/total_games*100
print(f"   Home team wins: {home_wins}/{total_games} ({home_win_pct:.1f}%)")
print(f"   Average point differential: {completed_games['point_differential'].mean():.2f} points")

print(f"\n📅 SCHEDULING STATISTICS:")
print(f"   Average rest days (home): {schedules['home_rest'].mean():.1f} days")
print(f"   Average rest days (away): {schedules['away_rest'].mean():.1f} days")

weekday_counts = schedules['weekday'].value_counts()
print(f"\n📆 GAMES BY DAY OF WEEK:")
for day, count in weekday_counts.items():
    pct = count/len(schedules)*100
    print(f"   {day:10s}: {count:4d} games ({pct:5.1f}%)")

print("\n" + "=" * 60)
print("✅ ALL DATASETS CREATED!")
print("=" * 60)
print("\nFiles created in nfl_data/ folder:")
print("  • complete_games.csv - All game data with calculated fields")
print("  • weather_analysis.csv - Weather-focused dataset")
print("  • weather_analysis_outdoor_only.csv - Only outdoor games with weather")
print("  • stadium_analysis.csv - Stadium and home field advantage data")
print("  • scheduling_analysis.csv - Scheduling impact data")

print("\n🚀 READY FOR VISUALIZATION!")
print("\nKey insights you can explore:")
print("  1. Weather Impact: Use weather_analysis_outdoor_only.csv")
print("  2. Home Field Advantage: Use stadium_analysis.csv")
print("  3. Scheduling Effects: Use scheduling_analysis.csv")