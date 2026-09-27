"""Gera o par de janelas de terminal da seção whoami do README:

  assets/portrait.svg  retrato em ASCII que "digita" linha a linha e congela
  assets/wordmark.svg  iniciais extrudadas em 3D, rasterizadas em ASCII, balançando

Uso (local; os SVGs são estáticos, só regerar se a foto ou o texto mudar):
    pip install -r scripts/requirements.txt
    python scripts/whoami.py [foto]

Sem foto, baixa o avatar do GitHub. Dentro de <img> o GitHub roda SMIL mas nunca
JS, então tudo é pré-renderizado: o retrato é um clip animado por linha e o
wordmark é um flipbook de quadros alternados por opacidade.
Técnica adaptada de github.com/AVIVASHISHTA29/AVIVASHISHTA29.
"""
import io
import math
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from activity import ACCENT, BG, BORDER, FAINT, MONO, MUTED, TEXT2, TEXT3

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOGIN = "Victorkaue333"
NAME = "Victor Kauê"
USER = "victor"  # usuário do prompt nas janelas
WORD = os.environ.get("WORDMARK_TEXT", "VK")
FONT = os.environ.get("WORDMARK_FONT", "GOTHICB.TTF")  # Century Gothic Bold (Windows)

# largura de exibição no README; a altura do wordmark é derivada destas para as
# duas janelas ficarem com a mesma altura lado a lado. iguais = mesma proporção,
# então as alturas continuam batendo quando a tabela encolhe em telas estreitas
PORTRAIT_SHOW, WORDMARK_SHOW = 400, 400

PAD = 20
BAR_H = 30
STATUS_H = 30


def window(w: float, h: float, title: str, label: str, body: str) -> str:
    dots = "".join(f'<circle cx="{PAD + i * 16}" cy="{BAR_H / 2:.0f}" r="5" fill="{c}"/>'
                   for i, c in enumerate((ACCENT, MUTED, FAINT)))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" '
        f'role="img" aria-label="{escape(label)}" font-family="{MONO}">'
        f'<title>{escape(label)}</title>'
        f'<rect width="{w:.0f}" height="{h:.0f}" rx="12" fill="{BG}"/>'
        f'<line x1="0" y1="{BAR_H}" x2="{w:.0f}" y2="{BAR_H}" stroke="{BORDER}"/>{dots}'
        f'<text x="{w / 2:.0f}" y="{BAR_H / 2 + 4:.0f}" fill="{TEXT2}" font-size="12" text-anchor="middle">{escape(title)}</text>'
        f'{body}'
        f'<rect x=".5" y=".5" width="{w - 1:.0f}" height="{h - 1:.0f}" rx="12" fill="none" stroke="{BORDER}"/>'
        '</svg>\n'
    )


def save(name: str, svg: str) -> None:
    out = os.path.join(ROOT, "assets", name)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"ok assets/{name} ({len(svg.encode()) / 1024:.1f} KB)")


# ------------------------------------------------------------------- retrato
P_COLS, P_ROWS = 100, 53
P_CW, P_CH = 8, 15
P_RAMP = " .`:-=+*cs#%@"  # claro/esparso -> escuro/denso; o espaço apaga o fundo
GAMMA = 1.18  # >1 clareia os meios-tons: o rosto cai nos caracteres esparsos
WHITE_FLOOR = 0.80  # acima disso vira espaço
ROW_DUR = 0.11  # cada linha digita nesse tempo, logo depois da anterior


def load_photo(path: str | None) -> Image.Image:
    if path:
        return Image.open(path).convert("RGB")
    with urllib.request.urlopen(f"https://github.com/{LOGIN}.png?size=460", timeout=30) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


