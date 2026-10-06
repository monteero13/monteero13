"""Skill genome: each group is a 'chromosome', each skill a row of thin loci,
like a sequence track. Lit loci encode the self-assessed level; the last one
is marked in the accent colour."""

from __future__ import annotations

from .config import Loc
from .svg import delayed_fade, document, esc, n, text_width

W = 840
COL_GAP = 48
LOCI = 25                   # one locus = 4 points
LOCUS_W, LOCUS_GAP = 3, 3.4
ROW_H = 24
GROUP_HEAD = 26
GROUP_GAP = 16


def _balance(groups: list[dict]) -> tuple[list, list]:
    """Split groups into two columns of similar height, keeping their order."""
    if len(groups) < 2:
        return groups, []
    sizes = [len(g["items"]) + 1.2 for g in groups]
    cut = min(range(1, len(groups)), key=lambda k: max(sum(sizes[:k]), sum(sizes[k:])))
    return groups[:cut], groups[cut:]


def render(cfg, loc: Loc, theme: str) -> str:
    c = cfg.palette(theme)
    font, mono = cfg.theme["font"], cfg.theme["mono"]
    cols = _balance(cfg.get("skills", []))
    col_w = (W - COL_GAP) / 2
    track_w = LOCI * (LOCUS_W + LOCUS_GAP) - LOCUS_GAP
    label_w = col_w - track_w - 40

    def col_height(col):
        return sum(GROUP_HEAD + len(g["items"]) * ROW_H + GROUP_GAP for g in col) - GROUP_GAP

    H = max(col_height(col) for col in cols if col) + 4

    body = []
    chrom = row = 0
    for ci, col in enumerate(cols):
        x0 = ci * (col_w + COL_GAP)
        y = 0
        for g in col:
            chrom += 1
            body.append(
                f'<text x="{n(x0)}" y="{y + 13}" font-family="{esc(mono)}" font-size="11" '
                f'fill="{c["muted"]}">chr{chrom}<tspan dx="8" fill="{c["strong"]}">'
                f'{esc(loc(g["group"]))}</tspan></text>'
            )
            y += GROUP_HEAD
            for item in g["items"]:
                label = loc(item["label"])
                level = max(0, min(100, int(item["level"])))
                lit = round(level / (100 / LOCI))
                while label and text_width(label, 12.5) > label_w:
                    label = label[:-2] + "…"
                body.append(f'<text x="{n(x0)}" y="{y + 12}" font-size="12.5" fill="{c["text"]}">'
                            f'{esc(label)}</text>')
                tx = x0 + label_w + 6
                ticks_off, ticks_on = [], []
                for k in range(LOCI):
                    d = f"M{n(tx + k * (LOCUS_W + LOCUS_GAP) + LOCUS_W / 2)} {y + 2}v11"
                    if k < lit - 1:
                        ticks_on.append(d)
                    elif k >= lit:          # k == lit - 1 is the accent marker
                        ticks_off.append(d)
                body.append(f'<path d="{"".join(ticks_off)}" stroke="{c["faint"]}" '
                            f'stroke-width="{LOCUS_W}" opacity=".55"/>')
                body.append(f'<path d="{"".join(ticks_on)}" stroke="{c["strong"]}" '
                            f'stroke-width="{LOCUS_W}">{delayed_fade(0.2 + row * 0.07, 1.6)}</path>')
                if lit:
                    mx = tx + (lit - 1) * (LOCUS_W + LOCUS_GAP) + LOCUS_W / 2
                    body.append(f'<path d="M{n(mx)} {y}v15" stroke="{c["accent"]}" '
                                f'stroke-width="{LOCUS_W}">{delayed_fade(0.5 + row * 0.07, 1.9)}</path>')
                body.append(f'<text x="{n(x0 + col_w)}" y="{y + 12}" text-anchor="end" '
                            f'font-family="{esc(mono)}" font-size="11" fill="{c["muted"]}">{level}</text>')
                y += ROW_H
                row += 1
            y += GROUP_GAP

    title = loc(cfg["headings"]["skills"])
    return document(W, H, title, font, "".join(body))
