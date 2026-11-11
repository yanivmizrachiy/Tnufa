# -*- coding: utf-8 -*-
"""Deterministic render: questions → A4 sheets → STUDENT.pdf + web reader (public/) and TEACHER.pdf (private/).
Chromium (Playwright) lays out the sheets; PyMuPDF adds bookmarks and metadata. Nothing here touches any
path outside exams/tnufa-exam-2/."""
import os, json, math, hashlib, datetime, shutil
import fitz
from playwright.sync_api import sync_playwright
from . import booklet as B

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))          # exams/tnufa-exam-2
PUBLIC = os.path.join(ROOT, "public")
PRIVATE = os.path.join(ROOT, "private")
BUILD = os.path.join(ROOT, "build")
STUDENT_PDF = os.path.join(PUBLIC, "STUDENT.pdf")
TEACHER_PDF = os.path.join(PRIVATE, "TEACHER.pdf")


def _uri(p):
    return "file:///" + p.replace("\\", "/")


def _write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Browser:
    def __enter__(self):
        self.p = sync_playwright().start()
        self.br = self.p.chromium.launch(headless=True, timeout=60000)
        self.pg = self.br.new_page(viewport={"width": 794, "height": 1123})
        self.pg.set_default_timeout(90000)
        self.errs = []
        self.pg.on("console", lambda m_: self.errs.append(m_.text) if m_.type == "error" else None)
        self.pg.on("pageerror", lambda e: self.errs.append(str(e)))
        self.pg.emulate_media(media="print")
        return self

    def __exit__(self, *a):
        try:
            self.br.close()
        finally:
            self.p.stop()

    def open(self, path):
        self.pg.goto(_uri(path), wait_until="networkidle")
        self.pg.evaluate("document.fonts.ready.then(()=>1)")
        self.pg.wait_for_timeout(150)
        assert self.pg.evaluate("document.fonts.check('15px Heebo') && document.fonts.check('700 22px Rubik')"), "fonts did not load"
        assert not self.errs, self.errs


# ---------------- student ----------------
def paginate(bw, qs, tmp):
    """Measure every question at the final column width, then pack greedily (a question is never split)."""
    html = B.head("measure") + B.sheet("".join(q.student_html for q in qs), assets="assets/").replace(
        'class="page "', 'class="page " style="height:auto;overflow:visible"') + "</body></html>"
    _write(tmp, html)
    bw.open(tmp)
    heights = bw.pg.evaluate("[...document.querySelectorAll('.q')].map(e => e.getBoundingClientRect().height)")
    avail = bw.pg.evaluate("""() => { const c = document.createElement('section'); c.className='page';
        c.innerHTML='<div class="content"></div>'; document.body.append(c);
        const h = c.querySelector('.content').getBoundingClientRect().height; c.remove(); return h; }""")
    too_tall = [qs[i].n for i, h in enumerate(heights) if h > avail]
    assert not too_tall, "questions taller than one sheet: %s" % too_tall
    sheets, cur, used = [], [], 0.0
    for i, h in enumerate(heights):
        if cur and used + h > avail:
            sheets.append(cur)
            cur, used = [], 0.0
        cur.append(i)
        used += h
    sheets.append(cur)
    return sheets, [round(h) for h in heights], round(avail)


def student_pages(qs, sheets):
    """All A4 sheets of the student booklet, in order, with page numbers."""
    pages = [B.cover(assets="assets/")]
    n = 2
    pages.append(B.sheet(B.INTRO, n))
    for s in sheets:
        n += 1
        pages.append(B.sheet("".join(qs[i].student_html for i in s), n))
    for d in (1, 2):
        n += 1
        pages.append(B.sheet(B.draft_sheet(d), n))
    n += 1
    pages.append(B.sheet(B.finale(), n, fin=True))
    return pages


