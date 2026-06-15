"""Generate small sample meshes for the gr.Model3D preview (build-time helper).

Permissive deps only (trimesh, MIT). Run once: `make assets` (= `uv run python -m scripts.make_assets`).
Produces a handful of .glb files keyed to geometry_type so the demo always has
something interactive to show without requiring an upload.
"""

from __future__ import annotations

from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def build() -> list[str]:
    import numpy as np
    import trimesh

    ASSETS.mkdir(parents=True, exist_ok=True)
    out: list[str] = []

    def save(mesh: "trimesh.Trimesh", name: str) -> None:
        path = ASSETS / name
        mesh.export(path)
        out.append(str(path))

    # overhang: a base with a cantilever creating a steep unsupported underside
    base = trimesh.creation.box(extents=[40, 40, 10])
    base.apply_translation([0, 0, 5])
    arm = trimesh.creation.box(extents=[40, 40, 10])
    arm.apply_translation([30, 0, 35])
    save(trimesh.util.concatenate([base, arm]), "overhang.glb")

    # bridge: two pillars + a flat span across the gap
    p1 = trimesh.creation.box(extents=[12, 40, 40]); p1.apply_translation([-24, 0, 20])
    p2 = trimesh.creation.box(extents=[12, 40, 40]); p2.apply_translation([24, 0, 20])
    span = trimesh.creation.box(extents=[60, 40, 6]); span.apply_translation([0, 0, 43])
    save(trimesh.util.concatenate([p1, p2, span]), "bridge.glb")

    # vase: a thin tall open cylinder shell
    vase = trimesh.creation.annulus(r_min=18, r_max=20, height=80)
    save(vase, "vase.glb")

    # generic / adhesion / stringing: a simple calibration cube
    save(trimesh.creation.box(extents=[20, 20, 20]), "cube.glb")
    return out


if __name__ == "__main__":
    paths = build()
    print(f"wrote {len(paths)} meshes:")
    for p in paths:
        print(" ", p)
