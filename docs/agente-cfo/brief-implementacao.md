# Agente CFO — Brief de Implementação (original, recebido do Murilo)

> Salvo verbatim como referência histórica. Este é o documento que originou o
> build em `scripts/agente_cfo/`, `.claude/skills/avaliacao-financeira-mensal/`
> e `docs/agente-cfo/spec-funcional-tecnica-v1.md`.
>
> **Nota de honestidade:** este brief referencia
> `claude/agente-cfo/spec-funcional-tecnica-v1.md` como já existente no
> projeto. Na data em que este brief foi processado (2026-09-21), o
> repositório `grupodesenvolve` estava completamente vazio (zero commits).
> Esse spec não existia em lugar nenhum acessível a este agente. A versão em
> `docs/agente-cfo/spec-funcional-tecnica-v1.md` neste diretório foi
> **reconstruída do zero** a partir do resumo de KPIs/schema contido neste
> brief (seções 3–4), não copiada de um original. Se existir um spec anterior
> em outro lugar (outro Drive, outro repo, Notion), ele precisa ser conciliado
> manualmente com o que foi reconstruído aqui.

---

Piloto: Desenvolve Consultoria e Hospitais (CNPJ 27.594.121/0001-65)
Cadência inicial: avaliação mensal, disparada por comando manual
Atualizado: 2026-09-21

Este documento é o input para o Claude Code construir o sistema. Ele reflete a
estrutura real do Google Drive que Murilo já criou (inspecionada nesta
sessão) — não é hipotética.

## 1. Objetivo

Ao receber o comando "rodar avaliação", o sistema deve:

1. Ler os documentos do mês mais recente nas pastas do Drive
2. Fazer backup desses documentos (snapshot íntegro, antes de qualquer
   alteração futura pelo time)
3. Calcular os KPIs financeiros
4. Comparar com o histórico de avaliações anteriores (evolução mês a mês)
5. Gerar um relatório executivo
6. Salvar o relatório na pasta `/Resultados`
7. Enviar o relatório por e-mail para Murilo e Diego

Fase 2 (futura, não agora): o mesmo fluxo disparado automaticamente por
agendamento, quando a entrada de dados estiver consistente.

## 2. Estrutura real do Google Drive (inspecionada em 2026-09-21)

Pasta raiz compartilhada: `1PSpBrJi6RaAx0wMmfNTg5u08A8jiPZHZ`

```
/ (raiz)
├── Notas Fiscais/
│   └── Notas Fiscais - Consultoria (Município e Hospital) - 2026/
│       ├── Janeiro - Notas Fiscais - Consultoria - 2026/   [vazia]
│       ├── Fevereiro .../  ... até Dezembro/                [todas as 12 já criadas, vazias]
├── Fluxo de Caixa/
│   └── Extratos - Consultoria - 2026/                       [criada, SEM subpastas de mês ainda]
├── DRE/
│   └── DRE - Consultoria - 2026/                             [criada, SEM subpastas de mês ainda]
├── Orçamento/
│   └── Orçamento 2026 - Grupo Desenvolve.png                [screenshot único, nível GRUPO, sem quebra por unidade/mês]
├── Resultados/                                                [vazia — destino dos relatórios]
└── Backup/                                                    [vazia — destino dos snapshots]
```

### Gaps identificados nesta estrutura (resolver antes ou durante o build)

1. Orçamento é um problema real. O único arquivo é um print de tela com o
   orçamento anual consolidado do grupo inteiro (ex: Impostos R$600k/ano,
   Pagamento CLT R$528k/ano), sem abertura por unidade nem por mês. Isso não
   permite calcular "desvio orçamentário de Desenvolve Consultoria e
   Hospitais" de forma real. Duas saídas: (a) construir um orçamento mensal
   por unidade agora — trabalho de planejamento, não de engenharia — ou (b) o
   primeiro ciclo do agente assume "sem orçado disponível para esta unidade"
   e reporta só o realizado, sinalizando o gap todo mês até ser resolvido.
   Recomendo (b) para não travar o piloto, mas isso precisa estar explícito
   no relatório, não escondido.
2. Fluxo de Caixa e DRE não têm subpastas por mês ainda — só Notas Fiscais
   tem. Recomendo replicar a mesma estrutura (Janeiro–Dezembro) nessas duas
   pastas antes de distribuir acesso ao time, para manter um padrão único de
   "onde eu subo o quê".
3. Faltam duas pastas do checklist original: Folha de Pagamento (custo de
   pessoal, normalmente a maior linha de despesa) e Contratos
   Ativos/Faturamento Previsto (essencial numa consultoria com receita por
   projeto — sem isso a projeção de caixa fica cega pro que ainda vai
   entrar). Sem esses dois inputs, a "leitura de caixa futura" do agente vai
   ser sistematicamente otimista, porque só vê saída e recebimento já
   ocorrido.
4. Nenhuma pasta identifica quem sobe o quê — isso fica só no combinado
   verbal com o time. Vale documentar isso fora do Drive (ex: no relatório
   inicial de setup) pra não depender de memória.

## 3. Modelo de dados e KPIs

(Igual ao spec funcional já salvo no projeto em
`claude/agente-cfo/spec-funcional-tecnica-v1.md`, seção 2–4 — reaproveitar
sem reescrever.) Resumo do essencial pro Claude Code:

* Entrada: arquivos brutos (PDF/CSV/imagem) nas pastas de mês de Notas
  Fiscais, Fluxo de Caixa (Extratos), DRE, Orçamento
* Normalização: extrair para o schema `cash_flow_entry` / `dre_line` (JSON)
  definido no spec
* KPIs: runway de caixa, projeção 13 semanas (limitada pelo gap #3 acima —
  sem contratos futuros, projeção usa só o observado), margem EBITDA, desvio
  orçamentário (quando houver orçado), contas a receber vencidas
* Alertas: thresholds da seção 4 do spec (runway < 30 dias = crítico, < 60 =
  atenção)

## 4. Backup

A cada execução:

1. Copiar (não mover) todos os arquivos lidos no ciclo do mês corrente para
   `/Backup/<AAAA-MM>_<timestamp da execução>/`
2. Incluir também o JSON normalizado (dado já extraído), não só os arquivos
   originais — permite auditar tanto a fonte quanto o número calculado
3. Nunca sobrescrever um backup anterior — cada execução gera sua própria
   pasta, mesmo que rode duas vezes no mesmo mês (ex: uma correção)

## 5. Histórico comparativo

Um arquivo único `/Resultados/Historico_Avaliacoes.csv` (ou Google Sheet, se
preferir edição visual), formato longo:

```
data_execucao, periodo_referencia, entidade, metrica, valor, status_alerta
2026-10-05, 2026-09, Desenvolve Consultoria e Hospitais, caixa_atual, 185000.00, ok
2026-10-05, 2026-09, Desenvolve Consultoria e Hospitais, runway_dias, 42, atencao
...
```

Cada execução adiciona linhas, nunca substitui. O relatório mensal lê esse
histórico pra montar a seção de evolução (tendência de 3, 6, 12 meses
conforme acumula) e o gráfico/tabela comparativa.

## 6. Envio por e-mail

* Remetente: conta do grupo já usada no Drive —
  `murilo.santos@grupodesenvolve.com.br` (se existir uma conta dedicada tipo
  `financeiro@grupodesenvolve.com.br` no futuro, migrar pra essa — mais claro
  que o relatório vem do sistema, não da caixa pessoal do Murilo)
* Destinatários: `murilo.santos@grupodesenvolve.com.br` e
  `diego.meloni@grupodesenvolve.com.br`
* Mecanismo: Gmail API (mesmo padrão de credencial usada para o acesso ao
  Drive, ver seção 7)
* Conteúdo: relatório executivo direto no corpo do e-mail (não só anexo) —
  quem abre no celular precisa entender a situação sem baixar nada; anexar o
  CSV/relatório completo como anexo

## 7. Autenticação — Google Drive e Gmail

Fase 1 (agora, comando manual, você operando o Claude Code): Configurar um
MCP server de Google Drive/Gmail dentro do Claude Code — mesmo tipo de
conector que uso aqui no Cowork. Login OAuth com a conta
`murilo.santos@grupodesenvolve.com.br` (dona das pastas). Rápido de
configurar, funciona bem para execução manual/sob demanda.

Fase 2 (quando migrar para agendamento automático): OAuth pessoal tende a
expirar ou pedir reautenticação sem alguém logado pra aprovar — ruim pra
rodar sozinho de madrugada. Nessa fase, migrar para uma service account
dedicada do Google Cloud, com as pastas do Drive compartilhadas diretamente
com o e-mail da service account (leitura) e, se o envio de e-mail também for
automático, delegação de domínio (domain-wide delegation) ou uma conta de
envio dedicada com App Password/API key própria. Não precisa resolver isso
agora — só não construir a Fase 1 de um jeito que trave a migração depois (ou
seja: já isolar a lógica de "acesso a arquivo" e "envio de e-mail" em funções
separadas, não espalhado pelo código).

## 8. Gatilho de execução

* Agora: comando explícito seu no Claude Code (ex: `rodar avaliação mensal —
  Desenvolve Consultoria e Hospitais`)
* Futuro: agendamento por cron/scheduled task, na data e horário que você
  definir — só ativar quando a entrada de dados do time estiver consistente
  por pelo menos 2-3 ciclos manuais seguidos, senão o sistema roda sozinho em
  cima de pasta vazia ou incompleta e manda alerta falso pra você e o Diego

## 9. Decisões pendentes de você antes/durante o build no Claude Code

* [ ] Confirmar remetente do e-mail (sua conta institucional ou uma dedicada
  tipo financeiro@)
* [ ] Resolver o gap do Orçamento: seguir sem orçado no piloto (recomendado)
  ou pausar pra montar orçamento mensal por unidade primeiro
* [ ] Criar as pastas de Folha de Pagamento e Contratos Ativos/Faturamento
  Previsto (ou decidir que ficam de fora do piloto por enquanto — mas aí o
  relatório de caixa futuro vem com essa limitação explícita)
* [ ] Replicar as subpastas de mês (Janeiro–Dezembro) em Fluxo de Caixa e
  DRE, no mesmo padrão de Notas Fiscais
* [ ] Confirmar thresholds de alerta da seção 4 do spec funcional (são um
  chute inicial meu, calibrar com a realidade de caixa da unidade)
