---
license: mit
language:
  - en
tags:
  - 3d-printing
  - additive-manufacturing
  - llm
  - interaction-logs
  - build-small-hackathon
pretty_name: "Microfactory Node: Field Log"
size_categories:
  - n<10K
---

# Microfactory Node: 3D Printer (Field Log)

Every interaction on the live [node](https://node.microfactory.space)
appends one row here: every build, second opinion, simulated print, iteration run, and recorded
outcome. It is the node's field notebook, written as people use it, so the craft keeps
accumulating past a single maker's bench. Logging is gated on a write token and silently does
nothing without it.

## What is and isn't here

Job configuration and outcomes only. No personal data. No uploaded mesh files (only the geometry
class the engineer inferred). Rows are **candidates**, never auto-promoted into the curated
[lesson ledger](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger): a human
reviews before anything earns "lesson" status. The same honesty rule the product runs on.

## Schema (one flat row per interaction)

A single rectangular table, one `kind` per row, so it reads cleanly in the dataset viewer.

| Column | Meaning |
|---|---|
| `ts`, `kind` | timestamp, and one of: build, second_opinion, simulate, print_run, print_override, record |
| `material`, `geometry`, `env_temp`, `env_humidity`, `bed_position`, `printer` | the job |
| `nozzle_temp`, `bed_temp`, `fan_pct`, `retraction_mm`, `first_layer_fan_pct` | proposed settings |
| `backend`, `used_fallback` | which model path served the build (live Gemma or deterministic) |
| `risks`, `risk_count` | the failure regions O'Brien flagged |
| `inspector_stance`, `inspector_headline`, `agreement` | La Forge's verdict (and, on a graded print, whether the prediction held) |
| `outcome`, `quality` | the simulated/real result |
| `iterations`, `q_start`, `q_end`, `first_clean` | the Print-loop run summary |

**Kinds in detail:**
- `build` — what O'Brien proposed for a fresh job.
- `second_opinion` — La Forge's critique and verdict.
- `print_override` — operator changed O'Brien's settings before printing.
- `print_run` — the simulated/real print outcome, including iteration curve.
- `simulate` / `record` — one-off simulator runs or manual outcome records.

Fields not relevant to a row's `kind` are null. Two named agents produce the judgment: Chief
Engineer O'Brien proposes, La Forge inspects.
