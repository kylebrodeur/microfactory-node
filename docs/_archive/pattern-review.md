# The Chief Engineer — Pattern Review & Python Porting Guide

Based on a review of the `microfactory-lab` and `pi-qmd-ledger` repositories. *(Note: `pi-context`, `pi-guideline-loader`, and `UACS` were not present in the cloned workspace, so context injection patterns were extrapolated from `hubAgent.ts`.)*

> **Editor's note (resolved, post-review):** The three missing repos do **not** affect any design decision and the review was **not** rerun. `pi-context` is a third-party extension whose context-injection approach is superseded by the locked `build_system_prompt()` design in the plan. `pi-guideline-loader` just loads agent files (Claude/CLAUDE.md style) — a file read, not an architecture; the plan hardcodes the persona in `prompts.py`. `UACS` is a deliberately *abandoned, over-scoped* project — it serves as an anti-pattern reference (the scope discipline this whole plan is designed around), not a pattern source. The load-bearing findings below — agent structure, Brain/Spine veto, ledger, the `reviewOutcome()` reflection loop, the HITL trigger — all came from code that **was** reviewed and are complete.

---

## 1. AGENT STRUCTURE

**How it actually works (`hubAgent.ts`):** 
The `HubAgent` extends a pub/sub base `Agent` class. It builds prompts via template literals (injecting `job` and `nodeState`), enforces structured JSON by appending `"Respond ONLY with valid JSON"`, and invokes the LLM via a generic `this.askLLM(prompt, true)`. It handles errors by falling back to conservative defaults (e.g., rejecting the job) if the model returns null or malformed data.

**Carry forward:**
- The prompt assembly via string interpolation.
- The strict `"Respond ONLY with valid JSON"` instruction block coupled with a JSON schema structure.
- The fallback/default behavior when the LLM fails to return valid JSON.

