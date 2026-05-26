"""
Dashboard REST authentication module.

Provides three Flask Blueprint routes:
    POST /api/auth/login   — validate credentials, issue JWT + set session
    POST /api/auth/logout  — clear session + invalidate token client-side
    GET  /api/auth/me      — return current user info (JWT required)

Also exports:
    require_jwt  — decorator for protecting other API routes via Bearer token
    DEMO_USERS   — in-memory credential store (replace with DB in production)
"""

import os
import time
import functools
from typing import Optional

import jwt
from flask import Blueprint, request, jsonify, session
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 8 * 3600  # 8 hours

# ── In-memory users (replace with DB query in production) ────────────────────
# Structure: { username: { "password": ..., "role": ..., "name": ... } }
DEMO_USERS = {
    "admin": {
        "password": os.getenv("DASHBOARD_ADMIN_PASSWORD", "admin123"),
        "role": "admin",
        "name": "Admin User",
    },
    "manager": {
        "password": os.getenv("DASHBOARD_MANAGER_PASSWORD", "manager123"),
        "role": "manager",
        "name": "Fleet Manager",
    },
}

# ── Blueprint ─────────────────────────────────────────────────────────────────

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _issue_token(username: str, role: str, name: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "name": name,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _bearer_token() -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None


# ── Decorator ─────────────────────────────────────────────────────────────────

def require_jwt(f):
    """Protect an API route — requires a valid Bearer token in Authorization header."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = _bearer_token()
        if not token:
            return jsonify({"error": "Authorization header missing"}), 401
        payload = _decode_token(token)
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.jwt_payload = payload
        return f(*args, **kwargs)
    return decorated


# ── Routes ────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body (JSON): { "username": "...", "password": "..." }
    Returns: { "token": "...", "user": { username, role, name } }
    Also sets Flask session so the dashboard_required decorator still works.
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = DEMO_USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    token = _issue_token(username, user["role"], user["name"])

    # Also hydrate Flask session so server-side dashboard_required decorator passes
    session["user"] = username
    session["role"] = user["role"]
    session["name"] = user["name"]

    return jsonify({
        "token": token,
        "user": {
            "username": username,
            "role": user["role"],
            "name": user["name"],
        },
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/auth/logout
    Clears server-side session. Client should discard the JWT.
    """
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@auth_bp.route("/me", methods=["GET"])
@require_jwt
def me():
    """
    GET /api/auth/me
    Returns current user info decoded from Bearer token.
    """
    p = request.jwt_payload
    return jsonify({
        "username": p.get("sub"),
        "role": p.get("role"),
        "name": p.get("name"),
    }), 200
