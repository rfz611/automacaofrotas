"""
Provider Anthropic — usa Structured Outputs nativo (client.messages.parse com
output_format=ExtracaoVeiculosResult), disponível de forma geral na API da Anthropic
para modelos Claude 4.5+ (verificado em docs.claude.com/.../structured-outputs em
24/07/2026). O SDK deriva o JSON Schema diretamente do Pydantic e já devolve um
ExtracaoVeiculosResult validado em `response.parsed_output` — não precisamos fazer
json.loads/validação manual.

Modelo: "claude-sonnet-5" — atualiza o "Claude 3.5 Sonnet" citado em IA.md, que a esta
altura (jul/2026) muito provavelmente já foi descontinuado. Nomes de versão de modelo
envelhecem rápido; o papel pretendido (Claude de nível intermediário para extração) é
o que preservei, não o literal "3.5".

O cliente Anthropic é injetado no construtor (em vez de instanciado aqui dentro) para
permitir testar a lógica de prompt/parsing com um cliente falso, sem chamar a API de
verdade nem precisar de ANTHROPIC_API_KEY no ambiente de teste.
"""

from __future__ import annotations

from typing import Any

from ..prompts.extract_veiculos import SYSTEM_PROMPT, montar_prompt_usuario
from .base_provider import BaseLLMProvider, ExtracaoVeiculosResult, LLMProviderError

MODEL_PADRAO = "claude-sonnet-5"
MAX_TOKENS_PADRAO = 8192


class AnthropicProvider(BaseLLMProvider):
    nome = "anthropic"

    def __init__(self, client: Any, model: str = MODEL_PADRAO, max_tokens: int = MAX_TOKENS_PADRAO):
        """`client` é uma instância de `anthropic.Anthropic()` (ou um dublê de teste
        com a mesma interface `.messages.parse(...)`) — injetado no construtor para
        permitir testar sem precisar de ANTHROPIC_API_KEY nem chamar a API de verdade."""
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    def extrair(self, texto_pdf: str, seguradora_detectada: str | None) -> ExtracaoVeiculosResult:
        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=self._max_tokens,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": montar_prompt_usuario(texto_pdf, seguradora_detectada),
                    }
                ],
                output_format=ExtracaoVeiculosResult,
            )
        except Exception as exc:  # noqa: BLE001 — qualquer falha de rede/API vira LLMProviderError
            raise LLMProviderError(f"Anthropic: falha ao chamar a API ({exc})") from exc

        parsed = getattr(response, "parsed_output", None)
        if parsed is None:
            raise LLMProviderError("Anthropic: resposta sem parsed_output (possível refusal)")
        return parsed
