"""Recording preflight + integrated cap-cli + Playwright beat driver.

One command from chief-engineer/:
    uv run python -m scripts.record           # preflight → pre-warm → record → export
    uv run python -m scripts.record --preflight-only
    uv run python -m scripts.record --beat 3  # single beat for re-takes
    uv run python -m scripts.record --mode studio

Modes:
    manual   cap-cli start/stop/export + printed cues (you drive browser)
    auto     Playwright drives browser; cap-cli records screen; exports mp4
    cues     just printed cues — you handle Cap Desktop + browser
    studio   Playwright drives browser; checks/starts Cap CLI recording; leaves
             the raw .cap project (no export). Use this for Cap Desktop Studio.

Prerequisites (one-time):
    source ~/projects/cap-cli-skill/setup.sh   # defines cap() in your shell
    uv pip install playwright && uv run playwright install chromium
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

SPACE_URL = os.environ.get("CHIEF_ENGINEER_SPACE_URL", "https://node.microfactory.space")
CAP_SETUP_SCRIPT = os.path.expanduser("~/projects/cap-cli-skill/setup.sh")
CAP_CLI_FALLBACK = "/mnt/c/Users/kyleb/AppData/Local/Cap/cap-cli.exe"
CHROME_EXE = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
CDP_PORT = "9222"
SCREEN_ID = "65800"
CAP_START_TMP = "/tmp/cap-start-output.txt"
EXPORT_DIR_WIN = "D:\\workspace\\recordings"
EXPORT_DIR_WSL = "/mnt/d/workspace/recordings"
SLOWMO_DEFAULT = 400
CAP_FPS = "60"
EXPORT_QUALITY = "maximum"
EXPORT_RES = "1707x1067"

# How long to wait after the WARM UP button is clicked and after each heavy
# inference step so the ZeroGPU cold-start is captured cleanly.
WARMUP_WAIT = 35.0
INFERENCE_WAIT = 10.0

# ---------------------------------------------------------------------------
# cap cli helpers
# ---------------------------------------------------------------------------


def _cap_bin() -> str:
    """Return the shell command used to invoke cap.
    Prefer the user's sourced `cap` function/alias, then the Windows exe."""
    if shutil.which("cap"):
        return "cap"
    if Path(CAP_CLI_FALLBACK).exists():
        return CAP_CLI_FALLBACK
    return "cap"


def _cap(*args: str) -> subprocess.CompletedProcess:
    """Run a cap command. Use bash -c for `cap record start --detach` so the
    Windows child process doesn't keep our Python process hanging."""
    bin_ = _cap_bin()
    if "record" in args and "start" in args and "--detach" in args:
        cmd = f"nohup {bin_} " + " ".join(args) + f" > {CAP_START_TMP} 2>&1 &"
        subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=10)
        time.sleep(1.5)
        try:
            with open(CAP_START_TMP) as f:
                out = f.read()
        except FileNotFoundError:
            out = ""
        return subprocess.CompletedProcess(
            args=[bin_] + list(args),
            returncode=0 if out else 1,
            stdout=out,
            stderr="",
        )
    return subprocess.run([bin_] + list(args), capture_output=True, text=True, timeout=120)


def _cap_json(*args: str) -> dict | list | None:
    """Run cap --json and return parsed JSON."""
    r = _cap(*args)
    if r.returncode != 0:
        print(f"  ✗ cap {' '.join(args)} failed: {r.stderr.strip()}")
        return None
    out = r.stdout.strip()
    if not out:
        return None
    lines = out.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass
    depth = 0
    buf = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not started:
            if stripped.startswith("{") or stripped.startswith("["):
                started = True
        if started:
            buf.append(line)
            depth += stripped.count("{") + stripped.count("[") - stripped.count("}") - stripped.count("]")
            if depth == 0 and buf:
                try:
                    return json.loads("\n".join(buf))
                except json.JSONDecodeError:
                    return None
    return None


