"""Command-line entry point.

Subcommands cover the reusable workflows:
  trace   — record a real user's drag into JSON
  probe   — run a session-vs-IP controlled experiment
  analyze — summarize a recorded trace (speed thirds, pauses, y-noise)
  solve   — end-to-end solve using a profile (see examples/)

Site-specific values (URL, slider selector, OCR credentials, offset,
reference trajectory) are supplied via a Python profile module, so the CLI
itself stays site-agnostic.
"""

from __future__ import annotations

import argparse
import json
import sys

from .track import analyze_trace, scale_to_distance


def _cmd_analyze(args) -> int:
    with open(args.trace, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    trace = data.get("trace", data if isinstance(data, list) else [])
    moves = [p for p in trace if p.get("type") == "move"]
    if not moves:
        print("no move points found", file=sys.stderr)
        return 1
    xs = [p["x"] for p in moves]
    ys = [p["y"] for p in moves]
    ts = [p["t"] for p in moves]
    dx = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    dy = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    dt = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
    total = sum(dx)
    points = scale_to_distance(dx, dt, dy, total)
    summary = analyze_trace(points)
    print(json.dumps(summary, indent=2))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="slider-solver")
    sub = parser.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="summarize a recorded trace JSON")
    a.add_argument("trace", help="path to a user_trace.json-style file")
    a.set_defaults(func=_cmd_analyze)

    sub.add_parser("trace", help="record a real user's drag (see examples/)")
    sub.add_parser("probe", help="session-vs-IP experiment (see examples/)")
    sub.add_parser("solve", help="end-to-end solve (see examples/)")

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
