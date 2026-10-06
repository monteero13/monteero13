"""Small helpers shared by every SVG renderer, plus the two signature motifs
(helix and pulse) drawn at detail size."""

from __future__ import annotations

import math


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def n(v: float) -> str:
    """Compact number for SVG attributes."""
    return f"{v:.1f}".rstrip("0").rstrip(".")


def text_width(s: str, size: float, mono: bool = False, bold: bool = False) -> float:
    """Estimated advance width. Generous on purpose: it only drives layout."""
    if mono:
        return len(s) * size * 0.61
    return len(s) * size * (0.58 if bold else 0.54)


def wrap(text: str, size: float, max_w: float, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    i = 0
    while i < len(words):
        trial = f"{cur} {words[i]}".strip()
        if text_width(trial, size) <= max_w or not cur:
            cur = trial
            i += 1
        else:
            lines.append(cur)
            cur = ""
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if i < len(words) and lines:
        last = lines[-1]
        while last and text_width(last + "…", size) > max_w:
            last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
        lines[-1] = last + "…"
    return lines


def document(w: float, h: float, label: str, font: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(w)} {n(h)}" '
        f'width="{n(w)}" height="{n(h)}" role="img" aria-label="{esc(label)}" '
        f'font-family="{esc(font)}"><title>{esc(label)}</title>{body}</svg>'
    )


def delayed_fade(delay: float, total: float) -> str:
    """Fade-in starting at `delay`. One animation from t=0, so renderers that
    ignore SMIL still show the element's own (visible) state."""
    k = min(delay / total, 0.98)
    return (f'<animate attributeName="opacity" dur="{n(total)}s" fill="freeze" '
            f'values="0;0;1" keyTimes="0;{k:.3f};1"/>')


# --------------------------------------------------------------------------- #
# motifs
# --------------------------------------------------------------------------- #


def helix(uid: str, x: float, y: float, w: float, h: float, c: dict, period: float = 26) -> str:
    """A tiny double helix that scrolls sideways, which reads as rotation.
    The pattern is two periods wide and translates by exactly one, so the
    loop is seamless. `uid` keeps clipPath ids unique inside one document."""
    amp, cy = h / 2 - 1, y + h / 2
    span = w + period
    steps = int(span / 1.5)

    def strand(sign: int) -> str:
        pts = [(x + i * span / steps, cy + sign * amp * math.sin(2 * math.pi * i * span / steps / period))
               for i in range(steps + 1)]
        return "M" + " L".join(f"{n(px)} {n(py)}" for px, py in pts)

    rungs = ""
    for j in range(int(span / (period / 8)) + 1):
        s = abs(math.sin(2 * math.pi * j / 8))
        if s > 0.4:  # skip the crossings, where the strands meet
            half = amp * s * 0.8
            rungs += f"M{n(x + j * period / 8)} {n(cy - half)}v{n(2 * half)}"
    return (
        f'<clipPath id="hx{uid}"><rect x="{n(x)}" y="{n(y - 1)}" width="{n(w)}" height="{n(h + 2)}"/></clipPath>'
        f'<g clip-path="url(#hx{uid})"><g>'
        f'<animateTransform attributeName="transform" type="translate" values="0 0;{n(-period)} 0" '
        f'dur="2.6s" repeatCount="indefinite"/>'
        f'<path d="{rungs}" stroke="{c["faint"]}" stroke-width="1"/>'
        f'<path d="{strand(1)}" fill="none" stroke="{c["strong"]}" stroke-width="1.3" stroke-linecap="round"/>'
        f'<path d="{strand(-1)}" fill="none" stroke="{c["muted"]}" stroke-width="1.3" stroke-linecap="round"/>'
        f'</g></g>'
    )


def ecg_path(x0: float, x1: float, base: float, amp: float, period: float,
             offset: float = 0.0) -> str:
    """A stylised PQRST trace from x0 to x1, one beat every `period` px."""
    pts = [(x0, base)]
    shape = [(0.18, 0), (0.22, -0.12), (0.26, 0), (0.30, 0), (0.32, 0.18),
             (0.35, -1.0), (0.38, 0.38), (0.41, 0), (0.50, 0), (0.56, -0.22),
             (0.62, 0), (1.0, 0)]
    x = x0 - offset
    while x < x1:
        for fx, fy in shape:
            px = x + fx * period
            if x0 < px <= x1:
                pts.append((px, base + fy * amp))
        x += period
    if pts[-1][0] < x1:
        pts.append((x1, base))
    return "M" + " L".join(f"{n(px)} {n(py)}" for px, py in pts)


