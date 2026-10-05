"""Testes de kpis.py -- sem pytest, roda com `python3 test_kpis.py`."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from agente_cfo import kpis


def entry(date, type_, status, amount, category="geral"):
    return {
        "id": f"{date}-{type_}-{amount}",
        "entity": "Desenvolve Consultoria e Hospitais",
        "period": date[:7],
        "date": date,
        "type": type_,
        "status": status,
        "category": category,
        "amount": amount,
        "origem": "extrato",
        "source_file_id": "fid",
        "source_file_name": "extrato.pdf",
    }


def dre(account, value, budgeted_value=None):
    return {
        "id": f"dre-{account}",
        "entity": "Desenvolve Consultoria e Hospitais",
        "period": "2026-08",
        "account": account,
        "value": value,
        "budgeted_value": budgeted_value,
        "source_file_id": "fid",
        "source_file_name": "dre.pdf",
    }


def test_saldo_atual_soma_entradas_e_saidas():
    entries = [
        entry("2026-08-01", "entrada", "realizado", 10000),
        entry("2026-08-05", "saida", "realizado", 3000),
        entry("2026-08-10", "entrada", "previsto", 50000),  # nao entra: previsto
    ]
    assert kpis.saldo_atual(entries, as_of="2026-08-31") == 7000


def test_saldo_atual_respeita_as_of():
    entries = [
        entry("2026-08-01", "entrada", "realizado", 10000),
        entry("2026-09-01", "saida", "realizado", 3000),
    ]
    assert kpis.saldo_atual(entries, as_of="2026-08-31") == 10000


def test_runway_dias_com_queima_positiva():
    entries = [entry("2026-08-01", "entrada", "realizado", 30000)]
    for d in range(2, 32):
        entries.append(entry(f"2026-08-{d:02d}", "saida", "realizado", 100))
    dias = kpis.runway_dias(entries, as_of="2026-08-31", window_days=30)
    assert dias > 0
    assert dias != float("inf")


def test_runway_infinito_quando_caixa_estavel_ou_crescendo():
    entries = [
        entry("2026-08-01", "entrada", "realizado", 100000),
        entry("2026-08-05", "entrada", "realizado", 5000),
        entry("2026-08-10", "saida", "realizado", 1000),
    ]
    dias = kpis.runway_dias(entries, as_of="2026-08-31")
    assert dias == float("inf")
    assert kpis.classificar_alerta_runway(dias) == "ok"


def test_classificar_alerta_runway_thresholds():
    assert kpis.classificar_alerta_runway(10) == "critico"
    assert kpis.classificar_alerta_runway(45) == "atencao"
    assert kpis.classificar_alerta_runway(90) == "ok"
    assert kpis.classificar_alerta_runway(29.9) == "critico"
    assert kpis.classificar_alerta_runway(30) == "atencao"


def test_margem_ebitda():
    lines = [dre("receita_liquida", 100000), dre("ebitda", 20000)]
    assert kpis.margem_ebitda(lines) == 0.2


def test_margem_ebitda_none_sem_dre():
    assert kpis.margem_ebitda([]) is None


def test_desvio_orcamentario_none_quando_sem_orcado():
    lines = [dre("receita_liquida", 100000), dre("custos_servicos", -40000)]
    assert kpis.desvio_orcamentario(lines) is None


def test_desvio_orcamentario_calcula_quando_disponivel():
    lines = [dre("despesas_pessoal", -55000, budgeted_value=-50000)]
    resultado = kpis.desvio_orcamentario(lines)
    assert resultado is not None
    assert resultado[0]["desvio_pct"] == 0.1


def test_contas_a_receber_vencidas():
    entries = [
        entry("2026-08-01", "entrada", "previsto", 5000),  # vencida (antes do as_of)
        entry("2026-09-15", "entrada", "previsto", 8000),  # nao vencida ainda
        entry("2026-08-01", "saida", "previsto", 1000),    # ignorada: e saida
    ]
    assert kpis.contas_a_receber_vencidas(entries, as_of="2026-09-01") == 5000


def test_projecao_13_semanas_tem_13_pontos():
    entries = [entry("2026-08-01", "entrada", "realizado", 50000)]
    projecao = kpis.projecao_13_semanas(entries, as_of="2026-08-31")
    assert len(projecao) == 13
    assert projecao[0]["semana"] == 1
    assert projecao[-1]["semana"] == 13


def test_calcular_todos_kpis_integra_tudo():
    entries = [
        entry("2026-08-01", "entrada", "realizado", 50000),
        entry("2026-08-15", "saida", "realizado", 10000),
    ]
    lines = [dre("receita_liquida", 50000), dre("ebitda", 10000)]
    resultado = kpis.calcular_todos_kpis(entries, lines, as_of="2026-08-31")
    assert resultado["caixa_atual"] == 40000
    assert resultado["margem_ebitda"] == 0.2
    assert resultado["desvio_orcamentario"] is None
    assert "runway_alerta" in resultado


def test_saldo_atual_inclui_saldo_de_abertura():
    entries = [entry("2026-08-05", "saida", "realizado", 2000)]
    assert kpis.saldo_atual(entries, as_of="2026-08-31", saldo_abertura=7000) == 5000


def test_runway_usa_saldo_de_abertura():
    entries = [entry("2026-08-31", "saida", "realizado", 3000)]  # queima 100/dia na janela de 30d
    # sem abertura o caixa e negativo -> 0 dias; com abertura de 10000 o caixa e 7000 -> 70 dias
    assert kpis.runway_dias(entries, as_of="2026-08-31") == 0.0
    assert kpis.runway_dias(entries, as_of="2026-08-31", saldo_abertura=10000) == 70.0


def test_run_kpis_cli_suprime_runway_quando_faltam_contas():
    import json
    import subprocess
    import tempfile

    payload = {
        "cash_flow_entries": [entry("2026-08-05", "saida", "realizado", 1000)],
        "dre_lines": [],
        "saldo_abertura": 5000,
        "contas_faltantes": ["Banco do Brasil CC 36436-3"],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(payload, f)
    script = Path(__file__).resolve().parent.parent / "run_kpis.py"
    out = subprocess.run(
        [sys.executable, str(script), f.name, "2026-08-31"], capture_output=True, text=True, check=True
    )
    result = json.loads(out.stdout)
    assert result["caixa_atual"] == 4000
    assert result["runway_dias"] is None
    assert result["runway_alerta"] == "indisponivel"
    assert result["projecao_13_semanas"] == []
    assert result["avisos"] == ["conta/fonte de caixa nao enviada: Banco do Brasil CC 36436-3"]


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