def _cap_is_recording() -> bool:
    """Ask cap whether a recording is currently in progress."""
    status = _cap_json("status", "--json")
    if isinstance(status, dict):
        if status.get("recording") or status.get("status") == "recording":
            return True
    # fallback: list recent recordings and look for a running one
    try:
        recs = _cap_json("list", "--json")
        if isinstance(recs, dict) and "recordings" in recs:
            for r in recs["recordings"]:
                if isinstance(r, dict) and r.get("state") in ("recording", "in-progress"):
                    return True
    except Exception:
        pass
    return False


def _cap_start_recording() -> dict | None:
    """Start a detached Cap screen recording if none is running."""
    if _cap_is_recording():
        print("  ✓ Cap is already recording")
        return None
    screen_id = _get_screen_id()
    print(f"  starting Cap recording (screen {screen_id})...")
    started = _cap_json("record", "start", "--screen", screen_id, "--fps", CAP_FPS, "--detach", "--json")
    if not started:
        print("  ✗ failed to start Cap recording")
        return None
    print(f"  ✓ Cap recording started  ({started.get('recordingId', '?')})")
    return started


def _cap_stop_recording(rec_id: str | None = None) -> dict | None:
    """Stop the current Cap recording. Returns the recording metadata."""
    print("  stopping Cap recording...")
    if rec_id:
        stopped = _cap_json("record", "stop", "--id", rec_id, "--json")
    else:
        stopped = _cap_json("record", "stop", "--json")
    if stopped:
        print("  ✓ Cap recording stopped")
    else:
        print("  ⚠ Cap stop may have failed")
    return stopped


# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------


def preflight(url: str = SPACE_URL, require_playwright: bool = True) -> bool:
    """Check everything is ready before recording."""
    print("=== RECORDING PREFLIGHT ===\n")
    gates = []

    if shutil.which("cap") or Path(CAP_CLI_FALLBACK).exists():
        print(f"  ✓ G1 cap-cli found  ({_cap_bin()})")
        gates.append(True)
    else:
        print("  ✗ G1 cap-cli NOT ready — source ~/projects/cap-cli-skill/setup.sh")
        gates.append(False)

    targets = _cap_json("targets", "--json")
    screens = targets.get("screens", []) if isinstance(targets, dict) else []
    if screens:
        print(f"  ✓ G2 screen target  ({screens[0].get('name')} @ {screens[0].get('fps')}fps)")
        gates.append(True)
    else:
        print("  ✗ G2 no screen targets found")
        gates.append(False)

    # Playwright can be installed via uv OR via npm/pnpm globally.
    # Check the Python import first; if missing, try the system `playwright` CLI.
    have_python_pw = False
    try:
        import playwright  # noqa: F401
        have_python_pw = True
    except ImportError:
        pass
    have_cli_pw = shutil.which("playwright") is not None
    if have_python_pw or have_cli_pw:
        print(f"  ✓ G3 playwright available  (python={have_python_pw}, cli={have_cli_pw})")
        gates.append(True)
    else:
        if require_playwright:
            print("  ✗ G3 playwright missing — uv pip install playwright && uv run playwright install chromium")
            gates.append(False)
        else:
            print("  ⚠ G3 playwright missing, but --skip-playwright set — continuing")
            gates.append(True)

    # HF Spaces returns 403 on bare HEAD. Try GET with a browser user-agent and
    # treat any response (even 403) as "reachable" because the Space is alive.
    try:
        import urllib.request
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0"})
        try:
            urllib.request.urlopen(req, timeout=15)
            print(f"  ✓ G4 URL reachable  ({url})")
        except urllib.error.HTTPError as e:
            if e.code in (403, 401, 503):
                print(f"  ✓ G4 URL reachable (HTTP {e.code} is an HF block, not a real failure)  ({url})")
            else:
                raise
        gates.append(True)
    except Exception as e:
        print(f"  ✗ G4 URL unreachable  ({e})")
        gates.append(False)

    Path(EXPORT_DIR_WSL).mkdir(parents=True, exist_ok=True)
    print(f"  ✓ G5 output dir  ({EXPORT_DIR_WSL})")
    gates.append(True)

    passed = all(gates)
    print(f"\n  Preflight: {'✓ ALL GATES PASS' if passed else '✗ SOME GATES FAILED'}")
    return passed


