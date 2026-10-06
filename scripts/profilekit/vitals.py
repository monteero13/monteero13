"""Vital signs: a quiet row of GitHub numbers separated by hairlines, and the
language composition as one thin stacked bar."""

from __future__ import annotations

import datetime as dt

from .config import Loc
from .github import GitHubData
from .svg import LANG_COLOR, delayed_fade, document, esc, live_dot, n, pulse

W = 840


def _fmt(v) -> str:
    return "—" if v is None else f"{v:,}".replace(",", " ")


def render(cfg, loc: Loc, theme: str, gh: GitHubData) -> str:
    c = cfg.palette(theme)
    font, mono = cfg.theme["font"], cfg.theme["mono"]
    vcfg = cfg.get("vitals", {})

    stats = [(loc.s("stars"), _fmt(gh.stars)),
             (loc.s("repos"), _fmt(gh.public_repos)),
             (loc.s("followers"), _fmt(gh.followers))]
    streak_index = None
    if gh.contributions is not None:
        stats.append((loc.s("contributions"), _fmt(gh.contributions)))
        streak_index = len(stats)
        stats += [(loc.s("streak"), f'{_fmt(gh.streak)}{loc.s("days")}'),
                  (loc.s("longest"), f'{_fmt(gh.longest)}{loc.s("days")}')]

    langs = sorted(gh.languages.items(), key=lambda kv: -kv[1])
    top_n = vcfg.get("languages_top", 5)
    if len(langs) > top_n:
        langs = langs[:top_n] + [(loc.s("other"), sum(v for _, v in langs[top_n:]))]
    total = sum(v for _, v in langs) or 1

    body = []
    # status line
    stamp = (f'@{cfg.username} · {loc.s("updated")} {dt.date.today().isoformat()}'
             if gh.online else loc.s("no_data"))
    body.append(live_dot(4, 8, c))
    body.append(f'<text x="14" y="12" font-family="{esc(mono)}" font-size="11" '
                f'fill="{c["muted"]}">{esc(stamp)}</text>')

    # numbers
    y0 = 30
    cell = W / len(stats)
    for i, (label, value) in enumerate(stats):
        x = i * cell + (0 if i == 0 else 18)
        if i:
            body.append(f'<line x1="{n(i * cell)}" x2="{n(i * cell)}" y1="{y0 + 4}" y2="{y0 + 50}" '
                        f'stroke="{c["line"]}"/>')
        body.append(
            f'<g>{delayed_fade(0.1 + i * 0.1, 1.2)}'
            f'<text x="{n(x)}" y="{y0 + 28}" font-size="24" font-weight="600" fill="{c["strong"]}" '
            f'letter-spacing="-.5">{esc(value)}</text>'
            f'<text x="{n(x)}" y="{y0 + 48}" font-family="{esc(mono)}" font-size="10.5" '
            f'fill="{c["muted"]}">{esc(label.lower())}</text></g>'
        )
        if i == streak_index:  # the one place the heartbeat shows up in here
            body.append(pulse(x + 64, y0 + 12, 44, 16, c))

    H = y0 + 62
    if langs:
        by = H + 6
        gap = 2
        usable = W - gap * (len(langs) - 1)
        body.append(f'<clipPath id="bar"><rect x="0" y="{by}" width="{W}" height="4" rx="2"/></clipPath>'
                    f'<g clip-path="url(#bar)">')
        x = 0.0
        for name, size in langs:
            w = max(usable * size / total, 2)
            body.append(f'<rect x="{n(x)}" y="{by}" width="{n(w)}" height="4" '
                        f'fill="{LANG_COLOR.get(name, c["faint"])}"/>')
            x += w + gap
        body.append("</g>")
        lx, ly = 0.0, by + 24
        for name, size in langs:
            pct = f"{100 * size / total:.1f}%"
            body.append(
                f'<circle cx="{n(lx + 4)}" cy="{ly - 4}" r="3.5" fill="{LANG_COLOR.get(name, c["faint"])}"/>'
                f'<text x="{n(lx + 13)}" y="{ly}" font-family="{esc(mono)}" font-size="11" '
                f'fill="{c["text"]}">{esc(name.lower())}<tspan dx="6" fill="{c["muted"]}">{pct}</tspan></text>'
            )
            lx += 13 + (len(name) + len(pct) + 1) * 11 * 0.61 + 22
        H = ly + 8

    return document(W, H, f'{loc(cfg["headings"]["vitals"])} — @{cfg.username}', font, "".join(body))
