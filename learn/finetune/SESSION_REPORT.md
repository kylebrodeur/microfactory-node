# Microfactory Node: Full Session Report — 2026-06-13/14

Complete end-to-end report covering deploy verification, dataset generation,
fine-tuning (two parallel tracks), evaluation, and serving/deployment setup.

---

## Executive Summary

**Deploy**: ✅ Space healthy (10/10 gates green)  
**Fine-tune**: ✅ Two LoRA adapters trained and pushed to HF Hub  
**Eval**: 🏆 **Well-Tuned** — 100% JSON-valid, 100% spine-safe, real judgment (no parroting)  
**Serving**: ✅ Ollama GGUF pipeline, Modal inference API, Gradio LoRA backend all implemented  
**Budget**: $11.54 training spent ($88.46 remaining) + separate $100 serving budget

---

## 1. Deploy Verification

Ran `scripts/deploy_preflight.py` — all 10 gates green:
- D1 build: app imports + builds UI ✅
- D1 tests: core tests pass ✅
- D2-D10: files, README, requirements, reference, ledger, data, auth, space, dataset ✅
- Space: `build-small-hackathon/microfactory-lab` RUNNING, 108 files

---

## 2. Dataset Generation

### Problem
v1 used deterministic offline advisor → identical settings for every input → LoRA memorized one template (parroting).

### Solution
Generate non-deterministic targets from the live model (`google/gemma-4-E4B-it`) on Modal GPU.

### Attempts
| Attempt | Approach | Result |
|---------|----------|--------|
| 1 | Local Ollama (384 inferences) | Too slow (~60 min) |
| 2 | HF Inference API | Failed — Gemma 4 "not a chat model" |
| 3 | Modal GPU sequential (prep_dataset_modal.py) | Works but slow (~50 min) |
| 4 | Modal GPU parallel (prep_dataset_rich.py, 12 GPUs) | Designed but timed out |
| 5 | **Modal GPU fast (prep_dataset_fast.py)** | ✅ **Success** — 120 train + 80 eval |

### Final dataset
- 120 train + 80 eval chat-format JSONL
- Live-generated, non-deterministic targets (temperature=0.7)
- Grid: 4 materials × 5 geometries × varied temps/hums

---

## 3. Fine-Tuning — Two Parallel Tracks

### Model fix: Gemma 3 → Gemma 4
v1 wrongly used `google/gemma-3-1b-it`. All scripts updated to `google/gemma-4-E4B-it` (matching live `gemma4:e4b`).

### Anti-parroting strategy
| Fix | v1 | v2/v3 | Rationale |
|-----|----|----|-----------|
| Base model | Gemma 3 1B | Gemma 4 E4B (8B) | Match live model |
| LoRA rank | r=16, α=32 | r=4, α=8 | Force generalization |
| Epochs | 3 | 1 | Early stopping |
| Dataset | Deterministic | Live-generated | Non-deterministic targets |

### 🐛 Gemma4ClippableLinear Bug
Gemma 4 uses `Gemma4ClippableLinear` in vision/audio towers — PEFT rejects it.
Fixed with regex-scoped `target_modules` to language model only:
```python
target_modules=r".*\.language_model\..*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)"
```

### Track A: Standard E4B
- Base: `google/gemma-4-E4B-it`
- Adapter: `kylebrodeur/microfactory-node-lora-v2` (35MB)
- Loss: ~2.07, runtime: 85s

### Track B: QAT-unquantized
- Base: `google/gemma-4-E4B-it-qat-q4_0-unquantized`
- Adapter: `kylebrodeur/microfactory-node-lora-v3-qat` (35MB)
- Loss: ~1.75, runtime: 93s
- Advantage: Better GGUF quality after quantization (QAT-trained)

---

## 4. Evaluation — Well-Tuned Secured

