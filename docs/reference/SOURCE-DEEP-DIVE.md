# Source Deep-Dive: What Each Source Produced, Gaps, and What to Find Next

**Companion to `INGESTION-REPORT.md`. Focus: per-source contribution analysis + gap-driven sourcing recommendations.**

**Update 2026-06-12 (Phase 2):** 5 Tier-S structured sources added. Lane C "100% success" trap fixed with 178 mixed-outcome observations from FDM error detection. See §4 for filled gaps.

---

## 1. Per-Source Contribution Analysis

### 1.1 3DTime Dataset (`3DTimeDataset/3DTime`) — 1,148 refs + 82 obs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| bbox_x_mm, bbox_y_mm, bbox_z_mm | 164 each | ✅ Real measurements from STL files |
| infill_density_pct | 164 | ✅ Real slicer settings (5–77%) |
| infill_rotation | 164 | ✅ Real slicer settings (0–90°) |
| infill_type | 164 | ✅ 6 types: stars, cubic, grid, line, supportcubic |
| print_time_s | 164 | ✅ Actual print duration from G-code simulation |
| nozzle_temp (Lane C) | 82 | ⚠️ All 210°C — no variation |
| bed_temp (Lane C) | 82 | ⚠️ All 60°C — no variation |
| fan_pct (Lane C) | 82 | ✅ Some variation: 40, 51, 76, 100, 255 |

**Assessment:** Our single most valuable source. 89% of all reference facts. But the G-code files all use the same PrusaSlicer profile (210°C/60°C), so there's no temperature diversity. The infill and geometry diversity is excellent.

**What it's missing:** Different temperature profiles, retraction settings, first-layer settings, failed prints.

---

### 1.2 G-code Actions Wiki (`reprap.org/wiki/G-code`) — 74 refs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| linear_advance_k | 30 | ⚠️ Filtered to 0.7–2.0 range, but these are G-code parameters not real K-factors |
| fan_pct | 26 | ⚠️ Extracted from M106 examples in docs, not real print settings |
| bed_temp | 8 | ⚠️ From M140/M190 examples |
| nozzle_temp | 6 | ⚠️ From M104/M109 examples |
| max_temp | 4 | ✅ From thermistor tables |

**Assessment:** Low-quality reference facts. The regex extracted example values from documentation, not real printer configurations. The linear_advance_k values are particularly suspect — they're G-code command parameters (e.g., `G1 X100 Y100 E0.5 F1200` where K appears in context), not Marlin K-factors.

**Verdict:** ⛔ Drop this source. Documentation examples ≠ real printer settings.

---

### 1.3 Prusa Filament INI (`prusa_filaments.ini`) — 16 refs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| nozzle_temp | 8 | ✅ Real PrusaSlicer defaults for PLA(210/215), PETG(240), ABS(250/255), TPU(230) |
| bed_temp | 4 | ✅ Real defaults: PLA(60), PETG(85), ABS(100), TPU(50) |
| retraction_mm | 4 | ✅ Real defaults: PLA(5), PETG(4), ABS(4), TPU(2) |

**Assessment:** High-quality, real manufacturer settings. But only 4 materials, one profile each.

**What's missing:** More materials (ASA, PC, Nylon, PLA+, Silk PLA, Wood-fill), more brands (eSun, Overture, Hatchbox, Polymaker), first-layer variants, fan speed profiles.

---

### 1.4 Moonraker GitHub Repo — 12 refs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| max_temp | 6 | ✅ From Klipper config examples in repo |
| bed_max_temp | 6 | ✅ From Klipper config examples in repo |

**Assessment:** Useful safety limits. But extracted from example configs in documentation, not production printer configs.

---

### 1.5 3DTime Dataloader Repo — 12 refs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| max_temp | 4 | ✅ From VoronV24 Klipper config |
| bed_max_temp | 4 | ✅ From VoronV24 Klipper config |
| pressure_advance | 4 | ✅ Real Klipper pressure_advance values |

**Assessment:** High-quality. The VoronV24.cfg in the 3DTime repo is a real, production Klipper config. This is the kind of source we need more of.

---

### 1.6 Klipper Thermistor Docs — 10 refs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| fan_pct | 8 | ⚠️ From documentation examples |
| nozzle_temp | 2 | ⚠️ From documentation examples |

