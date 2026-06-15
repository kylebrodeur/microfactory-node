"""Astrometrics OS — the Off-Brand visual layer (badge: Off-Brand).

Single source of truth for the custom look, kept OUT of app.py so it stays a
removable layer: `from core.theme import THEME, CSS, rule, command_bar`. Every
token traces to ../DESIGN.md §1 — no ad-hoc colors. Aesthetic: Futuristic
Brutalism / LCARS terminal — Command Orange on Void Black, monospace, square
corners, signal-colored panes (orange=active, purple=cognition, yellow=human
gate, red=veto, green=pass).

Two parts:
  THEME — a gr.themes.Base that recolors Gradio's OWN component variables (so
          buttons/inputs/blocks obey the palette, not just our CSS overrides).
  CSS   — the structural chrome CSS does on top can't: the LCARS command bar,
          ribbon tabs, rule headers, elbow corners, focused-pane borders.
"""

from __future__ import annotations

import gradio as gr

# --- canonical palette (DESIGN.md §1) ----------------------------------------
VOID = "#131313"
SURFACE = "#1f1f1f"
SURFACE_HI = "#2a2a2a"
ORANGE = "#ff9c00"
ORANGE_SOFT = "#ffc384"
PURPLE = "#c2c1ff"
BLUE = "#5fafff"
YELLOW = "#ffff66"
TEXT = "#e2e2e2"
OUTLINE = "#a28d79"
OUTLINE_DIM = "#544433"
GREEN = "#82c88c"
RED = "#ffb4ab"

_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def astrometrics_theme() -> gr.themes.Base:
    """Recolor Gradio's component variables to the Astrometrics palette. Both the
    base and *_dark variants are set so the deck looks identical regardless of the
    browser's light/dark preference (a Space defaults to system).

    Uses .set() to override CSS variables at the theme level — this is the
    PROPER way to kill borders, reduce spacing, and control component styling.
    The raw CSS string handles only things the theme can't express (LCARS rule
    headers, pill radios, command bar, custom icons, etc.).
    """
    t = gr.themes.Base(
        primary_hue=gr.themes.colors.orange,
        secondary_hue=gr.themes.colors.blue,
        neutral_hue=gr.themes.colors.stone,
        font=[_MONO], font_mono=[_MONO],
        radius_size=gr.themes.sizes.radius_none,
        spacing_size=gr.themes.sizes.spacing_sm,  # tighter than default — sections sit closer
    )
    pairs = dict(
        body_background_fill=VOID, body_background_fill_dark=VOID,
        body_text_color=TEXT, body_text_color_dark=TEXT,
        body_text_color_subdued=OUTLINE, body_text_color_subdued_dark=OUTLINE,
        background_fill_primary=VOID, background_fill_primary_dark=VOID,
        background_fill_secondary=SURFACE, background_fill_secondary_dark=SURFACE,
        block_background_fill=SURFACE, block_background_fill_dark=SURFACE,
        # KILL ALL BLOCK BORDERS via theme variables (the right way)
        block_border_color=VOID, block_border_color_dark=VOID,
        block_border_width="0px", block_border_width_dark="0px",
        block_label_background_fill=VOID, block_label_background_fill_dark=VOID,
        block_label_text_color=ORANGE, block_label_text_color_dark=ORANGE,
        block_title_text_color=ORANGE, block_title_text_color_dark=ORANGE,
        # KILL ALL GENERAL BORDERS
        border_color_primary=VOID, border_color_primary_dark=VOID,
        border_color_accent=VOID, border_color_accent_dark=VOID,
        # BORDERS WIDTH ZERO across the board
        input_border_width="0px",
        button_border_width="0px",
        color_accent_soft=SURFACE_HI, color_accent_soft_dark=SURFACE_HI,
        input_background_fill=VOID, input_background_fill_dark=VOID,
        input_border_color=OUTLINE_DIM, input_border_color_dark=OUTLINE_DIM,
        input_border_color_focus=ORANGE, input_border_color_focus_dark=ORANGE,
        button_primary_background_fill=ORANGE, button_primary_background_fill_dark=ORANGE,
        button_primary_text_color=VOID, button_primary_text_color_dark=VOID,
        button_secondary_background_fill=SURFACE, button_secondary_background_fill_dark=SURFACE,
        button_secondary_text_color=ORANGE, button_secondary_text_color_dark=ORANGE,
        button_secondary_border_color=VOID, button_secondary_border_color_dark=VOID,
        slider_color=ORANGE, slider_color_dark=ORANGE,
        link_text_color=BLUE, link_text_color_dark=BLUE,
        # SPACING: tighter section padding via theme variables
        block_padding="6px",
    )
    return t.set(**pairs)


THEME = astrometrics_theme()

# --- structural chrome the theme can't express -------------------------------
CSS = f"""
/* kill the stock Gradio tells */
footer, .gradio-container footer {{ display:none !important; }}
.gradio-container {{ padding-top:4px; }}

/* deck frame around the whole console */
#ce-deck {{ border:1px solid var(--ao-outline-dim); border-top:2px solid var(--ao-orange);
  padding:14px 16px 4px; background:linear-gradient(180deg, rgba(255,156,0,0.03), transparent 120px); }}

/* flatten Gradio's boxed labels into bare instrument labels */
.block {{ box-shadow:none !important; }}
.block > .label-wrap, span[data-testid="block-info"] {{ background:transparent !important;
  border:none !important; padding:0 0 2px !important; }}
.block .label-wrap span, label > span:first-child {{ background:transparent !important; }}

/* a "console" column: NO side border (was: border-left:2px solid var(--ao-orange)) */
.ce-console {{ padding-left:4px !important; padding-right:4px !important; gap:16px !important; }}
"""

