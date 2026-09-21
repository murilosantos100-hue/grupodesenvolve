# Gaps e decisões pendentes — Agente CFO

Checklist da seção 9 do brief original, com minha recomendação direta em
cada item e o estado atual (2026-09-21). Nada aqui foi executado
automaticamente contra o Drive de produção ou por e-mail real — são ações
que mudam estado compartilhado (a estrutura de pastas que o time vai usar, a
caixa de entrada do Murilo e do Diego) e ficam para confirmação explícita.

## 1. Remetente do e-mail

**Pendente.** `config.json` está com `murilo.santos@grupodesenvolve.com.br`
como default (é a conta autenticada no conector hoje). Minha recomendação:
não criar `financeiro@` só por estética agora — é infraestrutura extra
(mais uma conta, mais um OAuth, mais uma coisa pra manter) para um piloto de
uma unidade. Migre quando o piloto virar operação de verdade para mais de
uma unidade, ou quando alguém além de você for operar o disparo.

## 2. Gap do orçamento

**Decisão tomada: opção (b) do brief.** O sistema já está construído
assumindo "sem orçado disponível" — `desvio_orcamentario` retorna `None`
quando nenhuma linha de DRE tem `budgeted_value`, e o relatório expõe isso
como um aviso visível, não como ausência silenciosa. Não bloqueei o piloto
esperando um orçamento mensal por unidade porque isso é trabalho de
planejamento financeiro, não de engenharia — travar o build nisso teria sido
usar um problema de processo como desculpa para não entregar o que dá pra
entregar agora. Quando você tiver o orçamento mensal por unidade, é só
começar a preencher `budgeted_value` nas linhas de DRE extraídas — o cálculo
já está pronto para consumir isso sem mudança de código.

## 3. Folha de Pagamento e Contratos Ativos/Faturamento Previsto

**Resolvido em 2026-09-21**, com sua confirmação explícita. Criei no Drive
de produção:
- `/Folha de Pagamento/Folha de Pagamento - Consultoria - 2026/` com as 12
  subpastas de mês (Janeiro–Dezembro)
- `/Contratos Ativos e Faturamento Previsto/Contratos Ativos e Faturamento
  Previsto - Consultoria - 2026/` com as 12 subpastas de mês

Mesmo padrão de nomenclatura de Notas Fiscais (`<Mês> - <Categoria> -
Consultoria - 2026`). IDs em `scripts/agente_cfo/config.json`
(`folha_de_pagamento_folder_id`, `contratos_ativos_folder_id`).

**As pastas estão vazias** — a estrutura existe, mas ninguém subiu
documento ainda. Isso não é um gap de engenharia, é um gap de processo: a
skill não vai encontrar dado ali até o time começar a subir. O gap real que
sobra agora é combinar com o time quem sobe o quê (item 4 do brief
original) — isso não se resolve criando pasta, se resolve com um combinado
verbal ou um documento curto de onboarding.

## 4. Subpastas de mês em Fluxo de Caixa e DRE

**Resolvido em 2026-09-21**, com sua confirmação explícita. Criei as 12
subpastas de mês (Janeiro–Dezembro/2026) dentro de `Extratos - Consultoria
- 2026` (Fluxo de Caixa) e `DRE - Consultoria - 2026` (DRE), replicando
exatamente o padrão já usado em Notas Fiscais. As três fontes de dado
(Notas Fiscais, Fluxo de Caixa, DRE) agora seguem a mesma convenção de
pasta por mês — "onde eu subo o quê" deixou de ser ambíguo.

## 5. Thresholds de alerta de runway

**Mantidos como chute inicial do brief:** crítico < 30 dias, atenção < 60
dias, em `config.json.alert_thresholds`. Ficaram parametrizados fora do
código de propósito — para recalibrar depois de 2–3 ciclos reais, edite só
o JSON, sem tocar em `kpis.py`. Não tenho dado real de caixa da unidade
ainda para sugerir um número melhor do que o seu chute — isso é uma decisão
de risco do negócio, não uma decisão técnica, e é sua e do Diego, não minha.

---

## O que eu faria a seguir, na sua posição

Direto: o gargalo real deste piloto não é mais engenharia nem estrutura de
pasta — isso está resolvido agora. É dado. O sistema está pronto para rodar
hoje, mas contra pastas vazias "rodar avaliação" não te dá informação
nenhuma, só valida que o cano não vaza. O primeiro ciclo de valor de verdade
só acontece depois que alguém sobe pelo menos um extrato e uma nota fiscal
de um mês fechado (agosto, já que setembro ainda não fechou). Eu
priorizaria, nessa ordem: (1) subir os documentos de agosto para o primeiro
teste real, (2) rodar a avaliação e revisar comigo e o Diego se o relatório
faz sentido antes de confiar nele, (3) só depois disso vale a pena gastar
tempo calibrando threshold — calibrar em cima de zero dado real é estética,
não estratégia. Orçamento por unidade (item 2) continua sendo a decisão
mais cara pendente — é trabalho de planejamento seu, não meu, e não há
atalho de engenharia para isso.
