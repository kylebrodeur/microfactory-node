[[KB: Created the space and setup HF CLI and Skills locally so we can manage it and update as needed. Update docs to review and make the changes need to push to space.]]

# 08 — ZeroGPU live-inference deploy (staged, off by default)

Closes the weakness in `docs/writeup/05-PROJECTED-OUTCOME.md` §3: lets the
published Space run the **real model** (not just the deterministic fallback) so
a judge who *opens* the Space sees real precedent-evaluation, matching the video.

**Plan update (6/10): Kyle is recording *from the Space*.** Since Ollama can't run
on a Space, live on-screen reasoning there must come from ZeroGPU — so this is now
on the recording path, not a post-submission nicety. The discipline still holds:
the **deterministic fallback is the safety net** (if ZeroGPU is flaky/gated/slow on
the day, you can still record the fallback or fall back to the local Ollama take).
Keep a known-good fallback Space (this same repo, line commented) as Plan B.
---

## How it's wired (already in the code)

- `core/llm_zerogpu.py` — transformers backend, `@spaces.GPU`-decorated generate,
  import-guarded heavy deps, JSON-contract-compatible with `llm.chat_json`.
- `core/llm.py` — dispatches to it ONLY when `CHIEF_ENGINEER_BACKEND=zerogpu`;
  otherwise behaves exactly as today (Ollama → fallback). Import failure or an
  unloadable model silently degrades to the fallback. Nothing local changes.
- `requirements-zerogpu.txt` — the deploy-only deps (kept out of base reqs).

So the entire feature is behind one env var. Local dev, tests, and recording are
untouched.

## To turn it on — the one-step flip (now wired)

1. **Hardware:** set the Space to **ZeroGPU** (org/Pro; `spaces` is provided by the
   runtime). Add `python_version: "3.11"` to the README frontmatter if not default.
2. **Deps — one line:** in `requirements.txt`, uncomment
   `# -r requirements-zerogpu.txt` → it pulls torch/transformers/accelerate/spaces.
   (Leave it commented on the light CPU fallback Space.)
3. **Env vars** (Space → Settings → Variables/Secrets):
   - `CHIEF_ENGINEER_BACKEND=zerogpu`
   - `CHIEF_ENGINEER_HF_MODEL=google/gemma-4-E2B-it`  (see Model choice)
   - if the model is gated: add `HF_TOKEN` (a secret) **and** accept the license on
     the model's HF page with the same account.
   - optional: `CHIEF_ENGINEER_GPU_SECONDS` (default 90 — the first call loads the
     model), `CHIEF_ENGINEER_MAX_NEW_TOKENS` (512).
4. Redeploy. Banner reads "🟢 live · google/gemma-4-E2B-it (transformers on ZeroGPU)
   (loads on first analyze)". A cold/errored model still degrades to deterministic —
   never a crash.

## Recording from the Space (the new plan)

- **Pre-warm.** The first ANALYZE downloads + loads the model inside the GPU window
  (tens of seconds). Do one throwaway analyze, wait for "🟢 … (loaded)", *then*
  record — warm calls on a ZeroGPU H200 are fast (sub-few-seconds), far quicker than
  local CPU. Same pre-warm habit as local, different reason.
- **Queue/quota.** ZeroGPU time-shares the GPU; there can be a short queue and a
  per-user daily GPU-seconds quota. Record in one sitting; don't burn the quota on
  retries — use the local/offline path for rehearsal, the Space for the real take.
- **Reset state** before takes: the Space ledger persists between sessions just like
  local; clear it (or redeploy) so "seed → earned" reads clean on camera.
- **Plan B stays armed:** if ZeroGPU misbehaves on the day, record the local Ollama
  take (RUNBOOK Phase 3) or the deterministic fallback — the story survives either way.

## Model choice — RESOLVED 6/10 (web-verified ids; spot-check the repo page once)

- **Primary (safe): `google/gemma-4-E2B-it`** (or `-E4B-it`) — bf16,
  transformers-native, loads with `AutoModelForCausalLM` in `core/llm_zerogpu.py`
  as-is. ZeroGPU H200s have ample memory; QAT isn't needed for capacity.
- **Option (smaller/faster, unverified on ZeroGPU):**
  `google/gemma-4-E2B-it-qat-mobile-transformers` (~1GB; ⚠ its 2-bit decode
  layers are NOT confirmed to run unmodified on ZeroGPU — test before relying).
- **Do NOT point transformers at the GGUF repos**
  (`google/gemma-4-E2B-it-qat-q4_0-gguf`, `unsloth/...-GGUF`) — llama.cpp only.
- **Gating:** sources conflict on whether `google/` Gemma-4 repos are gated
  (weights are Apache 2.0). Check the repo page; if gated, accept the agreement
  + set `HF_TOKEN` on the Space, or use an ungated mirror.
- ≤32B total params: satisfied either way (E2B 5.1B / E4B 8.0B raw).
- Gemma chat template has **no system role**; `core/llm_zerogpu.py` already folds the
  system prompt into the first user turn (the standard Gemma pattern).

## Story reconciliation (don't undercut Off-the-Grid)

Using ZeroGPU does NOT weaken the local-first claim. The thesis is "it *can* run
fully local, on consumer hardware, for free" — proven in the video (offline,
on Kyle's laptop via Ollama). ZeroGPU is only the hosted convenience so judges
can try it live without pulling a model. State it exactly that way in the
writeup: local-first is the headline; the live Space is a courtesy.

## gradio.Server — the future custom-frontend path (Off-Brand award; post-baseline)

The [gradio.Server blog](https://huggingface.co/blog/introducing-gradio-server)
(2026-04-01) is the clean unlock for stretch #5: it extends **FastAPI** so you can
bring **any** frontend (React/Svelte/plain HTML/JS) while keeping Gradio's queuing,
SSE streaming, `gradio_client`, MCP, **and ZeroGPU `@spaces.GPU`** — `@app.api()`
wraps your function with the queue + GPU allocation. So a fully custom Astrometrics
frontend over our Python backend (`advise`/`ledger`/`spine`/`sim`) is legitimate AND
ZeroGPU-compatible — and it would still count as a Gradio Space. This revises the
earlier "don't do React" call: with gradio.Server, a custom frontend doesn't mean
abandoning Gradio's engine. Still a big lift and strictly **post-recording** — but
if we chase the Off-Brand *award*, this is the door, not a from-scratch SPA.

## Validate before trusting it live

- It cannot be exercised from the build sandbox (no torch/GPU). On the Space:
  open cold, confirm the banner is green, run the four scripted-demo jobs, and
  re-check the §G4 reasoning quality and the novel "no precedent" case there too
  — ZeroGPU output may differ from local Ollama output; don't assume parity.
