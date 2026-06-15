"""Outcome simulator — the deterministic stand-in for the printer + sensors.

⚠ THIS IS THE PHYSICAL-WORLD PLACEHOLDER. See ../SIMULATION.md. On real
hardware this whole module is replaced by: stream g-code to the printer →
read env sensors → a camera + the 3D-ADAM defect classifier reports the
outcome. Here we model the *same* physics the seed lessons describe, so the
learning loop is reproducible and runs with no hardware and no network.

Crucially this is NOT the model grading its own work. The Chief Engineer
proposes settings; this separate, deterministic world returns an outcome the
model never sees in advance — exactly the role a printer + sensors play.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.models import Environment, Job, PrintSettings

# Per-material workable bands (nozzle °C lo/ideal/hi, bed °C lo).
BANDS = {
    "PLA":  {"n_lo": 195, "n_id": 205, "n_hi": 225, "bed_lo": 52},
    "PETG": {"n_lo": 230, "n_id": 240, "n_hi": 252, "bed_lo": 70},
    "ABS":  {"n_lo": 235, "n_id": 248, "n_hi": 262, "bed_lo": 95},
    "TPU":  {"n_lo": 215, "n_id": 228, "n_hi": 240, "bed_lo": 40},
}

# outcome strings stay inside models.OUTCOMES; failure_mode carries the detail.
_MODE_TO_OUTCOME = {
    "none": "success",
    "stringing": "failed_stringing",
    "sag": "failed_sag",
    "warp": "failed_sag",
    "adhesion": "failed_sag",
    "under_extrusion": "failed_sag",
}


@dataclass
class SimResult:
    outcome: str           # in models.OUTCOMES
    quality: float         # 0..1 — how clean the (simulated) print came out
    failure_mode: str      # "none"|"sag"|"stringing"|"adhesion"|"warp"|"under_extrusion"
    penalties: dict[str, float] = field(default_factory=dict)

    @property
    def detail(self) -> str:
        if self.failure_mode == "none":
            return f"clean print (quality {self.quality:.2f})"
        worst = max(self.penalties, key=self.penalties.get) if self.penalties else self.failure_mode
        return f"{self.failure_mode} (quality {self.quality:.2f}, dominant cost: {worst})"


def simulate(settings: PrintSettings, job: Job, env: Environment) -> SimResult:
    """Deterministic physics-lite outcome. Higher quality = cleaner print."""
    b = BANDS.get(job.material.upper(), BANDS["PLA"])
    geo = job.geometry_type
    s = settings
    pen: dict[str, float] = {}

    # 1) Nozzle temperature band — too cold under-extrudes, too hot oozes.
    if s.nozzle_temp < b["n_lo"]:
        pen["under_extrusion"] = min(0.5, (b["n_lo"] - s.nozzle_temp) / 40)
    over = max(0.0, s.nozzle_temp - b["n_hi"]) / 40  # feeds stringing/sag below

    # 2) Cooling vs. unsupported geometry (overhang/bridge/vase) — the sag axis.
    if geo in ("overhang", "bridge", "vase"):
        need = {"overhang": 60, "bridge": 82, "vase": 50}[geo] + max(0.0, env.temp - 20) * 3.5
        sag = max(0.0, (need - s.fan_pct)) / 100 * 0.7 + over * 0.6
        if sag > 0:
            pen["sag"] = min(0.6, sag)

    # 3) Stringing — hygroscopic materials in humid air, hot nozzle, weak retraction.
    hygro = job.material.upper() in ("PETG", "TPU", "ABS")
    if geo == "stringing" or hygro or env.humidity > 50:
        w = 0.6 if geo == "stringing" else 0.4
        string = (max(0.0, env.humidity - 45) / 55 * 0.45
                  + over * 0.45
                  + max(0.0, 2.0 - s.retraction_mm) / 2 * 0.30) * w
        if string > 0.02:
            pen["stringing"] = min(0.6, string)

    # 4) Adhesion — first layer needs a hot enough bed and calm air.
    if geo == "adhesion":
        adh = (max(0.0, b["bed_lo"] - s.bed_temp) / 30 * 0.6
               + s.first_layer_fan_pct / 100 * 0.4)
        if adh > 0.02:
            pen["adhesion"] = min(0.6, adh)

    # 5) ABS hates fan — too much cooling cracks/warps it.
    if job.material.upper() == "ABS" and s.fan_pct > 40:
        pen["warp"] = min(0.4, (s.fan_pct - 40) / 100 * 0.6)

    # 6) Build-plate position — bed edges/corners run cooler and see more draft, so
    #    warp + first-layer adhesion suffer there; worst for high-shrink materials.
    #    'center' (default) = 0 → no change to prior behavior. See ../SIMULATION.md.
    pos_sev = {"center": 0.0, "edge": 0.5, "corner": 1.0}.get(getattr(job, "bed_position", "center"), 0.0)
    if pos_sev:
        mat = {"ABS": 0.45, "PETG": 0.18, "PLA": 0.06, "TPU": 0.05}.get(job.material.upper(), 0.10)
        pen["warp"] = min(0.6, pen.get("warp", 0.0) + pos_sev * mat)
        pen["adhesion"] = min(0.6, pen.get("adhesion", 0.0) + pos_sev * mat * 0.5)

    total = sum(pen.values())
    quality = max(0.0, min(1.0, 1.0 - total))
    if quality >= 0.7 or not pen:
        return SimResult("success", quality, "none", pen)
    mode = max(pen, key=pen.get)
    return SimResult(_MODE_TO_OUTCOME.get(mode, "failed_sag"), quality, mode, pen)
