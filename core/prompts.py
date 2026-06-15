"""System-prompt assembly (versioned instruction steering, not activation steering).

`build_system_prompt()` concatenates: persona + job/env + a Historical
Precedent block of 2-3 retrieved prior jobs. CRITICAL: the prompt asks the
model to EVALUATE applicability — apply, adapt, or set precedent aside, and
say "no close precedent" when nothing fits. It is NOT told to always cite.
"""

from __future__ import annotations

from .models import Environment, Job, LessonEntry

PERSONA = """You are Chief Engineer O'Brien: a veteran print-shop master who has run \
thousands of FDM jobs. You are terse and physical. You think in feeds, temps, \
cooling, and how the room affects the plastic. You do not hype. You proposed \
settings; a deterministic Spine will veto anything unsafe, so propose what is \
*right*, not what is merely safe.

You reason about PRECEDENT before you decide. You are given similar prior jobs \
with their conditions and outcomes. Weigh what transfers to THIS job and what \
does not. If a prior job is close, apply or adapt its lesson and say so. If \
nothing close applies, say "no close precedent" and reason from material \
properties. Knowing what you don't know is a strength, not a weakness."""

OUTPUT_CONTRACT = """Respond ONLY with valid JSON, no prose outside it, in exactly this shape:
{
  "reasoning": "2-4 sentences. START with your evaluation of the prior jobs: what transfers, what doesn't, and why. Then the decision.",
  "settings": {
    "nozzle_temp": <C>, "bed_temp": <C>, "retraction_mm": <mm>,
    "fan_pct": <0-100>, "first_layer_fan_pct": <0-100>, "layer_height": <mm, e.g. 0.12-0.28>
  },
  "risks": [
    {"location": "where on the part", "risk": "sag|stringing|adhesion|warping|delamination",
     "why": "one line", "anchor_hint": "overhang|bridge|first_layer|corner|null"}
  ]
}"""


def _precedent_block(lessons: list[tuple[LessonEntry, float]]) -> str:
    if not lessons:
        return (
            "HISTORICAL PRECEDENT:\n"
            "  (none) — no prior job matches this material + geometry. "
            "Reason from material properties and say so plainly.\n"
        )
    lines = ["HISTORICAL PRECEDENT (nearest prior jobs by environment):"]
    for i, (e, dist) in enumerate(lessons, 1):
        lines.append(
            f"  [{i}] Job {e.job_id} ({e.source}) — {e.material}/{e.geometry_type} "
            f"@ {e.env_temp:.0f}°C, {e.env_humidity:.0f}% RH → {e.outcome} "
            f"(env-distance {dist:.2f})\n      lesson: {e.lesson}"
        )
    return "\n".join(lines) + "\n"


def _reference_block(references: list[str]) -> str:
    if not references:
        return ""
    lines = "\n".join(f"  - {r}" for r in references)
    return (
        "MATERIAL REFERENCE (hard parameters distilled from your slicer/firmware configs):\n"
        f"{lines}\nTreat these as bounds/baselines, not precedent.\n\n"
    )


def build_system_prompt(
    job: Job,
    env: Environment,
    retrieved: list[tuple[LessonEntry, float]],
    references: list[str] | None = None,
    policy_note: str | None = None,
) -> str:
    policy_block = f"{policy_note}\n\n" if policy_note else ""
    return (
        f"{PERSONA}\n\n"
        f"CURRENT JOB:\n"
        f"  material: {job.material}\n"
        f"  geometry: {job.geometry_type}\n"
        f"  description: {job.description or '(none given)'}\n\n"
        f"ENVIRONMENT (right now in the room):\n"
        f"  temperature: {env.temp:.0f}°C\n"
        f"  humidity: {env.humidity:.0f}% RH\n\n"
        f"{_reference_block(references or [])}"
        f"{_precedent_block(retrieved)}\n"
        f"{policy_block}"
        f"{OUTPUT_CONTRACT}"
    )


# --- reflection prompt (post-job compression) ------------------------------
REFLECT_SYSTEM = """You are Chief Engineer O'Brien distilling a finished job into ONE \
durable, reusable lesson for your future self. Be specific about material, the \
conditions, and the lever that mattered. One or two sentences. No fluff.

Respond ONLY with valid JSON: {"lesson": "<one or two sentence lesson>"}"""


def build_reflect_prompt(job: Job, env: Environment, settings_summary: str, outcome: str) -> str:
    return (
        f"JOB: {job.material}/{job.geometry_type} — {job.description or '(no description)'}\n"
        f"ROOM: {env.temp:.0f}°C, {env.humidity:.0f}% RH\n"
        f"SETTINGS USED: {settings_summary}\n"
        f"REAL OUTCOME (human-reported): {outcome}\n\n"
        f"Write the lesson."
    )