def prep(img: Image.Image) -> np.ndarray:
    """Recorta no aspecto da arte, isola a pessoa (GrabCut) e sobe o contraste
    local (CLAHE). Devolve luminância 0–1 com o fundo em branco."""
    ratio = P_COLS * P_CW / (P_ROWS * P_CH)
    w, h = img.size
    if w / h > ratio:
        cw = round(h * ratio)
        img = img.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
    else:
        img = img.crop((0, 0, w, round(w / ratio)))  # corta embaixo: a cabeça fica
    rgb = np.array(img)
    h, w = rgb.shape[:2]

    # semente: faixa central e metade de baixo (ombros chegam na borda) são provável
    # pessoa; rosto e peito são pessoa; cantos de cima são fundo
    seed = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    seed[int(h * .08):, int(w * .12):int(w * .88)] = cv2.GC_PR_FGD
    seed[int(h * .6):, :] = cv2.GC_PR_FGD
    seed[int(h * .3):, int(w * .35):int(w * .65)] = cv2.GC_FGD
    corner = int(min(w, h) * .12)
    seed[:corner, :corner] = seed[:corner, -corner:] = cv2.GC_BGD
    bg_model, fg_model = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(rgb, seed, None, bg_model, fg_model, 6, cv2.GC_INIT_WITH_MASK)
    person = np.isin(seed, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.float32)
    person = cv2.GaussianBlur(person, (0, 0), 1.5)  # borda suave, sem halo

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)
    lum = gray.astype(np.float32) * person + 255 * (1 - person)
    lum = cv2.resize(lum, (P_COLS, P_ROWS), interpolation=cv2.INTER_AREA)
    return np.clip(lum / 255, 0, 1) ** GAMMA


def ascii_rows(lum: np.ndarray) -> list[str]:
    idx = np.rint((1 - lum) * (len(P_RAMP) - 1)).astype(int)
    idx[lum >= WHITE_FLOOR] = 0
    return ["".join(P_RAMP[i] for i in row) for row in idx]


def portrait(rows: list[str]) -> tuple[str, float]:
    art_w = P_COLS * P_CW
    W = art_w + 2 * PAD
    H = BAR_H + P_ROWS * P_CH + STATUS_H + PAD
    top = BAR_H + PAD * .35
    body = []
    for r, line in enumerate(rows):
        y = top + r * P_CH
        begin = r * ROW_DUR
        body.append(
            f'<clipPath id="r{r}"><rect x="{PAD}" y="{y:.1f}" height="{P_CH}" width="0">'
            f'<animate attributeName="width" to="{art_w}" begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
            f'<text clip-path="url(#r{r})" xml:space="preserve" x="{PAD}" y="{y + P_CH * .74:.1f}" fill="{TEXT3}" '
            f'font-size="{P_CH * .86:.1f}" textLength="{art_w}" lengthAdjust="spacing">{escape(line)}</text>'
            # cursor que corre na borda do texto enquanto a linha digita
            f'<rect y="{y + 1:.1f}" width="{P_CW}" height="{P_CH - 2}" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + art_w}" begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to=".85" begin="{begin:.2f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.2f}s"/></rect>'
        )

    line_y = BAR_H + P_ROWS * P_CH + PAD * .35
    status_y = line_y + 19
    prompt = f"{USER}@github:~$ whoami "
    cursor_x = PAD + len(prompt + NAME + " ") * 13 * .6  # 13px mono ≈ .6em por caractere
    body.append(
        f'<line x1="0" y1="{line_y:.1f}" x2="{W}" y2="{line_y:.1f}" stroke="{BORDER}"/>'
        f'<text x="{PAD}" y="{status_y:.1f}" fill="{TEXT2}" font-size="13">{escape(prompt)}'
        f'<tspan fill="{TEXT3}">{escape(NAME)}</tspan></text>'
        f'<rect x="{cursor_x:.1f}" y="{status_y - 12:.1f}" width="8" height="14" fill="{ACCENT}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" dur="1s" repeatCount="indefinite"/></rect>'
    )
    svg = window(W, H, f"{USER}@github: ~$ ./portrait.sh", f"{NAME} — retrato em ASCII", "".join(body))
    return svg, H * PORTRAIT_SHOW / W