CSS += f"""
:root, .gradio-container {{
  --ao-void:{VOID}; --ao-surface:{SURFACE}; --ao-surface-hi:{SURFACE_HI};
  --ao-orange:{ORANGE}; --ao-orange-soft:{ORANGE_SOFT}; --ao-purple:{PURPLE};
  --ao-blue:{BLUE}; --ao-yellow:{YELLOW}; --ao-text:{TEXT};
  --ao-outline:{OUTLINE}; --ao-outline-dim:{OUTLINE_DIM}; --ao-green:{GREEN}; --ao-red:{RED};
}}
.gradio-container {{ background:var(--ao-void) !important; max-width:1600px !important; }}
* {{ font-family:{_MONO} !important; }}
.gradio-container .prose, .gradio-container p, .gradio-container span,
.gradio-container li {{ color:var(--ao-text); }}

/* ── LCARS COMMAND BAR ─────────────────────────────────────────────── */
#ce-cmdbar {{ display:flex; align-items:stretch; gap:0; margin-bottom:14px; }}
#ce-cmdbar .ce-elbow {{ background:var(--ao-orange); color:var(--ao-void);
  font-weight:800; letter-spacing:3px; text-transform:uppercase; font-size:15px;
  padding:10px 22px 10px 16px; border-top-right-radius:18px; white-space:nowrap;
  display:flex; align-items:center; }}
#ce-cmdbar .ce-bar {{ flex:1; background:var(--ao-surface-hi);
  border-bottom:2px solid var(--ao-orange); display:flex; align-items:center;
  justify-content:flex-end; gap:18px; padding:0 16px; font-size:11px;
  letter-spacing:1px; text-transform:uppercase; }}
#ce-cmdbar .ce-bar b {{ color:var(--ao-orange); }}
#ce-cmdbar #ce-clock {{ color:var(--ao-blue); }}
.ce-sub {{ color:var(--ao-outline); letter-spacing:.5px; font-size:12px; line-height:1.5; }}
.ce-sub b {{ color:var(--ao-orange-soft); }}

/* ── RULE HEADERS  ──  LABEL ──────────── (flex line fills the width) */
.ce-rule {{ display:flex; align-items:center; gap:10px; color:var(--ao-orange);
  text-transform:uppercase; letter-spacing:3px; font-size:12px; font-weight:700; margin:10px 0 4px; }}
.ce-rule::after {{ content:""; flex:1; height:0; border-top:1px solid var(--ao-outline-dim); }}
.ce-rule::before {{ content:"▸"; color:var(--ao-orange); }}

/* labels as orange uppercase */
.block .label-wrap span, label > span, span[data-testid="block-info"] {{
  color:var(--ao-orange) !important; text-transform:uppercase; letter-spacing:1.4px;
  font-size:11px !important; font-weight:700; }}

/* square brutalist blocks, dim borders removed for clean look */
.block, .form, .gr-box, .gr-panel {{ border-radius:0 !important;
  border:none !important; background:transparent !important; }}
textarea, input, select, .gr-input {{ background:var(--ao-void) !important;
  color:var(--ao-text) !important; border-radius:0 !important; }}
textarea:focus, input:focus {{ border-color:var(--ao-orange) !important; box-shadow:none !important; }}

/* ── RIBBON TABS (LCARS elbows) ── each tab a rounded ribbon; selected = solid orange */
.tab-nav, .tab-container {{ border-bottom:2px solid var(--ao-orange) !important; gap:6px !important;
  padding-bottom:0 !important; }}
.tab-nav button, .tab-container button, button[role="tab"] {{
  color:var(--ao-orange-soft) !important; background:var(--ao-outline-dim) !important;
  text-transform:uppercase; letter-spacing:2px; font-size:12px !important; font-weight:800;
  border:none !important; border-radius:14px 14px 0 0 !important; padding:8px 22px !important;
  margin:0 !important; }}
.tab-nav button:hover, button[role="tab"]:hover {{ color:var(--ao-void) !important;
  background:var(--ao-orange-soft) !important; }}
.tab-nav button.selected, button[role="tab"][aria-selected="true"],
.tab-container button.selected {{ background:var(--ao-orange) !important; color:#131313 !important; }}

/* ── file dropzone as a clean drop area (no border) ── */
.ce-drop, .ce-drop .center, .ce-drop [data-testid="block-label"] {{ background:var(--ao-void) !important; }}
.ce-drop {{ border:none !important; border-radius:0 !important; }}
.ce-drop:hover {{ border-color:var(--ao-orange) !important; }}
.ce-drop .wrap, .ce-drop .or, .ce-drop button {{ color:var(--ao-orange-soft) !important;
  text-transform:uppercase; letter-spacing:1px; font-size:12px; }}

/* ── ICON BUTTONS (SVG via CSS mask, no raw HTML in labels) ── */
/* Each icon class injects a 12x12 SVG via mask-image. The SVG is a data URL
   so no external requests. Color inherits from currentColor. */
.ce-pillbtn {{ display:inline-flex !important; align-items:center !important; gap:6px !important; }}
.ce-icon-bolt::before, .ce-icon-shuffle::before, .ce-icon-anchor::before,
.ce-icon-refresh::before, .ce-icon-play::before, .ce-icon-printer::before,
.ce-icon-search::before, .ce-icon-check::before, .ce-icon-x::before,
.ce-icon-arrow::before, .ce-icon-target::before, .ce-icon-layers::before,
.ce-icon-flask::before, .ce-icon-gauge::before, .ce-icon-info::before,
.ce-icon-sliders::before {{
  content:""; display:inline-block; width:12px; height:12px; flex:0 0 12px;
  background:currentColor; -webkit-mask-size:contain; mask-size:contain;
  -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat;
  -webkit-mask-position:center; mask-position:center; }}
.ce-icon-bolt::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'><path d='M13 2L4 14h7l-1 8 10-12h-7l0-8z'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'><path d='M13 2L4 14h7l-1 8 10-12h-7l0-8z'/></svg>"); }}
.ce-icon-shuffle::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M16 3h5v5 M21 3l-7 7 M16 21h5v-5 M3 3l18 18 M3 21l7-7'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M16 3h5v5 M21 3l-7 7 M16 21h5v-5 M3 3l18 18 M3 21l7-7'/></svg>"); }}
.ce-icon-anchor::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='5' r='2'/><path d='M12 7v15 M5 12H2a10 10 0 0020 0h-3'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='5' r='2'/><path d='M12 7v15 M5 12H2a10 10 0 0020 0h-3'/></svg>"); }}
.ce-icon-refresh::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M21 2v6h-6 M20.5 13a9 9 0 11-2.6-7.4L21 8'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M21 2v6h-6 M20.5 13a9 9 0 11-2.6-7.4L21 8'/></svg>"); }}
.ce-icon-play::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'><path d='M6 4l14 8-14 8V4z'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'><path d='M6 4l14 8-14 8V4z'/></svg>"); }}
.ce-icon-printer::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 9V2h12v7 M6 18H4a2 2 0 01-2-2v-4a2 2 0 012-2h16a2 2 0 012 2v4a2 2 0 01-2 2h-2 M6 14h12v8H6z'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 9V2h12v7 M6 18H4a2 2 0 01-2-2v-4a2 2 0 012-2h16a2 2 0 012 2v4a2 2 0 01-2 2h-2 M6 14h12v8H6z'/></svg>"); }}
.ce-icon-info::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='9'/><path d='M12 11v5 M12 8h.01'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='9'/><path d='M12 11v5 M12 8h.01'/></svg>"); }}
.ce-icon-sliders::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4 6h10 M18 6h2 M4 12h2 M10 12h10 M4 18h8 M16 18h4 M16 4v4 M6 10v4 M12 16v4'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4 6h10 M18 6h2 M4 12h2 M10 12h10 M4 18h8 M16 18h4 M16 4v4 M6 10v4 M12 16v4'/></svg>"); }}
.ce-icon-arrow::before {{ -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'><path d='M5 12h14 M13 5l7 7-7 7'/></svg>"); mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'><path d='M5 12h14 M13 5l7 7-7 7'/></svg>"); }}

/* Arrow AFTER text (right-side icon — indicates "next step"). For buttons whose
   label means "proceed to next stage" (SLICE →, PRINT →, REFRESH →).
   Gradio wraps each button in a .wrap; elem_classes lands on that wrapper, so we
   target the label <span> inside the <button> and append the arrow as an SVG
   mask-image pseudo-element. */
.ce-icon-arrow-after button {{ display:inline-flex !important; align-items:center !important; gap:4px !important; }}
.ce-icon-arrow-after button span {{ display:inline-flex !important; align-items:center !important; gap:4px !important; }}
.ce-icon-arrow-after button span::after {{
  content:""; display:inline-block; width:14px; height:14px; flex:0 0 14px;
  margin-left:4px; vertical-align:-2px;
  background:currentColor; -webkit-mask-size:contain; mask-size:contain;
  -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat;
  -webkit-mask-position:center; mask-position:center;
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'><path d='M5 12h14 M13 5l7 7-7 7'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'><path d='M5 12h14 M13 5l7 7-7 7'/></svg>");
}}

/* ── TAB ICONS (CSS-only via :nth-child on the four workflow tabs) ── */
/* Tab bar order is fixed: LOAD · SLICE · PRINT · REVIEW. Each gets its own icon
   prepended via ::before. The icons are inline-svg via mask-image so they inherit
   the tab's text color (orange-on-dark or dark-on-orange when selected). */
.tab-nav button::before, button[role="tab"]::before {{
  content:""; display:inline-block; width:13px; height:13px; margin-right:8px;
  vertical-align:-2px; background:currentColor;
  -webkit-mask-size:contain; mask-size:contain;
  -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat;
  -webkit-mask-position:center; mask-position:center; }}
/* LOAD — inbox/upload tray icon */
.tab-nav button:nth-of-type(1)::before, button[role="tab"]:nth-of-type(1)::before {{
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M22 12h-6l-2 3h-4l-2-3H2 M5.5 6h13l3 6v6a2 2 0 01-2 2h-15a2 2 0 01-2-2v-6l3-6z'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M22 12h-6l-2 3h-4l-2-3H2 M5.5 6h13l3 6v6a2 2 0 01-2 2h-15a2 2 0 01-2-2v-6l3-6z'/></svg>"); }}
/* SLICE — layered stack icon */
.tab-nav button:nth-of-type(2)::before, button[role="tab"]:nth-of-type(2)::before {{
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2l9 5-9 5-9-5 9-5z M3 12l9 5 9-5 M3 17l9 5 9-5'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2l9 5-9 5-9-5 9-5z M3 12l9 5 9-5 M3 17l9 5 9-5'/></svg>"); }}
/* PRINT — printer icon */
.tab-nav button:nth-of-type(3)::before, button[role="tab"]:nth-of-type(3)::before {{
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 9V2h12v7 M6 18H4a2 2 0 01-2-2v-4a2 2 0 012-2h16a2 2 0 012 2v4a2 2 0 01-2 2h-2 M6 14h12v8H6z'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M6 9V2h12v7 M6 18H4a2 2 0 01-2-2v-4a2 2 0 012-2h16a2 2 0 012 2v4a2 2 0 01-2 2h-2 M6 14h12v8H6z'/></svg>"); }}
/* REVIEW — clipboard-check icon */
.tab-nav button:nth-of-type(4)::before, button[role="tab"]:nth-of-type(4)::before {{
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M9 3h6v3H9z M9 5H6a2 2 0 00-2 2v13a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-3 M8 14l3 3 5-6'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M9 3h6v3H9z M9 5H6a2 2 0 00-2 2v13a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-3 M8 14l3 3 5-6'/></svg>"); }}

/* ── IMPLICIT GROUPING (borderless, proximity-based) ── */
/* Model switcher row: sits BELOW the LCARS command bar (right-aligned).
   Previous attempt lifted it into the header but overlapped the status text. */
#ce-modelswitch {{ display:flex !important; align-items:center !important;
  gap:8px !important; padding:0 !important;
  margin:8px 0 12px 0 !important;
  background:transparent !important;
  justify-content:flex-end !important; flex-wrap:nowrap !important;
  width:100% !important; }}
#ce-modelswitch > * {{ flex:0 0 auto !important; min-width:0 !important; max-width:none !important;
  width:auto !important; }}
#ce-modelswitch .ce-modeldd {{ width:200px !important; min-width:200px !important; max-width:200px !important; flex:0 0 200px !important; }}
#ce-modelswitch .ce-modeldd > div, #ce-modelswitch .ce-modeldd .wrap {{ width:200px !important; max-width:200px !important; }}
#ce-modelswitch .ce-pillbtn {{ width:auto !important; }}

/* Hide the old duplicate model status (the command bar already shows it) */
.ce-status-inline, #ce-modelswitch .ce-status-inline {{ display:none !important; }}

/* dropdown styling: orange border, no double outlines */
.ce-modeldd .wrap, .ce-modeldd .secondary-wrap {{
  border:1px solid var(--ao-orange) !important; outline:none !important; box-shadow:none !important; }}
.ce-modeldd:focus-within .wrap, .ce-modeldd:focus-within .secondary-wrap {{
  outline:none !important; border-color:var(--ao-orange) !important; }}

/* contained block: NO padding/margin additions */
.ce-card {{ padding:0 !important; margin:0 !important; gap:8px !important;
  display:flex !important; flex-direction:column !important; }}

/* ENVIRONMENT bar: env readout + OVERRIDE + POSITION + MATERIAL grouped on the left;
   RANDOMIZE / RESET / SLICE grouped on the right, bottom-aligned to the pill row. */
.ce-envbar {{ display:flex !important; align-items:flex-end !important; gap:8px !important;
  flex-wrap:wrap !important; margin-bottom:2px !important;
  padding:8px 0 6px !important;
  border-top:1px solid var(--ao-outline-dim) !important;
  border-bottom:1px solid var(--ao-outline-dim) !important;
  justify-content:space-between !important; }}
.ce-envbar > * {{ flex:0 0 auto !important; width:auto !important; min-width:0 !important; }}
.ce-envbar .ce-inline-group {{ margin:0 10px 0 0 !important; }}
/* left group: ENVIRONMENT / POSITION / MATERIAL in one row; environment allowed to wrap */
.ce-envbar .ce-envbar-left {{ display:flex !important; flex-direction:row !important;
  align-items:flex-end !important; gap:0 !important; margin:0 !important; flex-wrap:wrap !important; }}
.ce-envbar .ce-envbar-left .ce-inline-group {{ margin:0 8px 4px 0 !important; }}
/* right-side action group: no label gap, pills in a tight row */
.ce-envbar .ce-envbar-actions {{ display:flex !important; flex-direction:column !important;
  justify-content:flex-end !important; margin:0 !important; }}
.ce-envbar .ce-envbar-actions .ce-inline-pills {{ display:flex !important; gap:6px !important;
  align-items:flex-end !important; justify-content:flex-end !important; }}
.ce-envbar .ce-envbar-actions .ce-inline-pills > * {{ flex:0 0 auto !important; }}
.ce-envbar .ce-envbar-readout {{ flex:0 1 auto; min-width:0;
  color:var(--ao-text); font-size:12px; letter-spacing:1px;
  text-transform:uppercase; white-space:normal !important;
  overflow:visible;
  max-width:100%; padding-top:3px; }}
.ce-envbar .ce-envbar-readout * {{ font-size:12px !important; }}

/* ── PART row: top-align the viewer (left) and the dropzone/buttons (right) ── */
.ce-part-row {{ align-items:flex-start !important; gap:16px !important; }}
.ce-part-viewer-col, .ce-part-actions-col {{ align-self:flex-start !important; }}

/* Right column: dropzone on top, then matching-style mesh-source buttons.
   gap gives breathing room between dropzone → button → button. */
.ce-part-actions-col {{ display:flex !important; flex-direction:column !important;
  gap:12px !important; padding-top:0 !important; }}

/* Constrain dropzone height so it doesn't dominate; match the viewer's visual weight */
.ce-part-actions-col .ce-drop {{ min-height:140px !important; max-height:180px !important; }}
.ce-part-actions-col .ce-drop > * {{ min-height:140px !important; }}

/* QUICK-LOAD BENCHY + GENERATE A PRIMITIVE share the same "mesh source" pill look.
   Both fill the column width, equal height, equal padding. */
.ce-mesh-source {{ width:100% !important; }}
.ce-mesh-source button, .ce-mesh-source > button {{
  width:100% !important; justify-content:center !important;
  padding:12px 16px !important; min-height:44px !important;
  font-size:12px !important; letter-spacing:1px !important; }}

/* Accordion-as-pill: make the GENERATE A PRIMITIVE accordion header look
   identical to QUICK-LOAD BENCHY when collapsed. */
.ce-accordion-pill {{ background:transparent !important; border:none !important;
  padding:0 !important; }}
.ce-accordion-pill > button, .ce-accordion-pill > .label-wrap {{
  border-radius:999px !important; border:1px solid var(--ao-orange) !important;
  background:var(--ao-surface) !important; color:var(--ao-orange-soft) !important;
  text-transform:uppercase !important; letter-spacing:.5px !important;
  font-size:12px !important; font-weight:700 !important;
  padding:12px 16px !important; min-height:44px !important;
  cursor:pointer !important; display:flex !important;
  align-items:center !important; justify-content:center !important;
  width:100% !important; gap:8px !important; }}
.ce-accordion-pill > button:hover, .ce-accordion-pill > .label-wrap:hover {{
  background:var(--ao-orange) !important; color:#131313 !important; }}
/* hide the accordion's expand arrow (we want pure pill look) */
.ce-accordion-pill .icon, .ce-accordion-pill svg {{ display:none !important; }}
/* inner content (radio + number + generate) gets a nicer recessed area when open */
.ce-accordion-pill > .wrap, .ce-accordion-pill .gap {{
  padding:14px 12px !important; margin-top:8px !important;
  background:var(--ao-surface) !important;
  border:1px solid var(--ao-outline-dim) !important;
  display:flex !important; flex-direction:column !important; gap:10px !important; }}

/* ── OVERRIDE ENVIRONMENT POPUP ──
   Hidden by default; toggled via JS clicking the OVERRIDE button.
   Modal-style overlay with the override fields inside. */
.ce-popup {{ display:none !important; position:fixed; top:50%; left:50%;
  transform:translate(-50%,-50%); z-index:1000;
  background:var(--ao-surface-hi); border:2px solid var(--ao-orange);
  padding:18px 22px; min-width:420px; max-width:520px;
  box-shadow:0 20px 60px rgba(0,0,0,0.7); }}
.ce-popup.open {{ display:block !important; }}
.ce-popup.open .ce-popup {{ display:block !important; }}
.ce-popup-backdrop {{ display:none !important; position:fixed; inset:0; z-index:999;
  background:rgba(0,0,0,0.6); }}
.ce-popup-backdrop.open {{ display:block !important; }}
.ce-popup-title {{ color:var(--ao-orange); letter-spacing:3px;
  text-transform:uppercase; font-size:13px; font-weight:800;
  margin-bottom:10px; display:flex; align-items:center; justify-content:space-between; }}
.ce-popup-close {{ cursor:pointer; color:var(--ao-orange-soft);
  font-size:18px; line-height:1; padding:0 4px; }}
.ce-popup-close:hover {{ color:var(--ao-orange); }}

/* ── PRINT · compact ITERATIONS control (kept tight, not full-width) ── */
.ce-iter-row {{ display:flex; align-items:center; gap:10px;
  max-width:520px; margin:6px 0 0; }}
.ce-iter-slider {{ flex:1; min-width:200px; max-width:340px; }}

/* ── CUSTOM DROPZONE (matches the ce-viewer aesthetic) ── */
.ce-drop, .ce-drop > div, .ce-drop .wrap {{ background:#0a0c14 !important;
  border:1px dashed var(--ao-outline-dim) !important;
  border-radius:0 !important; min-height:140px !important; }}
.ce-drop:hover, .ce-drop:hover > div {{ border-color:var(--ao-orange) !important; }}
.ce-drop .center, .ce-drop .upload-container {{ background:transparent !important;
  padding:20px 12px !important; }}
.ce-drop .icon-wrap {{ color:var(--ao-orange) !important; }}
.ce-drop .wrap p, .ce-drop .or, .ce-drop button {{
  color:var(--ao-orange-soft) !important;
  text-transform:uppercase; letter-spacing:1px; font-size:11px !important;
  font-weight:700; }}

/* sliders + ranges */
input[type=range] {{ accent-color:var(--ao-orange) !important; }}

/* buttons: square, uppercase, letter-spaced */
button.primary, .gr-button-primary, button[variant="primary"] {{
  background:var(--ao-orange) !important; color:var(--ao-void) !important;
  font-weight:800 !important; border:none !important; border-radius:0 !important;
  letter-spacing:1.5px !important; text-transform:uppercase; }}
button.secondary {{ background:var(--ao-surface) !important; color:var(--ao-orange) !important;
  border:none !important; border-radius:0 !important;
  text-transform:uppercase; letter-spacing:1px !important; }}
button.secondary:hover {{ border-color:var(--ao-orange) !important; }}

/* ── SIGNAL-CODED PANELS (left accent = meaning) ── — accent moved to top to be subtle, no left border */
#ce-reasoning {{ padding:8px 0 !important; }}
#ce-precedent .ce-panel, .ce-cognition {{ border-left:none; padding-left:4px; }}
#ce-confirm {{ background:var(--ao-orange) !important; color:var(--ao-void) !important;
  font-weight:800 !important; border:none !important; border-radius:0 !important;
  text-transform:uppercase; letter-spacing:2px !important; }}
/* outcome / sim buttons get a quieter deck look — no border, just surface */
#ce-sim button, #ce-outcomes button {{ background:var(--ao-surface) !important;
  border:none !important; color:var(--ao-text) !important; }}

/* JSON + code blocks on the void */
.gr-json, .cm-editor, .code-wrap {{ background:var(--ao-void) !important; }}
footer {{ color:var(--ao-outline-dim) !important; }}

/* ── LCARS pill radio groups (part type, material) ── */
.ce-pills fieldset, .ce-pills .wrap {{ display:flex !important; flex-wrap:wrap; gap:6px;
  border:none !important; background:transparent !important; }}
.ce-pills label {{ border:1px solid var(--ao-outline) !important; border-radius:999px !important;
  padding:5px 15px !important; cursor:pointer; background:var(--ao-surface) !important;
  color:var(--ao-text) !important; text-transform:uppercase; letter-spacing:.5px;
  font-size:12px !important; font-weight:600; transition:all .12s; margin:0 !important; }}
.ce-pills label span {{ color:var(--ao-text) !important; }}            /* unselected: light, legible */
.ce-pills label:hover {{ border-color:var(--ao-orange) !important; color:var(--ao-orange-soft) !important; }}
.ce-pills label:hover span {{ color:var(--ao-orange-soft) !important; }}
.ce-pills input[type=radio] {{ position:absolute !important; opacity:0 !important; width:0 !important; height:0 !important; }}
.ce-pills label:has(input:checked) {{ background:var(--ao-orange) !important;
  border-color:var(--ao-orange) !important; font-weight:800; }}
.ce-pills label:has(input:checked), .ce-pills label:has(input:checked) span {{
  color:#131313 !important; }}                                         /* selected: dark on orange, readable */

/* ── LCARS pill buttons (mesh sources) ── */
.ce-pillbtn button {{ border-radius:999px !important; border:1px solid var(--ao-orange) !important;
  background:var(--ao-surface) !important; color:var(--ao-orange-soft) !important; box-shadow:none !important;
  text-transform:uppercase; letter-spacing:.5px; font-size:12px !important; font-weight:700; }}
.ce-pillbtn button:hover {{ border-color:var(--ao-orange) !important;
  background:var(--ao-orange) !important; color:#131313 !important; }}

/* number inputs as instrument fields */
.ce-num input {{ background:var(--ao-void) !important; border:1px solid var(--ao-outline-dim) !important;
  border-radius:0 !important; color:var(--ao-blue) !important; font-size:15px !important; font-weight:700; }}

/* accordion headers as LCARS stage bars */
.gradio-container .label-wrap, button.label-wrap {{ color:var(--ao-orange) !important; }}
details > summary, .accordion .label-wrap {{ text-transform:uppercase; letter-spacing:2px; }}

/* optional CRT scanline — off by default; add class 'ce-crt' to body to enable */
body.ce-crt .gradio-container::before {{ content:""; position:fixed; inset:0; z-index:9999;
  pointer-events:none; background:repeating-linear-gradient(0deg,
  rgba(0,0,0,0.10) 0px, rgba(0,0,0,0.10) 1px, transparent 1px, transparent 3px); }}
"""

