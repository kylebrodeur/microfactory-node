# 05 — Projected Outcome & Honest Prize Assessment

*Compiled June 10, 2026 (Day 6 of 10). A simulation of project completion, a
critical judgment, and a calibrated prize read — with the verification kept
honest: what is fact, what is projection, and what is unknown are labeled
throughout.*

---

## 0. Epistemic status (read this first)

This report mixes three kinds of statements; they are tagged so optimism can't
masquerade as fact:

- **[FACT]** — verified in this repo/session (tests run, app served, files exist).
- **[PROJ]** — projection assuming the endgame plan is executed competently.
- **[UNK]** — genuinely unknown / unverifiable from here; a risk or assumption.

**Sources & their limits.** Build facts: direct repo inspection. Field facts:
Kyle's two competitor surveys (a dated Jun 9–10 roster) — secondhand, and the
field is *still forming* before Jun 15. Hackathon rules/badges: my web research
+ the project's internal docs, which **partially conflict** (see §7). The HF org
page and field-guide Space were network-blocked from this environment, so badge
taxonomy and exact submission mechanics are **[UNK]** pending Kyle's check.

No numbers here are data. Probability bands are calibrated judgment with wide
error bars, given to be useful, not precise.

---

## 1. Verified baseline — what actually exists today [FACT]

- Core loop builds, serves HTTP 200, four workspaces (Studio / Build / Print /
  Review) + a separate QA Inspector. 10/10 core tests pass headless. ~2,500 LOC
  across the demo-path modules. 12 seed lessons.
- Offline path is solid end to end: `scripted_demo.py` runs the four-beat story
  (precedent applied → env shift → earned-lesson reuse → novel "no precedent");
  ledger compounds 12→15; Spine clamps an unsafe PLA 260°C→220°C.
- Endgame kit in place: `preflight.py` (8 gates + Tiny Titan check),
  `06-CONTINGENCY.md`, `05-ENDGAME.md`, writeup draft, social drafts, checklist.
- **Not yet done:** real-model run (no Ollama here), recording, Space deploy,
  writeup voice-pass, social post, badge submissions. Three of the four scored
  artifacts (Space, video, writeup) **do not exist yet**.

The honest one-liner of the baseline: *build ahead of plan, proof behind plan.*

---

## 2. The simulation — how completion actually goes

Completion hinges on **one fork** the sandbox could never resolve: **does the
real Gemma produce the load-bearing precedent-evaluation text, well and fast
enough?** [UNK] Everything else is comparatively low-variance. So the sim is
three branches off that fork.

### Branch A — "It works" (baseline-likely if the plan is followed) [PROJ]
Preflight goes green or green-with-warnings. Gemma e4b (or e2b) returns
schema-valid JSON with reasoning that genuinely weighs precedent against the
room. Kyle records the four beats locally today, deploys a Space (running the
**deterministic fallback** path — see §3), voice-passes the writeup tomorrow,
posts social, harvests badges Day 9, submits Day 14.
**Result:** a complete, polished, on-time, honest submission. The compounding
moment lands in the video. Most likely outcome **if** the fork resolves well.

### Branch B — "It works AND runs live on the Space" (upgrade) [PROJ]
As A, plus the model is made to run *on the Space* (ZeroGPU or Modal; §3),
so judges who open the Space see the real reasoning, not the fallback. Higher
ceiling, more risk/time. Only reachable if A is locked first.

### Branch C — "The model underwhelms" (the real downside) [PROJ/UNK]
Gemma's reasoning is terse/generic, or it hallucinates precedent on the novel
case, or latency is brutal, or JSON is flaky. Prompt-tuning (§G3/§G4) buys some
back; if not, Kyle falls to the deterministic precedent panel for Beats 3–4
(honestly framed). **Submission still ships and is still coherent** — this is
the payoff of the all-removable-layers doctrine — but the "wow" is muted and it
reads closer to a polished lookup+rules tool than a reasoning one.

**Probability mass (judgment, wide bars):** A ≈ 55%, B ≈ 10%, C ≈ 35%. The 35%
on C is not pessimism — it's that we have *zero* observations of the real model
and small models are genuinely variable on structured-reasoning prose.

---

## 3. Critical judgment — the load-bearing weaknesses

Strengths are real and already covered elsewhere (unique stateful/compounding
design, strongest story in the field, on-meta deterministic scaffolding, clean
offline robustness). The job here is the **weaknesses**, honestly:

