"""Seed the ledger on first run.

If `data/lessons.jsonl` is empty, load the 12 curated seed lessons
(`data/seed_lessons.jsonl`, source="seed") so the demo starts with a real
capability corpus and the ledger visibly grows seed → earned.
"""

from __future__ import annotations

import json
from pathlib import Path

from .ledger import LedgerManager
from .models import LessonEntry

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_lessons.jsonl"


def ensure_seeded(ledger: LedgerManager) -> int:
    """Load seeds if the ledger has no entries. Returns count loaded."""
    if ledger.all():
        return 0
    if not SEED_PATH.exists():
        return 0
    loaded = 0
    for line in SEED_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = LessonEntry(**json.loads(line))
        except Exception:
            continue
        entry.source = "seed"
        ledger.append(entry)
        loaded += 1
    return loaded
