"""Fast half-grid dataset generation — runs in parallel with full grid.

Half the train examples (90 instead of 180) for faster turnaround.
Same model, same format. Use when you want to start training sooner.

Run:  modal run learn/finetune/prep_dataset_fast.py
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

try:
    import modal
except Exception:
    modal = None  # type: ignore

MATERIALS = ["PLA", "PETG", "ABS", "TPU"]
GEOMETRY_TYPES = ["overhang", "bridge", "stringing", "adhesion", "vase"]
# Half grid: 2 temps × 3 hums = 90 train (vs 180 full)
TEMPS_TRAIN = [18, 32]
HUMS_TRAIN = [35, 55, 70]
TEMPS_EVAL = [22, 28]
HUMS_EVAL = [38, 68]

BASE_MODEL = os.environ.get("FINETUNE_BASE", "google/gemma-4-E4B-it")

try:
    ROOT = Path(__file__).resolve().parents[2]
except IndexError:
    ROOT = Path(__file__).resolve().parent

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


if modal is not None:
    app = modal.App("microfactory-node-prep-dataset-fast")
    image = (
        modal.Image.debian_slim(python_version="3.12")
        .pip_install("torch", "transformers>=4.49", "accelerate>=0.34", "huggingface_hub")
    )
    vol = modal.Volume.from_name("microfactory-node-finetune", create_if_missing=True)

    @app.function(image=image, gpu="A10G", timeout=7200,
                  volumes={"/out": vol},
                  secrets=[modal.Secret.from_name("chief-engineer-secrets")])
    def generate(base: str = BASE_MODEL, temperature: float = 0.7) -> dict:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print(f"Loading {base}...")
        tok = AutoTokenizer.from_pretrained(base)
        model = AutoModelForCausalLM.from_pretrained(
            base, dtype=torch.bfloat16, device_map="auto"
        )
        print(f"Model loaded on {model.device}")

        def _infer(user_text: str) -> dict | None:
            msgs = [{"role": "user", "content": user_text}]
            prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inputs = tok(prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                out = model.generate(
                    **inputs, max_new_tokens=512,
                    do_sample=True, temperature=temperature, top_p=0.95,
                )
            text = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                return None
            try:
                return json.loads(m.group(0))
            except Exception:
                return None

        def _build_rows(temps, hums, label):
            rows = []
            total = len(MATERIALS) * len(GEOMETRY_TYPES) * len(temps) * len(hums)
            n = 0
            for mat in MATERIALS:
                for geo in GEOMETRY_TYPES:
                    for t in temps:
                        for h in hums:
                            n += 1
                            full = f"{_build_prompt(mat, geo, t, h)}\n\n{USER_TURN}"
                            advice = _infer(full)
                            if advice is None:
                                advice = _infer(full)  # retry once
                            if advice is None:
                                print(f"  [{n}/{total}] {mat}/{geo} @ {t}C/{h}% → SKIPPED")
                                continue
                            rows.append({"messages": [
                                {"role": "user", "content": full},
                                {"role": "assistant", "content": json.dumps(advice)},
                            ]})
                            s = advice.get("settings", {})
                            print(f"  [{n}/{total}] {mat}/{geo} @ {t}C/{h}% → "
                                  f"nozzle={s.get('nozzle_temp','?')} bed={s.get('bed_temp','?')} fan={s.get('fan_pct','?')}")
            return rows

        print(f"Generating TRAIN set ({len(MATERIALS)}×{len(GEOMETRY_TYPES)}×{len(TEMPS_TRAIN)}×{len(HUMS_TRAIN)} = {len(MATERIALS)*len(GEOMETRY_TYPES)*len(TEMPS_TRAIN)*len(HUMS_TRAIN)})...")
        train = _build_rows(TEMPS_TRAIN, HUMS_TRAIN, "train")
        print(f"Train: {len(train)} rows")

        print(f"Generating EVAL set...")
        ev = _build_rows(TEMPS_EVAL, HUMS_EVAL, "eval")
        print(f"Eval: {len(ev)} rows")

        with open("/out/sft.train.jsonl", "w") as f:
            for r in train:
                f.write(json.dumps(r) + "\n")
        with open("/out/sft.eval.jsonl", "w") as f:
            for r in ev:
                f.write(json.dumps(r) + "\n")
        vol.commit()

        print(f"Saved: /out/sft.train.jsonl ({len(train)}), /out/sft.eval.jsonl ({len(ev)})")
        return {"train_rows": len(train), "eval_rows": len(ev)}

    @app.local_entrypoint()
    def main(base: str = BASE_MODEL, temperature: float = 0.7):
        result = generate.remote(base=base, temperature=temperature)
        print("\n=== GENERATION COMPLETE ===")
        print(json.dumps(result, indent=2))
        print("\nDownload:")
        print("  modal volume get microfactory-node-finetune sft.train.jsonl data/finetune/sft.train.jsonl")
        print("  modal volume get microfactory-node-finetune sft.eval.jsonl data/finetune/sft.eval.jsonl")


if __name__ == "__main__":
    print("Fast half-grid dataset generation. Run:")
    print("  modal run learn/finetune/prep_dataset_fast.py")
