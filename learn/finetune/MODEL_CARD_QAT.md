---
base_model: google/gemma-4-E4B-it-qat-q4_0-unquantized
library_name: peft
license: gemma
tags:
- lora
- 3d-printing
- microfactory
- build-small-hackathon
- peft
- chief-engineer
- qat
---

# Microfactory Node: 3D Printer (LoRA v3 QAT)

I trained this LoRA on top of the QAT-trained `gemma-4-E4B-it-qat-q4_0-unquantized` base. It runs parallel to v2: the same O'Brien judgment, but I wanted to see if fine-tuning on a Quantization-Aware-Trained base keeps more quality after q4_0 GGUF conversion.

## What it does

Give it a print job — material, geometry, room temperature and humidity — and it returns structured **Advice JSON**:
- **Settings**: nozzle_temp, bed_temp, retraction_mm, fan_pct, first_layer_fan_pct
- **Risk regions**: where on the part, what risk, why, anchor hint
- **Reasoning**: what transfers from prior knowledge and why

## Training

| Parameter | Value |
|-----------|-------|
| Base model | `google/gemma-4-E4B-it-qat-q4_0-unquantized` |
| Method | LoRA (PEFT) |
| Rank | r=4, α=8 |
| Epochs | 1 |
| Learning rate | 2e-4 |
| Batch size | 2 × 4 gradient accumulation |
| Max sequence length | 1536 |
| Dataset | 180 train / 80 eval (live-generated on Modal A10G) |
| GPU | NVIDIA A10G (24GB) |
| Framework | TRL SFTTrainer + transformers 5.x |

Same low-rank, single-epoch setup as v2. The variable is the QAT base.

## Dataset

I generated the training set by driving the base model across a grid of 4 materials × 5 geometries × 3 temperatures × 3 humidities (train), with 2 temperatures × 2 humidities held out for eval. Each example is a chat-format pair: system prompt describing the job → structured Advice JSON response.

I kept targets noisy — temperature=0.7, top_p=0.95 — to prevent template memorization.

## Usage

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

tok = AutoTokenizer.from_pretrained("google/gemma-4-E4B-it-qat-q4_0-unquantized")
base = AutoModelForCausalLM.from_pretrained(
    "google/gemma-4-E4B-it-qat-q4_0-unquantized",
    dtype=torch.bfloat16,
    device_map="auto"
)
tuned = PeftModel.from_pretrained(base, "kylebrodeur/microfactory-node-lora-v3-qat")

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
| v2 | gemma-4-E4B-it | r=4 | 1 | live-generated | ✅ Well-Tuned |
| **v3** | **gemma-4-E4B-it-qat-q4_0-unquantized** | **r=4** | **1** | **live-generated** | **✅ Well-Tuned (QAT-trained — better fidelity after q4_0 quant)** |

v1 taught me what not to do. v3 tests whether QAT pre-training helps the quantized artifact.

## Limitations

This adapter is narrow by design, and it will fail loudly outside that narrow band.

- **Materials and geometries outside the training grid** — The grid covered four materials and five geometries. Hand it an exotic filament or an unusual geometry and it will guess confidently. That guess is extrapolation, not recall.
- **Humid PETG stringing** — Small Gemmas can return perfectly valid JSON with bad physics. During early driving I saw a lesson recommend slightly higher nozzle temperature to fight humid-PETG stringing, when the correct move is lower. Schema validation does not catch that. The human reads the plan before it runs.
- **Multi-tool or multi-material prints** — These were not in the training grid. Expect invented tool-change behavior.
- **ABS without an enclosure** — The model may propose settings that ignore chamber drafts. The Spine clamps individual values, but it does not model enclosure physics.
- **Mechanically risky combinations** — Very small layer heights paired with aggressive retraction can pass JSON schema and still fail on the bed. That is why La Forge inspects and the human decides.
- **No live sensor feedback** — It predicts from precedent and stops. It does not see actual bed adhesion, layer curling, or nozzle state. The printer and the human close the loop.
- **QAT-specific quant mismatch** — The QAT base was trained for q4_0. If you pick q4_k_m you get a balanced default, but it is slightly off the quant the base prepared for. Use q4_0 for highest fidelity.
- **Single-epoch, low-rank LoRA on a specialized base** — It has not deeply rewritten base knowledge, and the QAT base is already a specialized artifact. Ask it something far from 3D printing and it may behave less like general Gemma than v2 does. That is the trade-off.

## Try it via GGUF (Ollama / llama.cpp)

Two quantized GGUFs of this adapter, merged into the QAT base, are published.
Both live in [`kylebrodeur/microfactory-node-gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf)
and on the public Ollama registry:

| Quant | HF Hub file | `ollama run …` (registry tag) | Why pick this one |
|-------|-------------|--------------------------------|-------------------|
| q4_k_m | [`microfactory-node-v3-qat.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat.gguf) (5.1 GB) | [`kylebrodeur/microfactory-node-v3-qat`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat) | Balanced default |
| q4_0 (QAT-native) | [`microfactory-node-v3-qat-q4_0.gguf`](https://huggingface.co/kylebrodeur/microfactory-node-gguf/blob/main/microfactory-node-v3-qat-q4_0.gguf) (4.9 GB) | [`kylebrodeur/microfactory-node-v3-qat:q4_0`](https://ollama.com/kylebrodeur/microfactory-node-v3-qat:q4_0) | Highest fidelity — this is the quant the QAT base was trained for |

```bash
# Public Ollama registry (one-liner)
ollama run kylebrodeur/microfactory-node-v3-qat        # q4_k_m, recommended
ollama run kylebrodeur/microfactory-node-v3-qat:q4_0   # QAT-native quant

# Direct from HF Hub (template/system/params auto-applied)
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat-q4_0.gguf
```

See the
[full publishing runbook](https://github.com/kylebrodeur/microfactory-node/blob/main/learn/finetune/OLLAMA_PUBLISHING.md)
for the merge → quantize → upload pipeline. The non-QAT sibling lives at
[`microfactory-node-lora-v2`](https://huggingface.co/kylebrodeur/microfactory-node-lora-v2).

## License

This adapter inherits the [Gemma license](https://ai.google.dev/gemma/terms) from its base model.
