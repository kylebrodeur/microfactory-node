# Fine-Tune Runbook

Every command, in order. Run from `chief-engineer/`. Budget: ~$1 total, $96 remaining.

---

## 0. Prerequisites (already done)
- [x] `modal token set` — authenticated
- [x] `chief-engineer-secrets` Modal secret with HF_TOKEN (WRITE scope)
- [x] Accepted `google/gemma-4-E4B-it` license on HF
- [x] All scripts updated for v2 (Gemma 4 E4B, LoRA r=4, 1 epoch)
- [x] Gemma4ClippableLinear fix applied (regex target_modules)
- [x] prep_dataset_rich.py: 12-batch multi-perspective parallel design

## Budget Tracking & Agent Logging
Check before/after each Modal step:
```bash
modal billing report --for today --json | python3 -c "
import sys,json
data=json.load(sys.stdin)
total=sum(float(d['cost']) for d in data)
print(f'Total today: \${total:.2f}')
"
```

**Agent Note**: You MUST append your actions and billing updates to `learn/finetune/activity.jsonl` using the JSON format: `{"timestamp": "...", "action": "...", "event": "...", "details": "..."}`. Backfill any missed steps when you take over. See `BUDGET.md` for full tracking rules.

---

## 1. Generate Rich Dataset (~15 min parallel, ~$15)

```bash
modal run --detach learn/finetune/prep_dataset_rich.py
```

12 batches on 12 separate A10G GPUs concurrently via Modal `.map()`.
Covers all 13 input variables (bed_position, printer, precedent, policy,
machine_wear, layer_height, print_speed). ~960 total examples.

**Check progress:**
```bash
modal app logs <app-id> | grep -E "COMPLETE|Aggregat"
```

**Wait for:** `=== RICH DATASET COMPLETE ===`

---

## 2. Download Dataset

```bash
modal volume get microfactory-node-finetune sft.train.jsonl data/finetune/sft.train.jsonl --force
```

The rich dataset produces a single aggregated `sft.train.jsonl`.
No separate eval file — eval_modal.py uses its own held-out logic.

---

## 3. Smoke Test Train (~5 min, ~$0.10 per track)

⚠️ Gemma 4 uses `Gemma4ClippableLinear` in vision/audio towers — PEFT rejects it.
Fixed via regex-scoped `target_modules` to language model only. See REPORT.md §v2 Bug.

You can run these in parallel in separate terminals:

**Track A (Standard E4B):**
```bash
modal run learn/finetune/train_modal.py
```

**Track B (QAT-unquantized):**
```bash
modal run learn/finetune/train_modal.py --base google/gemma-4-E4B-it-qat-q4_0-unquantized
```

1 epoch, no push. Verify: image builds, GPU attaches, loss decreases, checkpoint saves.

---

## 4. Full Train + Publish (~8 min, ~$0.12 per track)

Run in parallel in separate terminals:

**Track A (Standard E4B):**
```bash
modal run learn/finetune/train_modal.py --push-to kylebrodeur/microfactory-node-lora-v2
```

**Track B (QAT-unquantized):**
```bash
modal run learn/finetune/train_modal.py \
  --base google/gemma-4-E4B-it-qat-q4_0-unquantized \
  --push-to kylebrodeur/microfactory-node-lora-v3-qat
```

Pushes LoRA adapter + tokenizer to HF Hub. Model card can be added after.

---

## 5. Evaluate (~15 min, ~$0.24 per track)

Evaluations now use `modal.map()` to fan out `BASE` and `TUNED` model inference across 2 separate A10G GPUs concurrently to prevent timeouts and cut evaluation time in half.

Run in parallel in separate terminals:

**Track A (Standard E4B):**
```bash
modal run learn/finetune/eval_modal.py --adapter kylebrodeur/microfactory-node-lora-v2
```

**Track B (QAT-unquantized):**
```bash
modal run learn/finetune/eval_modal.py \
  --base google/gemma-4-E4B-it-qat-q4_0-unquantized \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat
```

Outputs: json-valid%, spine-safe%, 5 sample outputs for BASE and TUNED.
**Well-Tuned gate:** TUNED ≥ BASE on both metrics AND samples show real judgment.

---

## 6. GGUF Conversion + Upload to HF Hub (~7 min, ~$0.15)

