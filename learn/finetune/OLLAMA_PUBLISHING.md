# Publishing GGUFs to ollama.com — runbook & decision log

Date: 2026-06-14. This documents how the Chief Engineer GGUFs got listed on the public Ollama registry at `ollama.com/kylebrodeur/microfactory-node-*`. I wrote it so the next adapter, quant, or mistake is reproducible.

## TL;DR — what got pushed

| Ollama tag | Source GGUF (HF Hub) | Quant | Size | Notes |
|---|---|---|---|---|
| `kylebrodeur/microfactory-node-v3-qat` | `microfactory-node-v3-qat.gguf` | q4_k_m | 5.3 GB | **Recommended.** QAT model, balanced quant |
| `kylebrodeur/microfactory-node-v3-qat:q4_0` | `microfactory-node-v3-qat-q4_0.gguf` | q4_0 | 4.9 GB | QAT-native quant (best fidelity for the QAT model) |
| `kylebrodeur/microfactory-node-v2` | `microfactory-node-v2.gguf` | q4_k_m | 5.3 GB | Standard E4B fine-tune |
| `kylebrodeur/microfactory-node` | `microfactory-node.gguf` | q4_k_m | 5.3 GB | First fine-tune (v1, historical) |

All four are public on `https://ollama.com/kylebrodeur` and pullable with one command:

```bash
ollama run kylebrodeur/microfactory-node-v3-qat        # recommended
ollama run kylebrodeur/microfactory-node-v3-qat:q4_0   # QAT-native quant
ollama run kylebrodeur/microfactory-node-v2
ollama run kylebrodeur/microfactory-node
```

The same files are also pullable from HF directly (no ollama.com round-trip). See the HF-direct path at the bottom of this doc.

---

## The pipeline (end-to-end, what actually happened)

```
LoRA adapter (HF Hub)
        │
        │ modal run gguf_pipeline_modal.py::main --upload <repo>
        ▼
Merged HF model (Modal GPU volume)
        │
        │ llama.cpp convert_hf_to_gguf.py → bf16 GGUF
        │ llama-quantize → q4_k_m (or q4_0)
        ▼
GGUF on Modal volume
        │
        │ HfApi.upload_file (huggingface_hub)
        ▼
HF Hub: kylebrodeur/microfactory-node-gguf/<name>.gguf
        │
        │ ollama pull hf.co/kylebrodeur/microfactory-node-gguf:<filename>.gguf
        ▼
Local ollama store (`/usr/share/ollama/.ollama/models/`)
        │
        │ ollama cp <hf.co-tag> kylebrodeur/<short-name>
        │ ollama push kylebrodeur/<short-name>
        ▼
ollama.com/kylebrodeur/<short-name>
```

Every box left of `ollama.com` is automated. The two manual one-time steps are generating an Ollama SSH keypair and registering it on your ollama.com profile.

---

## One-time setup

### 1. Ollama account on `ollama.com`

Sign up at <https://ollama.com>. The username you pick becomes the namespace prefix on every model you publish (`<username>/<model>`). I used `kylebrodeur` to match my GitHub and Hugging Face handles. Keeping the three in sync makes documentation and cross-linking sane.

### 2. Generate an Ollama SSH key

The system Ollama daemon (typically `/usr/share/ollama/.ollama/`) does NOT own your push credentials. The `ollama push` client looks for an ED25519 keypair in `~/.ollama/` for the invoking user. Generate it once:

```bash
ssh-keygen -t ed25519 -f ~/.ollama/id_ed25519 -N "" -C "<your-handle>-ollama" -q
cat ~/.ollama/id_ed25519.pub
```

Ollama itself will lazily create this on first push, but only inside the daemon's home dir (e.g. `/usr/share/ollama/.ollama/`). When the daemon runs as a different user (typical on Linux package installs), the client-side push uses YOUR home dir. Generate it there explicitly.

### 3. Register the public key on ollama.com

Open <https://ollama.com/settings/keys>, click Add Ollama Public Key, paste the contents of `~/.ollama/id_ed25519.pub`. Save.

That is the entire auth surface — no API token, no `ollama login`. Pushes authenticate via that ED25519 signature on every request.

---

## Per-model publishing flow

Given an adapter at `kylebrodeur/microfactory-node-lora-vN` on HF Hub:

### A. Build & upload the GGUF (Modal)

`learn/finetune/gguf_pipeline_modal.py` has three Modal functions (`merge` on GPU → `convert_to_gguf` on CPU → `upload_to_hub` on CPU) and two entrypoints (`::main` for the full pipeline, `::upload_only` for re-uploading something already on the volume).

