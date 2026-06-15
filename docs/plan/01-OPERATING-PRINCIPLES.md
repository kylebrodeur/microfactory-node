# 01 — Operating Principles

*Adapted from the Kaggle sprint's operating-principles doc, which got the discipline right. This is the briefing for any agent (or you) working in this codebase during the June 5–15 window.*

---

## Why this document exists

This is a 10-day solo build against a hard deadline, one Gradio Space submission, built nights and weekends. It's connected to a book, a research corpus, a pi ecosystem, and a multi-year vision. All of that is interesting. Most of it is not what we're doing right now.

The risk isn't bad work. The risk is **excellent work on the wrong thing** — chasing a real architectural improvement or a compelling connection while the demo doesn't get finished. That's how the Kaggle attempt ended: the architecture was sound, but the demo path wasn't verified end-to-end before the deadline. (The Kaggle session log's final entry: "Remaining before video: live end-to-end test, real routing verification." It never happened in time.)

This document keeps good thinking pointed at the right target.

---

## The One Test

Before starting anything — or going deeper on something you discovered — ask:

> **Does this help a judge watch the demo video and understand why compounding knowledge matters?**

- If yes: do it.
- If no but genuinely important: note it in `FUTURE-WORK.md` and move on.
- If it's future work: same — log it, move on.

That's the whole framework. Everything below elaborates.

---

## In scope (creative work welcome)

- **The compounding loop made legible.** The one moment that matters: the Chief Engineer evaluates prior jobs against the current environment and says why it's adjusting. Make that unmistakable on screen.
- **The cockpit output.** What the Gradio app shows is what the video captures. The model's *evaluation* of precedent, the proposed settings, the risk annotations on the 3D model. Clear labels, human-readable, the reasoning visible.
- **The 3D preview + annotations.** Interactive, with model-driven risk markers. It makes the demo watchable.
- **The node mesh as context.** The capability-node view that frames the print node inside the Microfactory vision.
- **The story connection.** Tie technical choices back to the narrative (`writeup/00-STORY.md`). "It runs locally because expert knowledge shouldn't depend on a cloud subscription" beats "supports offline inference." Same fact, more resonance.

## Capture, don't chase (out of scope)

Log these in `FUTURE-WORK.md` and move on:

- Weight-level fine-tuning (Well-Tuned badge / Option B)
- The Android e-waste edge node (BONUS)
- Full pi-agent-bus / pi-model-router / pi-qmd-ledger integration
- Real distributed multi-node execution (IPC, pi-link)
- A real print simulator (physics/thermal/slicing)
- Embeddings / vector DB for retrieval
- Book chapter work
- Any new package or major abstraction

If something here turns out to be unexpectedly easy or load-bearing, **surface it before building it** — don't silently reroute. Format: "I found X. It affects Y. Options A/B/C. I recommend A because… waiting for confirmation."

---

## The five rules (anti-Kaggle doctrine)

1. **The demo path is the product.** On a Gradio Space there's no real system behind the demo — the app IS the demo. Stand up one end-to-end happy path early, ugly, then improve inward.
2. **Record early, re-record often.** The demo video is your integration test. A scrappy full recording mid-window exposes the demo-path bugs while there's still time to fix them. This is the step Kaggle never reached.
3. **Every advanced layer is removable.** 3D annotations, node mesh, G-code readout, sensors — each sits ON the working core and can be cut without breaking the submission.
4. **Submit with a multi-day buffer.** Complete and submittable well before the 15th. The back days are hardening on a shippable artifact, not a scramble.
5. **Narrow manufacturing surface, deep memory.** 3–4 setting levers is enough vocabulary. Depth goes into the compounding memory, not print-domain breadth. Judges score whether knowledge compounded, not slicer coverage.

---

## Forcing functions are features

- **One submission.** Every "what to build" is also a "what not to build." A constraint on scope, not quality.
- **~10 solo days, nights and weekends.** Each hour on something out of scope is an hour the demo doesn't get. There is no reserve.
- **Video + story dominate scoring.** A tight, honest demo where the story is legible beats a sprawling system with rough edges. Scope cuts that make the demo cleaner are wins.

---

## The spirit of the thing

The project exists because a grandfather's shop — a lifetime of accumulated making skill — disappeared when Alzheimer's took him and the shop was sold. The Chief Engineer is the attempt to make expert making-knowledge something that accumulates and persists instead of vanishing. When in doubt about scope, ask whether the thing makes that reason more legible to a judge watching the video. If it does, it belongs. If it's interesting but doesn't — capture it and move.

The goal is to ship something true.
