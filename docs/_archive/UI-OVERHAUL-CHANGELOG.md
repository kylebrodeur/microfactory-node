# UI Overhaul — Changelog (against the walkthrough spec)

Date: 2026-06-14. Source spec: `walkthrough/index.md` (54 items across 4 tabs + global
rules + 3 open questions). This records what changed, file by file, and the honest status
of every spec item (done / partial / deferred), including the interpretation calls.

### Latest
- **2026-06-14: envbar action grouping** — Both the left-side controls (ENVIRONMENT +
  OVERRIDE + POSITION + MATERIAL) and the right-side actions (RANDOMIZE + RESET + SLICE) are
  wrapped in their own column groups. The action group is pushed to the far right and
  bottom-aligned to the pill rows. Tightened CSS so the row fills the full width without
  pushing the left group toward the center or clipping the environment readout.
- **2026-06-14: arrow glyphs on next-step buttons** — primary SLICE / PRINT / REFRESH
  buttons use `.ce-icon-arrow-after` to append a right-pointing arrow glyph via CSS
  pseudo-element (SVG mask, no emoji).
- **2026-06-14: removed pre-rendered demo video** — deleted `.cap/` recording artifacts
  (including `display.mp4`) from the Space and added `*.cap/**` to deploy_preflight.py
  `SPACE_IGNORE` so future uploads never ship misleading pre-rendered footage.

## Open questions — resolved (via AskUserQuestion)

- **oq-1 (print-11/12) Single vs Iterations:** ONE default action. The `ITERATIONS` slider
  drives `PRINT`; slider at 1 is a single print; La Forge grades each run inline. The separate
  "Simulate One Print" button is gone.
- **oq-2 (build-10) Second opinion reveal:** an inline **segmented toggle** (Engineer's Read |
  Second Opinion) that shows one panel at a time, computed lazily. No tab switch.
- **oq-3 (print-08/13/14) Outcome clarity:** **two-zone outcome** — a dominant SIMULATED RESULT
  zone (final outcome + climb + La Forge run verdict) and a compact (~20%) LOG A REAL PRINT
  strip for feeding a real-machine outcome back into the ledger.

## Files touched

- `core/theme.py` — added the no-emoji **icon set** (`_ICONS` + `icon()`), the consolidated
  custom **`loader()`**, **`tab_intro()`**, and a UI-overhaul CSS layer (hide stock loaders,
  `.ce-loader` scan bar, `.ce-actionbar` top-right action row, `.ce-card` contained block,
  empty-collapse, `.ce-tabintro`, vertical slider, `.ce-seg` segmented toggle, model switcher).
  De-emojied `inspector_panel` (search/check/x icons).
- `core/viewer.py` — de-emojied risk/placement/inspector markers (now `icon()`); imports `icon`.
- `core/llm.py`, `core/llm_zerogpu.py` — `backend_status()` no longer uses 🟢/🟡; uses a colored
  `●` glyph in HTML.
- `app.py` — full `build()` re-layout + rewired handlers: header model switcher + warm-up +
  status; per-tab top-right action bar with persistent Reset; Build slice/preview side-by-side +
  vertical layer slider + Engineer's-Read/Second-Opinion toggle; merged Print action +
  progressive reveal + two-zone outcome + LOG A REAL PRINT; Review single collapsible mesh +
  carded ledger; scroll-to-top on build/print; model switcher (`pick_model`, honest about
  LoRA/QAT not yet serving); `studio_log_html`.

## Verification

`make test` green (10/10) · `make deploy-check` D1–D7 green (D8–D10 are no-credential warnings) ·
`python -c "import app; app.build()"` OK · emoji scan clean on all rendered files · offline E2E
(generate → build → toggle → print → log real outcome) OK.

## Item-by-item status

### Global rules
- No emojis (custom icons only): **done** (icon set; scan clean).
- Small primary, same top-right spot every tab + persistent Reset: **done** (`_action_bar` on all 4).
- Custom loaders / one consolidated then reveal: **done** (stock loaders hidden in CSS;
  `loader()` on Build; progressive reveal via `build_results` / `results_group`).
