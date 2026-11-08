#!/usr/bin/env python3
"""Собирает SVG-карточку с распределением языков по объёму кода.

Берёт публичные репозитории пользователя через GitHub REST API и суммирует
байты по языкам. Никаких внешних сервисов и токенов не требуется
(токен используется, если передан, — на случай лимитов на общие IP).
"""
import json
import os
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import date

USER = os.environ.get("GH_USER", "Alex-399745146")
OUT = os.environ.get("OUT_FILE", "languages.svg")
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()

COLORS = {
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Jupyter Notebook": "#DA5B0B",
    "Go": "#00ADD8",
    "C++": "#f34b7d",
    "C": "#555555",
    "Java": "#b07219",
    "PHP": "#4F5D95",
    "Vue": "#41b883",
    "Rust": "#dea584",
    "Kotlin": "#A97BFF",
    "Ruby": "#701516",
    "C#": "#178600",
    "Makefile": "#427819",
    "Batchfile": "#C1F12E",
}
FALLBACK = ["#6a737d", "#8b949e", "#c9d1d9", "#57606a", "#adbac7", "#444c56"]


def api(path, token=None):
    url = "https://api.github.com" + path
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-languages-card")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403) and token:
            return api(path, None)
        if e.code == 404:
            return None
        raise


def collect():
    repos = api(f"/users/{USER}/repos?per_page=100&sort=updated", TOKEN) or []
    totals = defaultdict(int)
    for repo in repos:
        if repo.get("fork") or repo.get("archived"):
            continue
        langs = api(f"/repos/{repo['full_name']}/languages", TOKEN) or {}
        for name, size in langs.items():
            totals[name] += int(size or 0)
    return totals


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render(totals, limit=7):
    total = sum(totals.values()) or 1
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    rest = total - sum(v for _, v in items)
    if rest > 0:
        items.append(("Другое", rest))

    row_h = 24
    height = 54 + row_h * len(items) + 26
    bar_w = 440
    x0 = 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="{height}" '
        f'viewBox="0 0 480 {height}" font-family="-apple-system,BlinkMacSystemFont,'
        f'Segoe UI,Helvetica,Arial,sans-serif">',
        '<style>.t{font-size:14px;fill:#57606a}.n{font-size:13px;fill:#24292f}'
        '.p{font-size:12px;fill:#57606a}</style>',
        f'<text x="{x0}" y="26" font-size="14" font-weight="600" fill="#24292f">'
        f'Языки по объёму кода</text>',
    ]

    # стек-бар
    x = x0
    for i, (name, size) in enumerate(items):
        w = bar_w * size / total
        color = COLORS.get(name, FALLBACK[i % len(FALLBACK)])
        parts.append(
            f'<rect x="{x:.2f}" y="40" width="{max(w, 1):.2f}" height="10" rx="3" fill="{color}"/>'
        )
        x += w

    # легенда
    y = 76
    for i, (name, size) in enumerate(items):
        color = COLORS.get(name, FALLBACK[i % len(FALLBACK)])
        pct = 100 * size / total
        parts.append(f'<rect x="{x0}" y="{y - 9}" width="10" height="10" rx="2" fill="{color}"/>')
        parts.append(f'<text class="n" x="{x0 + 18}" y="{y}">{esc(name)}</text>')
        parts.append(
            f'<text class="p" x="460" y="{y}" text-anchor="end">{pct:.1f}%</text>'
        )
        y += row_h

    parts.append(
        f'<text class="t" x="{x0}" y="{height - 8}" font-size="11">'
        f'обновлено {date.today().isoformat()}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    totals = collect()
    if not totals:
        print("нет данных о языках", file=sys.stderr)
        return 1
    svg = render(totals)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    top = ", ".join(f"{k} {v}" for k, v in sorted(totals.items(), key=lambda kv: -kv[1])[:5])
    print("готово:", OUT)
    print("топ:", top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