1. **The live-Space experience is the weak one. [FACT/architecture + UNK on Space]**
   The app uses **Ollama**, which does not run on a standard HF CPU Gradio Space.
   So a judge who opens our Space most likely sees the **deterministic fallback**
   ("🟡 offline fallback"), whose reasoning text is mechanical — while the *video*
   shows the real model. Several top Backyard rivals (ClinIQ, Pakistan Helper)
   ship small **GGUF via llama.cpp** that *does* run live on the Space, so their
   "open it and try it" experience is stronger than ours. The field guide
   sanctions video-carries-judging, which protects us — but this is a genuine
   competitive gap, not a non-issue.
   - *Mitigations:* retrieval + ledger growth + the precedent panel ARE fully
     live on our Space (real, just not the LLM prose). And the §S2 upgrade
     (ZeroGPU/Modal, or swapping Ollama→llama-cpp-python in-process) would close
     it — but it's a code change under freeze and must wait until the baseline
     submission is locked.

2. **Utility reads lower-stakes than the top rivals. [FACT/field]**
   Drug-conflict / scam / ADHD-paralysis carry visceral stakes; "a failed print"
   needs to be *made* to carry weight ("six hours and a spool gone, every time,
   until you've built the intuition"). The draft does this; the video must too,
   or we win story and lose the utility axis.

3. **The reasoning quality is unproven and it's the whole demo. [UNK]**
   Restating Branch C: the single highest-variance element is also the single
   most load-bearing one. Until preflight G4 runs green locally, the submission's
   centerpiece is a hypothesis.

4. **The simulator could read as "fake." [FACT]**
   The Print loop improves against a *deterministic outcome simulator*, not
   a real printer. It's labeled honestly in-app, but on camera a skeptical judge
   could discount it. Framing matters: it's a stand-in for the printer, one swap
   from real, and the *retrieval/reflection* loop (the thesis) is genuine.

5. **The field is still forming. [UNK]**
   More/stronger Backyard entries may land before Jun 15. Today's roster is a
   snapshot; our read could be stale by the deadline.

---

## 4. Projected final artifacts (Branch A) [PROJ]

- **Space** in `build-small-hackathon`: 3-tab cockpit, fallback-live, honest
  backend banner, seeded ledger, README with track+badge tags, video + social
  links. Cold-starts and serves (low risk — clean reqs, served 200 locally).
- **Video** (~2.5 min): the six beats; Beat 3 the real-model precedent eval;
  Beat 4 the novel case + ledger growth; offline shown for Off-the-Grid.
- **Writeup** (~1,500 wds): the audited draft, voice-passed; honesty table held.
- **Social post:** one of the three drafted variants, linked from README.
- **Badge claims:** Off the Grid, Llama Champion, Sharing is Caring, Field Notes,
  + (conditional) Off-Brand; Tiny Titan only if the E-model param ruling lands our way (storytelling = judging principle, not a badge — 6/10).

---

## 5. Prize assessment — what could actually be awarded

Calibrated judgment, wide bars, conditional on Branch A unless noted. "Field
unknown/forming" caps confidence on everything competitive.

### Track: Backyard AI ($5k pool, placements)
- **Any top-3 cash placement:** **Moderate** — ~20–30% (A), ~30–40% (B),
  <10% (C). We're a credible top-tier entry on originality+story; the live-app
  gap and strong, higher-stakes rivals are what keep it from being better.
- **Winning the track outright:** **Low–Moderate** — ~8–15% (A/B). Possible if
  story + uniqueness dominate judging and execution is clean; not the base case.
- **What moves it most:** Branch A→B (live model on Space), and a video where
  the compounding moment is undeniable.

### Badges (more controllable → higher confidence)
- **Off the Grid (local):** **Strong/Near-certain** if the video shows offline. ✅ by design.
- **Llama Champion (llama.cpp):** **Strong** — true by construction; just document it.
- **Sharing is Caring (open trace):** **Near-certain** — `make trace` + push; low effort, in plan.
- **Field Notes (blog):** **Near-certain** — post is mostly written; publish on the org blog.
- **Storytelling:** **Moderate–Strong** — our biggest edge, BUT likely cross-track
  competition from narrative-heavy Thousand Token Wood entries (Kintsugi, the
  economy saga). Contender, not lock.
- **Tiny Titan (≤4B):** **Conditional** — eligible IF the shipped model counts as
  ≤4B (E2B safe; E4B depends on raw-vs-effective counting, [UNK]) AND tagged.
  Competitive (Mind of Tashi ~200M, ClinIQ 3B, Pakistan 4B). Contender if tagged.
- **Off-Brand (custom UI):** **Low–Moderate** — CSS exists but is visually
  unverified; only claim if it genuinely reads as custom, not restyled-default.
- **Well-Tuned:** **None** — correctly not attempted.

**Most likely realistic haul (A):** 3–4 badges banked (Off-Grid, Llama,
Sharing, Field Notes), 1–2 conditional (Storytelling, Tiny Titan), and a real
but minority shot at a Backyard cash placement. **That is a genuinely good
hackathon outcome** — decorated, honest, on-time — even if it isn't 1st.

---

## 6. Highest-leverage moves to improve the odds (priority order)

1. **Resolve the fork TODAY.** `ollama serve` → `make preflight` → read the
   reasoning text. If G4 is weak, spend the prompt-tuning budget now (§G4). This
   collapses the biggest uncertainty in the entire assessment.
2. **Record today.** A scrappy full take is the integration test; it converts
   "build" into a scored artifact and de-risks everything downstream.
3. **Decide E2B vs E4B once** (latency + Tiny Titan + quality). Ship the smallest
   that clears G4. Tag Tiny Titan if the count qualifies.
4. **Lock the baseline submission (Branch A) before any upgrade.** Space +
   video + writeup + social, submittable, by Jun 11.
5. **Only then consider Branch B** (live model on Space via ZeroGPU/Modal, §S2)
   — the single biggest ceiling-raiser, but never before A is safe.
6. **Make utility visceral in the video** (the six-hours-and-a-spool line) so we
   don't trade the utility axis for the story axis.
7. **Verify badge taxonomy + submission mechanics on the live org page** (§7) so
   no points are left on the table from mis-tagging.

---

## 7. Honest verification & validation (stress-testing this report)

Where this assessment could be **wrong**, stated plainly:

- **Badge taxonomy is [UNK] and sources conflict.** The internal docs list
  {Off-Grid, Llama, Sharing, Field Notes, Off-Brand, Well-Tuned}; my web research
  surfaced {Tiny Titan, Storytelling, and an "Off the Grid = most-criteria-met"
  definition} that doesn't match the internal "local-first" meaning. **Someone
  has to read the live field guide.** If the badge set differs, §5's badge rows
  shift. This is the biggest factual soft spot in the report.
- **The live-Space claim needs validation.** "Ollama won't run on the Space" is
  high-confidence but not verified on the actual target hardware. If the Space
  tier *can* host the model (or ZeroGPU is trivially available to the org),
  weakness #1 shrinks and Branch B gets cheaper.
- **The probability bands are judgment, not data.** No visibility into judge
  composition, weighting, or the final field. Treat A/B/C and the prize % as
  directional. The honest core claim is ordinal, not cardinal: *badges are
  high-confidence; a cash placement is a real minority shot; the dominant
  variance is the unproven model output and whether it ships.*
- **Optimism check on "writeup is easy / record immediately."** Plausible (the
  material exists), but recording a *good* take and a clean deploy each have a
  way of eating a day. The Jun 11 submittable gate has buffer; the risk is
  spending Branch-B effort before Branch A is locked. The plan guards against
  this; discipline is the dependency.
- **What would falsify the rosy read fastest:** a weak G4 reasoning result
  tonight. If that happens, drop to Branch C honestly and compete on polish +
  story + the (real) retrieval/compounding, not on model reasoning.

---

## 8. Bottom line

**[PROJ]** If the plan is executed, the most likely outcome is a **complete,
honest, well-decorated Backyard AI submission** — 3–4 badges near-certain, 1–2
more in reach, the strongest story in its track, and a **real but minority
chance at a cash placement**, gated mainly by (a) whether the live model
delivers the load-bearing moment and (b) the weaker live-on-Space experience
versus rivals whose models run in-browser.

**The result is decided this week, and mostly today.** The build already earns a
respectable finish; the difference between "respectable" and "contender" is
almost entirely execution now — resolve the model fork, record, ship the
baseline, and only then reach for the live-Space upgrade. The honest verdict:
**a good outcome is likely; a winning one is reachable but not the base case —
and the single highest-value hour you can spend is the preflight run that tells
us which.**
