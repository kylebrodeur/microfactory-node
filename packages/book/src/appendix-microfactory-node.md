---
title: "Microfactory Node: A Working Proof of Concept"
status: "draft"
---

# Appendix: Microfactory Node — 3D Printer

This is a clever proof of concept that works — not a production system. It is the first concrete node of the larger Microfactory idea: a small, local AI that learns a craft job by job so the craft cannot be lost.

I built it in ten days for the Hugging Face Build Small hackathon. The one judged moment is the Chief Engineer reading today's room against prior jobs before the nozzle moves: *"Humidity is higher than the job where this overhang sagged, so I'm raising retraction and adding support."* When nothing close exists, it says plainly *"no close precedent"* and reasons from material properties instead. Everything else — the two agents, the Spine, the ledger, the learned policy — is scaffolding for that moment.

## What it does

The node is a small local **Gemma** model running through **Ollama** on my own machine. Before a print runs it looks at the part, the material, and the room, retrieves the closest prior jobs it has already seen, and weighs what they teach about this one. Then it proposes settings and points at where the print will fail, before the nozzle moves.

Two named agents do the work. **Chief Engineer O'Brien** proposes. He reads the room, recalls precedent, commits to a plan, terse and physical. **La Forge** inspects. He is the skeptic who reads O'Brien's plan before anything prints and says where the optimism is thin. When La Forge disputes a plan, the print is held until I clear it. O'Brien is the optimist. La Forge is not. My grandfather was both at once. The model is never allowed to grade its own work.

The knowledge compounds. Every real outcome becomes one durable lesson, keyed to material, geometry, and the room, appended to a ledger the node reads from forever after. Job N+1 starts smarter than job N.

## How it is constrained

A model this size earns trust through constraints, not through scale. The surface is narrow: three or four setting levers. The Spine validates every proposed setting against hardcoded material bounds — PLA nozzle at 260°C gets clamped to 220°C and a human gate trips. La Forge grades the plan before it prints. A deterministic simulator provides ground truth for outcomes. The model grades neither.

This is retrieval plus reflection plus a small learned policy, not fine-tuning, and that is deliberate. Fine-tuning would bury the knowledge in the weights where you cannot watch it move. Retrieval keeps the memory visible: a lesson gets written after one job and pulled back up to shape the next, in plain sight. For craft you want to preserve and show, visible memory beats invisible memory.

It runs offline, on my own hardware, for $0 a month. The public Space runs the live model on ZeroGPU so you can see the real reasoning. If the GPU is cold or out of quota the node falls back to a deterministic advisor and the banner says so plainly.

## What is real and what is honest

- **Built:** condition-keyed retrieval, visible precedent evaluation, the Spine veto, O'Brien and La Forge, human-reported outcomes, the growing ledger, the learning loop, fully local Gemma inference, knowledge ingestion from slicer and firmware configs, and the two-agent integrity model.
- **Simulated (the one boundary):** print outcomes, via a deterministic physics-lite stand-in for the printer. The simulator was calibrated against 178 real FDM failure prints from a Modal ingestion run. The first pass read 34.2% because the parser only looked at G-code headers, so 178 of 260 rows had fan speed defaulting to zero. After cleaning that the score settled at 32.6%: correct on every clean success, blind to moderate failures. The gap is structural, not a knob to quietly turn. Rather than fake a prettier number, the gap is documented.
- **In progress:** a LoRA fine-tune on the accumulated ledger so the craft lives in the weights as well as the memory.
- **Frontier (not built):** real distributed multi-node execution, g-code streaming, live environmental sensors, camera-based defect detection.

## Distribution

The fine-tune produced four GGUFs, but a GGUF on a Modal volume is not a shippable artifact — it is a binary blob with no chat template, no system prompt, and no way for a stranger to try it. So I added the missing half of the pipeline: the same Modal app that quantizes the model also uploads it to HF Hub alongside `template`, `system`, and `params` files so `ollama run hf.co/…` works out of the box. Done means someone you've never met can pull and run it in one line.

## Links

- **Live app:** [node.microfactory.space](https://node.microfactory.space)
- **Demo video:** [Microfactory Node 3D Printer Interface Demo and AI‑Powered Print Optimization](https://cap.so/s/f346fkqk32krv5k)
- **Source code:** [kylebrodeur/microfactory-node](https://github.com/kylebrodeur/microfactory-node)
- **Lesson ledger:** [kylebrodeur/chief-engineer-ledger](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger)
- **Deliberation traces:** [kylebrodeur/chief-engineer-deliberation](https://huggingface.co/datasets/kylebrodeur/chief-engineer-deliberation)
- **Field log:** [build-small-hackathon/chief-engineer-field-log](https://huggingface.co/datasets/build-small-hackathon/chief-engineer-field-log)
- **Build activity trace:** [kylebrodeur/chief-engineer-build-activity](https://huggingface.co/datasets/kylebrodeur/chief-engineer-build-activity)
- **Fine-tune activity trace:** [kylebrodeur/chief-engineer-finetune-activity](https://huggingface.co/datasets/kylebrodeur/chief-engineer-finetune-activity)
- **Field notes (blog):** [Microfactory Node: Field Notes — building a shop-floor AI on a small local model](https://huggingface.co/blog/build-small-hackathon/microfactory-lab-field-notes) · dataset [`build-small-hackathon/microfactory-lab-field-notes`](https://huggingface.co/datasets/build-small-hackathon/microfactory-lab-field-notes)
- **Ollama models:** [ollama.com/kylebrodeur](https://ollama.com/kylebrodeur)
