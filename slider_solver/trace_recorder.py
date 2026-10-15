"""Record a real user's drag from the page, immune to navigation resets.

A page navigation (e.g. after a successful solve) wipes any in-page buffer.
The recorder therefore *drains* points into Python on an interval, so the
trace survives even if the page navigates mid-drag.
"""

from __future__ import annotations

import time as _time
from typing import Callable, List, Optional

_INJECT = """
window.__user_trace = [];
let __dragging = false;
document.addEventListener('mousedown', e => { __dragging = true; window.__user_trace.push({t: Date.now(), x: e.clientX, y: e.clientY, type: 'down'}); });
document.addEventListener('mousemove', e => { if (__dragging) window.__user_trace.push({t: Date.now(), x: e.clientX, y: e.clientY, type: 'move'}); });
document.addEventListener('mouseup', e => { window.__user_trace.push({t: Date.now(), x: e.clientX, y: e.clientY, type: 'up'}); __dragging = false; });
"""


class TraceRecorder:
    """Collect raw (type, x, y, t) events from a page's document listeners."""

    def __init__(self, page) -> None:
        self.page = page
        self.points: List[dict] = []

    def start(self) -> None:
        """Inject the document-level listeners and reset the buffer."""
        self.page.evaluate(_INJECT)
        self.points = []

    def drain(self) -> List[dict]:
        """Atomically pull pending points out of the page."""
        pts = self.page.evaluate(
            "() => { const a = window.__user_trace || []; window.__user_trace = []; return a; }"
        )
        if pts:
            self.points.extend(pts)
        return pts

    def poll(
        self,
        timeout_s: float = 150.0,
        interval: float = 0.3,
        stop: Optional[Callable[[], bool]] = None,
    ) -> List[dict]:
        """Poll until ``stop()`` is truthy or ``timeout_s`` elapses.

        Returns the full list of collected points. Navigation during polling
        raises inside the evaluate and is swallowed, so the loop keeps going.
        """
        deadline = _time.time() + timeout_s
        while _time.time() < deadline:
            _time.sleep(interval)
            try:
                self.drain()
            except Exception:
                pass
            if stop is not None and stop():
                break
        return self.points

    @staticmethod
    def summarize(trace: List[dict]) -> dict:
        """Extract down/move/up counts, drag distance and inter-move timing."""
        downs = [p for p in trace if p.get("type") == "down"]
        ups = [p for p in trace if p.get("type") == "up"]
        moves = [p for p in trace if p.get("type") == "move"]
        out = {"down": len(downs), "move": len(moves), "up": len(ups)}
        if downs and ups:
            out["drag_distance_px"] = round(ups[-1]["x"] - downs[0]["x"], 1)
            out["drag_duration_ms"] = ups[-1]["t"] - downs[0]["t"]
        if len(moves) > 1:
            dts = [moves[i + 1]["t"] - moves[i]["t"] for i in range(len(moves) - 1)]
            out["dt_min_ms"] = min(dts)
            out["dt_max_ms"] = max(dts)
            out["dt_avg_ms"] = round(sum(dts) / len(dts), 1)
        return out
