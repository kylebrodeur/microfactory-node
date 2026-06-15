"""Deliberation log — live, turn-by-turn capture of the personas' argument.

Companion to field_log.py. Where the field log records the *interaction config*,
this records *how the agent reasoned*: each run appends the turns of the
multi-persona deliberation (O'Brien proposes -> Spine vetoes -> La Forge second
opinion / dispute -> operator override -> world simulates -> La Forge grades ->
run verdict) and CommitScheduler pushes them to an open HF Dataset.

Same guarantees as field_log:
- Gated on HF_TOKEN — nothing is written or pushed if the secret is absent.
- Best-effort + exception-safe — logging never breaks a run.
- Config + agent reasoning only; no PII, no uploaded mesh files.

Schema mirrors scripts/export_deliberation.py (one row per turn) so the live
dataset and the static export share the same shape:
  session_id, track, turn, agent, role, act, stance, content,
  material, geometry, bed_position, env_temp, env_humidity, ts
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DELIB_LOG_DIR = Path(__file__).resolve().parent.parent / "deliberation_logs"
DELIB_LOG_FILE = DELIB_LOG_DIR / "deliberations.jsonl"
DELIB_LOG_REPO = "kylebrodeur/chief-engineer-deliberation"
FLUSH_MINUTES = 5

ROLE = {
    "O'Brien": "Chief Engineer",
    "La Forge": "QA Inspector",
    "Spine": "Safety Spine",
    "World": "Outcome Simulator",
    "Operator": "Operator",
}

_CANON = (
    "session_id", "track", "turn", "agent", "role", "act", "stance", "content",
    "material", "geometry", "bed_position", "env_temp", "env_humidity", "ts",
)

_scheduler: Any = None
_lock = threading.Lock()
_turns: dict[str, int] = {}   # session_id -> last turn number (single process on the Space)


def _get_scheduler():
    """Lazy-init the CommitScheduler. Returns None if HF_TOKEN is missing."""
    global _scheduler
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        return None
    if _scheduler is None:
        with _lock:
            if _scheduler is None:
                try:
                    from huggingface_hub import CommitScheduler
                except ImportError:
                    return None
                DELIB_LOG_DIR.mkdir(parents=True, exist_ok=True)
                if not DELIB_LOG_FILE.exists():
                    DELIB_LOG_FILE.write_text("", encoding="utf-8")
                _scheduler = CommitScheduler(
                    repo_id=DELIB_LOG_REPO,
                    repo_type="dataset",
                    folder_path=str(DELIB_LOG_DIR),
                    every=FLUSH_MINUTES,
                    token=token,
                    allow_patterns=["*.jsonl"],
                )
    return _scheduler


def is_active() -> bool:
    """True if deliberation logging is live (HF_TOKEN present + scheduler ready)."""
    return _get_scheduler() is not None


def _next_turn(session_id: str) -> int:
    with _lock:
        n = _turns.get(session_id, 0) + 1
        _turns[session_id] = n
        return n


def log_turns(session_id: str, track: str, turns: list[dict], ctx: dict) -> bool:
    """Append a batch of deliberation turns for one phase of one run.

    `turns` is a list of {agent, act, content, stance?} dicts; `ctx` carries
    material/geometry/bed_position/env_temp/env_humidity. Gated + exception-safe:
    if HF_TOKEN is unset or anything fails, this is a silent no-op."""
    try:
        sched = _get_scheduler()
        if sched is None or not session_id or not turns:
            return False
        lines: list[str] = []
        for tn in turns:
            agent = tn.get("agent", "")
            row = {k: None for k in _CANON}
            row.update({
                "session_id": session_id, "track": track, "turn": _next_turn(session_id),
                "agent": agent, "role": ROLE.get(agent, agent),
                "act": tn.get("act"), "stance": tn.get("stance", ""),
                "content": (tn.get("content") or "").strip(),
                "material": ctx.get("material"), "geometry": ctx.get("geometry"),
                "bed_position": ctx.get("bed_position"),
                "env_temp": ctx.get("env_temp"), "env_humidity": ctx.get("env_humidity"),
                "ts": datetime.now(timezone.utc).isoformat(),
            })
            lines.append(json.dumps(row, ensure_ascii=False))
        with _lock:
            with DELIB_LOG_FILE.open("a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        try:
            sched.trigger()
        except Exception:
            pass
        return True
    except Exception:
        return False  # logging is best-effort — never break a run