# ---------------------------------------------------------------------------
# chrome + cdp
# ---------------------------------------------------------------------------


def _windows_host_ip() -> str:
    try:
        r = subprocess.run(
            ["bash", "-c", "ip route show | grep default | awk '{print $3}'"],
            capture_output=True, text=True, timeout=5,
        )
        ip = r.stdout.strip()
        if ip:
            return ip
    except Exception:
        pass
    return "127.0.0.1"


def _get_screen_id() -> str:
    targets = _cap_json("targets", "--json")
    screens = targets.get("screens", []) if isinstance(targets, dict) else []
    for s in screens:
        if s.get("primary"):
            return s["id"]
    if screens:
        return screens[0]["id"]
    return SCREEN_ID


def _launch_chrome():
    import urllib.request
    host_ip = _windows_host_ip()
    try:
        urllib.request.urlopen(f"http://{host_ip}:{CDP_PORT}/json/version", timeout=3)
        print("  Chrome CDP already alive — reusing")
        return
    except Exception:
        pass
    import uuid
    profile_dir = f"/tmp/chrome-cdp-profile-{uuid.uuid4().hex[:8]}"
    cmd = (f'nohup "{CHROME_EXE}" --remote-debugging-port={CDP_PORT} '
           f'--remote-debugging-address=0.0.0.0 --user-data-dir={profile_dir} '
           f'--disable-session-crashed-bubble --no-first-run --no-default-browser-check '
           f'--disable-features=TranslateUI --start-maximized about:blank > /tmp/chrome-cdp.log 2>&1 &')
    subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=10)
    time.sleep(4)


def _dismiss_popups(page):
    for sel in ('button:has-text("Restore")', 'cr-button:has-text("Restore")',
                'button:has-text("Accept")', '[aria-label="Close"]', 'button:has-text("Close")'):
        try:
            page.locator(sel).first.click(timeout=1500)
        except Exception:
            pass


def _hide_hf_chrome(page):
    page.add_style_tag(content="""
        #huggingface-space-header { display: none !important; }
        div[class*="cookie"], div[class*="consent"], div[class*="banner"] { display: none !important; }
    """)
    try:
        collapse = page.locator('#space-header__collapse')
        if collapse.is_visible():
            collapse.click()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# beat helpers
# ---------------------------------------------------------------------------


def _pill(page, value):
    page.locator(".ce-pills label", has_text=value).first.click()


def _open_override(page):
    try:
        popup = page.locator("#ce-popup-override")
        if not popup.is_visible():
            page.locator("#ce-override").first.click()
            time.sleep(0.3)
    except Exception:
        pass


def _close_override(page):
    try:
        popup = page.locator("#ce-popup-override")
        if popup.is_visible():
            page.locator("#ce-popup-override .ce-popup-close").first.click()
            time.sleep(0.2)
    except Exception:
        pass


def _set_sensors(page, t, h):
    nums = page.locator("#ce-popup-override .ce-num input")
    try:
        nums.nth(0).fill(str(t)); nums.nth(0).dispatch_event("change")
        nums.nth(1).fill(str(h)); nums.nth(1).dispatch_event("change")
    except Exception:
        pass


def _warm_model(page, url: str):
    """Click the WARM UP button and wait for the GPU model to load."""
    print("  warming the model (WARM UP)...")
    page.goto(url + "/?__theme=dark", wait_until="domcontentloaded")
    time.sleep(2.0)
    _dismiss_popups(page)
    _hide_hf_chrome(page)
    try:
        page.locator("#ce-warm").first.click(timeout=5000)
    except Exception:
        print("  ⚠ WARM UP button not found — proceeding anyway")
    print(f"  waiting {WARMUP_WAIT:.0f}s for model load...")
    time.sleep(WARMUP_WAIT)
    print("  warm-up complete")


