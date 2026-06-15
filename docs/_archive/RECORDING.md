# Recording workflow (internal)

How we capture clean demo footage for the Microfactory Node Space. This doc is
for local/internal use; the public runbook points here for mechanics.

## Recommended setup: WSL + Windows Chrome + Cap Desktop Studio

Why this setup:
- The Space works best in Chrome's installed Gradio app / PWA mode (chromeless window).
- Cap Desktop Studio mode gives you the raw `.cap` project to edit before export.
- We do **not** auto-export from the CLI; exporting was brittle and produced the
  misleading pre-rendered `display.mp4` that had to be removed from the Space.

## One-liner

From WSL, inside `chief-engineer/`:

```bash
./record-studio.sh
```

Options:

```bash
./record-studio.sh --beat=3        # just the load-bearing beat
./record-studio.sh --beat=all      # full tour (default)
./record-studio.sh --pause=4       # longer pause between beats
```

What the script does:
1. Sources `~/projects/cap-cli-skill/setup.sh` so `cap` is available.
2. Discovers your Windows host IP from the WSL default gateway.
3. Launches Chrome in app mode at `https://node.microfactory.space/?__theme=dark`
   with remote debugging on port `9222`.
4. Runs `node scripts/record-studio.mjs` which uses **npm/pnpm-based Playwright**
   to drive the browser via CDP.

## Manual steps if you prefer

1. Source Cap CLI:

   ```bash
   source ~/projects/cap-cli-skill/setup.sh
   ```

2. Get Windows host IP:

   ```bash
   HOST_IP=$(ip route show | grep default | awk '{print $3}')
   echo $HOST_IP
   ```

3. Launch the chromeless Space window (Windows side):

   ```powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" `
     --app=https://node.microfactory.space/?__theme=dark `
     --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0
   ```

4. Run the studio driver from WSL:

   ```bash
   uv run python -m scripts.record --mode studio --cdp-url http://$HOST_IP:9222
   ```

## What the studio driver does

- Checks if `cap` is already recording.
- If not, starts a detached screen recording via `cap record start --screen <primary> --fps 60 --detach`.
- Connects **npm/pnpm-based Playwright** to your Chrome CDP window.
- Clicks **WARM UP** and waits ~35s for the ZeroGPU model to load.
- Navigates to the Space and drives the selected beats with generous waits so
  GPU inference, animations, and the quality curve all land cleanly on screen.
- Leaves the Cap recording running when done.

The Python driver (`uv run python -m scripts.record --mode studio`) is still
available, but it requires Python playwright installed in the uv venv. The Node
driver is the recommended path because it matches your npm/pnpm Playwright setup.

## After the run

Stop Cap in the Desktop app (or via CLI):

```bash
cap record stop
```

The raw `.cap` project is now in Cap Desktop Studio. Edit and export from there.

## Resetting demo state before a take

To get a clean compounding curve:

```bash
git checkout -- data/lessons.jsonl && rm -f data/policy.json
```

Or click **RESET TO BASELINE** in the UI.

## Modes reference

Recommended (npm/pnpm Playwright):

```bash
./record-studio.sh                              # full tour, raw .cap project
./record-studio.sh --beat=3 --pause=4          # single beat with longer waits
```

Python fallback (requires `uv pip install playwright` in the venv):

```bash
uv run python -m scripts.record --preflight-only
uv run python -m scripts.record --mode cues
uv run python -m scripts.record --mode manual
uv run python -m scripts.record --mode auto
uv run python -m scripts.record --mode studio --skip-playwright
```
