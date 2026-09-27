"""Gera o card de atividade do README a partir do calendário de contribuições.

Uso (dentro do GitHub Actions):
    GITHUB_TOKEN=... GITHUB_LOGIN=Victorkaue333 python3 scripts/activity.py dist/github-activity.svg

Só biblioteca padrão. Consulta a API GraphQL do GitHub (últimos 12 meses, o
mesmo período do gráfico do perfil) e desenha um SVG no visual do README.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from collections import Counter, defaultdict
from xml.sax.saxutils import escape

# design system do portfólio (victor-kaue.vercel.app, tema escuro)
BG = "#050505"
SURFACE = "#1a1a1a"
BORDER = "#222222"
ACCENT = "#ff7a00"
ACCENT_SOFT = "#ff9933"
ACCENT_DEEP = "#cc6200"
TEXT = "#ffffff"
TEXT3 = "#cccccc"
TEXT2 = "#808080"
MUTED = "#4d4d4d"
FAINT = "#333333"

SANS = "system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

MONTHS = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
WEEKDAYS = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
WEEKDAYS_SHORT = ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB"]
LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday contributionLevel } }
      }
    }
  }
}
"""


def fetch(login: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-activity-card"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors") or not (payload.get("data") or {}).get("user"):
        raise SystemExit(f"GraphQL falhou: {payload.get('errors')}")

    col = payload["data"]["user"]["contributionsCollection"]
    cal = col["contributionCalendar"]
    days = [
        (d["date"], d["contributionCount"], d["weekday"])
        for week in cal["weeks"]
        for d in week["contributionDays"]
    ]
    return {
        "total": cal["totalContributions"],
        "days": days,
        # nível 0–4 de cada dia, pelos mesmos quartis do gráfico do perfil (usado em heatmap.py)
        "levels": {
            d["date"]: LEVELS.index(d["contributionLevel"])
            for week in cal["weeks"]
            for d in week["contributionDays"]
        },
        "breakdown": [
            ("COMMITS", col["totalCommitContributions"], ACCENT),
            ("PULL REQUESTS", col["totalPullRequestContributions"], ACCENT_SOFT),
            ("ISSUES", col["totalIssueContributions"], ACCENT_DEEP),
            ("REVIEWS", col["totalPullRequestReviewContributions"], TEXT3),
            ("REPOSITÓRIOS", col["totalRepositoryContributions"], TEXT2),
            ("PRIVADAS", col["restrictedContributionsCount"], MUTED),
        ],
    }


def num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def t(s) -> str:
    return escape(str(s))


