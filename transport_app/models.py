from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]


class RouteLeg(BaseModel):
    leg_id: str
    mode: str = "train"
    line: str
    route_id: str
    origin: str
    destination: str
    scheduled_minutes: int = Field(gt=0)
    planned_transfer_minutes_after: int = Field(default=0, ge=0)


class RouteDefinition(BaseModel):
    route_id: str
    name: str
    origin: str
    destination: str
    planned_departure: str
    legs: list[RouteLeg]


class RouteEvaluationRequest(BaseModel):
    sample_route_id: str | None = None
    route: RouteDefinition | None = None


class LegEvaluation(BaseModel):
    leg_id: str
    line: str
    route_id: str
    current_risk: RiskLevel
    expected_delay_minutes: int
    transfer_risk: RiskLevel
    reliability_score: float
    matched_alerts: int
    active_vehicles: int
    explanation: str


class RouteEvaluationResponse(BaseModel):
    route_id: str
    route_name: str
    generated_at: str
    current_risk: RiskLevel
    expected_delay_minutes: int
    predicted_delay_minutes: float | None = None
    delay_over_threshold_probability: float | None = None
    transfer_risk: RiskLevel
    route_reliability_score: float
    legs: list[LegEvaluation]
    explanation: str
    feature_summary: dict[str, float] | None = None


class FeedStatus(BaseModel):
    feed_type: str
    fetched_at: str | None = None
    snapshot_path: str | None = None
    entity_count: int = 0
    parsed_count: int = 0
    status: str = "missing"
    details: dict[str, Any] = Field(default_factory=dict)
