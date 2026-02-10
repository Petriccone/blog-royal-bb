"""
Agente de design de prompts de imagem para posts do blog.

Objetivo:
- Ler título, resumo e conteúdo (Markdown) do artigo
- Entender o contexto e o ângulo principal
- Propor prompts coerentes para geração de imagem (capa e inline)

Regras importantes:
- NÃO mostrar produtos específicos, aparelhos, refis, marcas ou logotipos.
- Focar em cenas conceituais de água, saúde, pessoas, casas, natureza,
  copos de água, paisagens de água limpa, interiores neutros etc.
- Evitar close-ups de equipamentos de filtração ou embalagens de produto.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from execution.utils import llm


@dataclass
class PromptDesignerParams:
    title: str
    summary: str
    content: str


def _build_system_prompt() -> str:
    return (
        "Você é um designer sênior responsável por criar PROMPTS de imagem para um "
        "blog sobre água, filtros de água e saúde, ligado à empresa Royal B&B, que "
        "vende soluções como carcaças, refis, purificadores, torneiras com filtro, "
        "mídias filtrantes e sistemas de osmose reversa.\n\n"
        "Sua função NÃO é descrever layout de site, e sim sugerir textos curtos que serão "
        "usados em modelos de geração de imagem (como Fal / Midjourney / Stable Diffusion).\n\n"
        "Regras de estilo muito importantes:\n"
        "- NUNCA mostre produtos específicos, aparelhos, refis, carcaças, embalagens ou marcas visíveis.\n"
        "- Não mostrar purificadores, filtros, geladeiras ou qualquer produto identificável em close.\n"
        "- Foque em cenas conceituais que transmitam os benefícios das soluções de filtragem: água cristalina, "
        "pessoas se hidratando, famílias em casa, cozinhas e áreas de serviço limpas, detalhes abstratos de tubulações "
        "e cartuchos, paisagens de água limpa.\n"
        "- Estilo editorial premium, moderno, clean, adequado a um blog de saúde.\n"
        "- Cores predominantes: azuis limpos, brancos, verdes suaves.\n"
    )


def _build_user_prompt(p: PromptDesignerParams) -> str:
    return (
        "Use as informações a seguir para criar prompts de imagem para um artigo de blog.\n\n"
        f"Título do artigo: {p.title}\n"
        f"Resumo do artigo: {p.summary}\n\n"
        "Trecho do conteúdo (Markdown):\n"
        f"{p.content[:4000]}\n\n"
        "Gere a resposta ESTRITAMENTE em JSON com este formato:\n"
        "{\n"
        '  \"cover_prompt\": \"...\",\n'
        '  \"inline_prompt\": \"...\"\n'
        "}\n\n"
        "Onde:\n"
        "- cover_prompt: descrição visual para a IMAGEM DE CAPA do artigo, mais ampla e impactante.\n"
        "- inline_prompt: descrição visual para uma IMAGEM INLINE, mais simples, para aparecer no meio do texto.\n\n"
        "Requisitos dos prompts:\n"
        "- Escreva os prompts em português claro.\n"
        "- Não cite marcas, logotipos, rótulos ou modelos de aparelhos.\n"
        "- Não descreva close-ups de equipamentos ou refis; foque em água, pessoas, natureza e ambientes neutros.\n"
        "- Use entre 1 e 3 frases por prompt, no máximo ~220 caracteres.\n"
    )


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gera prompts de imagem (capa e inline) para um artigo.

    Espera em `params`:
    - title: str
    - summary: str
    - content: str (markdown ou texto)
    """
    p = PromptDesignerParams(
        title=str(params.get("title", "")),
        summary=str(params.get("summary", "")),
        content=str(params.get("content", "")),
    )

    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": _build_user_prompt(p)},
    ]

    raw = llm.chat_completion_text(messages, temperature=0.4, max_tokens=600)

    cover_prompt_fallback = (
        f"Imagem conceitual de água cristalina e bem-estar, inspirada em '{p.title}', "
        "sem mostrar produtos ou aparelhos, estilo editorial limpo em tons de azul e branco."
    )
    inline_prompt_fallback = (
        "Ilustração simples sobre qualidade da água e saúde, com foco em água limpa "
        "e pessoas se hidratando, sem produtos ou marcas."
    )

    cover_prompt = cover_prompt_fallback
    inline_prompt = inline_prompt_fallback

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            cp = str(data.get("cover_prompt") or "").strip()
            ip = str(data.get("inline_prompt") or "").strip()
            if cp:
                cover_prompt = cp
            if ip:
                inline_prompt = ip
    except Exception:
        # Em caso de erro de parsing, usamos os fallbacks.
        pass

    return {
        "ok": True,
        "cover_prompt": cover_prompt,
        "inline_prompt": inline_prompt,
        "raw_response": raw,
    }


if __name__ == "__main__":
    demo = run(
        {
            "title": "Exemplo de artigo sobre qualidade da água em casa",
            "summary": "Como a qualidade da água impacta a saúde da família.",
            "content": "Texto de exemplo sobre água, filtros e saúde.",
        }
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2))

