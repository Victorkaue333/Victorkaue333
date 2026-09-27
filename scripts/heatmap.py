"""Gera o heatmap de contribuições do README: as células surgem uma a uma, em
diagonal, e as que têm contribuição piscam ao aparecer. Toca uma vez e congela.

Uso:
    GITHUB_TOKEN=... GITHUB_LOGIN=Victorkaue333 python3 scripts/heatmap.py   # Actions
    python scripts/heatmap.py                                                # local, usa o snapshot

Só biblioteca padrão; reaproveita a consulta GraphQL de activity.py. Com token,
busca os dados e atualiza data/contributions.json; sem token (ou se a API
falhar), redesenha a partir desse snapshot. Sai um SVG só, versionado em
assets/, com os dois temas via prefers-color-scheme: nada depende da branch
output nem de URL externa. A animação é CSS, que o GitHub roda em <img>.
"""
import datetime as dt
import json
import os
import sys

from activity import ACCENT, ACCENT_DEEP, MONTHS, SANS, fetch, num, t

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets", "contrib-heatmap.svg")
SNAPSHOT = os.path.join(ROOT, "data", "contributions.json")

THEMES = {
    "dark": {
        "cells": ["#1a1a1a", "#3d1d00", "#7a3a00", "#cc6200", "#ff7a00"],
        "label": "#808080",
        "text": "#ffffff",
        "accent": ACCENT,
    },
    "light": {
        "cells": ["#ebedf0", "#ffd9b3", "#ffb366", "#ff8c1a", "#cc6200"],
        "label": "#57606a",
        "text": "#1f2328",
        "accent": ACCENT_DEEP,
    },
}
WEEKDAY_LABELS = [(1, "Seg"), (3, "Qua"), (5, "Sex")]

CELL, GAP, RADIUS = 13, 3, 2.5
STEP = CELL + GAP
LEFT, TOP = 34, 24
REVEAL, POP = 3.6, 0.55  # duração da varredura inteira e de cada célula (s)
ROW_LAG = 0.55  # atraso de cada linha, em colunas: é o que inclina a varredura


def palette_css(pal: dict) -> str:
    cells = " ".join(f".v{i} {{ fill: {c}; }}" for i, c in enumerate(pal["cells"]))
    return (f'.l {{ fill: {pal["label"]}; }} .t {{ fill: {pal["text"]}; }} '
            f'.a {{ fill: {pal["accent"]}; }} {cells}')


def render(data: dict) -> str:
    days = data["days"]
    first = dt.date.fromisoformat(days[0][0])
    start = first - dt.timedelta(days=days[0][2])  # domingo da primeira coluna
    n_cols = (dt.date.fromisoformat(days[-1][0]) - start).days // 7 + 1
    W = LEFT + n_cols * STEP + 6
    H = TOP + 7 * STEP + 30

    # mês novo = coluna cujo domingo já caiu nele; o primeiro sai se ficar colado no segundo
    marks = []
    for c in range(n_cols):
        month = max(first, start + dt.timedelta(weeks=c)).month
        if not marks or marks[-1][1] != month:
            marks.append((c, month))
    if len(marks) > 1 and marks[1][0] - marks[0][0] < 3:
        marks.pop(0)
    labels = [f'<text class="l" x="{LEFT + c * STEP}" y="{TOP - 8}">{MONTHS[m - 1].capitalize()}</text>'
              for c, m in marks]
    labels += [f'<text class="l" x="2" y="{TOP + r * STEP + CELL - 2}">{name}</text>'
               for r, name in WEEKDAY_LABELS]

    last = (n_cols - 1) + 6 * ROW_LAG
    cells = []
    for date, _, wd in days:
        c = (dt.date.fromisoformat(date) - start).days // 7
        level = data["levels"][date]
        delay = (c + wd * ROW_LAG) / last * REVEAL
        cells.append(f'<rect class="c v{level}{" g" if level else ""}" x="{LEFT + c * STEP}" y="{TOP + wd * STEP}" '
                     f'width="{CELL}" height="{CELL}" rx="{RADIUS}" style="animation-delay:{delay:.2f}s"/>')

    # legenda Menos ▢▢▢▢▢ Mais, alinhada à direita na linha do total
    fy = H - 8
    lx = W - 6 - 30
    legend = [f'<text class="l" x="{lx}" y="{fy}">Mais</text>']
    for level in reversed(range(5)):
        lx -= 14
        legend.append(f'<rect class="v{level}" x="{lx}" y="{fy - 10}" width="11" height="11" rx="2"/>')
    legend.append(f'<text class="l" x="{lx - 6}" y="{fy}" text-anchor="end">Menos</text>')

    total = data["total"]
    label = f"Heatmap de contribuições: {num(total)} contribuições nos últimos 12 meses"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{t(label)}" font-family="{SANS}">
<title>{t(label)}</title>
<style>
{palette_css(THEMES["dark"])}
@media (prefers-color-scheme: light) {{ {palette_css(THEMES["light"])} }}
text.l {{ font-size: 12px; font-weight: 600; }}
.c {{ transform-box: fill-box; transform-origin: center; opacity: 0; animation: pop {POP}s ease-out both; }}
.g {{ animation: pop {POP}s ease-out both, flash {POP + .15:.2f}s ease-out both; }}
@keyframes pop {{ 0% {{ opacity: 0; transform: scale(.2); }} 60% {{ opacity: 1; transform: scale(1.1); }} 100% {{ opacity: 1; transform: scale(1); }} }}
@keyframes flash {{ 0%, 45% {{ filter: brightness(2.2); }} 100% {{ filter: brightness(1); }} }}
@media (prefers-reduced-motion: reduce) {{ .c {{ opacity: 1; animation: none; }} }}
</style>
{"".join(labels)}
{"".join(cells)}
<text class="t" x="{LEFT}" y="{fy}" font-size="14" font-weight="700"><tspan class="a">{num(total)}</tspan> contribuições nos últimos 12 meses</text>
{"".join(legend)}
</svg>
"""


def load() -> dict:
    """Dados frescos da API quando há token; senão (ou se falhar), o último snapshot."""
    login, token = os.environ.get("GITHUB_LOGIN"), os.environ.get("GITHUB_TOKEN")
    if login and token:
        try:
            data = fetch(login, token)
            snap = {"total": data["total"], "days": data["days"], "levels": data["levels"]}
            os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)
            with open(SNAPSHOT, "w", encoding="utf-8", newline="\n") as f:
                json.dump(snap, f, separators=(",", ":"))
            return snap
        except (OSError, SystemExit) as e:  # rede/HTTP ou erro do GraphQL
            print(f"API falhou ({e}); usando o snapshot", file=sys.stderr)
    with open(SNAPSHOT, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    svg = render(load())
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"ok assets/contrib-heatmap.svg ({len(svg.encode()) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
