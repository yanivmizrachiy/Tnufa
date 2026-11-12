# -*- coding: utf-8 -*-
"""Publish the student outputs (public/) to the GitHub Pages repo yanivmizrachiy/tnufa-exam-2.

The site repo is a pure build artifact of this folder: it is wiped and re-filled from public/ on every run,
so the single source of truth stays here (src/exam2/questions/*.py → build.py → public/).

    python exams/tnufa-exam-2/tools/publish.py             # copy, commit on a branch, push, open a PR
    python exams/tnufa-exam-2/tools/publish.py --push-main # verify + copy, commit and push site main directly (CI path)
    python exams/tnufa-exam-2/tools/publish.py --dry-run   # only show what would change

Every publish first runs a fail-closed version gate (verify_public): the reader manifest, the district
workbook manifest and STUDENT.pdf must describe one version and all referenced pages/assets must exist,
so a half-built or mismatched tree is never published and the last good version stays live.

Requires: a clone of the site repo next to the Tnufa checkout (../tnufa-exam-2), or SITE_DIR env var; gh logged in.
"""
import os, sys, json, shutil, subprocess, hashlib, datetime
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
EXAM2 = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(EXAM2, "..", ".."))
PUBLIC = os.path.join(EXAM2, "public")
SITE = os.environ.get("SITE_DIR") or os.path.abspath(os.path.join(REPO, "..", "tnufa-exam-2"))
SITE_REPO = "yanivmizrachiy/tnufa-exam-2"
KEEP = {".git", ".github"}           # preserve GitHub release workflow; regenerate the site content
SKIP = {".print.html", ".preview.html", ".answer-key-print.html"}

README = """# מבחן תנופה לדוגמה — אתר הפרסום (נוצר אוטומטית)

**אין לערוך כאן.** ריפו זה הוא תוצר בנייה בלבד: תוכנו מוחלף כולו בכל הרצה של
`python exams/tnufa-exam-2/tools/publish.py` בריפו `yanivmizrachiy/Tnufa` (מקור האמת היחיד: `exams/tnufa-exam-2`).

מכיל חוברת תלמיד `STUDENT.pdf` (ללא פתרונות), מחוון תשובות וניקוד בטבלה בתוך `index.html`,
קובץ `ANSWER_KEY.pdf`, וחוברת `EXAM_WITH_KEY.pdf` עם המחוון בסופה.
המחוון ציבורי לבקשת בעל המבחן. חוברת המורה המורחבת `private/TEACHER.pdf` אינה מתפרסמת.
`SOURCE.json` מציין את commit המקור.
"""


def run(cmd, cwd, check=True):
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, encoding="utf-8")
    if r.stdout.strip():
        print(r.stdout.strip())
    if check and r.returncode != 0:
        print(r.stderr.strip())
        sys.exit(r.returncode)
    return r


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def verify_public():
    """Fail-closed version gate: the reader manifest, the district workbook manifest and STUDENT.pdf
    must describe ONE version, and every page/asset they reference must exist. Returns (version, errors).
    Only student outputs may be published — a teacher PDF in public/ is an error."""
    rm = json.load(open(os.path.join(PUBLIC, "manifest.json"), encoding="utf-8"))
    wm = json.load(open(os.path.join(PUBLIC, "WORKBOOK_MANIFEST.json"), encoding="utf-8"))
    pdf_sha = "sha256-" + sha(os.path.join(PUBLIC, "STUDENT.pdf"))
    errors = []
    if not (rm["pdf"]["sha256"] == wm["pdf"]["sha256"] == pdf_sha):
        errors.append("PDF sha differs across version: reader=%s workbook=%s actual=%s"
                      % (rm["pdf"]["sha256"][:21], wm["pdf"]["sha256"][:21], pdf_sha[:21]))
    counts = {rm["pages"], wm["totalPages"], len(wm["pages"]), rm["pdf"]["pageCount"], wm["pdf"]["pageCount"]}
    if len(counts) != 1:
        errors.append("page count differs across version: %s" % sorted(counts))
    for page in wm["pages"]:
        if not os.path.exists(os.path.join(PUBLIC, page["file"])):
            errors.append("district page referenced by manifest is missing: %s" % page["file"])
    for href in (wm.get("assets", {}).get("css") or []):
        if not os.path.exists(os.path.join(PUBLIC, href)):
            errors.append("stylesheet referenced by manifest is missing: %s" % href)
    # The public key and combined download must originate in this verified build.
    for field, expected in (("answerKey", 1), ("examWithKey", rm["pdf"]["pageCount"] + 1)):
        meta = rm.get(field) or {}
        expected_file = {"answerKey": "ANSWER_KEY.pdf", "examWithKey": "EXAM_WITH_KEY.pdf"}[field]
        if meta.get("file") != expected_file:
            errors.append("%s missing or wrong filename" % field)
            continue
        full = os.path.join(PUBLIC, expected_file)
        if not os.path.isfile(full):
            errors.append("%s missing: %s" % (field, expected_file))
            continue
        if meta.get("sha256") != "sha256-" + sha(full):
            errors.append("%s hash mismatch" % field)
        if meta.get("pageCount") != expected:
            errors.append("%s pageCount differs" % field)
    index_path = os.path.join(PUBLIC, "index.html")
    if os.path.isfile(index_path):
        with open(index_path, encoding="utf-8") as f:
            index = f.read()
        if ('id="answer-key"' not in index or
                index.count('class="rubric-breakdown"') < 41):
            errors.append("public reader is missing the full 41-part scoring key")
    if os.path.exists(os.path.join(PUBLIC, "TEACHER.pdf")) or os.path.isdir(os.path.join(PUBLIC, "private")):
        errors.append("teacher material must never reach the published folder")
    return pdf_sha, errors