# ---------------------------------------------------------------------------
# beats
# ---------------------------------------------------------------------------


def beat_load(page, slow):
    """LOAD: quick-load Benchy, set material + environment."""
    page.get_by_role("tab", name="LOAD").click(); time.sleep(slow)
    _open_override(page); _set_sensors(page, 28, 60); _close_override(page)
    _pill(page, "PLA"); time.sleep(slow)
    page.locator("#ce-benchy").first.click()
    time.sleep(2.5)


def beat_slice(page, slow):
    """SLICE: reasoning + settings readout."""
    page.locator("#ce-run").first.click()
    time.sleep(INFERENCE_WAIT)
    print("  waiting for reasoning to land...")
    time.sleep(4.0)


def beat_second_opinion(page, slow):
    """Second Opinion panel."""
    page.locator("input[type=radio][value='Second Opinion']").first.check()
    time.sleep(5.0)


def beat_scrub(page, slow):
    """Scrub through layers."""
    sl = page.locator("input[type=range]").last
    for v in (8, 18, 30, 40):
        sl.fill(str(v)); sl.dispatch_event("input"); sl.dispatch_event("change")
        time.sleep(1.2)


def beat_placement(page, slow):
    """ABS in corner: warp predicted."""
    page.get_by_role("tab", name="LOAD").click(); time.sleep(slow)
    _pill(page, "ABS")
    _open_override(page)
    _pill(page, "corner")
    _close_override(page)
    page.locator("#ce-benchy").first.click()
    time.sleep(slow)
    page.locator("#ce-run").first.click()
    time.sleep(INFERENCE_WAIT)
    print("  waiting for placement reasoning...")
    time.sleep(4.0)


def beat_climbing_job(page, slow):
    """PETG @ 30°C/65%: different conditions."""
    page.get_by_role("tab", name="LOAD").click(); time.sleep(slow)
    _open_override(page); _set_sensors(page, 30, 65); _close_override(page)
    _pill(page, "PETG")
    page.locator("#ce-benchy").first.click()
    time.sleep(2.5)
    page.locator("#ce-run").first.click()
    time.sleep(INFERENCE_WAIT)
    print("  waiting for climbing-job reasoning...")
    time.sleep(4.0)


def beat_print_loop(page, slow):
    """PRINT: run iterations, quality climbs."""
    page.get_by_role("tab", name="PRINT").click(); time.sleep(slow)
    page.locator("#ce-print-run, #ce-print").first.click()
    print("  waiting for print simulation + curve...")
    time.sleep(10.0)


def beat_review(page, slow):
    """REVIEW: ledger + verdict."""
    page.get_by_role("tab", name="REVIEW").click()
    time.sleep(5.0)


BEATS = {
    "3": [beat_load, beat_slice],
    "scrub": [beat_load, beat_slice, beat_scrub],
    "second": [beat_load, beat_slice, beat_second_opinion],
    "placement": [beat_placement],
    "climb": [beat_climbing_job, beat_print_loop, beat_review],
    "loop": [beat_print_loop, beat_review],
    "all": [
        beat_load, beat_slice, beat_second_opinion, beat_scrub,
        beat_placement, beat_climbing_job, beat_print_loop, beat_review,
    ],
}


# ---------------------------------------------------------------------------
# manual cues
# ---------------------------------------------------------------------------

