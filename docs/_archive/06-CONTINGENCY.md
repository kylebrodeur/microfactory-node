# 06 — Contingency Runbook

When something doesn't work locally, come here. Each section is keyed to a
`make preflight` gate (run that first — it tells you which section you're in) or
to a deploy/record failure. Format: **symptom → diagnose → fix → if the fix
fails, the fallback that keeps the submission alive.**

The prime directive under failure: **the submission needs a video, a Space, and
a writeup — not a perfect system.** Every fallback below trades capability for
shippability on purpose.

---

## §G1 — Ollama / model unavailable

**Symptom:** `G1 env: FAIL` — daemon unreachable or model tag missing.

**Diagnose (in order):**
1. `ollama --version` — installed at all?
2. `ollama serve` in its own terminal; then `ollama list`.
3. `ollama list` shows tags — is `gemma4:e4b` (= `gemma4:latest`) there?
4. If the tag is misspelled anywhere: **`gemma4:4b` does not exist.** Check
   `echo $CHIEF_ENGINEER_MODEL` and `.env`.

**Fix:** `ollama pull gemma4:e4b` (9.6GB — start it FIRST, it's the long pole).
While it pulls, do offline work (writeup, social post, Space scaffold).

**Fallbacks, in order:**
1. `ollama pull gemma4:e2b` (smaller, faster pull AND faster inference).
2. Any local Gemma you already have pulled: `CHIEF_ENGINEER_MODEL=<tag> make preflight`.
   The persona prompt is model-agnostic; latency/quality gates re-grade it.
3. **Nuclear:** the deterministic fallback IS demo-safe (every path tested
   offline). Record Beats 1/2/5/6 of the video normally; for Beats 3–4 use the
   deterministic PRECEDENT EVALUATION panel (it narrates the env-delta vs the
   nearest prior job legibly without the LLM). Do NOT show the "[fallback]"
   reasoning string on screen; lead with the panel, the settings shift, and the
   ledger growth — those are all real. Note honestly in the writeup that live
   inference runs locally via Ollama; do not imply the recording's reasoning
   text came from the model if it didn't.

---

## §G2 — Latency too slow for live demo

**Symptom:** `G2 latency: WARN` (warm avg 20–35s) or `FAIL` (warm avg ≥ 35s).

**First, read the right number.** Preflight now splits the one-time **cold-start**
(first model load — can be 40–60s) from the **warm steady-state** (every call
after). The demo experience is the *warm* number; you pre-warm with one throwaway
call before recording so the cold load never shows. Bands were re-calibrated
against real cockpit driving (6/10): **warm < 20s is a PASS** — it reads fine in
a narrated demo where you talk through the reasoning while it generates.
20–35s is a WARN; only warm ≥ 35s is a real FAIL.

**Diagnose:** Which hardware? Laptop CPU vs the Space's CPU are different
problems. Re-run `make bench` for a clean number.

**Fixes, in order:**
1. `CHIEF_ENGINEER_MODEL=gemma4:e2b` — re-run preflight; if G4 reasoning still
   passes on e2b, ship e2b. (Smaller + on-message beats bigger + unwatchable.)
2. Trim the system prompt: drop the reference block (`references=None`) — it's
   optional by design — and cap retrieved precedent at k=2.
3. `options={"num_predict": 350}` in `core/llm.py:chat_json` — the output contract fits
   comfortably; this bounds the long tail.

**Fallback:** for the VIDEO, latency is editable — cut the wait, keep the
result, and say on screen "~Ns on my laptop CPU" honestly. For the LIVE Space,
pre-warm with one call on startup, and let the fallback handle judge clicks if
Ollama isn't present on the Space anyway (it won't be — the Space path is
fallback-by-design unless you host inference; see §S2).

---

## §G3 — JSON parse / schema failures

**Symptom:** `G3 contract: WARN/FAIL` — model returns prose, truncated JSON, or
wrong-shaped fields.

**Diagnose:** run one call by hand and READ the raw output:
```bash
uv run python -c "
from core import llm
from core.models import Environment, Job
from core.prompts import build_system_prompt
s = build_system_prompt(Job(geometry_type='overhang', material='PLA'), Environment(temp=28, humidity=50), [])
import ollama
r = ollama.chat(model=llm.MODEL, messages=[{'role':'system','content':s},{'role':'user','content':'Give your recommendation for THIS job now.'}], format='json', options={'temperature':0.4})
print(r['message']['content'])"
```

**Fixes, in order (one at a time, re-run preflight between):**
1. Truncation → raise `num_predict` / check it's not set too low.
2. Wrong field names → tighten `OUTPUT_CONTRACT` in `core/prompts.py`: add a literal
   one-line example object after the shape spec (small models imitate examples
   better than schemas).
3. Numbers as strings → add a pre-parse coercion shim in `chat_json` (cast
   numeric-looking strings in `settings` before `Advice(**raw)`), or loosen the
   Pydantic types to accept `float | str` with a validator. Keep it in ONE place.
4. Temperature 0.4 → 0.2. Determinism beats flair for a contract.
5. The small-Gemma playbook lives in `docs/reference/GEMMA-STEERING.md`
   (persona grounding, JSON enforcement, constraint narrowing, prompt budget).

**Fallback:** the app already falls back per-call, so a 1-in-5 parse failure is
cosmetic for the Space. For the video, retry the take — you only need ONE good
on-screen run per beat.

---

## §G4 — Reasoning text is weak (the load-bearing moment underwhelms)

**Symptom:** `G4 reasoning: WARN` — settings fine but the reasoning doesn't
visibly *evaluate* precedent; or G4b hallucination warning on the novel case.

This is the highest-stakes gate: Beat 3 of the video IS this text.

**Fixes, in order:**
1. Prompt, not code. In `core/prompts.py` PERSONA, make the evaluation demand
   concrete: "Name the prior job you are weighing (its id) and compare ITS
   conditions to THIS room (give the temperature/humidity delta in numbers)
   before you decide."
2. Add a one-shot example reasoning string to the OUTPUT_CONTRACT ("reasoning"
   example: "Job seed-008 strung at 25°C/65% — today is 3° cooler but just as
   humid, so moisture is still the enemy: dropping nozzle 5°, raising
   retraction."). Small models follow examples.
3. Novel-case hallucination (G4b): add to PERSONA: "If the precedent block says
   (none), you MUST say 'no close precedent' and must not invent prior jobs."
4. Re-run `make preflight` after each change; stop at the first green.
5. See `docs/reference/GEMMA-STEERING.md` — the same techniques (one-shot
   examples, explicit behavioral constraints) fixed this class of problem before.

**Fallback:** the deterministic `precedent_eval_html` panel already narrates the
env-delta ("4°C warmer, 12 pts more humid → conditions worse") — in the video,
frame the panel as the system's evaluation and the model text as the decision.
That division is honest and reads well even with terse model output.

---

## §G6 — Spine fails to clamp

**Symptom:** `G6 spine: FAIL`. Should never happen (covered by test_core), so
treat as environment skew: `git status` / `git stash` local edits to `core/spine.py`,
re-run `make test`. Do not record until green — the "deterministic
veto" claim is in the writeup.

---

## §G7 — App won't build/serve

**Symptom:** `G7 app: FAIL` — import error, port conflict, Gradio version skew.

**Diagnose:** the error text in the gate output. Most likely locally:
1. Different Gradio version than 6.17.3 → `uv sync` (the locked uv.lock pins it)
   (the README frontmatter pins `sdk_version: 6.17.3` — local should match).
2. Port in use → preflight uses 7991; the app itself 7860. `lsof -i :7860`.
3. Missing assets → §G8.

**Fallback:** none needed historically (app has served 200 in every sandbox
check) — this gate exists to catch local-env drift before it eats a night.

---

## §G8 — Assets / seed data missing

**Symptom:** `G8 assets: FAIL/WARN`.
**Fix:** `make assets` (meshes are gitignored by design);
`data/seed_lessons.jsonl` must be the canonical 12 (tracked in git — if it's
wrong, `git checkout -- data/seed_lessons.jsonl`).
To reset runtime demo state before recording: delete `data/lessons.jsonl` and
`data/policy.json` (both gitignored; see commit 1dce4d5 docs).

---

## §S1 — Space deploy fails (push rejected, build error)

**Symptom:** `git push` to the Space rejected; build log red; Space won't start.

**Diagnose, in order:**
1. Build log on the Space page — Python version / dependency resolution first.
2. `requirements.txt` resolves on a clean venv locally?
   `python -m venv /tmp/v && /tmp/v/bin/pip install -r requirements.txt`
   (deliberately pip, NOT uv — this reproduces exactly how the Space installs).
3. README frontmatter valid? (`sdk: gradio`, `sdk_version: 6.17.3`,
   `app_file: app.py` — already correct in repo.)

**Fixes:**
- Dependency conflict → pin exact versions that resolved locally.
- App boots but errors at runtime → check it's not trying to reach Ollama and
  failing loudly: it shouldn't (graceful fallback is built in), but verify the
  cold-start path shows "🟡 offline fallback" and still serves recommendations.
- trimesh heavy at build → it's in requirements; if the Space build times out,
  make trimesh import lazy in `core/viewer.py` (it's a removable layer by design).

**Fallback ladder:**
1. Deploy under your personal namespace first to debug, then transfer/redeploy
   into `build-small-hackathon` (submission requires the org).
2. Strip removable layers until it builds: Print loop → mesh preview →
   references. The core Studio→Build + ledger alone is still a valid submission.
3. **Deadline-day nuclear:** the org requires a Gradio Space; the VIDEO carries
   the judging if the live Space is degraded ("submit a demo video showing your
   app working so judges can evaluate it even if GPU or API limits stop a live
   run" — field guide). A degraded-but-up Space + strong video >> no Space.

---

## §S2 — "Live inference on the Space" expectations

The Space will NOT have Ollama/gemma running on free CPU hardware. This is
**by design**: the app surfaces "🟡 offline fallback" honestly, and the writeup
says live inference runs locally. Decide ONCE (Day 7) and stop revisiting:

- **Default (recommended):** Space ships the deterministic path + full UI;
  video shows the live local model; writeup states the split honestly. The
  PRECEDENT EVALUATION panel still demonstrates compounding live on the Space
  (retrieval + ledger growth are fully real there).
- **Upgrade (only if everything else is green by Day 8):** host the model on
  Modal (credits available, sponsor award) and point `core/llm.py` at it via an
  OpenAI-compatible endpoint. New env var, ~30 lines. Do NOT start this before
  the default path is recorded and submitted-quality. It risks the Off-the-Grid
  story — if you do it, keep local-first as the headline and Modal as the
  "judges can try it live" bonus, stated plainly.

---

## §R1 — Recording day problems

**Symptom:** the run won't behave on camera (wrong precedent retrieved, lesson
text awkward, novel case not novel).

**Fixes:**
- Reset state first, every take: delete `data/lessons.jsonl` + `data/policy.json`
  (seeds reload on launch; takes become reproducible).
- Script the beats from `scripted_demo.py`'s four jobs — they were chosen to hit
  the beats (precedent applied → env-shift → earned-lesson reuse → novel).
- Latency on camera → §G2; cut waits in the edit, never fake the output.
- A flubbed take is a take: re-record the beat, not the day. Beats are
  independent by design.

**Hard rule:** if by 18:00 local on Jun 12 the live-model recording still isn't
working, record the §G1-fallback version of Beats 3–4 THAT NIGHT and ship it.
A finished honest video beats a perfect missing one. (That's the Kaggle lesson
in one sentence.)

---

## §W1 — Writeup/social blockers

No technical dependencies: drafts exist (`docs/writeup/01-SUBMISSION-DRAFT.md`,
`04-SOCIAL-POST.md`). If time collapses, the draft is submittable after a
15-minute voice pass — facts are already verified against `00-STORY.md` and the
honesty table. Do not write new claims under deadline pressure; cut instead.