def render(data: dict, today: dt.date) -> str:
    W, H = 1200, 480
    L, R = 48, 1152
    days = data["days"]
    total = data["total"]

    active = sum(1 for _, c, _ in days if c > 0)
    best_date, best_count, _ = max(days, key=lambda d: (d[1], d[0]))
    by_weekday = Counter()
    by_month = defaultdict(int)
    for date, count, wd in days:
        by_weekday[wd] += count
        by_month[date[:7]] += count
    months = sorted(by_month)[-12:]
    top_wd = max(range(7), key=lambda w: by_weekday[w])
    wd_sum = sum(by_weekday.values()) or 1

    def fmt_date(iso):
        y, m, d = iso.split("-")
        return f"{int(d)} {MONTHS[int(m) - 1]} {y}"

    kpis = [
        ("CONTRIBUIÇÕES", num(total), "ÚLTIMOS 12 MESES", TEXT),
        ("DIAS ATIVOS", num(active), f"{round(100 * active / max(1, len(days)))}% DO PERÍODO", TEXT),
        ("MELHOR DIA", num(best_count) if best_count else "—",
         fmt_date(best_date) if best_count else "SEM REGISTROS", TEXT),
        ("DIA MAIS ATIVO", WEEKDAYS[top_wd] if total else "—",
         f"{round(100 * by_weekday[top_wd] / wd_sum)}% DAS CONTRIBUIÇÕES" if total else "", TEXT),
    ]
    pitch = (R - L) / 4
    kpi_svg = []
    for i, (label, value, sub, color) in enumerate(kpis):
        x = L + i * pitch + (0 if i == 0 else 24)
        kpi_svg.append(
            f'<text x="{x:.0f}" y="104" font-family="{MONO}" font-size="12" fill="{TEXT2}" letter-spacing="3">{t(label)}</text>'
            f'<text x="{x - 2:.0f}" y="152" font-size="42" font-weight="700" fill="{color}" letter-spacing="-1">{t(value)}</text>'
            f'<text x="{x:.0f}" y="178" font-family="{MONO}" font-size="11.5" fill="{TEXT2}" letter-spacing="2">{t(sub)}</text>'
        )
        if i:
            kpi_svg.append(f'<line x1="{L + i * pitch:.0f}" y1="86" x2="{L + i * pitch:.0f}" y2="182" stroke="{BORDER}"/>')

    # por mês
    cx0, cx1, top, base = L, 700, 268, 368
    gap = 10
    bw = (cx1 - cx0 - gap * 11) / 12
    peak = max((by_month[m] for m in months), default=0) or 1
    top_month = max(months, key=lambda m: (by_month[m], m)) if months else None
    bars = []
    for i, m in enumerate(months):
        v = by_month[m]
        h = max(3, (base - top) * v / peak)
        x = cx0 + i * (bw + gap)
        hi = m == top_month and v > 0
        bars.append(f'<rect x="{x:.1f}" y="{base - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" '
                    f'fill="{ACCENT if hi else BORDER}"/>')
        bars.append(f'<text x="{x + bw / 2:.1f}" y="{base + 24}" text-anchor="middle" font-family="{MONO}" '
                    f'font-size="11" fill="{TEXT if hi else TEXT2}" letter-spacing="1">{MONTHS[int(m[5:]) - 1]}</text>')
        if hi:
            bars.append(f'<text x="{x + bw / 2:.1f}" y="{base - h - 10:.1f}" text-anchor="middle" font-size="14" '
                        f'font-weight="600" fill="{TEXT}">{num(v)}</text>')

    # por dia da semana
    wx, track0, track1 = 760, 812, 1096
    rows = []
    wd_peak = max(by_weekday.values(), default=0) or 1
    for w in range(7):
        y = 272 + w * 17
        frac = by_weekday[w] / wd_peak
        hi = w == top_wd and total
        rows.append(
            f'<text x="{wx}" y="{y}" font-family="{MONO}" font-size="11" fill="{TEXT if hi else TEXT2}" letter-spacing="1.5">{WEEKDAYS_SHORT[w]}</text>'
            f'<rect x="{track0}" y="{y - 8}" width="{track1 - track0}" height="7" rx="3.5" fill="{SURFACE}"/>'
            f'<rect x="{track0}" y="{y - 8}" width="{max(3, (track1 - track0) * frac):.1f}" height="7" rx="3.5" '
            f'fill="{ACCENT if hi else MUTED}"/>'
            f'<text x="{R}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{TEXT2}">'
            f'{round(100 * by_weekday[w] / wd_sum)}%</text>'
        )

    # composição
    parts = [(n, v, c) for n, v, c in data["breakdown"] if v > 0]
    comp_total = sum(v for _, v, _ in parts) or 1
    comp, legend = [], []
    x = L
    for i, (name, v, color) in enumerate(parts):
        w = (R - L) * v / comp_total
        comp.append(f'<rect x="{x:.1f}" y="416" width="{max(2, w - 2):.1f}" height="6" rx="3" fill="{color}"/>')
        x += w
    lx = L
    for name, v, color in parts:
        label = f"{name} {num(v)}"
        legend.append(f'<rect x="{lx}" y="442" width="8" height="8" rx="2" fill="{color}"/>'
                      f'<text x="{lx + 16}" y="450" font-family="{MONO}" font-size="11" fill="{TEXT2}" '
                      f'letter-spacing="1.5">{t(label)}</text>')
        lx += 16 + len(label) * 8.3 + 28

    updated = f"ATUALIZADO EM {today.day:02d} {MONTHS[today.month - 1]} {today.year}"
    label = f"Atividade no GitHub: {num(total)} contribuições nos últimos 12 meses, {num(active)} dias ativos"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{t(label)}">
<title>{t(label)}</title>
<desc>Resumo do calendário de contribuições: totais, distribuição por mês e por dia da semana e composição por tipo. Gerado diariamente via GitHub Actions.</desc>
<defs><clipPath id="a-clip"><rect width="{W}" height="{H}" rx="18"/></clipPath></defs>
<g clip-path="url(#a-clip)" font-family="{SANS}">
<rect width="{W}" height="{H}" fill="{BG}"/>
<circle cx="{L + 4}" cy="44" r="4" fill="{ACCENT}"><animate attributeName="opacity" values="1;.25;1" dur="2.4s" repeatCount="indefinite"/></circle>
<text x="{L + 18}" y="48" font-family="{MONO}" font-size="12" fill="{TEXT2}" letter-spacing="3">ATIVIDADE · ÚLTIMOS 12 MESES</text>
<text x="{R}" y="48" text-anchor="end" font-family="{MONO}" font-size="12" fill="{TEXT2}" letter-spacing="3">{updated}</text>
<line x1="{L}" y1="68" x2="{R}" y2="68" stroke="{BORDER}"/>
{"".join(kpi_svg)}
<line x1="{L}" y1="206" x2="{R}" y2="206" stroke="{BORDER}"/>
<text x="{L}" y="240" font-family="{MONO}" font-size="12" fill="{TEXT2}" letter-spacing="3">POR MÊS</text>
<text x="{wx}" y="240" font-family="{MONO}" font-size="12" fill="{TEXT2}" letter-spacing="3">POR DIA DA SEMANA</text>
{"".join(bars)}
<line x1="{cx0}" y1="{base + .5}" x2="{cx1}" y2="{base + .5}" stroke="{BORDER}"/>
{"".join(rows)}
{"".join(comp)}
{"".join(legend)}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{BORDER}"/>
</svg>
"""


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else "github-activity.svg"
    login = os.environ["GITHUB_LOGIN"]
    token = os.environ["GITHUB_TOKEN"]
    svg = render(fetch(login, token), dt.datetime.now(dt.timezone.utc).date())
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"ok {out} ({len(svg.encode()) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
