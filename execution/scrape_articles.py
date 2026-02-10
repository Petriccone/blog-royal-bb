"""
Scraper de artigos usando Article Scraper (RapidAPI).

Fluxo:
- descobre URLs de artigos nos sites configurados em `sources_config.py`
- para cada URL nova, chama o endpoint Article Scraper
- salva o conteúdo bruto no SQLite via `execution.utils.storage`
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List

import requests
from bs4 import BeautifulSoup  # type: ignore[import]
from dotenv import load_dotenv

from execution.sources_config import SOURCES, SourceConfig
from execution.utils import storage


ARTICLE_SCRAPER_URL = "https://article-scraper5.p.rapidapi.com/urltextextract"


def _init_env() -> None:
    load_dotenv()


def _get_rapidapi_key() -> str:
    key = os.getenv("ARTICLE_SCRAPER_API_KEY")
    if not key:
        raise RuntimeError(
            "ARTICLE_SCRAPER_API_KEY não definido no .env. "
            "Adicione sua chave RapidAPI para Article Scraper."
        )
    return key


def _full_url(source: SourceConfig, href: str) -> str:
    href = href.strip()
    if href.startswith("http://") or href.startswith("https://"):
        return href
    # trata caminhos relativos
    base = source.base_url.rstrip("/")
    if href.startswith("/"):
        return f"{base}{href}"
    return f"{base}/{href}"


def discover_article_urls(source: SourceConfig) -> List[str]:
    """
    Faz uma descoberta simples de links de artigos em páginas de listagem.
    Critérios atuais:
    - href começa com base_url OU é relativo
    - evita links com '#', parâmetros muito longos ou seções óbvias de navegação
    """
    urls: List[str] = []
    session = requests.Session()
    for path in source.list_paths:
        page_url = _full_url(source, path)
        try:
            resp = session.get(page_url, timeout=20)
            resp.raise_for_status()
        except Exception:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if not href or href.startswith("#"):
                continue
            full = _full_url(source, href)
            # heurísticas bem simples para filtrar links de posts
            if any(x in full for x in ["/202", "/20", "/blog/"]):
                if full not in urls:
                    urls.append(full)

    # limita por execução
    return urls[: source.max_articles_per_run]


def scrape_article(url: str, rapidapi_key: str) -> dict:
    """
    Chama Article Scraper para extrair texto de um único artigo.
    """
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "article-scraper5.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key,
    }
    payload = {"url": url}

    resp = requests.post(ARTICLE_SCRAPER_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data


def run() -> None:
    """
    Ponto de entrada principal para scraping.
    Pode ser chamado diretamente ou via script orquestrador.
    """
    _init_env()
    rapidapi_key = _get_rapidapi_key()
    storage.init_db()

    total_new = 0

    for source in SOURCES:
        urls = discover_article_urls(source)
        for url in urls:
            try:
                data = scrape_article(url, rapidapi_key)
            except Exception as exc:
                # registra artigo com falha para futura inspeção se desejado
                article_id = storage.upsert_raw_article(
                    source=source.id,
                    original_url=url,
                    title=None,
                    raw_text=f"ERRO AO SCRAPEAR: {exc}",
                    language=None,
                )
                storage.mark_article_failed(article_id, f"scrape_error: {exc}")
                continue

            title = data.get("title") or data.get("headline")
            text = (
                data.get("text")
                or data.get("content")
                or data.get("article_text")
                or ""
            )
            language = data.get("language")

            if not text:
                # se não há texto útil, marca como falha
                article_id = storage.upsert_raw_article(
                    source=source.id,
                    original_url=url,
                    title=title,
                    raw_text="",
                    language=language,
                )
                storage.mark_article_failed(article_id, "empty_text_from_article_scraper")
                continue

            article_id = storage.upsert_raw_article(
                source=source.id,
                original_url=url,
                title=title,
                raw_text=text,
                language=language,
            )
            # se já existia, upsert_raw_article apenas retorna o id; contamos novos
            total_new += 1

    print(f"[scrape_articles] Execução concluída em {datetime.now(timezone.utc).isoformat()}Z")
    print(f"[scrape_articles] Novos artigos (incluindo possíveis duplicatas ignoradas): {total_new}")


if __name__ == "__main__":
    run()

