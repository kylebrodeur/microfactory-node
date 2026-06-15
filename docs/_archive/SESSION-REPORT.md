# Session Report — 2026-06-12 (Phase 2: Clean Data + Calibration Diagnosis)

**Branch:** `claude/microfactory-gradio-hackathon-9e81fh`
**Session focus:** Fix Lane-C data extraction bugs, run calibration on clean data, diagnose structural bottleneck.

---

## Docs Updated This Session

| Doc | Change | Why |
|-----|--------|-----|
| `sim/calibration/CALIBRATION-REPORT.md` | Rewrote results section | Old report described fan=0 artifact (178/260 rows). New report describes clean data (0 fan=0 rows) and the structural bottleneck found. |

Docs updated in prior session (already committed):
- `docs/INGESTION-REPORT.md` — Phase 2 Tier-S sources, calibration results
- `docs/SOURCE-DEEP-DIVE.md` — Lane C gap marked PARTIALLY FIXED

---

## What We Did

### 1. Read RESEARCH-NEEDS.md + pulled upstream changes

`git pull` brought in:
- `docs/RESEARCH-NEEDS.md` — prioritized data gaps from first calibration pass
- `sim/calibration/CALIBRATION-REPORT.md` — initial calibration report (fan=0 artifact documented)
- `sim/calibration/results/` — baseline calibration metrics
- Updated `ingest/distill.py` — improved local parsers

RESEARCH-NEEDS.md identified the critical bottleneck: **178/260 rows had fan_pct=0** because the Lane-C extractor only parsed the G-code header (first 5KB), missing M106 commands in the file body and slicer footer comments.

### 2. Fixed Lane-C extractor (3 bugs → 0 fan=0 rows)

