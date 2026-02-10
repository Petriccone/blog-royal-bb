"""
Helper para chamadas de LLM usando a OpenRouter.

Sempre que precisarmos de um modelo de linguagem (writer, reviewer etc),
usamos esta função centralizada.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def _init_env() -> None:
    load_dotenv()


def _get_openrouter_key() -> str:
    _init_env()
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY não definido no .env. "
            "Configure-o com a sua chave sk-or-v1-..."
        )
    return key


def _get_openrouter_model() -> str:
    """
    Modelo padrão da OpenRouter.
    Pode ser sobrescrito via OPENROUTER_MODEL no .env.
    """
    model = os.getenv("OPENROUTER_MODEL")
    if model:
        return model
    # Usamos um alias genérico; o usuário pode customizar via env.
    return "openrouter/auto"


def chat_completion(
    messages: List[Dict[str, Any]],
    *,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Chama a API de chat da OpenRouter e retorna o JSON de resposta.
    """
    api_key = _get_openrouter_key()
    model = _get_openrouter_model()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    resp = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def chat_completion_text(
    messages: List[Dict[str, Any]],
    *,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Versão utilitária que já extrai o texto da primeira escolha.
    """
    data = chat_completion(
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"Resposta inesperada da OpenRouter: {json.dumps(data)[:1000]}") from exc

