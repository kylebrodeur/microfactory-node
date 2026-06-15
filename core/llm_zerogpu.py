"""ZeroGPU inference backend — STAGED for the published HF Space, OFF by default.

Why this exists: `docs/writeup/05-PROJECTED-OUTCOME.md` §3 flags that a judge who
opens our Space sees the deterministic FALLBACK (Ollama can't run on a standard
CPU Space), while only the video shows the real model. This module lets the LIVE
Space run the real model on **ZeroGPU** with a **QAT Gemma** checkpoint — closing
that gap — WITHOUT changing anything locally or in the current demo path.

Activation is opt-in and total:
  - Selected ONLY when `CHIEF_ENGINEER_BACKEND=zerogpu`. Otherwise `llm.py`
    behaves exactly as before (Ollama → deterministic fallback). Nothing about
    the local dev / recording flow changes.
  - Deploy-only deps (torch/transformers/accelerate/spaces) live in
    `requirements-zerogpu.txt`, NOT base `requirements.txt`, and are import-
    guarded here — importing this on a box without them is a safe no-op that
    reports unavailable.

It preserves the Off-the-Grid story: the model CAN run fully local (proven in the
video); ZeroGPU is just the hosted convenience so judges can try it live.

Model ids RESOLVED 6/10 — see docs/_archive/08-ZEROGPU-DEPLOY.md (primary:
google/gemma-4-E2B-it, bf16 transformers-native). Original checklist:
  - Set `CHIEF_ENGINEER_HF_MODEL` to the QAT Gemma checkpoint you pick. Google's
    Gemma QAT int4 releases are the target. CONFIRM the exact repo id AND that it
    loads via `transformers` — some QAT releases ship **GGUF** (for llama.cpp);
    for those, use a llama-cpp-python path, not this transformers one.
  - Confirm the model is ≤32B (hackathon rule) and note its params for Tiny Titan.
See `docs/_archive/08-ZEROGPU-DEPLOY.md`.
"""

from __future__ import annotations

import json
import os
import re

HF_MODEL = os.environ.get("CHIEF_ENGINEER_HF_MODEL", "google/gemma-4-E4B-it")  # matches live gemma4:e4b
_GPU_SECONDS = int(os.environ.get("CHIEF_ENGINEER_GPU_SECONDS", "90"))  # 1st call loads the model
_MAX_NEW = int(os.environ.get("CHIEF_ENGINEER_MAX_NEW_TOKENS", "512"))

# Import-guarded heavy deps. Absent locally → module reports unavailable, no crash.
try:
    import torch  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    _HAVE_HF = True
except Exception:  # pragma: no cover
    torch = None  # type: ignore
    _HAVE_HF = False

try:
    import spaces  # type: ignore  (the ZeroGPU package; only present on the Space)
    _HAVE_SPACES = True
except Exception:  # pragma: no cover
    _HAVE_SPACES = False


def _gpu(fn):
    """Decorate with @spaces.GPU when available; identity off-Space (e.g. local GPU)."""
    if _HAVE_SPACES:
        return spaces.GPU(duration=_GPU_SECONDS)(fn)
    return fn


_tok = None
_model = None


def _ensure_loaded() -> bool:
    """Load tokenizer + model once. MUST be called inside the @spaces.GPU context on
    ZeroGPU (GPU is only allocated there) — we load to CPU then move to CUDA. No
    device_map='auto' (discouraged on ZeroGPU; it grabs devices outside the GPU window)."""
    global _tok, _model
    if not _HAVE_HF:
        return False
    if _model is not None:
        return True
    try:
        _tok = AutoTokenizer.from_pretrained(HF_MODEL)
        _model = AutoModelForCausalLM.from_pretrained(
            HF_MODEL,
            torch_dtype=getattr(torch, "bfloat16", None),
            low_cpu_mem_usage=True,
        )
        if torch is not None and torch.cuda.is_available():
            _model = _model.to("cuda")
        return True
    except Exception:
        _tok = _model = None
        return False


def is_available() -> bool:
    """Whether this backend CAN serve — i.e. the heavy deps imported. The actual
    model load is lazy (first chat, inside the GPU window), so we don't block app
    startup on a multi-GB load that would also run outside the GPU allocation."""
    return _HAVE_HF


def backend_status() -> str:
    where = "ZeroGPU" if _HAVE_SPACES else "local GPU/CPU"
    if not _HAVE_HF:
        return ("<span style='color:var(--ao-yellow);'>●</span> offline fallback · "
                "transformers/torch absent (deterministic)")
    loaded = " (loaded)" if _model is not None else " (loads on first analyze)"
    return (f"<span style='color:var(--ao-green);'>●</span> live · "
            f"{HF_MODEL} (transformers on {where}){loaded}")


def _build_prompt(system: str, user: str) -> str:
    # Gemma's chat template has no separate system role — fold system into the
    # first user turn (the standard Gemma pattern).
    messages = [{"role": "user", "content": f"{system}\n\n{user}"}]
    return _tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


@_gpu
def _generate(system: str, user: str, temperature: float) -> str | None:
    if not _ensure_loaded():
        return None
    prompt = _build_prompt(system, user)
    if torch is not None and torch.cuda.is_available() and _model.device.type != "cuda":
        _model.to("cuda")                       # ZeroGPU: ensure on-GPU during the call
    inputs = _tok(prompt, return_tensors="pt").to(_model.device)
    out = _model.generate(
        **inputs,
        max_new_tokens=_MAX_NEW,
        do_sample=temperature > 0,
        temperature=max(temperature, 1e-4),
    )
    text = _tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    return text


@_gpu
def warm() -> str:
    """Load the model inside the GPU window and run a 1-token generation so the cold
    start (and CUDA kernel init) is paid now, not on the first BUILD. Returns status."""
    if not _ensure_loaded():
        return backend_status()
    try:
        if torch is not None and torch.cuda.is_available() and _model.device.type != "cuda":
            _model.to("cuda")
        inputs = _tok("ok", return_tensors="pt").to(_model.device)
        _model.generate(**inputs, max_new_tokens=1, do_sample=False)
    except Exception:
        pass
    return backend_status()


_JSON = re.compile(r"\{.*\}", re.DOTALL)


def chat_json(system: str, user: str, temperature: float = 0.4) -> dict | None:
    """Mirror of llm.chat_json's contract: parsed dict, or None to trigger fallback."""
    try:
        text = _generate(system, user, temperature)
    except Exception:
        return None
    if not text:
        return None
    # Strip code fences, then grab the outermost JSON object.
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    m = _JSON.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None
