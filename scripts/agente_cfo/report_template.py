"""Renderizacao do relatorio executivo em Markdown.

Funcao pura: recebe um dict de contexto ja montado (KPIs calculados,
tendencias do historico, flags de gaps conhecidos) e devolve texto Markdown
pronto para ir no corpo do e-mail e ser salvo em /Resultados. Nao decide
nada sobre dados -- so formata o que ja foi calculado.
"""
from __future__ import annotations


def _fmt_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _fmt_pct(valor: float) -> str:
    return f"{valor * 100:.1f}%"


def _fmt_runway(dias: float) -> str:
    if dias == float("inf"):
        return "sem risco de esgotamento no ritmo atual (caixa estavel ou positivo)"
    return f"{dias:.0f} dias"


_ALERTA_LABEL = {"critico": "🔴 CRÍTICO", "atencao": "🟡 ATENÇÃO", "ok": "🟢 OK"}


def render_report(context: dict) -> str:
    """`context` esperado:
    {
      "entidade": str, "periodo_referencia": "AAAA-MM", "data_execucao": "AAAA-MM-DD",
      "kpis": <saida de kpis.calcular_todos_kpis>,
      "trends": {"caixa_atual": [...], "runway_dias": [...], ...} (opcional, de history_csv.trend_for_metric),
      "gaps": {"orcamento_disponivel": bool, "folha_pagamento_disponivel": bool,
               "contratos_ativos_disponivel": bool},
      "backup_link": str (url da pasta de backup desta execucao),
      "arquivos_processados": int,
    }
    """
    entidade = context["entidade"]
    periodo = context["periodo_referencia"]
    kpis = context["kpis"]
    gaps = context.get("gaps", {})
    trends = context.get("trends", {})

    linhas = []
    linhas.append(f"# Avaliação Financeira — {entidade}")
    linhas.append(f"**Período de referência:** {periodo}  ")
    linhas.append(f"**Executado em:** {context['data_execucao']}  ")
    linhas.append(f"**Documentos processados neste ciclo:** {context.get('arquivos_processados', 0)}")
    linhas.append("")

    linhas.append("## Situação de caixa")
    linhas.append(f"- **Caixa atual:** {_fmt_moeda(kpis['caixa_atual'])}")
    alerta = kpis.get("runway_alerta", "ok")
    linhas.append(
        f"- **Runway:** {_fmt_runway(kpis['runway_dias'])} — {_ALERTA_LABEL.get(alerta, alerta)}"
    )
    linhas.append(
        f"- **Contas a receber vencidas:** {_fmt_moeda(kpis['contas_a_receber_vencidas'])}"
    )
    linhas.append("")

    linhas.append("## Projeção de 13 semanas")
    linhas.append(
        "> ⚠️ **Projeção baseada apenas em fluxo observado (histórico).** Não inclui "
        "contratos ativos/faturamento previsto nem folha de pagamento futura, porque "
        "essas fontes ainda não existem no Drive. Trate como piso otimista, não como "
        "previsão completa."
    )
    linhas.append("")
    linhas.append("| Semana | Saldo projetado |")
    linhas.append("|---|---|")
    for item in kpis["projecao_13_semanas"]:
        linhas.append(f"| {item['semana']} | {_fmt_moeda(item['saldo_projetado'])} |")
    linhas.append("")

    linhas.append("## DRE do mês")
    if kpis.get("margem_ebitda") is not None:
        linhas.append(f"- **Margem EBITDA:** {_fmt_pct(kpis['margem_ebitda'])}")
    else:
        linhas.append("- **Margem EBITDA:** indisponível (DRE do mês não encontrado ou incompleto)")

    linhas.append("")
    linhas.append("### Desvio orçamentário")
    if not gaps.get("orcamento_disponivel", False):
        linhas.append(
            "> ⚠️ **Sem orçamento por unidade/mês disponível para esta entidade.** "
            "O único orçamento no Drive é um consolidado anual do grupo inteiro, sem "
            "quebra por unidade nem por mês — não é possível calcular desvio real. "
            "Esta seção fica em aberto até existir um orçamento mensal por unidade "
            "(decisão pendente com o Murilo, ver `docs/agente-cfo/gaps-e-decisoes.md`)."
        )
    elif kpis.get("desvio_orcamentario"):
        linhas.append("| Conta | Realizado | Orçado | Desvio |")
        linhas.append("|---|---|---|---|")
        for item in kpis["desvio_orcamentario"]:
            desvio_str = _fmt_pct(item["desvio_pct"]) if item["desvio_pct"] is not None else "n/a"
            linhas.append(
                f"| {item['account']} | {_fmt_moeda(item['realizado'])} | "
                f"{_fmt_moeda(item['orcado'])} | {desvio_str} |"
            )
    else:
        linhas.append("Sem linhas de DRE com orçamento associado neste ciclo.")
    linhas.append("")

    if trends:
        linhas.append("## Evolução histórica")
        for metrica, pontos in trends.items():
            if not pontos:
                continue
            linhas.append(f"**{metrica}**")
            linhas.append("| Período | Valor | Alerta |")
            linhas.append("|---|---|---|")
            for p in pontos:
                linhas.append(f"| {p['periodo_referencia']} | {p['valor']} | {p['status_alerta']} |")
            linhas.append("")

    linhas.append("## Gaps conhecidos nesta avaliação")
    gap_items = []
    if not gaps.get("orcamento_disponivel", False):
        gap_items.append("Orçamento por unidade/mês ausente — desvio orçamentário não calculável.")
    if not gaps.get("folha_pagamento_disponivel", True):
        gap_items.append(
            "Pasta de Folha de Pagamento ainda não existe — maior linha de despesa "
            "normalmente não está no fluxo de caixa lido."
        )
    if not gaps.get("contratos_ativos_disponivel", True):
        gap_items.append(
            "Pasta de Contratos Ativos/Faturamento Previsto ainda não existe — a "
            "projeção de 13 semanas não vê receita futura contratada."
        )
    if gap_items:
        for g in gap_items:
            linhas.append(f"- {g}")
    else:
        linhas.append("Nenhum gap estrutural identificado neste ciclo.")
    linhas.append("")

    if context.get("backup_link"):
        linhas.append(f"Backup dos documentos fonte desta execução: {context['backup_link']}")

    return "\n".join(linhas)
