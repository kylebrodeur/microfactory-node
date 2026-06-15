"""Learned policy — the parametric layer that actually *improves*.

This is what makes the Chief Engineer more than a lookup. Each (material,
geometry, environment-BUCKET) cell holds learned offsets to the baseline
settings, updated from observed outcomes. Because cells are bucketed (not
exact env points), a lesson from one humid PETG bridge transfers to the *next*
humid PETG bridge — it generalizes, rather than recalling a single past job.

Two knowledge sources feed a recommendation, exactly as intended:
  • RAG  — retrieved prior jobs reasoned over by the LLM (chief_engineer.py)
  • policy — these learned offsets, applied deterministically + shown to the LLM

Persisted to data/policy.json. Pure-Python, deterministic, no network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from core.chief_engineer import _FALLBACK_SETTINGS
from core.models import Environment, Job, PrintSettings
from sim.outcome import SimResult

POLICY_PATH = Path(__file__).resolve().parent.parent / "data" / "policy.json"

# Corrective step per observed failure mode: which offsets to nudge, and by how
# much. Each move reduces the matching penalty in sim.outcome — so cells climb.
_CORRECTIONS = {
    "sag":             {"fan_pct": +12, "nozzle_temp": -3},
    "stringing":       {"retraction_mm": +0.5, "nozzle_temp": -4},
    "adhesion":        {"bed_temp": +6, "first_layer_fan_pct": -10},
    "under_extrusion": {"nozzle_temp": +5},
    "warp":            {"fan_pct": -10},
}
# Keep learned offsets sane; the Spine still clamps the final settings.
_OFFSET_CLAMP = {
    "nozzle_temp": 30, "bed_temp": 25, "retraction_mm": 3, "fan_pct": 80, "first_layer_fan_pct": 60,
}


def env_bucket(temp: float, humidity: float) -> tuple[str, str]:
    tb = "cool" if temp < 20 else ("warm" if temp > 26 else "mid")
    hb = "dry" if humidity < 35 else ("humid" if humidity > 55 else "mid")
    return tb, hb


def cell_key(material: str, geometry: str, env: Environment) -> str:
    tb, hb = env_bucket(env.temp, env.humidity)
    return f"{material}/{geometry}/{tb}/{hb}"


@dataclass
class Cell:
    offsets: dict[str, float]
    trials: int = 0
    successes: int = 0
    quality_history: list[float] | None = None

    @property
    def success_rate(self) -> float:
        return self.successes / self.trials if self.trials else 0.0


class LearnedPolicy:
    def __init__(self, path: Path = POLICY_PATH) -> None:
        self.path = path
        self.cells: dict[str, Cell] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return
        for k, v in raw.items():
            self.cells[k] = Cell(offsets=v.get("offsets", {}), trials=v.get("trials", 0),
                                 successes=v.get("successes", 0),
                                 quality_history=v.get("quality_history", []))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        out = {k: {"offsets": c.offsets, "trials": c.trials, "successes": c.successes,
                   "quality_history": c.quality_history or []} for k, c in self.cells.items()}
        self.path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    def reset(self) -> None:
        """Clear all learned cells back to baseline (and remove the saved file).
        Powers the UI 'reset' button alongside the ledger reset."""
        self.cells = {}
        try:
            self.path.unlink(missing_ok=True)
        except Exception:
            pass

    # --- read side ---------------------------------------------------------
    def _baseline(self, material: str) -> dict[str, float]:
        return dict(_FALLBACK_SETTINGS.get(material.upper(), _FALLBACK_SETTINGS["PLA"]))

    def offsets_for(self, material: str, geometry: str, env: Environment) -> dict[str, float]:
        c = self.cells.get(cell_key(material, geometry, env))
        return dict(c.offsets) if c else {}

    def propose(self, material: str, geometry: str, env: Environment) -> PrintSettings:
        """Deterministic proposal = material baseline + learned offsets (clamped)."""
        base = self._baseline(material)
        for k, dv in self.offsets_for(material, geometry, env).items():
            base[k] = base.get(k, 0.0) + dv
        base["fan_pct"] = max(0.0, min(100.0, base["fan_pct"]))
        base["first_layer_fan_pct"] = max(0.0, min(100.0, base["first_layer_fan_pct"]))
        base["retraction_mm"] = max(0.0, base["retraction_mm"])
        return PrintSettings(**base)

    def cell_stats(self, material: str, geometry: str, env: Environment) -> Cell | None:
        return self.cells.get(cell_key(material, geometry, env))

    def policy_note(self, material: str, geometry: str, env: Environment) -> str:
        """One line for the system prompt — steers the LLM with what's been learned."""
        c = self.cell_stats(material, geometry, env)
        if not c or not c.offsets:
            return ""
        tb, hb = env_bucket(env.temp, env.humidity)
        deltas = ", ".join(f"{k} {v:+g}" for k, v in c.offsets.items())
        return (f"LEARNED POLICY for {material}/{geometry} in {tb}/{hb} conditions "
                f"(earned over {c.trials} runs, {c.success_rate*100:.0f}% clean): adjust baseline by {deltas}. "
                f"Weigh this against the precedent above.")

    # --- write side (learning) --------------------------------------------
    def update(self, material: str, geometry: str, env: Environment, result: SimResult) -> str:
        """Fold one observed outcome into the cell. Returns a human log line."""
        key = cell_key(material, geometry, env)
        c = self.cells.setdefault(key, Cell(offsets={}))
        c.trials += 1
        c.quality_history = (c.quality_history or []) + [round(result.quality, 3)]
        if result.outcome == "success":
            c.successes += 1
            self.save()
            return f"{key}: success (q={result.quality:.2f}) — holding policy"
        moved = []
        for field, step in _CORRECTIONS.get(result.failure_mode, {}).items():
            cur = c.offsets.get(field, 0.0) + step
            lim = _OFFSET_CLAMP.get(field, 1e9)
            c.offsets[field] = max(-lim, min(lim, cur))
            moved.append(f"{field} {step:+g}")
        self.save()
        return f"{key}: {result.failure_mode} (q={result.quality:.2f}) — learned: {', '.join(moved) or 'no-op'}"