- Group related controls, no orphans/empty boxes/gaps: **mostly done** (`.ce-card` containers;
  results hidden until run). Fine-grained empty-state polish may need a visual pass.
- Mirrored headers/footers: **done** (`tab_intro` per tab; single shared footer).

### Studio
- 01 Slice→Print terms: **partial** — `tab_intro` says "SLICE (Build) and PRINT"; the tab is still
  titled BUILD (renaming the tab ripples into RUNBOOK/video/deploy-gate copy; left as a flag).
- 02 remove busy block: **done** · 03/16 warm-up to header: **done** · 04 no emojis: **done** ·
  05 fold nonsensical section: **done** · 06 env half-width + materials beside: **done** ·
  07 small Build Job top-right + Reset: **done** · 08 group secondary buttons: **partial** —
  Randomize Environment kept inside the Environment card (env-specific) rather than top-right ·
  09 part/preview full width, drop random material: **done** (no random-material control existed) ·
  10 stack Upload/Benchy/Generate beside 3D: **done** · 11 keep bottom status bar: **done** ·
  12/15 remove duplicate LLM copy, essentials to header: **done** (footer carries the
  "LLM proposes · Spine disposes · Inspector grades" line) · 13 env as status: **done** ·
  14 Job Log to top: **done** · 17 storage info + field lock: **partial** — storage info added;
  "field lock" not addressed (unclear what it refers to) · 18 model switcher Live/LoRA/QAT:
  **done** (honest: Live serves; LoRA/QAT marked training-not-serving) · 19 otherwise good: n/a.

### Build
- 01 clean empty state: **done** (results hidden + loader) · 02 custom loaders: **done** ·
  03 one consolidated loader then reveal: **done** · 04 remove duplicate running-info: **done** ·
  05 remove empty slicer blocks: **done** · 06 group slicer+slider+copy, vertical slider, higher:
  **done** · 07 motion preview side-by-side with slice: **done** · 08 preload/precache slicer
  images: **deferred** — scrubber renders server-side on demand; background pre-render not built ·
  09 Engineer's Read full section + fold validation: **done** · 10 second opinion reveal: **done**
  (toggle) · 11 Print Run Iterations button top-right: **done** (Build top-right routes to Print) ·
  12 improve get-opinion loader: **done**.

### Print
- 01 jump to top on run: **done** · 02 relocate next-step copy: **done** · 03 mirror headers/
  footers: **done** · 04 hide empties pre-run, buttons here: **done** · 05 slider next to print +
  restyle sliders: **partial** — slider grouped in the Run card (not literally adjacent to the
  top-right button) · 06 run = contained container: **done** · 07 progressive reveal: **done** ·
  08 advice-followed vs overridden, prediction held: **partial** — La Forge verdict + prediction-
  held shown; explicit cross-tab "you overrode the dispute" tracking not wired · 09 results show
  quality + time + best settings: **partial** — quality + iteration log + learned policy shown;
  print-time/duration not modeled by the sim · 10 log next to chart: **done** · 11 merge single +
  iterations: **done** · 12 inspector grade within iteration, single default: **done** ·
  13 manual real-print logging: **done** (LOG A REAL PRINT zone) · 14 clarify copy + relocate:
  **partial** · 15 shared footer: **done**.

### Review
- 01 fine: n/a · 02 buttons top-right: **done** · 03 clear full-run verdicts: **partial** — La
  Forge run verdict shown; the itemized engineer/second-opinion/sim/quality breakdown not fully
  enumerated · 04 show printable config if not completed: **deferred** — not built · 05 capability
  mesh one minimizable section: **done** (single collapsed Accordion) · 06 move note to footer/
  header: **done** · 07 lesson ledger merge heading+container: **done** · 08 great: n/a.

## Addendum — model switcher reconciled with the fine-tune backend (2026-06-14)

