# Microfactory Node: Full Fine-Tune Pipeline

End-to-end pipeline from dataset generation through GGUF conversion.
Earns **Well-Tuned** + **Llama Champion** badges when eval passes.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DATASET GENERATION (prep_dataset_fast.py)                     │
│    → 120 train + 80 eval JSONL on Modal volume                   │
│    → Live Gemma 4 E4B generates non-deterministic targets         │
├─────────────────────────────────────────────────────────────────┤
│ 2. DOWNLOAD                                                      │
│    modal volume get microfactory-node-finetune *.jsonl            │
├─────────────────────────────────────────────────────────────────┤
│ 3. FINE-TUNE (LoRA) — Parallel Tracks A & B                      │
│    Track A: gemma-4-E4B-it → microfactory-node-lora-v2            │
│    Track B: gemma-4-E4B-it-qat-q4_0-unquantized → lora-v3-qat    │
│    → LoRA r=4, 1 epoch, A10G                                     │
│    → Adapters pushed to HF Hub (~35MB each)                      │
├─────────────────────────────────────────────────────────────────┤
│ 4. EVALUATE — Parallel Tracks, Sharded (2 GPUs each)              │
│    → BASE vs TUNED on 80 held-out examples                       │
│    → json-valid%, spine-safe%, sample outputs                    │
│    → 🏆 Well-Tuned badge secured (100%/100%, real judgment)      │
├─────────────────────────────────────────────────────────────────┤
│ 5. SERVE (three backends, all live)                              │
│    5a. Ollama GGUF — gguf_pipeline_modal.py merges + quantizes    │
│        + uploads to kylebrodeur/microfactory-node-gguf on HF Hub  │
│    5b. Modal API   — modal_serve.py exposes OpenAI /v1/chat       │
│    5c. Gradio      — llm_zerogpu_lora.py + model switcher dropdown │
├─────────────────────────────────────────────────────────────────┤
│ 6. PUBLISH (ollama.com + HF model cards)                         │
│    → ollama pull hf.co/… → ollama cp … → ollama push             │
│    → ollama.com/kylebrodeur/microfactory-node[-v2|-v3-qat[:q4_0]] │
│    → dual-table model card on HF GGUF repo                       │
│    → details: OLLAMA_PUBLISHING.md                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Dataset Generation

**Script:** `learn/finetune/prep_dataset_modal.py`  
**Runtime:** ~50-70 min on A10G  
**Cost:** ~$0.30-0.50

Generates chat-format SFT data by running the base model (`google/gemma-4-E4B-it`)
over a grid of (material × geometry × temperature × humidity) conditions.

```bash
cd chief-engineer/
modal run learn/finetune/prep_dataset_modal.py
```

**Grid:**
- Train: 4 materials × 5 geometries × 3 temps × 3 hums = 180 rows
- Eval: 4 materials × 5 geometries × 2 temps × 2 hums = 80 rows (held-out temps/hums)

**Key parameters:**
- `temperature=0.7, top_p=0.95` — non-deterministic sampling prevents template memorization
- Output format: `{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`

**Output:** `sft.train.jsonl` + `sft.eval.jsonl` on Modal volume `microfactory-node-finetune`

---

## Step 2: Download Dataset

```bash
modal volume get microfactory-node-finetune sft.train.jsonl data/finetune/sft.train.jsonl
modal volume get microfactory-node-finetune sft.eval.jsonl data/finetune/sft.eval.jsonl
```

---

## Step 3: LoRA Fine-Tune

**Script:** `learn/finetune/train_modal.py`  
**Runtime:** ~5-10 min on A10G  
**Cost:** ~$0.10-0.20

### Smoke test first (no push)
```bash
modal run learn/finetune/train_modal.py
```
Verify: image builds, GPU attaches, loss decreases, checkpoint saves.

### Full run + publish
```bash
modal run learn/finetune/train_modal.py --push-to kylebrodeur/microfactory-node-lora-v2
```

