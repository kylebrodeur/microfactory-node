"""Calibration harness — measure how well sim/outcome.py matches REAL data.

The simulator is the one simulated boundary (SIMULATION.md). This module scores
its predictions against observed print outcomes so the constants in
`sim/outcome.py` (BANDS + penalty terms) can be tuned to reality instead of
guessed. Used by the `tune-simulator` skill; also runnable directly:

    uv run python -m sim.calibrate                # uses the sample observations
    uv run python -m sim.calibrate --data path/to/obs.jsonl

Observation row (one JSON object per line):
    {"material":"PETG","geometry_type":"bridge","env_temp":29,"env_humidity":62,
     "nozzle_temp":235,"bed_temp":80,"retraction_mm":4,"fan_pct":40,
     "first_layer_fan_pct":0,"outcome":"failed_sag","quality":0.45}
`quality` (0-1) is optional — include it when you have a graded result (e.g. the
3D-ADAM defect classifier); outcome is always one of models.OUTCOMES.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from core.models import Environment, Job, OUTCOMES, PrintSettings
from sim.outcome import simulate

SAMPLE = Path(__file__).resolve().parent / "calibration" / "observations.sample.jsonl"

_SETTING_KEYS = ("nozzle_temp", "bed_temp", "retraction_mm", "fan_pct", "first_layer_fan_pct")


@dataclass
class Mismatch:
    obs: dict
    predicted: str
    expected: str
    penalties: dict


@dataclass
class Report:
    n: int = 0
    correct: int = 0
    quality_abs_err: float = 0.0
    quality_n: int = 0
    confusion: dict[tuple[str, str], int] = field(default_factory=dict)
    mismatches: list[Mismatch] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct / self.n if self.n else 0.0

    @property
    def quality_mae(self) -> float | None:
        return self.quality_abs_err / self.quality_n if self.quality_n else None


def load_observations(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def evaluate(observations: list[dict]) -> Report:
    """Run the simulator over observations and score outcome-match + quality error."""
    r = Report()
    for o in observations:
        if o.get("outcome") not in OUTCOMES:
            continue
        settings = PrintSettings(**{k: float(o[k]) for k in _SETTING_KEYS})
        job = Job(geometry_type=o["geometry_type"], material=o["material"])
        env = Environment(temp=float(o["env_temp"]), humidity=float(o["env_humidity"]))
        res = simulate(settings, job, env)
        r.n += 1
        expected = o["outcome"]
        r.confusion[(expected, res.outcome)] = r.confusion.get((expected, res.outcome), 0) + 1
        if res.outcome == expected:
            r.correct += 1
        else:
            r.mismatches.append(Mismatch(o, res.outcome, expected, res.penalties))
        if "quality" in o:
            r.quality_abs_err += abs(res.quality - float(o["quality"]))
            r.quality_n += 1
    return r


def format_report(r: Report) -> str:
    lines = [
        f"observations:     {r.n}",
        f"outcome accuracy: {r.accuracy*100:.1f}%  ({r.correct}/{r.n})",
    ]
    if r.quality_mae is not None:
        lines.append(f"quality MAE:      {r.quality_mae:.3f}  (over {r.quality_n} graded rows)")
    lines.append("confusion (expected → predicted):")
    for (exp, pred), c in sorted(r.confusion.items(), key=lambda x: -x[1]):
        mark = "✓" if exp == pred else "✗"
        lines.append(f"  {mark} {exp:18} → {pred:18} ×{c}")
    if r.mismatches:
        lines.append("mismatches (diagnose which constant to move):")
        for m in r.mismatches:
            worst = max(m.penalties, key=m.penalties.get) if m.penalties else "none"
            lines.append(
                f"  · {m.obs['material']}/{m.obs['geometry_type']} "
                f"@ {m.obs['env_temp']:.0f}°C/{m.obs['env_humidity']:.0f}% "
                f"fan={m.obs['fan_pct']:.0f} noz={m.obs['nozzle_temp']:.0f} "
                f"ret={m.obs['retraction_mm']:.1f}: predicted {m.predicted}, real {m.expected} "
                f"(dominant sim cost: {worst}; penalties={ {k: round(v,2) for k,v in m.penalties.items()} })"
            )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=SAMPLE)
    args = ap.parse_args()
    obs = load_observations(args.data)
    print(f"# calibration against {args.data}")
    print(format_report(evaluate(obs)))


if __name__ == "__main__":
    main()
