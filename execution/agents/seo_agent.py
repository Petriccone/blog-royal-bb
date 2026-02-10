"""
Agente SEO: otimiza título, resumo, palavras-chave e estrutura do artigo
para mecanismos de busca, mantendo foco em água, filtros de água e saúde.

Ele é chamado depois do writer_agent e antes do revisor técnico.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from execution.utils import llm


@dataclass
class SEOParams:
    title: str
    summary: str
    content_markdown: str
    keywords: List[str]


def _build_system_prompt() -> str:
    return (
        "Você é um especialista sênior em SEO para blogs de saúde e qualidade da água, "
        "com profundo conhecimento em filtros de água, tratamento da água e boas práticas de SEO.\n\n"
        "Seu objetivo é melhorar um artigo já escrito, sem mudar o sentido nem a responsabilidade técnica, "
        "otimizando-o para mecanismos de busca (Google etc.).\n\n"
        "Boas práticas obrigatórias:\n"
        "- Focar em palavras-chave relacionadas a água, filtros de água, purificação, qualidade da água, hidratação.\n"
        "- Criar um título chamativo, mas honesto, que contenha pelo menos uma palavra-chave importante.\n"
        "- Criar uma meta-descrição (usaremos como resumo) com 140–160 caracteres, clara e convidativa.\n"
        "- Ajustar as headings (H2, H3) para refletir bem os tópicos e conter variações de palavras-chave quando natural.\n"
        "- NÃO exagerar em repetições (evitar keyword stuffing).\n"
        "- Manter o texto em português brasileiro, fluido e natural.\n"
        "- Não adicionar promessas médicas nem afirmações sem base.\n"
    )


def _build_user_prompt(params: SEOParams) -> str:
    base_keywords = ", ".join(params.keywords) if params.keywords else "água, filtros de água, qualidade da água, hidratação"

    return (
        "ARTIGO ATUAL:\n"
        "---------------------------------\n"
        f"Título: {params.title}\n\n"
        f"Resumo atual: {params.summary}\n\n"
        f"Palavras-chave atuais: {base_keywords}\n\n"
        "Conteúdo em Markdown:\n"
        f"{params.content_markdown}\n"
        "---------------------------------\n\n"
        "TAREFA:\n"
        "- Otimizar o artigo para SEO, mantendo o tom e o conteúdo responsável.\n"
        "- Melhorar título, resumo/meta-descrição e lista de palavras-chave.\n"
        "- Você pode ajustar levemente a estrutura de headings (H2/H3) no corpo para refletir melhor as buscas.\n\n"
        "FORMATO DE RESPOSTA (SIGA EXATAMENTE):\n"
        "NOVO TÍTULO:\n"
        "...\n\n"
        "NOVA META-DESCRICAO:\n"
        "...\n\n"
        "NOVAS PALAVRAS-CHAVE:\n"
        "- palavra 1\n"
        "- palavra 2\n"
        "- ...\n\n"
        "CONTEUDO OTIMIZADO:\n"
        "Artigo completo em Markdown, já com headings ajustadas quando necessário.\n"
    )


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Espera:
    - new_title
    - summary
    - content_markdown
    - keywords (lista)
    """
    seo_params = SEOParams(
        title=str(params.get("new_title", "")),
        summary=str(params.get("summary", "")),
        content_markdown=str(params.get("content_markdown", "")),
        keywords=list(params.get("keywords") or []),
    )

    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": _build_user_prompt(seo_params)},
    ]

    content = llm.chat_completion_text(messages, temperature=0.55, max_tokens=None)

    # Extração simples por marcações
    def extract_block(marker: str) -> str:
        lower = content.lower()
        idx = lower.find(marker.lower())
        if idx == -1:
            return ""
        sub = content[idx + len(marker) :]
        # até o próximo marcador ou fim
        for next_marker in [
            "NOVA META-DESCRICAO:",
            "NOVAS PALAVRAS-CHAVE:",
            "CONTEUDO OTIMIZADO:",
        ]:
            nidx = sub.find(next_marker)
            if nidx != -1:
                sub = sub[:nidx]
        return sub.strip()

    new_title = extract_block("NOVO TÍTULO:")
    new_summary = extract_block("NOVA META-DESCRICAO:")
    keywords_block = extract_block("NOVAS PALAVRAS-CHAVE:")
    optimized_content = extract_block("CONTEUDO OTIMIZADO:")

    new_keywords: List[str] = []
    if keywords_block:
        for line in keywords_block.splitlines():
            line = line.strip("-*• \t")
            if line:
                new_keywords.append(line.strip())

    return {
        "ok": True,
        "new_title": new_title or seo_params.title,
        "summary": new_summary or seo_params.summary,
        "keywords": new_keywords or seo_params.keywords,
        "content_markdown": optimized_content or seo_params.content_markdown,
        "model_raw_output": content,
    }


if __name__ == "__main__":
    demo = run(
        {
            "new_title": "Exemplo de artigo sobre filtros de água",
            "summary": "Um texto explicando por que filtros de água são importantes para a saúde.",
            "content_markdown": "## Introdução\nConteúdo de exemplo sobre água e saúde.",
            "keywords": ["água", "filtros"],
        }
    )
    print(demo["new_title"])