# --- UI-overhaul layer (global rules from the walkthrough spec) ---------------
# No-emoji icons, custom consolidated loader (no stock radio spinners), top-right
# action bar + persistent reset, contained blocks (no orphans/empty boxes/gaps),
# mirrored headers/footers, vertical layer slider, segmented toggle, model switcher.
CSS += """
/* GLOBAL: kill every stock Gradio progress/loading indicator — one custom loader only.
   This is the single switch for all loaders (the user asked for it to be globally updatable). */
.gradio-container .progress, .gradio-container .progress-bar, .gradio-container .progress-level,
.gradio-container .progress-text, .gradio-container .meta-text, .gradio-container .meta-text-center,
.gradio-container .eta-bar, .gradio-container svg.loader, .gradio-container .loader,
.gradio-container .wrap.generating, .gradio-container .wrap.default.generating,
.gradio-container .status, .gradio-container .timer,
.gradio-container [class*="loading"], .gradio-container [aria-label="loading"] {
  display:none !important; opacity:0 !important; animation:none !important; }
/* never dim/blur/animate a component while it updates — content just appears when ready */
.gradio-container .generating, .gradio-container .pending, .gradio-container .dimmed,
.gradio-container .wrap.generating * {
  opacity:1 !important; filter:none !important; animation:none !important; border-color:var(--ao-outline-dim) !important; }
.gradio-container .generating::before, .gradio-container .generating::after { content:none !important; }

/* one custom consolidated loader: scanning bar + cycling stages + LCARS panels.
   When inside the slice tab, fills more vertical space so the user sees something
   is happening (was tiny before). */
.ce-loader { display:flex; flex-direction:column; gap:14px; align-items:stretch;
  padding:32px 24px; background:linear-gradient(180deg, rgba(255,156,0,0.04), transparent 120px);
  border-top:2px solid var(--ao-orange); min-height:220px; }
.ce-loader-bar { position:relative; width:100%; height:8px; background:var(--ao-surface-hi);
  overflow:hidden; border:1px solid var(--ao-outline-dim); }
.ce-loader-bar span { position:absolute; top:0; left:-40%; width:40%; height:100%;
  background:var(--ao-orange); animation:ce-scan 1.05s linear infinite;
  box-shadow:0 0 12px var(--ao-orange); }
@keyframes ce-scan { 0% { left:-40%; } 100% { left:100%; } }
.ce-loader-text { color:var(--ao-orange); letter-spacing:3px; text-transform:uppercase;
  font-size:13px; font-weight:800; }
.ce-loader-text::after { content:"…"; }

/* cycling stage list: each row dims/illuminates in turn so the user knows the
   pipeline is working even though we can't stream true progress from the LLM. */
.ce-loader-stages { display:flex; flex-direction:column; gap:4px;
  font-size:11px; letter-spacing:1.5px; text-transform:uppercase;
  color:var(--ao-outline); }
.ce-loader-stages > div { display:flex; align-items:center; gap:8px;
  opacity:0.35; transition:opacity .25s ease; }
.ce-loader-stages > div::before { content:"▸"; color:var(--ao-orange);
  opacity:0.5; }
.ce-loader-stages > div.active { opacity:1; color:var(--ao-orange-soft); }
.ce-loader-stages > div.active::before { opacity:1; }
.ce-loader-stages > div.done { opacity:0.7; color:var(--ao-text); }
.ce-loader-stages > div.done::before { content:"✓"; color:var(--ao-green); opacity:1; }

/* top-right action bar: small primary button, same spot every tab, reset persistent */
.ce-actionbar { display:flex !important; justify-content:flex-end !important;
  align-items:center; gap:8px; flex-wrap:nowrap; margin:2px 0 8px; }
.ce-actionbar > * { flex:0 0 auto !important; width:auto !important; min-width:0 !important; }
.ce-act button { min-width:0 !important; padding:7px 16px !important; font-size:12px !important; }

/* contained block: no border, just spacing — clean open layout */
.ce-card { padding:6px 0 !important; margin:0; }
.ce-card.cog { /* was border-left purple, now none */ }
/* collapse empty HTML panes so the unloaded state has no empty boxes */
.ce-collapse:empty, .ce-collapse > div:empty { display:none !important; }
.ce-collapse .html-container:empty { display:none !important; }

/* mirrored per-tab caption strip */
.ce-tabintro { color:var(--ao-outline); letter-spacing:.5px; font-size:12px; line-height:1.5;
  border-left:2px solid var(--ao-outline-dim); padding:4px 10px; margin:2px 0 8px; }
.ce-tabintro b { color:var(--ao-orange-soft); }

/* vertical layer slider (slides up/down beside the slicer) */
.ce-vslider input[type=range] { writing-mode:vertical-lr; direction:rtl;
  width:8px !important; height:300px !important; }
.ce-vslider { display:flex; justify-content:center; }

/* ── HORIZONTAL LAYER SCRUBBER (replaces the broken vertical slider) ── */
/* Spans full width below the slicer image. Filled track left of the thumb,
   tick marks every 5 layers, big thumb, current/max readout above. */
.ce-hslider { width:100% !important; margin:14px 0 8px !important;
  padding:14px 16px !important;
  background:linear-gradient(180deg, rgba(255,156,0,0.04), transparent);
  border-top:1px solid var(--ao-outline-dim);
  border-bottom:1px solid var(--ao-outline-dim); }
.ce-hslider > * { width:100% !important; }
.ce-hslider label, .ce-hslider .head { color:var(--ao-orange) !important;
  letter-spacing:3px; text-transform:uppercase; font-weight:800 !important;
  font-size:11px !important; margin-bottom:6px !important;
  display:flex !important; align-items:center !important; gap:10px !important; }
.ce-hslider label::before { content:"LAYER"; }
.ce-hslider label > * { font-size:11px !important; }
.ce-hslider input[type=range] { width:100% !important; height:14px !important;
  -webkit-appearance:none !important; appearance:none !important;
  background:transparent !important; cursor:pointer; }
.ce-hslider input[type=range]::-webkit-slider-runnable-track {
  height:6px; background:var(--ao-surface-hi);
  border:1px solid var(--ao-outline-dim);
  background-image:repeating-linear-gradient(90deg,
    var(--ao-outline-dim) 0, var(--ao-outline-dim) 1px,
    transparent 1px, transparent calc(100% / 8)); }
.ce-hslider input[type=range]::-moz-range-track {
  height:6px; background:var(--ao-surface-hi);
  border:1px solid var(--ao-outline-dim); }
.ce-hslider input[type=range]::-webkit-slider-thumb {
  -webkit-appearance:none; appearance:none;
  width:20px; height:20px; border-radius:0;
  background:var(--ao-orange); border:2px solid var(--ao-orange);
  margin-top:-7px; cursor:grab;
  box-shadow:0 0 8px rgba(255,156,0,0.6); }
.ce-hslider input[type=range]::-webkit-slider-thumb:active { cursor:grabbing;
  background:#fff; }
.ce-hslider input[type=range]::-moz-range-thumb {
  width:20px; height:20px; border-radius:0;
  background:var(--ao-orange); border:2px solid var(--ao-orange);
  cursor:grab; box-shadow:0 0 8px rgba(255,156,0,0.6); }
/* hide gradio's number-field side (we only want the slider here) */
.ce-hslider .min, .ce-hslider .max,
.ce-hslider input[type=number],
.ce-hslider button[aria-label="Reset"],
.ce-hslider .source-selection { display:none !important; }
.ce-hslider .head .v { color:var(--ao-blue); font-weight:800; }
.ce-hslider .head .max { color:var(--ao-outline); font-weight:600; }

/* Virtual print preview — bigger, framed, motion-aware */
.ce-vp { padding:8px !important; border:1px solid var(--ao-outline-dim) !important;
  background:var(--ao-void) !important; display:flex !important; flex-direction:column !important; gap:6px !important; }
.ce-vp-wrap { border:1px solid var(--ao-outline-dim); background:#0a0c14; display:inline-block; }
.ce-vp canvas { display:block; max-width:100%; height:auto; }
.ce-vp svg { width:100% !important; height:auto !important; max-height:300px !important; }
.ce-vp .ce-vp-caption { color:var(--ao-outline); font-size:11px;
  letter-spacing:1px; text-transform:uppercase; padding:4px 2px; }
.ce-vp-replay { align-self:flex-start; }
/* side-by-side slice visualizers: equal-width columns */
.ce-slice-viz { gap:16px !important; }
.ce-slice-viz .ce-slice-col { flex:1 1 0 !important; min-width:0 !important; }
.ce-slice-viz .ce-slice-col .gr-image,
.ce-slice-viz .ce-slice-col .gr-image > div,
.ce-slice-viz .ce-slice-col .gr-image img { width:100% !important; height:auto !important; display:block !important; }

/* Mini loader (Second Opinion in-flight — smaller than the full preflight loader).
   Same scanning-bar look but condensed. */
.ce-mini-loader { display:flex; flex-direction:column; gap:8px;
  padding:14px 16px; min-height:90px;
  background:linear-gradient(180deg, rgba(255,156,0,0.04), transparent 80px);
  border-left:3px solid var(--ao-orange); margin:6px 0; }
.ce-mini-loader .ce-loader-bar { height:4px; }
.ce-mini-loader .ce-loader-text { font-size:11px; letter-spacing:2px; }
.ce-mini-loader .ce-loader-stages > div { font-size:10px; }

/* segmented toggle (Engineer's Read | Second Opinion) — reuses pill radios, joined */
.ce-seg fieldset, .ce-seg .wrap { display:flex !important; gap:0 !important; }
.ce-seg label { border-radius:0 !important; border:1px solid var(--ao-outline) !important;
  margin:0 -1px 0 0 !important; padding:6px 16px !important; }
.ce-seg label:first-of-type { border-top-left-radius:4px !important; border-bottom-left-radius:4px !important; }
.ce-seg label:last-of-type { border-top-right-radius:4px !important; border-bottom-right-radius:4px !important; }

/* model switcher pills sit in the header row — KEEP concise, don't conflict with main rule */
#ce-modelswitch .ce-seg label {{ font-size:11px !important; padding:5px 12px !important; }}

/* compact inline pill groups inside the envbar (BUILD-PLATE POSITION + MATERIAL) */
.ce-envbar .ce-inline-group { display:flex !important; flex-direction:column !important;
  gap:3px !important; margin:0 4px !important; min-width:0; }
.ce-envbar .ce-inline-group:first-of-type { margin-left:0 !important; }
.ce-envbar .ce-inline-label { color:var(--ao-orange); font-size:10px !important;
  letter-spacing:1.5px; text-transform:uppercase; font-weight:700;
  display:flex !important; align-items:center !important; gap:4px; }
.ce-envbar .ce-inline-label .ce-callout { font-size:10px !important; }
.ce-envbar .ce-inline-label .ce-tip { width:280px; top:120%; }
/* inline pills are smaller than the full-width ones */
.ce-envbar .ce-pills label { padding:4px 10px !important; font-size:11px !important; }
.ce-envbar .ce-pills label span { display:inline-flex !important; align-items:center !important;
  gap:5px !important; }
/* pill icons by value (small, before the label text) */
.ce-pills label:has(input[value="center"]) span::before,
.ce-pills label:has(input[value="edge"]) span::before,
.ce-pills label:has(input[value="corner"]) span::before,
.ce-pills label:has(input[value="PLA"]) span::before,
.ce-pills label:has(input[value="PETG"]) span::before,
.ce-pills label:has(input[value="ABS"]) span::before,
.ce-pills label:has(input[value="TPU"]) span::before {
  content:""; display:inline-block; width:11px; height:11px; flex:0 0 11px;
  background:currentColor; -webkit-mask-size:contain; mask-size:contain;
  -webkit-mask-repeat:no-repeat; mask-repeat:no-repeat;
  -webkit-mask-position:center; mask-position:center; }
.ce-pills label:has(input[value="center"]) span::before {
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2v3 M12 19v3 M2 12h3 M19 12h3 M12 7a5 5 0 100 10 5 5 0 000-10z'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2v3 M12 19v3 M2 12h3 M19 12h3 M12 7a5 5 0 100 10 5 5 0 000-10z'/></svg>"); }
.ce-pills label:has(input[value="edge"]) span::before {
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4 4h16v16H4z M4 4v16'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4 4h16v16H4z M4 4v16'/></svg>"); }
.ce-pills label:has(input[value="corner"]) span::before {
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4 4h16v16H4z M4 4v7 M4 4h7'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M4 4h16v16H4z M4 4v7 M4 4h7'/></svg>"); }
.ce-pills label:has(input[value="PLA"]) span::before,
.ce-pills label:has(input[value="PETG"]) span::before,
.ce-pills label:has(input[value="ABS"]) span::before,
.ce-pills label:has(input[value="TPU"]) span::before {
  -webkit-mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2.5C12 2.5 5 10 5 14a7 7 0 0014 0c0-4-7-11.5-7-11.5z'/></svg>");
  mask-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2.5C12 2.5 5 10 5 14a7 7 0 0014 0c0-4-7-11.5-7-11.5z'/></svg>"); }
/* tighten space below the envbar so the PART card sits directly under it */
.ce-envbar { margin-bottom:2px !important; }

/* hover callout (info icon next to the model switcher) */
.ce-callout { position:relative; display:inline-flex; align-items:center; gap:4px; cursor:help;
  color:var(--ao-orange); font-size:11px; letter-spacing:1px; text-transform:uppercase; }
.ce-callout .ce-tip { display:none; position:absolute; top:135%; left:0; z-index:60; width:340px;
  background:var(--ao-surface-hi); border:1px solid var(--ao-orange); padding:9px 11px;
  font-size:11px; line-height:1.55; color:var(--ao-text); text-transform:none; letter-spacing:.3px;
  box-shadow:0 6px 20px rgba(0,0,0,.55); }
.ce-callout:hover .ce-tip, .ce-callout:focus .ce-tip { display:block; }

/* padded markdown/text inside grouped sections (no flush-left text against the panel edge) */
.ce-pad, .ce-pad p { padding-left:12px !important; padding-right:12px !important; }

/* custom blank model/part viewer (no generic Gradio empty canvas) */
.ce-viewer { display:flex; flex-direction:column; align-items:center; justify-content:center;
  text-align:center; min-height:360px; gap:12px; padding:24px;
  border:1px dashed var(--ao-outline-dim); background:
  radial-gradient(circle at 50% 38%, rgba(255,156,0,0.06), transparent 60%), #0a0c14; }
.ce-viewer-ico { color:var(--ao-orange); opacity:.85; }
.ce-viewer-title { color:var(--ao-orange); letter-spacing:3px; font-weight:800; font-size:13px; }
.ce-viewer-copy { color:var(--ao-text); font-size:13px; line-height:1.6; max-width:440px; }
.ce-viewer-copy b { color:var(--ao-orange-soft); }
.ce-viewer-hint { color:var(--ao-outline); font-size:11px; letter-spacing:1px; text-transform:uppercase; }

/* fully custom dropdown (model switcher) — ONE border on the outer wrapper.
   Previously stacked borders on .wrap + .secondary-wrap + .container + label > div
   produced nested outlines. Now everything inside is transparent + borderless. */
.ce-modeldd, .ce-modeldd > div, .ce-modeldd .wrap, .ce-modeldd .secondary-wrap,
.ce-modeldd .container, .ce-modeldd > label > div, .ce-modeldd input {
  border:none !important; outline:none !important; box-shadow:none !important;
  border-radius:0 !important; background:var(--ao-void) !important;
  color:var(--ao-orange-soft) !important; }
.ce-modeldd { border:1px solid var(--ao-orange) !important; }
.ce-modeldd:focus-within { box-shadow:0 0 0 1px var(--ao-orange) !important; }
.ce-modeldd input { text-transform:uppercase; letter-spacing:1px;
  font-size:11px !important; font-weight:700; cursor:pointer;
  padding:6px 10px !important; }
.ce-modeldd .icon-wrap, .ce-modeldd svg { color:var(--ao-orange) !important; fill:var(--ao-orange) !important; }
/* dropdown options panel */
ul.options, .ce-modeldd ul { background:var(--ao-surface-hi) !important; border:1px solid var(--ao-orange) !important;
  border-radius:0 !important; }
ul.options li, .ce-modeldd ul li { color:var(--ao-text) !important; text-transform:uppercase;
  letter-spacing:.5px; font-size:11px !important; }
ul.options li.selected, ul.options li:hover { background:var(--ao-orange) !important; color:#131313 !important; }
"""

