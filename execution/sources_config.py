"""
Configuração das fontes de artigos sobre água/saúde.

Cada fonte define:
- base_url: URL base do blog
- list_paths: caminhos relativos para páginas de listagem (se vazio, usar a base_url)
- max_articles_per_run: limite de artigos novos por execução

O scraping de links é propositalmente simples (parse de <a href="...">)
e pode ser refinado conforme aprendermos mais sobre a estrutura dos sites.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class SourceConfig:
    id: str
    base_url: str
    list_paths: List[str]
    max_articles_per_run: int = 10


SOURCES: List[SourceConfig] = [
    SourceConfig(
        id="superfilter",
        base_url="https://blog.superfilter.com.br",
        list_paths=["/"],
        max_articles_per_run=8,
    ),
    SourceConfig(
        id="doctoragua",
        base_url="https://doctoragua.es",
        list_paths=["/blog/"],
        max_articles_per_run=8,
    ),
]

