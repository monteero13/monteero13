"""Loading profile.toml and resolving translatable values."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

# Interface strings used inside the SVGs. Any of them can be overridden from
# profile.toml with a [strings.<lang>] table.
STRINGS = {
    "en": {
        "updated": "updated",
        "stars": "Stars",
        "repos": "Public repos",
        "followers": "Followers",
        "contributions": "Contributions · 1y",
        "streak": "Current streak",
        "longest": "Longest streak",
        "days": "d",
        "no_data": "offline build — no live data",
        "private": "private",
        "no_description": "No description yet.",
        "other": "other",
    },
    "es": {
        "updated": "actualizado",
        "stars": "Estrellas",
        "repos": "Repos públicos",
        "followers": "Seguidores",
        "contributions": "Contribuciones · 1a",
        "streak": "Racha actual",
        "longest": "Racha máxima",
        "days": "d",
        "no_data": "build sin conexión — sin datos en vivo",
        "private": "privado",
        "no_description": "Sin descripción todavía.",
        "other": "otros",
    },
}

THEMES = ("dark", "light")


@dataclass
class Loc:
    """Picks the right translation of a value for one language."""

    lang: str
    default: str
    strings: dict

    def __call__(self, value, **fmt) -> str:
        if isinstance(value, dict):
            value = value.get(self.lang) or value.get(self.default) or next(iter(value.values()), "")
        text = "" if value is None else str(value)
        return text.format(**fmt) if fmt else text

    def s(self, key: str) -> str:
        return self.strings.get(key) or STRINGS["en"].get(key, key)


class Config:
    def __init__(self, path: Path):
        self.path = path
        self.data = tomllib.loads(path.read_text(encoding="utf-8"))
        self.profile = self.data["profile"]
        self.languages: list[str] = self.profile.get("languages") or ["en"]
        self.default_lang = self.languages[0]
        self.theme = self.data.get("theme", {})
        for name in THEMES:
            if name not in self.theme:
                raise SystemExit(f"profile.toml: missing [theme.{name}]")

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    @property
    def username(self) -> str:
        return self.profile["username"]

    def loc(self, lang: str) -> Loc:
        strings = dict(STRINGS.get(lang, STRINGS["en"]))
        strings.update(self.data.get("strings", {}).get(lang, {}))
        return Loc(lang, self.default_lang, strings)

    def palette(self, theme: str) -> dict:
        return self.theme[theme]

    def readme_name(self, lang: str) -> str:
        return "README.md" if lang == self.default_lang else f"README.{lang}.md"
