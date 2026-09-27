"""Gera os títulos de seção do README (assets/titles/*.svg): nome em mono
caixa alta, centralizado entre duas linhas finas que somem nas bordas
(──── ESTATÍSTICAS GITHUB ────). As linhas crescem do título para fora uma
vez ao carregar.

Uso (local; os SVGs são estáticos, só regerar se mudar uma seção):
    python scripts/titles.py

Fundo transparente: o nome troca de cor pelo prefers-color-scheme para
funcionar nos temas claro e escuro do GitHub. Só biblioteca padrão.
"""
import os
from xml.sax.saxutils import escape

from activity import MONO

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# (arquivo, nível, nome); nível 2 = subtítulo, desenhado menor
SECTIONS = [
    ("sobre-mim", 1, "Sobre mim"),
    ("foco", 2, "No que eu foco"),
    ("stack", 1, "Stack principal"),
    ("stack-outras", 2, "Também trabalho com"),
    ("projetos", 1, "Projetos pessoais em destaque"),
    ("projetos-corporativos", 1, "Projetos corporativos em destaque"),
    ("estatisticas", 1, "Estatísticas GitHub"),
]

# ~largura real do README no GitHub: sem width no <img>, fica 1:1 e só encolhe em tela estreita
W = 840
SIZES = {  # nível: (altura, linha de base, fonte do nome)
    1: (64, 42, 26),
    2: (52, 34, 20),
}
GAP = 22  # entre o título e as linhas


def title(level: int, label: str) -> str:
    H, base, label_size = SIZES[level]
    text = label.upper()
    # textLength fixa a largura (avanço mono .6em + letter-spacing), então a
    # centralização não depende da fonte do sistema
    tl = len(text) * (label_size * .6 + 4) - 4
    x0 = (W - tl) / 2
    left, right = x0 - GAP, x0 + tl + GAP
    line_y = base - label_size * .36
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}" font-family="{MONO}">
<title>{escape(label)}</title>
<defs>
  <linearGradient id="gl" gradientUnits="userSpaceOnUse" x1="0" x2="{left:.0f}" y1="0" y2="0"><stop offset="0" class="s0"/><stop offset="1" class="s1"/></linearGradient>
  <linearGradient id="gr" gradientUnits="userSpaceOnUse" x1="{right:.0f}" x2="{W}" y1="0" y2="0"><stop offset="0" class="s1"/><stop offset="1" class="s0"/></linearGradient>
</defs>
<style>
.t {{ fill: #ffffff; }}
.s0 {{ stop-color: #808080; stop-opacity: 0; }} .s1 {{ stop-color: #808080; stop-opacity: .9; }}
@media (prefers-color-scheme: light) {{ .t {{ fill: #1f2328; }} .s0, .s1 {{ stop-color: #8c959f; }} }}
.r {{ stroke-dasharray: {left:.0f}; animation: grow .9s cubic-bezier(.2,.8,.2,1) .15s backwards; }}
@keyframes grow {{ from {{ stroke-dashoffset: {left:.0f}; }} }}
@media (prefers-reduced-motion: reduce) {{ .r {{ animation: none; }} }}
</style>
<line class="r" x1="{left:.0f}" y1="{line_y:.1f}" x2="0" y2="{line_y:.1f}" stroke="url(#gl)" stroke-width="1.5"/>
<line class="r" x1="{right:.0f}" y1="{line_y:.1f}" x2="{W}" y2="{line_y:.1f}" stroke="url(#gr)" stroke-width="1.5"/>
<text class="t" x="{x0:.1f}" y="{base}" font-size="{label_size}" font-weight="700" textLength="{tl:.0f}" lengthAdjust="spacing">{escape(text)}</text>
</svg>
"""


def main() -> None:
    out_dir = os.path.join(ROOT, "assets", "titles")
    os.makedirs(out_dir, exist_ok=True)
    for slug, level, label in SECTIONS:
        with open(os.path.join(out_dir, f"{slug}.svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(title(level, label))
        print(f"ok assets/titles/{slug}.svg")


if __name__ == "__main__":
    main()
