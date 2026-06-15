"""Scripted demo / integration test — the Day-4/5 dry run, in code.

Runs a curated job sequence through the REAL loop (advise → Spine → reflect) on
a fresh seeded ledger and prints a readable transcript. It exists to (a) expose
demo-path bugs early — the step Kaggle never reached — and (b) be the source of
truth for the video beats: precedent applied, environment-driven shift, and the
"no close precedent" discrimination case.

Works offline (deterministic fallback) and gets richer with real Ollama.
Run: `make demo`  (or `uv run python -m scripts.scripted_demo`)
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.chief_engineer import advise
from core.ledger import LedgerManager
from core.models import Environment, Job, PrintSettings
from core.reflect import reflect_on_job
from core.seed_lessons import ensure_seeded
from core.spine import SpineValidator

SPINE = SpineValidator()

# (job, env, beat, outcome-to-record) — designed to make compounding legible.
SCENARIOS = [
    (Job(geometry_type="overhang", material="PLA", description="45° bracket, 60mm tall"),
     Environment(temp=28, humidity=50),
     "Warm room — should match the prior PLA overhang that SAGGED at 28°C.",
     "failed_sag"),
    (Job(geometry_type="overhang", material="PLA", description="same bracket, cooler day"),
     Environment(temp=23, humidity=40),
     "Cooler/drier — recommendation should shift vs the warm run.",
     "success"),
    (Job(geometry_type="stringing", material="PETG", description="hex grid, lots of travel"),
     Environment(temp=25, humidity=65),
     "Humid PETG — precedent should suspect MOISTURE, not just retraction.",
     "success"),
    (Job(geometry_type="vase", material="TPU", description="flexible spiral vase"),
     Environment(temp=22, humidity=45),
     "NOVEL: no TPU/vase precedent — expect 'no close precedent' reasoning.",
     None),
]


def _rule(label: str) -> None:
    print(f"\n{'─' * 70}\n{label}\n{'─' * 70}")


def run() -> None:
    led = LedgerManager(Path(tempfile.mkdtemp()) / "lessons.jsonl")
    print(f"seeded {ensure_seeded(led)} lessons · ledger={led.count()}")

    for i, (job, env, beat, outcome) in enumerate(SCENARIOS, 1):
        _rule(f"JOB {i}: {job.material}/{job.geometry_type} @ {env.temp:.0f}°C/{env.humidity:.0f}% RH")
        print(f"  beat → {beat}")

        retrieved = led.retrieve(job.material, job.geometry_type, env.temp, env.humidity)
        if retrieved:
            print("  precedent:")
            for e, d in retrieved:
                print(f"    • {e.job_id} ({e.source}) {e.outcome}  dist={d:.2f}")
        else:
            print("  precedent: (none — novel situation)")

        rec = advise(job, env, retrieved)
        s = rec.advice.settings
        spine = SPINE.check(s, job.material)
        print(f"  backend: {rec.backend}{' [fallback]' if rec.used_fallback else ''}")
        print(f"  reasoning: {rec.advice.reasoning}")
        print(f"  settings: nozzle={spine.settings.nozzle_temp:.0f} bed={spine.settings.bed_temp:.0f} "
              f"retr={spine.settings.retraction_mm:.1f} fan={spine.settings.fan_pct:.0f}%")
        if spine.vetoes:
            print("  🛡 spine:", "; ".join(spine.vetoes))
        for r in rec.advice.risks:
            print(f"  ⚠ risk: {r.risk} @ {r.location} — {r.why}")

        if outcome:
            entry = reflect_on_job(job, env, spine.settings, outcome, led)
            print(f"  📒 recorded ({outcome}) → earned: {entry.lesson}")

    print(f"\nFINAL LEDGER: {led.count()}  (knowledge compounded across the run)")


if __name__ == "__main__":
    run()
