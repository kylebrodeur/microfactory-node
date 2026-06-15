# Field Notes: building a shop-floor AI on a small local model

I spent ten days building a small local Gemma that learns 3D printing job by job, and these are the notes from doing it. The one moment worth watching: it reads today's room, pulls up the closest prior jobs, and either applies what they taught — *"humidity is higher than the job where this overhang sagged, so I'm raising retraction and adding support"* — or says, plainly, *"no close precedent."* Two named agents keep it honest: Chief Engineer O'Brien proposes, La Forge inspects.

It's a proof of concept that works, not a production system, and I built it that way on purpose. The hackathon judges a demo, a writeup, a working app, and a believable "someone could use this" story — so anything nobody judges never got more effort than something that did. Simplify as you go. What follows is what that discipline actually taught me.

![Build page: Chief Engineer O'Brien reads precedent and flags where the print will fail before the nozzle moves](https://huggingface.co/spaces/build-small-hackathon/microfactory-lab/resolve/main/assets/screenshots/hero-build.png)

## 1. Small models need a spine, not a leash

The single best architectural decision: the model proposes, deterministic code disposes. The
Spine validates every proposed setting against hardcoded material bounds. PLA nozzle at 260C gets
clamped to 220C and a human gate trips. Once that boundary exists, you stop prompt-engineering for
safety and let the model do the thing it is actually good at, judgment over precedent, without
betting the printer on it. Never ask a small model to be its own safety system. Constraints are
what make it trustworthy.

## 2. Steering a small Gemma is a discipline

Everything in the steering playbook earned its place: a role-locked persona ("you do not hype"),
JSON mode with an output contract and cleanup code behind it, pre-filtered context (the
ledger hands the model two or three relevant precedents, never the whole history), and a typed
fallback for every call so a parse failure costs one shrug, not a crash. Prompt budget matters
more than context window. Attention quality sags past about 800 tokens, so the hot-path prompt
stays near 600 and the preflight gate measures it.

## 3. Two agents are more honest than one

O'Brien proposes the plan. La Forge, a separate skeptical persona, reads it before anything
prints and says where the optimism is thin. When La Forge disputes, the print is held until the
human acknowledges. O'Brien is the optimist. La Forge is not. My grandfather was both at once:
he built the thing and he inspected it, both voices in the same patient person. The model is never
allowed to grade its own homework. This cost almost nothing to add: one extra call, same model, a
different system prompt. It changes the trust story. The system is not asking you to believe one
agent grading itself. It shows you two views and makes the human decide.

![La Forge's second-opinion card disputing a plan: the two-agent integrity moment](https://huggingface.co/spaces/build-small-hackathon/microfactory-lab/resolve/main/assets/screenshots/second-opinion.png)

## 4. "Effective parameters" is a real thing you have to explain

I worked with Gemma 4 E-class from the start — specifically `gemma4:e2b` and `gemma4:e4b`, and later
the QAT variants. The E-models report about 8B raw parameters but run as effective ~4B or ~2B, because
the architecture (MatFormer) nests a smaller model inside a larger one. The preflight initially read the
raw count and told us to skip the small-model badge. Know which number your model actually is, and
prefer the variant that needs no argument: E4B is ~4B effective, comfortably a small model.

## 5. Latency warnings should be calibrated by driving, not by vibes

The gate said "too slow" at 18s a turn. Then I drove the cockpit. A narrated demo where you talk
through the model's precedent evaluation while it thinks reads fine at 18s, and the 40s first call
is a one-time model load you pre-warm away. The gate was recalibrated to match the observed
experience: warm under 20s passes. Benchmarks exist to predict the experience. When the experience
disagrees, the benchmark is wrong.

## 6. The smaller model was twice as fast, and made a physics mistake

E2B answered in 10s where E4B took 18, and both passed every contract and reasoning gate. But one
E2B-distilled lesson came out backwards: "slightly higher nozzle temp" to fight humid-PETG
stringing, when you go lower. The JSON was valid. The physics was wrong. Schema validation cannot
catch that, which is exactly why the human reads the lessons before they are trusted, and why
outcomes come from outside the model. Size buys you nuance. Plan for its absence.

## 7. Verify the real stack before you record, not while

`make preflight` grades eight gates on the actual model: env, latency (cold and warm split), JSON
contract, reasoning quality on a precedent-rich case and a novel one, reflection, the Spine clamp,
the app serving, the assets. Every fail points at a written contingency. A previous project died
integrating on the last night. This one ran its dress rehearsal on day one of the endgame, and the
"novel case" gate caught what matters most: the model saying "no close precedent" honestly instead
of inventing one.

## 8. Honesty is a feature you can ship, even when the numbers are bad

I checked the simulator against real FDM failure prints from a Modal ingestion run. The first pass
read 34.2%. The cause was the data, not the model: the parser only looked at G-code headers, so 178
of 260 rows had fan speed defaulting to zero. After cleaning that — parse M106 across the whole file,
final temps, real retraction — the score settled at 32.6% on 178 prints: correct on every clean
success, blind to the moderate failures. That gap is structural, not a knob to turn, and forcing a
prettier number would have broken the part that works. So the constants stayed, the reason got
written down, and the fix got named. Calibration is also a data check. One unparsed field had
quietly flipped the read on a third of the set. The same rule that keeps the model from grading
itself kept me from grading the simulator on bad data. Build the system so the honest answer is
also the impressive one.

![The Print loop: quality climbs from failure to clean as the ledger learns, with La Forge grading each run](https://huggingface.co/spaces/build-small-hackathon/microfactory-lab/resolve/main/assets/screenshots/print-loop.png)

## 9. Tooling debt compounds faster on a deadline

Mid-endgame I adopted uv (locked env), reorganized a flat 20-file root into `core/` and `scripts/`,
and found that the `.env` file had never actually been loaded by anything. None of it was the fun
work. All of it was cheaper than discovering it during the recording. Maintenance is the work.

## 10. Distribution is part of the build

The fine-tune produced four GGUFs, but a GGUF on a Modal volume isn't a
shippable artifact — it's a binary blob with no chat template, no system
prompt, and no way for a stranger to try it. So I added the missing half of
the pipeline: the same Modal app that quantizes the model also uploads it to
HF Hub alongside `template`, `system`, and `params` files so `ollama run
hf.co/…` works out of the box, and a per-variant `ollama pull → ollama cp →
ollama push` step gets the same blobs listed on [`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur)
for the one-liner case (`ollama run kylebrodeur/microfactory-node-v3-qat`).
One adapter, three derived artifacts (q4_k_m, q4_0, original LoRA), two
registries, both with model cards that link to each other. The QAT model got
a q4_0 variant because that's the quant it was trained for — highest
fidelity for the QAT base — and the `--as-name` flag I added to the upload
step keeps the two quants from overwriting each other on the Hub. Seven
gotchas got written down on the way (HF tokens with whitespace, `nohup &`
losing cwd, Ollama keys living in your home not the daemon's, `ollama push`
refusing any prefix that isn't `<username>/`, etc.) so the next adapter is a
ten-minute job, not a half-day. Done means someone you've never met can pull
and run it in one line. Build the publishing in.

## 11. Capture interest without overpromising

To capture interest without pretending the product is finished, I added a simple email signup at the bottom of the Space. It is opt-in only: checkbox + email, clear privacy note, stored as a local JSONL and optionally synced to a private HF dataset when `HF_TOKEN` is set. No print data, no uploaded files, no third-party trackers. The same pattern as the field log, but for people instead of jobs.

---

### Build paper trail

The full paper trail behind the build, linked from the Space README and the GitHub repo:

- **Model cards:** [`learn/finetune/MODEL_CARD.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/MODEL_CARD.md) · [`MODEL_CARD_QAT.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/MODEL_CARD_QAT.md)
- **Local run / publish:** [`SERVING.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/SERVING.md) · [`OLLAMA_PUBLISHING.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/OLLAMA_PUBLISHING.md)
- **Fine-tune pipeline:** [`learn/finetune/README.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/README.md) · [`PIPELINE.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/PIPELINE.md) · [`RUNBOOK.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/RUNBOOK.md) · [`BUDGET.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/BUDGET.md)
- **Session report + activity trace:** [`SESSION_REPORT.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/SESSION_REPORT.md) · [`activity.jsonl`](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/activity.jsonl)
- **Calibration:** [`sim/calibration/CALIBRATION-REPORT.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/sim/calibration/CALIBRATION-REPORT.md) · [`sim/calibration/README.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/sim/calibration/README.md)
- **Ingestion + assets + outputs:** [`ingest/README.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/ingest/README.md) · [`assets/screenshots/README.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/assets/screenshots/README.md) · [`dist/README.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/dist/README.md) · [`dist/deliberation/README.md`](https://github.com/kylebrodeur/microfactory-node/blob/main/dist/deliberation/README.md)

**Book chapter.** The same build is chaptered in the Microfactory book as
*Appendix: Microfactory Node — 3D Printer* (in progress), which frames it as the first concrete node of the larger Microfactory idea: a small, local AI that
learns a craft job by job so the craft cannot be lost.

*Microfactory Node: 3D Printer runs fully local (Ollama / llama.cpp, Gemma E4B/E2B), falls back
to a deterministic advisor, and publishes both its lesson ledger and its live interaction log as open
datasets. It is the first node of the Microfactory, a network of small machines and the people who
run them, with a real economy growing around the work.*

*Live: [node.microfactory.space](https://node.microfactory.space) ·
Ledger: [kylebrodeur/chief-engineer-ledger](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger) ·
Field notes: [build-small-hackathon/microfactory-lab-field-notes](https://huggingface.co/datasets/build-small-hackathon/microfactory-lab-field-notes) ·
GGUFs: [kylebrodeur/microfactory-node-gguf](https://huggingface.co/kylebrodeur/microfactory-node-gguf) · [ollama.com/kylebrodeur](https://ollama.com/kylebrodeur) ·
Code: [kylebrodeur/microfactory-node](https://github.com/kylebrodeur/microfactory-node)*
