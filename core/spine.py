"""The Spine — deterministic veto over the model's proposed settings.

Reimplements the lab's "LLM proposes, code decides" paradigm (nodeAgent.ts
canDoJob() / 15W breaker; pattern-review.md §2) as hardcoded material bounds.
No power/Joule tracking. The model never overrides these clamps.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import PrintSettings

# Hardcoded hardware/material envelope (Ender-class FDM).
# nozzle/bed in °C; retraction in mm; fan in %.
MATERIAL_BOUNDS: dict[str, dict[str, tuple[float, float]]] = {
    "PLA":  {"nozzle_temp": (190, 220), "bed_temp": (45, 65)},
    "PETG": {"nozzle_temp": (220, 245), "bed_temp": (70, 90)},
    "ABS":  {"nozzle_temp": (230, 260), "bed_temp": (95, 110)},
    "TPU":  {"nozzle_temp": (220, 235), "bed_temp": (35, 60)},
}
COMMON_BOUNDS: dict[str, tuple[float, float]] = {
    "retraction_mm": (0.5, 8.0),
    "fan_pct": (0.0, 100.0),
    "first_layer_fan_pct": (0.0, 30.0),
    "layer_height": (0.08, 0.60),
}


@dataclass
class SpineResult:
    settings: PrintSettings       # clamped, safe-to-run
    vetoes: list[str]             # human-readable clamp notes
    requires_approval: bool       # trips the HITL gate


class SpineValidator:
    def check(self, settings: PrintSettings, material: str) -> SpineResult:
        vetoes: list[str] = []
        data = settings.model_dump()

        bounds = dict(COMMON_BOUNDS)
        mat = MATERIAL_BOUNDS.get(material.upper())
        if mat:
            bounds.update(mat)
        else:
            vetoes.append(f"Unknown material '{material}' — applying generic limits only.")

        for field, (lo, hi) in bounds.items():
            val = float(data[field])
            if val < lo:
                vetoes.append(f"{field} {val:g} below safe {lo:g} for {material} → clamped to {lo:g}.")
                data[field] = lo
            elif val > hi:
                vetoes.append(f"{field} {val:g} above safe {hi:g} for {material} → clamped to {hi:g}.")
                data[field] = hi

        clamped = PrintSettings(**data)
        # Trip the human gate if the model tried to push a real boundary.
        requires_approval = any("clamped" in v for v in vetoes)
        return SpineResult(settings=clamped, vetoes=vetoes, requires_approval=requires_approval)
