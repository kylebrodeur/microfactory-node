# Calibration data — Chief Engineer outcome simulator

Observations used to calibrate `sim/outcome.py` (the one simulated boundary — see
`../../SIMULATION.md`). Each row is a real(ish) print: the **settings used + room +
the real outcome** (+ optional 0–1 `quality`). The `tune-simulator` skill scores the
simulator against these. **Packaged so it can be published as a Hub dataset later
(Sharing is Caring).**

## Files
| File | Rows | What |
|---|---|---|
| `observations.sample.jsonl` | 12 | Hand-crafted template, mixed outcomes — the schema reference. |
| `observations.modal.jsonl` | 260 | Ingested on Modal: 82 from **3DTime** (G-code headers) + 178 from **FDM Error Detection** (known-failure logs). |
| `results/baseline.*.json` | — | Machine-readable metrics (accuracy, MAE, confusion, fan=0 count) per dataset. |
| `results/report.*.txt` | — | Human-readable harness output (confusion + per-row mismatches). |
| `CALIBRATION-REPORT.md` | — | The analysis + the decision (and why we did **not** tune to this data). |

## Schema (one JSON object per line)
```json
{"material":"PLA","geometry_type":"overhang","env_temp":22.0,"env_humidity":45.0,
 "nozzle_temp":210.0,"bed_temp":60.0,"retraction_mm":3.0,"fan_pct":0,
 "first_layer_fan_pct":0,"outcome":"failed_sag","quality":0.7}
```
Enums (`material`/`geometry_type`/`outcome`) match `core/models.py`.

## Provenance & licenses
- **3DTime** (`3DTimeDataset/3DTime`) — published Printables models; outcomes are all
  `success` (they printed). Settings parsed from G-code headers.
- **FDM Error Detection** (`NilsHagenBeyer/3D-printing_recorder`) — G-code + YAML with
  labelled failures (good / stringing / under-extrusion). The source of the real failures.

## ⚠ Known data-quality caveats (read before trusting a calibration)
- **`fan_pct` defaults to 0** when `M106` isn't in the G-code header (178/260 rows).
  This makes overhangs look fan-off and the simulator (correctly) predict sag → false
  mismatches. **Do not tune sag to these rows.**
- **Geometry is a bbox heuristic** for 3DTime rows (no real geometry label), so many
  ordinary prints are tagged `overhang`.
- **3DTime outcomes are uniformly `success`** — no failure signal; good for Lane-A
  references, weak for outcome calibration.
See `CALIBRATION-REPORT.md` and `../../docs/plan/RESEARCH-NEEDS.md` for the fixes that make
this set tunable.
