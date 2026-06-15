# 02 — The demo video (two-track plan)

You produce video professionally, so this is structure, not technique. It is deliberately
short: the click-by-click path lives in **`docs/RUNBOOK.md` §2 (the judge's tour)** and stays
current as the UI changes, so it is not duplicated here. This doc is the two-track plan and a
set of plain talking points you can paraphrase, not a script to read.

**Cast (name them once on screen):** **Chief Engineer O'Brien** proposes settings; **La Forge**
(QA Inspector) grades. O'Brien never grades his own work.

> UI is being updated. Keep this doc at the beat level. Treat RUNBOOK §2 as the single source
> of truth for exact clicks, and re-read it right before recording.

---

## The shape

Two tracks you cut together. Target ~2 to 3 minutes.

- **Track A — Camera (you, to lens).** Two short end caps you can shoot fast: the open (the
  story) and the close. Optionally a talking head you overlay on the demo where your face helps
  the moment connect.
- **Track B — Screen recording (the tool).** The judge's tour from RUNBOOK §2, Build to Slice
  to Print to Review, with a few beats emphasized and one plain line each.

Record the demo from the **live node at [node.microfactory.space](https://node.microfactory.space)**
(HF Pro means live Gemma reasoning on screen; the branded domain also reads cleaner on camera).
Reset the demo curve first so the compounding is real on camera (RUNBOOK §4).

---

## Track A — Camera (end caps)

Keep these spare and in your own voice. Spoken plainly beats performed. Full narrative and the
exact closing line are in `writeup/00-STORY.md`.

- **Open (~20 to 30s).** The shop. Your grandfather, an engineer who tinkered. Alzheimer's, the
  shop sold, the skill in his hands gone. Land on why you built this. Let it sit; do not rush it.
- **Close (~15s).** Back to him. The closing line from `00-STORY.md`. End on the human point,
  never on a feature or a metric.
- **Optional: camera over the demo.** If a beat connects better with your face on it (the second
  opinion, or the "no close precedent" honesty moment), overlay a talking head there. Use it to
  connect, not to narrate every click.

---

## Track B — Screen recording (the tour)

Follow RUNBOOK §2 for the path. Emphasize these beats and say one plain line at each. Paraphrase
freely; these are talking points, not lines to recite.

| Beat (tab) | What to emphasize | One plain line |
|---|---|---|
| **Build** | Drop one of **your own printed STLs** (fallback: quick-load Benchy). It learned on your real jobs. | "This is a part I actually printed. I fed it my own OctoPrint history, so it learned on my jobs, not a stock set." |
| **Build** | You pick material and the room; you never pick the part type. | "I give it the part, the material, and the room. It works out what kind of part this is on its own." |
| **Slice** *(the load-bearing moment)* | O'Brien recalls the closest prior jobs, says what transfers, and flags where it fails, before anything prints. The Spine vetoes unsafe values. | "It tells me where this print fails before the nozzle moves, and points at the prior job it is reasoning from." |
| **Slice** *(second opinion)* | Flip the THE READ toggle from Engineer's Read to Second Opinion; La Forge critiques the plan, and a dispute holds the print until you clear it. | "A separate reviewer grades the plan, and can hold the print. It never marks its own homework." |
| **Print** *(the climax)* | Quality climbs fail to clean over a few iterations; La Forge grades each run. | "Every job makes the next one better. That is the whole point." |
| **Review** | The ledger grows seed to earned, and the run verdict lands. | "The knowledge compounds instead of disappearing." |
| **Optional: one real print** | Take O'Brien's settings, run them on the real Ender, report the true outcome with the record button. | "Same loop, a real print. The settings and the learning are real; only the auto demo uses a stand-in." |

**Pick a climbing job for the Print beat** so the curve actually moves on camera (the sim only
fails prints that genuinely should). Verified climbers: PETG overhang at ~30 °C / 65 % RH
(0.55 to 0.70), or quick-load Benchy + PETG with the room overridden to 30 °C / 68 %
(0.68 to 0.81). Avoid an easy default job; it sits flat and tells no story.

---

## VO script — one line per beat (read these, paraphrase to taste)

The minimal-voice plan: voice the two camera end-caps, then drop **one spoken
sentence per screen beat** over the Cap/Playwright capture. This carries the
story without full narration — and it maps 1:1 onto the beats `scripts/capture.py`
already drives, so you can record a clip per line and cut them together.

| Beat (capture.py) | Line to speak |
|---|---|
| **Open** *(camera, ~15–20s)* | "My grandfather spent a lifetime building skill that lived in his hands — then Alzheimer's took him, the shop was sold, and it all just went. This is my attempt at the opposite." |
| **Build / LOAD** (`beat_load`) | "I give it the part, the material, and the room — it figures out what kind of part this is on its own." |
| **Slice — the read** (`beat_slice`) | "It tells me where this print will fail before the nozzle moves, and points at the prior job it's reasoning from." |
| **Second opinion** (`beat_second_opinion`) | "A separate reviewer grades the plan and can hold the print — it never marks its own homework." |
| **Print — the climax** (`beat_print_loop`) | "Every job makes the next one better. That's the whole point." |
| **Review** (`beat_review`) | "The knowledge compounds instead of disappearing." |
| **Optional: one real print** | "Same loop, a real print — the settings and the learning are real; only the auto demo uses a stand-in." |
| **Close** *(camera, ~15s)* | "The shop is gone — but the kind of knowledge that lived in it doesn't have to disappear anymore." |

These are intentionally spare. Spoken plainly beats performed, and one true
sentence per beat reads better to judges than a wall-to-wall script. Use a
**climbing job** for the Print beat (see below) so the line "every job makes the
next one better" is backed by the curve actually moving on screen.

---


- **Emphasize:** the compounding (make it the climax), the honesty split (O'Brien proposes,
  Spine disposes, La Forge grades), the real data (your own prints), and the "no close
  precedent" moment where it declines to bluff.
- **Avoid:** rushing the open, narrating every click, theatrical lines, and claiming
  fine-tuning, multi-node execution, or real physics as done. Name those as next, briefly, if
  at all.

---

## Capture

Mechanics, preflight, and the automated/cued capture commands are in **RUNBOOK §4**. Reset the
curve first (the **RESET** button on any tab, or `git checkout -- data/lessons.jsonl && rm -f
data/policy.json`), then record. Beats are independent clips, so you can re-record one without
redoing the whole take.

For a clean screen track: **install the Chrome app Gradio offers** at node.microfactory.space
(chromeless PWA window, no tabs or URL bar), and cut the screen capture against a **Desktop Background in Cap
Studio exported at 1080p** so it matches the camera footage (RUNBOOK §4 has the detail).