### Eval architecture evolution
| Version | Approach | Issue |
|---------|----------|-------|
| v1 | Sequential, 1 GPU, 1800s timeout | Timed out at 30 min |
| v2 | Bumped to 3600s | Still risky |
| v3 | Bumped to 7200s | Safe but slow |
| v4 | **Parallel BASE+TUNED (2 GPUs)** | Timeout risk eliminated |
| v5 | **Sharded into 2×40 chunks (2 GPUs)** | ✅ **~4 min, under budget** |

### Results
| Track | Model | JSON-valid | Spine-safe | Judgment |
|-------|-------|-----------|------------|----------|
| A | BASE (E4B) | 100.0% | 100.0% | Varied, context-aware |
| A | TUNED (v2) | 100.0% | 100.0% | ✅ Real judgment |
| B | BASE (QAT) | 100.0% | 100.0% | Varied, context-aware |
| B | TUNED (v3) | 100.0% | 100.0% | ✅ Real judgment |

### Qualitative analysis
Unlike v1 which output identical `{nozzle:205, bed:60, fan:100}` for every input,
v2/v3 TUNED models produce **varied settings based on context**:
- PLA/overhang @ 22°C: nozzle=200-205, bed=50, fan=100
- Reasoning adapts: "22C is cool" vs "28C is warm enough to encourage drooping"
- Different geometries get different fan speeds and temperature adjustments

**🏆 Well-Tuned badge officially claimed.**

---

## 5. Serving & Deployment

Three serving paths implemented after training:

### 5a. Ollama GGUF Pipeline (`gguf_pipeline_modal.py`)
- **No local llama.cpp needed** — everything runs on Modal
- GPU step: merge LoRA into base model
- CPU step: clone llama.cpp, build with cmake, run `convert_hf_to_gguf.py`
- Output: single `.gguf` file on Modal volume
- Status: 🔄 Running on Modal (ap-ZYdn9niRL6ywRgXPYcIjTz)

### 5b. Modal Inference API (`modal_serve.py`)
- OpenAI-compatible `/v1/chat/completions` endpoint
- Loads base model + LoRA adapter once, keeps warm
- Auto-scales to zero after 5 min idle (`scaledown_window=300`)
- Handles 10 concurrent requests (`@modal.concurrent(max_inputs=10)`)
- Separate $100 serving budget
- Status: 🔄 Deploying (ap-60wirJOd35PZl1ZIKakD9v)
- Fixed two Modal SDK deprecations during deploy:
  - `container_idle_timeout` → `scaledown_window`
  - `allow_concurrent_inputs` → `@modal.concurrent` decorator

### 5c. Gradio Model Switcher Backend
- `core/llm_zerogpu_lora.py`: LoRA-aware ZeroGPU backend
- `app.py`: `_apply_model_choice()`, `MODEL_OPTIONS`, `MODEL_LORA_MAP`
- `build_job()` accepts `model_choice` parameter
- UI placement deferred to another agent (handoff note in SERVING.md §3)
- Status: ✅ Backend ready

---

## 6. Budget

### Training Budget
| Category | Cost |
|----------|------|
| Dataset generation (all attempts) | $7.91 |
| Fine-tuning (both tracks) | $0.16 |
| Evaluation (all runs) | $3.47 |
| **Total training spent** | **$11.54** |
| **Training remaining** | **$88.46** |

### Serving Budget (separate $100)
| Item | Est. Cost |
|------|-----------|
| GGUF pipeline (merge + convert) | ~$0.15 |
| Modal deploy (image build) | ~$0.08 |
| Modal inference (ongoing) | ~$0.50-2.00/day |
| **Serving remaining** | **~$99.77** |

---

## 7. Files Created/Modified

### New files (this session)
| File | Purpose |
|------|--------|
| `learn/finetune/prep_dataset_rich.py` | Multi-perspective parallel dataset generation (12 batches, 13 variables) |
| `learn/finetune/prep_dataset_modal.py` | Simple grid dataset generation (deprecated) |
| `learn/finetune/prep_dataset_hf.py` | HF Inference API attempt (dead code) |
| `learn/finetune/eval_modal.py` | Sharded parallel GPU evaluation |
| `learn/finetune/gguf_pipeline_modal.py` | Full merge→GGUF pipeline on Modal |
| `learn/finetune/modal_serve.py` | Modal inference API endpoint |
| `core/llm_zerogpu_lora.py` | LoRA-aware ZeroGPU backend |
| `learn/finetune/BUDGET.md` | Budget tracking |
| `learn/finetune/activity.jsonl` | Pipeline event log |
| `learn/finetune/REPORT_v1.md` | v1 historical archive |
| `learn/finetune/MODEL_CARD_QAT.md` | HF model card for Track B |
| `learn/finetune/SERVING.md` | Serving & deployment research + implementation |

