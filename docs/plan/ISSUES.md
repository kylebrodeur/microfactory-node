# ISSUES.md — Open items & decisions needed

Created 2026-06-12, updated 2026-06-13 (Day 9). Items here are
either blocked on Kyle's action, unresolved, or deferred post-submission.

**Day-9 (cont.) landed:** ZeroGPU graceful fallback (`@spaces.GPU` on inference only,
not `build_job`) — fixes the "Error" in the first recording; UI widened to 1600px;
renamed to **Microfactory Node: 3D Printer** (personas: O'Brien proposes, La Forge
inspects); in-UI **↺ RESET TO BASELINE**; **all runs** now log to the field-log dataset;
RUNBOOK refreshed + **field-log setup** documented (dataset + `HF_TOKEN` secret + prompt);
RUNBOOK rewritten clean (run → use/tour → deploy → record); history split to
`reference/RUNBOOK-FINDINGS.md`; the judge tour folded into RUNBOOK §2 (JUDGE-GUIDE removed);
fixed dangling doc links (DEPLOYMENT moved
to `reference/`, deleted `docs/README.md` references). **Decided:** upgrade HF Pro (quota);
keep ZeroGPU now, Modal inference backend is a post-submission option.

---

## ⚡ Blockers for submission (Day 9–10)

### 1. Restructured app on Space ✅ Kyle handles
**Source:** RUNBOOK.md "Pre-record checklist" item #1.
Kyle pushes on each update. Space is 🟢 RUNNING on ZeroGPU.
**Action:** Push after any code change; factory reboot; smoke-test before recording.

### 2. Writeup voice pass ✅ DONE 6/12
`01-SUBMISSION.md` written in Kyle's first-person voice, ~1,300 words.
Calibration honesty story + QA Inspector paragraph added. Both ⚠ marks resolved.

### 3. Sharing-is-Caring badge ✅ DONE 6/12
Trace pushed to [`kylebrodeur/chief-engineer-ledger`](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger).
Tag added to README frontmatter.

**Day-10:** now **three** open artifacts — the lesson ledger, the live field log
(`build-small-hackathon/chief-engineer-field-log`), and the new **deliberation traces**
(`kylebrodeur/chief-engineer-deliberation`): the turn-by-turn argument between the personas,
both a static export (`make deliberation`) and logged **live on every run** via
`core/deliberation_log.py` (same `HF_TOKEN` gate as the field log). Pending Kyle: set the Space
secret (one token powers both live logs) + seed/upload the deliberation export. See RUNBOOK §3.

### 4. Recording pipeline ✅ DONE 6/13
`scripts/record.py` — fully automated: preflight → Chrome CDP → pre-warm →
Cap 60fps → 8-beat Playwright drive → stop → export to `D:\workspace\recordings`.
Multiple takes produced. Kyle to review and pick final.

### 5. Field Notes post not published
**Source:** Badge tracker, 05-ENDGAME.md Day 9 task #3.
Draft at `docs/writeup/06-FIELD-NOTES.md`. Needs voice-pass + publish on the
org blog (required for badge + discoverability).

### 6. Off-Brand badge: CSS not verified with screenshot
**Source:** Badge tracker.
Astrometrics CSS is started but needs visual verification + a screenshot for
the badge claim.

### 7. Social post not published
**Source:** 03-SUBMISSION-CHECKLIST.md.
3 variants drafted at `docs/writeup/04-SOCIAL-POST.md`. Needs Kyle to pick one,
post, and provide the URL for README linking.

### 8. README placeholder links
**Source:** SUBMISSION-AUDIT.md #11, #12.
Video URL + social post URL are MISSING from README. Agent can fill once
Kyle provides the URLs.

---

## ⚠ Unresolved decisions

### 9. Tiny Titan eligibility
**Source:** Badge tracker, RUNBOOK findings log.
The $1.5k special award caps at 32B TOTAL params. e2b=5.1B raw / e4b=8.0B raw
are under the cap, but the field guide may count effective params (~2B/~4B).
**Unresolved.** Ask in org discussions before tagging.

### 10. Model choice for recording
**Source:** RUNBOOK findings log.
Decision recorded as "record on e4b" (Kyle's pick, 6/11). Space runs
`google/gemma-4-E4B-it` on ZeroGPU. Confirmed.

---

---

## 🎬 Demo video — recorded beats (2026-06-14)

### 12. Raw `.cap` beat recordings captured
**Status:** ✅ Captured; raw projects in `recordings/raw/`.
- `load.cap` — LOAD tab, Benchy, orbit, RANDOMIZE demo, click to SLICE.
- `slice.cap` — SLICE tab, O'Brien's read renders.
- `second.cap` — Second Opinion tab, La Forge dispute.
- `climb.cap` — Climbing PETG job + Print loop + Review.

Exported MP4s and trimmed clips live in `recordings/beats/` and `recordings/beats/trimmed/`.
Fast-cut preview with placeholder VO/camera: `recordings/output/microfactory-node-demo-fast-cut-preview.mp4` (~4:30).

### 13. Real VO + camera end-caps still needed
**Status:** ⏳ Waiting on Kyle.
- Record camera `open.mp4` and `close.mp4` with natural camera audio.
- Record one WAV per beat from `docs/writeup/02-VIDEO.md`.
- Drop into `recordings/vo/` and `recordings/camera/`, then re-run:
  ```bash
  uv run python scripts/assemble-video.py recordings/manifest.json
  ```

### 14. Recording quality checklist for re-takes
- Close all apps/windows; silence notifications.
- Chrome app window maximized on primary display.
- Reset demo curve first: `git checkout -- data/lessons.jsonl && rm -f data/policy.json`.
- Run `./record-beat.sh <beat>` per beat; review raw `.cap` in Cap Studio.

---

## 🎨 UI critiques (from Kyle)

### 15. Layer slicer slider — too long / horizontal
**Action:** Make it vertical and place it next to the slicer preview.

### 16. Slicer + virtual print sliders inconsistent
**Action:** Use the same slider style/alignment for both; they currently look mismatched.

### 17. Remove pre-Read status copy
**Action:** Drop the "live · google/gemma-4-E4B-it (transformers on ZeroGPU) (loads on first analyze) · deterministic fallback" copy that appears before The Read panel.

### 18. The Read / Second Opinion panels need more visibility
**Action:** Move them up the page so a user cannot miss them.

### 19. LOAD tab should highlight models/adapters
**Action:** In the LOAD beat, surface the local model/adapter info visibly so the viewer understands what is running.

---

## 📡 Deferred designs (not blockers)

### 12. Field logging ✅ BUILT 6/12
`core/field_log.py` built + wired into `app.py`. Dataset repo created.

### 13. Next Modal data-acquisition run
**Source:** RESEARCH-NEEDS.md kickoff prompt. Post-submission item.

### 14. MCP-hackathon Modal code / knowledge sources / sensors / machine control
**Source:** TODO.md follow-ups. All post-submission.
