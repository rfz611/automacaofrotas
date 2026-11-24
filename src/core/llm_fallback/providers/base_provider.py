"""
Interface comum dos providers de LLM (Anthropic/OpenAI) + o schema-container que
"trava" o structured output exatamente no VeiculoSchema da Fase 1 — um PDF tem N
veículos, então o container é só {"veiculos": [VeiculoSchema, ...]}.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from schemas.veiculo_schema import VeiculoSchema


class ExtracaoVeiculosResult(BaseModel):
    """Formato que travamos no structured output de ambos os providers — string exata
    dos 17 campos por veículo, herdada de VeiculoSchema (Fase 1), sem alteração."""

    veiculos: list[VeiculoSchema] = Field(default_factory=list)


class LLMProviderError(Exception):
    """Levantada quando o provider de LLM falha (erro de rede, resposta vazia, etc).
    O llm_service decide se tenta o próximo provider ou propaga."""


class BaseLLMProvider(ABC):
    """Cada provider concreto sabe montar a chamada específica da sua API e devolver
    um ExtracaoVeiculosResult — nunca um VeiculoSchema malformado (a própria validação
    do Pydantic no schema garante isso; um campo que o LLM não achou já vem como None,
    igual ao parser determinístico — Coding-Standards.md)."""

    nome: str

    @abstractmethod
    def extrair(self, texto_pdf: str, seguradora_detectada: str | None) -> ExtracaoVeiculosResult:
        """Pode levantar LLMProviderError em caso de falha de comunicação/API."""
        ...
