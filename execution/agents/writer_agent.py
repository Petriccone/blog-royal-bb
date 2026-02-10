"""
Agente escritor: reescreve artigos sobre água/saúde
com voz de especialista (PhD em filtros de água).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List

from execution.utils import llm


@dataclass
class WriterParams:
    raw_text: str
    original_title: str | None
    original_source: str
    language: str | None
    target_audience: str = "público leigo interessado em saúde e qualidade da água"


def _build_system_prompt() -> str:
    return (
        "Você é um redator especialista, com nível de PhD em temas de filtros de água, "
        "qualidade da água, saúde e hidratação. Sua função é reescrever artigos existentes "
        "criando textos ORIGINAIS, profundos, bem estruturados e tecnicamente responsáveis.\n\n"
        "Contexto de negócio:\n"
        "- Você escreve para um blog que apoia uma empresa brasileira chamada Royal B&B, "
        "especializada em soluções de filtragem de água (carcaças, refis, purificadores, "
        "torneiras com filtro, mídias filtrantes e sistemas de osmose reversa) — veja, por exemplo, "
        "as categorias de produtos presentes em `https://www.royalbeb.com.br/`.\n"
        "- O blog não é um catálogo de produtos; seu papel é educar o leitor sobre qualidade da água, "
        "benefícios da filtragem e escolhas conscientes, alinhado com o tipo de solução que a Royal B&B oferece.\n"
        "- Evite citar modelos específicos ou fazer reviews de produtos individuais, a menos que seja explicitamente solicitado; "
        "prefira falar em categorias (por exemplo, \"refis de polipropileno\", \"carcaças para filtros\", \"purificadores de parede\").\n\n"
        "Regras importantes:\n"
        "- NUNCA copie frases inteiras do texto original; mude estrutura, ordem e exemplos.\n"
        "- Explique conceitos de forma clara para leigos, mas com profundidade científica: "
        "discuta mecanismos fisiológicos, parâmetros de qualidade da água, tipos de contaminantes e tecnologias de filtração.\n"
        "- O texto final deve ter, no mínimo, 800 palavras (busque entre 800 e 1.300 palavras).\n"
        "- Evite qualquer promessa médica exagerada ou diagnóstico; use linguagem cuidadosa.\n"
        "- Conecte naturalmente o tema à importância de usar água filtrada de qualidade.\n"
        "- Use subtítulos organizando a leitura (seções lógicas), parágrafos relativamente curtos e listas quando fizer sentido.\n"
        "- Sempre que mencionar evidências científicas, faça isso de forma geral (\"estudos mostram\", "
        "\"pesquisas indicam\"), sem inventar nomes de autores, revistas ou números de referência específicos.\n"
        "- NÃO use citações numéricas do tipo [1], [2], [3] no texto final.\n"
        "- Escreva em português brasileiro, mesmo que o artigo original esteja em outro idioma.\n"
        "- No final, inclua um parágrafo de conclusão com um call-to-action suave relacionado a filtros de água.\n"
        "- NÃO mencione que o texto foi gerado por IA ou baseado em outro artigo.\n"
    )


def _build_user_prompt(params: WriterParams) -> str:
    lang_info = f"Idioma original detectado: {params.language}.\n" if params.language else ""
    title_info = f"Título original: {params.original_title}\n" if params.original_title else ""

    return (
        f"{lang_info}"
        f"{title_info}"
        f"Fonte original: {params.original_source}\n"
        f"Público-alvo: {params.target_audience}\n\n"
        "TEXTO ORIGINAL (NÃO COPIAR, APENAS USAR COMO REFERÊNCIA DE IDEIAS):\n"
        "-------------------------\n"
        f"{params.raw_text}\n"
        "-------------------------\n\n"
        "TAREFA:\n"
        "- Reescreva COMPLETAMENTE o artigo acima em português brasileiro.\n"
        "- Crie um novo título atraente, mas responsável.\n"
        "- Gere também um resumo curto (1 parágrafo) e uma lista de 5–10 palavras-chave de SEO relacionadas a água, filtros e saúde.\n"
        "- Garanta que o corpo do artigo tenha pelo menos 800 palavras e aprofunde conceitos técnicos de forma acessível.\n\n"
        "FORMATO DE RESPOSTA (IMPORTANTE – SIGA EXATAMENTE ESTE MODELO):\n"
        "TÍTULO:\n"
        "...\n\n"
        "RESUMO:\n"
        "...\n\n"
        "PALAVRAS-CHAVE:\n"
        "- palavra 1\n"
        "- palavra 2\n"
        "- ...\n\n"
        "CONTEÚDO:\n"
        "Escreva aqui o artigo completo em Markdown, usando subtítulos (##, ###) quando fizer sentido.\n"
    )


def _extract_sections(text: str) -> Dict[str, Any]:
    """
    Extrai seções TÍTULO, RESUMO, PALAVRAS-CHAVE, CONTEÚDO do texto plano.
    É tolerante a pequenas variações.
    """
    sections = {"title": "", "summary": "", "keywords": [], "content_markdown": ""}

    title_match = re.search(r"T[IÍ]TULO:\s*(.+)", text, flags=re.IGNORECASE)
    if title_match:
        sections["title"] = title_match.group(1).strip()

    summary_match = re.search(r"RESUMO:\s*(.+?)(?:\n{2,}|PALAVRAS-CHAVE:)", text, flags=re.IGNORECASE | re.DOTALL)
    if summary_match:
        sections["summary"] = summary_match.group(1).strip()

    keywords_match = re.search(
        r"PALAVRAS-CHAVE:\s*(.+?)(?:\n{2,}|CONTE[ÚU]DO:)", text, flags=re.IGNORECASE | re.DOTALL
    )
    keywords: List[str] = []
    if keywords_match:
        block = keywords_match.group(1)
        for line in block.splitlines():
            line = line.strip("-*• \t")
            if line:
                keywords.append(line.strip())
    sections["keywords"] = keywords

    content_match = re.search(r"CONTE[ÚU]DO:\s*(.+)$", text, flags=re.IGNORECASE | re.DOTALL)
    if content_match:
        sections["content_markdown"] = content_match.group(1).strip()

    return sections


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ponto de entrada do agente escritor.

    Espera um dict com:
    - raw_text (str)
    - original_title (str|None)
    - original_source (str)
    - language (str|None)
    - target_audience (opcional)
    """
    writer_params = WriterParams(
        raw_text=str(params.get("raw_text", "")),
        original_title=params.get("original_title"),
        original_source=str(params.get("original_source", "desconhecida")),
        language=params.get("language"),
        target_audience=params.get(
            "target_audience",
            "público leigo interessado em saúde e qualidade da água",
        ),
    )

    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": _build_user_prompt(writer_params)},
    ]

    content = llm.chat_completion_text(messages, temperature=0.65, max_tokens=None)
    sections = _extract_sections(content)

    return {
        "ok": True,
        "model_raw_output": content,
        "new_title": sections["title"],
        "summary": sections["summary"],
        "keywords": sections["keywords"],
        "content_markdown": sections["content_markdown"],
    }


if __name__ == "__main__":
    demo = run(
        {
            "raw_text": "A água é essencial para a vida...",
            "original_title": "Artigo de teste",
            "original_source": "demo",
            "language": "pt",
        }
    )
    print(demo["new_title"])

