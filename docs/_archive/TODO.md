# Chief Engineer — Running Log & TODO

Living doc. Update as work lands. Authority for *what* to build: `docs/plan/`. This tracks
*state* + follow-ups + anything from the conversation that must not be lost.

_Last updated: 2026-06-13 (endgame Day 9 — recording automated). Open items → docs/ISSUES.md._

▶▶ **START HERE to run & test locally: `RUNBOOK.md` (ordered command sequence).**

---

## ✅ Done (2026-06-13 — recording automated)

- **`scripts/record.py`** — one-command recording pipeline: preflight (5 gates) →
  launch Chrome (CDP, about:blank, --start-maximized) → pre-warm ZeroGPU →
  start Cap (60fps, detached) → drive 8 beats via Playwright → stop → export
  MP4 to `D:\workspace\recordings`. Beats: studio, build, second opinion, scrub,
  placement, climbing job, print loop, review.
- **Chrome restore popup** fixed: `about:blank` + unique `--user-data-dir` per run.
- **HF header badge** hidden: CSS injection targets `#huggingface-space-header`.
- **Screen ID** discovered dynamically (was hardcoded, broke on reboot).
- **Export** direct to `D:\workspace\recordings` (dir created from Windows side).
- **Quality:** 60fps, 1707×1067 viewport, longer beat settle times (BUILD 7s, etc).
- **RUNBOOK + Makefile** updated: `make record-check`, `make record`.

## ✅ Done (2026-06-12 — writeup voice pass + field notes + submission audit)

