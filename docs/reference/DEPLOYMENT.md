# The Chief Engineer — HF Space Deployment Guide

**Space:** `build-small-hackathon/microfactory-lab`  
**Hardware:** zero-a10g (ZeroGPU)  
**Live:** https://node.microfactory.space (custom domain)  
**Status:** 🟢 LIVE — fallback URL: https://build-small-hackathon-microfactory-lab.hf.space

---

## Quick Summary

The Gradio app was failing on HF Spaces due to three platform-specific issues:
1. **SSR crash** — Gradio 6's Node.js SSR proxy crashes on zero-a10g
2. **Missing `@spaces.GPU`** — ZeroGPU hardware requires at least one decorated function
3. **Theme/CSS/head lost** — pySpaces calls `demo.launch()` without our custom args (Gradio 6 moved these from `Blocks()` to `launch()`)

All fixed. The app runs on **ZeroGPU** with Gemma 4 E2B (2B params, Apache 2.0, not gated).

---

## Dual-Config Architecture

The codebase supports **both** local development and Space deployment from a single `app.py`:

| Environment | Launch Trigger | Theme Injection | ZeroGPU |
|-------------|----------------|-----------------|---------|
| **Local dev** | `if __name__ == "__main__": demo.launch(...)` | Explicit args + monkey-patch defaults | `@spaces.GPU` no-op |
| **HF Space** | pySpaces imports module → calls `demo.launch()` | Monkey-patch `setdefault()` fills THEME/CSS/VP_HEAD/ssr_mode | `@spaces.GPU` wraps function |

**Key mechanisms:**
- `demo = build()` at module level — pySpaces finds it
- `if __name__ == "__main__":` guarded — only runs locally
- `@spaces.GPU` decorator no-ops when `Config.zero_gpu=False` (local)
- `_patched_launch` uses `kwargs.setdefault()` — respects explicit local args, fills defaults on Space

---

## Space Variables (set via `hf spaces variables`)

| Variable | Value | Purpose |
|----------|-------|---------|
| `GRADIO_SSR_MODE` | `False` | Disables SSR to prevent Node.js crash |
| `CHIEF_ENGINEER_BACKEND` | `zerogpu` | Enables live inference path |
| `CHIEF_ENGINEER_HF_MODEL` | `google/gemma-4-E2B-it` | Model for ZeroGPU inference |

---

## Requirements Strategy

HF Spaces builds mount **only `requirements.txt`** to `/tmp/requirements.txt`. The `-r requirements-zerogpu.txt` pattern fails because the included file isn't mounted.

**Solution:** ZeroGPU deps are **inlined** in `requirements.txt`:

```txt
# Core deps
gradio>=6.17,<7
ollama>=0.4
pydantic>=2.7
trimesh>=4.4
shapely>=2.0

# ZeroGPU deps (inlined — build mounts only requirements.txt)
spaces>=0.30          # @spaces.GPU decorator
torch>=2.4
transformers>=4.49    # Gemma 3/4 family
accelerate>=0.34
```

---

## Code Changes in `app.py`

### 1. Module-level `demo` for pySpaces
```python
def build() -> gr.Blocks:
    with gr.Blocks(title="The Chief Engineer") as demo:
        # ... build UI ...
    return demo

demo = build()  # Module level — pySpaces finds this
```

### 2. `@spaces.GPU` on inference function
```python
import spaces

@spaces.GPU
def get_recommendation(part, material, description, temp, humidity, bed_position):
    # Heavy inference — GPU allocated on call via ZeroGPU
    ...
```

`import spaces` is wrapped in a `try/except` shim in `app.py`: when the package
is absent (local base env / offline), `@spaces.GPU` no-ops and returns the function
unchanged. On the Space, HF provides `spaces` and the real decorator allocates the GPU.

### 3. Monkey-patch `demo.launch` for theme/CSS/head
```python
# After demo = build()
_original_launch = demo.launch

def _patched_launch(**kwargs):
    kwargs.setdefault("theme", THEME)
    kwargs.setdefault("css", CSS)
    kwargs.setdefault("head", VP_HEAD)
    kwargs.setdefault("ssr_mode", False)
    return _original_launch(**kwargs)

demo.launch = _patched_launch
```

- **Local:** `__main__` calls `demo.launch(ssr_mode=False, server_name="0.0.0.0", ...)` → explicit args win
- **Space:** pySpaces calls `demo.launch()` → `setdefault()` injects THEME/CSS/VP_HEAD/ssr_mode

### 4. Guarded `__main__` for local dev only
```python
if __name__ == "__main__":
    print(f"[chief-engineer] {llm.backend_status()} | seeded {_loaded} lessons this run")
    demo.launch(ssr_mode=False, server_name="0.0.0.0", server_port=7860, share=False)
```

Runs locally; skipped on Space (pySpaces imports module, `__name__ != "__main__"`).

