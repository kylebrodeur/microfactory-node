# Steering a small Gemma so it earns its keep

> Hard-won lessons from shipping `gemma4:e4b` / `gemma4:e2b` in the Chief
> Engineer — an offline 3D-printing copilot built for the Hugging Face Build
> Small hackathon. If you're handing a quantized 4B model real decisions, this
> is the discipline that keeps it honest.

These are not theory. Every technique here has a code path in
[`microfactory-lab/chief-engineer`](https://github.com/kylebrodeur/microfactory-node)
that you can read.

| Technique | Where it lives in this repo |
|---|---|
| T1 — Strict persona grounding | `core/prompts.py` (`PERSONA` is role-locked) |
| T2 — Zero-shot JSON enforcement | `core/llm.py:chat_json` (`format="json"` + fence strip) |
| T3 — Constraint narrowing | `core/ledger.py:retrieve` pre-filters to 2–3 precedents; `core/spine.py` owns physics |
| T4 — Graceful degradation | `core/llm.py:chat_json` returns `None` → deterministic advisor; demo never crashes |
| T5 — Prompt length budget | `scripts/deploy_preflight.py` measures prompt size; warns past ~800 tokens |
| T6 — Two agents, not one | `core/chief_engineer.py` proposes; `core/inspector.py` second-opinion + grades |

The published GGUFs ([`kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf),
[`ollama.com/kylebrodeur`](https://ollama.com/kylebrodeur)) carry the matching
`template` / `system` / `params` so all six techniques apply when someone runs
the model from the Hub. The publishing pipeline that gets them there is in
[`learn/finetune/OLLAMA_PUBLISHING.md`](../learn/finetune/OLLAMA_PUBLISHING.md).

---

## The problem: small models over-align

A quantized Gemma 4B is heavily aligned for safety and helpfulness. In an
agentic context that creates predictable failure modes:

- **Refusal on simple tasks.** Asked to make a routing decision, the model
  answers "I don't have enough information to…" instead of executing.
- **Conversational filler.** It wraps JSON output in markdown fences and
  prose: "Sure! Here's the JSON you requested: ```json…```".
- **Context confusion.** Without a strong persona, manufacturing instructions
  get interpreted as general chat.
- **Tool-call hesitation.** It second-guesses parameter values and adds
  qualifiers instead of returning clean JSON.

All six techniques below exist to suppress one or more of those failure modes
without giving up the judgment the model is actually good at.

---

## T1 — Strict persona grounding

**Problem:** the model falls into "helpful assistant" mode and refuses to
decide.

**Solution:** open the system prompt with an unambiguous, role-locked identity
statement. From `core/prompts.py`:

```
You are O'Brien, a veteran print-shop master.
You do not hype. You do not hedge. You do not converse.
You read precedent and propose settings. The Spine enforces safety;
La Forge gives the second opinion. You only output structured advice.
```

Two things make it work:

1. **First-person identity.** "You are O'Brien" is stickier than "You are an
   assistant that…". Gemma latches on to a name + persona faster than a role
   description.
2. **Explicit negations.** "You do not converse" suppresses the helpfulness
   reflex that causes filler. Pair it with "you do not hype" / "you do not
   hedge" and the tone drops to the register you want.

---

## T2 — Zero-shot JSON enforcement (with a safety net)

**Problem:** the model wraps responses in markdown fences or adds prose
before/after the JSON.

**Solution** is three layers — assume each will fail sometimes:

1. **API-level JSON mode.** Ollama: `format="json"` on the chat call. This
   alone is not enough — small Gemmas still emit fences ~5% of the time under
   load.
2. **An explicit format contract at the end of the prompt:**
   ```
   Respond ONLY with valid JSON in this exact shape:
   {"settings": {...}, "reasoning": "..."}
   ```
3. **A post-processing fence-strip net.** `core/llm.py:chat_json` peels
   ` ```json ... ``` ` before `json.loads`. Then if the parse still fails, it
   returns `None` and T4 (graceful degradation) takes over.

Three layers is paranoid. Without the third one, ~1 in 200 calls eats the
demo. With it, the path from prompt to typed object is unconditional.

---

## T3 — Constraint narrowing (give the model binary choices)

**Problem:** the model hallucinates ids, capabilities, or physics when given a
large state to reason about.

**Solution:** pre-filter the state on the host side. Hand the model a small
shortlist; never ask it to reason about physics constraints — let the
deterministic Spine handle that.

Bad prompt pattern:

```
Here is the full ledger of 200 past prints across 8 materials.
Which settings should I use for this PETG overhang at 25C / 55%?
```

Good prompt pattern:

```
Closest precedents (top 2, filtered by material + geometry + env distance):
- PETG overhang at 24C / 50%: nozzle 235, bed 80, fan 30%, retraction 5.5 — Result: clean
- PETG overhang at 26C / 60%: nozzle 240, bed 80, fan 35%, retraction 5.8 — Result: minor sag

Material bounds (Spine-enforced — do not propose outside):
  nozzle 220–250, bed 70–85, fan 0–50%, retraction 4.0–7.0

Propose settings as JSON.
```

The ledger does the retrieval. The Spine owns the bounds. The model does the
one thing only it can do — read precedent and write a defensible plan.

---

## T4 — Graceful degradation

**Problem:** even with all of the above, the model occasionally returns null
or malformed JSON.

**Solution:** give every LLM call a typed fallback from the deterministic layer.
From `core/llm.py`:

```python
def chat_json(...) -> dict | None:
    try:
        raw = ollama.chat(..., format="json")
        return json.loads(_strip_fences(raw["message"]["content"]))
    except Exception:
        return None    # caller falls back to the deterministic advisor
```

The caller treats `None` as a clear signal:

```python
proposal = chat_json(...) or fallback_advisor.recommend(job, env)
```

A null from the LLM becomes a conservative recommendation. The Spine then
clamps anything unsafe regardless of which path produced it. The system
never hangs and never crashes due to model failure — it just gets less
clever for one turn and tells the operator that's what happened.

---

## T5 — Prompt length budget

**Problem:** small Gemmas degrade significantly with long prompts. The
context window is large; attention quality drops well before it
fills.

**Solution:** keep hot-path prompts under ~500 tokens. Reserve longer prompts
for offline tasks where latency and quality slip cost nothing.

| Task | Budget | Path |
|---|---|---|
| Routing / settings proposal | ~400 tokens | hot path — keep tight |
| Second opinion | ~300 tokens | hot path — even tighter (one job, one plan) |
| Reflection / lesson extraction | ~600 tokens | post-print, async |
| Status summary | ~500 tokens | background |

`scripts/deploy_preflight.py` measures actual prompt size on a representative
job and warns past ~800. If the ledger retrieval grows the precedent block
too far, the first thing to drop is `k=3` → `k=2`.

---

## T6 — Two agents, not one

**Problem:** a single model grading its own homework is not honest, and
operators feel it.

**Solution:** run a second persona — same model, different system prompt —
explicitly framed as a skeptic. O'Brien proposes; La Forge reads the plan
before anything prints and says where the optimism is thin.

- O'Brien is the optimist with the precedent in hand.
- La Forge is not. La Forge's prompt opens "You are skeptical by default" and
  ends "if anything looks past the envelope, dispute."
- If La Forge disputes, the system holds the print until the human acknowledges.

Cost: one extra inference call per job. Benefit: the trust story changes.
The system is no longer asking you to believe one agent grading itself — it
shows two views and lets you decide. The model never marks its own homework.

This is in `core/inspector.py` (`second_opinion`, `grade_iteration`,
`summarize_run`). Turn-by-turn deliberation between the personas lands in
[`kylebrodeur/chief-engineer-deliberation`](https://huggingface.co/datasets/kylebrodeur/chief-engineer-deliberation),
so anyone can read exactly how it argued.

---

## Quick-reference prompt skeleton

```
You are [ROLE]. You do not converse. You only [ACTION].

[PRE-FILTERED CONTEXT — 2–3 items max, binary choices only]

[HARD BOUNDS — what the deterministic layer enforces, so the model
doesn't have to invent them]

Respond ONLY with valid JSON in this exact shape:
{ ... }
```

That's the whole steering surface. Six techniques, six lines of discipline,
no fine-tune required to get there. The published GGUFs bake the
matching template/system/params into the model card so the discipline
travels with the weights.

---

## Further reading

- **[`docs/reference/LEARNINGS.md`](docs/reference/LEARNINGS.md)** — broader field notes from ten days
  building this thing (what surprised me, what I'd do again, what the small
  model couldn't quite do).
- **[`learn/finetune/OLLAMA_PUBLISHING.md`](../learn/finetune/OLLAMA_PUBLISHING.md)**
  — how the GGUFs get from a Modal volume to `ollama.com` with the matching
  `template` / `system` / `params` baked in.
- **[`learn/finetune/SERVING.md`](../learn/finetune/SERVING.md)** — the live
  serving story (ZeroGPU + Modal OpenAI-compatible endpoint + the GGUF
  fallback path).
- **[`kylebrodeur/chief-engineer-deliberation`](https://huggingface.co/datasets/kylebrodeur/chief-engineer-deliberation)**
  — open dataset of the turn-by-turn deliberation between the personas.
  Every claim above is auditable against the trace.
- **[`kylebrodeur/chief-engineer-ledger`](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger)**
  — environment-keyed lesson memory the agent retrieves from before each print.
- **[`build-small-hackathon/chief-engineer-field-log`](https://huggingface.co/datasets/build-small-hackathon/chief-engineer-field-log)**
  — live interaction log from the Space (builds, second opinions, print runs, recorded outcomes).
