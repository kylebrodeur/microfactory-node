# Ingestion work order (run this in a separate local session)

A self-contained brief for ingesting your real knowledge sources into the Chief
Engineer. Hand the **kickoff prompt** at the bottom to a fresh Claude Code session
on your machine (where the sources live). Detail/reference: `INGESTION-GUIDE.md`.

## Goal

Turn your real sources into the three knowledge lanes the app consumes:
- **Lane A — reference facts** (slicer/firmware configs → `data/references.jsonl`),
  injected into the prompt as material baselines.
- **Lane B — candidate lessons** (outcome-bearing observations → the ledger as
  `source="ingested"`), retrieved as precedent like seed/earned lessons.
- **Lane C — calibration observations** (print records that include the **settings
  used** + room + real outcome → `sim/calibration/observations.jsonl`) → feeds the
  `tune-simulator` skill to calibrate `sim/outcome.py` to real data. Emit a Lane-C
  row whenever a source has the settings (Lane B can't calibrate — it stores no
  settings). Schema + details in `INGESTION-GUIDE.md` (Lane C).

**Honesty rule (load-bearing):** only ingest Lane-B lessons grounded in a real
source (a doc, a dataset, your own prints). A small real ledger beats a big
invented one — fabricated lessons poison the whole "honest compounding" story.

## Docs to review first (in order)

1. `docs/INGESTION-GUIDE.md` — the two lanes, formats, the 10-minute path.
2. `core/models.py` — `LessonEntry`, `MATERIALS`, `GEOMETRY_TYPES`, `OUTCOMES`
   (the exact enums your Lane-B rows must use).
3. `ingest/distill.py` — the deterministic parsers (`parse_prusa_ini`,
   `parse_klipper_cfg`, `parse_marlin_config`) and `ingest_candidate_lessons`.
   Add a new parser here if a source format isn't covered.
4. `ingest/run.py` — the CLI entrypoint and what file globs it scans.
5. `docs/KNOWLEDGE-SOURCES.md` — the running catalog; add what you ingest.

## Steps

1. Point the distiller at your sources (or drop them in `ingest/samples/`):
   ```bash
   cd chief-engineer
   uv run python -m ingest.run --dir /path/to/your/sources
   ```
   Lane A formats: `*.ini` (Prusa), `*.cfg` (Klipper), `*.h`/`*config*.txt`
   (Marlin). Lane B: `research_lessons.jsonl` (one JSON object per line; schema in
   the guide, enums from `models.py`).
2. **Eyeball the result for honesty + physics:** open `data/references.jsonl` and
   the new `source="ingested"` rows in `data/lessons.jsonl`. Each lesson should be
   1–2 physical sentences that are *true* and *directional* (e.g. humid PETG →
   *lower* nozzle, not higher). Drop anything you can't stand behind.
3. `make test` — confirm the schema/invariants still pass.
4. `make run` → drive a job whose material has ingested data; confirm the
   reference baselines feed the recommendation and an ingested lesson can appear
   as retrieved precedent.
5. Commit on the feature branch with counts in the message
   (`branch claude/microfactory-gradio-hackathon-9e81fh`).

## Optional — Modal (the bonus, only if time)

`ingest/modal_app.py` is a marked stub for large-scale ingestion on Modal. If you
drop your MCP-hackathon Modal code in here it may qualify for the **Modal bonus** —
see `MODAL-WORKORDER.md` (its kickoff prompt + the vetted "Reference patterns":
`modal.Volume` caching, `modal.Secret`, sharing the enums into the image). NOT
required for the demo — the local `ingest.run` path fully covers the recording.

## Acceptance
- [x] `data/references.jsonl` has real material baselines (Lane A): 20 facts from Prusa INI, Klipper CFG, Marlin config
- [x] 13 real `source="ingested"` lessons in the ledger (Lane B): 3 original + 10 added (PETG stringing/bridge, PLA overhang/vase, ABS overhang, TPU stringing, PETG adhesion)
- [x] `make test` green — all 10 core tests pass
- [x] Every ingested lesson is true, directional, 1-2 sentences, using exact enums
- [ ] `make run` to confirm ingested baselines/lessons feed a recommendation (needs Gradio app running)
- [ ] Commit on feature branch with counts

---

## KICKOFF PROMPT (paste into a fresh local Claude Code session)

```
You're working in the chief-engineer/ project on branch
claude/microfactory-gradio-hackathon-9e81fh. Task: ingest my real 3D-printing
knowledge sources into the app's two lanes. Do NOT touch app.py, core/, or the
UI — this is data ingestion only.

1. Read these first: docs/INGESTION-WORKORDER.md, docs/INGESTION-GUIDE.md,
   core/models.py (LessonEntry + the MATERIALS/GEOMETRY_TYPES/OUTCOMES enums),
   ingest/distill.py, ingest/run.py.
2. My sources are at: <PATH — I'll fill this in>. Tell me what formats you see and
   which lane each maps to (A = slicer/firmware configs -> references; B =
   outcome-bearing lessons -> ledger; C = records WITH settings+outcome ->
   sim/calibration/observations.jsonl for sim calibration). If a row carries the
   actual settings, emit a Lane-C observation too. If a format isn't covered by an
   existing parser in ingest/distill.py, add a small parser there (deterministic, no LLM).
3. Run `uv run python -m ingest.run --dir <PATH>`. Report the counts.
4. HONESTY GATE: show me every Lane-B lesson you're about to add. Each must be a
   true, directional, 1-2 sentence physical lesson using the exact enums. Drop or
   flag anything questionable — do not invent lessons to pad the ledger.
5. `make test` must stay green. Then `make run` and confirm an ingested baseline/
   lesson actually feeds a recommendation.
6. Update docs/KNOWLEDGE-SOURCES.md with what you ingested, and commit on the
   feature branch with the counts in the message. Do not push a PR.
```
