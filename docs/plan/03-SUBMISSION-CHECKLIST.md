# 03 — Final Submission Checklist

The mechanical list. Work it top to bottom on Day 10 (June 14). Every box is
binary; "almost" is unchecked. Field-guide requirements marked **[REQ]**.

## ⚡ URGENT — do first

- [ ] **CONFIRM you are a member of the `build-small-hackathon` org.**
      Registration CLOSED June 3, 2026 (registration Space). If you're in, the
      submission path is open; if not, escalate immediately. (Verified 6/10.)

## The Space

- [ x] **[REQ]** Space deployed **inside the `build-small-hackathon` org** (not personal namespace)
- [ x] **[REQ]** It's a Gradio app (it is; sdk pinned 6.17.3 in README frontmatter)
- [ x] **[REQ]** Model ≤32B params (gemma4 e4b/e2b — trivially yes; state it)
- [ ] Cold start verified **today**: open in incognito, no cache — cockpit loads,
      recommendation renders on the fallback path, precedent panel + ledger work
- [ x] Backend banner honest on the Space ("🟡 offline fallback" if no live model there)
- [x ] README frontmatter tags (verified 6/10 from real submissions + an org-wide
      crawl; the field guide page itself couldn't be read verbatim — spot-check
      one current submission before pushing): hackathon `build-small-hackathon`,
      track `backyard-ai`; badges from: `off-the-grid`, `llama-champion`,
      `sharing-is-caring`, `field-notes`, `off-brand` (+ `tiny-titan` ONLY if
      the E-model ruling comes back favorable — see Badges below)
- [x ] README: short write-up of idea + tech present (frontmatter `short_description`
      + body — already drafted, verify it reads)
- [ ] README: **[REQ]** link to the social post
- [ ] README: link to the demo video
- [x ] Runtime state clean: no junk lessons in the deployed ledger (seeds only)

## The video

- [ ] **[REQ]** Shows the app actually working (Beat 3 = real cockpit run)
- [ ] Tight (~2–3 min). No official length limit found (searched 6/10: the field
      guide only asks for "a demo video") — brevity is still strategy
- [ ] Beat 3 reasoning text is REAL model output (or §G1.3 fallback framing,
      honestly presented — never a faked "model" quote)
- [ ] Novel-case "no close precedent" beat included
- [ ] Ledger growth shown (seed → earned)
- [ ] No "[fallback]" string visible in any live-model beat
- [ ] Frontier items (fine-tuning, multi-node, physics) named as NEXT, not shown as built
- [ ] Uploaded where the submission form wants it + linked in README

## The writeup

- [ ] Voice pass done on `01-SUBMISSION-DRAFT.md`; ≤ ~1,500 words
- [ ] Both ⚠ marks in the draft resolved against the final artifacts
- [ ] Claim audit re-run after edits (built vs frontier table respected)
- [ ] Published as a Field Notes post on the org blog (badge + discoverability)

## The social post

- [ ] Posted, public, opens logged-out
- [ ] Linked from Space README **[REQ]**
- [ ] Variant-B quote (if used) is genuine model output

## Badges (claim only what's verifiable)

- [ ] Off the Grid — video shows local/offline operation
- [ ] Llama Champion — one sentence in writeup (Ollama = llama.cpp)
- [ ] Sharing is Caring — three open datasets linked in README: ledger (`make trace`),
  live field log, and deliberation traces (`make deliberation` + live `core/deliberation_log.py`)
- [ ] Field Notes — org blog post live
- [ ] Off-Brand — ONLY if CSS visually verified; screenshot as evidence
- [ ] **Storytelling — NOT a badge** (verified 6/10: it's a judging principle —
      "storytelling counts as much as the build"). No tag. It remains our
      biggest edge; Beat 1 must still earn it.
- [ ] **Tiny Titan — separate $1.5k special award, not a merit badge, and our
      eligibility is AMBIGUOUS** (verified 6/10): the guide's 32B cap counts
      **total** params ("not just active"), and e2b/e4b are 5.1B/8.0B raw
      (effective ~2B/~4B via MatFormer). No ruling found for E-models on the
      ≤4B award. **Ask in the org discussions before tagging `tiny-titan`**;
      if unfavorable, drop the claim — do NOT argue it in the writeup.
- [ ] Well-Tuned — NOT claimed (correct)

## The submission mechanism (verified 6/10 — no form, no thread)

- [ ] Submission = the Space itself, **inside the org**, with README carrying:
      frontmatter tags + demo-video link + social-post link + short writeup.
      Multiple apps allowed; max 10 ZeroGPU apps/user.
- [ ] Submitted on June 14, not June 15 (the 15th is buffer)
- [ ] Confirmation screenshot saved

## Post-submit (only after confirmed)

- [ ] Tag the submitted commit (`git tag submitted-build-small`)
- [ ] Stop. Do not push to the Space after submitting unless something is on fire.
