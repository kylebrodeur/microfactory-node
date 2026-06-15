"""Capture beat driver — drive the live app through the demo beats deterministically.

This does NOT record video itself. Use it alongside Cap desktop, or use
scripts/record-beat.sh to start Cap and drive one beat at a time. The script walks
the UI slowly with deliberate pauses while YOU (or cap-cli) capture the screen.

The UI tabs are LOAD · SLICE · PRINT · REVIEW. Selectors prefer stable IDs
over visible text wherever possible, so renames are less likely to break this
script than the previous text-only version.

One-time setup (local; not a Space/runtime dep):
    uv pip install playwright && uv run playwright install chromium

Run the app first in another terminal:
    make run                      # http://localhost:7860   (pre-warm one analyze!)

Then walk the beats (headed browser; record it with Cap):
    uv run python -m scripts.capture --beat all
    uv run python -m scripts.capture --beat 3            # load-bearing beat
    uv run python -m scripts.capture --beat benchy       # LOAD + Benchy quick-load
    uv run python -m scripts.capture --beat loop         # the learning loop

Options:
    --url      Space or local URL (default: https://node.microfactory.space)
    --slowmo   ms between Playwright actions (default 350)
    --pause    seconds between beats (default 1.5)
    --headless hide the browser (no recording)
"""

from __future__ import annotations

import argparse
import sys
import time


def _pill(page, value):
    """Click an LCARS pill. CSS uppercases the text, but the DOM keeps the raw
    value (part types are lowercase; materials are uppercase). Match the <label>
    by its real text, scoped to pill groups."""
    page.locator(".ce-pills label", has_text=value).first.click()


def _open_override(page):
    """Open the OVERRIDE ENVIRONMENT popup if it is not already open.
    Idempotent: checks the popup's visibility before toggling."""
    try:
        popup = page.locator("#ce-popup-override")
        if not popup.is_visible():
            page.locator("#ce-override").first.click()
            time.sleep(0.3)
    except Exception:
        pass


def _close_override(page):
    """Click the popup close button if it is open."""
    try:
        popup = page.locator("#ce-popup-override")
        if popup.is_visible():
            page.locator("#ce-popup-override .ce-popup-close").first.click()
            time.sleep(0.2)
    except Exception:
        pass


def _set_sensors(page, t, h):
    """Set ambient °C + humidity %RH inside the override popup."""
    nums = page.locator("#ce-popup-override .ce-num input")
    try:
        nums.nth(0).fill(str(t)); nums.nth(0).dispatch_event("change")
        nums.nth(1).fill(str(h)); nums.nth(1).dispatch_event("change")
    except Exception:
        pass


def _load_benchy(page, slow):
    """Shared helper: LOAD tab → quick-load Benchy."""
    page.get_by_role("tab", name="LOAD").click(); time.sleep(slow)
    page.locator("#ce-benchy").first.click()
    time.sleep(1.5)


def beat_load(page, slow):
    """Beat 3a — define the job in LOAD (empty start → quick-load a part +
    material; set deterministic environment for a repeatable, risk-relevant take)."""
    page.get_by_role("tab", name="LOAD").click(); time.sleep(slow)
    _open_override(page); _set_sensors(page, 28, 60)  # warm + humid → precedent-rich
    _close_override(page)
    _pill(page, "PLA"); time.sleep(slow)
    page.locator("#ce-benchy").first.click()
    time.sleep(2.0)                                   # part preview (3D model) settles


def beat_benchy(page, slow):
    """LOAD + the 3DBenchy quick-load (the recognizable hero part)."""
    page.get_by_role("tab", name="LOAD").click(); time.sleep(slow)
    page.locator("#ce-benchy").first.click()
    time.sleep(3.0)                                  # watch the hull preview settle


def beat_slice(page, slow):
    """Beat 3b — SLICE: auto-switch to SLICE, let the engineer's read land."""
    page.locator("#ce-run").first.click()
    time.sleep(5.0)                                  # reasoning + settings readout appear


def beat_second_opinion(page, slow):
    """The QA Inspector's pre-print critique on the SLICE page."""
    page.locator("input[type=radio][value='Second Opinion']").first.check()
    time.sleep(3.0)


def beat_scrub(page, slow):
    """Slide through the filled cross-section layers (on the SLICE page)."""
    sl = page.locator("input[type=range]").last
    for v in (8, 18, 30, 40):
        sl.fill(str(v)); sl.dispatch_event("input"); sl.dispatch_event("change")
        time.sleep(0.9)


def beat_placement(page, slow):
    """Plate-position beat — ABS in the corner: warp predicted + 'center it' suggestion."""
    page.get_by_role("tab", name="LOAD").click(); time.sleep(slow)
    _pill(page, "ABS")                 # high-shrink material
    _open_override(page)
    _pill(page, "corner")              # worst plate position
    _close_override(page)
    page.locator("#ce-benchy").first.click()
    time.sleep(slow)
    page.locator("#ce-run").first.click()
    time.sleep(5.0)                    # PLACEMENT risk + suggested alignment appear


def beat_print_single(page, slow):
    """Beat 4a — go to PRINT, run one print (deterministic) + inspector grade."""
    page.get_by_role("tab", name="PRINT").click(); time.sleep(slow)
    page.locator("#ce-print-run, #ce-print").first.click()
    time.sleep(3.0)


def beat_print_loop(page, slow):
    """Beat 4b — PRINT: run iterations, quality climbs fail->clean with inspector grades."""
    page.get_by_role("tab", name="PRINT").click(); time.sleep(slow)
    page.locator("#ce-print-run, #ce-print").first.click()
    time.sleep(5.0)                                  # the curve fills in


def beat_review(page, slow):
    """Beat 4c — REVIEW: the ledger where lessons accumulate + the run verdict."""
    page.get_by_role("tab", name="REVIEW").click()
    time.sleep(3.0)


BEATS = {
    "load": [beat_load],
    "benchy": [beat_benchy],
    "3": [beat_load, beat_slice],
    "scrub": [beat_load, beat_slice, beat_scrub],
    "second": [beat_load, beat_slice, beat_second_opinion],
    "placement": [beat_placement, beat_scrub],
    "4": [beat_print_single, beat_print_loop, beat_review],
    "loop": [beat_print_loop, beat_review],
    "review": [beat_review],
    "all": [beat_load, beat_slice, beat_second_opinion, beat_scrub,
            beat_placement, beat_print_single, beat_print_loop, beat_review],
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Walk the demo beats for screen capture.")
    ap.add_argument("--beat", default="all", choices=sorted(BEATS), help="which beat(s) to walk")
    ap.add_argument("--url", default="https://node.microfactory.space")
    ap.add_argument("--slowmo", type=int, default=350, help="ms between Playwright actions")
    ap.add_argument("--pause", type=float, default=1.5, help="seconds between beats")
    ap.add_argument("--headless", action="store_true", help="hide the browser (no recording)")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright not installed — run:  uv pip install playwright && uv run playwright install chromium")

    print(f"Walking beat '{args.beat}' against {args.url} — start your Cap recording now.")
    time.sleep(2.0)
    slow = args.slowmo / 1000.0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless, slow_mo=args.slowmo)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.goto(args.url + "/?__theme=dark", wait_until="domcontentloaded")
        time.sleep(2.5)
        for step in BEATS[args.beat]:
            print(f"  → {step.__name__}")
            step(page, slow)
            time.sleep(args.pause)
        print("done — stop the recording. (browser stays open 5s)")
        time.sleep(5.0)
        browser.close()


if __name__ == "__main__":
    main()
