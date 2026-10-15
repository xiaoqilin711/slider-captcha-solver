"""Human-like drag trajectory: generation and analysis.

This module holds the *mechanics* of turning a recorded drag into an
absolute point list and summarizing its shape. It carries no site-specific
constants: the reference ``(dx, dt, dy)`` recording is passed in by the
caller, typically from an ``examples`` profile or an external file.

The reference shape used in the case study is a recording of a real human
drag — a "fast sprint, then slow fine-tune" curve — normalized to unit
distance and scaled to any target distance by :func:`scale_to_distance`.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

# (x, y, dt_ms) — absolute cumulative position + per-step duration.
Point = Tuple[float, float, float]


def scale_to_distance(
    dx: Sequence[float],
    dt: Sequence[float],
    dy: Sequence[float],
    distance: float,
) -> List[Point]:
    """Scale a recorded per-step trajectory to an absolute ``distance``.

    ``dx`` is per-step horizontal displacement, ``dt`` per-step duration in
    milliseconds and ``dy`` per-step vertical displacement. Returns absolute
    cumulative ``(x, y, dt_ms)`` points. Displacements are scaled by
    ``distance / sum(dx)`` so the original shape is preserved; timings are
    kept verbatim.
    """
    if len({len(dx), len(dt), len(dy)}) != 1:
        raise ValueError("dx, dt and dy must have equal length")
    total = float(sum(dx))
    if total <= 0:
        raise ValueError("sum(dx) must be positive")
    points: List[Point] = []
    ratio = distance / total
    cx = 0.0
    cy = 0.0
    for dxi, dyi, dti in zip(dx, dy, dt):
        cx += dxi * ratio
        cy += dyi
        points.append((cx, cy, float(dti)))
    return points


def analyze_trace(points: Sequence[Point]) -> dict:
    """Summarize a drag trace.

    Returns speed by thirds, pause indices and y-axis noise — the three
    features that matter when judging whether a drag looks human.
    """
    if not points:
        return {"count": 0}
    n = len(points)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    dts = [p[2] for p in points]  # per-step duration (ms)

    # Cumulative timestamp at which each point is reached.
    cum_t = []
    acc = 0.0
    for d in dts:
        acc += d
        cum_t.append(acc)

    thirds = []
    for a, b in ((0, n // 3), (n // 3, 2 * n // 3), (2 * n // 3, n)):
        if b <= a:
            continue
        seg_dx = xs[b - 1] - xs[a]
        seg_dt = cum_t[b - 1] - cum_t[a]
        thirds.append(
            {
                "distance_px": round(seg_dx, 2),
                "duration_ms": round(seg_dt, 2),
                "speed_px_s": round(seg_dx / seg_dt * 1000.0, 1) if seg_dt else 0.0,
            }
        )

    pauses = [i for i, dti in enumerate(dts) if dti > 30]
    y_noise = {
        "nonzero": sum(1 for y in ys if abs(y) > 0.5),
        "max": round(max((abs(y) for y in ys), default=0.0), 2),
    }
    return {"count": n, "thirds": thirds, "pause_indices": pauses, "y_noise": y_noise}
