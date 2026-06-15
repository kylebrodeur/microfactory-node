"""Virtual printer — a clean-room, dependency-light visual of a part building up
layer by layer. The "more legit in that direction" visual (Kyle's call), done
from the REAL mesh, not a canned animation.

Honest about what it is: it slices the actual uploaded/sample mesh into real
horizontal cross-sections at the chosen layer height and animates them rising —
so it's the genuine geometry of *this* part, layer by layer. It is NOT a slicer
(no infill/supports/true toolpaths) and NOT a physics sim; the failure
prediction stays in sim/outcome.py. This is the motion/visual legitimacy layer;
that's the failure legitimacy layer. Keep the claim exactly that narrow.

Zero new deps: numpy + Pillow + trimesh (all already required). No scipy/shapely
(trimesh's high-level sectioning needs them — we do triangle-plane intersection
ourselves). Fully permissive; runs on a CPU Space. Isolated + removable: nothing
in the demo path imports this yet (see integration snippet at the bottom).

CLI:  uv run python -m sim.virtual_printer assets/overhang.glb out.gif
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Astrometrics palette (ties to the Off-Brand look)
_BG = (10, 12, 20)
_DONE = (70, 95, 130)      # already-printed layers (cool, receding)
_CUR = (255, 150, 40)      # the layer printing now (orange)
_NOZZLE = (255, 230, 180)
_TEXT = (210, 220, 235)
_ISO = 0.55                # oblique projection skew (fakes 3D)


def slice_segments(mesh_path: str | Path, layer_height_mm: float = 0.6,
                   max_layers: int = 140) -> list[tuple[float, np.ndarray]]:
    """Return [(z, segments)] where segments is (N,2,3) float — real cross-section
    line segments of the mesh at each layer Z. Pure numpy triangle-plane slicing."""
    import trimesh
    mesh = trimesh.load(str(mesh_path), force="mesh")
    tris = mesh.vertices[mesh.faces]            # (F,3,3)
    zmin, zmax = float(mesh.bounds[0, 2]), float(mesh.bounds[1, 2])
    height = max(zmax - zmin, 1e-6)
    n = min(max_layers, max(2, int(height / max(layer_height_mm, 1e-3))))
    zs = np.linspace(zmin + height * 0.01, zmax - height * 0.01, n)

    out: list[tuple[float, np.ndarray]] = []
    for z in zs:
        segs = _slice_at(tris, float(z))
        if len(segs):
            out.append((float(z), segs))
    return out


_OTHERS = np.array([[1, 2], [0, 2], [0, 1]])  # the two non-odd vertices, by odd index


def _slice_at(tris: np.ndarray, z: float) -> np.ndarray:
    """Intersect all triangles with plane Z=z at once (vectorized) → (S,2,3) segments.

    A straddling triangle has exactly one vertex on the minority side ('odd'); the
    two intersection points lie on the edges from the odd vertex to the other two.
    """
    below = tris[:, :, 2] < z                  # (F,3)
    cnt = below.sum(1)
    strad = (cnt > 0) & (cnt < 3)
    if not strad.any():
        return np.empty((0, 2, 3))
    T = tris[strad]                            # (S,3,3)
    b = below[strad]
    maj_below = cnt[strad] >= 2                 # majority side
    odd_i = (b != maj_below[:, None]).argmax(1)  # the lone-side vertex, (S,)
    ar = np.arange(len(T))
    o = _OTHERS[odd_i]                          # (S,2)
    V0 = T[ar, odd_i]                           # (S,3) odd vertex
    Va, Vb = T[ar, o[:, 0]], T[ar, o[:, 1]]

    def interp(A, B):
        dz = B[:, 2] - A[:, 2]
        t = (z - A[:, 2]) / np.where(dz == 0, 1e-9, dz)
        return A + t[:, None] * (B - A)

    return np.stack([interp(V0, Va), interp(V0, Vb)], axis=1)  # (S,2,3)


def _project(p: np.ndarray) -> tuple[float, float]:
    """Oblique 3D→2D: x picks up some y (depth); screen-height tracks z + some y."""
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    return x + _ISO * y, z + _ISO * y


def render_gif(layers: list[tuple[float, np.ndarray]], out_path: str | Path,
               caption: str | None = None, size: tuple[int, int] = (520, 420),
               max_frames: int = 60, fps: int = 14) -> Path:
    """Animate the layers rising into a looping GIF (Pillow only)."""
    from PIL import Image, ImageDraw

    if not layers:
        raise ValueError("no layers to render")

    # Global projected bounds for a stable camera across all frames.
    allpts = np.concatenate([s.reshape(-1, 3) for _, s in layers], axis=0)
    sx, sy = _project(allpts)
    xmin, xmax, ymin, ymax = sx.min(), sx.max(), sy.min(), sy.max()
    W, H = size
    pad = 36
    spanx, spany = max(xmax - xmin, 1e-6), max(ymax - ymin, 1e-6)
    scale = min((W - 2 * pad) / spanx, (H - 2 * pad) / spany)

    def to_px(seg_xy):
        x, y = seg_xy
        px = pad + (x - xmin) * scale
        py = H - (pad + (y - ymin) * scale)   # invert: higher z → higher on screen
        return px, py

    # Sample layer indices down to max_frames; each frame adds the next layer.
    idxs = list(range(len(layers)))
    if len(idxs) > max_frames:
        idxs = [idxs[int(i)] for i in np.linspace(0, len(idxs) - 1, max_frames)]

    frames = []
    for upto in idxs:
        img = Image.new("RGB", (W, H), _BG)
        d = ImageDraw.Draw(img)
        for li, (z, segs) in enumerate(layers[: upto + 1]):
            color = _CUR if li == upto else _DONE
            width = 2 if li == upto else 1
            for seg in segs:
                p0 = to_px(_project(seg[0]))
                p1 = to_px(_project(seg[1]))
                d.line([p0, p1], fill=color, width=width)
        # nozzle marker at the centroid of the current layer
        _, cur = layers[upto]
        cx, cy = to_px(_project(cur.reshape(-1, 3).mean(axis=0)))
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=_NOZZLE)
        pct = int(100 * (upto + 1) / len(layers))
        d.text((pad, 10), f"VIRTUAL PRINT  ·  layer {upto + 1}/{len(layers)}  ·  {pct}%",
               fill=_TEXT)
        if caption:
            d.text((pad, H - 22), caption[:70], fill=_CUR)
        frames.append(img)

    # Hold the final frame a beat.
    frames += [frames[-1]] * max(1, fps // 2)
    out = Path(out_path)
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=int(1000 / fps), loop=0, optimize=True)
    return out


def build_print_gif(mesh_path: str | Path, out_path: str | Path,
                    layer_height_mm: float = 0.6, caption: str | None = None) -> Path:
    """One-call convenience: slice a mesh and render the build animation."""
    return render_gif(slice_segments(mesh_path, layer_height_mm), out_path, caption=caption)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "assets/overhang.glb"
    dst = sys.argv[2] if len(sys.argv) > 2 else "virtual_print.gif"
    cap = sys.argv[3] if len(sys.argv) > 3 else "PLA overhang · watch the underside"
    layers = slice_segments(src)
    p = build_print_gif(src, dst, caption=cap)
    print(f"sliced {len(layers)} layers from {src} → {p} ({p.stat().st_size//1024} KB)")

# --- integration snippet (wire AFTER the Branch-A baseline is submitted) -------
# In app.py, add a removable component to the Cockpit and populate it on recommend:
#
#     from sim.virtual_printer import build_print_gif
#     vprint = gr.Image(label="VIRTUAL PRINT", height=300)   # beside gr.Model3D
#     # in get_recommendation(), after you know the mesh + a risk caption:
#     gif = build_print_gif(mesh_path, "data/_vprint.gif",
#                           caption=f"{material} {geometry_type} · {top_risk}")
#     return (..., gif)
#
# It reads the SAME mesh the 3D preview uses; if no mesh, fall back to a sample
# (viewer.sample_mesh(geometry_type)). Pure offline; safe on a CPU Space.
