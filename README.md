## NSW Route Reliability Lab

Predict route reliability and expected delays using GTFS static + realtime feeds, with an ML-assisted delay predictor and React dashboard.

### Setup
1) Activate venv  
   `.venv\Scripts\Activate.ps1`
2) Install deps (add GTFS bindings)  
   `pip install -r requirements.txt gtfs-realtime-bindings`

### Run data fetch (optional but recommended)
Fetch fresh feeds before testing:  
`python -m transport_app.poller --with-static --with-historical --interval-seconds 60`  
Let it run a minute, then Ctrl+C.

### Start backend API
`uvicorn transport_app.api:app --reload --port 8000`

Key endpoints:
- `GET /health`
- `GET /sample-routes`
- `POST /evaluate-route` (body: `{ "sample_route_id": "sample_central_to_hornsby" }` or provide a route)
- `GET /route-history/{route_id}` (trend + summaries)
- `POST /compare-routes` (body: `{ "sample_route_ids": ["id1","id2"] }`)
- `POST /train-model` (trains delay regressor from stored evaluations)
- `GET /latest-feed-status` (alerts/vehicles counts, feed age, static/historical availability)

### Train the delay model
Generate a handful of evaluations first (curl or UI), then:  
`curl -X POST http://localhost:8000/train-model`
Artifacts land in `app_data/models/` with metrics JSON.

### Frontend (React + Vite)
```
cd frontend
npm install
npm run dev   # http://localhost:5173 (proxy to API)
```
Dashboard features:
- Reliability over time chart
- Delay over time chart
- Per-leg breakdown (risk, delay, alerts, vehicles, transfer risk)
- Feed health panel (counts + feed age + static/historical status)
- Quick route comparison

### Data ingest scripts
- `Data ingestion/collect_data.py` — one-off pipeline
- `transport_app/collector.py` — records snapshots + counts to SQLite
- `transport_app/poller.py` — scheduled realtime polling loop

### Notes
- Data/DB/model artifacts should stay untracked (`data/`, `app_data/`).
- Sources: TfNSW GTFS static, realtime alerts, realtime vehicle positions, historical GTFS (see opendata.transport.nsw.gov.au).***

## Deploy

### Frontend (Vercel)
- Uses `vercel.json` to build `frontend/` with `@vercel/static-build` and serve `frontend/dist`.
- Set `VITE_API_BASE` (in Vercel env) to the Render API URL.
- Deploy by connecting this repo to Vercel and selecting the root; build command auto-detected from `vercel.json`.

### Backend (Render or any Procfile host)
- `render.yaml` defines a Python web service; start command via `uvicorn transport_app.api:app --host 0.0.0.0 --port $PORT`.
- `Procfile` provided for Procfile-based hosts; works on Render/Heroku-like platforms.
- Set `FRONTEND_ORIGIN` env var for CORS (or "*" to allow all).
- Optional: `POLL_INTERVAL_SECONDS` to adjust realtime polling defaults.
