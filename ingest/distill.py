"""Knowledge distiller — turn structured sources into Chief Engineer knowledge.

Two outputs, matching how the sources actually carry information:

1. **Reference facts** (material baselines from slicer/firmware configs) →
   `data/references.jsonl`. Injected into the prompt as a "Material Reference"
   block. These are NOT env-keyed precedent — they're hard parameters.
2. **Candidate lessons** (research distilled into env-keyed rows) → appended to
   the ledger as `source="ingested"`, retrieved exactly like seed/earned lessons.

Deterministic + stdlib (configparser/regex). License-safe: we ingest *profile
data*, never slicer code. No OrcaSlicer/PrusaSlicer imports.
"""

from __future__ import annotations

import configparser
import json
import re
from pathlib import Path

from pydantic import BaseModel

from core.ledger import LedgerManager
from core.models import LessonEntry, MATERIALS

DATA = Path(__file__).resolve().parent.parent / "data"
REFERENCES_PATH = DATA / "references.jsonl"


class ReferenceFact(BaseModel):
    material: str
    param: str            # "nozzle_temp" | "bed_temp" | "retraction_mm" | "max_temp" | ...
    value: float
    source: str           # where it came from (filename / profile)


def _material_of(text: str) -> str | None:
    up = text.upper()
    for m in MATERIALS:
        if m in up:
            return m
    if "ACETAL" in up or "DELRIN" in up:
        return None
    return None


# --- 3D-ADAM defect taxonomy (encoded from the paper's defect classes) ------
# RAG-ready risk knowledge keyed to the geometry/condition that triggers it.
DEFECT_TAXONOMY = {
    "warping": {"risk": "warping", "trigger": "high-shrinkage material on a cool/draughty bed",
                "note": "corners lift as lower layers cool and contract; raise bed temp, enclose, slow first layer."},
    "under_extrusion": {"risk": "under_extrusion", "trigger": "too-low temp / too-fast flow / partial clog",
                        "note": "gaps and weak walls; raise temp or slow down, check for moisture and clogs."},
    "stringing": {"risk": "stringing", "trigger": "wet filament or hot travel",
                  "note": "fine whiskers across gaps; dry filament first, then lower temp / tune retraction."},
    "cracking": {"risk": "delamination", "trigger": "over-cooling on tall prints / poor layer bond",
                 "note": "layers split under stress; reduce fan, raise temp, enclose for ABS."},
}


def parse_prusa_ini(path: Path) -> list[ReferenceFact]:
    """Extract per-filament baselines from a PrusaSlicer-style INI (data only)."""
    facts: list[ReferenceFact] = []
    cp = configparser.ConfigParser(strict=False, interpolation=None)
    try:
        cp.read(path, encoding="utf-8")
    except Exception:
        return facts
    for section in cp.sections():
        mat = _material_of(section)
        if not mat:
            continue
        src = f"{path.name}:[{section}]"
        kv = cp[section]

        def first_num(raw: str | None) -> float | None:
            if not raw:
                return None
            m = re.search(r"-?\d+(?:\.\d+)?", raw.split(",")[0])
            return float(m.group()) if m else None

        for key, param in (
            ("temperature", "nozzle_temp"),
            ("first_layer_temperature", "nozzle_temp"),
            ("bed_temperature", "bed_temp"),
            ("retract_length", "retraction_mm"),
        ):
            v = first_num(kv.get(key))
            if v is not None:
                facts.append(ReferenceFact(material=mat, param=param, value=v, source=src))
    return facts


def parse_klipper_cfg(path: Path) -> list[ReferenceFact]:
    """Pull safety-relevant limits from a Klipper printer.cfg ([extruder] max_temp)."""
    facts: list[ReferenceFact] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return facts
    for section, param in (("extruder", "max_temp"), ("heater_bed", "bed_max_temp")):
        m = re.search(rf"\[{section}\][^\[]*?max_temp\s*[:=]\s*(\d+(?:\.\d+)?)", text, re.S | re.I)
        if m:
            facts.append(ReferenceFact(material="*", param=param, value=float(m.group(1)),
                                       source=f"{path.name}:[{section}]"))
    return facts


def parse_marlin_config(path: Path) -> list[ReferenceFact]:
    """Pull hotend/bed max temps from a Marlin Configuration.h (#define ... MAXTEMP)."""
    facts: list[ReferenceFact] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return facts
    for define, param in (("HEATER_0_MAXTEMP", "max_temp"), ("BED_MAXTEMP", "bed_max_temp")):
        m = re.search(rf"#define\s+{define}\s+(\d+)", text)
        if m:
            facts.append(ReferenceFact(material="*", param=param, value=float(m.group(1)),
                                       source=f"{path.name}:{define}"))
    return facts


