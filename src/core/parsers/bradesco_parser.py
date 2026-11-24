import re
from typing import Dict, Any, List, Optional, Tuple
import pdfplumber

from core.detection.signatures.bradesco import BRADESCO_SIGNATURE
from core.detection.detector import limpar_texto_duplicado

try:
    from .base_parser import BaseParser
except ImportError:
    class BaseParser:
        pass


MONTADORAS = [
    "VOLKSWAGEN", "VW", "CHEVROLET", "GM", "FIAT", "FORD", "TOYOTA", 
    "HYUNDAI", "RENAULT", "HONDA", "JEEP", "NISSAN", "MERCEDES-BENZ", 
    "MERCEDES BENZ", "M.BENZ", "MERCEDES", "MB", "SCANIA", "VOLVO", 
    "IVECO", "PEUGEOT", "CITROEN", "MITSUBISHI", "BMW", "AUDI", "DAF", 
    "MAN", "BYD", "GWM", "CHERY"
]


class BradescoParser(BaseParser):
    seguradora = BRADESCO_SIGNATURE.nome if hasattr(BRADESCO_SIGNATURE, "nome") else "Bradesco Seguros"

    def _converter_valor(self, valor_str: Optional[str]) -> Optional[float]:
        if not valor_str:
            return None
        try:
            val = re.sub(r'[^\d,.]', '', valor_str).strip()
            if ',' in val and '.' in val:
                val = val.replace('.', '').replace(',', '.')
            elif ',' in val:
                val = val.replace(',', '.')
            return float(val)
        except Exception:
            return None

    def _extrair_metadados(self, texto: str) -> Dict[str, Any]:
        apolice_match = re.search(r'(?:Ap[óo]lice|Proposta)\s*(?:n[ºo\.]?)?\s*[:\.\n]?\s*([\d\.\-\/]+)', texto, re.IGNORECASE)
        numero_apolice = apolice_match.group(1).strip() if apolice_match else None

        vigencia_match = re.search(
            r'(\d{2}/\d{2}/\d{4})\s*(?:[aà\s]+|\s*at[ée]\s*)\s*(\d{2}/\d{2}/\d{4})',
            texto,
            re.IGNORECASE
        )
        vigencia_inicio = vigencia_match.group(1) if vigencia_match else None
        vigencia_fim = vigencia_match.group(2) if vigencia_match else None

        premio_match = re.search(r'Pr[êe]mio\s*Total\s*[:\.]?\s*(?:R\$\s*)?([\d\.]+,\d{2})', texto, re.IGNORECASE)
        premio_total = self._converter_valor(premio_match.group(1)) if premio_match else None

        return {
            "numero_apolice": numero_apolice,
            "vigencia_inicio": vigencia_inicio,
            "vigencia_fim": vigencia_fim,
            "premio_total": premio_total,
        }

    def _separar_marca_modelo(self, texto_modelo: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not texto_modelo:
            return None, None

        texto = texto_modelo.strip()
        marca_encontrada = None

        for m in MONTADORAS:
            if re.search(r'\b' + re.escape(m) + r'\b', texto, re.IGNORECASE):
                marca_encontrada = m
                break

        if marca_encontrada:
            if marca_encontrada in ["VW"]:
                marca_encontrada = "VOLKSWAGEN"
            elif marca_encontrada in ["MB", "M.BENZ", "MERCEDES", "MERCEDES BENZ"]:
                marca_encontrada = "MERCEDES-BENZ"
            elif marca_encontrada in ["GM"]:
                marca_encontrada = "CHEVROLET"

        return marca_encontrada, texto

    def _parse_bloco_item(self, bloco: str, fallback_idx: int) -> Optional[Dict[str, Any]]:
        # 1. Item Apólice
        item_match = re.search(r'Dados\s*do\s*Item\s*N[ºo\.]?\s*(\d+)', bloco, re.IGNORECASE)
        item_apolice = int(item_match.group(1)) if item_match else fallback_idx

        # 2. Placa e Chassi
        placa = None
        chassi = None
        
        licenca_chassi_match = re.search(
            r'Licen[çc]a\s+Chassi[^\n]*\n\s*([A-Z0-9\-]+)\s+([A-HJ-NPR-Z0-9]{17})',
            bloco,
            re.IGNORECASE
        )
        if licenca_chassi_match:
            placa = licenca_chassi_match.group(1).replace("-", "").strip()
            chassi = licenca_chassi_match.group(2).strip()
        else:
            placa_match = re.search(r'\b([A-Z]{3}[0-9][0-9A-Z][0-9]{2}|[A-Z]{3}-\d{4})\b', bloco)
            if placa_match:
                placa = placa_match.group(1).replace("-", "").strip()

            chassi_match = re.search(r'\b(?=[A-HJ-NPR-Z0-9]{17}\b)(?![0-9]{17}\b)(?![A-Z]{17}\b)[A-HJ-NPR-Z0-9]{17}\b', bloco)
            if chassi_match:
                chassi = chassi_match.group(0).strip()

        if not placa and not chassi:
            return None

        # 3. Código de Identificação (CI)
        codigo_identificacao = None
        ci_match = re.search(r'(?:C\s*I|C\.I\.|C[óo]digo\s*Identifica[çc][ãa]o)[^\n]*\n\s*([\d\.]+)', bloco, re.IGNORECASE)
        if ci_match:
            codigo_identificacao = ci_match.group(1).strip()

        # 4. Classe de Bônus
        classe_bonus = None
        bonus_match = re.search(r'Classe\s*de\s*B[ôo]nus[^\n]*\n\s*(\d{1,2})', bloco, re.IGNORECASE)
        if bonus_match:
            classe_bonus = int(bonus_match.group(1))

        # 5. Marca e Modelo
        raw_modelo = None
        modelo_match = re.search(r'Marca\/Tipo\s*Ve[íi]culo[^\n]*\n\s*([^\n]+)', bloco, re.IGNORECASE)
        if modelo_match:
            raw_modelo = modelo_match.group(1).strip()
        marca, modelo = self._separar_marca_modelo(raw_modelo)

        # 6. Ano Fabricação e Modelo
        ano_fabricacao = None
        ano_modelo = None
        ano_match = re.search(r'Ano\s*Fab[^\n]*\n\s*(\d{4})\s*[\/\-]\s*(\d{4})', bloco, re.IGNORECASE)
        if ano_match:
            ano_fabricacao = ano_match.group(1)
            ano_modelo = ano_match.group(2)
        else:
            ano_gen = re.search(r'\b(19\d\d|20\d\d)\s*[\/\-]\s*(19\d\d|20\d\d)\b', bloco)
            if ano_gen:
                ano_fabricacao = ano_gen.group(1)
                ano_modelo = ano_gen.group(2)

        # 7. Código FIPE
        codigo_fipe = None
        fipe_match = re.search(r'C[óo]digo\s*FIPE[^\n]*\n\s*(\d{6,8})', bloco, re.IGNORECASE)
        if fipe_match:
            codigo_fipe = fipe_match.group(1).strip()

        # 8. Casco (Compreensiva)
        casco_match = re.search(r'(?:Valor\s*de\s*Mercado|Compreensiva|Casco)[^\n]*\n\s*(?:R\$\s*)?([\d\.]+,\d{2})', bloco, re.IGNORECASE)
        valor_casco = self._converter_valor(casco_match.group(1)) if casco_match else None

        # 9. Coberturas RCF (LMI - Danos Materiais, Corporais, Morais e APP)
        rcf_dm_match = re.search(
            r'Danos\s*Materiais(?:\s*a\s*Terceiros)?[^\n]*\n\s*([\d\.]+,\d{2})',
            bloco,
            re.IGNORECASE
        )
        rcf_danos_materiais = self._converter_valor(rcf_dm_match.group(1)) if rcf_dm_match else None

        rcf_dc_match = re.search(
            r'Danos\s*Corporais(?:\s*a\s*Terceiros)?[^\n]*\n\s*([\d\.]+,\d{2})',
            bloco,
            re.IGNORECASE
        )
        rcf_danos_corporais = self._converter_valor(rcf_dc_match.group(1)) if rcf_dc_match else None

        dmo_match = re.search(
            r'Danos\s*Morais[^\n]*\n\s*([\d\.]+,\d{2})',
            bloco,
            re.IGNORECASE
        )
        danos_morais = self._converter_valor(dmo_match.group(1)) if dmo_match else None

        app_match = re.search(
            r'(?:APP|Acidentes\s*Pessoais(?:\s*a\s*Passageiros)?)[^\n]*\n\s*([\d\.]+,\d{2})',
            bloco,
            re.IGNORECASE
        )
        app_passageiros = self._converter_valor(app_match.group(1)) if app_match else None

        # 10. Vidros e Assistência
        # A coluna Vidros recebe o limite (LMI) da cobertura. O Bradesco só cita
        # Vidros nas cláusulas, sem valor; por isso fica vazia (decisão da corretora, 11/2026).
        cobertura_vidros = None
        
        assistencia = None
        if re.search(r'Reboque\s*Somente\s*para\s*Acidente', bloco, re.IGNORECASE):
            assistencia = "Reboque Acidente"
        elif re.search(r'(?:Assist[êe]ncia|Socorro|24\s*Horas|Guincho)', bloco, re.IGNORECASE):
            assistencia = "Incluso"

        return {
            "item_apolice": item_apolice,
            "placa": placa,
            "marca": marca,
            "modelo": modelo,
            "ano_fabricacao": ano_fabricacao,
            "ano_modelo": ano_modelo,
            "chassi": chassi,
            "classe_bonus": classe_bonus,
            "codigo_fipe": codigo_fipe,
            "valor_casco": valor_casco,
            "rcf_danos_materiais": rcf_danos_materiais,
            "rcf_danos_corporais": rcf_danos_corporais,
            "danos_morais": danos_morais,
            "app_passageiros": app_passageiros,
            "cobertura_vidros": cobertura_vidros,
            "assistencia": assistencia,
            "codigo_identificacao": codigo_identificacao
        }

    def _extrair_veiculos(self, texto: str) -> List[Dict[str, Any]]:
        itens = []
        blocos = re.split(r'(?=Dados\s*do\s*Item\s*N[ºo\.]?\s*\d+)', texto, flags=re.IGNORECASE)

        for idx, bloco in enumerate(blocos):
            if not re.search(r'Licen[çc]a\s+Chassi|Marca\/Tipo\s*Ve[íi]culo', bloco, re.IGNORECASE):
                continue
            item = self._parse_bloco_item(bloco, len(itens) + 1)
            if item:
                itens.append(item)

        if not itens:
            padrao_chassi = re.compile(r'\b(?=[A-HJ-NPR-Z0-9]{17}\b)(?![0-9]{17}\b)(?![A-Z]{17}\b)[A-HJ-NPR-Z0-9]{17}\b')
            for match in padrao_chassi.finditer(texto):
                pos = match.start()
                bloco = texto[max(0, pos - 500):min(len(texto), pos + 1000)]
                item = self._parse_bloco_item(bloco, len(itens) + 1)
                if item and not any(x["chassi"] == item["chassi"] for x in itens):
                    itens.append(item)

        return itens

    def parse(self, caminho_pdf: Optional[str] = None, texto: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        if not texto and caminho_pdf:
            paginas = []
            with pdfplumber.open(caminho_pdf) as pdf:
                for page in pdf.pages:
                    raw = page.extract_text() or ""
                    paginas.append(limpar_texto_duplicado(raw))
            texto = "\n".join(paginas)

        texto_limpo = texto or ""
        metadados = self._extrair_metadados(texto_limpo)
        itens = self._extrair_veiculos(texto_limpo)

        return {
            "seguradora": self.seguradora,
            "numero_apolice": metadados.get("numero_apolice"),
            "vigencia_inicio": metadados.get("vigencia_inicio"),
            "vigencia_fim": metadados.get("vigencia_fim"),
            "total_itens": len(itens),
            "premio_total": metadados.get("premio_total"),
            "itens": itens
        }
