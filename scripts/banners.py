"""Gera os banners de foto do README, os dois do mesmo tamanho:

  assets/hero.svg    topo: mãos da Criação de Adão, de borda a borda
  assets/footer.svg  rodapé: ambiente de trabalho, inteiro e centralizado

Uso (local; só regerar se trocar uma foto em images/):
    pip install -r scripts/requirements.txt
    python scripts/banners.py

SVG em <img> não carrega arquivo externo, então a foto vai embutida em base64
(WebP). O mix-blend-mode: screen faz o preto das fotos sumir no fundo do card.
"""
import base64
import io
import os

import numpy as np
from PIL import Image

from activity import ACCENT, BG, BORDER

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W = 1200
# faixa do setup na foto (fração da altura): do topo dos monitores à borda da mesa
SETUP_ROWS = (.26, .91)
FADE_X, FADE_Y = .12, .1  # quanto das bordas da foto do rodapé some no fundo


def photo(name: str) -> Image.Image:
    return Image.open(os.path.join(ROOT, "images", name)).convert("RGB")


def encode(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "WEBP", quality=82, method=6)
    return base64.b64encode(buf.getvalue()).decode()


def card(H: int, label: str, defs: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label}">
<title>{label}</title>
<defs>
  <linearGradient id="b-bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0a0a0a"/>
    <stop offset=".55" stop-color="{BG}"/>
    <stop offset="1" stop-color="{BG}"/>
  </linearGradient>
  <radialGradient id="b-glow" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="{ACCENT}" stop-opacity=".07"/>
    <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
  </radialGradient>
  <pattern id="b-dots" width="24" height="24" patternUnits="userSpaceOnUse">
    <circle cx="12" cy="12" r="1" fill="{BORDER}"/>
  </pattern>
  <clipPath id="b-clip"><rect width="{W}" height="{H}" rx="18"/></clipPath>{defs}
</defs>
<g clip-path="url(#b-clip)">
<rect width="{W}" height="{H}" fill="url(#b-bg)"/>
<rect width="{W}" height="{H}" fill="url(#b-dots)" opacity=".7"/>
<rect width="{W}" height="{H}" fill="url(#b-glow)"/>
{body}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{BORDER}"/>
</svg>
"""


def hero() -> tuple[str, int]:
    """Faixa das mãos, com uma pequena margem, ocupando a largura toda."""
    src = photo("images.webp")
    sw, _ = src.size
    rows = np.nonzero((np.array(src.convert("L")) > 40).any(1))[0]
    top, bottom = rows.min(), rows.max()
    pad = round((bottom - top) * .06)
    crop = src.crop((0, top - pad, sw, bottom + pad))
    H = round(crop.height * W / sw)
    img = crop.resize((W, H), Image.LANCZOS)
    body = f'<image href="data:image/webp;base64,{encode(img)}" width="{W}" height="{H}" style="mix-blend-mode:screen"/>'
    return card(H, "Victor Kauê — mãos da Criação de Adão", "", body), H


def footer(H: int) -> str:
    """Setup inteiro, na altura do card e centralizado; as bordas somem no fundo."""
    src = photo("ambiente-de-trabalho.webp")
    sw, sh = src.size
    crop = src.crop((0, round(sh * SETUP_ROWS[0]), sw, round(sh * SETUP_ROWS[1])))
    w = round(crop.width * H / crop.height)
    x = (W - w) // 2
    img = crop.resize((w, H), Image.LANCZOS)

    def fade(axis: str, edge: float) -> str:
        x2, y2 = ("1", "0") if axis == "x" else ("0", "1")
        return (f'<linearGradient id="f-{axis}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
                f'<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                f'<stop offset="{edge}" stop-color="#fff"/><stop offset="{1 - edge}" stop-color="#fff"/>'
                f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')

    defs = (f"\n  {fade('x', FADE_X)}\n  {fade('y', FADE_Y)}"
            f'\n  <mask id="f-mx"><rect x="{x}" width="{w}" height="{H}" fill="url(#f-x)"/></mask>'
            f'\n  <mask id="f-my"><rect x="{x}" width="{w}" height="{H}" fill="url(#f-y)"/></mask>')
    # o blend fica no grupo: um <g> com mask vira grupo isolado, e o filho não enxergaria o fundo
    body = (f'<g mask="url(#f-my)" style="mix-blend-mode:screen"><image href="data:image/webp;base64,{encode(img)}" '
            f'x="{x}" width="{w}" height="{H}" mask="url(#f-mx)"/></g>')
    return card(H, "Ambiente de trabalho de Victor Kauê", defs, body)


def main() -> None:
    svg, H = hero()
    for name, content in (("hero.svg", svg), ("footer.svg", footer(H))):
        with open(os.path.join(ROOT, "assets", name), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"ok assets/{name} {W}x{H} ({len(content.encode()) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
