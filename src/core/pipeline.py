import os
from typing import Dict, Any, Optional
from fastapi import HTTPException

from core.detection.detector import Detector
from core.parsers.bradesco_parser import BradescoParser
from core.parsers.porto_seguro_parser import PortoParser
from core.parsers.sura_parser import SuraParser
from core.parsers.llm_fallback_parser import LLMFallbackParser
from core.normalizer.normalizer import Normalizer, criar_resumo_validacao
from schemas.veiculo_schema import VeiculoSchema


class ParserPipeline:
    def __init__(
        self,
        detector: Optional[Any] = None,
        usar_fallback_llm: bool = True,
        **kwargs,
    ):
        self.detector = detector or Detector()
        self.usar_fallback_llm = usar_fallback_llm
        # Evita inicializar integrações externas quando o MVP estiver operando
        # somente com os parsers determinísticos.
        self.llm_parser = LLMFallbackParser() if usar_fallback_llm else None
        self.parsers = {
            "BRADESCO": BradescoParser(),
            "BRADESCO SEGUROS": BradescoParser(),
            "PORTO SEGURO": PortoParser(),
            "PORTO": PortoParser(),
            "SEGUROS SURA": SuraParser(),
            "SURA": SuraParser(),
        }

    def processar(self, caminho_pdf: str, **kwargs) -> Dict[str, Any]:
        if not os.path.exists(caminho_pdf):
            raise HTTPException(status_code=400, detail=f"Arquivo PDF não encontrado: {caminho_pdf}")

        # 1. Detecção da Seguradora
        deteccao = self.detector.detectar(caminho_pdf)
        seguradora_detectada = str(deteccao).strip()
        chave = seguradora_detectada.upper()

        parser = self.parsers.get(chave)
        if not parser:
            for k, p in self.parsers.items():
                if k in chave or chave in k:
                    parser = p
                    break

        resultado: Optional[Dict[str, Any]] = None

        # 2. Fast Path: Tenta extração determinística via Regex
        if parser:
            try:
                resultado = parser.parse(caminho_pdf=caminho_pdf, **kwargs)
            except Exception as e:
                print(f"[!] Falha no parser determinístico ({seguradora_detectada}): {e}")
                resultado = None

        # 3. Fallback Inteligente: Se não há parser ou se retornou 0 itens
        precisa_fallback = (
            not resultado
            or not resultado.get("itens")
            or len(resultado["itens"]) == 0
        )

        usou_fallback_llm = False
        if precisa_fallback and self.usar_fallback_llm:
            print(f"[+] Acionando Fallback de LLM para o arquivo: {caminho_pdf}")
            try:
                usou_fallback_llm = True
                resultado = self.llm_parser.parse(
                    caminho_pdf=caminho_pdf,
                    seguradora_sugerida=seguradora_detectada
                )
            except Exception as e:
                if not resultado:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Não foi possível extrair a apólice nem via Regex nem via LLM: {str(e)}"
                    )

        if not resultado or not resultado.get("itens"):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Nenhum item/veículo foi identificado pelo parser determinístico."
                    if not self.usar_fallback_llm
                    else "Nenhum item/veículo foi identificado no documento fornecido."
                ),
            )

        veiculos_validados = Normalizer().normalizar_lista(
            [VeiculoSchema.model_validate(item) for item in resultado["itens"]]
        )
        resultado["itens"] = [veiculo.model_dump() for veiculo in veiculos_validados]
        resultado["validacao"] = criar_resumo_validacao(veiculos_validados)
        resultado["usou_fallback_llm"] = usou_fallback_llm
        return resultado