**Training config:**
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Base model | `google/gemma-4-E4B-it` | Matches live `gemma4:e4b` |
| Method | LoRA (PEFT) | Efficient, small adapter |
| Rank | r=4, α=8 | Force generalization (v1 r=16 memorized) |
| Epochs | 1 | Early stopping (v1 3 epochs overfit) |
| Learning rate | 2e-4 | Standard for LoRA SFT |
| Batch size | 2 × 4 accumulation | Effective batch = 8 |
| Max length | 1536 tokens | Covers prompt + Advice JSON |
| Precision | bfloat16 | A10G native |
| GPU | NVIDIA A10G (24GB) | Modal on-demand |
| Target modules | `language_model.*.(q/k/v/o/gate/up/down)_proj` | Regex-scoped to text decoder only — avoids `Gemma4ClippableLinear` in vision/audio towers ([peft#3129](https://github.com/huggingface/peft/issues/3129)) |

**⚠️ Gemma 4-specific:** Vision/audio towers use `Gemma4ClippableLinear` (wraps `nn.Linear`, inherits from `nn.Module`). PEFT rejects it. Fix: regex-scoped `target_modules` to language model only + `exclude_modules` for vision/audio/multimodal projector.

**Anti-parroting strategy (v2 fixes):**
1. **Live-generated dataset**: Non-deterministic targets from the base model itself
2. **Lower rank (r=4)**: Less capacity to memorize, forced to generalize
3. **Single epoch**: Stop before loss collapses to 0.10 (v1 hit 0.10 at epoch 3)
4. **Correct base model**: Gemma 4 E4B (v1 wrongly used Gemma 3 1B)

---

## Step 4: Honest Evaluation

**Script:** `learn/finetune/eval_modal.py`  
**Runtime:** ~5-10 min on A10G  
**Cost:** ~$0.10-0.20

```bash
modal run learn/finetune/eval_modal.py --adapter kylebrodeur/microfactory-node-lora-v2
```

**Metrics:**
- **json-valid%**: Does output parse as valid Advice JSON?
- **spine-safe%**: Are settings within material bounds?
- **Qualitative**: Do samples show varied, context-aware judgment? (Not identical template)

**Well-Tuned gate:** TUNED ≥ BASE on both metrics AND samples show real judgment.

---

## Step 5: GGUF Conversion + Publish (HF Hub + ollama.com)

**Earns: Llama Champion badge** (llama.cpp in the loop)

**The implemented path:** `gguf_pipeline_modal.py` runs the full merge →
quantize → upload entirely on Modal. No local llama.cpp, no GPU on the
dev machine. Outputs land on both the Modal volume and the HF Hub repo
[`kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf).

```bash
PYFILE=learn/finetune/gguf_pipeline_modal.py

# Full pipeline (merge → quantize → upload), q4_k_m by default:
modal run "${PYFILE}::main" \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat \
  --name microfactory-node-v3-qat \
  --upload kylebrodeur/microfactory-node-gguf

# Same adapter, q4_0 quant (QAT-native) — use --as-name to avoid HF filename collision:
modal run "${PYFILE}::main" \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat \
  --name microfactory-node-v3-qat \
  --outtype q4_0 \
  --upload kylebrodeur/microfactory-node-gguf

# Re-upload an existing GGUF on the volume to HF Hub (rename allowed):
modal run "${PYFILE}::upload_only" \
  --name microfactory-node-v3-qat \
  --repo kylebrodeur/microfactory-node-gguf \
  --as-name microfactory-node-v3-qat-q4_0
```

After this, any user can run the model via Ollama in one of two ways:

```bash
# Path 1: pull from HF Hub directly (template/system/params auto-applied)
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf

# Path 2: pull from the public Ollama registry (after Step 6 publish)
ollama run kylebrodeur/microfactory-node-v3-qat
```

**Quantization options:**
| Format | Size (8B) | Notes |
|--------|-----------|-------|
| q8_0 | ~8.5 GB | Near-lossless, slow |
| q4_k_m | ~5.1 GB | Balanced default for v1/v2/v3-qat |
| q4_0 | ~4.9 GB | QAT-native target — highest fidelity for QAT models |

### Alternative paths (kept for reference)

- **Direct LoRA → GGUF adapter** via `llama.cpp/convert_lora_to_gguf.py` — no
  merge, ~30-60 MB output, loads via `--lora`. Useful when the base GGUF is
  already on disk and you want to keep the adapter modular.
- **Ollama Safetensors `ADAPTER`** — declarative, but Gemma 4 support is
  partial; we found the merge path more reliable in practice.

---

## Step 6: Publish to ollama.com

**One-time setup:** generate an Ollama SSH key, register the public half at
<https://ollama.com/settings/keys>.

```bash
ssh-keygen -t ed25519 -f ~/.ollama/id_ed25519 -N "" -C "<handle>-ollama" -q
cat ~/.ollama/id_ed25519.pub   # paste this into ollama.com settings
```

**Per model:** pull from HF → rename into your namespace → push.

```bash
# Pull from HF Hub (auto-detects template/system/params from the repo)
ollama pull hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf

# Rename into the namespace the push will use
ollama cp "hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf" \
          kylebrodeur/microfactory-node-v3-qat

# Push to the public registry
ollama push kylebrodeur/microfactory-node-v3-qat
```

A tag suffix (`:q4_0`) cleanly separates quants under the same model name:

```bash
ollama cp "hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat-q4_0.gguf" \
          kylebrodeur/microfactory-node-v3-qat:q4_0
ollama push kylebrodeur/microfactory-node-v3-qat:q4_0
```

**Published artifacts:**

| Variant | HF Hub file | ollama.com tag |
|---------|-------------|----------------|
| v3-qat (q4_k_m, recommended) | [`microfactory-node-v3-qat.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat.gguf) | [`kylebrodeur/microfactory-node-v3-qat`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat) |
| v3-qat (q4_0 native) | [`microfactory-node-v3-qat-q4_0.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat-q4_0.gguf) | [`kylebrodeur/microfactory-node-v3-qat:q4_0`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0) |
| v2 | [`microfactory-node-v2.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v2.gguf) | [`kylebrodeur/microfactory-node-v2`](https://ollama.com/kylebrodeur/microfactory-node-v2) |
| v1 (historical) | [`microfactory-node.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node.gguf) | [`kylebrodeur/microfactory-node`](https://ollama.com/kylebrodeur/microfactory-node) |

Full runbook including the seven gotchas hit and the
`/tmp/all-pushes.sh` template for queuing multi-model pushes:
[**`OLLAMA_PUBLISHING.md`**](OLLAMA_PUBLISHING.md).

Adapter model cards on the LoRA repos:

```bash
hf upload kylebrodeur/microfactory-node-lora-v2 \
  learn/finetune/MODEL_CARD.md README.md \
  --commit-message "Add model card with training details, usage, and iteration history"

hf upload kylebrodeur/microfactory-node-lora-v3-qat \
  learn/finetune/MODEL_CARD_QAT.md README.md \
  --commit-message "Add QAT model card with training details, usage, and iteration history"
```

---

## Badge Map

| Badge | How Earned | Evidence |
|-------|-----------|----------|
| **Well-Tuned** | eval shows TUNED ≥ BASE + real judgment | eval_modal.py output |
| **Llama Champion** | GGUF conversion via llama.cpp | convert_hf_to_gguf.py in pipeline |
| **Off the Grid** | Local Ollama inference | ollama run microfactory-node-v2 |
| **Tiny Titan** | 8B params ≤ 32B limit | google/gemma-4-E4B-it |

---

## Cost Summary (estimated)

| Step | Compute | Est. Cost |
|------|---------|-----------|
| Dataset generation | A10G, ~60 min | ~$0.40 |
| LoRA training | A10G, ~8 min | ~$0.12 |
| Evaluation | A10G, ~8 min | ~$0.12 |
| Image builds (3×) | CPU | ~$0.18 |
| **Total** | | **~$0.82** |

Well under $2 estimate and $100 budget.

---

## Files Reference

| File | Status | Purpose |
|------|--------|--------|
| `learn/finetune/prep_dataset_rich.py` | ✅ Active | Multi-perspective parallel dataset generation (12 batches, 13 variables) |
| `learn/finetune/prep_dataset_fast.py` | 🟡 Alternate | Faster single-GPU variant |
| `learn/finetune/prep_dataset_supplemental.py` | 🟡 Alternate | Supplemental variable-coverage examples |
| `learn/finetune/train_modal.py` | ✅ Active | LoRA fine-tune on Modal GPU |
| `learn/finetune/eval_modal.py` | ✅ Active | BASE vs TUNED evaluation on Modal GPU |
| `learn/finetune/eval.py` | 🟡 Local | Local eval (superseded by eval_modal.py) |
| `learn/finetune/merge_modal.py` | ✅ Active | LoRA merge for GGUF conversion |
| `learn/finetune/prep_dataset_modal.py` | 🔴 Deprecated | Simple grid (superseded by _rich) |
| `learn/finetune/prep_dataset_hf.py` | 🔴 Dead | HF API attempt (Gemma 4 not supported) |
| `learn/finetune/prep_dataset.py` | 🔴 Deprecated | Original local script |
| `learn/finetune/REPORT.md` | ✅ Active | Iteration tracking + results |
| `learn/finetune/REPORT_v1.md` | 📦 Archive | Full v1 iteration report (Gemma 3, parroting) |
| `learn/finetune/MODEL_CARD.md` | ✅ Active | HF adapter repo model card (v2 — standard E4B) |
| `learn/finetune/MODEL_CARD_QAT.md` | ✅ Active | HF adapter repo model card (v3 — QAT) |
| `learn/finetune/PIPELINE.md` | ✅ Active | This document |
| `learn/finetune/RUNBOOK.md` | ✅ Active | Step-by-step commands |
| `learn/finetune/SERVING.md` | ✅ Active | Serving & deployment (HF + ollama.com tags) |
| `learn/finetune/OLLAMA_PUBLISHING.md` | ✅ Active | Full ollama.com publishing runbook + gotchas |
| `learn/finetune/SESSION_REPORT.md` | ✅ Active | End-to-end session report (Phase 1 → Distribution) |
| `learn/finetune/gguf_pipeline_modal.py` | ✅ Active | Merge → quantize → upload-to-HF (Modal app) |
| `learn/finetune/modal_serve.py` | ✅ Active | OpenAI-compatible /v1/chat/completions on Modal |
| `learn/finetune/BUDGET.md` | ✅ Active | Budget tracking |
| `learn/finetune/activity.jsonl` | ✅ Active | Pipeline event log |
| `data/finetune/sft.train.jsonl` | 🔄 Generating | Training data (~960 rows from 12 batches) |
