# -*- coding: utf-8 -*-
"""Publish the student outputs (public/) to the GitHub Pages repo yanivmizrachiy/tnufa-exam-2.

The site repo is a pure build artifact of this folder: it is wiped and re-filled from public/ on every run,
so the single source of truth stays here (src/exam2/questions/*.py → build.py → public/). The generated
student outputs (STUDENT.pdf, index.html, manifest.json) are not committed in Tnufa; this script rebuilds them
from the committed source and the site repo is the only place they are stored.

    python exams/tnufa-exam-2/tools/publish.py            # copy, commit on a branch, push, open a PR
    python exams/tnufa-exam-2/tools/publish.py --dry-run  # only show what would change

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
KEEP = {".git"}                      # everything else in the site repo is regenerated
SKIP = {".print.html", ".preview.html"}

README = """# מבחן תנופה לדוגמה — אתר הפרסום (נוצר אוטומטית)

**אין לערוך כאן.** ריפו זה הוא תוצר בנייה בלבד: תוכנו מוחלף כולו בכל הרצה של
`python exams/tnufa-exam-2/tools/publish.py` בריפו `yanivmizrachiy/Tnufa` (מקור האמת היחיד: `exams/tnufa-exam-2`).

מכיל רק את תוצרי התלמיד: `index.html` (קורא: שער, עמודי החוברת, הדפסה, הורדה), `STUDENT.pdf`, `manifest.json`, `assets/`.
אין פתרונות ואין מחוון. `SOURCE.json` מציין מאיזה commit במקור נבנה האתר.
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
    src_sha = run(["git", "rev-parse", "HEAD"], REPO).stdout.strip()
    dirty = run(["git", "status", "--porcelain", "--", "exams/tnufa-exam-2"], REPO).stdout.strip()
    if dirty and not dry:
        print("exams/tnufa-exam-2 has uncommitted changes — commit first, so the site is built from a real source commit.")
        return 1
    # the student outputs are not kept in git: always rebuild them from the committed source before publishing
    run([sys.executable, os.path.join(EXAM2, "build.py"), "--student"], REPO)

    refill(src_sha, dry)

    status = run(["git", "status", "--porcelain"], SITE).stdout.strip()
    if dry:
        print("dry run — site would be rebuilt from public/ (source commit %s)" % src_sha[:10])
        return 0
    if not status:
        print("site already up to date with public/")
        return 0
    branch = "publish-%s-%s" % (datetime.date.today().strftime("%Y%m%d"), src_sha[:7])
    run(["git", "checkout", "-q", "-B", branch], SITE)
    run(["git", "add", "-A"], SITE)
    run(["git", "commit", "-q", "-m", "Publish exam outputs from Tnufa@%s\n\nGenerated by exams/tnufa-exam-2/tools/publish.py" % src_sha[:10]], SITE)
    run(["git", "push", "-u", "origin", branch, "--force-with-lease"], SITE)
    r = run(["gh", "pr", "create", "--repo", SITE_REPO, "--base", "main", "--head", branch, "--fill"], SITE, check=False)
    if r.returncode != 0:
        print(r.stderr.strip())
    print("published branch %s → merge the PR to update https://yanivmizrachiy.github.io/tnufa-exam-2/" % branch)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
