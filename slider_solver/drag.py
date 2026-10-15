"""Drive a slider drag with CDP mouse events via Playwright.

``page.mouse`` maps to CDP ``Input.dispatchMouseEvent``, which the target's
document-level ``mousedown``/``mousemove``/``mouseup`` handlers consume. This
is why synthetic pointer events do not work but ``page.mouse`` does.
"""

from __future__ import annotations

import time
from typing import Sequence, Tuple

# (x, y, dt_ms) — absolute position relative to the drag start.
Point = Tuple[float, float, float]


def slider_center(page, selector: str) -> Tuple[float, float]:
    """Return the (x, y) center of the element matched by ``selector``."""
    box = page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            if (!el) throw new Error("slider not found: " + sel);
            const r = el.getBoundingClientRect();
            return {x: r.x, y: r.y, w: r.width, h: r.height};
        }""",
        selector,
    )
    return box["x"] + box["w"] / 2.0, box["y"] + box["h"] / 2.0


def drag(
    page,
    start_x: float,
    start_y: float,
    points: Sequence[Point],
    settle_ms: int = 200,
) -> None:
    """Perform a drag from ``(start_x, start_y)`` through ``points``.

    ``points`` are absolute offsets from the start; the final position is the
    last point, followed by a short settle pause before releasing the mouse.
    """
    page.mouse.move(start_x, start_y)
    time.sleep(0.2)
    page.mouse.down()
    for x, y, dt_ms in points:
        page.mouse.move(start_x + x, start_y + y)
        time.sleep(dt_ms / 1000.0)
    last_x, last_y = points[-1][0], points[-1][1]
    page.mouse.move(start_x + last_x, start_y + last_y)
    time.sleep(settle_ms / 1000.0)
    page.mouse.up()


def drag_distance(
    page,
    selector: str,
    distance: float,
    points: Sequence[Point],
    settle_ms: int = 200,
) -> None:
    """Locate the slider by ``selector`` and drag it by ``distance`` pixels."""
    sx, sy = slider_center(page, selector)
    drag(page, sx, sy, points, settle_ms=settle_ms)
