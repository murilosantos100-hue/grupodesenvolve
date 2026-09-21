"""Schema e validacao dos dados normalizados do Agente CFO.

Nenhuma funcao aqui faz I/O de rede ou arquivo. Ver
docs/agente-cfo/spec-funcional-tecnica-v1.md secao 2 para a definicao
funcional de cada campo.
"""
from __future__ import annotations

CASH_FLOW_TYPES = ("entrada", "saida")
CASH_FLOW_STATUS = ("realizado", "previsto")
CASH_FLOW_ORIGENS = ("extrato", "nota_fiscal", "outro")

DRE_ACCOUNTS = (
    "receita_bruta",
    "deducoes",
    "receita_liquida",
    "custos_servicos",
    "despesas_operacionais",
    "despesas_pessoal",
    "ebitda",
    "resultado_financeiro",
    "resultado_liquido",
)

_REQUIRED_CASH_FLOW_FIELDS = (
    "id", "entity", "period", "date", "type", "status",
    "category", "amount", "origem", "source_file_id", "source_file_name",
)

_REQUIRED_DRE_FIELDS = (
    "id", "entity", "period", "account", "value",
    "source_file_id", "source_file_name",
)


def validate_cash_flow_entry(entry: dict) -> list[str]:
    """Retorna lista de erros (vazia se valido)."""
    errors = []
    for field in _REQUIRED_CASH_FLOW_FIELDS:
        if field not in entry or entry[field] in (None, ""):
            errors.append(f"campo obrigatorio ausente: {field}")

    if "type" in entry and entry["type"] not in CASH_FLOW_TYPES:
        errors.append(f"type invalido: {entry['type']!r} (esperado {CASH_FLOW_TYPES})")

    if "status" in entry and entry["status"] not in CASH_FLOW_STATUS:
        errors.append(f"status invalido: {entry['status']!r} (esperado {CASH_FLOW_STATUS})")

    if "origem" in entry and entry["origem"] not in CASH_FLOW_ORIGENS:
        errors.append(f"origem invalida: {entry['origem']!r} (esperado {CASH_FLOW_ORIGENS})")

    if "amount" in entry:
        try:
            if float(entry["amount"]) < 0:
                errors.append("amount deve ser positivo (o sinal vem de 'type')")
        except (TypeError, ValueError):
            errors.append(f"amount nao numerico: {entry['amount']!r}")

    for date_field in ("date",):
        if date_field in entry and entry[date_field]:
            if not _looks_like_date(entry[date_field]):
                errors.append(f"{date_field} nao parece 'AAAA-MM-DD': {entry[date_field]!r}")

    if "period" in entry and entry["period"] and not _looks_like_period(entry["period"]):
        errors.append(f"period nao parece 'AAAA-MM': {entry['period']!r}")

    return errors


def validate_dre_line(line: dict) -> list[str]:
    errors = []
    for field in _REQUIRED_DRE_FIELDS:
        if field not in line or line[field] in (None, ""):
            errors.append(f"campo obrigatorio ausente: {field}")

    if "account" in line and line["account"] not in DRE_ACCOUNTS:
        errors.append(
            f"account nao reconhecida: {line['account']!r} (esperado uma de {DRE_ACCOUNTS})"
        )

    if "value" in line:
        try:
            float(line["value"])
        except (TypeError, ValueError):
            errors.append(f"value nao numerico: {line['value']!r}")

    if line.get("budgeted_value") is not None:
        try:
            float(line["budgeted_value"])
        except (TypeError, ValueError):
            errors.append(f"budgeted_value nao numerico: {line['budgeted_value']!r}")

    if "period" in line and line["period"] and not _looks_like_period(line["period"]):
        errors.append(f"period nao parece 'AAAA-MM': {line['period']!r}")

    return errors


def _looks_like_date(value: str) -> bool:
    parts = value.split("-")
    return len(parts) == 3 and all(p.isdigit() for p in parts) and len(parts[0]) == 4


def _looks_like_period(value: str) -> bool:
    parts = value.split("-")
    return len(parts) == 2 and all(p.isdigit() for p in parts) and len(parts[0]) == 4
