"""
Agente gerador de imagem para posts usando Fal API (nano-banana-pro).

Fluxo:
- Recebe título, resumo e conteúdo do artigo
- Gera um prompt descritivo alinhado ao tema água/saúde
- Chama o endpoint síncrono da Fal em `https://fal.run/fal-ai/nano-banana-pro`
- Retorna a URL da imagem gerada (campo `images[0].url`)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict

import requests
from dotenv import load_dotenv


FAL_SYNC_URL = "https://fal.run/fal-ai/nano-banana-pro"


def _init_env() -> None:
    load_dotenv()


def _get_fal_key() -> str:
    _init_env()
    key = os.getenv("FAL_KEY")
    if not key:
        raise RuntimeError(
            "FAL_KEY não definido no .env. "
            "Configure-o com o valor fornecido para a Fal API."
        )
    return key


@dataclass
class ImageParams:
    title: str
    summary: str
    kind: str = "cover"  # cover | inline
    main_topic: str = "filtros de água, saúde e hidratação"
    prompt_override: str | None = None


def _build_prompt(params: ImageParams) -> str:
    """
    Cria um prompt visual coerente com o conteúdo do artigo.

    Observação: evitamos imagens com PRODUTOS específicos (aparelhos,
    refis, embalagens), focando em cenas conceituais e contextos neutros.
    """
    if params.prompt_override:
        return params.prompt_override.strip()

    if params.kind == "inline":
        base = (
            f"Ilustração detalhada relacionada a {params.main_topic}, "
            f"com foco em um conceito específico do artigo '{params.title}' "
            "como qualidade da água, hidratação, bem-estar da família ou água limpa no dia a dia. "
            "Composição mais simples, adequada para aparecer no meio do texto, "
            "com fundo limpo, cores em tons de azul e branco, sem texto na imagem "
            "e sem mostrar produtos ou aparelhos específicos."
        )
    else:
        base = (
            f"Imagem de capa impactante para um artigo de blog sobre {params.main_topic}. "
            f"Inspirada no título '{params.title}'. "
            "Cenas limpas, sensação de pureza, foco em água cristalina, pessoas se hidratando, "
            "famílias em casa ou paisagens de natureza com água limpa, "
            "Estilo editorial premium para blog de saúde e qualidade de vida, em tons de azul, branco e verde suave, "
            "sem texto sobreposto e sem mostrar produtos, marcas ou aparelhos específicos."
        )
    return base


def _submit_to_fal(prompt: str, fal_key: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Key {fal_key}",
        "Content-Type": "application/json",
    }
    # O endpoint síncrono recebe diretamente o payload descrito na doc.
    payload = {
        "prompt": prompt,
        "num_images": 1,
        "aspect_ratio": "4:3",
        "output_format": "png",
        "resolution": "1K",
        "safety_tolerance": "4",
    }
    resp = requests.post(FAL_SYNC_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _get_result_from_fal(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Para o endpoint síncrono, o resultado já vem na própria resposta.
    Mantemos esta função apenas por compatibilidade de interface.
    """
    return response


def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ponto de entrada do agente de imagem.

    Espera:
    - title
    - summary
    - main_topic (opcional)
    - kind: "cover" | "inline"
    - prompt (opcional): se fornecido, é usado diretamente em vez de gerar via _build_prompt
    """
    fal_key = _get_fal_key()
    prompt_override = str(params.get("prompt") or "").strip() or None
    image_params = ImageParams(
        title=str(params.get("title", "")),
        summary=str(params.get("summary", "")),
        kind=str(params.get("kind", "cover")),
        main_topic=str(
            params.get(
                "main_topic",
                "filtros de água, saúde, qualidade da água e hidratação diária",
            )
        ),
        prompt_override=prompt_override,
    )

    prompt = _build_prompt(image_params)
    sync_resp = _submit_to_fal(prompt, fal_key)
    result = _get_result_from_fal(sync_resp)

    data = result
    images = data.get("images") or []
    image_url = None
    if images:
        image_url = images[0].get("url")

    return {
        "ok": True,
        "prompt": prompt,
        "request_id": None,
        "raw_submit_response": sync_resp,
        "raw_result": result,
        "image_url": image_url,
    }


if __name__ == "__main__":
    print("Este módulo deve ser usado a partir do pipeline principal.")

