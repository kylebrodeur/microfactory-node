"""Modal app — heavy ingestion at scale (the Modal-bonus track).

Ingests 3D-printing knowledge from documentation URLs, GitHub repos, slicer
profiles, and HF datasets into the three lanes the Chief Engineer consumes.

THE CONTRACT — three artifact shapes (one JSON object per line):
  A) reference fact     -> data/references.jsonl
     {"material","param","value","source"}                       (hard params)
  B) candidate lesson   -> data/_modal_candidate_lessons.jsonl    (REVIEW before ledger)
     {"job_id","material","geometry_type","env_temp","env_humidity",
      "outcome","lesson","source":"ingested","timestamp"}
  C) calibration obs    -> sim/calibration/observations.modal.jsonl
     {"material","geometry_type","env_temp","env_humidity","nozzle_temp",
      "bed_temp","retraction_mm","fan_pct","first_layer_fan_pct","outcome","quality"?}

Run (after `uv pip install modal datasets` + `modal token set`):
    modal run ingest/modal_app.py                          # all sources
    modal run ingest/modal_app.py --source klipper-config  # single source
    modal run ingest/modal_app.py --category firmware      # category of sources
"""

from __future__ import annotations

import json
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Import-guarded so the rest of the app/tests never depend on modal being present.
try:
    import modal
except Exception:  # pragma: no cover
    modal = None  # type: ignore

# ── Enums (must match core/models.py) ──────────────────────────────────────────
MATERIALS = ["PLA", "PETG", "ABS", "TPU"]
GEOMETRY_TYPES = ["overhang", "bridge", "stringing", "adhesion", "vase"]
OUTCOMES = ["success", "failed_sag", "failed_stringing"]

# ── Source Registry ───────────────────────────────────────────────────────────
# Each source: key -> (url, category, source_type, description)
# source_type determines how we fetch & parse it:
#   "github_repo"  — clone, scan for config files (*.cfg, *.h, *.ini)
#   "web_doc"      — fetch HTML, extract text, parse for params & lessons
#   "prusa_profiles" — download INI files, parse with Prusa parser
#   "product_spec" — extract material parameters from product pages
#   "research_repo" — clone, look for datasets/configs

SOURCES: dict[str, tuple[str, str, str, str]] = {
    # ── Firmware, Libraries & Host Controllers ──
    "moonraker": (
        "https://github.com/Arksine/moonraker",
        "firmware", "github_repo",
        "Moonraker web API server for Klipper"
    ),
    "mainsail": (
        "https://github.com/meteyou/mainsail",
        "firmware", "github_repo",
        "Mainsail web dashboard for Klipper"
    ),
    "tmcstepper": (
        "https://github.com/teemuatlut/TMCStepper",
        "firmware", "github_repo",
        "TMC stepper driver library"
    ),
    "klipper-thermistors": (
        "https://www.klipper3d.org/Config_Reference.html#common-thermistors",
        "firmware", "web_doc",
        "Klipper thermistor sensor designations"
    ),
    "tmc26x": (
        "https://github.com/trinamic/TMC26XStepper",
        "firmware", "github_repo",
        "TMC26X high-current driver library"
    ),
    "arduino-l6470": (
        "https://github.com/ameyer/Arduino-L6470",
        "firmware", "github_repo",
        "L6470 stepper driver library"
    ),
    "u8glib": (
        "https://github.com/olikraus/U8glib_Arduino",
        "firmware", "github_repo",
        "Display rendering library"
    ),
    "platformio": (
        "http://docs.platformio.org/en/latest/projectconf.html",
        "firmware", "web_doc",
        "PlatformIO project configuration"
    ),

    # ── Calibration Frameworks & Parametric Rules ──
    "reprap-calibration": (
        "http://reprap.org/wiki/Calibration",
        "calibration", "web_doc",
        "RepRap calibration framework"
    ),
    "pid-tuning": (
        "http://reprap.org/wiki/PID_Tuning",
        "calibration", "web_doc",
        "PID tuning for heater performance"
    ),
    "linear-advance": (
        "http://marlinfw.org/docs/features/lin_advance.html",
        "calibration", "web_doc",
        "Marlin Linear Advance configuration"
    ),
    "laser-spindle": (
        "http://marlinfw.org/docs/configuration/laser_spindle.html",
        "calibration", "web_doc",
        "PWM-to-RPM spindle configuration"
    ),
    "probes": (
        "http://marlinfw.org/docs/configuration/probes.html",
        "calibration", "web_doc",
        "Z-probe configuration"
    ),
    "gcode-actions": (
        "https://reprap.org/wiki/G-code#Action_commands",
        "calibration", "web_doc",
        "G-code protocol specification"
    ),
    "jerk-motion": (
        "https://github.com/synthetos/TinyG/wiki/Jerk-Controlled-Motion-Explained",
        "calibration", "web_doc",
        "Jerk-controlled motion kinematics"
    ),
    "junction-deviation": (
        "https://reprap.org/forum/read.php?1,739819",
        "calibration", "web_doc",
        "Junction Deviation equations"
    ),

    # ── Research Datasets & ML Resources ──
    "bcn3d-moveo": (
        "https://www.bcn3d.com/bcn3d-moveo-the-future-of-learning-robotic-arm/",
        "research", "web_doc",
        "BCN3D Moveo robotic arm (3D-ADAM base)"
    ),
    "3dtime-dataloader": (
        "https://github.com/3DTimeDataset/3DTime_pytorch_dataloader",
        "research", "research_repo",
        "3DTime time-series slicing data loader"
    ),
    "klipper-analysis": (
        "https://github.com/worksasintended/klipper_linear_movement_analysis",
        "research", "research_repo",
        "Klipper linear movement analysis"
    ),

    # ── Hardware Profiles & Slicer Configuration ──
    "prusa-anycubic": (
        "https://files.prusa3d.com/wp-content/uploads/repository/PrusaSlicer-settings-master/live/Anycubic/",
        "profiles", "prusa_profiles",
        "PrusaSlicer Anycubic machine profiles"
    ),
    "hartrusion-config": (
        "https://hartrusion.com/en/prusaslicer-config-for-anycubic-4max-pro-2-0/",
        "profiles", "web_doc",
        "Anycubic 4Max Pro 2.0 PrusaSlicer config"
    ),
    "sainsmart-tpu": (
        "https://www.sainsmart.com/collections/tpu-filament/products/all-colors-tpu-flexible-filament-1-75mm-0-8kg-1-76lb",
        "profiles", "product_spec",
        "Sainsmart TPU filament specifications"
    ),
    "ratos-install": (
        "https://os.ratrig.com/docs/installation",
        "profiles", "web_doc",
        "RatOS installation framework"
    ),
    "ratos-upgrade": (
        "https://os.ratrig.com/docs/upgrading_rc3",
        "profiles", "web_doc",
        "RatOS upgrade migration"
    ),

    # ── Structured Profile & Config Repos (Tier S) ──
    "bambu-filament-profiles": (
        "https://github.com/bambulab/BambuStudio",
        "structured", "bambu_json_profiles",
        "BambuStudio tree-structured filament JSON profiles (200+ materials)"
    ),
    "kanrog-klipper-configs": (
        "https://github.com/Kanrog/klipper-config-generator",
        "structured", "klipper_config_repo",
        "Klipper config generator: 150+ motherboard pin maps, PID, max temps"
    ),
    "3dprint-saviour-thresholds": (
        "https://github.com/Manicben/3DPrintSaviour",
        "structured", "failure_detection_repo",
        "3DPrintSaviour: NRMSE failure detection thresholds + classification logic"
    ),
    "jklewa-filament-profiles": (
        "https://github.com/jklewa/filament-profiles-data",
        "structured", "filament_profiles_repo",
        "Community-verified filament profiles: nozzle/bed temps, vendor, price"
    ),
    "fdm-error-detection": (
        "https://github.com/NilsHagenBeyer/3D-printing_recorder",
        "structured", "fdm_error_gcode",
        "FDM error detection: G-code + YAML with known failure outcomes (Lane C goldmine)"
    ),
}

# ── HF Dataset Mappers (for structured datasets) ──────────────────────────────
# These are separate from the documentation sources above.
# Each mapper takes one dataset row and returns zero or more ("A"|"B"|"C", record) tuples.

