# 07 — Competitive Landscape (read against our build)

Built from Kyle's field survey of ~20 Build Small entries, incl. a dated roster
snapshot (Jun 9–10). The field is still forming — treat as a snapshot.
Purpose: turn intel into a few sharp plays — NOT into new scope. The build is
frozen (`05-ENDGAME.md`); almost everything below is *confirmation* or
*narration*, and the one model-sizing decision is already on our table.

---

## The winning meta (and we're already on it)

The recurring pattern across the strongest projects: **heavily constrained
prompts + deterministic Python scaffolding + strict routing**, used to keep a
small model fast, cheap, and safe. Concretely in the field:

- **Kintsugi Garden** — *four* layers of deterministic Python safety scaffolding
  so the model can't drift into acting like a therapist.
- **ClinIQ** — deterministic regex for extraction, the 3B model only for
  reasoning ("don't use an LLM for what code does better").
- **Pakistan Notice Helper** — a 4B model held to a strict safety output contract.

**What this means for us:** the Chief Engineer already embodies this meta and we
under-sell it. The **Spine veto** (deterministic clamp over the model's
proposed settings), the **structured output contract**, the **human-only outcome
button**, and the **deterministic precedent-evaluation panel** are exactly the
"scaffolding around a small model" judges are rewarding. This is a free
positioning win: name it explicitly in the writeup and narrate it in the video.
No code changes — we built it; we just have to *say* it.

> Narration line to use: "The Chief Engineer does the opposite of the AI meta.
> Narrow surface, deterministic Spine veto, retrieval over generation, and it's
> never allowed to grade its own work. The small model does judgment; Python
> does safety."

---

## Who we actually compete against (track-aware)

Prizes are **per-track ($5k each)**, so our money is the **Backyard AI** pool —
not the whole 21. ⚠ Track tags are inferred from descriptions below; confirm
each rival's frontmatter track on its Space before relying on this.

**Backyard AI (our prize — the real rivals):** ClinIQ (drug-conflict safety),
Pakistan Notice Helper (scam triage), NeuroBait (ADHD nudge), Nutri-Analyser
(grocery health), Job Searcher (resume fit), **CraftPilot** (craft marketplace).
Possibly Her / Room360 (track unclear).

**Thousand Token Wood (NOT competing for our money):** the four-part economy
saga, Kintsugi Garden, TurboSkillSlug, Room Vibe Check, Mythograph, Mind of
Tashi, Case Zero, Persona Atlas, Caro5, Amazing Digital Dentures. Impressive,
but a different $5k. Don't be intimidated by the polish of work we're not racing.

### Our structural differentiator: we're the only stateful one
Nearly every Backyard AI rival is a **stateless single-shot tool** — photo →
listing (CraftPilot), message → verdict (Pakistan Helper), doc → conflict
(ClinIQ), label → score (Nutri). They don't get better with use. **The Chief
Engineer is the only entry whose knowledge compounds** — job N+1 starts smarter
than job N, and you watch the ledger grow on screen. That, plus **proactive
prediction** (pre-failure, not post-hoc analysis), **knowing what it doesn't
know**, and the **grandfather/loss story**, is the four-part edge. CraftPilot is
the only other "maker" project and it's stateless e-commerce — adjacent theme,
no learning loop, different emotional register.

**Demo implication:** make "it gets better every job" the thing the video
*screams*. It's the one differentiator no rival in our track can match — so it,
not the settings or the 3D view, is the climax.

---

## What the timestamps tell us (dated roster, Jun 9–10)

- **The field is still forming.** ~20 entries, most posted in the final 1–3 days
  before the snapshot; more will land before Jun 15. This is a snapshot, not the
  final field — don't optimize against a frozen list.
- **The operational gut-punch: rivals already have live Spaces. We don't.** The
  named Backyard contenders are deployed and working *now*. Our build is more
  complete than several of theirs, but "complete on a branch" scores zero. This
  is the whole argument for the endgame plan: the gap isn't capability, it's a
  shipped artifact. Close it today (preflight → record → deploy), not Jun 14.
- **One author (skamathramesh) shipped two projects.** Volume is in play; we win
  on depth + story, not count. Stay single-target.

## Judged on (Backyard AI): utility · specificity · honest-fit — mapped

The track's stated axes, against us:

- **Specificity — our strongest.** One real user (Kyle), one machine (the
  Ender), one domain, one true personal story. This is exactly what NeuroBait
  ("built for the dev's wife") did well — and our grandfather "why" goes deeper
  than anything in the field. Make "real user = me" explicit and concrete.
- **Honest small-model fit — strong, and we can articulate it.** Craft = memory
  + recall, not frontier reasoning; it runs where the printer lives. We have a
  thesis for the fit, not just a deployment fact.
