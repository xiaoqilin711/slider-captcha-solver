"""End-to-end solve demo: OCR gap -> distance -> human-like drag -> check.

Requires a Chromium/Edge with remote debugging enabled:

    msedge --remote-debugging-port=9222

Fill in the redacted placeholders in ``profile_slider_vendor.py`` for your own
authorized target, then run ``python examples/solve_demo.py``.
"""

import sys
import time

sys.path.insert(0, ".")           # for the slider_solver package
sys.path.insert(0, "examples")    # for the profile module

from playwright.sync_api import sync_playwright

from slider_solver.capture import ResponseCollector, extract_by_pattern
from slider_solver.drag import slider_center, drag
from slider_solver.ocr import GapLocator
from slider_solver.track import scale_to_distance

import profile_slider_vendor as P  # noqa: E402

CDP = "http://127.0.0.1:9222"


def main() -> int:
    locator = GapLocator(P.OCR_URL, P.KEY_CODE, question=P.QUESTION, model_name=P.MODEL_NAME)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        ctx = browser.new_context()
        page = ctx.new_page()

        getter = ResponseCollector(P.GET_URL_SUBSTR)
        getter.attach(page)
        page.goto(P.TARGET_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)  # let the challenge load
        getter.detach(page)

        bg_url = extract_by_pattern(getter.body or "", P.BG_PATTERN)
        if not bg_url:
            print("background image not captured")
            return 1

        bg = ctx.request.get(bg_url).body()  # fast direct fetch, not the page
        open("_bg.jpg", "wb").write(bg)
        x1 = locator.locate("_bg.jpg")
        if x1 is None:
            print("gap localization failed")
            return 1

        distance = int(x1) + P.OFFSET
        print(f"gap x1={x1} -> drag distance={distance}")

        check = ResponseCollector(P.CHECK_URL_SUBSTR)
        check.attach(page)
        sx, sy = slider_center(page, P.SLIDER_SELECTOR)
        points = scale_to_distance(P.REFERENCE_DX, P.REFERENCE_DT, P.REFERENCE_DY, distance)
        drag(page, sx, sy, points)

        result = None
        for _ in range(20):
            time.sleep(1)
            if check.body:
                result = extract_by_pattern(check.body, P.RESULT_PATTERN)
                if result:
                    break
            try:
                if page.evaluate("() => document.body.innerText.length") > 5000:
                    break  # navigated to full content
            except Exception:
                pass  # mid-navigation

        print(f"check result={result}")
        print("done")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
