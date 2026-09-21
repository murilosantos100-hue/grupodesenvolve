---
name: avaliacao-financeira-mensal
description: >
  Roda a avaliação financeira mensal do Agente CFO para a Desenvolve
  Consultoria e Hospitais: lê os documentos do mês no Google Drive, faz
  backup, calcula KPIs, compara com o histórico e envia um relatório
  executivo por e-mail para Murilo e Diego. Use quando o usuário disser
  algo como "rodar avaliação", "rodar avaliação mensal", "avaliação
  financeira", "roda o agente CFO", ou mencionar avaliar/fechar o mês da
  Desenvolve Consultoria e Hospitais.
---

# Avaliação financeira mensal — Agente CFO

Você está executando o pipeline descrito em
`docs/agente-cfo/spec-funcional-tecnica-v1.md`. Leia esse arquivo e
`scripts/agente_cfo/config.json` antes de começar — eles têm os IDs de
pasta do Drive, os schemas de dado e os thresholds de alerta.

**Princípio geral: cálculo é determinístico, extração é sua.** Você lê e
interpreta os documentos brutos (PDF, imagem, CSV) e os normaliza para JSON
conforme o schema. Toda matemática financeira (saldo, runway, projeção,
margem, desvio) é feita pelos scripts em `scripts/agente_cfo/`, nunca de
cabeça. Isso existe para não colocar um número errado calculado por um LLM
na frente do Murilo e do Diego.

**Princípio de honestidade: gaps vão no relatório, não escondidos.** Se
faltar orçamento por unidade, pasta de Folha de Pagamento, pasta de
Contratos Ativos, ou qualquer fonte esperada — reporte a ausência
explicitamente na seção correspondente. Nunca preencha um KPI com um
palpite para "completar" o relatório.

## Passo 0 — Resolver o período de referência

Por padrão, "mês mais recente" significa: o mês calendário anterior ao mês
corrente (ex: se hoje é setembro, o período é 2026-08), a menos que o
usuário tenha pedido um mês específico no comando. Confirme com o usuário
apenas se o comando for ambíguo (ex: "roda a avaliação" sem contexto nenhum
e for a primeira execução).

## Passo 1 — Levantar os arquivos-fonte do mês

Use as ferramentas MCP `Google_Drive` (`search_files`,
`read_file_content`/`download_file_content`). Para cada uma das pastas
`notas_fiscais_folder_id`, `fluxo_de_caixa_folder_id`, `dre_folder_id` em
`config.json`:

1. Busque a subpasta do ano (2026) e dentro dela a subpasta do mês de
   referência, por nome (ex: "Agosto - Extratos - Consultoria - 2026" em
   Fluxo de Caixa, "Agosto - DRE - Consultoria - 2026" em DRE, "Agosto -
   Notas Fiscais - Consultoria - 2026" em Notas Fiscais), usando `parentId
   = '<id>'` + `title contains '<mês>'`. As três fontes seguem essa mesma
   convenção desde 2026-09-21 (ver `config.json.gaps_conhecidos`). Mesmo
   assim, não assuma cegamente que a subpasta existe — se a busca não
   retornar nada (pasta renomeada, movida, ou uma fonte nova ainda sem essa
   convenção), trate como "zero arquivos nessa fonte" e siga adiante, não
   pare o pipeline por causa disso.
2. Liste os arquivos dentro da subpasta do mês (ou da pasta do ano, se não
   houver subpasta de mês).
3. Para Orçamento (`orcamento_folder_id`), leia o(s) arquivo(s) existente(s).
   No estado atual só existe 1 PNG consolidado do grupo, sem quebra por
   unidade/mês — trate isso como "sem orçamento disponível para esta
   entidade" (não tente inferir uma fatia por unidade a partir do
   consolidado).

**Se a soma de arquivos em Notas Fiscais + Fluxo de Caixa + DRE for zero**
para o mês de referência: não invente dados nem gere um relatório vazio
silenciosamente. Informe o usuário nesta conversa que não há documentos
para o período e pergunte se ele quer (a) apontar outro mês, (b) confirmar
mesmo assim um relatório "sem dados" (só para validar o pipeline), ou (c)
abortar. Não prossiga para os passos 2–7 sem essa confirmação quando não
houver nenhum arquivo.

## Passo 2 — Extrair e normalizar

Para cada arquivo encontrado, leia o conteúdo (PDF/imagem via
`read_file_content`, que você processa nativamente; CSV via
`download_file_content` + parse). Extraia lançamentos para o schema
`cash_flow_entry` (extratos, notas fiscais) ou `dre_line` (DRE), conforme
definido em `docs/agente-cfo/spec-funcional-tecnica-v1.md` seção 2.

Monte um único JSON:
```json
{"cash_flow_entries": [...], "dre_lines": [...]}
```
e salve no seu scratchpad como `normalized_<periodo>.json`. Esse arquivo é
o que vai para o backup (passo 3) e para o cálculo (passo 4).

Se um documento estiver ilegível ou ambíguo, não invente o valor — pule o
lançamento e anote isso para incluir no relatório como observação, citando
o nome do arquivo.

## Passo 3 — Backup (antes de calcular)

1. Crie uma pasta nova em `/Backup` (id em `config.json`) chamada
   `<periodo_referencia>_<timestamp ISO da execução>` (ex:
   `2026-08_2026-09-21T14-30-00`). Nunca reutilize uma pasta de backup
   existente, mesmo que já exista uma para o mesmo período — cada execução
   gera a sua.
2. Copie (Google_Drive `copy_file`, nunca mova) cada arquivo-fonte lido no
   passo 1 para dentro dessa pasta.
3. Faça upload do `normalized_<periodo>.json` (Google_Drive `create_file`
   com `textContent`) para dentro da mesma pasta de backup.

## Passo 4 — Calcular os KPIs (script, não de cabeça)

Rode:
```
python3 scripts/agente_cfo/run_kpis.py <caminho do normalized_<periodo>.json> <data de hoje AAAA-MM-DD>
```
Use a saída JSON do script como os KPIs oficiais desta execução. Se o
script falhar com `validation_errors`, corrija a extração no passo 2 (não
tente contornar a validação) e rode de novo.

## Passo 5 — Atualizar o histórico

1. Baixe `/Resultados/Historico_Avaliacoes.csv` (Google_Drive
   `download_file_content`, `resultados_folder_id` em `config.json`, buscar
   por nome — `historico_csv_filename`). Se o arquivo ainda não existir,
   trate o texto existente como vazio (o script já lida com isso).
2. Gere as novas linhas com `history_csv.kpis_to_history_rows(...)` e junte
   com `history_csv.append_rows(...)` — não escreva CSV na mão, chame os
   módulos via um pequeno script Python (`python3 -c "..."` ou um script
   temporário no scratchpad) para garantir que o formato bate exatamente
   com o schema.
3. Faça upload do CSV resultante de volta para `/Resultados`, sobrescrevendo
   o arquivo anterior com o texto completo (histórico velho + linhas novas
   — nunca só as linhas novas).
4. Calcule tendências (`history_csv.trend_for_metric`) para `caixa_atual` e
   `runway_dias` (e `margem_ebitda` se houver DRE em pelo menos 2 meses) —
   até 12 pontos cada — para a seção de evolução do relatório.

## Passo 6 — Gerar e salvar o relatório

Monte o `context` para `report_template.render_report(...)` com os KPIs do
passo 4, as tendências do passo 5, e as flags de gap lidas de
`config.json.gaps_conhecidos` (atualize essas flags checando a existência
real das pastas/arquivos nesta execução, não confie cegamente no valor
salvo). Salve o Markdown resultante como um arquivo novo em `/Resultados`
(Google_Drive `create_file`), nomeado
`Avaliacao_<entidade sem espaços>_<periodo>_<timestamp>.md`.

## Passo 7 — Enviar por e-mail (confirmar antes de enviar)

Monte o e-mail:
- Remetente: implícito na conta autenticada do conector Gmail.
- Destinatários: `email.recipients` em `config.json`.
- Assunto: `Avaliação Financeira — <entidade> — <periodo_referencia>`.
- Corpo: o relatório em HTML simples (converta o Markdown do passo 6 para
  HTML básico — títulos, listas, tabelas) via `htmlBody`, para abrir bem no
  celular sem precisar baixar nada.
- Anexo: o CSV de histórico atualizado (e opcionalmente o `.md` do
  relatório).

**Antes de chamar `Gmail.send_message`, mostre o rascunho do e-mail
(assunto + corpo) ao usuário nesta conversa e peça confirmação explícita**,
a menos que o usuário já tenha dito de forma inequívoca nesta mesma
solicitação para enviar direto sem revisar. Enviar e-mail para duas pessoas
reais é uma ação que não dá pra desfazer — não pule essa confirmação para
"economizar uma pergunta".

## Passo 8 — Resumo final

Depois de enviado (ou depois de gerar o draft, se o usuário preferiu não
enviar ainda), resuma nesta conversa: período avaliado, KPIs principais,
alerta de runway, gaps reportados, link do relatório em `/Resultados`, link
da pasta de backup, e se o e-mail foi enviado ou só preparado.
