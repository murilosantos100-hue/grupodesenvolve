# Agente CFO — Spec Funcional e Técnica v1

> Reconstruída em 2026-09-21 a partir do resumo contido no brief de
> implementação (`docs/agente-cfo/brief-implementacao.md`, seção 3–4). O
> brief citava um spec anterior já salvo no projeto em
> `claude/agente-cfo/spec-funcional-tecnica-v1.md` — esse arquivo não existe
> no repositório `grupodesenvolve` (que estava vazio, zero commits, quando
> este trabalho começou). Se um original existir em outro lugar, ele é a
> fonte de verdade e esta versão deve ser conciliada com ele, não o
> contrário.

## 1. Escopo do piloto

- Entidade única: **Desenvolve Consultoria e Hospitais** (CNPJ
  27.594.121/0001-65)
- Cadência: mensal, disparo manual (Fase 1)
- Fontes de dado: pastas do Google Drive `Notas Fiscais`, `Fluxo de Caixa`,
  `DRE`, `Orçamento` (ver `config.json` para IDs)

## 2. Schema de dados normalizados

Todo documento bruto lido (PDF, imagem, CSV) é convertido para uma destas
duas estruturas JSON antes de qualquer cálculo. Isso separa "extração"
(que exige julgamento — feita pelo Claude ao ler o arquivo) de "cálculo"
(determinístico — feito pelos scripts Python). Ver `schema.py` para a
implementação e validação.

### 2.1 `cash_flow_entry`

Representa um lançamento de caixa: uma linha de extrato bancário ou uma nota
fiscal emitida/recebida.

| campo             | tipo                          | obrigatório | descrição                                              |
|--------------------|--------------------------------|-------------|---------------------------------------------------------|
| `id`               | string                         | sim         | identificador único (gerado na extração, ex: hash)       |
| `entity`            | string                         | sim         | nome da entidade (ex: "Desenvolve Consultoria e Hospitais") |
| `period`            | string `"AAAA-MM"`             | sim         | mês de referência do lançamento                          |
| `date`              | string `"AAAA-MM-DD"`          | sim         | data do lançamento (ou vencimento, se `status=previsto`) |
| `type`              | `"entrada"` \| `"saida"`       | sim         | direção do fluxo                                          |
| `status`            | `"realizado"` \| `"previsto"`  | sim         | já ocorreu (extrato) ou é esperado (nota a receber/pagar)|
| `category`          | string                         | sim         | categoria livre (ex: "honorarios", "folha", "impostos") |
| `description`       | string                         | não         | texto livre da origem                                     |
| `amount`            | number (positivo)              | sim         | valor absoluto; o sinal é dado por `type`                 |
| `origem`            | `"extrato"` \| `"nota_fiscal"` \| `"outro"` | sim | tipo de documento fonte                        |
| `source_file_id`    | string                         | sim         | ID do arquivo no Drive de onde foi extraído               |
| `source_file_name`  | string                         | sim         | nome do arquivo, para auditoria humana                    |
| `counterparty`      | string                         | não         | cliente/fornecedor, quando identificável                  |

### 2.2 `dre_line`

Representa uma linha da Demonstração de Resultado do mês.

