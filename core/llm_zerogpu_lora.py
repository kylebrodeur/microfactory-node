"""ZeroGPU LoRA inference backend — loads fine-tuned adapters on the Space.

Extends llm_zerogpu.py to wrap the base model with a PeftModel (LoRA adapter)
after loading. The adapter is only 35MB — loads in ~2 seconds after the base
model is in memory.

Activation: Set CHIEF_ENGINEER_LORA_REPO to a HF Hub adapter repo id.
  CHIEF_ENGINEER_LORA_REPO=kylebrodeur/microfactory-node-lora-v2

This module is import-guarded like llm_zerogpu.py — absent deps → safe no-op.
"""

from __future__ import annotations

import json
import os
import re

HF_MODEL = os.environ.get("CHIEF_ENGINEER_HF_MODEL", "google/gemma-4-E4B-it")
LORA_REPO = os.environ.get("CHIEF_ENGINEER_LORA_REPO", "")
_GPU_SECONDS = int(os.environ.get("CHIEF_ENGINEER_GPU_SECONDS", "90"))
_MAX_NEW = int(os.environ.get("CHIEF_ENGINEER_MAX_NEW_TOKENS", "512"))

try:
    import torch  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    _HAVE_HF = True
except Exception:
    torch = None  # type: ignore
    _HAVE_HF = False

try:
    import spaces  # type: ignore
    _HAVE_SPACES = True
except Exception:
    _HAVE_SPACES = False


def _gpu(fn):
    if _HAVE_SPACES:
        return spaces.GPU(duration=_GPU_SECONDS)(fn)
    return fn


_tok = None
_model = None


def _ensure_loaded() -> bool:
    global _tok, _model
    if not _HAVE_HF:
        return False
    if _model is not None:
        return True
    try:
        _tok = AutoTokenizer.from_pretrained(HF_MODEL)
        base = AutoModelForCausalLM.from_pretrained(
            HF_MODEL,
            dtype=getattr(torch, "bfloat16", None),
            low_cpu_mem_usage=True,
        )
        if LORA_REPO:
            from peft import PeftModel
            _model = PeftModel.from_pretrained(base, LORA_REPO)
        else:
            _model = base
        if torch is not None and torch.cuda.is_available():
            _model = _model.to("cuda")
        return True
    except Exception:
        _tok = _model = None
        return False


def is_available() -> bool:
    return _HAVE_HF


def backend_status() -> str:
    where = "ZeroGPU" if _HAVE_SPACES else "local GPU/CPU"
    if not _HAVE_HF:
        return "offline fallback · transformers/torch absent (deterministic)"
    lora_tag = f" + LoRA({LORA_REPO.split('/')[-1]})" if LORA_REPO else ""
    loaded = " (loaded)" if _model is not None else " (loads on first analyze)"
    return f"live · {HF_MODEL}{lora_tag} (transformers on {where}){loaded}"


def _build_prompt(system: str, user: str) -> str:
    messages = [{"role": "user", "content": f"{system}\n\n{user}"}]
    return _tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


@_gpu
def _generate(system: str, user: str, temperature: float) -> str | None:
    if not _ensure_loaded():
        return None
    prompt = _build_prompt(system, user)
    if torch is not None and torch.cuda.is_available() and _model.device.type != "cuda":
        _model.to("cuda")
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
    try:
        text = _generate(system, user, temperature)
    except Exception:
        return None
    if not text:
        return None
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    m = _JSON.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None
