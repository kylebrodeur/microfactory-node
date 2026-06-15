# Ten field notes from building the Chief Engineer

Microfactory Node — 3D Printer is a small local Gemma that learns 3D printing
job by job. It retrieves what happened in similar conditions, reasons about
what transfers, proposes settings, and deterministic code vetoes it when
it's wrong. Two named agents run it: **Chief Engineer O'Brien** proposes,
**La Forge** inspects. Built in ten days for the Hugging Face Build Small
hackathon. These are the notes from building it small, in the open, on my own
machine.

> The polished writeup that came out of these notes is in
> [`docs/writeup/06-FIELD-NOTES.md`](writeup/06-FIELD-NOTES.md). This page is
> the developer-facing version — same lessons, less marketing-readable, more
> useful if you're about to build something similar.

---

## 1. Small models need a spine, not a leash

The single best architectural decision: **the model proposes, deterministic
code disposes.** The Spine validates every proposed setting against hardcoded
material bounds. The Spine clamps a PLA nozzle at 260°C to 220°C and trips the human gate. Once that boundary exists, you stop prompt-engineering for safety. You
let the model do what it's actually good at — judgment over precedent —
without betting the printer on it.

> **Don't ask a small model to be its own safety system.** Constraints are
> what make it trustworthy.

`core/spine.py` owns the bounds. `core/chief_engineer.py` does not.

---

## 2. Steering a small Gemma is a discipline

Everything in the steering playbook earned its place. A role-locked persona
("you do not hype"). JSON mode with an output contract and a fence-stripping
net behind it. Pre-filtered context: the ledger hands the model 2–3 relevant
precedents, never the whole history. A typed fallback on every call so a parse
failure costs one shrug, not a crash. Prompt budget matters more than
context window — attention quality sags past about 800 tokens, so the
hot-path prompt stays near 600 and the preflight gate measures it.

Full writeup with code paths: [`docs/GEMMA-STEERING.md`](GEMMA-STEERING.md).

---

## 3. Two agents are more honest than one

O'Brien proposes the plan. La Forge — a separate skeptical persona, same
model, different system prompt — reads it before anything prints and says
where the optimism is thin. When La Forge disputes, the system holds the print until the human acknowledges. O'Brien is the optimist. La Forge is not. **The model
never marks its own homework.**

