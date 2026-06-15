# 08 — Publish the two activity-trace datasets (local-agent prompt)

Two build-activity logs share one schema and should ship as **two separate** open
trace datasets (Sharing is Caring). They're already linked from the Space README, so
publish them **before** the next `make deploy` so the links resolve.

| Source file (in repo) | Dataset repo | What it is |
|---|---|---|
| `docs/reference/ACTIVITY.jsonl` | `kylebrodeur/chief-engineer-build-activity` | The app/build activity log (restructures, fixes, deploys). |
| `learn/finetune/activity.jsonl` | `kylebrodeur/chief-engineer-finetune-activity` | The fine-tune pipeline activity log (train/eval/quantize/publish). |

**Schema (both):** one JSON object per line — `timestamp` (ISO-8601), `action` (short tag),
`event` (short tag), `details` (free text). Renders as a clean 4-column table in the HF viewer.

> Format note: `learn/finetune/activity.jsonl` had one row with two objects joined by `}{`
> (invalid JSONL); fixed in-repo (now 39 valid rows). Re-validate before upload:
> `python -c "import json,sys;[json.loads(l) for l in open(sys.argv[1]) if l.strip()]" <file>`.

## Paste-to-the-local-agent prompt

> Publish two open HF **dataset** repos from this repo (branch
> `claude/microfactory-gradio-hackathon-9e81fh`, dir `microfactory-lab/chief-engineer/`).
> Needs an HF write token. For each: create the repo if missing (never recreate), upload the
> JSONL, and upload a `README.md` dataset card. Then confirm both render a table in the viewer.
>
> ```bash
> # 1) validate both JSONL files parse
> for f in docs/reference/ACTIVITY.jsonl learn/finetune/activity.jsonl; do
>   python -c "import json,sys; n=sum(1 for l in open(sys.argv[1]) if l.strip() and json.loads(l)); print(sys.argv[1], n, 'rows OK')" "$f"
> done
>
> # 2) build-activity dataset (card already written in-repo)
> hf repo info kylebrodeur/chief-engineer-build-activity --repo-type dataset \
>   || hf repo create kylebrodeur/chief-engineer-build-activity --repo-type dataset -y
> hf upload kylebrodeur/chief-engineer-build-activity docs/reference/ACTIVITY.jsonl activity.jsonl --repo-type dataset
> hf upload kylebrodeur/chief-engineer-build-activity docs/reference/dataset-cards/build-activity-README.md README.md --repo-type dataset
>
> # 3) finetune-activity dataset (card already written in-repo)
> hf repo info kylebrodeur/chief-engineer-finetune-activity --repo-type dataset \
>   || hf repo create kylebrodeur/chief-engineer-finetune-activity --repo-type dataset -y
> hf upload kylebrodeur/chief-engineer-finetune-activity learn/finetune/activity.jsonl activity.jsonl --repo-type dataset
> hf upload kylebrodeur/chief-engineer-finetune-activity docs/reference/dataset-cards/finetune-activity-README.md README.md --repo-type dataset
> ```
>
> Verify both dataset pages render a 4-column table (`timestamp`, `action`, `event`, `details`).
> The README already links both — no README edit needed; just redeploy the Space after.

The dataset cards are committed in-repo at
`docs/reference/dataset-cards/build-activity-README.md` and
`docs/reference/dataset-cards/finetune-activity-README.md` (same pattern as the ledger /
deliberation / field-log cards) — upload them as each repo's `README.md`, as above.