| campo             | tipo              | obrigatório | descrição                                                    |
|--------------------|--------------------|-------------|-----------------------------------------------------------------|
| `id`               | string             | sim         | identificador único                                              |
| `entity`            | string             | sim         | nome da entidade                                                  |
| `period`            | string `"AAAA-MM"` | sim         | mês de referência                                                 |
| `account`           | string             | sim         | conta do plano de contas (ver lista abaixo)                     |
| `value`             | number             | sim         | valor realizado no mês (pode ser negativo, ex: custos)           |
| `budgeted_value`    | number \| null     | não         | valor orçado, quando existir orçamento por unidade/mês (hoje não existe — ver gap #1) |
| `source_file_id`    | string             | sim         | ID do arquivo DRE no Drive                                        |
| `source_file_name`  | string             | sim         | nome do arquivo                                                   |

Contas esperadas em `account` (nomes normalizados; nem todo DRE vai ter
todas): `receita_bruta`, `deducoes`, `receita_liquida`, `custos_servicos`,
`despesas_operacionais`, `despesas_pessoal`, `ebitda`,
`resultado_financeiro`, `resultado_liquido`.

### 2.3 `contract` (contrato ativo)

**Modelo revisado em 2026-09-28.** Diferente de Notas Fiscais/Fluxo de
Caixa/DRE, `Contratos Ativos e Faturamento Previsto` **não é organizado por
mês** — o modelo de negócio da Desenvolve é de contratos perenes, de longa
duração e valor mensal fixo, então uma pasta por mês não fazia sentido e o
time já abandonou essa estrutura na prática. O modelo real, confirmado por
inspeção direta do Drive, é:

```
Contratos Ativos e Faturamento Previsto - Consultoria - 2026/
├── CONSULTORIA/
│   └── <Município>/
│       ├── (arquivos diretos: contrato inicial + aditivos numerados, o mais
│       │    recente marcado "(VIGENTE)" no nome do arquivo)
│       │    OU
│       └── CONTRATO <nº> - <modalidade> - VIGENTE|ENCERRADO/
│           └── (arquivo do contrato)
└── HOSPITALAR/
    └── <Hospital>/
        └── (mesmo padrão acima)
```

Cada cliente pode ter mais de um contrato ao longo do tempo (histórico) —
só o marcado `VIGENTE` (por nome de subpasta ou por ser o aditivo mais
recente) importa para o financeiro atual. Uma subpasta pode existir
marcada `VIGENTE` sem nenhum arquivo dentro (gap real observado, ex:
Sales Oliveira) — nesse caso o contrato fica sinalizado como
`valor_mensal_origem: indisponivel`, nunca com valor inventado.

**Achado importante sobre CNPJ:** o Grupo Desenvolve tem mais de uma
empresa (pelo menos `Desenvolve Consultoria Ltda`, CNPJ
27.594.121/0001-65 — a entidade piloto — e `Desenvolve Hospitais Ltda`,
CNPJ 48.986.804/0001-38). Um contrato dentro da pasta `HOSPITALAR` pode ter
sido originalmente firmado com a outra empresa e só migrado para o CNPJ
piloto via aditivo de substituição de contratada. Por isso `cnpj_contratada`
é campo obrigatório e verificado por contrato, individualmente — a pasta
(`CONSULTORIA`/`HOSPITALAR`) não é um proxy confiável para "qual CNPJ".

Campos (ver `scripts/agente_cfo/schema.py::validate_contract`):

| campo                    | tipo                                      | obrigatório | descrição |
|---------------------------|--------------------------------------------|-------------|-----------|
| `id`                       | string                                      | sim | identificador único (slug do cliente) |
| `cliente`                  | string                                      | sim | nome do contratante |
| `segmento`                 | `"consultoria"` \| `"hospitalar"`           | sim | qual subpasta de origem |
| `cnpj_contratante`         | string                                      | sim | CNPJ do cliente |
| `cnpj_contratada`          | string                                      | sim | CNPJ da empresa do grupo que é parte no contrato vigente — **conferir sempre**, não presumir |
| `contratada_razao_social`  | string                                      | não | razão social correspondente ao CNPJ acima |
| `numero_contrato_original` | string                                      | não | número/processo do contrato de origem |
| `aditivos`                 | lista de `{numero, data, resumo}`           | não | histórico de aditamentos, mais recente por último |
| `status`                   | `"vigente"` \| `"encerrado"` \| `"indeterminado"` | sim | |
| `objeto_resumo`            | string                                      | sim | resumo do objeto contratual |
| `valor_mensal`             | number \| null                              | condicional | obrigatório salvo quando `valor_mensal_origem="indisponivel"` |
| `valor_mensal_origem`      | `"explicito"` \| `"calculado_de_valor_global"` \| `"indisponivel"` | sim | se o contrato afirma o valor mensal diretamente, se foi derivado de um valor global ÷ período, ou se não dá pra apurar com confiança |
| `valor_global_referencia`  | number \| null                              | não | valor global citado no documento, quando existir, para auditoria do cálculo acima |
| `reajuste_indice`          | string \| null                              | não | ex: "IPCA" |
| `reajuste_periodicidade`   | string \| null                              | não | |
| `vigencia_inicio`          | string `"AAAA-MM-DD"`                       | sim | |
| `vigencia_fim`             | string `"AAAA-MM-DD"` \| null               | não | null = prazo indeterminado |
| `dia_vencimento_pagamento` | int 1-31 \| null                            | não | |
| `fonte_arquivo_id`         | string                                      | sim | ID do Drive do documento usado como base — auditoria |
| `fonte_arquivo_nome`       | string                                      | sim | |
| `observacoes`              | string                                      | não | gaps, ambiguidades, decisões de interpretação tomadas na extração |

O catálogo consolidado (todos os clientes) fica em
`contratos_ativos.json` dentro da própria pasta `Contratos Ativos e
Faturamento Previsto` no Drive — dado comercial real não é versionado no
repositório git. O repo guarda só o schema/validação e um piloto de 3
clientes em `scripts/agente_cfo/contratos_ativos_piloto.json`, para
referência de formato.

Esse catálogo ainda **não está plugado** em `kpis.projecao_13_semanas` —
integrá-lo é o próximo passo natural depois que o catálogo cobrir os 26
clientes, e vai transformar a projeção de "só extrapolação de histórico"
em "piso de receita contratada + variação observada".

## 3. KPIs (implementados em `scripts/agente_cfo/kpis.py`)

Todos calculados de forma determinística a partir das listas de
`cash_flow_entry` / `dre_line` do mês — nunca por estimativa do modelo.

| KPI                          | Fórmula                                                                                   | Limitação atual                                                                 |
|-------------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `caixa_atual`                 | soma de `amount` (entrada − saída) de todos `status=realizado`, até a data mais recente     | —                                                                                   |
| `runway_dias`                 | `caixa_atual / queima_media_diaria`, onde queima média vem da janela móvel de 30 dias de `realizado` | se queima ≤ 0 (caixa líquido positivo), runway é `infinito`, reportar como tal, não como número |
| `projecao_13_semanas`         | projeta saldo semana a semana usando a média semanal de fluxo **observado** (realizado) dos últimos meses | **enviesada para otimista**: não inclui contratos futuros nem folha prevista (gaps #3 do brief) — isso vai no relatório, não é nota de rodapé |
| `margem_ebitda`                | `ebitda / receita_liquida` das linhas de DRE do mês                                          | requer DRE do mês presente; se ausente, KPI é `null` e reportado como indisponível |
| `desvio_orcamentario`          | por conta de DRE com `budgeted_value` não nulo: `(value - budgeted_value) / budgeted_value` | **hoje sempre indisponível** para esta unidade — só existe orçamento anual consolidado do grupo, sem quebra por unidade/mês (gap #1). O agente reporta isso explicitamente, não omite a seção |
| `contas_a_receber_vencidas`    | soma de `amount` onde `type=entrada`, `status=previsto`, `date < data_de_execucao`           | depende de notas fiscais emitidas estarem lançadas como `previsto` até serem conciliadas |

## 4. Alertas

| Métrica       | Crítico   | Atenção   | OK        |
|-----------------|-----------|-----------|-----------|
| `runway_dias`   | < 30 dias | < 60 dias | ≥ 60 dias (ou infinito) |

Thresholds são um **chute inicial** (seção 4/9 do brief original). Ficam em
`config.json` (`alert_thresholds`) para serem calibrados sem mexer em código,
depois de 2–3 ciclos reais com Murilo e Diego.

Não há threshold definido ainda para `margem_ebitda` nem para
`desvio_orcamentario` (este último nem é calculável no momento — ver acima).
Não inventar um número aqui sem validar com o Murilo.

## 5. Histórico comparativo

Formato longo em `/Resultados/Historico_Avaliacoes.csv`, uma linha por
métrica por execução:

```
data_execucao,periodo_referencia,entidade,metrica,valor,status_alerta
```

- `data_execucao`: `AAAA-MM-DD` (data em que a avaliação rodou, não o
  período de referência)
- `periodo_referencia`: `AAAA-MM`
- `valor`: número puro; para métricas sem alerta aplicável, `status_alerta`
  fica `"n/a"`
- Nunca sobrescrever linhas existentes — sempre append. Implementado em
  `scripts/agente_cfo/history_csv.py`.

## 6. Backup

A cada execução, cria `/Backup/<AAAA-MM>_<timestamp ISO>/` contendo:

1. Cópia de cada arquivo fonte lido no ciclo (nunca mover o original)
2. O JSON normalizado (`cash_flow_entry[]` + `dre_line[]`) daquele ciclo,
   para permitir auditar tanto a fonte quanto o número calculado
3. Nunca sobrescrever backup anterior — cada execução gera pasta própria,
   mesmo que rode duas vezes no mesmo mês

## 7. Separação de responsabilidades (arquitetura)

Requisito explícito do brief (seção 7): isolar "acesso a arquivo" de "envio
de e-mail" para não travar a migração de OAuth pessoal (Fase 1) para service
account + domain-wide delegation (Fase 2).

- **Scripts Python (`scripts/agente_cfo/*.py`)**: cálculo puro. Zero
  chamadas de rede, zero dependência de credencial. Recebem JSON, devolvem
  JSON/texto. Testáveis isoladamente, reaproveitáveis sem mudança entre Fase
  1 e Fase 2.
- **Acesso a arquivo (Drive)**: na Fase 1, feito pelo Claude Code via
  conector MCP `Google_Drive` durante a execução da skill — não há código
  Python fazendo chamada HTTP direta à API do Google. Na Fase 2, essa
  responsabilidade migra para um client dedicado (service account), mas os
  scripts de cálculo não mudam.
- **Envio de e-mail**: na Fase 1, feito pelo Claude Code via conector MCP
  `Gmail`. Na Fase 2, migra para envio via API com credencial de serviço
  própria. Mesma lógica de isolamento.
- A skill (`.claude/skills/avaliacao-financeira-mensal/SKILL.md`) é o único
  lugar que orquestra as três camadas (Drive → cálculo → Gmail) — os scripts
  não se chamam entre si além do necessário, e não fazem I/O externo.

## 8. Não escopo desta v1

- Múltiplas entidades do grupo (só "Desenvolve Consultoria e Hospitais" por
  enquanto)
- Geração de gráficos (a seção de evolução do relatório é tabular)
- Agendamento automático (Fase 2)
- Reconciliação automática de notas fiscais "previstas" com extratos
  "realizados" (feita por leitura humana do relatório, por ora)
