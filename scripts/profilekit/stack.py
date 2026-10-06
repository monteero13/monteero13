"""One mono line under the skill-icons row for tools that have no icon there
(LangGraph, Qdrant...): `also  langgraph · langchain · qdrant`."""

from __future__ import annotations

from .config import Loc
from .svg import document, esc, n, text_width

W, H = 840, 24
SIZE = 12.5
GAP = 18


def render(cfg, loc: Loc, theme: str) -> str:
    c = cfg.palette(theme)
    mono = cfg.theme["mono"]
    s = cfg.get("stack", {})
    key = loc(s.get("extra_label", ""))
    items = [loc(i) for i in s.get("extra", [])]

    widths = [text_width(i, SIZE, mono=True) for i in items]
    key_w = text_width(key, SIZE, mono=True) + 14 if key else 0
    total = key_w + sum(widths) + GAP * (len(items) - 1)
    x = (W - total) / 2  # centred under the icon row

    parts = []
    if key:
        parts.append(f'<text x="{n(x)}" y="16" font-family="{esc(mono)}" font-size="{SIZE}" '
                     f'fill="{c["muted"]}">{esc(key)}</text>')
        x += key_w
    for k, (item, w) in enumerate(zip(items, widths)):
        if k:
            parts.append(f'<circle cx="{n(x - GAP / 2)}" cy="11.5" r="1.4" fill="{c["faint"]}"/>')
        parts.append(f'<text x="{n(x)}" y="16" font-family="{esc(mono)}" font-size="{SIZE}" '
                     f'fill="{c["strong"]}">{esc(item)}</text>')
        x += w + GAP
    return document(W, H, ", ".join(items), cfg.theme["font"], "".join(parts))
