"""Deploy / record preflight — is the app ready to ship to the Space and record?

Distinct from `scripts/preflight.py` (which gates the live *model* on the real
stack). This one gates *deployment + recording readiness* and runs fully offline:

  • local build is sound (imports, builds the UI, core tests pass, no errors)
  • every file the Space needs is present + the README frontmatter is valid
  • the prompt won't regress (reference block is lean, ledger is the clean baseline)
  • the credentials/tooling to actually push exist — and if not, says exactly what
    to set and where (this remote session does NOT carry HF_TOKEN by default)
  • (only if a token is present) the live Space exists and what's deployed

GO  → safe to `hf upload` + reboot + record.   Run:  make deploy-check
"""

from __future__ import annotations

import json
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SPACE = "build-small-hackathon/microfactory-lab"
FIELD_LOG_DATASET = "build-small-hackathon/chief-engineer-field-log"
# Uploaded to the Space = everything EXCEPT these (keeps learn/ + assets/ + data/*.jsonl,
# which the app imports/needs; drops docs, spikes, secrets, caches, runtime/transient files).
# Public-facing learn/finetune docs that stay on the Space: README.md, MODEL_CARD*.md,
# SERVING.md, OLLAMA_PUBLISHING.md. Internal session/budget/iteration logs stay in the
# GitHub repo but are kept out of the Space.
SPACE_IGNORE = [
    # Docs are internal by default, but two reference docs are public-facing.
    "docs/**",
    "!docs/reference/DEPLOYMENT.md",
    "!docs/reference/SIMULATION.md",
    "spike/**", "field_logs/**", "deliberation_logs/**", ".venv/**", "node_modules/**",
    "recordings/**", "**/__pycache__/**", "**/*.pyc", ".git/**", ".gitignore", ".env", ".agents/**",
    ".codeboarding/**", ".codeboardingignore", "data/policy.json", "data/_generated.glb",
    "data/_vprint.gif", "uv.lock", ".pytest_cache/**", "*.cap/**",
    # Internal finetune workpapers kept internal.
    "learn/finetune/REPORT.md",
    "learn/finetune/REPORT_v1.md",
]
_fail: list[str] = []
_warn: list[str] = []


def ok(gate: str, detail: str = "") -> None:
    print(f"🟢 {gate}{' — ' + detail if detail else ''}")


def warn(gate: str, detail: str) -> None:
    _warn.append(gate)
    print(f"🟡 {gate} — {detail}")


def fail(gate: str, detail: str) -> None:
    _fail.append(gate)
    print(f"🔴 {gate} — {detail}")


# ── D1 · local build is sound ────────────────────────────────────────────────
def d1_build() -> None:
    try:
        import app  # noqa: F401  (also exercises the whole import graph)
        if type(getattr(app, "demo", None)).__name__ != "Blocks":
            fail("D1 build", "app.demo is not a Gradio Blocks — build() did not run")
            return
        ok("D1 build", "app imports + builds the UI (Studio→Build→Print→Review)")
    except Exception as e:  # noqa: BLE001
        fail("D1 build", f"import/build error: {e!r}")


