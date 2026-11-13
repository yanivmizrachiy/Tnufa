# -*- coding: utf-8 -*-
"""Booklet markup: shared CSS, cover, instructions, draft and closing sheets, and the teacher pages.
Everything is print-first A4 (210×297 mm). The same sheets feed the PDF and the web reader."""
from . import html as H
from .model import DOMAIN_HE, THINKING_HE, DIFFICULTY_HE

TITLE = "מבחן תנופה לדוגמה"
DATE = "נובמבר 2026"   # appears in SUBTITLE
SUBTITLE = "מתמטיקה · הכנה לכיתה ט׳ · נובמבר 2026"
CREDIT_1 = "יניב רז — מדריך מחוזי חט״ב בעיר ירושלים"
CREDIT_2 = "הדרכה במחוז ירושלים והעיר ירושלים — מנח״י, בהובלת איילת קריספין"
FONTS = "https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800;900&family=Rubik:wght@700;900&family=Suez+One&family=Gveret+Levin+AlefAlefAlef&display=swap"

CSS = r"""
:root{--ink:#16202c;--mute:#4f5f6b;--navy:#15386e;--deep:#0a2550;--g1:#5ca585;--g2:#3c8468;--g3:#276149;--turq:#15bda9;
  --line:#cdd8d4;--pale:#e6f1ec;--foot:92px;--cream:#fbf7ea}
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
@page{size:A4;margin:0}
html,body{margin:0;padding:0;background:#fff}
body{color:var(--ink);font-family:"Heebo",Arial,sans-serif;font-size:14.8px;line-height:1.55}
.page{position:relative;width:210mm;height:297mm;overflow:hidden;break-after:page;display:flex;flex-direction:column;
  padding:34px 60px var(--foot);background:#fff}
.page:last-child{break-after:auto}
.content{flex:1 1 auto;min-height:0;display:flex;flex-direction:column}
/* footer */
.foot{position:absolute;inset-inline:0;bottom:0;height:var(--foot);background:#fff}
.foot .rule{position:absolute;top:0;inset-inline:0;height:4px;background:var(--deep)}
.foot .row{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:12px;padding-top:4px}
.foot img{width:52px;height:52px;border-radius:50%}
.foot .lines{display:flex;flex-direction:column;text-align:center;line-height:1.3}
.foot b{font-weight:800;font-size:12.5px;color:#122f4c}
.foot span{font-size:11px;color:#3a5168}
.foot .pn{position:absolute;inset-inline-start:60px;bottom:30px;font-size:12px;color:#3a5168;font-weight:600}
.foot .tag{position:absolute;inset-inline-end:60px;bottom:30px;font-size:11px;color:#3a5168}
.foot.fin{background:var(--navy)}
.foot.fin b,.foot.fin .pn,.foot.fin .tag{color:#fff}
.foot.fin span{color:#dbe7f5}
/* questions */
.q{padding-block:14px 16px;border-top:1.5px solid var(--line)}
.q:first-child,.student-fields + .q{border-top:0;padding-top:0}
.student-fields{display:grid;grid-template-columns:1.5fr 1fr;gap:22px;margin:0 0 18px;padding:10px 15px;border:1px solid #cdd8e4;border-radius:8px;color:var(--ink);direction:rtl;font-size:14px}
.student-fields .entry{display:flex;align-items:baseline;gap:10px;min-width:0}
.student-fields .entry b{white-space:nowrap;font-weight:600}
.student-fields .entry span{flex:1;height:22px;border-bottom:1.3px solid #647789}
.qh{display:flex;gap:12px;align-items:flex-start}
.num{flex:0 0 auto;width:36px;height:36px;border-radius:50%;background:var(--g3);color:#fff;font-weight:700;font-size:18px;
  display:flex;align-items:center;justify-content:center;font-variant-numeric:tabular-nums}
.qb{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:7px;padding-top:5px}
.qb p{margin:0}
.fig{margin:4px auto;width:100%}
.fig svg{display:block;width:100%;height:auto;font-family:"Heebo",Arial,sans-serif}
.part{display:flex;gap:8px;margin-top:5px}
.pl{flex:0 0 16px;font-weight:800}
.pb{flex:1 1 auto;min-width:0}
.pb>p,.pb>.opts,.pb>.work,.pb>.ans,.pb>.fig,.pb>.tw{margin-top:7px;margin-bottom:0}
.math{font-family:Arial,"Heebo",sans-serif;white-space:nowrap;unicode-bidi:isolate}
.math sup{font-size:.72em;vertical-align:.45em;line-height:0}
.frac{display:inline-flex;flex-direction:column;align-items:center;vertical-align:middle;line-height:1.15;margin:0 2px;font-size:.95em}
.frac .fn{border-bottom:1.4px solid var(--ink);padding:0 4px 1px}
.frac .fd{padding:1px 4px 0}
.rad{display:inline-flex;direction:ltr;unicode-bidi:isolate;align-items:stretch;vertical-align:-.3em;margin-inline:0 3px;font-family:Arial,"Heebo",sans-serif;font-size:1.08em;line-height:1.3}
.rad svg{display:block;width:.68em;height:auto;flex:0 0 auto}
.rad .rc{border-top:1.5px solid #16202c;padding:.02em .14em 0 .08em}
.opts{display:grid;gap:7px 22px;margin-block:3px}
.opts.c2{grid-template-columns:repeat(2,minmax(0,1fr))}
.opts.c3{grid-template-columns:repeat(3,minmax(0,1fr))}
.opts.c4{grid-template-columns:repeat(4,minmax(0,1fr))}
.opts.c5{grid-template-columns:repeat(5,minmax(0,1fr))}
.opt{display:flex;align-items:center;gap:8px;min-width:0}
.opt>span:last-child{flex:1 1 auto;min-width:0}
.let{font-size:11px;color:var(--mute);width:10px;flex:0 0 auto}
.box{flex:0 0 auto;width:16px;height:16px;border:1.3px solid #6d7a84;border-radius:3px;background:#fff}
.sys{display:inline-block;font-family:Arial,"Heebo",sans-serif;line-height:1.45;text-align:left;margin-top:4px}
.work,.fill{position:relative;overflow:hidden}
.work svg,.fill svg{position:absolute;inset:0;display:block}
.fill{position:absolute;inset:0 0 var(--foot) 0}
.ans{font-weight:500}
.blank{display:inline-block;position:relative;width:97px;height:25px;margin-inline:3px;vertical-align:middle}
.blank svg{position:absolute;inset:0;display:block}
.blank.s{width:61px}
.tw{overflow:hidden}
.t{border-collapse:collapse;width:100%;font-size:14px;text-align:center}
.t th{background:var(--g3);color:#fff;font-weight:600;padding:6px 10px;border:1px solid var(--g3);white-space:nowrap}
.t th.rh{text-align:right}
.t td{border:1px solid #6d7a84;padding:6px 10px;min-width:44px;height:34px;font-variant-numeric:tabular-nums}
.note{color:var(--mute);font-size:13px}
/* instructions page */
.intro{color:#2b4080;display:flex;flex-direction:column;flex:1 1 auto}
.intro .meta{align-self:center;display:flex;align-items:center;gap:18px;margin:40px 0 26px;padding:11px 30px;background:#2d4799;color:#fff;border-radius:999px;font-size:15.5px;font-weight:500}
.intro .meta b{font-weight:800}
.intro .meta i{width:1.5px;height:20px;background:#fff;opacity:.6}
.intro h2{font-family:"Rubik","Heebo",sans-serif;font-weight:700;color:#2d4799;font-size:22.5px;text-align:center;margin:26px 0 12px}
.intro p.l{margin:0 0 12px}
.intro .luck{font-family:"Rubik","Heebo",sans-serif;font-weight:700;color:#2d4799;font-size:24px;text-align:center;margin-top:40px}
h2.draft{position:absolute;z-index:1;top:30px;inset-inline:0;margin:0;text-align:center;font-family:"Rubik","Heebo",sans-serif;font-weight:700;font-size:25px;line-height:1.2;color:#15386e}
/* closing page */
.finale{position:absolute;inset:0 0 var(--foot) 0;display:flex;flex-direction:column;overflow:hidden;
  background:#0f3266}
.fsky{flex:0 0 auto;position:relative;z-index:1;padding:58px 24px 30px;background:linear-gradient(to bottom,#061634,#0f3266);text-align:center;color:#fff;font-family:"Suez One","Rubik",serif;
  font-size:142px;line-height:1.06;text-shadow:0 6px 24px rgba(3,14,36,.45)}
.fsky p{margin:0}
.fsky p.gold{color:#ffcf6e}
.fsky .rule{display:block;width:180px;height:4px;margin:22px auto 0;border-radius:2px;background:linear-gradient(90deg,transparent,#ffcf6e,transparent)}
.fimg{flex:1 1 auto;min-height:0;position:relative}
.fimg img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:46% 100%;display:block}
.fimg::after{content:"";position:absolute;inset:0 0 auto 0;height:300px;background:linear-gradient(to bottom,#0f3266 0%,rgba(15,50,102,.6) 35%,rgba(15,50,102,0) 100%)}
/* cover */
.page.cover{padding:0;background:linear-gradient(152deg,var(--g1) 0%,var(--g2) 48%,var(--g3) 100%);color:var(--cream);display:flex;flex-direction:column;overflow:hidden}
.cover .cv-banner{position:relative;width:100%;height:118mm;overflow:hidden;line-height:0;flex:0 0 auto;margin:0}
.cover .cv-banner-img{width:100%;height:100%;display:block;object-fit:cover}
.cover .cv-banner::after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(to bottom,rgba(14,54,38,.30) 0%,transparent 24% 56%,rgba(39,97,73,.55) 85%,var(--g3) 100%)}
.cover .kicker{position:absolute;z-index:2;top:18px;inset-inline-start:26px;margin:0;color:#fff;text-shadow:0 2px 14px rgba(0,0,0,.6);font-size:20px;font-weight:800;letter-spacing:.03em;display:inline-flex;align-items:center;gap:9px;line-height:1.2}
.cover .note{position:absolute;z-index:3;bottom:16px;inset-inline-start:16px;max-width:290px;margin:0;background:var(--cream);color:#0e3626;padding:13px 15px 11px;border-radius:7px;rotate:-2.4deg;box-shadow:0 14px 30px rgba(10,40,26,.5);font-family:"Gveret Levin AlefAlefAlef",Heebo,cursive;line-height:1.45}
.cover .note .tape{position:absolute;top:-10px;inset-inline-end:20px;width:58px;height:20px;rotate:7deg;background:rgba(21,189,169,.7);border:1px solid rgba(255,255,255,.55);border-radius:2px;box-shadow:0 2px 6px rgba(0,0,0,.2)}
.cover .note p{margin:0;font-size:16px;line-height:1.45;font-weight:400}
.cover .note .hl{background:linear-gradient(transparent 55%,#ffe14d 55% 94%,transparent 94%);padding:0 2px}
.cover .note b{display:block;margin-top:4px;color:var(--g3);font-size:1.06em}
.cover .cv-body{position:relative;overflow:hidden;flex:1 1 auto;padding:30px 42px 34px;display:flex;flex-direction:column;gap:18px}
.cover .bg{position:absolute;inset:0;pointer-events:none;overflow:hidden}
.cover .blob{position:absolute;border-radius:48% 52% 60% 40%/55% 48% 52% 45%}
.cover .b1{width:36%;aspect-ratio:1;background:rgba(255,255,255,.10);top:-14%;inset-inline-start:-10%}
.cover .b2{width:32%;aspect-ratio:1;background:#123f2c;opacity:.35;bottom:-14%;inset-inline-end:-8%;border-radius:60% 40% 45% 55%/50% 60% 40% 50%}
.cover .b3{display:none}
.cover .geo{position:absolute;color:rgba(251,247,234,.16)}
.cover .g-compass{width:16%;bottom:8%;inset-inline-end:5%}
.cover .g-tri{width:15%;top:10%;inset-inline-start:-4%;rotate:8deg}
.cover .g-ruler,.cover .g-grid{display:none}
.cover .head{position:relative;z-index:1}
.cover .title{margin:0;font-family:"Suez One",Heebo,serif;font-weight:400;color:#fff;font-size:76px;line-height:1.02;letter-spacing:-.01em;text-shadow:0 3px 0 rgba(10,40,26,.22),0 12px 28px rgba(10,40,26,.3)}
.cover .sub{margin:10px 0 0;font-size:22px;font-weight:600;color:rgba(251,247,234,.95)}
.cover .cv-badges{display:flex;flex-wrap:wrap;align-items:center;gap:18px;margin-top:20px}
.cover .grade{display:inline-flex;flex-direction:column;align-items:center;justify-content:center;width:96px;height:96px;border-radius:50%;background:#0e3626;color:var(--cream);box-shadow:0 12px 26px rgba(10,40,26,.35),inset 0 0 0 3px rgba(251,247,234,.25);line-height:1}
.cover .grade small{font-size:15px;font-weight:600;opacity:.85}
.cover .grade b{font-family:"Suez One",Heebo,serif;font-weight:400;font-size:42px;margin-top:3px}
.cover .israel{display:inline-flex;align-items:center;gap:10px;background:#fff;color:#0038b8;padding:9px 16px 9px 11px;border-radius:999px;font-weight:800;font-size:21px;box-shadow:0 12px 26px rgba(10,40,26,.3),inset 0 0 0 2px #eaf0ff;rotate:-1.5deg}
.cover .il-flag{width:50px;height:auto;filter:drop-shadow(0 1px 1px rgba(0,0,0,.12))}
.cover .fields{position:relative;z-index:1;display:grid;grid-template-columns:1.4fr 1fr;gap:14px 28px;margin-top:8px;max-width:560px;color:#fff;font-weight:700;font-size:17px}
.cover .field{display:flex;align-items:flex-end;gap:10px}
.cover .field .line{flex:1;height:0;border-bottom:2.5px dashed rgba(251,247,234,.75);transform:translateY(-5px)}
.sfields{display:flex;gap:34px;margin:0 0 16px;padding:10px 16px;border:1.5px solid var(--line);border-radius:10px;background:var(--pale);font-weight:700;font-size:16px;color:var(--navy)}
.sfields .sf{display:flex;align-items:flex-end;gap:10px}
.sfields .sf:first-child{flex:1.6}.sfields .sf:last-child{flex:1}
.sfields .line{flex:1;height:0;border-bottom:2px solid #7d8f9c;transform:translateY(-4px)}
.cover .credit{position:relative;z-index:1;margin-top:auto;padding-top:16px;border-top:3px solid #0e3626;display:flex;align-items:center;gap:12px;justify-content:center;text-align:center}
.cover .credit img{width:56px;height:56px;border-radius:50%;background:#fff;box-shadow:0 0 0 3px rgba(251,247,234,.25)}
.cover .credit .lines{display:flex;flex-direction:column;gap:2px;font-size:13px;color:rgba(251,247,234,.95)}
.cover .credit .lines b{font-size:14.5px;color:#fff}
.cover.teacher{background:linear-gradient(152deg,#2d4799 0%,#15386e 52%,#0a2550 100%)}
.cover.teacher .cv-banner::after{background:linear-gradient(to bottom,rgba(7,26,58,.30) 0%,transparent 24% 56%,rgba(21,56,110,.55) 85%,#0a2550 100%)}
.cover.teacher .note b{color:#15386e}
.cover.teacher .grade{background:#071a3a}
.cover.teacher .credit{border-top-color:#071a3a}
.cover .badge{display:inline-block;background:#fff;color:#15386e;border-radius:999px;padding:6px 16px;font-weight:900;font-size:18px;margin-top:14px}
/* answer key (מחוון תשובות) — same layout and styles as the key of the previous exam (tools/build_exam.py) */
.kh{font-family:"Rubik","Heebo",sans-serif;font-weight:700;color:#15386e;font-size:25px;line-height:1.2;margin:0}
.ks{color:var(--mute);font-size:14px;margin:3px 0 0}
.key{border-collapse:collapse;width:100%;margin-top:12px;font-size:12.6px;line-height:1.38}
.key th{background:var(--g3);color:#fff;font-weight:600;padding:5px 7px;text-align:right;border:1px solid var(--g3)}
.key td{border:1px solid var(--line);padding:4px 7px;vertical-align:middle}
.key tbody{break-inside:avoid;border-top:1.6px solid #6d7a84}
.key tbody:nth-of-type(even) td{background:#f3f8f5}
.key .kq{width:42px;text-align:center;padding-inline:3px}
.key .num{display:inline-flex;width:25px;height:25px;font-size:13px}
.key .kt{width:92px;color:var(--mute);font-size:11.6px}
.key th.kt{color:#fff;font-size:12.6px}
.key .kp{width:36px;text-align:center;font-weight:800}
.key .ka{width:136px;font-weight:700}
.key .khow{width:auto;min-width:0}
.key .rubric-breakdown{margin-top:7px;border-top:1px solid #d9e3e0;padding-top:5px;font-size:11.9px;line-height:1.45;color:#3d4e58}
.key .krh{font-weight:650;color:#15386e;margin-bottom:3px}
.key .krl{margin:2px 0;break-inside:avoid}
.key .krp{white-space:nowrap;font-weight:650;color:#276149}
/* Preserve the previous Tnufa exam's five-column answer-key table on phones too.
   Scroll the key itself horizontally instead of changing rows to stacked cards;
   the student booklet and printed PDFs are untouched. */
@media screen and (max-width:700px){
 .answer-panel{padding:14px 12px!important;margin:10px!important;max-width:calc(100% - 20px);overflow-x:auto;-webkit-overflow-scrolling:touch}
 .answer-panel .key{width:100%;min-width:720px;font-size:12.6px;line-height:1.38}
 .answer-panel .key .rubric-breakdown{font-size:11.9px}
}
/* teacher booklet */
.tpage{width:210mm;min-height:297mm;padding:34px 60px var(--foot);position:relative}
.tfoot{position:fixed;bottom:0;inset-inline:0;height:var(--foot);background:#fff}
.tfoot .rule{position:absolute;top:0;inset-inline:0;height:4px;background:var(--deep)}
.tfoot .row{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:12px;padding-top:4px}
.tfoot img{width:52px;height:52px;border-radius:50%}
.tfoot .lines{display:flex;flex-direction:column;text-align:center;line-height:1.3}
.tfoot b{font-weight:800;font-size:12.5px;color:#122f4c}
.tfoot span{font-size:11px;color:#3a5168}
.tfoot .tag{position:absolute;inset-inline-end:60px;top:10px;font-size:11px;color:#b03030;font-weight:700}
.tbody{padding:0 60px 14px}
.tsec{break-before:page}
.tsec:first-child{break-before:auto}
h1.th{font-family:"Rubik","Heebo",sans-serif;font-weight:700;color:var(--navy);font-size:26px;margin:0 0 6px}
h2.th{font-family:"Rubik","Heebo",sans-serif;font-weight:700;color:var(--g3);font-size:17px;margin:14px 0 6px;break-after:avoid}
h3.th{font-weight:800;color:var(--navy);font-size:14.5px;margin:12px 0 4px;break-after:avoid}
.tsub{color:var(--mute);font-size:14px;margin:0 0 10px}
.tq{border:1.5px solid var(--line);border-radius:10px;padding:10px 14px;margin:8px 0 10px;background:#fbfdfc}
.tq .work,.tq .fill{display:none!important}
.tq .blank{width:60px;height:18px;border-bottom:1px solid #9aa8b4}
.tq .blank.s{width:40px}
.tq .q{padding-top:0;padding-bottom:0;border-top:0}
.tq .ans{color:var(--mute);font-size:13px}
.tmeta{display:flex;flex-wrap:wrap;gap:6px 10px;margin:6px 0 4px;font-size:12.5px}
.tmeta span{background:var(--pale);color:var(--g3);border-radius:999px;padding:3px 10px;font-weight:600}
.tmeta span.pt{background:var(--navy);color:#fff}
.rub{border-collapse:collapse;width:100%;font-size:13px;margin:4px 0 8px;break-inside:avoid}
.rub th{background:var(--g3);color:#fff;font-weight:600;padding:5px 8px;border:1px solid var(--g3);text-align:right}
.rub td{border:1px solid var(--line);padding:5px 8px;vertical-align:top}
.rub td.p{width:46px;text-align:center;font-weight:800;color:var(--navy);font-variant-numeric:tabular-nums}
.tpart{margin:8px 0 10px;padding-inline-start:12px;border-inline-start:3px solid var(--pale);break-inside:avoid}
.tpart .lead{font-weight:800;color:var(--g3)}
.tpart p{margin:3px 0}
.tpart .lab{font-weight:700;color:var(--navy)}
.map{border-collapse:collapse;width:100%;font-size:12.6px}
.map th{background:var(--navy);color:#fff;padding:5px 7px;border:1px solid var(--navy);font-weight:600}
.map td{border:1px solid var(--line);padding:4px 7px;text-align:center}
.map td.r{text-align:right}
.map tr:nth-child(even) td{background:#f3f8f5}
.sum{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:8px 0}
.sum table{width:100%}
ul.rules{margin:4px 0;padding-inline-start:20px}
ul.rules li{margin:3px 0}
"""