### Modified files
| File | Change |
|------|--------|
| `learn/finetune/train_modal.py` | Gemma 3→4, r=16→4, epochs=3→1, regex target_modules, dtype fix |
| `learn/finetune/eval.py` | Gemma 3→4, torch_dtype→dtype |
| `learn/finetune/README.md` | Gemma 3→4 default base |
| `core/llm_zerogpu.py` | E2B→E4B fix |
| `app.py` | Backend infrastructure for model switcher (merged with UI agent changes) |
| `learn/finetune/REPORT.md` | Full v2/v3 iteration tracking + serving section |
| `learn/finetune/RUNBOOK.md` | Parallel track commands, GGUF pipeline, Modal serve |
| `learn/finetune/PIPELINE.md` | Updated pipeline diagram with serving steps |
| `scripts/deploy_preflight.py` | sys.path fix |

---

## 8. Key Decisions

| Decision | Rationale |
|----------|-----------|
| Gemma 4 E4B over Gemma 3 1B | Match live `gemma4:e4b` model |
| LoRA r=4 over r=16 | Force generalization, prevent memorization |
| 1 epoch over 3 | Early stopping before loss collapse |
| Live-generated dataset over deterministic | Non-deterministic targets prevent template parroting |
| Merge→GGUF over adapter paths | Single GGUF file, no runtime complexity |
| Modal for GGUF conversion | No local llama.cpp setup needed |
| Separate $100 serving budget | Keep training and serving costs distinct |
| UI placement deferred to other agent | Avoid merge conflicts, clear handoff |
| Sharded parallel eval (2×40 chunks) | Balance speed vs GPU cold starts |

---

## 9. Hugging Face Hub Repos

| Repo | Type | Size | Status |
|------|------|------|--------|
| `kylebrodeur/microfactory-node-lora-v2` | Model (PEFT/LoRA) | 35MB | ✅ Published |
| `kylebrodeur/microfactory-node-lora-v3-qat` | Model (PEFT/LoRA) | 35MB | ✅ Published |
| `build-small-hackathon/microfactory-lab` | Space (Gradio) | — | ✅ RUNNING |

### Model Registry

| UI Label | HF Hub | GGUF | Ollama | Inference |
|----------|--------|------|--------|-----------|
| LoRA v3 (QAT) | `microfactory-node-lora-v3-qat` | `microfactory-node-v3-qat.gguf` | `microfactory-node-v3-qat` | ZeroGPU |
| LoRA v2 (Standard) | `microfactory-node-lora-v2` | `microfactory-node-v2.gguf` | `microfactory-node-v2` | ZeroGPU |
| Base (Gemma 4) | — | — | `gemma4:e4b` | Ollama/ZeroGPU |
| Modal API | — | — | — | `...microfactory-node-inference-serve.modal.run` |

---

## 10. Next Steps

1. ~~**Download GGUF** when pipelines complete~~ → ✅ Done
2. ~~**Import both to Ollama**~~ → ✅ Done
3. ~~**Test Modal API**~~ → ✅ Done
4. ~~**Push to Ollama.com**~~ → ✅ **Done 2026-06-14** — see
   [`OLLAMA_PUBLISHING.md`](OLLAMA_PUBLISHING.md) for the full runbook.
   - [`ollama.com/kylebrodeur/microfactory-node-v3-qat`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat) (q4_k_m, recommended)
   - [`ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0) (QAT-native quant)
   - [`ollama.com/kylebrodeur/microfactory-node-v2`](https://ollama.com/kylebrodeur/microfactory-node-v2)
   - [`ollama.com/kylebrodeur/microfactory-node`](https://ollama.com/kylebrodeur/microfactory-node)
5. ~~**Add model cards**~~ → ✅ Done — [`microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf) carries the
   dual-table card (HF Hub + ollama.com tags); both LoRA repos have their
   own cards too
