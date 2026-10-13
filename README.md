# NFL Performance & Weather Data Pipeline

Analyzed 25 seasons of NFL game data (2000-2024) to investigate 
how weather conditions impact team performance and tested the 
popular "cold teams struggle in heat" myth against real data.

## Key Findings
- Warm-weather teams show a 7.7pp win rate drop in extreme cold
- Cold-weather teams show no meaningful underperformance in heat
- Verdict: the myth is one-sided, not a full myth

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
