# slider-captcha-solver

[English](README.md) | [中文](README.zh-CN.md)

A research toolkit for **slider CAPTCHA automation** — OCR gap localization, human-like drag trajectory generation, network capture, and controlled experiments — extracted from a real, end-to-end engagement against a commercial slider CAPTCHA vendor.

> **Legal notice**: this project is for authorized security research, reverse-engineering study and automation learning only. All target-identifying details (site domain, vendor name, OCR credentials, CSS class names, API paths) are redacted; the reusable algorithmic findings are kept. Do not use it against any target without authorization.

## Why this exists

Most slider CAPTCHA write-ups stop at "I found the gap and dragged". The hard part — and the part this repository demonstrates — is the two things that actually determine success:

1. **The drag distance is not the gap's left edge.** A calibrated offset correction is required (here: `+10px`), and it is an empirical per-target constant, not a protocol value.
2. **The trajectory shape matters more than the distance.** A symmetric "ease-in-out" curve with overshoot and y-axis jitter is *rejected before the check request is even sent*; a real "fast sprint, then slow fine-tune" curve is accepted.

This repository packages the *reusable* mechanics (gap localization, trajectory generation/analysis, drag execution, network capture, controlled experiments) into a site-agnostic library, and keeps the *site-specific* findings (protocol, calibrated offset, recorded trajectory) in a redacted case study.

## Features

- **`track`** — scale a recorded human drag to any distance; summarize speed-by-thirds, pauses and y-noise.
- **`ocr`** — pluggable gap localization against any base64-in / box-out OCR endpoint.
- **`drag`** — drive a slider via CDP mouse events (Playwright `page.mouse`).
- **`capture`** — collect JSONP-wrapped responses and pull fields by regex.
- **`trace_recorder`** — record a real user's drag from the page, immune to navigation resets.
- **`probe`** — controlled session-vs-IP experiments (one variable at a time).
- **`dom`** — dump slider geometry and check whether the background image is at native pixel scale.

## Quick start

```bash
pip install -e .
# or, with test dependencies:
pip install -e ".[dev]"
pytest
```

Start a browser with remote debugging enabled:

```bash
msedge --remote-debugging-port=9222
```

Then run the end-to-end demo (fill the redacted placeholders in `examples/profile_slider_vendor.py` first):

```bash
python examples/solve_demo.py
```

## Architecture

```
slider_solver/            # site-agnostic library (no vendor constants)
  track.py                # trajectory scaling + analysis (pure logic, tested)
  ocr.py                  # pluggable gap localization
  capture.py              # JSONP unwrap + field extraction
  drag.py                 # CDP mouse drag
  trace_recorder.py       # in-page trace recording (navigation-safe)
  probe.py                # session-vs-IP controlled experiment
  dom.py                  # slider geometry dump
  cli.py                  # analyze / trace / probe / solve entry points
examples/                 # site-specific, redacted
  profile_slider_vendor.py  # redacted target profile + kept algorithmics
  solve_demo.py             # end-to-end wiring
tests/                    # pure-logic tests
docs/
  case-study.md           # full timeline (English)
  case-study.zh-CN.md     # full timeline (Chinese)
```

## How it works (the loop)

```
capture the challenge response   ->  extract background image URL
download the background image    ->  OCR gap left edge x1
drag distance = x1 + OFFSET      ->  scale the recorded trajectory
drive the slider via page.mouse  ->  frontend check -> server verify
```

## Honest boundaries

- This is **frontend-event simulation**, not an algorithm-level break: the vendor's frontend computes the `validate` token itself; we do not forge it.
- The `+10` offset and the recorded trajectory are **snapshots calibrated against one target at one point in time**. They are likely stale the moment the vendor ships a new challenge style. Re-calibrate per target (see the case study).
- Gap localization depends on a **third-party OCR service**; there is no self-hosted detector here.
- Server-side `verify` is confirmed **indirectly** (page navigates to full content), since the site-to-vendor verify call is not visible to the browser.
- Only the pure-logic parts (`track`, `capture`) are covered by tests; the browser path requires a live authorized target.

See `docs/case-study.md` for the full timeline, the failures, and how the offset and trajectory were calibrated.

## License

MIT — see [LICENSE](LICENSE).
