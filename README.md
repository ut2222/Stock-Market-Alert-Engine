# Stock Market Dashboard & Alert Engine

A real-time stock market monitoring system built end-to-end in six phases — live data ingestion, a custom data-structures core for efficient streaming analytics, a rule-based alert engine, a REST + WebSocket API, and a live React dashboard.

## What this is

Most "stock dashboard" projects either poll an API on a timer and re-render, or lean entirely on a charting library to do the heavy lifting. This one is built around a **custom analytics core** designed for streaming data — maintaining rolling statistics and technical indicators efficiently as new prices arrive, rather than recomputing from scratch on every update.

## Architecture

```
Alpha Vantage API
      ↓
[1] Ingestion Layer        — fetches & normalizes live/historical price data
      ↓
[2] Stream Processor       — DSA core: monotonic deque (sliding-window extrema),
                              segment tree (range queries over price history)
      ↓
[3] Alert Engine           — evaluates user-defined rules against live indicators,
                              dispatches triggered alerts
      ↓
[4] FastAPI REST Server    — exposes tickers, alert rules, and historical data
      ↓
[5] WebSocket Fan-out      — pushes live price/indicator updates to all connected clients
      ↓
[6] React + Vite Dashboard — live charts (Recharts), alert configuration UI
```

## Key components

- **Ingestion (`ingestion/`)** — fetches data from the Alpha Vantage API and normalizes it into a consistent internal schema, with a local cache (`historical_cache.json`) to avoid redundant calls against a rate-limited free API tier.
- **Stream processor (`stream_processor/`)** — the core of the project:
  - A **monotonic deque** for O(1) amortized sliding-window min/max tracking (used for fast-moving technical indicators).
  - A **segment tree** for efficient range queries (e.g. min/max/sum over arbitrary historical windows) without recomputing over the full price history each time.
- **Alert engine (`alert_engine/`)** — evaluates configurable rules (e.g. price crossing a threshold, indicator conditions) against live data and dispatches notifications when triggered.
- **API (`api/`)** — FastAPI REST endpoints for tickers and alert rules, plus a WebSocket route for real-time streaming to the frontend.
- **Dashboard (`dashboard/`)** — React + Vite frontend, live-updating charts via WebSocket, built with Recharts and Axios.

## Tech stack

**Backend:** Python, FastAPI, Uvicorn, WebSockets
**Frontend:** React, Vite, Recharts, Axios
**Data source:** Alpha Vantage API

## Running locally

**Backend:**
```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```
Create a `.env` file in the project root with your own Alpha Vantage API key:
```
ALPHA_VANTAGE_API_KEY=your_key_here
```
Then start the server:
```bash
python main.py
```

**Frontend:**
```bash
cd dashboard
npm install
npm run dev
```

## Notes

This project doesn't include a `requirements.txt` in this listing — if you're setting it up fresh, generate one from your local environment with `pip freeze > requirements.txt` before others try to run it.

## License

MIT
