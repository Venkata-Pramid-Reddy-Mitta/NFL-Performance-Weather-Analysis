"""
Quick script to check what columns are actually in the downloaded data
"""
import pandas as pd

# Load the data
schedules = pd.read_csv('nfl_data/schedules.csv')
teams = pd.read_csv('nfl_data/teams.csv')

print("=" * 60)
print("SCHEDULES COLUMNS")
print("=" * 60)
print("\nAll columns in schedules.csv:")
for i, col in enumerate(schedules.columns, 1):
    print(f"{i:2}. {col}")

print("\n" + "=" * 60)
print("TEAMS COLUMNS")
print("=" * 60)
print("\nAll columns in teams.csv:")
for i, col in enumerate(teams.columns, 1):
    print(f"{i:2}. {col}")

print("\n" + "=" * 60)
print("SAMPLE DATA")
print("=" * 60)
print("\nFirst row of schedules:")
print(schedules.iloc[0])

print("\n\nFirst row of teams:")
print(teams.iloc[0])