"""
Gerador de Excel (Parser-Engine.md: "04. Excel Generator") – RF-006, UC03.
Gera a planilha com cabeçalhos estilizados, larguras dimensionadas automaticamente
e formatação correta de moedas (R$ #,##0.00).
"""

from __future__ import annotations
import io
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Ordem A -> Q EXATA do Layout da Matriz
COLUNAS_ORDENADAS = (
    "item_apolice", "placa", "marca", "modelo", "ano_fabricacao", "ano_modelo",
    "chassi", "classe_bonus", "codigo_fipe", "valor_casco", "rcf_danos_materiais",
    "rcf_danos_corporais", "danos_morais", "app_passageiros", "cobertura_vidros",
    "assistencia", "codigo_identificacao",
)

CABECALHOS = (
    "Item Apólice", "Placa", "Marca", "Modelo", "Ano Fab", "Ano Mod", "Chassi",
    "Bônus", "FIPE", "Casco", "RCF DM", "RCF DC", "DMO", "APP", "Vidros",
    "Assist", "CI",
)

COLUNAS_MOEDA = {
    "valor_casco", "rcf_danos_materiais", "rcf_danos_corporais", 
    "danos_morais", "app_passageiros", "cobertura_vidros",
}

FORMATO_MOEDA_BRL = '"R$"\\ #,##0.00'
LINHA_INICIAL = 2
TEMPLATE_PADRAO = Path(__file__).resolve().parents[3] / "assets" / "excel-padrao.xlsx"

# Larguras mínimas ideais para cada coluna nunca cortar
LARGURAS_MINIMAS = {
    1: 14,  # Item Apólice
    2: 12,  # Placa
    3: 18,  # Marca
    4: 46,  # Modelo (descrição longa)
    5: 11,  # Ano Fab
    6: 11,  # Ano Mod
    7: 24,  # Chassi (17 dígitos)
    8: 10,  # Bônus
    9: 13,  # FIPE
    10: 18, # Casco (Moeda)
    11: 18, # RCF DM (Moeda)
    12: 18, # RCF DC (Moeda)
    13: 18, # DMO (Moeda)
    14: 18, # APP (Moeda)
    15: 16, # Vidros
    16: 15, # Assist
    17: 15, # CI
}


def _criar_template_minimo() -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "Frota"
    
    amarelo = PatternFill(start_color="FFF200", end_color="FFF200", fill_type="solid")
    fonte_cabecalho = Font(name="Calibri", size=11, bold=True, color="000000")
    borda_fina = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    for idx, titulo in enumerate(CABECALHOS, start=1):
        celula = ws.cell(row=1, column=idx, value=titulo)
        celula.fill = amarelo
        celula.font = fonte_cabecalho
        celula.alignment = Alignment(horizontal="center", vertical="center")
        celula.border = borda_fina

    ws.row_dimensions[1].height = 28
    return wb


def _ajustar_largura_colunas(ws) -> None:
    """Calcula e aplica as larguras ideais para todas as colunas abrirem perfeitamente."""
    for col_idx, col in enumerate(ws.columns, start=1):
        max_len = 0
        col_letter = get_column_letter(col_idx)
        
        for cell in col:
            val = cell.value
            if val is not None:
                # Se for número de moeda, adiciona folga para a formatação R$ #,##0.00
                if cell.number_format == FORMATO_MOEDA_BRL:
                    try:
                        comp = len(f"R$ {float(val):,.2f}") + 3
                    except (ValueError, TypeError):
                        comp = len(str(val))
                else:
                    comp = len(str(val))
                if comp > max_len:
                    max_len = comp
        
        largura_min = LARGURAS_MINIMAS.get(col_idx, 12)
        ws.column_dimensions[col_letter].width = max(max_len + 3, largura_min)


def _ordem_item(veiculo: Dict[str, Any]) -> tuple[int, int]:
    try:
        return (0, int(str(veiculo.get("item_apolice") or 0).strip() or 0))
    except (ValueError, TypeError):
        # Keep invalid edited items exportable, in their relative order.
        return (1, 0)


def gerar_excel(veiculos: List[Dict[str, Any]], template_path: Optional[str | Path] = None) -> Workbook:
    # Garante ordenação numérica crescente pelo número do item
    veiculos = sorted(
        veiculos, 
        key=_ordem_item
    )

    caminho_template = Path(template_path) if template_path is not None else TEMPLATE_PADRAO
    if caminho_template.exists():
        wb = load_workbook(caminho_template)
        ws = wb.active
    else:
        wb = _criar_template_minimo()
        ws = wb.active

    borda_dados = Border(
        left=Side(style='thin', color='E0E0E0'),
        right=Side(style='thin', color='E0E0E0'),
        top=Side(style='thin', color='E0E0E0'),
        bottom=Side(style='thin', color='E0E0E0')
    )

    for offset, veiculo in enumerate(veiculos):
        linha = LINHA_INICIAL + offset
        ws.row_dimensions[linha].height = 20
        
        for col_idx, campo in enumerate(COLUNAS_ORDENADAS, start=1):
            valor = veiculo.get(campo)
            celula = ws.cell(row=linha, column=col_idx)
            celula.border = borda_dados
            
            # 1. Moedas formatadas
            if campo in COLUNAS_MOEDA:
                if valor not in (None, ""):
                    try:
                        celula.value = float(valor)
                        celula.number_format = FORMATO_MOEDA_BRL
                    except (ValueError, TypeError):
                        celula.value = valor
                else:
                    celula.value = None
                celula.alignment = Alignment(horizontal="right", vertical="center")

            # 2. Inteiros (remove triângulo verde de número armazenado como texto)
            elif campo in ["item_apolice", "classe_bonus", "ano_fabricacao", "ano_modelo"]:
                if valor not in (None, ""):
                    try:
                        celula.value = int(valor)
                    except (ValueError, TypeError):
                        celula.value = valor
                else:
                    celula.value = None
                celula.alignment = Alignment(horizontal="center", vertical="center")

            # 3. Do not silently remove invalid characters from reviewed identifiers.
            elif campo in ["placa", "chassi"]:
                if valor not in (None, ""):
                    celula.value = str(valor).upper().strip()
                else:
                    celula.value = ""
                celula.alignment = Alignment(horizontal="center", vertical="center")

            # 4. Códigos e IDs com alinhamento centralizado
            elif campo in ["codigo_fipe", "codigo_identificacao"]:
                celula.value = str(valor).strip() if valor not in (None, "") else ""
                celula.alignment = Alignment(horizontal="center", vertical="center")

            # 5. Textos descritivos (Marca, Modelo, Vidros, Assist)
            else:
                celula.value = str(valor).strip() if valor not in (None, "") else ""
                celula.alignment = Alignment(horizontal="left", vertical="center")

            # Reviewed text is data, never an Excel formula.
            if isinstance(celula.value, str):
                celula.data_type = "s"

    # Aplica as larguras automáticas sem precisar puxar no mouse
    _ajustar_largura_colunas(ws)
    
    # Habilita filtros no cabeçalho
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUNAS_ORDENADAS))}{max(len(veiculos) + 1, 1)}"
    
    return wb


def gerar_excel_bytes(veiculos: List[Dict[str, Any]], template_path: Optional[str | Path] = None) -> bytes:
    wb = gerar_excel(veiculos, template_path)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
