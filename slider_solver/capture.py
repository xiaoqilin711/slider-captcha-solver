"""Network capture: collect response bodies and extract fields from
JSONP-wrapped responses.

The vendor's API returns JSONP like ``__JSONP_xxx({...});``. This module
unwraps the callback and lets callers pull individual fields by regex, which
is more forgiving than ``json.loads`` against a live, noisy response.
"""

from __future__ import annotations

import re
from typing import Optional

_JSONP_RE = re.compile(r"__JSONP_\w+\((\{.*\})\)\s*;?", re.S)


def unwrap_jsonp(text: str) -> str:
    """Strip the JSONP callback wrapper, returning the inner JSON object."""
    m = _JSONP_RE.search(text)
    return m.group(1) if m else text


def extract_by_pattern(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """Return the first regex capture from ``text``, or ``None``."""
    m = re.search(pattern, text)
    return m.group(group) if m else None


class ResponseCollector:
    """Collect the body of the last matching response by URL substring."""

    def __init__(self, url_substring: str) -> None:
        self.url_substring = url_substring
        self.body: Optional[str] = None
        self.url: Optional[str] = None
        self._handler = None

    def _on_response(self, resp) -> None:
        if self.url_substring in resp.url:
            try:
                self.body = resp.text()
                self.url = resp.url
            except Exception:
                pass

    def attach(self, page) -> None:
        """Start listening on ``page`` (a Playwright page)."""
        self._handler = self._on_response
        page.on("response", self._handler)

    def detach(self, page) -> None:
        """Stop listening on ``page``."""
        if self._handler is not None:
            page.remove_listener("response", self._handler)
            self._handler = None
