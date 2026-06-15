"""Build a supervised fine-tune dataset by DISTILLING the node's own judgment.

The live node decides with retrieval + a learned policy + a deterministic Spine.
This script turns that behaviour into (prompt -> Advice JSON) pairs over a grid of
(material, geometry, room) conditions, so a small Gemma can be fine-tuned to carry
the same judgment in its weights. That is the "Well-Tuned" frontier the writeup
names: visible memory (retrieval) stays the live path, and this bakes a copy of the
judgment into the weights.

Honesty: targets here are the node's *structured* output (the same Advice JSON the
live call returns). Offline, that is the deterministic advisor over real retrieved
precedent, so it is a faithful distillation of the system, not invented data. For a
higher-fidelity teacher, run with a live model up (Ollama) so `advise()` returns the
real Gemma output instead of the fallback; the pair format is identical either way.

Run:  uv run python -m learn.finetune.prep_dataset
Out:  data/finetune/sft.train.jsonl  +  data/finetune/sft.eval.jsonl  (chat format)
"""

from __future__ import annotations

import json
from pathlib import Path

from core import seed_lessons
from core.chief_engineer import advise
from core.ledger import LedgerManager
from core.models import Environment, GEOMETRY_TYPES, Job, MATERIALS
from core.prompts import build_system_prompt
from learn.policy import LearnedPolicy

try:
    from ingest.distill import reference_block
except Exception:  # pragma: no cover
    def reference_block(_m):  # type: ignore
        return []

OUT = Path(__file__).resolve().parents[2] / "data" / "finetune"
USER_TURN = "Give your recommendation for THIS job now."

# Grid: hold out two room points for eval so we measure generalization, not recall.
TEMPS_TRAIN = [16, 20, 24, 30, 34]
HUMS_TRAIN = [30, 45, 60, 75]
TEMPS_EVAL = [22, 28]
HUMS_EVAL = [38, 68]


def _pair(ledger: LedgerManager, policy: LearnedPolicy, material: str, geo: str,
          temp: float, hum: float) -> dict:
    job = Job(geometry_type=geo, material=material)
    env = Environment(temp=float(temp), humidity=float(hum))
    retrieved = ledger.retrieve(material, geo, env.temp, env.humidity)
    refs = reference_block(material)
    note = policy.policy_note(material, geo, env)
    system = build_system_prompt(job, env, retrieved, refs, note)
    advice = advise(job, env, retrieved, refs, note).advice   # offline -> deterministic distillation
    advice.reasoning = advice.reasoning.replace("[fallback] ", "").strip()  # drop the offline marker
    # Gemma has no system role: fold the system prompt into the first user turn,
    # exactly as the live inference path does (core/llm_zerogpu._build_prompt).
    return {"messages": [
        {"role": "user", "content": f"{system}\n\n{USER_TURN}"},
        {"role": "assistant", "content": advice.model_dump_json()},
    ]}


def build(temps: list[float], hums: list[float]) -> list[dict]:
    ledger = LedgerManager()
    seed_lessons.ensure_seeded(ledger)
    policy = LearnedPolicy()
    rows = []
    for m in MATERIALS:
        for g in GEOMETRY_TYPES:
            for t in temps:
                for h in hums:
                    rows.append(_pair(ledger, policy, m, g, t, h))
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    train = build(TEMPS_TRAIN, HUMS_TRAIN)
    ev = build(TEMPS_EVAL, HUMS_EVAL)
    (OUT / "sft.train.jsonl").write_text("\n".join(json.dumps(r) for r in train) + "\n")
    (OUT / "sft.eval.jsonl").write_text("\n".join(json.dumps(r) for r in ev) + "\n")
    print(f"train={len(train)} eval={len(ev)} → {OUT}/sft.train.jsonl + sft.eval.jsonl")
    print(f"  ({len(MATERIALS)} materials × {len(GEOMETRY_TYPES)} geometries × grid)")
    print("  targets = the node's structured Advice (offline = deterministic distillation;")
    print("  start `ollama serve` first to distill the live Gemma instead).")


if __name__ == "__main__":
    main()
