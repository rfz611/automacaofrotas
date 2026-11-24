"""Conversor mínimo de apólice PDF para a planilha padronizada de frotas."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.excel.excel_generator import gerar_excel_bytes
from core.pipeline import ParserPipeline


def criar_parser_argumentos() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extrai veículos de uma apólice PDF e gera uma planilha Excel."
    )
    parser.add_argument("pdf", type=Path, help="Caminho do PDF da apólice")
    parser.add_argument(
        "-o",
        "--saida",
        type=Path,
        help="Arquivo .xlsx de saída (padrão: mesmo nome do PDF)",
    )
    parser.add_argument(
        "--usar-llm",
        action="store_true",
        help="Permite fallback por IA quando nenhum parser determinístico funcionar",
    )
    return parser


def main() -> int:
    args = criar_parser_argumentos().parse_args()
    pdf = args.pdf.resolve()
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise SystemExit(f"PDF inválido ou não encontrado: {pdf}")

    saida = (args.saida or pdf.with_suffix(".xlsx")).resolve()
    saida.parent.mkdir(parents=True, exist_ok=True)

    resultado = ParserPipeline(usar_fallback_llm=args.usar_llm).processar(str(pdf))
    veiculos = resultado.get("itens", [])
    saida.write_bytes(gerar_excel_bytes(veiculos))

    print(f"Seguradora: {resultado.get('seguradora', 'DESCONHECIDA')}")
    print(f"Veículos extraídos: {len(veiculos)}")
    validacao = resultado.get("validacao", {})
    print(f"Validação: {validacao.get('status', 'NÃO EXECUTADA')}")
    print(f"Itens para revisão: {validacao.get('quantidade_com_atencao', 0)}")
    for item in validacao.get("itens_com_atencao", []):
        motivos = ", ".join(item["flags_atencao"])
        print(f"  - Item {item['item_apolice']} ({item.get('placa') or 'sem placa'}): {motivos}")
    print(f"Fallback por IA: {'sim' if resultado.get('usou_fallback_llm') else 'não'}")
    print(f"Planilha gerada: {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
