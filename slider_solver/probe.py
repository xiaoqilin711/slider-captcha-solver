"""Controlled experiments: is a bypass session-scoped or IP-scoped?

The single most useful diagnostic when a challenge "mysteriously disappears"
is to run the *same* probe against two contexts that differ in exactly one
variable (cookies), keeping IP, browser and user-agent identical. This module
packages that pattern.
"""

from __future__ import annotations

from typing import List


def probe_page(
    page,
    slider_selector: str,
    markers: List[str],
    settle_ms: int = 6000,
) -> dict:
    """Visit the current page URL and report challenge presence.

    ``markers`` are substrings that indicate a challenge (class names,
    localized strings like "human verification", etc.). Returns a dict with
    URL, slider presence, marker presence and body length.
    """
    page.wait_for_timeout(settle_ms)
    url = page.url
    has_slider = page.evaluate(
        "(sel) => !!document.querySelector(sel)", slider_selector
    )
    html = page.content()
    has_marker = any(m in html for m in markers)
    body_len = page.evaluate("() => document.body.innerText.length")
    return {
        "url": url,
        "slider_present": bool(has_slider),
        "marker_present": bool(has_marker),
        "body_length": int(body_len),
    }


def probe_contexts(
    contexts,
    url: str,
    slider_selector: str,
    markers: List[str],
    timeout_ms: int = 30000,
    settle_ms: int = 6000,
) -> List[dict]:
    """Probe the same ``url`` across contexts that differ in one variable.

    Each entry in ``contexts`` is ``(label, context)``. Returns one result per
    context. Use two contexts — one with cookies, one clean — to isolate
    session-scoped vs IP-scoped bypass.
    """
    results = []
    for label, ctx in contexts:
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            info = probe_page(page, slider_selector, markers, settle_ms=settle_ms)
            info["label"] = label
            results.append(info)
        finally:
            page.close()
    return results