**Implemented path:** `gguf_pipeline_modal.py` runs merge → quantize → upload
entirely on Modal. No local llama.cpp, no GPU on dev machine. Outputs land
on both the Modal volume and the HF repo
[`kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf).

### Track A (standard E4B → q4_k_m)
```bash
modal run learn/finetune/gguf_pipeline_modal.py::main \
  --adapter kylebrodeur/microfactory-node-lora-v2 \
  --name microfactory-node-v2 \
  --upload kylebrodeur/microfactory-node-gguf
```

### Track B (QAT → q4_k_m)
```bash
modal run learn/finetune/gguf_pipeline_modal.py::main \
  --base google/gemma-4-E4B-it-qat-q4_0-unquantized \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat \
  --name microfactory-node-v3-qat \
  --upload kylebrodeur/microfactory-node-gguf
```

### Track B' (QAT → q4_0 — the QAT-native quant)
```bash
modal run learn/finetune/gguf_pipeline_modal.py::main \
  --base google/gemma-4-E4B-it-qat-q4_0-unquantized \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat \
  --name microfactory-node-v3-qat \
  --outtype q4_0 \
  --upload kylebrodeur/microfactory-node-gguf
# Volume + HF filename collide with the q4_k_m — use upload_only --as-name to rename on HF:
modal run learn/finetune/gguf_pipeline_modal.py::upload_only \
  --name microfactory-node-v3-qat \
  --repo kylebrodeur/microfactory-node-gguf \
  --as-name microfactory-node-v3-qat-q4_0
```

### One-line local test
```bash
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf
```
(The HF repo carries `template`/`system`/`params`, so Ollama applies the
Gemma 4 chat template + Chief Engineer persona + sampling automatically.)

### Alternative paths (kept for reference)
Direct LoRA → GGUF adapter (no merge) and Ollama `ADAPTER` (Safetensors) are
both documented in [`PIPELINE.md` §5](PIPELINE.md#step-5-gguf-conversion--publish-hf-hub--ollamacom).
The Modal pipeline above is the one we shipped because it ends with a single
file per variant on HF Hub, no `--lora` runtime juggling.

---

## 7. Push to ollama.com (~14 min per variant, push only)

Makes models pullable as `ollama run kylebrodeur/<name>` for anyone who
doesn't want to type the HF URI. Full runbook (one-time SSH-key setup, the
seven gotchas hit and fixed, the `/tmp/all-pushes.sh` template for queuing
multi-model pushes): [**`OLLAMA_PUBLISHING.md`**](OLLAMA_PUBLISHING.md).

```bash
# One-time: generate Ollama SSH key, paste pubkey at https://ollama.com/settings/keys
ssh-keygen -t ed25519 -f ~/.ollama/id_ed25519 -N "" -C "$(whoami)-ollama" -q
cat ~/.ollama/id_ed25519.pub

# Per variant:
ollama pull hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf
ollama cp "hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf" \
          kylebrodeur/microfactory-node-v3-qat
ollama push kylebrodeur/microfactory-node-v3-qat
```

**Published:**

| Variant | ollama.com tag | HF Hub file |
|---------|----------------|-------------|
| v3-qat (recommended) | [`kylebrodeur/microfactory-node-v3-qat`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat) | [GGUF](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat.gguf) |
| v3-qat (QAT-native quant) | [`kylebrodeur/microfactory-node-v3-qat:q4_0`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0) | [GGUF](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat-q4_0.gguf) |
| v2 | [`kylebrodeur/microfactory-node-v2`](https://ollama.com/kylebrodeur/microfactory-node-v2) | [GGUF](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v2.gguf) |
| v1 | [`kylebrodeur/microfactory-node`](https://ollama.com/kylebrodeur/microfactory-node) | [GGUF](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node.gguf) |

---

## 8. (Optional) QAT base variants for direct inference

Google's [Gemma 4 QAT Q4_0](https://huggingface.co/collections/google/gemma-4-qat-q4-0)
collection ships a pre-quantized base GGUF that can be used directly (no LoRA
step) for a clean QAT baseline. Useful when comparing the LoRA's contribution
vs. the base QAT model alone:

```bash
hf download google/gemma-4-E4B-it-qat-q4_0-gguf --local-dir ./qat-gguf
cat > Modelfile.qat << 'EOF'
FROM ./qat-gguf/gemma-4-e4b-it-q4_0.gguf
TEMPLATE """{{ if .System }}<start_of_turn>system
{{ .System }}<end_of_turn>
{{ end }}<start_of_turn>user
{{ .Prompt }}<end_of_turn>
<start_of_turn>model
"""
PARAMETER stop "<start_of_turn>user"
PARAMETER stop "<end_of_turn>"
EOF
ollama create microfactory-qat-base -f Modelfile.qat
```

---

## Parallel Opportunities

Steps 5 (eval) and 6 (GGUF conversion) can run in parallel:

```bash
# Terminal 1:
modal run learn/finetune/eval_modal.py --adapter kylebrodeur/microfactory-node-lora-v2

# Terminal 2 (simultaneously, local):
hf download kylebrodeur/microfactory-node-lora-v2 --local-dir ./lora-v2-adapter
python llama.cpp/convert_lora_to_gguf.py --base-model-id google/gemma-4-E4B-it --outtype f16 ./lora-v2-adapter
```

---

## Quick Reference

| Step | Command | Time | Cost |
|------|---------|------|------|
| 1 | `modal run --detach learn/finetune/prep_dataset_rich.py` | ~15m | ~$15.00 |
| 2 | `modal volume get microfactory-node-finetune sft.train.jsonl data/finetune/` | <1m | $0 |
| 3 | `modal run learn/finetune/train_modal.py` | 5m | ~$0.10 |
| 4 | `modal run learn/finetune/train_modal.py --push-to kylebrodeur/microfactory-node-lora-v2` | 8m | ~$0.12 |
| 5 | `modal run learn/finetune/eval_modal.py ...` | ~15m | ~$0.24 |
| 6 | `modal run learn/finetune/gguf_pipeline_modal.py::main --adapter … --upload …` | ~7m | ~$0.15 |
| 7 | `ollama pull … → ollama cp … → ollama push kylebrodeur/…` (per variant) | ~14m | $0 |
| 8 | `hf upload … MODEL_CARD.md README.md` | <1m | $0 |
| **Total** | | **~60-90m** | **~$15.97** |

---

## Badges Earned

| Badge | Step | Evidence |
|-------|------|----------|
| **Well-Tuned** | 5 | eval_modal.py output (if TUNED passes) |
| **Llama Champion** | 6 | convert_lora_to_gguf.py from llama.cpp |
| **Off the Grid** | 6d | ollama run microfactory-node-v2 |
| **Tiny Titan** | — | 8B params ≤ 32B limit |

---

## Files

| File | Status | Purpose |
|------|--------|--------|
| `RUNBOOK.md` | ✅ Active | This file — every command in order |
| `PIPELINE.md` | ✅ Active | Detailed pipeline documentation |
| `REPORT.md` | ✅ Active | Iteration tracking + results (v1 marked HISTORICAL) |
| `SESSION_REPORT.md` | ✅ Active | End-to-end session report (Phase 1 → Distribution) |
| `SERVING.md` | ✅ Active | Serving & deployment — dual HF + ollama.com tables |
| `OLLAMA_PUBLISHING.md` | ✅ Active | Full ollama.com publishing runbook + gotchas |
| `MODEL_CARD.md` | ✅ Active | HF adapter repo card (Track A — standard E4B) |
| `MODEL_CARD_QAT.md` | ✅ Active | HF adapter repo card (Track B — QAT) |
| `BUDGET.md` | ✅ Active | Budget tracking |
| `activity.jsonl` | ✅ Active | Pipeline event log |
| `prep_dataset_rich.py` | ✅ Active | Step 1: Multi-perspective parallel dataset generation |
| `prep_dataset_fast.py` | 🟡 Alternate | Faster single-GPU variant of _rich |
| `prep_dataset_supplemental.py` | 🟡 Alternate | Supplemental examples for specific variables |
| `train_modal.py` | ✅ Active | Steps 3-4: LoRA fine-tune |
| `eval_modal.py` | ✅ Active | Step 5: Honest evaluation (Modal GPU) |
| `eval.py` | 🟡 Local | Local eval (requires GPU, superseded by eval_modal.py) |
| `merge_modal.py` | ✅ Active | LoRA merge for legacy GGUF workflow (superseded by gguf_pipeline_modal.py) |
| `gguf_pipeline_modal.py` | ✅ Active | Step 6: Full merge→quantize→HF-upload pipeline (no local llama.cpp) |
| `modal_serve.py` | ✅ Active | Modal inference API endpoint (OpenAI-compatible) |
| `prep_dataset_modal.py` | 🔴 Deprecated | Simple grid dataset gen (superseded by _rich) |
| `prep_dataset_hf.py` | 🔴 Dead | HF Inference API attempt (Gemma 4 not supported) |
| `prep_dataset.py` | 🔴 Deprecated | Original local script (superseded by Modal versions) |