**Assessment:** Low-quality. Documentation examples, not real settings.

---

### 1.7 RepRap Calibration Wiki — 8 refs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| nozzle_temp | 4 | ⚠️ From calibration examples |
| bed_temp | 4 | ⚠️ From calibration examples |

**Assessment:** Low-quality. Calibration procedure examples, not material baselines.

---

### 1.8 Sainsmart TPU Product Page — 4 refs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| nozzle_temp | 2 | ✅ Real manufacturer recommendation (210-230°C) |
| shore_hardness | 2 | ✅ Real material property (95A) |

**Assessment:** High-quality but tiny. Exactly the kind of source we need — manufacturer spec sheets.

---

### 1.9 Local Config Samples — 4 refs

**What it gave us:**
| Param | Count | Quality |
|-------|-------|---------|
| max_temp | 2 | ✅ From sample Klipper + Marlin configs |
| bed_max_temp | 2 | ✅ From sample Klipper + Marlin configs |

**Assessment:** High-quality but minimal. These are hand-crafted samples, not real printer configs.

---

### 1.10 ablam/gcode — 2 refs

**What it gave us:** 2 facts from 500 rows sampled (0.4% yield).

**Assessment:** ⛔ Effectively useless for our lane system. 443M rows of raw G-code, but the parquet format makes per-row regex parsing slow, and most rows don't contain M104/M140 in extractable positions. This dataset is for LLM training on G-code syntax, not for extracting print settings.

---

## 2. Gap Analysis by Lane

### 2.1 Lane A — Reference Facts

| Category | Have | Missing | Priority |
|----------|------|---------|----------|
| **Nozzle temps** | PLA(210/215), PETG(240), ABS(250/255), TPU(230) | ASA, PC, Nylon, PLA+, Silk, Wood-fill, CF-filled | HIGH |
| **Bed temps** | PLA(60), PETG(85), ABS(100), TPU(50) | Same materials as above | HIGH |
| **Retraction** | PLA(5), PETG(4), ABS(4), TPU(2) | Retraction SPEED, retraction PRIME, z-hop, wipe | HIGH |
| **Fan speeds** | Generic values from docs | Material-specific fan curves (PLA 100%, PETG 30-50%, ABS 0-20%, TPU 20-40%) | HIGH |
| **First layer** | Nothing | First layer temp, first layer bed temp, first layer height, first layer fan | HIGH |
| **Speed** | Nothing | Perimeters, infill, travel, first layer speeds | MEDIUM |
| **Hardware limits** | max_temp(275-300), bed_max_temp(120-125) | Per-printer-model limits (Ender 3, Prusa MK4, Voron, RatRig) | MEDIUM |
| **PID values** | Kp(22.2), Ki(1.08), Kd(114) from one config | Per-printer PID tunes | LOW |
| **Pressure advance** | 0.05 from one config | Per-filament PA values | MEDIUM |
| **Material properties** | TPU shore hardness(95A) | Glass transition temp, density, diameter tolerance per material | LOW |

**Bottom line:** We have good coverage of the 4 core materials at basic settings. Missing: more materials, first-layer settings, retraction details, material-specific fan curves.

---

### 2.2 Lane B — Lessons

| Material | Geometries covered | Geometries missing |
|----------|-------------------|-------------------|
| **PLA** | adhesion, bridge, overhang, stringing, vase | — (complete) |
| **PETG** | adhesion, bridge, overhang, stringing | vase |
| **ABS** | adhesion, overhang, warping | bridge, stringing, vase |
| **TPU** | stringing | adhesion, bridge, overhang, vase |

**Missing lesson topics entirely:**
- Z-offset effects (too close → elephant foot, too far → no adhesion)
- Moisture effects across all materials (PLA absorbs less but still matters)
- Print speed vs quality tradeoffs
- Support material settings (interface layers, z-distance)
- Multi-material printing (PLA+PETG support interface)
- Cold environment printing (garage in winter, <15°C)
- Hot environment printing (summer, >35°C)
- Very humid environment (>80% RH)
- Layer adhesion vs part orientation
- Post-processing effects (annealing PLA, ABS acetone smoothing)

**Environmental diversity missing:**
- All 13 lessons use env_temp 20-26°C, env_humidity 35-65%
- No cold weather lessons (<15°C)
- No hot weather lessons (>30°C)
- No extreme humidity lessons (>70% or <20%)

