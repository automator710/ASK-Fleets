"""GPS Tracking Service — simulates live vehicle positions and ETA."""

import math
import random
import time
from datetime import datetime, timedelta
from typing import Any, Optional

# Simulated vehicle fleet with predefined routes (lat/lng waypoints)
# status: Moving | Available | Arrived | Maintenance
_ROUTES = {
    "VH-001": {
        "name": "Truck Alpha",
        "type": "Heavy Truck",
        "driver": "Rajan Kumar",
        "destination": "Mumbai Warehouse",
        "dest_lat": 19.0760, "dest_lng": 72.8777,
        "fixed_status": None,  # dynamic (Moving/Arrived based on progress)
        "waypoints": [
            (18.5204, 73.8567), (18.7200, 73.5400),
            (18.9000, 73.2000), (19.0760, 72.8777),
        ],
    },
    "VH-002": {
        "name": "Van Beta",
        "type": "Delivery Van",
        "driver": "Priya Sharma",
        "destination": "Delhi Depot",
        "dest_lat": 28.7041, "dest_lng": 77.1025,
        "fixed_status": None,
        "waypoints": [
            (28.4089, 77.3178), (28.5000, 77.2500),
            (28.6000, 77.2000), (28.7041, 77.1025),
        ],
    },
    "VH-003": {
        "name": "Bike Gamma",
        "type": "Courier Bike",
        "driver": "Amit Verma",
        "destination": "Bangalore HQ",
        "dest_lat": 12.9716, "dest_lng": 77.5946,
        "fixed_status": None,
        "waypoints": [
            (12.8458, 77.6629), (12.9000, 77.6200),
            (12.9400, 77.6000), (12.9716, 77.5946),
        ],
    },
    "VH-004": {
        "name": "Truck Delta",
        "type": "Heavy Truck",
        "driver": "Sunita Rao",
        "destination": "Chennai Port",
        "dest_lat": 13.0827, "dest_lng": 80.2707,
        "fixed_status": None,
        "waypoints": [
            (12.8237, 80.0450), (12.9000, 80.1500),
            (13.0000, 80.2200), (13.0827, 80.2707),
        ],
    },
    # Arrived vehicles (parked at their destination)
    "VH-005": {
        "name": "Van Epsilon",
        "type": "Delivery Van",
        "driver": "Karan Mehta",
        "destination": "Hyderabad Hub",
        "dest_lat": 17.3850, "dest_lng": 78.4867,
        "fixed_status": "Arrived",
        "waypoints": [(17.3850, 78.4867), (17.3850, 78.4867)],
    },
    "VH-006": {
        "name": "Bike Zeta",
        "type": "Courier Bike",
        "driver": "Neha Singh",
        "destination": "Kolkata Depot",
        "dest_lat": 22.5726, "dest_lng": 88.3639,
        "fixed_status": "Arrived",
        "waypoints": [(22.5726, 88.3639), (22.5726, 88.3639)],
    },
    "VH-007": {
        "name": "Truck Eta",
        "type": "Heavy Truck",
        "driver": "Vikram Nair",
        "destination": "Ahmedabad Yard",
        "dest_lat": 23.0225, "dest_lng": 72.5714,
        "fixed_status": "Arrived",
        "waypoints": [(23.0225, 72.5714), (23.0225, 72.5714)],
    },
    "VH-008": {
        "name": "Van Theta",
        "type": "Delivery Van",
        "driver": "Deepa Iyer",
        "destination": "Pune Warehouse",
        "dest_lat": 18.5204, "dest_lng": 73.8567,
        "fixed_status": "Arrived",
        "waypoints": [(18.5204, 73.8567), (18.5204, 73.8567)],
    },
    # Available vehicles (idle, ready to move)
    "VH-009": {
        "name": "Truck Iota",
        "type": "Heavy Truck",
        "driver": "Suresh Babu",
        "destination": "—",
        "dest_lat": 28.6139, "dest_lng": 77.2090,
        "fixed_status": "Available",
        "waypoints": [(28.6139, 77.2090), (28.6139, 77.2090)],
    },
    "VH-010": {
        "name": "Bike Kappa",
        "type": "Courier Bike",
        "driver": "Meera Pillai",
        "destination": "—",
        "dest_lat": 13.0827, "dest_lng": 80.2707,
        "fixed_status": "Available",
        "waypoints": [(13.0827, 80.2707), (13.0827, 80.2707)],
    },
    # On maintenance
    "VH-011": {
        "name": "Truck Lambda",
        "type": "Heavy Truck",
        "driver": "Arjun Rao",
        "destination": "Service Centre",
        "dest_lat": 19.0760, "dest_lng": 72.8777,
        "fixed_status": "Maintenance",
        "waypoints": [(19.0760, 72.8777), (19.0760, 72.8777)],
    },
    "VH-012": {
        "name": "Van Mu",
        "type": "Delivery Van",
        "driver": "Pooja Das",
        "destination": "Service Centre",
        "dest_lat": 12.9716, "dest_lng": 77.5946,
        "fixed_status": "Maintenance",
        "waypoints": [(12.9716, 77.5946), (12.9716, 77.5946)],
    },
}

