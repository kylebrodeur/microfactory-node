# Modal work order (the Modal-bonus track — run locally)

Scale up ingestion on **Modal**: pull big source datasets (slicer g-code corpora,
3D-ADAM defect sets, etc.), parse them, and land the results in the same three
lanes the app already consumes. The scaffold + output contract are done in
`ingest/modal_app.py`; this is the brief for wiring your MCP-hackathon parser in.
Pairs with `INGESTION-GUIDE.md` (the lanes) and `INGESTION-WORKORDER.md` (local).

## Why this is the bonus, and why it's safe
- **Modal bonus:** real Modal compute doing the heavy ingestion = the qualifying use.
- **Isolated:** `modal` is import-guarded, NOT in the Space `requirements.txt`, and
  nothing in `app.py` imports `modal_app`. It can't break the demo or the deploy.

## The contract (already coded — just emit these shapes)
`ingest/modal_app.py` writes three artifact files in the existing lane schemas:
- **A → `data/references.jsonl`** — `{"material","param","value","source"}` (hard params).
- **B → `data/_modal_candidate_lessons.jsonl`** — env-keyed lessons (`source="ingested"`),
  written to a **REVIEW file**, never straight to the ledger (honesty gate).
- **C → `sim/calibration/observations.modal.jsonl`** — settings + env + outcome (+ quality);
  feeds `tune-simulator` to calibrate `sim/outcome.py` to real data.
Enums must match `core/models.py` (`MATERIALS`/`GEOMETRY_TYPES`/`OUTCOMES`).

## Where your code goes
The only thing missing is per-dataset **mapping**: in `modal_app.py`'s `MAPPERS`
registry, each dataset key points to `(hf_dataset_id, mapper_fn)`, and the mapper
turns one raw row into `("A"|"B"|"C", record)` tuples. Plug your MCP parser into
`_map_3d_adam` / `_map_gcode` (or add new mappers). The heavy `distill()` function,
the Modal fan-out, and the artifact-writing local entrypoint are already wired.

## Steps
1. `uv pip install modal datasets` (local-only; not a Space dep). `modal token set`.
2. Fill in `MAPPERS`: real dataset ids + your row→record mappers. Honesty rule —
   Lane B only true/directional lessons; Lane C only rows that carry the settings.
3. `modal run ingest/modal_app.py --dataset 3d-adam --limit 2000` (then `--dataset gcode`,
   or no flag for all). It fans out to Modal and writes the three artifacts locally.
4. **REVIEW `data/_modal_candidate_lessons.jsonl`**, then fold the good ones into the
   ledger (via `ingest_candidate_lessons` / the local ingestion work order).
5. Calibrate: `uv run python -m sim.calibrate --data sim/calibration/observations.modal.jsonl`.
6. `make test` → `make run` to confirm the references/lessons feed a recommendation.
7. Commit on the feature branch with row counts. Don't push a PR.

## Reference patterns (proven — from the `spanish-language-tutor` Modal pipeline)

A sibling project runs a real Modal ingestion pipeline; these idioms transfer 1:1
and are worth adopting as the datasets get big. Our `ingest/modal_app.py` already
matches the core shape (`modal.App`, `Image.pip_install`, `@app.function(timeout=…)`,
`@app.local_entrypoint` + `.remote()`); the additions below are the upgrades it shows.

- **Persist with a `modal.Volume`** so a big download/parse happens *once* and is
  cached across runs (vs. re-pulling each run + returning everything over the wire):
  ```python
  vol = modal.Volume.from_name("chief-engineer-ingest-data", create_if_missing=True)
  @app.function(image=image, volumes={"/data": vol}, timeout=7200)  # gpu="T4" if needed
  def distill(...):
      ...                       # write artifacts under /data
      vol.commit()              # persist before returning
  ```
  Make it **idempotent/resumable** like the reference does (`if out_path.exists(): skip`)
  so a re-run resumes instead of redoing the corpus.
- **Secrets** for gated HF datasets / any LLM-distill step:
  `secrets=[modal.Secret.from_name("chief-engineer-secrets")]` (HF_TOKEN, etc.) — never
  inline a token. (`modal secret create chief-engineer-secrets HF_TOKEN=…`.)
