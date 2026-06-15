# The Chief Engineer — Documentation Bundle

Build and submission docs for the Hugging Face **Build Small** hackathon (June 5–15, 2026). Solo build, Backyard AI track.

## Guiding principle

A **clever proof of concept that works** — not a production system. Backyard AI judges a demo video, a writeup, a plausible "someone could use it" story, and a working Gradio app. Build the judged things well; keep everything else minimal. **A component nobody judges should never cost more than a component that is judged.** Simplify as you go.

## Structure

Two numbered sets. Plan docs are how you build it. Write-up docs are what you submit.

```
plan/                          ← how to build it
  00-MASTER.md                 current state, locked decisions, index
  01-OPERATING-PRINCIPLES.md   the One Test, scope discipline, anti-Kaggle rules
  02-ARCHITECTURE.md           Python/Gradio/Ollama; patterns; model tags; honest claims
  03-EXECUTION-PLAN.md         pre-window tasks + day-by-day June 5–15 + badges
  04-BUILD-PROMPT.md           paste-into-Claude-Code prompt for the core build
  pattern-review.md            (reference) repo pattern digest
  seed_lessons.jsonl           (data) 12 starting lessons

writeup/                       ← what you submit
  00-STORY.md                  the grandfather narrative — verified facts, HF framing
  01-SUBMISSION.md             the ~1,500-word writeup: structure, honest claims, draft scaffold
  02-VIDEO.md                  demo video beats, the load-bearing moment, shot guidance
```

## The one thing that matters

The demo must show the Chief Engineer **proactively evaluate prior jobs against the current environment** before a print — applying precedent when it fits, recognizing when it doesn't: *"humidity is higher than the job where this overhang sagged — raising retraction, adding support."* Everything else is scaffolding for that moment.

## Status

- ✅ Registered. ✅ Seed lessons written. ✅ Build prompt ready. ✅ Reference docs reviewed and folded in.
- ☐ Pre-window: deploy a trivial Gradio Space with a static `gr.Model3D` cube; measure `gemma4:e4b` (or `e2b`) CPU latency on Space hardware.
- ☐ Day 1: run `plan/04-BUILD-PROMPT.md`; core loop running locally.

Start in `plan/00-MASTER.md`.
