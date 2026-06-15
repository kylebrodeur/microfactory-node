"""Preflight — gated GO/NO-GO check for the real local stack. Run this FIRST
thing when you sit down locally, before touching anything else:

    ollama serve &          (if not already running)
    make preflight          [CHIEF_ENGINEER_MODEL=gemma4:e2b make preflight]
                            (or: uv run python -m scripts.preflight)

It exercises the REAL model path (the thing the sandbox could never verify) and
grades every gate the demo depends on. Each FAIL points at the matching section
of docs/plan/06-CONTINGENCY.md — so a failure costs minutes, not a night.

Never touches demo state: uses a temp ledger copy. Offline gates still run
without Ollama (reported as SKIP for the live ones). Exit code 1 if any
REQUIRED gate fails — safe to wire into a pre-record ritual.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from core import llm                                            # noqa: E402
from core.ledger import LedgerManager                      # noqa: E402
from core.models import Advice, Environment, Job           # noqa: E402
from core.prompts import REFLECT_SYSTEM, build_reflect_prompt, build_system_prompt  # noqa: E402
from core.spine import SpineValidator                      # noqa: E402
from core.models import PrintSettings                      # noqa: E402

RESULTS: list[tuple[str, str, str]] = []   # (gate, status, detail)
CONTINGENCY = "docs/plan/06-CONTINGENCY.md"


def record(gate: str, status: str, detail: str, section: str = "") -> None:
    ptr = f"  → see {CONTINGENCY} §{section}" if (section and status == "FAIL") else ""
    RESULTS.append((gate, status, detail))
    icon = {"PASS": "✅", "WARN": "🟡", "FAIL": "🔴", "SKIP": "⏭"}[status]
    print(f"{icon} {gate}: {status} — {detail}{ptr}")


def _temp_ledger() -> LedgerManager:
    tmp = Path(tempfile.mkdtemp(prefix="preflight_")) / "lessons.jsonl"
    seeds = HERE / "data" / "seed_lessons.jsonl"
    if seeds.exists():
        shutil.copy(seeds, tmp)
    else:
        tmp.touch()
    return LedgerManager(path=tmp)


# --- G1: environment ---------------------------------------------------------
def g1_environment() -> bool:
    if "4b" == llm.MODEL.split(":")[-1]:
        record("G1 env", "FAIL", f"model tag '{llm.MODEL}' — gemma4:4b DOES NOT EXIST (Kaggle landmine)", "G1")
        return False
    if not llm.is_available():
        record("G1 env", "FAIL", "Ollama daemon unreachable (is `ollama serve` running?)", "G1")
        return False
    try:
        import ollama
        tags = [m.get("model") or m.get("name") for m in ollama.list().get("models", [])]
    except Exception as e:
        tags = []
        record("G1 env", "WARN", f"daemon up but list() odd: {e!r}")
    if tags and not any(llm.MODEL in (t or "") or (t or "").startswith(llm.MODEL) for t in tags):
        record("G1 env", "FAIL", f"'{llm.MODEL}' not pulled. Available: {tags}", "G1")
        return False
    record("G1 env", "PASS", f"daemon up, model '{llm.MODEL}' present ({len(tags)} tags local)")
    _tiny_titan_check()
    return True


def _tiny_titan_check() -> None:
    """Report Tiny Titan ($1.5k ≤4B special award) eligibility from `ollama show`.
    Informational — never blocks the demo. Verified 6/10: the field guide's 32B cap
    counts TOTAL params ("not just active"); no ruling found for MatFormer E-models
    (raw 5.1B/8.0B vs effective ~2B/~4B) on the ≤4B award → treat as ambiguous and
    ASK in the org discussions before tagging."""
    try:
        import ollama
        info = ollama.show(llm.MODEL)
    except Exception as e:
        record("Tiny Titan", "SKIP", f"`ollama show` unavailable ({e!r:.60}) — run it by hand")
        return

    def _get(obj, *keys):
        for k in keys:
            if isinstance(obj, dict) and k in obj:
                return obj[k]
            if hasattr(obj, k):
                return getattr(obj, k)
        return None

    details = _get(info, "details") or {}
    modelinfo = _get(info, "modelinfo", "model_info") or {}
    psize = _get(details, "parameter_size")  # e.g. "4.3B"
    b = None
    if isinstance(modelinfo, dict):
        for k, v in modelinfo.items():
            if str(k).endswith("parameter_count") and isinstance(v, (int, float)):
                b = float(v) / 1e9
    if b is None and isinstance(psize, str):
        try:
            b = float(psize.strip().upper().rstrip("B"))
        except Exception:
            b = None

    # Gemma 3n E-models report RAW params via ollama (E4B~8B) but are designed as
    # EFFECTIVE 4B/2B (MatFormer + per-layer embeddings). The badge counts the
    # effective size, so key off the model NAME, not the raw count.
    import re
    em = re.search(r"e(\d+)b", llm.MODEL.lower())
    eff = float(em.group(1)) if em else None
    raw = f"{b:.1f}B raw" if b is not None else "raw n/a"

    if eff is not None:
        if eff <= 4.0:
            # Verified 6/10: the guide's 32B cap counts TOTAL params ("not just
            # active") and no ruling exists for E-models on the <=4B award — so
            # effective-params eligibility is genuinely AMBIGUOUS. Ask, don't tag.
            record("Tiny Titan", "WARN",
                   f"{llm.MODEL}: effective ~{eff:.0f}B but {raw} — $1.5k award counts params "
                   f"ambiguously for E-models (32B cap counts TOTAL). ASK in the org "
                   f"discussions before tagging tiny-titan")
        else:
            record("Tiny Titan", "WARN",
                   f"{llm.MODEL}: effective ~{eff:.0f}B > 4B — outside Tiny Titan either way")
    elif b is None:
        record("Tiny Titan", "WARN", f"couldn't parse params (details={psize!r}); check `ollama show {llm.MODEL}` by hand")
    elif b <= 4.0:
        record("Tiny Titan", "PASS", f"{b:.2f}B ≤ 4B → ELIGIBLE; add the tag")
    else:
        record("Tiny Titan", "WARN", f"{b:.2f}B > 4B — outside Tiny Titan; skip that badge")


# --- G2-G4: the load-bearing live calls ---------------------------------------
def g2_g4_live_calls() -> None:
    lm = _temp_ledger()
    # Case A: precedent-rich (humid PETG stringing — seeds 007/008/012 match)
    job_a = Job(geometry_type="stringing", material="PETG", description="calibration tower, humid day")
    env_a = Environment(temp=25, humidity=65)
    retrieved = lm.retrieve("PETG", "stringing", 25, 65, k=3)
    sys_a = build_system_prompt(job_a, env_a, retrieved)
    # Case B: novel (TPU vase — no precedent in seeds)
    job_b = Job(geometry_type="vase", material="TPU", description="flexible vase")
    env_b = Environment(temp=22, humidity=45)
    sys_b = build_system_prompt(job_b, env_b, lm.retrieve("TPU", "vase", 22, 45, k=3))

    # Prompt-length budget (GEMMA-STEERING Technique 5): small-Gemma attention
    # quality degrades past ~800 tokens. Informational — trim references/k if hot.
    est = len(sys_a) // 4
    flag = "  ⚠ over the ~800-token small-Gemma budget — trim references / k" if est > 800 else ""
    print(f"   prompt size: ~{est} tokens (precedent-rich case){flag}")

    times, parses, schemas = [], 0, 0
    advice_a = None
    N = 3
    for i in range(N):
        t0 = time.time()
        raw = llm.chat_json(sys_a, "Give your recommendation for THIS job now.")
        dt = time.time() - t0
        times.append(dt)
        print(f"   live call {i+1}/{N}: {dt:5.1f}s {'(json ok)' if raw else '(parse FAIL)'}")
        if raw is not None:
            parses += 1
            try:
                advice_a = Advice(**raw)
                schemas += 1
            except Exception as e:
                print(f"     schema reject: {e!s:.120}")

    # G2 latency — separate the one-time COLD model-load from WARM steady-state.
    # The cold call (first) only happens once; you pre-warm before recording, so
    # the demo experience is the warm number. Gate on warm, report cold as a tip.
    cold = times[0]
    warm = times[1:] if len(times) > 1 else times
    warm_avg = sum(warm) / len(warm)
    print(f"   cold-start {cold:5.1f}s (one-time model load) · warm avg {warm_avg:.1f}s "
          f"over {len(warm)} — pre-warm with one throwaway call before recording")
    # Bands calibrated against real cockpit driving (Kyle, 6/10): warm ~18s on
    # e4b reads fine in a narrated demo, so <20s is a PASS, not a warning.
    if warm_avg < 20:
        record("G2 latency", "PASS",
               f"warm avg {warm_avg:.1f}s (cold {cold:.1f}s) — fine for a live narrated demo ({llm.MODEL}); pre-warm before recording")
    elif warm_avg < 35:
        record("G2 latency", "WARN",
               f"warm avg {warm_avg:.1f}s (cold {cold:.1f}s) — long pauses; tighten prompt, or gemma4:e2b / ZeroGPU", "G2")
    else:
        record("G2 latency", "FAIL",
               f"warm avg {warm_avg:.1f}s — too slow even warm; use gemma4:e2b or ZeroGPU", "G2")

    # G3 contract
    if schemas == N:
        record("G3 contract", "PASS", f"{schemas}/{N} valid JSON + Advice schema")
    elif schemas >= 1:
        record("G3 contract", "WARN", f"only {schemas}/{N} schema-valid (fallback will cover, but video needs live)", "G3")
    else:
        record("G3 contract", "FAIL", f"0/{N} valid — live path unusable as-is", "G3")

    # G4 reasoning quality — the load-bearing moment, heuristically graded
    if advice_a is not None:
        r = advice_a.reasoning.lower()
        checks = {
            "evaluates precedent (cites a job/precedent/prior)": any(w in r for w in ("precedent", "prior", "job", "seed-", "last time", "before")),
            "reasons about the room (humidity/temp/moisture/dry)": any(w in r for w in ("humid", "moisture", "temp", "°c", " rh", "dry", "wet")),
            "substantive (>120 chars)": len(advice_a.reasoning) > 120,
            "flags at least one risk region": len(advice_a.risks) >= 1,
        }
        failed = [k for k, ok in checks.items() if not ok]
        print(f"   reasoning sample: \"{advice_a.reasoning[:180]}...\"")
        if not failed:
            record("G4 reasoning", "PASS", "precedent-evaluation text present and substantive")
        else:
            record("G4 reasoning", "WARN", f"weak on: {'; '.join(failed)} — prompt-tune before recording", "G4")
    else:
        record("G4 reasoning", "FAIL", "no schema-valid advice to grade", "G3")

    # G4b novel case — must NOT hallucinate precedent
    raw_b = llm.chat_json(sys_b, "Give your recommendation for THIS job now.")
    if raw_b:
        try:
            adv_b = Advice(**raw_b)
            rb = adv_b.reasoning.lower()
            honest = any(w in rb for w in ("no close precedent", "no precedent", "no prior", "novel", "material properties", "first "))
            cites_fake = "seed-" in rb
            if honest and not cites_fake:
                record("G4b novel-case", "PASS", "says no-precedent / reasons from material properties")
            else:
                record("G4b novel-case", "WARN", f"novel-job reasoning suspect (honest={honest}, cites_fake={cites_fake}) — check by eye", "G4")
            print(f"   novel sample: \"{adv_b.reasoning[:180]}...\"")
        except Exception:
            record("G4b novel-case", "WARN", "novel call returned but schema-invalid", "G3")
    else:
        record("G4b novel-case", "WARN", "novel call failed to parse", "G3")

    # G5 reflection
    raw_r = llm.chat_json(REFLECT_SYSTEM, build_reflect_prompt(
        job_a, env_a, "nozzle 230°C, bed 80°C, retraction 4.5mm, fan 40%, first-layer fan 0%", "success"))
    lesson = (raw_r or {}).get("lesson") if isinstance(raw_r, dict) else None
    if lesson and len(lesson) > 30:
        record("G5 reflection", "PASS", f"lesson distilled: \"{lesson[:100]}...\"")
    elif lesson:
        record("G5 reflection", "WARN", f"lesson thin: \"{lesson}\"", "G4")
    else:
        record("G5 reflection", "WARN", "reflect returned no lesson (deterministic fallback covers it)", "G3")


# --- G6: spine (offline, always) ----------------------------------------------
def g6_spine() -> None:
    checked = SpineValidator().check(PrintSettings(
        nozzle_temp=260, bed_temp=60, retraction_mm=5, fan_pct=100, first_layer_fan_pct=0), "PLA")
    if checked.vetoes and checked.settings.nozzle_temp < 260:
        record("G6 spine", "PASS", f"unsafe PLA 260°C clamped to {checked.settings.nozzle_temp:.0f}°C ({len(checked.vetoes)} veto)")
    else:
        record("G6 spine", "FAIL", "Spine did NOT clamp an unsafe setting — demo safety claim broken", "G6")


# --- G7: app serves (offline, always) -------------------------------------------
def g7_app() -> None:
    try:
        import urllib.request
        import app as A
        d = A.build()
        d.launch(prevent_thread_lock=True, server_name="127.0.0.1", server_port=7991, quiet=True)
        code = urllib.request.urlopen("http://127.0.0.1:7991/", timeout=15).status
        d.close()
        if code == 200:
            record("G7 app", "PASS", "build() + launch + HTTP 200")
        else:
            record("G7 app", "FAIL", f"HTTP {code}", "G7")
    except Exception as e:
        record("G7 app", "FAIL", f"{e!r:.140}", "G7")


# --- G8: assets + data (offline, always) ---------------------------------------
def g8_assets() -> None:
    missing = [n for n in ("overhang.glb", "bridge.glb", "vase.glb", "cube.glb")
               if not (HERE / "assets" / n).exists()]
    seeds = HERE / "data" / "seed_lessons.jsonl"
    n_seeds = len([l for l in seeds.read_text().splitlines() if l.strip()]) if seeds.exists() else 0
    if not missing and n_seeds == 12:
        record("G8 assets", "PASS", "4 meshes present, 12 seed lessons")
    elif missing:
        record("G8 assets", "FAIL", f"missing meshes {missing} — run `make assets`", "G8")
    else:
        record("G8 assets", "WARN", f"seed count {n_seeds} != 12 — verify data/seed_lessons.jsonl", "G8")


def main() -> None:
    print(f"Chief Engineer preflight — model={llm.MODEL}  ({time.strftime('%Y-%m-%d %H:%M')})")
    print("=" * 70)
    live = g1_environment()
    if live:
        g2_g4_live_calls()
    else:
        for g in ("G2 latency", "G3 contract", "G4 reasoning", "G4b novel-case", "G5 reflection"):
            record(g, "SKIP", "no live backend (offline gates still checked below)")
    g6_spine()
    g7_app()
    g8_assets()

    print("=" * 70)
    fails = [g for g, s, _ in RESULTS if s == "FAIL"]
    warns = [g for g, s, _ in RESULTS if s == "WARN"]
    skips = [g for g, s, _ in RESULTS if s == "SKIP"]
    if fails:
        print(f"🔴 NO-GO: {len(fails)} gate(s) failed: {', '.join(fails)}")
        print(f"   Work {CONTINGENCY} top-to-bottom for each, then re-run.")
        sys.exit(1)
    if skips:
        print("🟡 OFFLINE-ONLY PASS — fallback demo is safe, but DO NOT record the video")
        print("   until the live gates run green. Start `ollama serve` and re-run.")
        sys.exit(0)
    if warns:
        print(f"🟡 GO with warnings ({', '.join(warns)}) — read them before recording.")
        sys.exit(0)
    print("🟢 GO — all gates green. Record the demo today, not tomorrow.")


if __name__ == "__main__":
    main()
