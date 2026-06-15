"""Email signup for Microfactory updates.

Lightweight, privacy-first opt-in collection. Stores one JSONL row per signup:
{ts, email, consent, source, app_version}. Local runs write to data/signups.jsonl.
Space runs can additionally push to a private HF dataset via CommitScheduler if
SIGNUPS_DATASET and HF_TOKEN are set. Never writes without explicit consent.
"""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIGNUPS_FILE = Path(__file__).resolve().parent.parent / "data" / "signups.jsonl"
SIGNUPS_DATASET = os.environ.get("SIGNUPS_DATASET", "kylebrodeur/microfactory-signups").strip()
FLUSH_MINUTES = 5

_scheduler: Any = None
_lock = threading.Lock()

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def _get_scheduler():
    """Lazy-init CommitScheduler for the private signup dataset."""
    global _scheduler
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        return None
    if not SIGNUPS_DATASET or "/" not in SIGNUPS_DATASET:
        return None
    if _scheduler is None:
        with _lock:
            if _scheduler is None:
                try:
                    from huggingface_hub import CommitScheduler
                except ImportError:
                    return None
                SIGNUPS_FILE.parent.mkdir(parents=True, exist_ok=True)
                if not SIGNUPS_FILE.exists():
                    SIGNUPS_FILE.write_text("", encoding="utf-8")
                _scheduler = CommitScheduler(
                    repo_id=SIGNUPS_DATASET,
                    repo_type="dataset",
                    folder_path=str(SIGNUPS_FILE.parent),
                    every=FLUSH_MINUTES,
                    token=token,
                    allow_patterns=["signups.jsonl"],
                )
    return _scheduler


def is_active() -> bool:
    """True if signup syncing to HF is configured and active."""
    return _get_scheduler() is not None


def validate_email(email: str) -> str | None:
    """Return normalized email or None if invalid."""
    if not email:
        return None
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        return None
    return email


def record_signup(email: str, consent: bool, source: str = "local") -> tuple[bool, str]:
    """Record one signup. Returns (ok, message).

    Requires explicit consent. Email is validated. Writes locally always;
    pushes to HF only when HF_TOKEN + SIGNUPS_DATASET are present.
    """
    if not consent:
        return False, "Please check the box to opt in before submitting."
    normalized = validate_email(email)
    if normalized is None:
        return False, "Enter a valid email address."

    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "email": normalized,
        "consent": True,
        "source": source,
        "app_version": os.environ.get("CHIEF_ENGINEER_VERSION", "0.1.0"),
    }

    try:
        SIGNUPS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _lock:
            with SIGNUPS_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        sched = _get_scheduler()
        if sched is not None:
            try:
                sched.trigger()
            except Exception:
                pass
        return True, "You're on the list. Microfactory updates will hit that inbox."
    except Exception as e:
        return False, f"Could not save signup: {e}"


def privacy_notice() -> str:
    return (
        "<div class='ce-sub' style='font-size:10px;opacity:0.7;margin-top:4px;'>"
        "📬 Microfactory updates: one email, no spam, unsub any time. "
        "We store only your email and this timestamp. No print data, no uploaded files.</div>"
    )