def refill(src_sha, dry=False):
    """Wipe the site clone (except .git) and copy public/ + README + SOURCE.json into it."""
    for name in os.listdir(SITE):
        if name in KEEP:
            continue
        p = os.path.join(SITE, name)
        if not dry:
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    for root, _dirs, files in os.walk(PUBLIC):
        rel = os.path.relpath(root, PUBLIC)
        for f in files:
            if f in SKIP:
                continue
            dst = os.path.join(SITE, rel, f) if rel != "." else os.path.join(SITE, f)
            if not dry:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(os.path.join(root, f), dst)
    if not dry:
        open(os.path.join(SITE, ".nojekyll"), "w").close()
        with open(os.path.join(SITE, "README.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(README)
        with open(os.path.join(SITE, "SOURCE.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"source": "yanivmizrachiy/Tnufa", "path": "exams/tnufa-exam-2", "commit": src_sha,
                       "student_pdf_sha256": sha(os.path.join(PUBLIC, "STUDENT.pdf")),
                       "published": datetime.date.today().isoformat()}, f, ensure_ascii=False, indent=2)
            f.write("\n")



def main(argv):
    dry = "--dry-run" in argv
    if not os.path.isdir(os.path.join(SITE, ".git")):
        print("site clone not found at %s — run: gh repo clone %s %s" % (SITE, SITE_REPO, SITE))
        return 1
    if not os.path.exists(os.path.join(PUBLIC, "STUDENT.pdf")):
        print("public/STUDENT.pdf missing — run build.py first")
        return 1
    # Fail-closed: never publish a half-built or mismatched version (keeps the last good one live).
    version, verr = verify_public()
    if verr:
        print("REFUSING to publish — version verification failed:")
        for e in verr:
            print("  -", e)
        return 1
    print("version verified: %s — manifest, district pages and PDF agree" % version[:21])
    src_sha = run(["git", "rev-parse", "HEAD"], REPO).stdout.strip()
    dirty = run(["git", "status", "--porcelain", "--", "exams/tnufa-exam-2"], REPO).stdout.strip()
    if dirty:
        print("WARNING: exams/tnufa-exam-2 has uncommitted changes; SOURCE.json will point at HEAD, not at these files.")

    refill(src_sha, dry)

    status = run(["git", "status", "--porcelain"], SITE).stdout.strip()
    if dry:
        print("dry run — site would be rebuilt from public/ (source commit %s)" % src_sha[:10])
        return 0
    if not status:
        print("site already up to date with public/")
        return 0
    msg = "Publish exam outputs from Tnufa@%s\n\nversion %s\nGenerated by exams/tnufa-exam-2/tools/publish.py" % (src_sha[:10], version[:21])
    # The site repo is a build artifact served straight from main (Pages, deploy-from-branch), so the
    # automated path commits to main directly — no review PR to merge, which is what makes the update
    # automatic. --push-main is used by CI and by local publishes once the build is verified above.
    if "--push-main" in argv:
        run(["git", "checkout", "-q", "main"], SITE, check=False)
        run(["git", "add", "-A"], SITE)
        run(["git", "commit", "-q", "-m", msg], SITE)
        run(["git", "push", "-q", "origin", "HEAD:main"], SITE)
        print("published to %s main (source %s) → GitHub Pages will serve https://yanivmizrachiy.github.io/tnufa-exam-2/" % (SITE_REPO, src_sha[:10]))
        return 0
    branch = "publish-%s-%s" % (datetime.date.today().strftime("%Y%m%d"), src_sha[:7])
    run(["git", "checkout", "-q", "-B", branch], SITE)
    run(["git", "add", "-A"], SITE)
    run(["git", "commit", "-q", "-m", msg], SITE)
    run(["git", "push", "-u", "origin", branch, "--force-with-lease"], SITE)
    r = run(["gh", "pr", "create", "--repo", SITE_REPO, "--base", "main", "--head", branch, "--fill"], SITE, check=False)
    if r.returncode != 0:
        print(r.stderr.strip())
    print("published branch %s → merge the PR to update https://yanivmizrachiy.github.io/tnufa-exam-2/" % branch)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
