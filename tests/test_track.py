"""Tests for the trajectory generation / analysis pure logic."""

from slider_solver.track import analyze_trace, scale_to_distance


def test_scale_preserves_total_distance():
    dx = [1, 2, 3, 4]
    dt = [10, 10, 10, 10]
    dy = [0, 0, 0, 0]
    points = scale_to_distance(dx, dt, dy, 100.0)
    assert abs(points[-1][0] - 100.0) < 1e-6
    assert points[-1][2] == 10.0


def test_scale_preserves_shape_ratio():
    dx = [5, 5]
    dt = [8, 8]
    dy = [0, 0]
    points = scale_to_distance(dx, dt, dy, 20.0)
    # 5/10 of 20 == 10, then full 20
    assert abs(points[0][0] - 10.0) < 1e-6
    assert abs(points[1][0] - 20.0) < 1e-6


def test_scale_rejects_mismatched_lengths():
    try:
        scale_to_distance([1, 2], [1, 2], [0], 10.0)
    except ValueError:
        return
    raise AssertionError("expected ValueError for mismatched lengths")


def test_analyze_reports_third_speeds():
    # 30 uniform points -> three thirds of 10 each
    dx = [1] * 30
    dt = [10] * 30
    dy = [0] * 30
    points = scale_to_distance(dx, dt, dy, 30.0)
    summary = analyze_trace(points)
    assert summary["count"] == 30
    assert len(summary["thirds"]) == 3
    # each third: 10px in 100ms -> 100 px/s
    for t in summary["thirds"]:
        assert t["speed_px_s"] == 100.0


def test_analyze_detects_pauses():
    dx = [1, 1, 1]
    dt = [8, 50, 8]  # middle step is a pause
    dy = [0, 0, 0]
    points = scale_to_distance(dx, dt, dy, 3.0)
    summary = analyze_trace(points)
    assert 1 in summary["pause_indices"]
