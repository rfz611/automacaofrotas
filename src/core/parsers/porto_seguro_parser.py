import re
import unicodedata
from typing import Dict, Any, List, Optional, Tuple
import pdfplumber

from core.detection.signatures.porto_seguro import PORTO_SIGNATURE

try:
    from .base_parser import BaseParser
except ImportError:
    class BaseParser:
        pass


MONTADORAS = [
    "JAC MOTORS", "SCANIA VABIS", "NIJU",
    "VOLKSWAGEN", "VW", "CHEVROLET", "GM", "FIAT", "FORD", "TOYOTA", 
    "HYUNDAI", "RENAULT", "HONDA", "JEEP", "NISSAN", "MERCEDES-BENZ", 
    "MERCEDES BENZ", "M.BENZ", "MERCEDES", "MB", "SCANIA", "VOLVO", 
    "IVECO", "PEUGEOT", "CITROEN", "MITSUBISHI", "BMW", "AUDI", "DAF", 
    "MAN", "BYD", "GWM", "CHERY", "RODOFORT", "RANDON", "FACCHINI", 
    "GUERRA", "LIBRELATO", "NOMA", "KRONE", "TRIEL-HT", "PASTRE"
]


class PortoParser(BaseParser):
    seguradora = "Porto Seguro"

    _ITEM_RELACAO_RE = re.compile(r'(?m)^\s*(\d{1,4})\s+VEICULO:')
    _CODIGOS_ASSISTENCIA = {"45V"}

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

    def _limpar_cid(self, texto: str) -> str:
        if not texto:
            return ""
        return re.sub(r'\(cid:\d+\)', '', texto)

    def _texto_ascii(self, texto: str) -> str:
        """Remove acentos somente para tornar os rótulos do PDF previsíveis."""
        return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()

    def _buscar(self, padrao: str, texto: str) -> Optional[str]:
        match = re.search(padrao, texto, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extrair_valor_bloco(self, padrao: str, texto: str) -> Optional[float]:
        valor = self._buscar(padrao, texto)
        return self._converter_valor(valor)

    def _consolidar_blocos_relacao(self, paginas: List[str]) -> Dict[int, str]:
        """Agrupa trechos repetidos/continuados pelo número real do item.

        A relação completa da Porto pode começar um veículo no fim de uma página e
        repeti-lo na página seguinte apenas para continuar as coberturas. O bloco só
        fica completo depois que todos esses trechos são concatenados.
        """
        blocos: Dict[int, str] = {}
        ultimo_item: Optional[int] = None

        for pagina_original in paginas:
            pagina = self._texto_ascii(pagina_original)
            if "Indice de Cobertura:" in pagina:
                break

            marcadores = list(self._ITEM_RELACAO_RE.finditer(pagina))
            if not marcadores:
                # Páginas 10 e 12 do exemplo começam com a continuação do item
                # anterior, sem repetir a palavra VEICULO.
                if ultimo_item is not None and re.search(
                    r'\b(?:PLACA|CHASSI|ANO/MODELO|CASCO|DMT|DCT|DMO)\s*:',
                    pagina,
                    re.IGNORECASE,
                ):
                    blocos[ultimo_item] += "\n" + pagina
                continue

            preambulo = pagina[:marcadores[0].start()]
            if ultimo_item is not None and re.search(
                r'\b(?:PLACA|CHASSI|ANO/MODELO|CASCO|DMT|DCT|DMO)\s*:',
                preambulo,
                re.IGNORECASE,
            ):
                blocos[ultimo_item] += "\n" + preambulo

            for indice, marcador in enumerate(marcadores):
                item = int(marcador.group(1))
                fim = marcadores[indice + 1].start() if indice + 1 < len(marcadores) else len(pagina)
                trecho = pagina[marcador.start():fim]
                blocos[item] = blocos.get(item, "") + "\n" + trecho
                ultimo_item = item

        return blocos

    def _extrair_marca_modelo_bloco(self, item: int, bloco: str) -> Tuple[Optional[str], Optional[str]]:
        cabecalho = re.search(
            rf'(?m)^\s*{item}\s+VEICULO:\s*(.*?)\s+TIPO EMISSAO:[^\n]*$',
            bloco,
            re.IGNORECASE,
        )
        if not cabecalho:
            return None, None

        partes_modelo = [cabecalho.group(1).strip()]
        for linha in bloco[cabecalho.end():].splitlines():
            linha = linha.strip()
            if not linha:
                continue
            if "ANO/MODELO:" in linha or re.match(r'^\d+\s+VEICULO:', linha, re.IGNORECASE):
                break
            if linha.lower().startswith("item veiculo"):
                continue
            complemento = linha.split("REGIAO DE RISCO:", 1)[0].strip()
            if complemento:
                partes_modelo.append(complemento)

        marca_modelo = re.sub(r'\s+', ' ', ' '.join(partes_modelo)).strip()
        if " - " not in marca_modelo:
            return self._separar_marca_modelo(marca_modelo)

        marca, modelo = marca_modelo.split(" - ", 1)
        return marca.upper().strip(), modelo.strip()

    def _extrair_veiculos_relacao_completa(self, paginas: List[str]) -> List[Dict[str, Any]]:
        blocos = self._consolidar_blocos_relacao(paginas)
        if len(blocos) < 2:
            return []

        itens: List[Dict[str, Any]] = []
        for item, bloco in sorted(blocos.items()):
            placa = self._buscar(r'PLACA:\s*([A-Z]{3}-?[0-9][A-Z0-9][0-9]{2})', bloco)
            chassi = self._buscar(r'CHASSI:\s*([A-HJ-NPR-Z0-9]{17})', bloco)
            if not placa and not chassi:
                continue

            marca, modelo = self._extrair_marca_modelo_bloco(item, bloco)
            anos = re.search(r'ANO/MODELO:\s*(\d{4})\s*/\s*(\d{4})', bloco, re.IGNORECASE)

            codigos: List[str] = []
            for codigo in re.findall(r'Cls\.\s*([A-Z0-9]+)', bloco, re.IGNORECASE):
                codigo = codigo.upper()
                if codigo not in codigos:
                    codigos.append(codigo)

            valor_vidros = self._extrair_valor_bloco(
                r'Vidros\s+076\s*/\s*IS:\s*R\$\s*([\d.]+,\d{2})',
                bloco,
            )

            itens.append({
                "item_apolice": item,
                "placa": placa.replace("-", "") if placa else None,
                "marca": marca,
                "modelo": modelo,
                "ano_fabricacao": anos.group(1) if anos else None,
                "ano_modelo": anos.group(2) if anos else None,
                "chassi": chassi,
                "classe_bonus": int(self._buscar(r'CLASSE BONUS:\s*(\d{1,2})', bloco) or 0)
                if re.search(r'CLASSE BONUS:\s*\d{1,2}', bloco, re.IGNORECASE)
                else None,
                "codigo_fipe": self._buscar(r'CODIGO FIPE:\s*(\d+)', bloco),
                # No relatório da Porto, o valor solicitado na coluna Casco é a
                # franquia exibida na linha da cobertura CASCO.
                "valor_casco": self._extrair_valor_bloco(
                    r'CASCO[^\n]*FRANQUIA:\s*R\$\s*([\d.]+,\d{2})',
                    bloco,
                ),
                "rcf_danos_materiais": self._extrair_valor_bloco(
                    r'DMT(?:\s+DESAT)?\s+1R\s*-\s*IS\s*R\$\s*([\d.]+,\d{2})',
                    bloco,
                ),
                "rcf_danos_corporais": self._extrair_valor_bloco(
                    r'DCT(?:\s+DESAT)?\s+1R\s*-\s*IS\s*R\$\s*([\d.]+,\d{2})',
                    bloco,
                ),
                "danos_morais": self._extrair_valor_bloco(
                    r'DMO\s+1R\s*-\s*IS\s*R\$\s*([\d.]+,\d{2})',
                    bloco,
                ),
                "app_passageiros": self._extrair_valor_bloco(
                    r'APP[^\n]*-\s*IS\s*R\$\s*([\d.]+,\d{2})',
                    bloco,
                ),
                "cobertura_vidros": f"{valor_vidros:.2f}" if valor_vidros is not None else None,
                "assistencia": "Incluso" if self._CODIGOS_ASSISTENCIA.intersection(codigos) else None,
                "codigo_identificacao": " / ".join(codigos) if codigos else None,
            })

        return itens

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
        else:
            # Fallback: assume a primeira palavra como marca caso não conste na lista
            partes = texto.split()
            if partes:
                marca_encontrada = partes[0].upper()

        return marca_encontrada, texto

    def _extrair_metadados(self, texto: str) -> Dict[str, Any]:
        apolice_match = re.search(r'Ap[óo]lice\s*(?:n[ºo\.]?)?\s*[:\.\n]?\s*([\d\.\-\/]+)', texto, re.IGNORECASE)
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

    def _extrair_lmi_cobertura(self, texto: str, padrao_nome: str) -> Optional[float]:
        """Extrai o Limite Máximo de Indenização (LMI), ignorando franquia e prêmio/tarifa."""
        match = re.search(rf'{padrao_nome}[^\n]*', texto, re.IGNORECASE)
        if not match:
            return None
        
        linha = match.group(0)
        if "NÃO CONTRATAD" in linha.upper() or "NAO CONTRATAD" in linha.upper():
            return None

        # Pega a primeira ocorrência de R$ na linha (LMI)
        valor_match = re.search(r'R\$\s*([\d\.]+,\d{2})', linha)
        if valor_match:
            valor = self._converter_valor(valor_match.group(1))
            return valor if valor and valor > 0 else None
        return None

    def _extrair_franquia_casco(self, texto: str) -> Optional[float]:
        """Extrai a franquia da cobertura Casco no layout tabular da Porto."""
        match = re.search(
            r'(?:COLIS[ÃA]O|COMPREENSIVA|INC[ÊE]NDIO)[^\n]*',
            texto,
            re.IGNORECASE,
        )
        if not match:
            return None

        linha = match.group(0)
        if "NÃO CONTRATAD" in linha.upper() or "NAO CONTRATAD" in linha.upper():
            return None

        valores = re.findall(r'R\$\s*([\d\.]+,\d{2})', linha)
        if not valores:
            return None

        # Quando o LMI é textual (ex.: 100% FIPE), o primeiro valor monetário é a
        # franquia. Quando o LMI é um valor determinado, a franquia é o segundo.
        indice_franquia = 0 if re.search(r'(?:%\s*FIPE|VALOR\s+DE\s+MERCADO)', linha, re.IGNORECASE) else 1
        if indice_franquia >= len(valores):
            return None
        return self._converter_valor(valores[indice_franquia])

    def _extrair_veiculos_por_paginas(self, paginas: List[str]) -> List[Dict[str, Any]]:
        itens_relacao = self._extrair_veiculos_relacao_completa(paginas)
        if itens_relacao:
            return itens_relacao

        # Layout legado: usado pelo segundo PDF de exemplo, cujo texto é composto
        # majoritariamente por glifos (cid) e traz um veículo a cada duas páginas.
        itens = []
        i = 0
        while i < len(paginas):
            texto_pag = paginas[i]
            chassi_match = re.search(
                r'\b(?=[A-HJ-NPR-Z0-9]{15,17}\b)(?=[A-HJ-NPR-Z0-9]*[A-Z])(?=[A-HJ-NPR-Z0-9]*\d)[A-HJ-NPR-Z0-9]{15,17}\b',
                texto_pag,
            )
            placa_match = re.search(r'\b([A-Z]{3}[0-9][0-9A-Z][0-9]{2}|[A-Z]{3}-\d{4})\b', texto_pag)

            if chassi_match or placa_match:
                bloco_cadastro = texto_pag
                bloco_coberturas = paginas[i + 1] if (i + 1) < len(paginas) else ""

                chassi = chassi_match.group(0).strip() if chassi_match else None
                placa = placa_match.group(1).replace("-", "").strip() if placa_match else None

                # 1. Número do Item
                item_apolice = len(itens) + 1
                item_m = re.search(r'(?:Item|Item:)\s*(\d{1,4})', bloco_cadastro, re.IGNORECASE)
                if not item_m:
                    # Neste layout os rótulos são glifos (cid), mas o número do item
                    # permanece como a primeira linha composta apenas por dígitos.
                    item_m = re.search(r'(?m)^\s*(\d{1,4})\s*$', bloco_cadastro)
                if item_m:
                    try:
                        item_apolice = int(item_m.group(1))
                    except Exception:
                        pass

                # 2. Código de Identificação (CI)
                ci_match = re.search(r'\b(\d{2}\.\d{3}\.\d{3}\.\d{3}\.\d{2}-\d|\d{14,16})\b', bloco_cadastro)
                codigo_identificacao = ci_match.group(1).strip() if ci_match else None

                # 3. Ano Fabricação / Modelo
                ano_fabricacao, ano_modelo = None, None
                ano_match = re.search(r'\b(\d{4})\s*\/\s*(\d{4})\b', bloco_cadastro)
                if ano_match:
                    ano_fabricacao = ano_match.group(1)
                    ano_modelo = ano_match.group(2)

                # 4. Código FIPE
                codigo_fipe = None
                fipe_match = re.search(r'FIPE[^\d\n]*(\d{6,8})', bloco_cadastro, re.IGNORECASE)
                if fipe_match:
                    codigo_fipe = fipe_match.group(1).strip()
                else:
                    # Fallback para número FIPE isolado
                    fipe_iso = re.search(r'\b([0-9]{6,7})\b', bloco_cadastro)
                    if fipe_iso and fipe_iso.group(1) not in [ano_fabricacao, ano_modelo]:
                        codigo_fipe = fipe_iso.group(1)

                # 5. Classe de Bônus (Captura direta do rótulo)
                classe_bonus = None
                bonus_match = re.search(r'b[ôo]?nus[^\d\n]*[:\s]\s*(\d{1,2})', bloco_cadastro, re.IGNORECASE)
                if bonus_match:
                    classe_bonus = int(bonus_match.group(1))
                else:
                    # Fallback posicional
                    bonus_fallback = re.search(r'\n\s*(\d{1,2})\s*\n[^\n]*(?:REGIAO|ESTADO|CURITIBA)', bloco_cadastro, re.IGNORECASE)
                    if bonus_fallback:
                        classe_bonus = int(bonus_fallback.group(1))

                # 6. Marca e Modelo (captura o texto após o rótulo Veículo ou linhas com montadoras)
                raw_modelo = None
                modelo_match = re.search(r'Ve[íi]culo[^\n:]*[:\s]\s*([^\n]+)', bloco_cadastro, re.IGNORECASE)
                if modelo_match:
                    raw_modelo = modelo_match.group(1).strip()
                else:
                    linhas = [linha.strip() for linha in bloco_cadastro.splitlines() if linha.strip()]
                    for indice_linha, linha in enumerate(linhas):
                        if re.fullmatch(r'\d{4}\s*/\s*\d{4}', linha) and indice_linha > 0:
                            raw_modelo = linhas[indice_linha - 1]
                            break
                    if not raw_modelo:
                        for linha in linhas:
                            if any(m in linha.upper() for m in MONTADORAS) or "SEMI REBOQUE" in linha.upper():
                                raw_modelo = linha
                                break

                marca, modelo = self._separar_marca_modelo(raw_modelo)

                # 7. Coberturas - Limite Máximo de Indenização (LMI)
                valor_casco = self._extrair_franquia_casco(bloco_coberturas)
                rcf_danos_materiais = self._extrair_lmi_cobertura(bloco_coberturas, r'DANOS\s*MATERIAIS')
                rcf_danos_corporais = self._extrair_lmi_cobertura(bloco_coberturas, r'DANOS\s*CORPORAIS')
                danos_morais = self._extrair_lmi_cobertura(bloco_coberturas, r'DANOS\s*MORAIS')
                app_passageiros = self._extrair_lmi_cobertura(bloco_coberturas, r'(?:ACIDENTES\s*PESSOAIS|APP)')

                valor_vidros = self._extrair_lmi_cobertura(bloco_coberturas, r'DANOS\s*AOS\s*VIDROS')
                cobertura_vidros = f"{valor_vidros:.2f}" if valor_vidros is not None else None
                assistencia = "Incluso" if re.search(r'ASSIST[ÊE]NCIA\s*24H', bloco_coberturas, re.IGNORECASE) else None

                item_dict = {
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

                duplicado = any(
                    (chassi and x.get("chassi") == chassi)
                    or (placa and x.get("placa") == placa)
                    for x in itens
                )
                if (chassi or placa) and not duplicado:
                    itens.append(item_dict)

                if "Cobe" in bloco_coberturas or "Franquia" in bloco_coberturas:
                    i += 2
                    continue
            i += 1

        return itens

    def parse(self, caminho_pdf: Optional[str] = None, texto: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        paginas_limpas = []
        if caminho_pdf:
            with pdfplumber.open(caminho_pdf) as pdf:
                for p in pdf.pages:
                    raw = p.extract_text() or ""
                    paginas_limpas.append(self._limpar_cid(raw))
        elif texto:
            paginas_limpas = [self._limpar_cid(texto)]

        texto_completo = "\n".join(paginas_limpas)
        metadados = self._extrair_metadados(texto_completo)
        itens = self._extrair_veiculos_por_paginas(paginas_limpas)

        return {
            "seguradora": self.seguradora,
            "numero_apolice": metadados.get("numero_apolice"),
            "vigencia_inicio": metadados.get("vigencia_inicio"),
            "vigencia_fim": metadados.get("vigencia_fim"),
            "total_itens": len(itens),
            "premio_total": metadados.get("premio_total"),
            "itens": itens
        }


# Aliases para compatibilidade de import
PortoSeguroParser = PortoParser
