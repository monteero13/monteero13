"""Live data from the GitHub API. Stdlib only; every call degrades gracefully."""

from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field

API = "https://api.github.com"
UA = {"User-Agent": "profilekit", "Accept": "application/vnd.github+json"}

CONTRIB_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


@dataclass
class GitHubData:
    online: bool = False
    followers: int | None = None
    public_repos: int | None = None
    stars: int | None = None
    repos: dict = field(default_factory=dict)        # lower-case name -> repo json
    languages: dict = field(default_factory=dict)    # language -> bytes
    contributions: int | None = None
    streak: int | None = None
    longest: int | None = None


def _request(url: str, token: str | None, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=dict(UA))
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def streaks(days: list[tuple[dt.date, int]]) -> tuple[int, int]:
    """(current, longest). An empty today does not break yesterday's streak."""
    days = sorted(days)
    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    current = 0
    for i, (_, count) in enumerate(reversed(days)):
        if count:
            current += 1
        elif i > 0:
            break
    return current, longest


def fetch(user: str, token: str | None, exclude_langs: set[str]) -> GitHubData:
    out = GitHubData()
    try:
        profile = _request(f"{API}/users/{user}", token)
        repos, page = [], 1
        while True:
            batch = _request(f"{API}/users/{user}/repos?per_page=100&page={page}&type=owner", token)
            repos += batch
            if len(batch) < 100:
                break
            page += 1
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  ! GitHub API unavailable ({e}); building without live data", file=sys.stderr)
        return out

    out.online = True
    out.followers = profile.get("followers", 0)
    out.public_repos = profile.get("public_repos", 0)
    out.repos = {r["name"].lower(): r for r in repos}
    own = [r for r in repos if not r.get("fork")]
    out.stars = sum(r.get("stargazers_count", 0) for r in own)

    for repo in own:
        if repo.get("archived"):
            continue
        try:
            langs = _request(repo["languages_url"], token)
        except (urllib.error.URLError, TimeoutError):
            continue
        for name, size in langs.items():
            if name.lower() not in exclude_langs:
                out.languages[name] = out.languages.get(name, 0) + size

    if token:
        try:
            res = _request(f"{API}/graphql", token, {"query": CONTRIB_QUERY, "variables": {"login": user}})
            cal = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"])
                    for w in cal["weeks"] for d in w["contributionDays"]]
            out.contributions = cal["totalContributions"]
            out.streak, out.longest = streaks(days)
        except (urllib.error.URLError, TimeoutError, KeyError, TypeError) as e:
            print(f"  ! contribution calendar unavailable ({e})", file=sys.stderr)
    else:
        print("  note: no token, contribution tiles skipped", file=sys.stderr)
    return out
