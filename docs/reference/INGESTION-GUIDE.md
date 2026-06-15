# Knowledge ingestion — what to do (Kyle's track)

The pipeline is **built and tested**; what it needs is **your sources**. This is
the work you can do locally in parallel. Two kinds of knowledge feed the model,
by very different paths — don't mix them up.

## The two lanes

| Lane | What | Where it lands | How the model uses it |
|---|---|---|---|
| **A — Reference facts** | Slicer/firmware configs (material temps, limits) | `data/references.jsonl` | Injected into the prompt as material baselines (`reference_block()`), optional/removable |
| **B — Candidate lessons** | Outcome-bearing observations ("ABS warped in a cool room because…") | the ledger (`data/lessons.jsonl`, `source="ingested"`) | Retrieved as precedent, exactly like seed/earned lessons |
| **C — Calibration observations** | Print records that include the **settings used** + room + real outcome (HF/GH print datasets, 3D-ADAM, etc.) | `sim/calibration/observations.*.jsonl` | Fed to the `tune-simulator` skill to fit `sim/outcome.py` to reality → "calibrated to data" |

**Lane C is the key insight (6/10):** if a source row carries the actual
**settings** (`nozzle_temp, bed_temp, retraction_mm, fan_pct, first_layer_fan_pct`)
alongside material/geometry/env/outcome (+ optional 0–1 `quality`), it can calibrate
the simulator — which Lane B can't, because the ledger deliberately stores no
settings. So the same HF/GH ingestion sources that feed Lanes A/B can *also* power
the sim-calibration stretch. One row, schema (one JSON object per line):
```json
{"material":"PETG","geometry_type":"bridge","env_temp":29,"env_humidity":62,
 "nozzle_temp":235,"bed_temp":80,"retraction_mm":4,"fan_pct":40,
 "first_layer_fan_pct":0,"outcome":"failed_sag","quality":0.45}
```
Then: `uv run python -m sim.calibrate --data sim/calibration/observations.jsonl`
(or invoke the `tune-simulator` skill). Same honesty rule — real records only.

**Honesty rule:** Lane B entries are *lessons the system claims to know*. Only
ingest ones grounded in a real source (a doc, a dataset, your own prints). Don't
fabricate lessons to pad the ledger — it poisons the whole "honest compounding"
story. A small, real ledger beats a big, invented one.

## Do it now — the 10-minute version

```bash
cd chief-engineer
# 1. drop your files in a folder (or replace ingest/samples/*):
#    *.ini (Prusa filament), *.cfg (Klipper), *.h / *config*.txt (Marlin),
#    research_lessons.jsonl (one JSON object per line — schema below)
uv run python -m ingest.run --dir /path/to/your/configs
# → writes references + appends ingested lessons; prints counts
make test          # confirm nothing broke
make run           # the cockpit now cites your ingested material baselines
```

### Lane A source formats (parsed deterministically — no LLM)
- **Prusa** `*.ini`: `nozzle_temperature`, `bed_temperature`, … per filament.
- **Klipper** `*.cfg`: `[extruder] max_temp`, etc.
- **Marlin** `*.h`: `#define HEATER_0_MAXTEMP`, bed maxtemp, etc.
Parsers live in `ingest/distill.py` (`parse_prusa_ini` / `parse_klipper_cfg` /
`parse_marlin_config`). Add a new format = add one parser there.

### Lane B lesson schema (`research_lessons.jsonl`, one per line)
```json
{"job_id":"ingest-001","material":"ABS","geometry_type":"warping",
 "env_temp":20.0,"env_humidity":40.0,"outcome":"failed_sag",
 "lesson":"ABS corners lifted in a cool, open room — needs an enclosure + 100-110C bed.",
 "source":"ingested","timestamp":"2026-05-22T09:00:00Z"}
```
`material` ∈ the app's MATERIALS, `geometry_type` ∈ GEOMETRY_TYPES,
`outcome` ∈ OUTCOMES. Keep `lesson` to 1–2 physical sentences (that's what the
model reads).

## Where the sources come from (your call)
- **Best:** your own Ender prints — real, defensible, on-brand. Even 5–10.
- Public slicer/firmware config repos (Prusa, Klipper, Marlin) → Lane A.
- 3D-printing defect datasets (e.g. 3D-ADAM) → Lane B, distilled to lessons.
- `docs/KNOWLEDGE-SOURCES.md` is the running catalog — add what you find.

## Heavy datasets / Modal (the bonus, optional)
`ingest/modal_app.py` is a **clearly-marked stub** for large-scale ingestion on
Modal (the MCP-hackathon code you have locally would slot in here → possible
**Modal bonus**). This is the bigger lift; it's **not** required for the demo —
the local `ingest.run` path fully covers the recording. Decide after the baseline
whether there's time. The stub keeps the wiring obvious without pulling Modal
into the Space requirements.

## What "done" looks like for the recording
- Lane A: the cockpit shows real ingested material baselines feeding a
  recommendation (optional, nice-to-have).
- Lane B: a couple of *real* ingested lessons show up as retrieved precedent →
  reinforces "knowledge compounds from outside sources, not just this session."
- If you run out of time: the 12 seed lessons already carry the story. Ingestion
  is additive, never blocking.
