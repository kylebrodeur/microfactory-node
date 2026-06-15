# Serving and deployment: Ollama, Modal, and Gradio model switching

This is what I figured out for publishing fine-tuned LoRA adapters to Ollama, hosting inference on Modal, and adding on-demand model switching to the Gradio app.

## Model Registry

| UI Label | HF Hub Adapter | GGUF File | Ollama Name | Inference |
|----------|---------------|-----------|-------------|-----------|
| LoRA v3 (QAT E4B) | `kylebrodeur/microfactory-node-lora-v3-qat` | `microfactory-node-v3-qat.gguf` | `microfactory-node-v3-qat` | ZeroGPU (Space) |
| LoRA v2 (Standard E4B) | `kylebrodeur/microfactory-node-lora-v2` | `microfactory-node-v2.gguf` | `microfactory-node-v2` | ZeroGPU (Space) |
| Base (Gemma 4 E4B) | — (no adapter) | — | `gemma4:e4b` | Ollama (local) / ZeroGPU (Space) |
| Modal API (remote) | — (HTTP call) | — | — | `kylebrodeur--microfactory-node-inference-serve.modal.run` |

---

## 1. Ollama Publishing — Implemented

### Status: GGUFs live on both HF Hub and ollama.com

The public Ollama registry is at [`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur):

| `ollama run …` | Quant | Size |
|----------------|-------|------|
| [`kylebrodeur/microfactory-node-v3-qat`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat) *(recommended)* | q4_k_m | 5.3 GB |
| [`kylebrodeur/microfactory-node-v3-qat:q4_0`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0) | q4_0 | 4.9 GB |
| [`kylebrodeur/microfactory-node-v2`](https://ollama.com/kylebrodeur/microfactory-node-v2) | q4_k_m | 5.3 GB |
| [`kylebrodeur/microfactory-node`](https://ollama.com/kylebrodeur/microfactory-node) | q4_k_m | 5.3 GB |

The HF Hub repo is [`kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf):

| File | Source adapter | Variant |
|------|----------------|---------|
| [`microfactory-node-v3-qat.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat.gguf) (5.1 GB, q4_k_m) | [`kylebrodeur/microfactory-node-lora-v3-qat`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v3-qat) | QAT-trained, balanced quant (recommended) |
| [`microfactory-node-v3-qat-q4_0.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat-q4_0.gguf) (4.9 GB, q4_0) | [`kylebrodeur/microfactory-node-lora-v3-qat`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v3-qat) | QAT-trained, QAT-native q4_0 quant (highest fidelity for the QAT model) |
| [`microfactory-node-v2.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v2.gguf) (5.1 GB, q4_k_m) | [`kylebrodeur/microfactory-node-lora-v2`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v2) | Standard E4B fine-tune |
| [`microfactory-node.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node.gguf) (5.1 GB, q4_k_m) | `kylebrodeur/microfactory-node-lora` (v1) | First fine-tune (historical) |

Users can pull either way:
```bash
ollama run kylebrodeur/microfactory-node-v3-qat                              # via ollama.com
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf   # via HF Hub
```

I keep the LoRA adapter repos on the Hub for further fine-tuning or inspection:
- [`kylebrodeur/microfactory-node-lora-v2`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v2) (35MB, Standard E4B)
- [`kylebrodeur/microfactory-node-lora-v3-qat`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v3-qat) (35MB, QAT-unquantized)

For the full ollama.com publishing walkthrough, see [`OLLAMA_PUBLISHING.md`](OLLAMA_PUBLISHING.md).

### Implemented: `gguf_pipeline_modal.py`

You do not need a local llama.cpp build. The full merge→GGUF→upload pipeline runs entirely on Modal:
1. **GPU step** (`merge`): loads base model + LoRA adapter, merges via `merge_and_unload()`
2. **CPU step** (`convert_to_gguf`): clones llama.cpp, builds with cmake, runs `convert_hf_to_gguf.py` → bf16 GGUF → `llama-quantize` to target type (q4_k_m default)
3. **CPU step** (`upload_to_hub`, optional): pushes the GGUF to a HF Hub model repo using `chief-engineer-secrets` + `HF_TOKEN` Modal secrets

The `--upload <owner>/<repo>` flag triggers step 3 inline. Without it, the GGUF stays on the Modal volume only.

**v3-qat with auto-upload (single command):**
```bash
modal run learn/finetune/gguf_pipeline_modal.py::main \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat \
  --name microfactory-node-v3-qat \
  --upload kylebrodeur/microfactory-node-gguf
```

**Upload an existing GGUF already on the volume** (used to push v1/v2 which were converted before the upload step existed):
```bash
modal run learn/finetune/gguf_pipeline_modal.py::upload_only \
  --name microfactory-node-v2 \
  --repo kylebrodeur/microfactory-node-gguf
```