STUDENT_FIELDS = ('<div class="student-fields" aria-label="פרטי התלמיד">'
    '<div class="entry"><b>שם התלמיד/ה:</b><span></span></div>'
    '<div class="entry"><b>כיתה:</b><span></span></div></div>')

GRID_JS = r"""
/* Writing windows: plain whole squares only. */
const LINE = 'stroke="#b5cce0" stroke-width="0.7"';
const squares = (cols, rows, S, x0, y0) => {
  let g = '';
  for (let i = 0; i <= cols; i++) g += `<line x1="${x0 + i * S}" y1="${y0}" x2="${x0 + i * S}" y2="${y0 + rows * S}"/>`;
  for (let j = 0; j <= rows; j++) g += `<line x1="${x0}" y1="${y0 + j * S}" x2="${x0 + cols * S}" y2="${y0 + j * S}"/>`;
  return `<g ${LINE}>${g}</g>`;
};
document.querySelectorAll('.fill').forEach(el => {
  const S = 18, w = Math.ceil(el.clientWidth), h = Math.ceil(el.clientHeight);
  el.insertAdjacentHTML('afterbegin', `<svg width="${w}" height="${h}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">${squares(Math.ceil(w / S), Math.ceil(h / S), S, 0, 0)}</svg>`);
});
document.querySelectorAll('.work').forEach(el => {
  const S = 18, IN = 3, w = Math.floor(el.clientWidth), h = Math.floor(el.clientHeight);
  const cols = Math.floor((w - 2 * IN) / S), rows = Math.floor((h - 2 * IN) / S);
  el.insertAdjacentHTML('afterbegin', `<svg width="${w}" height="${h}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">${squares(cols, rows, S, Math.floor((w - cols * S) / 2), IN)}</svg>`);
});
document.querySelectorAll('.blank').forEach(el => {
  const S = 12, w = el.clientWidth, h = el.clientHeight;
  const cols = Math.floor((w - 1) / S), rows = Math.floor((h - 1) / S);
  el.innerHTML = `<svg width="${w}" height="${h}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">${squares(cols, rows, S, 0.5, 0.5)}</svg>`;
});
"""

