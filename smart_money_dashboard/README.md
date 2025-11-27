Smart Money Dashboard

Overview
This project is a local research dashboard for institutional style trading analysis.
Backend is FastAPI and Python.
Frontend is HTML, CSS, and JavaScript.
The system reads OHLCV data, computes smart money logic, and returns a JSON model used for visual overlays.

Quick start

1. Open folder in VS Code
2. Create a virtual environment and activate it
3. Install dependencies with
   pip install -r requirements.txt
4. Run the API from VS Code using the provided launch configuration
   or from terminal with
   uvicorn backend.main:app --reload
5. Open browser at
   http://127.0.0.1:8000

Usage

Sample data
A small sample CSV is in data/XAUUSD_15m_sample.csv.
On the dashboard click Use Sample Data to see the engine running.

Own data
Export OHLCV to a CSV with columns
timestamp, open, high, low, close, volume
Then upload it from the UI.

What the backend computes

Swing highs and lows over a sliding window
Break of structure and change of character
Liquidity equal highs and equal lows
Fair value gaps and their bounds
Premium and discount zone based on recent swing range
Displacement candles and basic momentum
A combined directional bias

Endpoint summary

GET  /api/health
POST /api/analyze/file   multipart CSV upload
GET  /api/analyze/sample sample XAUUSD file analysis

Notes

All logic is inside backend/sm_analysis.py so you can extend rules and weights.
Frontend is intentionally minimal for clarity and can be restyled or expanded.
