"""
FedEx OAuth2 authentication helper.

Fetches and caches a Bearer token using the FedEx REST API
client-credentials flow. The token is re-fetched automatically
when it expires (or within REFRESH_BUFFER_SECONDS of expiry).

Required .env keys:
    FEDEX_CLIENT_ID       — OAuth2 client ID from developer.fedex.com
    FEDEX_CLIENT_SECRET   — OAuth2 client secret
    FEDEX_ENV             — set to "sandbox" to use the sandbox endpoint
    FEDEX_BASE_URL        — (optional) full URL override; takes precedence over FEDEX_ENV
"""

import os
import time
import threading
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

_PRODUCTION_BASE_URL = "https://apis.fedex.com"
_SANDBOX_BASE_URL = "https://apis-sandbox.fedex.com"
_TOKEN_ENDPOINT = "/oauth/token"
_REFRESH_BUFFER_SECONDS = 60  # refresh this many seconds before actual expiry


class FedExAuthError(Exception):
    pass


class FedExAuth:
    """Thread-safe FedEx OAuth2 token manager.

    Usage:
        auth = FedExAuth()
        headers = auth.get_headers()   # {"Authorization": "Bearer <token>", ...}

    Or grab just the token:
        token = auth.get_token()
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        sandbox: bool = False,
    ) -> None:
        self._client_id = client_id or os.getenv("FEDEX_CLIENT_ID")
        self._client_secret = client_secret or os.getenv("FEDEX_CLIENT_SECRET")

        if not self._client_id or not self._client_secret:
            raise FedExAuthError(
                "FedEx credentials missing. Set FEDEX_CLIENT_ID and "
                "FEDEX_CLIENT_SECRET in your .env file."
            )

        if base_url:
            self._base_url = base_url.rstrip("/")
        elif sandbox or os.getenv("FEDEX_ENV", "").strip().lower() == "sandbox":
            self._base_url = _SANDBOX_BASE_URL
        else:
            self._base_url = os.getenv("FEDEX_BASE_URL", _PRODUCTION_BASE_URL).rstrip("/")

        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def get_token(self) -> str:
        """Return a valid Bearer token, fetching/refreshing as needed."""
        with self._lock:
            if self._is_expired():
                self._fetch_token()
            return self._token  # type: ignore[return-value]

    def get_headers(self) -> "dict[str, str]":
        """Return Authorization headers ready to pass to requests."""
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
            "X-locale": "en_US",
        }

    def invalidate(self) -> None:
        """Force the next call to re-fetch a fresh token."""
        with self._lock:
            self._expires_at = 0.0

    # ── Internals ─────────────────────────────────────────────────────────────

    def _is_expired(self) -> bool:
        return time.monotonic() >= self._expires_at - _REFRESH_BUFFER_SECONDS

    def _fetch_token(self) -> None:
        url = self._base_url + _TOKEN_ENDPOINT
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        try:
            response = requests.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            response.raise_for_status()
        except requests.Timeout:
            raise FedExAuthError("FedEx token request timed out.")
        except requests.HTTPError as exc:
            raise FedExAuthError(
                f"FedEx token request failed [{exc.response.status_code}]: "
                f"{exc.response.text}"
            ) from exc
        except requests.RequestException as exc:
            raise FedExAuthError(f"FedEx token request error: {exc}") from exc

        data = response.json()

        if "access_token" not in data:
            raise FedExAuthError(
                f"FedEx token response missing 'access_token': {data}"
            )

        self._token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._expires_at = time.monotonic() + expires_in