# Spare room on a sheet raises the smallest writing window first, up to a cap.
FIT_JS = r"""
document.querySelectorAll('.page').forEach(pg => {
  const c = pg.querySelector('.content'); if (!c) return;
  const boxes = [...c.querySelectorAll('.work')];
  if (!boxes.length) return;
  const S = 18, CAP = 18;
  const hs = boxes.map(b => Math.floor((b.offsetHeight - 6) / S));
  boxes.forEach((b, i) => { b.style.height = hs[i] * S + 6 + 'px'; });
  let spare = c.getBoundingClientRect().bottom - c.lastElementChild.getBoundingClientRect().bottom;
  while (spare >= S) {
    const low = Math.min(...hs);
    if (low >= CAP) break;
    const i = hs.indexOf(low);
    hs[i]++; spare -= S;
    boxes[i].style.height = hs[i] * S + 6 + 'px';
  }
});
"""


def head(title, extra_css=""):
    return ('<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>%s</title><link rel="stylesheet" href="%s"><style>%s%s</style></head><body>' % (title, FONTS, CSS, extra_css))


def foot(page_no=None, fin=False, assets="assets/"):
    """Student footer: credit line only (no page number, no booklet name — Yaniv's request, 11.11.2026)."""
    return ('<div class="foot%s"><span class="rule"></span><div class="row"><img src="%slogo.svg" alt="">'
            '<div class="lines"><b>%s</b><span>%s</span></div></div></div>'
            % (" fin" if fin else "", assets, CREDIT_1, CREDIT_2))


