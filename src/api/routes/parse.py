import os
import shutil
import tempfile
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Response

from core.pipeline import ParserPipeline
from core.excel.excel_generator import gerar_excel_bytes

router = APIRouter()


def get_pipeline():
    return ParserPipeline()


@router.post("/parse", summary="Extrair dados do PDF em formato JSON")
async def parse_pdf(
    file: UploadFile = File(...),
    pipeline: ParserPipeline = Depends(get_pipeline)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        dados = pipeline.processar(tmp_path)
        lista_veiculos = dados.get("itens") or dados.get("veiculos") or []
        
        return {
            "seguradora": dados.get("seguradora"),
            "confianca_deteccao": dados.get("confianca_deteccao", 1.0),
            "usou_fallback_llm": dados.get("usou_fallback_llm", False),
            "quantidade_veiculos": len(lista_veiculos),
            "veiculos": lista_veiculos,
            "validacao": dados.get("validacao"),
            "erro": dados.get("erro")
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/upload-to-excel", summary="Enviar PDF e baixar planilha Excel (.xlsx) diretamente")
async def upload_pdf_to_excel(
    file: UploadFile = File(...),
    pipeline: ParserPipeline = Depends(get_pipeline)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        dados = pipeline.processar(tmp_path)
        itens = dados.get("itens", [])
        
        # Gera o Excel diretamente da extração
        excel_bytes = gerar_excel_bytes(veiculos=itens)
        
        nome_arquivo = f"frota_{os.path.splitext(file.filename)[0]}.xlsx"
        
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"}
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
