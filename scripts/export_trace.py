"""Export the lesson ledger as a Hugging Face Datasets-ready trace.

Earns the 'Sharing is Caring' badge: the agent's accumulated knowledge, posted
openly for others to learn from. Writes a clean JSONL + a dataset card.
Run: `make trace`  (or `uv run python -m scripts.export_trace`)  →  dist/
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core.ledger import LedgerManager
from core.seed_lessons import ensure_seeded

DIST = Path(__file__).resolve().parent.parent / "dist"
CARD = """---
license: mit
task_categories: [tabular-regression]
tags: [3d-printing, additive-manufacturing, agent-trace, build-small-hackathon]
---

# Chief Engineer — Lesson Ledger

Environment-keyed 3D-printing lessons accumulated by **The Chief Engineer**, a small local
Gemma agent built for the HF Build Small hackathon (Backyard AI). Each row is a durable lesson
keyed to material, geometry, and ambient conditions — `seed` rows bootstrap the corpus,
`earned` rows are written by the agent after a human-reported print outcome.

Schema: `job_id, material, geometry_type, env_temp, env_humidity, outcome, lesson, source, timestamp`.
"""


def export() -> Path:
    led = LedgerManager()
    if not led.all():
        ensure_seeded(led)
    DIST.mkdir(parents=True, exist_ok=True)

    out = DIST / "chief_engineer_ledger.jsonl"
    with out.open("w", encoding="utf-8") as f:
        for e in led.all():
            f.write(e.model_dump_json() + "\n")
    (DIST / "README.md").write_text(CARD, encoding="utf-8")

    c = led.count()
    print(f"exported {c['total']} lessons ({c['seed']} seed · {c['earned']} earned) → {out}")
    print(f"dataset card → {DIST / 'README.md'}")
    print("publish:  hf upload <user>/chief-engineer-ledger dist/ . --repo-type dataset")
    return out


if __name__ == "__main__":
    export()
