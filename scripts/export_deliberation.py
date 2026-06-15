"""Export the Chief Engineer's multi-persona DELIBERATION as a HF-ready trace.

The lesson ledger (scripts/export_trace.py) shares *what the agent learned*. This
shares *how the agent thinks*: the turn-by-turn argument between the personas on
each job — O'Brien proposes, the Spine vetoes unsafe values, La Forge gives a
skeptical second opinion (and can dispute → the operator overrides), the
deterministic world prints, La Forge grades each run, then delivers a run verdict.

Our own schema (one row per turn): session_id, track, turn, agent, role, act, stance,
content, + the job context (material/geometry/bed/env) so each row is self-describing.

Side-effect-free: runs against a throwaway ledger + policy in a temp dir, so the
shipped state is never touched. Offline-safe: with no LLM the personas fall back to
their deterministic voices, so the trace is fully reproducible.

Run: `make deliberation`  (or `uv run python -m scripts.export_deliberation`)  →  dist/deliberation/
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core import inspector, seed_lessons
from core.chief_engineer import advise
from core.ledger import LedgerManager
from core.models import Advice, Environment, Job, PrintSettings
from core.spine import SpineValidator
from learn.loop import run_iteration
from learn.policy import LearnedPolicy

try:  # ingestion is optional / removable (mirrors app.py)
    from ingest.distill import reference_block
except Exception:
    def reference_block(_material):  # type: ignore
        return []

DIST = Path(__file__).resolve().parent.parent / "dist" / "deliberation"
HF_REPO = "kylebrodeur/chief-engineer-deliberation"

# Representative jobs, chosen to exercise the full range of La Forge's stances
# (concur / caution / dispute→override) and the print-loop's climb to clean.
JOBS = [
    ("ABS",  "overhang",  "edge",   26.0, 60.0, 4),  # off-center ABS + thin fan → dispute → override
    ("PETG", "overhang",  "center", 24.0, 55.0, 3),  # thin fan for an overhang → caution
    ("PLA",  "adhesion",  "center", 21.0, 45.0, 3),  # inside sane bounds → concur
    ("TPU",  "stringing", "edge",   23.0, 65.0, 3),  # humid + short retraction → caution
]

ROLE = {
    "O'Brien": "Chief Engineer",
    "La Forge": "QA Inspector",
    "Spine": "Safety Spine",
    "World": "Outcome Simulator",
    "Operator": "Operator",
}

CARD = """---
license: mit
task_categories: [text-generation]
language: [en]
tags: [3d-printing, additive-manufacturing, agent-trace, multi-agent, deliberation, build-small-hackathon]
pretty_name: Chief Engineer — Deliberation Traces
---

# Chief Engineer — Deliberation Traces

Turn-by-turn **multi-persona deliberation** from **The Chief Engineer**, a small local
Gemma agent built for the HF Build Small hackathon (Backyard AI). Where the
[lesson ledger](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger)
records *what the agent learned*, this records *how it reasons*: the argument between
the personas on each job. It grows two ways: a reproducible static export
(`make deliberation`) and **live turns logged on every run of the Space** (gated on
`HF_TOKEN`; config + agent reasoning only, never PII or uploaded files).

Each row is one **turn**:

- **O'Brien** (Chief Engineer) — proposes settings + reasoning over precedent.
- **Spine** (Safety Spine) — deterministically vetoes/clamps unsafe values.
- **La Forge** (QA Inspector) — a separate, skeptical voice: second opinion before the
  print (`concur` / `caution` / `dispute`), a grade on each run, and a run verdict.
- **Operator** — the human, who can override a `dispute` and proceed.
- **World** (Outcome Simulator) — the deterministic physics-lite world that reports the
  actual print outcome (the agent never grades its own work).

The integrity rule made literal: the proposer never marks its own homework.

## Schema

`session_id, track, turn, agent, role, act, stance, content, material, geometry,
bed_position, env_temp, env_humidity, ts`

