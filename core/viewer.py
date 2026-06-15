"""3D preview helpers + G-code readout.

gr.Model3D gives orbit/zoom/pan for free. We keep trimesh use minimal: pick a
sample mesh for the geometry_type (or use an uploaded one) and, where it helps,
locate the steepest overhang so a risk callout anchors to something real. Risk
regions render as labeled callouts beside the interactive model — robust, and
the model stays interactive. No slicing, no simulation.
"""

from __future__ import annotations

from pathlib import Path

from .models import PrintSettings, RiskRegion
from .theme import icon

ASSETS = Path(__file__).resolve().parent.parent / "assets"
DATA = Path(__file__).resolve().parent.parent / "data"
_SAMPLE = {
    "overhang": "overhang.glb",
    "bridge": "bridge.glb",
    "vase": "vase.glb",
    "stringing": "cube.glb",
    "adhesion": "cube.glb",
}


def sample_mesh(geometry_type: str) -> str | None:
    path = ASSETS / _SAMPLE.get(geometry_type, "cube.glb")
    return str(path) if path.exists() else None


PART_LABEL = {
    "overhang": "OVERHANG TEST", "bridge": "BRIDGE TEST", "vase": "VASE (THIN WALL)",
    "stringing": "STRINGING TOWER", "adhesion": "ADHESION CUBE",
}


def benchy_mesh() -> str | None:
    """The CC0 3DBenchy, IF dropped into assets/benchy.glb (can't fetch on a
    locked Space; Kyle adds it locally). None → caller shows a 'add the file' hint."""
    p = ASSETS / "benchy.glb"
    return str(p) if p.exists() else None


_PRIMITIVES = ("box", "cylinder", "cone", "sphere")
# which geometry_type (the model's reasoning class) each primitive maps to
_PRIM_GEO = {"box": "adhesion", "cylinder": "vase", "cone": "overhang", "sphere": "overhang"}


def generate_primitive(kind: str, size_mm: float = 30.0) -> tuple[str, str]:
    """Generate a parametric primitive with trimesh → (mesh_path, geometry_type).
    Offline, zero new deps. Saved to data/_generated.glb for the preview/slicer."""
    import trimesh

    s = max(5.0, float(size_mm))
    kind = kind if kind in _PRIMITIVES else "box"
    if kind == "box":
        m = trimesh.creation.box(extents=(s, s, s))
    elif kind == "cylinder":
        m = trimesh.creation.cylinder(radius=s / 2, height=s)
    elif kind == "cone":
        m = trimesh.creation.cone(radius=s / 2, height=s)
    else:
        m = trimesh.creation.icosphere(radius=s / 2)
    m.apply_translation(-m.bounds[0])  # sit on the bed (z ≥ 0)
    DATA.mkdir(exist_ok=True)
    out = DATA / "_generated.glb"
    m.export(out)
    return str(out), _PRIM_GEO[kind]


# one-line human read for each inferred class — surfaced read-only ("the engineer
# reads this as …"), never a control the user sets.
GEO_READS = {
    "overhang": "overhang-dominant",
    "bridge": "has unsupported spans (bridging)",
    "vase": "tall thin-wall (vase-like)",
    "adhesion": "wide flat base (adhesion-critical)",
    "stringing": "many travel moves (stringing-prone)",
}


