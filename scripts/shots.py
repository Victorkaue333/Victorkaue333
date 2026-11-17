"""Troca o painel ilustrado do topo dos cards de projeto por um print real.

Para cada foto em images/projects/<slug>.(webp|png|jpg), embute o print no
painel de assets/projects/<slug>.svg (448×150, cortado em "cover" a partir do
topo da imagem). Cards sem foto ficam como estão. Pode rodar de novo à vontade.

Uso (local):
    pip install -r scripts/requirements.txt
    python scripts/shots.py
"""
import glob
import os
import re

from PIL import Image

from banners import ROOT, encode

X, Y, W, H = 36, 88, 448, 150
SCALE = 2  # nitidez em tela retina
# fundo do painel e contorno: o print entra entre os dois
PANEL = re.compile(r'(<rect x="36" y="88" width="448" height="150" rx="14" fill="#050505"/>)'
                   r'.*?'
                   r'(<rect x="36\.5" y="88\.5" width="447" height="149" rx="14" fill="none" stroke="#222222"/>)',
                   re.S)


def crop(img: Image.Image) -> Image.Image:
    w, h = W * SCALE, H * SCALE
    k = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    left = (img.width - w) // 2
    return img.crop((left, 0, left + w, h))  # topo da página é o que identifica o projeto


def main() -> None:
    for path in sorted(glob.glob(os.path.join(ROOT, "images", "projects", "*"))):
        slug, ext = os.path.splitext(os.path.basename(path))
        card = os.path.join(ROOT, "assets", "projects", f"{slug}.svg")
        if ext.lower() not in (".webp", ".png", ".jpg", ".jpeg") or not os.path.exists(card):
            print(f"ignorado: {path}")
            continue
        svg = open(card, encoding="utf-8").read()
        assert PANEL.search(svg), f"painel não encontrado em {card}"
        data = encode(crop(Image.open(path).convert("RGB")))
        shot = (f'<clipPath id="shot"><rect x="{X}" y="{Y}" width="{W}" height="{H}" rx="14"/></clipPath>'
                f'<image x="{X}" y="{Y}" width="{W}" height="{H}" clip-path="url(#shot)" '
                f'href="data:image/webp;base64,{data}"/>')
        svg = PANEL.sub(lambda m: m[1] + "\n" + shot + "\n" + m[2], svg, count=1)
        open(card, "w", encoding="utf-8", newline="\n").write(svg)
        print(f"ok: {slug}")


if __name__ == "__main__":
    main()
