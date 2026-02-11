"""
Agente buscador de conteúdo: pesquisa na web sobre água, saúde, filtros e temas relacionados.

Objetivo:
- Receber um tema ou título de artigo
- Fazer buscas (ex.: DuckDuckGo) sobre água e saúde
- Devolver trechos e fontes para enriquecer o texto do writer_agent
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

# Busca via DuckDuckGo (pacote ddgs) — gratuito, sem API key
try:
    from ddgs import DDGS
    _DDGS_AVAILABLE = True
except ImportError:
    _DDGS_AVAILABLE = False


@dataclass
class SearcherParams:
    topic: str  # tema ou título do artigo
    max_results: int = 5
    extra_query: str = "água saúde qualidade hidratação"


def _search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Executa busca e retorna lista de dicts com title, href, body."""
    if not _DDGS_AVAILABLE:
        return []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results, region="br-pt"))
        return results
    except Exception:
        return []


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pesquisa conteúdo sobre o tema, com foco em água e saúde.

    Espera em params:
    - topic: str (título ou tema do artigo)
    - max_results: int (opcional, default 5)
    - extra_query: str (opcional, termos fixos da busca)

    Retorna:
    - ok: bool
    - research_context: str (trechos formatados para o writer usar como contexto)
    - snippets: list (lista de dicts com title, href, body)
    """
    topic = str(params.get("topic", "")).strip()
    max_results = int(params.get("max_results", 5))
    extra = str(params.get("extra_query", "água saúde qualidade hidratação")).strip()

    if not topic:
        return {"ok": True, "research_context": "", "snippets": []}

    # Duas buscas: uma com o tema, outra mais geral sobre água e saúde
    query1 = f"{topic} {extra}"
    query2 = "qualidade da água filtros hidratação saúde"

    snippets: List[Dict[str, Any]] = []
    seen_bodies: set[str] = set()

    for q in [query1, query2]:
        results = _search(q, max_results=max_results)
        for r in results:
            body = (r.get("body") or "").strip()
            if body and body not in seen_bodies and len(body) > 30:
                seen_bodies.add(body)
                snippets.append({
                    "title": r.get("title") or "",
                    "href": r.get("href") or "",
                    "body": body[:500],
                })
        if len(snippets) >= 8:
            break

    # Formata contexto para o writer: trechos úteis sem URLs no meio do texto
    lines = []
    for i, s in enumerate(snippets[:6], 1):
        lines.append(f"[Fonte {i}] {s['body']}")
    research_context = "\n\n".join(lines) if lines else ""

    print(f"[content_searcher] Tema: {topic[:60]}... | {len(snippets)} trechos para o writer", flush=True)

    return {
        "ok": True,
        "research_context": research_context,
        "snippets": snippets,
    }


if __name__ == "__main__":
    r = run({"topic": "hidratação no verão filtros de água"})
    print("Snippets:", len(r["snippets"]))
    print("Contexto (início):", (r["research_context"] or "")[:400])