def infer_geometry(mesh_path: str | None) -> tuple[str, str]:
    """Classify the failure-mode the engineer should reason about, straight from
    the mesh — the user never picks it (the system figures it out). Returns
    (geometry_type, one-line read). Falls back to 'overhang' (the most common
    torture-test failure) when the mesh can't be read."""
    if not mesh_path or not Path(mesh_path).exists():
        return "overhang", GEO_READS["overhang"]
    try:
        import math

        import trimesh

        mesh = trimesh.load(mesh_path, force="mesh")
        w, d, h = (float(x) for x in mesh.bounding_box.extents)
        base = max(w, d, 1e-6)
        footprint = max(1e-6, w * d)
        downward = -mesh.face_normals[:, 2]            # +1 → horizontal ceiling (downward-facing)
        steep = float(downward.max()) if len(downward) else 0.0
        angle = math.degrees(math.asin(min(1.0, max(0.0, steep))))   # overhang angle from vertical
        ceiling = float(mesh.area_faces[downward > 0.94].sum()) if len(downward) else 0.0
        try:
            solidity = float(mesh.volume) / max(1e-6, w * d * h)
        except Exception:
            solidity = 1.0

        if h > 2.0 * base and solidity < 0.35:         # tall + mostly hollow → thin-wall shell
            return "vase", GEO_READS["vase"]
        if ceiling > 0.10 * footprint:                 # flat unsupported span → bridging
            return "bridge", GEO_READS["bridge"]
        if angle >= 45:                                # steep angled face → overhang
            return "overhang", GEO_READS["overhang"]
        if h < 0.5 * base:                             # wide + low → big bed contact
            return "adhesion", GEO_READS["adhesion"]
        return "stringing", GEO_READS["stringing"]
    except Exception:
        return "overhang", GEO_READS["overhang"]


def settings_panel_html(settings: PrintSettings, material: str) -> str:
    """Render proposed settings as an LCARS instrument readout (not raw JSON)."""
    rows = [
        ("NOZZLE", f"{settings.nozzle_temp:.0f}", "°C"),
        ("BED", f"{settings.bed_temp:.0f}", "°C"),
        ("RETRACTION", f"{settings.retraction_mm:.1f}", "mm"),
        ("FAN", f"{settings.fan_pct:.0f}", "%"),
        ("FIRST-LAYER FAN", f"{settings.first_layer_fan_pct:.0f}", "%"),
    ]
    cells = "".join(
        "<div style='display:flex;justify-content:space-between;align-items:baseline;"
        "border-bottom:1px solid var(--ao-outline-dim);padding:5px 2px;'>"
        f"<span style='color:var(--ao-orange);letter-spacing:1.5px;font-size:10px;'>{name}</span>"
        f"<span style='color:var(--ao-text);font-size:15px;font-weight:700;'>{val}"
        f"<span style='color:var(--ao-outline);font-size:10px;'> {unit}</span></span></div>"
        for name, val, unit in rows
    )
    return (
        "<div style='font-family:ui-monospace,monospace;background:var(--ao-void);"
        "border:1px solid var(--ao-outline-dim);border-left:3px solid var(--ao-orange);padding:8px 12px;'>"
        f"<div style='color:var(--ao-orange);font-weight:700;letter-spacing:2px;font-size:11px;"
        f"margin-bottom:4px;'>PROPOSED SETTINGS · {material} <span style='color:var(--ao-outline);"
        "font-weight:400;'>(SPINE-VALIDATED)</span></div>" + cells + "</div>"
    )


def gcode_panel_html(settings: PrintSettings, material: str) -> str:
    """The g-code readout as a styled terminal panel (not gr.Code)."""
    body = gcode_readout(settings, material).replace("<", "&lt;")
    return (
        "<div style='font-family:ui-monospace,monospace;background:var(--ao-void);"
        "border:1px solid var(--ao-outline-dim);padding:8px 12px;'>"
        "<div style='color:var(--ao-orange);font-weight:700;letter-spacing:2px;font-size:11px;'>"
        "START G-CODE <span style='color:var(--ao-outline);font-weight:400;'>(HEADER TIED TO SETTINGS)</span></div>"
        f"<pre style='color:var(--ao-blue);font-size:11px;margin:6px 0 0;white-space:pre-wrap;'>{body}</pre></div>"
    )


