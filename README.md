# NFL Performance & Weather Data Pipeline

Analyzed 25 seasons of NFL game data (2000-2024) to investigate 
how weather conditions impact team performance and tested the 
popular "cold teams struggle in heat" myth against real data.

## Key Findings
- Warm-weather teams show a 7.7pp win rate drop in cold road games (below 40°F)
- Cold-weather teams show no meaningful underperformance in heat
- Verdict: the myth is one-sided, not a full myth

| Scenario | Games | Win rate | Baseline (all away games) | Change |
|---|---|---|---|---|
| Warm-weather teams away in cold (< 40°F) | 144 | 32.6% | 40.3% | **-7.7 pp** |
| Cold-weather teams away in heat (> 75°F) | 288 | 46.5% | 43.2% | +3.4 pp |

**Definitions:** Warm-weather teams are MIA, TB, ARI, JAX, HOU, CAR, NO and ATL. Cold-weather teams are BUF, GB, CHI, NE, PIT, CLE, MIN, DET, NYG, NYJ and DEN. Win rate is the away team's win percentage. These are associations, not causal effects: team strength, travel and opponent quality are not controlled for.

Separately, the weather-impact section classifies games as extreme cold, windy, or rainy using percentile thresholds on Meteostat data across 3,833 outdoor games. Cold is the 10th percentile (below 1.1°C, about 34°F); wind and precipitation use the 90th percentile.

## Tools & Data Sources
- Python, Pandas, Matplotlib, Bokeh, Panel
- nflreadpy (game statistics)
- Meteostat API (weather data)

## Project Structure
- `main.ipynb` — full analysis and visualizations
- `scripts/download_nfl_data.py` — data ingestion pipeline
- `scripts/weather_data.py` — weather enrichment via Meteostat

## Setup
```bash
uv venv
uv sync
```
Select `.venv` as your kernel in `main.ipynb` and run all cells.
To regenerate the data in `data/`, run `scripts/download_nfl_data.py`, then `scripts/weather_data.py`.
