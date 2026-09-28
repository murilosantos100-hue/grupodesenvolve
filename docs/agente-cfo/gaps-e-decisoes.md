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

## 6. Contratos Ativos — modelo por cliente (2026-09-28)

**Resolvido — modelo atualizado.** O time já tinha abandonado as subpastas
de mês em Contratos Ativos e reorganizado por cliente
(`CONSULTORIA/<município>` e `HOSPITALAR/<hospital>`), confirmando que o
modelo por mês não fazia sentido pra contratos perenes. Documentei esse
modelo em `spec-funcional-tecnica-v1.md` seção 2.3 e criei o schema
`validate_contract` em `schema.py`. Rodei um piloto de leitura completa em
3 clientes (Brotas, Altinópolis, H.C. Cuiabá) — resultado em
`scripts/agente_cfo/contratos_ativos_piloto.json` e também salvo no Drive
em `/Contratos Ativos e Faturamento Previsto/contratos_ativos_piloto.json`.

**Achados do piloto que afetam os 23 clientes restantes:**

1. **CNPJ duplo dentro do grupo.** O contrato de H.C. Cuiabá foi
   originalmente firmado com `Desenvolve Hospitais Ltda` (CNPJ
   48.986.804/0001-38), não com a entidade piloto deste projeto
   (`Desenvolve Consultoria Ltda`, CNPJ 27.594.121/0001-65), e só migrou via
   aditivo de substituição de contratada. Isso significa que **nem todo
   contrato na pasta HOSPITALAR conta necessariamente para o caixa da
   entidade piloto** — cada um precisa ter o CNPJ conferido individualmente
   no texto, não presumido pela pasta de origem. Preciso da sua confirmação:
   contratos ainda em nome de Desenvolve Hospitais Ltda devem entrar na
   projeção de caixa deste piloto, ou só os já migrados para 27.594.121/0001-65?

2. **"Valor mensal" nem sempre está explícito.** Brotas declara "valor
   global do aditamento" sem dizer se é mensal ou anual — tive que inferir
   por coerência com outro trecho do mesmo documento (confiança média, não
   alta, sinalizado no campo `valor_mensal_origem`). Isso vai se repetir nos
   outros 23 — o schema já contempla essa incerteza (`explicito` vs
   `calculado_de_valor_global` vs `indisponivel`), mas o relatório final
   precisa deixar isso visível, nunca tratar tudo como igualmente confiável.

3. **Subpasta "VIGENTE" pode estar vazia.** Sales Oliveira tem uma subpasta
   `CONTRATO 036-026 - PE - VIGENTE` sem nenhum arquivo dentro — o contrato
   vigente real não está digitalizado no Drive. Vai virar
   `valor_mensal_origem: indisponivel` no catálogo, não um valor inventado.

**Limitação técnica encontrada:** o conector MCP do Google Drive desta
sessão **não tem permissão de delete/rename** (`trash_file` e
`update_file` retornaram "The caller does not have permission" mesmo em
pastas vazias criadas por mim). Não consegui apagar as 12 subpastas de mês
obsoletas que criei em Contratos Ativos antes dessa mudança de modelo —
**pedido: apague manualmente Janeiro–Dezembro dentro de `Contratos Ativos e
Faturamento Previsto - Consultoria - 2026` no Drive**, é rápido pela
interface web e eu não tenho esse escopo de permissão no momento.

**Decisão sobre CNPJ duplo (2026-09-28, confirmada pelo Murilo):**
contratos de qualquer empresa do Grupo Desenvolve (Desenvolve Consultoria
Ltda 27.594.121/0001-65 **e** Desenvolve Hospitais Ltda 48.986.804/0001-38,
e qualquer outra que apareça) contam para o caixa consolidado do Agente
CFO — tratamos o grupo como uma unidade operacional única pra fins de
fluxo de caixa gerencial, não pelo CNPJ formal de cada contrato. O campo
`cnpj_contratada` continua sendo capturado em todo contrato, só que agora
para auditoria/rastreabilidade, não como filtro de inclusão.

**Concluído (2026-09-28):** os 24 clientes restantes foram processados por
5 agentes em paralelo, um por lote. Catálogo completo (27 clientes: 21
CONSULTORIA + 6 HOSPITALAR) salvo em
`/Contratos Ativos e Faturamento Previsto/contratos_ativos.json` no Drive.
27/27 registros válidos contra `schema.validate_contract` (o schema foi
ajustado: campos como `cnpj_contratante`/`vigencia_inicio`/`fonte_arquivo_id`
só são obrigatórios quando `status='vigente'` — um gap real de pasta vazia
não tem nada pra citar).

**Resultado agregado:**
- 22 contratos vigentes com valor mensal confirmado
- 5 gaps/indeterminados (2 pastas HOSPITALAR completamente vazias — Santa
  Casa de Cajobi e Hospital Japonês Santa Cruz —, 1 pasta CONSULTORIA
  vazia — Sales Oliveira —, 2 com último registro digital vencido há meses
  sem renovação digitalizada — Nuporanga desde 05/2024, Catanduva desde
  02/2026)
- Total mensal vigente, CNPJs confirmados do grupo: **R$ 188.143,28**
- Total incluindo Pindorama (CNPJ fora do grupo, ver abaixo): R$ 192.780,97

**Achado que exige sua decisão explícita — não incluí no total:**
Pindorama tem contrato vigente com **Instituto de Apoio ao SUS (IASUS) /
"Mais Saúde"**, CNPJ 35.594.221/0001-10 — não é nenhum dos dois CNPJs do
Grupo Desenvolve. Murilo Silveira Soares dos Santos assina o termo de
ciência original como "Advogado" pela contratada, sugerindo alguma
relação, mas os documentos não confirmam vínculo societário. **Não somei
esse valor (R$4.637,69/mês) ao total consolidado** até você confirmar se
esse contrato deveria estar na carteira do grupo ou é uma entidade
parceira registrada por engano na pasta do Drive.

**Outros achados operacionais (não bloqueiam, mas merecem atenção do
time):**
- **Viradouro**: contrato vence exatamente hoje (28/09/2026), sem 5º
  aditivo no Drive — verificar se a renovação está em assinatura
- **Bebedouro**: vigência do 3º aditivo estimada (documento não tem data
  exata de início), muito próxima do vencimento, sem 4º aditivo ainda
- **Pompéia**: contrato nunca migrou pro CNPJ piloto — segue com
  Desenvolve Hospitais Ltda (48.986.804/0001-38), ao contrário do padrão
  visto em Cuiabá
- Vários contratos usam "Desenvolve Solutions Ltda" como razão social em
  documentos mais antigos (mesmo CNPJ 27.594.121/0001-65 que hoje é
  "Desenvolve Consultoria Ltda") — mudança de nome fantasia ao longo do
  tempo, sem impacto no caixa, mas registrado em `contratada_razao_social`
  exatamente como no documento-fonte

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