_SPEED = {"Heavy Truck": 60, "Delivery Van": 80, "Courier Bike": 45}


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _interpolate(p1: tuple, p2: tuple, t: float) -> tuple:
    return (p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t)


class GPSTrackingService:
    """Returns simulated real-time GPS positions and ETAs for all fleet vehicles."""

    @staticmethod
    def get_all_vehicles() -> list[dict[str, Any]]:
        vehicles = []
        cycle = (time.time() % 3600) / 3600  # 0..1 over an hour

        for vid, info in _ROUTES.items():
            rand = random.Random(vid + str(int(time.time() // 10)))
            waypoints = info["waypoints"]
            n_segments = len(waypoints) - 1
            fixed_status = info["fixed_status"]

            if fixed_status in ("Arrived", "Available", "Maintenance"):
                # Parked — use destination coords with tiny noise
                lat = info["dest_lat"] + rand.uniform(-0.001, 0.001)
                lng = info["dest_lng"] + rand.uniform(-0.001, 0.001)
                status = fixed_status
                remaining_km = 0.0
                eta_str = "—"
                eta_mins = 0
                speed = 0
            else:
                # Moving — interpolate along route
                seg_idx = min(int(cycle * n_segments), n_segments - 1)
                seg_t = (cycle * n_segments) - seg_idx
                lat, lng = _interpolate(waypoints[seg_idx], waypoints[seg_idx + 1], seg_t)
                lat += rand.uniform(-0.002, 0.002)
                lng += rand.uniform(-0.002, 0.002)

                dest_lat, dest_lng = info["dest_lat"], info["dest_lng"]
                remaining_km = _haversine_km(lat, lng, dest_lat, dest_lng)
                speed_base = _SPEED.get(info["type"], 60)
                speed = speed_base + rand.randint(-5, 10)
                eta_hours = remaining_km / max(speed, 1)
                eta_dt = datetime.now() + timedelta(hours=eta_hours)
                eta_str = eta_dt.strftime("%H:%M")
                eta_mins = int(eta_hours * 60)
                status = "Arrived" if cycle >= 0.95 else "Moving"

            vehicles.append({
                "id": vid,
                "name": info["name"],
                "type": info["type"],
                "driver": info["driver"],
                "destination": info["destination"],
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "dest_lat": info["dest_lat"],
                "dest_lng": info["dest_lng"],
                "speed_kmh": speed,
                "remaining_km": round(remaining_km, 1),
                "eta": eta_str,
                "eta_mins": eta_mins,
                "status": status,
                "last_updated": datetime.now().strftime("%H:%M:%S"),
            })
        return vehicles

    @staticmethod
    def get_vehicle(vehicle_id: str) -> Optional[dict[str, Any]]:
        for v in GPSTrackingService.get_all_vehicles():
            if v["id"] == vehicle_id:
                return v
        return None