```bash
PYFILE=/home/kylebrodeur/projects/microfactory-lab/chief-engineer/learn/finetune/gguf_pipeline_modal.py

# Full pipeline (merge → quantize → upload), q4_k_m by default:
modal run "${PYFILE}::main" \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat \
  --name microfactory-node-v3-qat \
  --upload kylebrodeur/microfactory-node-gguf

# Same adapter, q4_0 quant for the QAT model — note --outtype + --as-name to
# avoid overwriting the q4_k_m on HF that shares the same --name on the volume:
modal run "${PYFILE}::main" \
  --adapter kylebrodeur/microfactory-node-lora-v3-qat \
  --name microfactory-node-v3-qat \
  --outtype q4_0 \
  --upload kylebrodeur/microfactory-node-gguf

# If the file already sits on the Modal volume, just upload it (no re-quantize):
modal run "${PYFILE}::upload_only" \
  --name microfactory-node-v3-qat \
  --repo kylebrodeur/microfactory-node-gguf \
  --as-name microfactory-node-v3-qat-q4_0   # distinct HF filename
```

### B. Pull from HF into local Ollama

Ollama's native HF integration is the fastest pull path. I saw 10 MB/s+ versus ~30 MB/min via `hf download` Xet warm-up for the same file. Always specify the GGUF filename as a tag so Ollama picks the right one:

```bash
ollama pull hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf
```

This stores it under that full ID in `ollama list`:

```
hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf  5.3 GB
```

### C. Rename for the ollama.com namespace

Ollama push requires a `<username>/<name>[:<tag>]` ID. The `hf.co/...` ID is not pushable as-is. Use `ollama cp` to create the publishable alias:

```bash
# default tag (becomes `:latest`)
ollama cp "hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf" \
          kylebrodeur/microfactory-node-v3-qat

# alternate tag for the q4_0 variant
ollama cp "hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat-q4_0.gguf" \
          kylebrodeur/microfactory-node-v3-qat:q4_0
```

### D. Push to ollama.com

```bash
ollama push kylebrodeur/microfactory-node-v3-qat
ollama push kylebrodeur/microfactory-node-v3-qat:q4_0
```

Push speed is gated by Ollama's CDN ingest (~5 MB/s in my run, ~15 min per 5 GB model). It chunks + dedups across all models you push, so the second push of a model that shares any blobs with the first is much faster.

### E. Verify

```bash
ollama list | grep kylebrodeur
# kylebrodeur/microfactory-node-v3-qat:latest  f22b6f19f805  5.3 GB
# kylebrodeur/microfactory-node-v3-qat:q4_0    ...           4.9 GB
# kylebrodeur/microfactory-node-v2:latest      ...           5.3 GB
# kylebrodeur/microfactory-node:latest         ...           5.3 GB

# Test on a fresh machine:
ollama run kylebrodeur/microfactory-node-v3-qat
>>> PLA overhang at 22C, 45% humidity
```

The model card on `ollama.com/kylebrodeur/<name>` populates automatically from the `Modelfile` metadata once the manifest is uploaded.

---

## Doing it for all 3 (or 4) variants in one shot

`/tmp/all-pushes.sh` is the script I used. It runs detached, logs to `/tmp/all-pushes.log`, and processes v3-qat → v2 → v1 serially (pull → cp → push):

```bash
#!/usr/bin/env bash
set -uo pipefail
LOG=/tmp/all-pushes.log
exec >>"$LOG" 2>&1
step() { printf "\n[%s] %s\n" "$(date -u +%H:%M:%S)" "$*"; }

step "v3-qat: cp + push (already pulled)"
ollama cp "hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf" \
          kylebrodeur/microfactory-node-v3-qat || true
ollama push kylebrodeur/microfactory-node-v3-qat

step "v2: pull + cp + push"
ollama pull hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v2.gguf
ollama cp "hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v2.gguf" \
          kylebrodeur/microfactory-node-v2
ollama push kylebrodeur/microfactory-node-v2

step "v1: pull + cp + push"
ollama pull hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node.gguf
ollama cp "hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node.gguf" \
          kylebrodeur/microfactory-node
ollama push kylebrodeur/microfactory-node

step "DONE"
ollama list | grep kylebrodeur
```

Launch:

```bash
chmod +x /tmp/all-pushes.sh
nohup setsid /tmp/all-pushes.sh </dev/null >/dev/null 2>&1 &
disown
tail -f /tmp/all-pushes.log
```

