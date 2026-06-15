"""Generate fine-tune dataset on Modal GPU using the live base model.

Runs the same (material × geometry × temp × humidity) grid as prep_dataset.py,
but calls google/gemma-4-E4B-it directly on an A10G for fast, non-deterministic
targets. This fixes the parroting problem: the offline deterministic advisor
always returns identical settings; the live model produces varied, context-aware
judgment.

Run:  modal run learn/finetune/prep_dataset_modal.py
Out:  data/finetune/sft.{train,eval}.jsonl  (chat format, downloaded from volume)
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

# Grid: same as prep_dataset.py
MATERIALS = ["PLA", "PETG", "ABS", "TPU"]
GEOMETRY_TYPES = ["overhang", "bridge", "stringing", "adhesion", "vase"]
# Reduced grid for speed: 2 temps × 2 hums per split = 160 total (~30 min on A10G)
TEMPS_TRAIN = [18, 26, 32]
HUMS_TRAIN = [35, 55, 70]
TEMPS_EVAL = [22, 28]
HUMS_EVAL = [38, 68]

BASE_MODEL = os.environ.get("FINETUNE_BASE", "google/gemma-4-E4B-it")

# Resolve ROOT for local file paths; on Modal the file is at /root/
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
    app = modal.App("microfactory-node-prep-dataset")
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
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=temperature,
                    top_p=0.95,
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

        def _build_rows(temps: list[float], hums: list[float]) -> list[dict]:
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
                            advice = _infer(full)
                            if advice is None:
                                print(f"  [{n}/{total}] {mat}/{geo} @ {t}C/{h}% → FAILED, retrying...")
                                # Retry once with lower temperature
                                advice = _infer(full)
                            if advice is None:
                                print(f"  [{n}/{total}] {mat}/{geo} @ {t}C/{h}% → FAILED (skipping)")
                                continue
                            # Clean up reasoning
                            reasoning = advice.get("reasoning", "")
                            rows.append({"messages": [
                                {"role": "user", "content": full},
                                {"role": "assistant", "content": json.dumps(advice)},
                            ]})
                            settings = advice.get("settings", {})
                            print(f"  [{n}/{total}] {mat}/{geo} @ {t}C/{h}% → "
                                  f"nozzle={settings.get('nozzle_temp','?')} "
                                  f"bed={settings.get('bed_temp','?')} "
                                  f"fan={settings.get('fan_pct','?')}")
            return rows

        print("Generating TRAIN set...")
        train = _build_rows(TEMPS_TRAIN, HUMS_TRAIN)
        print(f"Train: {len(train)} rows")

        print("Generating EVAL set...")
        ev = _build_rows(TEMPS_EVAL, HUMS_EVAL)
        print(f"Eval: {len(ev)} rows")

        # Write to volume
        train_path = "/out/sft.train.jsonl"
        eval_path = "/out/sft.eval.jsonl"
        with open(train_path, "w") as f:
            for r in train:
                f.write(json.dumps(r) + "\n")
        with open(eval_path, "w") as f:
            for r in ev:
                f.write(json.dumps(r) + "\n")
        vol.commit()

        print(f"Saved: {train_path} ({len(train)} rows), {eval_path} ({len(ev)} rows)")
        return {"train_rows": len(train), "eval_rows": len(ev),
                "train_path": train_path, "eval_path": eval_path}

    @app.local_entrypoint()
    def main(base: str = BASE_MODEL, temperature: float = 0.7):
        result = generate.remote(base=base, temperature=temperature)
        print("\n=== GENERATION COMPLETE ===")
        print(json.dumps(result, indent=2))
        print("\nTo download the files locally:")
        print(f"  modal volume get microfactory-node-finetune sft.train.jsonl {ROOT / 'data' / 'finetune' / 'sft.train.jsonl'}")
        print(f"  modal volume get microfactory-node-finetune sft.eval.jsonl {ROOT / 'data' / 'finetune' / 'sft.eval.jsonl'}")


if __name__ == "__main__":
    print("Modal dataset generation. Install modal + `modal token set`, then:")
    print("  modal run learn/finetune/prep_dataset_modal.py")