**Bug 1 — Fan extraction (header-only):**
- **Before:** `re.findall(r'M106\s+S(\d+)', header)` on first 5KB only
- **After:** Parse M106 across the WHOLE G-code file. Also check PrusaSlicer/Orca footer comments (`fan_speed=`, `cooling_fan_speed=`, `bridge_fan_speed=`). Also check M107 (explicit fan off). If no fan command found → skip the row (don't default to 0).
- **Impact:** 178 fan=0 rows → **0 fan=0 rows**

**Bug 2 — Nozzle temperature (preheat vs final):**
- **Before:** `re.findall(r'M10[49]\s+S(\d+)', header)` — first match was often M104 S150 (anti-oozing preheat)
- **After:** Prefer M109 (wait-for-nozzle = final temp). Fall back to last M104 if no M109.
- **Impact:** Nozzle temps now 210/215/220°C (was 150°C preheat)

**Bug 3 — Retraction (hardcoded default):**
- **Before:** `retraction = float(yaml_entry.get("retraction", 5.0))` — hardcoded 5.0mm fallback
- **After:** Parse from YAML first, then PrusaSlicer footer (`retract_length=`), then G1 E- moves. Fallback 5.0mm only if nothing found.
- **Impact:** Real retraction values: 1, 3, 6, 8.5mm

**Bug 4 — Geometry inference (bbox heuristic):**
- **Before:** Geometry from bounding box ratio (bbox_x/bbox_y > 5 = bridge, bbox_z < 5 = vase)
- **After:** Infer from G-code move patterns: long same-Z X/Y runs = bridge, high travel/extrude ratio = stringing, default = overhang
- **Impact:** More accurate geometry labels for FDM data

**Code changed:** `ingest/modal_app.py` — `_parse_fdm_error_gcode()` rewritten (150+ lines), 3DTime Lane C extraction in `distill_hf_dataset()` updated.

### 3. Regenerated calibration data

- Cleared old `observations.modal.jsonl` (260 rows, 178 fan=0)
- Ran fixed FDM parser locally → 178 clean observations
- Ran 3DTime on Modal with fixed extraction → 82 observations (48 still fan=0 — real M107 in G-code, unverified "success" labels)
- **Decision:** Use only FDM data (known outcomes) for calibration. 3DTime "success" labels are unverified (published models, not confirmed prints).

**Final calibration dataset:** 178 FDM observations
- 58 success, 59 failed_stringing, 61 failed_sag
- 0 fan=0 rows
- Real nozzle temps (210/215/220), real retraction (1-8.5mm), real fan (67-100%)

### 4. Ran calibration → structural bottleneck found

```
observations:     178
outcome accuracy: 32.6%  (58/178)
confusion:
  ✓ success            → success            ×58  (100% recall)
  ✗ failed_sag         → success            ×61  (0% recall)
  ✗ failed_stringing   → success            ×59  (0% recall)
```

**Key finding:** Simulator catches 100% of success cases but 0% of failures. This is NOT a constant-tuning problem — it's a structural sensitivity gap.

### 5. Diagnosed root cause: quality threshold + weak penalty scaling

Read `sim/outcome.py` to understand the penalty formulas:

**Sag formula:**
```python
need = {"overhang": 60, "bridge": 82, "vase": 50}[geo]
sag = max(0.0, (need - fan_pct)) / 100 * 0.7 + over * 0.6
```
At fan=67%, need=60: (60-67) = -7 → sag=0. Raising need to 75: (75-67)/100*0.7 = 0.056. But quality threshold is 0.7 — need total penalty >0.3 to flip outcome. The penalty formulas are too weak for moderate conditions.

**Stringing formula:**
```python
string = (max(0.0, humidity - 45) / 55 * 0.45 + over * 0.45 + max(0.0, 2.0 - retraction) / 2 * 0.30) * w
```
At humidity=45%, nozzle=210°C (in-band), retraction=3mm: all terms = 0 → string=0. Adding a base penalty would need >0.5 to overcome the 0.7 threshold — implausibly strong.

### 6. Attempted two constant tunes — both blocked by 0.7 threshold

| Tune | Change | Result | Why blocked |
|------|--------|--------|-------------|
| Overhang cooling need | 60 → 75 | Sag=0.056, quality=0.944 → still "success" | Penalty too weak to reach 0.3 |
| Stringing base penalty | Added base=0.12 | String=0.072, quality=0.928 → still "success" | Same — 0.7 threshold requires >0.3 |

Both reverted. Documented in CALIBRATION-REPORT.md.

### 7. Identified path forward

The missing features that distinguish success from failure in the FDM data:
- **Extrusion multiplier** — under-extrusion causes sag (YAML has `ex_mul`/`extrusion_multiplier`)
- **Travel speed** — fast travels cause stringing (G-code has feedrate values)
- **Part complexity** — simple towers vs complex geometries

These need to be:
1. Added to the Lane C observation schema
2. Added as inputs to `sim/outcome.py` penalty formulas
3. Extracted from G-code during ingestion

### 8. Committed + pushed

```
1e0afe2 calibration: clean FDM data (0 fan=0 rows), structural bottleneck identified
fbd8604 fix: Lane-C extractor — parse M106 across full file, use final temps, skip fan=null
```

---

## Files Changed This Session

| File | Lines | Change |
|------|-------|--------|
| `ingest/modal_app.py` | +378/-319 | Rewrote `_parse_fdm_error_gcode()`, fixed 3DTime Lane C extraction |
| `sim/calibration/observations.modal.jsonl` | 178 rows | Regenerated with clean data |
| `sim/calibration/CALIBRATION-REPORT.md` | +38/-34 | Updated results for clean data, documented structural bottleneck |
| `sim/outcome.py` | 0 net | Attempted 2 tunes, both reverted |

---

## Key Insights

1. **Data quality beats quantity.** 178 clean rows > 260 noisy rows. The fan=0 bug silently corrupted 68% of the dataset.
2. **Calibration is a data-quality detector.** The harness caught the fan=0 artifact before it corrupted the simulator.
3. **Structural sensitivity gap.** The simulator's 0.7 quality threshold + weak penalty scaling make it blind to moderate failure conditions. This is by design (calibrated for extreme sample data) but limits real-world accuracy.
4. **Missing features.** Extrusion multiplier and travel speed are the signals that distinguish success from failure in real prints. Adding them to the simulator is the next step.
5. **Honest-by-design held.** We reported 32.6% and why we can't tune to it, instead of manufacturing a win.
