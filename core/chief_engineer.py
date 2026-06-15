"""The Chief Engineer — Brain.

Reimplements hubAgent.ts's call shape (pattern-review.md §1): assemble system
prompt → real Ollama call → parse to Pydantic, with a conservative fallback so
a parse failure or an offline Space never crashes the demo. The reasoning text
carries the model's EVALUATION of precedent — the load-bearing moment.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import llm
from .models import Advice, Environment, Job, LessonEntry, PrintSettings, RiskRegion
from .prompts import build_system_prompt

# Conservative per-material starting points for the offline/parse-fail fallback.
_FALLBACK_SETTINGS: dict[str, dict[str, float]] = {
    "PLA":  {"nozzle_temp": 205, "bed_temp": 60, "retraction_mm": 5, "fan_pct": 100, "first_layer_fan_pct": 0, "layer_height": 0.20},
    "PETG": {"nozzle_temp": 235, "bed_temp": 80, "retraction_mm": 4, "fan_pct": 40, "first_layer_fan_pct": 0, "layer_height": 0.20},
    "ABS":  {"nozzle_temp": 245, "bed_temp": 100, "retraction_mm": 4, "fan_pct": 20, "first_layer_fan_pct": 0, "layer_height": 0.20},
    "TPU":  {"nozzle_temp": 228, "bed_temp": 50, "retraction_mm": 2, "fan_pct": 40, "first_layer_fan_pct": 0, "layer_height": 0.24},
}
_GEOMETRY_RISK = {
    "overhang": ("underside of the overhang", "sag", "steep overhangs droop before the layer freezes", "overhang"),
    "bridge": ("the unsupported span", "sag", "long bridges sag without enough cooling", "bridge"),
    "stringing": ("travel moves across gaps", "stringing", "molten plastic oozes during travel", None),
    "adhesion": ("first layer / corners", "adhesion", "poor first-layer bond lifts the part", "first_layer"),
    "vase": ("thin single-wall sections", "warping", "tall thin walls can wobble or warp", None),
}


@dataclass
class Recommendation:
    advice: Advice
    used_fallback: bool
    backend: str


def _fallback_advice(job: Job, env: Environment, retrieved: list[tuple[LessonEntry, float]]) -> Advice:
    base = _FALLBACK_SETTINGS.get(job.material.upper(), _FALLBACK_SETTINGS["PLA"])
    loc, risk, why, hint = _GEOMETRY_RISK.get(
        job.geometry_type, ("the part", "warping", "general risk", None)
    )
    if retrieved:
        e, dist = retrieved[0]
        reasoning = (
            f"[fallback] Nearest precedent: Job {e.job_id} ({e.material}/{e.geometry_type} "
            f"@ {e.env_temp:.0f}°C/{e.env_humidity:.0f}% → {e.outcome}, env-dist {dist:.2f}). "
            f"Applying its lesson with conservative {job.material} defaults."
        )
    else:
        reasoning = (
            f"[fallback] No close precedent for {job.material}/{job.geometry_type}. "
            f"Reasoning from material properties with conservative defaults."
        )
    return Advice(
        reasoning=reasoning,
        settings=PrintSettings(**base),
        risks=[RiskRegion(location=loc, risk=risk, why=why, anchor_hint=hint)],
    )


def advise(
    job: Job,
    env: Environment,
    retrieved: list[tuple[LessonEntry, float]],
    references: list[str] | None = None,
    policy_note: str | None = None,
) -> Recommendation:
    system = build_system_prompt(job, env, retrieved, references, policy_note)
    raw = llm.chat_json(system, "Give your recommendation for THIS job now.")
    backend = llm.backend_status()
    if raw is None:
        return Recommendation(_fallback_advice(job, env, retrieved), used_fallback=True, backend=backend)
    try:
        advice = Advice(**raw)
        return Recommendation(advice, used_fallback=False, backend=backend)
    except Exception:
        return Recommendation(_fallback_advice(job, env, retrieved), used_fallback=True, backend=backend)
