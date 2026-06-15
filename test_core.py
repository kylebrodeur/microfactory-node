"""Headless tests for the deterministic core (no Ollama required).

Exercises retrieval, the Spine veto, the offline-fallback advisor, and the
reflection append. Run: `make test` (= `uv run python test_core.py`).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Force the deterministic fallback path so this suite is truly offline + fast
# even when `ollama serve` is running (otherwise advise() would do a real, slow
# model call and appear to hang). Set before importing modules that call the LLM.
os.environ.setdefault("CHIEF_ENGINEER_OFFLINE", "1")

from core.chief_engineer import advise
from core.ledger import LedgerManager
from core.models import Environment, Job, PrintSettings
from core.reflect import reflect_on_job
from core.seed_lessons import ensure_seeded
from core.spine import SpineValidator


def test_seed_and_retrieve():
    led = LedgerManager(Path(tempfile.mkdtemp()) / "lessons.jsonl")
    n = ensure_seeded(led)
    assert n == 12, f"expected 12 seeds, got {n}"
    # PLA overhang in a warm room → should match the warm-room sag seed nearest
    hits = led.retrieve("PLA", "overhang", temp=28, humidity=50)
    assert hits, "expected precedent for PLA/overhang"
    assert hits[0][0].geometry_type == "overhang" and hits[0][0].material == "PLA"
    # a material+geometry with no seeds → empty (valid 'no precedent' case)
    assert led.retrieve("TPU", "vase", 22, 45) == []
    print("✓ seed + retrieval (nearest:", hits[0][0].job_id, f"dist {hits[0][1]:.2f})")


def test_spine_veto():
    s = SpineValidator()
    # model proposes a PLA nozzle way too hot → must clamp to 220 and trip approval
    bad = PrintSettings(nozzle_temp=260, bed_temp=60, retraction_mm=5, fan_pct=100, first_layer_fan_pct=0)
    res = s.check(bad, "PLA")
    assert res.settings.nozzle_temp == 220, res.settings.nozzle_temp
    assert res.requires_approval and res.vetoes
    print("✓ spine clamps PLA 260→220 and trips HITL:", res.vetoes[0])


def test_fallback_advise():
    led = LedgerManager(Path(tempfile.mkdtemp()) / "lessons.jsonl")
    ensure_seeded(led)
    job = Job(geometry_type="overhang", material="PLA", description="45° bracket")
    env = Environment(temp=28, humidity=50)
    rec = advise(job, env, led.retrieve("PLA", "overhang", 28, 50))
    assert rec.used_fallback, "no Ollama here → should use fallback"
    assert rec.advice.settings.nozzle_temp > 0 and rec.advice.risks
    print("✓ fallback advise:", rec.advice.reasoning[:70], "…")


def test_reflect_appends():
    led = LedgerManager(Path(tempfile.mkdtemp()) / "lessons.jsonl")
    ensure_seeded(led)
    before = led.count()["earned"]
    job = Job(geometry_type="bridge", material="PETG")
    env = Environment(temp=24, humidity=44)
    settings = PrintSettings(nozzle_temp=235, bed_temp=80, retraction_mm=4, fan_pct=70, first_layer_fan_pct=0)
    entry = reflect_on_job(job, env, settings, "success", led)
    assert led.count()["earned"] == before + 1 and entry.source == "earned"
    print("✓ reflect appends earned lesson:", entry.lesson[:70], "…")


def test_retrieval_orders_by_env_distance():
    led = LedgerManager(Path(tempfile.mkdtemp()) / "lessons.jsonl")
    ensure_seeded(led)
    # PLA/stringing seeds sit at (22,45) and (24,70). A humid query should rank
    # the humid seed first; a dry query the dry one.
    humid = led.retrieve("PLA", "stringing", temp=24, humidity=70)
    dry = led.retrieve("PLA", "stringing", temp=22, humidity=45)
    assert humid[0][0].env_humidity >= 65, humid[0][0].env_humidity
    assert dry[0][0].env_humidity <= 50, dry[0][0].env_humidity
    print("✓ retrieval ranks by normalized env distance (humid→humid, dry→dry)")


def test_gcode_readout_ties_to_settings():
    from core.viewer import gcode_readout
    s = PrintSettings(nozzle_temp=205, bed_temp=60, retraction_mm=5, fan_pct=100, first_layer_fan_pct=0)
    g = gcode_readout(s, "PLA")
    assert "M104 S205" in g and "M140 S60" in g, g
    assert "layer height 0.20 mm" in g, g
    print("✓ g-code header is populated from proposed settings")


# GIF export button removed; keep motion preview tests via UI smoke if needed.


def test_virtual_printer_html_ties_to_settings():
    from core.widgets import virtual_printer_html
    from core.viewer import generate_primitive
    from core.models import PrintSettings
    mesh, _geo = generate_primitive("box", 20)
    default_html = virtual_printer_html(mesh)
    assert "0.20 mm layers" in default_html, default_html
    fine = PrintSettings(nozzle_temp=200, bed_temp=60, retraction_mm=4.5, fan_pct=80,
                         first_layer_fan_pct=0, layer_height=0.12)
    fine_html = virtual_printer_html(mesh, settings=fine)
    assert "0.12 mm layers" in fine_html, fine_html
    print("✓ virtual-print preview layer height follows PrintSettings")


def test_ingest_distiller():
    from pathlib import Path as _P
    from ingest.distill import parse_prusa_ini, parse_klipper_cfg, parse_marlin_config
    samples = _P(__file__).resolve().parent / "ingest" / "samples"
    prusa = parse_prusa_ini(samples / "prusa_filaments.ini")
    assert any(f.material == "PLA" and f.param == "bed_temp" for f in prusa), "PLA bed_temp not parsed"
    assert parse_klipper_cfg(samples / "klipper_extruder.cfg"), "klipper max_temp not parsed"
    assert parse_marlin_config(samples / "marlin_config.h"), "marlin maxtemp not parsed"
    print("✓ distiller parses Prusa INI + Klipper cfg + Marlin config")


def test_precedent_eval_narration():
    from core.viewer import precedent_eval_html
    from core.models import LessonEntry as LE, Environment as E
    e = LE(job_id="x", material="PLA", geometry_type="overhang", env_temp=28, env_humidity=50,
           outcome="failed_sag", lesson="sagged", source="seed", timestamp="t")
    html = precedent_eval_html([(e, 0.28)], E(temp=32, humidity=62))
    assert "warmer" in html and "more humid" in html and "worse" in html, html
    assert "NO CLOSE PRECEDENT" in precedent_eval_html([], E(temp=22, humidity=45))
    print("✓ precedent evaluation narrates env delta + novel case")


def test_simulator_physical_and_deterministic():
    from sim.outcome import simulate
    from core.models import Job as J, Environment as E, PrintSettings as PS
    bad = PS(nozzle_temp=235, bed_temp=80, retraction_mm=4, fan_pct=40, first_layer_fan_pct=0)
    r1 = simulate(bad, J(geometry_type="bridge", material="PETG"), E(temp=29, humidity=62))
    assert r1.outcome != "success" and r1.quality < 0.7, r1
    r2 = simulate(bad, J(geometry_type="bridge", material="PETG"), E(temp=29, humidity=62))
    assert (r2.outcome, r2.quality) == (r1.outcome, r1.quality), "simulator must be deterministic"
    good = PS(nozzle_temp=205, bed_temp=60, retraction_mm=5, fan_pct=100, first_layer_fan_pct=0)
    rg = simulate(good, J(geometry_type="overhang", material="PLA"), E(temp=20, humidity=40))
    assert rg.outcome == "success", rg
    # build-plate position: corner > edge > center warp for a shrink-prone material;
    # 'center' (default) must be unchanged.
    abs_s = PS(nozzle_temp=248, bed_temp=95, retraction_mm=4, fan_pct=20, first_layer_fan_pct=0)
    env = E(temp=22, humidity=40)
    qc = simulate(abs_s, J(geometry_type="adhesion", material="ABS", bed_position="center"), env).quality
    qe = simulate(abs_s, J(geometry_type="adhesion", material="ABS", bed_position="edge"), env).quality
    qk = simulate(abs_s, J(geometry_type="adhesion", material="ABS", bed_position="corner"), env).quality
    assert qc > qe > qk, (qc, qe, qk)
    assert qc == simulate(abs_s, J(geometry_type="adhesion", material="ABS"), env).quality
    print("✓ simulator is physical + deterministic, and bed-position warps edges/corners")


def test_policy_learns_and_generalizes():
    import tempfile, os
    from pathlib import Path
    from learn.policy import LearnedPolicy
    from learn.loop import run_session, run_iteration
    from core.ledger import LedgerManager
    from core.models import Job as J, Environment as E
    d = Path(tempfile.mkdtemp())
    pol = LearnedPolicy(path=d / "policy.json")
    led = LedgerManager(path=d / "lessons.jsonl")
    job, env = J(geometry_type="bridge", material="PETG"), E(temp=29, humidity=62)
    sess = run_session(job, env, 10, pol, led)
    assert sess.trajectory[-1] > sess.trajectory[0], "quality must improve"
    assert sess.first_success is not None, "should reach a clean print"
    # generalization: a similar (same-bucket, different exact env) job benefits
    cold = sess.trajectory[0]
    warm_start = run_iteration(J(geometry_type="bridge", material="PETG"),
                               E(temp=28, humidity=58), pol, led, 1, record=False)
    assert warm_start.result.quality > cold, "policy must transfer to similar conditions"
    print("✓ policy learns (quality climbs to a clean print) and generalizes to similar jobs")


if __name__ == "__main__":
    test_seed_and_retrieve()
    test_spine_veto()
    test_fallback_advise()
    test_reflect_appends()
    test_retrieval_orders_by_env_distance()
    test_gcode_readout_ties_to_settings()
    test_virtual_printer_html_ties_to_settings()
    test_ingest_distiller()
    test_precedent_eval_narration()
    test_simulator_physical_and_deterministic()
    test_policy_learns_and_generalizes()
    print("\nALL CORE TESTS PASSED")
