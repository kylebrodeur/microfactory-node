# Fine-tune track: the "Well-Tuned" frontier, realized (parallel, optional)

I run the live node on retrieval plus a learned policy plus the deterministic Spine. That keeps the memory visible. This track bakes the same judgment into a small Gemma LoRA so it lives in the weights too. I train it in parallel while I record. It never touches the live Space. I only claim the Well-Tuned badge if a held-out eval earns it.

## Files

- `prep_dataset.py`: builds `data/finetune/sft.{train,eval}.jsonl` (400 train / 80 held-out) by distilling the node's own Advice over a grid of material, geometry, and room. I already generated and committed this. Offline targets come from the deterministic advisor. Start `ollama serve` first to distill the live Gemma instead; the format stays the same.
- `train_modal.py`: Modal LoRA SFT (A10G, ~1 hr cap), pushes the adapter to the Hub.
- `eval.py`: honest base-vs-LoRA scoring on the held-out rooms. Checks JSON validity and Spine safety.
- `gguf_pipeline_modal.py`: end-to-end LoRA → merged HF → quantized GGUF → optional HF Hub upload. Two entrypoints: `::main` (full pipeline) and `::upload_only` (re-upload an existing volume file; use `--as-name` to rewrite the HF filename, e.g. q4_0 suffix).
- `SERVING.md`: production hosting playbook — ZeroGPU, Modal-hosted OpenAI endpoint, model switching in the Gradio app, current quant/HF/Ollama table.
- `OLLAMA_PUBLISHING.md`: end-to-end walkthrough for publishing GGUFs to ollama.com. Read this before publishing the next adapter.

## Published artifacts

- LoRA adapters — [`microfactory-node-lora`](https://huggingface.co/kylebrodeur/microfactory-node-lora) (v1) · [`-lora-v2`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v2) · [`-lora-v3-qat`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v3-qat)
- GGUFs (HF Hub) — [`kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf) (v1, v2, v3-qat q4_k_m, v3-qat q4_0)
- GGUFs (ollama.com) — [`kylebrodeur/microfactory-node`](https://ollama.com/kylebrodeur/microfactory-node), [`-v2`](https://ollama.com/kylebrodeur/microfactory-node-v2), [`-v3-qat`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat), [`-v3-qat:q4_0`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0)
- Modal inference API — `https://kylebrodeur--microfactory-node-inference-serve.modal.run`

## Honesty guardrails (non-negotiable)

- The live Space stays retrieval-based. The LoRA is the named frontier, realized, not a swap.
- Targets are the node's structured output. I distill them faithfully. I do not invent data.
- I only claim Well-Tuned if `eval.py` shows TUNED >= BASE on json-valid AND spine-safe, and the sampled advice reads as real judgment, not a memorized template. If it only parrots, I report that and stay "Not Well-Tuned." A thin badge is worse than an honest no.

## Budget

I have ~$100 Modal available plus run credits. A LoRA on ~400 short examples on one A10G is roughly a 30 to 60 min run, well under $2. There is no reason to exceed that. The dataset is small on purpose.

---

## KICKOFF PROMPT (paste into a fresh LOCAL Claude Code session with modal + hf access)

```
You're in chief-engineer/ on branch claude/microfactory-gradio-hackathon-9e81fh. Goal: stand up
and TEST the Modal LoRA fine-tune so we can decide on the Well-Tuned badge. Do NOT touch app.py,
core/, or the live Space. Budget: ~$100 Modal + run credits (a LoRA run is well under $2).

Read first: learn/finetune/README.md, learn/finetune/{prep_dataset,train_modal,eval}.py,
core/prompts.py (the prompt format), core/models.py (the Advice contract).

1. Prereqs: `uv pip install modal && modal token set`. Confirm the Space secret
   `chief-engineer-secrets` carries an HF_TOKEN with WRITE scope, and that you've accepted the
   base model's license on HF (default base: google/gemma-4-E4B-it; pick another small, loadable,
   ungated-by-you Gemma if that one is gated for you and update FINETUNE_BASE).
2. Data: `uv run python -m learn.finetune.prep_dataset` (already committed; regenerate with
   `ollama serve` running to distill the LIVE model for higher-fidelity targets).
3. SMOKE TEST CHEAP FIRST: `modal run learn/finetune/train_modal.py --epochs 1` on a small slice
   to confirm the image builds, the GPU attaches, the chat template maps, and a checkpoint saves.
   Fix any image/dep/template issues before the full run.
4. Full run: `modal run learn/finetune/train_modal.py --push-to <hf-user>/microfactory-node-lora`.
5. Eval honestly: `uv run python -m learn.finetune.eval --adapter <hf-user>/microfactory-node-lora`
   (on a GPU box / Modal). Capture json-valid %, spine-safe % for BASE and TUNED, plus 3 to 5 sample
   (job -> advice) pairs.
6. REPORT BACK (do not flip any badge yourself): the adapter repo id, the eval table, the samples,
   the actual Modal cost, and your honest read on whether the tune is real or just parroting. I'll
   verify, and only then do we (a) claim Well-Tuned in the README + writeup and (b) wire an optional
   backend toggle to load it.
```

## Model card (for the adapter repo, once trained)

```markdown
---
base_model: google/gemma-4-E4B-it
library_name: peft
license: gemma
tags: [lora, 3d-printing, microfactory, build-small-hackathon]
---
# Microfactory Node: 3D Printer (LoRA)
A LoRA that distills the judgment of Microfactory Node: 3D Printer (Chief Engineer O'Brien) into
the weights of a small Gemma. The live node uses retrieval over a lesson ledger; this adapter is
the "bake it into the weights" frontier. Trained on settings/risk advice distilled from the node
over a grid of materials, geometries, and room conditions. Outputs the same Advice JSON contract
(settings + risk regions + reasoning). Use the deterministic Spine to validate any setting before
a printer sees it: this adapter does judgment, not safety.
```