- **Utility — our gap to close.** The top Backyard rivals solve high-stakes
  problems for someone (drug conflicts, scams, ADHD paralysis). Ours — wasted
  filament, hours lost, the beginner's expertise gap — is real but reads as
  lower-stakes unless we make it concrete: "a failed overhang is six hours and a
  spool gone; a veteran would've caught it in two seconds." Don't let the
  emotional story crowd out the practical payoff — judges score both. We have
  both; say both.

## Quiet differentiator: we're not in the Qwen herd

The field is overwhelmingly Qwen (2.5-3B / 3-8B / VL-7B). We run **Gemma** via
Ollama. Minor, but worth one honest line: it diversifies us from the pack and
ties cleanly to Llama Champion (llama.cpp) and the local-first story. Don't
overplay it — model choice isn't the thesis — but don't blend in either.

---

## Three plays (all inside the freeze)

### 1. Tiny Titan badge — likely already ours, verify the number
The field guide's **Tiny Titan** badge = best app on a genuinely tiny model
(**≤4B params**), "biggest impact from the smallest weights." Pakistan Notice
Helper explicitly framed 4B as the "Goldilocks" choice and it paid off.

Our `gemma4:e4b` / `e2b` naming mirrors **Gemma 3n E4B / E2B**, whose *effective*
parameter counts are ~4B and ~2B (the "9.6GB" in our notes is file size, not
params). ⚠ **Action:** confirm the effective param count of the model we ship.
If E4B ≤4B effective, we qualify on our default model. If it's borderline,
shipping **E2B** wins Tiny Titan outright *and* fixes latency (§G2) — a
two-birds decision. This is a model-choice call we were already making on Day 6;
now it has a badge attached. Add the tag if eligible.

### 2. Storytelling — ours to lose *(correction 6/10: a judging principle, not a badge — "storytelling counts as much as the build". No tag; the edge is unchanged.)*
The full package (app + demo video +
social post) where storytelling counts as much as the build. Our single biggest
edge over this field is the grandfather narrative — specific, true, about loss.
Most projects here are clever; few are *moving*. Treat Storytelling as a primary
target, not a bonus: it rewards exactly what we're strongest at. Tag it; make
the video's Beat 1 earn it.

### 3. Field Notes / dev-log as a real category
Honest build narratives are clearly a thing judges/community engage with:
Lester Leong's **4-part** Thousand Token Wood saga, the **Caro5** field notes,
and a published **failed-project post-mortem** (Amazing Digital Dentures). Our
Field Notes post should be in that honest-build-log voice: the re-keyed-proven-
pattern framing (`00-MASTER.md`), what's real vs. frontier, and what we cut and
why (the off-target swarm misfire; the vault spike we quarantined). Publish it
**on the org blog**, not just the repo — that's the discoverability surface.

---

## These are COMPETITORS, not references — and several fine-tuned in-window

Correction to an earlier framing: these 21 are **current entries in this
hackathon**, not prior art. We don't cite rivals to justify our roadmap. The
useful read is differentiation and threat, not borrowing.

Two consequences:

1. **Fine-tuning is not exotic to this field — rivals did it in the 10-day
   window.** NeuroBait (16-bit LoRA on Gemma-3-12B via Unsloth), Kintsugi (QLoRA
   on Qwen3-8B), Job Searcher (DeepSeek-teacher → Qwen3-8B-student distillation).
   So our writeup must NOT imply fine-tuning a small model is hard or far-off —
   judges watched others ship it this week. Reframe our choice as **deliberate,
   not limited**: we chose retrieval + reflection because it makes the
   compounding *legible and inspectable on screen* — you watch a lesson get
   written and reused — which a weights-baked fine-tune hides. Fine-tuning the
   ledger is the natural next step, named as a roadmap choice, not a frontier we
   couldn't reach. (Switching to fine-tuning NOW, with no recording and 5 days
   left, is the Kaggle failure shape — do not.)
2. **The bar in our track is "tight, safe, practical local tool."** ClinIQ and
   Pakistan Notice Helper set it well. We clear it AND add what they lack
   (below).

---

## One-line takeaway

In our actual race (Backyard AI), we're on the winning meta, we're the only
**stateful/compounding** entry against a field of stateless single-shot tools,
and we're strongest exactly where the judging principle (storytelling) and the
Tiny Titan special award pay out — though Tiny Titan eligibility for E-models is
unresolved (raw vs effective params; ask the org).
Rivals fine-tuned in-window, so frame our retrieval choice as deliberate
(legible compounding), not as a frontier we couldn't reach. The work is
unchanged — **prove it, record it, ship it** — with the compounding loop as the
demo's climax.

---

## 2026-06-14 final-weekend update (submission day)

A second, wider field survey landed on submission morning. The roster grew and a
few patterns hardened. This section is the read against the fuller field; the
plays above still hold, this sharpens the targets.