**Track A (no upload, download to local):**
```bash
modal run learn/finetune/gguf_pipeline_modal.py::main \
  --adapter kylebrodeur/microfactory-node-lora-v2
modal volume get microfactory-node-finetune gguf/ --force
```

**Track B (v3, no upload):**
```bash
modal run learn/finetune/gguf_pipeline_modal.py::main \
  --base google/gemma-4-E4B-it-qat-q4_0-unquantized \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat
```

**Gotchas (encountered during the v1/v2/v3 push):**
- `modal run gguf_pipeline_modal.py` (without `::main`) fails once you add a second `@app.local_entrypoint()` — always pass `::main` or `::upload_only`.
- Modal secret values can include trailing whitespace/newlines — the upload helper now strips the token (`token = token.strip()`); otherwise `httpx` raises `LocalProtocolError: Illegal header value b'Bearer  hf_xxx   '`.
- Use absolute paths to the pipeline file when launching with `nohup &` — backgrounded shells lose cwd faster than you'd expect.

**After download — Ollama import:**
```bash
cat > Modelfile << 'EOF'
FROM ./microfactory-node.gguf
TEMPLATE """{{ if .System }}<start_of_turn>system
{{ .System }}<end_of_turn>
{{ end }}<start_of_turn>user
{{ .Prompt }}<end_of_turn>
<start_of_turn>model
"""
PARAMETER stop "<start_of_turn>user"
PARAMETER stop "<end_of_turn>"
EOF
ollama create microfactory-node-v2 -f Modelfile
ollama run microfactory-node-v2
ollama push kylebrodeur/microfactory-node-v2
```

### Decision: Merge→GGUF over adapter paths

I chose the merge path (single GGUF file) over Path A (LoRA→GGUF adapter) and Path B (Ollama ADAPTER command) because:
- A single GGUF file means no runtime adapter complexity.
- Ollama ADAPTER command is only documented for Gemma 1/2. I have not verified it for Gemma 4.
- I have not tested `convert_lora_to_gguf.py` compatibility with Gemma 4.
- Merge→GGUF is the most battle-tested path.

### Quantization

The GGUF pipeline uses `--outtype q4_k_m` by default:
- **Does NOT reduce parameter count**: 8B params stay 8B. Quantization reduces weight precision from 16-bit (bf16) to 4-bit per weight.
- **File size**: ~5-6GB for 8B model (vs ~16GB for bf16 safetensors)
- **Quality**: q4_k_m is the recommended balance of size vs quality
- **v3 advantage**: QAT-trained model retains more quality after quantization because it was trained with simulated quantization during fine-tuning

Other quantization options (pass `--outtype` to override):