**Bottom line:** 13 lessons is a good start but we need 30-50 to cover the material×geometry×environment matrix. Each new material adds ~5-8 lessons.

---

### 2.3 Lane C — Calibration Observations ✅ PARTIALLY FIXED

| Attribute | Before | After (Phase 2) | Still needed |
|-----------|--------|-----------------|--------------|
| **Total observations** | 82 | **260** | 500+ ideal |
| **Outcomes** | 100% success | **Mixed: 86 success, 59 stringing, 61 sag, 54 unknown** | More diversity |
| **Nozzle temps** | All 210°C | **210°C + 215°C** | Range 190-260°C |
| **Bed temps** | All 60°C | All 60°C | Range 50-110°C |
| **Fan speeds** | 40, 51, 76, 100, 255 | Same + 0 (FDM prints with fan off) | Full 0-100% per material |
| **Retraction** | All 5.0mm (hardcoded) | **Real: 1, 3, 6, 8.5mm** | More values |
| **Environment** | All 22°C/45% | All 22°C/45% | Range 15-35°C, 20-80% RH |
| **Quality scores** | All 0.85 (hardcoded) | **Estimated from extrusion_multiplier** | Real measurements |

**Critical fix applied:** The FDM error detection source (NilsHagenBeyer/3D-printing_recorder) provided 178 observations with real failure outcomes. The simulator now has data to learn failure boundaries — 100% recall on sag failures, but needs stringing penalty added.

---

## 3. What Sources You Should Find

### Priority 1 — Immediate High Impact (find these now)

#### 3.1 More PrusaSlicer Filament Profiles
**What:** INI files for additional materials and brands.
**Where to find:**
- PrusaSlicer built-in profiles: `PrusaSlicer/resources/profiles/` in the PrusaSlicer installation
- Community profiles on Printables.com
- Vendor-provided profiles (eSun, Overture, Hatchbox, Polymaker, Prusament)
**What they'll produce:** Lane A — nozzle_temp, bed_temp, retraction_mm, fan_pct per material
**Estimated yield:** 8-12 facts per material profile, 50+ materials available → 400-600 refs

#### 3.2 Real Klipper printer.cfg Files
**What:** Production Klipper configs from real printers.
**Where to find:**
- Voron Discord #print-configs channel
- VoronDesign/Voron-2 GitHub repo (`firmware/klipper_configurations/`)
- RatOS config repository
- Klipper3d/klipper GitHub (`config/` directory has 30+ printer configs)
**What they'll produce:** Lane A — max_temp, bed_max_temp, PID, pressure_advance, thermistor types
**Estimated yield:** 6-10 facts per config, 30+ configs → 180-300 refs

#### 3.3 Filament Manufacturer Datasheets
**What:** Technical spec sheets with temp ranges, density, Tg.
**Where to find:**
- eSun: `esun3d.com` → each product page has "Printing Parameters" table
- Overture: `overture3d.com` → product pages
- Hatchbox: `hatchbox3d.com` → product pages
- Polymaker: `polymaker.com` → each filament has "Technical Data Sheet" PDF
- Prusament: `prusa3d.com` → each filament has detailed specs
**What they'll produce:** Lane A — nozzle_temp range, bed_temp range, Tg, density, diameter
**Estimated yield:** 4-8 facts per filament, 20+ filaments → 80-160 refs

