"""The QA Inspector — a SEPARATE reviewer persona (the hybrid evaluator).

Integrity, restated: the Chief Engineer never grades its own work. The
deterministic simulated world (`sim/outcome.py`) produces the ground-truth
pass/fail. The Inspector is a *distinct* voice — skeptical, conservative —
that reads what the Engineer claimed and what actually happened and writes a
verdict. The grade is therefore "hybrid": deterministic physics + a second LLM
opinion, never the proposer marking its own homework.

One persona, three sets of rules depending on where it stands in the workflow:
  • second_opinion(...)  — BUILD: critique the PLAN before any print runs.
  • grade_outcome(...)   — PRINT: grade one finished (simulated) print vs the
                           Engineer's prediction — did the called risk hold?
  • summarize_run(...)   — REVIEW: one verdict across a whole iteration run.

LLM-backed via `llm.chat_json` with a distinct system prompt; each mode has a
deterministic fallback so the verdict is always present offline.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import llm
from .models import Advice, Environment, Job, PrintSettings
from sim.outcome import SimResult

PERSONA = """You are La Forge, the QA Inspector: a skeptical, conservative print-shop \
inspector. You did NOT propose these settings — Chief Engineer O'Brien did, and \
O'Brien is an optimist. Your job is to second-guess, not to please. You are \
terse and physical. You never flatter. You call out optimism, thin margins, and \
unflagged risks, and you give credit only when the evidence earns it."""

# predicted-risk vocabulary → simulated failure_mode it corresponds to
_RISK_TO_MODE = {
    "sag": "sag", "stringing": "stringing", "adhesion": "adhesion",
    "warping": "warp", "warp": "warp", "delamination": "under_extrusion",
}
_MODE_HUMAN = {
    "sag": "sagging", "stringing": "stringing", "adhesion": "first-layer adhesion",
    "warp": "warping", "under_extrusion": "under-extrusion", "none": "no failure",
}


@dataclass
class InspectorVerdict:
    stance: str                 # short label, e.g. "concur" / "caution" / "held" / "missed"
    headline: str               # one-line verdict
    detail: str                 # 1-2 lines of rationale
    agreement: bool | None = None   # outcome modes: did the Engineer's prediction match reality?

    @property
    def color(self) -> str:
        s = self.stance.lower()
        if s in ("dispute", "missed", "fail"):
            return "var(--ao-red, #d9534f)"
        if s in ("caution", "overcautious", "watch"):
            return "var(--ao-amber, #e0a458)"
        return "var(--ao-green)"


def _predicted_modes(advice: Advice) -> set[str]:
    out: set[str] = set()
    for r in advice.risks:
        key = (r.risk or "").strip().lower()
        out.add(_RISK_TO_MODE.get(key, key))
    return out


def _settings_line(s: PrintSettings) -> str:
    return (f"nozzle {s.nozzle_temp:.0f}°C, bed {s.bed_temp:.0f}°C, fan {s.fan_pct:.0f}%, "
            f"first-layer fan {s.first_layer_fan_pct:.0f}%, retraction {s.retraction_mm:.1f}mm")


# ── BUILD: a second opinion on the plan, before anything prints ───────────────
def second_opinion(job: Job, env: Environment, settings: PrintSettings, advice: Advice) -> InspectorVerdict:
    raw = llm.chat_json(
        PERSONA + "\n\nRespond ONLY with JSON: "
        '{"stance":"concur|caution|dispute","headline":"<one line>","detail":"<1-2 lines>"}',
        "Review this PLAN before it prints — do not re-propose, just critique.\n"
        f"JOB: {job.material}/{job.geometry_type}, bed position {job.bed_position}, "
        f"room {env.temp:.0f}°C/{env.humidity:.0f}%RH on a {env.printer}.\n"
        f"ENGINEER PROPOSED: {_settings_line(settings)}.\n"
        f"ENGINEER REASONING: {advice.reasoning}\n"
        f"ENGINEER FLAGGED RISKS: {[r.risk for r in advice.risks] or 'none'}.\n"
        "Where is the Engineer being optimistic? What would you watch?",
    )
    if raw and {"stance", "headline", "detail"} <= set(raw):
        return InspectorVerdict(str(raw["stance"]), str(raw["headline"]), str(raw["detail"]))
    return _second_opinion_fallback(job, env, settings, advice)


def _second_opinion_fallback(job: Job, env: Environment, settings: PrintSettings, advice: Advice) -> InspectorVerdict:
    geo, mat = job.geometry_type, job.material.upper()
    flags: list[str] = []
    if geo in ("overhang", "bridge") and settings.fan_pct < 60:
        flags.append(f"fan {settings.fan_pct:.0f}% is thin for a {geo} — sagging risk the Engineer may be underweighting")
    if mat == "ABS" and job.bed_position in ("edge", "corner"):
        flags.append(f"ABS off-center ({job.bed_position}) will pull at the edges — I'd second a warp watch and a brim")
    if mat == "ABS" and settings.fan_pct > 40:
        flags.append(f"fan {settings.fan_pct:.0f}% on ABS invites cracking/warp")
    if env.humidity > 55 and mat in ("PETG", "TPU", "ABS") and settings.retraction_mm < 3:
        flags.append(f"humid air ({env.humidity:.0f}%RH) + {settings.retraction_mm:.1f}mm retraction → expect stringing")
    if not advice.risks:
        flags.append("Engineer flagged NO failure regions — verify that's confidence, not optimism")

    if not flags:
        return InspectorVerdict("concur", "No red flags from a second look.",
                                "Plan sits inside sane bounds for this material and room. Cleared to print.")
    stance = "dispute" if len(flags) >= 2 else "caution"
    return InspectorVerdict(stance, f"Second opinion: {flags[0]}.",
                            " · ".join(flags[1:]) or "Print it, but watch that region.")


# ── PRINT: grade one finished (simulated) print against the prediction ────────
def grade_outcome(job: Job, env: Environment, settings: PrintSettings,
                  advice: Advice, result: SimResult) -> InspectorVerdict:
    predicted = _predicted_modes(advice)
    raw = llm.chat_json(
        PERSONA + "\n\nRespond ONLY with JSON: "
        '{"stance":"held|missed|overcautious|confirmed","headline":"<one line>","detail":"<1-2 lines>"}',
        "Grade this finished print. The outcome below came from the deterministic "
        "world, not from the Engineer — you are checking the Engineer's CALL against it.\n"
        f"JOB: {job.material}/{job.geometry_type} @ {env.temp:.0f}°C/{env.humidity:.0f}%RH.\n"
        f"ENGINEER PREDICTED RISKS: {[r.risk for r in advice.risks] or 'none'}.\n"
        f"ACTUAL OUTCOME: {result.outcome} — {result.detail} "
        f"(failure mode: {result.failure_mode}).\n"
        "Did the Engineer's prediction hold? Be blunt.",
    )
    agreement = _agreement(predicted, result)
    if raw and {"stance", "headline", "detail"} <= set(raw):
        return InspectorVerdict(str(raw["stance"]), str(raw["headline"]), str(raw["detail"]), agreement)
    return _grade_fallback(predicted, result, agreement)


def _agreement(predicted: set[str], result: SimResult) -> bool:
    if result.failure_mode == "none":
        return True            # clean print — nothing to have missed
    return result.failure_mode in predicted


def _grade_fallback(predicted: set[str], result: SimResult, agreement: bool) -> InspectorVerdict:
    mode = _MODE_HUMAN.get(result.failure_mode, result.failure_mode)
    if result.failure_mode == "none":
        if predicted:
            return InspectorVerdict("overcautious", f"Print held (q={result.quality:.2f}).",
                                    f"Engineer flagged {', '.join(sorted(predicted))}; the settings covered it. "
                                    "Credit the call — or it was conservative.", True)
        return InspectorVerdict("held", f"Clean print (q={result.quality:.2f}).",
                                "No failure flagged, none occurred. Plan and reality agree.", True)
    if agreement:
        return InspectorVerdict("confirmed", f"Failed on {mode} — exactly as called.",
                                f"Quality {result.quality:.2f}. The Engineer's risk flag was right; "
                                "the loop now has the lesson.", True)
    return InspectorVerdict("missed", f"Failed on {mode} — and it wasn't flagged.",
                            f"Quality {result.quality:.2f}. The Engineer didn't predict this mode. "
                            "That gap is what the next iteration has to close.", False)


# canonical failure mode each geometry is expected to risk (the loop's implicit
# prediction — the deterministic policy loop carries no LLM Advice per iteration)
_GEO_EXPECT = {"overhang": "sag", "bridge": "sag", "stringing": "stringing",
               "adhesion": "adhesion", "vase": "warp"}


def grade_iteration(geometry_type: str, result: SimResult) -> InspectorVerdict:
    """Deterministic-only grade for one loop iteration (no LLM — the loop runs
    many fast, reproducible iterations). Checks the outcome against the failure
    mode this geometry is expected to risk."""
    expected = {_GEO_EXPECT.get(geometry_type, "sag")}
    return _grade_fallback(expected, result, _agreement(expected, result))


# ── REVIEW: one verdict across a whole iteration run ──────────────────────────
def summarize_run(records: list, *, material: str, geometry: str) -> InspectorVerdict:
    if not records:
        return InspectorVerdict("watch", "No run to review yet.", "Run the Print loop first.")
    qualities = [r.result.quality for r in records]
    first_clean = next((r.n for r in records if r.result.outcome == "success"), None)
    start, end = qualities[0], qualities[-1]
    climbed = end - start
    if first_clean:
        stance, head = "concur", f"Converged to clean by iteration {first_clean}."
        detail = (f"{material}/{geometry} climbed {start:.2f} → {end:.2f}. The compounding is real: "
                  "each simulated outcome tightened the policy and the next run was better-informed.")
    elif climbed > 0.05:
        stance, head = "caution", f"Improving but not yet clean (best {max(qualities):.2f})."
        detail = (f"Quality rose {start:.2f} → {end:.2f} over {len(records)} runs but never crossed the "
                  "bar. More iterations or a different lever needed — the loop is learning, slowly.")
    else:
        stance, head = "dispute", "No real progress this run."
        detail = (f"Quality stuck around {start:.2f}. Either the job is mis-specified or the policy is "
                  "saturated for these conditions — worth a human look before trusting the trend.")
    return InspectorVerdict(stance, head, detail)
