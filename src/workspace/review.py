"""Contagem de pendências para a lista de documentos.

Espelha as regras de src/web/lib/review.ts (a tela de revisão). Mantenha as duas iguais.
"""
import re
import time

FIELDS = ("item_apolice", "placa", "marca", "modelo", "ano_fabricacao", "ano_modelo", "chassi", "classe_bonus",
          "codigo_fipe", "valor_casco", "rcf_danos_materiais", "rcf_danos_corporais", "danos_morais",
          "app_passageiros", "cobertura_vidros", "assistencia", "codigo_identificacao")
REQUIRED = set(FIELDS[:8])
INTEGER = {"item_apolice", "ano_fabricacao", "ano_modelo", "classe_bonus"}
MONEY = {"valor_casco", "rcf_danos_materiais", "rcf_danos_corporais", "danos_morais", "app_passageiros", "cobertura_vidros"}


def _text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def _key(value):
    return re.sub(r"[\s-]", "", _text(value).upper())


def vehicle_issues(rows):
    """Lista, por veículo, o conjunto de campos com pendência."""
    seen = {}
    for index, row in enumerate(rows):
        for field in ("item_apolice", "placa", "chassi"):
            value = _key(row.get(field))
            if value:
                seen.setdefault((field, value), []).append(index)
    max_year = time.localtime().tm_year + 1
    result = []
    for index, row in enumerate(rows):
        issues = set()
        for field in FIELDS:
            value = _text(row.get(field))
            if not value:
                if field in REQUIRED:
                    issues.add(field)
                continue
            if field in INTEGER and not re.fullmatch(r"\d+", value):
                issues.add(field)
                continue
            if field in MONEY and not re.fullmatch(r"\d+(?:\.\d{1,2})?", value):
                issues.add(field)
                continue
            if field == "placa" and not re.fullmatch(r"[A-Z]{3}(?:\d{4}|\d[A-Z]\d{2})", _key(value)):
                issues.add(field)
            if field == "chassi" and not re.fullmatch(r"[A-Za-z0-9]{17}", value):
                issues.add(field)
            if field == "classe_bonus" and int(value) > 10:
                issues.add(field)
            if field in ("ano_fabricacao", "ano_modelo") and not 1960 <= int(value) <= max_year:
                issues.add(field)
            if field == "item_apolice" and int(value) != index + 1:
                issues.add(field)
        fab, mod = _text(row.get("ano_fabricacao")), _text(row.get("ano_modelo"))
        if fab.isdigit() and mod.isdigit() and int(fab) and int(mod) and not int(fab) <= int(mod) <= int(fab) + 1:
            issues.add("ano_modelo")
        for field in ("item_apolice", "placa", "chassi"):
            if len(seen.get((field, _key(row.get(field))), [])) > 1:
                issues.add(field)
        for flag in row.get("flags_atencao") or []:
            for field in FIELDS:
                if (flag == field or flag.startswith(field + "_")) and field not in REQUIRED:
                    issues.add(field)
                    break
        result.append(issues)
    return result


def pending_count(rows):
    """Número de células com pendência (o mesmo número mostrado na tela de revisão)."""
    return sum(len(issues) for issues in vehicle_issues(rows))
