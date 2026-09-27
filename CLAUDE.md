# CLAUDE.md

README de perfil do GitHub de **Victor Kauê** (`Victorkaue333`), dev back-end (Python, Django, FastAPI). Todo o conteúdo é em **português (PT-BR)**.

## Regras de git

- **Nunca** adicionar o Claude como co-autor: nada de `Co-Authored-By: Claude ...` em commits.
- Nenhuma linha de atribuição ao Claude ("Generated with Claude Code" etc.) em commits nem em PRs.
- Só commitar ou dar push quando o Victor pedir.
- Antes de commitar o README, confira se os blocos `whoami` e `./contributions.sh` estão lá. Edições fora daqui já os removeram várias vezes.

## Estrutura

- `README.md` — o perfil. Ordem: hero, badges, `whoami` (retrato + wordmark), Sobre mim (+ No que eu foco), Stack principal (+ Também trabalho com), Projetos pessoais em destaque (4 cards em grade 2 × 2), Projetos corporativos em destaque (3 em linha), Estatísticas GitHub (título → `./contributions.sh` com o heatmap → card de atividade → cards de stats e linguagens), frase do Cortella e rodapé com a foto do setup.
  - Os cards têm `width="270"`. Com 4 numa seção, um `<br/>` depois do 2º monta a grade 2 × 2, porque 4 em linha estouram a largura do README.
- `assets/` — SVGs **estáticos**, versionados na `main`:
  - `hero.svg` e `footer.svg` — banners de foto do **mesmo tamanho** (1200×404), gerados por `scripts/banners.py` a partir de `images/`. As fotos vão embutidas em base64 como WebP, com `mix-blend-mode: screen` para o preto sumir no fundo do card.
    - Hero: faixa das mãos da Criação de Adão (`images.webp`), de borda a borda, sem texto.
    - Rodapé: o setup inteiro (`ambiente-de-trabalho.webp`), encaixado pela altura e centralizado, com as bordas sumindo no fundo; o recorte vertical é `SETUP_ROWS`. Fica logo abaixo da frase do Cortella.
  - `portrait.svg`, `wordmark.svg` — gerados por `scripts/whoami.py`.
  - `contrib-heatmap.svg` — **gerado**: o workflow regera e commita todo dia. Não editar à mão.
  - `projects/*.svg` — cards de projeto, 520×680, feitos à mão seguindo o mesmo template.
  - `titles/*.svg` — títulos das seções, **sem numeração**, centralizados entre duas linhas que somem nas bordas (`──── ESTATÍSTICAS GITHUB ────`), nome em mono caixa alta. As linhas crescem do título para fora ao carregar, mas o estado final fica visível mesmo sem animação. Subtítulos (nível 2 em `SECTIONS`) saem menores. Os SVGs têm 840 px de largura e entram no README **sem** `width`, então ficam 1:1 no desktop e só encolhem em tela estreita. Gerados por `scripts/titles.py`: para mudar ou adicionar uma seção, edite a lista `SECTIONS` e rode o script de novo.
- `images/` — fotos-fonte em WebP (`images.webp` → hero, `ambiente-de-trabalho.webp` 1200×1200 → rodapé). O README não aponta para elas: só os banners gerados. Salve fotos novas como WebP e rode `scripts/banners.py`.
- `scripts/` — geradores em Python:
  - `activity.py` — card de atividade; define os tokens de cor/fonte que os outros scripts importam. Só biblioteca padrão.
  - `heatmap.py` — heatmap de contribuições animado → `assets/contrib-heatmap.svg`, um arquivo só com os dois temas (`@media prefers-color-scheme` dentro do SVG). Com token, busca via GraphQL (`fetch()` do `activity.py`) e salva o snapshot `data/contributions.json`; sem token, ou se a API falhar, redesenha a partir do snapshot. Só biblioteca padrão.
  - `whoami.py` — retrato ASCII (a partir do avatar do GitHub) + wordmark 3D "VK". Roda **local**, precisa de `scripts/requirements.txt`.
