# 03 — Execution Plan

Pre-window prep + day-by-day for June 5–15. Front-load the end-to-end path; the back half is hardening. Holds the five rules from `01-OPERATING-PRINCIPLES.md`.

---

## Pre-window (now – June 4): de-risk the unknowns

- ✅ **Register** for the hackathon (done).
- ☐ **Pull the model** you'll ship (`gemma4:e4b`, or `e2b`). Confirm it runs under Ollama and returns clean structured JSON (settings + risk list) from a steering system prompt. **Measure latency on the Space's CPU** — if a response is 40s, pick a smaller quant now, not on June 13.
- ☐ **Deploy a trivial Gradio Space** (one textbox, one `gr.Model3D` static cube) to prove the hosting path end-to-end. Highest-value pre-window task — it has no bugs until the day you need it.
- ☐ **Decide sensors:** simulated temp/humidity sliders (default, lowest risk) vs. a real DHT22 (removable upgrade). The compounding thesis demonstrates identically either way.
- ☐ **Seed lessons** are written (`seed_lessons.jsonl`, 12 entries) — load them on first run.

---

## Weekend 1 — June 5–8: the compounding loop, end to end

**Goal by end of Day 3: a judge could watch one full loop and see knowledge compound. Ugly is fine.**

- **Day 1 (Jun 5):** Core loop skeleton. Gradio two-view shell. Job (text) + env → `chief_engineer.py` (real Ollama call, steering prompt) → structured settings + risk list → render in cockpit. No memory yet. Prove input→model→output renders.
- **Day 2 (Jun 6):** Ledger + reflection. On manual outcome, `reflect_on_job()` distills an env-keyed `LessonEntry` (JSONL append). Build retrieval (material + geometry exact-match, normalized env-distance, top 2–3). Inject retrieved jobs into the system prompt as precedent. `SpineValidator` clamps out-of-bounds settings.
- **Day 3 (Jun 7):** Make compounding LEGIBLE. The cockpit must show the model's *evaluation* of prior jobs — applies precedent on a match, says "no close precedent" on a novel job. Wire interactive `gr.Model3D` with at least one model-driven risk annotation. End-to-end happy path stands. **Tag this commit — fallback submittable.**
- **Day 4 (Jun 8):** Harden the happy path. Seed the ledger. Run 4–5 scripted jobs across varying simulated environments; confirm recommendations visibly shift and the evaluation reads clearly. Fix the bugs this surfaces.

---

## Mid-week — June 9–11: integration test, then layers

- **Day 5 (Jun 9) — RECORD.** Record a scrappy full demo today, rough as it is. This is your integration test: narrating a full run exposes every demo-path bug while there's still a week to fix them. **This is the step Kaggle never reached.**
- **Day 6 (Jun 10):** Fix what the recording exposed. Then build View 2 — the node/swarm mesh aligned to the lab + the live ledger panel (one real node, others as context). Refine 3D annotations. Slot in the G-code readout (real-ish or canned).
- **Day 7 (Jun 11) — SUBMITTABLE.** Write the ~1,500-word writeup (`writeup/01-SUBMISSION.md`) and the social post. End of day: complete submittable package — Space + video + writeup + social post. Everything after is polish on a shippable artifact.

---

## Weekend 2 — June 12–15: harden, polish, submit

- **Day 8 (Jun 12):** Re-record the demo properly now the app is solid. Tighten the load-bearing moment until it's unmistakable. Capture social-post assets. (You produce video professionally — this is your home turf.)
- **Day 9 (Jun 13):** Polish. Off-Brand custom-UI badge if the core is rock-solid (push past default Gradio — the LCARS/Astrometrics aesthetic you like is a natural fit). Write Field Notes (badge + book material). Post the ledger/agent trace to the Hub (Sharing is Caring badge).
- **Day 10 (Jun 14):** Freeze features. Full dry run on the actual Space hardware. Fix only what's broken. **Submit.** Add nothing.
- **Jun 15 (deadline):** Buffer. Final edits if needed. Otherwise done early, by design.

---

## Badges

"Falls out" = free given decisions already made; all six can apply.

| Badge | Status | Effort |
|---|---|---|
| Off the Grid (local-first) | Free — Ollama/Gemma local, no cloud | None |
| Llama Champion (llama.cpp) | Free — Ollama runs on llama.cpp | None |
| Sharing is Caring (open trace) | Near-free — post the ledger/lesson trace to the Hub | Low (Day 13) |
| Field Notes (blog/report) | Near-free — doubles as book material | Low (Day 13) |
| Off-Brand (custom UI) | Reach — only if core is rock-solid; LCARS aesthetic | Medium |
| Well-Tuned (fine-tuned model) | Frontier — name as future work, do NOT attempt in-window | Cut |

**Well-Tuned / fine-tuning:** the ledger of runs becomes training data post-hackathon (your "run it many times and submit as datasets" instinct + GCP credits). In-window it's the highest-variance path and the Kaggle failure shape. Name it as the frontier; demonstrate compression via retrieval.

---

## Risk register

| Risk | Mitigation |
|---|---|
| CPU inference too slow for a live demo | Measure pre-window; smaller quant; pre-record so latency never blocks judging |
| Compounding isn't legible — looks like a notes app | Day 3 dedicated to making the model's evaluation explicit on screen |
| 3D / node / G-code layers eat the back half | All removable, added only after Day 7 submittable build |
| AGPL contamination from slicer code | trimesh/PySLM only; never Orca/Prusa |
| Scope creep into a real print simulator | Hard rule: heuristic risk analysis, not physics |
| Model judging its own outcome | Manual outcome button only |
| Euclidean distance dominated by humidity scale | Normalize temp and humidity axes before distance |
| Last-mile demo bugs (the Kaggle ending) | Record-early Day 5; submittable Day 7; freeze Day 14 |
