// Apresentação comercial — Desenvolve Consultoria (municípios)
// PPTX 100% editável: textos, formas e gráfico nativos; imagens só para logos e textura.
// Ritmo de fundos: azul em introdução e pontos de atenção; branco nos slides de continuidade.
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const lu = require("react-icons/lu");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const A = (f) => path.join(__dirname, "assets", f);
const OUT = process.argv[2] || "Apresentacao Comercial - Desenvolve Consultoria.pptx";

const THEME = {
  name: "Desenvolve Consultoria",
  headFontFace: "Raleway",
  bodyFontFace: "Montserrat",
  colors: {
    dk1: "0D1150", lt1: "FFFFFF", dk2: "151A6B", lt2: "B8C4EC",
    accent1: "00C2CB", accent2: "004AAD", accent3: "2E6FD8", accent4: "7FE3E8",
    accent5: "0A2E7A", accent6: "EEF2FB", hlink: "004AAD", folHlink: "2E6FD8",
  },
};
const HEX = {
  ink: "0D1150", ink2: "151A6B", mist: "B8C4EC", cyan: "00C2CB", blue: "004AAD", white: "FFFFFF",
  slate: "4A5578", tint: "EEF2FB", tintLine: "D9E1F2", rule: "E1E7F4", barMuted: "A9B6DA",
};
// paletas por fundo
const DARK = { title: HEX.white, strong: HEX.cyan, eyebrow: HEX.cyan, text: HEX.white, muted: HEX.mist, card: HEX.ink2, cardLine: "2A3290", iconBg: HEX.cyan, iconFg: HEX.ink, src: HEX.mist };
const LIGHT = { title: HEX.ink, strong: HEX.blue, eyebrow: HEX.blue, text: HEX.ink, muted: HEX.slate, card: HEX.tint, cardLine: HEX.tintLine, iconBg: HEX.blue, iconFg: HEX.white, src: HEX.slate };

