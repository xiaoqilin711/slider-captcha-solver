"""Gap localization through an external OCR endpoint.

The OCR service is expected to accept a base64 image and return a JSON
payload whose structure differs by vendor. Both the request builder and the
response parser are injectable, so the module stays vendor-agnostic.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Callable, Optional

import requests


def default_response_parser(r: dict) -> Optional[float]:
    """Parse a nested ``[[x1, y1, x2, y2]]`` box, returning left edge x1.

    Many OCR vendors double-wrap the box; adjust the index path per vendor.
    """
    msg = r.get("msg")
    if not msg:
        return None
    try:
        box = json.loads(msg)[0]["box"][0]
        return float(box[0])
    except (TypeError, KeyError, IndexError, ValueError):
        return None


class GapLocator:
    """Locate the gap's left edge ``x1`` in a slider background image."""

    def __init__(
        self,
        url: str,
        key_code: str,
        question: str = "",
        model_name: str = "",
        parser: Callable[[dict], Optional[float]] = default_response_parser,
        timeout: int = 60,
    ) -> None:
        self.url = url
        self.key_code = key_code
        self.question = question
        self.model_name = model_name
        self.parser = parser
        self.timeout = timeout

    def locate(self, image_path: str) -> Optional[float]:
        """Return the gap left edge x1, or ``None`` if the OCR call fails."""
        with open(image_path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        payload: dict[str, Any] = {
            "base64Image": b64,
            "modelName": self.model_name,
            "keyCode": self.key_code,
            "question": self.question,
            "system": "",
        }
        resp = requests.post(self.url, json=payload, timeout=self.timeout).json()
        return self.parser(resp)