# tiny LCARS clock — updates the command-bar time; no-op if the element is absent
CLOCK_JS = """
() => {
  const tick = () => {
    const el = document.getElementById('ce-clock');
    if (el) {
      const d = new Date();
      el.textContent = d.toISOString().slice(11,19) + ' UTC';
    }
  };
  tick(); setInterval(tick, 1000);

  // Popup wiring: any [data-popup-trigger="X"] toggles all .ce-popup-X (and backdrop).
  // Click outside or on .ce-popup-close to dismiss. Re-runs in case popups are added later.
  const wirePopups = () => {
    document.querySelectorAll('[data-popup-trigger]').forEach(btn => {
      if (btn.dataset._wired) return;
      btn.dataset._wired = '1';
      btn.addEventListener('click', (e) => {
        e.preventDefault(); e.stopPropagation();
        const id = btn.dataset.popupTrigger;
        const pops = document.querySelectorAll('.ce-popup-' + id);
        const bd = document.querySelector('[data-popup-backdrop="' + id + '"]');
        const isOpening = pops.length && !pops[0].classList.contains('open');
        document.querySelectorAll('.ce-popup.open, .ce-popup-backdrop.open')
          .forEach(x => x.classList.remove('open'));
        if (isOpening) {
          pops.forEach(p => p.classList.add('open'));
          if (bd) bd.classList.add('open');
        }
      });
    });
    document.querySelectorAll('.ce-popup-close, [data-popup-backdrop]').forEach(el => {
      if (el.dataset._wired) return;
      el.dataset._wired = '1';
      el.addEventListener('click', () => {
        document.querySelectorAll('.ce-popup.open, .ce-popup-backdrop.open')
          .forEach(x => x.classList.remove('open'));
      });
    });
  };
  wirePopups(); setInterval(wirePopups, 1500);

  // Cycle loader stages: each [data-stages="cycle"] walks through its children
  // marking one .active, prior ones .done. Tracks per-element so multiple loaders
  // can run independently. Resets if the element is replaced (Gradio HTML update).
  const cycleStages = () => {
    document.querySelectorAll('[data-stages="cycle"]').forEach(el => {
      const kids = el.children;
      if (!kids.length) return;
      if (el.dataset._idx === undefined) {
        el.dataset._idx = '0';
        el.dataset._tick = String(Date.now());
      }
      const now = Date.now();
      const last = Number(el.dataset._tick);
      // advance every 1200ms
      if (now - last < 1200) return;
      el.dataset._tick = String(now);
      let i = Number(el.dataset._idx);
      // mark prior as done, current as active
      for (let k = 0; k < kids.length; k++) {
        kids[k].classList.remove('active', 'done');
        if (k < i) kids[k].classList.add('done');
        else if (k === i) kids[k].classList.add('active');
      }
      i = (i + 1) % (kids.length + 1);  // +1 lets all-done state breathe one tick
      el.dataset._idx = String(i);
    });
  };
  setInterval(cycleStages, 200);
}
"""


