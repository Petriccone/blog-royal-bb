"""
Agente mediador: coordena writer_agent, seo_agent e reviewer_agent.

Fluxo:
- Recebe um artigo bruto (texto + metadados)
- Chama writer_agent para gerar uma versão reescrita
- Chama seo_agent para otimizar o artigo para SEO (sem perder responsabilidade técnica)
- Chama reviewer_agent para aprovar/reprovar a versão já otimizada
- Em caso de reprovação, usa o feedback para orientar uma nova versão (até N tentativas)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from execution.agents import writer_agent, reviewer_agent, seo_agent


@dataclass
class MediatorParams:
    raw_text: str
    original_title: Optional[str]
    original_source: str
    language: Optional[str]
    max_attempts: int = 3


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ponto de entrada do mediador.

    Espera:
    - raw_text
    - original_title
    - original_source
    - language
    - max_attempts (opcional, default=3)
    """
    mp = MediatorParams(
        raw_text=str(params.get("raw_text", "")),
        original_title=params.get("original_title"),
        original_source=str(params.get("original_source", "desconhecida")),
        language=params.get("language"),
        max_attempts=int(params.get("max_attempts", 3)),
    )

    history: List[Dict[str, Any]] = []
    last_writer_output: Optional[Dict[str, Any]] = None
    last_seo_output: Optional[Dict[str, Any]] = None
    last_reviewer_output: Optional[Dict[str, Any]] = None

    for attempt in range(1, mp.max_attempts + 1):
        writer_input: Dict[str, Any] = {
            "raw_text": mp.raw_text,
            "original_title": mp.original_title,
            "original_source": mp.original_source,
            "language": mp.language,
        }

        # Se houver feedback do revisor anterior, passamos como contexto adicional.
        if last_reviewer_output:
            writer_input["reviewer_feedback"] = {
                "reasons": last_reviewer_output.get("reasons"),
                "suggestions": last_reviewer_output.get("suggestions"),
                "severity": last_reviewer_output.get("severity"),
            }

        writer_result = writer_agent.run(writer_input)
        last_writer_output = writer_result

        # Passo intermediário: agente SEO otimiza título, resumo, keywords e estrutura.
        seo_input: Dict[str, Any] = {
            "new_title": writer_result.get("new_title"),
            "summary": writer_result.get("summary"),
            "content_markdown": writer_result.get("content_markdown"),
            "keywords": writer_result.get("keywords"),
        }
        seo_result = seo_agent.run(seo_input)
        last_seo_output = seo_result

        review_input: Dict[str, Any] = {
            "new_title": seo_result.get("new_title"),
            "summary": seo_result.get("summary"),
            "content_markdown": seo_result.get("content_markdown"),
            "keywords": seo_result.get("keywords"),
            "original_source": mp.original_source,
        }
        reviewer_result = reviewer_agent.run(review_input)
        last_reviewer_output = reviewer_result

        iteration_record = {
            "attempt": attempt,
            "writer": writer_result,
            "seo": seo_result,
            "reviewer": reviewer_result,
        }
        history.append(iteration_record)

        if reviewer_result.get("approved"):
            return {
                "ok": True,
                "approved": True,
                "attempts": attempt,
                "final_article": seo_result,
                "review": reviewer_result,
                "history": history,
            }

    # Se chegou aqui, não foi aprovado em nenhuma tentativa
    return {
        "ok": True,
        "approved": False,
        "attempts": mp.max_attempts,
        "final_article": last_seo_output or last_writer_output,
        "review": last_reviewer_output,
        "history": history,
    }


if __name__ == "__main__":
    demo = run(
        {
            "raw_text": "A água é essencial para a vida...",
            "original_title": "Teste mediador",
            "original_source": "demo",
            "language": "pt",
        }
    )
    print(demo["approved"], "em", demo["attempts"], "tentativas")

