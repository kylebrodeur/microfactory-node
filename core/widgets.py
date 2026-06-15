"""Custom visual-beat widgets — live in-browser instruments rendered into gr.HTML.

The marquee one is the VIRTUAL PRINTER: the real mesh sliced into cross-sections
(reusing sim.virtual_printer) and animated *rising* on a <canvas>, client-side, so
it's a live instrument in the cockpit rather than a pre-rendered GIF. Astrometrics
palette; zero new deps; fully offline/Space-safe.

Gradio gotcha handled here: a <script> injected via gr.HTML does NOT execute. So
the animation logic lives once in VP_JS (loaded via the Blocks `js=`), exposing a
global that scans for `canvas.ce-vp` elements and animates any it hasn't started.
The HTML payload is just a <canvas> with the layer data in a data-attribute — no
inline script — and the global picks it up on the next tick.
"""

from __future__ import annotations

import json
from pathlib import Path

_ISO = 0.55  # oblique projection skew, matches sim/virtual_printer


def _projected_layers(mesh_path: str | Path, layer_height_mm: float = 0.2,
                      max_layers: int = 44, max_segs_per_layer: int = 520) -> dict:
    """Slice the mesh and return projected 2D polylines per layer + bounds.

    {bounds:[xmin,xmax,ymin,ymax], layers:[[[x0,y0,x1,y1],...], ...]}  — projected
    oblique screen space, rounded to keep the data-attribute payload small. Segments
    per layer are capped (down-sampled) so a high-res mesh doesn't bloat the page.
    """
    from sim.virtual_printer import slice_segments

    layers = slice_segments(mesh_path, layer_height_mm, max_layers=max_layers)
    out_layers, xs, ys = [], [], []
    for _z, segs in layers:
        if len(segs) > max_segs_per_layer:                       # down-sample for payload
            step = len(segs) // max_segs_per_layer + 1
            segs = segs[::step]
        L = []
        for seg in segs:
            (x0, y0, z0), (x1, y1, z1) = seg[0], seg[1]
            px0, py0 = x0 + _ISO * y0, z0 + _ISO * y0
            px1, py1 = x1 + _ISO * y1, z1 + _ISO * y1
            L.append([round(px0, 1), round(py0, 1), round(px1, 1), round(py1, 1)])
            xs += [px0, px1]; ys += [py0, py1]
        if L:
            out_layers.append(L)
    if not out_layers:
        return {}
    return {"bounds": [min(xs), max(xs), min(ys), max(ys)], "layers": out_layers}


# ── layer scrubber: full-fidelity single-layer cross-section, rendered server-side ──
_TRIS_CACHE: dict = {}


def _tris_for(mesh_path: str):
    """Load + cache (triangles, bounds) for a mesh so scrubbing doesn't reload it."""
    p = str(mesh_path)
    if p not in _TRIS_CACHE:
        import trimesh
        m = trimesh.load(p, force="mesh")
        _TRIS_CACHE[p] = (m.vertices[m.faces], m.bounds.copy())
    return _TRIS_CACHE[p]


SCRUB_LAYERS = 40  # fixed layer count for the scrubber slider (independent of the animation)


def _fill_or_outline(d, segs, px) -> str:
    """Draw a layer as FILLED solid regions (shapely polygonize on snap-rounded
    segments — like a real slicer) with bright perimeters and holes cut out. Falls
    back to plain outlines if shapely is absent or the rings don't close. Returns a
    short label describing what was drawn."""
    try:
        from shapely.geometry import LineString
        from shapely.ops import polygonize, unary_union
        lines = [LineString([(round(float(sg[0][0]), 2), round(float(sg[0][1]), 2)),
                             (round(float(sg[1][0]), 2), round(float(sg[1][1]), 2))]) for sg in segs]
        polys = list(polygonize(unary_union(lines)))
        if polys:
            for p in polys:                                   # solid body
                d.polygon([px(x, y) for x, y in p.exterior.coords], fill=(110, 70, 20))
            for p in polys:                                   # holes → background
                for r in p.interiors:
                    d.polygon([px(x, y) for x, y in r.coords], fill=(10, 12, 20))
            for p in polys:                                   # bright perimeters
                d.line([px(x, y) for x, y in p.exterior.coords], fill=(255, 150, 40), width=2)
                for r in p.interiors:
                    d.line([px(x, y) for x, y in r.coords], fill=(255, 150, 40), width=1)
            return f"{len(polys)} filled regions"
    except Exception:
        pass
    for sg in segs:                                           # fallback: outline
        d.line([px(sg[0][0], sg[0][1]), px(sg[1][0], sg[1][1])], fill=(255, 150, 40), width=1)
    return f"{len(segs)} perimeter segments"