MANUAL_BEATS: dict[str, list[dict]] = {
    "3": [
        {"cue": "LOAD → QUICK-LOAD BENCHY → PLA → SLICE",
         "say": "It recalls the closest prior jobs and says what transfers — before anything prints.",
         "wait": 10},
    ],
    "second": [
        {"cue": "LOAD → BENCHY → PLA → SLICE → toggle SECOND OPINION",
         "say": "A separate, skeptical reviewer grades the plan — and can hold the print.",
         "wait": 10},
    ],
    "scrub": [
        {"cue": "LOAD → BENCHY → PLA → SLICE → scrub the LAYER slider",
         "say": "Real cross-sections of this part, layer by layer.",
         "wait": 10},
    ],
    "placement": [
        {"cue": "LOAD → ABS → OVERRIDE → corner → BENCHY → SLICE",
         "say": "It even knows where on the bed matters — corner ABS will warp; center it.",
         "wait": 12},
    ],
    "climb": [
        {"cue": "LOAD → PETG → OVERRIDE 30°C / 65% → BENCHY → SLICE",
         "say": "Different conditions, different call — it's reasoning, not a lookup.",
         "wait": 10},
        {"cue": "PRINT → PRINT → watch quality climb",
         "say": "Each outcome makes the next print better — the Inspector grades it, the ledger grows.",
         "wait": 12},
        {"cue": "REVIEW → show ledger + verdict",
         "say": "Knowledge compounds instead of disappearing.",
         "wait": 5},
    ],
    "all": [
        {"cue": "LOAD → BENCHY → PLA → SLICE",
         "say": "I tell it the part, the material, and the room — it figures out what kind of part on its own.",
         "wait": 12},
        {"cue": "Point at THE READ + Spine line",
         "say": "The model proposes; deterministic code vetoes anything unsafe.",
         "wait": 5},
        {"cue": "Toggle SECOND OPINION → read Inspector card",
         "say": "A separate reviewer grades the plan. The engineer never marks its own homework.",
         "wait": 8},
        {"cue": "Scrub the LAYER slider",
         "say": "Real cross-sections of this part, layer by layer.",
         "wait": 8},
        {"cue": "LOAD → ABS → OVERRIDE → corner → BENCHY → SLICE",
         "say": "It even knows where on the bed matters — corner ABS will warp; center it.",
         "wait": 12},
        {"cue": "LOAD → PETG → OVERRIDE 30°C / 65% → BENCHY → SLICE",
         "say": "Different conditions, different call — it's reasoning, not a lookup.",
         "wait": 10},
        {"cue": "PRINT → PRINT → watch quality curve climb",
         "say": "Each outcome makes the next print better — the Inspector grades every run, the ledger grows.",
         "wait": 14},
        {"cue": "REVIEW → ledger + verdict",
         "say": "Knowledge built over a lifetime, lost in an afternoon — and the opposite of that.",
         "wait": 6},
    ],
}


# ---------------------------------------------------------------------------
# recording modes
# ---------------------------------------------------------------------------


def record_manual(beat_name: str, url: str = SPACE_URL, no_cap: bool = False) -> Path | None:
    """Printed cues + optional cap-cli start/stop/export."""
    print(f"\n=== RECORD (manual): beat '{beat_name}' ===\n")
    rec = None
    cap_path = None

    if not no_cap:
        rec = _cap_start_recording()
        if not rec:
            return None
        cap_path = rec.get("path")
    else:
        print("  🎬 Start your Cap desktop recording NOW.")
        time.sleep(2)

    beats = MANUAL_BEATS.get(beat_name, MANUAL_BEATS["all"])
    print(f"\n  Open the Space:\n  {url}/?__theme=dark\n")
    for i, b in enumerate(beats):
        print(f"  ── BEAT {i+1}/{len(beats)} ──")
        print(f"  CLICK: {b['cue']}")
        print(f"  SAY:   {b['say']}")
        for remaining in range(b["wait"], 0, -1):
            print(f"  ⏳ {remaining}s ", end="\r")
            time.sleep(1)
        print(f"  ✓ done{' ' * 20}")
        if i < len(beats) - 1:
            print("  ⏸  next beat in 3s...")
            time.sleep(3)

    print("\n  🎬 beats complete — hold closing shot for 5s...")
    time.sleep(5)

    if no_cap:
        print("  🛑 Stop your Cap desktop recording now.")
        return None

    stopped = _cap_stop_recording(rec.get("recordingId") if rec else None)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_win = f"{EXPORT_DIR_WIN}\\demo-{beat_name}-{ts}.mp4"
    print(f"  exporting to {out_win} ...")
    export_result = _cap("export", cap_path or "", "--output", out_win,
                         "--quality", EXPORT_QUALITY, "--resolution", EXPORT_RES, "--json")
    if "Completed" in export_result.stdout or "Progress" in export_result.stdout:
        print(f"  ✓ exported → {out_win}")
        return Path(EXPORT_DIR_WSL) / f"demo-{beat_name}-{ts}.mp4"
    print(f"  ✗ export may have failed: {export_result.stderr.strip()}")
    return None