def _map_3d_adam(row: dict) -> list[tuple[str, dict]]:
    """3D-ADAM defect dataset → Lane C calibration observations.

    The 3D-ADAM dataset (pmchard/3D-ADAM) contains images and defect masks
    for 3D printing defects. We extract defect type → outcome mapping and
    any available print settings to produce calibration observations.

    Dataset structure (from anomalib loader):
      - image: PIL Image of the printed part
      - mask: defect mask
      - label: defect class (warping, under_extrusion, stringing, cracking)
      - category: part category
    """
    records = []
    defect = str(row.get("label", row.get("category", ""))).lower()

    # Map 3D-ADAM defect classes to Chief Engineer outcomes
    defect_to_outcome = {
        "warping": "failed_sag",
        "under_extrusion": "failed_sag",
        "stringing": "failed_stringing",
        "cracking": "failed_sag",
    }
    outcome = defect_to_outcome.get(defect)
    if not outcome:
        return records

    # Map defect to geometry type
    defect_to_geometry = {
        "warping": "adhesion",
        "under_extrusion": "overhang",
        "stringing": "stringing",
        "cracking": "adhesion",
    }
    geometry_type = defect_to_geometry.get(defect, "overhang")

    # 3D-ADAM doesn't include print settings in the dataset itself,
    # but we can emit Lane B lessons from the defect taxonomy.
    # Lane C requires actual settings — only emit if settings columns exist.
    has_settings = all(k in row for k in ("nozzle_temp", "bed_temp", "retraction_mm", "fan_pct"))
    if has_settings:
        records.append(("C", {
            "material": row.get("material", "PLA"),
            "geometry_type": geometry_type,
            "env_temp": float(row.get("env_temp", 22)),
            "env_humidity": float(row.get("env_humidity", 45)),
            "nozzle_temp": float(row["nozzle_temp"]),
            "bed_temp": float(row["bed_temp"]),
            "retraction_mm": float(row["retraction_mm"]),
            "fan_pct": float(row["fan_pct"]),
            "first_layer_fan_pct": float(row.get("first_layer_fan_pct", 0)),
            "outcome": outcome,
            "quality": float(row.get("quality", 0.5)),
        }))

    # Always emit Lane B lesson from defect taxonomy
    defect_lessons = {
        "warping": "Corners lift when lower layers cool and contract — raise bed temp, enclose, slow first layer.",
        "under_extrusion": "Gaps and weak walls from too-low temp or too-fast flow — raise temp or slow down, check for clogs.",
        "stringing": "Fine whiskers across gaps from wet filament or hot travel — dry filament, lower temp, tune retraction.",
        "cracking": "Layers split under stress from over-cooling — reduce fan, raise temp, enclose for ABS.",
    }
    lesson_text = defect_lessons.get(defect, "")
    if lesson_text:
        job_id = f"modal-3dadam-{hashlib.md5(str(row).encode()).hexdigest()[:8]}"
        records.append(("B", {
            "job_id": job_id,
            "material": row.get("material", "PLA"),
            "geometry_type": geometry_type,
            "env_temp": float(row.get("env_temp", 22)),
            "env_humidity": float(row.get("env_humidity", 45)),
            "outcome": outcome,
            "lesson": lesson_text,
            "source": "ingested",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

    return records


def _map_gcode(row: dict) -> list[tuple[str, dict]]:
    """Slicer g-code corpus → Lane A material baselines.

    The ablam/gcode dataset contains G-code files from Printables.
    We parse M104 (set extruder temp), M140 (set bed temp), and
    retraction settings to extract reference facts.
    """
    records = []
    gcode_text = str(row.get("gcode", row.get("content", row.get("text", ""))))
    if not gcode_text:
        return records

    # Extract temperatures from G-code
    nozzle_match = re.search(r"M104\s+S(\d+)", gcode_text)
    bed_match = re.search(r"M140\s+S(\d+)", gcode_text)
    retract_match = re.search(r"G1\s+E-?(\d+\.?\d*).*retract", gcode_text, re.I)

    # Try to determine material from filename or comments
    filename = str(row.get("filename", row.get("file_name", ""))).upper()
    material = "PLA"  # default
    for m in MATERIALS:
        if m in filename:
            material = m
            break

    source = f"ablam/gcode:{row.get('filename', row.get('id', 'unknown'))}"

    if nozzle_match:
        records.append(("A", {
            "material": material,
            "param": "nozzle_temp",
            "value": float(nozzle_match.group(1)),
            "source": source,
        }))
    if bed_match:
        records.append(("A", {
            "material": material,
            "param": "bed_temp",
            "value": float(bed_match.group(1)),
            "source": source,
        }))
    if retract_match:
        records.append(("A", {
            "material": material,
            "param": "retraction_mm",
            "value": float(retract_match.group(1)),
            "source": source,
        }))

    return records


def _map_3dtime(row: dict) -> list[tuple[str, dict]]:
    """3DTime metadata CSV → Lane A reference facts (material, infill, geometry)."""
    records = []
    material_map = {"pla": "PLA", "pet": "PETG", "abs": "ABS", "tpu": "TPU"}
    material = material_map.get(str(row.get("Material", "")).lower(), "PLA")
    source = f"3DTime:{row.get('3D mesh name', row.get('G-code file name', 'unknown'))}"

    for dim, param in [("Bounding box X (mm)", "bbox_x_mm"),
                        ("Bounding box Y (mm)", "bbox_y_mm"),
                        ("Bounding box Z (mm)", "bbox_z_mm")]:
        val = row.get(dim)
        if val:
            try:
                records.append(("A", {"material": material, "param": param,
                                      "value": float(val), "source": source}))
            except ValueError:
                pass

    for key, param in [("Infill density (%)", "infill_density_pct"),
                        ("Infill rotation (°)", "infill_rotation")]:
        val = row.get(key)
        if val:
            try:
                records.append(("A", {"material": material, "param": param,
                                      "value": float(val), "source": source}))
            except ValueError:
                pass

    infill_type = row.get("Infill type", "")
    if infill_type:
        records.append(("A", {"material": material, "param": "infill_type",
                              "value": 0, "source": f"{source}:{infill_type}"}))

    print_time = row.get("Print time (s)")
    if print_time:
        try:
            records.append(("A", {"material": material, "param": "print_time_s",
                                  "value": float(print_time), "source": source}))
        except ValueError:
            pass

    return records


# dataset key → (HF dataset id, mapper)
HF_MAPPERS = {
    "3d-adam": ("pmchard/3D-ADAM", _map_3d_adam),
    "gcode": ("ablam/gcode", _map_gcode),
    "3dtime": ("3DTimeDataset/3DTime", _map_3dtime),
}

_VALID_LANES = {"A", "B", "C"}

# ── Deterministic parsers for documentation content ───────────────────────────

def _material_of(text: str) -> str | None:
    """Detect material name in text."""
    up = text.upper()
    for m in MATERIALS:
        if m in up:
            return m
    return None


def _extract_temperature_values(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Extract temperature reference facts from documentation text.

    Looks for patterns like:
      - "nozzle temperature: 200-220°C"
      - "bed temperature 60°C"
      - "max_temp: 300"
      - "recommended temperature 210°C for PLA"
    """
    records = []
    # Pattern: material name near a temperature value
    # e.g. "PLA at 200°C", "PETG: 230-240°C"
    temp_patterns = [
        # nozzle_temp patterns
        (r'(?:nozzle|hotend|extruder)\s*(?:temp(?:erature)?)?\s*[:=]?\s*(\d{3})(?:\s*[-–]\s*\d{3})?\s*°?[CF]?', "nozzle_temp"),
        (r'(?:print(?:ing)?\s*)?temp(?:erature)?\s*[:=]?\s*(\d{3})(?:\s*[-–]\s*\d{3})?\s*°?[CF]?', "nozzle_temp"),
        # bed_temp patterns
        (r'(?:bed|heatbed)\s*(?:temp(?:erature)?)?\s*[:=]?\s*(\d{2,3})\s*°?[CF]?', "bed_temp"),
        # retraction patterns
        (r'retract(?:ion)?\s*(?:length|distance)?\s*[:=]?\s*(\d+\.?\d*)\s*mm', "retraction_mm"),
        # max_temp patterns
        (r'max(?:imum)?\s*_?temp(?:erature)?\s*[:=]?\s*(\d{3})\s*°?[CF]?', "max_temp"),
        # fan patterns
        (r'(?:part\s*)?(?:cooling\s*)?fan\s*(?:speed|pct|percent)?\s*[:=]?\s*(\d{1,3})\s*%?', "fan_pct"),
    ]

    for pattern, param in temp_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = float(match.group(1))
            # Find nearby material mention (within 200 chars before)
            context_start = max(0, match.start() - 200)
            context = text[context_start:match.end()]
            material = _material_of(context) or "*"
            records.append(("A", {
                "material": material,
                "param": param,
                "value": value,
                "source": source_label,
            }))

    return records


def _extract_lessons_from_doc(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Extract candidate lessons from documentation text.

    Looks for patterns indicating cause→effect relationships:
      - "if ... then ..." (conditional advice)
      - "to prevent/avoid ... do ..." (preventative advice)
      - "when ... occurs, ..." (troubleshooting)
      - "increase/decrease ... to ..." (parametric advice)
    """
    records = []
    lesson_patterns = [
        # Conditional: "If [condition], [action]"
        (r'(?i)if\s+(.{20,200}?)(?:,\s*|then\s*)(.{20,200}?)(?:\.|$)', "conditional"),
        # Preventative: "To prevent/avoid [problem], [action]"
        (r'(?i)to\s+(?:prevent|avoid|reduce|fix)\s+(.{20,150}?)(?:,\s*|you\s*(?:should|can|need\s*to)?\s*)(.{20,150}?)(?:\.|$)', "preventative"),
        # Troubleshooting: "When/If [symptom], [cause/solution]"
        (r'(?i)(?:when|if)\s+(.{20,150}?)(?:occurs|happens|appears)(?:,\s*|it\s*(?:is|means|indicates)\s*)(.{20,150}?)(?:\.|$)', "troubleshooting"),
        # Parametric: "increase/decrease [param] to [effect]"
        (r'(?i)(increase|decrease|raise|lower)\s+(?:the\s*)?(\w+(?:\s*\w+)?)\s*(?:to|for|when)\s+(.{20,150}?)(?:\.|$)', "parametric"),
    ]

    for pattern, lesson_type in lesson_patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()
            if lesson_type == "conditional":
                condition, action = groups[0], groups[1]
                lesson_text = f"{condition.strip()} — {action.strip()}."
            elif lesson_type == "preventative":
                problem, action = groups[0], groups[1]
                lesson_text = f"To prevent {problem.strip()}, {action.strip()}."
            elif lesson_type == "troubleshooting":
                symptom, cause = groups[0], groups[1]
                lesson_text = f"When {symptom.strip()} occurs, {cause.strip()}."
            elif lesson_type == "parametric":
                direction, param, effect = groups[0], groups[1], groups[2]
                lesson_text = f"{direction.capitalize()} {param.strip()} to {effect.strip()}."
            else:
                continue

            # Skip if too short or too long
            if len(lesson_text) < 30 or len(lesson_text) > 300:
                continue

            # Try to detect material and geometry from context
            context_start = max(0, match.start() - 300)
            context = text[context_start:match.end()]
            material = _material_of(context) or "PLA"
            geometry = "overhang"  # default
            for gt in GEOMETRY_TYPES:
                if gt in context.lower():
                    geometry = gt
                    break

            # Detect outcome from lesson text
            outcome = "success"
            if any(w in lesson_text.lower() for w in ("fail", "warp", "sag", "string", "crack", "lift", "poor", "bad", "issue", "problem")):
                if "string" in lesson_text.lower():
                    outcome = "failed_stringing"
                else:
                    outcome = "failed_sag"

            job_id = f"modal-doc-{hashlib.md5(lesson_text.encode()).hexdigest()[:8]}"
            records.append(("B", {
                "job_id": job_id,
                "material": material,
                "geometry_type": geometry,
                "env_temp": 22.0,
                "env_humidity": 45.0,
                "outcome": outcome,
                "lesson": lesson_text,
                "source": "ingested",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }))

    return records


def _extract_pid_values(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Extract PID constants from documentation (specialized parser)."""
    records = []
    # Klipper-style: pid_Kp=22.2 pid_Ki=1.08 pid_Kd=114
    pid_match = re.search(
        r'pid_Kp\s*=\s*([\d.]+).*?pid_Ki\s*=\s*([\d.]+).*?pid_Kd\s*=\s*([\d.]+)',
        text, re.S | re.I
    )
    if pid_match:
        for i, (val, param) in enumerate(zip(pid_match.groups(), ("pid_Kp", "pid_Ki", "pid_Kd"))):
            records.append(("A", {
                "material": "*",
                "param": param,
                "value": float(val),
                "source": source_label,
            }))
    return records


def _extract_linear_advance(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Extract Linear Advance K-factors from documentation."""
    records = []
    # Marlin-style: M900 K0.05 for PLA, K0.08 for PETG
    for match in re.finditer(
        r'(?:M900\s*)?K\s*(\d+(?:\.\d+)?)\s*(?:for\s+)?(\w+)',
        text, re.I
    ):
        try:
            k_value = float(match.group(1))
        except ValueError:
            continue
        # Realistic K-factors are 0.0-2.0 (most filaments 0.0-0.2, flexible up to 2.0)
        if k_value < 0 or k_value > 2.0:
            continue
        material = _material_of(match.group(2)) or match.group(2).upper()
        if material not in MATERIALS:
            material = "*"
        records.append(("A", {
            "material": material,
            "param": "linear_advance_k",
            "value": k_value,
            "source": source_label,
        }))
    return records


def _extract_thermistor_types(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Extract thermistor type → max_temp mappings from Klipper docs."""
    records = []
    # Pattern: "EPCOS 100K B57560G104F" with max_temp nearby
    for match in re.finditer(
        r'(?:thermistor|sensor)_type\s*[:=]\s*[\'"]?(\w+(?:\s+\w+)*)[\'"]?.*?max_temp\s*[:=]\s*(\d+)',
        text, re.S | re.I
    ):
        records.append(("A", {
            "material": "*",
            "param": "max_temp",
            "value": float(match.group(2)),
            "source": f"{source_label}:{match.group(1).strip()}",
        }))
    return records


# ── Source-type dispatchers ───────────────────────────────────────────────────

def _parse_web_doc(text: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse a web documentation page into lane records."""
    records = []
    source_label = f"modal:{source_key}"

    # Clean HTML tags if present
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean).strip()

    if len(clean) < 100:
        return records

    # Run all deterministic parsers
    records.extend(_extract_temperature_values(clean, source_label))
    records.extend(_extract_lessons_from_doc(clean, source_label))
    records.extend(_extract_pid_values(clean, source_label))
    records.extend(_extract_linear_advance(clean, source_label))
    records.extend(_extract_thermistor_types(clean, source_label))

    return records


def _parse_github_repo(repo_path: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse a cloned GitHub repo for config files and documentation."""
    records = []
    repo_dir = Path(repo_path)
    if not repo_dir.exists():
        return records

    source_label = f"modal:{source_key}"

    # Look for config files
    config_patterns = [
        ("**/*.cfg", _parse_klipper_style_cfg),
        ("**/Configuration.h", _parse_marlin_style_h),
        ("**/*.ini", _parse_prusa_style_ini),
        ("**/README.md", _parse_readme),
    ]

    for glob_pattern, parser_fn in config_patterns:
        for filepath in repo_dir.glob(glob_pattern):
            try:
                text = filepath.read_text(encoding="utf-8", errors="ignore")
                records.extend(parser_fn(text, f"{source_label}:{filepath.name}"))
            except Exception:
                continue

    return records


def _parse_prusa_profiles(text: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse PrusaSlicer INI profiles."""
    return _parse_prusa_style_ini(text, f"modal:{source_key}")


def _parse_product_spec(text: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse product specification page for material parameters."""
    records = []
    source_label = f"modal:{source_key}"
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Extract temperature ranges
    for match in re.finditer(
        r'(?:print(?:ing)?|nozzle|extruder)\s*temp(?:erature)?\s*(?:range)?\s*[:=]?\s*(\d{3})\s*[-–]\s*(\d{3})\s*°?[CF]?',
        clean, re.I
    ):
        material = _material_of(clean) or "TPU"
        records.append(("A", {
            "material": material,
            "param": "nozzle_temp",
            "value": float(match.group(1)),
            "source": source_label,
        }))

    for match in re.finditer(
        r'(?:bed|heatbed)\s*temp(?:erature)?\s*(?:range)?\s*[:=]?\s*(\d{2,3})\s*[-–]\s*(\d{2,3})\s*°?[CF]?',
        clean, re.I
    ):
        material = _material_of(clean) or "TPU"
        records.append(("A", {
            "material": material,
            "param": "bed_temp",
            "value": float(match.group(1)),
            "source": source_label,
        }))

    # Shore hardness
    shore_match = re.search(r'(?:shore\s*hardness|hardness)\s*[:=]?\s*(\d{2}A)', clean, re.I)
    if shore_match:
        records.append(("A", {
            "material": _material_of(clean) or "TPU",
            "param": "shore_hardness",
            "value": float(shore_match.group(1).replace("A", "")),
            "source": source_label,
        }))

    return records


# ── Config file parsers (reuse logic from distill.py) ─────────────────────────

def _parse_klipper_style_cfg(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Parse Klipper-style cfg for max temps and settings."""
    records = []
    for section, param in (("extruder", "max_temp"), ("heater_bed", "bed_max_temp")):
        m = re.search(rf"\[{section}\][^\[]*?max_temp\s*[:=]\s*(\d+(?:\.\d+)?)", text, re.S | re.I)
        if m:
            records.append(("A", {
                "material": "*",
                "param": param,
                "value": float(m.group(1)),
                "source": source_label,
            }))
    # PID values
    records.extend(_extract_pid_values(text, source_label))
    # Pressure advance
    pa_match = re.search(r'pressure_advance\s*[:=]\s*([\d.]+)', text, re.I)
    if pa_match:
        records.append(("A", {
            "material": "*",
            "param": "pressure_advance",
            "value": float(pa_match.group(1)),
            "source": source_label,
        }))
    return records


def _parse_marlin_style_h(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Parse Marlin Configuration.h for max temps."""
    records = []
    for define, param in (("HEATER_0_MAXTEMP", "max_temp"), ("BED_MAXTEMP", "bed_max_temp")):
        m = re.search(rf"#define\s+{define}\s+(\d+)", text)
        if m:
            records.append(("A", {
                "material": "*",
                "param": param,
                "value": float(m.group(1)),
                "source": source_label,
            }))
    # DEFAULT_Kp/Ki/Kd
    for pid_param in ("DEFAULT_Kp", "DEFAULT_Ki", "DEFAULT_Kd"):
        m = re.search(rf"#define\s+{pid_param}\s+([\d.]+)", text)
        if m:
            records.append(("A", {
                "material": "*",
                "param": pid_param.lower(),
                "value": float(m.group(1)),
                "source": source_label,
            }))
    # Linear advance K factor
    la_match = re.search(r'#define\s+LIN_ADVANCE_K\s+([\d.]+)', text)
    if la_match:
        records.append(("A", {
            "material": "*",
            "param": "linear_advance_k",
            "value": float(la_match.group(1)),
            "source": source_label,
        }))
    return records


def _parse_prusa_style_ini(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Parse PrusaSlicer-style INI for filament settings."""
    records = []
    # Find filament sections and extract key values
    current_material = None
    for line in text.splitlines():
        line = line.strip()
        # Section header: [filament:Generic PLA]
        section_match = re.match(r'\[(?:filament:)?(.+)\]', line, re.I)
        if section_match:
            current_material = _material_of(section_match.group(1))
            continue

        if not current_material:
            continue

        # Key = value pairs
        kv_match = re.match(r'(\w+)\s*=\s*(.+)$', line)
        if not kv_match:
            continue

        key, raw_val = kv_match.group(1), kv_match.group(2).strip()
        num_match = re.search(r'-?\d+(?:\.\d+)?', raw_val.split(",")[0])
        if not num_match:
            continue
        value = float(num_match.group())

        param_map = {
            "temperature": "nozzle_temp",
            "first_layer_temperature": "nozzle_temp",
            "bed_temperature": "bed_temp",
            "first_layer_bed_temperature": "bed_temp",
            "retract_length": "retraction_mm",
            "retract_speed": "retraction_speed",
            "fan_speed": "fan_pct",
            "min_fan_speed": "fan_pct",
            "max_fan_speed": "fan_pct",
        }
        param = param_map.get(key)
        if param:
            records.append(("A", {
                "material": current_material,
                "param": param,
                "value": value,
                "source": source_label,
            }))

    return records


def _parse_readme(text: str, source_label: str) -> list[tuple[str, dict]]:
    """Parse README for reference facts and lessons."""
    records = []
    records.extend(_extract_temperature_values(text, source_label))
    records.extend(_extract_lessons_from_doc(text, source_label))
    return records


# ── Structured profile parsers (Tier S sources) ──────────────────────────────

def _parse_bambu_json_profiles(repo_path: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse BambuStudio tree-structured filament JSON profiles → Lane A.

    Three-layer inheritance: fdm_filament_pla → Material@base → Material@BBL_A1.
    Extracts: nozzle_temp, bed_temp, fan_speed, retraction, volumetric_speed,
    flow_ratio, density, cost per material.
    """
    import json as _json
    records = []
    repo_dir = Path(repo_path)
    filament_dir = repo_dir / "resources" / "profiles" / "BBL" / "filament"
    if not filament_dir.exists():
        return records

    source_label = f"modal:{source_key}"

    # First, load the root defaults (fdm_filament_pla.json, etc.)
    root_defaults = {}
    for root_file in filament_dir.glob("fdm_filament_*.json"):
        try:
            data = _json.loads(root_file.read_text(encoding="utf-8"))
            mat_key = root_file.stem.replace("fdm_filament_", "")
            root_defaults[mat_key] = data
        except Exception:
            continue

    # Then process each material-specific file
    for json_file in sorted(filament_dir.glob("*.json")):
        name = json_file.stem
        # Skip root defaults and non-material files
        if name.startswith("fdm_filament_") or "@" not in name:
            continue

        try:
            data = _json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Resolve inheritance chain
        inherits = data.get("inherits", "")
        parent_data = {}
        if inherits in root_defaults:
            parent_data = root_defaults[inherits]

        # Merge: child overrides parent
        merged = {**parent_data, **data}

        # Extract material name from filename: "Bambu PLA Basic @BBL A1" → "PLA"
        material = "*"
        for m in MATERIALS:
            if m in name.upper():
                material = m
                break
        # Handle special materials
        special_map = {
            "PA": "ABS", "PC": "ABS", "ASA": "ABS", "PETG": "PETG",
            "TPU": "TPU", "PLA": "PLA", "ABS": "ABS",
        }
        for key, mat in special_map.items():
            if key in name.upper() and material == "*":
                material = mat
                break

        src = f"{source_label}:{name}"

        # Extract settings (BambuStudio uses array format ["value"])
        def _first_num(val):
            if isinstance(val, list) and val:
                val = val[0]
            if isinstance(val, str):
                try:
                    return float(val.rstrip("%"))
                except ValueError:
                    return None
            if isinstance(val, (int, float)):
                return float(val)
            return None

        param_map = {
            "nozzle_temperature": "nozzle_temp",
            "nozzle_temperature_initial_layer": "nozzle_temp",
            "hot_plate_temp": "bed_temp",
            "hot_plate_temp_initial_layer": "bed_temp",
            "textured_plate_temp": "bed_temp",
            "textured_plate_temp_initial_layer": "bed_temp",
            "fan_max_speed": "fan_pct",
            "fan_min_speed": "fan_pct",
            "filament_max_volumetric_speed": "max_volumetric_speed",
            "filament_flow_ratio": "flow_ratio",
            "filament_density": "density",
            "filament_cost": "cost",
            "filament_retraction_length": "retraction_mm",
            "filament_retraction_speed": "retraction_speed",
            "slow_down_layer_time": "slow_down_layer_time",
        }

        for json_key, param in param_map.items():
            val = _first_num(merged.get(json_key))
            if val is not None:
                records.append(("A", {
                    "material": material,
                    "param": param,
                    "value": val,
                    "source": src,
                }))

    return records


def _parse_klipper_config_repo(repo_path: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse Kanrog Klipper config generator → Lane A.

    150+ .cfg files with motherboard pin maps, PID values, max temps,
    thermistor types, stepper driver settings.
    """
    records = []
    repo_dir = Path(repo_path)
    config_dir = repo_dir / "config-examples"
    if not config_dir.exists():
        return records

    source_label = f"modal:{source_key}"

    for cfg_file in config_dir.glob("*.cfg"):
        try:
            text = cfg_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        src = f"{source_label}:{cfg_file.name}"

        # Reuse existing Klipper parser for max temps + PID
        records.extend(_parse_klipper_style_cfg(text, src))

        # Additional: extract stepper run_current
        for match in re.finditer(r'run_current\s*[:=]\s*([\d.]+)', text):
            records.append(("A", {
                "material": "*",
                "param": "run_current",
                "value": float(match.group(1)),
                "source": src,
            }))

        # Extract thermistor type
        for match in re.finditer(r'sensor_type\s*[:=]\s*(\S+)', text):
            records.append(("A", {
                "material": "*",
                "param": "sensor_type",
                "value": 0,
                "source": f"{src}:{match.group(1)}",
            }))

        # Extract microsteps
        for match in re.finditer(r'microsteps\s*[:=]\s*(\d+)', text):
            records.append(("A", {
                "material": "*",
                "param": "microsteps",
                "value": float(match.group(1)),
                "source": src,
            }))

    return records


def _parse_failure_detection_repo(repo_path: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse 3DPrintSaviour failure detection thresholds → Lane B lessons.

    Extracts the NRMSE threshold constants and classification logic:
      - Detachment: score > 1.0 AND deviance > 1.0
      - Partial breakage: scr_diff > 0.2 AND dev_diff > 0.2
      - Filament runout/clog: score < 0.2 AND deviance < 0.2
      - Spaghetti: ML confidence ≥ 0.3
    """
    records = []
    repo_dir = Path(repo_path)
    source_label = f"modal:{source_key}"
    now = datetime.now(timezone.utc).isoformat()

    # Read printcontrol.py for threshold constants
    pc_path = repo_dir / "printcontrol.py"
    if pc_path.exists():
        text = pc_path.read_text(encoding="utf-8", errors="ignore")

        # Extract threshold constants
        thresholds = {}
        for match in re.finditer(r'(SCR_THRES|DEV_THRES|BR_SCR_THRES|BR_DEV_THRES|FIL_SCR_THRES|FIL_DEV_THRES)\s*=\s*([\d.]+)', text):
            thresholds[match.group(1)] = float(match.group(2))

        # Detachment lesson
        if "SCR_THRES" in thresholds:
            records.append(("B", {
                "job_id": f"modal-saviour-detach-{hashlib.md5(b'detach').hexdigest()[:8]}",
                "material": "PLA",
                "geometry_type": "adhesion",
                "env_temp": 22.0,
                "env_humidity": 45.0,
                "outcome": "failed_sag",
                "lesson": (
                    f"Print detachment detected when layer-to-layer NRMSE score > {thresholds['SCR_THRES']} "
                    f"AND 5-layer deviance > {thresholds.get('DEV_THRES', 1.0)}. "
                    "Large structural changes across consecutive layers indicate the part has separated from the bed. "
                    "Check bed adhesion: clean surface, raise bed temp, use brim or raft."
                ),
                "source": "ingested",
                "timestamp": now,
            }))

        # Clog/runout lesson
        if "FIL_SCR_THRES" in thresholds:
            records.append(("B", {
                "job_id": f"modal-saviour-clog-{hashlib.md5(b'clog').hexdigest()[:8]}",
                "material": "PLA",
                "geometry_type": "stringing",
                "env_temp": 22.0,
                "env_humidity": 45.0,
                "outcome": "failed_stringing",
                "lesson": (
                    f"Filament runout or nozzle clog detected when NRMSE score < {thresholds['FIL_SCR_THRES']} "
                    f"AND deviance < {thresholds.get('FIL_DEV_THRES', 0.2)}. "
                    "Near-zero structural change means no material is being deposited. "
                    "Check filament spool, extruder tension, and nozzle for clogs."
                ),
                "source": "ingested",
                "timestamp": now,
            }))

        # Partial breakage lesson
        if "BR_SCR_THRES" in thresholds:
            records.append(("B", {
                "job_id": f"modal-saviour-break-{hashlib.md5(b'break').hexdigest()[:8]}",
                "material": "PLA",
                "geometry_type": "overhang",
                "env_temp": 22.0,
                "env_humidity": 45.0,
                "outcome": "failed_sag",
                "lesson": (
                    f"Partial breakage detected when frame-to-frame score delta > {thresholds['BR_SCR_THRES']} "
                    f"AND deviance delta > {thresholds.get('BR_DEV_THRES', 0.2)}. "
                    "Sudden structural changes mid-print indicate layer delamination or part fracture. "
                    "Reduce cooling fan, increase nozzle temp, check for drafts."
                ),
                "source": "ingested",
                "timestamp": now,
            }))

    return records


def _parse_filament_profiles_repo(repo_path: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse jklewa filament-profiles-data → Lane A.

    sample-filaments.json: community-verified nozzle/bed temp ranges,
    material type, vendor, price, color per filament SKU.
    """
    import json as _json
    records = []
    repo_dir = Path(repo_path)
    json_path = repo_dir / "sample-filaments.json"
    if not json_path.exists():
        return records

    source_label = f"modal:{source_key}"

    try:
        data = _json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return records

    filaments = data.get("filaments", [])
    for fil in filaments:
        material_name = str(fil.get("material", "")).upper()
        material = "*"
        for m in MATERIALS:
            if m in material_name:
                material = m
                break

        brand = fil.get("brand_name", "unknown")
        color = fil.get("color", "")
        src = f"{source_label}:{brand}/{material_name}/{color}" if color else f"{source_label}:{brand}/{material_name}"

        # Properties: temp_min, temp_max, bed_temp_min, bed_temp_max
        props = fil.get("properties") or fil.get("default_properties") or {}

        for key, param in [("temp_min", "nozzle_temp_min"), ("temp_max", "nozzle_temp_max"),
                            ("bed_temp_min", "bed_temp_min"), ("bed_temp_max", "bed_temp_max")]:
            val = props.get(key)
            if val is not None:
                try:
                    records.append(("A", {"material": material, "param": param,
                                          "value": float(val), "source": src}))
                except (ValueError, TypeError):
                    pass

        # Optional: k_value, flow_ratio, fan_speed_min
        for key, param in [("k_value", "linear_advance_k"), ("flow_ratio", "flow_ratio"),
                            ("fan_speed_min", "fan_pct")]:
            val = props.get(key)
            if val is not None:
                try:
                    records.append(("A", {"material": material, "param": param,
                                          "value": float(val), "source": src}))
                except (ValueError, TypeError):
                    pass

        # Price data
        price_data = fil.get("price_data")
        if price_data and price_data.get("price"):
            try:
                records.append(("A", {"material": material, "param": "price_usd",
                                      "value": float(price_data["price"]), "source": src}))
            except (ValueError, TypeError):
                pass

    return records


def _parse_fdm_error_gcode(repo_path: str, url: str, source_key: str) -> list[tuple[str, dict]]:
    """Parse FDM error detection G-code + YAML → Lane C calibration observations.

    NilsHagenBeyer/3D-printing_recorder: G-code files with known failure outcomes.
    YAML metadata logs: class (GOOD/STRINGING/underextrusion), filament, nozzle,
    retraction, layer_height, extrusion_multiplier.
    G-code filenames encode: temperature, material, printer.

    FIXED (per RESEARCH-NEEDS.md):
    - Parse M106 across the WHOLE file, not just header
    - Parse retraction from G1 E- moves + PrusaSlicer footer comments
    - Infer geometry from G-code moves (bridge/overhang), not bbox heuristic
    - Skip rows where fan_pct can't be determined (no M106 found → null, not 0)
    """
    import yaml as _yaml
    records = []
    repo_dir = Path(repo_path)
    gcode_dir = repo_dir / "gcode"
    if not gcode_dir.exists():
        return records

    source_label = f"modal:{source_key}"

    # Failure class → outcome
    failure_map = {
        "good": "success",
        "stringing": "failed_stringing",
        "underextrusion": "failed_sag",
        "underex": "failed_sag",
    }

    def _infer_geometry_from_gcode(text: str) -> str:
        """Infer geometry type from G-code move patterns.

        Bridge: long X/Y moves at the same Z with extrusion → spanning gaps.
        Overhang: outward-stepping perimeters (X/Y expanding each layer).
        Stringing: many travel moves (G0) between disconnected regions.
        Default: overhang.
        """
        # Count travel moves vs extrusion moves
        travels = len(re.findall(r'\nG0\s', text))
        extrudes = len(re.findall(r'\nG1\s.*?E', text))
        if extrudes > 0 and travels > extrudes * 0.3:
            return "stringing"  # high travel ratio = disconnected regions

        # Look for bridge patterns: long X/Y moves at same Z
        bridge_moves = 0
        prev_z = None
        for match in re.finditer(r'G1\s.*?X([\d.]+)\s+Y([\d.]+)\s+Z([\d.]+).*?E([\d.]+)', text):
            z = float(match.group(3))
            e = float(match.group(4))
            if prev_z is not None and abs(z - prev_z) < 0.01 and e > 0.5:
                dx = abs(float(match.group(1)) - prev_x) if 'prev_x' in dir() else 0
                dy = abs(float(match.group(2)) - prev_y) if 'prev_y' in dir() else 0
                if dx > 30 or dy > 30:
                    bridge_moves += 1
            prev_z = z
            prev_x = float(match.group(1))
            prev_y = float(match.group(2))
        if bridge_moves > 3:
            return "bridge"

        return "overhang"

    def _parse_retraction(text: str, yaml_entry: dict) -> float | None:
        """Parse retraction from G-code moves + slicer footer + YAML."""
        # 1. YAML metadata (most reliable)
        yaml_ret = yaml_entry.get("retraction")
        if yaml_ret is not None:
            return float(yaml_ret)

        # 2. PrusaSlicer/Orca footer comment block (last 2KB of file)
        footer = text[-2000:] if len(text) > 2000 else text
        footer_match = re.search(r';\s*retract_length\s*=\s*([\d.]+)', footer, re.I)
        if footer_match:
            return float(footer_match.group(1))

        # 3. G1 E- retraction moves (negative extrusion = retract)
        retract_moves = re.findall(r'G1\s.*?E-([\d.]+)', text)
        if retract_moves:
            return float(retract_moves[0])

        return None

    def _parse_fan(text: str) -> float | None:
        """Parse fan speed from M106 across the WHOLE file + slicer footer."""
        # 1. M106 commands anywhere in the file
        fan_matches = re.findall(r'M106\s+S(\d+)', text)
        if fan_matches:
            # Use the most common non-zero fan speed
            fans = [int(f) for f in fan_matches if int(f) > 0]
            if fans:
                # Convert 0-255 PWM to 0-100%
                fan_val = max(set(fans), key=fans.count)
                return round(fan_val / 255.0 * 100, 1)

        # 2. PrusaSlicer/Orca footer comment block
        footer = text[-3000:] if len(text) > 3000 else text
        for key in ['fan_speed', 'fan_percentage', 'cooling_fan_speed', 'bridge_fan_speed']:
            m = re.search(rf';\s*{key}\s*=\s*([\d.]+)', footer, re.I)
            if m:
                return float(m.group(1))

        # 3. M107 (fan off) — explicit off is valid data
        if re.search(r'M107', text):
            return 0.0

        return None  # Can't determine — skip this row

    # Process each macro run directory
    for macro_dir in sorted(gcode_dir.iterdir()):
        if not macro_dir.is_dir():
            continue

        # Determine failure type from directory name
        dir_name = macro_dir.name.lower()
        failure_type = "good"
        if "stringing" in dir_name:
            failure_type = "stringing"
        elif "underex" in dir_name:
            failure_type = "underextrusion"
        elif "good" in dir_name:
            failure_type = "good"

        outcome = failure_map.get(failure_type, "success")

        # Load YAML metadata if present
        yaml_data = {}
        for yaml_file in macro_dir.glob("*.yaml"):
            try:
                yaml_data = _yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Build lookup from YAML: gcode filename → metadata
        yaml_lookup = {}
        if isinstance(yaml_data, list):
            for entry in yaml_data:
                gcode_name = entry.get("gcode", "")
                if gcode_name:
                    yaml_lookup[gcode_name] = entry

        # Process each G-code file
        for gcode_file in sorted(macro_dir.glob("*.gcode")):
            try:
                full_text = gcode_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Parse settings from the FULL file — use FINAL temps (M109/M190), not preheat
            nozzle_matches = re.findall(r'M109\s+S(\d+)', full_text)  # wait-for-nozzle = final temp
            if not nozzle_matches:
                nozzle_matches = re.findall(r'M104\s+S(\d+)', full_text)
                if nozzle_matches:
                    nozzle_temp = float(nozzle_matches[-1])  # last M104 = final
                else:
                    continue
            else:
                nozzle_temp = float(nozzle_matches[-1])

            bed_matches = re.findall(r'M190\s+S(\d+)', full_text)  # wait-for-bed = final temp
            if not bed_matches:
                bed_matches = re.findall(r'M140\s+S(\d+)', full_text)
            bed_temp = float(bed_matches[-1]) if bed_matches else 60.0

            # Parse fan — skip row if can't determine (RESEARCH-NEEDS.md fix #1)
            fan_pct = _parse_fan(full_text)
            if fan_pct is None:
                continue  # Skip — can't trust fan=0 default

            # Parse filename for material
            fname = gcode_file.name.upper()
            material = "PLA"
            for m in MATERIALS:
                if m in fname:
                    material = m
                    break

            # Get YAML metadata
            yaml_entry = yaml_lookup.get(gcode_file.name, {})

            # Parse retraction (RESEARCH-NEEDS.md fix #2)
            retraction = _parse_retraction(full_text, yaml_entry)
            if retraction is None:
                retraction = 5.0  # fallback default

            # Infer geometry from G-code moves (RESEARCH-NEEDS.md fix #3)
            geometry_type = _infer_geometry_from_gcode(full_text)
            # Override with failure type if it's more specific
            if failure_type == "stringing":
                geometry_type = "stringing"

            # Quality estimate from extrusion multiplier
            ex_mul = float(yaml_entry.get("extrusion_multiplier", yaml_entry.get("ex_mul", 1.0)))
            quality = max(0.1, min(1.0, ex_mul)) if failure_type == "good" else max(0.1, min(0.7, 1.0 - abs(1.0 - ex_mul)))

            records.append(("C", {
                "material": material,
                "geometry_type": geometry_type,
                "env_temp": 22.0,
                "env_humidity": 45.0,
                "nozzle_temp": nozzle_temp,
                "bed_temp": bed_temp,
                "retraction_mm": retraction,
                "fan_pct": fan_pct,
                "first_layer_fan_pct": 0,
                "outcome": outcome,
                "quality": round(quality, 2),
            }))

    return records


# ── Source-type → parser dispatch ─────────────────────────────────────────────

PARSER_DISPATCH = {
    "web_doc": _parse_web_doc,
    "github_repo": _parse_github_repo,
    "prusa_profiles": _parse_prusa_profiles,
    "product_spec": _parse_product_spec,
    "research_repo": _parse_github_repo,
    "bambu_json_profiles": _parse_bambu_json_profiles,
    "klipper_config_repo": _parse_klipper_config_repo,
    "failure_detection_repo": _parse_failure_detection_repo,
    "filament_profiles_repo": _parse_filament_profiles_repo,
    "fdm_error_gcode": _parse_fdm_error_gcode,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Modal App
# ═══════════════════════════════════════════════════════════════════════════════

if modal is not None:
    app = modal.App("chief-engineer-ingest")

    # Persistent volume for caching fetched content (Spanish tutor pattern)
    vol = modal.Volume.from_name("chief-engineer-ingest-data", create_if_missing=True)

    # Image with dependencies
    image = (
        modal.Image.debian_slim()
        .pip_install(
            "datasets", "pyarrow", "huggingface_hub",
            "pydantic>=2.7", "requests", "beautifulsoup4",
            "pyyaml",
        )
        .apt_install("git", "wget")
        # Share enums into the image (Spanish tutor pattern)
        # Must be last — add_local_* after build steps
        .env({"PYTHONPATH": "/root"})
        .add_local_file("core/models.py", "/root/core/models.py")
    )

    # ── HF Dataset Distillation ───────────────────────────────────────────

    @app.function(
        image=image,
        timeout=3600,
        cpu=4,
        memory=4096,
        secrets=[modal.Secret.from_name("chief-engineer-secrets")],
    )
    def distill_hf_dataset(dataset: str, limit: int = 1000, split: str = "train") -> dict:
        """Load an HF dataset, map rows → lane records.

        Special case: 3dtime loads from metadata CSV (not standard rows).
        """
        import csv
        import io
        import requests

        if dataset not in HF_MAPPERS:
            return {"error": f"unknown dataset '{dataset}'; known: {list(HF_MAPPERS)}"}
        hf_id, mapper = HF_MAPPERS[dataset]

        out: dict[str, list] = {"A": [], "B": [], "C": []}

        # 3DTime special case: download metadata CSV + G-code headers
        if dataset == "3dtime":
            csv_url = f"https://huggingface.co/datasets/{hf_id}/resolve/main/metadata/metadata_sub21.csv"
            resp = requests.get(csv_url, timeout=30)
            resp.raise_for_status()
            reader = csv.DictReader(io.StringIO(resp.text))
            rows = list(reader)[:limit]

            for row in rows:
                # Lane A: metadata reference facts
                for lane, rec in mapper(row):
                    if lane in _VALID_LANES:
                        out[lane].append(rec)

                # Lane C: download G-code header + footer, extract settings
                gcode_name = row.get("G-code file name", "")
                if gcode_name:
                    try:
                        gcode_url = f"https://huggingface.co/datasets/{hf_id}/resolve/main/sliced/21/{gcode_name}"
                        # Download header (first 10KB) for nozzle/bed temps
                        gcode_resp = requests.get(gcode_url, stream=True, timeout=15)
                        header = ""
                        for chunk in gcode_resp.iter_content(chunk_size=1024):
                            header += chunk.decode("utf-8", errors="ignore")
                            if len(header) > 10000:
                                break
                        # Also try to get footer (last 3KB) for fan/retraction settings
                        footer = ""
                        try:
                            content_length = gcode_resp.headers.get("Content-Length")
                            if content_length:
                                size = int(content_length)
                                if size > 3000:
                                    footer_resp = requests.get(gcode_url, headers={"Range": f"bytes={size-3000}-{size}"}, timeout=10)
                                    footer = footer_resp.text
                        except Exception:
                            pass
                        full_text = header + footer

                        # Parse nozzle/bed — use FINAL temps (M109/M190)
                        nozzle_matches = re.findall(r'M109\s+S(\d+)', full_text)
                        if not nozzle_matches:
                            nozzle_matches = re.findall(r'M104\s+S(\d+)', full_text)
                        bed_matches = re.findall(r'M190\s+S(\d+)', full_text)
                        if not bed_matches:
                            bed_matches = re.findall(r'M140\s+S(\d+)', full_text)
                        if not nozzle_matches or not bed_matches:
                            continue
                        nozzle_temp = float(nozzle_matches[-1])
                        bed_temp = float(bed_matches[-1])

                        # Parse fan from M106 across full text + slicer footer
                        fan_matches = re.findall(r'M106\s+S(\d+)', full_text)
                        fan_pct = None
                        if fan_matches:
                            fans = [int(f) for f in fan_matches if int(f) > 0]
                            if fans:
                                fan_pct = round(max(set(fans), key=fans.count) / 255.0 * 100, 1)
                        if fan_pct is None:
                            # Check slicer footer comments
                            for key in ['fan_speed', 'fan_percentage', 'cooling_fan_speed', 'bridge_fan_speed']:
                                m = re.search(rf';\s*{key}\s*=\s*([\d.]+)', full_text, re.I)
                                if m:
                                    fan_pct = float(m.group(1))
                                    break
                        if fan_pct is None and re.search(r'M107', full_text):
                            fan_pct = 0.0  # explicit fan off
                        if fan_pct is None:
                            continue  # Skip — can't determine fan (RESEARCH-NEEDS.md fix)

                        material_map = {"pla": "PLA", "pet": "PETG", "abs": "ABS", "tpu": "TPU"}
                        material = material_map.get(str(row.get("Material", "")).lower(), "PLA")

                        # Parse retraction from footer or G-code
                        retraction = 5.0
                        footer_ret = re.search(r';\s*retract_length\s*=\s*([\d.]+)', full_text, re.I)
                        if footer_ret:
                            retraction = float(footer_ret.group(1))
                        else:
                            retract_moves = re.findall(r'G1\s.*?E-([\d.]+)', full_text)
                            if retract_moves:
                                retraction = float(retract_moves[0])

                        # Geometry from bounding box (3DTime has no G-code move context in header)
                        try:
                            bx, by, bz = float(row["Bounding box X (mm)"]), float(row["Bounding box Y (mm)"]), float(row["Bounding box Z (mm)"])
                        except (KeyError, ValueError):
                            bx, by, bz = 50, 50, 20
                        ratio = bx / max(by, 0.1)
                        if bz < 5:
                            geometry = "vase"
                        elif ratio > 5:
                            geometry = "bridge"
                        elif bz > bx * 0.8:
                            geometry = "adhesion"
                        else:
                            geometry = "overhang"

                        out["C"].append({
                            "material": material,
                            "geometry_type": geometry,
                            "env_temp": 22.0,
                            "env_humidity": 45.0,
                            "nozzle_temp": float(nozzle_matches[-1]),
                            "bed_temp": float(bed_matches[-1]),
                            "retraction_mm": retraction,
                            "fan_pct": fan_pct,
                            "first_layer_fan_pct": 0,
                            "outcome": "success",
                            "quality": 0.85,
                        })
                    except Exception:
                        pass
            out["stats"] = {
                "dataset": dataset, "hf_id": hf_id, "rows": len(rows),
                "A": len(out["A"]), "B": len(out["B"]), "C": len(out["C"]),
            }
            return out

        # Standard HF dataset
        from datasets import load_dataset
        ds = load_dataset(hf_id, split=f"{split}[:{limit}]")
        for row in ds:
            for lane, rec in mapper(dict(row)):
                if lane in _VALID_LANES:
                    out[lane].append(rec)
        out["stats"] = {
            "dataset": dataset, "hf_id": hf_id, "rows": len(ds),
            "A": len(out["A"]), "B": len(out["B"]), "C": len(out["C"]),
        }
        return out

    # ── Documentation Source Fetching ─────────────────────────────────────

    @app.function(
        image=image,
        volumes={"/data": vol},
        timeout=600,
        secrets=[modal.Secret.from_name("chief-engineer-secrets")],
    )
    def fetch_and_parse_source(source_key: str) -> dict:
        """Fetch a documentation source, parse it, return lane records.

        Uses Modal Volume for caching: if already fetched, skips download.
        Idempotent/resumable (Spanish tutor pattern).
        """
        import requests
        import subprocess
        import tempfile

        if source_key not in SOURCES:
            return {"error": f"unknown source '{source_key}'", "source_key": source_key}

        url, category, source_type, description = SOURCES[source_key]
        cache_dir = Path("/data/cache")
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache key from URL hash
        cache_key = hashlib.md5(url.encode()).hexdigest()[:12]
        content_path = cache_dir / f"{source_key}_{cache_key}.txt"
        records_path = cache_dir / f"{source_key}_{cache_key}_records.json"

        # Check cache — idempotent/resumable
        if records_path.exists():
            try:
                cached = json.loads(records_path.read_text())
                print(f"  ✓ {source_key}: loaded from cache ({cached.get('stats', {}).get('total', 0)} records)")
                return cached
            except Exception:
                pass

        # Fetch content
        content = ""
        if source_type == "github_repo" or source_type == "research_repo" or source_type in ("bambu_json_profiles", "klipper_config_repo", "failure_detection_repo", "filament_profiles_repo", "fdm_error_gcode"):
            # Download repo as zip (more reliable than git clone on Modal)
            repo_name = url.rstrip("/").split("/")[-1]
            repo_dir = cache_dir / f"repo_{source_key}_{cache_key}"
            if not repo_dir.exists():
                print(f"  downloading {url} → {repo_dir}")
                zip_url = f"https://github.com/{url.split('github.com/')[-1]}/archive/refs/heads/main.zip"
                try:
                    resp = requests.get(zip_url, timeout=120, headers={"User-Agent": "chief-engineer/1.0"})
                    resp.raise_for_status()
                    import zipfile as _zipfile
                    import io as _io
                    with _zipfile.ZipFile(_io.BytesIO(resp.content)) as zf:
                        # Extract all files, stripping the top-level directory
                        for member in zf.namelist():
                            # Strip the leading repo-name-branch directory
                            parts = member.split("/", 1)
                            if len(parts) > 1:
                                target = repo_dir / parts[1]
                                if member.endswith("/"):
                                    target.mkdir(parents=True, exist_ok=True)
                                else:
                                    target.parent.mkdir(parents=True, exist_ok=True)
                                    with zf.open(member) as src, open(target, "wb") as dst:
                                        dst.write(src.read())
                    print(f"  ✓ extracted to {repo_dir}")
                except Exception as e:
                    print(f"  ⚠ download failed: {e}")
                    return {"error": f"download failed: {e}", "source_key": source_key}

            # Parse the cloned repo
            records = _parse_github_repo(str(repo_dir), url, source_key)
            content = f"[cloned repo at {repo_dir}]"

        elif source_type == "prusa_profiles":
            # Download INI files from PrusaSlicer repository
            print(f"  fetching Prusa profiles from {url}")
            try:
                resp = requests.get(url, timeout=30, headers={"User-Agent": "chief-engineer/1.0"})
                resp.raise_for_status()
                content = resp.text
                # Parse INI content
                records = _parse_prusa_profiles(content, url, source_key)
            except Exception as e:
                print(f"  ⚠ fetch failed: {e}")
                return {"error": f"fetch failed: {e}", "source_key": source_key}

        else:
            # web_doc, product_spec — fetch HTML
            print(f"  fetching {url}")
            try:
                resp = requests.get(url, timeout=30, headers={"User-Agent": "chief-engineer/1.0"})
                resp.raise_for_status()
                content = resp.text
            except Exception as e:
                print(f"  ⚠ fetch failed: {e}")
                return {"error": f"fetch failed: {e}", "source_key": source_key}

            # Parse based on source type
            parser = PARSER_DISPATCH.get(source_type, _parse_web_doc)
            records = parser(content, url, source_key)

        # Save content cache
        content_path.write_text(content[:50000], encoding="utf-8")  # truncate for cache

        # Build result
        out: dict[str, list] = {"A": [], "B": [], "C": []}
        for lane, rec in records:
            if lane in _VALID_LANES:
                out[lane].append(rec)

        stats = {
            "source_key": source_key,
            "category": category,
            "url": url,
            "A": len(out["A"]),
            "B": len(out["B"]),
            "C": len(out["C"]),
            "total": len(records),
        }
        out["stats"] = stats

        # Cache records
        records_path.write_text(json.dumps(out))

        # Commit volume (Spanish tutor pattern)
        vol.commit()

        print(f"  ✓ {source_key}: {stats['total']} records (A:{stats['A']} B:{stats['B']} C:{stats['C']})")
        return out

    # ── Main Entrypoint ───────────────────────────────────────────────────

    @app.local_entrypoint()
    def main(
        source: str = "",
        category: str = "",
        dataset: str = "",
        limit: int = 1000,
    ):
        """Run locally: fan out to Modal, then write artifacts.

        Usage:
            modal run ingest/modal_app.py                          # all sources
            modal run ingest/modal_app.py --source klipper-config  # single source
            modal run ingest/modal_app.py --category calibration   # category
            modal run ingest/modal_app.py --dataset 3d-adam       # HF dataset
        """
        root = Path(__file__).resolve().parent.parent
        agg: dict[str, list] = {"A": [], "B": [], "C": []}

        # ── Process documentation sources ──
        if not dataset:
            targets = []
            if source:
                if source not in SOURCES:
                    print(f"Unknown source: {source}")
                    print(f"Known sources: {list(SOURCES.keys())}")
                    return
                targets = [source]
            elif category:
                targets = [k for k, v in SOURCES.items() if v[1] == category]
                if not targets:
                    print(f"No sources in category '{category}'")
                    print(f"Categories: {set(v[1] for v in SOURCES.values())}")
                    return
            else:
                targets = list(SOURCES.keys())

            print(f"Processing {len(targets)} documentation sources...\n")
            for src_key in targets:
                res = fetch_and_parse_source.remote(src_key)
                stats = res.get("stats", res)
                if "error" in stats:
                    print(f"  ✗ {src_key}: {stats['error']}")
                else:
                    print(f"  ✓ {src_key}: A={stats.get('A',0)} B={stats.get('B',0)} C={stats.get('C',0)}")
                for lane in ("A", "B", "C"):
                    agg[lane].extend(res.get(lane, []))

        # ── Process HF datasets ──
        if dataset:
            targets = [dataset] if dataset else list(HF_MAPPERS)
            print(f"Processing {len(targets)} HF datasets...\n")
            for d in targets:
                res = distill_hf_dataset.remote(d, limit)
                stats = res.get("stats", res)
                print(f"  {stats}")
                for lane in ("A", "B", "C"):
                    agg[lane].extend(res.get(lane, []))

        # ── Write artifacts ──
        def _write(path: Path, rows: list, append: bool):
            if not rows:
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a" if append else "w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            print(f"  wrote {len(rows)} → {path.relative_to(root)}")

        print(f"\n── Artifacts ──")
        _write(root / "data" / "references.jsonl", agg["A"], append=True)
        _write(root / "data" / "_modal_candidate_lessons.jsonl", agg["B"], append=True)
        _write(root / "sim" / "calibration" / "observations.modal.jsonl", agg["C"], append=True)

        print(f"\n── Summary ──")
        print(f"  Lane A (references):     {len(agg['A'])}")
        print(f"  Lane B (candidate lessons): {len(agg['B'])}  ← REVIEW before ledger!")
        print(f"  Lane C (calibration obs):  {len(agg['C'])}")
        print(f"\nNext:")
        print(f"  • REVIEW data/_modal_candidate_lessons.jsonl (honesty gate)")
        print(f"  • Fold good lessons into ledger via ingest_candidate_lessons")
        print(f"  • Calibrate: uv run python -m sim.calibrate --data sim/calibration/observations.modal.jsonl")
        print(f"  • make test  →  make run")

    # FRONTIER (named in writeup, NOT in-window):
    # Fine-tune a small Gemma on the accumulated ledger.
    # @app.function(gpu="A10G", image=image, timeout=3600)
    # def finetune_on_ledger(...): ...


if __name__ == "__main__":
    print("Modal ingestion app for Chief Engineer.")
    print(f"  {len(SOURCES)} documentation sources registered")
    print(f"  {len(HF_MAPPERS)} HF dataset mappers registered")
    print()
    print("Categories:")
    for cat in sorted(set(v[1] for v in SOURCES.values())):
        count = sum(1 for v in SOURCES.values() if v[1] == cat)
        print(f"  {cat}: {count} sources")
    print()
    print("Run:")
    print("  modal run ingest/modal_app.py                          # all sources")
    print("  modal run ingest/modal_app.py --source klipper-thermistors")
    print("  modal run ingest/modal_app.py --category calibration")
    print("  modal run ingest/modal_app.py --dataset 3d-adam --limit 2000")
