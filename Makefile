.PHONY: setup setup-zerogpu assets run test demo bench trace deliberation preflight deploy-check deploy record record-check record-auto

# Local dev uses uv (fast, locked). The HF Space still installs via pip+requirements.txt.
# Entrypoints: app.py + test_core.py at root; helper scripts live in scripts/ and run
# as modules (-m scripts.<name>) so the repo root is importable for `from core...`.
setup:      ## create/sync the uv env (locked) + generate sample meshes
	uv sync
	uv run python -m scripts.make_assets

setup-zerogpu: ## sync incl. the ZeroGPU live-inference extra (deploy/testing only)
	uv sync --extra zerogpu
	uv run python -m scripts.make_assets

assets:     ## (re)generate sample meshes for the 3D preview
	uv run python -m scripts.make_assets

run:        ## launch the Gradio app (needs `ollama serve` for live inference)
	uv run python app.py

test:       ## headless core tests (no Ollama required)
	uv run python test_core.py

preflight:  ## GO/NO-GO gate on the real stack (see RUNBOOK)
	uv run python -m scripts.preflight

deploy-check: ## deploy/record readiness gate (offline: build + files + creds + Space + dataset)
	uv run python -m scripts.deploy_preflight

deploy:     ## run the gates, then UPDATE the Space files (hf upload) + factory reboot (needs HF_TOKEN)
	uv run python -m scripts.deploy_preflight --push

publish:    ## deploy to HF Space + sync the public GitHub mirror (needs HF_TOKEN + gh auth)
	uv run python -m scripts.publish

publish-dry: ## show what publish would change without pushing
	uv run python -m scripts.publish --dry-run

publish-mirror: ## sync only the public GitHub mirror (skip Space push)
	uv run python -m scripts.publish --mirror-only

demo:       ## scripted integration run / video-beat dry run
	uv run python -m scripts.scripted_demo

bench:      ## measure model latency on this hardware (needs Ollama)
	uv run python -m scripts.bench_latency

trace:      ## export the lesson ledger as a HF Datasets-ready trace
	uv run python -m scripts.export_trace

deliberation: ## export the multi-persona deliberation as a HF Datasets-ready trace
	uv run python -m scripts.export_deliberation

record-check: ## recording preflight (cap-cli + Space + playwright gates)
	uv run python -m scripts.record --preflight-only

record:     ## full recording (manual mode): preflight → cap → beat cues → export mp4
	uv run python -m scripts.record

record-cues: ## beat cues only (no cap) — you record with Cap desktop at high quality
	uv run python -m scripts.record --mode cues

record-auto: ## recording with Playwright auto-driver (WSL only)
	uv run python -m scripts.record --mode auto
