"""Modal wrapper for eval.py — runs the honest base-vs-LoRA eval on a GPU."""

import modal

app = modal.App("microfactory-node-eval")

# On Modal, file is at /root/eval_modal.py; locally it's deeper
try:
    _ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
except IndexError:
    _ROOT = __import__("pathlib").Path(__file__).resolve().parent

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "transformers>=4.49", "peft>=0.11", "huggingface_hub")
    .add_local_file(
        str(_ROOT / "data" / "finetune" / "sft.eval.jsonl"),
        "/root/sft.eval.jsonl")
)

@app.function(image=image, gpu="A10G", timeout=3600,
              secrets=[modal.Secret.from_name("chief-engineer-secrets")])
def evaluate_chunk(base: str, adapter: str, rows: list[dict]) -> dict:
    import json
    import re
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    # Minimal local copies of what eval needs
    class SpineValidator:
        BOUNDS = {
            "PLA": {"nozzle_temp": (190, 230), "bed_temp": (0, 70), "fan_speed": (0, 100)},
            "PETG": {"nozzle_temp": (220, 260), "bed_temp": (60, 90), "fan_speed": (0, 50)},
            "ABS": {"nozzle_temp": (220, 260), "bed_temp": (80, 110), "fan_speed": (0, 30)},
            "TPU": {"nozzle_temp": (210, 240), "bed_temp": (0, 60), "fan_speed": (0, 40)},
        }
        def check(self, settings: dict, material: str) -> dict:
            vetoes = []
            bounds = self.BOUNDS.get(material, {})
            for k, (lo, hi) in bounds.items():
                v = settings.get(k)
                if v is not None and (v < lo or v > hi):
                    vetoes.append(f"{k}={v} out of [{lo},{hi}]")
            return {"vetoes": vetoes}

    _SPINE = SpineValidator()

    def _generate(model, tok, user_text: str, max_new: int = 512) -> str:
        msgs = [{"role": "user", "content": user_text}]
        prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = tok(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=max_new, do_sample=False)
        return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    def _score(model, tok, rows: list[dict], label: str) -> dict:
        valid = spine_ok = 0
        samples = []
        for i, r in enumerate(rows):
            user = r["messages"][0]["content"]
            material = "PETG" if "material: PETG" in user else (
                "PLA" if "material: PLA" in user else ("ABS" if "material: ABS" in user else "TPU"))
            text = _generate(model, tok, user)
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                if len(samples) < 5:
                    samples.append({"idx": i, "material": material, "raw_output": text[:200], "valid_json": False})
                continue
            try:
                adv = json.loads(m.group(0))
            except Exception:
                if len(samples) < 5:
                    samples.append({"idx": i, "material": material, "raw_output": text[:200], "valid_json": False})
                continue
            valid += 1
            spine_result = _SPINE.check(adv.get("settings", {}), material)
            if not spine_result["vetoes"]:
                spine_ok += 1
            if len(samples) < 5:
                samples.append({
                    "idx": i, "material": material,
                    "settings": adv.get("settings", {}),
                    "reasoning": str(adv.get("reasoning", ""))[:200],
                    "valid_json": True,
                    "spine_safe": not spine_result["vetoes"],
                    "vetoes": spine_result["vetoes"],
                })
        n = len(rows)
        return {"label": label, "n": n,
                "valid": valid, "spine_ok": spine_ok,
                "json_valid_pct": round(100 * valid / n, 1) if n else 0,
                "spine_safe_pct": round(100 * spine_ok / n, 1) if n else 0,
                "samples": samples}

    print(f"Evaluating {len(rows)} held-out examples for BASE...")
    tok = AutoTokenizer.from_pretrained(base)
    model = AutoModelForCausalLM.from_pretrained(base, dtype=torch.bfloat16, device_map="auto")
    
    base_result = _score(model, tok, rows, "BASE")
    print(f"BASE: json_valid={base_result['json_valid_pct']}% spine_safe={base_result['spine_safe_pct']}%")
    
    tuned_result = None
    if adapter:
        print(f"Loading adapter {adapter}...")
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter)
        tuned_result = _score(model, tok, rows, "TUNED")
        print(f"TUNED: json_valid={tuned_result['json_valid_pct']}% spine_safe={tuned_result['spine_safe_pct']}%")
        
    return {"base": base_result, "tuned": tuned_result}


@app.local_entrypoint()
def main(base: str = "google/gemma-4-E4B-it", adapter: str = "", limit: int = 80):
    import json
    local_path = _ROOT / "data" / "finetune" / "sft.eval.jsonl"
    rows = [json.loads(l) for l in open(local_path).read().splitlines() if l.strip()][:limit]
    
    # 40 rows per chunk = 2 chunks for 80 rows.
    # This bounds parallel GPUs to 2 per track to avoid hitting concurrency limits,
    # and keeps evaluation well under the 8-minute mark.
    CHUNK_SIZE = 40
    chunks = [rows[i:i + CHUNK_SIZE] for i in range(0, len(rows), CHUNK_SIZE)]
    
    bases = [base] * len(chunks)
    adapters = [adapter] * len(chunks)
    
    print(f"Launching parallel evaluations across {len(rows)} rows in {len(chunks)} chunks (Total {len(chunks)} GPU jobs)...")
    
    results = list(evaluate_chunk.map(bases, adapters, chunks))
    
    # Aggregate results
    aggregated = {
        "base": {"label": "BASE", "n": 0, "valid": 0, "spine_ok": 0, "samples": []},
        "tuned": {"label": "TUNED", "n": 0, "valid": 0, "spine_ok": 0, "samples": []}
    }
    
    for res in results:
        for key in ["base", "tuned"]:
            if not res.get(key):
                continue
            aggregated[key]["n"] += res[key]["n"]
            aggregated[key]["valid"] += res[key]["valid"]
            aggregated[key]["spine_ok"] += res[key]["spine_ok"]
            if len(aggregated[key]["samples"]) < 5:
                aggregated[key]["samples"].extend(res[key]["samples"])
                aggregated[key]["samples"] = aggregated[key]["samples"][:5]
            
    # Calculate final percentages
    final_result = {}
    for key, data in aggregated.items():
        if data["n"] == 0:
            continue
        data["json_valid_pct"] = round(100 * data["valid"] / data["n"], 1)
        data["spine_safe_pct"] = round(100 * data["spine_ok"] / data["n"], 1)
        # Drop internal aggregate keys for cleaner JSON output
        data.pop("valid", None)
        data.pop("spine_ok", None)
        final_result[key] = data
        
    print("\n=== EVAL RESULTS ===")
    print(json.dumps(final_result, indent=2))
