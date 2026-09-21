"""Leitura/escrita do formato longo de /Resultados/Historico_Avaliacoes.csv.

Funcoes puras sobre texto CSV em memoria -- quem baixa/sobe o arquivo do
Drive e a skill (via MCP), nao este modulo. Ver spec secao 5.
"""
from __future__ import annotations

import csv
import io

HEADER = ["data_execucao", "periodo_referencia", "entidade", "metrica", "valor", "status_alerta"]


def parse_history_csv(text: str) -> list[dict]:
    """Le o CSV completo (com cabecalho) e devolve lista de dicts.
    Texto vazio ou so cabecalho devolve lista vazia.
    """
    if not text or not text.strip():
        return []
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        row["valor"] = float(row["valor"])
        rows.append(row)
    return rows


def format_history_csv(rows: list[dict]) -> str:
    """Serializa a lista completa de linhas (ja incluindo as antigas) de
    volta para texto CSV, com cabecalho.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=HEADER)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row[k] for k in HEADER})
    return buf.getvalue()


def kpis_to_history_rows(
    data_execucao: str,
    periodo_referencia: str,
    entidade: str,
    kpis: dict,
) -> list[dict]:
    """Achata o dict de KPIs (saida de kpis.calcular_todos_kpis) em linhas
    do formato longo do historico. Metricas sem valor numerico simples
    (ex: projecao semana a semana, desvio orcamentario detalhado) sao
    resumidas, nao explodidas linha a linha, para manter o CSV legivel.
    """
    rows = []

    def add(metrica: str, valor, status_alerta: str = "n/a"):
        if valor is None:
            return
        rows.append({
            "data_execucao": data_execucao,
            "periodo_referencia": periodo_referencia,
            "entidade": entidade,
            "metrica": metrica,
            "valor": float(valor),
            "status_alerta": status_alerta,
        })

    add("caixa_atual", kpis.get("caixa_atual"))

    runway = kpis.get("runway_dias")
    if runway is not None:
        runway_valor = 99999 if runway == float("inf") else runway
        add("runway_dias", runway_valor, kpis.get("runway_alerta", "n/a"))

    add("margem_ebitda", kpis.get("margem_ebitda"))
    add("contas_a_receber_vencidas", kpis.get("contas_a_receber_vencidas"))

    desvio = kpis.get("desvio_orcamentario")
    if desvio:
        for item in desvio:
            if item["desvio_pct"] is not None:
                add(f"desvio_orcamentario_{item['account']}", item["desvio_pct"])

    return rows


def append_rows(existing_text: str, new_rows: list[dict]) -> str:
    """Nunca sobrescreve: devolve o CSV completo = linhas existentes + novas."""
    existing_rows = parse_history_csv(existing_text)
    return format_history_csv(existing_rows + new_rows)


def trend_for_metric(rows: list[dict], entidade: str, metrica: str, n: int = 12) -> list[dict]:
    """Ultimas `n` observacoes de uma metrica para uma entidade, ordenadas
    por periodo_referencia crescente (para plotar/tabelar evolucao).
    """
    filtrado = [
        r for r in rows
        if r["entidade"] == entidade and r["metrica"] == metrica
    ]
    filtrado.sort(key=lambda r: r["periodo_referencia"])
    return filtrado[-n:]
