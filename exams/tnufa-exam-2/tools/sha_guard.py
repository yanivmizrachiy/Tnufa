# -*- coding: utf-8 -*-
"""Proof that the existing exam was not touched: records / compares SHA-256 of the original assets.

    python exams/tnufa-exam-2/tools/sha_guard.py record   # writes qa/original-assets.sha256 (once, before work)
    python exams/tnufa-exam-2/tools/sha_guard.py check    # compares the live files with the record; non-zero on drift
"""
import os, sys, hashlib, glob
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
EXAM2 = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(EXAM2, "..", ".."))
RECORD = os.path.join(EXAM2, "qa", "original-assets.sha256")

FILES = ["exam.pdf", "exam.json", "SOURCE_OF_TRUTH.md", "tools/build_exam.py", "tools/verify_manifest.py", "index.html",
         "cover.html", "app.js", "viewer.js", "viewer.css", "site.css", "WORKBOOK_MANIFEST.json", "sw.js",
         "manifest.webmanifest", "checklist.html", "README.md", ".vercelignore", "api/logo.js",
         "assets/logo.svg", "assets/cover.jpg", "assets/jerusalem.jpg"]
FILES += sorted(os.path.relpath(p, REPO).replace("\\", "/") for p in glob.glob(os.path.join(REPO, "page-*.html")))
FILES += sorted(os.path.relpath(p, REPO).replace("\\", "/") for p in glob.glob(os.path.join(REPO, "figures", "*")))
FILES += sorted(os.path.relpath(p, REPO).replace("\\", "/") for p in glob.glob(os.path.join(REPO, "assets", "icons", "*")))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def current():
    return {f: sha(os.path.join(REPO, f)) for f in FILES if os.path.exists(os.path.join(REPO, f))}


def main(cmd):
    cur = current()
    if cmd == "record":
        os.makedirs(os.path.dirname(RECORD), exist_ok=True)
        with open(RECORD, "w", encoding="utf-8", newline="\n") as f:
            for k, v in cur.items():
                f.write("%s  %s\n" % (v, k))
        print("recorded %d files → %s" % (len(cur), os.path.relpath(RECORD, REPO)))
        return 0
    old = {}
    for line in open(RECORD, encoding="utf-8"):
        v, k = line.strip().split("  ", 1)
        old[k] = v
    drift = [k for k in old if cur.get(k) != old[k]]
    missing = [k for k in old if k not in cur]
    if drift or missing:
        print("SHA GUARD FAIL — changed: %s; missing: %s" % (drift, missing))
        return 1
    print("sha-guard: OK — %d original files unchanged" % len(old))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "check"))