- **Share our enums into the image** if a mapper needs them, instead of re-typing:
  `image.add_local_file("core/models.py", "/root/core/models.py").env({"PYTHONPATH": "/root"})`
  (the reference bundles agent code this way with `add_local_dir(..., copy=True)`).
- **GPU only where it earns it** — the reference uses `gpu="T4"` for Whisper transcription.
  Our parsing is CPU; reserve GPU for the named *frontier* (fine-tune on the ledger).
- **FRONTIER — live Space↔Modal (named, not built):** the tutor's HF Space calls a
  *deployed* Modal function at runtime via `modal.Function.from_name("app","fn").remote(args)`
  (with `modal deploy`). We deliberately **don't** do this — ingestion stays offline and the
  artifacts drop into the repo, which keeps the demo/deploy isolated and honest. Worth naming
  in the writeup as the obvious next step (heavy retrieval/inference offloaded to Modal),
  not a thing in the window.

## Acceptance
- [x] Modal app built: 24 documentation sources + 2 HF dataset mappers registered
- [x] All parsers tested locally (Prusa INI, Klipper CFG, Marlin H, web docs, product specs)
- [x] Reference patterns applied: Volume caching, Secrets, enum sharing, CPU-only, no live Space↔Modal
- [x] `make test` green — nothing in the demo path imports modal
- [ ] A real Modal run produced ≥1 lane's worth of artifacts from a real dataset (needs `modal token set`)
- [ ] Lane-B lessons reviewed before entering the ledger
- [ ] Lane-C calibration ran
- [ ] Writeup can honestly say "heavy ingestion runs on Modal" (the bonus claim)

---

## KICKOFF PROMPT (paste into a fresh local Claude Code session)

```
You're in the chief-engineer/ project on branch
claude/microfactory-gradio-hackathon-9e81fh. Task: wire up Modal-based ingestion
for the Modal bonus. Do NOT touch app.py, core/, or the UI.

1. Read docs/MODAL-WORKORDER.md (incl. the "Reference patterns" section —
   idioms vetted against a sibling production Modal pipeline, safe to follow),
   docs/INGESTION-GUIDE.md (the three lanes), core/models.py
   (MATERIALS/GEOMETRY_TYPES/OUTCOMES), and ingest/modal_app.py (the scaffold +
   output contract — the structure is done, mapping is the gap).
2. My Modal/MCP-hackathon ingestion code is at: <PATH — I'll fill in>. My source
   datasets are: <HF ids / GH repos — I'll fill in>. Tell me how each maps to lanes
   A/B/C, then fill the MAPPERS registry in modal_app.py with real dataset ids and
   row→record mappers (reuse my parser where it fits).
3. Apply the Reference patterns AS THE DATASET REQUIRES (don't add them blindly):
   - large download/parse, or pulling the same corpus repeatedly → add a
     `modal.Volume` (`create_if_missing=True`) + `vol.commit()`, and make it
     resumable (skip artifacts that already exist). Otherwise the over-the-wire
     return in the current scaffold is fine.
   - gated HF dataset or any LLM-distill step → `modal.Secret.from_name(
     "chief-engineer-secrets")` (e.g. HF_TOKEN); never inline a token.
   - a mapper needs the enums → `image.add_local_file("core/models.py",
     "/root/core/models.py").env({"PYTHONPATH":"/root"})` instead of re-typing them.
   - keep GPU off unless a step earns it. Do NOT build live Space↔Modal calling —
     ingestion stays offline/artifact-based on purpose (it's a named frontier only).
4. HONESTY GATE: Lane B emits to data/_modal_candidate_lessons.jsonl for my review —
   only true, directional lessons. Lane C only when the row has the actual settings.
5. `uv pip install modal datasets`, `modal token set`, then
   `modal run ingest/modal_app.py --dataset <d> --limit 1000`. Report row counts.
6. Show me the candidate lessons before anything enters the ledger. Run
   `uv run python -m sim.calibrate --data sim/calibration/observations.modal.jsonl`
   if Lane C produced rows. Keep `make test` green.
7. Update docs/KNOWLEDGE-SOURCES.md, commit on the feature branch with counts. No PR.
```
