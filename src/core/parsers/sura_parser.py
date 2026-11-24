import re
from typing import Dict, Any, List, Optional, Tuple
import pdfplumber

from core.detection.signatures.sura import SURA_SIGNATURE

try:
    from .base_parser import BaseParser
except ImportError:
    class BaseParser:
        pass


ROMAN_TO_INT = {
    "0": 0, "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "ZERO": 0,
}


class SuraParser(BaseParser):
    seguradora = "Seguros Sura"

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

    def _converter_bonus(self, bonus_str: Optional[str]) -> Optional[int]:
        if not bonus_str:
            return None
        b_clean = bonus_str.strip().upper()
        if b_clean.isdigit():
            return int(b_clean)
        return ROMAN_TO_INT.get(b_clean, None)

    def _extrair_metadados(self, texto: str) -> Dict[str, Any]:
        apolice_match = re.search(r'Ap[óo]lice\s*:\s*([\d\.\-\/]+)', texto, re.IGNORECASE)
        numero_apolice = apolice_match.group(1).strip() if apolice_match else None

        vigencia_match = re.search(
            r'(\d{2}/\d{2}/\d{4})\s*(?:[aà\s]+|\s*at[ée]\s*)\s*(?:24:00hs\s*do\s*dia\s*)?(\d{2}/\d{2}/\d{4})',
            texto,
            re.IGNORECASE
        )
        vigencia_inicio = vigencia_match.group(1) if vigencia_match else None
        vigencia_fim = vigencia_match.group(2) if vigencia_match else None

        premio_match = re.search(r'Total\s*[:\.]?\s*(?:R\$\s*)?([\d\.]+,\d{2})', texto, re.IGNORECASE)
        premio_total = self._converter_valor(premio_match.group(1)) if premio_match else None

        return {
            "numero_apolice": numero_apolice,
            "vigencia_inicio": vigencia_inicio,
            "vigencia_fim": vigencia_fim,
            "premio_total": premio_total,
        }

    def _extrair_lmi_cobertura(self, bloco: str, nome_cobertura: str) -> Optional[float]:
        padrao = nome_cobertura + r'\s+([\d\.]+,\d{2})'
        match = re.search(padrao, bloco, re.IGNORECASE)
        if match:
            return self._converter_valor(match.group(1))
        return None

    def _parse_bloco_item(self, bloco: str, fallback_idx: int) -> Optional[Dict[str, Any]]:
        # 1. Item Apólice
        item_match = re.search(r'Item\s*:\s*(\d+)', bloco, re.IGNORECASE)
        item_apolice = int(item_match.group(1)) if item_match else fallback_idx

        # 2. Placa e Chassi
        placa = None
        chassi = None

        placa_match = re.search(r'Placa\s*:\s*([A-Z0-9\-]+)', bloco, re.IGNORECASE)
        if placa_match:
            placa = placa_match.group(1).replace("-", "").strip()

        chassi_match = re.search(r'Chassi\s*:\s*([A-HJ-NPR-Z0-9]{17})', bloco, re.IGNORECASE)
        if chassi_match:
            chassi = chassi_match.group(1).strip()
        else:
            chassi_gen = re.search(r'\b(?=[A-HJ-NPR-Z0-9]{17}\b)(?![0-9]{17}\b)(?![A-Z]{17}\b)[A-HJ-NPR-Z0-9]{17}\b', bloco)
            if chassi_gen:
                chassi = chassi_gen.group(0).strip()

        if not placa and not chassi:
            return None

        # 3. Código de Identificação (CI)
        ci_match = re.search(r'CI\s*:\s*([\d\.\-]+)', bloco, re.IGNORECASE)
        codigo_identificacao = ci_match.group(1).strip() if ci_match else None

        # 4. Marca e Modelo
        marca = None
        modelo = None
        marca_match = re.search(r'Marca\s*:\s*([A-Za-z0-9\-\.\s]+?)\s+Modelo\s*:\s*([^\n]+)', bloco, re.IGNORECASE)
        if marca_match:
            marca = marca_match.group(1).strip()
            modelo = marca_match.group(2).strip()

        # 5. Ano Fabricação e Modelo
        ano_fabricacao = None
        ano_modelo = None
        ano_match = re.search(r'Ano\s*Fabr/mod\s*:\s*(\d{4})\s*[\/\-]\s*(\d{4})', bloco, re.IGNORECASE)
        if ano_match:
            ano_fabricacao = ano_match.group(1)
            ano_modelo = ano_match.group(2)

        # 6. Classe de Bônus
        classe_bonus = None
        bonus_match = re.search(r'Classe\s*de\s*B[ôo]nus\s*:\s*([0-9A-Z]+)', bloco, re.IGNORECASE)
        if bonus_match:
            classe_bonus = self._converter_bonus(bonus_match.group(1))

        # 7. Código FIPE
        codigo_fipe = None
        fipe_match = re.search(r'FIPE[^\d\n]*(\d{6,8})', bloco, re.IGNORECASE)
        if fipe_match:
            codigo_fipe = fipe_match.group(1).strip()

        # 8. Casco: no layout Sura, após o fator de ajuste aparecem a franquia e
        # o prêmio. A coluna CASCO da planilha recebe a franquia, nunca um zero
        # sintético nem o prêmio.
        valor_casco = None
        casco_match = re.search(r'^\s*Casco[^\n]*$', bloco, re.IGNORECASE | re.MULTILINE)
        if casco_match:
            valores_monetarios = re.findall(
                r'(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}', casco_match.group(0)
            )
            if valores_monetarios:
                valor_casco = self._converter_valor(valores_monetarios[0])

        # 9. Coberturas LMI
        rcf_danos_materiais = self._extrair_lmi_cobertura(bloco, r'Danos\s*Materiais')
        rcf_danos_corporais = self._extrair_lmi_cobertura(bloco, r'Danos\s*Corporais')
        danos_morais = self._extrair_lmi_cobertura(bloco, r'Danos\s*Morais')
        app_passageiros = self._extrair_lmi_cobertura(bloco, r'(?:APP|Acidentes\s*Pessoais)')

        # 10. Vidros e Assistência
        # A Sura lista Vidros como serviço contratado, só com o prêmio, sem limite (LMI).
        # A coluna Vidros recebe o limite da cobertura; sem limite no PDF, fica vazia (decisão da corretora, 11/2026).
        cobertura_vidros = None

        assistencia = None
        assist_match = re.search(r'Assist[êe]ncia\s*24h\s*([^\n\d]+)', bloco, re.IGNORECASE)
        if assist_match:
            assistencia = assist_match.group(1).strip()
        elif re.search(r'Assist[êe]ncia\s*Caminh[ãa]o\s*([^\n\d]+)', bloco, re.IGNORECASE):
            assist_caminhao = re.search(r'Assist[êe]ncia\s*Caminh[ãa]o\s*([^\n\d]+)', bloco, re.IGNORECASE)
            assistencia = f"Caminhão {assist_caminhao.group(1).strip()}"

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
        blocos = re.split(r'(?=Item\s*:\s*\d+)', texto, flags=re.IGNORECASE)

        for bloco in blocos:
            if not re.search(r'DADOS\s*DO\s*AUTOM[ÓO]VEL|Placa\s*:', bloco, re.IGNORECASE):
                continue
            item = self._parse_bloco_item(bloco, len(itens) + 1)
            if item and item.get("chassi") and not any(x["chassi"] == item["chassi"] for x in itens):
                itens.append(item)

        return itens

    def parse(self, caminho_pdf: Optional[str] = None, texto: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        paginas = []
        if caminho_pdf:
            with pdfplumber.open(caminho_pdf) as pdf:
                for p in pdf.pages:
                    paginas.append(p.extract_text() or "")
        elif texto:
            paginas = [texto]

        texto_completo = "\n".join(paginas)
        metadados = self._extrair_metadados(texto_completo)
        itens = self._extrair_veiculos(texto_completo)

        return {
            "seguradora": self.seguradora,
            "numero_apolice": metadados.get("numero_apolice"),
            "vigencia_inicio": metadados.get("vigencia_inicio"),
            "vigencia_fim": metadados.get("vigencia_fim"),
            "total_itens": len(itens),
            "premio_total": metadados.get("premio_total"),
            "itens": itens
        }


# Aliases para import
SuraSegurosParser = SuraParser
