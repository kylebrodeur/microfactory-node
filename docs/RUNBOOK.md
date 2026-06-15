# RUNBOOK — set up, use, deploy, record

**Microfactory Node: 3D Printer** — the 3D-printing node of the Microfactory. A small,
**fully local Gemma** that learns 3D-printing expertise job-by-job and tells you where a
print will fail *before* it runs. Two personas keep it honest: **Chief Engineer O'Brien**
proposes settings; **La Forge** (a separate QA Inspector) grades — O'Brien never grades his
own work. Model: `gemma4:e4b` local · `google/gemma-4-E4B-it` on the Space (ZeroGPU).

This is the one operational doc: how to run it, use it, deploy it, and record it. History,
findings, and the phase log live in `docs/reference/RUNBOOK-FINDINGS.md`; day-by-day plan in
`docs/plan/`; the recording script in `docs/writeup/02-VIDEO.md`.

---

## 1 · Run it locally

```bash
cd chief-engineer
make setup                      # uv sync (locked env) + generate sample meshes
ollama serve &                  # its own terminal; leave running (for live Gemma)
ollama pull gemma4:e4b          # = gemma4:latest, ~9.6GB
make test                       # offline core tests (~1s, no Ollama) — expect ALL PASSED
make run                        # → http://localhost:7860  (status bar shows the live model)
```

Falls back to a deterministic advisor if Ollama is unreachable, so it never crashes; the UI
always shows which model ran. `CHIEF_ENGINEER_MODEL=gemma4:e2b` for ~2× faster CPU latency.