def sheet(inner, page_no=None, fin=False, cls="", assets="assets/"):
    return '<section class="page %s"><div class="content">%s</div>%s</section>' % (cls, inner, foot(page_no, fin, assets))


GEO = ('<div class="bg" aria-hidden="true"><span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span>'
       '<svg class="geo g-compass" viewBox="0 0 120 120"><g fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><circle cx="60" cy="18" r="7"/><path d="M60 25 38 104M60 25l22 79M46 78h28"/><circle cx="60" cy="18" r="2.5" fill="currentColor"/></g></svg>'
       '<svg class="geo g-ruler" viewBox="0 0 160 40"><g fill="none" stroke="currentColor" stroke-width="3"><rect x="3" y="8" width="154" height="24" rx="4"/><path d="M23 8v10M43 8v10M63 8v10M83 8v10M103 8v10M123 8v10M143 8v10"/></g></svg>'
       '<svg class="geo g-tri" viewBox="0 0 120 100"><path d="M10 90h100L10 20z" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M10 72h18v18" fill="none" stroke="currentColor" stroke-width="3"/></svg>'
       '<svg class="geo g-grid" viewBox="0 0 160 120"><g fill="none" stroke="currentColor" stroke-width="2"><path d="M10 10h140M10 40h140M10 70h140M10 100h140M20 5v110M55 5v110M90 5v110M125 5v110"/><polyline points="20,100 55,70 90,78 125,30" stroke-width="4"/></g></svg>'
       '</div>')


