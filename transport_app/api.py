from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from transport_app.feed_processing import (
    historical_feed_status,
    parse_alerts,
    parse_vehicle_positions,
    static_feed_status,
    vehicle_feed_age_seconds,
)
from transport_app.metrics import rolling_summary, route_timeseries
from transport_app.modeling import train_delay_model
from transport_app.models import FeedStatus, RouteEvaluationRequest, RouteEvaluationResponse
from transport_app.sample_routes import get_sample_route, get_sample_routes
from transport_app.scoring import evaluate_route
from transport_app.storage import init_db, latest_feed_statuses, record_route_evaluation, route_history


app = FastAPI(title="NSW Route Reliability API", version="0.1.0")
init_db()

# CORS for frontend (Vercel/Render). Use FRONTEND_ORIGIN env or allow all.
origins = [os.getenv("FRONTEND_ORIGIN", "*")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompareRoutesRequest(BaseModel):
    sample_route_ids: list[str] | None = None
    routes: list[RouteEvaluationRequest] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sample-routes")
def sample_routes() -> list[dict]:
    return [route.model_dump() for route in get_sample_routes()]


@app.get("/latest-feed-status")
def latest_feed_status() -> dict[str, object]:
    statuses = latest_feed_statuses()
    vehicle_summary = parse_vehicle_positions()
    decoded = {
        "alerts_in_memory": parse_alerts().entity_count,
        "vehicle_positions_in_memory": vehicle_summary.entity_count,
        "vehicle_feed_age_seconds": vehicle_feed_age_seconds(vehicle_summary),
        "static": static_feed_status(),
        "historical": historical_feed_status(),
    }
    return {"snapshots": statuses, "decoded": decoded}


@app.post("/evaluate-route", response_model=RouteEvaluationResponse)
def evaluate_route_endpoint(request: RouteEvaluationRequest) -> RouteEvaluationResponse:
    if request.sample_route_id:
        try:
            route = get_sample_route(request.sample_route_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    elif request.route:
        route = request.route
    else:
        raise HTTPException(status_code=400, detail="Provide sample_route_id or route.")

    response = evaluate_route(route)
    record_route_evaluation(
        route_id=response.route_id,
        route_name=response.route_name,
        request_payload=request.model_dump(),
        response_payload=response.model_dump(),
    )
    return response


@app.post("/compare-routes")
def compare_routes(payload: CompareRoutesRequest) -> list[dict]:
    route_inputs: list[RouteEvaluationRequest] = []
    if payload.sample_route_ids:
        for route_id in payload.sample_route_ids:
            route_inputs.append(RouteEvaluationRequest(sample_route_id=route_id))
    if payload.routes:
        route_inputs.extend(payload.routes)
    if not route_inputs:
        raise HTTPException(status_code=400, detail="Provide sample_route_ids or routes.")

    results: list[dict] = []
    for request in route_inputs:
        try:
            result = evaluate_route_endpoint(request)
        except HTTPException as exc:
            if exc.status_code == 404:
                continue
            raise
        results.append(result.model_dump())

    results.sort(key=lambda r: r.get("route_reliability_score", 0), reverse=True)
    return results


@app.get("/route-history/{route_id}")
def route_history_endpoint(route_id: str, limit: int = 100) -> dict[str, object]:
    history = route_history(route_id, limit=limit)
    summary = rolling_summary(route_id, limit=limit)
    timeseries = route_timeseries(route_id, limit=limit)
    return {"route_id": route_id, "history": history, "summary": summary, "timeseries": timeseries}


@app.post("/train-model")
def train_model_endpoint() -> dict[str, object]:
    metrics = train_delay_model()
    if metrics is None:
        raise HTTPException(status_code=400, detail="Not enough data or sklearn/xgboost not installed.")
    return {"status": "ok", "metrics": metrics}
