"""The Chief Engineer — Gradio app (four workspaces: Build, Slice, Print, Review).

STUDIO: define the job (part + material + simulated room). BUILD: slice + the
engineer's pre-flight read (precedent, risks, Spine veto, second opinion). PRINT:
run the closed loop (quality compounds fail->clean, the Inspector grades each run,
then log a real print). REVIEW: the compounding made visible (ledger + verdict).

UI follows the walkthrough spec: no emojis (custom inline-SVG icons only), one
consolidated custom loader then progressive reveal, a small primary action in the
same top-right spot on every tab with a persistent Reset, grouped contained blocks,
mirrored header/footer.

Local-first. Real Ollama calls (gemma4:e4b), deterministic fallback so the demo
never crashes. Run: `ollama serve` + `make run` (= `uv run python app.py`).
"""

from __future__ import annotations

import os
import random
import time
import uuid
from pathlib import Path

import gradio as gr

try:
    import spaces  # ZeroGPU @spaces.GPU decorator — HF-provided on the Space.
except ImportError:  # not installed locally (base env / offline); decorator no-ops.
    class _SpacesShim:
        @staticmethod
        def GPU(fn=None, **_kw):
            return fn if fn is not None else (lambda f: f)

    spaces = _SpacesShim()  # type: ignore

from core import deliberation_log
from core import field_log
from core import inspector
from core import llm
from core import seed_lessons
from core import signups
from core.theme import (
    THEME, CSS, rule, command_bar, footer_bar, inspector_panel, icon, loader, tab_intro,
    CLOCK_JS,
)
from core.widgets import virtual_printer_html, layer_image, SCRUB_LAYERS, VP_HEAD
from core.chief_engineer import advise
from core.ledger import LedgerManager
from core.models import Advice, BED_POSITIONS, Environment, Job, MATERIALS, PrintSettings
from core.nodes import render_node_cards
from core.reflect import reflect_on_job
from core.spine import SpineValidator
from learn.loop import run_iteration, SessionResult
from learn.policy import LearnedPolicy, cell_key
from core.viewer import (
    GEO_READS,
    benchy_mesh,
    gcode_panel_html,
    generate_primitive,
    infer_geometry,
    iteration_log_html,
    placement_callout,
    policy_cell_html,
    precedent_eval_html,
    quality_curve_html,
    risk_callouts_html,
    settings_panel_html,
    steepest_overhang_hint,
)

try:
    from ingest.distill import reference_block
except Exception:  # ingestion is optional / removable
    def reference_block(material):  # type: ignore
        return []

LEDGER = LedgerManager()
SPINE = SpineValidator()
POLICY = LearnedPolicy()
_loaded = seed_lessons.ensure_seeded(LEDGER)

# On the Space (backend=zerogpu), import the inference module at startup so its
# @spaces.GPU function (core/llm_zerogpu._generate) is registered — ZeroGPU requires
# at least one detected GPU function, and build_job is deliberately no longer one.
if __import__("os").environ.get("CHIEF_ENGINEER_BACKEND") == "zerogpu":
    try:
        import core.llm_zerogpu  # noqa: F401  (registers @spaces.GPU on import)
        import core.llm_zerogpu_lora  # noqa: F401  (LoRA-aware variant)
    except Exception:
        pass

# Model switcher: maps UI labels to backend configuration
# Space-compatible backends only (ZeroGPU + Modal). Local Ollama options removed —
# they only work in local development, not on the Space.
MODEL_OPTIONS = [
    "LoRA v3 (QAT E4B)",
    "LoRA v2 (Standard E4B)",
    "Base Gemma 4 E4B (ZeroGPU)",
    "Modal API (remote)",
]

MODEL_LORA_MAP = {
    "LoRA v2 (Standard E4B)": "kylebrodeur/microfactory-node-lora-v2",
    "LoRA v3 (QAT E4B)": "kylebrodeur/microfactory-node-lora-v3-qat",
}

def _apply_model_choice(model_choice: str):
    """Set environment variables so the next advise() call uses the chosen backend."""
    if model_choice == "Base Gemma 4 E4B (ZeroGPU)":
        os.environ.pop("CHIEF_ENGINEER_LORA_REPO", None)
        os.environ["CHIEF_ENGINEER_BACKEND"] = "zerogpu"
    elif model_choice in MODEL_LORA_MAP:
        os.environ["CHIEF_ENGINEER_LORA_REPO"] = MODEL_LORA_MAP[model_choice]
        os.environ["CHIEF_ENGINEER_BACKEND"] = "zerogpu"
    elif model_choice == "Modal API (remote)":
        os.environ.pop("CHIEF_ENGINEER_LORA_REPO", None)
        os.environ["CHIEF_ENGINEER_BACKEND"] = "modal"
    # No module reload needed: core.llm reads the backend + adapter env dynamically
    # (llm._backend() / CHIEF_ENGINEER_LORA_REPO), so the switch takes effect on the
    # next call. (reload(__import__("core.llm")) reloaded the package, not the submodule,
    # so it was a no-op for routing anyway.)

# Default to the winning LoRA v3 (QAT) model — best loss, best quantization quality
_apply_model_choice("LoRA v3 (QAT E4B)")

# Astrometrics OS visual layer lives in core/theme.py (THEME + CSS + helpers) so
# the Off-Brand skin stays a single removable module. See ../DESIGN.md.

PRINTER = "Creality Ender 3 V2"


def _delib_ctx(job, env) -> dict:
    """Context columns shared by every deliberation-log turn for a job."""
    return {"material": job.material, "geometry": job.geometry_type,
            "bed_position": job.bed_position, "env_temp": env.temp, "env_humidity": env.humidity}
_SCROLL_TOP = "() => { window.scrollTo({ top: 0, behavior: 'smooth' }); }"


def ledger_html() -> str:
    c = LEDGER.count()
    entries = LEDGER.all()[-8:][::-1]
    rows = []
    for e in entries:
        tag = "SEED" if e.source == "seed" else "EARNED"
        col = "var(--ao-outline)" if e.source == "seed" else "var(--ao-green)"
        rows.append(
            f"<div style='border-left:3px solid {col};background:var(--ao-surface);padding:6px 10px;"
            f"margin:4px 0;font-family:ui-monospace,monospace;font-size:11px;'>"
            f"<span style='color:{col};font-weight:700;'>{tag}</span> "
            f"<span style='color:var(--ao-orange);'>{e.material}/{e.geometry_type}</span> "
            f"<span style='color:var(--ao-outline);'>@ {e.env_temp:.0f}°C/{e.env_humidity:.0f}% → {e.outcome}</span>"
            f"<div style='color:var(--ao-text);'>{e.lesson}</div></div>"
        )
    head = (
        f"<div style='color:var(--ao-orange);font-family:ui-monospace,monospace;'>"
        f"LEDGER · {c['total']} lessons ({c['seed']} seed · {c['earned']} earned)</div>"
    )
    return head + "".join(rows)


def studio_log_html() -> str:
    """Job log near the top of Studio: what is stored, and where (studio-14/17)."""
    c = LEDGER.count()
    return (
        "<div class='ce-card'>"
        f"<div style='color:var(--ao-orange);font-weight:700;letter-spacing:1.5px;font-size:11px;'>"
        f"{icon('book')} JOB LOG · {c['total']} LESSONS "
        f"<span style='color:var(--ao-outline);font-weight:400;'>({c['seed']} seed · {c['earned']} earned)</span></div>"
        "<div class='ce-sub' style='margin-top:4px;'>Every build, print, and recorded outcome is stored "
        "to <b>data/lessons.jsonl</b> (durable) and the learned policy to <b>data/policy.json</b>. "
        "This session's runs append live; <b>Reset to Baseline</b> restores the curated seed + ingested set.</div>"
        "</div>"
    )


def reset_learnings():
    """Reset the live ledger + learned policy to the curated baseline (seed + ingested),
    clearing only this session's runtime lessons and the learned policy file. Does NOT
    touch: seed_lessons.jsonl, references.jsonl, HF trace datasets (ledger/deliberation/
    field-log), or any recorded Space logs. Also clears the loaded part and hides the
    result groups so the next run starts from a clean LOAD tab."""
    removed = LEDGER.reset_to_baseline()
    POLICY.reset()
    gr.Info(f"Reset to baseline — cleared {removed} runtime lesson(s) + the learned policy. "
            f"Seed/ingested traces and HF logs were not touched.")
    return (
        ledger_html(),                                                   # ledger_panel
        render_node_cards(Environment(temp=22, humidity=45)),            # node_cards
        "<div class='ce-sub'>Reset to baseline. Run the Print loop for a fresh verdict.</div>",  # review_summary
        "", "", "",                                                      # p_curve, p_policy, p_log
        "",                                                              # p_headline
        "",                                                              # outcome_panel
        gr.update(visible=False),                                        # print results_group (re-hide)
        "",                                                              # real_log_msg
        studio_log_html(),                                              # studio_log
        {"geometry": None, "mesh": None, "label": None, "read": None}, # part state
        gr.update(value=None, visible=False),                           # model3d
        gr.update(visible=True),                                         # part_placeholder
        "",                                                              # part_status
        gr.update(visible=False),                                        # build_results
        gr.update(visible=False),                                        # read_results
        gr.Tabs(selected="studio"),                                      # tabs back to LOAD
        review_record_html(None),                                        # review_record (clear)
    )