def parse_prusa_config(path: Path) -> list[ReferenceFact]:
    """Parse a PrusaSlicer flat config — the `; key = value` block inside a `.3mf`
    project (Metadata/*.config) or a standalone exported `.config`/`.ini`. Carries
    REAL per-filament settings incl. fan (which the slicer/firmware configs above
    don't). One filament_type per file; source = the profile id (curated)."""
    try:
        if path.suffix.lower() == ".3mf":
            import zipfile
            with zipfile.ZipFile(path) as z:
                name = next((n for n in z.namelist() if n.lower().endswith(".config")), None)
                if not name:
                    return []
                text = z.read(name).decode("utf-8", "ignore")
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    def get(key: str) -> str | None:
        m = re.search(rf"(?mi)^[;\s]*{re.escape(key)}\s*=\s*(.+)$", text)
        return m.group(1).strip().strip('"') if m else None

    def num(raw: str | None) -> float | None:
        if not raw:
            return None
        m = re.search(r"-?\d+(?:\.\d+)?", raw.split(",")[0])
        return float(m.group()) if m else None

    mat = (get("filament_type") or "").upper()
    if mat not in MATERIALS:
        return []
    src = (get("filament_settings_id") or path.stem) + (" (3mf)" if path.suffix.lower() == ".3mf" else "")
    facts: list[ReferenceFact] = []
    for key, param in (("temperature", "nozzle_temp"), ("first_layer_temperature", "nozzle_temp"),
                       ("bed_temperature", "bed_temp"), ("retract_length", "retraction_mm"),
                       ("max_fan_speed", "fan_pct")):
        v = num(get(key))
        if v is not None:
            facts.append(ReferenceFact(material=mat, param=param, value=v, source=src))
    return facts


def parse_octoprint_history(path: Path) -> list[dict]:
    """Extract Lane-B lesson candidates from an OctoPrint print-job-history CSV.
    The `result` column is COMPLETION status, not print quality (a 'success' row can
    read 'very stringy'), and fan/retraction/geometry/humidity aren't recorded — so
    this yields *lessons from the Note field*, not calibration rows. Honesty gate:
    only emit a lesson when the note names a real defect/outcome. Neutral env (the
    history doesn't log room conditions)."""
    import csv as _csv

    KEYWORDS = {  # note phrase → (outcome, geometry, what it teaches)
        "string": ("failed_stringing", "stringing"),
        "sag": ("failed_sag", "overhang"),
        "droop": ("failed_sag", "overhang"),
        "warp": ("failed_sag", "adhesion"),
        "curl": ("failed_sag", "adhesion"),
        "lift": ("failed_sag", "adhesion"),
        "rough": ("success", "adhesion"),        # finish note, not a hard failure
    }
    out: list[dict] = []
    try:
        rows = list(_csv.DictReader(path.open(encoding="utf-8")))
    except Exception:
        return out
    for r in rows:
        note = (r.get("Note") or "").strip()
        if note in ("", "-"):
            continue
        mat = (r.get("Material") or "").upper().replace("_PLUS", "").replace("PLA_PLUS", "PLA")
        if mat not in MATERIALS:
            continue
        m = re.search(r"_(\d{3})C_", r.get("File Name", ""))
        noz = m.group(1) if m else "?"
        low = note.lower()
        hit = next(((o, g) for k, (o, g) in KEYWORDS.items() if k in low), None)
        if not hit:
            continue
        outcome, geo = hit
        out.append({
            "job_id": f"octo-{r.get('Start Datetime [dd.mm.yyyy hh:mm]','')[:10].replace('.','')}",
            "material": mat, "geometry_type": geo, "env_temp": 22.0, "env_humidity": 50.0,
            "outcome": outcome,
            "lesson": f"My own print ({mat} at ~{noz}°C nozzle): \"{note}\". ",
            "source": "ingested", "_note": note, "_file": r.get("File Name", ""),
        })
    return out


def write_references(facts: list[ReferenceFact]) -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    with REFERENCES_PATH.open("w", encoding="utf-8") as f:
        for fact in facts:
            f.write(fact.model_dump_json() + "\n")
    return len(facts)


def load_references() -> list[ReferenceFact]:
    if not REFERENCES_PATH.exists():
        return []
    out = []
    for line in REFERENCES_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(ReferenceFact(**json.loads(line)))
            except Exception:
                continue
    return out