- `.github/workflows/snake.yml` — o nome é histórico (a cobra foi removida). Roda todo dia e em push na `main`:
  - regera o heatmap e **commita na `main`** (`assets/contrib-heatmap.svg` + `data/contributions.json`, mensagem com `[skip ci]`). Como o bot commita na `main`, é preciso dar pull antes de fazer push local;
  - gera o card de atividade e os cards do github-readme-stats e publica na branch **`output`**. O README aponta para `raw.githubusercontent.com/Victorkaue333/Victorkaue333/output/...`.

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
- Para tema claro/escuro, prefira um SVG só com `@media (prefers-color-scheme: light)` no `<style>`, como no heatmap. Assets versionados na `main` usam caminho relativo no README, que é mais confiável que URL raw de outra branch.
- `portrait.svg` e `wordmark.svg` aparecem lado a lado com a mesma altura. `whoami.py` calcula a altura do wordmark a partir de `PORTRAIT_SHOW`/`WORDMARK_SHOW` (400/400), que precisam bater com os `width` do README. Larguras iguais deixam as duas imagens com a mesma proporção, e assim as alturas continuam iguais quando a tabela encolhe numa tela estreita.

## Comandos

```bash
# retrato + wordmark (só quando a foto ou o texto mudarem)
pip install -r scripts/requirements.txt
python scripts/whoami.py [foto]          # sem argumento, usa o avatar do GitHub

# heatmap: sem token, redesenha a partir de data/contributions.json; com token, atualiza os dados
python scripts/heatmap.py
GITHUB_LOGIN=Victorkaue333 GITHUB_TOKEN=... python scripts/heatmap.py

# hero + rodapé (só quando trocar uma foto em images/)
python scripts/banners.py

# títulos das seções (só biblioteca padrão)
python scripts/titles.py

# card de atividade (precisa de token; normalmente só no Actions)
GITHUB_LOGIN=Victorkaue333 GITHUB_TOKEN=... python scripts/activity.py saida.svg
```

- A fonte do wordmark é Century Gothic Bold (`GOTHICB.TTF`, só Windows). Em outro SO, usar `WORDMARK_FONT=<caminho .ttf>`.
- Sem `rembg`: o recorte do retrato usa GrabCut do OpenCV.
- Para conferir um SVG visualmente: screenshot com Edge headless (`msedge --headless=new --screenshot=...`). Como as animações não avançam no screenshot, congele o estado final antes de capturar.

## Projetos pessoais em destaque

1. **Sertão Conecta**: o repositório é **privado**, então o card aponta para a produção (<https://sertaoconecta.floresta.ifsertao-pe.edu.br>).
2. **SuplaStock**: <https://github.com/Victorkaue333/SuplaStock>
3. **AgendeAqui**: <https://github.com/Victorkaue333/AgendeAqui>
4. **Portfólio Web**: <https://victor-kaue.vercel.app/> (repositório `Victorkaue333/my-portfolio-vk`: React, TypeScript, Vite, Tailwind, i18n em 4 idiomas). O painel do card reproduz o `developer.ts` da página Sobre.

Clones locais ficam em `C:\Users\Victor Alves\Documents\GitHub\VICTORKAUE\`, que é a fonte para stack e descrições.

## Projetos corporativos em destaque

Mesmo template dos cards pessoais. O cabeçalho mostra a empresa no lugar do repositório.

1. **Caji Agent** (Caji Solutions): <https://www.cajiagent.com/>. Clone em `GitHub\CajiSolutions\CajiAgent`.
2. **VA Suplementos** (VK Software, cliente): o repositório `vksoftware-infra/VA-Suplementos` é **privado**, então o card aponta para <https://victor-kaue.vercel.app/projetos>. Clone em `GitHub\VK SOFTWARE\VA-Suplementos`.
3. **NTIDI**: <https://www.ntidi.com.br/>. O estudo de caso está no portfólio, em `/projetos/ntidi`.
