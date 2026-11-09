# -*- coding: utf-8 -*-
"""Fail-closed gate for WORKBOOK_MANIFEST.json: proves the native web-reader pages
(page-N.html) and the committed exam.pdf are in lockstep — the single-source rule for the
jerusalem2 district reader. Any drift (edited page without re-emit, stale PDF, wrong range)
exits non-zero.

Run:  python tools/verify_manifest.py
"""
import os, sys, json, hashlib
import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errs = []


def fail(m):
    errs.append(m)


m = json.load(open(os.path.join(ROOT, "WORKBOOK_MANIFEST.json"), encoding="utf-8"))

if m.get("schemaVersion") != 3:
    fail("schemaVersion != 3")
if m.get("pageSelector") != ".a4-page":
    fail("pageSelector != .a4-page")
if m.get("cover") is not None:
    fail("cover must be null (reader shows the 19 exam pages, no cover sheet)")
if (m.get("assets") or {}).get("mathjax") is not None:
    fail("assets.mathjax must be null (tnufa draws its own SVG figures)")

pages = m.get("pages", [])
n = len(pages)
if m.get("totalPages") != n:
    fail("totalPages %s != pages.length %d" % (m.get("totalPages"), n))

# page files: present, contiguous numbering, native A4 root, resolved assets, lockstep hash
h = hashlib.sha256()
for i, p in enumerate(pages):
    if p.get("workbookNumber") != i + 1:
        fail("page %d: workbookNumber %s != %d" % (i, p.get("workbookNumber"), i + 1))
    fp = os.path.join(ROOT, p["file"])
    if not os.path.exists(fp):
        fail("missing page file: %s" % p["file"])
        continue
    b = open(fp, "rb").read()
    h.update(b)
    t = b.decode("utf-8", "replace")
    if '<section class="a4-page' not in t:
        fail("%s: no .a4-page root" % p["file"])
    if "../assets/" in t:
        fail("%s: unresolved ../assets/ reference" % p["file"])
if m.get("contentHash") != "sha256-" + h.hexdigest():
    fail("contentHash mismatch — pages changed without re-running the emitter")

# chapters cover 1..n contiguously
nxt = 1
for c in m.get("chapters", []):
    if c["startPage"] != nxt:
        fail("chapter %s starts at %d, expected %d" % (c["id"], c["startPage"], nxt))
    if c["endPage"] < c["startPage"]:
        fail("chapter %s end < start" % c["id"])
    nxt = c["endPage"] + 1
if nxt != n + 1:
    fail("chapters end at %d, expected %d" % (nxt - 1, n))

# HTML <-> PDF tie: the committed exam.pdf is the 19 content pages + 1 answer-key page
pdf = m.get("pdf", {})
pf = os.path.join(ROOT, pdf.get("file", "exam.pdf"))
if not os.path.exists(pf):
    fail("pdf missing: %s" % pdf.get("file"))
else:
    d = fitz.open(pf)
    pc = d.page_count
    d.close()
    if pdf.get("pageCount") != pc:
        fail("pdf.pageCount %s != actual %d" % (pdf.get("pageCount"), pc))
    if pc != n + 1:
        fail("exam.pdf must be %d pages (%d content + 1 answer key), got %d" % (n + 1, n, pc))
    ph = hashlib.sha256()
    with open(pf, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            ph.update(chunk)
    if pdf.get("sha256") != "sha256-" + ph.hexdigest():
        fail("pdf.sha256 mismatch — exam.pdf is not the version these pages were emitted from")
if pdf.get("coverPages") != 0:
    fail("pdf.coverPages must be 0")
if pdf.get("studentRange") != [1, n]:
    fail("pdf.studentRange must be [1,%d] (students get the exam without the key)" % n)

if errs:
    print("verify-manifest FAIL:")
    for e in errs:
        print("  - " + e)
    sys.exit(1)
print("verify-manifest: OK — %d reader pages, %d chapters, exam.pdf %d pages, content/PDF hashes in lockstep." % (n, len(m["chapters"]), n + 1))
