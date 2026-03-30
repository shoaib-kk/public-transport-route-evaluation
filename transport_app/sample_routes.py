from __future__ import annotations

from transport_app.models import RouteDefinition, RouteLeg


SAMPLE_ROUTES: list[RouteDefinition] = [
    RouteDefinition(
        route_id="sample_central_to_hornsby",
        name="Central to Hornsby via T1 North Shore",
        origin="Central",
        destination="Hornsby",
        planned_departure="08:30",
        legs=[
            RouteLeg(
                leg_id="leg_1",
                line="T1 North Shore Line",
                route_id="NTH_1a",
                origin="Central",
                destination="Hornsby",
                scheduled_minutes=42,
            )
        ],
    ),
    RouteDefinition(
        route_id="sample_central_to_parramatta",
        name="Central to Parramatta via T1 Western",
        origin="Central",
        destination="Parramatta",
        planned_departure="08:15",
        legs=[
            RouteLeg(
                leg_id="leg_1",
                line="T1 Western Line",
                route_id="WST_1a",
                origin="Central",
                destination="Parramatta",
                scheduled_minutes=31,
            )
        ],
    ),
    RouteDefinition(
        route_id="sample_townhall_to_wollongong",
        name="Town Hall to Wollongong with one transfer",
        origin="Town Hall",
        destination="Wollongong",
        planned_departure="17:45",
        legs=[
            RouteLeg(
                leg_id="leg_1",
                line="T4 Eastern Suburbs",
                route_id="ESI_2a",
                origin="Town Hall",
                destination="Hurstville",
                scheduled_minutes=24,
                planned_transfer_minutes_after=6,
            ),
            RouteLeg(
                leg_id="leg_2",
                line="South Coast Line",
                route_id="SCO_1a",
                origin="Hurstville",
                destination="Wollongong",
                scheduled_minutes=68,
            ),
        ],
    ),
]


def get_sample_routes() -> list[RouteDefinition]:
    return SAMPLE_ROUTES


def get_sample_route(route_id: str) -> RouteDefinition:
    for route in SAMPLE_ROUTES:
        if route.route_id == route_id:
            return route
    raise KeyError(f"Unknown sample route: {route_id}")
