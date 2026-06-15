# Claude Code Build Prompt — Chief Engineer

Run this in Claude Code from inside the new `chief-engineer/` project folder. It scaffolds the **core loop plus an interactive 3D preview and a node/swarm panel** — but deliberately as a faithful visualization, not a distributed-systems rebuild. Hold the doctrine in `01-OPERATING-PRINCIPLES.md`: clever proof of concept that works; a component nobody judges should never cost more than a judged one.

> **Read first:** `00-MASTER.md`, `02-ARCHITECTURE.md`, and `pattern-review.md`. They are the source of truth. When in doubt, choose the simpler thing.

---

## Paste into Claude Code

You are scaffolding a Gradio app called **Chief Engineer** for the Hugging Face Build Small hackathon. Read `00-MASTER.md`, `02-ARCHITECTURE.md`, and `pattern-review.md` first — they are the source of truth. Build the core loop plus the two visual elements described. Keep it a clever, working proof of concept — not production. Local-only, no cloud APIs.

**The thesis the app must demonstrate:** a small local model that has accumulated expert 3D-printing knowledge across prior jobs and applies it *proactively* to a new job. Given a print task, the system finds similar prior jobs and aspects, and the Chief Engineer EVALUATES what transfers — applying, adapting, or setting aside prior experience, and recognizing genuinely novel situations. The proactive learning is the JUDGMENT, not a forced citation.

**Stack:** Python, Gradio, Ollama (local Gemma GGUF), Pydantic, trimesh (light use only). Minimal dependencies.

### Core modules

1. `models.py` — Pydantic: `Job` (geometry_type, material, description, mesh_path optional), `Environment` (temp, humidity), `PrintSettings` (nozzle_temp, bed_temp, retraction_mm, fan_pct, first_layer_fan_pct), `RiskRegion` (location, risk, why, optional coords/hint for annotation), `LessonEntry` (exact schema in 02-ARCHITECTURE.md, incl. source: seed|earned).

2. `ledger.py` — `LedgerManager` over `data/lessons.jsonl`. Retrieval: filter exact `material` AND `geometry_type`, rank by Euclidean distance on NORMALIZED [temp, humidity] (temp 15-35C, humidity 20-80% → 0-1), return top 2-3. No embeddings.

3. `prompts.py` — Chief Engineer persona (experienced print-shop master; terse, physical) + `build_system_prompt(job, env, retrieved_jobs)`. CRITICAL: the prompt presents retrieved prior jobs as context and instructs the model to *evaluate applicability* — "here are similar past jobs; assess what transfers to THIS job, what doesn't, and why. If nothing closely applies, say so and reason from material properties." Do NOT instruct it to always cite a lesson.

4. `chief_engineer.py` — `advise(job, env, retrieved_jobs)`: build prompt, call Ollama (model from env var, small Gemma GGUF default), "Respond ONLY with valid JSON" → settings + risk regions + reasoning. Parse to Pydantic; fall back to conservative defaults if parsing fails (never crash the demo). The reasoning should reflect the model's EVALUATION of prior jobs — naturally citing when relevant, naturally noting "no close precedent" when not. That discrimination is the demo's point.

5. `spine.py` — `SpineValidator.check(settings, material)`: clamp/reject vs. hardcoded bounds (PLA nozzle 190-220C, PETG 220-245C; sane bed/retraction/fan). Return clamped settings + vetoes. LLM proposes, this decides.

6. `reflect.py` — `reflect_on_job(job, env, settings, outcome)`: one Ollama call distilling the result into a one-sentence lesson → `LessonEntry` (source="earned") appended to ledger. Outcome is passed IN from a manual button. The model NEVER judges its own outcome.

7. `seed_lessons.py` — load `data/seed_lessons.jsonl` into the ledger on first run if empty. (File is provided.)

### 3D preview (interactive + annotations — NOT static, NOT a geometry engine)

8. `viewer.py` + integration in `app.py`:
   - Use Gradio's native `gr.Model3D` to display an uploaded/selected mesh — orbit/zoom/pan come free.
   - Annotate predicted risk regions. Keep trimesh use MINIMAL: load the mesh, optionally compute face normals to locate the steepest overhang so an annotation anchors to something real. Render risk markers as simple overlays/highlighted points/labels at the model's reported regions. Do not build slicing or simulation.
   - If precise mesh annotation proves fiddly, fall back to labeled risk callouts displayed beside the model — but keep the model interactive.

### G-code readout (real-ish if easy, else canned)

9. Show a short G-code snippet whose header lines (temperature, retraction, fan) are populated from the actual `PrintSettings` the model proposed — so the readout visibly ties to the recommendation. If even that adds friction, use a canned snippet. Explicitly not load-bearing; spend no real time here.

### Node / swarm view (faithful visualization of the lab mesh — NOT a distributed system)

10. `nodes.py` + a second Gradio tab/panel. Mirror the microfactory-lab architecture (see pattern-review.md and the lab's zellij-layout.kdl): a **Chief Engineer hub** coordinating capability-typed nodes — **CNC Mill, Laser Cutter, 3D Print, Sinter Press, Metal 3D Print, Hub Router**. Render each as a status card: capability, state (🟢 online / working / idle), current job, environment reading.
    - **Only the 3D Print node executes real work** (the core loop above). The other five render as state-driven cards showing the mesh context — available capacity in the network. This is truthful (same architecture, one node executing, others shown as the network) without reimplementing FileBridge IPC, pi-link, or six live processes. DO NOT rebuild the distributed/IPC layer.
    - Include the live ledger panel here: lessons accumulating, seed vs earned tagged. This is where "knowledge is compounding" becomes visible.

### app.py wiring

- View 1 — Chief Engineer cockpit: inputs (geometry_type, material, description, temp slider, humidity slider, optional mesh upload) → "Get Recommendation" → retrieve prior jobs → advise → Spine check → display proposed settings, the interactive 3D model with risk annotations, the model's evaluation/reasoning, and the G-code readout. Then "Record Outcome" buttons (Printed clean / Sagged / Stringing) → reflect_on_job → ledger grows.
- View 2 — Node/swarm mesh + live ledger (module 10).

### Constraints

- Runnable with `python app.py` + `ollama serve`. README with exact steps.
- Permissive licenses only. NO OrcaSlicer/PrusaSlicer/AGPL code.
- Legibility of the model's proactive evaluation over polish.
- After scaffolding, run end-to-end with a couple of test jobs. Confirm: retrieval returns relevant prior jobs; the reasoning shows real evaluation (applies precedent on a match, says "no close precedent" on a novel job); the Spine clamps an out-of-range proposal; recording an outcome appends an earned lesson; the 3D model is interactive with at least one risk annotation; the node mesh renders. Report what worked and what you'd fix.

Build to a working demo of this scope. Do not add real multi-node execution, slicing, or fine-tuning — those are explicitly out.
