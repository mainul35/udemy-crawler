from __future__ import annotations

import time
from typing import Any

from curl_cffi import requests

from .auth import SecretCookies, load_auth
from .errors import AuthInvalid, CloudflareChallenge, RateLimited

USER_AGENT_TAG = "udemy-crawler/0.1.0 (+local CLI)"
MIN_INTERVAL_S = 0.5
BACKOFF_START_S = 2.0
BACKOFF_CAP_S = 60.0
MAX_429_ATTEMPTS = 5
CONNECT_TIMEOUT_S = 10.0
READ_TIMEOUT_S = 30.0


class UdemyClient:
    def __init__(self) -> None:
        cookies, headers = load_auth()
        self._cookies: SecretCookies = cookies
        self._headers: dict[str, str] = dict(headers)
        self._session = requests.Session(impersonate="chrome124")
        self._last_at: float = 0.0

    def get_json(self, url: str, *, referer: str | None = None) -> dict[str, Any]:
        headers = dict(self._headers)
        if referer:
            headers["referer"] = referer
        backoff = BACKOFF_START_S
        for attempt in range(1, MAX_429_ATTEMPTS + 1):
            self._throttle()
            r = self._session.get(
                url,
                cookies=self._cookies,
                headers=headers,
                timeout=(CONNECT_TIMEOUT_S, READ_TIMEOUT_S),
            )
            self._last_at = time.monotonic()
            ct = r.headers.get("content-type", "")

            if r.status_code in (401, 403):
                kind = "Cookies are stale (401)" if r.status_code == 401 else "Account does not own this resource (403)"
                raise AuthInvalid(f"{kind} on {url}. Re-export cookies if 401.")

            if r.status_code == 429:
                if attempt == MAX_429_ATTEMPTS:
                    raise RateLimited(f"429 on {url} after {attempt} attempts")
                wait = self._retry_after(r) or backoff
                time.sleep(wait)
                backoff = min(backoff * 2, BACKOFF_CAP_S)
                continue

            if "application/json" not in ct:
                snippet = r.text[:200].replace("\n", " ")
                if r.status_code == 200 and ("Just a moment" in r.text or "cf-mitigated" in r.text or "challenge-platform" in r.text):
                    raise CloudflareChallenge(
                        "Got Cloudflare challenge page instead of JSON. "
                        "cf_clearance / __cf_bm have likely expired — re-export cookies from your browser."
                    )
                r.raise_for_status()
                raise CloudflareChallenge(f"Unexpected non-JSON {ct} status={r.status_code}: {snippet!r}")

            r.raise_for_status()
            return r.json()

        raise RateLimited(f"Exhausted retries on {url}")

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_at
        if elapsed < MIN_INTERVAL_S:
            time.sleep(MIN_INTERVAL_S - elapsed)

    @staticmethod
    def _retry_after(response) -> float | None:
        raw = response.headers.get("retry-after")
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return None
