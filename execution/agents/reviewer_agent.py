"""
Agente revisor: última barreira de qualidade antes da publicação.

Ele recebe o artigo gerado pelo writer e decide se está aprovado ou não,
retornando feedback estruturado.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from execution.utils import llm


@dataclass
class ReviewParams:
    title: str
    summary: str
    content_markdown: str
    keywords: List[str]
    original_source: str


def _build_system_prompt() -> str:
    return (
        "Você é um revisor técnico extremamente rigoroso, com nível de PhD em filtros de água, "
        "qualidade da água, tratamento de água e saúde pública.\n\n"
        "Sua função é atuar como ÚLTIMA BARREIRA antes que um artigo seja publicado em um blog.\n"
        "Você deve avaliar clareza, coerência, responsabilidade técnica e foco em água/saúde.\n"
        "Você precisa ser conservador: se tiver dúvida razoável sobre a qualidade do texto, REPROVE.\n"
        "Evite qualquer afirmação médica forte sem contexto; prefira linguagem cuidadosa.\n"
    )


def _build_user_prompt(params: ReviewParams) -> str:
    keywords_str = ", ".join(params.keywords) if params.keywords else "nenhuma"

    return (
        f"Fonte original do conteúdo base: {params.original_source}\n\n"
        "ARTIGO GERADO PELO AGENTE ESCRITOR:\n"
        "---------------------------------\n"
        f"Título: {params.title}\n\n"
        f"Resumo: {params.summary}\n\n"
        f"Palavras-chave: {keywords_str}\n\n"
        "Conteúdo em Markdown:\n"
        f"{params.content_markdown}\n"
        "---------------------------------\n\n"
        "Sua tarefa:\n"
        "- Analise se o artigo é claro, coerente, tecnicamente responsável e focado em água/saúde.\n"
        "- Verifique se há promessas médicas exageradas ou afirmações sem base.\n"
        "- Tente identificar se o artigo parece cópia direta de algum texto (mesma estrutura repetitiva etc.).\n\n"
        "Responda ESTRITAMENTE em JSON válido, SEM nenhum texto antes ou depois, com o seguinte formato:\n"
        "{\n"
        '  \"approved\": true | false,\n'
        '  \"reasons\": [\"lista de razões principais\"],\n'
        '  \"suggestions\": [\"melhorias específicas\"],\n'
        '  \"severity\": \"low\" | \"medium\" | \"high\"\n'
        "}\n"
    )


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ponto de entrada do revisor.
    Espera:
    - new_title
    - summary
    - content_markdown
    - keywords (lista)
    - original_source
    """
    review_params = ReviewParams(
        title=str(params.get("new_title", "")),
        summary=str(params.get("summary", "")),
        content_markdown=str(params.get("content_markdown", "")),
        keywords=list(params.get("keywords", [])),
        original_source=str(params.get("original_source", "desconhecida")),
    )

    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": _build_user_prompt(review_params)},
    ]

    raw = llm.chat_completion_text(messages, temperature=0.2, max_tokens=512)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # fallback defensivo
        data = {
            "approved": False,
            "reasons": ["Resposta do modelo não estava em JSON válido."],
            "suggestions": [raw[:500]],
            "severity": "high",
        }

    approved = bool(data.get("approved"))
    reasons = data.get("reasons") or []
    suggestions = data.get("suggestions") or []
    severity = data.get("severity") or "medium"

    return {
        "ok": True,
        "approved": approved,
        "reasons": reasons,
        "suggestions": suggestions,
        "severity": severity,
        "model_raw_output": raw,
    }


if __name__ == "__main__":
    demo = run(
        {
            "new_title": "Título de exemplo",
            "summary": "Resumo de exemplo.",
            "content_markdown": "## Seção\nConteúdo de teste sobre água.",
            "keywords": ["água", "saúde"],
            "original_source": "demo",
        }
    )
    print(demo)

