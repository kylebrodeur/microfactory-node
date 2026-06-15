"""Field log — append-only interaction logging for the live Space.

Each BUILD appends one JSONL row to a local file; CommitScheduler pushes it
to a separate HF Dataset repo every N minutes. Gated on HF_TOKEN — if the
secret isn't set, nothing is written or pushed (local/offline unaffected).

Design per docs/RESEARCH-NEEDS.md "Capturing live Space interactions":
- Logs job config only (material, geometry, env, settings, risks, backend)
- Never logs PII or uploaded mesh files
- Rows are candidates, never auto-promoted into the curated ledger
- Privacy disclosure shown in UI when active
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FIELD_LOG_DIR = Path(__file__).resolve().parent.parent / "field_logs"
FIELD_LOG_FILE = FIELD_LOG_DIR / "interactions.jsonl"
FIELD_LOG_REPO = "build-small-hackathon/chief-engineer-field-log"
FLUSH_MINUTES = 5

_scheduler: Any = None
_lock = threading.Lock()


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
                FIELD_LOG_DIR.mkdir(parents=True, exist_ok=True)
                # Ensure the file exists so the scheduler has something to track
                if not FIELD_LOG_FILE.exists():
                    FIELD_LOG_FILE.write_text("", encoding="utf-8")
                _scheduler = CommitScheduler(
                    repo_id=FIELD_LOG_REPO,
                    repo_type="dataset",
                    folder_path=str(FIELD_LOG_DIR),
                    every=FLUSH_MINUTES,
                    token=token,
                    allow_patterns=["*.jsonl"],
                )
    return _scheduler


def is_active() -> bool:
    """True if field logging is live (HF_TOKEN present + scheduler initialized)."""
    return _get_scheduler() is not None


# Canonical FLAT schema — every row carries exactly these keys (None when N/A), all
# scalars/strings (no nested dicts/lists). This is what makes the HF dataset viewer
# render cleanly: a rectangular, well-typed table instead of ragged/nested JSON.
_CANON = (
    "ts", "kind", "material", "geometry", "env_temp", "env_humidity",
    "bed_position", "printer", "backend", "used_fallback",
    "nozzle_temp", "bed_temp", "fan_pct", "retraction_mm", "first_layer_fan_pct",
    "risks", "risk_count", "inspector_stance", "inspector_headline", "agreement",
    "outcome", "quality", "iterations", "q_start", "q_end", "first_clean",
)


def _write_row(fields: dict) -> bool:
    """Normalize to the canonical flat schema (drop unknown keys, fill missing with
    None) and append one JSONL line. Gated + exception-safe — never breaks a run."""
    try:
        sched = _get_scheduler()
        if sched is None:
            return False
        row = {k: None for k in _CANON}
        row.update({k: v for k, v in fields.items() if k in _CANON})
        row["ts"] = datetime.now(timezone.utc).isoformat()
        with _lock:
            with FIELD_LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        try:
            sched.trigger()
        except Exception:
            pass
        return True
    except Exception:
        return False  # logging is best-effort — never break a run


def log_event(kind: str, payload: dict) -> bool:
    """Append one interaction row of any KIND — build | second_opinion | simulate |
    record | print_run | print_override — normalized to the canonical flat schema.
    Same gate (HF_TOKEN) + privacy rules: config/outcomes only, never PII or files."""
    return _write_row({**payload, "kind": kind})


def log_build(job: dict, env: dict, settings: dict, advice: dict,
              backend: str, used_fallback: bool) -> bool:
    """Append one BUILD row (flattened settings + risks-as-string for the viewer)."""
    risks = advice.get("risks", []) or []
    return _write_row({
        "kind": "build",
        "material": job.get("material"), "geometry": job.get("geometry_type"),
        "env_temp": env.get("temp"), "env_humidity": env.get("humidity"),
        "bed_position": job.get("bed_position"),
        "printer": job.get("printer", "Creality Ender 3 V2"),
        "backend": backend, "used_fallback": used_fallback,
        "nozzle_temp": settings.get("nozzle_temp"), "bed_temp": settings.get("bed_temp"),
        "fan_pct": settings.get("fan_pct"), "retraction_mm": settings.get("retraction_mm"),
        "first_layer_fan_pct": settings.get("first_layer_fan_pct"),
        "risks": ", ".join(str(r.get("risk")) for r in risks if isinstance(r, dict)) or None,
        "risk_count": len(risks),
    })


def log_print_override(job: dict, env: dict, overrides: dict) -> bool:
    """Append one PRINT_OVERRIDE row with the operator-changed settings flattened.

    The canonical schema only accepts flat scalars, so this helper unpacks the
    override object rather than nesting it under a 'settings' key.
    """
    return _write_row({
        "kind": "print_override",
        "material": job.get("material"), "geometry": job.get("geometry_type"),
        "env_temp": env.get("temp"), "env_humidity": env.get("humidity"),
        "bed_position": job.get("bed_position"),
        "printer": job.get("printer", "Creality Ender 3 V2"),
        "nozzle_temp": overrides.get("nozzle_temp"),
        "bed_temp": overrides.get("bed_temp"),
        "fan_pct": overrides.get("fan_pct"),
        "retraction_mm": overrides.get("retraction_mm"),
        "first_layer_fan_pct": overrides.get("first_layer_fan_pct"),
    })


def privacy_notice() -> str:
    """One-line UI disclosure, shown only when logging is active."""
    return (
        "<div class='ce-sub' style='font-size:10px;opacity:0.6;margin-top:4px;'>"
        "🔒 Job config logged to improve the model (no personal data, no uploaded files). "
        f"<a href='https://huggingface.co/datasets/{FIELD_LOG_REPO}' target='_blank'>"
        "View the field log →</a></div>"
    )