### The fuller roster (what changed)

The field is bigger and more polished than the Jun 9 snapshot. The named
contenders worth tracking now:

- **Track 1 (general / Thousand Token Wood pool):** Pakistan Notice Helper (scam
  triage, 4B, strict safety contract), GigScan (gig-listing scam detector),
  ClinIQ (drug-conflict safety, regex extraction + small model for reasoning),
  NeuroBait (ADHD nudge, LoRA on Gemma 3 12B). These are the strongest "tight,
  safe, practical" builds.
- **Track 2 (Backyard AI / craft pool):** The Mind of Tashi (companion/persona),
  Lolaby (lullaby generator), Thousand Token Wood (the four-part economy saga),
  TurboSkillSlug (skill coach). Heavy on polish and narrative.

We are still the only entry in our pool whose knowledge **compounds**. Nothing in
the wider roster changes that. Lolaby and Tashi are generative-and-stateless;
GigScan and the safety tools are single-shot classifiers. The structural
differentiator from §"we're the only stateful one" holds against the bigger field.

### Three trends that matter for our positioning

1. **MiniCPM-V is the vision king of this field.** A lot of the strongest entries
   are multimodal (photo in, verdict out). We are deliberately text-only and that
   is fine, but it means the "wow on camera" bar elsewhere is a live photo demo.
   Our answer is not to chase vision; it is to make the **compounding curve** the
   visual payoff (the ledger growing, quality climbing fail to clean) since no
   vision demo can show learning-over-time in one frame.
2. **llama.cpp / GGUF over raw transformers is now the default.** The field moved
   to quantized local inference. This is a direct tailwind for **Llama Champion**
   (Ollama runs on llama.cpp) and the local-first thesis. Our QAT/GGUF fine-tune
   track (v3) lands us exactly on this trend if it earns the swap.
3. **Strict scaffolding is table stakes, not a differentiator.** What read as our
   edge in the Jun 9 survey (deterministic Spine, structured contract) is now the
   baseline everyone clears. The Spine still matters for *trust*, but it no longer
   sets us apart on its own. What sets us apart is the **two-agent honesty split**
   (O'Brien proposes, La Forge grades, the model never grades itself) layered on
   top of the scaffolding, plus the compounding loop.

### Where we win, ranked (against the fuller field)

1. **Story and specificity.** Still our single biggest edge. One real maker, one
   real machine, one true loss story. The wider field is more polished but not
   more *moving*. Beat 1 of the video has to earn this.
2. **Honest small-model fit.** Craft is memory and recall, not frontier
   reasoning. We have a thesis for the fit, not just a deployment fact.
3. **Compounding.** The only learning-over-time entry. This is the climax.
4. **On-trend architecture.** Local GGUF / llama.cpp, optional LoRA, two-agent
   honesty. We sit on the field's winning meta without having chased it.

### Where we are most exposed (rank-ordered risks)

1. **The simulated outcome is our number-one vulnerability.** Every rival's
   outcome is real (a real photo, a real document, a real message). Ours is a
   physics-lite stand-in. We must keep naming it plainly in the app and the
   writeup and frame it as "one swap from the machine," because a judge who feels
   it was hidden will discount the whole loop. Honesty here is the defense.
2. **Breadth of scope reads as ambition that could read as unfinished.** The
   Microfactory framing is large. Keep the submission scoped to the one shipped
   node; name the rest as roadmap, not demo.
3. **Well-Tuned against real fine-tuners.** NeuroBait and others shipped actual
   LoRAs in-window. Our end-to-end "system tuning" framing is honest but weaker
   than a weights-level claim. The v2/v3 LoRA is the strong basis; claim
   Well-Tuned on the LoRA only once a held-out eval earns it, and keep the
   system-tuning framing as the floor, not the headline.

### Tactical moves for the last hours

- Lead every public surface with **"Microfactory Node: 3D Printer," the named
  agents, and the grandfather story** in the first two lines, before any feature.
- Make the **compounding curve** the visual climax of the video, since vision
  rivals own the single-frame wow and we own learning-over-time.
- Lean on **Llama Champion** and local GGUF in the copy; the field's move to
  llama.cpp makes this a shared-language win, not a niche claim.
- Keep the **simulated boundary** labeled everywhere it appears. Treat the
  honesty as a feature we say out loud, not a caveat we bury.

### One-line takeaway (updated)

In the fuller field we are still the only compounding entry, now sitting on the
field's hardened meta (local GGUF, scaffolding, optional LoRA) without having
chased it, and strongest where it pays out (story, specificity, honest fit). The
field caught up on scaffolding, so our separation is the two-agent honesty split
plus the compounding loop, not the Spine alone. Biggest exposure is the simulated
outcome; the defense is to name it plainly. Work unchanged: prove it, record it,
ship it.
