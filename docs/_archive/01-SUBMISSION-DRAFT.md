# DRAFT — The Written Submission (~1,500 words)

> Status: full draft for Kyle's voice pass. Every claim is inside the honesty
> table (`01-SUBMISSION.md`) and the verified-facts list (`00-STORY.md`). Things
> to verify before publishing are marked ⚠. Cut, don't add, under pressure.

---

## The Chief Engineer: a small model that learns a craft so it can't be lost

My grandfather had a shop. He was an electrical engineer by training — twelve
years teaching EE labs, a career as a communications engineer — but at home he
was a tinkerer, and his shop was a home RadioShack with a machine shop attached.
I spent part of my childhood in there, making things, watching him build,
surrounded by tools I didn't understand and projects in every state of done. It
was one of my favorite places in the world.

He spent a lifetime accumulating the kind of skill that lives in your hands and
never quite makes it onto paper. Then Alzheimer's took him. The shop was sold,
the tools dispersed, and all of that knowledge just… went. There was no way to
capture it, no way to keep it. Knowledge built over a lifetime, lost in an
afternoon.

The Chief Engineer is my attempt at the opposite of that.

### The problem

Most 3D-printing failures are knowledge failures. A veteran looks at a part and
the room and already knows: that overhang will sag in this heat, that filament
has drunk too much of this humidity to bridge cleanly, those corners will lift
off a bed that cold. I'm not that veteran. I find out the way every beginner
does — six hours and a spool of filament later. The expertise that prevents
failed prints is tacit, local, and conditions-dependent, and today it lives in
individual people and dies with their shops.

### What I built

The Chief Engineer is a small local model — Gemma, running entirely on my own
machine through Ollama — that accumulates 3D-printing expertise the way a shop
hand would: job by job, conditions and all. Before a print runs, it looks at
the part, the material, and the room (temperature and humidity), recalls the
most similar jobs it has seen, and *evaluates* what they teach about this one.
Then it proposes settings and flags where this print will fail — before the
nozzle moves. Most tools watch a print fail in progress; this one is ahead of
the nozzle.

The knowledge compounds. Every real outcome becomes a durable, condition-keyed
lesson, so job N+1 starts smarter than job N. That's the whole thesis: craft
knowledge that accumulates and persists instead of vanishing.

### How it works — honestly

One loop, end to end:

1. **A job comes in** — geometry (overhang, bridge, vase…), material (PLA,
   PETG, ABS, TPU), and the room's temperature and humidity.
2. **It retrieves precedent** — prior jobs with the same material and geometry,
   ranked by how close their room conditions were to today's (normalized
   distance over temperature and humidity, top 2–3). Deliberately simple: no
   vector database, no embeddings — a mechanism I can inspect and trust.
3. **The model evaluates what transfers.** This is the load-bearing moment, and
   it's on screen: the Chief Engineer weighs the retrieved jobs against today's
   conditions and says so — "this same overhang sagged at lower humidity than
   today's, so conditions are worse; raising cooling, dropping temp." It is not
   forced to cite. When nothing close exists, it says **"no close precedent"**
   and reasons from material properties instead. Knowing what it doesn't know
   is a feature, not a failure.
4. **The Spine vetoes.** The model proposes; a deterministic validator clamps
   anything outside hard material/hardware bounds before it could ever reach a
   printer. Brain and Spine are separate on purpose.
5. **I print, and I report the outcome.** The model never grades its own work —
   a human presses *Printed clean / Sagged / Stringing*.
6. **It reflects.** The outcome is distilled into one durable lesson keyed to
   material, geometry, and the room — appended to a ledger it retrieves from
   forever after.

On top of that loop sits a learned policy: per material/geometry/conditions
bucket, the system accumulates setting offsets from observed outcomes, so what
it learned in one humid PETG job transfers to the *next* humid PETG job, not
just an identical one. Retrieval recalls; the policy generalizes. Both feed
every recommendation, and the UI shows knowledge moving through both — the
ledger growing, the quality curve climbing from failure to clean across a
session (the Print workspace; verified in-app — just confirm it makes
the final cut of the recording).

