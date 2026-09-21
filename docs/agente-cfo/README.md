# Agente CFO

Sistema de avaliação financeira mensal para Desenvolve Consultoria e
Hospitais (CNPJ 27.594.121/0001-65), disparado por comando manual no Claude
Code ("rodar avaliação").

## Onde está cada coisa

- `docs/agente-cfo/brief-implementacao.md` — brief original recebido do
  Murilo, salvo verbatim.
- `docs/agente-cfo/spec-funcional-tecnica-v1.md` — spec técnica: schema de
  dados, fórmulas de KPI, thresholds de alerta, arquitetura de separação
  entre acesso a arquivo / cálculo / envio de e-mail.
- `docs/agente-cfo/gaps-e-decisoes.md` — checklist de decisões pendentes
  (seção 9 do brief) com recomendação direta em cada uma.
- `scripts/agente_cfo/` — código Python determinístico (schema, KPIs,
  histórico CSV, template de relatório). Zero chamada de rede — só
  cálculo puro, testado.
- `.claude/skills/avaliacao-financeira-mensal/SKILL.md` — a skill que
  orquestra tudo: lê o Drive via MCP, chama os scripts para calcular, grava
  de volta no Drive, e manda o e-mail via MCP Gmail, com confirmação humana
  antes do envio.

## Como rodar

Numa sessão do Claude Code com os conectores MCP `Google_Drive` e `Gmail`
autenticados (conta `murilo.santos@grupodesenvolve.com.br`), diga algo como:

> rodar avaliação mensal — Desenvolve Consultoria e Hospitais

A skill `avaliacao-financeira-mensal` assume a partir daí.

## Rodar os testes

```
python3 scripts/agente_cfo/tests/test_kpis.py
python3 scripts/agente_cfo/tests/test_history_csv.py
```

Sem dependência externa — só biblioteca padrão do Python 3.

## Fase 1 vs Fase 2

Hoje (Fase 1): autenticação OAuth pessoal via conector MCP, disparo manual.
Fase 2 (agendamento automático): migra para service account + domain-wide
delegation. Os scripts de cálculo não mudam entre as fases — só quem
alimenta os dados e quem dispara o e-mail muda, e essa fronteira já está
isolada por design (ver spec seção 7).