def d1b_tests() -> None:
    r = subprocess.run([sys.executable, str(ROOT / "test_core.py")],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0 and "ALL CORE TESTS PASSED" in (r.stdout + r.stderr):
        ok("D1 tests", "core tests pass (offline)")
    else:
        fail("D1 tests", f"test_core.py failed (rc={r.returncode}); run `make test`")


# ── D2 · everything the Space needs is present ───────────────────────────────
def d2_files() -> None:
    required = ["app.py", "README.md", "requirements.txt", "core", "ingest", "sim",
                "scripts", "learn", "data/seed_lessons.jsonl", "data/references.jsonl",
                "data/lessons.jsonl"]
    missing = [p for p in required if not (ROOT / p).exists()]
    if missing:
        fail("D2 files", f"missing for the Space: {', '.join(missing)}")
    else:
        ok("D2 files", "all app + data files present")
    if not (ROOT / "assets" / "benchy.glb").exists():
        warn("D2 assets", "assets/benchy.glb missing — the hero quick-load won't render")


# ── D3 · README frontmatter the Space build reads ────────────────────────────
def d3_frontmatter() -> None:
    txt = (ROOT / "README.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", txt, re.S)
    if not m:
        fail("D3 README", "no YAML frontmatter block")
        return
    fm = m.group(1)
    need = {"sdk": "gradio", "app_file": "app.py"}
    for k, v in need.items():
        if not re.search(rf"^{k}:\s*{re.escape(v)}\s*$", fm, re.M):
            fail("D3 README", f"frontmatter `{k}: {v}` missing/wrong")
            return
    if not re.search(r"^sdk_version:\s*\S+", fm, re.M):
        fail("D3 README", "sdk_version missing")
        return
    sd = re.search(r"^short_description:\s*(.+)$", fm, re.M)
    if not sd:
        warn("D3 README", "no short_description")
    elif len(sd.group(1).strip().strip('"')) > 60:
        fail("D3 README", f"short_description >60 chars ({len(sd.group(1).strip())}) — upload will reject")
    else:
        ok("D3 README", "frontmatter valid (sdk/app_file/sdk_version/short_description)")


# ── D4 · requirements carry the Space (zerogpu) deps ─────────────────────────
def d4_requirements() -> None:
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    needed = ["gradio", "spaces", "torch", "transformers", "trimesh", "shapely", "pydantic"]
    missing = [p for p in needed if p not in req]
    if missing:
        fail("D4 requirements", f"missing pins: {', '.join(missing)} (Space build/zerogpu needs them)")
    else:
        ok("D4 requirements", "core + zerogpu deps inlined")


# ── D5 · the prompt won't regress (lean reference block) ─────────────────────
def d5_reference_block() -> None:
    try:
        from ingest.distill import reference_block
        worst = max((len(reference_block(m)) for m in ("PLA", "PETG", "ABS", "TPU")), default=0)
        if worst == 0:
            warn("D5 reference", "reference_block returned nothing — references not loaded?")
        elif worst > 12:
            fail("D5 reference", f"reference block is {worst} lines/material — prompt flood regression")
        else:
            ok("D5 reference", f"lean ({worst} lines/material max)")
    except Exception as e:  # noqa: BLE001
        fail("D5 reference", f"reference_block error: {e!r}")


# ── D6 · the deployed ledger is the clean baseline (no demo junk) ────────────
def d6_ledger() -> None:
    srcs: dict[str, int] = {}
    for line in (ROOT / "data" / "lessons.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                srcs[json.loads(line).get("source", "?")] = srcs.get(json.loads(line).get("source", "?"), 0) + 1
            except Exception:
                continue
    runtime = srcs.get("earned", 0) + srcs.get("sim", 0)
    summary = ", ".join(f"{k}:{v}" for k, v in sorted(srcs.items()))
    if runtime:
        warn("D6 ledger", f"{runtime} runtime lesson(s) in the ledger ({summary}) — "
                          "reset before upload: git checkout -- data/lessons.jsonl")
    else:
        ok("D6 ledger", f"clean baseline ({summary})")


# ── D7 · data integrity (valid JSONL, enums) ─────────────────────────────────
def d7_data() -> None:
    try:
        from core.models import MATERIALS, OUTCOMES
        bad = 0
        for line in (ROOT / "data" / "references.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if not {"material", "param", "value", "source"} <= set(r):
                    bad += 1
        obs = ROOT / "sim" / "calibration" / "observations.modal.jsonl"
        obad = sum(1 for l in obs.read_text().splitlines()
                   if l.strip() and json.loads(l).get("outcome") not in OUTCOMES) if obs.exists() else 0
        if bad or obad:
            warn("D7 data", f"{bad} malformed ref rows, {obad} bad-outcome obs rows")
        else:
            ok("D7 data", "references + calibration obs well-formed")
    except Exception as e:  # noqa: BLE001
        warn("D7 data", f"could not validate: {e!r}")


# ── D8 · credentials + tooling to actually deploy ────────────────────────────
def d8_credentials() -> None:
    has_hf_cli = shutil.which("hf") is not None
    token = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
             or os.environ.get("HUGGINGFACE_TOKEN"))
    whoami = None
    if has_hf_cli:
        r = subprocess.run(["hf", "auth", "whoami"], capture_output=True, text=True)
        if r.returncode == 0 and "Not logged in" not in r.stdout:
            whoami = r.stdout.strip().splitlines()[0] if r.stdout.strip() else "ok"
    if not has_hf_cli:
        fail("D8 hf-cli", "`hf` not installed — `uv pip install -U huggingface_hub`")
    if token or whoami:
        ok("D8 hf-auth", f"authenticated ({'token env' if token else 'hf login: ' + str(whoami)})")
    else:
        warn("D8 hf-auth", "NO HF credentials in this session. To deploy: run the `hf upload` "
                           "from a machine where you've run `hf auth login`, OR set HF_TOKEN "
                           "in the environment (HF write token, member of build-small-hackathon).")
    return bool(token or whoami)


# ── D9 · (token only) what's live on the Space right now ─────────────────────
def d9_space(authed: bool) -> None:
    if not authed:
        warn("D9 space", "skipped — no credentials to query the live Space")
        return
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        rt = api.get_space_runtime(SPACE)
        files = api.list_repo_files(SPACE, repo_type="space")
        has_core = "app.py" in files and any(f.startswith("core/") for f in files)
        stage = getattr(rt, "stage", "?")
        ok("D9 space", f"reachable · stage={stage} · app.py+core present={has_core} · {len(files)} files")
        if not has_core:
            warn("D9 space", "Space is missing app.py/core — likely the pre-restructure build; push the update")
    except Exception as e:  # noqa: BLE001
        warn("D9 space", f"could not query Space: {e!r}")


# ── D10 · the field-log dataset is set + reachable (Sharing-is-Caring / all-runs) ──
def d10_dataset(authed: bool) -> None:
    if not authed:
        warn("D10 dataset", "skipped — no credentials to verify the field-log dataset")
        return
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        if api.repo_exists(FIELD_LOG_DATASET, repo_type="dataset"):
            files = api.list_repo_files(FIELD_LOG_DATASET, repo_type="dataset")
            logged = any(f.endswith("interactions.jsonl") for f in files)
            ok("D10 dataset", f"{FIELD_LOG_DATASET} exists"
               + (" · interactions.jsonl present (runs are logging)" if logged
                  else " · no interactions.jsonl yet (do one BUILD on the Space to confirm)"))
        else:
            warn("D10 dataset", f"{FIELD_LOG_DATASET} not found — create it, or let CommitScheduler "
                                "make it on first run (needs HF_TOKEN as a Space secret).")
    except Exception as e:  # noqa: BLE001
        warn("D10 dataset", f"could not verify dataset: {e!r}")


# ── push: actually update the Space files (gated on green + auth) ─────────────
def push_space(factory_reboot: bool = True) -> None:
    """Upload the app to the Space (everything except SPACE_IGNORE) and reboot.
    Only runs after the gates pass + credentials are present."""
    try:
        from huggingface_hub import HfApi
    except Exception as e:  # noqa: BLE001
        fail("PUSH", f"huggingface_hub unavailable: {e!r}")
        return
    api = HfApi()
    print(f"\n⏫ uploading {ROOT.name}/ → {SPACE} (excluding docs, spike, caches, secrets)…")
    try:
        api.upload_folder(repo_id=SPACE, repo_type="space", folder_path=str(ROOT),
                          ignore_patterns=SPACE_IGNORE,
                          commit_message="deploy: update Space from deploy_preflight --push")
        ok("PUSH", "files uploaded")
        if factory_reboot:
            api.restart_space(SPACE, factory_reboot=True)
            ok("PUSH", "factory reboot requested — Space rebuilding (~1-2 min)")
        print("   Next: wait for build, then smoke-test (BUILD shows reasoning not Error; "
              "O'Brien/La Forge; reset button; wide UI).")
    except Exception as e:  # noqa: BLE001
        fail("PUSH", f"upload/restart failed: {e!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Deploy/record readiness gate (+ optional Space push).")
    ap.add_argument("--push", action="store_true",
                    help="after the gates pass, UPDATE the Space files (hf upload) + factory reboot")
    ap.add_argument("--no-reboot", action="store_true", help="with --push, skip the factory reboot")
    args = ap.parse_args()

    print("Deploy / record preflight — " + SPACE)
    print("=" * 70)
    d1_build()
    d1b_tests()
    d2_files()
    d3_frontmatter()
    d4_requirements()
    d5_reference_block()
    d6_ledger()
    d7_data()
    authed = d8_credentials()
    d9_space(authed)
    d10_dataset(authed)
    print("=" * 70)
    if _fail:
        print(f"🔴 NO-GO: fix {len(_fail)} blocker(s) — {', '.join(_fail)}")
        sys.exit(1)
    if args.push:
        if not authed:
            print("🔴 --push needs HF credentials (HF_TOKEN or `hf auth login`). Nothing pushed.")
            sys.exit(1)
        push_space(factory_reboot=not args.no_reboot)
        sys.exit(1 if _fail else 0)
    if _warn:
        print(f"🟡 GO with warnings ({', '.join(_warn)}) — read them; credentials/Space "
              "warnings just mean 'deploy from an authenticated machine'. "
              "Run with --push (authenticated) to update the Space.")
        sys.exit(0)
    print("🟢 GO — local build clean, files + frontmatter ready, authenticated. "
          "Re-run with --push to update the Space + reboot, then smoke-test → record.")


if __name__ == "__main__":
    main()
