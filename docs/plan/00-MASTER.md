# 00 — Master: Current State & Locked Decisions

**The Chief Engineer · Hugging Face Build Small · June 5–15, 2026 · Solo · Backyard AI track**

The single source of truth for where the project stands and what's been decided. Read this first; the other docs elaborate.

---

## The product, in one paragraph

The **Chief Engineer** is a small local model that has accumulated expert 3D-printing knowledge across prior jobs and applies it *proactively* to a new job. Given a print task and the current environment (temperature, humidity), the system retrieves similar prior jobs and the model **evaluates what transfers** — applying precedent when it fits, adapting it, or recognizing a genuinely novel situation — then proposes settings and flags where the print will fail before it runs. Knowledge **compounds**: job N+1 is better-informed than job N. This is the Microfactory *Capability Replicator*, demonstrated on 3D printing as the cheapest physical substrate. You are the user; the agents are copilots.

---

## Locked decisions

| Decision | Choice |
|---|---|
| Track | Backyard AI (Chapter One) — you are the real user |
| Stack | Python + Gradio + Ollama + Pydantic + light trimesh. No TypeScript port. |
| Model | Gemma via Ollama, fully local. `gemma4:e4b` (9.6GB, = `gemma4:latest`); `gemma4:e2b` if CPU latency demands. **`gemma4:4b` does not exist** — never use that tag. |
| Steering | System-instruction steering (versioned prompts), not activation steering |
| Compression | Semantic via retrieval — exact match on `material` AND `geometry_type`, ranked by Euclidean distance on **normalized** `[temp, humidity]`, top 2–3. No embeddings/vector DB. |
| Proactivity | The model **evaluates** retrieved jobs for applicability — it is NOT forced to cite. "No close precedent, reasoning from material properties" is a valid (and strong) output. |
| Geometry input | Text for the core loop; optional mesh upload drives the 3D preview; light trimesh feature extraction is a removable upgrade |
| 3D preview | Interactive `gr.Model3D` (orbit/zoom free) + model-driven risk annotations anchored by minimal trimesh. Not static, not a geometry engine. |
| Outcome signal | **Manual button only** (Printed clean / Sagged / Stringing). The model NEVER judges its own outcome. |
| Node/swarm view | Visualize the lab mesh (Chief Engineer hub + CNC, Laser, 3D Print, Sinter, Metal 3D, Hub Router). **One real node executes** (3D Print); others render as mesh context. Do NOT rebuild IPC/pi-link/distributed system. |
| Mocks | **Real Ollama calls, not mocks.** The UI surfaces which model is running. |
| Fine-tuning | **Not in-window.** Named as frontier. The ledger of runs becomes training data post-hackathon (GCP credits). |
| Licenses | Permissive only. trimesh/PySLM/manifold3d/pyclipr. **Never** OrcaSlicer/PrusaSlicer (AGPL). |

---

## Honest framing (important for the writeup)

The Microfactory lab's existing code is a **reactive routing engine** — it does not do environment-keyed storage or proactive print prediction. But the *mechanism* the Chief Engineer needs is already proven there: `GemmaAgent.reviewOutcome()` (lab Session 17) is a post-job `askLLM()` reflection that emits a lesson and federates it. The lab's own note: *"self-assessment is structurally the same as routing — just another askLLM() call with a different prompt, no new infrastructure."*

So the honest claim is: **the reflection loop is a proven pattern; re-keying it to environment + geometry for proactive print-failure prediction is what's new for this build.** "I re-keyed a proven loop and shipped the compounding-knowledge layer in 10 days" is true, specific, and stronger than implying it pre-existed.

---

## What's left

- **Pre-window:** deploy trivial Gradio Space (static `gr.Model3D` cube) + measure model latency on Space hardware. Register ✅.
- **Build:** core loop (see `04-BUILD-PROMPT.md`), then the day-by-day in `03-EXECUTION-PLAN.md`.
- **Submit:** writeup (`writeup/01-SUBMISSION.md`), video (`writeup/02-VIDEO.md`), public repo, live Space.

## Parked (post-hackathon)

Weight-level fine-tuning (Well-Tuned badge / Option B); the Android e-waste edge node (BONUS); full pi-ecosystem integration; the book rewrite. None are in the June 5–15 scope.

---

## Doc index

**Plan:** `01-OPERATING-PRINCIPLES` (how to decide what to build) · `02-ARCHITECTURE` (how it's built) · `03-EXECUTION-PLAN` (when) · `04-BUILD-PROMPT` (start here to build) · `pattern-review.md` + `seed_lessons.jsonl` (references).
**Write-up:** `00-STORY` (the narrative) · `01-SUBMISSION` (the writeup) · `02-VIDEO` (the video).
