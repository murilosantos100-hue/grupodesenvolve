#!/usr/bin/env python3
"""CLI usado pela skill de orquestracao (Claude Code) para acionar o calculo
determinístico sem fazer matematica financeira "na cabeca" do modelo.

Uso:
    python3 run_kpis.py <arquivo_normalizado.json> <as_of AAAA-MM-DD> [config.json]

`arquivo_normalizado.json` deve conter:
    {"cash_flow_entries": [...], "dre_lines": [...]}

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

    result = kpis.calcular_todos_kpis(cash_flow_entries, dre_lines, as_of=as_of, alert_thresholds=thresholds)

    if result["runway_dias"] == float("inf"):
        result["runway_dias"] = "infinito"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