def cover(teacher=False, assets="assets/"):
    """Keeps the existing cover structure but uses original vector mathematics/Jerusalem artwork with the note,
    Suez One title, grade circle, 'ישראל תצליח' badge, credit line with the round logo."""
    note = ('<figure class="note"><span class="tape" aria-hidden="true"></span><p><span class="hl">מירושלים תצא התנופה</span> '
            'ויפרצו המצליחים את הגבולות, ויגיעו <b>לאינסוף ∞</b></p></figure>')
    if teacher:
        note = ('<figure class="note"><span class="tape" aria-hidden="true"></span><p><span class="hl">חוברת זו מיועדת למורה בלבד.</span> '
                'פתרונות מלאים, מחוון, טעויות צפויות והערות להוראה.<b>לא לפרסום לתלמידים.</b></p></figure>')
    flag = ('<svg class="il-flag" viewBox="0 0 66 44" aria-hidden="true"><rect width="66" height="44" rx="4" fill="#fff" stroke="#d7dbe6"/>'
            '<rect x="4" y="7" width="58" height="5.4" fill="#0038b8"/><rect x="4" y="31.6" width="58" height="5.4" fill="#0038b8"/>'
            '<g fill="none" stroke="#0038b8" stroke-width="2.4" stroke-linejoin="round"><path d="M33 15.5l6.1 10.6H26.9z"/><path d="M33 28.5l-6.1-10.6h12.2z"/></g></svg>')
    badges = ('<div class="cv-badges"><span class="grade" aria-label="כיתה ט׳"><small>כיתה</small><b>ט׳</b></span>'
              '<span class="israel" aria-label="ישראל תצליח">%s<b>ישראל תצליח</b></span></div>' % flag)
    fields = ""  # name and class are on the first questions page (STUDENT_FIELDS), not the cover
    badge = '<span class="badge">חוברת מורה — פתרונות ומחוון</span>' if teacher else ""
    if teacher:
        fields = '<div class="fields"><div class="field"><label>שם המורה:</label><span class="line"></span></div><div class="field"><label>כיתה:</label><span class="line"></span></div></div>'
    return ('<section class="page cover%s">'
            '<figure class="cv-banner"><img class="cv-banner-img" src="%scover-math.svg" alt="שלושה תלמידים לומדים מתמטיקה מול נוף ירושלים, אחד מהם חובש כיפה">'
            '<p class="kicker">לקראת תנופה</p>%s</figure>'
            '<div class="cv-body">%s'
            '<div class="head"><h1 class="title">%s</h1><p class="sub">%s</p>%s%s</div>%s'
            '<div class="credit"><img src="%slogo.svg" alt="לוגו ההדרכה"><div class="lines"><b>%s</b><span>%s</span></div></div>'
            '</div></section>' % (" teacher" if teacher else "", assets, note, GEO, TITLE, SUBTITLE, badge, badges, fields, assets, CREDIT_1, CREDIT_2))


