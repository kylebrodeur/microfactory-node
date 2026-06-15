"""Pydantic domain types for the Chief Engineer.

Adapted from microfactory-lab `core/src/types.ts` — stripped of routing,
economic, energy, and tick concepts (over-scope per pattern-review.md §7).
Only what the compounding-knowledge loop needs.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

MATERIALS = ["PLA", "PETG", "ABS", "TPU"]
# geometry_type doubles as a retrieval key (pattern-review.md §3/§9)
GEOMETRY_TYPES = ["overhang", "bridge", "stringing", "adhesion", "vase"]
OUTCOMES = ["success", "failed_sag", "failed_stringing"]
# where the part sits on the heated bed — drives edge-cooling warp + adhesion risk
BED_POSITIONS = ["center", "edge", "corner"]


class Job(BaseModel):
    geometry_type: str
    material: str
    description: str = ""
    mesh_path: str | None = None
    bed_position: str = "center"   # center|edge|corner — affects warp/adhesion


class Environment(BaseModel):
    temp: float = Field(description="Ambient temperature °C")
    humidity: float = Field(description="Ambient humidity %")
    printer: str = "Creality Ender 3 V2"   # simulated machine (220×220×250 bed)


class PrintSettings(BaseModel):
    nozzle_temp: float
    bed_temp: float
    retraction_mm: float
    fan_pct: float
    first_layer_fan_pct: float
    layer_height: float = 0.2  # mm — drives virtual-print preview cross-sections


class RiskRegion(BaseModel):
    location: str               # human description, e.g. "underside of the overhang"
    risk: str                   # "sag" | "stringing" | "adhesion" | "warping" | ...
    why: str                    # one-line rationale
    anchor_hint: str | None = None  # optional geometry hint for the 3D annotation


class Advice(BaseModel):
    """The Chief Engineer's structured proposal (the LLM's output)."""

    reasoning: str              # the EVALUATION of precedent — the load-bearing text
    settings: PrintSettings
    risks: list[RiskRegion] = []


class LessonEntry(BaseModel):
    """Append-only ledger record. Schema is locked (02-ARCHITECTURE.md)."""

    job_id: str
    material: str
    geometry_type: str
    env_temp: float
    env_humidity: float
    outcome: str
    lesson: str
    source: str = "earned"      # "seed" | "earned"
    timestamp: str