def _viewer_placeholder() -> str:
    """Custom empty-state for the blank part/model viewer (no generic Gradio canvas)."""
    return (
        "<div class='ce-viewer'>"
        f"<div class='ce-viewer-ico'>{icon('layers', 40)}</div>"
        "<div class='ce-viewer-title'>NO PART LOADED</div>"
        "<div class='ce-viewer-copy'>Define the part, set the material and the room, then "
        "<b>SLICE</b> (Build) and <b>PRINT</b>. You give it the part, the material, and the room; "
        "it infers what kind of part this is.</div>"
        "<div class='ce-viewer-hint'>quick-load Benchy · drop a mesh · or generate a primitive →</div>"
        "</div>"
    )


def _set_part(geometry: str, mesh, label: str, read: str | None = None):
    """Shared preview update → (part_state, model3d, status, placeholder). The user never
    picks the class — the engineer infers it from the mesh (see infer_geometry). Loading a
    part reveals the 3D model and hides the custom placeholder."""
    read = read or GEO_READS.get(geometry, geometry)
    return (
        {"geometry": geometry, "mesh": mesh, "label": label, "read": read},
        gr.update(value=mesh, visible=True),
        f"ACTIVE PART · **{label}** · the engineer reads this as *{read}* → reasons about `{geometry}`",
        gr.update(visible=False),
    )


def build_start(part):
    """Instant feedback when BUILD is clicked: jump to Build, reveal the slicer +
    virtual print preview immediately, and show the read panel in a loading state
    while the model runs. No part → stay put."""
    if not (part and part.get("geometry")):
        gr.Warning("Load a part on the BUILD tab first — quick-load Benchy, generate a primitive, or drop a mesh.")
        return (gr.update(),) * 13
    mesh = part.get("mesh")
    label = part.get("label") or "PART"
    vp_html = virtual_printer_html(mesh, caption=f"{label} · virtual print preview")
    layer_img = layer_image(mesh, 1)
    return (
        gr.Tabs(selected="build"),                    # tabs
        gr.update(visible=True),                      # build_results (reveal)
        gr.update(visible=True),                      # read_results (reveal, loading state)
        loader("READING THE PLAN · O'Brien is checking precedent and proposing settings"),
                                                      # read_loader
        vp_html,                                      # vprint
        gr.update(value=1),                           # vp_slider reset
        layer_img,                                    # vp_layer
        gr.update(interactive=True),                  # to_print_btn (un-gate)
        gr.update(visible=False),                     # override_btn (hide)
        "",                                           # second_opinion_panel (clear stale)
        gr.update(value="Engineer's Read"),           # read_toggle (reset to the read)
        gr.update(visible=True),                      # eng_read_group
        gr.update(visible=False),                     # second_op_group
    )


def load_benchy():
    mesh = benchy_mesh()
    if not mesh:
        return ({"geometry": None, "mesh": None, "label": None, "read": None},
                gr.update(value=None), "**BENCHY MISSING** — add assets/benchy.glb", gr.update())
    geo, read = infer_geometry(mesh)
    return _set_part(geo, mesh, "3DBENCHY (CC0)", read)


def generate_part(kind, size):
    mesh, geo = generate_primitive(kind, size or 30)
    return _set_part(geo, mesh, f"GENERATED {str(kind).upper()} · {float(size or 30):.0f}MM")


def upload_part(f):
    if not f:
        return (gr.update(), gr.update(), gr.update(), gr.update())
    from pathlib import Path as _P
    geo, read = infer_geometry(f.name)
    return _set_part(geo, f.name, f"UPLOAD · {_P(f.name).name[:26]}", read)


def scrub_layer(idx, part):
    """Render one cross-section layer at full fidelity for the scrubber slider."""
    mesh = (part or {}).get("mesh")
    return layer_image(mesh, idx)


# ── model warm-up + live status + switcher (Live / LoRA / QAT) ────────────────
def _status_html() -> str:
    return f"<div class='ce-sub' style='font-size:12px;'>MODEL · {llm.backend_status()}</div>"


def warm_up_pending() -> str:
    """Header icon stays; the warm-up intent is signaled by a toast."""
    gr.Info("Warming up the model (first load can take ~30s on ZeroGPU)…")
    return _model_icon()


def warm_up_cb() -> str:
    """After warm-up, keep the info icon in the header."""
    return _model_icon()


def _model_icon() -> str:
    """Small info-icon callout for the header row. No text — the dropdown + warm-up
    button already give enough context; the tooltip explains the backends."""
    return (
        "<span class='ce-callout' tabindex='0'>" + icon("info") + ""
        "<span class='ce-tip'>The <b>LoRA v2/v3</b> adapters serve via ZeroGPU on the Space; "
        "<b>Base</b> is the stock Gemma 4 E4B; <b>Modal API</b> is the remote endpoint. "
        "Local users: pull the LoRA from HF Hub "
        "(kylebrodeur/microfactory-node-lora-v2 / -v3-qat) or via ollama.</span></span>"
    )


def _model_callout() -> str:
    """Legacy full-width model callout (used when more explanatory text is wanted)."""
    return (
        "<span class='ce-callout' tabindex='0'>" + icon("info") + " MODEL INFO"
        "<span class='ce-tip'>The <b>LoRA v2/v3</b> adapters serve via ZeroGPU on the Space; "
        "<b>Base</b> is the stock Gemma 4 E4B; <b>Modal API</b> is the remote endpoint. "
        "Local users: pull the LoRA from HF Hub "
        "(kylebrodeur/microfactory-node-lora-v2 / -v3-qat) or via ollama.</span></span>"
    )


def select_model(choice: str) -> str:
    """Model switcher: apply the chosen backend, then return the info icon so the
    header stays compact."""
    choice = choice or MODEL_OPTIONS[0]
    try:
        _apply_model_choice(choice)
    except Exception:
        pass
    return _model_icon()


# ── simulated environment (this is a sim lab — conditions are generated, overridable) ──
def _sensor_readout(t, h, pos) -> str:
    """Compact value line for the envbar. The 'ENVIRONMENT (SIMULATED)' label is
    rendered separately in app.py so it matches the POSITION / MATERIAL labels."""
    return (f"{icon('thermo')} <b style='color:var(--ao-blue);'>{float(t):.0f}°C</b> · "
            f"{icon('droplet')} <b style='color:var(--ao-blue);'>{float(h):.0f}%RH</b> · "
            f"{icon('target')} <b style='color:var(--ao-blue);'>{pos}</b> · "
            f"{icon('printer')} <b style='color:var(--ao-outline);'>{PRINTER}</b>")


def status_footer(part, material, t, h, pos):
    """Live job context for the sticky footer strip."""
    p = part or {}
    label = p.get("label") or "no part"
    geo = p.get("geometry") or "—"
    return footer_bar(job=f"{label} · {material} · {geo}",
                      env=f"{float(t):.0f}°C / {float(h):.0f}%RH · {pos} · {PRINTER}")


def randomize_sensors():
    """Roll a plausible ambient + plate position + material — the lab's simulated sensor feed."""
    t = random.choice([18, 20, 22, 24, 26, 28, 30, 32])
    h = random.choice([30, 38, 45, 52, 60, 68])
    pos = random.choices(BED_POSITIONS, weights=[3, 2, 1])[0]   # center most common
    mat = random.choice(MATERIALS)
    return (gr.update(value=t), gr.update(value=h), gr.update(value=pos),
            gr.update(value=mat), _sensor_readout(t, h, pos))


def sync_readout(t, h, pos):
    return _sensor_readout(t, h, pos)


