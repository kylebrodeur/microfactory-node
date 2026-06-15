# What's Simulated, What's Real, and What the Physical World Needs

The Chief Engineer's value is a **closed learning loop**: propose settings →
observe the outcome → learn → do better next time. To demo that loop without a
printer farm — and to keep it reproducible for judges — the *outcome* step runs
in a deterministic simulator. Everything else is real.

## Honest-claims table

| Component | Status | Notes |
|-----------|--------|-------|
| Environment-keyed retrieval (RAG) | **Real** | `core/ledger.py` — exact match + normalized env-distance |
| Chief Engineer reasoning (LLM) | **Real** | `core/chief_engineer.py` — real Ollama (gemma4), with deterministic fallback |
| Learned policy (parametric) | **Real** | `learn/policy.py` — offsets per (material, geometry, env-bucket), persisted |
| Spine safety veto | **Real** | `core/spine.py` — clamps unsafe settings; LLM proposes, code decides |
| Knowledge ingestion | **Real** | `ingest/` — slicer/firmware configs → references; research → lessons |
| **Print outcome** | **Simulated** | `sim/outcome.py` — physics-lite stand-in for the printer + sensors |
| Capability mesh (6 nodes) | **Context** | one node's logic is real; the others render as available capacity |
| Weight-level fine-tuning | **Framed frontier** | `ingest/modal_app.py` stub; the ledger becomes training data |

## The one simulated boundary

`sim/outcome.py` is the **only** stand-in for physical reality. It models the
same physics the seed lessons describe (cooling vs. overhang sag, humidity →
stringing, ABS warp, bed temp → adhesion, and **build-plate position** — edges/
corners of a heated bed run cooler + draftier, so warp/adhesion suffer there,
worst for high-shrink materials) and returns an outcome + a 0–1 quality score.
It is deterministic, so the learning curve is reproducible.

Critically, this is **not the model grading its own work**. The Chief Engineer
proposes; this separate world returns an outcome the model never sees in
advance — exactly the role a printer and its sensors play.

## Swapping in the physical world

Replace `sim.outcome.simulate(settings, job, env)` with a real adapter that
returns the same `SimResult`. Three interfaces are needed:

1. **Actuation — stream settings to the printer.** Generate g-code from the
   proposed `PrintSettings` (the readout in `viewer.gcode_readout` is the seed
   of this) and stream over USB/serial (Marlin) or the Moonraker/Klipper API.
   *Frontier on the roadmap: node → Ender serial control.*
2. **Sensing — read the environment.** A temp/humidity sensor (e.g. a BME280 on
   a Pi) feeds the `Environment` that today comes from the sliders.
3. **Outcome detection — judge the print.** A camera + a defect classifier
   (the **3D-ADAM** taxonomy already encoded in `ingest/distill.py`) maps an
   image to `outcome` + `quality`. This replaces the simulator's scoring.

Each is a clean substitution behind the existing types — the loop, the policy,
the ledger, and the UI do not change. That is the point of keeping the
simulated boundary this narrow.