---

## Build & Deploy Commands

```bash
# From chief-engineer/
hf upload build-small-hackathon/microfactory-lab ./app.py app.py --repo-type space
hf upload build-small-hackathon/microfactory-lab ./requirements.txt requirements.txt --repo-type space

# Set variables (triggers rebuild)
hf spaces variables add build-small-hackathon/microfactory-lab \
  -e GRADIO_SSR_MODE=False \
  -e CHIEF_ENGINEER_BACKEND=zerogpu \
  -e CHIEF_ENGINEER_HF_MODEL=google/gemma-4-E2B-it

# Factory reboot if needed
hf spaces restart build-small-hackathon/microfactory-lab --factory-reboot
```

---

## Local Development

```bash
# In chief-engineer/
make setup      # uv sync + generate assets
ollama serve &  # For live Gemma (optional; fallback works offline)
make run        # uv run python app.py → http://localhost:7860
```

- Full Astrometrics theme applied via monkey-patch defaults
- Falls back to deterministic advisor if Ollama unavailable
- All core tests pass offline: `uv run python test_core.py`

---

## Pre-flight / Verification

```bash
# Core tests (offline, fast)
uv run python test_core.py

# Preflight (needs Ollama for live path)
uv run python -m scripts.preflight

# Space logs
hf spaces logs build-small-hackathon/microfactory-lab --tail 30
hf spaces logs build-small-hackathon/microfactory-lab --build --tail 30
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `RUNTIME_ERROR` + "No @spaces.GPU function detected" | Missing GPU decorator on zero-a10g | Add `@spaces.GPU` to at least one function |
| SSR crash ("Stopping Node.js server...") | Gradio 6 SSR incompatible | Set `GRADIO_SSR_MODE=False` + `ssr_mode=False` |
| Theme/CSS missing on Space | pySpaces calls `launch()` without args | Monkey-patch `demo.launch` with `setdefault()` |
| Build fails: "No such file: requirements-zerogpu.txt" | `-r` not mounted | Inline deps in `requirements.txt` |
| 503 on zero-a10g, works on cpu-basic | Hardware-specific SSR/GPU issue | Apply SSR fix + `@spaces.GPU` |
| "ModuleNotFoundError: spaces" locally | ZeroGPU package not installed | None needed — `app.py` shims `spaces` to a no-op when absent. Install the real path only to test ZeroGPU locally: `uv sync --extra zerogpu`. |

---

## Model Details

- **Model:** `google/gemma-4-E2B-it` (Gemma 4, Efficient 2B, instruction-tuned)
- **Parameters:** ~2 billion (E2B = Efficient 2B)
- **License:** Apache 2.0 — **not gated**, no `HF_TOKEN` needed
- **Architecture:** Dense, multimodal (text + image), 128K context
- **Endpoint:** Loaded on first `analyze` call via ZeroGPU

---

## File Tree (Space Root)

```
build-small-hackathon/microfactory-lab/
├── app.py                    # Entry point (demo = build())
├── README.md                 # Space metadata (sdk: gradio, sdk_version: 6.17.3)
├── requirements.txt          # All deps inlined
├── assets/                   # .glb meshes (benchy, bridge, cube, overhang, vase)
├── core/                     # Core library (llm, ledger, spine, widgets, viewer, etc.)
├── learn/                    # Policy learning loop
├── ingest/                   # Config distillation (Klipper/Prusa/Marlin)
├── sim/                      # Virtual printer + outcome simulator
├── scripts/                  # Helpers (preflight, bench, demo, capture)
├── data/                     # seed_lessons.jsonl (gitignored: lessons.jsonl, policy.json)
└── test_core.py              # Offline core tests
```

---

## Key Files for Future Maintenance

| File | Purpose |
|------|---------|
| `app.py` | Space entry point + local launch |
| `core/llm.py` | Backend abstraction (Ollama / ZeroGPU / fallback) |
| `core/llm_zerogpu.py` | ZeroGPU transformers path |
| `core/chief_engineer.py` | Brain: precedent eval + settings proposal |
| `core/spine.py` | Deterministic veto (material bounds) |
| `learn/policy.py` | Learned parametric policy (env-bucketed) |
| `core/theme.py` | Astrometrics THEME + CSS + VP_HEAD |
| `scripts/preflight.py` | GO/NO-GO gate for releases |

---

## Next Steps / Frontiers

- [ ] Weight-level fine-tuning on accumulated ledger (named "Well-Tuned" — currently not built)
- [ ] Real distributed multi-node execution (currently single Space)
- [ ] Physical interfaces: g-code streaming, env sensors, camera defect CV
- [ ] Larger Gemma variants (E4B, 26B A4B, 31B) on larger GPUs

---

*Last updated: 2026-06-11 — Space live on zero-a10g with ZeroGPU Gemma 4 E2B*