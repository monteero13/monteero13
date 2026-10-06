#!/usr/bin/env python3
"""Build the GitHub profile README and its SVG assets from profile.toml.

    python scripts/build.py              # live data from the GitHub API
    python scripts/build.py --offline    # no network: fast local design loop

A token in $GITHUB_TOKEN (or $GH_TOKEN) adds the contribution and streak tiles
and lifts the API rate limit. Stdlib only, Python 3.11+.

Outputs:
    README.md, README.<lang>.md          one per language in profile.toml
    assets/generated/<lang>/*.svg        dark + light version of every image
    preview.html                         local preview of every asset (git-ignored)
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from profilekit import genome, header, heading, preview, projects, readme, stack, vitals
from profilekit.config import THEMES, Config
from profilekit.github import GitHubData, fetch

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=ROOT / "profile.toml")
    ap.add_argument("--offline", action="store_true", help="skip the GitHub API")
    args = ap.parse_args(argv)

    cfg = Config(args.config)
    sections = set(cfg.profile.get("sections", []))
    vcfg = cfg.get("vitals", {})

    if args.offline:
        gh = GitHubData()
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        exclude = {s.lower() for s in vcfg.get("languages_exclude", [])}
        print(f"fetching GitHub data for @{cfg.username}...")
        gh = fetch(cfg.username, token, exclude)

    out_root = ROOT / "assets" / "generated"
    if out_root.exists():
        shutil.rmtree(out_root)  # generated only: drops cards of removed projects

    written = 0
    for lang in cfg.languages:
        loc = cfg.loc(lang)
        out = out_root / lang
        out.mkdir(parents=True)
        for theme in THEMES:
            files = {}
            for i, section in enumerate(readme.headed_sections(cfg), start=1):
                files[f"heading-{section}"] = heading.render(cfg, loc, theme, section, i)
            if "banner" in sections and not cfg.get("banner", {}).get("dark"):
                files["header"] = header.render(cfg, loc, theme)
            if "stack" in sections and cfg.get("stack", {}).get("extra"):
                files["stack"] = stack.render(cfg, loc, theme)
            if "skills" in sections:
                files["genome"] = genome.render(cfg, loc, theme)
            if "vitals" in sections:
                files["vitals"] = vitals.render(cfg, loc, theme, gh)
            if "projects" in sections:
                for p in cfg.get("projects", []):
                    repo = gh.repos.get(p["repo"].lower())
                    first_pass = lang == cfg.default_lang and theme == THEMES[0]
                    if gh.online and repo is None and first_pass:
                        print(f"  ! {p['repo']}: not public on @{cfg.username}, card drawn from profile.toml",
                              file=sys.stderr)
                    files[f"project-{p['repo']}"] = projects.render(cfg, loc, theme, p, repo, gh.online)
            for name, svg in files.items():
                (out / f"{name}-{theme}.svg").write_text(svg, encoding="utf-8", newline="\n")
                written += 1

        md = readme.render(cfg, lang, gh)
        (ROOT / cfg.readme_name(lang)).write_text(md, encoding="utf-8", newline="\n")
        print(f"wrote {cfg.readme_name(lang)}")

    (ROOT / "preview.html").write_text(preview.render(cfg), encoding="utf-8", newline="\n")
    print(f"wrote {written} SVGs in assets/generated/ and preview.html"
          f"{'' if gh.online else '  (offline: no live stats)'}")


if __name__ == "__main__":
    main()
