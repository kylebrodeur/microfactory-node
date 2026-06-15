# How we used Modal (the Modal bonus, in one page)

Modal did the heavy lifting that does not belong on a laptop or a small Space: pulling and parsing
big source datasets, and fine-tuning. The live demo never calls Modal. `modal` is import-guarded,
it is not in the Space `requirements.txt`, and nothing in `app.py` imports it, so none of this can
break the demo or the deploy.

## 1. Knowledge ingestion at scale (`ingest/modal_app.py`)

The source corpora (slicer/firmware configs, the 3DTime model set, an FDM failure-print recorder)
are too big to fetch and parse locally. Modal does the download and parse and writes back the three
knowledge lanes the node consumes: reference facts, candidate lessons, and calibration observations.

- `modal.App("chief-engineer-ingest")`, a persistent `modal.Volume` cache (download/parse once),
  `modal.Secret` for the HF token, and the project enums shared into the image. CPU only: parsing
  is not GPU work.
- Output: 1,304 reference facts, and 178 cleaned calibration observations from real labeled failure
  prints. Those observations are what let us check the simulator honestly (32.6% on clean data, a
  structural gap we documented instead of papering over).
- Cost: roughly $0.05 across eight short runs. The Volume cache made re-runs nearly free.

Patterns came from a sibling production pipeline (the spanish-language-tutor Modal app): Volume
caching, Secret-based tokens, sharing local modules into the image. See
`docs/_archive/MODAL-WORKORDER.md` and `docs/writeup/INGESTION-REPORT.md` for the full record.

## 2. Fine-tuning (`learn/finetune/train_modal.py`)

The named "Well-Tuned" frontier, realized in parallel: a LoRA on a small Gemma, on an A10G, that
distills the node's judgment (settings + risk advice over a grid of conditions) into the weights.
It does not replace the live retrieval path. We claim the badge only if a held-out eval earns it.
Budget headroom is ample (about $100 plus credits); a run is well under $2.

## The bonus claim, stated honestly

Heavy ingestion and the fine-tune both run on real Modal compute. The qualifying use is genuine:
Modal produced the reference + calibration data the node and its honesty story depend on, and it
trains the optional Well-Tuned adapter. None of it is in the demo's hot path.