def render_student(bw, qs, log=print):
    tmp = os.path.join(PUBLIC, ".print.html")
    try:
        sheets, heights, avail = paginate(bw, qs, tmp)
        log("sheet content height: %d; question heights: %s" % (avail, heights))
        log("sheets: %s" % [[qs[i].n for i in s] for s in sheets])
        pages = student_pages(qs, sheets)
        _write(tmp, B.head(B.TITLE) + "".join(pages) + "</body></html>")
        bw.open(tmp)
        bw.pg.evaluate(B.FIT_JS)
        bw.pg.evaluate(B.GRID_JS)
        over = bw.pg.evaluate("[...document.querySelectorAll('.content')].map((c,i)=>[i+1,c.scrollHeight-c.clientHeight,c.scrollWidth-c.clientWidth]).filter(a=>a[1]>1||a[2]>1)")
        assert not over, "overflowing sheets: %s" % over
        assert not bw.errs, bw.errs
        rendered = bw.pg.evaluate("Array.from(document.querySelectorAll('.page')).map(s => s.outerHTML)")
        raw = STUDENT_PDF + ".raw"
        bw.pg.pdf(path=raw, prefer_css_page_size=True, print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    doc = fitz.open(raw)
    assert doc.page_count == len(pages), (doc.page_count, len(pages))
    toc = [[1, "עמוד שער", 1], [1, "הוראות", 2]]
    for i, s in enumerate(sheets):
        toc += [[1, "שאלה %d" % qs[k].n, i + 3] for k in s]
    n = len(sheets) + 3
    toc += [[1, "דף טיוטה 1", n], [1, "דף טיוטה 2", n + 1], [1, "עמוד סיום", n + 2]]
    doc.set_toc(toc)
    doc.set_metadata({"title": B.TITLE + " — " + B.SUBTITLE, "author": "יניב רז", "subject": "לקראת תנופה — מבחן לדוגמה, נובמבר 2026"})
    doc.save(STUDENT_PDF, garbage=4, deflate=True)
    doc.close()
    os.remove(raw)
    log("wrote public/STUDENT.pdf: %d pages, %d KB" % (len(pages), os.path.getsize(STUDENT_PDF) // 1024))
    emit_reader(qs, sheets, rendered)
    return sheets, rendered


READER_CSS = r"""
html,body{overflow-x:hidden}
body{background:#e3e9ef;margin:0}
.topbar{position:sticky;top:0;z-index:20;background:#161f31;color:#fff;box-shadow:0 4px 18px rgba(0,0,0,.25)}
.topbar .in{max-width:1100px;margin:0 auto;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px;padding:8px 14px}
.brand{display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none}
.brand img{width:34px;height:34px;border-radius:50%;background:#fff}
.brand strong{display:block;font-size:15px;line-height:1.1}
.brand small{font-size:11.5px;opacity:.8}
.acts{display:flex;gap:8px;align-items:center;flex-wrap:wrap;min-width:0;max-width:100%}
.btn{display:inline-flex;align-items:center;gap:6px;background:#276149;color:#fff;border:0;border-radius:999px;padding:8px 14px;font:600 14px Heebo,Arial,sans-serif;cursor:pointer;text-decoration:none}
.btn.alt{background:#2d4799}
.btn.ghost{background:transparent;border:1px solid rgba(255,255,255,.4)}
select.btn{appearance:none;padding-inline-end:22px}
main{padding:18px 0 40px}
main{overflow:hidden;direction:ltr}
.wrap{width:794px;transform-origin:top left;direction:rtl;margin:0}
.wrap .page{box-shadow:0 10px 30px rgba(10,30,50,.18);margin:0 auto 18px}
.sep{width:210mm;max-width:100%;height:3px;background:#126c6a;margin:0 auto 18px;border-radius:2px}
@media screen and (max-width:860px){.brand small{display:none}.btn span.l{display:none}select.btn{max-width:150px;font-size:13px}}
@media print{body{background:#fff}.topbar,.sep{display:none}main{padding:0}.wrap{transform:none!important;height:auto!important}.wrap .page{box-shadow:none;margin:0}}
"""

READER_JS = r"""
(function(){
  const wrap=document.getElementById('wrap');
  function fit(){
    const vw=document.documentElement.clientWidth;
    const s=Math.min(1,(vw-16)/794);
    wrap.style.transform='scale('+s+')';
    wrap.style.marginLeft=Math.max(0,(vw-794*s)/2)+'px';
    wrap.style.height=(wrap.scrollHeight*s)+'px';
  }
  window.addEventListener('resize',fit); window.addEventListener('load',fit); fit();
  document.getElementById('goto').addEventListener('change',e=>{const id=e.target.value; if(id){document.getElementById(id).scrollIntoView({behavior:'smooth',block:'start'});e.target.value='';}});
  document.getElementById('print').addEventListener('click',()=>window.print());
})();
"""


def emit_reader(qs, sheets, rendered):
    """public/index.html: the cover and every A4 sheet, inline, from the same render as the PDF."""
    opts = ['<option value="">מעבר בחוברת…</option>', '<option value="p1">עמוד שער</option>', '<option value="p2">הוראות</option>']
    for q in qs:
        opts.append('<option value="q%d">שאלה %d — %s</option>' % (q.n, q.n, q.topic))
    n = len(sheets) + 3
    opts += ['<option value="p%d">דף טיוטה 1</option>' % n, '<option value="p%d">דף טיוטה 2</option>' % (n + 1), '<option value="p%d">עמוד סיום</option>' % (n + 2)]
    body = ('<header class="topbar"><div class="in"><a class="brand" href="#p1"><img src="assets/logo.svg" alt=""><span><strong>%s</strong><small>%s</small></span></a>'
            '<div class="acts"><select id="goto" class="btn ghost" aria-label="מעבר בחוברת">%s</select>'
            '<button id="print" class="btn alt" type="button">🖨 <span class="l">הדפסה</span></button>'
            '<a class="btn" href="STUDENT.pdf" download="מבחן-תנופה-לדוגמה.pdf">⬇ <span class="l">הורדה</span></a></div></div></header>'
            '<main><div id="wrap" class="wrap">' % (B.TITLE, B.SUBTITLE, "".join(opts)))
    for i, html in enumerate(rendered):
        page = html.replace('<section class="page', '<section id="p%d" class="page' % (i + 1), 1)
        body += page + ('<div class="sep"></div>' if i < len(rendered) - 1 else "")
    body += '</div></main><script>%s</script>' % READER_JS
    doc = B.head(B.TITLE + " — " + B.SUBTITLE, READER_CSS) + body + "</body></html>"
    doc = doc.replace("<head>", '<head><meta name="description" content="מבחן תנופה לדוגמה (נובמבר 2026) — הכנה לכיתה ט׳ במתמטיקה: צפייה בחוברת, הדפסה והורדת PDF.">', 1)
    _write(os.path.join(PUBLIC, "index.html"), doc)
    manifest = {
        "id": "tnufa-exam-2", "name": B.TITLE + " — " + B.SUBTITLE, "pages": len(rendered),
        "sheets": [[qs[i].n for i in s] for s in sheets], "pdf": {"file": "STUDENT.pdf", "sha256": "sha256-" + _sha(STUDENT_PDF), "pageCount": len(rendered)},
        "builtAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _write(os.path.join(PUBLIC, "manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("wrote public/index.html + manifest.json (%d pages)" % len(rendered))


# ---------------- teacher ----------------
def render_teacher(bw, qs, plan, log=print):
    os.makedirs(PRIVATE, exist_ok=True)
    html_path = os.path.join(PRIVATE, "teacher.html")
    _write(html_path, B.teacher_doc(qs, plan, assets="../public/assets/"))
    bw.open(html_path)
    raw = TEACHER_PDF + ".raw"
    bw.pg.pdf(path=raw, prefer_css_page_size=True, print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    doc = fitz.open(raw)
    toc = [[1, "שער", 1], [1, "מפת המבחן וכללי בדיקה", 2]]
    # find the page of every question by its heading text
    for q in qs:
        needle = "שאלה %d —" % q.n
        for i in range(doc.page_count):
            if needle in doc[i].get_text("text"):
                toc.append([1, "שאלה %d" % q.n, i + 1])
                break
    doc.set_toc(toc)
    doc.set_metadata({"title": "חוברת מורה — " + B.TITLE, "author": "יניב רז", "subject": "פתרונות ומחוון — לא לפרסום"})
    doc.save(TEACHER_PDF, garbage=4, deflate=True)
    pc = doc.page_count
    doc.close()
    os.remove(raw)
    log("wrote private/TEACHER.pdf: %d pages, %d KB" % (pc, os.path.getsize(TEACHER_PDF) // 1024))
    return pc


# ---------------- single question preview ----------------
def preview(bw, q, log=print):
    os.makedirs(BUILD, exist_ok=True)
    tmp = os.path.join(PUBLIC, ".preview.html")
    try:
        _write(tmp, B.head("preview q%d" % q.n) + B.sheet(q.student_html, assets="assets/") + "</body></html>")
        bw.open(tmp)
        bw.pg.evaluate(B.FIT_JS)
        bw.pg.evaluate(B.GRID_JS)
        over = bw.pg.evaluate("(c=>[c.scrollHeight-c.clientHeight,c.scrollWidth-c.clientWidth])(document.querySelector('.content'))")
        html = bw.pg.evaluate("document.querySelector('.page').outerHTML")
        out_html = os.path.join(BUILD, "preview-q%d.html" % q.n)
        _write(out_html, B.head("preview q%d" % q.n) + html.replace('src="assets/', 'src="../public/assets/') + "</body></html>")
        png = os.path.join(BUILD, "preview-q%d.png" % q.n)
        bw.pg.screenshot(path=png, full_page=True)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    log("preview q%d → build/preview-q%d.png (overflow %s)" % (q.n, q.n, over))
    return png


# ---------------- page snapshots for QA ----------------
def snapshots(pdf, out_dir, dpi=60, prefix="p"):
    os.makedirs(out_dir, exist_ok=True)
    d = fitz.open(pdf)
    paths = []
    for i, p in enumerate(d):
        fp = os.path.join(out_dir, "%s%02d.png" % (prefix, i + 1))
        p.get_pixmap(dpi=dpi).save(fp)
        paths.append(fp)
    d.close()
    return paths