After the first pass, the fine-tune agent's serving work merged in (`learn/finetune/SERVING.md`):
it built the switcher **backend** (`core/llm_zerogpu_lora.py`, `_apply_model_choice()`,
`MODEL_OPTIONS`, `MODEL_LORA_MAP`, `build_job(model_choice)`) and handed the UI wiring to this
agent. Reconciled: my placeholder Live/LoRA/QAT Radio is replaced by the real
`gr.Dropdown(MODEL_OPTIONS)` — **Retrieval (default) · LoRA v2 (Standard E4B) · LoRA v3 (QAT
E4B) · Modal API (remote)** — wired so `select_model` applies the backend and `build_job`
receives `model_choice`. Added `import os` (the backend used it un-imported, which would have
crashed on selection) and a local-user note (pull the adapters from HF Hub / ollama). This is
no longer the "honest placeholder" — it switches real backends; the LoRA adapters serve via
ZeroGPU on the Space and fall back gracefully where the GPU/deps aren't present.

Backend note for the deploy/inspect pass (not changed here — the fine-tune agent's domain):
`core/llm.py::_zerogpu()` imports `llm_zerogpu`, not `llm_zerogpu_lora`, and treats only
`BACKEND=="zerogpu"` specially (not `"modal"`). So routing the LoRA/Modal selections through the
live inference path may need a small follow-up in `llm.py`. Flagged, not touched, to avoid
colliding with the concurrently-pushing fine-tune agent.

## Addendum 2 — reviewed the fine-tune agent's UI-touching changes + routing fix (2026-06-14)

Pulled again and reviewed everything the fine-tune (local) agent did that touches the UI:

**What the local agent changed in the UI layer:**
- `MODEL_OPTIONS` reordered and finalized to **LoRA v3 (QAT E4B) · LoRA v2 (Standard E4B) ·
  Base (Gemma 4 E4B) · Modal API (remote)**, with a commented future row for local Ollama GGUF.
- App now calls `_apply_model_choice("LoRA v3 (QAT E4B)")` at **import time** (default model).
- Re-added a hidden `model_choice_state` placeholder + a NOTE in two pushes; I removed both each
  time and kept the real `gr.Dropdown(model_select)` I wired (resolved 2 merge conflicts).

**Verified (offline):** app builds; header status renders; all four selections apply via
`select_model` without crashing; the status line honestly shows both the requested choice AND
the real backend (`backend_status()`); full E2E (generate → build → print) works on the default.

**Fixed (the real defect their changes left):** the dropdown offered/defaulted to LoRA + Modal,
but `core/llm.py::_zerogpu()` always imported `llm_zerogpu` (base E4B) and ignored
`CHIEF_ENGINEER_LORA_REPO` — so on the Space the UI would say "LoRA v3" while base E4B actually
served (a truthfulness break, and the LoRA is the whole Well-Tuned story). Fix: `_zerogpu()` now
prefers `llm_zerogpu_lora` when `CHIEF_ENGINEER_LORA_REPO` is set (read dynamically). One-line
router change; base path unchanged.

**Still flag for the deploy/inspect pass (fine-tune agent's domain, NOT touched):**
- `core/llm_zerogpu_lora.py` caches `LORA_REPO` at module import, and `app.py` imports it (line
  ~83) *before* the startup `_apply_model_choice` (line ~117) sets the env var. So the adapter
  actually loaded on the Space depends on init order — verify the served adapter matches the
  dropdown after deploy (check the status line says the LoRA model, not base).
- **Modal API (remote):** wired by the fine-tune agent (`_modal_api()` + HTTP client in
  `llm.py::chat_json`, `MODAL_API_URL` → `modal_serve.py`).

## Addendum 3 — backend must be dynamic, not a frozen Space var (2026-06-14)

Kyle's catch: switching ZeroGPU ↔ Modal can't be a static Space var. `core/llm.py` read
`BACKEND` once at import and routed on that cached value, while the dropdown's
`_apply_model_choice` only set the env var at runtime (its `importlib.reload(__import__(
"core.llm"))` reloaded the *package*, not the submodule, so it never updated `BACKEND`). Result:
a fixed `CHIEF_ENGINEER_BACKEND` Space var would freeze the switch — selecting Modal would keep
serving ZeroGPU. Fix: added `llm._backend()` that reads the env **dynamically** each call;
`_zerogpu()` and `_modal_api()` now use it. The Space var is now just the *initial default*, and
the in-app switch takes effect on the next call. Removed the now-redundant package reload from
`_apply_model_choice`. Verified: runtime set of `CHIEF_ENGINEER_BACKEND` flips `_backend()` /
`_modal_api()` correctly; build + tests green.

Remaining (fine-tune agent's domain): `core/llm_zerogpu_lora.py` caches `LORA_REPO` and the
loaded `_model` at import/first-load, so live-switching **v2 ↔ v3** (both are LoRA adapters)
won't reload the adapter without a small change there. ZeroGPU↔Modal↔base switching is fixed;
v2↔v3 live re-swap is the one remaining gap. The v3 default loads correctly if `LORA_REPO` is
set before the adapter backend first loads (verify on the deployed Space via the status line).

## Addendum 4 — visual review via headless render (2026-06-14)

The remote sandbox can't reach the live Space (egress allowlist blocks node.microfactory.space
and *.hf.space), so I rendered the *deployed code* locally with headless Chromium and screenshotted
every tab + the build flow. Findings:

**CRITICAL (fixed + pushed):** BUILD → SLICE never completed. The scroll-to-top JS was chained
*between* `build_start` and `build_job` (`.then(None,None,None,js=...)`), which blocked `build_job`
from firing — the SLICE tab showed the loader forever and never revealed the read/settings. NOT an
env, model-switcher, or Modal issue. Fixed by firing the scroll as a separate parallel click. The
deployed Space has this bug until the next `make deploy`.

**Fixed (copy):** stale tab names (Studio/Build → BUILD/SLICE) in the load warnings and the PRINT
empty-state.

**Verified working (headless):** tabs BUILD/SLICE/PRINT/REVIEW; top-right action bar + persistent
Reset on each; 3-column env band (readout+RANDOMIZE+OVERRIDE popup | build-plate+notes | material+
MODEL INFO callout); custom blank-viewer placeholder toggling to the live 3D model on part load;
the custom step-checklist loader; full SLICE read (cross-section + vertical layer slider, motion
preview, precedent evaluation, O'Brien reasoning, predicted risks, proposed settings + g-code,
Engineer's-Read/Second-Opinion toggle); PRINT run controls; REVIEW ledger + collapsible mesh.
End-to-end offline pipeline (generate/benchy → SLICE → PRINT → log real outcome) passes.

**Open visual issues (noted, NOT fixed — fine-tune agent owns the header CSS, actively tuning):**
- **Header collision:** the model switcher is lifted onto the command bar via `margin:-46px ... 280px`;
  at 1600px the dropdown overlaps the "BUILD SMALL · BACKYARD AI" tag and the clock. Needs the
  command-bar right content moved left or the dropdown given dedicated space.
- **Redundant label:** "ENVIRONMENT (SIMULATED)" appears twice (rule header + readout text).
- **Minor:** the loaded gr.Model3D keeps Gradio's small toolbar chrome (undo/download) — inherent to
  the live widget; empty state is custom.
- build-08 background preload of slicer layer images.
- review-04 surface the full printable config/environment in Review.
- print-09 model a print-time/duration estimate per iteration.
- print-08 carry dispute/override state into Print for an explicit "prediction held after override".
- studio-01 decide whether to rename the BUILD tab to SLICE (and ripple to RUNBOOK/video).
- studio-17 clarify and address the "field lock".
- General empty-state and gap polish that only a rendered review can catch (I cannot see the
  rendered Gradio layout from here — all checks were import/test/E2E + emoji scan).

---

## 2026-06-14 — Visual polish + GGUF distribution session

This pass was driven by live screenshots and Playwright (CDP) verification; every change
landed via `deploy_preflight.py --push` so the HF Space and the source tree never drift.

### Tab rename: workflow is now `LOAD → SLICE → PRINT → REVIEW`
- `app.py:584` — first tab label `BUILD` → `LOAD` (the tab `id="studio"` stays so existing
  `gr.Tabs(selected=...)` calls keep working). The button on `LOAD` is now `SLICE` (clicking
  it slices the part and jumps to the SLICE tab — same destination, clearer verb).
- Intro copy under PART rewritten: "Load the part, set the material and the room, then
  **SLICE** to read the engineer's pre-flight check."

### Action bar absorbs ENVIRONMENT (one row at the top of LOAD)
- ENVIRONMENT readout + `RANDOMIZE` + `OVERRIDE` (left) and `RESET` + `SLICE` (right) all on
  the same `.ce-actionbar.ce-envbar` row. The 3-column band underneath collapses to 2 cols
  (`BUILD-PLATE POSITION` | `MATERIAL`) since the env stuff is gone from there.
- `OVERRIDE` is now a popup trigger — see below.

### OVERRIDE → modal popup (not an inline band)
- New `.ce-popup` / `.ce-popup-backdrop` CSS in `core/theme.py` — fixed-position card with
  orange LCARS border, dark backdrop, `✕` close in the title row.
- Wiring: every `[data-popup-trigger="X"]` toggles the matching `[data-popup="X"]` +
  backdrop via JS in `CLOCK_JS`. Backdrop click and close button both dismiss. JS re-runs on
  a 1.5 s interval so popups added after first render still get wired.
- The override popup contains AMBIENT °C + HUMIDITY %RH (was previously the OVERRIDE
  ENVIRONMENT column in the BUILD tab).

### Model switcher: borderless inside, one outer border
- Old: orange `1px solid` borders applied to `.wrap` + `.secondary-wrap` + `.container` +
  `label > div` (Gradio nests all four) → 4 stacked outlines.
- New: every inner element gets `border:none`; **only** `.ce-modeldd` has the border. Focus
  state is a `box-shadow` ring (no second border).
- Model switcher row sits BELOW the LCARS command bar (was lifted into it via negative
  margin, which overlapped "BUILD SMALL · BACKYARD AI" and the clock).

### Beefed loader (SLICE feels alive while the model thinks)
- `loader(text, stages=[...])` in `core/theme.py` now renders: title + glowing scan bar +
  cycling stages list (`reading the part geometry` → `slicing cross-sections` →
  `querying precedent ledger` → `engineer proposing settings` → `qa inspector reviewing`).
  CSS classes: `.ce-loader`, `.ce-loader-bar`, `.ce-loader-stages > div.active|.done`.
- JS in `CLOCK_JS` walks `[data-stages="cycle"]` every 1.2 s, marking prior as `.done` and
  the current as `.active` with check/arrow glyphs.
- `min-height:220px` so the loader actually fills space (the old 14px-padded version felt
  like nothing happened).

### PART row top-aligned + matching mesh-source buttons
- `.ce-part-row { align-items:flex-start }` so the dropzone (right) and viewer (left) start
  at the same y — dropzone no longer floats centered against a tall viewer.
- `QUICK-LOAD BENCHY` and `GENERATE A PRIMITIVE` (accordion-as-pill via `.ce-accordion-pill`)
  share the `.ce-mesh-source` class — same width (100%), same padding (12×16), same
  min-height (44px). The accordion expand arrow is hidden so the collapsed header is
  visually indistinguishable from the button.

### `CLOCK_JS` finally attached
- It was defined in `core/theme.py` but never imported — the LCARS clock was static and
  popups didn't open. Fix: import `CLOCK_JS` in `app.py` and add
  `demo.load(None, None, None, js=CLOCK_JS)` alongside the existing sensor-randomize load.

### GGUF distribution — all three variants live on HF Hub
- `learn/finetune/gguf_pipeline_modal.py` gained `upload_to_hub` (CPU function, attaches
  `HF_TOKEN` Modal secret, strips whitespace from the token, creates the repo if missing)
  + a `--upload <owner>/<repo>` flag on `main`, + a separate `::upload_only` entrypoint
  for pushing existing GGUFs from the volume.
- Result — `kylebrodeur/microfactory-node-gguf` now holds 5.0 GB each of v1
  (`microfactory-node.gguf`), v2 (`microfactory-node-v2.gguf`), v3-qat
  (`microfactory-node-v3-qat.gguf`).
- README's local-run section now documents the Ollama Modelfile flow; `SERVING.md` has the
  full pipeline notes including the gotchas (`::main` requirement, token whitespace,
  background-cwd race).

### Verification
- Playwright smoke at `/tmp/smoke_test.py` (CDP, headless, full-page screenshots) covers:
  load, button labels (SLICE present, no stray BUILD JOB), 3/2-col layout, OVERRIDE
  popup open+close, model dropdown selection, command-bar status, emoji scan, JS errors,
  loader CSS presence. Screenshots saved per stage at `/tmp/microfactory_*.png`.
- `deploy_preflight.py --push` after every commit — Space rebuild typically 1–2 min.

### Commit trail (this session)
```
677054b fix: model switcher dropdown nested borders
a9decaa style: top-align PART row + match QUICK-LOAD/GENERATE pill styles + padding
d70e0e8 rename: BUILD tab → LOAD
ae278ba feat: merge ENVIRONMENT row into action bar → 2-col below
efadbc0 fix: drop model switcher row below LCARS header (was overlapping)
733ac94 fix: attach CLOCK_JS to demo.load (wires popups, clock, loader stages)
432280b feat: SLICE button rename, beefed loader with cycling stages
2d1b472 refactor: BUILD tab — header bake, 3-col, OVERRIDE popup, dropzone-top
```

---

## 2026-06-14 — ollama.com publishing

Distribution side-quest: all four GGUF variants now live on the public Ollama
registry at [`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur), in
addition to the canonical HF Hub copies. Same blobs, two discovery paths.

### What's published

| Tag | Quant | Pull command |
|---|---|---|
| [`kylebrodeur/microfactory-node-v3-qat`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat) *(recommended)* | q4_k_m | `ollama run kylebrodeur/microfactory-node-v3-qat` |
| [`kylebrodeur/microfactory-node-v3-qat:q4_0`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0) | q4_0 | `ollama run kylebrodeur/microfactory-node-v3-qat:q4_0` |
| [`kylebrodeur/microfactory-node-v2`](https://ollama.com/kylebrodeur/microfactory-node-v2) | q4_k_m | `ollama run kylebrodeur/microfactory-node-v2` |
| [`kylebrodeur/microfactory-node`](https://ollama.com/kylebrodeur/microfactory-node) | q4_k_m | `ollama run kylebrodeur/microfactory-node` |

The q4_0 variant is new — the QAT model was trained with simulated 4-bit
quantization targeting Google's `q4_0` quant, so it reconstructs better there
than at `q4_k_m`. Both quants are kept on HF Hub side-by-side:
[`microfactory-node-v3-qat.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat.gguf)
and
[`microfactory-node-v3-qat-q4_0.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat-q4_0.gguf).

### Pipeline tweaks

- `learn/finetune/gguf_pipeline_modal.py` — `upload_only` gained `--as-name` so
  the HF filename can differ from the volume filename (used to publish q4_0
  without overwriting q4_k_m).
- HF GGUF repo now carries `template` (Gemma 4 Go template), `system` (Chief
  Engineer persona), `params` (sampling JSON), and an Ollama-aware `README.md`
  with the registry tags inline. Together they let `ollama run hf.co/...`
  Just Work with no `Modelfile`.

### Docs

Full walkthrough — one-time SSH-key setup, the `ollama pull → ollama cp →
ollama push` flow per variant, the seven gotchas hit and fixed — lives in
[`learn/finetune/OLLAMA_PUBLISHING.md`](../../learn/finetune/OLLAMA_PUBLISHING.md).

Updated callers:
- Project [`README.md`](../../README.md) — "Run the fine-tuned Chief Engineer locally"
  section now lists all four ollama.com tags + the q4_0 HF link.
- [`learn/finetune/SERVING.md`](../../learn/finetune/SERVING.md) §1 — dual table
  (ollama.com tags + HF Hub files) replacing the old HF-only table.
- HF GGUF model card — [`kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf)
  shows all four variants + both pull paths inline.

## Addendum — final UI polish batch + live deploy verification (2026-06-14)

After the docs/Ollama batch landed, the remaining UI asks from the session were:
tab icons, arrow buttons, a usable layer scrubber, earlier slicer/preview reveal,
idempotent Second Opinion with progress, PRINT tab density + plan card + outcome
up top + progressive iteration reveal, and a settings-aware virtual print preview.
All are now implemented and the Space was deploy-checked live.

### Theme / global
- Tab icons added via CSS-only `:nth-of-type` on `.tab-nav button` (inbox / layers /
  printer / clipboard-check), no emoji, no Gradio escaping risk.
- Primary action buttons get a right-side SVG arrow via `.ce-icon-arrow-after`
  (LOAD → SLICE, SLICE → PRINT, PRINT → PRINT, REVIEW → REFRESH).
- New horizontal layer scrubber `.ce-hslider` (full-width, tick marks, square thumb,
  hides number field) replaces the broken vertical slider.
- Virtual print preview `.ce-vp` framed larger; its canvas HUD now shows the layer
  height from the actual `PrintSettings`.
- `.ce-mini-loader` CSS added for in-place Second Opinion loading state.

### LOAD tab
- ENVIRONMENT, POSITION, and MATERIAL now share the top envbar row with
  RANDOMIZE / OVERRIDE / RESET / SLICE on the far right.
- POSITION and MATERIAL use compact inline labels and smaller pills; each pill has
  an SVG icon (target/edge/corner for position, droplet for materials).
- The "edges/corners run cooler" helper text moved into a small info-icon tooltip
  on the POSITION label.
- `MODEL INFO` moved up to the header row as just an `info` icon (no text).
- NOTES (OPTIONAL) moved to the right-hand PART actions column, under the mesh
  source buttons, closing the empty gap in the left viewer column.
- Vertical spacing between the envbar and the PART card tightened.

### SLICE tab
- Slicer image + virtual print preview + horizontal scrubber render immediately on
  SLICE click; only "THE READ" section shows the loader while the model runs.
- Second Opinion is idempotent: computed once per build and cached in `state`; a
  mini-loader displays while La Forge reviews the plan.
- Virtual print preview caption shows the actual layer height from the plan.

### PRINT tab
- Restructured with an envbar-style row: job readout | iteration count chip | VARY button.
- New "THE PLAN" card shows the Engineer's proposed settings, Spine notes, and
  La Forge stance before the run.
- Iterations slider is now `.ce-hslider` with inline explanation of 1/4/8/16.
- Hidden VARY override panel lets the operator defy the Engineer's plan with
  explicit warning callout; logs operator override to field + deliberation logs.
- Results order changed: OUTCOME (SIMULATED RESULT + LA FORGE VERDICT) at the top,
  then headline, then full-width QUALITY PER ITERATION chart, then ITERATION LOG,
  then LEARNED POLICY CELL, then LOG A REAL PRINT.
- `run_print` is now a generator: it yields after each iteration so the chart, log,
  and policy cell fill in live; per-iteration timing appears next to each row.

### Reset
- `RESET TO BASELINE` now also clears the loaded part, hides the SLICE/PRINT result
  groups, and returns the active tab to LOAD.

### Validation
- `python3 -m py_compile app.py core/theme.py core/widgets.py core/viewer.py
  learn/loop.py core/models.py core/chief_engineer.py core/spine.py core/prompts.py` passes.
- `uv run python test_core.py` green.
- `uv run python -c "import app; app.build()"` green.
- Live Space deploy-check and smoke test completed by user.

### Removed
- GIF export for virtual print preview — the user decided the in-app canvas motion
  preview is sufficient; the EXPORT GIF button was removed (helper deleted from
  widgets; CSS and gitignore cleaned up).
- Legacy `MODEL INFO` text callout under MATERIAL; replaced by the header icon.
