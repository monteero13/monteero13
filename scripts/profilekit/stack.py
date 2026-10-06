"""Stack as a small mono manifest: muted keys, values separated by thin dots."""

from __future__ import annotations

from .config import Loc
from .svg import document, esc, n, text_width

W = 840
ROW = 26
SIZE = 13


def render(cfg, loc: Loc, theme: str) -> str:
    c = cfg.palette(theme)
    mono = cfg.theme["mono"]
    rows = cfg.get("stack", [])
    key_w = max((text_width(loc(r["key"]), SIZE, mono=True) for r in rows), default=0) + 28
    H = len(rows) * ROW + 6

    parts = []
    for i, row in enumerate(rows):
        y = 18 + i * ROW
        parts.append(f'<text x="0" y="{y}" font-family="{esc(mono)}" font-size="{SIZE}" '
                     f'fill="{c["muted"]}">{esc(loc(row["key"]))}</text>')
        x = key_w
        for k, item in enumerate(row["items"]):
            if k:
                parts.append(f'<circle cx="{n(x - 9)}" cy="{y - 4.5}" r="1.4" fill="{c["faint"]}"/>')
            label = loc(item)
            parts.append(f'<text x="{n(x)}" y="{y}" font-family="{esc(mono)}" font-size="{SIZE}" '
                         f'fill="{c["strong"]}">{esc(label)}</text>')
            x += text_width(label, SIZE, mono=True) + 18
    return document(W, H, ", ".join(", ".join(map(loc, r["items"])) for r in rows),
                    cfg.theme["font"], "".join(parts))