def record_auto(beat_name: str, slowmo: int, pause: float, url: str = SPACE_URL,
                 cdp_url: str | None = None) -> Path | None:
    """Auto mode: Playwright drives browser; cap-cli records + exports."""
    print(f"\n=== RECORD (auto): beat '{beat_name}' ===\n")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ✗ playwright not installed")
        return None

    rec = _cap_start_recording()
    if not rec:
        return None
    cap_path = rec.get("path")
    rec_id = rec.get("recordingId")

    slow = slowmo / 1000.0
    with sync_playwright() as p:
        if cdp_url:
            print(f"  connecting to existing Chrome CDP at {cdp_url}...")
            browser = p.chromium.connect_over_cdp(cdp_url)
        else:
            print("  launching Chrome (Windows) with remote debugging...")
            _launch_chrome()
            host_ip = _windows_host_ip()
            print(f"  connecting to Chrome CDP at {host_ip}:{CDP_PORT}...")
            browser = p.chromium.connect_over_cdp(f"http://{host_ip}:{CDP_PORT}")

        if browser.contexts:
            page = browser.contexts[0].pages[0] if browser.contexts[0].pages else browser.contexts[0].new_page()
        else:
            page = browser.new_page()
        page.set_viewport_size({"width": 1707, "height": 1067})

        if not cdp_url:
            page.keyboard.press("F11")
            time.sleep(0.5)
            time.sleep(1.0)
            _dismiss_popups(page)

        _warm_model(page, url)

        print("  navigating to Space for recording take...")
        page.goto(url + "/?__theme=dark", wait_until="domcontentloaded")
        time.sleep(2.0)
        _dismiss_popups(page)
        _hide_hf_chrome(page)
        time.sleep(1.0)

        steps = BEATS[beat_name]
        for i, step in enumerate(steps):
            print(f"  [{i+1}/{len(steps)}] {step.__name__}")
            step(page, slow)
            time.sleep(pause)

        print("  beats complete — holding 3s for closing shot...")
        time.sleep(3.0)
        browser.close()

    _cap_stop_recording(rec_id)
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_win = f"{EXPORT_DIR_WIN}\\demo-{beat_name}-{ts}.mp4"
    print(f"  exporting to {out_win} ...")
    export_result = _cap("export", cap_path or "", "--output", out_win,
                         "--quality", EXPORT_QUALITY, "--resolution", EXPORT_RES, "--json")
    if "Completed" in export_result.stdout or "Progress" in export_result.stdout:
        print(f"  ✓ exported → {out_win}")
        return Path(EXPORT_DIR_WSL) / f"demo-{beat_name}-{ts}.mp4"
    print(f"  ✗ export may have failed: {export_result.stderr.strip()}")
    return None


