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
    html = B.head("measure") + B.sheet(B.STUDENT_FIELDS + "".join(q.student_html for q in qs), assets="assets/").replace(
        'class="page "', 'class="page " style="height:auto;overflow:visible"') + "</body></html>"
    _write(tmp, html)
    bw.open(tmp)
    heights = bw.pg.evaluate("[...document.querySelectorAll('.q')].map(e => e.getBoundingClientRect().height)")
    fields_h = bw.pg.evaluate("(e => e.getBoundingClientRect().height + parseFloat(getComputedStyle(e).marginBottom))(document.querySelector('.sfields'))")
    avail = bw.pg.evaluate("""() => { const c = document.createElement('section'); c.className='page';
        c.innerHTML='<div class="content"></div>'; document.body.append(c);
        const h = c.querySelector('.content').getBoundingClientRect().height; c.remove(); return h; }""")
    too_tall = [qs[i].n for i, h in enumerate(heights) if h > avail]
    assert not too_tall, "questions taller than one sheet: %s" % too_tall
    sheets, cur, used = [], [], fields_h          # the first sheet also carries the name/class line
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
    for k, s in enumerate(sheets):
        n += 1
        pages.append(B.sheet((B.STUDENT_FIELDS if k == 0 else "") + "".join(qs[i].student_html for i in s), n))
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

        # the answer key: one long page as tall as its content (as in the previous exam), after the closing page
        key_page = B.sheet(B.key_sheet(qs)).replace('class="page "', 'class="page key-page" style="height:auto;overflow:visible"', 1)
        _write(tmp, B.head(B.TITLE) + key_page + "</body></html>")
        bw.open(tmp)
        key_h = math.ceil(bw.pg.evaluate("document.querySelector('.page').getBoundingClientRect().height")) + 48
        bw.pg.evaluate("h => { const s = document.querySelector('.page').style; s.height = h + 'px'; s.overflow = 'hidden'; }", key_h)
        assert not bw.errs, bw.errs
        rendered.append(bw.pg.evaluate("document.querySelector('.page').outerHTML"))
        key_raw = STUDENT_PDF + ".key"
        bw.pg.add_style_tag(content="@page{size:210mm %dpx;margin:0}.page{break-after:auto}.key tbody{break-inside:auto}" % key_h)
        bw.pg.pdf(path=key_raw, prefer_css_page_size=True, print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        log("key page height: %d px" % key_h)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    doc = fitz.open(raw)
    assert doc.page_count == len(pages), (doc.page_count, len(pages))
    key_doc = fitz.open(key_raw)
    assert key_doc.page_count == 1, key_doc.page_count
    doc.insert_pdf(key_doc)
    key_doc.close()
    os.remove(key_raw)
    toc = [[1, "עמוד שער", 1], [1, "הוראות", 2]]
    for i, s in enumerate(sheets):
        toc += [[1, "שאלה %d" % qs[k].n, i + 3] for k in s]
    n = len(sheets) + 3
    toc += [[1, "דף טיוטה 1", n], [1, "דף טיוטה 2", n + 1], [1, "עמוד סיום", n + 2], [1, "מחוון תשובות", n + 3]]
    doc.set_toc(toc)
    doc.set_metadata({"title": B.TITLE + " — " + B.SUBTITLE, "author": "יניב רז", "subject": "לקראת תנופה — מבחן לדוגמה, נובמבר 2026"})
    doc.save(STUDENT_PDF, garbage=4, deflate=True)
    doc.close()
    os.remove(raw)
    log("wrote public/STUDENT.pdf: %d pages (+ answer key), %d KB" % (len(pages) + 1, os.path.getsize(STUDENT_PDF) // 1024))
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
main{padding:18px 0 40px}
main{overflow:hidden;direction:ltr}
.wrap{width:794px;transform-origin:top left;direction:rtl;margin:0}
.wrap .page{margin:0 auto;box-shadow:0 0 0 1px #c3ced8}
.sep{width:210mm;max-width:100%;height:2px;background:#126c6a;margin:0 auto}
@media screen and (max-width:860px){.brand small{display:none}}
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
})();
"""


def emit_reader(qs, sheets, rendered):
    """public/index.html: the cover and every A4 sheet, inline, from the same render as the PDF."""
    body = ('<header class="topbar"><div class="in"><a class="brand" href="#p1"><img src="assets/logo.svg" alt=""><span><strong>%s</strong><small>%s</small></span></a>'
            '<div class="acts"><a class="btn" href="STUDENT.pdf" download="מבחן-תנופה-לדוגמה.pdf">⬇ הורדה</a></div></div></header>'
            '<main><div id="wrap" class="wrap">' % (B.TITLE, B.SUBTITLE))
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
    bw.pg.pdf(path=raw, prefer_css_page_size=True, print_background=True)
    # footer: rendered once on its own 210mm × 92px sheet and stamped into the empty 92px bottom margin of every
    # page except the cover, so rubric text can never slide under it
    foot_html = os.path.join(PRIVATE, ".tfoot.html")
    _write(foot_html, B.head("footer", "@page{size:210mm 92px;margin:0}html,body{margin:0}.tfoot{position:relative}") +
           B.tfoot(assets="../public/assets/") + "</body></html>")
    bw.open(foot_html)
    foot_pdf = raw + ".foot"
    bw.pg.pdf(path=foot_pdf, prefer_css_page_size=True, print_background=True)
    os.remove(foot_html)
    doc = fitz.open(raw)
    fdoc = fitz.open(foot_pdf)
    for i in range(1, doc.page_count):
        r = doc[i].rect
        doc[i].show_pdf_page(fitz.Rect(0, r.height - fdoc[0].rect.height, r.width, r.height), fdoc, 0)
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
    fdoc.close()
    os.remove(raw)
    os.remove(foot_pdf)
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
