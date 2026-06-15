#!/usr/bin/env bash
# One-liner studio recording for WSL + Windows Chrome + Cap Desktop.
#
# This script:
#   1. Sources the cap-cli-skill so `cap` is available.
#   2. Discovers the Windows host IP from WSL's default gateway.
#   3. Launches Chrome in app mode pointed at https://node.microfactory.space
#      with remote debugging enabled (if not already running).
#   4. Runs the Node-based studio driver, which uses npm/pnpm-based Playwright,
#      starts a Cap screen recording if none is active, warms the GPU via the
#      WARM UP button, then drives the full demo. It leaves the raw .cap
#      project — no export.
#
# Usage:
#   ./record-studio.sh
#   ./record-studio.sh --beat=3
#   ./record-studio.sh --beat=placement --pause=4
#
# Prerequisites:
#   Chrome installed at C:\Program Files\Google\Chrome\Application\chrome.exe
#   Cap CLI set up via ~/projects/cap-cli-skill/setup.sh

set -euo pipefail

cd "$(dirname "$0")"

source ~/projects/cap-cli-skill/setup.sh 2>/dev/null || true

HOST_IP=$(ip route show | grep default | awk '{print $3}')
CDP_URL="http://${HOST_IP}:9222"
CHROME="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
SPACE="https://node.microfactory.space/?__theme=dark"

echo "Windows host IP: ${HOST_IP}"
echo "CDP URL: ${CDP_URL}"

# Screen resolution from Cap target; adjust if your display differs.
SCREEN_W=1707
SCREEN_H=1067

# Launch Chrome in app mode with CDP if CDP is not already alive
if ! curl -s "${CDP_URL}/json/version" >/dev/null 2>&1; then
    echo "Launching Chrome app window..."
    PROFILE_DIR="/tmp/chrome-studio-profile-$(date +%s)"
    mkdir -p "$PROFILE_DIR"
    nohup "${CHROME}" --app="${SPACE}" --remote-debugging-port=9222 \
        --remote-debugging-address=0.0.0.0 \
        --user-data-dir="$PROFILE_DIR" \
        --window-size=${SCREEN_W},${SCREEN_H} \
        --window-position=0,0 \
        --disable-session-crashed-bubble --no-first-run \
        --no-default-browser-check --disable-features=TranslateUI \
        >/tmp/chrome-studio.log 2>&1 &
    sleep 5
else
    echo "Chrome CDP already alive — reusing existing window"
fi

# Install Node deps if Playwright is not resolvable
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
    echo "Installing Playwright (pnpm/npm)..."
    if command -v pnpm &> /dev/null; then
        pnpm install
    else
        npm install
    fi
    npx playwright install chromium
fi

echo "Starting studio recording..."
CDP_URL="${CDP_URL}" node scripts/record-studio.cjs "$@"
