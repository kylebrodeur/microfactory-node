# Submission Checklist — status audit (2026-06-13, endgame Day 9)

Run-through of `docs/writeup/03-SUBMISSION-CHECKLIST.md` against current state.
✅ = done, ◐ = partial/needs Kyle, ❌ = not done, ⚠ = unresolved.

---

## ⚡ URGENT

| # | Item | Status |
|---|------|--------|
| 1 | Member of `build-small-hackathon` org | ✅ `hf auth whoami` confirms |

## The Space

| # | Item | Status |
|---|------|--------|
| 2 | Space in `build-small-hackathon` org | ✅ Kyle handles deploys |
| 3 | Gradio app, sdk 6.17.3 | ✅ |
| 4 | Model ≤32B params | ✅ gemma4 e4b/e2b |
| 5 | Cold start verified (incognito) | ◐ Kyle to verify after next push |
| 6 | Backend banner honest | ◐ verify on live Space |
| 7 | README frontmatter tags | ✅ build-small-hackathon, backyard-ai, off-the-grid, llama-champion, sharing-is-caring, off-brand |
| 8 | `field-notes` tag | ❌ needs Field Notes published first |
| 9 | `tiny-titan` tag | ⚠ unresolved eligibility |
| 10 | README short write-up | ✅ |
| 11 | README: link to social post | ❌ **MISSING** |
| 12 | README: link to demo video | ❌ **MISSING** |
| 13 | Runtime state clean | ◐ verify ledger on Space after push |

## The video

| # | Item | Status |
|---|------|--------|
| 14 | Shows app working (Beat 3) | ◐ recordings exist — Kyle to review + pick final |
| 15 | Tight ~2–3 min | ◐ 87s take at D:\workspace\recordings |
| 16 | Beat 3 real model output | ◐ captured in recordings |
| 17 | Novel-case beat included | ◐ captured in recordings |
| 18 | Ledger growth shown | ◐ captured in recordings |
| 19 | No "[fallback]" in live beats | ◐ verify in recording review |
| 20 | Frontier named as NEXT | ✅ in writeup |
| 21 | Uploaded + linked in README | ❌ needs Kyle to pick final + provide URL |

## The writeup

| # | Item | Status |
|---|------|--------|
| 22 | Voice pass done | ✅ `01-SUBMISSION.md` written in Kyle's voice |
| 23 | ⚠ marks resolved | ✅ calibration story added, Space inference split stated |
| 24 | Claim audit re-run | ✅ built vs frontier table respected |
| 25 | Published as Field Notes | ◐ `06-FIELD-NOTES.md` written, needs org blog publish |

## The social post

| # | Item | Status |
|---|------|--------|
| 26 | Posted, public | ❌ not posted |
| 27 | Linked from Space README | ❌ **MISSING** |
| 28 | Variant-B quote genuine | ◐ verify against real model output |

## Badges

| # | Badge | Status |
|---|-------|--------|
| 29 | Off the Grid | ◐ video needs to show local/offline operation — verify in recording review |
| 30 | Llama Champion | ✅ in writeup (Ollama = llama.cpp) |
| 31 | Sharing is Caring | ✅ dataset pushed + linked in README |
| 32 | Field Notes | ◐ written, needs org blog publish |
| 33 | Off-Brand | ◐ needs CSS screenshot verification |
| 34 | Storytelling | ✅ NOT a badge (judging principle) — correct |
| 35 | Tiny Titan | ⚠ eligibility unresolved — ask org |
| 36 | Well-Tuned | ✅ NOT claimed — correct |

## Submission mechanism

| # | Item | Status |
|---|------|--------|
| 37 | Space in org with README tags + links | ◐ missing social + video links |
| 38 | Submit June 14 | ◐ pending |
| 39 | Confirmation screenshot | ❌ pending |

## Post-submit

| # | Item | Status |
|---|------|--------|
| 40 | Tag commit `submitted-build-small` | ❌ pending |
| 41 | Stop pushing after submit | ❌ pending |

---

## Summary: what's NOT done

### Kyle must do (can't delegate)
- **Record the demo video** (items 14–21) — the whole video section
- **Publish social post** (item 26) — pick variant, post, get the URL
- **Publish Field Notes on org blog** (items 25, 32) — copy from `06-FIELD-NOTES.md`
- **Verify Off-Brand CSS** (item 33) — open Space, check Astrometrics, screenshot
- **Ask org about Tiny Titan** (item 35) — E-model eligibility
- **Verify cold start** (item 5) — incognito window, Space loads + fallback works

### Agent can do now
- **Add social post + video links to README** (items 11, 12, 27) — needs the URLs from Kyle
- **Add `field-notes` tag** (item 8) — after Field Notes is published

### After recording
- **Upload video, get URL, add to README** (item 21)
- **Final submission June 14** (items 37–41)