def build_job(part, material, description, temp, humidity, bed_position, model_choice):
    # NOTE: deliberately NOT @spaces.GPU. The GPU window lives on the inference
    # function only (core/llm_zerogpu._generate). Decorating the whole handler made
    # a ZeroGPU quota/error reject the ENTIRE build (slicer, retrieval, fallback) →
    # "Error" on the Space with no graceful fallback.
    if not (part and part.get("geometry")):   # guard: empty start, no part chosen
        return ("", "", "**Load a part on the BUILD tab** (quick-load Benchy, generate, or drop a mesh) "
                "before building.", "", "", "", "", gr.update(visible=False),
                gr.update(), {}, "", gr.update(), gr.update(), "", gr.update(visible=False))

    # Apply model choice before inference
    _apply_model_choice(model_choice or "LoRA v3 (QAT E4B)")
    geometry_type, mesh = part["geometry"], part.get("mesh")
    job = Job(geometry_type=geometry_type, material=material, description=description or "",
              bed_position=bed_position or "center", mesh_path=mesh)
    env = Environment(temp=float(temp), humidity=float(humidity))

    retrieved = LEDGER.retrieve(material, geometry_type, env.temp, env.humidity)
    references = reference_block(material)
    policy_note = POLICY.policy_note(material, geometry_type, env)
    rec = advise(job, env, retrieved, references, policy_note)
    spine = SPINE.check(rec.advice.settings, material)
    hint = steepest_overhang_hint(mesh) if geometry_type in ("overhang", "bridge") else None
    vp_html = virtual_printer_html(mesh, settings=spine.settings,
                                     caption=f"{material} · {geometry_type}")  # init on BUILD

    precedent = precedent_eval_html(retrieved, env)
    if retrieved:
        rows = "".join(
            f"<div style='font-family:ui-monospace,monospace;font-size:11px;color:var(--ao-outline);'>"
            f"• {e.job_id} ({e.source}) {e.outcome} @ {e.env_temp:.0f}°C/{e.env_humidity:.0f}% "
            f"(dist {dist:.2f})</div>"
            for e, dist in retrieved
        )
        precedent += f"<div style='margin-top:4px;'>{rows}</div>"

    fb = " · deterministic fallback" if rec.used_fallback else ""
    spine_md = (f"**{icon('shield')} Spine veto:** " + "  \n".join(spine.vetoes)) if spine.vetoes else ""
    confirm_vis = gr.update(visible=spine.requires_approval)
    approval_md = ("**HITL gate:** the Spine clamped a boundary setting — review, then **Confirm & Print**."
                   if spine.requires_approval else "Within safe envelope — ready when you are.")
    spine_notes_text = f"{spine_md}\n\n{approval_md}" if spine_md else approval_md
    session_id = uuid.uuid4().hex
    state = {"job": job.model_dump(), "env": env.model_dump(), "settings": spine.settings.model_dump(),
             "advice": rec.advice.model_dump(), "label": part.get("label"), "session_id": session_id,
             "spine_notes": spine_notes_text}

    # ── field log (Space only — gated on HF_TOKEN; local/offline no-ops) ──
    field_log.log_build(
        job=state["job"], env=state["env"], settings=state["settings"],
        advice=state["advice"], backend=rec.backend, used_fallback=rec.used_fallback,
    )
    # ── deliberation log: O'Brien proposes -> Spine vetoes (same gate) ──
    s = spine.settings
    deliberation_log.log_turns(session_id, "preflight", [
        {"agent": "O'Brien", "act": "propose",
         "content": f"{rec.advice.reasoning} Proposed: nozzle {s.nozzle_temp:.0f}°C, bed "
                    f"{s.bed_temp:.0f}°C, fan {s.fan_pct:.0f}%, retraction {s.retraction_mm:.1f}mm."},
        {"agent": "Spine", "act": "veto",
         "stance": "clamped" if spine.requires_approval else "clear",
         "content": ("Clamped: " + " · ".join(spine.vetoes)) if spine.vetoes
                    else "Within the safe envelope for this material — no clamp."},
    ], _delib_ctx(job, env))

    return (
        f"{rec.backend}{fb}",                                          # backend status
        precedent,                                                     # precedent
        f"**Chief Engineer O'Brien:** {rec.advice.reasoning}",         # reasoning
        risk_callouts_html(rec.advice.risks, hint) + placement_callout(material, bed_position),  # risks
        settings_panel_html(spine.settings, material),                 # settings (LCARS panel)
        spine_notes_text,                                                # spine notes
        gcode_panel_html(spine.settings, material),                    # g-code (LCARS panel)
        confirm_vis,                                                   # confirm visibility
        render_node_cards(env, working=True),                          # node cards
        state,                                                         # state
        virtual_printer_html(mesh, settings=spine.settings,
                              caption=f"{material} · {geometry_type}"),  # vprint (refined caption)
        gr.update(value=1),                                            # reset layer scrubber
        layer_image(mesh, 1),                                          # initial scrubbed layer
        "",                                                            # read_loader (clear)
    )


def _compute_second_opinion(state):
    """Run the Inspector (La Forge) critique once. Returns the raw tuple used by
    the UI: (panel_html, to_print_update, override_update)."""
    if not state or "advice" not in state:
        return ("<div class='ce-sub'>Build a job first — then I'll give the plan a second look.</div>",
                gr.update(interactive=True), gr.update(visible=False))
    job = Job(**state["job"])
    env = Environment(**state["env"])
    settings = PrintSettings(**state["settings"])
    advice = Advice(**state["advice"])
    verdict = inspector.second_opinion(job, env, settings, advice)
    field_log.log_event("second_opinion", {"material": job.material, "geometry": job.geometry_type,
                                            "inspector_stance": verdict.stance,
                                            "inspector_headline": verdict.headline})
    deliberation_log.log_turns(state.get("session_id"), "preflight", [
        {"agent": "La Forge", "act": "second_opinion", "stance": verdict.stance,
         "content": f"{verdict.headline} — {verdict.detail}"},
    ], _delib_ctx(job, env))
    panel = inspector_panel(verdict, label="LA FORGE · SECOND OPINION (PRE-PRINT)")
    if verdict.stance.lower() == "dispute":
        panel += ("<div style='margin-top:6px;padding:6px 10px;border-left:3px solid var(--ao-red,#d9534f);"
                  "background:var(--ao-surface);font-family:ui-monospace,monospace;font-size:12px;"
                  "color:var(--ao-text);'>" + icon('alert') + " <b>The Inspector disputes this plan.</b> "
                  "→ PRINT is held. Review the objection, then acknowledge to proceed anyway.</div>")
        return panel, gr.update(interactive=False), gr.update(visible=True)
    return panel, gr.update(interactive=True), gr.update(visible=False)


def second_opinion(state):
    """Idempotent wrapper: if La Forge already weighed in on this build, return the
    cached verdict; otherwise compute it once and store it in state."""
    if state and state.get("second_opinion"):
        return state["second_opinion"]
    result = _compute_second_opinion(state)
    if state:
        state["second_opinion"] = result
    return result


def toggle_read(choice, state):
    """Segmented toggle on Build: flip between Engineer's Read and Second Opinion,
    showing one panel at a time. The opinion is computed lazily on first reveal and
    then cached for the rest of the build. While it computes, the Second Opinion panel
    shows a mini-loader so the user knows La Forge is reviewing the plan."""
    if str(choice).lower().startswith("engineer"):
        yield (gr.update(visible=True), gr.update(visible=False),
               "", gr.update(), gr.update(), state)
        return
    cached = state.get("second_opinion") if state else None
    if cached:
        panel, to_print, override = cached
        yield (gr.update(visible=False), gr.update(visible=True), panel, to_print, override, state)
        return
    # show in-place loader while the Inspector runs
    yield (gr.update(visible=False), gr.update(visible=True),
           loader("CONSULTING LA FORGE", stages=[
               "reading the engineer's plan",
               "checking precedent and risks",
               "comparing settings to the safe envelope",
               "drafting the pre-print verdict",
           ]), gr.update(interactive=True), gr.update(visible=False), state)
    panel, to_print, override = _compute_second_opinion(state)
    state = (state or {}) | {"second_opinion": (panel, to_print, override)}
    yield (gr.update(visible=False), gr.update(visible=True), panel, to_print, override, state)


def ack_override(state):
    """Human overrides the Inspector's dispute — re-open → PRINT (on the operator's call)."""
    if state and state.get("session_id"):
        deliberation_log.log_turns(state["session_id"], "preflight", [
            {"agent": "Operator", "act": "override", "stance": "override",
             "content": "Acknowledged La Forge's objection. Proceeding to print on the operator's call."},
        ], _delib_ctx(Job(**state["job"]), Environment(**state["env"])))
    return gr.update(interactive=True), gr.update(visible=False)


