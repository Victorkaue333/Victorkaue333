"""Gera assets/typing.svg: linha abaixo do hero que digita e apaga frases,
com prompt "~ $" e cursor laranja piscando.

Uso (local; o SVG é estático, só regerar se mudar uma frase):
    python scripts/typing.py

Tudo em SMIL (o GitHub não roda JS em SVG). Cada frase é recortada por um
<rect> cuja largura avança um caractere por vez; a fonte mono com textLength
fixo deixa a largura de cada caractere previsível. Sem animação, aparece a
primeira frase inteira. Só biblioteca padrão.
"""
import os
from xml.sax.saxutils import escape

from activity import ACCENT, MONO

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PHRASES = [
    "Backend com Python, Django e FastAPI",
    "APIs REST pensadas para durar",
    "Do modelo de dados ao deploy em produção",
    "Sistemas web que resolvem problema de negócio",
]
PROMPT = "~ $ "

W, H = 840, 48
SIZE = 20
SPACING = 1
ADV = SIZE * .6 + SPACING  # avanço de um caractere mono
BASE = 31
TYPE, ERASE, HOLD, GAP = .07, .025, 1.8, .4  # segundos


def timeline() -> list[tuple[float, int, int]]:
    """(instante, frase, caracteres visíveis) a cada passo do ciclo."""
    t, steps = 0.0, []
    for i, p in enumerate(PHRASES):
        for n in range(1, len(p) + 1):
            steps.append((t, i, n))
            t += TYPE
        t += HOLD
        for n in range(len(p) - 1, -1, -1):
            steps.append((t, i, n))
            t += ERASE
        t += GAP
    return [(s / t, i, n) for s, i, n in steps], t


def text(x: float, s: str, cls: str, extra: str = "") -> str:
    tl = len(s) * ADV - SPACING
    return (f'<text x="{x:.1f}" y="{BASE}" class="{cls}" textLength="{tl:.1f}" '
            f'lengthAdjust="spacingAndGlyphs"{extra}>{escape(s)}</text>')


def render() -> str:
    steps, dur = timeline()
    longest = max(map(len, PHRASES))
    x0 = (W - (len(PROMPT) + longest) * ADV) / 2
    xt = x0 + len(PROMPT) * ADV
    assert x0 > 0, "frase longa demais para a largura"
    keys = ";".join(f"{k:.4f}" for k, _, _ in steps)

    def anim(attr: str, values: list[float]) -> str:
        vals = ";".join(f"{v:.1f}" for v in values)
        return (f'<animate attributeName="{attr}" dur="{dur:.2f}s" repeatCount="indefinite" '
                f'calcMode="discrete" keyTimes="{keys}" values="{vals}"/>')

    clips, lines = [], []
    for i, p in enumerate(PHRASES):
        width = len(p) * ADV if i == 0 else 0  # estado sem animação: 1ª frase inteira
        clips.append(f'<clipPath id="p{i}"><rect x="{xt:.1f}" y="0" width="{width:.1f}" height="{H}">'
                     + anim("width", [n * ADV if j == i else 0 for _, j, n in steps])
                     + "</rect></clipPath>")
        lines.append(text(xt, p, "t", f' clip-path="url(#p{i})"'))
    cursor = (f'<rect x="{xt + len(PHRASES[0]) * ADV + 2:.1f}" y="{BASE - SIZE * .78:.1f}" width="3" height="{SIZE:.0f}" fill="{ACCENT}">'
              + anim("x", [xt + n * ADV + 2 for _, _, n in steps])
              + '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/></rect>')
    label = " · ".join(PHRASES)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}" font-family="{MONO}" font-size="{SIZE}">
<title>{escape(label)}</title>
<defs>{"".join(clips)}</defs>
<style>
.t {{ fill: #ffffff; }} .p {{ fill: #808080; }}
@media (prefers-color-scheme: light) {{ .t {{ fill: #1f2328; }} .p {{ fill: #8c959f; }} }}
</style>
{text(x0, PROMPT.strip(), "p")}
{"".join(lines)}
{cursor}
</svg>
"""


if __name__ == "__main__":
    path = os.path.join(ROOT, "assets", "typing.svg")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(render())
    print(path)
