---
title: "Microfactory Node: 3D Printer"
emoji: 🖨️
colorFrom: gray
colorTo: yellow
sdk: gradio
sdk_version: 6.17.3
python_version: "3.11"
app_file: app.py
pinned: false
license: mit
short_description: Local Gemma that predicts 3D-print failures before they run
tags:
  - build-small-hackathon
  - backyard-ai
  - off-the-grid
  - llama-champion
  - sharing-is-caring
  - field-notes
  - off-brand
  - tiny-titan
  - well-tuned
  - track:backyard
  - sponsor:modal
  - achievement:offgrid
  - achievement:welltuned
  - achievement:offbrand
  - achievement:llama
  - achievement:sharing
  - achievement:fieldnotes
---

# Microfactory Node: 3D Printer

**Build Small hackathon · Backyard AI track.** A small local **Gemma** model that has accumulated
expert 3D-printing knowledge across prior jobs and applies it **proactively** to a new one.
Knowledge **compounds**: job N+1 is better-informed than job N. The proactive part is the
*judgment*: the model evaluates what prior jobs transfer to this one, applies precedent when it
fits, and says *"no close precedent"* when it doesn't.

## The Story

My grandfather had a shop. He was an electrical engineer by training — taught EE labs for twelve years, then spent a career as a communications engineer for the City of Beaumont. At home he was a tinkerer: a home RadioShack with a machine shop attached. He spent a lifetime accumulating skill that lived in his hands — the kind you can't quite write down. He was the one who built the thing and the one who inspected it, both voices in the same patient person. Then Alzheimer's took him. The shop was sold, the tools dispersed, and all of that knowledge just… went.

The Chief Engineer is my attempt at the opposite of that: a small AI that runs on my own machine and learns the craft of 3D printing the way a shop veteran would, job by job, remembering what worked in which conditions, and tells me where a print will fail *before* it runs. The judged moment is simple: it reads the room, recalls the closest prior jobs, and either applies what they teach — *"humidity is higher than the job where this overhang sagged, so I'm raising retraction and adding support"* — or says plainly *"no close precedent"* when nothing close exists. It compresses expert knowledge so it compounds instead of disappearing. Because the knowledge a maker builds over a lifetime shouldn't rent space in someone's cloud — and it shouldn't vanish when the shop closes.

