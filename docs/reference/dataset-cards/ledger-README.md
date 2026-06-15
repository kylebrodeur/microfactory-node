---
license: mit
language:
  - en
tags:
  - 3d-printing
  - additive-manufacturing
  - llm
  - retrieval
  - build-small-hackathon
pretty_name: "Microfactory Node: Lesson Ledger"
size_categories:
  - n<1K
---

# Microfactory Node: 3D Printer (Lesson Ledger)

The compounding memory of **Microfactory Node: 3D Printer**, a small local Gemma that learns 3D
printing job by job. Each row is one durable lesson keyed to the conditions it was learned in.
The node retrieves from this ledger before every print, so job N+1 starts smarter than job N.
This is the knowledge that usually lives in one maker's head and dies with the shop. Here it
persists, and anyone can read it.

Project: [Live](https://node.microfactory.space) ·
[Code](https://github.com/kylebrodeur/microfactory-node).

## Schema (one JSON object per line)

```json
{"job_id": "seed-004", "material": "PLA", "geometry_type": "overhang",
 "env_temp": 28.0, "env_humidity": 50.0, "outcome": "failed_sag",
 "lesson": "PLA overhang sagged at 28C with the fan low; raise cooling, drop nozzle ~10C.",
 "source": "seed", "timestamp": "2026-05-20T09:00:00Z"}
```

| Field | Meaning |
|---|---|
| `material` | PLA, PETG, ABS, TPU |
| `geometry_type` | overhang, bridge, stringing, adhesion, vase (the failure-mode class) |
| `env_temp` / `env_humidity` | room conditions the lesson was learned in |
| `outcome` | success, failed_sag, failed_stringing |
| `lesson` | one durable, directional sentence (the transferable craft) |
| `source` | `seed` (curated start), `ingested` (from real configs/prints), `earned` (a real reported outcome), `sim` (the deterministic world) |

## How the knowledge is sourced

Lessons are grounded, never invented. Seed lessons are hand-curated starters. Ingested lessons
come from real slicer/firmware profiles and real print history. Earned and simulated lessons come
from outcomes reported outside the model: the model proposes, a deterministic world or a human
reports what happened, and only then is a lesson written. The model never grades its own work.

## Honest limits

Small and deliberately so. The simulated outcomes are a physics-lite stand-in for a printer, used
to run the closed loop on camera; they are labeled as such. Treat the lessons as a maker's
notebook: directionally true, condition-keyed, and meant to be checked against your own machine.
