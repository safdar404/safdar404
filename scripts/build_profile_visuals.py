#!/usr/bin/env python3
"""Build the live SVG visuals used in the profile README.

Runs in GitHub Actions (see .github/workflows/profile-visuals.yml) and writes:

  assets/generated/portfolio-infographic.svg  - portfolio at a glance
  assets/generated/agent-capabilities.svg     - agent app x capability matrix
  assets/generated/live-status.svg            - uptime check of every live deployment
  assets/generated/github-stats.svg           - contributions, streaks, repos, languages

Only the Python standard library is used. Edit scripts/live_projects.json to add,
rename or remove projects; the visuals update on the next run.

Usage:
  python scripts/build_profile_visuals.py                 # full run (network)
  python scripts/build_profile_visuals.py --seed s.json   # offline, stats from a seed file
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import http.cookiejar
import datetime as dt
import html
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "scripts" / "live_projects.json"
OUT = ROOT / "assets" / "generated"

# ---- theme (dark card; renders the same on GitHub light and dark) -------------
BG = "#0b1220"
CARD = "#111a2c"
STROKE = "#22304a"
TEXT = "#f1f5f9"
TEXT2 = "#a7b4c8"
MUTED = "#6b7a93"
GRID = "#1c2840"
STATUS = {  # reserved status colours, always shipped with a label
    "online": ("#22c55e", "Online"),
    "sleeping": ("#f59e0b", "Asleep"),
    "down": ("#ef4444", "Down"),
    "unchecked": ("#64748b", "Pending"),
}
HEAT = ["#161f30", "#0e4429", "#006d32", "#26a641", "#39d353"]  # one hue, light->bright
FONT = "font-family=\"'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif\""
UA = "safdar404-profile-visuals/1.0 (+https://github.com/safdar404/safdar404)"


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def svg_open(w: int, h: int, title: str, desc: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t d" {FONT}>'
        f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc)}</desc>'
        "<style>.pulse{animation:p 2.4s ease-in-out infinite}@keyframes p{0%,100%{opacity:1}50%{opacity:.35}}"
        "@media (prefers-reduced-motion:reduce){.pulse{animation:none}}</style>"
        f'<rect width="{w}" height="{h}" rx="20" fill="{BG}"/>'
    )


def eyebrow(x, y, text, color=TEXT2):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="13" font-weight="700" letter-spacing="2">{esc(text.upper())}</text>'


def host_of(url: str) -> str:
    h = urllib.parse.urlparse(url).netloc
    if h.endswith("streamlit.app"):
        return "Streamlit Cloud"
    if h.endswith("github.io"):
        return "GitHub Pages"
    if h.endswith("chatgpt.site"):
        return "ChatGPT Sites"
    if h.endswith("ai.studio"):
        return "Google AI Studio"
    if h.endswith("lovable.app"):
        return "Lovable"
    return h


# ---- data -------------------------------------------------------------------
def http_get(url: str, token: str | None = None, timeout: int = 25, data: bytes | None = None):
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json, text/html;q=0.9, */*;q=0.8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, data=data)
    # Cookie jar lets Streamlit Cloud's auth redirect handshake complete instead of looping.
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    with opener.open(req, timeout=timeout) as r:
        return r.status, r.read(400_000)


def check_url(url: str) -> dict:
    """GET the page; classify online / sleeping / down with latency in ms."""
    best = {"state": "down", "ms": None, "code": None}
    for attempt in range(2):
        t0 = time.monotonic()
        try:
            code, body = http_get(url, timeout=30)
            ms = int((time.monotonic() - t0) * 1000)
            text = body.decode("utf-8", "ignore").lower()
            asleep = ("gone to sleep" in text or "zzzz" in text) and "streamlit" in text
            return {"state": "sleeping" if asleep else "online", "ms": ms, "code": code}
        except urllib.error.HTTPError as e:
            ms = int((time.monotonic() - t0) * 1000)
            # 3xx loop / 401 / 403 = deployed, with an auth handshake or bot protection in front
            if 300 <= e.code < 400 or e.code in (401, 403, 429):
                return {"state": "online", "ms": ms, "code": e.code}
            best = {"state": "down", "ms": ms, "code": e.code}
        except Exception:  # timeout, DNS, TLS
            best = {"state": "down", "ms": None, "code": None}
        time.sleep(3)
    return best


def check_all(projects: list[dict]) -> dict[str, dict]:
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        res = dict(zip([p["url"] for p in projects], ex.map(check_url, [p["url"] for p in projects])))
    return res


def github_stats(owner: str, token: str | None) -> dict:
    api = "https://api.github.com"
    _, body = http_get(f"{api}/users/{owner}", token)
    user = json.loads(body)
    _, body = http_get(f"{api}/users/{owner}/repos?per_page=100&type=owner", token)
    repos = [r for r in json.loads(body) if not r.get("fork")]
    langs = Counter((r.get("language") or "Other") for r in repos)
    days: list[int] = []
    start = None
    if token:
        q = {"query": "query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}",
             "variables": {"l": owner}}
        _, body = http_get(f"{api}/graphql", token, data=json.dumps(q).encode())
        weeks = json.loads(body)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        flat = [d for w in weeks for d in w["contributionDays"]]
        start = flat[0]["date"]
        days = [d["contributionCount"] for d in flat]
    return {
        "public_repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "stars": sum(r.get("stargazers_count", 0) for r in repos),
        "recent_repos": sum(1 for r in repos if dt.datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00"))
                            > dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)),
        "languages": dict(langs.most_common()),
        "days": days,
        "start": start,
    }


def streaks(days: list[int]) -> tuple[int, int]:
    longest = run = 0
    for c in days:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    cur = 0
    seq = days[:]
    if seq and seq[-1] == 0:  # today not counted yet -> streak still alive from yesterday
        seq = seq[:-1]
    for c in reversed(seq):
        if c == 0:
            break
        cur += 1
    return cur, longest


# ---- visuals ----------------------------------------------------------------
def kpi(x, y, w, value, label, sub, color):
    return (
        f'<g transform="translate({x} {y})"><rect width="{w}" height="104" rx="14" fill="{CARD}" stroke="{STROKE}"/>'
        f'<rect x="0" y="16" width="4" height="72" rx="2" fill="{color}"/>'
        f'<text x="20" y="46" fill="{TEXT}" font-size="32" font-weight="800">{esc(value)}</text>'
        f'<text x="20" y="70" fill="{TEXT}" font-size="14" font-weight="700">{esc(label)}</text>'
        f'<text x="20" y="90" fill="{TEXT2}" font-size="12">{esc(sub)}</text></g>'
    )


def hbars(x, y, w, rows, max_v=None, bar_h=18, gap=12, label_w=190):
    """rows: [(label, value, color)] -> horizontal bars, direct-labelled, 4px rounded ends."""
    max_v = max_v or max(v for _, v, _ in rows) or 1
    out = []
    for i, (lab, v, col) in enumerate(rows):
        yy = y + i * (bar_h + gap)
        bw = max(6, (w - label_w - 44) * v / max_v)
        out.append(f'<text x="{x}" y="{yy + bar_h - 4}" fill="{TEXT2}" font-size="13">{esc(lab)}</text>')
        out.append(f'<rect x="{x + label_w}" y="{yy}" width="{w - label_w - 44}" height="{bar_h}" rx="4" fill="{GRID}"/>')
        out.append(f'<rect x="{x + label_w}" y="{yy}" width="{bw:.1f}" height="{bar_h}" rx="4" fill="{col}"><title>{esc(lab)}: {v}</title></rect>')
        out.append(f'<text x="{x + label_w + bw + 8:.1f}" y="{yy + bar_h - 4}" fill="{TEXT}" font-size="13" font-weight="700">{v}</text>')
    return "".join(out)


def build_infographic(cat: dict, stats: dict, status: dict | None) -> str:
    projects, domains = cat["projects"], cat["domains"]
    W, H = 1280, 640
    dom_count = Counter(p["domain"] for p in projects)
    agents = [p for p in projects if p["domain"] == "agentic"]
    hosts = Counter(host_of(p["url"]) for p in projects).most_common()
    online = sum(1 for p in projects if status and status.get(p["url"], {}).get("state") in ("online", "sleeping"))
    s = [svg_open(W, H, "Live portfolio at a glance",
                  f"{len(projects)} live deployments across {len(domains)} domains; hosting split and agent capability coverage.")]
    s.append(eyebrow(40, 44, "Live portfolio at a glance"))
    s.append(f'<text x="40" y="76" fill="{TEXT}" font-size="26" font-weight="800">{len(projects)} deployed apps you can open right now</text>')
    if status:
        s.append(f'<circle class="pulse" cx="1066" cy="68" r="6" fill="{STATUS["online"][0]}"/>'
                 f'<text x="1080" y="73" fill="{TEXT2}" font-size="14"><tspan fill="{TEXT}" font-weight="700">{online}/{len(projects)}</tspan> responding</text>')
    tiles = [
        (str(len(projects)), "Live deployments", "Streamlit · Pages · Web apps", domains[0]["color"]),
        (str(len(agents)), "Agentic AI apps", "Voice · RAG · Tool calling", domains[1]["color"]),
        ("8", "Applied ML studies", "Classification → forecasting", domains[3]["color"]),
        (str(dom_count.get("geoai", 0)), "GeoAI & GIS apps", "Flood · Crops · Site intel", domains[2]["color"]),
        (f'{sum(stats.get("days") or [0]):,}', "Contributions", "In the last 12 months", domains[4]["color"]),
    ]
    tw = (W - 80 - 4 * 16) / 5
    for i, t in enumerate(tiles):
        s.append(kpi(40 + i * (tw + 16), 100, tw, *t))

    # left: deployments by domain
    s.append(f'<rect x="40" y="228" width="590" height="380" rx="16" fill="{CARD}" stroke="{STROKE}"/>')
    s.append(eyebrow(64, 262, "Live deployments by domain"))
    rows = [(d["label"], dom_count.get(d["id"], 0), d["color"]) for d in domains]
    s.append(hbars(64, 284, 548, rows, bar_h=20, gap=20))

    # right top: hosting split as one segmented bar with 2px gaps + legend
    x0, y0 = 650, 228
    s.append(f'<rect x="{x0}" y="{y0}" width="590" height="160" rx="16" fill="{CARD}" stroke="{STROKE}"/>')
    s.append(eyebrow(x0 + 24, y0 + 34, "Where they run"))
    host_cols = ["#3987e5", "#199e70", "#c98500", "#d55181", "#9085e9", "#e66767"]
    bx, bw_total, total = x0 + 24, 542, sum(c for _, c in hosts)
    cx = bx
    for i, (h, c) in enumerate(hosts):
        seg = bw_total * c / total - 2
        s.append(f'<rect x="{cx:.1f}" y="{y0 + 52}" width="{seg:.1f}" height="22" rx="4" fill="{host_cols[i % 6]}"><title>{esc(h)}: {c}</title></rect>')
        cx += seg + 2
    for i, (h, c) in enumerate(hosts):
        lx = bx + (i % 3) * 182
        ly = y0 + 104 + (i // 3) * 26
        s.append(f'<rect x="{lx}" y="{ly - 10}" width="12" height="12" rx="3" fill="{host_cols[i % 6]}"/>'
                 f'<text x="{lx + 18}" y="{ly}" fill="{TEXT2}" font-size="13">{esc(h)} <tspan fill="{TEXT}" font-weight="700">{c}</tspan></text>')

    # right bottom: agent capability coverage
    y1 = 404
    s.append(f'<rect x="{x0}" y="{y1}" width="590" height="204" rx="16" fill="{CARD}" stroke="{STROKE}"/>')
    s.append(eyebrow(x0 + 24, y1 + 34, f"Capabilities across {len(agents)} agent apps"))
    caps = Counter(c for p in agents for c in p.get("caps", []))
    capsorted = sorted(cat["capabilities"], key=lambda c: -caps.get(c, 0))
    col_w = 542 / 2
    for i, c in enumerate(capsorted):
        cx_ = x0 + 24 + (i % 2) * col_w
        cy_ = y1 + 56 + (i // 2) * 36
        v = caps.get(c, 0)
        frac = v / len(agents)
        s.append(f'<text x="{cx_}" y="{cy_ + 4}" fill="{TEXT2}" font-size="13">{esc(c)}</text>')
        s.append(f'<rect x="{cx_}" y="{cy_ + 12}" width="{col_w - 60}" height="8" rx="4" fill="{GRID}"/>')
        s.append(f'<rect x="{cx_}" y="{cy_ + 12}" width="{max(6, (col_w - 60) * frac):.1f}" height="8" rx="4" fill="{domains[0]["color"]}"><title>{esc(c)}: {v} of {len(agents)}</title></rect>')
        s.append(f'<text x="{cx_ + col_w - 52}" y="{cy_ + 21}" fill="{TEXT}" font-size="13" font-weight="700">{v}/{len(agents)}</text>')
    s.append("</svg>")
    return "".join(s)


def build_matrix(cat: dict) -> str:
    agents = [p for p in cat["projects"] if p["domain"] == "agentic"]
    caps = cat["capabilities"]
    name_w, col_w, row_h, top = 230, 118, 34, 132
    W = 40 + name_w + col_w * len(caps) + 70
    H = top + row_h * len(agents) + 64
    s = [svg_open(W, H, "Agent capability matrix", "Which capabilities each generative AI application implements.")]
    s.append(eyebrow(40, 44, "Agent capability matrix"))
    s.append(f'<text x="40" y="74" fill="{TEXT}" font-size="22" font-weight="800">What each live AI app can actually do</text>')
    for j, c in enumerate(caps):
        cx = 40 + name_w + col_w * j + col_w / 2
        s.append(f'<text x="{cx}" y="{top - 22}" fill="{TEXT2}" font-size="12.5" font-weight="700" text-anchor="middle">{esc(c)}</text>')
    s.append(f'<text x="{W - 70 + 24}" y="{top - 22}" fill="{TEXT2}" font-size="12.5" font-weight="700" text-anchor="middle">Total</text>')
    for i, p in enumerate(agents):
        y = top + row_h * i
        if i % 2 == 0:
            s.append(f'<rect x="28" y="{y - 4}" width="{W - 56}" height="{row_h}" rx="8" fill="{CARD}"/>')
        s.append(f'<text x="44" y="{y + 18}" fill="{TEXT}" font-size="14" font-weight="700">{esc(p["name"])}</text>')
        for j, c in enumerate(caps):
            cx = 40 + name_w + col_w * j + col_w / 2
            if c in p.get("caps", []):
                s.append(f'<circle cx="{cx}" cy="{y + 13}" r="8" fill="#3987e5"><title>{esc(p["name"])}: {esc(c)}</title></circle>'
                         f'<path d="M{cx - 4} {y + 13} l3 3 l5 -6" stroke="#0b1220" stroke-width="2" fill="none" stroke-linecap="round"/>')
            else:
                s.append(f'<circle cx="{cx}" cy="{y + 13}" r="3" fill="{MUTED}" opacity=".5"/>')
        s.append(f'<text x="{W - 70 + 24}" y="{y + 18}" fill="{TEXT}" font-size="14" font-weight="800" text-anchor="middle">{len(p.get("caps", []))}</text>')
    s.append(f'<text x="40" y="{H - 24}" fill="{MUTED}" font-size="12">● implemented feature, as documented in each app’s README · provider-dependent features need an API key</text>')
    s.append("</svg>")
    return "".join(s)


def build_status(cat: dict, status: dict | None) -> str:
    projects, domains = cat["projects"], OrderedDict((d["id"], d) for d in cat["domains"])
    cols, tile_w, tile_h, gx, gy, top = 4, 291, 56, 12, 10, 112
    rows = -(-len(projects) // cols)
    W = 40 * 2 + cols * tile_w + (cols - 1) * gx
    H = top + rows * (tile_h + gy) + 76
    now = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5)).strftime("%d %b %Y · %H:%M PKT")
    counts = Counter((status or {}).get(p["url"], {}).get("state", "unchecked") for p in projects)
    up = counts["online"] + counts["sleeping"]
    s = [svg_open(W, H, "Live deployment status", f"Automated availability check of {len(projects)} deployed projects.")]
    s.append(eyebrow(40, 44, "Live deployment status · auto-checked every 6 hours"))
    if status:
        s.append(f'<circle class="pulse" cx="48" cy="69" r="7" fill="{STATUS["online"][0]}"/>'
                 f'<text x="64" y="76" fill="{TEXT}" font-size="22" font-weight="800">{up} of {len(projects)} apps responding</text>'
                 f'<text x="{W - 40}" y="76" fill="{TEXT2}" font-size="13" text-anchor="end">Last check {now}</text>')
    else:
        s.append(f'<text x="40" y="76" fill="{TEXT}" font-size="22" font-weight="800">{len(projects)} deployed apps · first automated check pending</text>')
    ordered = sorted(projects, key=lambda p: list(domains).index(p["domain"]))
    for i, p in enumerate(ordered):
        x = 40 + (i % cols) * (tile_w + gx)
        y = top + (i // cols) * (tile_h + gy)
        st = (status or {}).get(p["url"], {"state": "unchecked"})
        col, lab = STATUS[st["state"]]
        dcol = domains[p["domain"]]["color"]
        name = p["name"] if len(p["name"]) <= 28 else p["name"][:27] + "…"
        meta = host_of(p["url"]) + (f' · {st["ms"]:,} ms' if st.get("ms") else "")
        pulse = 'class="pulse" ' if st["state"] == "online" else ""
        s.append(f'<a href="{esc(p["url"])}" target="_blank"><g transform="translate({x} {y})">'
                 f'<rect width="{tile_w}" height="{tile_h}" rx="10" fill="{CARD}" stroke="{STROKE}"/>'
                 f'<rect x="0" y="10" width="3" height="{tile_h - 20}" rx="1.5" fill="{dcol}"/>'
                 f'<circle {pulse}cx="22" cy="{tile_h / 2}" r="6" fill="{col}"><title>{esc(lab)}</title></circle>'
                 f'<text x="38" y="24" fill="{TEXT}" font-size="13.5" font-weight="700">{esc(name)}</text>'
                 f'<text x="38" y="43" fill="{TEXT2}" font-size="11.5">{esc(meta)} · <tspan fill="{col}">{esc(lab)}</tspan></text>'
                 "</g></a>")
    ly = H - 48
    lx = 40
    for key in ("online", "sleeping", "down"):
        col, lab = STATUS[key]
        s.append(f'<circle cx="{lx + 6}" cy="{ly - 4}" r="5" fill="{col}"/><text x="{lx + 16}" y="{ly}" fill="{TEXT2}" font-size="12">{esc(lab)}</text>')
        lx += 90
    s.append(f'<text x="{W - 40}" y="{ly}" fill="{MUTED}" font-size="12" text-anchor="end">Streamlit apps sleep when idle and wake on first visit · open any app from the table below</text>')
    ly, lx = H - 22, 40
    for d in domains.values():
        s.append(f'<rect x="{lx}" y="{ly - 10}" width="4" height="12" rx="2" fill="{d["color"]}"/><text x="{lx + 10}" y="{ly}" fill="{MUTED}" font-size="11.5">{esc(d["label"])}</text>')
        lx += 14 + len(d["label"]) * 6.3 + 16
    s.append("</svg>")
    return "".join(s)


def build_stats(owner: str, stats: dict) -> str:
    days = stats.get("days") or []
    start = dt.date.fromisoformat(stats["start"]) if stats.get("start") else dt.date.today() - dt.timedelta(days=len(days) - 1)
    cur, longest = streaks(days)
    active = sum(1 for c in days if c > 0)
    W, H = 1280, 470
    s = [svg_open(W, H, f"{owner} GitHub statistics", "Contribution heatmap, streaks, repositories and language mix for the last 12 months.")]
    s.append(eyebrow(40, 44, "GitHub activity · last 12 months"))
    s.append(f'<text x="40" y="76" fill="{TEXT}" font-size="26" font-weight="800">{sum(days):,} contributions · {active} active days</text>')
    tiles = [
        (f"{cur} days", "Current streak", "Consecutive active days", "#39d353"),
        (f"{longest} days", "Longest streak", "Best run this year", "#3987e5"),
        (str(stats.get("public_repos", 0)), "Public repositories", "Apps, labs & studies", "#c98500"),
        (str(stats.get("stars", 0)), "Stars earned", "Across owned repos", "#d55181"),
        (str(stats.get("recent_repos", 0)), "Repos shipped to", "Pushed in the last 30 days", "#9085e9"),
    ]
    tw = (W - 80 - 4 * 16) / 5
    for i, t in enumerate(tiles):
        s.append(kpi(40 + i * (tw + 16), 100, tw, *t))

    # heatmap
    s.append(f'<rect x="40" y="226" width="820" height="214" rx="16" fill="{CARD}" stroke="{STROKE}"/>')
    s.append(eyebrow(64, 258, "Contribution calendar"))
    cell, gap = 11, 2
    hx, hy = 92, 286
    peak = max(days) if days else 1
    nonzero = sorted(c for c in days if c > 0)
    q = [nonzero[int(len(nonzero) * f)] if nonzero else 1 for f in (0.25, 0.5, 0.75)]
    pad = (start.weekday() + 1) % 7  # Sunday-first rows
    for i, c in enumerate(days):
        k = i + pad
        wk, dow = divmod(k, 7)
        lvl = 0 if c == 0 else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4
        d = start + dt.timedelta(days=i)
        s.append(f'<rect x="{hx + wk * (cell + gap)}" y="{hy + dow * (cell + gap)}" width="{cell}" height="{cell}" rx="2.5" fill="{HEAT[lvl]}"><title>{c} on {d:%d %b %Y}</title></rect>')
        if d.day == 1:
            s.append(f'<text x="{hx + wk * (cell + gap)}" y="{hy - 8}" fill="{MUTED}" font-size="11">{d:%b}</text>')
    for r, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        s.append(f'<text x="{hx - 10}" y="{hy + r * (cell + gap) + 10}" fill="{MUTED}" font-size="11" text-anchor="end">{lab}</text>')
    lx = 640
    s.append(f'<text x="{lx - 8}" y="425" fill="{MUTED}" font-size="11" text-anchor="end">Less</text>')
    for i, c in enumerate(HEAT):
        s.append(f'<rect x="{lx + i * 15}" y="415" width="12" height="12" rx="2.5" fill="{c}"/>')
    s.append(f'<text x="{lx + 5 * 15 + 4}" y="425" fill="{MUTED}" font-size="11">More · peak {peak}/day</text>')

    # languages
    langs = stats.get("languages") or {}
    total = sum(langs.values()) or 1
    lang_cols = {"Python": "#3987e5", "TypeScript": "#9085e9", "HTML": "#d95926", "JavaScript": "#c98500", "Jupyter Notebook": "#d55181"}
    s.append(f'<rect x="876" y="226" width="364" height="214" rx="16" fill="{CARD}" stroke="{STROKE}"/>')
    s.append(eyebrow(900, 258, "Repository languages"))
    bx, cx = 900, 900
    for lang, n in langs.items():
        w = 316 * n / total - 2
        s.append(f'<rect x="{cx:.1f}" y="276" width="{max(w, 2):.1f}" height="14" rx="4" fill="{lang_cols.get(lang, MUTED)}"><title>{esc(lang)}: {n}</title></rect>')
        cx += w + 2
    for i, (lang, n) in enumerate(list(langs.items())[:5]):
        y = 318 + i * 24
        s.append(f'<rect x="{bx}" y="{y - 10}" width="12" height="12" rx="3" fill="{lang_cols.get(lang, MUTED)}"/>'
                 f'<text x="{bx + 20}" y="{y}" fill="{TEXT2}" font-size="13">{esc(lang)}</text>'
                 f'<text x="1216" y="{y}" fill="{TEXT}" font-size="13" font-weight="700" text-anchor="end">{n} · {100 * n / total:.0f}%</text>')
    s.append("</svg>")
    return "".join(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", help="offline: JSON with days/start/public_repos/followers/stars/languages")
    ap.add_argument("--no-check", action="store_true", help="skip live URL checks")
    a = ap.parse_args()
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    token = os.environ.get("GITHUB_TOKEN")
    if a.seed:
        stats = json.loads(Path(a.seed).read_text())
    else:
        stats = github_stats(cat["owner"], token)
    status = None if a.no_check else check_all(cat["projects"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "portfolio-infographic.svg").write_text(build_infographic(cat, stats, status), encoding="utf-8")
    (OUT / "agent-capabilities.svg").write_text(build_matrix(cat), encoding="utf-8")
    (OUT / "live-status.svg").write_text(build_status(cat, status), encoding="utf-8")
    (OUT / "github-stats.svg").write_text(build_stats(cat["owner"], stats), encoding="utf-8")
    if status:
        up = sum(1 for v in status.values() if v["state"] != "down")
        print(f"{up}/{len(status)} deployments responding")
        for p in cat["projects"]:
            st = status[p["url"]]
            print(f'  {st["state"]:9} {st.get("code")} {st.get("ms")}ms  {p["name"]}')


if __name__ == "__main__":
    main()