def steepest_overhang_hint(mesh_path: str | None) -> str | None:
    """Optional: report where the steepest downward-facing face sits (minimal trimesh)."""
    if not mesh_path or not Path(mesh_path).exists():
        return None
    try:
        import numpy as np
        import trimesh

        mesh = trimesh.load(mesh_path, force="mesh")
        import math
        normals = mesh.face_normals
        downward = normals[:, 2]               # -1 = fully downward-facing
        idx = int(downward.argmin())
        steep = -float(downward[idx])          # 0..1; 1 = horizontal ceiling
        if steep > 0.30:                       # meaningfully overhanging
            angle = math.degrees(math.asin(min(1.0, steep)))   # overhang angle from vertical
            c = mesh.triangles_center[idx]
            note = f"steepest overhang ~{angle:.0f}° near (x={c[0]:.0f}, y={c[1]:.0f}, z={c[2]:.0f}) mm"
            if angle >= 50:                    # past the usual support threshold
                note += " — likely needs supports (or reorient to reduce it)"
            return note
    except Exception:
        return None
    return None


def risk_callouts_html(risks: list[RiskRegion], geo_hint: str | None = None) -> str:
    if not risks:
        body = "<div style='color:var(--ao-green);'>No failure regions flagged.</div>"
    else:
        rows = []
        for r in risks:
            anchor = f" · {r.anchor_hint}" if r.anchor_hint else ""
            rows.append(
                f"<div style='border-left:3px solid var(--ao-red);background:var(--ao-surface);"
                f"padding:6px 10px;margin:5px 0;font-family:ui-monospace,monospace;font-size:12px;'>"
                f"<span style='color:var(--ao-red);font-weight:700;'>{icon('alert')} {r.risk.upper()}</span> "
                f"<span style='color:var(--ao-text);'>@ {r.location}{anchor}</span>"
                f"<div style='color:var(--ao-outline);'>{r.why}</div></div>"
            )
        body = "".join(rows)
    if geo_hint:
        body += f"<div style='color:var(--ao-outline);font-size:11px;font-family:ui-monospace,monospace;'>↳ {geo_hint}</div>"
    return f"<div><div style='color:var(--ao-orange);font-family:ui-monospace,monospace;font-size:11px;'>PREDICTED FAILURE REGIONS</div>{body}</div>"


_VERDICT = {"failed_sag": "sagged", "failed_stringing": "strung", "success": "printed clean"}


def precedent_eval_html(retrieved, env) -> str:
    """The load-bearing moment, narrated deterministically from the env delta.

    Makes the "humidity is higher than the job that sagged" framing reliable on
    screen even before the model's prose — the model's reasoning then adds to it.
    """
    if not retrieved:
        return (
            "<div style='border-left:3px solid var(--ao-purple);background:var(--ao-surface);"
            "padding:10px 14px;font-family:ui-monospace,monospace;'>"
            "<div style='color:var(--ao-purple);font-weight:700;letter-spacing:1px;'>NO CLOSE PRECEDENT</div>"
            "<div style='color:var(--ao-text);'>Nothing in the ledger matches this material + geometry. "
            "Reasoning from material properties — and saying so. Knowing what it doesn't know is the point.</div></div>"
        )
    e, dist = retrieved[0]
    dt = env.temp - e.env_temp
    dh = env.humidity - e.env_humidity

    def phrase(delta, unit, hi, lo):
        if abs(delta) < 1:
            return f"about the same {unit}"
        return f"{abs(delta):.0f}{unit} {hi if delta > 0 else lo}"

    t_ph = phrase(dt, "°C", "warmer", "cooler")
    h_ph = phrase(dh, " pts", "more humid", "drier")
    verdict = _VERDICT.get(e.outcome, e.outcome)

    failed = e.outcome.startswith("failed")
    worse = (e.geometry_type in ("overhang", "bridge") and dt > 1) or ("string" in e.geometry_type and dh > 1)
    if failed and worse:
        impl = "Conditions are <b>worse</b> than that failure — expect the same risk and adjusting to prevent it."
        col = "var(--ao-red)"
    elif failed and not worse:
        impl = "Conditions are <b>better</b> than that failure — the original cause is less likely now."
        col = "var(--ao-orange)"
    else:
        impl = "That job succeeded under similar conditions — leaning on what worked."
        col = "var(--ao-green)"

    return (
        f"<div style='border-left:3px solid {col};background:var(--ao-surface);"
        f"padding:10px 14px;font-family:ui-monospace,monospace;'>"
        f"<div style='color:var(--ao-orange);font-weight:700;letter-spacing:1px;'>PRECEDENT EVALUATION</div>"
        f"<div style='color:var(--ao-text);'>Nearest prior job <b>{e.job_id}</b> ({e.source}) — "
        f"{e.material}/{e.geometry_type} <b>{verdict}</b> at {e.env_temp:.0f}°C / {e.env_humidity:.0f}% RH.<br>"
        f"Right now it's <b>{t_ph}</b> and <b>{h_ph}</b> (env-distance {dist:.2f}).<br>{impl}</div></div>"
    )


