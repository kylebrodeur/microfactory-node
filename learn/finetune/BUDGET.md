# Fine-Tune Budget Tracking

Budget: **$100** total for Modal compute (fine-tuning + dataset generation + eval).
**Serving budget: Separate $100** for Modal inference API hosting (distinct from training).

## Training Budget (Spent)

| Date | Step | Description | Cost |
|------|------|-------------|------|
| 2026-06-13 | v1 smoke test | Gemma 3, 1 epoch, A10G | ~$0.04 |
| 2026-06-13 | v1 full train | Gemma 3, 3 epochs, A10G | ~$0.12 |
| 2026-06-13 | v1 eval | Gemma 3 base vs LoRA, A10G | ~$0.10 |
| 2026-06-13 | v1 image builds | 3 Modal images | ~$0.24 |
| 2026-06-13 | v2 dataset attempts | Multiple prep_dataset runs (sequential, failed) | $3.91 |
| 2026-06-13 | v2 eval attempts | Test eval runs | $0.68 |
| 2026-06-13 | v2 finetune attempts | Smoke tests | $0.12 |
| 2026-06-13 | v2 rich dataset | prep_dataset_rich.py parallel (12×A10G) | $0.85 |
| 2026-06-13 | v2 fast dataset | prep_dataset_fast.py | $1.60 |
| 2026-06-14 | v2 eval | Multiple eval runs and timeouts | $1.48 |
| 2026-06-14 | v2 & v3 finetune | Track A & B full training | $0.16 |
| **Training Subtotal** | | | **~$11.54** |
| **Training Remaining** | | | **~$88.46** |

## Serving Budget (Separate $100)

| Date | Step | Description | Est. Cost |
|------|------|-------------|-----------|
| 2026-06-14 | GGUF pipeline | merge→GGUF on Modal (GPU merge + CPU convert) | ~$0.15 |
| 2026-06-14 | Modal deploy | modal_serve.py image build | ~$0.08 |
| 2026-06-14 | Modal inference | A10G active (~$5.04/hr, scale-to-zero) | ~$0.50-2.00/day |
| **Serving Subtotal** | | | **~$0.23 + ongoing** |
| **Serving Remaining** | | | **~$99.77** |

## Cost per GPU Type (Modal)

| GPU | $/sec | $/hr | Use case |
|-----|-------|------|----------|
| A10G | $0.0014 | $5.04 | LoRA training, dataset gen, eval |
| A100 | $0.0036 | $12.96 | Faster dataset gen (3× speed) |
| H100 | $0.0056 | $20.16 | Not needed for 8B model |

## Agent Protocol: Activity Logging

Future agents picking up this work MUST follow this logging protocol:

1. **Log Format**: Every significant action, decision, or budget check must be appended to `learn/finetune/activity.jsonl`.
2. **Schema**: `{"timestamp": "ISO8601", "action": "category", "event": "specific_event", "details": "context"}`
3. **Backfilling**: When inheriting a task, read the `activity.jsonl` to understand the state. If you perform an action that was missed in the log, backfill it with an approximate timestamp.
4. **Billing Updates**: Any time a Modal job completes, query the billing API (see RUNBOOK.md) and log the exact cost in the `details` field.

## Budget Rules

1. Check `modal billing report --for today` before and after each Modal step
2. Log every cost to `activity.jsonl`
3. Never exceed $100 total
4. Prefer A10G over A100/H100 unless speed-critical
5. Parallel GPU jobs: count GPUs × time × rate