def job_readout(state):
    """The job Print inherits from Studio/Build (no re-picking — it prints THIS job)."""
    if not state or "job" not in state:
        return ("<div class='ce-sub'>No job built yet. Go to <b>BUILD</b> → define a part → "
                "<b>SLICE</b>, then return here to print it.</div>")
    j, e = state["job"], state["env"]
    return (f"<div class='ce-sub' style='font-size:13px;'>PRINTING · "
            f"<b style='color:var(--ao-orange);'>{state.get('label') or j['geometry_type']}</b> · "
            f"{j['material']}/{j['geometry_type']} · {icon('target')} {j.get('bed_position','center')} · "
            f"{icon('thermo')} {e['temp']:.0f}°C / {icon('droplet')} {e['humidity']:.0f}%RH · "
            f"{icon('printer')} {PRINTER}</div>")


def plan_card_html(state):
    """THE PLAN card: Spine-validated proposed settings + Spine notes for the current job."""
    if not state or "settings" not in state:
        return ("<div class='ce-sub'>No plan built yet. Go to <b>BUILD</b> → define a part → "
                "<b>SLICE</b>, then return here to print it.</div>")
    settings = PrintSettings(**state["settings"])
    material = state["job"]["material"]
    html = settings_panel_html(settings, material)
    notes = state.get("spine_notes") or ""
    if notes:
        html += ("<div class='ce-sub' style='margin-top:6px;'>" +
                 notes.replace("\n", "<br>") + "</div>")
    return html


def plan_verdict_html(state):
    """La Forge's pre-print stance if already computed on the SLICE tab."""
    if not state or "settings" not in state:
        return ("<div class='ce-sub'>Build a job first to get La Forge's pre-print stance.</div>")
    cached = state.get("second_opinion")
    if cached:
        return cached[0]
    return ("<div class='ce-sub'>" + icon("search") +
            " Run the Inspector (<b>Second Opinion</b>) on the SLICE tab for a pre-print stance.</div>")


def plan_testing_html(state):
    """THE PLAN header: restate plainly what this run tests (job + conditions + question)."""
    if not state or "job" not in state:
        return ("<div class='ce-sub'>No job yet — build one on <b>BUILD → SLICE</b>, then return "
                "here to print it.</div>")
    j, e = state["job"], state["env"]
    return ("<div class='ce-sub' style='font-size:13px;'>Testing the engineer's plan for "
            f"<b style='color:var(--ao-orange);'>{state.get('label') or j['geometry_type']}</b> "
            f"({j['material']}/{j['geometry_type']}) at {e['temp']:.0f}°C / {e['humidity']:.0f}%RH on "
            f"{PRINTER}: <i>does it print clean, and does the policy improve across the run?</i></div>")


def _next_steps_html(state):
    """NEXT STEPS for the REVIEW record — what the run earned and what to do next."""
    run = state.get("run") if state else None
    j = state["job"]
    steps = []
    if run:
        if run.get("first"):
            steps.append(f"Converged to a clean print by iteration <b>{run['first']}</b> — the learned "
                         f"policy for {j['material']}/{j['geometry_type']} at these conditions is now stored "
                         "and will pre-bias the next similar job.")
        else:
            steps.append("No clean print this run — the job is genuinely hard for these conditions or the "
                         "policy is saturated. Worth a human look, an <b>OVERRIDE</b>, or logging a real outcome.")
        steps.append("Print this on the real machine and use <b>LOG A REAL PRINT</b> to feed the true "
                     "outcome back into the ledger.")
    else:
        steps.append("Run the <b>PRINT</b> loop to simulate this job and learn from the outcome.")
    return "".join(f"<div class='ce-sub' style='margin:3px 0;'>{icon('arrow')} {s}</div>" for s in steps)


def review_record_html(state):
    """The full session record on REVIEW: inputs → O'Brien's read → La Forge's
    pre-print stance → the simulated run → outcome → next steps. Assembled from
    state so the whole story of this job lives in one place."""
    if not state or "job" not in state:
        return ("<div class='ce-sub'>No session yet. Build a job (<b>BUILD → SLICE</b>), get the read "
                "and a second opinion, then <b>PRINT</b> — the full record assembles here.</div>")
    j, e = state["job"], state["env"]
    p = []
    p.append(rule("INPUTS · THE JOB"))
    p.append("<div class='ce-sub' style='font-size:13px;'>"
             f"<b style='color:var(--ao-orange);'>{state.get('label') or j['geometry_type']}</b> · "
             f"{j['material']}/{j['geometry_type']} · {icon('target')} {j.get('bed_position','center')} · "
             f"{icon('thermo')} {e['temp']:.0f}°C / {icon('droplet')} {e['humidity']:.0f}%RH · "
             f"{icon('printer')} {PRINTER}</div>")
    p.append(rule("CHIEF ENGINEER O'BRIEN · THE READ"))
    adv = state.get("advice") or {}
    p.append(f"<div class='ce-sub'>{adv.get('reasoning') or '(no read captured this session)'}</div>")
    p.append(rule("LA FORGE · PRE-PRINT SECOND OPINION"))
    cached = state.get("second_opinion")
    p.append(cached[0] if cached else
             "<div class='ce-sub'>No second opinion captured — run it on the SLICE tab (THE READ → Second Opinion).</div>")
    run = state.get("run")
    p.append(rule("SIMULATED PRINT RUN"))
    if run:
        p.append(run["curve_html"])
        p.append(run["log_html"])
        p.append(rule("OUTCOME · WHAT HAPPENED"))
        p.append(run["outcome_html"])
    else:
        p.append("<div class='ce-sub'>Not printed yet — run the PRINT loop to see the simulated run + outcome.</div>")
    p.append(rule("NEXT STEPS"))
    p.append(_next_steps_html(state))
    return "".join(p)



def _print_plan_values(state):
    """Return the Engineer's proposed settings values (or safe defaults) for VARY sliders."""
    defaults = {"nozzle_temp": 200, "bed_temp": 60, "fan_pct": 80, "retraction_mm": 4.5}
    if not state or "settings" not in state:
        return defaults
    s = state["settings"]
    return {k: s.get(k, defaults[k]) for k in defaults}


def apply_overrides(state, nozzle, bed, fan, retract):
    """Compare VARY slider values to the Engineer's plan. If anything changed, build an
    override PrintSettings and log that the operator defied the plan. Returns the override
    dict (or None when the plan is unchanged)."""
    if not state or "settings" not in state:
        return None
    plan = PrintSettings(**state["settings"])
    diffs = {}
    if abs(float(nozzle) - plan.nozzle_temp) > 1e-6:
        diffs["nozzle_temp"] = float(nozzle)
    if abs(float(bed) - plan.bed_temp) > 1e-6:
        diffs["bed_temp"] = float(bed)
    if abs(float(fan) - plan.fan_pct) > 1e-6:
        diffs["fan_pct"] = float(fan)
    if abs(float(retract) - plan.retraction_mm) > 1e-6:
        diffs["retraction_mm"] = float(retract)
    if not diffs:
        state.pop("print_overrides", None)
        return None
    overrides = plan.model_copy(update=diffs)
    state["print_overrides"] = overrides.model_dump()
    job = Job(**state["job"])
    env = Environment(**state["env"])
    field_log.log_print_override(job.model_dump(), env.model_dump(), overrides.model_dump())
    if state.get("session_id"):
        deliberation_log.log_turns(state["session_id"], "preflight", [
            {"agent": "Operator", "act": "override",
             "content": (f"Overrode the Engineer: nozzle {overrides.nozzle_temp:.0f}°C, "
                         f"bed {overrides.bed_temp:.0f}°C, fan {overrides.fan_pct:.0f}%, "
                         f"retraction {overrides.retraction_mm:.1f}mm.")},
        ], _delib_ctx(job, env))
    return overrides.model_dump()


