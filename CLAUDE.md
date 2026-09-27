# CLAUDE.md

README de perfil do GitHub de **Victor Kauê** (`Victorkaue333`), dev back-end (Python, Django, FastAPI). Todo o conteúdo é em **português (PT-BR)**.

## Regras de git

- **Nunca** adicionar o Claude como co-autor: nada de `Co-Authored-By: Claude ...` em commits.
- Nenhuma linha de atribuição ao Claude ("Generated with Claude Code" etc.) em commits nem em PRs.
- Só commitar ou dar push quando o Victor pedir.

## Estrutura

- `README.md` — o perfil. Seções: hero, badges, `whoami` (retrato + wordmark), sobre mim, stack, projetos em destaque, `./contributions.sh` (heatmap + card de atividade), estatísticas, contato.
- `assets/` — SVGs **estáticos**, versionados na `main`:
  - `hero.svg`, `footer.svg` — feitos à mão. O hero (1200×360) é **só a imagem**, sem texto, ocupando o card de borda a borda: `images/images.jpg` (mãos da Criação de Adão, 351×144) é recortado nas linhas das mãos, ampliado com Lanczos + nitidez leve e embutido em base64, com `mix-blend-mode: screen` para o preto sumir no fundo. Se trocar a foto, é preciso gerar e embutir de novo.
  - `portrait.svg`, `wordmark.svg` — gerados por `scripts/whoami.py`.
  - `projects/*.svg` — cards de projeto, 520×680, feitos à mão seguindo o mesmo template.
- `scripts/` — geradores em Python:
  - `activity.py` — card de atividade; define os tokens de cor/fonte que os outros scripts importam. Só biblioteca padrão.
  - `heatmap.py` — heatmap de contribuições animado (versões clara e escura). Só biblioteca padrão; reaproveita `fetch()` do `activity.py`.
  - `whoami.py` — retrato ASCII (a partir do avatar do GitHub) + wordmark 3D "VK". Roda **local**, precisa de `scripts/requirements.txt`.
- `.github/workflows/snake.yml` — o nome é histórico (a cobra foi removida). Roda todo dia e em push na `main`: gera heatmap, card de atividade e cards do github-readme-stats e publica na branch **`output`**. O README aponta para `raw.githubusercontent.com/Victorkaue333/Victorkaue333/output/...`.

## Design system

Tema escuro do portfólio (victor-kaue.vercel.app). Usar sempre estes tokens (definidos em `scripts/activity.py`):

- Fundo `#050505`, superfície `#1a1a1a`, borda `#222222`
- Destaque laranja `#ff7a00` (suave `#ff9933`, escuro `#cc6200`)
- Texto `#ffffff` / `#cccccc` / `#808080`, apagado `#4d4d4d` / `#333333`
- Sans: `system-ui, -apple-system, 'Segoe UI', ...`; mono: `ui-monospace, SFMono-Regular, ...`
- Rótulos em mono, caixa alta, com `letter-spacing`. Um único elemento em laranja por bloco para marcar o destaque.

Headers no estilo terminal (`<h3><code>victor@github ~ $ ...</code></h3>`) nas seções animadas.

## Restrições dos SVGs no GitHub

- O GitHub mostra SVG dentro de `<img>`: **sem JS**, sem recursos externos. SMIL e animação CSS funcionam.
- Tudo o que anima precisa ser pré-renderizado (o wordmark é um flipbook de quadros alternados por opacidade).
- Para tema claro/escuro, gerar dois arquivos e escolher com `<picture>` + `prefers-color-scheme` (como no heatmap).
- `portrait.svg` e `wordmark.svg` aparecem lado a lado com a mesma altura. `whoami.py` calcula a altura do wordmark a partir de `PORTRAIT_SHOW`/`WORDMARK_SHOW` (400/400), que precisam bater com os `width` do README. Larguras iguais deixam as duas imagens com a mesma proporção, e assim as alturas continuam iguais quando a tabela encolhe numa tela estreita.

## Comandos

```bash
# retrato + wordmark (só quando a foto ou o texto mudarem)
pip install -r scripts/requirements.txt
python scripts/whoami.py [foto]          # sem argumento, usa o avatar do GitHub

# heatmap / card de atividade (normalmente só no Actions; precisam de token)
GITHUB_LOGIN=Victorkaue333 GITHUB_TOKEN=... python scripts/heatmap.py claro.svg escuro.svg
GITHUB_LOGIN=Victorkaue333 GITHUB_TOKEN=... python scripts/activity.py saida.svg
```

- A fonte do wordmark é Century Gothic Bold (`GOTHICB.TTF`, só Windows). Em outro SO, usar `WORDMARK_FONT=<caminho .ttf>`.
- Sem `rembg`: o recorte do retrato usa GrabCut do OpenCV.
- Para conferir um SVG visualmente: screenshot com Edge headless (`msedge --headless=new --screenshot=...`). Como as animações não avançam no screenshot, congele o estado final antes de capturar.

## Projetos em destaque

1. **Sertão Conecta**: o repositório é **privado**, então o card aponta para a produção (<https://sertaoconecta.floresta.ifsertao-pe.edu.br>).
2. **SuplaStock**: <https://github.com/Victorkaue333/SuplaStock>
3. **AgendeAqui**: <https://github.com/Victorkaue333/AgendeAqui>

Clones locais ficam em `C:\Users\Victor Alves\Documents\GitHub\VICTORKAUE\`, que é a fonte para stack e descrições.
