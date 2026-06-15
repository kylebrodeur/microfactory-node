"""Quick visual verification of the recording/CDP setup.

Takes a screenshot of the connected Chrome window to prove Playwright + CDP works.
"""
from __future__ import annotations

import argparse
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cdp-url", default="http://172.25.144.1:9222", help="Chrome CDP URL")
    ap.add_argument("--output", default="/tmp/microfactory_verify.png", help="screenshot path")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Python playwright not installed. Run: uv pip install playwright && uv run playwright install chromium")

    print(f"Connecting to {args.cdp_url} ...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(args.cdp_url)
        if browser.contexts:
            page = browser.contexts[0].pages[0] if browser.contexts[0].pages else browser.contexts[0].new_page()
        else:
            page = browser.new_page()
        page.bring_to_front()
        time.sleep(1)
        page.screenshot(path=args.output, full_page=True)
        browser.close()
    print(f"Screenshot saved: {args.output}")


if __name__ == "__main__":
    main()
