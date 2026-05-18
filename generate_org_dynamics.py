#!/usr/bin/env python3
"""
Génère 3 SVG dynamiques pour le README de l'organisation NeoHeberg :
- activity-graph.svg : commits par mois
- org-stats.svg     : repos / forks / stars
- org-languages.svg : top 8 langages (barres)

Les SVG sont sans fond (transparents) et utilisent des couleurs sombres pour le texte,
ce qui les rend lisibles sur fond clair. En mode sombre, le contraste peut être réduit ;
pour un meilleur résultat sur les deux thèmes, envisagez d'ajouter un fond légèrement
teinté ou d'utiliser des couleurs adaptatives via CSS média (non supporté dans les
images SVG sur GitHub).
"""

import requests, datetime, math, os, sys, json
from collections import defaultdict, Counter

ORG = "NeoHeberg"
TOKEN = os.environ["GH_TOKEN"]
HEADERS = {"Authorization": f"token {TOKEN}"}
YEAR = datetime.date.today().year
SINCE = f"{YEAR}-01-01T00:00:00Z"

# ─── Récupération des dépôts ──────────────────────────────────────
def get_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{ORG}/repos?type=all&per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            print(f"Erreur API repos: {r.status_code} {r.text}")
            sys.exit(1)
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

# ─── 1. Activité mensuelle ────────────────────────────────────────
def get_monthly_commits(repos):
    monthly = defaultdict(int)
    for repo in repos:
        name = repo["full_name"]
        page = 1
        while True:
            url = f"https://api.github.com/repos/{name}/commits?since={SINCE}&per_page=100&page={page}"
            r = requests.get(url, headers=HEADERS)
            if r.status_code != 200:
                break
            data = r.json()
            if not data:
                break
            for c in data:
                try:
                    dt = datetime.datetime.fromisoformat(c["commit"]["committer"]["date"].rstrip("Z"))
                    monthly[dt.month] += 1
                except:
                    pass
            page += 1
            if len(data) < 100:
                break
    return monthly

# ─── 2. Statistiques globales ─────────────────────────────────────
def get_global_stats(repos):
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    total_repos = len(repos)
    return total_repos, total_forks, total_stars

# ─── 3. Langages dominants ────────────────────────────────────────
def get_top_languages(repos):
    lang_counter = Counter()
    for repo in repos:
        url = repo["languages_url"]
        r = requests.get(url, headers=HEADERS)
        if r.status_code != 200:
            continue
        langs = r.json()
        for lang, bytes_count in langs.items():
            if lang:
                lang_counter[lang] += bytes_count
    return lang_counter.most_common(8)

# ─── Fonctions SVG génériques ─────────────────────────
def svg_bar_chart_activity(monthly):
    months_labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
                     "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    values = [monthly.get(m, 0) for m in range(1, 13)]
    max_val = max(values) if values else 0
    if max_val == 0:
        max_axe = 1
    else:
        step = 1
        if max_val > 20: step = 5
        if max_val > 50: step = 10
        if max_val > 100: step = 25
        max_axe = math.ceil(max_val / step) * step

    width, height = 1200, 350
    ml, mr, mt, mb = 80, 40, 40, 60
    pw = width - ml - mr
    ph = height - mt - mb
    bw = pw / 12 - 4

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    svg.append('<style>text{font-family:system-ui,sans-serif;fill:#24292e;font-size:12px}.title{font-size:18px;fill:#0366d6;font-weight:600}.axe-line{stroke:#d1d5da;stroke-width:1}.bar-green{fill:#28a745}.bar-empty{fill:#e1e4e8}</style>')

    step_axe = max(1, math.ceil(max_axe / 5))
    for val in range(0, max_axe + 1, step_axe):
        y = mt + ph - (val / max_axe) * ph if max_axe > 0 else mt + ph
        svg.append(f'<line x1="{ml}" y1="{y}" x2="{width - mr}" y2="{y}" class="axe-line" stroke-dasharray="3,3"/>')
        svg.append(f'<text x="{ml - 10}" y="{y + 4}" text-anchor="end">{val}</text>')

    for i, (month, count) in enumerate(zip(months_labels, values)):
        x = ml + i * (pw / 12)
        bar_h = (count / max_axe) * ph if max_axe > 0 else 0
        y = mt + ph - bar_h
        cls = 'bar-green' if count > 0 else 'bar-empty'
        svg.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bar_h}" class="{cls}"/>')
        svg.append(f'<text x="{x + bw/2}" y="{mt + ph + 20}" text-anchor="middle">{month}</text>')

    svg.append(f'<line x1="{ml}" y1="{mt + ph}" x2="{width - mr}" y2="{mt + ph}" class="axe-line"/>')
    svg.append(f'<text x="{width/2}" y="28" text-anchor="middle" class="title">Activité de NeoHeberg en {YEAR}</text>')
    svg.append(f'<!-- {datetime.datetime.now().isoformat()} -->')
    svg.append('</svg>')
    return "\n".join(svg)