def _simulated_result_panel(sess, run_summary, material, geometry_type, env, label) -> str:
    """Two-zone outcome — the dominant SIMULATED RESULT zone (the compact LOG A REAL
    PRINT zone is static UI below). Shows the final outcome, the climb, whether the
    Inspector's prediction held, and La Forge's run verdict."""
    traj = sess.trajectory
    final = sess.records[-1].result
    first = sess.first_success
    passed = final.outcome == "success"
    col = "var(--ao-green)" if passed else "var(--ao-red)"
    badge = "PASS" if passed else "FAIL"
    climb = (f"first clean print at iteration <b>{first}</b>" if first
             else f"still improving — best <b>{max(traj):.2f}</b>")
    return (
        "<div style='font-family:ui-monospace,monospace;background:var(--ao-void);"
        "border:1px solid var(--ao-outline-dim);border-left:3px solid var(--ao-orange);padding:10px 12px;'>"
        f"<div style='color:var(--ao-orange);font-weight:700;letter-spacing:2px;font-size:11px;'>"
        f"{icon('flask')} SIMULATED RESULT <span style='color:var(--ao-outline);font-weight:400;'>"
        "(deterministic world — stand-in for printer + sensors)</span></div>"
        f"<div class='ce-sub' style='margin-top:6px;'>WHAT WAS SIMULATED · {material}/{geometry_type} "
        f"· {env.temp:.0f}°C/{env.humidity:.0f}%RH · {PRINTER}</div>"
        f"<div style='margin-top:4px;font-size:15px;'>FINAL · "
        f"<span style='color:{col};font-weight:700;'>[{badge}] {final.detail}</span></div>"
        f"<div class='ce-sub'>Started at quality <b>{traj[0]:.2f}</b>; {climb}; now <b>{traj[-1]:.2f}</b> "
        f"over {len(traj)} runs.</div></div>"
        + inspector_panel(run_summary, label="LA FORGE · RUN VERDICT")
    )


def run_print(state, iterations, nozzle, bed, fan, retract, progress=gr.Progress()):
    """PRINT: run THIS job (inherited from Build) through the closed loop.
    Now a generator so the iteration log + quality chart + policy cell fill in
    live as each iteration completes. Per-iteration timing is shown next to each row."""
    if not state or "job" not in state:
        gr.Warning("Build a job first (BUILD → SLICE), then print it here.")
        yield (gr.update(),) * 9
        return
    job = Job(**state["job"])
    env = Environment(**state["env"])
    material, geometry_type = job.material, job.geometry_type
    key = cell_key(material, geometry_type, env)
    before_html = policy_cell_html(POLICY.cell_stats(material, geometry_type, env), key)

    overrides_dict = apply_overrides(state, nozzle, bed, fan, retract)
    overrides = PrintSettings(**overrides_dict) if overrides_dict else None

    records, verdicts, timings = [], [], []
    n_iters = int(iterations)
    start_iter = time.perf_counter()
    for i in range(1, n_iters + 1):
        progress(i / n_iters, desc=f"Iteration {i}/{n_iters}")
        record = run_iteration(job, env, POLICY, LEDGER, i, overrides=overrides)
        verdict = inspector.grade_iteration(geometry_type, record.result)
        elapsed = time.perf_counter() - start_iter
        start_iter = time.perf_counter()
        records.append(record)
        verdicts.append(verdict)
        timings.append(elapsed)
        yield (
            gr.update(visible=True),                                 # results_group
            "",                                                      # outcome_panel
            "",                                                      # p_headline
            quality_curve_html([r.result.quality for r in records]), # p_curve
            iteration_log_html(records, verdicts, timings),          # p_log
            policy_cell_html(POLICY.cell_stats(material, geometry_type, env), key),  # p_policy
            gr.update(),                                             # ledger_panel
            gr.update(),                                             # node_cards
            "",                                                      # review_summary
        )

    after = POLICY.cell_stats(material, geometry_type, env)
    run_summary = inspector.summarize_run(records, material=material, geometry=geometry_type)

    traj = [r.result.quality for r in records]
    first = next((r.n for r in records if r.result.outcome == "success"), None)
    field_log.log_event("print_run", {"material": material, "geometry": geometry_type,
                                       "env_temp": env.temp, "env_humidity": env.humidity,
                                       "iterations": len(records), "q_start": round(traj[0], 3),
                                       "q_end": round(traj[-1], 3), "first_clean": first,
                                       "inspector_stance": run_summary.stance,
                                       "used_override": overrides is not None,
                                       "override_settings": overrides.model_dump() if overrides else None})
    # ── deliberation log: World simulates -> La Forge grades, per iteration; then verdict ──
    ctx = _delib_ctx(job, env)
    loop_turns = []
    for r, g in zip(records, verdicts):
        clamp = " (Spine clamped a setting)" if r.clamped else ""
        loop_turns.append({"agent": "World", "act": "simulate", "stance": r.result.outcome,
                           "content": f"Iteration {r.n}: {r.result.detail}.{clamp} Policy: {r.learned}."})
        loop_turns.append({"agent": "La Forge", "act": "grade", "stance": g.stance,
                           "content": f"{g.headline} — {g.detail}"})
    deliberation_log.log_turns(state.get("session_id"), "print-loop", loop_turns, ctx)
    deliberation_log.log_turns(state.get("session_id"), "review", [
        {"agent": "La Forge", "act": "verdict", "stance": run_summary.stance,
         "content": f"{run_summary.headline} — {run_summary.detail}"},
    ], ctx)
    headline = (
        f"**{state.get('label') or geometry_type} · {material} @ {env.temp:.0f}°C / {env.humidity:.0f}% RH** — "
        f"started at quality **{traj[0]:.2f}** ({records[0].result.outcome}); "
        + (f"first clean print at **iteration {first}**, now **{traj[-1]:.2f}**."
           if first else f"still improving — best **{max(traj):.2f}** after {len(traj)} runs.")
        + " The Engineer proposed; a separate simulated world reported the outcome; the **Inspector** "
        "graded each run; the policy and ledger learned. *(Simulated — see [SIMULATION.md](docs/reference/SIMULATION.md).)*"
    )
    policy_html = (f"{before_html}<div style='text-align:center;color:var(--ao-orange);font-size:11px;"
                   f"letter-spacing:2px;'>{icon('arrow')} LEARNED</div>{policy_cell_html(after, key)}")
    outcome = _simulated_result_panel(
        SessionResult(job=job, env=env, records=records),
        run_summary, material, geometry_type, env, state.get("label"))
    # Stash the run on state so the REVIEW tab can assemble the full session record.
    state["run"] = {
        "iterations": len(records), "traj": traj, "first": first,
        "outcome": records[-1].result.outcome, "detail": records[-1].result.detail,
        "headline": headline, "curve_html": quality_curve_html(traj),
        "log_html": iteration_log_html(records, verdicts, timings),
        "outcome_html": outcome, "verdict_stance": run_summary.stance,
    }
    yield (
        gr.update(visible=True),                                  # results_group
        outcome,                                                  # outcome_panel
        headline,                                                 # p_headline
        quality_curve_html(traj),                                 # p_curve
        iteration_log_html(records, verdicts, timings),           # p_log
        policy_html,                                              # p_policy
        ledger_html(),                                            # ledger_panel
        render_node_cards(env, working=False),                    # node_cards
        inspector_panel(run_summary, label="LA FORGE · RUN VERDICT"),  # review_summary
    )


def record_outcome(outcome, state):
    """LOG A REAL PRINT: a human reports what actually happened on the real machine,
    feeding a real outcome back into the ledger (use the tool today, then teach it)."""
    if not state or "job" not in state:
        gr.Warning("Build a job first (BUILD → SLICE), then record a real outcome here.")
        return gr.update(), ledger_html(), render_node_cards(Environment(temp=22, humidity=45))
    job = Job(**state["job"])
    env = Environment(**state["env"])
    settings = PrintSettings(**state["settings"])
    entry = reflect_on_job(job, env, settings, outcome, LEDGER)
    field_log.log_event("record", {"material": job.material, "geometry": job.geometry_type,
                                    "env_temp": env.temp, "env_humidity": env.humidity, "outcome": outcome})
    msg = (f"<div class='ce-sub'>{icon('book')} Real outcome logged (earned): "
           f"<i>{entry.lesson}</i></div>")
    return msg, ledger_html(), render_node_cards(env, working=False)


def launch(**kw):
    """Single launch entrypoint so the Astrometrics theme/CSS/clock apply
    everywhere the app is started (Gradio 6 takes these on launch, not Blocks)."""
    return build().queue().launch(theme=THEME, css=CSS, head=VP_HEAD, **kw)


def _action_bar(reset_btn_label="RESET", primary_label=None, primary_variant="primary",
                primary_id=None, primary_arrow=True):
    """Build the consistent top-right action bar (small primary + persistent Reset).
    Both buttons are scale=0 so they DON'T stretch full-width. Primary buttons get
    a right-side arrow icon by default to signal "proceed to next stage".
    If primary_id is omitted, a stable kebab-case id is derived from the label."""
    with gr.Row(elem_classes=["ce-actionbar"]):
        reset = gr.Button(reset_btn_label, elem_classes=["ce-pillbtn", "ce-act"], scale=0)
        primary = None
        if primary_label:
            primary_classes = ["ce-act"]
            if primary_arrow:
                primary_classes.append("ce-icon-arrow-after")
            if primary_id is None:
                primary_id = "ce-" + primary_label.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("'", "")
            primary = gr.Button(primary_label, variant=primary_variant,
                                elem_classes=primary_classes, elem_id=primary_id, scale=0)
    return reset, primary


