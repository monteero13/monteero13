"""Profile header: optional round portrait, name, role, a status line and a
prompt that types a few phrases in turn. A tiny agent graph sits on the right as the one moving detail."""

from __future__ import annotations

import base64
from pathlib import Path

from .config import Loc
from .svg import document, esc, flow, live_dot, n

W, H = 840, 168
PHRASE_S = 4.2      # seconds each phrase stays on screen (typing included)
TYPE_S = 0.045      # seconds per typed character
AVATAR_D = 132     # portrait diameter
AVATAR_Y = 16


def _typing(phrases: list[str], x: float, y: float, size: float, c: dict, mono: str) -> str:
    """Each phrase is revealed by a clip that grows one character at a time
    (discrete steps), then hidden while the next one types. textLength pins the
    glyph advance, so clip steps land exactly on character boundaries."""
    cw = size * 0.6
    total = PHRASE_S * len(phrases)
    out = []
    for i, phrase in enumerate(phrases):
        start = i * PHRASE_S
        times, widths = [0.0], [0.0]
        for k in range(1, len(phrase) + 1):
            times.append(start + k * TYPE_S)
            widths.append(k * cw)
        times.append(start + PHRASE_S - 0.05)
        widths.append(0.0)
        if times[1] > 0:  # stay hidden until this phrase's turn
            times.insert(1, start)
            widths.insert(1, 0.0)
        # discrete keyTimes must be strictly increasing and end before 1
        kt = ";".join(f"{t / total:.4f}" for t in times)
        clip = f"tp{i}"
        out.append(
            f'<clipPath id="{clip}"><rect x="{n(x)}" y="{n(y - size)}" height="{n(size * 1.5)}" '
            f'width="{n(widths[-1] if i else len(phrase) * cw)}">'
            f'<animate attributeName="width" dur="{n(total)}s" repeatCount="indefinite" '
            f'calcMode="discrete" keyTimes="{kt}" values="{";".join(n(v) for v in widths)}"/></rect></clipPath>'
            f'<text x="{n(x)}" y="{n(y)}" clip-path="url(#{clip})" font-family="{esc(mono)}" '
            f'font-size="{size}" fill="{c["strong"]}" textLength="{n(len(phrase) * cw)}" '
            f'lengthAdjust="spacingAndGlyphs">{esc(phrase)}</text>'
        )
        # cursor follows the clip edge and is only shown during its phrase
        end = (start + PHRASE_S) / total
        if start:
            vis_kt, vis = f"0;{start / total:.4f};{end:.4f}", "0;.85;0"
        else:
            vis_kt, vis = f"0;{end:.4f}", ".85;0"
        out.append(
            f'<rect x="{n(x + (len(phrase) * cw if i == 0 else 0))}" y="{n(y - size * 0.8)}" '
            f'width="{n(cw * 0.9)}" height="{n(size * 1.05)}" fill="{c["accent"]}" opacity="0">'
            f'<animate attributeName="x" dur="{n(total)}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{kt}" values="{";".join(n(x + v + 2) for v in widths)}"/>'
            f'<animate attributeName="opacity" dur="{n(total)}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{vis_kt}" values="{vis}"/></rect>'
        )
    return "".join(out)


def _avatar(path: Path, c: dict) -> str:
    """The portrait embedded as a data URI (an SVG shown through <img> cannot
    load external files), clipped to a circle with a hairline ring and an
    online-style live dot."""
    if not path.exists():
        raise SystemExit(f"profile.toml: [header].avatar not found: {path}")
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode()
    r = AVATAR_D / 2
    cx, cy = r, AVATAR_Y + r
    dot_x, dot_y = cx + r * 0.71, cy + r * 0.71
    return (
        f'<clipPath id="av"><circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r - 1)}"/></clipPath>'
        f'<image href="data:{mime};base64,{data}" x="0" y="{AVATAR_Y}" width="{AVATAR_D}" '
        f'height="{AVATAR_D}" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>'
        f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r - 0.5)}" fill="none" stroke="{c["line"]}"/>'
        f'<circle cx="{n(dot_x)}" cy="{n(dot_y)}" r="7" fill="{c["bg"]}"/>'
        + live_dot(dot_x, dot_y, c, r=4.5)
    )


def render(cfg, loc: Loc, theme: str) -> str:
    c = cfg.palette(theme)
    font, mono = cfg.theme["font"], cfg.theme["mono"]
    h = cfg.get("header", {})
    p = cfg.profile

    body = []
    x = 0
    avatar = h.get("avatar")
    if avatar:
        body.append(_avatar(cfg.path.parent / avatar, c))
        x = AVATAR_D + 26

    body.append(f'<text x="{x}" y="16" font-family="{esc(mono)}" font-size="12" fill="{c["muted"]}">'
                f'~/{esc(cfg.username)}</text>')
    status = loc(h.get("status", ""))
    if status:
        body.append(f'<text x="{W}" y="16" text-anchor="end" font-family="{esc(mono)}" font-size="12" '
                    f'fill="{c["text"]}">{esc(status)}</text>')
        if not avatar:  # with an avatar the live dot sits on the portrait instead
            body.append(live_dot(W - len(status) * 12 * 0.61 - 12, 12, c))

    body.append(f'<text x="{x}" y="66" font-size="38" font-weight="700" fill="{c["strong"]}" '
                f'letter-spacing="-1">{esc(p["name"])}</text>')
    body.append(f'<text x="{x}" y="96" font-size="15" fill="{c["text"]}">{esc(loc(h.get("role", "")))}</text>')

    phrases = [loc(t) for t in h.get("typing", [])]
    if phrases:
        body.append(f'<text x="{x}" y="136" font-family="{esc(mono)}" font-size="14" '
                    f'fill="{c["accent"]}">&gt;</text>')
        body.append(_typing(phrases, x + 18, 136, 14, c, mono))

    labels = h.get("flow_labels")
    if labels is not None or h.get("flow", True):
        # beside the prompt line, inset so the outer labels never touch the edge
        body.append(flow(W - 236, 106, 214, 40, c, [loc(lb) for lb in (labels or [])], mono))

    body.append(f'<line x1="0" x2="{W}" y1="{H - 0.5}" y2="{H - 0.5}" stroke="{c["line"]}"/>')
    return document(W, H, f'{p["name"]} — {loc(h.get("role", ""))}', font, "".join(body))
