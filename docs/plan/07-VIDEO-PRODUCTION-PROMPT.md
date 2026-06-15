# 07 — Video production: local-agent prompt

**What this is.** A self-contained brief to hand a **local agent on Kyle's WSL/Windows
machine** (where Cap CLI, Chrome, Cap Studio, and Premiere all live). The agent drives the
existing capture tooling + Cap Studio to assemble the submission video from Kyle's two
voice/camera recordings plus automated screen capture of the live Space.

**Why local.** This sandbox has no Cap, no Chrome-with-CDP, no Premiere, and no access to
Kyle's recorded files. Everything below runs on Kyle's machine. The Claude-on-the-web session
authored this brief and the on-screen scripts; the local agent executes.

---

## Paste-to-the-local-agent prompt

> You are producing the ~2–3 min submission video for **Microfactory Node: 3D Printer**
> (Build Small hackathon, Backyard AI track). It is a **two-track cut**: a camera end-cap
> story + a screen-capture tour of the live Space, with one spoken line per beat and burned-in
> captions. Target **1.5 hours**. Work on branch `claude/microfactory-gradio-hackathon-9e81fh`
> in `microfactory-lab/chief-engineer/`. **Do a `git pull` first.**
>
> ### Inputs Kyle provides (confirm paths before starting)
> 1. **`story-open.*`** — ~15 s, iPhone + AirPods, Kyle on camera telling the grandfather story
>    (the open; optionally a second clip for the close).
> 2. **`vo-notes.*`** — AirPods voice-note(s): Kyle reading the per-beat narration. **This audio
>    is the VO source of truth** — use his real voice as the narration track, do not synthesize.
>
> ### Assets already in the repo (after pull)
> - `assets/screenshots/hero-build.png`, `second-opinion.png`, `print-loop.png` (1500px/2×) —
>   for thumbnails/fallback stills if a beat needs a hold frame.
> - `docs/writeup/02-VIDEO.md` — the **two-track plan + the canonical VO line per beat**
>   (the "VO script" table). Treat these as the script Kyle read; reconcile to his actual
>   recording where they differ.
> - `scripts/record.py` (`MANUAL_BEATS` has the same lines as `say:` fields) and
>   `scripts/capture.py` (the beat drivers). `docs/RUNBOOK.md` §4 = capture mechanics.
>
> ### Toolchain (all local)
> - `source ~/projects/cap-cli-skill/setup.sh` → defines `cap()` (start/stop/export).
> - `uv run python -m scripts.record --mode studio --beat climb` → drives Chrome over CDP
>   through the climbing-job beats against the live Space, starts a Cap recording, and leaves a
>   **raw `.cap` project** for Cap Studio (no auto-export). Use `--beat all` for the full tour,
>   `--beat <name>` for re-takes. `make record-check` first (preflight gates).
> - **Cap Studio**: auto-zoom on clicks, click/cursor indicators, frame holds, speed ramps.
> - **Premiere Pro**: escape hatch only (a fussy cross-dissolve or audio duck). Don't reach for
>   it for plain cuts + overlays.
>
> ### Production sequence
> 1. **Prep.** `git pull`; `source ~/projects/cap-cli-skill/setup.sh`; `make record-check`.
>    Confirm the live Space is warm (HF Pro → real Gemma reasoning on screen, not `[fallback]`).
>    **Reset the demo curve** so compounding is real on camera: click ↺ RESET on the Space, or
>    `git checkout -- data/lessons.jsonl && rm -f data/policy.json`.
> 2. **Transcribe + align.** Run STT (e.g. whisper) on `vo-notes.*` → a timestamped transcript.
>    Segment it into the beats below; produce (a) a **caption track** (SRT/burn-in text) and
>    (b) the **VO clip per beat** with its true duration. Where Kyle's wording drifts from the
>    `02-VIDEO.md` table, follow **Kyle's audio** and update the caption text to match what he said.
> 3. **Capture screen.** `uv run python -m scripts.record --mode studio --beat climb` (then
>    `--beat second`, `--beat scrub`, `--beat placement` as needed for coverage). Use a **climbing
>    job** (PETG overhang @ ~30 °C/65 %, or Benchy+PETG @ 30 °C/68 %) so the Print curve actually
>    moves. Stop Cap (`cap record stop`) → open the raw project in Cap Studio.
> 4. **Cap Studio edit.** Apply **auto-zoom** on the load-bearing moments (THE READ, the Second
>    Opinion card, the climbing curve), add **click indicators**, and **retime each screen beat to
>    its VO length** with frame holds / speed ramps (hold on a still where Kyle's line runs long;
>    trim dead air where it runs short). The screenshots can serve as hold frames if a live frame
>    is noisy.
> 5. **Assemble the cut.** Sequence: **story open (camera)** → the beats in order (screen + Kyle's
>    VO + burned captions) → **close (camera)**. One line per beat; let the open breathe (don't
>    rush the grief — that beat is the whole submission).
> 6. **Captions — placement-aware, not always-on.** Kyle's VO carries the narration, so captions
>    are a readability aid, not the primary channel. Rules:
>    - **Don't cover the load-bearing UI.** Never let a caption sit over THE READ panel, the Second
>      Opinion card, the proposed-settings/g-code, or the climbing curve. Those panels *are* the demo.
>    - **Reserve a safe lane.** Put captions in the bottom safe-zone where the app has dead margin,
>      or add a thin **letterbox band** (small black bar) under the capture and place the caption there
>      so it never overlaps content. Keep a single short line at a time.
>    - **Be selective.** Caption the camera story open/close lightly or not at all (his face + voice
>      carry it). On screen beats, caption the spoken line only while it's being said, then clear it —
>      conditional per beat, not a persistent strip.
>    - **Watch auto-zoom.** Cap auto-zoom reframes the shot; pin captions to the output frame's safe
>      area (not to a UI element) so a zoom never pushes text over the panel.
>    - Burn-in is fine once placement is solved (survives re-upload); if a clean safe lane isn't
>      possible on a given beat, prefer a soft/sidecar caption or skip the caption for that beat
>      rather than obscure the interface.
> 7. **Export.** 1080p mp4, match the camera end-cap resolution (Cap export ~`1707x1067`/1080p,
>    `maximum` quality, 60 fps). Name it `microfactory-node-demo.mp4`.
> 8. **Screenshots → HF.** The three PNGs in `assets/screenshots/` ship to the Space via
>    `make deploy` (assets/ is in the upload). After the next deploy, confirm they render in the
>    Space README. (They are Kyle's to keep; they already live in the repo — just don't drop them.)
> 9. **Wire the video URL.** After Kyle uploads the mp4 (YouTube/HF), paste the URL into the
>    README **Links → Demo video** placeholder and redeploy.
>
> ### Beats + lines (read from `02-VIDEO.md`; Kyle's audio wins on wording)
> | Beat | capture.py | Spoken line (caption) |
> |---|---|---|
> | Open (camera) | — | grandfather story → "this is my attempt at the opposite" |
> | Build / LOAD | `beat_load` | "I give it the part, the material, and the room — it figures out what kind of part this is on its own." |
> | Slice — the read | `beat_slice` | "It tells me where this print will fail before the nozzle moves, and points at the prior job it's reasoning from." |
> | Second opinion | `beat_second_opinion` | "A separate reviewer grades the plan and can hold the print — it never marks its own homework." |
> | Print — climax | `beat_print_loop` | "Every job makes the next one better. That's the whole point." |
> | Review | `beat_review` | "The knowledge compounds instead of disappearing." |
> | Close (camera) | — | "The shop is gone — but the kind of knowledge that lived in it doesn't have to disappear anymore." |
>
> ### Acceptance checklist
> - [ ] Story open is Kyle's real voice/face; not rushed.
> - [ ] Every screen beat has its VO line; captions (where used) sit in a safe lane / letterbox band
>       and never cover THE READ, the Second Opinion card, settings/g-code, or the curve.
> - [ ] Print beat shows the curve actually climbing (climbing job, curve reset).
> - [ ] Reasoning on screen is real Gemma (no `[fallback]`), or the fallback banner is honestly shown.
> - [ ] No overclaiming: fine-tune / multi-node / real physics named as next, not done.
> - [ ] Export is 1080p mp4 matching the camera footage; total 2–3 min.
> - [ ] Screenshots still present in `assets/screenshots/`; README video URL wired after upload.

---

## Notes for Kyle

- **Honesty guardrail:** keep the "Simulated (one boundary) / Frontier (named, not faked)" framing
  from `01-SUBMISSION.md` — the video should never imply the sim is real physics or that the
  fine-tune/multi-node is shipped.
- **If a beat's live reasoning is weak on the take,** re-run just that beat (`--beat second`,
  `--beat climb`, …) rather than redoing the whole tour; beats are independent clips.
- **Premiere** is only worth opening if Cap Studio can't do a specific audio duck under the VO or a
  clean cross-dissolve between the camera and screen tracks. For straight cuts + overlays, Cap is enough.
