#!/usr/bin/env python3
"""Update README.md with auto-generated project table from GitHub repos."""

import os
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
OWNER = "francomoreira"
README_PATH = "README.md"

BLACKLIST = {
    "francomoreira.github.io-OLD",    # deprecated
    "todo-app-react",                 # viejo de práctica
    "calculate-your-weight-on-mars",  # viejo de práctica
}

PREFERRED_ORDER = [
    "francomoreira.github.io",
]


def fetch_repos():
    """Fetch public repos for the user, excluding forks."""
    url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=updated&direction=desc"
    headers = {"User-Agent": "readme-updater", "Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def should_include(repo):
    """Filter: not fork, not archived, has description or recent activity, not profile repo, not blacklisted."""
    if repo["fork"]:
        return False
    if repo["archived"]:
        return False
    if repo["name"] == OWNER:
        return False
    if repo["name"] in BLACKLIST:
        return False
    # Include if has a description
    if repo.get("description") and repo["description"].strip():
        return True
    # Or if updated in the last year
    updated = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) - updated < timedelta(days=365):
        return True
    return False


def format_table(repos):
    """Generate the markdown table."""
    lines = [
        "| Proyecto | Qué es? |",
        "| -------- | ------ |",
    ]
    for r in repos:
        desc = r.get("description") or "Sin descripción"
        desc = desc.split("\n")[0].strip()
        if len(desc) > 80:
            desc = desc[:77] + "..."
        name = r["name"]
        url = f"https://github.com/{OWNER}/{r['name']}"
        lines.append(f"| [{name}]({url}) | {desc} |")
    return "\n".join(lines)


def sort_key(repo):
    """Sort: preferred repos first (in given order), then by pushed_at descending."""
    name = repo["name"]
    if name in PREFERRED_ORDER:
        return (0, PREFERRED_ORDER.index(name))
    return (1, 0)


def update_readme():
    repos = fetch_repos()
    included = [r for r in repos if should_include(r)]
    # Preferred order first, then by pushed_at
    included.sort(key=lambda r: (r["pushed_at"],), reverse=True)
    included.sort(key=sort_key)

    table = format_table(included)

    with open(README_PATH, "r") as f:
        content = f.read()

    start_marker = "<!-- PROYECTOS:START -->"
    end_marker = "<!-- PROYECTOS:END -->"

    if start_marker not in content or end_marker not in content:
        print(f"ERROR: Markers {start_marker} / {end_marker} not found in README.md")
        sys.exit(1)

    new_content = re.sub(
        f"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
        f"{start_marker}\n\n{table}\n\n{end_marker}",
        content,
        flags=re.DOTALL,
    )

    with open(README_PATH, "w") as f:
        f.write(new_content)

    print(f"README.md updated with {len(included)} repos.")


if __name__ == "__main__":
    update_readme()
