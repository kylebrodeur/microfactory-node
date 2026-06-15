# 02 — Architecture

How the Chief Engineer is built. Python/Gradio/Ollama, reusing the Microfactory lab's *patterns* (not its TypeScript). Confirmed `file:function` references are from the pattern review (`pattern-review.md`).

---

## Stack

- **Python + Gradio** — the app and the demo surface. Hosted as a Hugging Face Space.
- **Ollama (local)** — serves Gemma. Fully local, no cloud APIs (earns Off the Grid + Llama Champion).
- **Pydantic** — strict types for model I/O.
- **trimesh (light)** — mesh load + overhang location for annotations. Not a geometry engine.
- **PySLM (optional)** — slicing/overhang analysis + G-code readout, if time allows.

**Real calls, not mocks.** The Kaggle build leaned on a `DemoLLMProvider` mock; here the model calls are real and the UI surfaces which model is running. (Per your runbook note: "we need to know clearly when mocks vs real and what models are used.")

---

## Model

| Tier | Tag | Notes |
|---|---|---|
| Primary (local) | `gemma4:e4b` | 9.6GB quantized, = `gemma4:latest`. Pin the explicit tag. |
| Faster (local) | `gemma4:e2b` | Use if `e4b` CPU latency on the Space is too slow for a responsive demo. |

**`gemma4:4b` does not exist** — a stale tag that broke the Kaggle build. Never use it. Measure latency on the actual Space hardware pre-window; pick the tag that keeps the demo snappy. Optional tiering (your runbook instinct): Chief Engineer on `e4b`, nodes on `e2b` — but keep it all-local for the Off-the-Grid badge.

---

## Patterns carried from the lab (reimplement in Python)

| Concept (lab source) | Python module | Notes |
|---|---|---|
| Agent structure (`hubAgent.ts`) | `chief_engineer.py` | Format system prompt → real Ollama call → parse Pydantic. Keep "Respond ONLY with valid JSON" + conservative fallback on parse failure (never crash the demo). Leave the MessageBus, tick loops, LLMProvider abstraction. |
| Brain/Spine veto (`nodeAgent.ts` `canDoJob()`, 15W breaker) | `spine.py` | `SpineValidator` clamps/rejects settings vs. material bounds. LLM proposes, code decides. Leave power/Joule tracking. |
| Ledger (`pi-qmd-ledger` `append_ledger`) | `ledger.py` | Append-only `data/lessons.jsonl`. **Use it for real** — not simulated. Leave qmd embeddings/vector search. |
| Reflection loop (`reviewOutcome()`, lab Session 17) | `reflect.py` | Post-job `askLLM()` distills outcome → structured lesson. **This is the proven precedent.** Re-key it from routing-confidence to environment + geometry. Leave bus federation and confidence-float math. |
| HITL gate (`shouldTriggerHITL()`, conf<0.75 / value>500) | in `app.py` | A Gradio state flag + "Confirm & Print" button. Leave Promise maps/timeouts/bus handlers. |
| Context injection (`hubAgent.ts` templates) | `prompts.py` | `build_system_prompt()` = persona + job/env + retrieved prior jobs as a "Historical Precedent" block. |
| Domain types (`core/src/types.ts`) | `models.py` | Pydantic: `Job`, `Environment`, `PrintSettings`, `RiskRegion`, `LessonEntry`. Leave routing/economic/energy/tick types. |

---

## The compounding loop

```
Job (text + optional mesh) + Environment (temp, humidity)
        │
        ▼
  retrieve prior jobs   ──►  exact match material + geometry_type,
  (ledger.py)                rank by normalized [temp,humidity] distance, top 2–3
        │
        ▼
  Chief Engineer        ──►  EVALUATES what transfers (apply / adapt / set aside /
  (chief_engineer.py)        "no close precedent"). Proposes settings + risk regions.
        │
        ▼
  Spine validates       ──►  clamp/reject vs material bounds
  (spine.py)
        │
        ▼
  HITL gate (if risky)  ──►  "Confirm & Print"
        │
        ▼
  manual outcome button ──►  Printed clean / Sagged / Stringing  (model never self-judges)
        │
        ▼
  reflect_on_job        ──►  distill an env-keyed LessonEntry (source="earned"),
  (reflect.py)               append to ledger → next job is better-informed
```

The proactive learning is the **evaluation**, not a forced citation. The demo's load-bearing moment is the model saying *why* it's adjusting — citing a prior job when one fits, or naming the situation novel when none does.

---

## Lesson schema

```python
class LessonEntry(BaseModel):
    job_id: str
    material: str            # "PLA", "PETG"
    geometry_type: str       # "overhang", "bridge", "vase"  — also a retrieval key
    env_temp: float
    env_humidity: float
    outcome: str             # "success", "failed_sag", "failed_stringing"
    lesson: str              # compressed human-readable reflection
    source: str              # "seed" | "earned"             — honest provenance
    timestamp: str
```

Resist adding fields. Add one only when a retrieval query or a demo moment needs it. 12 seed lessons are in `seed_lessons.jsonl`.

---

## The two-view Gradio app

**View 1 — Chief Engineer cockpit.** Inputs (geometry_type, material, description, temp slider, humidity slider, optional mesh upload) → recommendation. Shows: the interactive 3D model with risk annotations, the model's evaluation/reasoning, proposed settings, a G-code readout, and the Confirm/Record-Outcome controls. This is where the load-bearing moment happens.

**View 2 — Node/swarm mesh + live ledger.** Mirror the lab's mesh (`zellij-layout.kdl`): Chief Engineer hub + CNC Mill, Laser Cutter, 3D Print, Sinter Press, Metal 3D Print, Hub Router, each a status card. **Only the 3D Print node executes real work** (the core loop); the others render as mesh context / available capacity. The live ledger panel (lessons accumulating, seed vs earned) lives here — this is where "knowledge is compounding" is visible. Do NOT rebuild FileBridge IPC / pi-link / live processes — that's the Kaggle failure surface and none of it is judged.

This honors your runbook push for "one level up — at least one node genuinely executes, not just coordination sim," without dragging a distributed system into a 10-day build.

---

## 3D preview

Native `gr.Model3D` gives orbit/zoom/pan free. On top: model-driven risk **annotations** — markers/labels at the regions the Chief Engineer flags, anchored by minimal trimesh (load mesh, face normals to find the steepest overhang so a marker lands somewhere real). If precise mesh annotation gets fiddly, fall back to labeled risk callouts beside the model — but keep the model interactive. No slicing, no simulation.

## G-code readout

A short snippet whose temperature/retraction/fan lines are populated from the actual proposed `PrintSettings` — real-ish, tied to the recommendation. Canned fallback if it adds friction. Not load-bearing.

---

## Honest-claims discipline

Borrowed from the lab's architecture doc: maintain a table of what the code actually does vs. what's named as future work, and let the writeup claim only the former. The lab listed physics/Decision-Transformers/FECN as "designed, not implemented" and was honest about it — do the same here. What's real: retrieval-based compounding, environment-keyed lessons, the Brain/Spine veto, proactive geometric risk flags. What's named-as-frontier: weight-level fine-tuning, real multi-node execution, physics simulation.

## License landmine

OrcaSlicer and PrusaSlicer are **AGPL-3.0**. Bundling or linking them — even behind the Space's web server — forces your whole app under AGPL and undermines clean sharing. Use trimesh / PySLM / manifold3d / pyclipr only. Judges can read the repo.
