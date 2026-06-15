"""Pre-window latency check — does the model respond fast enough for a live demo?

Run on the ACTUAL target hardware (your laptop / the Space). If a turn takes
~40s, switch to a smaller quant now (gemma4:e2b), not on June 13.
Run: `make bench`  (optionally CHIEF_ENGINEER_MODEL=gemma4:e2b)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root on path

from core import llm
from core.models import Environment, Job
from core.prompts import build_system_prompt

N = 3


def main() -> None:
    if not llm.is_available():
        print("⚠ Ollama not reachable — start `ollama serve` and pull the model, then re-run.")
        print(f"  target model: {llm.MODEL}")
        return

    job = Job(geometry_type="overhang", material="PLA", description="45° bracket")
    env = Environment(temp=28, humidity=50)
    system = build_system_prompt(job, env, [])

    times = []
    for i in range(N):
        t0 = time.time()
        out = llm.chat_json(system, "Give your recommendation for THIS job now.")
        dt = time.time() - t0
        times.append(dt)
        ok = "ok" if out else "parse-fail"
        print(f"  run {i + 1}: {dt:5.1f}s ({ok})")

    # Same cold/warm split + bands as preflight G2 (calibrated 6/10: warm <20s
    # reads fine in a narrated demo).
    cold, warm = times[0], (times[1:] or times)
    warm_avg = sum(warm) / len(warm)
    verdict = ("✅ fine for a live narrated demo" if warm_avg < 20 else
               ("🟡 long pauses — tighten prompt or use e2b/ZeroGPU" if warm_avg < 35 else
                "🔴 too slow — use gemma4:e2b"))
    print(f"\n{llm.MODEL}: warm avg {warm_avg:.1f}s (first call {cold:.1f}s) over {N} runs → {verdict}")


if __name__ == "__main__":
    main()
