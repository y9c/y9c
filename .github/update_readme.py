#!/usr/bin/env python3
"""Regenerate the y9c profile README from `.github/repos.json` + live GitHub metadata.

The README is data-driven so it stays current automatically:
  * Star badges are live shields.io links (no baking in).
  * Age badges are computed from each repo's *creation date*:
      - repo created this year  -> `new-<year>`   (green  `2ea44f`)
      - repo created any earlier -> `since-<year>` (teal   `17a2b8`)
  * To add / remove / reword a featured repo, edit `repos.json`; the monthly
    workflow regenerates the README and commits any diff.

Only README.md is ever modified by this script.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
DATA_FILE = HERE / "repos.json"
README_FILE = REPO_ROOT / "README.md"

USER = "y9c"
COL_STARS = "yellow"      # star counter badge
COL_NEW = "2ea44f"        # created this year
COL_SINCE = "17a2b8"      # created in an earlier year
CURRENT_YEAR = datetime.now(timezone.utc).year
# Only tag a repo with a "since-<year>" badge once it is at least this old.
# Newer repos (e.g. created last year or the year before) get no age badge.
SINCE_MIN_AGE = 3

# Order of groups within the right-hand column.
GROUP_ORDER = ["rna", "tools", "utils"]


def _gh_headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _gh_get(path):
    """GET a GitHub API path, following pagination, and return the JSON."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers=_gh_headers())
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_repo(repo):
    """Return (stars, created_year) for a single repo via the GitHub API."""
    data = _gh_get(f"/repos/{USER}/{repo}")
    return data["stargazers_count"], int(data["created_at"][:4])


def age_badge(repo, created_year, since=None):
    """Build the age badge for a repo based on its creation year.

    * if `since` is given (per-repo override in repos.json) -> `since-<year>`
      regardless of age, so a young repo can still advertise its lineage.
    * created this year          -> `new-<year>`  (green)
    * created >= SINCE_MIN_AGE yrs ago -> `since-<year>`  (teal)
    * anything in between        -> no age badge
    """
    url = f"https://github.com/{USER}/{repo}"
    if since is not None:
        return (
            f'<a href="{url}"><img src="https://img.shields.io/badge/'
            f'since-{since}-{COL_SINCE}?style=flat-square" '
            f'alt="since {since}" /></a>'
        )
    if created_year >= CURRENT_YEAR:
        return (
            f'<a href="{url}"><img src="https://img.shields.io/badge/'
            f'new-{created_year}-{COL_NEW}?style=flat-square" alt="new" /></a>'
        )
    if CURRENT_YEAR - created_year >= SINCE_MIN_AGE:
        return (
            f'<a href="{url}"><img src="https://img.shields.io/badge/'
            f'since-{created_year}-{COL_SINCE}?style=flat-square" '
            f'alt="since {created_year}" /></a>'
        )
    return ""


def star_badge(repo):
    url = f"https://github.com/{USER}/{repo}"
    return (
        f'<a href="{url}"><img src="https://img.shields.io/github/stars/'
        f'{USER}/{repo}?style=flat-square&color={COL_STARS}" alt="stars" /></a>'
    )


def render_item(item, created_year):
    repo = item["repo"]
    badges = []
    if item.get("show_stars", True):
        badges.append(star_badge(repo))
    age = age_badge(repo, created_year, since=item.get("since"))
    if age:
        badges.append(age)
    badge_html = (" " + " ".join(badges)) if badges else ""
    return (
        f'<p><a href="https://github.com/{USER}/{repo}"><b>{item["name"]}</b></a>'
        f'{badge_html}<br /><small>{item["desc"]}</small></p>\n'
    )


def build_readme(items):
    by_group = {group: [] for group in GROUP_ORDER}
    for item in items:
        by_group[item["group"]].append(item)

    collections = []

    collections.append(
        '<div align="center">\n\n'
        "### 👋 Hi, I'm Chang Ye\n\n"
        "**Bioinformatics × RNA epigenetics** — open-source pipelines for\n"
        "single-base-resolution RNA modification detection (`m⁵C` · `m⁶A` · `Ψ`) and NGS tooling.\n\n"
        "[![GitHub followers](https://img.shields.io/github/followers/y9c?style=social)](https://github.com/y9c?tab=followers)\n"
        "[![GitHub stars](https://img.shields.io/github/stars/y9c?style=social)](https://github.com/y9c?tab=repositories)\n"
        "\n"
        "<br />\n\n"
        '<i>🏛️ Organizations</i>\n\n'
        '<table align="center">\n'
        "<tr>\n"
        '<td align="center" width="50%">\n'
        '<a href="https://github.com/yclab"><img src="https://github.com/yclab.png?size=64" width="64" height="64" alt="yclab" /></a><br />\n'
        '<a href="https://github.com/yclab"><b>yclab</b></a> <a href="https://github.com/yclab?tab=followers"><img src="https://img.shields.io/github/followers/yclab?style=flat-square" alt="yclab followers" /></a>\n'
        "</td>\n"
        '<td align="center" width="50%">\n'
        '<a href="https://github.com/srils"><img src="https://github.com/srils.png?size=64" width="64" height="64" alt="srils" /></a><br />\n'
        '<a href="https://github.com/srils"><b>srils</b></a> <a href="https://github.com/srils?tab=followers"><img src="https://img.shields.io/github/followers/srils?style=flat-square" alt="srils followers" /></a>\n'
        "</td>\n"
        "</tr>\n"
        "</table>\n\n"
        "</div>\n"
    )

    def render_group(group):
        lines = []
        for item in by_group[group]:
            _, created_year = fetch_repo(item["repo"])
            lines.append(render_item(item, created_year))
        return "\n".join(lines)

    rna = render_group("rna")
    tools = render_group("tools")
    utils = render_group("utils")

    collections.append(
        "<table>\n"
        "<tr>\n"
        '<td width="50%" valign="top">\n\n'
        '<h2 align="center">🧬 RNA modification pipelines</h2>\n'
        '<p align="center"><small>Single-base-resolution detection of RNA epitranscriptomic modifications — from method to pipeline.</small></p>\n\n'
        f"{rna}"
        "\n</td>\n"
        '<td width="50%" valign="top">\n\n'
        '<h2 align="center">🛠️ Analysis &amp; NGS tools</h2>\n'
        '<p align="center"><small>Bioinformatics tooling: alignment, QC, visualization &amp; reporting.</small></p>\n\n'
        f"{tools}"
        '\n<p><small><b>Utilities &amp; experiments</b></small></p>\n\n'
        f"{utils}"
        "\n</td>\n"
        "</tr>\n"
        "</table>\n"
    )

    return "\n".join(collections)


def main():
    items = json.loads(DATA_FILE.read_text())
    content = build_readme(items)
    if README_FILE.read_text() != content:
        README_FILE.write_text(content)
        print("README.md updated.")
    else:
        print("README.md up to date, no changes.")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.HTTPError as exc:
        print(f"GitHub API error: {exc.code} {exc.reason}", file=sys.stderr)
        sys.exit(1)
