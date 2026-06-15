# Project history & findings (moved out of the RUNBOOK)

Reference/archive — the proven results and the phase-by-phase history. The RUNBOOK
(`docs/RUNBOOK.md`) is now the clean operational doc; this holds the "what we already
proved + decided" record so it doesn't clutter the day-to-day.

---

## Findings log — real hardware (PEGASUS, 2026-06-10)

Preflight ran clean **end-to-end on the real model stack, twice per model**. All gates
PASS on both models (env, JSON contract, reasoning quality, novel-case honesty,
reflection, Spine clamp, app serves, assets). Beat 3 — the precedent-evaluating
reasoning — works on camera-quality output.

| | `gemma4:e4b` | `gemma4:e2b` |
|---|---|---|
| Warm latency | 18.5s | **10.3s** (≈2× faster) |
| Cold load (one-time) | 38.7s | 41.8s |
| Params (raw / effective) | 8.0B / ~4B (MatFormer) | 5.1B / ~2B |
| G3 JSON contract | 3/3 | 3/3 |
| G4 reasoning | sharpest ("hygroscopicity is the dominant failure mode") | substantive, cites 3 precedents, slightly more generic |
| G4b novel case | honest "no close precedent" | honest "no close precedent" |

**Decisions taken:**
- **Latency bands:** warm < 20s = PASS (reads fine narrated); 20–35s WARN; ≥35s FAIL.
- **Model:** record on **e4b** (sharpest reasoning; warm ~18s). e2b is one env var away.
- **GEMMA-STEERING adopted** (`reference/GEMMA-STEERING.md`): fence-strip net in `chat_json`,
  prompt-size telemetry in preflight (~600 tokens; budget ~800).
- **Tiny Titan:** separate $1.5k award; E-model eligibility AMBIGUOUS (32B cap counts TOTAL
  params; e2b 5.1B raw) → **ask in org discussions before tagging.**
- **Hackathon facts (web-verified 6/10):** submission = Space in the org w/ README tags +
  video link + social link (no form; registration closed Jun 3). Storytelling = judging
  principle, NOT a badge. No video/writeup length limits found.
- **Space dress rehearsal PASS:** clean-venv pip install + app boots + HTTP 200 + honest
  🟡 fallback banner.

## Phase history (0 → 6)

- **Phase 0 — setup ✅** `make setup`; `ollama serve`; `ollama pull gemma4:e4b`; `make test`.
- **Phase 1 — prove the model ✅** `make preflight` (G1–G8) + `make bench`; both models GO.
- **Phase 2 — offline dry-run ✅** `make demo` (precedent → env-shift → earned lesson → novel).
- **Phase 3 — RECORD** (the hard gate) — see RUNBOOK "Record the demo".
- **Phase 4 — submittable baseline** — Space deployed, writeup, social, tags. See
  `writeup/SUBMISSION-AUDIT.md`.
- **Phase 5 — upgrades** — ZeroGPU live inference (done), sim calibration (`tune-simulator`),
  filled virtual printer, badges.
- **Phase 6 — freeze & submit** — `make test`, cold-open as a judge, fix only breakage,
  `git tag submitted-build-small`.

## Pointers
- Day-by-day plan: `docs/plan/05-ENDGAME.md` · contingencies: `docs/plan/06-CONTINGENCY.md`.
- Open items / decisions: `docs/plan/ISSUES.md` · submission audit: `docs/writeup/SUBMISSION-AUDIT.md`.
- ZeroGPU deploy deep-dive: `docs/reference/DEPLOYMENT.md` (+ `docs/_archive/08-ZEROGPU-DEPLOY.md`).
