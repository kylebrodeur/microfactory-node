"""CLI: distill the sample sources into references + candidate lessons.

    uv run python -m ingest.run           # uses ingest/samples/
    uv run python -m ingest.run --dir /path/to/your/configs

Replace ingest/samples/ with your real Marlin/Klipper/Prusa files and research
JSONL (or point --dir at them). Heavy datasets (ablam/gcode, 3DTime) go through
ingest/modal_app.py, not here.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from core.ledger import LedgerManager
from ingest.distill import (
    ingest_candidate_lessons,
    parse_klipper_cfg,
    parse_marlin_config,
    parse_prusa_ini,
    write_references,
)

SAMPLES = Path(__file__).resolve().parent / "samples"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=SAMPLES, help="folder of source files")
    args = ap.parse_args()
    d = args.dir

    facts = []
    for p in d.glob("*.ini"):
        facts += parse_prusa_ini(p)
    for p in d.glob("*.cfg"):
        facts += parse_klipper_cfg(p)
    for p in list(d.glob("*.h")) + list(d.glob("*config*.txt")):
        facts += parse_marlin_config(p)
    n_ref = write_references(facts)
    print(f"references: {n_ref} facts → data/references.jsonl")
    for f in facts:
        print(f"  · {f.material:4} {f.param:14} {f.value:g}  ({f.source})")

    ledger = LedgerManager()
    total = 0
    for p in d.glob("*lessons*.jsonl"):
        k = ingest_candidate_lessons(p, ledger)
        total += k
        print(f"candidate lessons: +{k} from {p.name}")
    print(f"ledger now: {ledger.count()}")


if __name__ == "__main__":
    main()
