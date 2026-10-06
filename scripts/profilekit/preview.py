"""preview.html: every generated asset on GitHub's dark and light canvases,
plus a theme toggle, so the design loop needs no push."""

from __future__ import annotations

PAGE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Profile preview</title>
<style>
  :root {{ --bg:#0d1117; --fg:#e6edf3; --muted:#8b949e; --line:#30363d; }}
  :root[data-theme="light"] {{ --bg:#ffffff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0; }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
         font:15px/1.5 -apple-system,'Segoe UI',Helvetica,Arial,sans-serif; }}
  main {{ max-width:880px; margin:0 auto; padding:32px 16px 80px; }}
  header {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin-bottom:24px; }}
  h1 {{ font-size:18px; margin:0 auto 0 0; }}
  button {{ background:transparent; color:var(--fg); border:1px solid var(--line); border-radius:6px;
            padding:5px 12px; font:inherit; font-size:13px; cursor:pointer; }}
  button[aria-pressed="true"] {{ border-color:var(--fg); }}
  img {{ display:block; max-width:100%; height:auto; margin:0 auto 12px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:8px; }}
  .grid img {{ margin:0; }}
  .note {{ color:var(--muted); font-size:13px; font-style:italic; }}
  main > img {{ margin-bottom:28px; }}
</style>
<main>
<header>
  <h1>Profile preview</h1>
  {lang_buttons}
  <button id="theme">toggle theme</button>
  <button id="replay">replay animations</button>
</header>
{sections}
</main>
<script>
  const root = document.documentElement;
  let theme = 'dark', lang = '{default_lang}';
  try {{ theme = localStorage.getItem('pv-theme') || theme; lang = localStorage.getItem('pv-lang') || lang; }} catch (e) {{}}
  function paint() {{
    root.dataset.theme = theme;
    document.querySelectorAll('img[data-name]').forEach(img => {{
      img.src = `assets/generated/${{lang}}/${{img.dataset.name}}-${{theme}}.svg?` + Date.now();
    }});
    document.querySelectorAll('img[data-static-dark]').forEach(img => {{
      img.src = theme === 'dark' ? img.dataset.staticDark : img.dataset.staticLight;
    }});
    document.querySelectorAll('[data-lang]').forEach(b => b.setAttribute('aria-pressed', b.dataset.lang === lang));
    try {{ localStorage.setItem('pv-theme', theme); localStorage.setItem('pv-lang', lang); }} catch (e) {{}}
  }}
  document.getElementById('theme').onclick = () => {{ theme = theme === 'dark' ? 'light' : 'dark'; paint(); }};
  document.getElementById('replay').onclick = paint;
  document.querySelectorAll('[data-lang]').forEach(b => b.onclick = () => {{ lang = b.dataset.lang; paint(); }});
  paint();
</script>
</html>
"""


def render(cfg) -> str:
    """Mirror the README order so spacing and rhythm can be judged too."""
    from .readme import HEADED

    banner = cfg.get("banner", {})
    blocks = []
    for section in cfg.profile.get("sections", []):
        if section in HEADED:
            blocks.append(f'<img data-name="heading-{section}" alt="{section} heading">')
        if section == "banner" and banner.get("dark"):
            light = banner.get("light", banner["dark"])
            blocks.append(f'<img data-static-dark="{banner["dark"]}" data-static-light="{light}" alt="banner">')
        elif section == "banner":
            blocks.append('<img data-name="header" alt="header">')
        elif section == "about":
            blocks.append('<p class="note">about: markdown text, see README</p>')
        elif section == "stack":
            icons = cfg.get("stack", {}).get("icons", [])
            if icons:
                base = f'https://skillicons.dev/icons?i={",".join(icons)}&perline={cfg["stack"].get("per_line", 15)}'
                blocks.append(f'<img data-static-dark="{base}&theme=dark" data-static-light="{base}&theme=light" alt="icons">')
            if cfg.get("stack", {}).get("extra"):
                blocks.append('<img data-name="stack" alt="stack">')
        elif section == "skills":
            blocks.append('<img data-name="genome" alt="genome">')
        elif section == "projects":
            cards = "".join(f'<img data-name="project-{p["repo"]}" alt="{p["repo"]}">'
                            for p in cfg.get("projects", []))
            blocks.append(f'<div class="grid">{cards}</div>')
        elif section == "vitals":
            blocks.append('<img data-name="vitals" alt="vitals">')
    buttons = "".join(f'<button data-lang="{lang}">{lang}</button>' for lang in cfg.languages)
    return PAGE.format(lang_buttons=buttons, sections="\n".join(blocks), default_lang=cfg.default_lang)
