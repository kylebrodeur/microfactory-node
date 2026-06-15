"""The closed learning loop — the primary thing we demo.

One iteration: the policy PROPOSES settings → the Spine vetoes unsafe values →
the simulated world returns an outcome (the printer's role) → the outcome is
written to the ledger as precedent AND folded into the policy. Run it N times
on the same job and watch quality climb from failure to clean: knowledge
compounding, made literal and self-driving.

Deterministic and offline by design (no LLM call in the loop) so the demo is
reproducible and fast. The cockpit's live path still runs the real LLM with
this same policy injected — see chief_engineer.advise / prompts.policy_note.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.ledger import LedgerManager
from learn.policy import LearnedPolicy
from core.models import Environment, Job, LessonEntry, PrintSettings
from sim.outcome import SimResult, simulate
from core.spine import SpineValidator

_SPINE = SpineValidator()


@dataclass
class IterationRecord:
    n: int
    settings: PrintSettings
    result: SimResult
    learned: str            # what the policy changed
    clamped: bool


@dataclass
class SessionResult:
    job: Job
    env: Environment
    records: list[IterationRecord] = field(default_factory=list)

    @property
    def trajectory(self) -> list[float]:
        return [r.result.quality for r in self.records]

    @property
    def first_success(self) -> int | None:
        for r in self.records:
            if r.result.outcome == "success":
                return r.n
        return None


def _record_lesson(job: Job, env: Environment, s: PrintSettings, result: SimResult,
                   ledger: LedgerManager) -> None:
    verb = {"success": "printed clean", "failed_sag": "sagged",
            "failed_stringing": "strung"}.get(result.outcome, result.outcome)
    lesson = (f"[sim] {job.material} {job.geometry_type} at {env.temp:.0f}°C/{env.humidity:.0f}% RH "
              f"{verb} (q={result.quality:.2f}) with nozzle {s.nozzle_temp:.0f}°C, fan {s.fan_pct:.0f}%, "
              f"retraction {s.retraction_mm:.1f}mm.")
    ledger.append(LessonEntry(
        job_id=f"sim-{datetime.now(timezone.utc).strftime('%H%M%S%f')}",
        material=job.material, geometry_type=job.geometry_type,
        env_temp=env.temp, env_humidity=env.humidity, outcome=result.outcome,
        lesson=lesson, source="sim", timestamp=datetime.now(timezone.utc).isoformat()))


def run_iteration(job: Job, env: Environment, policy: LearnedPolicy, ledger: LedgerManager,
                 n: int, record: bool = True, overrides: PrintSettings | None = None) -> IterationRecord:
    proposed = overrides if overrides is not None else policy.propose(job.material, job.geometry_type, env)
    checked = _SPINE.check(proposed, job.material)
    settings = checked.settings
    result = simulate(settings, job, env)
    if record:
        _record_lesson(job, env, settings, result, ledger)
    learned = policy.update(job.material, job.geometry_type, env, result)
    return IterationRecord(n=n, settings=settings, result=result, learned=learned,
                           clamped=bool(checked.vetoes))


def run_session(job: Job, env: Environment, iterations: int, policy: LearnedPolicy,
               ledger: LedgerManager) -> SessionResult:
    sess = SessionResult(job=job, env=env)
    for i in range(1, iterations + 1):
        sess.records.append(run_iteration(job, env, policy, ledger, i))
    return sess
