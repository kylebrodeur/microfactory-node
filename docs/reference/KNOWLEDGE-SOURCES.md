# Knowledge Sources — Chief Engineer

Catalog of sources for the system's knowledge basis (RAG + future fine-tuning), evaluated for
AI-ingestion readiness. Provided by Kyle; more to come in the local dev environment.

> **Doctrine reminder:** we are NOT hardcoding a big lesson corpus. The 12 curated seeds in
> `data/seed_lessons.jsonl` only bootstrap the demo. Real depth comes from (a) earned lessons the
> system writes as it runs, and (b) distilling the sources below into `LessonEntry` rows. The
> ledger's retrieval (`ledger.py`) is the ingestion point — anything that can be reduced to
> `{material, geometry_type, env, outcome, lesson}` drops straight in. Heavier sources feed a
> post-hackathon fine-tune, named as frontier.

---

## Category 1 — Pre-formatted ML datasets (training-ready)

| Source | Format / size | Use | Readiness |
|--------|---------------|-----|-----------|
| `ablam/gcode` (HF) | Parquet, 100M–1B rows, >6GB raw G-code from Printables | Train LLM on G-code / slicer-parameter prediction | High (training, not RAG) |
| `3DTimeDataset/3DTime` (HF) | Parquet/CSV time-series regression | Map mesh props + infill + slicing → print duration (supervised) | High |

## Category 2 — Academic literature & multimodal (RAG + vision)

| Source | Form | Use | Readiness |
|--------|------|-----|-----------|
| 3D-ADAM (arXiv PDF + dataset) | PDF text; 14,120 image/point-cloud scans, 27,346 defect masks (warping, under-extrusion, cracks) | RAG on defect taxonomy; CV training on defects | PDF→RAG high; dataset is a separate download for vision |

## Category 3 — Raw code & config (code-LLM + RAG)

| Source | Form | Use |
|--------|------|-----|
| Marlin `Configuration.h` / `Configuration_adv.h` | C++ headers | Hardware/thermal/PID/kinematics knowledge |
| Voron-2 Klipper `Voron2_Octopus_Config.cfg` | Klipper cfg | CoreXY kinematics, TMC2209 UART settings |
| PrusaSlicer profiles `Anycubic.ini`* | INI key-value | Printer/material profiles, start/end G-code |

\* **License note:** ingest *profile data* (INI values) for knowledge; do **not** import or link
OrcaSlicer/PrusaSlicer *code* (AGPL-3.0). Keep the app MIT-clean.

## Category 4 — Docs & community discussion (RAG text)

| Source | Use |
|--------|-----|
| Klipper `Overview.md`, DuetSoftwareFramework `README.md` | High-level overviews, API/CLI, socket config |
| RatOS release changelogs | Version-aware / temporal RAG (features, macros) |
| Cura-OctoPrintPlugin issue #227 | Troubleshooting RAG (Cura ↔ Moonraker ↔ Mainsail) |

---

## Recommended additional acquisitions (from the sources, verify independently)

1. External 3D-anomaly datasets referenced by 3D-ADAM: **MVTec3D-AD**, **Real3D-AD**, **PAD**.
2. Scrape GitHub for Klipper `printer.cfg` and Marlin `Configuration.h` (firmware knowledge).
3. **Thingi10K** STL corpus — pair with G-code for multimodal training.
4. Klipper Discourse / r/3Dprinting / r/klippers + issue trackers — best format for teaching
   error→fix reasoning.

---

## Ingestion plan (how these become Chief Engineer knowledge)

- **RAG-now (cheap):** chunk Categories 3–4 + the 3D-ADAM defect taxonomy into short, retrievable
  notes. Where a note maps to a print condition, distill it into a `LessonEntry` so it surfaces
  through the same retrieval the demo already uses.
- **Earned lessons:** every real print the user runs on their Ender writes an `earned` lesson —
  the highest-value, in-distribution data.
- **Fine-tune (frontier, post-hackathon):** the accumulated `lessons.jsonl` + `ablam/gcode` +
  `3DTime` become training data. Use Modal credits ($500 on hand + $250 participant) / HF credits
  for the run. Named as frontier; not in-window.

## ⚑ Modal Ingestion App — ACTIVE (Modal bonus track)

**`ingest/modal_app.py`** is now a full Modal ingestion pipeline that fetches, parses, and
distills 3D-printing knowledge from 24 documentation sources + 2 HF datasets into the three
lanes the Chief Engineer consumes. Built following the vetted Modal patterns from the
`spanish-language-tutor` production pipeline (Volume caching, Secrets, idempotent/resumable).

### Registered Sources (24 total)

| Category | Count | Sources |
|----------|-------|---------|
| **firmware** | 8 | Moonraker, Mainsail, TMCStepper, Klipper thermistor docs, TMC26X, Arduino-L6470, U8glib, PlatformIO |
| **calibration** | 8 | RepRap Calibration, PID Tuning, Linear Advance, Laser/Spindle, Probes, G-code Actions, Jerk Motion, Junction Deviation |
| **profiles** | 5 | PrusaSlicer Anycubic profiles, Hartrusion config, Sainsmart TPU specs, RatOS install/upgrade |
| **research** | 3 | BCN3D Moveo, 3DTime dataloader, Klipper linear analysis |

### HF Dataset Mappers (2)

| Dataset | HF ID | Lanes |
|---------|-------|-------|
| 3D-ADAM | `pmchard/3D-ADAM` | B (defect→lesson), C (if settings present) |
| G-code corpus | `ablam/gcode` | A (M104/M140 temps, retraction) |

### How to run

```bash
# Install deps (local-only, not a Space dep)
uv pip install modal datasets
modal token set

# All documentation sources
modal run ingest/modal_app.py

# Single source or category
modal run ingest/modal_app.py --source klipper-thermistors
modal run ingest/modal_app.py --category calibration

# HF datasets
modal run ingest/modal_app.py --dataset 3d-adam --limit 2000
modal run ingest/modal_app.py --dataset gcode --limit 5000
```

### Output contract

- **Lane A** → `data/references.jsonl` (appended) — material baselines, max temps, PID/PA values
- **Lane B** → `data/_modal_candidate_lessons.jsonl` (REVIEW before ledger) — extracted lessons
- **Lane C** → `sim/calibration/observations.modal.jsonl` — calibration observations (only when settings present)

### Reference patterns applied (from spanish-language-tutor)

- ✅ `modal.Volume` for caching fetched content (idempotent/resumable)
- ✅ `modal.Secret` for HF_TOKEN (never inline tokens)
- ✅ `image.add_local_file("core/models.py")` — shares enums into the image
- ✅ CPU-only parsing (no GPU needed)
- ✅ No live Space↔Modal calling (ingestion stays offline/artifact-based)
- ✅ Lane B to REVIEW file (honesty gate)

### Acceptance status

- [x] Modal app built with 24 sources + 2 HF mappers
- [x] All parsers tested locally (Prusa INI, Klipper CFG, Marlin H, web docs)
- [x] `make test` green — nothing in demo path imports modal
- [ ] Modal run with real artifacts (needs `modal token set` + `modal run`)
- [ ] Lane-B lessons reviewed before entering ledger
- [ ] Lane-C calibration run
- [ ] Commit on feature branch with row counts
