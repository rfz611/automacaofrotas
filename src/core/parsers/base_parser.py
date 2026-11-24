"""
Interface abstrata dos parsers determinísticos por seguradora (RNF-002: cada
seguradora tem um parser independente).

Design: BaseParser implementa o algoritmo de extração completo (localizar tabela de
veículos, mapear cabeçalho -> campo, converter linha -> VeiculoSchema) como um Template
Method. Cada subclasse concreta só declara QUAIS palavras-chave de cabeçalho identificam
cada um dos 17 campos (`mapeamento_colunas`) — sem repetir a lógica de extração.
Uma seguradora com layout muito diferente pode sobrescrever `extrair()` inteiramente.

Nunca lança exceção por CAMPO individual ausente ou malformado — isso vira None
(Coding-Standards.md). Só lança `ParserIndisponivelError` quando não consegue localizar
NENHUMA tabela reconhecível no PDF inteiro — sinal para o orquestrador acionar o
fallback LLM (Parser-Engine.md: "se falhar ou layout for novo").
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import ClassVar

from schemas.veiculo_schema import VeiculoSchema

from .pdf_utils import extrair_tabelas

CAMPOS_INTEIROS = {"item_apolice", "ano_fabricacao", "ano_modelo", "classe_bonus"}
CAMPOS_DECIMAIS = {
    "valor_casco",
    "rcf_danos_materiais",
    "rcf_danos_corporais",
    "danos_morais",
    "app_passageiros",
}
CAMPOS_TEXTO = {
    "placa",
    "marca",
    "modelo",
    "chassi",
    "codigo_fipe",
    "cobertura_vidros",
    "assistencia",
    "codigo_identificacao",
}


class ParserIndisponivelError(Exception):
    """Levantada quando o parser determinístico não localiza nenhuma tabela de
    veículos reconhecível no PDF — sinaliza o orquestrador para acionar o fallback LLM.
    NÃO deve ser levantada por causa de um campo individual ausente/malformado."""


def _parse_decimal_brl(texto: str | None) -> Decimal | None:
    """Converte "R$ 2.319,60" / "2319.60" / "2319,60" -> Decimal. None se não der pra
    interpretar — nunca lança exceção."""
    if texto is None:
        return None
    limpo = str(texto).strip().replace("R$", "").replace(" ", "")
    if not limpo:
        return None
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return Decimal(limpo)
    except (InvalidOperation, ValueError):
        return None


def _parse_int(texto: str | None) -> int | None:
    if texto is None:
        return None
    limpo = re.sub(r"[^\d-]", "", str(texto).strip())
    if not limpo or limpo == "-":
        return None
    try:
        return int(limpo)
    except ValueError:
        return None


class BaseParser(ABC):
    """Interface + implementação padrão (Template Method) dos parsers determinísticos."""

    seguradora: ClassVar[str]

    # campo -> palavras-chave que podem aparecer na célula de cabeçalho daquele campo
    # (contains, case-insensitive — tolera variações como "PLACA" ou "PLACA VEICULO").
    # AVISO: sem PDFs reais para calibrar, este mapeamento genérico é o mesmo ponto de
    # partida usado pelas 3 seguradoras — cada subclasse pode sobrescrever com os
    # termos reais assim que houver amostras (RNF-002: não afeta as outras).
    mapeamento_colunas: ClassVar[dict[str, tuple[str, ...]]] = {
        "item_apolice": ("ITEM", "SEQ", "Nº", "NUM"),
        "placa": ("PLACA",),
        "marca": ("MARCA",),
        "modelo": ("MODELO",),
        "ano_fabricacao": ("ANO FAB", "ANO DE FABRICACAO", "FABRICACAO"),
        "ano_modelo": ("ANO MOD", "ANO DO MODELO"),
        "chassi": ("CHASSI", "CHASSIS"),
        "classe_bonus": ("BONUS", "CLASSE BONUS", "CLASSE DE BONUS"),
        "codigo_fipe": ("FIPE", "CODIGO FIPE"),
        "valor_casco": ("CASCO",),
        "rcf_danos_materiais": ("RCF DM", "RCF - DM", "DANOS MATERIAIS"),
        "rcf_danos_corporais": ("RCF DC", "RCF - DC", "DANOS CORPORAIS"),
        "danos_morais": ("DMO", "DANOS MORAIS"),
        "app_passageiros": ("APP", "ACIDENTES PESSOAIS"),
        "cobertura_vidros": ("VIDROS",),
        "assistencia": ("ASSISTENCIA", "ASSIST"),
        "codigo_identificacao": ("CI", "CODIGO DE IDENTIFICACAO", "IDENTIFICACAO"),
    }

    # coluna combinada opcional: se detectada, preenche `modelo` com o texto inteiro e
    # deixa `marca` como None (flagueado) — melhor do que adivinhar errado.
    palavras_chave_marca_modelo_combinado: ClassVar[tuple[str, ...]] = (
        "MARCA/MODELO",
        "MARCA MODELO",
        "VEICULO",
        "VEÍCULO",
    )

    def consegue_processar(self, texto_pdf: str) -> bool:
        """Confirma se este parser sabe lidar com o layout do texto informado.
        Por padrão reusa o nome da seguradora; sobrescreva se precisar de lógica própria."""
        return self.seguradora.upper() in texto_pdf.upper()

    def extrair(self, pdf_path: str | Path) -> list[VeiculoSchema]:
        """Extrai os veículos do PDF. Nunca lança exceção por campo — campos não
        localizados/malformados voltam como None em VeiculoSchema."""
        tabelas = extrair_tabelas(pdf_path)
        tabela, indices_campo = self._localizar_tabela_veiculos(tabelas)
        if tabela is None:
            raise ParserIndisponivelError(
                f"{self.seguradora}: nenhuma tabela de veículos reconhecível no PDF"
            )

        veiculos: list[VeiculoSchema] = []
        for linha in tabela[1:]:  # pula o cabeçalho
            if linha is None or all(celula is None or str(celula).strip() == "" for celula in linha):
                continue  # linha em branco (comum em PDFs) — ignora, não é veículo
            dados = self._linha_para_dict(linha, indices_campo)
            veiculos.append(VeiculoSchema(**dados))
        return veiculos

    # ---------------- lógica compartilhada (Template Method) ----------------

    def _localizar_tabela_veiculos(
        self, tabelas: list[list[list[str | None]]]
    ) -> tuple[list[list[str | None]] | None, dict[str, int]]:
        """Entre todas as tabelas do PDF, escolhe a que tem o cabeçalho com mais campos
        reconhecidos. Retorna (None, {}) se nenhuma tabela tiver cabeçalho reconhecível
        (mínimo: pelo menos placa OU chassi, senão não é uma tabela de veículos)."""
        melhor_tabela: list[list[str | None]] | None = None
        melhor_indices: dict[str, int] = {}
        for tabela in tabelas:
            if not tabela or not tabela[0]:
                continue
            indices = self._mapear_colunas(tabela[0])
            if ("placa" in indices or "chassi" in indices) and len(indices) > len(melhor_indices):
                melhor_tabela, melhor_indices = tabela, indices
        return melhor_tabela, melhor_indices

    def _mapear_colunas(self, cabecalho: list[str | None]) -> dict[str, int]:
        indices: dict[str, int] = {}
        marca_modelo_combinado_idx: int | None = None

        for idx, celula in enumerate(cabecalho):
            texto_celula = (celula or "").strip().upper()
            if not texto_celula:
                continue
            if any(chave in texto_celula for chave in self.palavras_chave_marca_modelo_combinado):
                marca_modelo_combinado_idx = idx
                continue
            for campo, palavras_chave in self.mapeamento_colunas.items():
                if campo in indices:
                    continue
                if any(chave in texto_celula for chave in palavras_chave):
                    indices[campo] = idx
                    break

        # só usa a coluna combinada se marca/modelo separados não foram encontrados
        if marca_modelo_combinado_idx is not None and "modelo" not in indices:
            indices["modelo"] = marca_modelo_combinado_idx

        return indices

    def _linha_para_dict(self, linha: list[str | None], indices_campo: dict[str, int]) -> dict:
        dados: dict[str, object] = {}
        for campo, idx in indices_campo.items():
            valor_bruto = linha[idx] if idx < len(linha) else None
            valor_bruto = valor_bruto.strip() if isinstance(valor_bruto, str) else valor_bruto
            if campo in CAMPOS_INTEIROS:
                dados[campo] = _parse_int(valor_bruto)
            elif campo in CAMPOS_DECIMAIS:
                dados[campo] = _parse_decimal_brl(valor_bruto)
            else:
                dados[campo] = valor_bruto or None
        return dados
