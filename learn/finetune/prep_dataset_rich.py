"""Multi-perspective dataset generation — covers ALL input variables.

Runs multiple small batches with different prompt configurations (bed_position,
printer, precedent scenarios, policy stances) and aggregates into one rich
training dataset. Each batch is ~40 examples, total ~200-300.

Strategy:
  Batch A: bed_position=center, no precedent, standard policy     (40 ex)
  Batch B: bed_position=edge,   no precedent, standard policy     (40 ex)
  Batch C: bed_position=corner, no precedent, standard policy     (40 ex)
  Batch D: bed_position=center, close precedent, standard policy  (40 ex)
  Batch E: bed_position=center, distant precedent, cautious policy(40 ex)
  Batch F: bed_position=edge,   close precedent, aggressive policy(40 ex)

Run:  modal run learn/finetune/prep_dataset_rich.py
Out:  data/finetune/sft.train.jsonl (aggregated, ~240 rows)
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
BED_POSITIONS = ["center", "edge", "corner"]
# Small grid per batch: 2 temps × 2 hums = 4 per material×geometry = 80 per batch
TEMPS = [20, 30]
HUMS = [40, 65]

BASE_MODEL = os.environ.get("FINETUNE_BASE", "google/gemma-4-E4B-it")

try:
    ROOT = Path(__file__).resolve().parents[2]
except IndexError:
    ROOT = Path(__file__).resolve().parent

# --- Prompt templates with variable injection ---

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

# Synthetic precedent snippets per material
PRECEDENT = {
    "PLA": {
        "close": (
            "HISTORICAL PRECEDENT (nearest prior jobs by environment):\n"
            "  [1] Job pla-042 (earned) — PLA/overhang @ 22°C, 45% RH → success "
            "(env-distance 0.15)\n"
            "      lesson: PLA overhangs at 22°C: 210°C nozzle, 60°C bed, 100% fan "
            "gave clean results. Dropping bed to 55°C caused slight sag on steep overhangs.\n"
        ),
        "distant": (
            "HISTORICAL PRECEDENT (nearest prior jobs by environment):\n"
            "  [1] Job pla-128 (earned) — PLA/bridge @ 18°C, 30% RH → success "
            "(env-distance 0.72)\n"
            "      lesson: Cold dry room: PLA bridges needed 215°C and 40% fan. "
            "Stringing appeared above 60% fan in these conditions.\n"
        ),
    },
    "PETG": {
        "close": (
            "HISTORICAL PRECEDENT (nearest prior jobs by environment):\n"
            "  [1] Job petg-031 (earned) — PETG/overhang @ 24°C, 50% RH → success "
            "(env-distance 0.12)\n"
            "      lesson: PETG at 245°C/80°C bed with 40% fan. Dropping below 235°C "
            "caused layer adhesion issues on overhangs.\n"
        ),
        "distant": (
            "HISTORICAL PRECEDENT (nearest prior jobs by environment):\n"
            "  [1] Job petg-089 (earned) — PETG/stringing @ 30°C, 70% RH → failed_stringing "
            "(env-distance 0.68)\n"
            "      lesson: Hot humid room: PETG stringing at 240°C with 50% fan. "
            "Needed 6mm retraction to control oozing.\n"
        ),
    },
    "ABS": {
        "close": (
            "HISTORICAL PRECEDENT (nearest prior jobs by environment):\n"
            "  [1] Job abs-015 (earned) — ABS/overhang @ 26°C, 45% RH → success "
            "(env-distance 0.18)\n"
            "      lesson: ABS at 250°C/105°C bed, 20% fan, enclosed. Warping on "
            "corners when bed dropped below 100°C.\n"
        ),
        "distant": (
            "HISTORICAL PRECEDENT (nearest prior jobs by environment):\n"
            "  [1] Job abs-072 (earned) — ABS/adhesion @ 34°C, 75% RH → failed_sag "
            "(env-distance 0.81)\n"
            "      lesson: Hot humid room: ABS corner warping despite 105°C bed. "
            "Added brim and dropped fan to 0% for first 3 layers.\n"
        ),
    },
    "TPU": {
        "close": (
            "HISTORICAL PRECEDENT (nearest prior jobs by environment):\n"
            "  [1] Job tpu-008 (earned) — TPU/overhang @ 22°C, 40% RH → success "
            "(env-distance 0.10)\n"
            "      lesson: TPU at 220°C/45°C bed, 60% fan, 2mm retraction. "
            "Flexible filament needs slow speeds and low retraction.\n"
        ),
        "distant": (
            "HISTORICAL PRECEDENT (nearest prior jobs by environment):\n"
            "  [1] Job tpu-044 (earned) — TPU/bridge @ 28°C, 60% RH → success "
            "(env-distance 0.55)\n"
            "      lesson: Warm room TPU bridges: 225°C, 45°C bed, 80% fan. "
            "TPU bridges sag easily — max fan and minimum extrusion width.\n"
        ),
    },
}

# Policy stances
POLICY = {
    "standard": "",
    "cautious": (
        "POLICY NOTE (Chief Engineer's standing guidance):\n"
        "  This is a customer-facing part. Prioritize surface finish over speed. "
        "Conservative settings preferred — err on the side of cooler and slower.\n\n"
    ),
    "aggressive": (
        "POLICY NOTE (Chief Engineer's standing guidance):\n"
        "  This is a prototype iteration. Speed matters more than surface finish. "
        "Push temps to the high end of the material range for faster layer bonding.\n\n"
    ),
}

# Printer models
PRINTERS = {
    "ender3": "Creality Ender 3 V2 (220×220×250 bed, Bowden extruder)",
    "prusa": "Prusa MK4 (250×210×220 bed, direct drive extruder)",
    "bambu": "Bambu Lab X1C (256×256×256 bed, direct drive, enclosed)",
}

# Machine wear states (print count since last maintenance)
MACHINE_WEAR = {
    "fresh": (
        "MACHINE STATE (print count since last service):\n"
        "  Fresh maintenance — nozzle is sharp, bed is clean, belts are tight.\n"
        "  Settings can be precise; expect accurate temps and clean extrusion.\n"
    ),
    "broken_in": (
        "MACHINE STATE (print count since last service):\n"
        "  ~80 prints on this nozzle — slight wear, predictable behavior.\n"
        "  Bed has some residue in the center zone. Nozzle may run 2-3°C hot.\n"
    ),
    "worn": (
        "MACHINE STATE (print count since last service):\n"
        "  200+ prints since last service — nozzle shows visible wear, bed has\n"
        "  residue buildup in center, belts have stretched slightly.\n"
        "  Expect 5-8°C overshoot on nozzle, compensate down. Bed adhesion\n"
        "  is weaker at center — bump bed temp 5°C or use edge/corner.\n"
    ),
}

# Layer height options
LAYER_HEIGHTS = {
    "fine": (
        "  layer_height: 0.12mm (fine detail) — thin layers, more bonding time,\n"
        "  better overhangs but slower print. Lower fan needed; too much cooling\n"
        "  on thin layers causes warping.\n"
    ),
    "standard": (
        "  layer_height: 0.20mm (standard) — balanced detail and speed.\n"
    ),
    "draft": (
        "  layer_height: 0.28mm (draft/fast) — thick layers, less detail,\n"
        "  needs more cooling per layer. Overhangs suffer; bridges need max fan.\n"
    ),
}

# Print speed options
PRINT_SPEEDS = {
    "slow": (
        "  print_speed: 40mm/s (slow/precise) — long layer times, good bonding,\n"
        "  less stringing. Can run lower temps since plastic stays in melt zone longer.\n"
    ),
    "standard": (
        "  print_speed: 60mm/s (standard) — balanced.\n"
    ),
    "fast": (
        "  print_speed: 80mm/s (fast) — short layer times, needs higher temps\n"
        "  to keep plastic flowing. More stringing risk; bump retraction 1-2mm.\n"
    ),
}


def _build_prompt(
    material: str, geometry: str, temp: float, hum: float,
    bed_position: str, printer: str,
    precedent: str, policy: str,
    machine_wear: str = "", layer_height: str = "", print_speed: str = "",
) -> str:
    printer_line = f"  printer: {printer}\n" if printer else ""
    bed_line = f"  bed_position: {bed_position}\n"
    return (
        f"{PERSONA}\n\n"
        f"CURRENT JOB:\n"
        f"  material: {material}\n"
        f"  geometry: {geometry}\n"
        f"  description: (none given)\n"
        f"{bed_line}"
        f"{layer_height}"
        f"{print_speed}"
        f"ENVIRONMENT (right now in the room):\n"
        f"  temperature: {temp:.0f}°C\n"
        f"  humidity: {hum:.0f}% RH\n"
        f"{printer_line}\n"
        f"{machine_wear}"
        f"{precedent}\n"
        f"{policy}"
        f"{OUTPUT_CONTRACT}"
    )


# --- Batch definitions ---
# (label, bed_position, printer_key, precedent_key, policy_key, machine_wear, layer_height, print_speed)
BATCHES = [
    # Core variable coverage (bed_position, precedent, policy)
    ("A_center_noprec_standard",  "center", "ender3", None,     "standard",  "fresh",    "standard", "standard"),
    ("B_edge_noprec_standard",    "edge",   "ender3", None,     "standard",  "fresh",    "standard", "standard"),
    ("C_corner_noprec_standard",  "corner", "ender3", None,     "standard",  "fresh",    "standard", "standard"),
    ("D_center_close_standard",   "center", "ender3", "close",  "standard",  "broken_in", "standard", "standard"),
    ("E_center_distant_cautious", "center", "ender3", "distant","cautious",  "broken_in", "standard", "standard"),
    ("F_edge_close_aggressive",   "edge",   "ender3", "close",  "aggressive","broken_in", "standard", "standard"),
    # Machine wear variation
    ("G_center_worn_standard",     "center", "ender3", "close",  "standard",  "worn",      "standard", "standard"),
    ("H_edge_worn_cautious",       "edge",   "ender3", "close",  "cautious",  "worn",      "standard", "standard"),
    # Layer height variation
    ("I_center_fine_standard",     "center", "ender3", "close",  "standard",  "broken_in", "fine",     "slow"),
    ("J_center_draft_aggressive",  "center", "ender3", "close",  "aggressive","broken_in", "draft",    "fast"),
    # Print speed variation
    ("K_edge_slow_cautious",       "edge",   "ender3", "close",  "cautious",  "broken_in", "standard", "slow"),
    ("L_corner_fast_aggressive",   "corner", "ender3", "close",  "aggressive","broken_in", "draft",    "fast"),
]


if modal is not None:
    app = modal.App("microfactory-node-prep-rich")
    image = (
        modal.Image.debian_slim(python_version="3.12")
        .pip_install("torch", "transformers>=4.49", "accelerate>=0.34", "huggingface_hub")
    )
    vol = modal.Volume.from_name("microfactory-node-finetune", create_if_missing=True)

    @app.function(image=image, gpu="A10G", timeout=1800,
                  secrets=[modal.Secret.from_name("chief-engineer-secrets")])
    def generate_batch(batch_idx: int, base: str = BASE_MODEL, temperature: float = 0.8) -> dict:
        """Generate ONE batch on its own GPU. Called in parallel via .map()."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        label, bed_pos, printer_key, prec_key, pol_key, wear_key, lh_key, ps_key = BATCHES[batch_idx]
        printer = PRINTERS.get(printer_key, "")
        precedent = PRECEDENT.get("PLA", {}).get(prec_key, "") if prec_key else (
            "HISTORICAL PRECEDENT:\n"
            "  (none) — no prior job matches this material + geometry. "
            "Reason from material properties and say so plainly.\n"
        )
        policy = POLICY.get(pol_key, "")
        machine_wear = MACHINE_WEAR.get(wear_key, "")
        layer_height = LAYER_HEIGHTS.get(lh_key, "")
        print_speed = PRINT_SPEEDS.get(ps_key, "")

        print(f"[Batch {batch_idx+1}/{len(BATCHES)}] {label} — loading model...")
        tok = AutoTokenizer.from_pretrained(base)
        model = AutoModelForCausalLM.from_pretrained(
            base, dtype=torch.bfloat16, device_map="auto"
        )
        print(f"[Batch {batch_idx+1}] Model on {model.device}, generating...")

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

        batch_rows = []
        per_batch = len(MATERIALS) * len(GEOMETRY_TYPES) * len(TEMPS) * len(HUMS)
        n = 0
        for mat in MATERIALS:
            prec = PRECEDENT.get(mat, {}).get(prec_key, "") if prec_key else precedent
            for geo in GEOMETRY_TYPES:
                for t in TEMPS:
                    for h in HUMS:
                        n += 1
                        prompt = _build_prompt(mat, geo, t, h, bed_pos, printer, prec, policy,
                                               machine_wear, layer_height, print_speed)
                        full = f"{prompt}\n\n{USER_TURN}"
                        advice = _infer(full)
                        if advice is None:
                            advice = _infer(full)
                        if advice is None:
                            print(f"  [{n}/{per_batch}] {mat}/{geo} @ {t}C/{h}% bed={bed_pos} → SKIPPED")
                            continue
                        batch_rows.append({"messages": [
                            {"role": "user", "content": full},
                            {"role": "assistant", "content": json.dumps(advice)},
                        ]})
                        s = advice.get("settings", {})
                        print(f"  [{n}/{per_batch}] {mat}/{geo} @ {t}C/{h}% bed={bed_pos} → "
                              f"nozzle={s.get('nozzle_temp','?')} bed={s.get('bed_temp','?')} fan={s.get('fan_pct','?')}")

        print(f"[Batch {batch_idx+1}] {label}: {len(batch_rows)} rows COMPLETE")
        return {"label": label, "rows": batch_rows, "count": len(batch_rows)}

    @app.function(image=image, volumes={"/out": vol}, timeout=600)
    def aggregate(results: list[dict]) -> dict:
        """Collect all batch results and write final JSONL to volume."""
        all_rows = []
        for r in results:
            all_rows.extend(r["rows"])
        with open("/out/sft.train.jsonl", "w") as f:
            for row in all_rows:
                f.write(json.dumps(row) + "\n")
        vol.commit()
        bed_counts = {}
        for row in all_rows:
            user = row["messages"][0]["content"]
            for bp in BED_POSITIONS:
                if f"bed_position: {bp}" in user:
                    bed_counts[bp] = bed_counts.get(bp, 0) + 1
        print(f"Aggregated {len(all_rows)} rows from {len(results)} batches")
        print(f"Bed distribution: {bed_counts}")
        return {"total_rows": len(all_rows), "batches": len(results),
                "bed_distribution": bed_counts}

    @app.local_entrypoint()
    def main(base: str = BASE_MODEL, temperature: float = 0.8):
        print(f"Launching {len(BATCHES)} parallel batch jobs on separate GPUs...")
        batch_indices = list(range(len(BATCHES)))
        results = list(generate_batch.map(batch_indices, kwargs={"base": base, "temperature": temperature}))
        print(f"\nAll {len(results)} batches complete. Aggregating...")
        final = aggregate.remote(results)
        print("\n=== RICH DATASET COMPLETE ===")
        print(json.dumps(final, indent=2))
        print("\nDownload:")
        print("  modal volume get microfactory-node-finetune sft.train.jsonl data/finetune/sft.train.jsonl --force")


if __name__ == "__main__":
    print("Multi-perspective rich dataset generation. Run:")
    print("  modal run learn/finetune/prep_dataset_rich.py")
