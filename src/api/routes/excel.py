"""
POST /excel — recebe os veículos já revisados pelo usuário no Preview (RF-005) e
devolve o binário .xlsx gerado a partir do template (RF-006, UC03). Chamado pelo
Backend no endpoint POST /apolices/:id/export (API.md) — ver ponto de atenção da
Fase 0 sobre essa integração Backend <-> Parser Engine.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.excel.excel_generator import gerar_excel_bytes

router = APIRouter()


class VeiculoExportacaoSchema(BaseModel):
    """Export preserves reviewed values, including pending formats, without
    weakening the strict extraction schema or inventing missing coverage."""
    item_apolice: str | int | float | None = None
    placa: str | int | float | None = None
    marca: str | int | float | None = None
    modelo: str | int | float | None = None
    ano_fabricacao: str | int | float | None = None
    ano_modelo: str | int | float | None = None
    chassi: str | int | float | None = None
    classe_bonus: str | int | float | None = None
    codigo_fipe: str | int | float | None = None
    valor_casco: str | int | float | None = None
    rcf_danos_materiais: str | int | float | None = None
    rcf_danos_corporais: str | int | float | None = None
    danos_morais: str | int | float | None = None
    app_passageiros: str | int | float | None = None
    cobertura_vidros: str | int | float | None = None
    assistencia: str | int | float | None = None
    codigo_identificacao: str | int | float | None = None


class ExportarExcelRequest(BaseModel):
    veiculos: list[VeiculoExportacaoSchema]


@router.post("/excel")
async def gerar_excel(payload: ExportarExcelRequest) -> StreamingResponse:
    dados = [v.model_dump() for v in payload.veiculos]
    xlsx_bytes = gerar_excel_bytes(dados, template_path="assets/excel-padrao.xlsx")

    import io

    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=frota.xlsx"},
    )