# ------------------------------------------------------------------ wordmark
W_COLS = 50
W_CW, W_CH = 9.0, 15.5
W_RAMP = " .`:-=+*csS#%@"  # escuro/esparso -> claro/denso; índice 0 é vazio
MASK_H = 300  # altura do glifo rasterizado, em px: define a densidade de pontos
TRACKING = .14  # espaço extra entre letras (em): os vãos precisam sobreviver à extrusão
DEPTH = .34  # profundidade da extrusão, fração da altura do glifo
TILT = math.radians(4)  # inclinação fixa em X para o topo aparecer; mais que isso desalinha a base
CAM, FOCAL = 6.0, 4.15  # câmera afastada + lente longa: as letras não encolhem ao girar
FIT = .92  # fração da largura que a pose mais larga ocupa
# luz quase no eixo da câmera: faces densas, paredes mais apagadas. esse contraste é o 3D
LIGHT = np.array([-.15, -.45, -1.0]) / np.linalg.norm([-.15, -.45, -1.0])
AMBIENT, FOG, FOG_SPAN = .22, .34, .55
REST, SWING = math.radians(-13), math.radians(11)  # pose de repouso 3/4 e amplitude do balanço
FRAMES, LOOP, REVEAL = 20, 5.0, 1.6


def shell() -> tuple[np.ndarray, np.ndarray]:
    """Pontos e normais da superfície do texto extrudado (tampas + paredes)."""
    font = ImageFont.truetype(FONT, MASK_H)
    _, top, _, bottom = font.getbbox(WORD)
    track = round(TRACKING * MASK_H)
    width = round(sum(font.getlength(ch) for ch in WORD) + track * (len(WORD) - 1)) + 8
    img = Image.new("L", (width, bottom - top + 8), 0)
    draw, pen = ImageDraw.Draw(img), 4.0
    for ch in WORD:  # letra a letra, para aplicar o tracking
        draw.text((pen, 4 - top), ch, font=font, fill=255)
        pen += font.getlength(ch) + track
    mask = np.array(img) > 127
    ys, xs = np.nonzero(mask.any(1))[0], np.nonzero(mask.any(0))[0]
    mask = mask[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
    h, w = mask.shape
    depth = max(4, round(h * DEPTH))

    cy, cx = np.nonzero(mask)
    # a tampa da frente fica um pouco à frente de z=0, onde as paredes começam: sem isso
    # as duas empatam no z-buffer e a face da letra sai riscada com o tom da parede
    pts = [np.stack([cx, cy, np.full(len(cx), -.6)], 1), np.stack([cx, cy, np.full(len(cx), depth)], 1)]
    nrm = [np.tile([0., 0., -1.], (len(cx), 1)), np.tile([0., 0., 1.], (len(cx), 1))]

    pad = np.pad(mask, 1)
    right, left = ~pad[1:-1, 2:], ~pad[1:-1, :-2]
    down, up = ~pad[2:, 1:-1], ~pad[:-2, 1:-1]
    ey, ex = np.nonzero(mask & (right | left | down | up))
    n = np.stack([right[ey, ex] * 1. - left[ey, ex], down[ey, ex] * 1. - up[ey, ex], np.zeros(len(ex))], 1)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    for z in np.linspace(0, depth, max(3, depth // 2)):
        pts.append(np.stack([ex, ey, np.full(len(ex), z)], 1))
        nrm.append(n)

    P = np.concatenate(pts).astype(np.float32)
    P -= [w / 2, h / 2, depth / 2]
    return P / w, np.concatenate(nrm).astype(np.float32)  # 1.0 = largura do texto


def project(P: np.ndarray, N: np.ndarray, yaw: float):
    c, s = math.cos(yaw), math.sin(yaw)
    ct, st = math.cos(TILT), math.sin(TILT)
    M = np.array([[1, 0, 0], [0, ct, -st], [0, st, ct]]) @ np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    p, n = P @ M.T.astype(np.float32), N @ M.T.astype(np.float32)
    visible = n[:, 2] < 0  # câmera em -z: só normais apontando para ela
    p, n = p[visible], n[visible]
    z = p[:, 2] + CAM
    light = AMBIENT + (1 - AMBIENT) * np.clip(n @ LIGHT, 0, 1)
    light *= 1 - FOG * (np.clip((z - CAM) / FOG_SPAN, -1, 1) + 1) / 2  # a ponta mais longe escurece
    shade = np.clip(np.rint(light * (len(W_RAMP) - 1)), 1, len(W_RAMP) - 1).astype(int)
    return p[:, 0] * FOCAL / z, p[:, 1] * FOCAL / z, z, shade


def wordmark(height: float) -> str:
    P, N = shell()
    frames = [project(P, N, REST + SWING * math.sin(2 * math.pi * i / FRAMES)) for i in range(FRAMES)]

    art_w = W_COLS * W_CW
    W = art_w + 2 * PAD
    rows = int((height - BAR_H - PAD) // W_CH)
    art_top = BAR_H + (height - BAR_H - rows * W_CH) / 2 - PAD * .2

    # uma escala e um centro para todos os quadros, senão o texto "respira"
    xs = np.concatenate([f[0] for f in frames])
    ys = np.concatenate([f[1] for f in frames])
    aspect = W_CW / W_CH
    scale = FIT * (W_COLS - 1) / (xs.max() - xs.min())
    cx = (W_COLS - 1) / 2 - (xs.min() + xs.max()) / 2 * scale
    cy = (rows - 1) / 2 - (ys.min() + ys.max()) / 2 * scale * aspect

    def raster(frame) -> list[str]:
        x, y, z, shade = frame
        col = np.rint(cx + x * scale).astype(int)
        row = np.rint(cy + y * scale * aspect).astype(int)
        ok = (col >= 0) & (col < W_COLS) & (row >= 0) & (row < rows)
        col, row, z, shade = col[ok], row[ok], z[ok], shade[ok]
        grid = np.zeros((rows, W_COLS), int)
        order = np.argsort(-z)  # do fundo para a frente: o ponto mais perto sobrescreve
        grid[row[order], col[order]] = shade[order]
        return ["".join(W_RAMP[i] for i in r) for r in grid]

    def group(lines: list[str], extra: str = "", anim: str = "") -> str:
        out = []
        for r, line in enumerate(lines):
            text = line.rstrip()
            if not text.strip():
                continue
            lead = len(text) - len(text.lstrip())
            out.append(f'<text xml:space="preserve" x="{PAD + lead * W_CW:.1f}" y="{art_top + r * W_CH + W_CH * .78:.1f}" '
                       f'textLength="{(len(text) - lead) * W_CW:.1f}" lengthAdjust="spacing">{escape(text[lead:])}</text>')
        return f'<g{extra}>{"".join(out)}{anim}</g>'

    grids = [raster(f) for f in frames]
    art_h = rows * W_CH
    body = [f'<g fill="{ACCENT}" font-size="{W_CH * .92:.1f}">']
    # entrada: a pose de repouso aparece da esquerda para a direita atrás de uma barra
    body.append(
        f'<clipPath id="wipe"><rect x="{PAD}" y="{art_top:.1f}" height="{art_h:.1f}" width="0">'
        f'<animate attributeName="width" to="{art_w:.0f}" dur="{REVEAL}s" fill="freeze"/></rect></clipPath>'
        + group(grids[0], ' clip-path="url(#wipe)"', f'<set attributeName="opacity" to="0" begin="{REVEAL}s"/>')
        + f'<rect x="{PAD}" y="{art_top + 2:.1f}" width="{W_CW * 1.6:.1f}" height="{art_h - 4:.1f}" opacity=".16">'
        f'<animate attributeName="x" to="{PAD + art_w:.0f}" dur="{REVEAL}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0" begin="{REVEAL}s"/></rect>'
    )
    # flipbook: cada quadro é dono de uma fatia 1/n do loop; discrete = corte seco, sem fade
    for i, lines in enumerate(grids):
        values, times = ("1;0", f"0;{1 / FRAMES:.4f}") if i == 0 else ("0;1;0", f"0;{i / FRAMES:.4f};{(i + 1) / FRAMES:.4f}")
        body.append(group(lines, ' opacity="0"',
                          f'<animate attributeName="opacity" calcMode="discrete" values="{values}" keyTimes="{times}" '
                          f'dur="{LOOP}s" begin="{REVEAL}s" repeatCount="indefinite"/>'))
    body.append("</g>")
    return window(W, height, f"{USER}@github: ~$ ./wordmark.sh --3d", f"{WORD} — wordmark 3D em ASCII", "".join(body))


def main() -> None:
    svg, shown_h = portrait(ascii_rows(prep(load_photo(sys.argv[1] if len(sys.argv) > 1 else None))))
    save("portrait.svg", svg)
    # mesma altura exibida: altura_real = altura_exibida * largura_real / largura_exibida
    save("wordmark.svg", wordmark(shown_h * (W_COLS * W_CW + 2 * PAD) / WORDMARK_SHOW))


if __name__ == "__main__":
    main()
