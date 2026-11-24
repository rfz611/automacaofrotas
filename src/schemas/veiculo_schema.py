"""
Schema estrito dos 17 campos extraídos de uma apólice de frota.

Espelha EXATAMENTE Parser-Engine.md / Layout-do-Excel.md / Banco.md (tabela
frota_veiculos) — mesma ordem de colunas (A -> Q), mesmos nomes de campo usados no
DTO NestJS (create-veiculo.dto.ts) e no schema Zod (veiculo.schema.ts).

Filosofia de validação (Coding-Standards.md + UC02):
    - Nenhum campo é obrigatório NO NÍVEL DO TIPO: o parser (determinístico ou LLM)
      pode não localizar um valor e grava None, marcando a linha para revisão humana
      em vez de falhar a extração inteira.
    - placa/chassi fora do formato NÃO lançam exceção aqui — UC02 espera que
      apareçam destacados no Preview, não que bloqueiem o parsing. Por isso os
      validators desses campos normalizam (upper/strip) mas não rejeitam; a checagem
      "está válido?" vive em métodos separados (`placa_valida`, `chassi_valido`)
      usados por `flags_atencao()`.
    - RCF/DMO nunca recebem defaults: os limites variam por proposta. Quando o
      documento não trouxer um valor, ele permanece None para revisão humana.

ATUALIZAÇÃO (Fase 2): a normalização/validação de placa (RN-02) e chassi (RN-01) foi
extraída para core/normalizer/validators/{placa,chassi}_validator.py — este arquivo
agora IMPORTA de lá em vez de manter sua própria cópia do regex, para não haver duas
fontes de verdade para a mesma regra de negócio. Reexecutei os 7 testes da Fase 1
contra esta versão refatorada antes de entregar (ver resumo da resposta) — nenhum
comportamento mudou, só a origem do código.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.normalizer.validators.chassi_validator import (
    chassi_valido as _chassi_valido_fn,
    normalizar_chassi,
)
from core.normalizer.validators.placa_validator import normalizar_placa
from core.normalizer.validators.placa_validator import placa_valida as _placa_valida_fn

# Campos tratados como obrigatórios pelo negócio (Layout-do-Excel.md).
# Coberturas podem estar ausentes ou não contratadas e, por isso, não são inferidas.
CAMPOS_OBRIGATORIOS: tuple[str, ...] = (
    "item_apolice",
    "placa",
    "marca",
    "modelo",
    "ano_fabricacao",
    "ano_modelo",
    "chassi",
    "classe_bonus",
)


class VeiculoSchema(BaseModel):
    """Os 17 campos — colunas A a Q do Excel padrão da corretora (assets/excel-padrao.xlsx)."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    item_apolice: Optional[int] = Field(default=None, description="Coluna A — numérico sequencial")
    placa: Optional[str] = Field(default=None, description="Coluna B")
    marca: Optional[str] = Field(default=None, max_length=100, description="Coluna C")
    modelo: Optional[str] = Field(default=None, max_length=255, description="Coluna D")
    ano_fabricacao: Optional[int] = Field(default=None, description="Coluna E — 4 dígitos")
    ano_modelo: Optional[int] = Field(default=None, description="Coluna F — 4 dígitos")
    chassi: Optional[str] = Field(default=None, description="Coluna G")
    classe_bonus: Optional[int] = Field(default=None, description="Coluna H — 0 a 10")
    codigo_fipe: Optional[str] = Field(default=None, max_length=50, description="Coluna I")
    valor_casco: Optional[Decimal] = Field(default=None, description="Coluna J — moeda")
    rcf_danos_materiais: Optional[Decimal] = Field(default=None, description="Coluna K")
    rcf_danos_corporais: Optional[Decimal] = Field(default=None, description="Coluna L")
    danos_morais: Optional[Decimal] = Field(default=None, description="Coluna M")
    app_passageiros: Optional[Decimal] = Field(default=None, description="Coluna N — opcional")
    cobertura_vidros: Optional[str] = Field(default=None, max_length=100, description="Coluna O — opcional")
    assistencia: Optional[str] = Field(default=None, max_length=100, description="Coluna P — opcional")
    codigo_identificacao: Optional[str] = Field(
        default=None, max_length=100, description="Coluna Q — opcional"
    )

    # ---------------- normalização (não rejeita, só limpa formato) ----------------

    @field_validator("placa", mode="before")
    @classmethod
    def normaliza_placa(cls, v: Optional[str]) -> Optional[str]:
        """RN-02 — delega para core/normalizer/validators/placa_validator.py."""
        return normalizar_placa(v) if isinstance(v, str) else v

    @field_validator("chassi", mode="before")
    @classmethod
    def normaliza_chassi_campo(cls, v: Optional[str]) -> Optional[str]:
        """RN-01 — delega para core/normalizer/validators/chassi_validator.py."""
        return normalizar_chassi(v) if isinstance(v, str) else v

    @field_validator("marca", mode="before")
    @classmethod
    def normaliza_marca(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if isinstance(v, str) else v

    # ---------------- checagens de validade (usadas para flagging, não para rejeitar) ----------------

    def placa_valida(self) -> bool:
        """RN-02."""
        return _placa_valida_fn(self.placa)

    def chassi_valido(self) -> bool:
        """RN-01: exatamente 17 caracteres alfanuméricos."""
        return _chassi_valido_fn(self.chassi)

    def classe_bonus_valida(self) -> bool:
        return self.classe_bonus is not None and 0 <= self.classe_bonus <= 10

    def calcular_flags_atencao(self) -> list[str]:
        """
        Campos ausentes ou inválidos — usada para popular `flags_atencao` na resposta
        ao Frontend (API.md) e destacar células no Preview (RF-017/UC02).

        Renomeado de `flags_atencao()` (Fase 1) para `calcular_flags_atencao()` na
        Fase 2: um MÉTODO chamado `flags_atencao` e um CAMPO de mesmo nome em
        VeiculoExtraido (core/normalizer/normalizer.py), que precisa ficar com esse
        nome exato para bater com API.md, colidiam — a subclasse silenciosamente
        deixava o método inacessível (`'list' object is not callable`). Testado e
        confirmado antes da correção.
        """
        flags = [campo for campo in CAMPOS_OBRIGATORIOS if getattr(self, campo) is None]
        if self.placa is not None and not self.placa_valida():
            flags.append("placa")
        if self.chassi is not None and not self.chassi_valido():
            flags.append("chassi")
        if self.classe_bonus is not None and not self.classe_bonus_valida():
            flags.append("classe_bonus")
        return list(dict.fromkeys(flags))  # remove duplicatas mantendo ordem
