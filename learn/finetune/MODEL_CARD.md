---
base_model: google/gemma-4-E4B-it
library_name: peft
license: gemma
tags:
- lora
- 3d-printing
- microfactory
- build-small-hackathon
- peft
- chief-engineer
---

# Microfactory Node: 3D Printer (LoRA v2)

I trained this LoRA to bake Chief Engineer O'Brien's judgment into Gemma 4 E4B. The live node still reads from the lesson ledger; this adapter is what happens when I try to put that ledger into the weights instead.

## What it does

Give it a print job — material, geometry, room temperature and humidity — and it returns structured **Advice JSON**:
- **Settings**: nozzle_temp, bed_temp, retraction_mm, fan_pct, first_layer_fan_pct
- **Risk regions**: where on the part, what risk, why, anchor hint
- **Reasoning**: what transfers from prior knowledge and why

## Training

| Parameter | Value |
|-----------|-------|
| Base model | `google/gemma-4-E4B-it` |
| Method | LoRA (PEFT) |
| Rank | r=4, α=8 |
| Epochs | 1 |
| Learning rate | 2e-4 |
| Batch size | 2 × 4 gradient accumulation |
| Max sequence length | 1536 |
| Dataset | 180 train / 80 eval (live-generated on Modal A10G) |
| GPU | NVIDIA A10G (24GB) |
| Framework | TRL SFTTrainer + transformers 5.x |

I kept rank low and epochs at one on purpose. v1 used r=16 for three epochs on deterministic targets and parroted the same settings for every input. This run sacrifices raw capacity for actual attention to the job.

## Dataset

I generated the training set by driving the base model across a grid of 4 materials × 5 geometries × 3 temperatures × 3 humidities (train), with 2 temperatures × 2 humidities held out for eval. Each example is a chat-format pair: system prompt describing the job → structured Advice JSON response.

I kept targets noisy — temperature=0.7, top_p=0.95 — so the model cannot memorize a single template. v1 proved that deterministic targets and a high rank just produce a parrot. Noise forces judgment.

## Usage

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

tok = AutoTokenizer.from_pretrained("google/gemma-4-E4B-it")
base = AutoModelForCausalLM.from_pretrained(
    "google/gemma-4-E4B-it",
    dtype=torch.bfloat16,
    device_map="auto"
)
tuned = PeftModel.from_pretrained(base, "kylebrodeur/microfactory-node-lora-v2")

messages = [{"role": "user", "content": "Your prompt here"}]
inputs = tok.apply_chat_template(messages, return_tensors="pt", add_generation_prompt=True).to(tuned.device)
out = tuned.generate(**inputs, max_new_tokens=512, do_sample=True, temperature=0.7)
print(tok.decode(out[0], skip_special_tokens=True))
```

## Safety

This adapter proposes settings. It does not validate them. A deterministic Spine clamps every proposed value against hard material bounds before any printer sees them. The LoRA gives the opinion; the Spine has the veto.

## Iteration history

| Version | Base | Rank | Epochs | Dataset | Result |
|---------|------|------|--------|---------|--------|
| v1 | gemma-3-1b-it | r=16 | 3 | deterministic | ❌ Parroted template |
| **v2** | **gemma-4-E4B-it** | **r=4** | **1** | **live-generated** | **✅ Well-Tuned (100% JSON-valid, 100% Spine-safe, real judgment)** |

v1 taught me what not to do.

## Limitations

This adapter is narrow by design, and it will fail loudly outside that narrow band.

- **Materials and geometries outside the training grid** — The grid covered four materials and five geometries. Hand it an exotic filament or an unusual geometry and it will guess confidently. That guess is extrapolation, not recall.
- **Humid PETG stringing** — Small Gemmas can return perfectly valid JSON with bad physics. During early driving I saw a lesson recommend slightly higher nozzle temperature to fight humid-PETG stringing, when the correct move is lower. Schema validation does not catch that. The human reads the plan before it runs.
- **Multi-tool or multi-material prints** — These were not in the training grid. Expect invented tool-change behavior.
- **ABS without an enclosure** — The model may propose settings that ignore chamber drafts. The Spine clamps individual values, but it does not model enclosure physics.
- **Mechanically risky combinations** — Very small layer heights paired with aggressive retraction can pass JSON schema and still fail on the bed. That is why La Forge inspects and the human decides.
- **No live sensor feedback** — It predicts from precedent and stops. It does not see actual bed adhesion, layer curling, or nozzle state. The printer and the human close the loop.
- **Single-epoch, low-rank LoRA** — It has not deeply rewritten the base model. Ask it something far from 3D printing and it answers like base Gemma. That is intentional.

## Try it via GGUF (Ollama / llama.cpp)

A quantized GGUF of this adapter, merged into the base model, is published as
[`kylebrodeur/microfactory-node-gguf` · `microfactory-node-v2.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v2.gguf)
(5.1 GB, q4_k_m) and on the public Ollama registry:

```bash
# Public Ollama registry (one-liner)
ollama run kylebrodeur/microfactory-node-v2

# Direct from HF Hub (template/system/params auto-applied)
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v2.gguf
```

See the
[full publishing runbook](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/OLLAMA_PUBLISHING.md)
for the merge → quantize → upload pipeline and the QAT-trained v3 sibling
([`microfactory-node-lora-v3-qat`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v3-qat)).

## License

This adapter inherits the [Gemma license](https://ai.google.dev/gemma/terms) from its base model.
