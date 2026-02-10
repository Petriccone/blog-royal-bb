"""
Script orquestrador para rodar todo o workflow:
- Scraping de artigos
- Geração de posts + imagens

Use este script no agendador (Task Scheduler / cron) para rodar 4x por dia.
"""

from __future__ import annotations

from datetime import datetime

from execution import scrape_articles
from execution import pipeline_generate_posts


def main() -> None:
    print(f"[run_all] Início da execução em {datetime.utcnow().isoformat()}Z")

    print("[run_all] Etapa 1: scraping de artigos...")
    scrape_articles.run()

    print("[run_all] Etapa 2: geração de posts...")
    pipeline_generate_posts.run(
        {
            # modo mais permissivo para garantir publicação regular
            "review_mode": "lenient",
            "limit": 5,
            "status": "raw",
            "generate_images": True,
        }
    )

    print(f"[run_all] Fim da execução em {datetime.utcnow().isoformat()}Z")


if __name__ == "__main__":
    main()

