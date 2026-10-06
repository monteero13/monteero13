"""Section headings: `01 · about ─────────────── ≈≈≈` in mono.
A hairline runs to the right edge and ends in a small motif."""

from __future__ import annotations

from .config import Loc
from .svg import document, esc, helix, n, pulse, text_width

W, H = 840, 30


def render(cfg, loc: Loc, theme: str, section: str, index: int) -> str:
    c = cfg.palette(theme)
    mono = cfg.theme["mono"]
    style = cfg.get("style", {})
    spec = cfg["headings"][section]
    title = loc(spec)
    motif = spec.get("motif", style.get("heading_motif", "helix")) if isinstance(spec, dict) \
        else style.get("heading_motif", "helix")

    y = 19
    parts = []
    x = 0.0
    if style.get("numbered", True):
        num = f"{index:02d}"
        parts.append(f'<text x="0" y="{y}" font-family="{esc(mono)}" font-size="12" '
                     f'fill="{c["muted"]}">{num}<tspan dx="6" fill="{c["faint"]}">/</tspan></text>')
        x = text_width(num + " /", 12, mono=True) + 12
    parts.append(f'<text x="{n(x)}" y="{y}" font-family="{esc(mono)}" font-size="14" '
                 f'font-weight="600" fill="{c["strong"]}" letter-spacing=".3">{esc(title)}</text>')
    x += text_width(title, 14, mono=True) + 16

    motif_w = 72 if motif != "none" else 0
    line_end = W - motif_w - (14 if motif_w else 0)
    parts.append(f'<line x1="{n(x)}" x2="{n(line_end)}" y1="{y - 4.5}" y2="{y - 4.5}" '
                 f'stroke="{c["line"]}"/>')
    if motif == "helix":
        parts.append(helix(section, W - motif_w, y - 12, motif_w, 15, c, period=30))
    elif motif == "pulse":
        parts.append(pulse(W - motif_w, y - 15, motif_w, 16, c))

    return document(W, H, title, cfg.theme["font"], "".join(parts))