INTRO = """<div class="intro">
<p class="meta"><span>זמן: <b>90 דקות</b></span><i></i><span>17 שאלות</span><i></i><span>מותר להשתמש במחשבון ובסרגל</span></p>
<h2>מה במבחן?</h2>
<p class="l">לפניכם מבחן במתמטיקה להכנה לקראת מבחן תנופה. השאלות משתייכות לתחום המספרי, לתחום האלגברי, לתחום הגאומטרי ולתחום הנתונים.</p>
<p class="l">המבחן אינו מבחן רשמי של ראמ״ה. הוא נכתב כדי לתרגל את סוגי השאלות, את דרכי החשיבה ואת ההסברים שנדרשים במבחן.</p>
<h2>אז מה צריך לעשות?</h2>
<p class="l">יש לפתור את כל השאלות ברצינות ובתשומת לב, ולקרוא כל שאלה עד סופה.</p>
<p class="l">לכתוב רק בעט כחול, בעט שחור או בעיפרון.</p>
<p class="l">בשאלות שבהן יש לבחור תשובה, יש לסמן X במשבצת שליד התשובה שלדעתכם היא הנכונה. בשאלות שבהן נאמר &quot;סמנו את כל&quot; — אפשר לסמן יותר מתשובה אחת.</p>
<p class="l">כאשר כתוב &quot;הציגו את דרך הפתרון&quot; או &quot;נמקו&quot; — הדרך וההסבר הם חלק מהתשובה, וגם הם נבדקים.</p>
<h2>ומה אפשר לעשות?</h2>
<p class="l">אפשר להיעזר במחשבון ובסרגל.</p>
<p class="l">אפשר להיעזר בדפי הטיוטה המצורפים בסוף המבחן. דפי הטיוטה לא ייבדקו, אלא אם ציינתם בשאלה שהמשכתם בהם.</p>
<p class="l">אפשר לכתוב בשטח המשובץ שמתחת לכל שאלה. אם חסר מקום — אפשר להמשיך בדף הטיוטה ולציין זאת בשאלה.</p>
<p class="l" style="margin-top:20px">שימו לב, הסרטוטים במבחן מוקטנים.</p>
<p class="luck">בהצלחה!</p>
</div>"""


STUDENT_FIELDS = ('<div class="sfields"><div class="sf"><label>שם התלמיד/ה:</label><span class="line"></span></div>'
                  '<div class="sf"><label>כיתה:</label><span class="line"></span></div></div>')


