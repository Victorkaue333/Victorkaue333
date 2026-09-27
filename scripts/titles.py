"""Gera os títulos de seção do README (assets/titles/*.svg), no estilo do
cabeçalho dos cards de projeto: número laranja, linha fina e nome em mono
caixa alta. A linha se desenha uma vez ao carregar.

Uso (local; os SVGs são estáticos, só regerar se mudar uma seção):
    python scripts/titles.py

Fundo transparente: o nome troca de cor pelo prefers-color-scheme para
funcionar nos temas claro e escuro do GitHub. Só biblioteca padrão.
"""
import os
from xml.sax.saxutils import escape

from activity import ACCENT, MONO

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# (arquivo, número, nome); número com ponto = subtítulo, desenhado menor
SECTIONS = [
    ("sobre-mim", "01", "Sobre mim"),
    ("foco", "01.1", "No que eu foco"),
    ("stack", "02", "Stack principal"),
    ("stack-outras", "02.1", "Também trabalho com"),
    ("projetos", "03", "Projetos pessoais em destaque"),
    ("estatisticas", "04", "Estatísticas GitHub"),
]

# ~largura real do README no GitHub: sem width no <img>, fica 1:1 e só encolhe em tela estreita
W = 840
SIZES = {  # nível: (altura, linha de base, fonte do número, fonte do nome)
    1: (64, 42, 30, 26),
    2: (52, 34, 22, 20),
}
GAP = 24


def title(num: str, label: str) -> str:
    H, base, num_size, label_size = SIZES[2 if "." in num else 1]
    char = label_size * .6 + 4  # avanço mono (.6em) + letter-spacing; textLength fixa a largura
    text = label.upper()
    tl = len(text) * char - 4
    x1 = len(num) * (num_size * .6 + 4) + GAP
    x2 = W - tl - GAP
    line_y = base - label_size * .36
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{num} — {escape(label)}" font-family="{MONO}">
<title>{num} — {escape(label)}</title>
<style>
.n {{ fill: {ACCENT}; }} .t {{ fill: #ffffff; }} .r {{ stroke: #333333; }}
@media (prefers-color-scheme: light) {{ .t {{ fill: #1f2328; }} .r {{ stroke: #d0d7de; }} }}
.r {{ stroke-dasharray: {x2 - x1:.0f}; stroke-dashoffset: {x2 - x1:.0f}; animation: draw .9s cubic-bezier(.2,.8,.2,1) .15s forwards; }}
@keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
@media (prefers-reduced-motion: reduce) {{ .r {{ stroke-dashoffset: 0; animation: none; }} }}
</style>
<text class="n" x="2" y="{base}" font-size="{num_size}" font-weight="700" letter-spacing="4">{num}</text>
<line class="r" x1="{x1:.0f}" y1="{line_y:.1f}" x2="{x2:.0f}" y2="{line_y:.1f}" stroke-width="1.5"/>
<text class="t" x="{W - 2}" y="{base}" text-anchor="end" font-size="{label_size}" font-weight="700" textLength="{tl:.0f}" lengthAdjust="spacing">{escape(text)}</text>
</svg>
"""


def main() -> None:
    out_dir = os.path.join(ROOT, "assets", "titles")
    os.makedirs(out_dir, exist_ok=True)
    for slug, num, label in SECTIONS:
        with open(os.path.join(out_dir, f"{slug}.svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(title(num, label))
        print(f"ok assets/titles/{slug}.svg")


if __name__ == "__main__":
    main()
