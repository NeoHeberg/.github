import requests, datetime, math, os, sys
from collections import defaultdict

ORG = "NeoHeberg"
TOKEN = os.environ["GH_TOKEN"]
HEADERS = {"Authorization": f"token {TOKEN}"}

# Repos public
def get_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{ORG}/repos?type=public&per_page=100&page={page}"
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

# Activité de commits hebdomadaire
def get_commit_activity(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/stats/commit_activity"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 202:
        return []
    if r.status_code != 200:
        print(f"⚠️  Erreur stats pour {repo_full_name}: {r.status_code}")
        return []
    return r.json()

year = datetime.date.today().year
monthly = defaultdict(int)

repos = get_repos()
print(f"📦 {len(repos)} repos trouvés")

for repo in repos:
    name = repo["full_name"]
    data = get_commit_activity(name)
    for week in data:
        week_unix = week["week"]
        week_date = datetime.datetime.utcfromtimestamp(week_unix).date()
        if week_date.year == year:
            month = week_date.month
            monthly[month] += week["total"]

months_labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
                 "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
values = [monthly[m] for m in range(1, 13)]
max_val = max(values) if values else 10
step = 1
if max_val > 20: step = 5
if max_val > 50: step = 10
if max_val > 100: step = 25
max_axe = math.ceil(max_val / step) * step

width, height = 1200, 350
margin_left, margin_right, margin_top, margin_bottom = 80, 40, 40, 60
plot_width = width - margin_left - margin_right
plot_height = height - margin_top - margin_bottom
bar_width = plot_width / 12 - 4  # 12 mois

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')
svg.append('<style>text{font-family:system-ui,-apple-system,sans-serif;fill:#ccc;font-size:12px}.title{font-size:18px;fill:#5bcdec;font-weight:600}.axe-line{stroke:#555;stroke-width:1}.bar-green{fill:#39d353}.bar-empty{fill:#2d333b}</style>')
svg.append(f'<rect width="100%" height="100%" fill="#0d1117"/>')

# Axe Y
for val in range(0, max_axe + 1, step):
    y = margin_top + plot_height - (val / max_axe) * plot_height
    svg.append(f'<line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" class="axe-line" stroke-dasharray="3,3"/>')
    svg.append(f'<text x="{margin_left - 10}" y="{y + 4}" text-anchor="end">{val}</text>')

# Barres
for i, (month, count) in enumerate(zip(months_labels, values)):
    x = margin_left + i * (plot_width / 12)
    bar_h = (count / max_axe) * plot_height if count > 0 else 0
    y = margin_top + plot_height - bar_h
    cls = 'bar-green' if count > 0 else 'bar-empty'
    svg.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_h}" class="{cls}"/>')
    svg.append(f'<text x="{x + bar_width/2}" y="{margin_top + plot_height + 20}" text-anchor="middle">{month}</text>')

# Axe X
svg.append(f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" class="axe-line"/>')

# Titre
svg.append(f'<text x="{width/2}" y="28" text-anchor="middle" class="title">Activité de NeoHeberg en {year}</text>')

svg.append(f'<!-- Cache bust: {datetime.datetime.now().isoformat()} -->')
svg.append('</svg>')

with open("profile/activity-graph.svg", "w") as f:
    f.write("\n".join(svg))

print("✅ Graphique d'activité généré.")