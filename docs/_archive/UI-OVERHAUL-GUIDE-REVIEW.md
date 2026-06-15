# How the UI Overhaul Guide Worked (a builder's retrospective)

Date: 2026-06-14. Author: implementing agent. Subject: the `walkthrough/` guide Kyle
produced (a narrated tab-by-tab UI review, 54 numbered items with a screenshot each,
plus Global Rules, resolved Contradictions, and Open Questions).

This is an honest retrospective on the guide *as a spec to build from*: what made it
unusually effective, where it cost time or created ambiguity, and concrete changes that
would make the next one even better. It is feedback on the format, not the taste — the
design calls themselves were sound.

## What the format is

A spoken UI walkthrough, transcribed and structured into: one item per change request,
each with `id · timestamp · what you said · decision`, the screen at that moment, grouped
by tab. Cross-tab rules pulled up into **Global Rules**. Self-corrections reconciled under
**Contradictions — resolved to your final word**. Genuinely undecided forks parked in
**Open Questions**.

## What worked unusually well

1. **Decisions, not just observations.** Almost every item ended in a `Decision:` line. That
   is the single biggest thing. Most design feedback is a list of reactions; this was a list
   of resolved instructions. I could act on ~45 of 54 items without guessing.
2. **Contradictions were pre-reconciled to a final word.** The two places you changed your
   mind mid-walkthrough (the warm-up button placement, the duplicate header block) were
   collapsed into one stated final decision with the reasoning. Without that I would have
   implemented the first instinct and then had to redo it. This alone probably saved a full
   round-trip.
3. **Open Questions were named and quarantined.** Instead of burying three genuine forks
   inside 54 items, you flagged them explicitly and said "needs your decision." That let me
   resolve exactly those three up front (one AskUserQuestion call) and then run the rest
   straight through. Knowing *what was undecided* was as valuable as knowing what was decided.
4. **Global Rules separated from per-item asks.** Pulling "no emojis," "primary top-right +
   persistent Reset," "one custom loader," "contained blocks," "mirrored header/footer" out
   of the item list meant I built them once as system-level changes (an icon set, a loader
   helper, an action-bar helper, CSS) instead of re-deriving them 54 times. The structure
   matched the shape of the implementation.
5. **Stable item ids.** `studio-06`, `build-10`, `print-11` gave both of us a shared address
   space. The changelog maps cleanly back to your ids, so review is "is print-08 done?" not
   "which thing did you mean?"
6. **Screenshots anchored each ask to a real screen.** Even reading the markdown without
   opening the images, the per-item screen reference made the location unambiguous.

## Where it cost time or created ambiguity

1. **A few items were observations dressed as decisions.** `studio-17` ("check the field
   lock") and parts of `print-09`/`print-14` ("not sure what the solution is") are real, but
   they are open questions living in the item list rather than in the Open Questions section.
   They read as actionable and then aren't. Promoting "I'm not sure" items into Open Questions
   would keep the item list 100% executable.
2. **Vocabulary drift between the guide and the code.** The guide says "Slice/Print,"
   "Engineer's Read," "Get Second Opinion," "Job Log"; the code had "Build," "the engineer's
   read," "second opinion," and no "Job Log" component. Most mapped cleanly, but `studio-01`
   (rename to Slice/Print) is genuinely ambiguous: rename the *tab*, or just the step copy?
   Renaming the tab ripples into the RUNBOOK, the video, and a deploy gate. One line — "rename
   the labels, not the tab" or vice versa — would have removed a judgement call on something
   with cross-file blast radius.
3. **"Group these together" without a target size or order.** Several items ("group the
   slicer + slider + copy," "stack the three buttons") were clear on *what* to group but not
   on proportions or priority. I chose ratios (e.g. slice 3 / slider 1 / preview 3); a rough
   "left half / right half" or "1:1" note would remove the guess.
4. **A couple of asks need design, not just placement.** `build-08` (preload slicer images)
   and `review-04` (show the printable config) are features, not layout tweaks. Mixed into a
   layout-review list, they look small and are not. Tagging items as `layout` vs `behavior` vs
   `new-feature` would set effort expectations and let me sequence the cheap wins first.
5. **No priority or "must-ship vs nice-to-have."** With a same-day deadline, knowing which 10
   items are load-bearing for the demo vs which are polish would let me guarantee the critical
   ones and defer the rest cleanly, instead of treating all 54 as equal.

## Concrete suggestions for the next guide

- Keep the exact structure (it is good): id · what you said · decision · screen, grouped by
  tab, with Global Rules / Contradictions / Open Questions as separate sections.
- Move every "I'm not sure" out of the item list and into Open Questions, even one-liners.
- Add a one-word **type tag** per item: `layout` / `copy` / `behavior` / `new-feature`.
- Add a **priority tag** for items that must ship for the demo (`P0`) vs polish (`P2`).
- When an ask touches a name a judge/doc/script will also see (tab titles, button labels),
  say explicitly whether to rename the user-facing label only or the underlying concept too.
- For grouping items, give a rough proportion or order ("1:1", "stack in this order").
- Optionally, a tiny **acceptance line** per item ("done when X is top-right and Reset is
  visible") — turns review into a checklist and removes interpretation on "done?".

## Net

This was one of the most directly buildable design specs I have worked from. The decision
discipline and the explicit handling of contradictions and open questions are the parts to
keep. The improvements are all about removing the last ~10% of interpretation: separate the
truly-undecided from the decided, tag effort and priority, and pin down names that cross file
boundaries. With those, a guide like this could be executed end to end with zero clarifying
questions.
