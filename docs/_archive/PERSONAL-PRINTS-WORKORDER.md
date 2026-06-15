# Personal prints work order — ingest Kyle's own Pi run-data + photos

The highest-integrity data the project can have: **your own prints — the settings you
ran and what actually happened.** This is the grandfather's-shop thesis made literal,
and it's exactly the data the simulator calibration is bottlenecked on
(`RESEARCH-NEEDS.md` §1). Run locally (the data lives on your Pi); your IP stays yours.

## What we already used (in hand, done)
- The `.3mf` you sent → real **Prusament PETG @CREALITY** baselines (incl. the fan value
  we were missing). Parsed by `ingest.distill.parse_prusa_config`, committed as
  `ingest/samples/user_creality_petg.config` (settings only — STL geometry NOT committed).
- The **OctoPrint job-history CSV** (514 rows) → parsed by `parse_octoprint_history`. Honest
  yield was small: **512 success / 2 failed, 4 notes** — and `result` = *completion*, not
  quality (one "success" row reads "very stringy"). It produced **one** genuine lesson
  (PETG strings at 240 °C, from your own print). It is NOT calibration data — all-success +
  no fan/retraction/geometry/humidity per row.

## Where the real signal lives on your OctoPi (the actual unlock)
The CSV is just the **index**. The data that moves the system is alongside it:
- **Snapshots → the REAL outcome label.** `/home/pi/.octoprint/data/PrintJobHistory/snapshots`
  — one end-of-print photo per job. This is what reveals stringing/sag/warp that "success"
  (completed) hides. Pair a snapshot to its CSV row by filename/timestamp; the photo (eyeballed
  or via a defect classifier) sets the true outcome.
- **G-code → the REAL settings.** `~/.octoprint/uploads/` (and the filename encodes
  `…_<layer>mm_<temp>C_<material>_<printer>.gcode`). Parse M106/G1 E-/feedrate for the real
  fan / retraction / speed the CSV lacks, and geometry from the moves.
- **Together = real Lane-C with outcome diversity** — the thing the public datasets couldn't
  give us, and the only honest way to un-defer the simulator tune.

> **Access:** the g-code + snapshots live on the OctoPi (behind the OctoPi manager / SSH —
> Kyle to restore access). **Run the ingestion ON the Pi** via the kickoff prompt below — no
> need to upload hundreds of files anywhere; only the derived lane rows leave the Pi. This is a
> **post-record** task (don't reset SSH under recording pressure). To pre-build + test the
> parser ahead of time, the only inputs needed are **one sample `.gcode` (header+footer is
> enough)** and **one snapshot filename**.

## What the Pi data unlocks (the lanes)
- **Lane C — calibration (the prize).** Each record with *settings + real outcome* →
  `sim/calibration/observations.user.jsonl`. Real success+failure with your settings is
  what lets us **tune the simulator honestly** (close the deferred sensitivity gap with
  ground truth, not synthetic). → "calibrated to my own prints."
- **Lane B — lessons.** Your hard-won fixes → `source="ingested"` ledger rows, retrieved
  as precedent. The ledger compounds on *your* history.
- **Lane A — baselines.** Any slicer profiles / configs on the Pi → `data/references.jsonl`.
- **Photos → outcome labels.** Where a record lacks an explicit outcome, the photo supplies
  it (good / sag / stringing / warp) to complete the Lane-C row. Also the raw material for
  the named camera-defect-CV frontier, and authentic video B-roll.

## Honesty + privacy rules (load-bearing)
- **Outcomes come from you/the photo, never the model.** Same gate as all ingestion.
- **Review Lane-B lessons before they enter the ledger** — true, directional, 1–2 sentences.
- **Keep raw records + photos OUT of the public repo/Space.** Commit only derived rows
  (settings/outcomes), not the originals. Log mesh-derived metadata, never the STL.
- **Additive is safe pre-record; re-tuning the simulator is not (without re-verifying).**
  Adding your references/lessons enriches BUILD with no risk to the demo loop. Changing
  `sim/outcome.py` constants can shift the Print-loop fail→clean curves — if you tune,
  re-run `make deploy-check` + confirm a climbing job still climbs (`writeup/02-VIDEO.md`).

## What I need from you to wire the parser
1. **One sample record** — paste a single row and say what it is (OctoPrint print-history
   JSON? Klipper/Moonraker history? Obico? a CSV? a folder of `.gcode` + a log?).
2. **How a photo ties to a print** — filename convention, a column/field, or a separate log.
3. Roughly how outcomes are recorded, if at all (status field? only in the photo?).

With those, I'll add a `parse_*` in `ingest/distill.py` (or a Modal mapper) that emits the
three lanes, then we review Lane B, ingest, and — if you want — calibrate.

---

## KICKOFF PROMPT (paste into a fresh local Claude Code session, on the Pi / where the data is)

```
You're in chief-engineer/ on branch claude/microfactory-gradio-hackathon-9e81fh.
Task: ingest MY OWN 3D-print run-data + photos into the three lanes. Read first:
docs/PERSONAL-PRINTS-WORKORDER.md, docs/INGESTION-GUIDE.md (the lanes),
core/models.py (MATERIALS/GEOMETRY_TYPES/OUTCOMES), ingest/distill.py
(parsers incl. parse_prusa_config), sim/calibration/README.md (Lane-C schema).
Do NOT touch app.py, core/, or the UI.

   OctoPi layout (mine): job index CSV (parse_octoprint_history already handles it),
   snapshots at /home/pi/.octoprint/data/PrintJobHistory/snapshots (one photo per print =
   the REAL outcome), g-code at ~/.octoprint/uploads (real fan/retraction/speed/geometry).
1. Pair each snapshot to its print (filename/timestamp) and to its g-code. The snapshot
   sets the true outcome (eyeball a sample, or classify); the g-code gives real settings.
2. Write a deterministic parser in ingest/distill.py that emits:
   - Lane A refs (any slicer settings) -> data/references.jsonl
   - Lane B lessons (my fixes) -> show me EACH for review before the ledger
   - Lane C observations (settings + real outcome [+ quality]) -> sim/calibration/observations.user.jsonl
   Use the photo to set/confirm the outcome where the record doesn't state it.
3. HONESTY GATE: outcomes come from my records/photos, never invented. Keep raw
   records + photos and STL geometry OUT of git — commit only derived rows.
4. Report counts + outcome mix. Then:
   uv run python -m sim.calibrate --data sim/calibration/observations.user.jsonl
   and update sim/calibration/results/ + CALIBRATION-REPORT.md.
5. ONLY if the data clearly supports it, tune ONE sim constant at a time
   (tune-simulator skill); after ANY tune, run `make test` AND `make deploy-check`
   AND confirm a climbing demo job still climbs. Otherwise leave constants and
   report the finding.
6. Commit derived artifacts on the feature branch with counts. No PR.
```
