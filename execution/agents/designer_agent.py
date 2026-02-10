"""
Agente designer: propõe diretrizes de design para o website do blog,
inspirado no visual do blog Doctor Agua.

Este agente não aplica o design diretamente, mas retorna um guia com:
- paleta de cores
- tipografia
- componentes principais (header, cards de posts, barra lateral, rodapé)
que podem ser usados na camada de frontend (Next.js).
"""

from __future__ import annotations

from typing import Any, Dict

from execution.utils import llm


def _build_system_prompt() -> str:
    return (
        "Você é um designer sênior de interfaces especializado em blogs para marcas de filtros de água, "
        "capaz de traduzir referências visuais em um design system claro.\n\n"
        "Contexto:\n"
        "- O cliente é a Royal B&B, empresa brasileira de soluções em filtragem de água "
        "(carcaças, refis, purificadores, torneiras, mídias filtrantes, sistemas de osmose), "
        "com visual limpo, profissional e forte uso de branco e tons de azul.\n"
        "- O site institucional da Royal B&B (por exemplo, páginas de categorias como "
        "\"Carcaças\", \"Refis\", \"Purificadores\" e \"Osmose\" em `https://www.royalbeb.com.br/`) "
        "usa muito espaço em branco, tipografia simples e menus horizontais claros.\n\n"
        "Seu objetivo é criar um guia de design para um blog sobre água, filtros de água e saúde "
        "que se pareça visualmente compatível com o site da Royal B&B, "
        "mantendo linguagem editorial (cards de artigos, sidebar, etc.) e sensação de confiança.\n"
    )


def _build_user_prompt() -> str:
    return (
        "Crie um guia de design para um website de blog chamado 'Blog Água & Saúde', "
        "que será usado como hub de conteúdo educativo para a Royal B&B.\n\n"
        "O visual do blog deve conversar com o site da Royal B&B: fundo predominantemente branco, "
        "barras de navegação limpas em tons de azul, botões com bordas arredondadas, "
        "tipografia sem serifa, foco em legibilidade e sensação de empresa de engenharia/confiabilidade.\n\n"
        "Forneça a resposta ESTRUTURADA em JSON, com os seguintes campos:\n"
        "{\n"
        '  \"palette\": {\n'
        '    \"primary\": \"#...\",\n'
        '    \"primaryDark\": \"#...\",\n'
        '    \"accent\": \"#...\",\n'
        '    \"background\": \"#...\",\n'
        '    \"surface\": \"#...\",\n'
        '    \"text\": \"#...\",\n'
        '    \"mutedText\": \"#...\"\n'
        "  },\n"
        '  \"typography\": {\n'
        '    \"fontFamily\": \"...\",\n'
        '    \"headingWeight\": 700,\n'
        '    \"bodyWeight\": 400\n'
        "  },\n"
        '  \"components\": {\n'
        '    \"header\": {\"description\": \"...\"},\n'
        '    \"postCard\": {\"description\": \"...\"},\n'
        '    \"postPage\": {\"description\": \"...\"},\n'
        '    \"sidebar\": {\"description\": \"...\"},\n'
        '    \"footer\": {\"description\": \"...\"}\n'
        "  }\n"
        "}\n"
        "Use cores e descrições adequadas a um blog moderno, limpo e confiável.\n"
    )


def run(params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Ponto de entrada do agente designer.
    Retorna um dicionário com a sugestão de design system.
    """
    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": _build_user_prompt()},
    ]
    raw = llm.chat_completion_text(messages, temperature=0.4, max_tokens=900)
    # Devolvemos o JSON em string; o chamador pode fazer json.loads se quiser.
    return {
        "ok": True,
        "design_spec_json": raw,
    }


if __name__ == "__main__":
    spec = run({})
    print(spec["design_spec_json"])

