from __future__ import annotations

import json
from pathlib import Path

from .errors import AuthMissing


class SecretCookies(dict):
    """A dict that won't leak its values via repr/str."""

    def __repr__(self) -> str:
        return f"SecretCookies(<{len(self)} cookies redacted>)"

    __str__ = __repr__


AUTH_DIR = Path.home() / "Documents" / ".udemy"
COOKIES_PATH = AUTH_DIR / "cookies.json"
HEADERS_PATH = AUTH_DIR / "headers.json"


def load_auth() -> tuple[SecretCookies, dict[str, str]]:
    if not AUTH_DIR.exists():
        raise AuthMissing(
            f"Auth directory not found at {AUTH_DIR}. Create it and place cookies.json "
            f"(exported from a logged-in Udemy browser tab). See CLAUDE.md > Authentication."
        )
    if not COOKIES_PATH.exists():
        raise AuthMissing(f"Missing {COOKIES_PATH}. Export browser cookies into a JSON name→value map.")
    if not HEADERS_PATH.exists():
        raise AuthMissing(f"Missing {HEADERS_PATH}. Run the auth-persistence script after capturing browser request headers.")

    try:
        cookies_raw = json.loads(COOKIES_PATH.read_text(encoding="utf-8"))
        headers = json.loads(HEADERS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise AuthMissing(f"Auth file is not valid JSON: {e}") from None

    if not isinstance(cookies_raw, dict) or not isinstance(headers, dict):
        raise AuthMissing("cookies.json and headers.json must each be a JSON object (name → value).")

    return SecretCookies(cookies_raw), headers
