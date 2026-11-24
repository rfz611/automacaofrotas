import logging
import os
import re
import json
import urllib.request
from typing import Dict, Any, List
import pdfplumber
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class LLMFallbackParser:
    """Parser universal alimentado pela API nativa do Gemini com Structured Outputs."""

    def __init__(self):
        self.api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        self.model = os.getenv("LLM_MODEL", "gemini-flash-latest")
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        logger.info(f"[LLM Parser] Modelo carregado: {self.model}")

    def _limpar_texto(self, texto: str) -> str:
        if not texto:
            return ""
        return re.sub(r'\(cid:\d+\)', '', texto)

    def _dividir_em_lotes(self, paginas: List[str], tamanho_lote: int = 6) -> List[str]:
        lotes = []
        for i in range(0, len(paginas), tamanho_lote):
            lote = "\n--- QUEBRA DE PÁGINA ---\n".join(paginas[i:i + tamanho_lote])
            lotes.append(lote)
        return lotes

    def _chamar_gemini(self, prompt: str) -> Dict[str, Any]:
        schema = {
            "type": "OBJECT",
            "properties": {
                "seguradora": {"type": "STRING"},
                "numero_apolice": {"type": "STRING"},
                "vigencia_inicio": {"type": "STRING"},
                "vigencia_fim": {"type": "STRING"},
                "premio_total": {"type": "NUMBER"},
                "itens": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "item_apolice": {"type": "INTEGER"},
                            "placa": {"type": "STRING"},
                            "marca": {"type": "STRING"},
                            "modelo": {"type": "STRING"},
                            "ano_fabricacao": {"type": "STRING"},
                            "ano_modelo": {"type": "STRING"},
                            "chassi": {"type": "STRING"},
                            "classe_bonus": {"type": "INTEGER"},
                            "codigo_fipe": {"type": "STRING"},
                            "valor_casco": {"type": "NUMBER"},
                            "rcf_danos_materiais": {"type": "NUMBER"},
                            "rcf_danos_corporais": {"type": "NUMBER"},
                            "danos_morais": {"type": "NUMBER"},
                            "app_passageiros": {"type": "NUMBER"},
                            "cobertura_vidros": {"type": "NUMBER"},
                            "assistencia": {"type": "STRING"},
                            "codigo_identificacao": {"type": "STRING"}
                        }
                    }
                }
            },
            "required": ["itens"]
        }

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.1
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }

        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            texto_resposta = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(texto_resposta)

    def parse(self, caminho_pdf: str, seguradora_sugerida: str = "Desconhecida", **kwargs) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada no arquivo .env.")

        paginas = []
        with pdfplumber.open(caminho_pdf) as pdf:
            for p in pdf.pages:
                raw = p.extract_text() or ""
                paginas.append(self._limpar_texto(raw))

        lotes = self._dividir_em_lotes(paginas, tamanho_lote=6)
        todos_itens: List[Dict[str, Any]] = []
        metadados_gerais = {
            "seguradora": seguradora_sugerida,
            "numero_apolice": None,
            "vigencia_inicio": None,
            "vigencia_fim": None,
            "premio_total": None,
        }

        prompt_base = """
        Extraia com precisão os dados cadastrais e coberturas de cada veículo da apólice de frota.
        Regras obrigatórias:
        1. Em coberturas (Casco, RCF Danos Materiais, Corporais, Morais, APP): capture APENAS o Limite Máximo de Indenização (LMI).
        2. NUNCA coloque valores de Franquia ou Tarifa nos campos de coberturas.
        3. Se o Casco for Cobertura Compreensiva / 100% FIPE sem valor fixo em R$, preencha valor_casco = 0.0.
        4. Converta a classe de bônus sempre para número inteiro (ex: X -> 10, V -> 5).
        """

        for idx, lote_texto in enumerate(lotes):
            prompt = f"{prompt_base}\n\nTrecho do documento (Lote {idx+1}/{len(lotes)}):\n{lote_texto}"
            try:
                parsed = self._chamar_gemini(prompt)
                if idx == 0:
                    if parsed.get("seguradora") and parsed["seguradora"].upper() != "DESCONHECIDA":
                        metadados_gerais["seguradora"] = parsed["seguradora"]
                    metadados_gerais["numero_apolice"] = parsed.get("numero_apolice")
                    metadados_gerais["vigencia_inicio"] = parsed.get("vigencia_inicio")
                    metadados_gerais["vigencia_fim"] = parsed.get("vigencia_fim")
                    metadados_gerais["premio_total"] = parsed.get("premio_total")

                for it in parsed.get("itens", []):
                    chassi = it.get("chassi")
                    placa = it.get("placa")
                    if chassi and not any(x.get("chassi") == chassi for x in todos_itens):
                        todos_itens.append(it)
                    elif placa and not any(x.get("placa") == placa for x in todos_itens):
                        todos_itens.append(it)
            except Exception as e:
                print(f"[!] Erro no lote {idx+1} da LLM: {e}")

        for idx, item in enumerate(todos_itens):
            item["item_apolice"] = idx + 1

        return {
            "seguradora": metadados_gerais["seguradora"],
            "numero_apolice": metadados_gerais["numero_apolice"],
            "vigencia_inicio": metadados_gerais["vigencia_inicio"],
            "vigencia_fim": metadados_gerais["vigencia_fim"],
            "total_itens": len(todos_itens),
            "premio_total": metadados_gerais["premio_total"],
            "itens": todos_itens
        }