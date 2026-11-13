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
ANSWER_KEY_PDF = os.path.join(PUBLIC, "ANSWER_KEY.pdf")
WITH_KEY_PDF = os.path.join(PUBLIC, "EXAM_WITH_KEY.pdf")
A4_KEY_PDF = os.path.join(PUBLIC, "ANSWER_KEY_A4.pdf")
WITH_A4_KEY_PDF = os.path.join(PUBLIC, "EXAM_WITH_KEY_A4.pdf")
TEACHER_PDF = os.path.join(PRIVATE, "TEACHER.pdf")


def _uri(p):
    return "file:///" + p.replace("\\", "/")


def _write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def _pdf_page_count(path):
    with fitz.open(path) as doc:
        return doc.page_count


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
        # Force every declared @font-face to download, then wait for the set to settle. Relying on
        # document.fonts.ready alone is flaky: it can resolve before swap-loaded faces are requested,
        # so the check below would fail. Loading each face (plus the two asserted specs) explicitly
        # makes the render deterministic and guarantees the cover's display fonts are ready for the PDF.
        self.pg.evaluate(
            "() => Promise.all(["
            "  document.fonts.load('15px Heebo'), document.fonts.load('700 22px Rubik'),"
            "  ...[...document.fonts].map(f => f.load())"
            "].map(p => Promise.resolve(p).catch(() => null))).then(() => document.fonts.ready)"
        )
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
        # The published student booklet is students-only: the answer key / מחוון lives ONLY in the
        # teacher booklet (private/, never published). The public folder must not carry solutions.
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
    log("wrote public/STUDENT.pdf: %d pages (students-only, no key), %d KB" % (len(pages), os.path.getsize(STUDENT_PDF) // 1024))
    key_markup = render_public_key(bw, qs, log=log)
    render_printable_key(bw, key_markup, log=log)
    emit_reader(qs, sheets, rendered, key_markup)
    verify_mobile_key_layout(bw)
    return sheets, rendered


def verify_mobile_key_layout(bw):
    """Guard the owner's original five-column rubric format at phone widths.

    This runs in the existing Chromium build, without requiring any second source
    of answer data or touching student PDF/page generation.
    """
    page = bw.br.new_page(viewport={"width": 390, "height": 844})
    try:
        for width in (390, 700):
            page.set_viewport_size({"width": width, "height": 844})
            page.goto(_uri(os.path.join(PUBLIC, "index.html")), wait_until="networkidle")
            state = page.evaluate("""() => {
                const panel = document.querySelector('#answer-key');
                const table = panel.querySelector('table.key');
                const head = table.querySelector('thead');
                const row = table.querySelector('tbody tr');
                const cell = row.querySelector('td');
                return {
                    headings: [...head.querySelectorAll('th')].map(el => el.textContent.trim()),
                    rows: table.querySelectorAll('tbody tr').length,
                    headDisplay: getComputedStyle(head).display,
                    rowDisplay: getComputedStyle(row).display,
                    cellDisplay: getComputedStyle(cell).display,
                    panelOverflowX: getComputedStyle(panel).overflowX,
                    panelCanScroll: panel.scrollWidth > panel.clientWidth,
                    documentOverflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
                };
            }""")
            assert state["headings"] == ["שאלה", "נושא", "סעיף", "תשובה", "דרך הפתרון"], state
            assert state["rows"] == 41, state
            assert state["headDisplay"] == "table-header-group", state
            assert state["rowDisplay"] == "table-row" and state["cellDisplay"] == "table-cell", state
            assert state["panelOverflowX"] == "auto" and state["panelCanScroll"], state
            assert not state["documentOverflow"], state
        print("mobile five-column answer-key layout: OK (390px and 700px)")
    finally:
        page.close()


def render_public_key(bw, qs, log=print):
    """Render the checked scoring table once; append it to a separate teacher-download PDF.

    Keep STUDENT.pdf and the district's 17 A4 question pages unchanged.
    EXAM_WITH_KEY.pdf follows the previous exam's one-long-key-page convention.
    """
    key_html = B.key_sheet(qs)
    part_count = sum(len(q.parts) for q in qs)
    assert key_html.count('class="rubric-breakdown"') == part_count
    assert key_html.count('class="khow"') == part_count
    assert all(p.rubric[0][0] == p.points and p.rubric[-1][0] == 0
               for q in qs for p in q.parts)
    tmp = os.path.join(PUBLIC, ".answer-key-print.html")
    styles = ('html,body{margin:0;background:#fff;width:210mm}'
              '.key-print{width:210mm;box-sizing:border-box;padding:34px 46px 40px}'
              '.key-print .key{font-size:11.4px;line-height:1.34}'
              '.key-print .key .rubric-breakdown{font-size:10.6px}'
              '.key-print .key td{vertical-align:top}'
              '.key-print .key tbody{break-inside:avoid}')
    try:
        _write(tmp, B.head("מחוון תשובות — " + B.TITLE, styles) +
               '<section class="key-print">' + key_html + '</section></body></html>')
        bw.open(tmp)
        height = math.ceil(bw.pg.evaluate(
            "document.querySelector('.key-print').getBoundingClientRect().height")) + 32
        assert 1100 < height < 14000, "unexpected key sheet height: %s" % height
        bw.pg.add_style_tag(content="@page{size:210mm %dpx;margin:0}" % height)
        bw.pg.pdf(path=ANSWER_KEY_PDF, prefer_css_page_size=True, print_background=True,
                  margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        assert not bw.errs, bw.errs
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    key_doc = fitz.open(ANSWER_KEY_PDF)
    try:
        assert key_doc.page_count == 1, "key must be one long PDF page"
        assert len(key_doc[0].get_text()) > 1000, "key PDF rendered without enough text"
        with fitz.open(STUDENT_PDF) as combined:
            n = combined.page_count
            combined.insert_pdf(key_doc)
            assert combined.page_count == n + 1
            combined.set_toc(combined.get_toc() + [[1, "מחוון תשובות", n + 1]])
            combined.save(WITH_KEY_PDF, garbage=4, deflate=True)
        with fitz.open(WITH_KEY_PDF) as check:
            assert check.page_count == n + 1
            assert len(check[n].get_text()) > 1000
    finally:
        key_doc.close()
    log("checked public scoring key: %d parts; ANSWER_KEY.pdf and EXAM_WITH_KEY.pdf" % part_count)
    return key_html


def render_printable_key(bw, key_html, log=print):
    """Additional A4 print edition from the exact same five-column scoring key.

    Preserve the previous long-page ANSWER_KEY.pdf and EXAM_WITH_KEY.pdf links.
    This independent print alternative never changes STUDENT.pdf or district pages.
    """
    import re

    temp_html = os.path.join(PUBLIC, ".answer-key-a4-print.html")
    print_css = (
        '@page{size:A4;margin:12mm 10mm}'
        'html,body{margin:0;padding:0;width:auto;background:#fff}'
        '.a4-print{width:auto;box-sizing:border-box}'
        '.a4-print .key{font-size:12.4px;line-height:1.35}'
        '.a4-print .key .rubric-breakdown{font-size:11.7px}'
        '.a4-print .key th,.a4-print .key td{padding:4px 6px;vertical-align:top}'
        '.a4-print .key thead{display:table-header-group}'
        '.a4-print .key tbody{break-inside:avoid;page-break-inside:avoid}'
        '.a4-print .key tr{break-inside:avoid;page-break-inside:avoid}'
    )
    try:
        _write(temp_html, B.head("מחוון להדפסה A4 — " + B.TITLE, print_css) +
               '<section class="a4-print">' + key_html + '</section></body></html>')
        bw.open(temp_html)
        bw.pg.pdf(path=A4_KEY_PDF, prefer_css_page_size=True, print_background=True,
                  margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        assert not bw.errs, bw.errs
    finally:
        if os.path.exists(temp_html):
            os.remove(temp_html)

    with fitz.open(A4_KEY_PDF) as key_doc:
        count = key_doc.page_count
        assert 2 <= count <= 15, "unexpected printable key page count: %s" % count
        assert all(abs(pg.rect.width - 595.28) < 1 and abs(pg.rect.height - 841.89) < 1
                   for pg in key_doc), "print key has non-A4 pages"
        key_text = "".join(pg.get_text() for pg in key_doc)
        assert len(re.findall(r'(?:כללי\s+ניקוד|ניקוד\s+כללי)', key_text)) == 41, (
            "printable key is missing one of the 41 score rubrics")
        with fitz.open(STUDENT_PDF) as combined:
            student_count = combined.page_count
            combined.insert_pdf(key_doc)
            assert combined.page_count == student_count + count
            combined.set_toc(combined.get_toc() +
                             [[1, "מחוון להדפסה (A4)", student_count + 1]])
            combined.save(WITH_A4_KEY_PDF, garbage=4, deflate=True)
        with fitz.open(WITH_A4_KEY_PDF) as check:
            assert check.page_count == student_count + count
            assert all(check[student_count + i].get_text() == key_doc[i].get_text()
                       for i in range(count)), "printable combined PDF key differs"
    log("checked printable A4 scoring key: %d pages; combined PDF: %d pages" %
        (count, student_count + count))


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
.answer-panel{direction:rtl;background:#fff;max-width:1100px;margin:24px auto;padding:30px 36px;box-sizing:border-box;border:1px solid #cdd8d4;border-radius:10px}
.answer-panel .key{width:100%;font-size:12px;line-height:1.42}
.answer-panel .key td{vertical-align:top}
.answer-panel .key .rubric-breakdown{font-size:11.7px}
.print-links{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 20px}
.print-links a{display:inline-block;border:1px solid #c9dcd1;background:#f3f8f5;border-radius:6px;
  color:#18553a;text-decoration:none;padding:7px 12px;font:600 13px Heebo,Arial,sans-serif}
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


def emit_reader(qs, sheets, rendered, key_markup):
    """public/index.html: the cover and every A4 sheet, inline, from the same render as the PDF."""
    body = ('<header class="topbar"><div class="in"><a class="brand" href="#p1"><img src="assets/logo.svg" alt=""><span><strong>%s</strong><small>%s</small></span></a>'
            '<div class="acts"><a class="btn" href="STUDENT.pdf" download="מבחן-תנופה-לדוגמה.pdf">הורדת מבחן</a><a class="btn" href="#answer-key">מחוון וניקוד</a><a class="btn" href="EXAM_WITH_KEY.pdf" download="מבחן-תנופה-כולל-מחוון.pdf">מבחן + מחוון</a></div></div></header>'
            '<main><div id="wrap" class="wrap">' % (B.TITLE, B.SUBTITLE))
    for i, html in enumerate(rendered):
        page = html.replace('<section class="page', '<section id="p%d" class="page' % (i + 1), 1)
        body += page + ('<div class="sep"></div>' if i < len(rendered) - 1 else "")
    body += ('</div><section id="answer-key" class="answer-panel" aria-label="מחוון תשובות וניקוד">'
             '<nav class="print-links" aria-label="קובצי מחוון להדפסה">'
             '<a href="ANSWER_KEY_A4.pdf" download>מחוון להדפסה ב־A4</a>'
             '<a href="EXAM_WITH_KEY_A4.pdf" download>מבחן ומחוון להדפסה ב־A4</a>'
             '</nav>' + key_markup + '</section></main><script>' + READER_JS + '</script>')
    doc = B.head(B.TITLE + " — " + B.SUBTITLE, READER_CSS) + body + "</body></html>"
    doc = doc.replace("<head>", '<head><meta name="description" content="מבחן תנופה לדוגמה (נובמבר 2026) — הכנה לכיתה ט׳ במתמטיקה: צפייה בחוברת, הדפסה והורדת PDF.">', 1)
    _write(os.path.join(PUBLIC, "index.html"), doc)
    manifest = {
        "id": "tnufa-exam-2", "name": B.TITLE + " — " + B.SUBTITLE, "pages": len(rendered),
        "sheets": [[qs[i].n for i in s] for s in sheets], "pdf": {"file": "STUDENT.pdf", "sha256": "sha256-" + _sha(STUDENT_PDF), "pageCount": len(rendered)},
        "answerKey": {"file": "ANSWER_KEY.pdf", "sha256": "sha256-" + _sha(ANSWER_KEY_PDF), "pageCount": 1},
        "examWithKey": {"file": "EXAM_WITH_KEY.pdf", "sha256": "sha256-" + _sha(WITH_KEY_PDF), "pageCount": len(rendered) + 1},
        "answerKeyA4": {"file": "ANSWER_KEY_A4.pdf", "sha256": "sha256-" + _sha(A4_KEY_PDF),
                        "pageCount": _pdf_page_count(A4_KEY_PDF)},
        "examWithKeyA4": {"file": "EXAM_WITH_KEY_A4.pdf", "sha256": "sha256-" + _sha(WITH_A4_KEY_PDF),
                          "pageCount": _pdf_page_count(WITH_A4_KEY_PDF)},
        "builtAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _write(os.path.join(PUBLIC, "manifest.json"), json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("wrote public/index.html + manifest.json (%d pages)" % len(rendered))
    emit_district_reader(rendered, manifest)


def emit_district_reader(rendered, manifest):
    """Expose the same student sheets through the district's native workbook format: one A4 HTML page
    per sheet (district/page-N.html), a shared stylesheet, and WORKBOOK_MANIFEST.json — all from the
    SAME render as STUDENT.pdf, so a source edit updates the district reader with no second edit."""
    css = B.CSS.replace(":root{", ":host,:root{", 1).replace("body{color:", "body,.a4-page{color:", 1)
    pages = []
    digest = hashlib.sha256()
    for number, sheet in enumerate(rendered, start=1):
        assert sheet.startswith('<section class="page'), "unexpected student sheet root"
        sheet = sheet.replace('<section class="page', '<section dir="rtl" class="page a4-page', 1)
        html = (
            '<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
            '<base href="../"><link rel="stylesheet" href="district/pages.css">'
            '<link rel="stylesheet" href="%s"></head><body>%s</body></html>\n'
            % (B.FONTS, sheet)
        )
        digest.update(html.encode("utf-8"))
        filename = "district/page-%d.html" % number
        pages.append({"file": filename, "workbookNumber": number})
        _write(os.path.join(PUBLIC, filename), html)
    _write(os.path.join(PUBLIC, "district/pages.css"), css)
    workbook = {
        "schemaVersion": 3,
        "id": manifest["id"],
        "name": manifest["name"],
        "pageSelector": ".a4-page",
        "totalPages": len(pages),
        "cover": None,
        "pages": pages,
        "assets": {"css": ["district/pages.css"], "fontsCss": B.FONTS},
        "contentHash": "sha256-" + digest.hexdigest(),
        "pdf": {**manifest["pdf"], "coverPages": 0},
    }
    _write(os.path.join(PUBLIC, "WORKBOOK_MANIFEST.json"), json.dumps(workbook, ensure_ascii=False, indent=2) + "\n")
    print("wrote public/district/ (%d pages) + WORKBOOK_MANIFEST.json" % len(pages))


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
