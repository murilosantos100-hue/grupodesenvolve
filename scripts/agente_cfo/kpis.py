"""Calculo deterministico de KPIs financeiros do Agente CFO.

Toda funcao aqui e pura: recebe listas de dict (cash_flow_entry / dre_line,
ja validados por schema.py) e devolve numeros ou estruturas de dado. Nenhuma
chamada de rede, nenhuma leitura de arquivo, nenhum uso de LLM para
matematica -- isso e deliberado (ver spec secao 7): o Claude extrai e
normaliza os dados, este modulo calcula, para nao arriscar erro aritmetico
de um modelo de linguagem em numero que vai pro Murilo e pro Diego.

Ver docs/agente-cfo/spec-funcional-tecnica-v1.md secao 3 para a definicao
funcional de cada KPI e suas limitacoes conhecidas.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

INFINITO = float("inf")


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _signed_amount(entry: dict) -> float:
    amount = float(entry["amount"])
    return amount if entry["type"] == "entrada" else -amount


def saldo_atual(entries: list[dict], as_of: str | None = None) -> float:
    """Soma de entradas menos saidas realizadas, ate (e incluindo) `as_of`.

    `as_of` no formato 'AAAA-MM-DD'. Se None, considera todos os lancamentos
    'realizado' presentes.
    """
    limite = _parse_date(as_of) if as_of else None
    total = 0.0
    for entry in entries:
        if entry["status"] != "realizado":
            continue
        if limite is not None and _parse_date(entry["date"]) > limite:
            continue
        total += _signed_amount(entry)
    return round(total, 2)


def queima_media_diaria(entries: list[dict], as_of: str, window_days: int = 30) -> float:
    """Media diaria de saida liquida (saida - entrada) nos ultimos `window_days`
    dias realizados antes de `as_of` (inclusive). Retorna numero negativo se
    o fluxo liquido do periodo foi positivo (caixa entrando mais do que saindo).
    """
    limite = _parse_date(as_of)
    inicio = limite - timedelta(days=window_days - 1)
    net_saida = 0.0
    for entry in entries:
        if entry["status"] != "realizado":
            continue
        d = _parse_date(entry["date"])
        if inicio <= d <= limite:
            net_saida += -_signed_amount(entry)
    return round(net_saida / window_days, 2)


def runway_dias(entries: list[dict], as_of: str, window_days: int = 30) -> float:
    """Dias de caixa restantes ao ritmo de queima observado nos ultimos
    `window_days` dias. Retorna float('inf') se a queima media for <= 0
    (caixa estavel ou crescendo) -- nesse caso NAO ha um numero finito de
    dias e o relatorio deve dizer "sem risco de runway", nao imprimir 'inf'.
    """
    caixa = saldo_atual(entries, as_of=as_of)
    queima = queima_media_diaria(entries, as_of=as_of, window_days=window_days)
    if queima <= 0:
        return INFINITO
    if caixa <= 0:
        return 0.0
    return round(caixa / queima, 1)


def classificar_alerta_runway(dias: float, critico: int = 30, atencao: int = 60) -> str:
    if dias == INFINITO:
        return "ok"
    if dias < critico:
        return "critico"
    if dias < atencao:
        return "atencao"
    return "ok"


def projecao_13_semanas(entries: list[dict], as_of: str, semanas: int = 13) -> list[dict]:
    """Projeta saldo semana a semana usando a media semanal de fluxo liquido
    OBSERVADO (realizado) nos ultimos 90 dias antes de `as_of`.

    LIMITACAO CONHECIDA (deve ir explicita no relatorio, nao em rodape):
    nao inclui contratos futuros nem folha de pagamento prevista -- gaps #3
    do brief. Projecao e sistematicamente otimista ate essas fontes existirem.
    """
    limite = _parse_date(as_of)
    inicio = limite - timedelta(days=89)
    net_total = 0.0
    for entry in entries:
        if entry["status"] != "realizado":
            continue
        d = _parse_date(entry["date"])
        if inicio <= d <= limite:
            net_total += _signed_amount(entry)
    media_semanal = net_total / (90 / 7)

    saldo = saldo_atual(entries, as_of=as_of)
    resultado = []
    for semana in range(1, semanas + 1):
        saldo += media_semanal
        resultado.append({
            "semana": semana,
            "saldo_projetado": round(saldo, 2),
        })
    return resultado


def margem_ebitda(dre_lines: list[dict]) -> float | None:
    ebitda = _find_dre_value(dre_lines, "ebitda")
    receita_liquida = _find_dre_value(dre_lines, "receita_liquida")
    if ebitda is None or receita_liquida in (None, 0):
        return None
    return round(ebitda / receita_liquida, 4)


def _find_dre_value(dre_lines: list[dict], account: str) -> float | None:
    for line in dre_lines:
        if line["account"] == account:
            return float(line["value"])
    return None


def desvio_orcamentario(dre_lines: list[dict]) -> list[dict] | None:
    """Retorna lista de {account, realizado, orcado, desvio_pct} para as
    contas que tem `budgeted_value` preenchido. Retorna None se NENHUMA
    linha tiver orcamento -- caso atual desta unidade (gap #1 do brief):
    so existe orcamento anual consolidado do grupo, sem quebra por
    unidade/mes. O relatorio deve reportar essa ausencia explicitamente,
    nunca omitir a secao silenciosamente.
    """
    resultado = []
    for line in dre_lines:
        orcado = line.get("budgeted_value")
        if orcado is None:
            continue
        realizado = float(line["value"])
        desvio_pct = None if orcado == 0 else round((realizado - orcado) / orcado, 4)
        resultado.append({
            "account": line["account"],
            "realizado": realizado,
            "orcado": float(orcado),
            "desvio_pct": desvio_pct,
        })
    return resultado or None


def contas_a_receber_vencidas(entries: list[dict], as_of: str) -> float:
    limite = _parse_date(as_of)
    total = 0.0
    for entry in entries:
        if entry["type"] != "entrada" or entry["status"] != "previsto":
            continue
        if _parse_date(entry["date"]) < limite:
            total += float(entry["amount"])
    return round(total, 2)


def calcular_todos_kpis(
    cash_flow_entries: list[dict],
    dre_lines: list[dict],
    as_of: str,
    alert_thresholds: dict | None = None,
) -> dict:
    """Ponto de entrada unico usado pela skill: calcula todos os KPIs de
    uma vez e ja aplica a classificacao de alerta. `as_of` e a data de
    execucao ('AAAA-MM-DD'), nao o periodo de referencia.
    """
    thresholds = alert_thresholds or {}
    critico = thresholds.get("runway_dias_critico", 30)
    atencao = thresholds.get("runway_dias_atencao", 60)

    dias_runway = runway_dias(cash_flow_entries, as_of=as_of)

    return {
        "caixa_atual": saldo_atual(cash_flow_entries, as_of=as_of),
        "runway_dias": dias_runway,
        "runway_alerta": classificar_alerta_runway(dias_runway, critico=critico, atencao=atencao),
        "projecao_13_semanas": projecao_13_semanas(cash_flow_entries, as_of=as_of),
        "margem_ebitda": margem_ebitda(dre_lines),
        "desvio_orcamentario": desvio_orcamentario(dre_lines),
        "contas_a_receber_vencidas": contas_a_receber_vencidas(cash_flow_entries, as_of=as_of),
    }
