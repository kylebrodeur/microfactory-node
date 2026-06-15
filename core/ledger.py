"""Append-only lesson ledger + environment-keyed retrieval.

Modeled on pi-qmd-ledger's `append_ledger` (pattern-review.md §3) but with the
qmd embeddings / vector search deliberately left behind. Retrieval is the
locked design: exact match on material AND geometry_type, then rank by
Euclidean distance on NORMALIZED [temp, humidity], top 2-3. No vector DB.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from .models import LessonEntry

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LEDGER_PATH = DATA_DIR / "lessons.jsonl"

# Normalization ranges (02-ARCHITECTURE.md / 04-BUILD-PROMPT.md): map both env
# axes to 0-1 so humidity's 0-100 span doesn't swamp temperature in the metric.
TEMP_MIN, TEMP_MAX = 15.0, 35.0
HUM_MIN, HUM_MAX = 20.0, 80.0


def _norm(temp: float, humidity: float) -> tuple[float, float]:
    t = (temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)
    h = (humidity - HUM_MIN) / (HUM_MAX - HUM_MIN)
    return t, h


class LedgerManager:
    def __init__(self, path: Path = LEDGER_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    # --- storage -----------------------------------------------------------
    def all(self) -> list[LessonEntry]:
        out: list[LessonEntry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                out.append(LessonEntry(**json.loads(line)))
            except Exception:
                continue  # never let one bad line crash the demo
        return out

    def append(self, entry: LessonEntry) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

    def count(self) -> dict[str, int]:
        buckets = {"seed": 0, "earned": 0, "ingested": 0, "sim": 0}
        for e in self.all():
            buckets[e.source if e.source in buckets else "earned"] += 1
        buckets["total"] = sum(buckets.values())
        return buckets

    def reset_to_baseline(self, keep_sources: tuple[str, ...] = ("seed", "ingested")) -> int:
        """Drop runtime-accumulated lessons (earned/sim), keeping only the curated
        baseline. Returns the count removed. Powers the UI 'reset' button — works on
        the Space's ephemeral filesystem where `git checkout` isn't available."""
        entries = self.all()
        kept = [e for e in entries if e.source in keep_sources]
        with self.path.open("w", encoding="utf-8") as f:
            for e in kept:
                f.write(e.model_dump_json() + "\n")
        return len(entries) - len(kept)

    # --- retrieval (the thesis-critical query) -----------------------------
    def retrieve(
        self, material: str, geometry_type: str, temp: float, humidity: float, k: int = 3
    ) -> list[tuple[LessonEntry, float]]:
        """Return up to k (lesson, env_distance) sorted nearest-first.

        Exact match on material AND geometry_type; ranked by normalized
        Euclidean env-distance. Returns [] when no precedent matches — which
        is a *valid, strong* outcome (the model reasons from material
        properties instead).
        """
        tn, hn = _norm(temp, humidity)
        scored: list[tuple[LessonEntry, float]] = []
        for e in self.all():
            if e.material != material or e.geometry_type != geometry_type:
                continue
            etn, ehn = _norm(e.env_temp, e.env_humidity)
            dist = math.hypot(tn - etn, hn - ehn)
            scored.append((e, dist))
        scored.sort(key=lambda x: x[1])
        return scored[:k]
