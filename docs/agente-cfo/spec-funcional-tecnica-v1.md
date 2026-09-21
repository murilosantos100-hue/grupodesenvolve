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
