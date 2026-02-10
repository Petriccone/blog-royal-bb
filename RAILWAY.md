# Railway — Blog Royal B&B

## Serviço vs Cron

- **Serviço (Deploy)**  
  O start command é `tail -f /dev/null`. Esse processo fica **sempre rodando** (por isso aparece "Running" por horas). Ele **não** gera posts; só mantém o ambiente ativo para o cron.

- **Cron (execuções agendadas)**  
  O que realmente roda o pipeline é o **Cron**. No Railway: **Cron** → comando = `python -m execution.run_all`. Ele executa às 06:00, 12:00, 18:00 e 22:00 UTC. Cada execução aparece em **Cron Runs** com duração de alguns minutos (ex.: 3m, 5m).

Resumo: o "Running 1h" no painel é o **serviço** (tail), não o cron. Os logs do **cron** ficam em **Deploy Logs** do deploy disparado pelo cron (ou na execução correspondente em Cron Runs → View logs).

## Onde ver os logs do pipeline

1. **Cron Runs** → clique na execução desejada → **View logs** (ou Deploy Logs do deploy acionado pelo cron).
2. Nos logs você deve ver, em ordem:
   - `[run_all] Etapa 1: scraping...` → `Etapa 1 concluída.`
   - `[run_all] Etapa 2: geração de posts...`
   - `[pipeline_generate_posts] Artigos a processar: N`
   - Para cada artigo: `Processando artigo X (1/N)...`, `mediator_agent...`, `image_agent capa...`, `image_agent inline...`, `Artigo X concluído`
   - `[run_all] Etapa 2 concluída.` → Etapa 3 (push) → `Fim da execução`

Se os logs pararem no meio (ex.: após "Etapa 2: geração de posts" ou "image_agent capa..."), o processo travou ou foi encerrado nesse ponto (timeout, Fal/API lenta, memória). Use a última linha exibida para saber onde corrigir.

## Variáveis no Railway

Configure em **Variables** (e opcionalmente no `env.example`):

- `ARTICLE_SCRAPER_API_KEY`, `OPENROUTER_API_KEY`, `FAL_KEY` — obrigatórias para scraping e geração.
- `PUSH_TO_GITHUB=1` e `GITHUB_TOKEN` — para commit + push automático dos posts para o GitHub (e redeploy na Vercel).

## Comando do Cron

- **Schedule:** `0 6,12,18,22 * * *` (4x por dia em UTC).
- **Command:** `python -m execution.run_all`

Não use o start command do serviço para rodar o pipeline; use apenas o Cron com o comando acima.

## Erro "No such file or directory: 'git'"

O container padrão do Railway pode não ter o **Git** instalado. Sem ele, a Etapa 3 (push) falha.

**Solução:** o projeto inclui um **Dockerfile** que instala Git na imagem. No Railway:

1. No seu serviço, em **Settings**, confira se o **Builder** está usando o Dockerfile (deploy a partir do repositório com Dockerfile ativado).
2. Se o Railway usar Nixpacks em vez do Dockerfile: em **Settings** → **Build**, ative **Use Dockerfile** ou adicione um **nixpacks.toml** com a instalação de `git`. A forma mais garantida é usar o **Dockerfile** do repositório.

Depois do próximo deploy, o cron terá o comando `git` disponível e o push para o GitHub deve funcionar.
