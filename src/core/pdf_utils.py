"""
Utilitário compartilhado de leitura de PDF (pdfplumber) — usado tanto pela Detecção
(precisa do texto corrido) quanto pelos Parsers determinísticos (precisam das tabelas).
Mantido fora de core/detection/ e core/parsers/ especificamente para evitar que um
dependa do outro só para ler PDF.
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber


def extrair_texto(pdf_path: str | Path) -> str:
    """Concatena o texto de todas as páginas — usado pela Detecção."""
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)


def extrair_tabelas(pdf_path: str | Path) -> list[list[list[str | None]]]:
    """Retorna todas as tabelas de todas as páginas, na ordem em que aparecem."""
    tabelas: list[list[list[str | None]]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            tabelas.extend(pagina.extract_tables())
    return tabelas
