"""Dump the geometry of slider-related DOM elements.

Useful to discover the draggable button, its track, the background image and
the puzzle piece — and, crucially, whether the background image is rendered
at its native pixel size (so OCR coordinates need no scaling).
"""

from __future__ import annotations

from typing import Optional

_GEOMETRY_JS = """
(sel) => {
    const out = {root: null, children: []};
    const el = document.querySelector(sel);
    if (!el) return out;
    const r = el.getBoundingClientRect();
    out.root = {x: Math.round(r.x), y: Math.round(r.y),
                w: Math.round(r.width), h: Math.round(r.height)};
    el.querySelectorAll('*').forEach(c => {
        const rr = c.getBoundingClientRect();
        if (rr.width > 0 && rr.height > 0) {
            out.children.push({
                tag: c.tagName,
                cls: (c.className || '').toString().slice(0, 60),
                x: Math.round(rr.x), y: Math.round(rr.y),
                w: Math.round(rr.width), h: Math.round(rr.height),
                cursor: getComputedStyle(c).cursor
            });
        }
    });
    return out;
}
"""


def dump_slider(page, selector: str) -> dict:
    """Return the geometry of ``selector`` and its visible descendants."""
    return page.evaluate(_GEOMETRY_JS, selector)


def natural_size(page, selector: str) -> Optional[tuple]:
    """Return the natural (unscaled) pixel size of an image element.

    If this equals the rendered size, OCR coordinates map 1:1 to page pixels.
    """
    size = page.evaluate(
        """(sel) => {
            const el = document.querySelector(sel);
            if (!el || !el.naturalWidth) return null;
            return {nw: el.naturalWidth, nh: el.naturalHeight};
        }""",
        selector,
    )
    if not size:
        return None
    return size["nw"], size["nh"]
