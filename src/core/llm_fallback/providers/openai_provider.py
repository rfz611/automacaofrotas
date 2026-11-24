"""
Provider OpenAI — usa Structured Outputs (`client.chat.completions.parse` com
`response_format=ExtracaoVeiculosResult`), o padrão mais consistente encontrado nas
buscas em 24/07/2026 entre a documentação e exemplos atuais do SDK Python da OpenAI.

Modelo: "gpt-5.6-terra" — atualiza o "GPT-4o" citado em IA.md. GPT-4o está claramente
descontinuado a esta altura (a família atual é a GPT-5.6: Sol/Terra/Luna); "Terra" é
descrito como o modelo balanceado para uso do dia a dia, papel equivalente ao que o
GPT-4o tinha quando IA.md foi escrito. Diferente do model name da Anthropic (que
confirmei via a skill de autoconhecimento de produto), não tenho como verificar este
com o mesmo grau de certeza — recomendo confirmar contra a documentação oficial da
OpenAI antes de ir para produção.

Cliente injetado no construtor pelo mesmo motivo do provider Anthropic: testável sem
API key nem chamada de rede real (e este sandbox nem alcança api.openai.com).
"""

from __future__ import annotations

from typing import Any

from ..prompts.extract_veiculos import SYSTEM_PROMPT, montar_prompt_usuario
from .base_provider import BaseLLMProvider, ExtracaoVeiculosResult, LLMProviderError

MODEL_PADRAO = "gpt-5.6-terra"


class OpenAIProvider(BaseLLMProvider):
    nome = "openai"

    def __init__(self, client: Any, model: str = MODEL_PADRAO):
        """`client` é uma instância de `openai.OpenAI()` (ou um dublê de teste com a
        mesma interface `.chat.completions.parse(...)`)."""
        self._client = client
        self._model = model

    def extrair(self, texto_pdf: str, seguradora_detectada: str | None) -> ExtracaoVeiculosResult:
        try:
            completion = self._client.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": montar_prompt_usuario(texto_pdf, seguradora_detectada)},
                ],
                response_format=ExtracaoVeiculosResult,
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMProviderError(f"OpenAI: falha ao chamar a API ({exc})") from exc

        escolha = completion.choices[0] if getattr(completion, "choices", None) else None
        parsed = getattr(escolha.message, "parsed", None) if escolha else None
        if parsed is None:
            motivo = getattr(escolha.message, "refusal", None) if escolha else None
            raise LLMProviderError(f"OpenAI: resposta sem parsed (refusal: {motivo})")
        return parsed
