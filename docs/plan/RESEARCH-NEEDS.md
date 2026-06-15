# Research needs — the data that would actually move the needle

What the first ingestion + calibration pass taught us we're missing, in priority
order, plus a kickoff prompt to go get it. Pairs with `MODAL-WORKORDER.md` (how to
run ingestion) and `../sim/calibration/CALIBRATION-REPORT.md` (why the current data
can't tune the simulator).

## The one thing that matters most
**Outcome-diverse print logs that carry the full settings AND the room.** The
calibration is bottlenecked on data, not on the simulator. We need rows that have:
`material, geometry, nozzle, bed, fan, retraction, speed, ambient temp, humidity →
real outcome (success / sag / stringing / …)`, across **both successes and
failures**. Everything else below is in service of getting that.

## Prioritized gaps (what to source, and why)
1. **Failure data with settings (highest value).** 3DTime is all-success; the model
   and the simulator both need failures with the settings that caused them. Targets:
   the FDM Error Detection repo (have — get the rest of it), Obico/Spaghetti-Detective
   failure datasets, r/FixMyPrint posts with settings, OctoPrint timelapse+log dumps.
2. **Reliable fan / retraction / speed extraction.** Today fan defaults to 0 (M106
   missing from headers → 178/260 rows wrong). Parse `M106` across the file (not just
   header), retraction from `G1 E-` moves, speed from feedrates, and the slicer footer
   comment block (PrusaSlicer/Orca write the real `fan_speed`, `retract_length` there).
3. **Real geometry labels.** Replace the bbox heuristic with geometry inferred from
   G-code moves (long same-Z X/Y runs = bridge; outward-stepping perimeters = overhang)
   or from the source CAD/tags. Mislabelled geometry is a second source of false sags.
4. **Ambient temp + humidity at print time.** This is the signal the whole product
   keys on and it's almost never logged. Worth a dedicated hunt: enclosure-sensor
   datasets, maker logs that note room conditions, or our own recorded prints.
5. **Curated material baselines incl. cooling.** Fully parse Prusa/Bambu/Orca filament
   profiles for `fan_pct` + first-layer fan (the curated configs we already trust for
   temps/retraction just didn't carry fan) so `reference_block` can drop the noisy
   bulk fan values it currently excludes.

## Datasets worth trying next (from the deep-dive + this pass)
- **SLICE-100K** (when on HF) — 100K G-code paired with CAD → massive Lane A + C.
- **BambuStudio / Kanrog Klipper configs** — parsers are written; need a 4 GB+ Modal
  instance (they OOM'd the 512 MB run). Lane A: 200+ materials, 150+ board configs.
- **Obico / The Spaghetti Detective** open failure datasets — labelled failures.
- A small **self-recorded set**: 15–20 of your own prints with the room noted — tiny
  but it's the only source with trustworthy humidity, and it's honest ground truth.

## What we learned from the bad data (keep this — it's Field-Notes material)
- **Quantity ≠ quality.** 1,304 ingested facts, but every *correct* prompt baseline
  came from 4 tiny curated config files — not the 825 MB dataset. We now prefer curated
  sources and keep the bulk corpus as data, not prompt input.
- **A single unparsed field (`fan→0`) silently flipped 112 predictions** and would have
  corrupted the simulator had we tuned to it blind. The calibration harness caught it —
  it doubles as a data-quality detector.
- **The simulator is right where the data is clean** (61/61 sag recall). The lesson is
  to fix inputs before touching constants.
- **Honest-by-design held under our own results.** We reported 34.2% and *why we
  won't tune to it*, instead of manufacturing a calibrated-looking win. Same rule the
  product runs on, applied to ourselves.

---

## KICKOFF PROMPT — next data-acquisition Modal run (paste into a fresh local session)

```
You're in chief-engineer/ on branch claude/microfactory-gradio-hackathon-9e81fh.
Goal: get OUTCOME-DIVERSE print data with full settings, to make the simulator
tunable. Do NOT touch app.py, core/, or the UI. Read first: docs/RESEARCH-NEEDS.md,
docs/MODAL-WORKORDER.md (Reference patterns — Volume/Secret/enum-sharing),
ingest/modal_app.py (MAPPERS), sim/calibration/CALIBRATION-REPORT.md (why the
current set can't tune), core/models.py (enums).

1. Fix the Lane-C extractor in ingest/modal_app.py FIRST (this is the bottleneck):
   - parse M106 across the whole G-code file, not just the header; if no fan command
     is found, emit fan_pct=null (NOT 0) and skip the row for calibration.
   - parse retraction from G1 E- moves and the PrusaSlicer/Orca footer comment block.
   - infer geometry from G-code moves (long same-Z runs = bridge; stepped perimeters
     = overhang), not the bbox heuristic.
2. Add at least one FAILURE-bearing source with settings (see RESEARCH-NEEDS §1):
   pull the full FDM Error Detection repo, and/or an Obico/Spaghetti failure set.
   Map to Lane C with the real labelled outcome.
3. Re-run on Modal (Volume-cached, CPU, Secret for any token), write
   sim/calibration/observations.modal.jsonl, and REPORT row counts + outcome mix.
   Lane B candidates still go to data/_modal_candidate_lessons.jsonl for review.
4. Re-calibrate: `uv run python -m sim.calibrate --data sim/calibration/observations.modal.jsonl`
   and update sim/calibration/results/ + CALIBRATION-REPORT.md with the new numbers.
   If (and only if) the data is now clean, tune ONE constant at a time with the
   tune-simulator skill; keep make test green.
5. For BambuStudio/Kanrog, request a larger Modal instance (memory=4096) — they OOM at 512MB.
6. Commit on the feature branch with counts. No PR.
```

---

## Capturing live Space interactions (judge / visitor runs)

**Yes, we can — and it's a great data source — but the Space filesystem is ephemeral, so
it needs a Dataset, not a local file.** Anything written to `data/*.jsonl` on the Space is
wiped on every rebuild and never comes back to the repo. The standard Spaces pattern is to
append each interaction to a **HF Dataset** repo.

**Design (isolated, honest, privacy-aware):**
- **Mechanism:** `huggingface_hub.CommitScheduler` pointed at a *separate* dataset repo
  (e.g. `build-small-hackathon/chief-engineer-field-log`), appending one JSONL row per BUILD:
  `{ts, material, geometry(inferred), env(temp/humidity/bed/printer), backend, settings,
  risks, used_fallback, inspector_verdict, simulated_outcome?}`. Flush on a timer; survives restarts.
- **Honesty gate (same as Lane B):** field-log rows are **candidates**, never auto-promoted
  into the curated ledger or the demo. Review before anything earns "lesson" status. The model
  still doesn't grade itself — we log the inputs, the recommendation, and (if the visitor clicks
  *Simulate*) the deterministic outcome.
- **Privacy/consent:** add a one-line UI disclosure ("interactions are logged to improve the
  model"); log only job *config*, never PII. For **uploaded meshes, log derived geometry/metadata
  only — never persist the uploaded file** (it may be someone's IP).
- **Secrets:** needs a write `HF_TOKEN` as a Space secret + the target dataset created.
- **Payoff:** real jobs judges tried = (a) live demo evidence, (b) more calibration/ingestion
  candidates, (c) a second **Sharing-is-Caring** dataset alongside `make trace` and the
  calibration set, (d) Field-Notes material ("here's what people actually asked it").

**Not a record blocker.** It's a small, import-guarded add (≈30 lines in `app.py`, gated on the
secret so local/offline is unaffected). Recommend wiring it *right before judging opens* so the
log captures the judging window — ask before building (it touches `app.py` and adds a UI notice).