![Microfactory Node: 3D Printer. The Build page, O'Brien reads precedent and flags where the print will fail, before the nozzle moves.](https://huggingface.co/spaces/build-small-hackathon/microfactory-lab/resolve/main/assets/screenshots/hero-build.png)

`Local Gemma via Ollama` · `two agents: O'Brien proposes, La Forge inspects` · `knowledge that compounds` · `honest about what it doesn't know` · `LCARS console skin (Off-Brand badge)`

## The loop

```
Job (geometry + material) + Environment (temp, humidity)
  → retrieve nearest prior jobs   (exact material+geometry, normalized [temp,humidity] distance, top 2-3)
  → Chief Engineer O'Brien EVALUATES what transfers, terse and direct  (Brain)
  → proposes settings + risk regions; "no close precedent" when none exists
  → Spine validates against material bounds, clamps/vetoes unsafe values          (Safety)
  → La Forge (QA Inspector) gives the plan a second opinion; disputes hold the print  (Integrity)
  → HITL "Confirm & Print"  → you print  → you report the real outcome
  → reflect → distill an environment-keyed lesson → ledger grows → next job is smarter
```

**The two-agent integrity model.** Chief Engineer O'Brien proposes settings and flags failure regions. He reads precedent out loud, on screen — "this overhang sagged at lower humidity, so conditions are worse today." La Forge, a separate QA Inspector, reads O'Brien's plan *before* anything prints and writes a second opinion. When La Forge disputes a plan, the print is held until you acknowledge it. O'Brien is the optimist. La Forge is not. My grandfather was both at once. The model never marks its own homework.

**Knowledge compounding.** The outcome comes from outside the model — you click *Printed clean / Sagged / Stringing*, or run the **simulated world** (a deterministic stand-in for the printer + sensors). Either way the honest signal makes the compounding real. Every outcome distills into one durable lesson, keyed to material, geometry, and room condition, and appended to a ledger the node reads from forever after. Job N+1 starts smarter than job N.

**Retrieval plus learned policy.** Two knowledge sources feed every recommendation. *Retrieval-Augmented Generation* (RAG): the model recalls the closest prior jobs (same material + geometry, ranked by [temperature, humidity] distance). A **learned parametric policy** (`learn/policy.py`) stores setting offsets per (material, geometry, *environment-bucket*) and updates from each outcome. Because cells are bucketed, a lesson from one humid PETG bridge **generalizes** to the next humid PETG job, not just an identical one. Retrieval brings back the specific cases. The policy makes the knowledge travel across similar conditions. The **Print** workspace runs the closed loop live on your job: watch quality climb fail→clean over iterations while La Forge grades each run. The one simulated boundary (print outcomes) is spelled out in *What's real vs frontier* below.

## Design Principles: Why Small, Local, and Constrained

A model this size earns trust through constraints, not through scale. The surface is narrow: three or four setting levers. The Spine does safety in plain Python — no deep learning, no black box. La Forge grades the plan before it prints. A deterministic simulator provides ground truth for outcomes. The model grades neither. Take the guardrails away and a small model will confidently hand you a ruined spool. Leave them in and it behaves like a careful shop hand. **Constraints are what make a small model trustworthy in front of a machine.**

It runs offline, on your own hardware, for $0 a month. That is not a deployment footnote — it is the point. The knowledge a maker builds over a lifetime should not rent space in someone's cloud, and it should not vanish when the shop closes. The public Space runs the live model on ZeroGPU so you can see the real reasoning. If the GPU is cold or out of quota the node falls back to the deterministic advisor and the banner says so plainly — the reasoning panel never fakes output.

This is retrieval plus reflection plus a small learned policy, not fine-tuning, and that is deliberate. Fine-tuning would bury the knowledge in the weights where you can't watch it move. Retrieval keeps the memory visible: a lesson gets written after one job and pulled back up to shape the next, in plain sight. For craft you want to preserve and show, visible memory beats invisible memory.

## Run it (fully local, no cloud, no API key)

Runs entirely on your own machine — no cloud, no API key (**Off the Grid**), on Ollama /
llama.cpp (**Llama Champion**), as a Gemma 4 E-class model that's ~4B effective parameters
(**Tiny Titan**). The best local run uses the fine-tuned Chief Engineer model — pull it from the
public Ollama registry or load the same GGUF directly in llama.cpp:

```bash
ollama serve &
ollama pull kylebrodeur/microfactory-node-v3-qat   # fine-tuned Chief Engineer, ~5 GB
make setup                                          # uv sync + generate sample meshes
CHIEF_ENGINEER_MODEL=kylebrodeur/microfactory-node-v3-qat make run
```

Stock Gemma 4B also works if you want the base model without the fine-tuned adapter:

```bash
ollama pull gemma4:e4b        # = gemma4:latest, ~9.6 GB. (gemma4:4b does NOT exist.)
make run                       # uses gemma4:e4b by default
```

Any GGUF on [kylebrodeur/microfactory-node-gguf](https://huggingface.co/kylebrodeur/microfactory-node-gguf)
can also be served with llama.cpp; point Chief Engineer at it with `CHIEF_ENGINEER_MODEL`.

### Run the fine-tuned Chief Engineer locally (Ollama + GGUF on HF Hub)

The LoRA-fine-tuned adapters are pre-merged + quantized and published two ways
so anyone can `ollama run` them with no fine-tune toolchain:

- **[`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur)** — the public Ollama registry (one-command pulls)
- **[`huggingface.co/kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf)** — the canonical GGUF + `template`/`system`/`params` config files

| Variant | `ollama run …` | HF Hub file | Notes |
|---------|----------------|-------------|-------|
| **v3-qat** *(recommended)* | [`kylebrodeur/microfactory-node-v3-qat`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat) | [`microfactory-node-v3-qat.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat.gguf) (5.1 GB, q4_k_m) | QAT-trained, retains more quality after 4-bit quant |
| v3-qat (QAT-native) | [`kylebrodeur/microfactory-node-v3-qat:q4_0`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0) | [`microfactory-node-v3-qat-q4_0.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat-q4_0.gguf) (4.9 GB, q4_0) | Quant Google's QAT was trained for — highest fidelity for the QAT model |
| v2 | [`kylebrodeur/microfactory-node-v2`](https://ollama.com/kylebrodeur/microfactory-node-v2) | [`microfactory-node-v2.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v2.gguf) (5.1 GB, q4_k_m) | Standard E4B fine-tune |
| v1 | [`kylebrodeur/microfactory-node`](https://ollama.com/kylebrodeur/microfactory-node) | [`microfactory-node.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node.gguf) (5.1 GB, q4_k_m) | First fine-tune (historical) |

```bash
# one-liner via the public Ollama registry (recommended)
ollama run kylebrodeur/microfactory-node-v3-qat

# or pull directly from HF — the repo's template/system/params apply automatically
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf

# then point Chief Engineer at it
CHIEF_ENGINEER_MODEL=kylebrodeur/microfactory-node-v3-qat make run
```

For the full pipeline (LoRA → Modal merge → GGUF → HF Hub → ollama.com), the
decisions behind quant choice, and gotchas, see
[`learn/finetune/OLLAMA_PUBLISHING.md`](learn/finetune/OLLAMA_PUBLISHING.md)
and [`learn/finetune/SERVING.md`](learn/finetune/SERVING.md).

Local dev uses [uv](https://docs.astral.sh/uv); the HF Space installs via `requirements.txt`.
**Layout:** `app.py` (Space entrypoint) + `test_core.py` at the root; the core library lives in
`core/`, runnable helpers in `scripts/` (run via `make <target>` or `uv run python -m scripts.<name>`),
and the simulator / learning-loop / ingestion packages in `sim/`, `learn/`, `ingest/`. See
[`docs/RUNBOOK.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/docs/RUNBOOK.md) for the full run-and-test order of operations.

Falls back to a deterministic advisor if Ollama is unreachable, so the demo never crashes; the
UI always shows which model ran.

**Resetting demo state.** `data/lessons.jsonl` is now the **durable knowledge base** (12 seed +
14 ingested lessons, *tracked*, not disposable); the Print loop appends earned/sim lessons to it
at runtime, and `data/policy.json` is the derived learned policy. For a clean curve between demos,
**don't delete the ledger**: restore it to the committed baseline and clear only the derived policy:

```bash
git checkout -- data/lessons.jsonl     # discard this session's runtime lessons, keep seed + ingested
rm -f data/policy.json                 # drop the learned policy (re-derives from the loop)
```

On the **live Space** (no shell), use the **↺ RESET TO BASELINE** button in the **Review** tab:
it clears this session's accumulated runs + learned policy back to the curated baseline.

## Workspaces: the real print workflow

The app has four tabs, left to right — **LOAD → SLICE → PRINT → REVIEW**:

1. **LOAD**. Define and preview the job: quick-load 3DBenchy, generate a primitive, or drop a
   mesh (the engineer *infers* the part class itself, you don't pick it); choose material; the
   simulated **environment** (temp/humidity/plate position on a Creality Ender 3 V2) populates.
   This is also where you load a built model variant via the header switcher (LoRA v3 QAT / v2 /
   base Gemma 4 / Modal).
2. **SLICE**. The pre-flight check, **before it prints**: the slicer / layer-by-layer virtual
   print, the engineer's precedent read + reasoning + predicted failure regions, the Spine-validated
   settings + G-code (terminal readout), and a **second opinion** from a separate QA Inspector.
3. **PRINT**. Run *this* job through the closed loop and watch quality compound fail→clean.
   **THE PLAN** card frames the run — what's being tested, the Engineer's Spine-validated
   settings, and what La Forge expects: the Engineer proposes → the Spine vetoes → a simulated
   world prints → the **Inspector grades each run** → policy + ledger learn. **OVERRIDE PLAN**
   prints against your own settings; simulate one print, or record a real outcome.
4. **REVIEW**. The whole job in one place — a **session record** of the inputs, O'Brien's read,
   La Forge's pre-print second opinion, the simulated run + outcome, and next steps — plus the
   live ledger (seed → earned → sim), the capability mesh, and the Inspector's run verdict.

**The hybrid evaluator (honest by design).** The Engineer, *Chief Engineer O'Brien*, never grades
its own work. The deterministic world (`sim/outcome.py`) produces the ground-truth pass/fail; a
*separate* **QA Inspector** persona, *La Forge* (`core/inspector.py`), reads what O'Brien claimed vs
what actually happened and writes the verdict: a second opinion in **Slice**, a per-print grade in
**Print**, a run verdict in **Review**. Physics plus a skeptical second voice, never the proposer marking its
own homework.

![The Print loop: quality climbs from failure to clean over a few iterations as the ledger learns, with La Forge grading each run.](https://huggingface.co/spaces/build-small-hackathon/microfactory-lab/resolve/main/assets/screenshots/print-loop.png)

## Links

*(Badges earned are marked inline — Off the Grid, Llama Champion, Tiny Titan above; Off-Brand in the console skin; the rest below.)*

- **Live:** [node.microfactory.space](https://node.microfactory.space) · fallback: [build-small-hackathon/microfactory-lab](https://huggingface.co/spaces/build-small-hackathon/microfactory-lab)
- **Book chapter:** [Microfactory Node — 3D Printer (appendix)](packages/book/src/appendix-microfactory-node.md) — frames this hackathon entry as the first concrete node of the larger Microfactory economy
- **Open trace datasets on HF Hub** *(Sharing is Caring)*:
  - **Lesson ledger:** [kylebrodeur/chief-engineer-ledger](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger)
  - **Deliberation traces:** [kylebrodeur/chief-engineer-deliberation](https://huggingface.co/datasets/kylebrodeur/chief-engineer-deliberation)
  - **Field log (live):** [build-small-hackathon/chief-engineer-field-log](https://huggingface.co/datasets/build-small-hackathon/chief-engineer-field-log)
  - **Build activity trace:** [kylebrodeur/chief-engineer-build-activity](https://huggingface.co/datasets/kylebrodeur/chief-engineer-build-activity)
  - **Fine-tune activity trace:** [kylebrodeur/chief-engineer-finetune-activity](https://huggingface.co/datasets/kylebrodeur/chief-engineer-finetune-activity)
- **Build story / field notes** *(Field Notes)*: [`build-small-hackathon/microfactory-lab-field-notes`](https://huggingface.co/datasets/build-small-hackathon/microfactory-lab-field-notes)
- **Demo video:** coming soon (recorded for the submission)
- **Social post:** coming soon
- **Stay in the loop:** an email signup lives at the bottom of the live Space — opt-in only, clear privacy note, no third-party trackers.
- **How to use it (guided tour):** [`docs/RUNBOOK.md` §2](https://github.com/kylebrodeur/microfactory-node/blob/main/docs/RUNBOOK.md#2--use-the-tool-the-guided-tour--also-the-judges-tour)
- **Fine-tune + serving paper trail** *(Well-Tuned)*:
  - **Model cards:** [`LoRA v2`](learn/finetune/MODEL_CARD.md) · [`LoRA v3 QAT`](learn/finetune/MODEL_CARD_QAT.md)
  - **Local run / publish:** [`SERVING.md`](learn/finetune/SERVING.md) · [`OLLAMA_PUBLISHING.md`](learn/finetune/OLLAMA_PUBLISHING.md)
  - **Fine-tune pipeline:** [`learn/finetune/README.md`](learn/finetune/README.md) · [`PIPELINE.md`](learn/finetune/PIPELINE.md) · [`RUNBOOK.md`](learn/finetune/RUNBOOK.md) · [`BUDGET.md`](learn/finetune/BUDGET.md)
  - **Session report + activity trace:** [`SESSION_REPORT.md`](learn/finetune/SESSION_REPORT.md) · [`activity.jsonl`](learn/finetune/activity.jsonl)
  - **Calibration:** [`sim/calibration/CALIBRATION-REPORT.md`](sim/calibration/CALIBRATION-REPORT.md) · [`sim/calibration/README.md`](sim/calibration/README.md)
  - **Ingestion + assets:** [`ingest/README.md`](ingest/README.md) · [`assets/screenshots/README.md`](assets/screenshots/README.md) · [`dist/README.md`](dist/README.md) · [`dist/deliberation/README.md`](dist/deliberation/README.md)
- **Source:** [kylebrodeur/microfactory-node](https://github.com/kylebrodeur/microfactory-node)

## What's real vs frontier (honest claims)

- **Built:** retrieval-based compounding knowledge, environment-keyed lessons, a learned parametric
  policy that generalizes across similar conditions, the closed learning loop, the Brain/Spine veto,
  flags for risky geometry before it prints, fully local Gemma 4 inference, human-reported outcomes,
  knowledge ingestion from slicer/firmware configs, and the two-agent integrity model (proposer +
  inspector, never the model grading itself). The node is tuned end to end — persona/prompt steering,
  the deterministic Spine, the Brain/Inspector split, and a LoRA fine-tune on the ledger (**Well-Tuned**).

- **Simulated (the one boundary):** print outcomes, via a deterministic physics-lite stand-in for the
  printer + sensors (`sim/outcome.py`). The simulator was calibrated against 178 real FDM failure prints.
  Ingestion and parsing of those corpora ran on **Modal** for about five cents of compute, producing
  1,304 material reference facts and 178 cleaned calibration prints. The first pass read 34.2% — the
  parser only looked at G-code headers, so 178 of 260 rows had fan speed defaulting to zero. After
  cleaning that, the score settled at 32.6%: correct on clean successes, blind to moderate failures. The
  gap is structural (the model can't infer true defects without real vision + sensors), not a knob to
  quietly turn. Rather than fake a prettier number, the gap is documented in
  `sim/calibration/CALIBRATION-REPORT.md`. The same rule that keeps the model from grading itself kept us
  from tuning the simulator on bad data.

- **In progress:** a LoRA fine-tune on the accumulated ledger (training on Modal), so the craft lives
  in the weights as well as the memory. The live node stays retrieval-based until a held-out eval
  earns the swap.

- **Frontier (not built):** real distributed multi-node execution, physical interfaces (g-code
  streaming, live environmental sensors, camera-based defect detection).

## Acknowledgements

Built for the Hugging Face **Build Small** hackathon (Backyard AI track). Model: Google **Gemma 4**
E-class (E4B/E2B), run locally via [Ollama](https://ollama.com) / llama.cpp; fine-tuning and corpus
ingestion on [Modal](https://modal.com); UI on [Gradio](https://gradio.app); meshes via
trimesh / PySLM / manifold3d / pyclipr. Storytelling is a judging principle, not a badge — but it is
the reason this exists.

## License

MIT.