def draft_sheet(n):
    return '<div class="fill"></div><h2 class="draft">דף טיוטה %d — ייבדק רק אם צוין בשאלה</h2>' % n


def key_group(q):
    """Preserve the previous exam's five-column layout and merged question/topic cells.

    Keep the new exam's validated per-part scoring inside the solution column.
    Desktop: one numbered question/topic cell spanning all parts, exactly as in
    tools/build_exam.py. Mobile: the whole <tbody> remains one grouped card.
    """
    rows = ""
    for index, p in enumerate(q.parts):
        lead = (
            '<td class="kq" rowspan="%d" data-label="שאלה"><span class="num">%d</span></td>'
            '<td class="kt" rowspan="%d" data-label="נושא">%s</td>'
            % (len(q.parts), q.n, len(q.parts), q.topic)
        ) if index == 0 else ""
        rubric = "".join(
            '<div class="krl"><span class="krp">%d נק׳</span> — %s</div>' % (points, criterion)
            for points, criterion in p.rubric
        )
        scoring = ('<div class="rubric-breakdown"><div class="krh">כללי ניקוד (מתוך %d נק׳)</div>%s</div>'
                   % (p.points, rubric))
        rows += (
            '<tr>%s'
            '<td class="kp" data-label="סעיף">%s</td>'
            '<td class="ka" data-label="תשובה">%s</td>'
            '<td class="khow" data-label="דרך הפתרון וכללי ניקוד">%s%s</td></tr>'
        ) % (lead, p.letter or "—", p.key, p.how, scoring)
    return "<tbody>%s</tbody>" % rows


def key_sheet(qs):
    """The prior exam's five-column table, enriched with full/partial/zero scoring."""
    head = '<h1 class="kh">מחוון תשובות</h1><p class="ks">%s במתמטיקה לכיתה ט׳ · %s · למורה</p>' % (TITLE, DATE)
    return head + ('<table class="key"><thead><tr><th class="kq">שאלה</th><th class="kt">נושא</th><th class="kp">סעיף</th><th class="ka">תשובה</th>'
                   '<th>דרך הפתרון</th></tr></thead>%s</table>' % H.auto_math("".join(key_group(q) for q in qs)))

def finale(assets="assets/"):
    return ('<div class="finale"><div class="fsky"><p>ירושלים</p><p class="gold">תצליח!</p><span class="rule"></span></div>'
            '<div class="fimg"><img src="%sfinale.jpg" alt="זריחה מעל ירושלים מהר הזיתים; על אבן בחזית מחברת ומחוגה"></div></div>' % assets)


# ---------------- teacher booklet ----------------
TEACHER_PAGE_CSS = "@page{size:A4;margin:34px 0 92px 0}@page:first{margin:0}"

def tfoot(assets="assets/"):
    return ('<div class="tfoot"><span class="rule"></span><div class="row"><img src="%slogo.svg" alt="">'
            '<div class="lines"><b>%s</b><span>%s</span></div></div><span class="tag">חוברת מורה — לא לפרסום לתלמידים</span></div>' % (assets, CREDIT_1, CREDIT_2))


def rubric_table(rows):
    return '<table class="rub"><thead><tr><th style="width:46px">נק׳</th><th>קריטריון</th></tr></thead><tbody>%s</tbody></table>' % "".join(
        '<tr><td class="p">%d</td><td>%s</td></tr>' % (p, c) for p, c in rows)


def teacher_question(q):
    meta = ('<div class="tmeta"><span class="pt">%d נקודות</span><span>תחום: %s</span><span>רמת קושי: %s</span><span>זמן מתוכנן: %d דק׳</span>%s</div>' % (
        q.points, DOMAIN_HE[q.domain], DIFFICULTY_HE[q.difficulty], q.minutes,
        "".join('<span>%s</span>' % r for r in q.representations)))
    out = '<section class="tsec"><h1 class="th">שאלה %d — %s</h1><p class="tsub">%s</p>%s' % (q.n, q.topic, q.skill, meta)
    out += '<div class="tq">%s</div>' % q.student_html
    out += ('<h3 class="th">מטרת השאלה (Claim–Evidence–Task)</h3><p><span class="lab">טענה:</span> %s<br><span class="lab">ראיה:</span> %s<br>'
            '<span class="lab">משימה:</span> %s</p>' % (q.claim, q.evidence, q.task))
    if q.depends:
        out += '<p><span class="lab">תלות בין סעיפים:</span> %s</p>' % q.depends
    for p in q.parts:
        lead = ("סעיף %s" % p.letter) if p.letter else "השאלה"
        out += '<div class="tpart"><p class="lead">%s · %d נק׳ · %s</p>' % (lead, p.points, THINKING_HE[p.thinking])
        out += '<p><span class="lab">תשובה:</span> %s</p><p><span class="lab">פתרון מלא:</span> %s</p>' % (p.answer, p.solution)
        if p.alternatives:
            out += '<p><span class="lab">דרכים חלופיות:</span> %s</p>' % p.alternatives
        out += '<p class="lab" style="margin-top:6px">מחוון:</p>' + rubric_table(p.rubric)
        if p.errors:
            out += '<p><span class="lab">טעויות צפויות ומה הן מאבחנות:</span> %s</p>' % p.errors
        if p.carry:
            out += '<p><span class="lab">טעות נגררת:</span> %s</p>' % p.carry
        out += '</div>'
    out += '<h3 class="th">הערות להוראה</h3><p>%s</p>' % q.notes
    out += '<h3 class="th">מקוריות ונגישות</h3><p>%s</p><p>%s</p></section>' % (q.reference, q.accessibility)
    return out


