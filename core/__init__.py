"""Core library for the Chief Engineer (models, LLM, ledger, spine, advisor).
Imported as a package; entrypoints live at the repo root (app.py) and in scripts/."""

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Tiny stdlib .env loader (no python-dotenv dep): reads KEY=VALUE lines from
    the repo root .env. Real environment always wins (setdefault), so
    `CHIEF_ENGINEER_MODEL=x make run` still overrides the file."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.is_file():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k:
            os.environ.setdefault(k, v)


_load_dotenv()