_POS_SHRINK = {"ABS": "high", "PETG": "moderate", "PLA": "low", "TPU": "low"}


def placement_callout(material: str, bed_position: str) -> str:
    """Deterministic build-plate placement risk + suggested alignment. Bed edges/
    corners run cooler + draftier → warp/adhesion risk, worst for high-shrink
    materials. Returns an HTML block (or '' when centered/low-risk)."""
    pos = (bed_position or "center").lower()
    if pos == "center":
        return ""
    shrink = _POS_SHRINK.get(material.upper(), "moderate")
    risky = shrink in ("high", "moderate")
    col = "var(--ao-red)" if (pos == "corner" and risky) else (
        "var(--ao-orange)" if risky else "var(--ao-outline)")
    sev = "corner" if pos == "corner" else "edge"
    body = (f"{material} has <b>{shrink}</b> shrink; a {sev} of the heated bed runs cooler and "
            f"draftier, so the first layer can lift and the part can warp.")
    fix = ("Center the part on the bed" + (
        ", add a brim, and an enclosure if you have one." if shrink == "high"
        else " and add a brim." if risky else "; minor risk for this material."))
    return (
        f"<div style='border-left:3px solid {col};background:var(--ao-surface);padding:6px 10px;"
        f"margin:5px 0;font-family:ui-monospace,monospace;font-size:12px;'>"
        f"<span style='color:{col};font-weight:700;'>{icon('target')} PLACEMENT · {sev.upper()}</span> "
        f"<span style='color:var(--ao-text);'>{body}</span>"
        f"<div style='color:var(--ao-orange-soft);'>↳ suggested: {fix}</div></div>"
    )


def gcode_readout(settings: PrintSettings, material: str) -> str:
    """Short snippet whose header lines come from the proposed settings."""
    return "\n".join([
        f"; Chief Engineer — start g-code for {material} (header tied to recommendation)",
        f"; layer height {settings.layer_height:.2f} mm",
        f"M140 S{settings.bed_temp:.0f}      ; set bed",
        f"M104 S{settings.nozzle_temp:.0f}   ; set nozzle",
        f"M190 S{settings.bed_temp:.0f}      ; wait for bed",
        f"M109 S{settings.nozzle_temp:.0f}   ; wait for nozzle",
        "G28               ; home all axes",
        "G92 E0            ; reset extruder",
        f"M106 S{settings.first_layer_fan_pct * 2.55:.0f}   ; first-layer fan {settings.first_layer_fan_pct:.0f}%",
        f"; retraction {settings.retraction_mm:.1f} mm   ; cruise fan {settings.fan_pct:.0f}%",
        "; … (toolpath generated by your slicer, never by the model)",
    ])


# --- learning-loop renderers (the primary demo surface) --------------------

