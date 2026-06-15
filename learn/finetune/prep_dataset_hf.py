"""Generate fine-tune dataset using HF Serverless Inference API.

Calls google/gemma-4-E4B-it via huggingface_hub.InferenceClient for each grid
point. Fast (~2-3s per call), free tier, no GPU cold start, no timeout issues.

Run:  uv run python -m learn.finetune.prep_dataset_hf
Out:  data/finetune/sft.{train,eval}.jsonl
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from huggingface_hub import InferenceClient

# Grid: same as prep_dataset.py
MATERIALS = ["PLA", "PETG", "ABS", "TPU"]
GEOMETRY_TYPES = ["overhang", "bridge", "stringing", "adhesion", "vase"]
TEMPS_TRAIN = [16, 20, 24, 30, 34]
HUMS_TRAIN = [30, 45, 60, 75]
TEMPS_EVAL = [22, 28]
HUMS_EVAL = [38, 68]

BASE_MODEL = os.environ.get("FINETUNE_BASE", "google/gemma-4-E4B-it")
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "finetune"

PERSONA = """You are Chief Engineer O'Brien: a veteran print-shop master who has run \
thousands of FDM jobs. You are terse and physical. You think in feeds, temps, \
cooling, and how the room affects the plastic. You do not hype. You propose \
settings; a deterministic Spine will veto anything unsafe, so propose what is \
*right*, not what is merely safe.

You reason about PRECEDENT before you decide. Weigh what transfers to THIS job \
and what does not. If nothing close applies, say "no close precedent" and reason \
from material properties."""

OUTPUT_CONTRACT = """Respond ONLY with valid JSON, no prose outside it, in exactly this shape:
{
  "reasoning": "2-4 sentences. START with your evaluation of prior knowledge: what transfers, what doesn't, and why. Then the decision.",
  "settings": {
    "nozzle_temp": <C>, "bed_temp": <C>, "retraction_mm": <mm>,
    "fan_pct": <0-100>, "first_layer_fan_pct": <0-100>
  },
  "risks": [
    {"location": "where on the part", "risk": "sag|stringing|adhesion|warping|delamination",
     "why": "one line", "anchor_hint": "overhang|bridge|first_layer|corner|null"}
  ]
}"""

USER_TURN = "Give your recommendation for THIS job now."


def _build_prompt(material: str, geometry: str, temp: float, hum: float) -> str:
    return (
        f"{PERSONA}\n\n"
        f"CURRENT JOB:\n"
        f"  material: {material}\n"
        f"  geometry: {geometry}\n"
        f"  description: (none given)\n\n"
        f"ENVIRONMENT (right now in the room):\n"
        f"  temperature: {temp:.0f}°C\n"
        f"  humidity: {hum:.0f}% RH\n\n"
        f"HISTORICAL PRECEDENT:\n"
        f"  (none) — no prior job matches this material + geometry. "
        f"Reason from material properties and say so plainly.\n\n"
        f"{OUTPUT_CONTRACT}"
    )


def _infer(client: InferenceClient, user_text: str) -> dict | None:
    try:
        resp = client.chat_completion(
            messages=[{"role": "user", "content": user_text}],
            model=BASE_MODEL,
            max_tokens=512,
            temperature=0.7,
            top_p=0.95,
        )
        text = resp.choices[0].message.content.strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        return json.loads(m.group(0))
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def _build_rows(client: InferenceClient, temps: list[float], hums: list[float]) -> list[dict]:
    rows = []
    total = len(MATERIALS) * len(GEOMETRY_TYPES) * len(temps) * len(hums)
    n = 0
    for mat in MATERIALS:
        for geo in GEOMETRY_TYPES:
            for t in temps:
                for h in hums:
                    n += 1
                    prompt = _build_prompt(mat, geo, t, h)
                    full = f"{prompt}\n\n{USER_TURN}"
                    t0 = time.time()
                    advice = _infer(client, full)
                    elapsed = time.time() - t0
                    if advice is None:
                        print(f"  [{n}/{total}] {mat}/{geo} @ {t}C/{h}% → FAILED ({elapsed:.1f}s)")
                        # Retry once
                        time.sleep(1)
                        advice = _infer(client, full)
                    if advice is None:
                        print(f"  [{n}/{total}] {mat}/{geo} @ {t}C/{h}% → SKIPPED")
                        continue
                    rows.append({"messages": [
                        {"role": "user", "content": full},
                        {"role": "assistant", "content": json.dumps(advice)},
                    ]})
                    settings = advice.get("settings", {})
                    print(f"  [{n}/{total}] {mat}/{geo} @ {t}C/{h}% → "
                          f"nozzle={settings.get('nozzle_temp','?')} "
                          f"bed={settings.get('bed_temp','?')} "
                          f"fan={settings.get('fan_pct','?')} "
                          f"({elapsed:.1f}s)")
    return rows


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("ERROR: HF_TOKEN not set. Run: export HF_TOKEN=$(hf token)")
        sys.exit(1)

    client = InferenceClient(token=token)
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"Model: {BASE_MODEL}")
    print(f"Generating TRAIN set ({len(MATERIALS)}×{len(GEOMETRY_TYPES)}×{len(TEMPS_TRAIN)}×{len(HUMS_TRAIN)} = {len(MATERIALS)*len(GEOMETRY_TYPES)*len(TEMPS_TRAIN)*len(HUMS_TRAIN)} rows)...")
    train = _build_rows(client, TEMPS_TRAIN, HUMS_TRAIN)
    print(f"Train: {len(train)} rows")

    print(f"\nGenerating EVAL set ({len(MATERIALS)}×{len(GEOMETRY_TYPES)}×{len(TEMPS_EVAL)}×{len(HUMS_EVAL)} = {len(MATERIALS)*len(GEOMETRY_TYPES)*len(TEMPS_EVAL)*len(HUMS_EVAL)} rows)...")
    ev = _build_rows(client, TEMPS_EVAL, HUMS_EVAL)
    print(f"Eval: {len(ev)} rows")

    (OUT / "sft.train.jsonl").write_text("\n".join(json.dumps(r) for r in train) + "\n")
    (OUT / "sft.eval.jsonl").write_text("\n".join(json.dumps(r) for r in ev) + "\n")
    print(f"\nSaved: {OUT}/sft.train.jsonl ({len(train)} rows), {OUT}/sft.eval.jsonl ({len(ev)} rows)")


if __name__ == "__main__":
    main()