def layer_image(mesh_path: str | Path | None, idx: int, n: int = SCRUB_LAYERS,
                size: tuple[int, int] = (560, 380)):
    """Top-down cross-section of layer `idx` at FULL mesh fidelity (no payload cap —
    one layer at a time), drawn as a filled solid layer like a real slicer. Stable XY
    bounds so the part doesn't jump while scrubbing. Returns an RGB numpy array."""
    import numpy as np
    from PIL import Image, ImageDraw
    from sim.virtual_printer import _slice_at

    W, H, pad = size[0], size[1], 26
    img = Image.new("RGB", (W, H), (10, 12, 20))
    d = ImageDraw.Draw(img)
    if not mesh_path or not Path(str(mesh_path)).exists():
        d.text((pad, H // 2), "run ANALYZE to slice the part", fill=(150, 160, 180))
        return np.asarray(img)

    tris, bounds = _tris_for(mesh_path)
    zmin, zmax = float(bounds[0, 2]), float(bounds[1, 2])
    h = max(zmax - zmin, 1e-6)
    zs = np.linspace(zmin + h * 0.01, zmax - h * 0.01, n)
    idx = max(1, min(n, int(idx)))
    z = float(zs[idx - 1])
    segs = _slice_at(tris, z)

    xmin, ymin = float(bounds[0, 0]), float(bounds[0, 1])
    xmax, ymax = float(bounds[1, 0]), float(bounds[1, 1])
    s = min((W - 2 * pad) / max(xmax - xmin, 1e-6), (H - 2 * pad) / max(ymax - ymin, 1e-6))

    def px(x, y):
        return (pad + (x - xmin) * s, H - (pad + (y - ymin) * s))

    drawn = _fill_or_outline(d, segs, px)
    d.text((pad, 8), f"LAYER {idx}/{n}  ·  z={z:.1f} mm  ·  {drawn}", fill=(210, 220, 235))
    return np.asarray(img)


def virtual_printer_html(mesh_path: str | Path | None,
                         settings: "PrintSettings | None" = None,
                         caption: str = "") -> str:
    """A live virtual-printer canvas for the cockpit (animated by VP_JS).

    Uses the layer height from the proposed PrintSettings so the preview is tied
    to the actual recommendation rather than a hard-coded default. Canvas size is
    chosen from the projected mesh aspect ratio so the preview is not squished.
    """
    if not mesh_path or not Path(str(mesh_path)).exists():
        return ("<div class='ce-rule'>VIRTUAL PRINT</div>"
                "<div class='ce-sub'>run a recommendation to slice the part →</div>")
    layer_height = settings.layer_height if settings else 0.2
    data = _projected_layers(mesh_path, layer_height_mm=layer_height)
    if not data:
        return ("<div class='ce-rule'>VIRTUAL PRINT</div>"
                "<div class='ce-sub'>mesh too thin to slice.</div>")
    payload = json.dumps(data).replace("'", "&#39;")
    lh_note = f"{layer_height:.2f} mm layers"

    # Canvas size derived from projected bounds so the preview is not squished.
    # Max width is clamped to the column; height follows aspect ratio.
    xmin, xmax, ymin, ymax = data["bounds"]
    proj_w = max(xmax - xmin, 1)
    proj_h = max(ymax - ymin, 1)
    aspect = proj_h / proj_w
    max_css_w = 560
    css_h = min(round(max_css_w * aspect), 340)
    canvas_w, canvas_h = max_css_w, css_h

    return (
        "<div class='ce-rule'>VIRTUAL PRINT · MOTION PREVIEW</div>"
        "<div class='ce-vp-wrap'>"
        f"<canvas class='ce-vp' width='{canvas_w}' height='{canvas_h}' data-vp='{payload}' "
        f"data-aspect='{aspect:.4f}' style='width:{max_css_w}px;height:{css_h}px;display:block;'></canvas>"
        "</div>"
        f"<div class='ce-sub ce-vp-caption'>{caption} · {lh_note} · real cross-sections of "
        "this part, rising layer by layer (motion preview — not a slicer). Click REPLAY to restart.</div>"
        "<button class='ce-pillbtn ce-vp-replay' type='button' "
        "onclick=\"const cv=this.parentNode.querySelector('canvas.ce-vp');"
        "if(window.__vp_replay) window.__vp_replay(cv);\">REPLAY</button>"
    )


# One-time client animator, injected as a real <script> via launch(head=...).
# (launch(js=...) proved unreliable for setting up a persistent scan loop; a head
# script runs on load deterministically and is CSP-friendly on a Space.)
VP_HEAD = r"""
<script>
(function(){
 function start(){
  // --- LCARS clock ---
  const tickClock = () => {
    const el = document.getElementById('ce-clock');
    if (el) el.textContent = new Date().toISOString().slice(11,19) + ' UTC';
  };
  tickClock(); setInterval(tickClock, 1000);

  // --- virtual-printer animator ---
  const DONE='#46627f', CUR='#ff9c00', NOZ='#ffe6b4', BG='#0a0c14';
  window.__vp_replay = function(cv){
    if(cv._raf){ cancelAnimationFrame(cv._raf); cv._raf=null; }
    cv.removeAttribute('data-init');
    const ctx = cv.getContext('2d'); ctx.fillStyle=BG; ctx.fillRect(0,0,cv.width,cv.height);
    scan();
  };
  function animate(cv){
    let data; try { data = JSON.parse(cv.getAttribute('data-vp')); } catch(e){ return; }
    if(!data || !data.layers || !data.layers.length) return;
    const ctx = cv.getContext('2d'); const W=cv.width, H=cv.height, pad=22;
    const [xmin,xmax,ymin,ymax] = data.bounds;
    const sx = (W-2*pad)/Math.max(xmax-xmin,1e-6), sy=(H-2*pad)/Math.max(ymax-ymin,1e-6);
    const s = Math.min(sx,sy);
    const X = x => pad + (x-xmin)*s, Y = y => H - (pad + (y-ymin)*s);
    const N = data.layers.length;
    let upto = 0, hold = 0;
    // bigger hold count = slower animation. default 6; override with window.__vp_speed.
    const speed = Math.max(1, Math.min(20, Number(window.__vp_speed || 6)));
    function frame(){
      ctx.fillStyle=BG; ctx.fillRect(0,0,W,H);
      for(let li=0; li<=upto && li<N; li++){
        const segs = data.layers[li];
        ctx.strokeStyle = (li===upto)?CUR:DONE; ctx.lineWidth=(li===upto)?1.6:1;
        ctx.beginPath();
        for(const [x0,y0,x1,y1] of segs){ ctx.moveTo(X(x0),Y(y0)); ctx.lineTo(X(x1),Y(y1)); }
        ctx.stroke();
      }
      // nozzle: centroid of current layer
      const cur = data.layers[Math.min(upto,N-1)];
      let cx=0,cy=0,n=0; for(const s2 of cur){ cx+=s2[0]+s2[2]; cy+=s2[1]+s2[3]; n+=2; }
      if(n){ ctx.fillStyle=NOZ; ctx.beginPath(); ctx.arc(X(cx/n),Y(cy/n),3.2,0,7); ctx.fill(); }
      // HUD
      ctx.fillStyle='#9fb0c8'; ctx.font='10px ui-monospace,monospace';
      ctx.fillText('LAYER '+(upto+1)+'/'+N+'  ·  '+Math.round(100*(upto+1)/N)+'%', pad, 14);
      if(upto < N-1){ if(++hold>=speed){ hold=0; upto++; } cv._raf = requestAnimationFrame(frame); }
      // else: full part drawn — hold final frame
    }
    frame();
  }
  function scan(){ document.querySelectorAll('canvas.ce-vp:not([data-init])').forEach(cv=>{
    cv.setAttribute('data-init','1'); animate(cv); }); }
  setInterval(scan, 400); scan();
 }
 if (document.readyState !== 'loading') start();
 else document.addEventListener('DOMContentLoaded', start);
})();
</script>
"""
