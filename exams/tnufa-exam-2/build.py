# -*- coding: utf-8 -*-
"""One command for the whole exam (student booklet + web reader + teacher booklet + blueprint + QA).

    python exams/tnufa-exam-2/build.py                 # checks, STUDENT.pdf + public/index.html, TEACHER.pdf, BLUEPRINT.json
    python exams/tnufa-exam-2/build.py --student       # only the student outputs (public/)
    python exams/tnufa-exam-2/build.py --teacher       # only the teacher outputs (private/, not committed)
    python exams/tnufa-exam-2/build.py --preview 7     # one question on one A4 sheet → build/preview-q7.png
    python exams/tnufa-exam-2/build.py --check         # automatic QA only, no browser
    python exams/tnufa-exam-2/build.py --update-hashes # accept the current question texts as the regression baseline
    python exams/tnufa-exam-2/build.py --snapshots     # render every PDF page to qa/pages (student) and private/pages (teacher)

Edit one question: open src/exam2/questions/qNN.py (text, data, figure, answer, rubric live together), then run
build.py. The regression hashes report which questions changed.
"""
import os, sys, json, runpy
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))

from exam2 import questions, checks, blueprint  # noqa: E402


def main(argv):
    qs = questions.load()
    update = "--update-hashes" in argv
    errs, warns, act, changed = checks.run(qs, update_hashes=update)
    for w in warns:
        print("WARN:", w)
    if errs:
        print("CHECKS FAILED:")
        for e in errs:
            print("  -", e)
        return 1
    # Independent fixed-answer baseline and arithmetic; deliberately does not use q.check().
    ns = runpy.run_path(os.path.join(HERE, "tests", "independent_math_audit.py"))
    assert ns["verify"](qs) == 100
    print("independent math and scoring audit: OK — 41 parts, 100 points")
    print("checks: OK — %d questions, %d items, %d points; domains %s; thinking %s; literacy %d; solving minutes %d" % (
        act["questions"], act["items"], act["points"], act["domains"], act["thinking"], act["literacy"], act["minutes_solving"]))
    bp = blueprint.blueprint(qs)
    with open(os.path.join(HERE, "BLUEPRINT.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(bp, f, ensure_ascii=False, indent=2)
        f.write("\n")
    if "--check" in argv:
        return 0

    from exam2 import render
    only_student = "--student" in argv
    only_teacher = "--teacher" in argv
    with render.Browser() as bw:
        if "--preview" in argv:
            n = int(argv[argv.index("--preview") + 1])
            render.preview(bw, qs[n - 1])
            return 0
        if not only_teacher:
            render.render_student(bw, qs)
        if not only_student:
            render.render_teacher(bw, qs, blueprint.PLAN)
    if "--snapshots" in argv:
        if not only_teacher:
            ps = render.snapshots(render.STUDENT_PDF, os.path.join(HERE, "qa", "pages"), dpi=55)
            print("student page snapshots: %d → qa/pages" % len(ps))
        if not only_student:
            ps = render.snapshots(render.TEACHER_PDF, os.path.join(HERE, "private", "pages"), dpi=55, prefix="t")
            print("teacher page snapshots: %d → private/pages" % len(ps))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