def quality_curve_html(trajectory: list[float], threshold: float = 0.7) -> str:
    """Astrometrics bar chart of quality per iteration — the 'it gets better' shot."""
    if not trajectory:
        return "<div style='color:var(--ao-outline);font-family:ui-monospace,monospace;'>run the loop →</div>"
    bars = []
    for i, q in enumerate(trajectory, 1):
        h = max(4, int(q * 120))
        col = "var(--ao-green)" if q >= threshold else ("var(--ao-orange)" if q >= 0.5 else "var(--ao-red)")
        bars.append(
            f"<div style='display:flex;flex-direction:column;justify-content:flex-end;align-items:center;'>"
            f"<div style='color:var(--ao-text);font-size:9px;'>{q:.2f}</div>"
            f"<div style='width:22px;height:{h}px;background:{col};'></div>"
            f"<div style='color:var(--ao-outline);font-size:9px;'>{i}</div></div>"
        )
    line_top = int((1 - threshold) * 120) + 14
    return (
        "<div style='font-family:ui-monospace,monospace;'>"
        "<div style='color:var(--ao-orange);font-weight:700;letter-spacing:1px;'>PRINT QUALITY PER ITERATION "
        f"<span style='color:var(--ao-outline);font-weight:400;'>(green = clean ≥ {threshold:.2f})</span></div>"
        "<div style='position:relative;display:flex;gap:6px;align-items:flex-end;padding:16px 4px 0;"
        "background:var(--ao-surface);border-left:3px solid var(--ao-orange);'>"
        f"<div style='position:absolute;left:0;right:0;top:{line_top}px;border-top:1px dashed var(--ao-outline-dim);'></div>"
        + "".join(bars) + "</div></div>"
    )


def iteration_log_html(records, verdicts=None, timings=None) -> str:
    """Per-iteration log. `verdicts` (optional, aligned to records) adds the QA
    Inspector's terse grade on each run — the second voice in the loop.
    `timings` (optional, aligned to records) adds per-iteration elapsed ms."""
    rows = []
    for i, r in enumerate(records):
        clean = r.result.outcome == "success"
        col = "var(--ao-green)" if clean else "var(--ao-red)"
        insp = ""
        if verdicts and i < len(verdicts) and verdicts[i] is not None:
            v = verdicts[i]
            insp = (f"<br><span style='color:{v.color};'>{icon('search')} inspector [{v.stance}]: {v.headline}</span>")
        timing = ""
        if timings and i < len(timings):
            timing = (f"<span style='float:right;color:var(--ao-outline);'>"
                      f"+{timings[i]*1000:.0f}ms</span>")
        rows.append(
            f"<div style='font-family:ui-monospace,monospace;font-size:11px;border-left:3px solid {col};"
            f"background:var(--ao-surface);padding:5px 10px;margin:3px 0;color:var(--ao-text);'>"
            f"<b style='color:{col};'>#{r.n} {r.result.outcome}</b> · q={r.result.quality:.2f} · "
            f"noz {r.settings.nozzle_temp:.0f}°C bed {r.settings.bed_temp:.0f}°C fan {r.settings.fan_pct:.0f}% "
            f"ret {r.settings.retraction_mm:.1f}mm"
            + (" · <span style='color:var(--ao-orange);'>spine-clamped</span>" if r.clamped else "")
            + f"{timing}<br><span style='color:var(--ao-outline);'>↳ {r.learned}</span>{insp}</div>"
        )
    return "".join(rows)


def policy_cell_html(cell, key: str) -> str:
    if cell is None or not getattr(cell, "offsets", None):
        return ("<div style='color:var(--ao-outline);font-family:ui-monospace,monospace;font-size:11px;'>"
                f"POLICY CELL {key}: untrained (baseline only).</div>")
    deltas = "  ".join(f"{k} {v:+g}" for k, v in cell.offsets.items())
    return (
        f"<div style='border-left:3px solid var(--ao-purple);background:var(--ao-surface);"
        f"padding:8px 12px;font-family:ui-monospace,monospace;font-size:11px;'>"
        f"<div style='color:var(--ao-purple);font-weight:700;'>LEARNED POLICY CELL · {key}</div>"
        f"<div style='color:var(--ao-text);'>offsets vs baseline: <b>{deltas}</b></div>"
        f"<div style='color:var(--ao-outline);'>{cell.trials} runs · {cell.success_rate*100:.0f}% clean</div></div>"
    )