async function icon(name, color, size = 256) {
  const Comp = lu[name] || lu.LuCheck;
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).resize(size, size).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
async function dMark(color, size = 512) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="${size}" height="${size}"><path fill="#${color}" fill-rule="evenodd" d="M6 94V52A44 44 0 1 1 50 94Z M30 70V52A20 20 0 1 1 50 70Z"/></svg>`;
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  pres.title = "Apresentação Comercial — Desenvolve Consultoria";
  pres.author = "Desenvolve Consultoria";
  pres.company = "Desenvolve Consultoria Ltda.";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

  const W = 13.333, M = 0.6;
  const dsveW = A("dsve-branco.png"), dsveB = A("dsve-azul.png");

  // ---------- layouts ----------
  const contentMaster = (name, P, bg, logo, extra = []) =>
    pres.defineSlideMaster({
      title: name,
      background: bg,
      objects: [
        ...extra,
        { image: { path: logo, x: M, y: 6.92, w: 0.96, h: 0.35 } },
        { text: { text: "Desenvolve Consultoria · Grupo Desenvolve", options: { x: 1.75, y: 6.95, w: 6, h: 0.3, fontSize: 10, color: P.src, fontFace: "Montserrat", margin: 0, valign: "middle" } } },
        { placeholder: { options: { name: "eyebrow", type: "body", x: M, y: 0.45, w: 12, h: 0.32, fontSize: 12, bold: true, color: P.eyebrow, charSpacing: 4, margin: 0, fontFace: "Montserrat" }, text: "" } },
        { placeholder: { options: { name: "title", type: "title", x: M, y: 0.8, w: 12.1, h: 1.1, fontSize: 30, color: P.title, fontFace: "Raleway", valign: "top", align: "left", margin: 0 }, text: "" } },
      ],
      slideNumber: { x: 12.2, y: 6.95, w: 0.55, h: 0.3, fontSize: 10, color: P.src, fontFace: "Montserrat", align: "right" },
    });
  pres.defineSlideMaster({
    title: "CAPA",
    background: { path: A("fundo-azul.jpg") },
    objects: [{ rect: { x: 0, y: 0, w: W, h: 7.5, fill: { color: HEX.ink, transparency: 22 } } }],
  });
  contentMaster("AZUL", DARK, { path: A("fundo-azul.jpg") }, dsveW, [{ rect: { x: 0, y: 0, w: W, h: 7.5, fill: { color: HEX.ink, transparency: 12 } } }]);
  contentMaster("BRANCO", LIGHT, { color: HEX.white }, dsveB);

  // ---------- helpers ----------
  const eyebrow = (s, t) => s.addText(t, { placeholder: "eyebrow" });
  const title = (s, P, plain, strong) =>
    s.addText([{ text: plain }, { text: strong, options: { bold: true, color: P.strong } }], { placeholder: "title" });
  const card = (s, P, x, y, w, h, opts = {}) =>
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: opts.fill || P.card, transparency: opts.transparency ?? 0 }, line: { color: opts.line || P.cardLine, width: 1 }, objectName: opts.name });
  const iconCircle = async (s, P, x, y, d, name) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: P.iconBg }, line: { color: P.iconBg } });
    const p = d * 0.22;
    s.addImage({ data: await icon(name, P.iconFg), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
  };
  const T = (s, text, o) => s.addText(text, { margin: 0, isTextBox: true, ...o });

  // ================= 1 · CAPA (azul) =================
  pres.addSection({ title: "Abertura" });
  let s = pres.addSlide({ masterName: "CAPA", sectionTitle: "Abertura" });
  s.addImage({ data: await dMark(HEX.cyan), x: 9.0, y: 1.55, w: 3.6, h: 3.6 });
  s.addImage({ path: dsveW, x: 0.85, y: 0.85, w: 2.6, h: 0.95 });
  T(s, "SECRETARIAS MUNICIPAIS DE SAÚDE", { x: 0.85, y: 2.45, w: 7.5, h: 0.35, fontSize: 13, bold: true, color: HEX.cyan, charSpacing: 4 });
  T(s, [
    { text: "Mais recursos, mais segurança e " },
    { text: "mais resultado", options: { bold: true, color: HEX.cyan } },
    { text: " para a saúde do seu município" },
  ], { x: 0.85, y: 2.9, w: 7.8, h: 2.0, fontSize: 38, fontFace: "Raleway", color: HEX.white, valign: "top" });
  T(s, "Consultoria e assessoria em gestão da saúde pública, com método próprio e painel de dados.", { x: 0.85, y: 5.05, w: 7.2, h: 0.75, fontSize: 16, color: HEX.mist, valign: "top" });
  T(s, "Uma empresa do", { x: 0.85, y: 6.55, w: 1.6, h: 0.35, fontSize: 11, color: HEX.mist, valign: "middle" });
  s.addImage({ path: A("grupo-branco.png"), x: 2.4, y: 6.6, w: 1.7, h: 0.254 });
  s.addNotes("Abertura. Apresente a Desenvolve Consultoria e o objetivo da conversa: mostrar como apoiamos a Secretaria a ter mais recursos, mais segurança na gestão e mais resultado.");

  // ================= 2 · RECURSO (branco) =================
  pres.addSection({ title: "O desafio" });
  let P = LIGHT;
  s = pres.addSlide({ masterName: "BRANCO", sectionTitle: "O desafio" });
  eyebrow(s, "O DESAFIO DO RECURSO");
  title(s, P, "O recurso existe, mas ", "nem sempre está onde o município precisa");
  // destaque do saldo: cartão azul sólido (único bloco escuro do slide)
  card(s, P, M, 2.15, 5.85, 4.45, { fill: HEX.blue, line: HEX.blue, name: "Saldo em conta" });
  T(s, [{ text: "R$ 51,7", options: { bold: true } }, { text: " bi", options: { bold: true, color: HEX.cyan, fontSize: 30 } }], { x: M + 0.4, y: 2.45, w: 5.1, h: 1.0, fontSize: 60, fontFace: "Raleway", color: HEX.white, valign: "middle" });
  T(s, "em saldo nas contas dos fundos públicos de saúde", { x: M + 0.4, y: 3.45, w: 5.1, h: 0.65, fontSize: 16, bold: true, color: HEX.white, valign: "top" });
  T(s, "O recurso federal e estadual chega vinculado a blocos e finalidades definidos fora do município, que nem sempre atendem às necessidades locais. Enquanto ele se acumula em conta, o recurso próprio é pressionado a cobrir o restante.", { x: M + 0.4, y: 4.15, w: 5.05, h: 1.8, fontSize: 14, color: "DCE6FA", valign: "top" });
  T(s, "Fonte: InvestSUS, Painel de Saldos, Ministério da Saúde (consulta em out/2026).", { x: M + 0.4, y: 6.05, w: 5.1, h: 0.35, fontSize: 10, color: "C9D7F5" });

  const rx = 6.85, rw = 5.88;
  card(s, P, rx, 2.15, rw, 4.45, { name: "Receita própria" });
  T(s, "Receita própria aplicada em saúde pelos municípios, 2025", { x: rx + 0.35, y: 2.35, w: rw - 0.7, h: 0.5, fontSize: 15, bold: true, color: HEX.ink });
  s.addChart(pres.charts.BAR, [{ name: "% da receita", labels: ["Mínimo constitucional", "Média aplicada"], values: [15, 22.2] }], {
    x: rx + 0.2, y: 2.9, w: rw - 0.4, h: 1.9, barDir: "bar", chartColors: [HEX.barMuted, HEX.blue],
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '0.0"%"', dataLabelColor: HEX.ink, dataLabelFontSize: 14, dataLabelFontBold: true, dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: HEX.slate, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisLineShow: false,
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 28, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: false, barGapWidthPct: 60, objectName: "Gráfico receita própria",
  });
  T(s, [{ text: "R$ 57,4 bilhões", options: { bold: true, color: HEX.blue } }, { text: " acima do piso constitucional, aplicados pelos municípios em 2024" }], { x: rx + 0.35, y: 4.95, w: rw - 0.7, h: 0.8, fontSize: 16, color: HEX.ink, valign: "top" });
  T(s, "Fonte: CNM, a partir de dados do SIOPS (2024 e 2025).", { x: rx + 0.35, y: 6.05, w: rw - 0.7, h: 0.35, fontSize: 10, color: HEX.slate });
  s.addNotes("Saldo: R$ 51.674.490.522,78 (InvestSUS, Painel de Saldos, consulta em out/2026). Receita própria: média de 22,2% em 2025 contra mínimo de 15%; R$ 57,4 bi acima do piso em 2024 (CNM/SIOPS). Mensagem: o município banca a saúde com recurso próprio enquanto o recurso vinculado fica parado.");

  // ================= 3 · GESTÃO (branco) =================
  s = pres.addSlide({ masterName: "BRANCO", sectionTitle: "O desafio" });
  eyebrow(s, "A GESTÃO NO DIA A DIA");
  title(s, P, "O Secretário responde por tudo. ", "Nem sempre tem quem o apoie");
  T(s, "A pressão sobre a gestão", { x: M, y: 2.15, w: 5.8, h: 0.4, fontSize: 18, bold: true, color: HEX.blue });
  const press = [
    ["LuFileText", "Processos licitatórios e montagem de documentos"],
    ["LuLandmark", "Respostas e ofícios a Tribunais de Contas e Ministério Público"],
    ["LuScale", "Responsabilidade pessoal por atos da Secretaria que nem sempre consegue acompanhar"],
    ["LuRefreshCw", "Regras e portarias que mudam a todo momento"],
  ];
  for (let i = 0; i < press.length; i++) {
    const y = 2.75 + i * 0.95;
    await iconCircle(s, P, M, y, 0.62, press[i][0]);
    T(s, press[i][1], { x: M + 0.85, y: y - 0.05, w: 4.95, h: 0.72, fontSize: 15, color: HEX.ink, valign: "middle" });
  }
  card(s, P, rx, 2.15, rw, 4.45, { name: "Autodiagnóstico" });
  T(s, "Quais destes suportes a sua Secretaria tem hoje?", { x: rx + 0.35, y: 2.35, w: rw - 0.7, h: 0.75, fontSize: 18, bold: true, color: HEX.ink, valign: "top" });
  const sup = ["Jurídico-sanitário", "Financeiro e orçamentário", "Técnico e de faturamento", "Sistemas do Ministério da Saúde", "Sistemas estaduais"];
  for (let i = 0; i < sup.length; i++) {
    const y = 3.2 + i * 0.52;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: rx + 0.35, y: y + 0.07, w: 0.3, h: 0.3, rectRadius: 0.05, fill: { color: HEX.white }, line: { color: HEX.blue, width: 1.5 } });
    T(s, sup[i], { x: rx + 0.85, y, w: rw - 1.2, h: 0.44, fontSize: 16, color: HEX.ink, valign: "middle" });
  }
  T(s, "Cada suporte que falta é um ponto de risco para a gestão e para o gestor.", { x: rx + 0.35, y: 5.85, w: rw - 0.7, h: 0.55, fontSize: 14, italic: true, bold: true, color: HEX.blue, valign: "top" });
  s.addNotes("Peça ao Secretário que responda mentalmente: quais desses suportes ele tem na equipe hoje? Funciona para quem não tem nenhum e para quem tem um ou dois. Não aponte falhas; deixe que ele identifique as lacunas.");

  // ================= 4 · CUSTO DE NÃO AGIR (azul — atenção) =================
  P = DARK;
  s = pres.addSlide({ masterName: "AZUL", sectionTitle: "O desafio" });
  eyebrow(s, "O CUSTO DE NÃO AGIR");
  title(s, P, "Quando falta suporte, a conta chega ", "para o município e para o gestor");
  const costs = [
    ["LuWallet", "Recurso parado, recurso próprio estrangulado", "O saldo vinculado se acumula em conta enquanto o tesouro municipal cobre o que falta."],
    ["LuShieldAlert", "Apontamentos e responsabilização", "Órgãos de controle apontam falhas, e o gestor responde pessoalmente por elas."],
    ["LuTrendingDown", "Perda de repasse na Atenção Primária", "No novo cofinanciamento da APS, parte do repasse federal depende do desempenho em indicadores de qualidade."],
    ["LuFileClock", "Instrumentos de gestão pendentes", "Plano de Saúde, PAS, RDQA e RAG fora do prazo comprometem a regularidade e travam transferências."],
  ];
  const cw = 5.95, ch = 2.05;
  for (let i = 0; i < 4; i++) {
    const x = M + (i % 2) * (cw + 0.23), y = 2.15 + Math.floor(i / 2) * (ch + 0.2);
    card(s, P, x, y, cw, ch, { fill: HEX.ink, transparency: 10, line: "3A4AA8", name: costs[i][1] });
    await iconCircle(s, P, x + 0.35, y + 0.35, 0.7, costs[i][0]);
    T(s, costs[i][1], { x: x + 1.3, y: y + 0.3, w: cw - 1.6, h: 0.75, fontSize: 18, bold: true, color: HEX.white, valign: "middle" });
    T(s, costs[i][2], { x: x + 1.3, y: y + 1.05, w: cw - 1.6, h: 0.85, fontSize: 14, color: HEX.mist, valign: "top" });
  }
  T(s, "Referências: Portaria GM/MS nº 3.493/2024 (cofinanciamento da APS); Lei Complementar nº 141/2012 (RAG ao Conselho de Saúde até 30 de março).", { x: M, y: 6.5, w: 12.1, h: 0.3, fontSize: 10, color: HEX.mist });
  s.addNotes("Transforme as dores em risco concreto. Destaque o ponto que mais tocou o Secretário no slide anterior.");

  // ================= 5 · QUEM SOMOS (branco) =================
  pres.addSection({ title: "A solução" });
  P = LIGHT;
  s = pres.addSlide({ masterName: "BRANCO", sectionTitle: "A solução" });
  eyebrow(s, "QUEM SOMOS");
  title(s, P, "Experiência em gestão municipal da saúde, ", "desde 2017");
  T(s, "A Desenvolve Consultoria apoia Secretarias Municipais de Saúde no planejamento, no financiamento e no cumprimento das exigências do SUS. Faz parte do Grupo Desenvolve, que reúne consultoria, formação e tecnologia em saúde pública.", { x: M, y: 2.15, w: 6.2, h: 1.5, fontSize: 16, color: HEX.slate, valign: "top" });
  const stats = [["+100", "municípios atendidos"], ["2017", "início da atuação"], ["5", "frentes de atuação"]];
  for (let i = 0; i < 3; i++) {
    const x = M + i * 2.1;
    T(s, stats[i][0], { x, y: 3.95, w: 2.0, h: 0.9, fontSize: 48, bold: true, fontFace: "Raleway", color: i === 0 ? HEX.blue : HEX.ink, valign: "bottom" });
    T(s, stats[i][1], { x, y: 4.9, w: 1.95, h: 0.6, fontSize: 14, color: HEX.slate, valign: "top" });
  }
  T(s, "Parceiros institucionais", { x: 7.35, y: 2.15, w: 5.4, h: 0.4, fontSize: 15, bold: true, color: HEX.ink });
  card(s, P, 7.35, 2.65, 5.38, 3.3, { fill: HEX.white, line: HEX.tintLine, name: "Placa de logos" });
  s.addImage({ path: A("logo-conasems.png"), x: 7.85, y: 2.95, w: 4.38, h: 0.785 });
  const lg = ["logo-cosems-pr.png", "logo-cosems-pi.png", "logo-cosems-ac.png"];
  const metas = await Promise.all(lg.map((f) => sharp(A(f)).metadata()));
  const gap = 0.35, avail = 5.38 - 0.6;
  let h = 0.95;
  const totalW = (hh) => metas.reduce((t, m) => t + hh * m.width / m.height, 0) + gap * (metas.length - 1);
  if (totalW(h) > avail) h = h * (avail - gap * (metas.length - 1)) / (totalW(h) - gap * (metas.length - 1));
  let lx = 7.35 + (5.38 - totalW(h)) / 2;
  for (let i = 0; i < lg.length; i++) {
    const w = h * metas[i].width / metas[i].height;
    s.addImage({ path: A(lg[i]), x: lx, y: 4.35 + (0.95 - h) / 2, w, h });
    lx += w + gap;
  }
  s.addNotes("Atualize o número de municípios atendidos sempre que mudar.");

  // ================= 6 · MÉTODO (branco) =================
  s = pres.addSlide({ masterName: "BRANCO", sectionTitle: "A solução" });
  eyebrow(s, "NOSSO MÉTODO");
  title(s, P, "Método Desenvolve: ", "cinco frentes para uma gestão mais forte");
  const fronts = [
    ["Recursos", "Captação e ampliação de recursos federais e estaduais, com habilitações, programas e propostas técnicas que aumentam o orçamento da saúde do município."],
    ["Segurança financeira", "Aplicação e priorização dos recursos vinculados federais e estaduais, liberando o recurso próprio para as necessidades definidas pelo município."],
    ["Informação rápida e confiável", "Acompanhamento diário de portarias e publicações do Ministério da Saúde e da Secretaria Estadual, com o impacto para o município, espaço para dúvidas e indicação de providências."],
    ["Cumprimento normativo", "Correto preenchimento dos sistemas da saúde e elaboração e atualização do Plano de Saúde, PAS, RDQA, RAG e demais instrumentos no DigiSUS."],
    ["Segurança jurídico-sanitária na gestão", "Apoio técnico-normativo na instrução de processos licitatórios e contratações públicas, na organização de documentos e em subsídios técnicos para respostas a Tribunais de Contas, Ministério Público e demais órgãos de controle."],
  ];
  for (let i = 0; i < 5; i++) {
    const y = 2.05 + i * 0.93;
    s.addShape(pres.shapes.OVAL, { x: M, y: y + 0.1, w: 0.6, h: 0.6, fill: { color: HEX.blue }, line: { color: HEX.blue } });
    T(s, "+", { x: M, y: y + 0.1, w: 0.6, h: 0.6, fontSize: 26, bold: true, color: HEX.white, align: "center", valign: "middle" });
    T(s, fronts[i][0].toUpperCase(), { x: M + 0.85, y, w: 3.35, h: 0.8, fontSize: 15, bold: true, color: HEX.ink, valign: "middle" });
    T(s, fronts[i][1], { x: 4.95, y, w: 7.8, h: 0.8, fontSize: 13, color: HEX.slate, valign: "middle" });
    if (i < 4) s.addShape(pres.shapes.LINE, { x: M + 0.85, y: y + 0.865, w: 12.73 - M - 0.85, h: 0, line: { color: HEX.rule, width: 0.75 } });
  }
  s.addNotes("Percorra as cinco frentes ligando cada uma a uma dor dos slides anteriores.");

  // ================= 7 · VISÃO 360 (azul — atenção / demonstração) =================
  P = DARK;
  s = pres.addSlide({ masterName: "AZUL", sectionTitle: "A solução" });
  eyebrow(s, "PAINEL DE GESTÃO");
  title(s, P, "Visão 360 Saúde: ", "os números da gestão em um só lugar");
  T(s, "Dados da saúde do município reunidos em gráficos, relatórios e indicadores-chave, para apoiar decisões estratégicas e o acompanhamento das políticas públicas.", { x: M, y: 2.15, w: 5.5, h: 1.3, fontSize: 15, color: HEX.mist, valign: "top" });
  const feats = ["Indicadores-chave do município", "Gráficos e relatórios personalizados", "Acompanhamento de políticas públicas", "Acesso pela web e pelo aplicativo"];
  for (let i = 0; i < feats.length; i++) {
    const y = 3.55 + i * 0.5;
    s.addImage({ data: await icon("LuCheck", HEX.cyan), x: M, y: y + 0.06, w: 0.3, h: 0.3 });
    T(s, feats[i], { x: M + 0.45, y, w: 5.0, h: 0.42, fontSize: 15, color: HEX.white, valign: "middle" });
  }
  const link = { url: "https://www.visao360saude.com.br/login.php", tooltip: "Abrir o Visão 360 Saúde" };
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: M, y: 5.75, w: 4.6, h: 0.62, rectRadius: 0.31, fill: { color: HEX.cyan }, line: { color: HEX.cyan }, hyperlink: link, objectName: "Botão Visão 360" });
  T(s, "Ver os números do seu município  →", { x: M, y: 5.75, w: 4.6, h: 0.62, fontSize: 15, bold: true, color: HEX.ink, align: "center", valign: "middle", hyperlink: link });
  // tela ilustrativa (formas nativas, sem números)
  const fx = 6.55, fy = 2.15, fw = 6.18, fh = 4.25;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: fy, w: fw, h: fh, rectRadius: 0.12, fill: { color: "F4F7FD" }, line: { color: "F4F7FD" }, objectName: "Tela ilustrativa" });
  s.addShape(pres.shapes.RECTANGLE, { x: fx, y: fy + 0.12, w: fw, h: 0.33, fill: { color: "E3E9F7" }, line: { color: "E3E9F7" } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: fy, w: fw, h: 0.45, rectRadius: 0.12, fill: { color: "E3E9F7" }, line: { color: "E3E9F7" } });
  ["F26B5E", "F5BE4F", "4CC38A"].forEach((c, i) => s.addShape(pres.shapes.OVAL, { x: fx + 0.2 + i * 0.22, y: fy + 0.15, w: 0.14, h: 0.14, fill: { color: c }, line: { color: c } }));
  s.addShape(pres.shapes.RECTANGLE, { x: fx, y: fy + 0.45, w: 1.15, h: fh - 0.57, fill: { color: HEX.blue }, line: { color: HEX.blue } });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx, y: fy + fh - 0.25, w: 1.15, h: 0.25, rectRadius: 0.12, fill: { color: HEX.blue }, line: { color: HEX.blue } });
  s.addImage({ data: await dMark("FFFFFF"), x: fx + 0.38, y: fy + 0.65, w: 0.4, h: 0.4 });
  for (let i = 0; i < 4; i++) s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: fx + 0.22, y: fy + 1.35 + i * 0.42, w: 0.72, h: 0.12, rectRadius: 0.06, fill: { color: "5E86D6" }, line: { color: "5E86D6" } });
  const kx = fx + 1.4, kw = (fw - 1.4 - 0.25 - 0.3) / 3;
  for (let i = 0; i < 3; i++) {
    const x = kx + i * (kw + 0.15);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: fy + 0.7, w: kw, h: 0.95, rectRadius: 0.08, fill: { color: HEX.white }, line: { color: "DDE4F3" } });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.15, y: fy + 0.88, w: kw * 0.5, h: 0.1, rectRadius: 0.05, fill: { color: "C9D3EA" }, line: { color: "C9D3EA" } });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.15, y: fy + 1.12, w: kw * 0.7, h: 0.28, rectRadius: 0.06, fill: { color: i === 0 ? HEX.cyan : HEX.blue }, line: { color: i === 0 ? HEX.cyan : HEX.blue } });
  }
  const gx = kx, gy = fy + 1.85, gw = fw - 1.4 - 0.25, gh = 2.0;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: gx, y: gy, w: gw, h: gh, rectRadius: 0.08, fill: { color: HEX.white }, line: { color: "DDE4F3" } });
  const bars = [0.45, 0.62, 0.55, 0.78, 0.7, 0.9, 0.82];
  const bw = (gw - 0.6) / bars.length;
  bars.forEach((v, i) => {
    const bh = (gh - 0.55) * v, c = i === bars.length - 1 ? HEX.cyan : "7FA4E6";
    s.addShape(pres.shapes.RECTANGLE, { x: gx + 0.3 + i * bw + bw * 0.18, y: gy + gh - 0.25 - bh, w: bw * 0.64, h: bh, fill: { color: c }, line: { color: c } });
  });
  T(s, "Imagem ilustrativa", { x: fx, y: fy + fh + 0.05, w: fw, h: 0.28, fontSize: 10, color: HEX.mist, align: "right" });
  s.addNotes("Clique no botão para abrir o Visão 360 em nova aba e mostrar os números do município do cliente. Link: https://www.visao360saude.com.br/login.php");

  // ================= 8 · COMO TRABALHAMOS (branco) =================
  pres.addSection({ title: "Fechamento" });
  P = LIGHT;
  s = pres.addSlide({ masterName: "BRANCO", sectionTitle: "Fechamento" });
  eyebrow(s, "COMO TRABALHAMOS");
  title(s, P, "Três formas de contratar, ", "conforme a necessidade do município");
  const opts = [
    ["LuSearch", "Diagnóstico situacional", "Raio-x da gestão municipal da saúde, com prioridades e oportunidades identificadas.", null, "Contratado de forma autônoma ou incluído na consultoria completa."],
    ["LuTarget", "Assessoria em frentes específicas", "Atuação dirigida a uma necessidade pontual, como:", ["Revisão de teto MAC", "Análise de faturamento", "Estudo de captação", "Contratualização"], null],
    ["LuLayers", "Consultoria e assessoria completa", "Diagnóstico e atuação contínua nas cinco frentes do Método Desenvolve.", null, "A forma mais completa de apoio à Secretaria."],
  ];
  const ow = 3.85, og = 0.27;
  for (let i = 0; i < 3; i++) {
    const x = M + i * (ow + og), y = 2.15, hh = 4.45, hi = i === 2;
    card(s, P, x, y, ow, hh, { fill: hi ? HEX.blue : HEX.tint, line: hi ? HEX.blue : HEX.tintLine, name: opts[i][1] });
    // ícone: no cartão de destaque, círculo branco com ícone azul
    s.addShape(pres.shapes.OVAL, { x: x + 0.35, y: y + 0.35, w: 0.75, h: 0.75, fill: { color: hi ? HEX.white : HEX.blue }, line: { color: hi ? HEX.white : HEX.blue } });
    s.addImage({ data: await icon(opts[i][0], hi ? HEX.blue : HEX.white), x: x + 0.515, y: y + 0.515, w: 0.42, h: 0.42 });
    T(s, opts[i][1], { x: x + 0.35, y: y + 1.25, w: ow - 0.7, h: 0.8, fontSize: 19, bold: true, color: hi ? HEX.white : HEX.ink, valign: "top" });
    T(s, opts[i][2], { x: x + 0.35, y: y + 2.05, w: ow - 0.7, h: 0.7, fontSize: 14, color: hi ? "DCE6FA" : HEX.slate, valign: "top" });
    if (opts[i][3]) {
      T(s, opts[i][3].map((t, j, a) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: j < a.length - 1 } })), { x: x + 0.35, y: y + 2.75, w: ow - 0.7, h: 1.55, fontSize: 14, color: HEX.ink, valign: "top", paraSpaceAfter: 3 });
    }
    if (opts[i][4]) T(s, opts[i][4], { x: x + 0.35, y: y + 3.4, w: ow - 0.7, h: 0.8, fontSize: 13, italic: true, bold: true, color: hi ? HEX.cyan : HEX.blue, valign: "top" });
  }
  s.addNotes("Pergunte qual formato faz mais sentido agora. O diagnóstico situacional é a porta de entrada mais simples.");

  // ================= 9 · EQUIPE E PRÓXIMOS PASSOS (branco) =================
  s = pres.addSlide({ masterName: "BRANCO", sectionTitle: "Fechamento" });
  eyebrow(s, "EQUIPE E PRÓXIMOS PASSOS");
  title(s, P, "Vamos conversar sobre ", "a saúde do seu município");
  const team = [["DM", "Dr. Diego Meloni", "Diretor Técnico"], ["LN", "Luciana Nazar", "Diretora de Operação"], ["MS", "Dr. Murilo Santos", "Diretor Jurídico\nOAB/SP 311.759"]];
  for (let i = 0; i < 3; i++) {
    const x = M + i * (ow + og), y = 2.15;
    card(s, P, x, y, ow, 1.3, { name: team[i][1] });
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: y + 0.28, w: 0.74, h: 0.74, fill: { color: HEX.blue }, line: { color: HEX.blue } });
    T(s, team[i][0], { x: x + 0.3, y: y + 0.28, w: 0.74, h: 0.74, fontSize: 16, bold: true, color: HEX.white, align: "center", valign: "middle" });
    T(s, team[i][1], { x: x + 1.22, y: y + 0.2, w: ow - 1.4, h: 0.42, fontSize: 16, bold: true, color: HEX.ink, valign: "middle" });
    T(s, team[i][2], { x: x + 1.22, y: y + 0.65, w: ow - 1.4, h: 0.5, fontSize: 13, color: HEX.slate, valign: "middle" });
  }
  // faixa de próximos passos: bloco azul (fechamento em destaque dentro do slide branco)
  card(s, P, M, 3.75, 12.13, 1.15, { fill: HEX.blue, line: HEX.blue, name: "Próximos passos" });
  const steps = ["Conversa de diagnóstico", "Proposta técnica", "Início da atuação"];
  for (let i = 0; i < 3; i++) {
    const x = M + 0.35 + i * (ow + og), y = 4.015;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.62, h: 0.62, fill: { color: HEX.white }, line: { color: HEX.white } });
    T(s, String(i + 1), { x, y, w: 0.62, h: 0.62, fontSize: 18, bold: true, color: HEX.blue, align: "center", valign: "middle" });
    T(s, steps[i], { x: x + 0.8, y, w: 2.55, h: 0.62, fontSize: 17, bold: true, color: HEX.white, valign: "middle" });
    if (i < 2) s.addImage({ data: await icon("LuArrowRight", HEX.cyan), x: x + ow - 0.45, y: y + 0.13, w: 0.36, h: 0.36 });
  }
  const contacts = [["Site", "grupodesenvolve.com.br"], ["E-mail", "contato@grupodesenvolve.com.br"], ["Instagram", "@grupodsve"]];
  let cx = M;
  const cws = [3.2, 4.3, 2.4];
  for (let i = 0; i < 3; i++) {
    T(s, contacts[i][0].toUpperCase(), { x: cx, y: 5.37, w: cws[i], h: 0.28, fontSize: 10, bold: true, color: HEX.blue, charSpacing: 3 });
    T(s, contacts[i][1], { x: cx, y: 5.67, w: cws[i], h: 0.4, fontSize: 15, color: HEX.ink });
    cx += cws[i] + 0.35;
  }
  T(s, "Desenvolve Consultoria Ltda. · CNPJ 27.594.121/0001-65 · Ribeirão Preto/SP", { x: M, y: 6.45, w: 12.1, h: 0.3, fontSize: 10, color: HEX.slate });
  s.addNotes("Feche combinando a conversa de diagnóstico, com data. Deixe o contato e, se possível, o acesso ao Visão 360.");

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("ok", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
