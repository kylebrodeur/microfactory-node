# 05 — Endgame Plan (June 10–15)

The strictest version of what's left. Supersedes `03-EXECUTION-PLAN.md` for the
remaining window (we are ahead of its feature plan and behind its proof plan).
Companion: `06-CONTINGENCY.md` (when things break) and `make preflight` (run it
first, every local session).

**Standing as of June 10:** build complete and tested offline; real-model path
never exercised; no recording; no Space; writeup drafted (see
`../writeup/01-SUBMISSION-DRAFT.md`) but not voiced. Five days left.

---

## The three rules of the endgame

1. **FEATURE FREEZE — total.** Nothing new enters any path, demo or otherwise.
   The only allowed code changes: prompt tuning (§G4), contract fixes (§G3),
   latency knobs (§G2), deploy fixes (§S1). Each must be driven by a failing
   preflight gate, not by an idea.
2. **Every local session starts with `make preflight`.** Green gates are
   the only permission to record. A failing gate sends you to the runbook
   section it names — not to improvisation.
3. **Ship the fallback version of anything that isn't green by its deadline
   below.** Every deadline has a named fallback. Missing a deadline silently is
   the only unrecoverable failure.

---

## Day-by-day with gates and abort criteria

### Day 6 — TODAY, June 10 (first local session)

The whole day is converting "built" into "proven live."

| # | Task | Done means | If it fails |
|---|------|-----------|-------------|
| 1 | `ollama pull gemma4:e4b` started immediately (long pole) | model present | §G1 — pull e2b instead |
| 2 | `make preflight` until green | exit 0, no FAIL | the gate's § in runbook |
| 3 | READ the reasoning text on 3–4 real runs (cockpit, `make run`) | Beat-3-worthy text on a precedent-rich job AND honest no-precedent on a novel one | §G4 prompt tuning, max 3 iterations, re-preflight each |
| 4 | `make bench` on THIS laptop; decide e4b vs e2b ONCE | a number written down + model choice committed to `.env` | §G2 |
| 5 | **Record the scrappy full demo** (phone-quality fine; beats from `02-VIDEO.md`, jobs from `scripted_demo.py`) | a watchable end-to-end file exists | §R1; if model not green by 20:00, record fallback beats per §G1.3 |
| 6 | Note every demo-path bug the recording exposed | list in TODO.md | — |

**Hard gate at end of day:** a full scrappy recording EXISTS. This was due
yesterday (plan Day 5). It is the single highest-leverage artifact left —
it is the integration test Kaggle never ran.

### Day 7 — June 11 (SUBMITTABLE day, per the original plan)

| # | Task | Done means | If it fails |
|---|------|-----------|-------------|
| 1 | Fix only what the Day-6 recording exposed | re-run preflight green | runbook |
| 2 | **Deploy the Space** into `build-small-hackathon` org | cold-start serves the cockpit; fallback path shows recommendations + precedent panel + ledger growth | §S1 ladder (personal-namespace debug → strip layers) |
| 3 | Voice-pass the writeup draft (`01-SUBMISSION-DRAFT.md` → final) | ~1,500 words in your voice, every claim within the honesty table | §W1 — draft is shippable as-is |
| 4 | Social post drafted (`04-SOCIAL-POST.md` → pick one) | text + asset chosen | — |
| 5 | README frontmatter: track + badge tags added per checklist | `03-SUBMISSION-CHECKLIST.md` items ticked | — |

**Hard gate:** end of Day 7 = a complete submittable package (degraded
quality allowed): Space up + scrappy video + writeup + social text. From here
on, everything is upgrade-only.

### Day 8 — June 12 (the REAL recording)

- Re-record the demo properly. Reset state every take (§R1). Beats per
  `02-VIDEO.md`; let Beat 3 breathe; show the novel case; show the ledger grow.
- **18:00 abort criterion:** live-model Beats 3–4 not in the can by 18:00 →
  record the fallback version tonight (§R1 hard rule). Decided by the clock,
  not by optimism.
- Capture social-post assets (screen recordings/stills) in the same session.

### Day 9 — June 13 (polish + badge harvest, in this order)

1. Edit the video; tighten to the hackathon's length limit; verify Beat 3 lands.
2. Push ledger trace to the Hub (`make trace` → dataset repo) — Sharing is Caring.
3. Publish Field Notes post on the org blog (adapted from the writeup — see
   intel below: org blog posts are how the field shows up in public).
4. Social post goes live; LINK IT in the Space README (explicit requirement).
5. Off-Brand pass ONLY if all above is done: verify Astrometrics CSS renders;
   screenshot for the post. No new CSS work beyond verification.

### Day 10 — June 14 (freeze + SUBMIT)

- Full dry run of the actual submitted artifacts as a judge: open the Space
  cold, watch the video, read the writeup, click the social link.
- Fix only breakage. **Submit everything today.** June 15 is buffer, not
  workspace.

---

## Field intel (researched June 10 — verify on the org page locally)

The org's public footprint (sandbox couldn't open the org page directly —
network-restricted; these come from indexed pages):

- **Stakes:** ~$48k cash + 2× RTX GPUs + 20k Modal credits across **29 awards**;
  $5k per track. Two tracks: Backyard AI / Thousand Token Wood.
- **Hard requirements confirmed:** Gradio Space IN the org; demo video showing
  the app working ("so judges can evaluate it even if GPU/API limits stop a
  live run" — i.e., the video carries judging when the Space is degraded:
  our §S2 default is officially sanctioned); one social post **linked from the
  Space README**; frontmatter tags for tracks + badges; ≤32B params.
- **Visible field (indexed org blog posts so far):** Job Searcher; Persona
  Atlas (research-a-person agent); a multi-model finance-economy sim (Thousand
  Token Wood track, 2 posts — polished competitor); "Her · हेर" Claude-session
  detective; Room360 video-to-3D; one honest "failed project" post (Amazing
  Digital Dentures). **Nothing indexed so far resembles a physical-fabrication
  / craft-knowledge / compounding-memory build.** The story lane is open.
- **Badge landscape note:** searches also surfaced badge names not in our docs
  ("Tiny Titan" ≤4B special award — E-model eligibility UNRESOLVED, ask the org;
  "Storytelling" = judging principle, not a badge — verified 6/10). Verify
  the live field-guide badge list when you're on the org page —
  **Storytelling, if real, is ours to lose** (the video/story IS our edge), and
  check whether the e2b/e4b effective-parameter sizes qualify for Tiny Titan.
- **Action this implies:** publish the Field Notes post ON the org blog (that's
  the discoverability surface judges/sponsors demonstrably look at), not only
  in the repo.

---

## What is explicitly NOT happening this window

Restated from the freeze, so it's unambiguous under pressure: no vault-spike
graduation, no Modal inference unless Day-8-green (§S2), no fine-tuning, no new
tabs, no new materials/geometries, no sensor hardware, no swarm work, no
refactors. Log temptations in TODO.md and walk away.
