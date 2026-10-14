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
- **Números do slide 8:** no array `KPIS`, no topo do script. Item com `value: null` não aparece. Os campos "projetos entregues" e "pessoas impactadas" estão nulos até haver número validado.
- Depois de editar, rode `python3 build.py`, que regenera o `index.html` com as imagens embutidas.

## Fontes do conteúdo

- **Identidade, missão, cultura, unidades, trajetória e governança:** Base de Conhecimento (FUND-01, FUND-02, CONST-01, CONST-03, ANEX-01, ANEX-02, ANEX-03).
- **Dados de contexto, método e logos de parceiros:** Apresentação Gov Consultoria 2025.
- **Cores e tipografia:** Manual de Marca.