def pulse(x: float, y: float, w: float, h: float, c: dict, beats: int = 1) -> str:
    """A small heartbeat: faint trace plus a short coral sweep running along it."""
    period = w / beats
    d = ecg_path(x, x + w, y + h * 0.66, h * 0.62, period, offset=period * 0.05)
    return (
        f'<path d="{d}" fill="none" stroke="{c["faint"]}" stroke-width="1.2" stroke-linejoin="round"/>'
        f'<path d="{d}" pathLength="100" fill="none" stroke="{c["accent"]}" stroke-width="1.5" '
        f'stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="22 100">'
        f'<animate attributeName="stroke-dashoffset" values="22;-100" dur="2.4s" '
        f'repeatCount="indefinite"/></path>'
    )


def flow(x: float, y: float, w: float, h: float, c: dict, labels: list[str] | None = None,
         mono: str = "monospace") -> str:
    """A tiny agent graph (input → agent ⇄ tools → output, LangGraph style).
    A coral packet walks it, looping once through the tools before leaving."""
    k = 4
    cy = y + h * 0.62
    xs = [x + 4 + i * (w - 8) / (k - 1) for i in range(k)]
    lift = h * 0.55
    loop = f"Q{n((xs[1] + xs[2]) / 2)} {n(cy - lift)} {n(xs[1])} {n(cy)}"
    edges = (f'<path d="M{n(xs[0])} {n(cy)}H{n(xs[3])}" stroke="{c["faint"]}" stroke-width="1"/>'
             f'<path d="M{n(xs[2])} {n(cy)}{loop}" fill="none" stroke="{c["faint"]}" '
             f'stroke-width="1" stroke-dasharray="2 2"/>')
    nodes = "".join(
        f'<circle cx="{n(px)}" cy="{n(cy)}" r="3" fill="{c["strong"] if i in (1, 2) else c["muted"]}"/>'
        for i, px in enumerate(xs)
    )
    route = (f"M{n(xs[0])} {n(cy)}H{n(xs[2])}{loop}H{n(xs[3])}")
    packet = (f'<circle r="2.2" fill="{c["accent"]}"><animateMotion dur="3.4s" '
              f'repeatCount="indefinite" path="{route}"/></circle>')
    text = ""
    if labels:
        text = "".join(
            f'<text x="{n(px)}" y="{n(cy + 15)}" text-anchor="middle" font-family="{esc(mono)}" '
            f'font-size="9.5" fill="{c["muted"]}">{esc(lb)}</text>'
            for px, lb in zip(xs, labels)
        )
    return edges + nodes + packet + text


def live_dot(x: float, y: float, c: dict, r: float = 3) -> str:
    return (f'<circle cx="{n(x)}" cy="{n(y)}" r="{r}" fill="{c["accent"]}">'
            f'<animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>')


# GitHub linguist colours: a language keeps the same colour everywhere.
LANG_COLOR = {
    "Python": "#3572A5", "R": "#198CE7", "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A", "Java": "#B07219", "HTML": "#E34C26", "CSS": "#663399",
    "Jupyter Notebook": "#DA5B0B", "TeX": "#3D6117", "SPARQL": "#0C4597",
    "Shell": "#89E051", "C": "#555555", "C++": "#F34B7D", "Go": "#00ADD8",
    "Rust": "#DEA584", "Kotlin": "#A97BFF", "Dart": "#00B4AB", "Vue": "#41B883",
    "PLpgSQL": "#336790", "SQL": "#E38C00", "Svelte": "#FF3E00", "PHP": "#4F5D95",
    "Ruby": "#701516", "Scala": "#C22D40", "MATLAB": "#E16737", "Julia": "#A270BA",
    "Dockerfile": "#384D54", "Makefile": "#427819", "Perl": "#0298C3",
}