This cost almost nothing to add: one extra call, same model, a different
prompt. It changed the trust story. The system is not asking you to believe
one agent grading itself. It shows two views and makes the human decide. The
turn-by-turn deliberation is logged to
[`kylebrodeur/chief-engineer-deliberation`](https://huggingface.co/datasets/kylebrodeur/chief-engineer-deliberation)
so the argument is auditable, not theatre.

---

## 4. "Effective parameters" is a real thing you have to explain

Gemma 4 E-models report ~8B raw parameters but run as effective ~4B (E4B) or
~2B (E2B) — that's MatFormer. The preflight initially read the raw count and
told me to skip the small-model badge. **Know which number your model
actually is**, and prefer the variant that needs no argument.

Numbers from `make bench` on PEGASUS (2026-06-10):

| | `gemma4:e4b` | `gemma4:e2b` |
|---|---|---|
| Warm latency | 18.5 s | **10.3 s** (~2× faster) |
| Cold load (one-time) | 38.7 s | 41.8 s |
| Params (raw / effective) | 8.0B / ~4B | 5.1B / ~2B |
| JSON-contract gate | 3/3 | 3/3 |
| Reasoning quality | sharpest ("hygroscopicity is the dominant failure mode") | substantive, cites 3 precedents, slightly more generic |
| Novel-case honesty | "no close precedent" | "no close precedent" |

I recorded the demo on E4B for the sharper reasoning. E2B is one env var
away. Both variants are fine-tunable and both are published — see
[`learn/finetune/SERVING.md`](../learn/finetune/SERVING.md).

---

## 5. Latency warnings should be calibrated by driving, not by vibes

The gate said "too slow" at 18 s a turn. Then I drove the cockpit. A narrated
demo where you talk through the model's precedent evaluation while it thinks
reads fine at 18 s. The 40 s first call is a one-time model load you
pre-warm away. I recalibrated the gate to match the observed experience:

| Warm latency | Verdict |
|---|---|
| < 20 s | PASS — reads fine narrated |
| 20–35 s | WARN |
| ≥ 35 s | FAIL |

**Benchmarks exist to predict the experience. When the experience disagrees,
the benchmark is wrong.**

---

## 6. The smaller model was twice as fast, and made a physics mistake

E2B answered in 10 s where E4B took 18, and both passed every contract and
reasoning gate. But one E2B-distilled lesson came out backwards: *"slightly
higher nozzle temp" to fight humid-PETG stringing*, when you go lower. The
JSON was valid. The physics was wrong.

Schema validation cannot catch that, which is exactly why:

- the human reads the lessons before they're trusted (the ledger ships open),
- outcomes come from outside the model (the deterministic World simulator,
  never the LLM grading itself), and
- the **Well-Tuned** badge is a held-out eval, not a vibe.

Size buys you nuance. Plan for its absence.

---

## 7. Verify the real stack before you record, not while

`make preflight` grades eight gates on the actual model: env, latency (cold
and warm split), JSON contract, and reasoning quality on a precedent-rich case
and a novel one. It also checks reflection, the Spine clamp, app serving, and
assets.
Every fail points at a written contingency. A previous project died
integrating on the last night. This one ran its dress rehearsal on day one
of the endgame. The "novel case" gate caught what matters most: the
model saying "no close precedent" honestly instead of inventing one.

---

## 8. Honesty is a feature you can ship, even when the numbers are bad

I checked the simulator against real FDM failure prints from a Modal
ingestion run. First pass read **34.2%**, and the cause was the data, not the
model: 178 of 260 rows had fan speed defaulting to zero because the parser
only looked at G-code headers. After cleaning that (parse `M106` across the
whole file, final temps, real retraction) the score settled at **32.6% on
178 prints**. It was correct on every clean success, blind to the moderate
failures.

That gap is structural, not a knob to turn, and forcing a prettier number
would have broken the part that works. So the constants stayed, I wrote down the reason, and I named the fix.

Two lessons fell out of that:

1. **Calibration is also a data check.** One unparsed field had quietly
   flipped the read on a third of the set.
2. **The same rule that keeps the model from grading itself kept me from
   grading the simulator on bad data.** Build the system so the honest answer
   is also the impressive one.

---

## 9. Tooling debt compounds faster on a deadline

Mid-endgame I adopted `uv` (locked env), reorganized a flat 20-file root
into `core/` and `scripts/`, and found that nothing had ever loaded the `.env` file. None of it was the fun work. All of it was
cheaper than discovering it during the recording. **Maintenance is the
work.**

---

## 10. Distribution is part of the build

The fine-tune produced four GGUFs, but a GGUF on a Modal volume isn't a
shippable artifact — it's a binary blob with no chat template, no system
prompt, and no way for a stranger to try it. So I added the missing half of
the pipeline:

- The same Modal app that quantizes the model also uploads it to HF Hub
  alongside `template`, `system`, and `params` files so
  `ollama run hf.co/…` works out of the box.
- A per-variant `ollama pull → ollama cp → ollama push` step gets the same
  blobs listed on [`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur)
  for the one-liner case
  (`ollama run kylebrodeur/microfactory-node-v3-qat`).
- One adapter, three derived artifacts (q4_k_m, q4_0, original LoRA), two
  registries, both with model cards that link to each other.
- The QAT model got a q4_0 variant because that's the quant it was trained
  for — highest fidelity for the QAT base — and the `--as-name` flag I added
  to the upload step keeps the two quants from overwriting each other on
  the Hub.

I wrote down seven gotchas on the way: HF tokens with whitespace, `nohup
&` losing cwd, Ollama keys living in your home not the daemon's, `ollama
push` refusing any prefix that isn't `<username>/`, etc. The next adapter is a
ten-minute job, not a half-day. The full runbook is in
[`learn/finetune/OLLAMA_PUBLISHING.md`](../learn/finetune/OLLAMA_PUBLISHING.md).

**The shape of "done" for a small local model is: not just the eval passed,
but someone you've never met can pull and run it in one line.** Build the
publishing in.

---

## What I'd do differently

- **Start with the Spine, then the persona, then the model.** The first
  three days I tuned prompts before I had the safety layer. The bounds
  changed the prompts anyway. Constraints first means less wasted prompt
  iteration.
- **Add the second agent on day one, not day six.** La Forge took an hour
  to build and shifted the entire trust story. The earlier the skeptic
  exists, the earlier you get used to operating with two views.
- **Treat publishing as a beat in the build plan.** "Train → eval → done"
  is missing a step. The Modal pipeline's `upload_to_hub` Modal function
  + the `ollama pull/cp/push` loop is the real done. I only shook out
  half the gotchas listed above because I left publishing for the last day.

---

## Live artifacts

- **Space (live demo):** `https://build-small-hackathon-microfactory-lab.hf.space`
- **GGUFs (HF Hub):** [`kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf)
- **GGUFs (ollama.com):** [`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur)
- **LoRA adapters:**
  [`microfactory-node-lora`](https://huggingface.co/kylebrodeur/microfactory-node-lora)
  · [`-lora-v2`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v2)
  · [`-lora-v3-qat`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v3-qat)
- **Lesson ledger (dataset):** [`kylebrodeur/chief-engineer-ledger`](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger)
- **Deliberation log (dataset):** [`kylebrodeur/chief-engineer-deliberation`](https://huggingface.co/datasets/kylebrodeur/chief-engineer-deliberation)
- **Field log (live, dataset):** [`build-small-hackathon/chief-engineer-field-log`](https://huggingface.co/datasets/build-small-hackathon/chief-engineer-field-log)
- **Code:** [`kylebrodeur/microfactory-lab`](https://github.com/kylebrodeur/microfactory-node)