def refresh_tabs(state):
    """Refresh on every tab visit: the PRINT plan readouts, the override sliders
    (seeded to the Engineer's plan), and the REVIEW session record."""
    vals = _print_plan_values(state)
    return (job_readout(state), plan_testing_html(state), plan_card_html(state),
            plan_verdict_html(state),
            gr.update(value=vals["nozzle_temp"]), gr.update(value=vals["bed_temp"]),
            gr.update(value=vals["fan_pct"]), gr.update(value=vals["retraction_mm"]),
            review_record_html(state))


def seed_plan_sliders(state):
    """Reset the override sliders back to the Engineer's proposed plan."""
    vals = _print_plan_values(state)
    return (gr.update(value=vals["nozzle_temp"]), gr.update(value=vals["bed_temp"]),
            gr.update(value=vals["fan_pct"]), gr.update(value=vals["retraction_mm"]))


# outputs touched by Reset (shared by the persistent Reset on every tab)
def _reset_outputs(ledger_panel, node_cards, review_summary, p_curve, p_policy, p_log,
                   p_headline, outcome_panel, results_group, real_log_msg, studio_log,
                   part, model3d, part_placeholder, part_status, build_results,
                   read_results, tabs, review_record):
    return [ledger_panel, node_cards, review_summary, p_curve, p_policy, p_log,
            p_headline, outcome_panel, results_group, real_log_msg, studio_log,
            part, model3d, part_placeholder, part_status, build_results, read_results, tabs,
            review_record]


