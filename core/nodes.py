"""Node / swarm mesh — faithful VISUALIZATION of the lab, not a distributed system.

Mirrors microfactory-lab's `zellij-layout.kdl`: a Chief Engineer hub coordinating
capability nodes. Only the 3D Print node executes real work (the core loop);
the others render as mesh context / available capacity. No FileBridge IPC, no
pi-link, no six live processes (that was the Kaggle failure surface).
"""

from __future__ import annotations

from .models import Environment

# (name, capability, active?) — active node runs the real core loop.
NODES = [
    ("Chief Engineer", "hub / router", True),
    ("3D Print", "fdm", True),
    ("CNC Mill", "cnc", False),
    ("Laser Cutter", "laser", False),
    ("Sinter Press", "sinter", False),
    ("Metal 3D Print", "metal3d", False),
    ("Hub Router", "routing", False),
]


def render_node_cards(env: Environment, working: bool = False) -> str:
    cards = []
    for name, cap, active in NODES:
        if name == "3D Print":
            state = "WORKING" if working else "ONLINE"
            sub = f"{env.temp:.0f}°C · {env.humidity:.0f}% RH"
            border = "var(--ao-orange)"
        elif active:
            state = "ONLINE"
            sub = "coordinating"
            border = "var(--ao-orange)"
        else:
            state = "⚪ IDLE"
            sub = "mesh context · available capacity"
            border = "var(--ao-outline-dim)"
        cards.append(
            f"<div style='border-left:3px solid {border};background:var(--ao-surface);"
            f"padding:8px 12px;margin:6px 0;font-family:ui-monospace,monospace;'>"
            f"<div style='color:var(--ao-orange);font-weight:600;letter-spacing:1px;'>{name.upper()}"
            f"<span style='float:right;color:var(--ao-text);font-weight:400;'>{state}</span></div>"
            f"<div style='color:var(--ao-outline);font-size:11px;'>{cap} · {sub}</div></div>"
        )
    return (
        "<div><div style='color:var(--ao-outline);font-family:ui-monospace,monospace;"
        "font-size:11px;margin-bottom:4px;'>CAPABILITY MESH — 1 node executing, "
        "others shown as network context</div>" + "".join(cards) + "</div>"
    )
