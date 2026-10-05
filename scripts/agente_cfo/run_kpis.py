#!/usr/bin/env python3
"""CLI usado pela skill de orquestracao (Claude Code) para acionar o calculo
determinístico sem fazer matematica financeira "na cabeca" do modelo.

Uso:
    python3 run_kpis.py <arquivo_normalizado.json> <as_of AAAA-MM-DD> [config.json]

`arquivo_normalizado.json` deve conter:
    {"cash_flow_entries": [...], "dre_lines": [...], "saldo_abertura": 7013.14}

`contas_faltantes` (opcional, lista de strings): contas bancarias/fontes de caixa
que existem mas nao foram enviadas. Se nao vazia, runway e projecao de 13
semanas NAO sao calculados (viram null/[]) e a lista vai em `avisos` --
calcular em cima de caixa incompleto produz numero confiante e errado.

`saldo_abertura` (opcional, default 0) e a soma dos saldos de todas as contas
no inicio do periodo carregado, lido do cabecalho de cada extrato. Sem ele,
`caixa_atual` e so o fluxo liquido do periodo, nao o saldo real em conta.

Cada item e validado contra schema.py antes do calculo; se houver erro de
validacao, o script falha alto (exit code 1) com a lista de erros em vez de
calcular em cima de dado ruim silenciosamente.

Saida: JSON dos KPIs em stdout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agente_cfo import kpis, schema


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 1

    normalized_path = Path(sys.argv[1])
    as_of = sys.argv[2]
    config_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).resolve().parent / "config.json"

    data = json.loads(normalized_path.read_text(encoding="utf-8"))
    cash_flow_entries = data.get("cash_flow_entries", [])
    dre_lines = data.get("dre_lines", [])
    saldo_abertura = float(data.get("saldo_abertura", 0.0))
    contas_faltantes = list(data.get("contas_faltantes", []))

    errors = []
    for i, entry in enumerate(cash_flow_entries):
        for err in schema.validate_cash_flow_entry(entry):
            errors.append(f"cash_flow_entries[{i}]: {err}")
    for i, line in enumerate(dre_lines):
        for err in schema.validate_dre_line(line):
            errors.append(f"dre_lines[{i}]: {err}")

    if errors:
        print(json.dumps({"validation_errors": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    thresholds = {}
    if config_path.exists():
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        thresholds = cfg.get("alert_thresholds", {})

    result = kpis.calcular_todos_kpis(
        cash_flow_entries, dre_lines, as_of=as_of, alert_thresholds=thresholds, saldo_abertura=saldo_abertura
    )

    if contas_faltantes:
        result["runway_dias"] = None
        result["runway_alerta"] = "indisponivel"
        result["projecao_13_semanas"] = []
        result["avisos"] = [f"conta/fonte de caixa nao enviada: {c}" for c in contas_faltantes]
    elif result["runway_dias"] == float("inf"):
        result["runway_dias"] = "infinito"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