def record_studio(beat_name: str, slowmo: int, pause: float, url: str = SPACE_URL,
                  cdp_url: str | None = None) -> dict | None:
    """Studio mode: Playwright drives the app; cap-cli starts a recording if
    one is not already running; beats are executed with generous waits so the
    GPU inference + UI animations land cleanly. Does NOT export — leaves the
    raw .cap project for Cap Desktop Studio."""
    print(f"\n=== RECORD (studio): beat '{beat_name}' ===\n")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ✗ playwright not installed")
        return None

    rec = _cap_start_recording()
    if not rec and not _cap_is_recording():
        print("  ✗ could not confirm an active Cap recording")
        return None
    rec_id = rec.get("recordingId") if rec else None

    slow = slowmo / 1000.0
    with sync_playwright() as p:
        if cdp_url:
            print(f"  connecting to existing Chrome CDP at {cdp_url}...")
            browser = p.chromium.connect_over_cdp(cdp_url)
        else:
            print("  launching Chrome (Windows) with remote debugging...")
            _launch_chrome()
            host_ip = _windows_host_ip()
            print(f"  connecting to Chrome CDP at {host_ip}:{CDP_PORT}...")
            browser = p.chromium.connect_over_cdp(f"http://{host_ip}:{CDP_PORT}")

        if browser.contexts:
            page = browser.contexts[0].pages[0] if browser.contexts[0].pages else browser.contexts[0].new_page()
        else:
            page = browser.new_page()
        page.set_viewport_size({"width": 1707, "height": 1067})

        if not cdp_url:
            page.keyboard.press("F11")
            time.sleep(0.5)
            time.sleep(1.0)
            _dismiss_popups(page)

        _warm_model(page, url)

        print("  navigating to Space for recording take...")
        page.goto(url + "/?__theme=dark", wait_until="domcontentloaded")
        time.sleep(2.0)
        _dismiss_popups(page)
        _hide_hf_chrome(page)
        time.sleep(1.0)

        steps = BEATS[beat_name]
        for i, step in enumerate(steps):
            print(f"  [{i+1}/{len(steps)}] {step.__name__}")
            step(page, slow)
            print(f"  pausing {pause:.1f}s between beats...")
            time.sleep(pause)

        print("  beats complete — holding 4s for closing shot...")
        time.sleep(4.0)
        browser.close()

    print("\n=== STUDIO MODE DONE ===")
    print("  Cap is still recording. Stop it manually in Cap Desktop, or run:")
    print(f"    cap record stop{' --id ' + rec_id if rec_id else ''}")
    print("  The raw .cap project can now be edited/exported from Cap Desktop Studio.")
    return rec


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="Recording preflight + cap-cli + beat driver")
    ap.add_argument("--beat", default="all", choices=sorted(MANUAL_BEATS),
                    help="which beat(s) to record (default: all)")
    ap.add_argument("--mode", default="manual", choices=["manual", "auto", "cues", "studio"],
                    help="manual=cap CLI+export+cues; auto=Playwright+cap export; cues=cues only; studio=Playwright+cap raw project")
    ap.add_argument("--preflight-only", action="store_true", help="run preflight checks and exit")
    ap.add_argument("--skip-playwright", action="store_true",
                    help="allow preflight to pass even if Python playwright is not installed (e.g. npm/pnpm playwright)")
    ap.add_argument("--slowmo", type=int, default=SLOWMO_DEFAULT, help="ms between Playwright actions")
    ap.add_argument("--pause", type=float, default=3.0, help="seconds between beats (auto/studio only)")
    ap.add_argument("--cdp-url", default=None, help="attach to existing Chrome CDP endpoint")
    ap.add_argument("--url", default=None, help="Space URL (default: node.microfactory.space)")
    args = ap.parse_args()

    url = args.url or SPACE_URL

    if not preflight(url, require_playwright=not args.skip_playwright):
        sys.exit(1)

    if args.preflight_only:
        print("\nPreflight only — exiting.")
        return

    if args.mode in ("auto", "studio"):
        try:
            import playwright  # noqa: F401
        except ImportError:
            print("\n✗ Python playwright is required for auto/studio modes.")
            print("  Install with: uv pip install playwright && uv run playwright install chromium")
            print("  Or use --mode cues and drive the browser manually.")
            sys.exit(1)

    if args.mode == "auto":
        result = record_auto(args.beat, args.slowmo, args.pause, url, cdp_url=args.cdp_url)
    elif args.mode == "studio":
        result = record_studio(args.beat, args.slowmo, args.pause, url, cdp_url=args.cdp_url)
    elif args.mode == "cues":
        result = record_manual(args.beat, url, no_cap=True)
    else:
        result = record_manual(args.beat, url)

    if result:
        print(f"\n✓ DONE — {result}")
    else:
        print("\n✗ Recording failed — check cap + Space logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