# --- custom icon set (no emojis anywhere — global UI rule) --------------------
# Inline SVG, stroke=currentColor so each icon inherits its surrounding text
# color. (name → (path_d, filled?)). Drawn on a 24x24 grid, Feather-ish.
_ICONS: dict[str, tuple[str, bool]] = {
    "bolt": ("M13 2L4 14h7l-1 8 10-12h-7l0-8z", True),
    "shuffle": ("M16 3h5v5 M21 3l-7 7 M16 21h5v-5 M3 3l18 18 M3 21l7-7", False),
    "sliders": ("M4 6h10 M18 6h2 M4 12h2 M10 12h10 M4 18h8 M16 18h4 "
                "M16 4v4 M6 10v4 M12 16v4", False),
    "search": ("M11 4a7 7 0 100 14 7 7 0 000-14z M21 21l-4.3-4.3", False),
    "check": ("M20 6L9 17l-5-5", False),
    "alert": ("M12 3L2 21h20L12 3z M12 10v5 M12 18h.01", False),
    "shield": ("M12 2l8 4v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-4z", False),
    "flask": ("M9 2h6 M10 2v6L4 19a1 1 0 001 1h14a1 1 0 001-1L14 8V2 M7 14h10", False),
    "thermo": ("M14 14V5a2 2 0 10-4 0v9a4 4 0 104 0z", False),
    "droplet": ("M12 2.5C12 2.5 5 10 5 14a7 7 0 0014 0c0-4-7-11.5-7-11.5z", False),
    "target": ("M12 2v3 M12 19v3 M2 12h3 M19 12h3 M12 7a5 5 0 100 10 5 5 0 000-10z", False),
    "edge": ("M4 4h16v16H4z M4 4v16", False),
    "corner": ("M4 4h16v16H4z M4 4v7 M4 4h7", False),
    "printer": ("M6 9V2h12v7 M6 18H4a2 2 0 01-2-2v-4a2 2 0 012-2h16a2 2 0 012 2v4a2 2 0 01-2 2h-2 "
                "M6 14h12v8H6z", False),
    "play": ("M6 4l14 8-14 8V4z", True),
    "x": ("M18 6L6 18 M6 6l12 12", False),
    "book": ("M4 4a2 2 0 012-2h12v18H6a2 2 0 01-2 2V4z M8 2v18", False),
    "reset": ("M3 2v6h6 M3.5 13a9 9 0 102.6-7.4L3 8", False),
    "refresh": ("M21 2v6h-6 M20.5 13a9 9 0 11-2.6-7.4L21 8", False),
    "arrow": ("M4 12h14 M13 6l6 6-6 6", False),
    "chip": ("M9 9h6v6H9z M5 5h14v14H5z M9 2v3 M15 2v3 M9 19v3 M15 19v3 "
             "M2 9h3 M2 15h3 M19 9h3 M19 15h3", False),
    "layers": ("M12 2l9 5-9 5-9-5 9-5z M3 12l9 5 9-5 M3 17l9 5 9-5", False),
    "anchor": ("M12 2a2 2 0 100 4 2 2 0 000-4z M12 6v15 M5 12H2a10 10 0 0020 0h-3", False),
    "gauge": ("M12 13l4-4 M12 21a9 9 0 119-9 M3 12a9 9 0 019-9", False),
    "info": ("M12 3a9 9 0 100 18 9 9 0 000-18z M12 11v5 M12 8h.01", False),
}


