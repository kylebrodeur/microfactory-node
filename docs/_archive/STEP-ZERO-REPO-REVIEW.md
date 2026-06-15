# Step Zero: Repo Pattern Review

**Handoff prompt for an agent with filesystem access to your repos. Run before the June 5 build window — feeds the Chief Engineer Hackathon Plan.**

---

## Why this is a separate prompt

This review needs to read the actual code in `microfactory-lab` and the connected pi packages/extensions. That requires an agent with real filesystem or repo access — a pi session, Claude Code, Cursor, or any agent you can point at the cloned repos. An assistant working only from descriptions would be guessing at your patterns, which is exactly what this step exists to avoid.

The output feeds directly into the Python reimplementation in the build plan. The goal is to carry forward proven patterns and deliberately leave behind everything that doesn't serve a 10-day solo Gradio build.

> **The one rule that governs this review:**
> Extract patterns to reimplement in Python. Do **NOT** port the TypeScript, and do **NOT** recreate the full pi architecture. The moment this becomes "rebuild the whole system in Python," it has stopped serving the hackathon and started competing with it. Capture the shapes; leave the implementation.

---

## Repos and packages to review

Point the agent at whichever you have cloned. The first is the application; the rest are the connected pi infrastructure whose logic the app depends on.

- **microfactory-lab** — the application. Focus: `packages/agents` (hubAgent, nodeAgent), `packages/core` (domain types), `packages/engine` (the DES loop), `packages/scenarios`, and `pi-qmd-ledger.config.json`.
- **pi-qmd-ledger** — append-only JSONL ledger with hybrid/semantic search. The compression/expansion store is modeled on this.
- **pi-model-router** — tier routing (high/medium/low) by intent/budget/context. Relevant only for how routing decisions are structured, not for in-window use.
- **pi-context / pi-guideline-loader** — context assembly and guideline injection. Relevant to how lessons get injected into a system prompt.
- **pi-agent-bus** — inter-agent messaging / pub-sub. Relevant for the HITL and knowledge-update flow patterns.
- **UACS (universal-agent-context)** — skill/context format translation, if relevant to lesson representation.

---

## The prompt

Paste everything in the block below into the agent session that has the repos. Adjust the repo list to what you actually have cloned.

---

You have filesystem access to my repositories. I'm building a solo Gradio app for the Hugging Face Build Small hackathon (June 5–15) called the **Chief Engineer** — a small local Gemma model that compresses expert 3D-printing knowledge into environment-keyed lessons and expands them proactively into future jobs. I will reimplement the relevant patterns in **PYTHON**. I am NOT porting TypeScript and NOT recreating the full system.

Your job is a **PATTERN REVIEW, not a rewrite**. Read the actual code and produce a "carry forward / leave behind" digest I can build from. Do not write application code yet.

**REVIEW THESE REPOS** (read, do not assume): microfactory-lab (`packages/agents`, `core`, `engine`, `scenarios`; `pi-qmd-ledger.config.json`), pi-qmd-ledger, pi-model-router, pi-context, pi-guideline-loader, pi-agent-bus, UACS. Skip any I haven't cloned and say which were missing.

**FOR EACH** of the following pattern areas, report: (a) how it actually works in my code, with specific `file:function` references; (b) the minimal version worth reimplementing in Python for a 10-day solo build; (c) what to deliberately leave behind as over-scope for a hackathon.

1. **AGENT STRUCTURE** — How HubAgent structures an LLM call: prompt assembly, how system instructions are built, how structured output (settings/decisions) is parsed and validated, error handling. What's the smallest Python equivalent?
2. **BRAIN/SPINE VETO** — How the deterministic NodeAgent validates/vetoes the LLM's proposal (capacity, capability, power budget). What are the exact constraint checks, and what's the minimal Python validator that preserves "LLM proposes, deterministic layer vetoes"?
3. **LEDGER** — How pi-qmd-ledger keys, writes, and retrieves entries. What fields/schema make an entry retrievable? How does the hybrid/semantic search work, and what's the lightest Python retrieval that gives me "find prior lessons matching this job + environment" (e.g. embedding similarity vs keyword vs hybrid)?
4. **KNOWLEDGE FLOW** — How knowledge_update / federated lessons propagate between nodes (`handleKnowledgeUpdate` and related). What's the compression step — how is a raw outcome distilled into a reusable lesson? This is the thesis-critical part: report exactly how (or whether) my current code compresses and expands knowledge.
5. **HITL GATE** — How the human-in-the-loop confirmation works: what triggers it (confidence/value thresholds), how the pause/resume resolves (hitlResolvers pattern). What's the minimal Gradio-friendly equivalent (a state flag + an approve button)?
6. **CONTEXT/PROMPT INJECTION** — How pi-context / pi-guideline-loader assemble context and inject guidelines into a prompt. How should retrieved lessons be formatted and injected into the Gemma system instruction?
7. **DOMAIN TYPES** — From `packages/core`: which domain types (Job, NodeState, Capability, etc.) are worth carrying into the Python model as dataclasses/pydantic, and which are lab-specific noise?

**ALSO ANSWER:** Is there anything in the existing code that already does environment-keyed lesson storage or proactive (pre-job) prediction? Or is the current system reactive/routing-only? Be honest — I need to know what exists vs what I'm building fresh.

**OUTPUT FORMAT:** A markdown digest organized by the 7 pattern areas above, each with carry-forward / leave-behind / minimal-Python-shape. End with: (a) a proposed Python **lesson schema** (the fields that make a lesson retrievable and environment-keyed), and (b) a list of 3–7 questions for me where the code was ambiguous or where a design decision is mine to make.

**CONSTRAINTS:** Cite real `file:function` references — if you can't find something, say so, don't invent it. Flag anything in the code that overclaims relative to what's implemented (I have a recurring issue with strategy docs claiming features the code doesn't have — catch it). Keep the digest tight; this feeds a build, not an archive.

---

## After the digest comes back

Bring the digest back to the build conversation. It will sharpen three things in the plan that are currently described generically:

- The Python **lesson schema** (the single most important design decision — it determines whether compounding is legible).
- The **retrieval mechanism** (embedding vs keyword vs hybrid) for matching prior lessons to a new job + environment.
- The exact **compression step** — how a resolved job becomes a durable lesson — which is the thesis-critical logic.

Then the agent-sourced seed-lesson pipeline (agents discover candidate lessons from HF/Kaggle/GH, you approve) can be designed against the real schema rather than a guessed one. Recommendation from the plan still stands: hand-write the first 8–12 lessons to guarantee a quality corpus exists, then build the discovery pipeline as the mechanism that grows it — so you are never blocked on the pipeline working.

> **Sequencing reminder:** This review is pre-window foundation work. Do it alongside the two no-bugs-until-you-need-them tasks (deploy a trivial Gradio Space with a static `gr.Model3D` cube; measure Gemma CPU latency on Space hardware) and registering before June 3. None of these are the build — they are what make the June 5 build start from solid ground instead of discovery.
