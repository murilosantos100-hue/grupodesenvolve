# Pitch institucional — Grupo Desenvolve

Apresentação curta (11 slides) para parceiros e investidores, em HTML autocontido, PT/EN.

**Abrir:** `index.html` direto no navegador. Funciona offline. Sem internet, as fontes Raleway e Montserrat são substituídas por fontes do sistema.

## Atalhos durante a apresentação

| Tecla | Ação |
|---|---|
| → / Espaço / PageDown | próximo slide (passadores de slide funcionam) |
| ← / PageUp | slide anterior |
| 1–9, Home, End | ir direto ao slide |
| L | alternar PT / EN |
| F | tela cheia |
| B | tela preta (pausa) |

O link com `#en` abre em inglês, e `#s5` abre no slide 5.

## Editar

- **Textos em PT:** no HTML de `src/pitch.src.html`.
- **Textos em EN:** no objeto `EN` do script.
- **Números do slide 9:** no array `KPIS`, no topo do script. Item com `value: null` não aparece. Os campos "projetos entregues" e "pessoas impactadas" estão nulos até haver número validado.
- Depois de editar, rode `python3 build.py`, que regenera o `index.html` com as imagens embutidas.

## Fontes do conteúdo

- **Identidade, missão, cultura, unidades, trajetória e governança:** Base de Conhecimento (FUND-01, FUND-02, CONST-01, CONST-03, ANEX-01, ANEX-02, ANEX-03).
- **Dados de contexto, método e logos de parceiros:** Apresentação Gov Consultoria 2025.
- **Cores e tipografia:** Manual de Marca.

## Logos

Cada logo fica em `assets/` como `logo-<nome>.png`. No HTML, o marcador `{{LOGO:nome|Nome}}` usa o arquivo quando ele existe e, se não existir, mostra o nome em texto. Depois de trocar ou adicionar logos, rode `python3 build.py`.

## Fontes dos números do SUS (slides 2 e 3)

- **R$ 271,3 bi:** orçamento do Ministério da Saúde na LOA 2026 sancionada (Futuro da Saúde; Fundação Perseu Abramo).
- **5,03% do PIB:** gasto público com saúde em 2024 (Tesouro Nacional, relatório COFOG).
- **31,7 mil transplantes em 2025:** Ministério da Saúde, gov.br, maio de 2026.
- **829 mil pessoas em tratamento de HIV, 95% com carga viral suprimida:** Ministério da Saúde, Monitoramento Integrado do Cuidado do HIV e da Aids 2025 (dados de 2024).
- **R$ 35,7 bi em saldo nos fundos de saúde:** InvestSUS, dados até 31/08/2024.
