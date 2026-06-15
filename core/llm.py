"""Local Ollama client (real calls, not mocks).

Fully local Gemma inference → earns Off the Grid + Llama Champion by
construction (Ollama runs on llama.cpp). The UI surfaces which model ran and
whether it was a real call or the deterministic fallback (never crash the demo).

`gemma4:e4b` is the default (= gemma4:latest, 9.6GB). `gemma4:e2b` if CPU
latency demands. NOTE: `gemma4:4b` does NOT exist — never use that tag.
"""

from __future__ import annotations

import json
import os

MODEL = os.environ.get("CHIEF_ENGINEER_MODEL", "gemma4:e4b")
MODAL_API_URL = os.environ.get("CHIEF_ENGINEER_MODAL_URL",
    "https://kylebrodeur--microfactory-node-inference-serve.modal.run/v1/chat/completions")

# Backend select. Default "ollama" keeps local/recording behavior IDENTICAL.
# CHIEF_ENGINEER_BACKEND is the *initial default* (e.g. a Space var = zerogpu); it is
# NOT a hard lock. The in-app model switcher changes the backend at runtime by setting
# the env var, so routing reads it dynamically via _backend() — a fixed Space var would
# otherwise freeze the ZeroGPU<->Modal switch. BACKEND keeps the startup value for
# back-compat/logging. Unknown/import-fail → ollama.
BACKEND = os.environ.get("CHIEF_ENGINEER_BACKEND", "ollama").lower()


def _backend() -> str:
    """Active backend, read dynamically so the model switcher's selection takes effect
    at runtime (the dropdown sets CHIEF_ENGINEER_BACKEND via app._apply_model_choice)."""
    return os.environ.get("CHIEF_ENGINEER_BACKEND", BACKEND).lower()


try:
    import ollama  # type: ignore
except Exception:  # pragma: no cover
    ollama = None  # type: ignore


def _zerogpu():
    """Lazily import the ZeroGPU backend; None unless selected and importable.

    Prefer the LoRA-aware backend when the model switcher has selected an adapter
    (CHIEF_ENGINEER_LORA_REPO set, read dynamically so a runtime switch takes effect).
    Otherwise the base ZeroGPU backend. Without this, the switcher's LoRA selections
    would silently serve the base model — the UI would say one thing and serve another."""
    if _backend() != "zerogpu":
        return None
    try:
        if os.environ.get("CHIEF_ENGINEER_LORA_REPO"):
            from . import llm_zerogpu_lora  # heavy deps are import-guarded inside
            return llm_zerogpu_lora
        from . import llm_zerogpu  # heavy deps are import-guarded inside
        return llm_zerogpu
    except Exception:
        return None


def _modal_api():
    """Lazily check if Modal API backend is selected."""
    if _backend() != "modal":
        return None
    return True  # Modal API is always available (HTTP endpoint)


def _forced_offline() -> bool:
    """Force the deterministic fallback path regardless of any daemon/backend.
    Read dynamically (not cached) so tests can toggle it. Used by the offline
    core suite so `make test` never touches Ollama, even when `ollama serve` is up."""
    return os.environ.get("CHIEF_ENGINEER_OFFLINE", "").lower() in ("1", "true", "yes")


def is_available() -> bool:
    """True if the active backend can serve a real call."""
    if _forced_offline():
        return False
    zg = _zerogpu()
    if zg is not None:
        return zg.is_available()
    if _modal_api():
        return True
    if ollama is None:
        return False
    try:
        ollama.list()
        return True
    except Exception:
        return False


def backend_status() -> str:
    zg = _zerogpu()
    if zg is not None:
        return zg.backend_status()
    if _modal_api():
        return f"<span style='color:var(--ao-green);'>●</span> live · Modal API (remote GPU)"
    return (f"<span style='color:var(--ao-green);'>●</span> live · {MODEL} (local Ollama)"
            if is_available() else
            f"<span style='color:var(--ao-yellow);'>●</span> offline fallback · "
            f"{MODEL} unreachable (deterministic)")


def warm_up() -> str:
    """Pay the model's cold start now (off-camera), so the first real BUILD is fast.
    On ZeroGPU this enters the GPU window and loads the model; on Ollama/fallback it is
    a cheap no-op. On Modal API it's a no-op (Modal handles its own warm-up).
    Returns the (post-load) backend status. Never raises."""
    zg = _zerogpu()
    if zg is not None:
        try:
            return zg.warm()
        except Exception:
            return backend_status()
    return backend_status()


def chat_json(system: str, user: str, temperature: float = 0.4) -> dict | None:
    """One JSON-mode chat turn. Returns parsed dict, or None to signal fallback."""
    if _forced_offline():
        return None
    zg = _zerogpu()
    if zg is not None:
        try:
            return zg.chat_json(system, user, temperature)
        except Exception:
            return None
    if _modal_api():
        try:
            import urllib.request
            body = json.dumps({
                "messages": [{"role": "user", "content": f"{system}\n\n{user}"}],
                "max_tokens": 512,
                "temperature": temperature,
            }).encode()
            req = urllib.request.Request(MODAL_API_URL, data=body,
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                text = data["choices"][0]["message"]["content"].strip()
                if text.startswith("```"):
                    text = text.strip("`").lstrip()
                    if text[:4].lower() == "json":
                        text = text[4:]
                return json.loads(text)
        except Exception:
            return None
    if not is_available():
        return None
    try:
        resp = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            format="json",
            options={"temperature": temperature},
        )
        content = resp["message"]["content"].strip()
        # Fence-strip safety net (GEMMA-STEERING Technique 2): small Gemmas can
        # wrap JSON in ```json fences even in JSON mode. Strip before parsing.
        if content.startswith("```"):
            content = content.strip("`").lstrip()
            if content[:4].lower() == "json":
                content = content[4:]
        return json.loads(content)
    except Exception:
        return None
