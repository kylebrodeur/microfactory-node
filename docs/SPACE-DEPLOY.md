# Space deploy & config (HF CLI) — build-small-hackathon/microfactory-lab

** (Space vars,
> dual-config, build strategy, troubleshooting) + the **"Deploy to the Space"**
> section in [`RUNBOOK.md`](RUNBOOK.md) (the exact `hf upload` commands). The Space
> is now 🟢 LIVE on ZeroGPU. This file is kept for the two project-specific bits
> those don't repeat: the **subtree-root rule** below, and the historical
> **dev-mode diagnosis** (what "nothing shows / default greet template" meant).

What must be true on the Space, and the exact values. Run the CLI locally (you have
`hf` + the skills); this captures the project-specific bits so nothing's guessed.

## ⚠ #1 rule: the Space ROOT is the `chief-engineer/` contents — not the lab repo root

The Space is `microfactory-lab`, but our app lives in the `chief-engineer/`
**subdirectory**. HF Spaces need `app.py` + `README.md` (frontmatter) + `requirements.txt`
at the **repo root**. The lab repo root still has the retired-swarm `README.md`
(`title: Microfactory Lab — V3 Swarm`, `app_file: app.py`) and that root `app.py` was
removed — so if the Space was populated from the lab root, the build fails / serves
the wrong thing. Push the **contents of `chief-engineer/`** to the Space root so the
Space card is `chief-engineer/README.md` ("The Chief Engineer", `app_file: app.py`).

```bash
hf auth login                       # once
# RECOMMENDED: hf upload routes binaries (assets/*.glb) through HF Xet automatically —
# plain `git push` REJECTS binaries unless LFS-tracked (see note below).
# NOTE: the `hf` CLI needs --exclude REPEATED per pattern (not one flag w/ many args):
hf upload build-small-hackathon/microfactory-lab ./chief-engineer . --repo-type space \
  --exclude "*.pyc" --exclude "*__pycache__*" --exclude ".venv/*" --exclude ".env" \
  --exclude "docs/*" --exclude "spike/*" \
  --exclude "data/lessons.jsonl" --exclude "data/policy.json" --exclude "data/references.jsonl" \
  --exclude "data/_*" --exclude "dist/*"
```

**⚠ Binaries (`assets/*.glb`) need Xet/LFS — not plain git.** `hf upload` (above)
handles this for you. If you instead `git push`, HF's pre-receive hook **rejects**
the `.glb` ("use Xet to store binary files") unless you LFS-track it first:
```bash
git clone https://huggingface.co/spaces/build-small-hackathon/microfactory-lab /tmp/ce-space
git archive HEAD:chief-engineer | tar -x -C /tmp/ce-space      # only git-tracked chief-engineer files
rm -rf /tmp/ce-space/docs /tmp/ce-space/spike                  # internal docs + spike stay off the public Space
cd /tmp/ce-space
git lfs install && git lfs track "*.glb"                       # ← REQUIRED so HF accepts the meshes
git add .gitattributes && git add -A
git commit -m "deploy chief-engineer" && git push
```
No external storage bucket is needed — HF Xet/LFS *is* the binary store.

**Why exclude `docs/`:** it's internal working material (strategy, TODO/KB notes,
contingency, projected-outcome, work orders) — not for a judged public Space, and the
app imports none of it. The README is the public face. After the video + write-up are
done, add back a curated public set (likely just the final Field Notes, optionally
`SIMULATION.md` + `reference/GEMMA-STEERING.md`).


