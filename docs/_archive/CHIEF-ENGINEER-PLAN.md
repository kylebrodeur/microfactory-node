# The Chief Engineer — Build Small Hackathon Plan

**A Microfactory Capability Replicator · Backyard AI track · Solo build · June 5–15, 2026**

> **Status:** Locked. Pattern review complete (see companion doc). Schema and retrieval decided. Next actions are pre-window execution, not planning.

---

## The one thing this submission must prove

> **The demo's load-bearing moment:**
> *"Humidity is 22 points higher than the last time I printed this kind of overhang — back on Job 3, that combination sagged. So before you print, I'm raising retraction, dropping temp 5°, and adding support here."*

If a judge sees the Chief Engineer say something like that — proactively, before the print, citing a prior job and the current environment — the submission lands. Everything in this plan exists to make that one moment real, legible, and reliable. If a feature doesn't serve that moment, it's cut.

**The thesis:** expert 3D-printing knowledge, compressed into durable environment-keyed lessons, expanded proactively into future jobs by a small local model. Knowledge that *compounds* — job N+1 is better-informed than job N. That is the Microfactory Capability Replicator, demonstrated on the cheapest available physical substrate.

**What it is NOT:** not a print simulator (no melt physics), not a slicer (don't rebuild Orca), not a generic symptom→fix app (those are stateless; this compounds), not an activation-steering research artifact (steering here is versioned system instructions). Every one of those is a scope cliff that ends with a half-built engine and no submission.

---

## Honest framing (from the pattern review)

The pattern review confirmed: **the existing microfactory-lab code does no environment-keyed storage and no proactive prediction. It is a reactive routing engine.** The compounding-knowledge layer is net-new to this build.

This shapes the writeup. Do **not** imply this capability already existed in a mature Microfactory system. The honest framing is stronger: *"the lab proved the agent-coordination patterns (Brain/Spine, ledger, post-job reflection); this hackathon builds the compounding-knowledge layer for the first time."* "I built the novel thing in 10 days" beats "I had it already" — and it sidesteps the overclaiming trap that has shown up in every prior artifact in this project.

> **Note on review completeness:** The pattern review flagged three repos as not-present (`pi-context`, `pi-guideline-loader`, `UACS`). These were dispositioned and the review was **not** rerun: none affects a design decision. `pi-context` is third-party and superseded by the locked `build_system_prompt()` design; `pi-guideline-loader` is a file loader, not an architecture (persona is hardcoded in `prompts.py`); `UACS` is a deliberately abandoned, over-scoped project that serves as an anti-pattern reference, not a pattern source. The load-bearing findings are complete.

---

## Operating doctrine (why Kaggle failed, and the rules that prevent a repeat)

Kaggle didn't fail on strategy or architecture — it failed on the last mile: bugs in the demo path discovered too late, no time to edit. The architecture was "so close." These five rules exist specifically to prevent that ending. They override ambition every time they conflict.

1. **The demo path is the product.** On a Gradio Space there is no "real system behind the demo" — the app IS the demo. Get one end-to-end happy path standing by Day 3, ugly and dumb, then improve inward.
2. **Record early, re-record often.** The demo video is your integration test. Record a scrappy full run by Day 5 (June 9). It will expose the demo-path bugs while you still have a week to fix them — the exact runway you lacked at Kaggle.
3. **Every advanced layer is removable.** trimesh feature extraction, 3D viz, sensors, slicer/G-code readout, fine-tuning — each sits ON the working core and can be ripped out on June 14 without breaking the submission. If a layer can't be made removable, it doesn't go in.
4. **Submit with a multi-day buffer.** Target a complete, submittable build by June 11. June 12–15 is hardening and polish on an already-shippable artifact, not a scramble.
5. **Narrow manufacturing surface, deep memory.** 3–4 setting levers (temp, retraction, cooling, first-layer speed) is enough vocabulary. The depth goes into the compression/expansion memory, not into print-domain breadth. Judges score whether knowledge compounded, not your slicer coverage.

---

## Architecture — reuse concepts, not code

Reimplement the lab's proven patterns cleanly in Python. Do not port the TypeScript. Patterns and `file:function` references below are confirmed from the pattern review of `microfactory-lab` and `pi-qmd-ledger`.

| Concept (lab source) | In this build (Python) | Carry / leave | Risk |
|---|---|---|---|
| Agent structure (`hubAgent.ts`) | `ChiefEngineer` class: format system prompt → call Ollama → parse Pydantic. Keep "Respond ONLY with valid JSON" + fallback defaults | Leave the MessageBus, tick() loops, LLMProvider abstraction | Core |
| Brain/Spine veto (`nodeAgent.ts`, `canDoJob()`, 15W breaker) | `SpineValidator`: clamp/reject settings vs. material bounds (PLA ≤ 230°C). LLM proposes, code decides | Leave power-budget/Joule tracking, capacity loops | Core, low |
| Ledger (`pi-qmd-ledger/tools.ts`, `append_ledger`) | `LedgerManager`: append-only `lessons.jsonl` | Leave qmd embeddings, vector search, gated/autopilot queues | Core |
| Compression/expansion (`hubAgent.ts reviewOutcome()`) | `reflect_on_job()`: post-job LLM reflection → structured lesson. Retrieved lessons injected into next system prompt | Leave network federation broadcast, confidence-float math | **Core — THE thesis** |
| HITL gate (`shouldTriggerHITL()`, conf < 0.75 / value > 500) | Gradio `requires_approval` state flag + "Confirm & Print" button | Leave Promise maps, timeouts, bus handlers | Core, low |
| Context injection (`hubAgent.ts` template literals) | `build_system_prompt()`: persona + job/env + 2–3 matched lessons as "Historical Precedent" block | Leave file-based guideline loading; hardcode in `prompts.py` | Core |
| Domain types (`core/src/types.ts`) | Pydantic: `Job`, `Environment`, `PrintSettings`, `RiskRegion`, `LessonEntry` | Leave routing/economic/energy/tick types | Core |
| Articraft [Vis-Block] | `gr.Model3D` preview + trimesh/PySLM overhang & risk regions | Additive | Removable |
| Environmental sensing | Temp/humidity — simulated slider (default) or real DHT22 | Additive | Removable |

### The two-view Gradio app

- **Chief Engineer cockpit:** the `gr.Model3D` preview with predicted failure regions highlighted, the agent's proactive reasoning (citing prior jobs + environment), the proposed settings, the slicer/G-code readout, and the "Confirm & Print" HITL gate. This is where the load-bearing moment happens.
- **Node / swarm state view:** node status, current environment readings, job flow, and the growing ledger of lessons (seed → earned). This is where "knowledge is accumulating" becomes visible. State visualization, never physics simulation.

### Open-source leverage (permissive licenses only)

- **trimesh (MIT):** mesh load, overhang detection via face normals, wall-thickness/bridge heuristics, primitive generation for risk-region overlays.
- **PySLM (permissive deps):** slicing, hatching, built-in overhang analysis on trimesh v4 — for the slicer/G-code readout if time allows.
- **gr.Model3D (Gradio native):** renders `.glb`/`.obj`/`.stl` with orbit/zoom/wireframe. No custom JS, no language boundary.
- **Ollama + Gemma GGUF:** fully local inference. Earns Off the Grid + Llama Champion by construction.

> **⚠ License landmine — do not trip it**
> OrcaSlicer and PrusaSlicer are **AGPL-3.0**. Bundling or linking them — even behind the Space's web server — forces your entire app under AGPL and undermines clean sharing. Use trimesh / PySLM / manifold3d / pyclipr only. Never import Orca or Prusa code. Judges can and do read the repo.

---

## Locked design decisions (from the pattern review Q&A)

These were open in earlier drafts; they're now decided. Build to these, don't relitigate them.

- **Proactive evaluation, not forced citation:** the system retrieves similar prior jobs and feeds them to the Chief Engineer as context; the model EVALUATES what transfers to the new job — applying, adapting, or setting precedent aside, and recognizing genuinely novel situations ("no close precedent, reasoning from material properties"). The proactive learning being simulated is the judgment, not a citation. The "no close precedent" case is a *stronger* demo beat than a forced citation because it shows discrimination. Do NOT instruct the model to always cite a lesson.
- **Geometry input:** text description drives the core loop; an optional mesh upload drives the 3D preview. Light trimesh use (load mesh, face-normals to locate steepest overhang) anchors annotations to something real — not a geometry engine, not slicing.
- **3D preview:** interactive `gr.Model3D` (orbit/zoom/pan free) with model-driven risk **annotations** — markers/labels at the regions the Chief Engineer flags. A static model is not enough; full trimesh analysis is too much. The middle is: interactive viewer + annotations anchored by minimal trimesh.
- **G-code readout:** show a short snippet whose temp/retraction/fan lines are populated from the actual proposed `PrintSettings`, tying readout to recommendation. If that adds friction, canned snippet. Not load-bearing.
- **Outcome signal:** **manual button only** — you click "Printed clean / Sagged / Stringing." The LLM must NEVER judge its own outcome; that closed loop fabricates success and poisons every downstream lesson. The honest human signal is what makes compounding real, and it reinforces you as the genuine user (Backyard rubric).
- **Retrieval:** exact match on `material` AND `geometry_type`, then rank by Euclidean distance on **normalized** `[temp, humidity]`, take top 2–3. No embeddings, no vector DB. Normalize both env axes so humidity's 0–100 range doesn't swamp temperature.
- **Node/swarm view — align to the lab, visualize don't rebuild:** mirror microfactory-lab's actual mesh (Chief Engineer hub + capability nodes: CNC Mill, Laser Cutter, 3D Print, Sinter Press, Metal 3D Print, Hub Router; ref `zellij-layout.kdl`). Render each as a status card. **Only the 3D Print node executes real work** (the core loop); the others show as mesh context / available capacity. This is truthful — same architecture, one node executing — without reimplementing FileBridge IPC, pi-link, or six live processes. The live ledger panel lives here (lessons accumulating, seed vs earned).
- **Seed lessons:** 12 provided in `seed_lessons.jsonl`, `source: "seed" | "earned"` for honest provenance; retrieved identically to earned lessons; lets the demo show the ledger growing.

### Lesson schema (final)

```python
class LessonEntry(BaseModel):
    job_id: str
    material: str            # "PLA", "PETG"
    geometry_type: str       # "overhang", "bridge", "vase"  -- also a retrieval key
    env_temp: float
    env_humidity: float
    outcome: str             # "success", "failed_sag", "failed_stringing"
    lesson: str              # compressed human-readable reflection
    source: str              # "seed" | "earned"             -- provenance
    timestamp: str
```

Resist adding fields. Add one only when a retrieval query or a demo moment actually needs it (`confidence`, `layer_height`, `print_duration` are scope creep until proven otherwise).

---

## Suggested project layout

For the new `/projects` folder, referencing the other repos as read-only pattern sources:

```
chief-engineer/
├── README.md
├── app.py                    # Gradio entry — two-view app, Space target
├── pyproject.toml            # deps: gradio, ollama, pydantic, trimesh, (pyslm)
├── prompts.py                # static persona + build_system_prompt()
├── chief_engineer.py         # ChiefEngineer: prompt -> Ollama -> Pydantic
├── spine.py                  # SpineValidator: clamp/reject vs material bounds
├── ledger.py                 # LedgerManager: append + retrieve (material+geo+env-dist)
├── reflect.py                # reflect_on_job(): outcome -> LessonEntry
├── models.py                 # Pydantic: Job, Environment, PrintSettings, RiskRegion, LessonEntry
├── geometry.py               # trimesh feature extraction (Day 6, removable)
├── seed_lessons.py           # writes 8-12 seed lessons into data/lessons.jsonl
├── data/
│   └── lessons.jsonl
└── docs/
    ├── pattern-review.md     # the companion digest
    └── plan.md               # this file
```

Reference the source repos (`microfactory-lab`, `pi-qmd-ledger`) read-only for patterns; do not import from them.

---

## The build window — June 5 to 15

Two weekends plus the week between. Front-load the end-to-end path; treat the back half as hardening. Dates assume you registered before June 3 and have Ollama + Gemma pulled and a baseline Gradio Space deploying before June 5.

### Pre-window (now – June 4): de-risk the unknowns

- **Register for the hackathon org before June 3** (hard cutoff).
- Pull the Gemma GGUF you'll ship. Confirm it runs under Ollama and produces clean structured JSON (settings + risk list) from a steering system prompt. **Measure latency on CPU** — if a response is 40s, pick a smaller quant now, not on June 13.
- **Deploy a trivial Gradio Space** (one textbox, one `gr.Model3D` static cube) to prove the Space hosting path end-to-end. Highest-value pre-window task — it's the thing with no bugs until the day you need it.
- Decide sensors: real DHT22 or simulated slider. Default simulated; real hardware is a removable upgrade.
- Write the **8–12 seed lessons** against the final schema (`seed_lessons.py`). Your starting capability corpus and Field Notes raw material.

### Weekend 1 — June 5–8: the compounding loop, end to end

**Goal by end of Day 3 (June 7): a judge could watch one full loop and see knowledge compound. Ugly is fine.**

- **Day 1 (Jun 5):** Core loop skeleton. Gradio two-view shell. Job (text) + env → `ChiefEngineer` (Ollama, steering prompt) → structured settings + risk list → render in cockpit. No memory yet. Prove input→model→output renders.
- **Day 2 (Jun 6):** Ledger + compression. On manual outcome, `reflect_on_job()` distills an env-keyed `LessonEntry` (JSONL append). Build retrieval (material + geometry exact-match, env-distance ranked). Inject top 2–3 lessons into the system prompt. `SpineValidator` clamps out-of-bounds settings.
- **Day 3 (Jun 7):** Make compounding LEGIBLE. The cockpit must show the model's *evaluation* of prior jobs (applies precedent on a match; says "no close precedent" on a novel job). Wire interactive `gr.Model3D` with at least one model-driven risk annotation. End-to-end happy path stands. **Tag this commit — fallback submittable.**
- **Day 4 (Jun 8):** Harden the happy path. Seed the ledger. Run 4–5 scripted jobs under varying simulated environments; confirm recommendations visibly shift and cite history. Fix bugs this surfaces.

### Mid-week — June 9–11: integration test, then layers

- **Day 5 (Jun 9) — RECORD.** Record a scrappy full demo today. This is your integration test: narrating a full run exposes every demo-path bug while you still have days to fix them. The step you didn't get to at Kaggle. Do it now.
- **Day 6 (Jun 10):** Fix what the recording exposed. Then build the node/swarm view (View 2): the capability-node mesh aligned to the lab + the live ledger panel. Faithful visualization, one real node, others as mesh context. Refine 3D annotations if needed. The G-code readout (real-ish or canned) slots in here.
- **Day 7 (Jun 11) — SUBMITTABLE.** Slicer/G-code readout via PySLM (removable). Write the ~1,500-word writeup and social post. End of day: complete submittable package (Space + video + writeup + social post). Everything after is polish on a shippable artifact.

### Weekend 2 — June 12–15: harden, polish, submit

- **Day 8 (Jun 12):** Re-record the demo properly now the app is solid and viz is in. Tighten the load-bearing moment until it's unmistakable. Capture social-post assets.
- **Day 9 (Jun 13):** Polish. Off-Brand custom-UI badge if core is rock-solid. Write Field Notes (badge + book material). Post the ledger/agent trace to the Hub (Sharing is Caring badge).
- **Day 10 (Jun 14):** Freeze features. Full dry run on actual Space hardware (not just local). Fix only what's broken. **Submit.** Add nothing.
- **Jun 15 (deadline):** Buffer. Final edits if needed. Otherwise done early, by design.

---

## Badges — what falls out, what's a reach

"Falls out" = free given decisions already made for other reasons; it doesn't mean a badge doesn't apply. All six can apply. Sorted by *added effort*.

| Badge | Status in this design | Effort |
|---|---|---|
| Off the Grid (local-first) | Free — Ollama/Gemma GGUF, no cloud APIs | None |
| Llama Champion (llama.cpp) | Free — Ollama runs on llama.cpp | None |
| Sharing is Caring (open trace) | Near-free — post the ledger/lesson trace to the Hub | Low (Day 13) |
| Field Notes (blog/report) | Near-free — doubles as book material | Low (Day 13) |
| Off-Brand (custom UI) | Reach — only if core is rock-solid by Day 13 | Medium |
| Well-Tuned (fine-tuned model) | Frontier — name as future work, do NOT attempt in-window | High / cut |

**On Well-Tuned:** weight-level compression (fine-tuning Gemma on accumulated job outcomes) is the truer form of "compressing expert knowledge into the model," and it's your post-hackathon Option B. In-window it's the highest-variance path and mirrors the Kaggle failure surface. Name it as the frontier; demonstrate compression via retrieval. Point your GCP credits at the `lessons.jsonl` this build generates — better training data than anything scraped.

---

## Submission checklist (all mandatory)

- [ ] Gradio app hosted as a Hugging Face Space (under the hackathon org)
- [ ] Demo video — short, showing the load-bearing compounding moment
- [ ] Social-media post
- [ ] Public repo, permissive license, no AGPL slicer code
- [ ] Track selected: Backyard AI (Chapter One)
- [ ] ≤ 32B parameters — Gemma GGUF qualifies with room to spare
- [ ] Optional badges claimed in the README/writeup as applicable

---

## Risk register — the things most likely to end this

| Risk | Mitigation |
|---|---|
| CPU inference too slow for a live demo on the Space | Measure pre-window; pick smaller Gemma quant; pre-record demo so latency never blocks judging |
| Compounding isn't legible — looks like a notes app | Day 3 is dedicated to making "because of Job N + environment" explicit in the UI |
| trimesh / viz / slicer layer eats the back half | All removable, added only after Day 7 submittable build; rip out if they fight |
| AGPL contamination from slicer code | trimesh/PySLM only; never import Orca/Prusa |
| Scope creep into a real print simulator | Hard rule: heuristic risk analysis, not physics. "Simulator" = agent predicts, not melt modeled |
| LLM judging its own print outcome | Manual outcome button only; the model never scores itself |
| Euclidean distance dominated by humidity scale | Normalize temp and humidity axes before distance |
| Last-mile demo bugs (the Kaggle ending) | Record-early-on-Day-5 as integration test; submittable by Day 7; freeze Day 14 |

---

## After June 15

Win, place, or neither, this build produces durable Microfactory assets by design: a working Chief Engineer demonstrating the compression/expansion thesis, a Field Notes writeup that is Chapter-8 raw material, a public agent trace, and a clean Python reference of the Brain/Spine + ledger patterns. The weight-level compression frontier (Well-Tuned / Option B) is the obvious next thread — now with a real `lessons.jsonl` of job outcomes to fine-tune on.

*The submission is a test of the idea, in your words. Built this way, the test produces a result you keep regardless of the hackathon outcome — which is the definition of non-throwaway.*
