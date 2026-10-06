"""Project cards: hairline frame, name, two lines of description and a mono
footer. No fill, so the card sits on GitHub's own background."""

from __future__ import annotations

from .config import Loc
from .svg import LANG_COLOR, document, esc, n, text_width, wrap

W, H = 410, 116
PAD = 16

ICON_STAR = "M8 .8l2.1 4.3 4.7.7-3.4 3.3.8 4.7L8 11.6l-4.2 2.2.8-4.7L1.2 5.8l4.7-.7z"
ICON_LOCK = "M4.5 7V5a3.5 3.5 0 0 1 7 0v2M3 7h10v7.5H3z"


def render(cfg, loc: Loc, theme: str, project: dict, repo: dict | None,
           online: bool = True) -> str:
    c = cfg.palette(theme)
    font, mono = cfg.theme["font"], cfg.theme["mono"]
    name = repo["name"] if repo else project["repo"]
    desc = loc(project.get("description")) or (repo or {}).get("description") or loc.s("no_description")
    language = project.get("language") or (repo or {}).get("language")

    body = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="8" fill="none" '
            f'stroke="{c["line"]}"/>']
    body.append(f'<text x="{PAD}" y="{PAD + 13}" font-size="14" font-weight="600" '
                f'fill="{c["strong"]}">{esc(name)}</text>')

    # top-right: stars, or a lock for private repos
    if repo is not None:
        stars = str(repo.get("stargazers_count", 0))
        tx = W - PAD - text_width(stars, 11, mono=True)
        body.append(f'<text x="{n(tx)}" y="{PAD + 12}" font-family="{esc(mono)}" font-size="11" '
                    f'fill="{c["muted"]}">{stars}</text>'
                    f'<path transform="translate({n(tx - 15)},{PAD + 2}) scale(.7)" d="{ICON_STAR}" '
                    f'fill="none" stroke="{c["muted"]}" stroke-width="1.6" stroke-linejoin="round"/>')
    elif online:
        label = loc.s("private")
        tx = W - PAD - text_width(label, 10.5, mono=True)
        body.append(f'<text x="{n(tx)}" y="{PAD + 12}" font-family="{esc(mono)}" font-size="10.5" '
                    f'fill="{c["muted"]}">{esc(label)}</text>'
                    f'<path transform="translate({n(tx - 14)},{PAD + 2}) scale(.68)" d="{ICON_LOCK}" '
                    f'fill="none" stroke="{c["muted"]}" stroke-width="1.6"/>')

    for i, line in enumerate(wrap(desc, 12, W - 2 * PAD, 2)):
        body.append(f'<text x="{PAD}" y="{PAD + 38 + i * 17}" font-size="12" '
                    f'fill="{c["text"]}">{esc(line)}</text>')

    # footer: language dot · tags
    fy = H - PAD
    x = PAD
    if language:
        body.append(f'<circle cx="{x + 4}" cy="{fy - 4}" r="3.5" fill="{LANG_COLOR.get(language, c["faint"])}"/>'
                    f'<text x="{x + 13}" y="{fy}" font-family="{esc(mono)}" font-size="10.5" '
                    f'fill="{c["muted"]}">{esc(language.lower())}</text>')
        x += 13 + text_width(language, 10.5, mono=True) + 14
    for tag in project.get("tags", []):
        label = f"#{loc(tag)}"
        w = text_width(label, 10.5, mono=True)
        if x + w > W - PAD:
            break
        body.append(f'<text x="{n(x)}" y="{fy}" font-family="{esc(mono)}" font-size="10.5" '
                    f'fill="{c["muted"]}" opacity=".8">{esc(label)}</text>')
        x += w + 10

    return document(W, H, f"{name}: {desc}", font, "".join(body))