Keep: `app.py`, `requirements.txt`, `README.md` (chief-engineer's), `core/ sim/ learn/
ingest/ scripts/`, `assets/*.glb` (incl. `benchy.glb` — the Space can't regenerate
these), `data/seed_lessons.jsonl` (the canonical 12). Exclude runtime state so the
ledger reads clean on camera (seeds only).

Verify after push: `https://…/microfactory-lab` shows the Chief Engineer UI, and the
files tab has `app.py` at root (not `chief-engineer/app.py`).

## Two Space variants

| | Fallback Space (baseline) | ZeroGPU Space (live, for recording) |
|---|---|---|
| `requirements.txt` | `-r requirements-zerogpu.txt` **commented** | **uncomment** that line |
| Hardware | CPU basic | **ZeroGPU** (Settings → Hardware) |
| Banner | 🟡 deterministic fallback (honest) | 🟢 live · google/gemma-4-E2B-it |

## ZeroGPU live config (the flip)

1. Uncomment `-r requirements-zerogpu.txt` in `requirements.txt` before upload.
2. Settings → Hardware → **ZeroGPU**.
3. Variables/secrets (web Settings, or the `huggingface_hub` API below):
   - variable `CHIEF_ENGINEER_BACKEND=zerogpu`
   - variable `CHIEF_ENGINEER_HF_MODEL=google/gemma-4-E2B-it`
   - secret `HF_TOKEN=<token>` **only if** the model is gated (also accept its
     license on the model's HF page with the same account)
   - optional: `CHIEF_ENGINEER_GPU_SECONDS=90`, `CHIEF_ENGINEER_MAX_NEW_TOKENS=512`

```python
# set vars/secrets without the web UI:
from huggingface_hub import HfApi
api = HfApi(); rid = "build-small-hackathon/microfactory-lab"
api.add_space_variable(rid, "CHIEF_ENGINEER_BACKEND", "zerogpu")
api.add_space_variable(rid, "CHIEF_ENGINEER_HF_MODEL", "google/gemma-4-E2B-it")
# api.add_space_secret(rid, "HF_TOKEN", "<token>")            # only if gated
# api.request_space_hardware(rid, "zero-a10g")                # or use the Settings UI
```

## Verify (then record)
- Build log green; banner reads 🟢 live (or honest 🟡 on the fallback Space).
- **Pre-warm:** one ANALYZE loads the model (banner → "(loaded)"); then record.
- Cold-open in incognito: STUDIO → pick part / Benchy → ANALYZE → Analysis renders.
- README links (video + social) present for submission.

## Notes / gotchas
- **The Space SDK MUST be `gradio`.** If the app is blank / you only see *container*
  logs, the Space was likely created as **Docker** or **Static** — then `sdk: gradio`
  in the README is ignored and nothing runs. Check Settings → SDK; if it's not Gradio,
  recreate the Space as a **Gradio SDK** space (or add a Dockerfile, but Gradio is simpler).
- **`hf upload` only ADDS/updates — it never deletes.** Files already on the Space that
  you later exclude (e.g. `spike/`, `docs/`) stay until you remove them:
  ```python
  from huggingface_hub import HfApi
  api = HfApi(); rid = "build-small-hackathon/microfactory-lab"
  for d in ("spike", "docs"):
      try: api.delete_folder(path_in_repo=d, repo_id=rid, repo_type="space")
      except Exception as e: print(d, e)
  ```
- `sdk_version` pinned `6.17.3`; if HF rejects it, set the nearest version HF lists.
- ZeroGPU has a per-user daily GPU-seconds quota + short queue — rehearse local, spend
  the Space on the real take. Fallback Space stays armed as Plan B.
- If the build log shows a wrong title/app_file, it's the #1 rule above (wrong root).

---

## KICKOFF PROMPT (paste into a local Claude Code session that has the HF skills)

```
You have the Hugging Face CLI + skills installed. Deploy and verify our Gradio Space.
Repo: microfactory-lab, branch claude/microfactory-gradio-hackathon-9e81fh.
Space: build-small-hackathon/microfactory-lab (currently EMPTY).

CONTEXT (read docs/SPACE-DEPLOY.md first):
- Our app lives in the chief-engineer/ SUBDIRECTORY. HF needs app.py + README.md
  (frontmatter) + requirements.txt at the SPACE ROOT. So the Space root must be the
  CONTENTS of chief-engineer/, NOT the lab repo root (the lab root has a retired-swarm
  README + a removed app.py — that would build-fail).
- Never upload .env or secrets. Keep runtime state out (clean ledger = seeds only).

PHASE A — deploy the fallback build and confirm it's green:
1. From the repo root, push ONLY git-tracked chief-engineer files to the Space root,
   and DROP the internal docs/ tree. PREFER `hf upload` — it routes the binary meshes
   (assets/*.glb) through HF Xet automatically; plain `git push` rejects binaries
   unless you `git lfs track "*.glb"` first. Either:
     hf upload build-small-hackathon/microfactory-lab ./chief-engineer . --repo-type space \
       --exclude "*.pyc" --exclude "*__pycache__*" --exclude ".venv/*" --exclude ".env" \
       --exclude "docs/*" --exclude "spike/*" --exclude "data/lessons.jsonl" --exclude "data/policy.json" \
       --exclude "data/references.jsonl" --exclude "data/_*" --exclude "dist/*"
   …or the git method (clone Space → `git archive HEAD:chief-engineer | tar -x` →
     `rm -rf docs spike` → `git lfs install && git lfs track "*.glb"` → add/commit/push).
2. Verify on the Space: files tab shows app.py at ROOT, NO docs/ folder; card title = "The Chief Engineer"
   (not "Microfactory Lab — V3 Swarm"); requirements.txt has the `-r requirements-zerogpu.txt`
   line COMMENTED; hardware = CPU basic.
3. Watch the container/build logs. Expect a green build and the app to serve, with the
   banner reading 🟡 "offline fallback" (Ollama isn't on the Space — correct + honest).
   Open it: STUDIO → pick a part → ANALYZE → Analysis renders on the fallback path.
   If the build is RED, capture the exact error from the container logs and report it.

PHASE B — flip to ZeroGPU live (for recording), only after A is green:
4. On the Space, uncomment `# -r requirements-zerogpu.txt` in requirements.txt.
5. Settings → Hardware → ZeroGPU.
6. Settings → Variables: CHIEF_ENGINEER_BACKEND=zerogpu ;
   CHIEF_ENGINEER_HF_MODEL=google/gemma-4-E2B-it ; (optional CHIEF_ENGINEER_GPU_SECONDS=90).
   If google/gemma-4-E2B-it is GATED: accept its license on the model page with this
   account AND add HF_TOKEN as a Space SECRET (never a variable, never in git).
7. Redeploy. Verify the banner reads 🟢 "live · google/gemma-4-E2B-it (transformers on
   ZeroGPU)". Pre-warm: one ANALYZE loads the model (banner → "(loaded)"); then it's fast.
   If the model errors, the app still falls back to deterministic (no crash) — report the log.

REPORT BACK: build status (green/red + any error), the live banner text, the resolved
model param count (for the Tiny Titan question), and whether the model was gated.
Do NOT commit secrets. Do NOT push a PR.
```


---

## TROUBLESHOOTING KICKOFF PROMPT — "old/template app still showing"

Paste into a local Claude Code session with the HF CLI + huggingface_hub + HF skills,
authenticated for the build-small-hackathon org.

```
Goal: make OUR Gradio app ("The Chief Engineer") actually run on the Space
build-small-hackathon/microfactory-lab. It currently shows the default Gradio
greet template (name -> output) even after an hf upload. Read docs/SPACE-DEPLOY.md.

Repo: microfactory-lab, branch claude/microfactory-gradio-hackathon-9e81fh; our app is
the CONTENTS of chief-engineer/ and must sit at the SPACE ROOT.

Top hypothesis: DEV MODE is ON, so the Space runs a dev container (openvscode-server)
and our app.py was never (re)started — the build log shows a VS Code dev image, not
`pip install -r requirements.txt` + our app. Secondary: files nested under a
chief-engineer/ subfolder, or just needs a restart/factory rebuild.

Work through these, reporting findings at each step:

1) Inspect the file tree:
     from huggingface_hub import HfApi
     api = HfApi(); rid = "build-small-hackathon/microfactory-lab"
     print("\n".join(sorted(api.list_repo_files(rid, repo_type="space"))))
   CONFIRM app.py, README.md, requirements.txt are at ROOT (not under chief-engineer/).
   If nested, re-upload to root:
     hf upload build-small-hackathon/microfactory-lab ./chief-engineer . --repo-type space \
       --exclude "*.pyc" --exclude "*__pycache__*" --exclude ".venv/*" --exclude ".env" \
       --exclude "docs/*" --exclude "spike/*" --exclude "data/lessons.jsonl" \
       --exclude "data/policy.json" --exclude "data/references.jsonl" --exclude "data/_*" --exclude "dist/*"

2) Confirm the ROOT README is ours (title "The Chief Engineer", sdk: gradio, app_file: app.py),
   not the HF template. (Our upload overwrites by filename.)

3) DEV MODE: if it's enabled, DISABLE it (Settings -> Dev mode -> Disable). With dev mode on,
   HF will NOT auto-run our app.py. Then rebuild/restart:
     api.restart_space(rid)        # or "Factory rebuild" in Settings if a cached layer persists

4) Remove internal folders that should not be public:
     for d in ("spike", "docs"):
         try: api.delete_folder(path_in_repo=d, repo_id=rid, repo_type="space")
         except Exception as e: print(d, e)

5) Watch the BUILD logs (not the dev/container logs). You should see pip install OUR deps
   (gradio==6.17.3, trimesh, shapely, ollama, pydantic) and the app start. Open the App tab:
   expect the STUDIO/ANALYSIS "Chief Engineer" UI with a yellow "offline fallback" banner
   (Ollama isn't on the Space — correct + honest). If the build errors, capture the exact text.

6) Once OUR app renders on fallback, enable ZeroGPU live inference:
   - Uncomment the line "# -r requirements-zerogpu.txt" in requirements.txt (edit + re-upload).
   - Settings -> Hardware -> ZeroGPU (Kyle already selected it).
   - api.add_space_variable(rid, "CHIEF_ENGINEER_BACKEND", "zerogpu")
     api.add_space_variable(rid, "CHIEF_ENGINEER_HF_MODEL", "google/gemma-4-E2B-it")
   - If google/gemma-4-E2B-it is GATED: accept its license on the model page with this account
     AND api.add_space_secret(rid, "HF_TOKEN", "<token>")  (secret, never a variable, never in git).
   - Restart; confirm the banner reads green "live"; pre-warm one ANALYZE.

REPORT: the root file tree, dev-mode state, build-log result, the banner text, the resolved
model param count (for the Tiny Titan question), and whether the model was gated.
Do NOT commit secrets; do NOT push a PR.
```
