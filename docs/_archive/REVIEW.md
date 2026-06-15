# Review packet: writeup, social, metadata (2026-06-13)

Everything drafted/revised in this pass, in one place, so you can review fast. All copy is in
the Practical Polymath voice (`docs/reference/VOICE.md`): no em or en dashes, varied rhythm,
information centered, grounded metaphors. Public naming leads with **Microfactory Node: 3D
Printer**, with **Chief Engineer O'Brien** (proposes) and **La Forge** (inspects) as the agents.

## What I made or revised

| Item | File | Notes |
|---|---|---|
| Submission writeup | `docs/writeup/01-SUBMISSION.md` | Full rewrite. New lead, grandfather mapped to both agents, "connect the makers / humans front and center," light Microfactory-economy touch, honest current calibration (32.6%). 1,444 words, 0 dashes. |
| Social post | `docs/writeup/04-SOCIAL-POST.md` | 3 variants rewritten (A = story, recommended). New name/agents, real Space slug, 0 dashes. |
| Field Notes | `docs/writeup/06-FIELD-NOTES.md` | 9 lessons, voice pass, agents named, calibration corrected to the cleaned 32.6%/178 story. 0 dashes. |
| Voice guide | `docs/reference/VOICE.md` | Your Practical Polymath guide, now canonical in-repo for every future agent. |
| Space card | `README.md` | All 23 em-dashes removed; hero + value-prop + screenshot placeholders added; ingested count fixed (14). |
| Ledger dataset card | `docs/reference/dataset-cards/ledger-README.md` | Upload as the README of `kylebrodeur/chief-engineer-ledger`. |
| Field-log dataset card | `docs/reference/dataset-cards/field-log-README.md` | Upload as the README of `build-small-hackathon/chief-engineer-field-log`. |
| Screenshot specs | `assets/screenshots/README.md` | What to capture for each placeholder. |
| Modal usage doc | `docs/reference/MODAL-USAGE.md` | One-page citable record of how we used Modal (ingestion + fine-tune). Now also credited in the submission. |
| Fine-tune track | `learn/finetune/` (+ `data/finetune/sft.*.jsonl`) | Well-Tuned frontier: dataset generated (400/80), Modal LoRA trainer + honest eval + a kickoff prompt for a local agent. Parallel + optional; never touches the live Space. |

(Earlier this session: RUNBOOK rewritten clean, history moved to `docs/reference/RUNBOOK-FINDINGS.md`,
JUDGE-GUIDE folded into RUNBOOK §2, `02-VIDEO.md` reframed as the recording companion with the agents named.)

## Decisions I made (please confirm)

1. **Naming:** public copy leads with "Microfactory Node: 3D Printer"; "the Chief Engineer" survives
   as O'Brien's role. The README H1 and HF Space title match. Confirm you're happy with that split.
2. **Calibration number:** I used the cleaned **32.6% on 178 prints** (with the structural-gap
   framing) everywhere, and retired the old pre-clean 34.2%/260 figure. This is the more honest
   and current number.
3. **README first impression:** added a one-line value prop under the tagline, a hero image slot,
   and a "quick facts" chip line, above the grandfather story. The story still opens the body.

## Things to check / your call

- [ ] **Voice gut-check on `01-SUBMISSION.md`.** It's the centerpiece and the first thing I wrote
  to your guide. If the tone is off anywhere, flag it and I'll fix it once, then re-align the rest.
- [ ] **Social Variant B quote must be real.** It currently uses a representative O'Brien line.
  Replace with an actual (lightly trimmed) output from the final recording before posting.
- [ ] **Pick a social variant** (A recommended) and tell me, or post it and send the URL.
- [ ] **Screenshots.** Placeholders point at `assets/screenshots/{hero-build,print-loop,...}.png`.
  Until captured they show broken-image icons on the card, so grab them before deploying for
  submission. Specs in `assets/screenshots/README.md`.
- [ ] **Tiny Titan tag.** Still unresolved (does the 32B cap count total or effective params?).
  Ask in the org before adding `tiny-titan` to the README frontmatter.
- [ ] **Microfactory-economy line.** I kept it light ("the rest is on the roadmap, not in this
  demo"). Tell me if you want more or less of that forward-looking framing.

## Action items only you can do

- [ ] Publish the social post; add its URL to `README.md` Links (placeholder is in).
- [ ] Add the demo video URL to `README.md` Links (placeholder is in).
- [ ] Upload the dataset cards as each dataset's `README.md` (the `CommitScheduler` only pushes
  `*.jsonl`, so the field-log + deliberation cards need a manual upload; the deliberation card
  ships in `dist/deliberation/` from `make deliberation`).
- [ ] Seed the deliberation dataset: `ollama serve` + `make deliberation` →
  `hf upload kylebrodeur/chief-engineer-deliberation dist/deliberation . --repo-type dataset`.
- [ ] Set `HF_TOKEN` as a **Space secret** — the one token makes BOTH the field log and the
  live deliberation log go live (see RUNBOOK §3).
- [ ] Capture the screenshots.
- [ ] Set the GH repo description + topics (draft below).
- [ ] Publish the Field Notes on the org blog.

## GH repo metadata (draft, apply in repo Settings)

**Description:**
> Microfactory Node: 3D Printer. A small local Gemma that learns 3D printing job by job and
> predicts where a print will fail before it runs. Built for the HF Build Small hackathon.

**Topics:** `3d-printing` `local-llm` `gemma` `ollama` `huggingface` `gradio` `retrieval`
`build-small-hackathon` `backyard-ai` `additive-manufacturing`

(Note: the *root* `microfactory-lab` README may still describe the older swarm project. If GH
presentation matters to judges, point the root README at the `chief-engineer/` node, or note that
this hackathon entry lives in `chief-engineer/`.)

## Notes / things to think about

- **The story is your strongest asset.** Judges weight story and demo heavily, and the grandfather
  framing (one person who was both builder and inspector, now split into O'Brien and La Forge) is
  genuinely distinctive. Lead with it in the video too.
- **The honesty thesis is consistent end to end:** the model never grades itself, the Space banner
  shows the live backend, the simulator is labeled, and we reported a calibration number we didn't
  like instead of faking it. That consistency is worth saying out loud to a judge.
- **"Off-Brand" badge** wants a screenshot of the Astrometrics skin for the claim. The hero shot
  doubles as that evidence.
- **Field-log dataset** is a second Sharing-is-Caring artifact alongside the ledger. Once the token
  is set and a few builds run, it's a live, growing open dataset. Worth a line in the video.
- **Deliberation traces** are a third artifact (`kylebrodeur/chief-engineer-deliberation`): the
  turn-by-turn persona argument, captured both as a static export (`make deliberation`) and **live
  on every run** (`core/deliberation_log.py`, same token gate). This is the one that shows the agent
  *thinking* — a strong dataset-viewer story for the video. Static + live share one schema.