def icon(name: str, size: int = 14, color: str | None = None) -> str:
    """Inline SVG icon (no emoji). Inherits text color unless `color` is given."""
    path, filled = _ICONS.get(name, ("", False))
    stroke = "none" if filled else "currentColor"
    fill = "currentColor" if filled else "none"
    style = "vertical-align:-0.16em;display:inline-block;"
    if color:
        style += f"color:{color};"
    return (
        f"<svg viewBox='0 0 24 24' width='{size}' height='{size}' fill='{fill}' "
        f"stroke='{stroke}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' "
        f"style='{style}'><path d='{path}'/></svg>"
    )


def loader(text: str = "WORKING", stages: list[str] | None = None) -> str:
    """Consolidated custom loader: scanning bar + label + cycling stages list.
    The stages animate via JS (CLOCK_JS wires it on load) to communicate that
    work is happening through a multi-stage pipeline."""
    stage_html = ""
    if stages is None:
        stages = [
            "reading the part geometry",
            "slicing cross-sections",
            "querying precedent ledger",
            "engineer proposing settings",
            "qa inspector reviewing",
        ]
    if stages:
        items = "".join(f"<div>{s}</div>" for s in stages)
        stage_html = f"<div class='ce-loader-stages' data-stages='cycle'>{items}</div>"
    return (
        "<div class='ce-loader'>"
        f"<div class='ce-loader-text'>{text}</div>"
        "<div class='ce-loader-bar'><span></span></div>"
        f"{stage_html}"
        "</div>"
    )


