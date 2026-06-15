# Microfactory demo — editing notes

> See **`docs/writeup/02-VIDEO.md`** for the full beat sheet, shot list, and VO lines.  
> See **`docs/RUNBOOK.md` §4** for the original recording mechanics.

This folder holds the post-production pipeline. The goal is a **~2 minute** demo built from short screen-capture beats, your camera end-caps, and your VO line per beat.

## File naming convention

Recordings are organized by **source type**, not by story order.

```
recordings/
  camera/
    open.mp4      # you, face to lens (~15–20 s)
    close.mp4     # you, face to lens (~15 s)
  beats/          # exported from Cap Studio
    load.mp4      # LOAD tab: part + material + room
    slice.mp4     # SLICE tab: O'Brien's precedent read + failure flag
    second.mp4    # Second Opinion tab: La Forge dispute
    scrub.mp4     # layer scrubber
    placement.mp4 # placement override
    print.mp4     # PRINT tab only
    review.mp4    # REVIEW tab only
    climb.mp4     # PRINT + REVIEW combined (legacy one-take)
  beats/trimmed/  # trimmed / Cap-polished versions used by the manifest
  vo/             # one WAV per beat, recorded by you
    load.wav
    slice.wav
    second.wav
    scrub.wav
    placement.wav
    print.wav
    review.wav
    climb.wav
  output/         # final renders go here
```

## Beats to record (all of them)

Record every beat below. No optionals: each one is a source clip the edit can pull from.

| # | Beat | File | Cap Studio treatment | Why record it |
|---|------|------|----------------------|---------------|
| 1 | **load** | `beats/load.mp4` | **RAW export OK** — trimming only | Establishes the job: part, material, room. |
| 2 | **slice** | `beats/slice.mp4` | **POLISH** — auto-zoom on THE READ panel + click indicator on SLICE | The judged moment: O'Brien reads precedent before the nozzle moves. |
| 3 | **second** | `beats/second.mp4` | **POLISH** — auto-zoom on Second Opinion card + toggle click | The integrity moment: La Forge holds the print. |
| 4 | **scrub** | `beats/scrub.mp4` | **RAW export OK** | Cutaway: layer-by-layer cross-section. |
| 5 | **placement** | `beats/placement.mp4` | **RAW export OK** | Cutaway: environment/position override. |
| 6 | **print** | `beats/print.mp4` | **RAW export OK** | The print simulation running, curve beginning. |
| 7 | **review** | `beats/review.mp4` | **RAW export OK** | Ledger growing, run verdict. |
| 8 | **climb** | `beats/climb.mp4` | **POLISH** — auto-zoom on quality curve + La Forge grades | The climax: quality climbs fail→clean in one take. |

**Cap Studio treatment rule of thumb:** polish the three beats that carry the story (slice, second, climb). Everything else is fine as a clean raw export with a top/tail trim.

## Story order (fast cut)

The final edit follows the VO script in `docs/writeup/02-VIDEO.md`:

| Story order | File(s) | VO line (from `02-VIDEO.md`) |
|---|---|---|
| Open | `camera/open.mp4` | *“My grandfather spent a lifetime building skill…”* |
| Build / LOAD | `beats/load.mp4` + `vo/load.wav` | *“I give it the part, the material, and the room…”* |
| Slice — the read | `beats/slice.mp4` + `vo/slice.wav` | *“It tells me where this print will fail before the nozzle moves…”* |
| Second opinion | `beats/second.mp4` + `vo/second.wav` | *“A separate reviewer grades the plan and can hold the print…”* |
| Layer scrub (optional cutaway) | `beats/scrub.mp4` + `vo/scrub.wav` or silence | — |
| Placement override (optional cutaway) | `beats/placement.mp4` + `vo/placement.wav` or silence | — |
| Print | `beats/print.mp4` + `vo/print.wav` | *“Every job makes the next one better…”* |
| Review | `beats/review.mp4` + `vo/review.wav` | *“The knowledge compounds instead of disappearing.”* |
| Print+Review combined | `beats/climb.mp4` + `vo/climb.wav` / `vo/review.wav` | Use if you want the curve and verdict in one take. |
| Close | `camera/close.mp4` | *“The shop is gone — but the kind of knowledge…”* |

> Use either the separate `print` + `review` beats **or** the combined `climb` beat for the climax, not both. The combined `climb` beat is the legacy one-take path; the separate beats give the editor more control.

## Fast cut (do this first)

No Premiere, no Cap Studio polish. Record, export, add VO + captions, assemble with ffmpeg.

