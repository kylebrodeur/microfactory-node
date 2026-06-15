"""Post-job reflection — the compression step (the thesis).

Reimplements hubAgent.ts `reviewOutcome()` (pattern-review.md §4), re-keyed
from routing-confidence to environment + geometry. A finished job + a
HUMAN-REPORTED outcome becomes one durable, env-keyed LessonEntry. The model
NEVER judges its own outcome — the outcome is always passed in from the manual
button.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import llm
from .ledger import LedgerManager
from .models import Environment, Job, LessonEntry, PrintSettings
from .prompts import REFLECT_SYSTEM, build_reflect_prompt


def _settings_summary(s: PrintSettings) -> str:
    return (
        f"nozzle {s.nozzle_temp:.0f}°C, bed {s.bed_temp:.0f}°C, "
        f"retraction {s.retraction_mm:.1f}mm, fan {s.fan_pct:.0f}%, "
        f"first-layer fan {s.first_layer_fan_pct:.0f}%"
    )


def _fallback_lesson(job: Job, env: Environment, s: PrintSettings, outcome: str) -> str:
    verdict = {
        "success": "held up",
        "failed_sag": "sagged",
        "failed_stringing": "strung",
    }.get(outcome, outcome)
    return (
        f"{job.material} {job.geometry_type} at {env.temp:.0f}°C/{env.humidity:.0f}% RH "
        f"{verdict} with {_settings_summary(s)}."
    )


def reflect_on_job(
    job: Job,
    env: Environment,
    settings: PrintSettings,
    outcome: str,
    ledger: LedgerManager,
    job_id: str | None = None,
) -> LessonEntry:
    """Distill outcome → lesson, append as an 'earned' entry, return it."""
    raw = llm.chat_json(REFLECT_SYSTEM, build_reflect_prompt(job, env, _settings_summary(settings), outcome))
    lesson = (raw or {}).get("lesson") if isinstance(raw, dict) else None
    if not lesson:
        lesson = _fallback_lesson(job, env, settings, outcome)

    entry = LessonEntry(
        job_id=job_id or f"job-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        material=job.material,
        geometry_type=job.geometry_type,
        env_temp=env.temp,
        env_humidity=env.humidity,
        outcome=outcome,
        lesson=lesson,
        source="earned",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    ledger.append(entry)
    return entry