`track` is the phase — `preflight` (propose → veto → second opinion → override),
`print-loop` (simulate → grade, per iteration), `review` (run verdict).
"""


def _settings_line(s: PrintSettings) -> str:
    return (f"nozzle {s.nozzle_temp:.0f}°C, bed {s.bed_temp:.0f}°C, fan {s.fan_pct:.0f}%, "
            f"first-layer fan {s.first_layer_fan_pct:.0f}%, retraction {s.retraction_mm:.1f}mm")


def export() -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / "deliberations.jsonl"

    # throwaway state so the shipped ledger/policy are never mutated
    tmp = Path(tempfile.mkdtemp(prefix="ce-delib-"))
    ledger = LedgerManager(path=tmp / "ledger.jsonl")
    seed_lessons.ensure_seeded(ledger)
    spine = SpineValidator()

    import json

    clock = datetime(2026, 6, 14, 12, 0, 0, tzinfo=timezone.utc)
    rows: list[dict] = []

    def emit(job_id, track, turn, agent, act, content, *, ctx, stance=""):
        nonlocal clock
        clock += timedelta(seconds=7)
        rows.append({
            "session_id": job_id, "track": track, "turn": turn,
            "agent": agent, "role": ROLE[agent], "act": act, "stance": stance,
            "content": content.strip(),
            "material": ctx["material"], "geometry": ctx["geometry"],
            "bed_position": ctx["bed_position"],
            "env_temp": ctx["env_temp"], "env_humidity": ctx["env_humidity"],
            "ts": clock.isoformat(),
        })

    for material, geometry, bed, temp, hum, iters in JOBS:
        job_id = f"{material}-{geometry}-{bed}".lower()
        job = Job(geometry_type=geometry, material=material, bed_position=bed)
        env = Environment(temp=temp, humidity=hum)
        ctx = {"material": material, "geometry": geometry, "bed_position": bed,
               "env_temp": temp, "env_humidity": hum}
        # fresh policy per job so the loop's climb starts from baseline each time
        policy = LearnedPolicy(path=tmp / f"policy-{job_id}.json")

        # ── preflight: propose → veto → second opinion → (override) ──
        retrieved = ledger.retrieve(material, geometry, env.temp, env.humidity)
        rec = advise(job, env, retrieved, reference_block(material),
                     policy.policy_note(material, geometry, env))
        checked = spine.check(rec.advice.settings, material)
        t = 1
        emit(job_id, "preflight", t, "O'Brien", "propose",
             f"{rec.advice.reasoning}\nProposed: {_settings_line(checked.settings)}.", ctx=ctx)
        t += 1
        emit(job_id, "preflight", t, "Spine", "veto",
             ("Clamped: " + " · ".join(checked.vetoes)) if checked.vetoes
             else "Within the safe envelope for this material — no clamp.", ctx=ctx,
             stance="clamped" if checked.requires_approval else "clear")
        t += 1
        verdict = inspector.second_opinion(job, env, checked.settings, rec.advice)
        emit(job_id, "preflight", t, "La Forge", "second_opinion",
             f"{verdict.headline} — {verdict.detail}", ctx=ctx, stance=verdict.stance)
        if verdict.stance.lower() == "dispute":
            t += 1
            emit(job_id, "preflight", t, "Operator", "override",
                 "Acknowledged La Forge's objection. Proceeding to print on the operator's call.",
                 ctx=ctx, stance="override")

        # ── print-loop: simulate → grade, per iteration ──
        for n in range(1, iters + 1):
            t += 1
            r = run_iteration(job, env, policy, ledger, n, record=False)
            clamp = " (Spine clamped a setting)" if r.clamped else ""
            emit(job_id, "print-loop", t, "World", "simulate",
                 f"Iteration {n}: {r.result.detail}.{clamp} Policy: {r.learned}.", ctx=ctx,
                 stance=r.result.outcome)
            t += 1
            g = inspector.grade_iteration(geometry, r.result)
            emit(job_id, "print-loop", t, "La Forge", "grade",
                 f"{g.headline} — {g.detail}", ctx=ctx, stance=g.stance)

        # ── review: one verdict across the run ──
        # rebuild records for the summary from a fresh deterministic pass
        sess_records = []
        rpolicy = LearnedPolicy(path=tmp / f"policy-rev-{job_id}.json")
        for n in range(1, iters + 1):
            sess_records.append(run_iteration(job, env, rpolicy, ledger, n, record=False))
        summary = inspector.summarize_run(sess_records, material=material, geometry=geometry)
        t += 1
        emit(job_id, "review", t, "La Forge", "verdict",
             f"{summary.headline} — {summary.detail}", ctx=ctx, stance=summary.stance)

    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    (DIST / "README.md").write_text(CARD, encoding="utf-8")

    jobs = len({r["session_id"] for r in rows})
    print(f"exported {len(rows)} turns across {jobs} jobs → {out}")
    print(f"dataset card → {DIST / 'README.md'}")
    print(f"publish:  hf upload {HF_REPO} {DIST} . --repo-type dataset")
    return out


if __name__ == "__main__":
    export()
