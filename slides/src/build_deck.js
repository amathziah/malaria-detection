// Phase 3 final deck: "Does 98 % survive unseen patients?"
// node build_deck.js <repo> <out.pptx>
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const SKILL = "/Users/madhav/.claude/skills/synced/ff395372-6350-47fe-acab-02e14f0b0302_c6b3c67e-340a-42bc-b527-c52d6dd0fa5b/pptx";
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const REPO = process.argv[2] || "/Users/madhav/malaria-detection";
const OUT = process.argv[3] || "deck.pptx";
const ASSETS = path.join(__dirname, "assets");  // slides/src/make_deck_assets.py
const R = (...p) => path.join(REPO, ...p);
const readJSON = (p) => (fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : null);

// ------------------------------------------------------------------ theme
const HEX = {
  navy: "13203A", ink: "1F2A44", teal: "00809A", orange: "D9622B", giemsa: "8E3B8E",
  muted: "5F6B7A", light: "F3F5F7", tealTint: "E2F0F3", orangeTint: "FBEBE3", white: "FFFFFF", line: "D9DDE3",
};
const THEME = {
  name: "Giemsa Ink",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: HEX.ink, lt1: HEX.white, dk2: HEX.navy, lt2: HEX.light,
    accent1: HEX.teal, accent2: HEX.orange, accent3: HEX.giemsa, accent4: HEX.muted,
    accent5: "7FB8C4", accent6: "EDA77F", hlink: HEX.teal, folHlink: HEX.giemsa,
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "J Amathziah, C Murali Madhav, Ravi Yadav, Pugazhendhi J";
pres.company = "Rishihood University";
pres.title = "Does 98 % survive unseen patients? Automated malaria cell detection";
const C = pres.SchemeColor;
const W = 13.333, H = 7.5, M = 0.6;

// ------------------------------------------------------------------ layouts
const footer = (dark) => ({
  text: { text: "Automated Malaria Cell Detection · Rishihood University",
    options: { x: M, y: 7.02, w: 8, h: 0.3, fontSize: 10, color: dark ? "AEB7C4" : HEX.muted, margin: 0 } },
});
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: HEX.navy },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: M, y: 1.35, w: 7.4, h: 0.4, fontSize: 14, bold: true,
        color: "7FD3E0", charSpacing: 2, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 1.85, w: 7.4, h: 2.3, fontSize: 46, bold: true,
        color: HEX.white, fontFace: "Cambria", valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.2, w: 7.0, h: 1.0, fontSize: 18,
        color: "C9D3DF", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION_DARK",
  background: { color: HEX.navy },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: M, y: 2.55, w: 8, h: 0.45, fontSize: 16, bold: true,
        color: "7FD3E0", charSpacing: 2, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 3.05, w: 7.6, h: 1.6, fontSize: 40, bold: true,
        color: HEX.white, fontFace: "Cambria", valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.75, w: 7.2, h: 1.0, fontSize: 18,
        color: "C9D3DF", valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: "AEB7C4", align: "right" },
});
const contentLayout = (name, dark) => pres.defineSlideMaster({
  title: name,
  background: { color: dark ? HEX.navy : HEX.white },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: M, y: 0.38, w: 9, h: 0.32, fontSize: 12, bold: true,
        color: dark ? "7FD3E0" : HEX.teal, charSpacing: 2, margin: 0 }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.68, w: W - 2 * M, h: 0.62, fontSize: 28, bold: true,
        color: dark ? HEX.white : HEX.ink, fontFace: "Cambria", valign: "top", align: "left", margin: 0 }, text: "" } },
    footer(dark),
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: dark ? "AEB7C4" : HEX.muted, align: "right" },
});
contentLayout("CONTENT", false);
contentLayout("CONTENT_DARK", true);

// ------------------------------------------------------------------ helpers
async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}
function addSlide(layout, section, kicker, title) {
  const s = pres.addSlide({ masterName: layout, sectionTitle: section });
  if (kicker) s.addText(kicker, { placeholder: "kicker" });
  if (title) s.addText(title, { placeholder: "title" });
  return s;
}
const T = (s, text, o) => s.addText(text, { isTextBox: true, margin: 0, fontFace: "Calibri", color: HEX.ink, ...o });
function card(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill },
    rectRadius: 0.12, objectName: name });
}
async function iconBubble(s, Comp, x, y, d, bg, fg = HEX.white) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg } });
  const pad = d * 0.25;
  s.addImage({ data: await icon(Comp, fg), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad });
}
function cellImg(s, name, x, y, d, ring = null) {
  if (ring) s.addShape(pres.shapes.OVAL, { x: x - 0.05, y: y - 0.05, w: d + 0.1, h: d + 0.1, fill: { color: ring }, line: { color: ring } });
  s.addImage({ path: path.join(ASSETS, name + ".png"), x, y, w: d, h: d });
}
function img(s, file, x, y, w, h) {
  if (!fs.existsSync(file)) {
    card(s, x, y, w, h, HEX.light);
    T(s, "figure pending: " + path.basename(file), { x: x + 0.2, y: y + h / 2 - 0.2, w: w - 0.4, h: 0.4, fontSize: 12, color: HEX.muted });
    return;
  }
  s.addImage({ path: file, x, y, w, h });
}
// keep an image's aspect ratio inside a box
function imgFit(s, file, x, y, w, h, align = "center") {
  if (!fs.existsSync(file)) return img(s, file, x, y, w, h);
  const meta = require("child_process").execSync(`sips -g pixelWidth -g pixelHeight "${file}"`).toString();
  const pw = +meta.match(/pixelWidth: (\d+)/)[1], ph = +meta.match(/pixelHeight: (\d+)/)[1];
  const r = Math.min(w / pw, h / ph), iw = pw * r, ih = ph * r;
  const ix = align === "left" ? x : x + (w - iw) / 2;
  s.addImage({ path: file, x: ix, y: y + (h - ih) / 2, w: iw, h: ih });
  return { x: ix, y: y + (h - ih) / 2, w: iw, h: ih };
}
function stat(s, x, y, w, big, label, color, dark = false, size = 48) {
  T(s, big, { x, y, w, h: 0.95, fontSize: size, bold: true, color, fontFace: "Cambria" });
  T(s, label, { x, y: y + 0.95, w, h: 0.8, fontSize: 14, color: dark ? "C9D3DF" : HEX.muted, valign: "top" });
}

// ------------------------------------------------------------------ data
const A0 = readJSON(R("results/A0_10fold_paper/A0_10fold_summary.json"));
const ABL = readJSON(R("results/ablation/ablation_summary.json"));
const fmt = (x, d = 2) => (x == null || Number.isNaN(x) ? "–" : Number(x).toFixed(d));
const pct = (x, d = 2) => fmt(100 * x, d);

module.exports = { pres, C, HEX, THEME, W, H, M, R, ASSETS, A0, ABL, T, card, iconBubble, cellImg, img, imgFit, stat,
  addSlide, icon, fmt, pct, fa, applyTheme, OUT };