`setsid` + `</dev/null` + `disown` is what kept it alive across my own shell exits during the ~60 min total runtime.

---

## Gotchas hit (and the fixes)

### G1 — Ollama keys live in YOUR home, not the daemon's

On Linux package installs the daemon usually runs as the `ollama` user with `HOME=/usr/share/ollama`. `ollama push` (client) signs with whatever user is invoking it — so `~/.ollama/id_ed25519` must exist for you. Generating it with `ssh-keygen -t ed25519 -f ~/.ollama/id_ed25519 -N ""` is faster than poking at the daemon to lazy-create it.

### G2 — `hf download` via Xet was 20–30× slower than `ollama pull hf.co/...`

I started with `hf download kylebrodeur/microfactory-node-gguf microfactory-node-v3-qat.gguf` expecting Xet acceleration; got ~30 MB in 60 s (looked stuck). Killed it and ran `ollama pull hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf` instead — 10–11 MB/s immediately, ETA ~8 min. The HF→Ollama path uses HTTP range requests against the LFS-backed file, skipping the Xet handshake.

### G3 — `modal run gguf_pipeline_modal.py` fails after a second `@app.local_entrypoint()`

Once the file has more than one entrypoint, Modal demands you disambiguate:

```
Error: > modal run /.../gguf_pipeline_modal.py::my_function [..args]
'.../gguf_pipeline_modal.py' has the following functions and local entrypoints:
  upload_only / app.upload_only
  main / app.main
  ...
```

Always pass `::main` or `::upload_only` explicitly once that second entrypoint exists.

### G4 — HF tokens stored as Modal secrets can carry trailing whitespace

The first upload attempt failed with:

```
httpx.LocalProtocolError: Illegal header value b'Bearer  hf_xxx  '
```

…because the value pasted into Modal's secret editor had a leading space and a trailing newline. The upload helper now does `token.strip()` before passing it to `HfApi`. Worth doing in any code reading Modal secrets generally.

### G5 — `nohup &` + `&&`-chained `modal run` lose cwd

Several backgrounded `modal run` invocations failed because Modal resolved a stale `cwd` and tried to load the pipeline file from the wrong path. Two mitigations: always pass an absolute path to the `.py` file, and chain via `setsid` rather than the shell's job control.

### G6 — Overlapping filenames between Modal volume and HF repo

The Modal pipeline derives both the volume path (`/out/gguf/<name>.gguf`) and the HF path (`<repo>/<name>.gguf`) from the same `--name`. Generating the q4_0 variant of a model that already has a q4_k_m on HF would silently overwrite unless you split the names. I added `--as-name <hf-filename>` to `upload_only` so the HF target can differ from the volume source:

```bash
modal run ...::upload_only --name microfactory-node-v3-qat \
  --as-name microfactory-node-v3-qat-q4_0 \
  --repo kylebrodeur/microfactory-node-gguf
```

For full pipeline runs, append `-q4_0` to `--name` directly so both layers stay in sync. The volume keeps a copy too.

### G7 — `ollama push` needs `<user>/<name>` exactly

You cannot push a model whose ID starts with `hf.co/...` or any other non-username prefix. `ollama cp` is the only way to rename, and the new name must match `<username>/<model>` where `<username>` equals your registered ollama.com handle.

---

## HF-direct path (alternative to ollama.com)

For users who just want to run the model locally without pulling from ollama.com, the same GGUFs live on HF Hub and Ollama supports `hf.co/...` URIs natively. The HF repo also holds `template`, `system`, and `params` files so the chat template, persona, and sampling apply automatically:

```bash
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat-q4_0.gguf
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v2.gguf
ollama run hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node.gguf
```

The `ollama.com/kylebrodeur/...` tags exist for discoverability via the public registry. The HF-direct URIs are the canonical, single-source-of-truth distribution. Both paths point at the same blobs.

---

## Cleanup

The pulled `hf.co/...` tags can be removed once they've been cp'd into the `kylebrodeur/...` namespace. Both share the same underlying blob in the content-addressed Ollama store, so deleting the alias is free:

```bash
ollama rm hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat.gguf
ollama rm hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v3-qat-q4_0.gguf
ollama rm hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node-v2.gguf
ollama rm hf.co/kylebrodeur/microfactory-node-gguf:microfactory-node.gguf
```

The `kylebrodeur/...` tags keep working because the manifest still references the same blob digests.
