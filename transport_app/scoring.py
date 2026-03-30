from __future__ import annotations

from datetime import datetime, timezone

from transport_app.feed_processing import parse_alerts, parse_vehicle_positions, vehicle_feed_age_seconds
from transport_app.features import extract_features
from transport_app.modeling import predict_delay
from transport_app.models import LegEvaluation, RouteDefinition, RouteEvaluationResponse
from transport_app.storage import route_history


def risk_level(value: float) -> str:
    if value >= 70:
        return "high"
    if value >= 35:
        return "medium"
    return "low"


def evaluate_route(route: RouteDefinition) -> RouteEvaluationResponse:
    alerts = parse_alerts()
    vehicles = parse_vehicle_positions()
    feed_age_seconds = vehicle_feed_age_seconds(vehicles)
    history = route_history(route.route_id, limit=200)

    leg_results: list[LegEvaluation] = []
    route_delay_total = 0
    route_risk_value = 0.0
    transfer_risk_value = 0.0

    for leg in route.legs:
        matched_alerts = alerts.route_alert_counts.get(leg.route_id, 0)
        active_vehicles = vehicles.route_vehicle_counts.get(leg.route_id, 0)

        delay_from_alerts = matched_alerts * 4
        delay_from_coverage = 3 if active_vehicles == 0 else 0
        delay_from_staleness = 2 if feed_age_seconds is not None and feed_age_seconds > 120 else 0
        expected_delay = min(30, delay_from_alerts + delay_from_coverage + delay_from_staleness)

        leg_risk_value = min(100.0, matched_alerts * 25 + (12 if active_vehicles == 0 else 0))
        transfer_value = min(
            100.0,
            max(0, expected_delay - leg.planned_transfer_minutes_after) * 12
            if leg.planned_transfer_minutes_after
            else leg_risk_value * 0.35,
        )
        reliability_score = max(
            5.0,
            min(100.0, 100 - (expected_delay * 2.5) - (matched_alerts * 8) + min(active_vehicles, 5) * 2),
        )

        explanation_bits = []
        if matched_alerts:
            explanation_bits.append(f"{matched_alerts} live alert(s) currently match this leg")
        if active_vehicles:
            explanation_bits.append(f"{active_vehicles} active vehicle position(s) were seen on the route")
        else:
            explanation_bits.append("no active vehicle positions were seen for this route")
        if feed_age_seconds is not None:
            explanation_bits.append(f"vehicle feed age is about {feed_age_seconds} seconds")

        leg_results.append(
            LegEvaluation(
                leg_id=leg.leg_id,
                line=leg.line,
                route_id=leg.route_id,
                current_risk=risk_level(leg_risk_value),
                expected_delay_minutes=expected_delay,
                transfer_risk=risk_level(transfer_value),
                reliability_score=round(reliability_score, 1),
                matched_alerts=matched_alerts,
                active_vehicles=active_vehicles,
                explanation="; ".join(explanation_bits),
            )
        )

        route_delay_total += expected_delay
        route_risk_value = max(route_risk_value, leg_risk_value)
        transfer_risk_value = max(transfer_risk_value, transfer_value)

    route_score = round(sum(leg.reliability_score for leg in leg_results) / max(len(leg_results), 1), 1)
    features = extract_features(route=route, alerts=alerts, vehicles=vehicles, history=history)
    predicted_delay_minutes, prob_delay = predict_delay(features)
    overall_explanation = (
        f"Scored {len(route.legs)} leg(s) using current GTFS alerts and vehicle positions. "
        f"Model predicts ~{predicted_delay_minutes:.1f} minute delay "
        f"with {prob_delay*100:.1f}% chance of exceeding {10} minutes."
    )

    return RouteEvaluationResponse(
        route_id=route.route_id,
        route_name=route.name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        current_risk=risk_level(route_risk_value),
        expected_delay_minutes=route_delay_total,
        predicted_delay_minutes=round(predicted_delay_minutes, 2),
        delay_over_threshold_probability=round(prob_delay, 3),
        transfer_risk=risk_level(transfer_risk_value),
        route_reliability_score=route_score,
        legs=leg_results,
        explanation=overall_explanation,
        feature_summary=features,
    )
