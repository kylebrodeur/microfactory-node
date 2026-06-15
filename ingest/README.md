# Knowledge Ingestion

Turns the sources in `../docs/KNOWLEDGE-SOURCES.md` into Chief Engineer knowledge.
Two kinds, matching how each source actually carries information:

| Output | From | Goes to | Used as |
|--------|------|---------|---------|
| **Reference facts** | Prusa `.ini`, Klipper `.cfg`, Marlin `.h` (data only) | `data/references.jsonl` | injected into the prompt as a *Material Reference* block |
| **Candidate lessons** | research distilled into env-keyed JSONL rows | the ledger (`source="ingested"`) | retrieved exactly like seed/earned lessons |

## Local distiller (deterministic, runs offline)

```bash
uv run python -m ingest.run          # uses ingest/samples/
uv run python -m ingest.run --dir /path/to/your/marlin_klipper_prusa_files
```

Replace `ingest/samples/*` with your real configs and a `*lessons*.jsonl` of
research-distilled rows. The sample files are illustrative and clearly marked.

> **License-safe:** we ingest profile *data* (INI/cfg/#define values). We never
> import or link OrcaSlicer/PrusaSlicer code (AGPL-3.0).

## Heavy datasets + fine-tune → Modal (`modal_app.py`)

`ablam/gcode` (>6GB) and `3DTimeDataset/3DTime` are too big for the Space; they
run on Modal. `modal_app.py` is a **stub to be replaced by Kyle's MCP-hackathon
ingestion code** (which already parses training data for multi-agent use).
Off the critical demo path; this is where the Modal bonus + the frontier
fine-tune live.

```bash
uv pip install modal datasets      # not in the Space requirements
modal token set
modal run ingest/modal_app.py::sample_gcode
```
