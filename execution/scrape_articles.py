"""
Scraper de artigos a partir de URLs.

Por padrão usa Trafilatura (gratuito, sem API key): baixa a página e extrai
o texto principal + metadados. Opcionalmente pode usar RapidAPI (ARTICLE_SCRAPER_API_KEY
e USE_RAPIDAPI=1) como fallback.

Fluxo:
- descobre URLs nos sites configurados em `sources_config.py`
- para cada URL, extrai título e texto (Trafilatura ou RapidAPI)
- salva no SQLite via `execution.utils.storage`
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup  # type: ignore[import]
from dotenv import load_dotenv
from trafilatura import extract
from trafilatura.downloads import fetch_url

from execution.sources_config import SOURCES, SourceConfig
from execution.utils import storage


ARTICLE_SCRAPER_URL = "https://article-scraper5.p.rapidapi.com/urltextextract"


def _init_env() -> None:
    load_dotenv()


def _use_rapidapi() -> bool:
    return os.getenv("USE_RAPIDAPI", "").strip().lower() in ("1", "true", "yes")


def _get_rapidapi_key() -> str | None:
    return (os.getenv("ARTICLE_SCRAPER_API_KEY") or "").strip() or None


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
            # só links do mesmo domínio/base
            if not full.startswith(source.base_url.rstrip("/")) and not full.startswith(source.base_url):
                continue
            parsed = urlparse(full)
            path = (parsed.path or "").strip("/")
            segments = [s for s in path.split("/") if s]
            # aceita: URLs com data (/2024/01/...), /blog/..., ou path com segmento que parece slug
            is_article_like = (
                any(x in full for x in ["/202", "/20", "/blog/"])
                or len(segments) >= 2
                or (len(segments) == 1 and len(segments[0]) > 8 and "-" in segments[0])
            )
            if is_article_like and full not in urls:
                urls.append(full)

    # limita por execução
    return urls[: source.max_articles_per_run]


def scrape_article_trafilatura(url: str) -> Dict[str, Any]:
    """
    Extrai título e texto principal de uma URL com Trafilatura (gratuito, sem API key).
    Retorna dict com title, text, url; language se disponível.
    """
    downloaded = fetch_url(url)
    if not downloaded:
        raise ValueError("Falha ao baixar a página")
    result = extract(
        downloaded,
        output_format="json",
        with_metadata=True,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
        url=url,
    )
    if not result:
        raise ValueError("Trafilatura não extraiu conteúdo")
    data = json.loads(result) if isinstance(result, str) else result
    title = data.get("title") or data.get("headline") or ""
    text = data.get("text") or data.get("content") or ""
    return {
        "title": title,
        "url": url,
        "text": text,
        "language": data.get("language"),
    }


def scrape_article_rapidapi(url: str, rapidapi_key: str) -> Dict[str, Any]:
    """
    Chama Article Scraper (RapidAPI). Requer ARTICLE_SCRAPER_API_KEY.
    """
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "article-scraper5.p.rapidapi.com",
        "x-rapidapi-key": rapidapi_key,
    }
    resp = requests.post(
        ARTICLE_SCRAPER_URL, json={"url": url}, headers=headers, timeout=60
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "title": data.get("title") or data.get("headline") or "",
        "url": url,
        "text": (
            data.get("text")
            or data.get("content")
            or data.get("article_text")
            or ""
        ),
        "language": data.get("language"),
    }


def run() -> None:
    """
    Ponto de entrada principal para scraping.
    Usa Trafilatura (gratuito) por padrão. Para usar RapidAPI: USE_RAPIDAPI=1 e ARTICLE_SCRAPER_API_KEY.
    """
    _init_env()
    use_rapidapi = _use_rapidapi() and _get_rapidapi_key()
    if use_rapidapi:
        rapidapi_key = _get_rapidapi_key()
        print("[scrape_articles] Modo: RapidAPI (ARTICLE_SCRAPER_API_KEY)", flush=True)
    else:
        rapidapi_key = None
        print("[scrape_articles] Modo: Trafilatura (gratuito)", flush=True)
    storage.init_db()

    total_new = 0
    num_errors = 0
    num_empty = 0
    first_error: str | None = None
    delay = 3 if use_rapidapi else 1  # RapidAPI rate limit; Trafilatura: ser educado com os sites

    for source in SOURCES:
        urls = discover_article_urls(source)
        print(f"[scrape_articles] Fonte {source.id}: {len(urls)} URLs descobertas", flush=True)
        if not urls:
            continue
        for url in urls:
            time.sleep(delay)
            try:
                if use_rapidapi and rapidapi_key:
                    data = scrape_article_rapidapi(url, rapidapi_key)
                else:
                    data = scrape_article_trafilatura(url)
            except Exception as exc:
                num_errors += 1
                if first_error is None:
                    first_error = str(exc)
                article_id = storage.upsert_raw_article(
                    source=source.id,
                    original_url=url,
                    title=None,
                    raw_text=f"ERRO AO SCRAPEAR: {exc}",
                    language=None,
                )
                storage.mark_article_failed(article_id, f"scrape_error: {exc}")
                continue

            title = data.get("title") or ""
            text = data.get("text") or ""
            language = data.get("language")

            if not text:
                num_empty += 1
                article_id = storage.upsert_raw_article(
                    source=source.id,
                    original_url=url,
                    title=title,
                    raw_text="",
                    language=language,
                )
                storage.mark_article_failed(article_id, "empty_text_from_article_scraper")
                continue

            storage.upsert_raw_article(
                source=source.id,
                original_url=url,
                title=title,
                raw_text=text,
                language=language,
            )
            total_new += 1

    print(f"[scrape_articles] Execução concluída em {datetime.now(timezone.utc).isoformat()}Z", flush=True)
    print(f"[scrape_articles] Artigos processados nesta execução: {total_new}", flush=True)
    if num_errors or num_empty:
        print(f"[scrape_articles] URLs com erro: {num_errors}, texto vazio: {num_empty}", flush=True)
        if first_error:
            print(f"[scrape_articles] Exemplo de erro: {first_error[:200]}", flush=True)


if __name__ == "__main__":
    run()

