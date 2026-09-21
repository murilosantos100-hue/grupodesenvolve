"""Testes de history_csv.py -- roda com `python3 test_history_csv.py`."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agente_cfo import history_csv


def test_parse_csv_vazio():
    assert history_csv.parse_history_csv("") == []
    assert history_csv.parse_history_csv("   ") == []


def test_roundtrip_format_e_parse():
    rows = [
        {
            "data_execucao": "2026-09-05",
            "periodo_referencia": "2026-08",
            "entidade": "Desenvolve Consultoria e Hospitais",
            "metrica": "caixa_atual",
            "valor": 185000.5,
            "status_alerta": "ok",
        }
    ]
    text = history_csv.format_history_csv(rows)
    parsed = history_csv.parse_history_csv(text)
    assert len(parsed) == 1
    assert parsed[0]["valor"] == 185000.5
    assert parsed[0]["metrica"] == "caixa_atual"


def test_append_rows_nunca_perde_linhas_antigas():
    existing = history_csv.format_history_csv([{
        "data_execucao": "2026-08-05", "periodo_referencia": "2026-07",
        "entidade": "X", "metrica": "caixa_atual", "valor": 100.0, "status_alerta": "ok",
    }])
    new_text = history_csv.append_rows(existing, [{
        "data_execucao": "2026-09-05", "periodo_referencia": "2026-08",
        "entidade": "X", "metrica": "caixa_atual", "valor": 200.0, "status_alerta": "ok",
    }])
    rows = history_csv.parse_history_csv(new_text)
    assert len(rows) == 2
    assert rows[0]["periodo_referencia"] == "2026-07"
    assert rows[1]["periodo_referencia"] == "2026-08"


def test_kpis_to_history_rows_ignora_none():
    kpis = {
        "caixa_atual": 1000.0,
        "runway_dias": float("inf"),
        "runway_alerta": "ok",
        "margem_ebitda": None,
        "desvio_orcamentario": None,
        "contas_a_receber_vencidas": 0.0,
    }
    rows = history_csv.kpis_to_history_rows("2026-09-05", "2026-08", "X", kpis)
    metricas = {r["metrica"] for r in rows}
    assert "caixa_atual" in metricas
    assert "runway_dias" in metricas
    assert "margem_ebitda" not in metricas  # None nao vira linha


def test_trend_for_metric_ordena_e_limita():
    rows = [
        {"data_execucao": "d", "periodo_referencia": p, "entidade": "X",
         "metrica": "caixa_atual", "valor": float(i), "status_alerta": "ok"}
        for i, p in enumerate(["2026-05", "2026-07", "2026-06"])
    ]
    trend = history_csv.trend_for_metric(rows, "X", "caixa_atual", n=2)
    periodos = [r["periodo_referencia"] for r in trend]
    assert periodos == ["2026-06", "2026-07"]


def run_all():
    tests = [obj for name, obj in globals().items() if name.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passaram")
    return failed


if __name__ == "__main__":
    raise SystemExit(1 if run_all() else 0)
