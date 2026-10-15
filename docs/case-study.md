# Case Study: Automating a Commercial Slider CAPTCHA

> Target identity fully redacted. This is the write-up behind the
> `slider-captcha-solver` repository — the timeline, the dead ends, and how
> the two non-obvious keys (the `+10px` offset and the "fast sprint, slow
> fine-tune" trajectory) were found and calibrated.

## Goal and context

A technical forum triggers a commercial slider CAPTCHA on *older* articles
(~2024 and earlier) but not on newer ones. The task: automate the slider so a
pipeline can fetch the full article body without a human in the loop.

The vendor's JS bundle reports version **2.28.5** — a recent generation; most
public write-ups target older versions.

## The chain, in one line

```
old article triggers slider
  -> local Pillow gap detector        (dead end: 1-32px unstable)
  -> third-party OCR                  (works: 4 identical reads on one image)
  -> capture + DOM recon              (getconf/get/check, slider geometry)
  -> drag = OCR x1                    (dead end: check false)
  -> manual drag to calibrate offset  (distance = x1 + 10)
  -> symmetric "humanized" track      (dead end: check never sent)
  -> replay a real recorded track     (works)
  -> check true + validate            -> server verify -> body 108 -> 29236
```

## 1. First anomaly: the challenge "disappeared"

Early on, one visit returned the full article with no slider at all. The
tempting hypothesis was "the risk control lifted itself". A two-context
experiment — identical IP/browser/UA, one context with cookies, one clean —
settled it:

| Context | Cookies | Result |
|---|---|---|
| existing | yes | body 29298, no slider |
| fresh incognito | no | body 111, **slider** |

Conclusion: **session-scoped bypass, not IP-scoped**. A clean context on the
same IP re-triggers the challenge immediately.

> Lesson: change exactly one variable, and don't mistake "two things happened
> at once" for causation.

## 2. Gap localization: local algorithm vs OCR

The local detector (pure Pillow, no numpy/OpenCV) did: grayscale -> edge
filter -> extract the puzzle piece's alpha-boundary pixels -> slide that
template across the background's edge map and pick the max-response window.
The idea was sound; the precision was not — it drifted 1-32px between reads.
Against an OCR read of `x1=144`, it once returned `164`, a 20px miss. For a
slider that rejects a few pixels of error, that is unusable.

The third-party OCR endpoint (`question=框出正确位置`) returned a nested box.
The parsing detail matters — the box is double-wrapped:

```python
x1 = json.loads(r["msg"])[0]["box"][0][0]   # box is [[x1,y1,x2,y2]]
```

Four consecutive reads of the same image returned `x1=144` unchanged (only
`y2` jittered ±1), each in ~0.9s. **OCR is the correct gap localizer; the
local algorithm is a dead end and should be abandoned, not revisited.**

## 3. Protocol and DOM recon

The vendor's initialization is three JSONP calls:

- **`getconf`** — config: JS bundle version, image servers, zone, API servers.
- **`get`** — returns `bg` (background with the gap), `front` (puzzle piece),
  `token`, `type=2` (slider), `waitTime`.
- **`check`** — receives the drag, returns `result:true` + `validate` (base64).

DOM geometry (via `getBoundingClientRect`):

| element | size |
|---|---|
| slider button | 40×38 |
| track | 320×40 |
| background image | 320×160 |
| puzzle piece | ~61×160 |

Two conclusions: the background image is rendered at its **native 320×160**,
so OCR pixel coordinates map 1:1 to page pixels (no scaling); and the 40px
button vs 61px piece matter for the `+10` derivation below.

Event layer: the frontend listens on **document-level
`mousedown`/`mousemove`/`mouseup`**, not pointer events. Playwright's
`page.mouse` maps to CDP `Input.dispatchMouseEvent` and lands on exactly that
layer — which is why synthetic pointer events did nothing but `page.mouse`
works.

## 4. Ground truth from one manual drag

A human dragged the slider once while the trace was recorded. That single
sample exposed two truths at once:

```
OCR box=[119, 28, 174, 86]  left edge x1=119
[check] true
user drag distance = 129px, duration = 1042ms
x1 - drag = -10px
64 move points, dt min=5 max=178 avg=13.0ms
```

1. **distance = OCR x1 + 10** — OCR returns the gap box's *left edge*; the
   correct drag distance is 10px past it.
2. The real shape: 64 move points over 129px in ~1s, 8-9ms sampling with
   occasional pauses.

A first recording attempt lost the trace because the page navigated after the
solve and wiped `window.__user_trace`. The fix — drain points into Python on
an interval — became `trace_recorder.py`:

```python
while not done:
    time.sleep(0.3)
    pts = page.evaluate("() => { const a = window.__user_trace || []; window.__user_trace = []; return a; }")
    trace.extend(pts)
```

## 5. The distance mystery: why +10

A second target (different article, different gap) confirmed the offset is
fixed, not a one-off:

```
OCR box=[106, 95, 162, 155]  x1=106 -> drag 116
[check] true  -> body 29236, URL -> ...-1.htm
```

The geometry: OCR frames the gap with a ~55px-wide box (left edge = x1), the
puzzle piece is 61px wide, the button is 40px wide. Half the box minus half
the button, plus the OCR framing bias, lands near 10px.

**Important**: the offset is an empirical per-target calibration, *not* a
value read out of the protocol. Change the target or the OCR model and it
must be re-calibrated.

## 6. The trajectory mystery: why the check was never sent

With the correct distance, the *shape* became the blocker:

| track | check sent? | result |
|---|---|---|
| symmetric accel/decel + 3px overshoot + y±1.5 | **no** | None |
| uniform deceleration, no overshoot | yes | false (wrong distance) |
| replayed real track | yes | **true** |

The "humanized" track — acceleration, overshoot, y-jitter — was rejected
*before the check request was even sent*. The overshoot and the large y-jitter
made the frontend drop the drag on mouseup.

A second trap: `check result=None` does **not** mean the check was not sent.
On success the page navigates immediately, and Playwright's response listener
dies with the context. Judge success by the *final state* (body length, URL),
not by a listener's return value.

## 7. The real trajectory: "fast sprint, slow fine-tune"

Analyzing the recorded 64-point drag by thirds:

| third | displacement | duration | speed |
|---|---|---|---|
| first (21 pts) | 84px | 166ms | **506 px/s** |
| middle (21 pts) | 27px | 167ms | 162 px/s |
| last (22 pts) | 14px | 469ms | **30 px/s** |

The human yanks the slider ~65% of the way in a third of the time, then
nudges 0-1px at a time near the gap. Four pauses (`dt > 30ms`): at indices 0
(46ms), 56 (74ms), 61 (50ms), 63 (178ms) — the last being "hold before
release". Y-noise is nearly zero: 4 of 64 points moved 1px, the rest 0.

Replay is `scale_to_distance` — normalize the recorded displacements to unit
distance and scale to the target, keeping the original timings. See
`examples/profile_slider_vendor.py` for the full sequence.

## 8. The hidden performance trap: how the image is downloaded

- In-page (browser) download of the background: **10-30s**.
- `ctx.request.get()` (direct API fetch): **~0.2s**.

The difference is not the bytes; it is that the `get` response's `token` has a
lifetime. A slow download stretches the get→check gap until the token expires,
which is exactly the "sometimes it fails for no reason" bug. **Download the
background via `ctx.request.get()` and keep OCR under ~1s.**

## 9. Final step: check -> verify

Two-stage confirmation:

- `check` — the frontend submits the drag, gets `result:true` + `validate`.
- `verify` — the site's *server* calls the vendor with `validate`; this call
  is not visible to the browser, so verify is confirmed only indirectly.

Evidence of verify passing: body length 108 → 29236, URL navigates to the
article page. A bonus: the bypass is **session-scoped for ~1 hour** — keep
fetching in the same session rather than re-solving per article.

## Results

1. `drag distance = OCR x1 + 10` (per-target calibrated).
2. Reference trajectory: 64 points, normalized by `sum(dx)=129`, shape
   "fast sprint, slow fine-tune" (full sequence in the profile).
3. Reusable library: `track`, `ocr`, `drag`, `capture`, `trace_recorder`,
   `probe`, `dom` — all site-agnostic, pure-logic parts tested.
4. Download the background with `ctx.request.get()`, not the page.

## Honest boundaries

- **Frontend-event simulation, not an algorithm-level break**: the vendor's
  frontend computes `validate`; we never forge it.
- The offset and trajectory are **snapshots calibrated against one target at
  one point in time**; re-calibrate per target.
- Gap localization depends on a **third-party OCR**; no self-hosted detector.
- `verify` is confirmed **indirectly** (page navigation), not captured.
- Only `track` and `capture` are unit-tested; the browser path needs a live
  authorized target.

## Retrospective

Four real turning points; the rest was trial-and-error around them:

1. **Lock the tool that is proven to work** (OCR), don't regress to the dead
   end (local detector).
2. **One manual drag as ground truth** beats a dozen blind tuning rounds — it
   surfaced both the offset and the trajectory shape at once.
3. **Judge by final state, not by an intermediate listener's return value** —
   otherwise `check None` and `-1.htm` both masquerade as failure.
4. **Remove the hidden variable** (image download time / token expiry) before
   trusting the loop.

For re-calibration: record a fresh human drag with `trace_recorder.py`, and
sweep the offset around `x1` (`+8/+10/+12`) to find which one returns
`result:true`. Full instructions live in the repository README and memory
notes.
