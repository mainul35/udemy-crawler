from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t ]+")


def clean_html(s: str | None) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = _TAG_RE.sub("", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _WS_RE.sub(" ", s)
    return s.strip()