#### 3.4 Print Failure Reports with Settings
**What:** Real failed prints where the user recorded their settings.
**Where to find:**
- r/FixMyPrint posts that include slicer settings in comments
- Your own Ender 3 print logs (the cockpit's manual outcome buttons)
- 3D-printing Discord servers with help channels
**What they'll produce:** Lane C — settings + real failure outcomes
**Estimated yield:** 5-20 observations with diverse outcomes

### Priority 2 — High Impact, More Effort

#### 3.5 Simplify3D Print Quality Guide
**What:** Visual defect → cause → fix reference. The gold standard for 3D printing troubleshooting.
**Where:** `https://www.simplify3d.com/resources/print-quality-troubleshooting/`
**What it'll produce:** Lane B — 20+ high-quality lessons mapping defects to causes and fixes
**Format:** Each defect page has: photo, problem description, cause checklist, solution steps
**Estimated yield:** 20-30 lessons covering all geometry types

#### 3.6 Teaching Tech Calibration Guide
**What:** Michael Laws' comprehensive calibration resource.
**Where:** `https://teachingtechyt.github.io/calibration.html`
**What it'll produce:** Lane A — baseline calibration values (flow rate, PID, retraction, acceleration)
**Estimated yield:** 15-25 refs

#### 3.7 CNC Kitchen YouTube Transcripts
**What:** Stefan Hermann's material science deep-dives.
**Where:** YouTube channel `@CNCKitchen` — transcripts via `yt-dlp --write-auto-subs`
**What it'll produce:** Lane B — material-specific lessons backed by measured data
**Key videos:** "Which filament is strongest?", "PETG vs PLA", "Annealing PLA", "Moisture effects"
**Estimated yield:** 10-15 high-quality, data-backed lessons

### Priority 3 — Nice to Have

#### 3.8 Marlin Configuration.h Examples
**What:** Real Marlin configs from different printers.
**Where:** MarlinFirmware/Marlin GitHub (`config/examples/` directory has 100+ printer configs)
**What they'll produce:** Lane A — max_temp, bed_max_temp, PID, linear advance, jerk, acceleration
**Estimated yield:** 8-12 facts per config

#### 3.9 Thingi10K STL Corpus
**What:** 10,000 3D models from Thingiverse.
**Where:** `ten-thousand-models.appspot.com` or HF dataset if available
**What it'll produce:** Lane A — geometry statistics (bbox, face count, manifold checks)
**Estimated yield:** 4-6 facts per model

#### 3.10 All3DP Filament Guides
**What:** Comprehensive filament comparison articles.
**Where:** `all3dp.com` → search "filament guide", "PLA vs PETG", etc.
**What they'll produce:** Lane B — comparative lessons, material selection guidance
**Estimated yield:** 5-10 lessons

---

## 4. Source Quality Tiers

| Tier | Source Type | Quality | Example |
|------|-------------|---------|---------|
| **S** | Manufacturer datasheets, real printer configs | Ground truth | Prusa INI, Voron Klipper cfg, eSun spec sheet |
| **A** | Published datasets with settings | Real, verifiable | 3DTime metadata CSV + G-code |
| **B** | Expert guides, calibration tutorials | Authoritative | Simplify3D guide, Teaching Tech |
| **C** | Community reports with settings | Real but unverified | r/FixMyPrint with slicer settings |
| **D** | Documentation examples | Not real settings | G-code wiki, Klipper docs examples |
| **F** | Auto-extracted from unstructured text | Noise | Web doc regex extraction (369/456 discarded) |

**Rule:** Prefer Tier S and A sources. Tier B for lessons. Avoid Tier D and F for reference facts.

---

## 5. Recommended Next Ingestion Run

If you can find the Priority 1 sources, here's what a second Modal run would look like:

```bash
# Add new sources to modal_app.py SOURCES registry:
# - PrusaSlicer community profiles (10-20 INI files)
# - Voron Klipper configs (5-10 printer.cfg files)
# - Filament datasheets (10-15 product pages)

modal run ingest/modal_app.py --category profiles   # ~200-400 new refs
modal run ingest/modal_app.py --category firmware   # ~100-200 new refs

# For Lane C, add a new source type: "print_log"
# Parse your Ender 3 print logs or r/FixMyPrint posts
modal run ingest/modal_app.py --source my-print-logs
```

**Projected totals after Priority 1 sources:**
- Lane A: 1,290 → ~2,000 reference facts
- Lane B: 25 → ~50 lessons
- Lane C: 82 → ~100 observations (with failure cases)

---

## 6. Sources to Avoid

| Source | Reason |
|--------|--------|
| **ablam/gcode** (bulk) | 443M rows, 0.4% yield. Only useful for LLM training, not setting extraction. |
| **3D-ADAM** (bulk) | 87K images, no print settings. Useful for vision model fine-tune, not our lanes. |
| **marlinfw.org** | 403 Forbidden from Modal IPs. Use GitHub repo instead. |
| **prusa3d.com** (live profiles) | 403 Forbidden from Modal IPs. Use local PrusaSlicer installation profiles. |
| **General web docs** | Regex extraction produces Tier F noise. Use only for lessons with LLM distillation. |
