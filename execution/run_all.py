"""
Script orquestrador para rodar todo o workflow:
- Scraping de artigos
- Geração de posts + imagens

Use este script no agendador (Task Scheduler / cron) para rodar 4x por dia.
No Railway: o CRON deve chamar "python -m execution.run_all". O serviço principal
fica com start command "tail -f /dev/null" só para manter o ambiente; o que
realmente gera posts são as execuções agendadas do cron.
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime, timezone

from execution import scrape_articles
from execution import pipeline_generate_posts
from execution.utils import git_push


def main() -> None:
    print(f"[run_all] Início da execução em {datetime.now(timezone.utc).isoformat()}Z", flush=True)

    print("[run_all] Etapa 1: scraping de artigos...", flush=True)
    scrape_articles.run()
    print("[run_all] Etapa 1 concluída.", flush=True)

    print("[run_all] Etapa 2: geração de posts (até 4 artigos)...", flush=True)
    pipeline_generate_posts.run(
        {
            "review_mode": "lenient",
            "limit": 4,
            "status": "raw",
            "generate_images": True,
        }
    )
    print("[run_all] Etapa 2 concluída.", flush=True)

    print("[run_all] Etapa 3: push para GitHub (se PUSH_TO_GITHUB=1)...", flush=True)
    git_push.push_posts_to_github()
    print("[run_all] Etapa 3 concluída.", flush=True)

    print(f"[run_all] Fim da execução em {datetime.now(timezone.utc).isoformat()}Z", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[run_all] ERRO: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

