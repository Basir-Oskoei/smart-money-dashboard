Smart Money Dashboard

A full institutional-style market structure and liquidity analysis engine built using FastAPI, Python, and a JavaScript frontend.
The dashboard processes OHLCV price data and automatically detects:

Market structure (BOS, CHoCH)

Swing highs and lows

Liquidity levels (EQH, EQL)

Fair Value Gaps (FVG)

Displacement candles

Premium and discount zones

Trend bias scoring

The frontend visualizes all smart money concepts on a chart using TradingView’s Lightweight Charts library.

This project supports Forex, Indices, Gold, Crypto, Commodities and any OHLCV CSV input.

Requirements

Python 3.10 or higher

Node not required

FastAPI + Uvicorn

Pandas, NumPy, Requests

Install them automatically using the provided requirements.txt.

Installation and Setup

Follow these steps carefully.

1. Navigate into the project root folder

Open PowerShell:

cd C:\Users\basir\OneDrive\Desktop\programs\smart_money_dashboard


This folder contains the smart_money_dashboard directory, your virtual environment folder, and requirements.

2. Create and activate the virtual environment
python -m venv venv


Activate:

venv\Scripts\Activate.ps1


You should see:

(venv) PS C:\Users\basir\OneDrive\Desktop\programs\smart_money_dashboard>

3. Install dependencies
pip install -r requirements.txt

Running the Backend Application

This step must be done from inside the project folder that contains backend and frontend.

From the root:

cd smart_money_dashboard


Inside this folder, you should see:

backend/
frontend/
data/


Now run:

uvicorn backend.main:app --reload


If it launches correctly, you will see:

Uvicorn running on http://127.0.0.1:8000


Open the frontend by visiting:

http://127.0.0.1:8000


The dashboard will load in your browser.

Running the XAUUSD Data Downloader

The downloader fetches gold data from TwelveData and saves it as a CSV file compatible with the dashboard.

From the root folder:

cd C:\Users\basir\OneDrive\Desktop\programs\smart_money_dashboard


Activate the virtual environment:

venv\Scripts\Activate.ps1


Run the script:

python download_xauusd.py


This script will:

Request OHLCV data for XAUUSD from the TwelveData API

Save the CSV file into the current folder

Produce a file you can upload directly to the dashboard

Make sure to edit your API key inside download_xauusd.py.

How the System Works

The backend uses institutional concepts to break down market behavior.

Market Structure

The system identifies:

Swing highs and lows

Break of Structure (BOS)

Change of Character (CHoCH)

These are derived using windowed pivot logic and buffer thresholds.

Liquidity Mapping

The engine detects equal highs and equal lows that likely represent liquidity pools.

Fair Value Gaps (FVG)

It scans every 3-candle sequence to detect imbalances and creates a list of bullish and bearish gaps.

Displacement Detection

Large-bodied candles relative to wick size are classified as displacement candles, contributing to bias.

Premium/Discount Model

Based on recent swing low and swing high:

Price below mid = discount zone

Price above mid = premium zone

Bias Engine

Combines:

Trend direction

Zone location

FVG confluence

Liquidity context

Displacement strength

Outputs a final bias:

strong_bullish

bullish

neutral

bearish

strong_bearish

Frontend Visualization

The frontend plots:

Candles

BOS/CHoCH markers

Swing points

Liquidity zones

FVGs

Displacement overlays

The dashboard updates when a new CSV is uploaded or sample data is selected.

Summary

This project provides a complete institutional trading analysis engine with a professional browser dashboard.
It is modular, expandable, and can be adapted into an automated strategy, trade journaling system, or AI-powered assistant.