**Leave behind (over-scope):**
- The pub/sub `MessageBus`.
- The async `tick()` event loops. 
- The LLMProvider abstraction layers (just call Ollama's Python client directly).

**Minimal Python shape:**
A single stateless Python class/function (`ChiefEngineer`) that takes the inputs (job, env, history), formats a system prompt, calls the Ollama Python client, and returns a parsed Pydantic model. 

---

## 2. BRAIN/SPINE VETO

**How it actually works (`nodeAgent.ts`):**
The deterministic layer (`NodeAgent`) acts as the final gate. `canDoJob()` strictly validates if the node possesses the exact array of capabilities required, and then tracking logic checks capacity. A hard 15.0W safety breaker in `tick()` acts as a real-time veto—if the node overdraws power, it shuts down regardless of the job state.

**Carry forward:**
- The "LLM proposes, code decides" paradigm.
- Hardcoded safety clamps.

**Leave behind (over-scope):**
- Power budget tracking (Joules/Watts) over time.
- Node capacity availability loops.

**Minimal Python shape:**
A simple `SpineValidator` Python class. The LLM proposes settings (e.g., `temp: 260`, `retraction: 1.5`). The `SpineValidator` runs them against predefined hardware material boundaries (PLA = max 230°C). If it fails, the Spine clamps the value to the max safe limit or rejects the proposal entirely.

---

## 3. LEDGER

**How it actually works (`pi-qmd-ledger/src/tools.ts`):**
Entries are appended as JSONL strings via `append_ledger`. It uses `qmd` for semantic embeddings and fuzzy search (`qmd_search`), while exact searches happen via `query_ledger` iterating over the file and applying key-value filters.

**Carry forward:**
- Pure append-only JSONL storage format.
- Storing the job context + outcome + lesson together.

**Leave behind (over-scope):**
- Complex QMD semantic embeddings, indexing, and vector similarity search.
- "Gated" vs "Autopilot" HITL queue abstractions.

**Minimal Python shape:**
A `LedgerManager` class that reads/writes a `lessons.jsonl` file. For retrieval, since your thesis relies on *environment* keying, you don't need semantic search. Calculate the simple Euclidean distance or delta between the current job's `[temp, humidity]` and the historical records' environment, filter for the exact material, and grab the closest K lessons.

---

## 4. KNOWLEDGE FLOW

**How it actually works (`hubAgent.ts`):**
When a job resolves, `reviewOutcome()` fires. It prompts the LLM to reflect on its routing accuracy. The LLM outputs a 1-sentence `lesson` and a `confidenceAdjustment` float. This is logged to the ledger as a `knowledge-update` and then broadcasted across the network so peer nodes can update their confidence weights.

**Carry forward:**
- The post-job reflection LLM call ("What did this teach you?").
- The 1-sentence compressed lesson string.

**Leave behind (over-scope):**
- Network-wide federation (`broadcast('knowledge_update')`).
- Numerical confidence adjustment math.

**Minimal Python shape:**
A `reflect_on_job(job, outcome, env)` function. If a print strings heavily, Gemma gets the data, identifies the flaw, and writes: *"PLA at 60% humidity and 220°C requires 2mm retraction to avoid stringing."* Next time, the expansion step pulls this text string from JSONL and drops it straight into the Chief Engineer's system prompt context.

---

## 5. HITL GATE

**How it actually works (`hubAgent.ts`):**
`shouldTriggerHITL()` checks if model confidence is `< 0.75` or job value is `> 500`. If triggered, it sets up an unresolved Promise in a `hitlResolvers` map and waits. A separate bus message triggers the resolution, or a 500ms timeout auto-approves it in non-interactive mode.

**Carry forward:**
- Tripping human review based on high-risk model outputs.

**Leave behind (over-scope):**
- Promise maps, timeout fallbacks, and event bus handlers.

**Minimal Python shape:**
A boolean state flag in Gradio (`requires_approval`). When the LLM flags a high-risk region or a major temperature shift, the Gradio workflow naturally halts at the "Proposed Settings" view. You click "Confirm & Print" to advance. 

---

## 6. CONTEXT/PROMPT INJECTION

**How it actually works (Extrapolated / `hubAgent.ts`):**
The prompt is a massive template literal where state (`job.steps`, `networkState`, `capabilities`) is string-interpolated directly into the LLM context just before inference.

**Carry forward:**
- System prompt assembly via structured string building.

**Leave behind (over-scope):**
- Dynamic file-based guideline loading (`pi-guideline-loader` style). Keep it hardcoded in a `prompts.py` file for a 10-day sprint.

**Minimal Python shape:**
A `build_system_prompt()` function that concatenates: 
1. The static Chief Engineer Persona.
2. The current Job + Environment.
3. 2-3 matched lessons from the ledger injected as a "Historical Precedent" text block.

---

## 7. DOMAIN TYPES

**How it actually works (`core/src/types.ts`):**
The codebase relies heavily on network/economic primitives: `Capability`, `Material`, `NodeState`, `EnergyState`, `TickSnapshot`, `RoutingDecision`.

**Carry forward (rename/adapt):**
- `Job` (but stripped down to geometry info and material, no economic values).
- `Decision` (the LLM's structured output).

**Leave behind (over-scope):**
- Everything related to network routing, money/balances, capabilities matching, and energy/tick states.

**Minimal Python shape:**
Use Pydantic models for strict type checking before Ollama generation.
- `Job` (geometry features, material)
- `Environment` (temp, humidity)
- `PrintSettings` (temp, retraction, fan speed)
- `RiskRegion` (description of predicted failure)

---

## 8. Is there anything in the existing code that already does environment-keyed lesson storage or proactive (pre-job) prediction?

**No.** I reviewed the code carefully. The current system is purely a *reactive routing engine*. `hubAgent.ts` adjusts floating-point confidences based on job routing outcomes. It does not track temperature or humidity, and it does not make physics or overhang predictions prior to execution. The compounding "environment-keyed lesson" thesis is entirely new to this hackathon build. You are starting fresh on this feature.

---

## 9. Proposed Python Lesson Schema

To make lessons easily retrievable and environment-keyed without complex vector databases, use this flat Pydantic/JSON schema:

```python
class LessonEntry(BaseModel):
    job_id: str
    material: str             # e.g., "PLA", "PETG"
    geometry_type: str        # e.g., "overhang", "bridge", "vase"
    env_temp: float           # Ambient temperature °C
    env_humidity: float       # Ambient humidity %
    outcome: str              # "success", "failed_sag", "failed_stringing"
    lesson: str               # The LLM's compressed text reflection
    timestamp: str
```
*(Retrieval becomes a simple query: `where material == current_material and distance(env) < threshold`)*

---

## 10. Questions For You (Ambiguities / Decisions to Make)

1. **Geometry Inputs:** Since we are ditching physics simulation, how exactly is the job's geometry represented to Gemma? Are you passing in raw text descriptions ("It's a cube with a 45-degree overhang") or are you extracting features from `trimesh` (e.g. "Overhang Volume: 12mm³") and passing those?
2. **Environment Simulation:** If you use a slider for the DHT22 simulation in Gradio, should the "post-print reflection" outcome also be simulated via a slider/button (e.g. clicking "Print Failed: Sagged"), or do you want the LLM to somehow guess the outcome? *(I highly recommend a manual outcome button for the demo).*
3. **Retrieval Metric:** Do you want to retrieve prior lessons strictly by exact material match + Euclidean distance of the `[temp, humidity]` vector? 
4. **Seed Ledger:** You plan to write 8-12 seed lessons. Where do these live? Are they injected on startup, or just permanently sit at the top of the `lessons.jsonl` file?