| Format | Size (8B) | Quality | Use Case |
|--------|-----------|---------|----------|
| q8_0 | ~8.5GB | Near-lossless | Max quality, local GPU |
| q4_k_m | ~5.5GB | Good | Balanced (default) |
| q4_k_s | ~5.0GB | Slightly lower | Tight storage |
| q4_0 | ~4.5GB | Lower | QAT-optimized (Google's QAT Q4_0 target) |

### Parallel GGUF runs

Both tracks can run at the same time. The pipeline uses separate Modal functions (merge on GPU, convert on CPU) and writes distinct output filenames via `--name`:

```bash
# Terminal 1 — v2:
modal run learn/finetune/gguf_pipeline_modal.py \
  --adapter kylebrodeur/microfactory-node-lora-v2 \
  --name microfactory-node-v2

# Terminal 2 — v3 (simultaneously):
modal run learn/finetune/gguf_pipeline_modal.py \
  --base google/gemma-4-E4B-it-qat-q4_0-unquantized \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat \
  --name microfactory-node-v3-qat
```

Download both: `modal volume get microfactory-node-finetune gguf/ --force`

---

## 2. Modal Model Hosting — Implemented

### Status: Deploying (`ap-60wirJOd35PZl1ZIKakD9v`)

### Implemented: `modal_serve.py`

OpenAI-compatible `/v1/chat/completions` endpoint on Modal GPU. It loads base model + LoRA adapter once at container start and keeps warm. It auto-scales to zero after 5 min idle (`scaledown_window=300`). It handles up to 10 concurrent requests (`@modal.concurrent(max_inputs=10)`).

Deploy:
```bash
modal deploy learn/finetune/modal_serve.py
```

Test:
```bash
curl -X POST https://kylebrodeur--microfactory-node-inference.modal.run/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"PLA overhang at 22C, 45% humidity"}],"max_tokens":512}'
```

Switch adapters by redeploying with env var:
```bash
FINETUNE_ADAPTER=kylebrodeur/microfactory-node-lora-v3-qat modal deploy learn/finetune/modal_serve.py
```

### Modal API Deprecation Fixes Applied

During deployment I hit two Modal SDK deprecations and fixed them:
1. `container_idle_timeout` → `scaledown_window` (deprecated 2025-02-24)
2. `allow_concurrent_inputs` → `@modal.concurrent(max_inputs=10)` decorator (deprecated 2025-04-09)

### Budget: Separate $100 serving budget

This is separate from the ~$11.54 training budget I already spent. Serving costs:
- A10G active: ~$5.04/hr
- With scale-to-zero: ~$0.50-2.00/day typical
- Health check endpoint at `/health` for monitoring

---

## 3. Gradio Model Switching — Backend Implemented, UI Deferred

### Status: Backend ready, UI placement deferred to other agent

### Implemented: `core/llm_zerogpu_lora.py`

LoRA-aware ZeroGPU backend. It has the same API as `llm_zerogpu.py` (`chat_json`, `warm`, `backend_status`) but wraps the base model with `PeftModel.from_pretrained()` when `CHIEF_ENGINEER_LORA_REPO` is set. It is import-guarded — safe no-op if torch/transformers are absent.

### Implemented: `app.py` backend infrastructure

I added this to `app.py` (merged with UI agent's concurrent changes):
- `MODEL_OPTIONS` list: "Base (Gemma 4 E4B)", "LoRA v2 (Standard E4B)", "LoRA v3 (QAT E4B)", "Modal API (remote)"
- `MODEL_LORA_MAP` dict: maps UI labels → HF Hub adapter repo IDs
- `_apply_model_choice()` function: sets `CHIEF_ENGINEER_LORA_REPO` and `CHIEF_ENGINEER_BACKEND` env vars, reloads `core.llm` module
- `build_job()` now accepts `model_choice` parameter (defaults to "Base (Gemma 4 E4B)")
- `core.llm_zerogpu_lora` imported at Space startup alongside `core.llm_zerogpu`

### UI placement rolled back

Per user request (another agent is handling the Gradio UI), I removed the dropdown widget placement and HTML note from `app.py`. The backend infrastructure remains so the UI agent can wire it in.

### UI Agent Handoff (2026-06-14)

**Already done (do NOT re-implement):**
- `core/llm_zerogpu_lora.py` — LoRA-aware ZeroGPU backend
- `app.py` — `_apply_model_choice()` function, `MODEL_OPTIONS` list, `MODEL_LORA_MAP` dict
- `app.py` — `build_job()` now accepts `model_choice` parameter
- `app.py` — `core.llm_zerogpu_lora` imported at startup

**What the UI agent needs to do:**
1. Add a `gr.Dropdown` with `MODEL_OPTIONS` choices in the STUDIO tab
2. Wire `model_choice` into the `build_job` call in the event handler
3. Add info line: "Local users: get LoRA models from HF Hub or `ollama pull`"
4. `_apply_model_choice()` handles all backend switching automatically

---

## 4. Immediate Actions

| Priority | Action | File | Status |
|----------|--------|------|--------|
| 🔴 HIGH | Fix `llm_zerogpu.py` E2B→E4B | `core/llm_zerogpu.py` | ✅ DONE |
| 🔴 HIGH | Clone llama.cpp for GGUF conversion | Local setup | ✅ DONE (via Modal) |
| 🟡 MED | Create `core/llm_zerogpu_lora.py` | New file | ✅ DONE |
| 🟡 MED | Add model selector dropdown to `app.py` | `app.py` | ✅ DONE |
| 🟢 LOW | Create `modal_serve.py` for Modal inference | New file | ✅ DONE |
| 🟢 LOW | Create `gguf_pipeline_modal.py` for GGUF on Modal | New file | ✅ DONE |
| 🟢 LOW | Add explicit Track B Ollama commands to RUNBOOK.md | `RUNBOOK.md` | ✅ DONE |

---

## 5. Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `core/llm_zerogpu.py` | ✏️ Modified | E2B→E4B fix |
| `core/llm_zerogpu_lora.py` | ✨ Created | LoRA-aware ZeroGPU backend |
| `app.py` | ✏️ Modified | Add model selector dropdown + wiring |
| `learn/finetune/modal_serve.py` | ✨ Created | Modal inference API endpoint |
| `learn/finetune/gguf_pipeline_modal.py` | ✨ Created | Full merge→GGUF pipeline on Modal |
| `learn/finetune/RUNBOOK.md` | ✏️ Modified | Add Track B Ollama + GGUF pipeline commands |
| `learn/finetune/SERVING.md` | ✨ Created | This document |
