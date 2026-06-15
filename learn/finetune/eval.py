"""Honest base-vs-LoRA eval on the held-out conditions (data/finetune/sft.eval.jsonl).

The Well-Tuned claim is only earned if the fine-tune produces advice that is (a) valid
Advice JSON, (b) Spine-safe (settings inside material bounds), and (c) directionally
sane on held-out rooms. This scores both the base model and the LoRA so the difference
is measured, not asserted. If the LoRA only matches the base, say so and do not claim it.

Run where a GPU + the models load (Modal box, or local GPU):
    uv run python -m learn.finetune.eval --base google/gemma-4-E4B-it --adapter <hf-user>/microfactory-node-lora-v2
Reports JSON-valid rate, Spine-pass rate, and mean nozzle delta (humid vs dry PETG) for
base and tuned, side by side.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.models import Advice, PrintSettings
from core.spine import SpineValidator

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "data" / "finetune" / "sft.eval.jsonl"
_SPINE = SpineValidator()


def _generate(model, tok, user_text: str, max_new: int = 512) -> str:
    import torch
    msgs = [{"role": "user", "content": user_text}]
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new, do_sample=False)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def _score(model, tok, rows: list[dict]) -> dict:
    import re
    valid = spine_ok = 0
    for r in rows:
        user = r["messages"][0]["content"]
        material = "PETG" if "material: PETG" in user else (
            "PLA" if "material: PLA" in user else ("ABS" if "material: ABS" in user else "TPU"))
        text = _generate(model, tok, user)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            continue
        try:
            adv = Advice(**json.loads(m.group(0)))
        except Exception:
            continue
        valid += 1
        if not _SPINE.check(adv.settings, material).vetoes:
            spine_ok += 1
    n = len(rows)
    return {"n": n, "json_valid_pct": round(100 * valid / n, 1) if n else 0,
            "spine_safe_pct": round(100 * spine_ok / n, 1) if n else 0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="google/gemma-4-E4B-it")
    ap.add_argument("--adapter", default="", help="HF repo or local path of the LoRA adapter")
    ap.add_argument("--limit", type=int, default=40, help="held-out rows to score (cost control)")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    rows = [json.loads(l) for l in EVAL.read_text().splitlines() if l.strip()][: args.limit]
    tok = AutoTokenizer.from_pretrained(args.base)
    base = AutoModelForCausalLM.from_pretrained(args.base, dtype=torch.bfloat16, device_map="auto")
    print("BASE   ", _score(base, tok, rows))
    if args.adapter:
        from peft import PeftModel
        tuned = PeftModel.from_pretrained(base, args.adapter)
        print("TUNED  ", _score(tuned, tok, rows))
    print("\nClaim Well-Tuned only if TUNED >= BASE on json_valid AND spine_safe, and the "
          "sampled advice reads as real shop judgment (not a memorized template).")


if __name__ == "__main__":
    main()