def svg_stats_card(repos, forks, stars):
    width, height = 500, 200
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    svg.append('<style>text{font-family:system-ui,sans-serif}.title{fill:#0366d6;font-size:20px;font-weight:bold}.label{fill:#586069;font-size:14px}.number{fill:#24292e;font-size:32px;font-weight:bold}.icon{fill:#28a745}</style>')
    svg.append(f'<text x="25" y="40" class="title">Statistiques de NeoHeberg</text>')

    # Repos
    svg.append(f'<circle cx="50" cy="80" r="12" fill="#28a745"/>')
    svg.append(f'<text x="75" y="85" class="label">Repositories</text>')
    svg.append(f'<text x="75" y="120" class="number">{repos}</text>')

    # Forks
    svg.append(f'<circle cx="200" cy="80" r="12" fill="#0366d6"/>')
    svg.append(f'<text x="225" y="85" class="label">Forks</text>')
    svg.append(f'<text x="225" y="120" class="number">{forks}</text>')

    # Stars
    svg.append(f'<circle cx="350" cy="80" r="12" fill="#d73a49"/>')
    svg.append(f'<text x="375" y="85" class="label">Stars</text>')
    svg.append(f'<text x="375" y="120" class="number">{stars}</text>')

    svg.append('</svg>')
    return "\n".join(svg)

def svg_top_languages(lang_list):
    if not lang_list:
        return svg_stats_card(0,0,0)
    max_bytes = max(count for _, count in lang_list)
    colors = ["#f1e05a","#e34c26","#563d7c","#2b7489","#3572a5","#89e051","#dea584","#ffac45"]
    width, height = 500, 50 + 30 * len(lang_list)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">']
    svg.append('<style>text{font-family:system-ui,sans-serif}.title{fill:#0366d6;font-size:18px;font-weight:bold}.lang{fill:#24292e;font-size:14px}.pct{fill:#586069;font-size:12px}</style>')
    svg.append(f'<text x="20" y="30" class="title">Langages les plus utilisés</text>')

    y = 60
    for i, (lang, count) in enumerate(lang_list):
        pct = count / max_bytes
        bar_w = 300 * pct
        color = colors[i % len(colors)]
        svg.append(f'<rect x="20" y="{y}" width="{bar_w}" height="16" rx="4" fill="{color}"/>')
        svg.append(f'<text x="330" y="{y+13}" class="lang">{lang}</text>')
        y += 30
    svg.append('</svg>')
    return "\n".join(svg)

# ─── Main ─────────────────────────────────────────────────────────
def main():
    repos = get_repos()
    print(f"📦 {len(repos)} dépôts")

    # 1. Activité
    monthly = get_monthly_commits(repos)
    activity_svg = svg_bar_chart_activity(monthly)
    with open("profile/activity-graph.svg", "w") as f:
        f.write(activity_svg)
    print("✅ activity-graph.svg")

    # 2. Stats globales
    repos_count, forks_count, stars_count = get_global_stats(repos)
    stats_svg = svg_stats_card(repos_count, forks_count, stars_count)
    with open("profile/org-stats.svg", "w") as f:
        f.write(stats_svg)
    print(f"✅ org-stats.svg ({repos_count} repos, {forks_count} forks, {stars_count} stars)")

    # 3. Langages
    top_langs = get_top_languages(repos)
    langs_svg = svg_top_languages(top_langs)
    with open("profile/org-languages.svg", "w") as f:
        f.write(langs_svg)
    print(f"✅ org-languages.svg ({len(top_langs)} langages)")

if __name__ == "__main__":
    main()