Being precise about the mechanism: this is retrieval plus a reflection step
plus a small learned policy — **not** fine-tuning, and that's a deliberate
choice. Fine-tuning would bake the knowledge into the weights where you can't
see it; retrieval keeps the compounding *legible* — you watch a lesson get
written after one job and pulled back up to shape the next. For a system meant
to *preserve and show* accumulated craft, visible memory beats invisible memory.
The post-job reflection step itself re-keys a pattern proven in my own
Microfactory lab project, to environment and geometry, for *proactive*
print-failure prediction — shipped end to end in ten days.

### Why a small local model is the honest fit

This problem doesn't need frontier reasoning. It needs a system that holds a
craft and recalls the right piece of it at the right moment — which is exactly
what a compact model plus a good memory does well. The expertise lives in the
ledger and the policy; the model's job is judgment over precedent, terse and
physical, like the shop veteran it's standing in for.

Deliberately, the Chief Engineer runs against the grain of the usual LLM
approach: a narrow surface (three or four setting levers), a deterministic Spine
that vetoes anything unsafe before it could reach a printer, retrieval instead
of open-ended generation, and a model that is never allowed to grade its own
work. The small model does judgment; plain Python does safety. That division is
what makes a model this size trustworthy in front of a machine.

And it runs on my own machine, offline, for free. That's not a deployment
detail; it's the point. The knowledge a maker builds over a lifetime shouldn't
depend on a cloud subscription, and it shouldn't vanish when the shop closes.
A $0/month Chief Engineer that lives where the printer lives is the Build
Small thesis demonstrated, not a compromise endured. One honest note on the
hosted demo: live Gemma inference runs locally via Ollama (that's what the video
shows); the public Space defaults to the deterministic fallback so a judge can
click through instantly without pulling a model — the banner says which path is
live, and the reasoning panel never fakes model output.

### What's real and what's next

Everything above is in the demo: environment-keyed retrieval, visible
precedent evaluation, the deterministic Spine veto, human-reported outcomes,
the growing ledger, the learning loop on simulated outcomes, local Gemma
inference. The simulator is exactly that — a deterministic, physics-lite
stand-in for the printer that lets the closed loop run on camera; it is one
swap away from the real machine and is labeled honestly in the app.

What's next, named as frontier and not implied as built: fine-tuning on the
accumulated ledger so the knowledge lives in the weights as well as the memory;
driving the printer directly (streaming validated start-gcode to my Ender);
real sensors instead of sliders; physics-informed prediction; and extending the
same compounding loop across the other machines in a small shop — the
capability mesh the UI already sketches.

### The close

The shop is gone. The tools were dispersed, and the skill that lived in his
hands went with him. I built the Chief Engineer because that loss shouldn't be
the default ending for a maker's knowledge. The kind of knowledge that lived in
that shop doesn't have to disappear anymore.

---

*Track: Backyard AI (tags `build-small-hackathon`, `backyard-ai`). Badges:
Off the Grid (`off-the-grid`), Llama Champion (`llama-champion`, Ollama runs on
llama.cpp), Sharing is Caring (`sharing-is-caring`, ledger trace on the Hub),
Field Notes (`field-notes`, this post), Off-Brand (`off-brand`, Astrometrics UI).
Not claiming Well-Tuned (fine-tuning is named as frontier). Storytelling is a
judging principle, not a badge. Tiny Titan ($1.5k award) — e2b is effective ~2B
but 5.1B raw; eligibility for MatFormer E-models is ambiguous, so confirm in the
org before tagging `tiny-titan`. (Spot-check the live field guide for exact tags.)*

---

## Word-count + claim audit (delete before publishing)

- Draft body ≈ 1,100 words — room to breathe in the voice pass; target ≤1,500.
- Claims audit: every "built" claim maps to shipped code (retrieval `core/ledger.py`,
  evaluation `core/prompts.py`/`core/chief_engineer.py`, Spine `core/spine.py`,
  reflection `core/reflect.py`, policy `learn/policy.py`, loop `learn/loop.py`, sim
  `sim/outcome.py`, trace `scripts/export_trace.py`). Frontier claims are in the
  frontier paragraph only. Story facts are all from the verified list.
- ⚠ marks resolved (6/10): learning-loop is built+verified (confirm it's in the
  recording); the local-vs-Space inference split is now stated honestly; badges
  reconciled to verified facts. Remaining external check: spot-check the live
  field-guide tag strings and the Tiny Titan E-model ruling before publishing.
