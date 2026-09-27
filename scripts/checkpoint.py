"""Gera o HUD de rodapé do README: uma frase curta à esquerda e, à direita, o
indicador de salvamento de jogo com a data da última execução do workflow.

Uso (dentro do GitHub Actions):
    python3 scripts/checkpoint.py dist/checkpoint.svg

Só biblioteca padrão. Fundo transparente; as cores trocam pelo
prefers-color-scheme para funcionar nos temas claro e escuro do GitHub.
"""
import datetime as dt
import os
import sys

from activity import ACCENT, MONO, MONTHS, SANS, t

PHRASE = "Mesmo no escuro, a gente segue em frente."
BRT = dt.timezone(dt.timedelta(hours=-3))  # a data do "save" é a de Brasília

W, H = 840, 44
BASE = 27
SIZE = 12
CHAR = SIZE * .6 + 2  # avanço mono (.6em) + letter-spacing; textLength fixa a largura


def render(day: dt.date) -> str:
    label = "PROGRESSO SALVO · "
    date = f"{day.day:02d} {MONTHS[day.month - 1]} {day.year}"
    tl = len(label + date) * CHAR - 2
    x0 = W - 2 - tl  # início do texto da direita
    cx = x0 - 18  # centro do ícone de salvamento
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{t(PHRASE)} Progresso salvo em {t(date.lower())}.">
<title>{t(PHRASE)} Progresso salvo em {t(date.lower())}.</title>
<style>
.p {{ fill: #808080; }} .l {{ fill: #808080; }} .d {{ fill: #ffffff; }} .k {{ stroke: #333333; }}
@media (prefers-color-scheme: light) {{ .p, .l {{ fill: #57606a; }} .d {{ fill: #1f2328; }} .k {{ stroke: #d0d7de; }} }}
</style>
<text class="p" x="2" y="{BASE}" font-family="{SANS}" font-size="15" font-style="italic">{t(PHRASE)}</text>
<g>
  <circle class="k" cx="{cx:.1f}" cy="{BASE - 4.5}" r="7" fill="none" stroke-width="2"/>
  <path d="M{cx:.1f} {BASE - 11.5}a7 7 0 0 1 7 7" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round">
    <animateTransform attributeName="transform" type="rotate" from="0 {cx:.1f} {BASE - 4.5}" to="360 {cx:.1f} {BASE - 4.5}" dur="1.2s" repeatCount="indefinite"/>
  </path>
  <animate attributeName="opacity" values="1;.35;1" dur="1.6s" repeatCount="indefinite"/>
</g>
<text x="{x0:.1f}" y="{BASE}" font-family="{MONO}" font-size="{SIZE}" textLength="{tl:.0f}" lengthAdjust="spacing"><tspan class="l">{t(label)}</tspan><tspan class="d" font-weight="700">{t(date)}</tspan></text>
</svg>
"""


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else "checkpoint.svg"
    svg = render(dt.datetime.now(BRT).date())
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"ok {out} ({len(svg.encode()) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