def tab_intro(text: str) -> str:
    """A consistent per-tab caption strip (mirrored across tabs)."""
    return f"<div class='ce-tabintro'>{text}</div>"


def rule(label: str) -> str:
    """An LCARS rule header: ``LABEL ─────────────`` (line fills via CSS)."""
    return f"<div class='ce-rule'>{label}</div>"


def footer_bar(job: str | None = None, env: str | None = None) -> str:
    """Sticky Astrometrics status strip (replaces the hidden Gradio footer).
    When a job/env is passed, the strip carries the live job context."""
    left = f"JOB · {job}" if job else "ASTROMETRICS OS · MICROFACTORY NODE"
    right = env if env else "FULLY LOCAL · GEMMA4"
    return (
        "<div id='ce-footer' style='position:sticky;bottom:0;z-index:30;"
        "display:flex;justify-content:space-between;gap:16px;margin-top:14px;"
        "padding:6px 14px;border-top:2px solid var(--ao-orange);background:var(--ao-surface-hi);"
        "font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--ao-outline);'>"
        f"<span style='color:var(--ao-orange);'>{left}</span>"
        "<span>LLM PROPOSES · <b style='color:var(--ao-orange);'>SPINE DISPOSES</b> · INSPECTOR GRADES</span>"
        f"<span>{right}</span></div>"
    )