**Want the fine-tuned Chief Engineer instead of stock Gemma?** Four LoRA-fine-tuned variants are
pre-merged + quantized and live on the public Ollama registry at
[`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur):
```bash
ollama pull kylebrodeur/microfactory-node-v3-qat                    # recommended (q4_k_m, 5.3GB)
CHIEF_ENGINEER_MODEL=kylebrodeur/microfactory-node-v3-qat make run
```
The other tags (`-v2`, `:q4_0`, `microfactory-node` v1) plus the canonical HF Hub copies
and the full publishing runbook are documented in
[`learn/finetune/OLLAMA_PUBLISHING.md`](../learn/finetune/OLLAMA_PUBLISHING.md) and the
[GGUF model card](https://huggingface.co/kylebrodeur/microfactory-node-gguf).

---

## 2 · Use the tool (the guided tour — also the judge's tour)

Live at **[node.microfactory.space](https://node.microfactory.space)** (custom domain; fallback
`build-small-hackathon-microfactory-lab.hf.space`). Four tabs, left to right. This is exactly what
a judge should see. The top header carries the **model switcher** (LoRA v3 QAT / LoRA v2 / Base /
Modal API), a small **info icon** tooltip, the **Warm up Model** button, and the live model status
+ clock. Every tab has its small primary action and a persistent **Reset** in the same top-right
spot. The UI uses custom icons (no emojis) and one consolidated loader that reveals content once
the work finishes.

1. **Build — define the job.** Quick-load **3DBenchy** (or generate a primitive / drop a
   mesh; drop one of your own printed STLs to demo on real parts). You don't pick the part
   type — the engineer **infers** it from the mesh ("reads this as overhang-dominant").
   The simulated **environment** (temp / humidity), **build-plate position** (center / edge /
   corner), and **material** (PLA / PETG / ABS / TPU) share the top control row, with
   **RANDOMIZE / OVERRIDE / RESET / SLICE** on the right. The **Job Log** up top shows what
   is stored and where. Hit **SLICE** (top right).
2. **Slice — the pre-flight read (the load-bearing moment).** Slicer image + motion preview
   render immediately; the horizontal **LAYER** scrubber below the image steps through real
   cross-sections of *this* part. The **THE READ** segmented toggle flips between
   **Engineer's Read** and **Second Opinion**, one panel at a time. **O'Brien** recalls the
   closest prior jobs, says what transfers, flags the failure regions **before anything
   prints**, and the **Spine** vetoes unsafe values (validation + g-code fold into his read).
   Flip to **Second Opinion** → **La Forge** critiques the plan; a *dispute* **holds → PRINT**
   until you acknowledge. Clicking **Second Opinion** a second time does not re-run it for
   the same build.
3. **Print — run it and watch it compound.** **THE PLAN** card up top frames the run: *what
   we're testing* (the job + conditions + the question), the Engineer's Spine-validated
   proposed settings, and *what La Forge expects*. Press **PRINT** (top right); the compact
   **ITERATIONS** slider sets how many runs (**1 = a single print**). Results stream in live as
   each iteration finishes: the **OUTCOME · WHAT HAPPENED** block (simulated result + La Forge
   run verdict) appears first, followed by the quality curve, the **iteration log**, the learned
   policy cell, and a compact **LOG A REAL PRINT** strip to feed a real-machine outcome back into
   the ledger. **OVERRIDE PLAN** (same popup component as OVERRIDE ENVIRONMENT on LOAD) lets you
   print against your own settings instead of the Engineer's. *(Pick a genuinely hard job — the
   sim only fails prints that should: PETG overhang @ ~30 °C/65 % climbs 0.55→0.70; Benchy+PETG
   @30/68 climbs 0.68→0.81.)*
4. **Review — the whole job in one place.** The **SESSION RECORD** assembles the full story:
   the inputs, O'Brien's read, La Forge's pre-print second opinion, the simulated run (curve +
   iteration log), the outcome + run verdict, and next steps. Below it the lesson ledger grows
   (seed → earned → sim) and the **capability mesh** is a collapsible outlook view. La Forge's
   run verdict also sits up top. **RESET TO BASELINE** (top right, present on every tab) starts a
   fresh demo (clears this session's runs + learned policy; keeps seed + ingested).

**The honesty spine (say this out loud):** the Engineer proposes, a deterministic Spine
disposes, a deterministic world produces the outcome, and a *separate* Inspector grades it —
the model never marks its own homework. **Real:** compounding retrieval + learned policy,
proactive risk flags, local Gemma, the QA Inspector. **Simulated (the one boundary):** print
*outcomes* (`sim/outcome.py`). **Frontier (named, not faked):** weight-level fine-tuning,
multi-node execution, physical sensors/camera. We calibrated the sim against 178 real failure
prints, measured **32.6%**, found the gap was structural, and **documented it instead of
faking a tuned number** (`sim/calibration/CALIBRATION-REPORT.md`).

**If the live model is slow/falls back:** the Space runs Gemma on ZeroGPU (first BUILD loads
it, ~30s). If GPU quota is momentarily out it **falls back** to the deterministic
advisor (clearly labeled) rather than erroring.

---

## 3 · Deploy to the Space

> **Final submission pass?** Work the [`docs/plan/SUBMISSION-PUNCHDOWN.md`](docs/plan/SUBMISSION-PUNCHDOWN.md) list, and
> follow [`docs/plan/FINAL-SEED-AND-DEPLOY.md`](docs/plan/FINAL-SEED-AND-DEPLOY.md) — the ordered seed/deploy commands.

Space: **`build-small-hackathon/microfactory-lab`** · SDK gradio, app at **root**, hardware
**ZeroGPU**, **HF Pro active** (ample quota → live Gemma on screen). The Space installs from
`requirements.txt`; the `chief-engineer/` contents go to the Space **root**. The local agent
has `hf` CLI access and can run the auth/repo checks and the push directly.

```bash
make deploy-check      # offline GO/NO-GO gates (D1–D10). Run any time; nothing is pushed.
make deploy            # gates → if green + authenticated, upload_folder to the Space + factory reboot
```

`make deploy` (= `scripts/deploy_preflight.py --push`) uploads everything **except**
`docs/`, `spike/`, caches, secrets, and runtime files — so `learn/`, `assets/`, and
`data/*.jsonl` go too (the app needs them). The gates: build imports + core tests, all Space
files present, README frontmatter valid (`short_description` ≤60), lean reference block, clean
ledger baseline, data well-formed, credentials (D8), live Space state (D9), and the **field-log
dataset set + logging (D10)**.

**Credentials:** an **HF write token** (member of `build-small-hackathon`) — `hf auth login`
or `export HF_TOKEN=…`. Check with `hf auth whoami`. The Claude-on-the-web session carries no
token by default (deploy-check warns D8); deploy from an authenticated machine or set `HF_TOKEN`.

**Space variables** (set once; a change triggers rebuild):
```bash
hf spaces variables add build-small-hackathon/microfactory-lab \
  -e GRADIO_SSR_MODE=False -e CHIEF_ENGINEER_BACKEND=zerogpu \
  -e CHIEF_ENGINEER_HF_MODEL=google/gemma-4-E4B-it
```

After deploy, **smoke-test the live UI:** LOAD a part, then **SLICE** shows O'Brien
reasoning (NOT "Error"); La Forge second opinion + the dispute-gate work; LAYER
scrubber slides; Print loop runs; Review shows the ledger + verdict + **↺ RESET**;
wide layout, no empty right gutter.

### Field log — "all runs → a shared dataset" (Sharing is Caring)

Every interaction (build / second-opinion / simulate / print / record) logs one flat row to a
HF Dataset via `core/field_log.py` (`CommitScheduler`, flushes ~5 min) — **automatic once the
token is set, silently no-ops without it** (local/offline unaffected; config + outcomes only,
never PII or files; rows are candidates, never auto-promoted to the curated ledger).

1. **Dataset repo — check first** (it likely exists): `hf datasets info build-small-hackathon/chief-engineer-field-log`. Create only if missing (the first `hf upload` to a non-existent dataset creates it; add `--private` for a private repo); never recreate. Must match `FIELD_LOG_REPO` in `core/field_log.py`.
2. **`HF_TOKEN` as a Space *secret*** (write, org member): Space → Settings → Variables and secrets → New secret. Reboot.
3. **Verify:** do one SLICE on the Space, wait ≤5 min, confirm a new row in `interactions.jsonl` (or `make deploy-check` D10). The schema is one flat 26-column table → renders cleanly in the HF dataset viewer.

### Deliberation traces — "how the agent reasons" (Sharing is Caring)

A second open dataset that captures the **turn-by-turn argument between the personas**
(O'Brien proposes → Spine vetoes → La Forge second opinion/dispute → operator override →
World simulates → La Forge grades → run verdict). One row per turn; shares one schema across
two sources:

- **Static, reproducible export:** `make deliberation` → `dist/deliberation/` (JSONL + card).
  Offline-safe; run with `ollama serve` up first to capture O'Brien's *real* reasoning rather
  than the `[fallback]` text.
- **Live, every run:** `core/deliberation_log.py` (`CommitScheduler`, same `HF_TOKEN` gate +
  best-effort/never-break contract as the field log) appends turns on each Space run.

Schema: `session_id, track, turn, agent, role, act, stance, content, material, geometry,
bed_position, env_temp, env_humidity, ts` — renders cleanly in the dataset viewer.

1. **Dataset repo — check first:** `hf datasets info kylebrodeur/chief-engineer-deliberation`. Create only if missing (the first `hf upload` creates it; add `--private` for private); must match `DELIB_LOG_REPO` in `core/deliberation_log.py` and `HF_REPO` in `scripts/export_deliberation.py`.
2. **Seed it (optional but nicer):** `ollama serve` + `make deliberation`, then `hf upload kylebrodeur/chief-engineer-deliberation dist/deliberation . --repo-type dataset` (the card ships as the repo README).
3. **Live capture:** the **same** `HF_TOKEN` Space secret that powers the field log also powers this — no extra setup. Do one LOAD → SLICE → PRINT on the Space, wait ≤5 min, confirm new rows in `deliberations.jsonl`.

---

## 4 · Record the demo

Full beat sheet, shot list, and **what to say** for each beat: **`docs/writeup/02-VIDEO.md`**.

```bash
# clean curve first (keeps seed+ingested), then record
git checkout -- data/lessons.jsonl && rm -f data/policy.json   # or click ↺ RESET in Review
make record-check        # recording preflight (cap-cli + Space + playwright gates)
make record-beat BEAT=load   # record the LOAD beat (one .cap project per beat)
make record-beat BEAT=slice  # record the SLICE beat
./scripts/export-beat.sh /path/to/beat.cap recordings/beats/<beat>.mp4
```

Record from the **live Space** (HF Pro = live Gemma reasoning on screen). Use a **climbing
job** for the compounding beat (above). Per-beat recording is handled by `scripts/record-beat.sh`. See `recordings/EDITING.md` for the
full beat list and which beats need Cap Studio polish. One-time deps: `uv pip install playwright && uv run playwright install chromium`.

**Cleaner capture (Kyle's setup):**
- **Install the Chrome app Gradio offers** (the "Install" / PWA prompt in the address bar on the
  Space). It opens the app in its own chromeless window — no tabs, no URL bar — so the screen
  recording is a clean interface with just the console.
- **Cap Studio with a "Desktop Background"** for the final cut: export a **1080p** version so the
  screen capture sits cleanly alongside the regular (camera) footage when the two tracks are cut
  together. Match the 1080p export to the camera end-cap resolution.

---

## 5 · Quick reference

| Command | Purpose |
|---|---|
| `make setup` | uv sync (locked env) + generate meshes |
| `make test` | offline core tests (no Ollama, ~1s) |
| `make run` | launch the app (status bar shows the live model) |
| `make preflight` | live-stack GO/NO-GO (Ollama, latency, JSON, reasoning, Spine, assets) |
| `make deploy-check` | deploy/record readiness gates (D1–D10, offline) |
| `make deploy` | gates → push the Space (`upload_folder`) + factory reboot (needs `HF_TOKEN`) |
| `make record-check` | recording preflight (cap-cli + Space + playwright gates) |
| `make record-beat BEAT=load` | record one beat to its own `.cap` project |
| `./scripts/export-beat.sh <cap> <mp4>` | export a `.cap` project to MP4 |
| `uv run python scripts/assemble-video.py recordings/manifest.json` | assemble camera + beats + VO |
| `make trace` | export the ledger as a Hub-ready dataset → [kylebrodeur/chief-engineer-ledger](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger) |
| `make deliberation` | export the multi-persona deliberation as a Hub-ready dataset → [kylebrodeur/chief-engineer-deliberation](https://huggingface.co/datasets/kylebrodeur/chief-engineer-deliberation) |
| `core/field_log.py` | live Space interactions → [build-small-hackathon/chief-engineer-field-log](https://huggingface.co/datasets/build-small-hackathon/chief-engineer-field-log) |
| `git checkout -- data/lessons.jsonl && rm -f data/policy.json` | reset demo curve (keeps seed + ingested) |
| `CHIEF_ENGINEER_MODEL=gemma4:e2b` | faster model (env wins over `.env`) |

---

## 6 · Troubleshoot (durable gotchas)

- **Dev Mode must be OFF** on the Space — an `openvscode` build log means it runs the dev
  shell, not `app.py` (you'll see a default greet template). Disable + reboot.
- **`short_description` ≤ 60 chars** in README frontmatter or `hf upload` rejects it.
- **`requirements.txt` only** is mounted at build — ZeroGPU deps (`spaces`/`torch`/
  `transformers`/`accelerate`) are **inlined** there. Local dev stays lean (uv base, 4 deps);
  `app.py` shims `spaces` to a no-op when absent.
- **`@spaces.GPU` is on the inference function only** (`core/llm_zerogpu._generate`), NOT
  `build_job` — so a quota-out falls back to the advisor instead of erroring the whole handler.
  `app.py` imports `core.llm_zerogpu` at startup so ZeroGPU still detects the GPU function.
- **`data/lessons.jsonl` is the durable ledger** (tracked) — don't `rm` it; use the reset
  command (keeps seed + ingested).
- **Use `make` targets / `uv run python -m scripts.<name>`** — bare `python scripts/x.py` fails.

History, findings, and the phase log: **`docs/reference/RUNBOOK-FINDINGS.md`**. Deploy
deep-dive: `docs/reference/DEPLOYMENT.md`. Open items: `docs/plan/ISSUES.md`.