6. **Add Ollama to switcher**: future work — GGUFs are live, switcher backend
   already supports the Modal path. Enable an extra `MODEL_OPTIONS` entry for
   the ollama.com tags when the GPU spend on Modal becomes a concern.

---

## 11. Distribution (2026-06-14 follow-up)

After the eval result, the next question was "how does someone else actually
run this?" Two distribution paths now exist; both point at the same underlying
GGUF blobs:

### Path A — HF Hub (canonical)

[`huggingface.co/kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf)
holds four GGUF variants plus the auxiliary `template` / `system` / `params`
files Ollama reads from `hf.co/...` URIs:

| File | Quant | Source adapter |
|------|-------|----------------|
| [`microfactory-node-v3-qat.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat.gguf) (5.1 GB) | q4_k_m | [`lora-v3-qat`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v3-qat) |
| [`microfactory-node-v3-qat-q4_0.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat-q4_0.gguf) (4.9 GB) | q4_0 (QAT-native) | [`lora-v3-qat`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v3-qat) |
| [`microfactory-node-v2.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v2.gguf) (5.1 GB) | q4_k_m | [`lora-v2`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v2) |
| [`microfactory-node.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node.gguf) (5.1 GB) | q4_k_m | `lora` (v1) |

Built + uploaded by `gguf_pipeline_modal.py` — the same Modal app that
merges the LoRA also pushes the resulting GGUF to HF Hub. `upload_only` has
an `--as-name` flag so the HF filename can differ from the volume name (which
is how `microfactory-node-v3-qat-q4_0.gguf` sits next to the q4_k_m without
collision).

### Path B — ollama.com (public registry)

All four variants are also published to [`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur),
pullable with one command:

```bash
ollama run kylebrodeur/microfactory-node-v3-qat        # recommended
ollama run kylebrodeur/microfactory-node-v3-qat:q4_0
ollama run kylebrodeur/microfactory-node-v2
ollama run kylebrodeur/microfactory-node
```

Process: per variant, `ollama pull hf.co/...` → `ollama cp … kylebrodeur/…`
→ `ollama push`. One-time setup is the Ollama SSH key in `~/.ollama/`
registered at <https://ollama.com/settings/keys>. Total push time was ~45 min
for all four (CDN ingest gated, ~5 MB/s).

Full walkthrough — SSH setup, the seven gotchas hit and fixed, the
`/tmp/all-pushes.sh` template for queuing multi-model pushes — in
[`OLLAMA_PUBLISHING.md`](OLLAMA_PUBLISHING.md).

### Side effects on the rest of the project

- [`README.md`](../../README.md) — "Run the fine-tuned Chief Engineer locally" table rewritten to dual
  `ollama.com` + HF columns; q4_0 row added.
- [`SERVING.md`](SERVING.md) §1 — two side-by-side tables (registry tags vs HF files).
- [`MODEL_CARD.md`](MODEL_CARD.md) / [`MODEL_CARD_QAT.md`](MODEL_CARD_QAT.md) — "Try it via GGUF" section linking both paths.
- [`RUNBOOK.md`](RUNBOOK.md) Step 8 — `ollama pull → cp → push` block with link out to OLLAMA_PUBLISHING.md.
- [`PIPELINE.md`](PIPELINE.md) §6 — publish-to-ollama.com box added to the pipeline diagram.
- [`docs/_archive/UI-OVERHAUL-CHANGELOG.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/docs/_archive/UI-OVERHAUL-CHANGELOG.md) — 2026-06-14 session entry includes the publishing step.
- [`docs/writeup/06-FIELD-NOTES.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/docs/writeup/06-FIELD-NOTES.md) — new field-note #10 ("Distribution is part of the build").