def inspector_panel(verdict, *, label: str = "LA FORGE · QA INSPECTOR") -> str:
    """Render an InspectorVerdict as a distinct reviewer card (separate voice)."""
    col = verdict.color
    agree = ""
    if verdict.agreement is not None:
        ic = icon("check") if verdict.agreement else icon("x")
        txt = "prediction held" if verdict.agreement else "prediction missed"
        agree = ("<span style='float:right;font-size:10px;color:var(--ao-outline);'>"
                 f"{ic} {txt}</span>")
    return (
        "<div style='font-family:ui-monospace,monospace;background:var(--ao-void);"
        f"border:1px solid var(--ao-outline-dim);border-left:3px solid {col};padding:8px 12px;'>"
        f"<div style='color:{col};font-weight:700;letter-spacing:2px;font-size:11px;'>"
        f"{icon('search')} {label} <span style='color:var(--ao-outline);font-weight:400;'>"
        f"[{verdict.stance.upper()}]</span>{agree}</div>"
        f"<div style='color:var(--ao-text);font-size:14px;font-weight:700;margin:4px 0;'>{verdict.headline}</div>"
        f"<div class='ce-sub' style='font-size:12px;'>{verdict.detail}</div></div>"
    )


def command_bar(backend_status: str) -> str:
    """The top LCARS command strip: orange elbow title + status/clock bar.
    The model switcher (dropdown + warm + model info) gets baked into the right
    side of this bar via a placeholder div (#ce-cmdbar-slot) that the Gradio
    Row mounts into via CSS positioning."""
    return (
        "<div id='ce-cmdbar'>"
        "<div class='ce-elbow'>▚ MICROFACTORY NODE: 3D PRINTER</div>"
        "<div class='ce-bar'>"
        f"<span class='ce-cmdbar-status'>{backend_status}</span>"
        "<span class='ce-cmdbar-tag'>BUILD&nbsp;SMALL · BACKYARD&nbsp;AI</span>"
        "<span id='ce-clock'>--:--:-- UTC</span>"
        "</div></div>"
    )
