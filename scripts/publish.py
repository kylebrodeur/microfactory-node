"""Publish the Space + sync the public GitHub mirror in one command.

Run from `chief-engineer/`:

    make publish

or

    uv run python -m scripts.publish

What it does:
1. Runs `scripts.deploy_preflight --push` to update the HF Space and reboot.
2. Syncs the Space-facing file subset to the public mirror repo
   `kylebrodeur/microfactory-node` and pushes `main`.

Environment:
- HF_TOKEN or `hf auth login` must be active for the Space push.
- `gh auth login` or SSH key must be active for the GitHub push.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIRROR_REPO = "git@github.com:kylebrodeur/microfactory-node.git"
MIRROR_NAME = "microfactory-node"

# Same rules as deploy_preflight.SPACE_IGNORE, plus a .gitignore for the mirror itself.
MIRROR_IGNORE = [
    "docs/**",
    "!docs/RUNBOOK.md",
    "!docs/reference/DEPLOYMENT.md",
    "!docs/reference/SIMULATION.md",
    # Dev/recording scripts are not part of the public Space-facing runtime.
    "scripts/**",
    "spike/**", "field_logs/**", "deliberation_logs/**", ".venv/**", "node_modules/**",
    "recordings/**", "**/__pycache__/**", "**/*.pyc", ".git/**", ".gitignore", ".env", ".agents/**",
    ".codeboarding/**", ".codeboardingignore", "data/policy.json", "data/_generated.glb",
    "data/_vprint.gif", "uv.lock", ".pytest_cache/**", "*.cap/**",
    "learn/finetune/REPORT.md",
    "learn/finetune/REPORT_v1.md",
]


def match_ignore(rel_path: str) -> bool:
    import fnmatch

    # (pattern, is_negative)
    patterns: list[tuple[str, bool]] = []
    for pat in MIRROR_IGNORE:
        is_neg = pat.startswith("!")
        real_pat = pat[1:] if is_neg else pat
        patterns.append((real_pat, is_neg))

    # Inclusions override exclusions.
    for pat, is_neg in patterns:
        if is_neg and _matches(rel_path, pat):
            return False
    for pat, is_neg in patterns:
        if not is_neg and _matches(rel_path, pat):
            return True
    return False


def _matches(rel_path: str, pat: str) -> bool:
    import fnmatch

    if pat.endswith("/**"):
        prefix = pat[:-3]
        return rel_path.startswith(prefix + "/") or rel_path == prefix
    if pat.startswith("**/"):
        suffix = pat[3:]
        return rel_path.endswith(suffix) or ("/" + suffix) in rel_path
    if pat.startswith("*"):
        return fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(Path(rel_path).name, pat)
    return rel_path == pat or rel_path.startswith(pat + "/")


def run(cmd: list[str], cwd: Path | None = None, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    kwargs = {"cwd": cwd, "check": check, "text": True}
    if capture_output:
        kwargs["capture_output"] = True
    return subprocess.run(cmd, **kwargs)


def publish_space(*, no_reboot: bool = False, dry_run: bool = False) -> bool:
    print("\n⏫ Step 1 — update the HF Space")
    cmd = ["uv", "run", "python", "-m", "scripts.deploy_preflight"]
    if not dry_run:
        cmd.append("--push")
    if no_reboot:
        cmd.append("--no-reboot")
    r = subprocess.run(cmd, cwd=ROOT, text=True)
    return r.returncode == 0


def sync_mirror(*, dry_run: bool = False) -> bool:
    print("\n🪞 Step 2 — sync public GitHub mirror")
    mirror_dir = Path(tempfile.gettempdir()) / f"{MIRROR_NAME}-sync"
    if mirror_dir.exists():
        shutil.rmtree(mirror_dir)
    mirror_dir.mkdir(parents=True)

    print(f"   Mirroring Space-facing subset → {mirror_dir}")
    files_copied = 0
    for src in sorted(ROOT.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(ROOT).as_posix()
        if match_ignore(rel):
            continue
        dst = mirror_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        files_copied += 1

    # Drop transient pycache/pi that may have slipped through
    for d in list(mirror_dir.rglob("__pycache__")):
        shutil.rmtree(d)
    pi_dir = mirror_dir / ".pi"
    if pi_dir.exists():
        shutil.rmtree(pi_dir)

    print(f"   Copied {files_copied} files")

    run(["git", "init", "-b", "main"], cwd=mirror_dir, check=False)
    run(["git", "remote", "add", "origin", MIRROR_REPO], cwd=mirror_dir, check=False)
    run(["git", "fetch", "origin", "main"], cwd=mirror_dir, check=False)
    run(["git", "reset", "--hard", "origin/main"], cwd=mirror_dir, check=False)

    # Clean working tree but keep .git
    for item in mirror_dir.iterdir():
        if item.name == ".git":
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

    # Re-copy after reset
    for src in sorted(ROOT.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(ROOT).as_posix()
        if match_ignore(rel):
            continue
        dst = mirror_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    for d in list(mirror_dir.rglob("__pycache__")):
        shutil.rmtree(d)
    if (mirror_dir / ".pi").exists():
        shutil.rmtree(mirror_dir / ".pi")

    run(["git", "add", "-A"], cwd=mirror_dir)
    status = run(["git", "status", "--short"], cwd=mirror_dir, check=True, capture_output=True)
    if not status.stdout.strip():
        print("   Mirror already up to date.")
        return True

    print(f"   Changes:\n{status.stdout}")
    if dry_run:
        print("   (dry-run: not committing or pushing)")
        return True

    run(["git", "commit", "-m", "Re-sync from private microfactory-lab"], cwd=mirror_dir)
    run(["git", "push", "origin", "main"], cwd=mirror_dir)
    print(f"   ✅ Mirror pushed: https://github.com/kylebrodeur/{MIRROR_NAME}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish the HF Space + sync the public GitHub mirror.")
    ap.add_argument("--no-reboot", action="store_true", help="push to Space but skip factory reboot")
    ap.add_argument("--mirror-only", action="store_true", help="skip the HF Space push; only sync the mirror")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen; do not push")
    args = ap.parse_args()

    print("Publish Microfactory Node: HF Space + public GitHub mirror")
    print("=" * 60)

    if not args.mirror_only:
        if not publish_space(no_reboot=args.no_reboot, dry_run=args.dry_run):
            print("\n🔴 Space push failed — mirror sync skipped.")
            return 1

    if not sync_mirror(dry_run=args.dry_run):
        print("\n🔴 Mirror sync failed.")
        return 1

    print("\n🟢 Published: Space updated, mirror synced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