def build() -> gr.Blocks:
    with gr.Blocks(title="Microfactory Node: 3D Printer") as demo:
        gr.HTML(command_bar(llm.backend_status()))
        # header row: dropdown + warm button + info icon only (NO background tints, NO stretching)
        with gr.Row(elem_id="ce-modelswitch"):
            model_select = gr.Dropdown(MODEL_OPTIONS, value=MODEL_OPTIONS[0],
                                       show_label=False, container=False,
                                       elem_classes=["ce-modeldd"], scale=0)
            warm_btn = gr.Button("WARM UP", elem_id="ce-warm",
                                   elem_classes=["ce-pillbtn", "ce-icon-bolt"], scale=0)
            model_status = gr.HTML(_model_icon(), elem_classes=["ce-status-inline"])

        state = gr.State()
        part = gr.State({"geometry": None, "mesh": None, "label": None, "read": None})

        with gr.Tabs() as tabs:
            # ───────────────────────── BUILD · define the job ────────────────────────
            with gr.Tab("LOAD", id="studio"):
                # Top row: ENVIRONMENT + OVERRIDE + POSITION + MATERIAL grouped on the left;
                # RANDOMIZE / RESET / SLICE grouped on the right.
                with gr.Row(elem_classes=["ce-actionbar", "ce-envbar"], equal_height=False):
                    with gr.Column(elem_classes=["ce-inline-group", "ce-envbar-left"], scale=0):
                        with gr.Row(elem_classes=["ce-inline-pills"]):
                            with gr.Column(elem_classes=["ce-inline-group"], scale=0):
                                gr.HTML("<div class='ce-inline-label'>ENVIRONMENT (SIMULATED)</div>")
                                sensors_readout = gr.HTML(elem_classes=["ce-envbar-readout"])
                                gr.HTML("<button class='ce-pillbtn ce-icon-sliders' "
                                        "data-popup-trigger='override' type='button' "
                                        "id='ce-override' "
                                        "style='background:var(--ao-surface);color:var(--ao-orange);"
                                        "border:none;padding:5px 15px;border-radius:999px;"
                                        "text-transform:uppercase;letter-spacing:.5px;font-size:12px;"
                                        "font-weight:700;cursor:pointer;display:inline-flex;"
                                        "align-items:center;gap:6px;'>OVERRIDE</button>")
                            with gr.Column(elem_classes=["ce-inline-group"], scale=0):
                                gr.HTML("<div class='ce-inline-label'>POSITION"
                                        "<span class='ce-callout' tabindex='0'>" + icon("info", size=10) +
                                        "<span class='ce-tip'>edges/corners run cooler → warp/adhesion risk</span>"
                                        "</span></div>")
                                bed_position = gr.Radio(BED_POSITIONS, value="center", show_label=False,
                                                        elem_classes=["ce-pills"])
                            with gr.Column(elem_classes=["ce-inline-group"], scale=0):
                                gr.HTML("<div class='ce-inline-label'>MATERIAL</div>")
                                material = gr.Radio(MATERIALS, value="PLA", show_label=False, elem_classes=["ce-pills"])
                    # spacer pushes the action group to the right edge
                    gr.HTML("<div style='flex:1;'></div>")
                    with gr.Column(elem_classes=["ce-inline-group", "ce-envbar-actions"], scale=0):
                        gr.HTML("<div class='ce-inline-label'>&#8203;</div>")  # invisible label for alignment
                        with gr.Row(elem_classes=["ce-inline-pills"]):
                            roll_btn = gr.Button("RANDOMIZE", elem_id="ce-randomize",
                                                 elem_classes=["ce-pillbtn", "ce-icon-shuffle"], scale=0)
                            reset_s = gr.Button("RESET", elem_id="ce-reset-load",
                                                elem_classes=["ce-pillbtn", "ce-act"], scale=0)
                            run_btn = gr.Button("SLICE", variant="primary",
                                                elem_classes=["ce-act", "ce-icon-arrow-after"], elem_id="ce-run", scale=0)

                # OVERRIDE ENVIRONMENT popup (hidden by default; toggled via JS)
                gr.HTML("<div class='ce-popup-backdrop' data-popup-backdrop='override'></div>")
                with gr.Group(elem_classes=["ce-popup", "ce-popup-override"]):
                    gr.HTML("<div class='ce-popup-title'>OVERRIDE ENVIRONMENT"
                            "<span class='ce-popup-close'>✕</span></div>")
                    with gr.Row():
                        temp = gr.Number(value=22, label="AMBIENT °C", elem_classes=["ce-num"], scale=1)
                        humidity = gr.Number(value=45, label="HUMIDITY %RH", elem_classes=["ce-num"], scale=1)
                    gr.HTML("<div class='ce-sub' style='margin-top:6px;'>Override the simulated "
                            "environment to test the engineer's response to specific conditions.</div>")

                # PART card — intro + JOB LOG copy lives INSIDE here (not at top)
                with gr.Group(elem_classes=["ce-part-card"]):
                    gr.HTML(rule("PART"))
                    part_status = gr.Markdown("", elem_classes=["ce-pad"])
                    with gr.Row(equal_height=False, elem_classes=["ce-part-row"]):
                        # LEFT: 3D viewer with intro + job-log copy below it (moved from top)
                        with gr.Column(scale=3, elem_classes=["ce-part-viewer-col"]):
                            part_placeholder = gr.HTML(_viewer_placeholder())
                            model3d = gr.Model3D(value=None, label="", height=360, visible=False,
                                                    interactive=False)
                            # intro + job log moved DOWN into the part area
                            gr.HTML(tab_intro("Load the part, set the material and the room, then "
                                              "<b>SLICE</b> to read the engineer's pre-flight check. "
                                              "You give it the part, the material, and the room; it "
                                              "infers what kind of part this is."))
                            studio_log = gr.HTML(studio_log_html())
                        # RIGHT: dropzone + mesh-source buttons + NOTES
                        with gr.Column(scale=1, elem_classes=["ce-part-actions-col"]):
                            mesh_in = gr.File(file_types=[".stl", ".glb", ".obj"],
                                              label="UPLOAD MESH", show_label=False,
                                              elem_classes=["ce-drop"])
                            benchy_btn = gr.Button("QUICK-LOAD BENCHY", elem_id="ce-benchy",
                                                   elem_classes=["ce-pillbtn", "ce-icon-anchor",
                                                                 "ce-mesh-source"], scale=0)
                            # GENERATE A PRIMITIVE: styled to match QUICK-LOAD BENCHY (ce-mesh-source)
                            with gr.Accordion("GENERATE A PRIMITIVE", open=False,
                                              elem_classes=["ce-mesh-source", "ce-accordion-pill"]):
                                gen_kind = gr.Radio(["box", "cylinder", "cone", "sphere"], value="box",
                                                    show_label=False, elem_classes=["ce-pills"])
                                gen_size = gr.Number(value=30, label="SIZE (mm)", elem_classes=["ce-num"])
                                gen_btn = gr.Button("GENERATE", elem_id="ce-generate",
                                                    elem_classes=["ce-pillbtn"], scale=0)
                            description = gr.Textbox(label="NOTES (OPTIONAL)",
                                                     placeholder="e.g. 45° bracket, 60mm tall",
                                                     elem_classes=["ce-notes-inline"])

            # ───────────────── SLICE · slice + analyze + pre-flight check ─────────────
            with gr.Tab("SLICE", id="build"):
                reset_b, to_print_btn = _action_bar(primary_label="PRINT (RUN ITERATIONS)")
                gr.HTML(tab_intro("The pre-flight check, <b>before it prints</b>: slice the part, read "
                                  "precedent, flag failures, and get a second opinion. Then → PRINT."))
                with gr.Group(visible=False, elem_classes=["ce-part-card"]) as build_results:
                    # slice + motion preview side by side — equal width columns
                    gr.HTML(rule("SLICE · CROSS-SECTION + MOTION PREVIEW"))
                    with gr.Row(equal_height=False, elem_classes=["ce-part-row", "ce-slice-viz"]):
                        with gr.Column(scale=1, elem_classes=["ce-slice-col"]):
                            vp_layer = gr.Image(label="", height=360, show_label=False,
                                            interactive=False)
                        with gr.Column(scale=1, elem_classes=["ce-slice-col", "ce-vp"]):
                            vprint = gr.HTML()
                    with gr.Column(elem_classes=["ce-hslider"]):
                        vp_slider = gr.Slider(1, SCRUB_LAYERS, value=1, step=1,
                                               show_label=False, container=False)
                    gr.HTML("<div class='ce-sub' style='padding:0 12px;'>Scrub through real cross-sections of "
                            "<i>this</i> part at full mesh fidelity. The preview animates the layer rise "
                            "while the read loads below.</div>")

                    # Engineer's Read ↔ Second Opinion (one panel at a time)
                    with gr.Group(visible=False, elem_classes=["ce-card"]) as read_results:
                        backend = gr.Markdown()
                        gr.HTML(rule("THE READ"))
                        read_loader = gr.HTML()
                        read_toggle = gr.Radio(["Engineer's Read", "Second Opinion"],
                                               value="Engineer's Read", show_label=False,
                                               elem_classes=["ce-seg"])
                        with gr.Group(visible=True, elem_classes=["ce-card"]) as eng_read_group:
                            precedent = gr.HTML(elem_id="ce-precedent")
                            reasoning = gr.Markdown(elem_id="ce-reasoning")
                            risks = gr.HTML()
                            gr.HTML(rule("VALIDATION + G-CODE"))
                            spine_notes = gr.Markdown()
                            with gr.Row(equal_height=False):
                                settings_html = gr.HTML()
                                gcode_html = gr.HTML()
                            confirm_btn = gr.Button("CONFIRM & PRINT", elem_id="ce-confirm", visible=False)
                        with gr.Group(visible=False, elem_classes=["ce-card"]) as second_op_group:
                            gr.HTML("<div class='ce-sub' style='padding:0 12px;'>A separate inspector — <b>La Forge</b> — reviews "
                                    "the plan before it prints: O'Brien is an optimist, La Forge is not.</div>")
                            second_opinion_panel = gr.HTML()
                            override_btn = gr.Button("PRINT ANYWAY (I'VE REVIEWED THE OBJECTION)",
                                                     visible=False, elem_classes=["ce-pillbtn"])

            # ──────────────────── PRINT · run it, iterate, grade ─────────────────────
            with gr.Tab("PRINT", id="print"):
                reset_p, p_run = _action_bar(primary_label="PRINT")
                gr.HTML(tab_intro("Print <b>this job</b> (inherited from Build). The Engineer proposes → "
                                  "the Spine vetoes → a <b>simulated world</b> prints → the <b>Inspector "
                                  "grades</b> → policy + ledger learn. Quality compounds fail→clean."))

                # ENVBAR: what's printing (inherited from Build)
                with gr.Row(elem_classes=["ce-actionbar", "ce-envbar"]):
                    p_job = gr.HTML(job_readout(None), elem_classes=["ce-envbar-readout"])

                # THE PLAN — what we're testing · the engineer's settings · what they expect
                with gr.Group(elem_classes=["ce-card"]) as plan_card:
                    gr.HTML(rule("THE PLAN · WHAT WE'RE TESTING"))
                    plan_testing = gr.HTML(plan_testing_html(None))
                    gr.HTML("<div class='ce-sub' style='margin-top:8px;color:var(--ao-orange-soft);"
                            "letter-spacing:1px;'>ENGINEER'S PROPOSED SETTINGS · Spine-validated</div>")
                    plan_settings = gr.HTML()
                    gr.HTML("<div class='ce-sub' style='margin-top:8px;color:var(--ao-orange-soft);"
                            "letter-spacing:1px;'>WHAT THE ENGINEER EXPECTS · La Forge pre-print stance</div>")
                    plan_verdict = gr.HTML()
                    gr.HTML("<div style='margin-top:10px;display:flex;align-items:center;gap:10px;"
                            "flex-wrap:wrap;'>"
                            "<button class='ce-pillbtn ce-icon-sliders' data-popup-trigger='plan' "
                            "id='ce-override-plan' type='button' style='background:var(--ao-surface);"
                            "color:var(--ao-orange);border:none;padding:5px 15px;border-radius:999px;"
                            "text-transform:uppercase;letter-spacing:.5px;font-size:12px;font-weight:700;"
                            "cursor:pointer;display:inline-flex;align-items:center;gap:6px;'>"
                            "OVERRIDE PLAN</button>"
                            "<span class='ce-sub'>change the settings and print against your own values "
                            "instead of the engineer's plan</span></div>")

                # ITERATIONS — compact control + plain explainer
                with gr.Row(elem_classes=["ce-iter-row"]):
                    gr.HTML("<div class='ce-inline-label' style='align-self:center;"
                            "margin:0 6px 0 2px;'>ITERATIONS</div>")
                    p_iters = gr.Slider(1, 16, value=8, step=1, show_label=False, container=False,
                                        elem_classes=["ce-iter-slider"])
                    p_iter_readout = gr.HTML(
                        "<div class='ce-sub' style='align-self:center;white-space:nowrap;'>"
                        "<b>8</b> runs</div>")
                gr.HTML("<div class='ce-sub' style='margin:2px 0 10px;'>How many times to print this job "
                        "in the simulated world — each run feeds the next. 1 = single print · "
                        "4 = quick convergence · 8 = balanced climb · 16 = full convergence run.</div>")

                # OVERRIDE PLAN popup — same component as OVERRIDE ENVIRONMENT on the BUILD tab
                gr.HTML("<div class='ce-popup-backdrop' data-popup-backdrop='plan'></div>")
                with gr.Group(elem_classes=["ce-popup", "ce-popup-plan"]):
                    gr.HTML("<div class='ce-popup-title'>OVERRIDE THE ENGINEER'S PLAN"
                            "<span class='ce-popup-close'>✕</span></div>")
                    gr.HTML("<div class='ce-sub' style='border-left:3px solid var(--ao-red);"
                            "padding:6px 10px;margin-bottom:8px;'>" + icon("alert") + " The run will use "
                            "these settings instead of the Spine-validated proposal.</div>")
                    with gr.Row():
                        p_nozzle = gr.Slider(150, 300, value=200, step=1,
                                             label="NOZZLE °C", elem_classes=["ce-num"])
                        p_bed = gr.Slider(40, 120, value=60, step=1,
                                          label="BED °C", elem_classes=["ce-num"])
                    with gr.Row():
                        p_fan = gr.Slider(0, 100, value=80, step=1,
                                          label="FAN %", elem_classes=["ce-num"])
                        p_retract = gr.Slider(0, 10, value=4.5, step=0.1,
                                              label="RETRACTION mm", elem_classes=["ce-num"])
                    reset_plan_btn = gr.Button("RESET TO ENGINEER'S PLAN", elem_classes=["ce-pillbtn"])

                with gr.Group(visible=False) as results_group:
                    gr.HTML(rule("OUTCOME · WHAT HAPPENED"))
                    outcome_panel = gr.HTML()
                    p_headline = gr.Markdown()
                    gr.HTML(rule("QUALITY PER ITERATION"))
                    p_curve = gr.HTML()
                    gr.HTML(rule("ITERATION LOG"))
                    p_log = gr.HTML()
                    gr.HTML(rule("LEARNED POLICY CELL"))
                    p_policy = gr.HTML()
                    # compact secondary zone (~20%): log a REAL print back into the ledger
                    with gr.Row(elem_classes=["ce-card"]):
                        with gr.Column(scale=1):
                            gr.HTML("<div class='ce-sub'>LOG A REAL PRINT · printed this on your machine? "
                                    "Record what actually happened — it feeds the ledger.</div>")
                            with gr.Row(elem_id="ce-outcomes"):
                                b_clean = gr.Button("PRINTED CLEAN")
                                b_sag = gr.Button("SAGGED")
                                b_string = gr.Button("STRINGING")
                            real_log_msg = gr.HTML()

            # ───────────────── REVIEW · compounding + agent verdicts ─────────────────
            with gr.Tab("REVIEW", id="review"):
                reset_r, refresh = _action_bar(reset_btn_label="RESET TO BASELINE",
                                               primary_label="REFRESH LEDGER",
                                               primary_variant="secondary")
                gr.HTML(tab_intro("The whole job, end to end — inputs, O'Brien's read, La Forge's "
                                  "second opinion, the simulated run + outcome, and what the node learned. "
                                  "Plus the live ledger and the capability mesh."))
                gr.HTML(rule("LA FORGE · RUN VERDICT"))
                review_summary = gr.HTML("<div class='ce-sub'>Run the Print loop to get the Inspector's "
                                         "verdict on the whole run.</div>")
                # Full session record — the complete story of this job in one place.
                with gr.Group(elem_classes=["ce-card"]):
                    gr.HTML(rule("SESSION RECORD"))
                    review_record = gr.HTML(review_record_html(None))
                with gr.Row():
                    with gr.Column(elem_classes=["ce-card"]):
                        gr.HTML(rule("LESSON LEDGER"))
                        ledger_panel = gr.HTML(ledger_html())
                    with gr.Column(elem_classes=["ce-card"]):
                        with gr.Accordion("CAPABILITY MESH · NODE NETWORK (outlook view)", open=True):
                            node_cards = gr.HTML(render_node_cards(Environment(temp=22, humidity=45)))

        footer = gr.HTML(footer_bar())
        privacy_line = gr.HTML(visible=field_log.is_active())

        # Email signup for Microfactory updates (opt-in, privacy-first)
        with gr.Group(elem_classes=["ce-card"]):
            gr.HTML(rule("STAY IN THE LOOP"))
            gr.HTML("<div class='ce-sub'>Get Microfactory updates: new nodes, build notes, and when this thing learns to stream g-code straight to the printer. One email. No spam. Unsub any time.</div>")
            with gr.Row():
                signup_email = gr.Textbox(placeholder="you@example.com", label="EMAIL", show_label=False,
                                          elem_classes=["ce-notes-inline"], scale=3)
                signup_consent = gr.Checkbox(label="Yes, email me Microfactory updates", scale=2)
            signup_btn = gr.Button("SUBSCRIBE", elem_classes=["ce-pillbtn"])
            signup_status = gr.HTML()
            signup_privacy = gr.HTML(signups.privacy_notice())

        # ── wiring ──
        reset_outs = _reset_outputs(ledger_panel, node_cards, review_summary, p_curve, p_policy,
                                    p_log, p_headline, outcome_panel, results_group, real_log_msg,
                                    studio_log, part, model3d, part_placeholder, part_status,
                                    build_results, read_results, tabs, review_record)
        preview_outs = [part, model3d, part_status, part_placeholder]
        foot_in = [part, material, temp, humidity, bed_position]
        benchy_btn.click(load_benchy, None, preview_outs).then(status_footer, foot_in, [footer])
        gen_btn.click(generate_part, [gen_kind, gen_size], preview_outs).then(status_footer, foot_in, [footer])
        mesh_in.upload(upload_part, [mesh_in], preview_outs).then(status_footer, foot_in, [footer])
        material.change(status_footer, foot_in, [footer])

        # Model warm-up + switcher
        warm_btn.click(warm_up_pending, None, [model_status]).then(warm_up_cb, None, [model_status])
        model_select.change(select_model, [model_select], [model_status])

        # Simulated environment: roll on load, re-roll on demand, keep readout + footer in sync.
        sensor_outs = [temp, humidity, bed_position, material, sensors_readout]
        demo.load(randomize_sensors, None, sensor_outs).then(status_footer, foot_in, [footer])
        # CLOCK_JS wires the LCARS clock, popup toggles, and loader stage cycling.
        demo.load(None, None, None, js=CLOCK_JS)
        demo.load(lambda: field_log.privacy_notice() if field_log.is_active() else "",
                  None, [privacy_line])
        signup_btn.click(signups.record_signup,
                         [signup_email, signup_consent, gr.State("space" if signups.is_active() else "local")],
                         [signup_status])
        roll_btn.click(randomize_sensors, None, sensor_outs).then(status_footer, foot_in, [footer])
        for c in (temp, humidity, bed_position, material):
            c.change(sync_readout, [temp, humidity, bed_position], [sensors_readout]).then(
                status_footer, foot_in, [footer])

        # Two-step BUILD: instant loader + tab-switch, then the heavy model call (reveals
        # the results), then refresh the inherited-job readout on the Print tab.
        build_start_outs = [tabs, build_results, read_results, read_loader, vprint, vp_slider,
                            vp_layer, to_print_btn, override_btn, second_opinion_panel,
                            read_toggle, eng_read_group, second_op_group]
        build_outs = [backend, precedent, reasoning, risks, settings_html, spine_notes,
                      gcode_html, confirm_btn, node_cards, state, vprint, vp_slider, vp_layer,
                      read_loader]
        # Readouts on the PRINT plan + REVIEW record + override sliders, populated on
        # every path that lands a job (build completion, SLICE→PRINT, and tab visits).
        plan_outs = [p_job, plan_testing, plan_settings, plan_verdict,
                     p_nozzle, p_bed, p_fan, p_retract, review_record]
        run_btn.click(build_start, [part], build_start_outs).then(
            build_job, [part, material, description, temp, humidity, bed_position, model_select],
            build_outs).then(refresh_tabs, [state], plan_outs)
        run_btn.click(None, None, None, js=_SCROLL_TOP)  # scroll fires in parallel (not mid-chain)
        vp_slider.change(scrub_layer, [vp_slider, part], [vp_layer])
        read_toggle.change(toggle_read, [read_toggle, state],
                           [eng_read_group, second_op_group, second_opinion_panel,
                            to_print_btn, override_btn, state])
        override_btn.click(ack_override, state, [to_print_btn, override_btn])
        to_print_btn.click(lambda: gr.Tabs(selected="print"), None, [tabs]).then(
            refresh_tabs, [state], plan_outs).then(None, None, None, js=_SCROLL_TOP)
        tabs.select(refresh_tabs, [state], plan_outs)

        # PRINT: run the loop on THIS job (slider 1 = single print), or log a real outcome.
        print_outs = [results_group, outcome_panel, p_headline, p_curve, p_log, p_policy,
                      ledger_panel, node_cards, review_summary]
        p_run.click(run_print, [state, p_iters, p_nozzle, p_bed, p_fan, p_retract], print_outs).then(
            review_record_html, [state], [review_record]).then(
            None, None, None, js=_SCROLL_TOP)
        p_iters.change(lambda v: f"<div class='ce-sub' style='align-self:center;white-space:nowrap;'>"
                       f"<b>{int(v)}</b> runs</div>", [p_iters], [p_iter_readout])
        reset_plan_btn.click(seed_plan_sliders, [state], [p_nozzle, p_bed, p_fan, p_retract])
        for btn, oc in [(b_clean, "success"), (b_sag, "failed_sag"), (b_string, "failed_stringing")]:
            btn.click(record_outcome, [gr.State(oc), state], [real_log_msg, ledger_panel, node_cards])

        # REVIEW
        refresh.click(lambda: ledger_html(), outputs=[ledger_panel]).then(
            review_record_html, [state], [review_record])

        # persistent Reset on every tab → one baseline reset
        for rb in (reset_s, reset_b, reset_p, reset_r):
            rb.click(reset_learnings, None, reset_outs)

    return demo


demo = build()

# Monkey-patch launch so pySpaces (which calls demo.launch() without our
# custom args) still gets the Astrometrics theme, CSS, head, and SSR disabled.
_original_launch = demo.launch
def _patched_launch(**kwargs):
    kwargs.setdefault("theme", THEME)
    kwargs.setdefault("css", CSS)
    kwargs.setdefault("head", VP_HEAD)
    kwargs.setdefault("ssr_mode", False)
    return _original_launch(**kwargs)
demo.launch = _patched_launch

if __name__ == "__main__":
    print(f"[chief-engineer] {llm.backend_status()} | seeded {_loaded} lessons this run")
    demo.launch(ssr_mode=False, server_name="0.0.0.0", server_port=7860, share=False)
