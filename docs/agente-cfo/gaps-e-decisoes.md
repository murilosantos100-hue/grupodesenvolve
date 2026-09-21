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

**Ainda não criadas.** Não criei essas pastas no Drive de produção porque é
uma mudança estrutural que o time vai passar a depender — prefiro que você
confirme antes de eu mexer na árvore real que o Diego e o resto do time vão
usar. Minha recomendação honesta: **crie as duas agora**, antes do primeiro
ciclo real. O custo é baixo (duas pastas) e sem elas dois números centrais
do relatório ficam estruturalmente enviesados, não por bug, mas porque a
fonte não existe:
- Sem Folha de Pagamento: o fluxo de caixa realizado provavelmente já
  captura a saída quando ela sai do banco, mas você perde visibilidade de
  compromisso futuro de folha na projeção de 13 semanas.
- Sem Contratos Ativos: a projeção de 13 semanas só vê o que já é receita
  reconhecida, nunca o que está contratado mas ainda não faturado — numa
  consultoria com receita por projeto, isso é a diferença entre "vejo o
  caixa" e "vejo o caixa e sei se ele volta a subir".

Se quiser, eu crio as duas pastas agora — é uma ação reversível (dá pra
apagar), mas eu queria sua confirmação explícita antes de tocar na estrutura
real que o time vai começar a usar.

## 4. Subpastas de mês em Fluxo de Caixa e DRE

**Ainda não replicadas.** Mesma lógica do item 3: reversível, recomendado,
mas não fiz sem confirmação por afetar a árvore de produção. A skill já foi
escrita para não quebrar se essas subpastas não existirem (trata como "zero
arquivos" e segue), mas isso é uma rede de segurança, não uma razão para
adiar a padronização — sem subpasta por mês, fica sem convenção clara de
"onde eu subo o quê" assim que mais de uma pessoa começar a subir arquivo.

## 5. Thresholds de alerta de runway

**Mantidos como chute inicial do brief:** crítico < 30 dias, atenção < 60
dias, em `config.json.alert_thresholds`. Ficaram parametrizados fora do
código de propósito — para recalibrar depois de 2–3 ciclos reais, edite só
o JSON, sem tocar em `kpis.py`. Não tenho dado real de caixa da unidade
ainda para sugerir um número melhor do que o seu chute — isso é uma decisão
de risco do negócio, não uma decisão técnica, e é sua e do Diego, não minha.

---

## O que eu faria a seguir, na sua posição

Direto: o gargalo real deste piloto não é engenharia, é dado. O sistema
está pronto para rodar hoje contra pastas vazias e vai te dizer isso sem
inventar número — mas "rodar avaliação" contra uma pasta vazia não te dá
informação nenhuma, só valida que o cano não vaza. O primeiro ciclo de valor
de verdade só acontece depois que alguém sobe pelo menos um extrato e uma
nota fiscal de agosto. Eu priorizaria, nessa ordem: (1) confirmar comigo se
crio as pastas/subpastas faltantes agora, (2) subir os documentos de um mês
fechado (agosto, já que setembro ainda não fechou) para o primeiro teste
real, (3) só depois disso vale a pena gastar tempo calibrando threshold —
calibrar em cima de zero dado real é estética, não estratégia.
