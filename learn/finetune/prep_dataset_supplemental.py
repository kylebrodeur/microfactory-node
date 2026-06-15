"""Supplemental dataset generation — high temperature for more variation.

Runs a small grid with temperature=0.9 to produce more divergent outputs,
then merges with existing sft.train.jsonl. This adds per-condition variation
that the conservative temperature=0.7 run missed.

Run:  modal run learn/finetune/prep_dataset_supplemental.py
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
# Small grid: 2 temps × 2 hums = 40 supplemental examples
TEMPS = [22, 30]
HUMS = [40, 65]

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
    app = modal.App("microfactory-node-prep-supplemental")
    image = (
        modal.Image.debian_slim(python_version="3.12")
        .pip_install("torch", "transformers>=4.49", "accelerate>=0.34", "huggingface_hub")
    )
    vol = modal.Volume.from_name("microfactory-node-finetune", create_if_missing=True)

    @app.function(image=image, gpu="A10G", timeout=3600,
                  volumes={"/out": vol},
                  secrets=[modal.Secret.from_name("chief-engineer-secrets")])
    def generate(base: str = BASE_MODEL, temperature: float = 0.9) -> dict:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        print(f"Loading {base}...")
        tok = AutoTokenizer.from_pretrained(base)
        model = AutoModelForCausalLM.from_pretrained(
            base, dtype=torch.bfloat16, device_map="auto"
        )
        print(f"Model loaded on {model.device}")
        print(f"Temperature: {temperature} (high — forcing more variation)")

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

        rows = []
        total = len(MATERIALS) * len(GEOMETRY_TYPES) * len(TEMPS) * len(HUMS)
        n = 0
        for mat in MATERIALS:
            for geo in GEOMETRY_TYPES:
                for t in TEMPS:
                    for h in HUMS:
                        n += 1
                        full = f"{_build_prompt(mat, geo, t, h)}\n\n{USER_TURN}"
                        advice = _infer(full)
                        if advice is None:
                            advice = _infer(full)
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

        # Append to existing train file (don't overwrite)
        existing = []
        try:
            with open("/out/sft.train.jsonl", "r") as f:
                existing = [json.loads(l) for l in f.read().splitlines() if l.strip()]
        except Exception:
            pass

        all_rows = existing + rows
        with open("/out/sft.train.jsonl", "w") as f:
            for r in all_rows:
                f.write(json.dumps(r) + "\n")
        vol.commit()

        print(f"Supplemental: {len(rows)} new rows")
        print(f"Total train: {len(all_rows)} rows (was {len(existing)}, added {len(rows)})")
        return {"new_rows": len(rows), "total_train": len(all_rows)}

    @app.local_entrypoint()
    def main(base: str = BASE_MODEL, temperature: float = 0.9):
        result = generate.remote(base=base, temperature=temperature)
        print("\n=== SUPPLEMENTAL COMPLETE ===")
        print(json.dumps(result, indent=2))
        print("\nDownload merged dataset:")
        print("  modal volume get microfactory-node-finetune sft.train.jsonl data/finetune/sft.train.jsonl --force")


if __name__ == "__main__":
    print("Supplemental high-temperature dataset generation. Run:")
    print("  modal run learn/finetune/prep_dataset_supplemental.py")
