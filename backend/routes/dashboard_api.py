"""
Dashboard REST API — /api/dashboard/*

All routes require a valid JWT (via require_jwt decorator).
Business logic is stubbed; replace each TODO with real service calls
when the services layer is built.

Endpoints:
    GET  /api/dashboard/stats          — headline KPI metrics
    GET  /api/dashboard/fleet          — fleet vehicle list + status
    GET  /api/dashboard/fleet/<id>     — single vehicle detail
    GET  /api/dashboard/shipments      — active shipment list
    GET  /api/dashboard/shipments/<id> — single shipment detail
    GET  /api/dashboard/alerts         — unresolved operational alerts
    PATCH /api/dashboard/alerts/<id>   — acknowledge / resolve an alert
    GET  /api/dashboard/carriers       — connected carrier auth status
"""

from flask import Blueprint, jsonify, request
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from authentication.dashboard_auth import require_jwt
from services.gps_tracking import GPSTrackingService

dashboard_api = Blueprint("dashboard_api", __name__, url_prefix="/api/dashboard")


# ── Stats ─────────────────────────────────────────────────────────────────────

@dashboard_api.route("/stats", methods=["GET"])
@require_jwt
def stats():
    """Headline KPIs shown on the dashboard overview cards."""
    # TODO: replace with real DB / service aggregations
    return jsonify({
        "active_vehicles": 12480,
        "on_time_rate_pct": 94.2,
        "open_alerts": 7,
        "avg_fuel_savings_pct": 22,
        "shipments_today": 318,
        "revenue_today_usd": 148500,
    }), 200


# ── Fleet ─────────────────────────────────────────────────────────────────────

@dashboard_api.route("/fleet", methods=["GET"])
@require_jwt
def fleet_list():
    """Paginated vehicle list. Query params: page (default 1), per_page (default 20)."""
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    # TODO: query fleet service / database
    vehicles = [
        {
            "id": f"VH-{1000 + i}",
            "plate": f"TRK-{1000 + i}",
            "driver": f"Driver {i}",
            "status": "active" if i % 3 != 0 else "idle",
            "lat": 37.7749 + i * 0.01,
            "lng": -122.4194 + i * 0.01,
            "carrier": ["FedEx", "USPS", "Uber Freight"][i % 3],
            "fuel_pct": 80 - i * 3,
        }
        for i in range(1, per_page + 1)
    ]
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": 12480,
        "vehicles": vehicles,
    }), 200


@dashboard_api.route("/fleet/<vehicle_id>", methods=["GET"])
@require_jwt
def fleet_detail(vehicle_id):
    """Single vehicle details including last GPS ping and maintenance status."""
    # TODO: look up vehicle_id in fleet service
    return jsonify({
        "id": vehicle_id,
        "plate": vehicle_id.replace("VH-", "TRK-"),
        "driver": "John Doe",
        "status": "active",
        "lat": 37.7749,
        "lng": -122.4194,
        "speed_mph": 62,
        "carrier": "FedEx",
        "fuel_pct": 71,
        "odometer_miles": 48320,
        "last_ping": "2026-05-24T22:00:00Z",
        "maintenance": {"due_miles": 52000, "status": "ok"},
    }), 200


# ── Shipments ─────────────────────────────────────────────────────────────────

@dashboard_api.route("/shipments", methods=["GET"])
@require_jwt
def shipment_list():
    """Active shipment list. Query params: status (all|active|delayed|delivered), page."""
    status   = request.args.get("status", "all")
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    # TODO: query shipment service
    statuses = ["active", "delayed", "delivered"]
    shipments = [
        {
            "id": f"SHP-{2000 + i}",
            "awb": f"AWB-{3000 + i}",
            "carrier": ["FedEx", "USPS", "Uber Freight"][i % 3],
            "origin": "Los Angeles, CA",
            "destination": "San Francisco, CA",
            "status": statuses[i % 3] if status == "all" else status,
            "eta": "2026-05-25T10:00:00Z",
            "vehicle_id": f"VH-{1000 + i}",
        }
        for i in range(1, per_page + 1)
    ]
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": 318,
        "shipments": shipments,
    }), 200


@dashboard_api.route("/shipments/<shipment_id>", methods=["GET"])
@require_jwt
def shipment_detail(shipment_id):
    """Full detail for one shipment including tracking events."""
    # TODO: look up shipment_id in shipment service / FedEx API
    return jsonify({
        "id": shipment_id,
        "awb": shipment_id.replace("SHP-", "AWB-"),
        "carrier": "FedEx",
        "origin": "Los Angeles, CA",
        "destination": "San Francisco, CA",
        "status": "active",
        "eta": "2026-05-25T10:00:00Z",
        "vehicle_id": "VH-1001",
        "events": [
            {"time": "2026-05-24T08:00:00Z", "event": "Picked up", "location": "Los Angeles, CA"},
            {"time": "2026-05-24T14:00:00Z", "event": "In transit", "location": "Fresno, CA"},
        ],
    }), 200


# ── Alerts ────────────────────────────────────────────────────────────────────

@dashboard_api.route("/alerts", methods=["GET"])
@require_jwt
def alerts_list():
    """Unresolved operational alerts (maintenance, delay, compliance)."""
    # TODO: query alert service
    alerts = [
        {"id": "ALT-001", "type": "maintenance", "vehicle_id": "VH-1004", "message": "Oil change due in 200 miles", "severity": "warning", "resolved": False},
        {"id": "ALT-002", "type": "delay",       "vehicle_id": "VH-1007", "message": "ETA delayed by 45 min",       "severity": "info",    "resolved": False},
        {"id": "ALT-003", "type": "compliance",  "vehicle_id": "VH-1012", "message": "ELD log not submitted",       "severity": "critical","resolved": False},
    ]
    return jsonify({"alerts": alerts, "total": len(alerts)}), 200


@dashboard_api.route("/alerts/<alert_id>", methods=["PATCH"])
@require_jwt
def alert_update(alert_id):
    """Acknowledge or resolve an alert. Body: { "resolved": true }"""
    data = request.get_json(silent=True) or {}
    resolved = bool(data.get("resolved", False))
    # TODO: persist to alert service
    return jsonify({"id": alert_id, "resolved": resolved, "updated_by": request.jwt_payload.get("sub")}), 200


# ── GPS Tracking ──────────────────────────────────────────────────────────────

@dashboard_api.route("/gps", methods=["GET"])
@require_jwt
def gps_all():
    """Live GPS positions + ETA for all tracked vehicles."""
    return jsonify({"vehicles": GPSTrackingService.get_all_vehicles()}), 200


@dashboard_api.route("/gps/<vehicle_id>", methods=["GET"])
@require_jwt
def gps_vehicle(vehicle_id):
    """Live GPS position + ETA for a single vehicle."""
    vehicle = GPSTrackingService.get_vehicle(vehicle_id)
    if not vehicle:
        return jsonify({"error": "Vehicle not found"}), 404
    return jsonify(vehicle), 200


# ── Carriers ──────────────────────────────────────────────────────────────────

@dashboard_api.route("/carriers", methods=["GET"])
@require_jwt
def carriers():
    """Status of each integrated carrier's authentication token."""
    # TODO: check live token validity from authentication modules
    return jsonify({
        "carriers": [
            {"name": "FedEx",        "status": "connected", "env": "sandbox",    "token_valid": True},
            {"name": "USPS",         "status": "pending",   "env": None,         "token_valid": False},
            {"name": "Uber Freight", "status": "pending",   "env": None,         "token_valid": False},
        ]
    }), 200
