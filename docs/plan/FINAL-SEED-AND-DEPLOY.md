# Final seed & deploy — local runbook

Run this once, locally, on a machine with an **HF write token** (member of
`build-small-hackathon`) and `ollama serve` running. It seeds the three open
datasets, sets the one secret that turns on live logging, deploys the Space, and
verifies everything live. Self-contained; lifts the exact steps from RUNBOOK §3.

**The whole thing in one line:** seed 3 datasets → set 1 Space secret → deploy → verify.

---

## 0 · Prerequisites (90 seconds)

```bash
cd chief-engineer
hf auth login            # or: export HF_TOKEN=hf_...   (needs WRITE + build-small-hackathon member)
hf auth whoami           # confirm the token + org
ollama serve &           # so O'Brien's reasoning is REAL, not the [fallback] text
make test                # all core tests pass → safe to ship
```

Repos this touches (all should already exist — **check first, never recreate**):

| Artifact | Repo | Source |
|---|---|---|
| Lesson ledger | `kylebrodeur/chief-engineer-ledger` (dataset) | `make trace` |
| Field log (live) | `build-small-hackathon/chief-engineer-field-log` (dataset) | `core/field_log.py` |
| Deliberation (static + live) | `kylebrodeur/chief-engineer-deliberation` (dataset) | `make deliberation` + `core/deliberation_log.py` |
| The Space | `build-small-hackathon/microfactory-lab` (space) | `make deploy` |

```bash
# verify they exist; create ONLY a missing one (never recreate an existing repo)
hf datasets info kylebrodeur/chief-engineer-ledger
hf datasets info build-small-hackathon/chief-engineer-field-log
hf datasets info kylebrodeur/chief-engineer-deliberation
# if a dataset repo is missing, the first hf upload will create it;
# add --private if you want it private, otherwise it defaults to public.
```

---

## 1 · Seed the datasets (Sharing is Caring × 3)

### 1a. Ledger
```bash
make trace                                   # → dist/ (chief_engineer_ledger.jsonl + card)
cp docs/reference/dataset-cards/ledger-README.md dist/README.md   # ship the polished card as README
hf upload kylebrodeur/chief-engineer-ledger dist/ . --repo-type dataset
```

### 1b. Deliberation (run with Ollama up for real O'Brien reasoning)
```bash
make deliberation                            # → dist/deliberation/ (deliberations.jsonl + card)
# spot-check it captured real reasoning (NOT "[fallback]"):
head -1 dist/deliberation/deliberations.jsonl
hf upload kylebrodeur/chief-engineer-deliberation dist/deliberation . --repo-type dataset
```

### 1c. Field log card
The `CommitScheduler` only pushes `*.jsonl`, so the field-log card needs a manual upload:
```bash
hf upload build-small-hackathon/chief-engineer-field-log \
  docs/reference/dataset-cards/field-log-README.md README.md --repo-type dataset
```

> After 1a–1c, open each dataset's page and confirm the viewer renders a clean table.

---

## 2 · Turn on live logging (one secret powers BOTH live logs)

The field log **and** the deliberation log are gated on the **same** `HF_TOKEN`
Space secret. Set it once:

- Space → **Settings → Variables and secrets → New secret**
- Name `HF_TOKEN`, value = a **write** token that's a member of `build-small-hackathon`
- Save, then **reboot** the Space (Settings → Factory reboot)

Without this secret both live logs silently no-op (local/offline is unaffected).

---

## 3 · Deploy the Space

```bash
make deploy-check        # offline GO/NO-GO gates (D1–D10); pushes nothing
make deploy              # gates → upload_folder to the Space + factory reboot
```

`make deploy` uploads everything except `docs/`, `spike/`, caches, secrets, and
runtime files (so `learn/`, `assets/`, `data/*.jsonl` go too). If Space variables
were never set:
```bash
hf spaces variables add build-small-hackathon/microfactory-lab \
  -e GRADIO_SSR_MODE=False -e CHIEF_ENGINEER_BACKEND=zerogpu \
  -e CHIEF_ENGINEER_HF_MODEL=google/gemma-4-E4B-it
```

---

## 4 · Verify live (5 minutes)

1. **Smoke-test the UI:** LOAD a part, then **SLICE** shows O'Brien reasoning (NOT "Error");
   La Forge second opinion + the dispute-gate work; LAYER scrubber slides; Print loop runs;
   Review shows ledger + verdict + ↺ RESET; wide layout, no empty right gutter.
2. **Drive one full run** on the Space: LOAD → SLICE → Second Opinion → (override if
   disputed) → PRINT.
3. **Wait ≤5 min** (scheduler flush), then confirm new rows landed:
   - field log → `interactions.jsonl` in `build-small-hackathon/chief-engineer-field-log`
   - deliberation → `deliberations.jsonl` in `kylebrodeur/chief-engineer-deliberation`
     (one row per turn: propose / veto / second_opinion / override / simulate / grade / verdict)
4. **Link all three** datasets in the Space `README.md` (Sharing-is-Caring evidence).

---

## Done when
- [ ] All three datasets seeded + their cards render as the repo README
- [ ] `HF_TOKEN` set as a Space secret + Space rebooted
- [ ] `make deploy` green and the live UI smoke-tested
- [ ] One Space run produced fresh rows in BOTH live datasets
- [ ] All three datasets linked in the Space README

Rollback: redeploy is idempotent (`upload_folder` only adds/updates, never deletes);
if a run looks wrong, fix locally and `make deploy` again.