# Params injected as material baselines — restricted to ones we have HIGH-CONFIDENCE
# (curated config) values for. Deliberately excludes fan_pct/first_layer_fan_pct
# (only present from bulk 3DTime G-code headers where M106 was unparsed → defaulted
# to ~0, which is wrong and misleading) and the noisy modal-only advance params.
# Everything the ingestion collects still lives in data/references.jsonl as a dataset;
# this is just what's trustworthy enough to put in front of the model.
_PROMPT_PARAMS = ("nozzle_temp", "bed_temp", "retraction_mm", "fan_pct",
                  "max_temp", "bed_max_temp")
# Params we trust ONLY from curated configs, never from bulk modal/3DTime parses
# (fan was defaulted to ~0 by the G-code header extractor). So fan reaches the prompt
# only when a real slicer profile supplies it.
_CURATED_ONLY = {"fan_pct", "first_layer_fan_pct"}
# Sane physical ranges — drop parse-garbage (e.g. a G-code header that yields
# bed_temp=12 or nozzle_temp=120 from a misread M-code) before it reaches the model.
_SANE_RANGE = {
    "nozzle_temp": (170, 320), "bed_temp": (40, 130), "max_temp": (200, 350),
    "bed_max_temp": (60, 150), "retraction_mm": (0.2, 8.0), "fan_pct": (0, 100),
    "first_layer_fan_pct": (0, 100), "pressure_advance": (0.0, 1.5),
    "linear_advance_k": (0.0, 2.0), "shore_hardness": (0, 100),
}
_REF_ORDER = ("nozzle_temp", "bed_temp", "retraction_mm", "fan_pct", "max_temp", "bed_max_temp")


def material_facts(material: str, facts: list[ReferenceFact] | None = None,
                   params: tuple[str, ...] | None = None) -> dict[str, dict]:
    """On-demand reference lookup for ONE material: curated + range-filtered +
    aggregated. Returns {param: {value(median), lo, hi, n, sources}}. The bulk
    model-metadata params are excluded; out-of-range parse noise is dropped. This
    is the single source the prompt block and any targeted fact lookup draw from —
    facts are fetched per request, not bulk-injected."""
    facts = facts if facts is not None else load_references()
    want = set(params) if params else set(_PROMPT_PARAMS)
    # split curated (slicer/firmware/profile configs — precise) from bulk
    # (modal/3DTime/gcode-derived — high volume, lower precision). Prefer curated.
    cur: dict[str, list[tuple[float, str]]] = {}
    bulk: dict[str, list[tuple[float, str]]] = {}
    for f in facts:
        if f.material not in (material, "*") or f.param not in want:
            continue
        lo, hi = _SANE_RANGE.get(f.param, (float("-inf"), float("inf")))
        if not (lo <= f.value <= hi):
            continue
        head = f.source.split(":")[0]
        bucket = bulk if head.startswith(("modal", "ablam")) else cur
        bucket.setdefault(f.param, []).append((f.value, head))
    out: dict[str, dict] = {}
    for p in want:
        # authoritative first; bulk only if no curated AND the param is bulk-trustworthy
        pairs = cur.get(p) or (None if p in _CURATED_ONLY else bulk.get(p))
        if not pairs:
            continue
        vals = sorted(v for v, _ in pairs)
        out[p] = {"value": vals[len(vals) // 2], "lo": vals[0], "hi": vals[-1],
                  "n": len(vals), "sources": sorted({s for _, s in pairs})[:3]}
    return out


def lookup_fact(material: str, param: str, facts: list[ReferenceFact] | None = None) -> dict | None:
    """On-demand single-fact lookup (material+global), aggregated. None if unknown."""
    return material_facts(material, facts, params=(param,)).get(param)


def reference_block(material: str, facts: list[ReferenceFact] | None = None,
                    max_lines: int = 8) -> list[str]:
    """Lean prompt lines for THIS material — one aggregated line per useful param
    (median + observed range + source count), capped. Computed on demand, so the
    1,300-row reference corpus never floods the prompt (was 500+ lines/material)."""
    md = material_facts(material, facts)
    lines: list[str] = []
    for p in _REF_ORDER:
        d = md.get(p)
        if not d:
            continue
        rng = f" (range {d['lo']:g}–{d['hi']:g}, n={d['n']})" if d["n"] > 1 else ""
        src = f" [{', '.join(d['sources'])}]" if d["sources"] else ""
        lines.append(f"{p}≈{d['value']:g}{rng}{src}")
        if len(lines) >= max_lines:
            break
    return lines


def ingest_candidate_lessons(path: Path, ledger: LedgerManager) -> int:
    """Append research-distilled env-keyed rows to the ledger as source='ingested'."""
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            row["source"] = "ingested"
            ledger.append(LessonEntry(**row))
            n += 1
        except Exception:
            continue
    return n