- **Writeup voice-passed** (`docs/writeup/01-SUBMISSION.md`): Kyle's first-person voice, ~1,300 words.
  Calibration honesty story (34.2%, didn't tune to bad data), QA Inspector paragraph. Both ⚠ marks resolved.
- **Field Notes drafted** (`docs/writeup/06-FIELD-NOTES.md`): 9 sections, all links filled, ready for org blog copy-paste.
- **Submission audit** (`docs/writeup/SUBMISSION-AUDIT.md`): 41-item line-by-line audit. 18✅ 8◐ 12❌ 3⚠.
- **README**: added field-notes tag, Links section (Space, dataset, video placeholder, social placeholder, source).
- **Installed playwright+chromium** for `scripts/capture.py`.

## ✅ Done (2026-06-12 — restructure + hybrid evaluator)

- **Space is 🟢 LIVE on ZeroGPU** (`google/gemma-4-E2B-it`). Deploy fixes: SSR off,
  `@spaces.GPU` on `build_job`, monkey-patched `demo.launch`, zerogpu deps inlined in
  `requirements.txt`; local `make run` kept lean via a `spaces` shim. Canonical guide:
  `../DEPLOYMENT.md` + RUNBOOK "Deploy to the Space".
- **Re-homed to the real print workflow: Studio → Build → Print → Review.** Studio is
  define+preview only (primary action → BUILD at top; environment + simulated Ender 3 V2
  at top; part panel consolidated with the 3D viewer). **The part class is now inferred**
  from the mesh (`core/viewer.infer_geometry`) — the user doesn't pick it. Build = the
  pre-flight check (slicer + engineer's read + g-code terminal). Print **inherits the
  Build job** and runs the loop. Review = ledger + mesh + run verdict. Sticky footer.
- **Hybrid evaluator — `core/inspector.py`** (a SEPARATE QA Inspector persona; the
  Engineer never grades itself). Context rules: second opinion (Build), per-print/iteration
  grade (Print), run verdict (Review). A **dispute gates → PRINT** until acknowledged.
- **Capture + docs synced:** `scripts/capture.py` beats (new tabs/labels + `--beat second`),
  `02-VIDEO.md` (beats/shot-list + Inspector beat now live), README workspaces, RUNBOOK flow.
- **Doc tidy:** removed the duplicate top-level `docs/SPACE-DEPLOY.md`; `08-ZEROGPU` refs
  repointed to `_archive/`; docs map updated; `../DEPLOYMENT.md` named canonical.

### Follow-ups
- Push the restructured app to the live Space (`app.py`, `core/`, `ingest/`, `data/`, `README.md`) + reboot + smoke-test.
- Optional: push the `@spaces.GPU` decorator down to wrap only the LLM call (save ZeroGPU seconds).

## ✅ Done (2026-06-12 — ingestion review + calibration)

- **Reviewed the Modal ingestion** (local-session work, real `modal run`s, ~$0.05): Lane A
  1,304 refs, Lane C 260 obs (140 success / 61 sag / 59 stringing), 13 hand-written ingested
  lessons. Artifacts committed; enums valid; `make test` green; `modal_app.py` import-guarded.
- **Lean, on-demand `reference_block`** (`ingest/distill.py`): was flooding the prompt with
  500+ lines/material (3DTime bbox/infill metadata + parse-noise). Now ≤5 trustworthy aggregated
  lines, **prefers curated configs** (Prusa/Klipper/Marlin) over bulk modal-derived values,
  drops out-of-range garbage, and excludes fan (only available from the unreliable fan=0 parse).
  Added `material_facts()` / `lookup_fact()` for on-demand fetch. Bulk corpus stays in
  `references.jsonl` as data.
- **Calibration run + honest decision: did NOT tune** (`sim/calibration/CALIBRATION-REPORT.md`).
  34.2% on the modal set is dominated by data artifacts (178/260 rows fan=0 → false sags) +
  a structural stringing gap that, if forced, would break the Print loop. Sim is correct where
  data is clean (61/61 sag). Persisted as a shareable dataset (`sim/calibration/README.md` +
  `results/` metrics) for a future Hub dataset.
- **`data/lessons.jsonl` is now the durable ledger** (tracked); reset made non-destructive
  (`git checkout -- data/lessons.jsonl && rm -f data/policy.json`) across README + RUNBOOK.
- **`docs/RESEARCH-NEEDS.md`** — prioritized data gaps + the "what we learned from bad data"
  findings + a kickoff prompt for the next data-acquisition Modal run (fix fan/retraction/geometry
  extraction; add failure-bearing sources; re-calibrate).

### Follow-ups (data)
- Next Modal run per `RESEARCH-NEEDS.md`: fix Lane-C extraction, add outcome-diverse failure data, re-calibrate.
- BambuStudio/Kanrog parsers are written but OOM at 512MB — rerun with memory=4096.

## ✅ Done (2026-06-10 endgame session)

- **Real-hardware validation (PEGASUS):** preflight full GO on BOTH models; e4b/e2b
  head-to-head + decisions recorded in `RUNBOOK.md` → Findings log (G2 bands
  recalibrated to warm<20s PASS; Tiny Titan counts effective params; rec: e2b).
- **uv adoption** (locked env, `make` targets through `uv run`) + **core/ + scripts/
  reorg** (app.py stays at root for the Space) + repo-wide bare-python/pip sweep.
- **`.env` made real** — `core/__init__.py` stdlib loader (setdefault; shell wins).
  It was never loaded before.
- **GEMMA-STEERING adopted** — vendored to `docs/reference/` with an implementation
  map; fence-strip net in `chat_json` (T2); prompt-size telemetry in preflight (T5).
- **Docs architecture:** `docs/README.md` — the public-vs-internal map; the public
  tier (README, SIMULATION, reference/, writeup/) is the judge surface + writeup basis.
- **RUNBOOK restructured:** NOW → gotchas → findings log → phases → quick reference.
- **`RUNBOOK.md`** — the literal order of operations to run & test locally
  (Phase 0 setup → 1 prove the real model → 2 dry-run → 3 RECORD → 4 submittable
  baseline → 5 upgrades → 6 submit), each step with a check + contingency pointer.
- **`preflight.py`** — GO/NO-GO gate on the real stack (G1–G8: Ollama env, latency,
  JSON contract, reasoning quality + novel-case honesty, Spine, app, assets) + a
  Tiny Titan (≤4B) eligibility check via `ollama show`. Offline gates verified.
- **ZeroGPU live-inference backend (staged, OFF by default)** — `llm_zerogpu.py`
  (transformers + `@spaces.GPU`, QAT-Gemma-ready) dispatched from `llm.py` only
  when `CHIEF_ENGINEER_BACKEND=zerogpu`; default path byte-identical. Closes the
  "Space shows only the fallback" gap. `requirements-zerogpu.txt` +
  `docs/_archive/08-ZEROGPU-DEPLOY.md`. ⚠ verify the QAT model id on HF before publish.
- **Virtual printer visual** — `sim/virtual_printer.py`: slices the real mesh into
  real cross-sections (pure-numpy triangle-plane) and animates them rising → GIF
  (Pillow only, **zero new deps**, permissive, Space-safe). Verified on
  overhang/vase/bridge. Isolated/removable; integration snippet in-file. Scope kept
  honest: motion/visual legitimacy only — failure prediction stays in `sim/outcome.py`.
- **Strategy docs** — `docs/plan/05-ENDGAME.md` (strict day-by-day + abort gates),
  `06-CONTINGENCY.md` (symptom→fix→fallback runbook), `07-COMPETITIVE-LANDSCAPE.md`
  (track-aware read: rivals are mostly stateless single-shot; we're the only
  compounding one; Storytelling + Tiny Titan plays; rivals fine-tuned in-window so
  frame retrieval as deliberate), `docs/writeup/05-PROJECTED-OUTCOME.md` (honest
  prize sim: badges high-confidence, Backyard cash a real minority shot).
- **Submission drafts** — `docs/writeup/01-SUBMISSION-DRAFT.md`,
  `03-SUBMISSION-CHECKLIST.md`, `04-SOCIAL-POST.md`.
- **`spike/vault_mind/`** — pi-vault-mind (LanceDB vector+FTS+graph) spike, minus
  Obsidian; isolated, lancedb spike-only. Quarantined from the demo path.

---

## ✅ Done (2026-06-08 build session)

- **`tune-simulator` skill + calibration harness.** The simulator's constants are now
  data-tunable by an agent, not hand-guessed:
  - `sim/calibrate.py` — read-only, deterministic harness scoring `sim/outcome.py` against
    observed outcomes (accuracy + quality MAE + confusion + per-mismatch dominant-penalty
    diagnostics). `uv run python -m sim.calibrate [--data obs.jsonl]`.
  - `sim/calibration/observations.sample.jsonl` — template (settings + room + real outcome +
    optional quality); replace with real prints / 3D-ADAM classifier output.
  - `.claude/skills/tune-simulator/SKILL.md` — workflow: baseline → diagnose from confusion →
    one minimal lever at a time → keep only if accuracy↑/MAE not worse → protect the
    `test_simulator_physical_and_deterministic` invariant → report → commit on request. Includes
    a constant→failure-mode lever map. Validated end-to-end: sample 66.7%→83.3%, MAE 0.228→0.185,
    invariants intact (then reverted — shipped sim is NOT overfit to sample data).
  - Note: the ledger stores no settings, so it can't be calibration data directly; observations
    must carry the settings used.


- **Closed learning loop — the primary demo (NEW direction: simulated outcomes + improvement).**
  Per Kyle: this is more than a lookup; it must *improve* from past + knowledge base and be visible
  in the UI. Built, all removable layers, headless-tested:
  - `sim/outcome.py` — deterministic physics-lite **outcome simulator**: the single stand-in for the
    printer + sensors. Models the seed-lesson physics (cooling↔sag, humidity↔stringing, ABS warp,
    bed↔adhesion) → outcome + 0-1 quality. NOT the model grading itself (separate world). ✓ tested.
  - `learn/policy.py` — **learned parametric policy**: setting offsets per (material, geometry,
    env-*bucket*), persisted to `data/policy.json`. Generalizes to similar (not identical) jobs. The
    "not just a lookup" part. Injected into the live LLM prompt via `policy_note` (steering). ✓ tested.
  - `learn/loop.py` — the closed loop: propose → Spine → simulate → ledger(source=`sim`) → policy
    update. `run_session` shows quality climbing fail→clean; verified transfer to similar conditions.
  - UI: **Learning Loop tab** (quality curve + per-iteration log + policy cell before/after) and a
    cockpit **🧪 Simulate outcome** button. Both close the loop visibly. ✓ app serves, handlers work.
  - `SIMULATION.md` — honest-claims table + exactly what the physical interfaces need (g-code
    streaming, env sensors, camera + 3D-ADAM defect CV). The simulated boundary is kept to one swap.
  - Policy + RAG both feed every recommendation. Fine-tune stays framed-frontier (Modal stub).


- Retired the off-target misfire (book-production swarm + CNC CAM) built before the real spec
  arrived. `DESIGN.md` (Astrometrics) kept at lab root as the Off-Brand reference.
- Organized all provided plan/writeup docs into `docs/plan/` and `docs/writeup/`; seeds into
  `data/seed_lessons.jsonl` (the canonical 12).
- Built the core loop to spec (`models · ledger · prompts · spine · chief_engineer · reflect ·
  seed_lessons · nodes · viewer · llm · app`).
  - Retrieval: exact material+geometry, normalized `[temp,humidity]` Euclidean, top 2-3. ✓ tested.
  - Spine veto: hardcoded material bounds, clamps + trips HITL. ✓ tested (PLA 260→220).
  - Reflection: human outcome → earned `LessonEntry`, append-only. ✓ tested.
  - Real Ollama calls (`gemma4:e4b`) with deterministic fallback; UI shows which ran. ✓ offline path.
  - Two-view Gradio app (Cockpit + Capability Mesh/Ledger), Astrometrics CSS. ✓ launches, HTTP 200.
  - Sample meshes via trimesh (`make_assets.py`). ✓
- `requirements.txt` / `pyproject.toml` (gradio 6.17, ollama, pydantic, trimesh; MIT, no AGPL).
- `test_core.py` — all core tests pass headless.
- `docs/KNOWLEDGE-SOURCES.md` — catalog + ingestion plan.
- Pre-local-review scaffolding (all tested where possible):
  - `scripted_demo.py` — curated integration run / video-beat source. Shows precedent applied,
    env-driven shift, an earned lesson reused on the next job, and the novel "no precedent" case.
  - `export_trace.py` — ledger → HF Datasets-ready JSONL + card (Sharing-is-Caring badge).
  - `bench_latency.py` — measure gemma4 latency on real hardware (run locally pre-window).
  - `Makefile` + `.env.example` — one-command local bring-up.
  - Expanded `test_core.py` (retrieval ordering, no-precedent, g-code). All pass.

- Knowledge ingestion (`ingest/`): deterministic distiller (Prusa INI / Klipper cfg / Marlin .h →
  `references.jsonl`; research JSONL → ledger as `source="ingested"`) + 3D-ADAM defect taxonomy +
  a clearly-marked **Modal app stub** (`ingest/modal_app.py`) to be replaced by the MCP-hackathon
  code. Samples in `ingest/samples/`. References injected into the prompt (optional/removable). ✓ tested.
- Day-3 legibility: deterministic **PRECEDENT EVALUATION** panel — narrates the env delta vs the
  nearest prior job ("4°C warmer, 12 pts more humid → conditions worse → adjusting"), plus the
  novel "no close precedent" case. Reliable even in fallback. ✓ tested.
- Off-Brand UI: Astrometrics/LCARS CSS pass (orange-elbow header, mono everywhere, tab/slider/
  button accents). Next reach = `gr.Server` for the award.

## ✅ Ready for your local review
- `make setup && make test && make demo` should pass offline today.
- `ollama serve` + `make run` → live `gemma4:e4b` cockpit. `make bench` to check latency.

## 🎯 ENDGAME (June 10–15) — authority shifts to `docs/plan/05-ENDGAME.md`

Build is feature-frozen. What remains is proof: preflight green locally → record →
deploy Space → writeup voice pass → submit June 14. The kit:

- `make preflight` — run FIRST every local session; gates G1–G8 grade the real
  model path (latency, JSON contract, reasoning quality, novel-case honesty) +
  offline invariants. Each FAIL points into the runbook. Validated headless
  (offline gates pass; live gates exercise locally).
- `docs/plan/05-ENDGAME.md` — strict day-by-day with hard gates, abort
  criteria by the clock, and field intel (29 awards; visible competitors; story
  lane open; Storytelling/Tiny Titan badges to verify on the live field guide).
- `docs/plan/06-CONTINGENCY.md` — symptom→diagnose→fix→fallback for every
  local failure mode (Ollama, latency, JSON, weak reasoning, Space deploy,
  recording day, §S2 live-inference-on-Space decision).
- `docs/writeup/01-SUBMISSION-DRAFT.md` — full ~1,100-word draft (room for the
  voice pass), claims audited against the honesty table; two ⚠ to resolve.
- `docs/writeup/04-SOCIAL-POST.md` — 3 variants + mechanics checklist.
- `docs/writeup/03-SUBMISSION-CHECKLIST.md` — binary Day-10 list ([REQ] items
  from the field guide: Space in org, video, social post linked in README,
  frontmatter tags, ≤32B).

## ▶ Current (2026-06-13 — Day 9 of endgame)

Authority: `docs/plan/05-ENDGAME.md`. Recording is automated. Remaining:

- [ ] **Kyle reviews the recording** (latest: `D:\workspace\recordings\demo-all-20260613-102516.mp4`, 87s)
- [ ] **Publish Field Notes** on org blog (`docs/writeup/06-FIELD-NOTES.md`)
- [ ] **Post social** (pick variant from `docs/writeup/04-SOCIAL-POST.md`, get URL)
- [ ] **Verify Off-Brand CSS** (open Space, screenshot Astrometrics)
- [ ] **Ask org about Tiny Titan** eligibility
- [ ] **Fill README placeholder links** (video URL, social post URL) — agent can do once URLs known
- [ ] **UI polish** — Kyle to enumerate critiques (see `docs/ISSUES.md` #15–19)

## 🌙 Stretch goals — ranked

1. [x] **ZeroGPU live model on the Space** — 🟢 LIVE (`google/gemma-4-E4B-it`). Done 6/12.
2. [x] **Modal ingestion** — Done 6/12. 1,304 Lane-A refs, 260 Lane-C obs, 13 ingested lessons.
3. [x] **Calibrate the sim to real data** — Done 6/12 (honestly deferred; report at `sim/calibration/CALIBRATION-REPORT.md`).
4. [ ] **UI polish + filled virtual printer** — Kyle has UI critiques (see `docs/ISSUES.md` #15–19).
       `sim/virtual_printer.py` numpy outline works; `trimesh.section_multiplane` upgrade written but not integrated.
5. [ ] **gr.Server fully custom frontend** — Explicitly NOT happening this window (ENDGAME freeze). Frontier.

DONE: ~~3DBenchy hero mesh~~ (CC0, decimated to assets/benchy.glb, slices live via vectorized slicer).

## ⚑ Follow-ups / needs Kyle → moved to `docs/ISSUES.md`

All open follow-ups are now tracked in `docs/ISSUES.md` (#11–14):
MCP-hackathon Modal code, knowledge sources, sensors decision, node machine control.
Pre-window de-risk and deploy are done (preflight passes, Space is live).

## 🧪 Spikes (isolated, removable — not in demo path)

- [x] **`spike/vault_mind/`** — Done 6/10. Runnable skeleton + full handoff docs.
  LENS 1: subsumes `ledger.retrieve` 7/7. LENS 2: cross-key transfer precedent
  plumbing proven (needs real embedder for semantic payoff). **Graduation deferred**
  (not in endgame window). Keep as reference; remove with `rm -rf spike/vault_mind/`.

## 🧠 Must-not-lose context (from the conversation)

- **Domain:** FDM 3D printing on Kyle's **Ender** printers. Proactive *pre-print* error catching
  (most tools watch *during* printing — we're ahead of the nozzle). Real user = Kyle (no machinist).
- **Credits available:** Modal $500 + $250/participant; HF $20; Codex $100. Use Modal for ingestion
  + any fine-tune; pursue the Modal award.
- **Model:** quantized **gemma4** — `gemma4:e4b` default, `gemma4:e2b` fallback.
  **`gemma4:4b` does not exist — never use it** (it broke the Kaggle build).
- **Latest deps:** Gradio **6** (6.17.3 here). Re-audit ollama/pydantic/trimesh to latest before ship.
- **Honesty (60/40):** claim only what the demo shows; fine-tuning / multi-node / physics = frontier.
- **License landmine:** never import/link OrcaSlicer or PrusaSlicer (AGPL-3.0).
- **Story is the spine:** the grandfather's shop; "knowledge built over a lifetime, lost in an
  afternoon — and the opposite of that." (`docs/writeup/00-STORY.md`.)
- **Doctrine:** demo path is the product; record early; every advanced layer removable; submit with
  buffer; narrow surface (3-4 levers) + deep memory. Don't hardcode lessons — use research + earned.

## 🟢 Badge tracker

Verified 6/10 (agent research; guide page itself unreadable — slugs confirmed
from real submissions): **6 merit badges**; tags `off-the-grid`, `well-tuned`,
`off-brand`, `llama-champion`, `sharing-is-caring`, `field-notes`. **Storytelling
is a judging principle, NOT a badge.** **Tiny Titan is a separate $1.5k special
award** — and ambiguous for us (32B cap counts TOTAL params; e2b=5.1B/e4b=8.0B
raw vs ~2B/~4B effective): ask in org discussions before tagging. Bonus Quest
Champion ($2k) needs all 6 badges — out of reach without Well-Tuned.

| Badge (tag) | State |
|-------|-------|
| Off the Grid (`off-the-grid`) | ✅ by construction |
| Llama Champion (`llama-champion`) | ✅ Ollama runs on llama.cpp — documented in writeup |
| Sharing is Caring (`sharing-is-caring`) | ✅ trace pushed to HF ([dataset](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger)) |
| Field Notes (`field-notes`) | ◐ draft exists — needs voice-pass + publish (ISSUES.md #4) |
| Off-Brand (`off-brand`) | ◐ CSS started — needs verify + screenshot (ISSUES.md #5) |
| Well-Tuned (`well-tuned`) | ✂ frontier — not in-window |
| — Tiny Titan award (`tiny-titan`) | ⚠ eligibility unresolved (ISSUES.md #6) |