### 1. Reset the demo curve

The Print curve must actually climb on camera. From `chief-engineer/`:

```bash
git checkout -- data/lessons.jsonl && rm -f data/policy.json
```

(See `docs/RUNBOOK.md` §4.)

### 2. Record every beat

```bash
./scripts/record-beat.sh load
./scripts/record-beat.sh slice
./scripts/record-beat.sh second
./scripts/record-beat.sh scrub
./scripts/record-beat.sh placement
./scripts/record-beat.sh print
./scripts/record-beat.sh review
./scripts/record-beat.sh climb   # combined Print+Review; optional if you recorded print+review separately
```

### 3. Export each `.cap` project to MP4

```bash
./scripts/export-beat.sh /path/to/load.cap recordings/beats/load.mp4
./scripts/export-beat.sh /path/to/slice.cap recordings/beats/slice.mp4
./scripts/export-beat.sh /path/to/second.cap recordings/beats/second.mp4
./scripts/export-beat.sh /path/to/scrub.cap recordings/beats/scrub.mp4
./scripts/export-beat.sh /path/to/placement.cap recordings/beats/placement.mp4
./scripts/export-beat.sh /path/to/print.cap recordings/beats/print.mp4
./scripts/export-beat.sh /path/to/review.cap recordings/beats/review.mp4
./scripts/export-beat.sh /path/to/climb.cap recordings/beats/climb.mp4
```

### 4. Polish in Cap Studio (only the starred beats)

Open only these three `.cap` projects in Cap Desktop Studio:
- **slice** — add auto-zoom on THE READ panel and a click indicator on the SLICE button.
- **second** — add auto-zoom on the Second Opinion card and a click indicator on the toggle.
- **climb** — add auto-zoom on the quality curve and La Forge's per-run grades.

Export the polished versions as `beats/trimmed/<beat>.mp4`. All other beats can be exported raw from Cap as `beats/<beat>.mp4` and used directly.

### 5. Add your camera + VO files

Place these under `recordings/`:

```
recordings/
  camera/open.mp4
  camera/close.mp4
  vo/load.wav
  vo/slice.wav
  vo/second.wav
  vo/scrub.wav
  vo/placement.wav
  vo/print.wav
  vo/review.wav
  vo/climb.wav
```

### 6. Build the manifest

```bash
cp recordings/manifest.example.json recordings/manifest.json
# edit recordings/manifest.json to match your actual filenames and polish choices
```

### 7. Assemble

```bash
uv run python scripts/assemble-video.py recordings/manifest.json
```

Output: `recordings/output/microfactory-node-demo.mp4`

### Recording-quality checklist for re-takes

Before each recording pass, verify:

- [ ] Close all other apps/windows; silence notifications.
- [ ] Chrome app window is maximized and on the primary display.
- [ ] No WSL terminal or other window overlaps the capture area.
- [ ] Reset the demo curve so the Print curve climbs: `git checkout -- data/lessons.jsonl && rm -f data/policy.json`.
- [ ] Let the Space fully load before starting the beat driver.
- [ ] Record in a quiet room; camera open/close clips keep their natural audio.
- [ ] Use the same screen resolution/orientation for every beat.

### Known UI polish items (impact demo framing)

- The layer slicer slider is currently horizontal and long; it should be vertical and next to the slicer preview.
- The slicer slider and the virtual-print slider should share the same style/alignment.
- The status copy before The Read panel ("live · google/gemma-4-E4B-it…") should be removed.
- The Read and Second Opinion panels should move higher on the page so they are immediately visible.
- LOAD should surface the local model / adapter info so the viewer sees what is running.

See `docs/plan/ISSUES.md` #15–19 for full tracking.

## Polished cut

Polish only the three beats that carry the story. In Cap Desktop Studio:

1. Re-record just those beats if needed: `./scripts/record-beat.sh slice`, `./scripts/record-beat.sh second`, `./scripts/record-beat.sh climb`.
2. Apply auto-zoom + click indicators.
3. Export the polished beat MP4 to `recordings/beats/trimmed/<beat>.mp4`.
4. Swap it into `recordings/manifest.json` and re-run `assemble-video.py`.

This keeps Cap Studio work minimal: three beats, not eight.

## Caption safe-zone rule

The assembly script places captions at the bottom of the frame with a semi-transparent black box. If you edit in Cap Studio, keep captions in the bottom 100 px and never over THE READ panel, Second Opinion card, settings/g-code, or the climbing curve.