def teacher_map(qs):
    rows = ""
    for q in qs:
        th = "/".join(sorted({THINKING_HE[p.thinking].split(" ")[0] if p.thinking != "open" else "פתוח" for p in q.parts}))
        rows += '<tr><td>%d</td><td class="r">%s</td><td>%s</td><td>%d</td><td>%s</td><td>%s</td><td>%d</td><td>%s</td></tr>' % (
            q.n, q.topic, DOMAIN_HE[q.domain], q.points, th, DIFFICULTY_HE[q.difficulty], q.minutes, "✓" if q.literacy else "")
    return ('<table class="map"><thead><tr><th>שאלה</th><th>נושא</th><th>תחום</th><th>נק׳</th><th>רמות חשיבה</th><th>קושי</th><th>דק׳</th><th>אוריינות</th></tr></thead>'
            '<tbody>%s</tbody></table>' % rows)


def teacher_summary(qs, plan):
    from collections import Counter
    dom, th = Counter(), Counter()
    for q in qs:
        dom[q.domain] += q.points
        for p in q.parts:
            th[p.thinking] += p.points
    lit = sum(q.points for q in qs if q.literacy)
    t1 = '<table class="map"><thead><tr><th>תחום</th><th>מתוכנן</th><th>בפועל</th></tr></thead><tbody>%s</tbody></table>' % "".join(
        '<tr><td class="r">%s</td><td>%d</td><td>%d</td></tr>' % (DOMAIN_HE[d], plan["domains"][d], dom[d]) for d in dom)
    t2 = '<table class="map"><thead><tr><th>רמת חשיבה</th><th>מתוכנן</th><th>בפועל</th></tr></thead><tbody>%s</tbody></table>' % "".join(
        '<tr><td class="r">%s</td><td>%d</td><td>%d</td></tr>' % (THINKING_HE[k], plan["thinking"][k], th[k]) for k in th)
    return ('<div class="sum"><div>%s</div><div>%s</div></div><p>אוריינות מציאותית (מידול בהקשר חוץ־מתמטי): %d נקודות מתוך 100 (יעד: כ־%d). '
            'זמן פתרון מתוכנן: %d דקות + 10 דקות קריאה ובקרה = 90 דקות.</p>' % (t1, t2, lit, plan["literacy"], sum(q.minutes for q in qs)))


RULES = """<ul class="rules">
<li>יש לבדוק חישובים שנכתבו בצד, או בדף הטיוטה כשהתלמיד ציין בשאלה שהמשיך בו, ולקבל תשובות נכונות גם אם לא נכתבו במקום המיועד.</li>
<li>בכל מקום שבו כתוב &quot;דרך פתרון&quot; — מתקבלת כל דרך נכונה ומנומקת, גם אם אינה הדרך שבמחוון.</li>
<li>אין להוריד נקודות על מידע עודף שאינו סותר את דרך הפתרון.</li>
<li>בפתרון משוואות, כל איבר שגוי נחשב טעות אחת.</li>
<li>תשובה נכונה ללא דרך — רק כאשר המחוון מציין זאת במפורש. בשאלות &quot;הציגו את דרך הפתרון&quot; תשובה ללא דרך מקבלת לכל היותר את השורה המתאימה במחוון.</li>
<li>טעות נגררת: כאשר סעיף נסמך על תוצאה שגויה מסעיף קודם, והעבודה בסעיף הנוכחי נכונה ועקבית — ניקוד מלא לסעיף הנוכחי, לפי הכלל הרשום בשאלה.</li>
<li>בשאלות רב־ברירה עם תשובה אחת: סימון יותר מתשובה אחת — 0. בשאלות &quot;סמנו את כל&quot; — ניקוד רק לסימון המדויק.</li>
<li>בשאלות &quot;כן/לא + נימוק&quot;: אם הסימון חסר או שגוי אך הנימוק נכון ומובן ממנו הסימון שהתלמיד התכוון אליו — אין להפחית נקודות.</li>
<li>אם אין תשובה כלל או שהתשובה אינה ניסיון לענות (&quot;לא יודע&quot;, שרבוט) — 0 נקודות לסעיף.</li>
</ul>"""


def teacher_doc(qs, plan, assets="assets/"):
    body = cover(teacher=True, assets=assets)
    body += '<div class="tbody">'
    body += ('<section class="tsec"><h1 class="th">מפת המבחן</h1><p class="tsub">17 שאלות · 100 נקודות · 90 דקות · ארבעה תחומים</p>%s'
             '<h2 class="th">סיכום התמהיל</h2>%s<h2 class="th">כללי בדיקה</h2>%s</section>' % (teacher_map(qs), teacher_summary(qs, plan), RULES))
    for q in qs:
        body += teacher_question(q)
    body += '</div>'
    # the footer is printed by Chromium in the bottom page margin (render_teacher), so text never hides under it
    return head("חוברת מורה — " + TITLE, TEACHER_PAGE_CSS) + H.auto_math(body) + "</body></html>"
