# -*- coding: utf-8 -*-
"""Automatic QA that needs no browser: structure, points, plan, placeholders, figures, key sanity, regression hashes."""
import re, json, os, hashlib
import xml.etree.ElementTree as ET
from .blueprint import PLAN, actual
from .model import THINKING

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HASHES = os.path.join(ROOT, "tests", "question-hashes.json")
PLACEHOLDERS = ("TODO", "lorem", "ipsum", "XXX", "דמו", "placeholder", "TBD", "???", "%%", "...", "…")


def q_hash(q):
    """Hash of everything that reaches a student or a teacher for this question."""
    h = hashlib.sha256()
    h.update(q.student_html.encode("utf-8"))
    for p in q.parts:
        for s in (p.answer, p.solution, p.alternatives, p.errors, p.carry, str(p.rubric), str(p.points), p.thinking, p.key, p.how):
            h.update(s.encode("utf-8"))
    return h.hexdigest()[:16]


def run(qs, update_hashes=False):
    errs, warns = [], []

    def fail(m):
        errs.append(m)

    # counts
    a = actual(qs)
    if a["questions"] != PLAN["questions"]:
        fail("questions %d != %d" % (a["questions"], PLAN["questions"]))
    if a["points"] != PLAN["points"]:
        fail("points %d != %d" % (a["points"], PLAN["points"]))
    for d, v in PLAN["domains"].items():
        if a["domains"].get(d, 0) != v:
            fail("domain %s: %d != plan %d" % (d, a["domains"].get(d, 0), v))
    for k, v in PLAN["thinking"].items():
        if a["thinking"].get(k, 0) != v:
            fail("thinking %s: %d != plan %d" % (k, a["thinking"].get(k, 0), v))
    if abs(a["literacy"] - PLAN["literacy"]) > 5:
        fail("literacy points %d too far from ~%d" % (a["literacy"], PLAN["literacy"]))
    if a["minutes_solving"] != PLAN["minutes_solving"]:
        fail("planned solving minutes %d != %d" % (a["minutes_solving"], PLAN["minutes_solving"]))
    if a["representation_transitions"] < PLAN["min_representation_transitions"]:
        fail("representation transitions %d < %d" % (a["representation_transitions"], PLAN["min_representation_transitions"]))
    if a["reasoning_questions"] < PLAN["min_reasoning_questions"]:
        fail("reasoning questions %d < %d" % (a["reasoning_questions"], PLAN["min_reasoning_questions"]))
    if a["critique_questions"] < PLAN["min_critique_questions"]:
        fail("critique questions < 1")
    if a["strategy_questions"] < PLAN["min_strategy_questions"]:
        fail("strategy questions < 1")

    # per question
    letters = "אבגדהו"
    for q in qs:
        if [p.letter for p in q.parts] not in ([""], list(letters[:len(q.parts)])):
            fail("q%d: part letters not sequential: %s" % (q.n, [p.letter for p in q.parts]))
        if q.points != sum(p.points for p in q.parts):
            fail("q%d: points mismatch" % q.n)
        try:
            q.check()
        except AssertionError as e:
            fail("q%d: key check failed: %s" % (q.n, e))
        texts = [q.stem, q.notes, q.reference, q.accessibility] + [p.html + p.answer + p.solution + p.alternatives + p.errors + p.carry + p.key + p.how + " ".join(c for _, c in p.rubric) for p in q.parts]
        for s in texts:
            for ph in PLACEHOLDERS:
                if ph in s:
                    fail("q%d: placeholder-like text %r" % (q.n, ph))
        for p in q.parts:
            if p.thinking not in THINKING:
                fail("q%d: bad thinking" % q.n)
            if not p.key.strip() or not p.how.strip():
                fail("q%d%s: answer-key row (KEY) is empty" % (q.n, p.letter))
            pts = [r[0] for r in p.rubric]
            if pts[-1] != 0 or len(pts) != len(set(pts)) or any(x < 0 or x > p.points for x in pts):
                fail("q%d%s: invalid or repeated rubric score levels" % (q.n, p.letter))
            if any(not isinstance(c, str) or not c.strip() for _, c in p.rubric):
                fail("q%d%s: rubric has empty criterion" % (q.n, p.letter))
            if pts != sorted(pts, reverse=True) or pts[0] != p.points:
                fail("q%d%s: rubric rows must descend from %d to 0" % (q.n, p.letter, p.points))
            if ("הציגו את דרך הפתרון" in p.html or "נמקו" in p.html) and '<div class="work"' not in p.html:
                fail("q%d%s: asks for work/reasoning but has no writing window" % (q.n, p.letter))
        # figures must be well-formed XML
        for mth in re.finditer(r'<svg.*?</svg>', q.student_html, re.S):
            s = mth.group(0)
            if 'class="rad"' in s or 'viewBox="0 0 13 24"' in s:
                continue
            try:
                ET.fromstring(s.replace("&nbsp;", " "))
            except ET.ParseError as e:
                fail("q%d: figure is not well-formed XML: %s" % (q.n, e))
        if q.reference.count("(") < 4:
            fail("q%d: originality note must list 4 structural differences" % q.n)
        if q.minutes <= 0:
            fail("q%d: minutes" % q.n)
    # numbering
    if [q.n for q in qs] != list(range(1, 18)):
        fail("numbering not 1..17")

    # regression hashes
    cur = {"q%02d" % q.n: q_hash(q) for q in qs}
    changed = []
    if os.path.exists(HASHES):
        old = json.load(open(HASHES, encoding="utf-8"))
        changed = [k for k in cur if old.get(k) != cur[k]]
        if changed and not update_hashes:
            warns.append("questions changed since the last snapshot: %s (run build.py --update-hashes to accept)" % ", ".join(changed))
    if update_hashes or not os.path.exists(HASHES):
        os.makedirs(os.path.dirname(HASHES), exist_ok=True)
        with open(HASHES, "w", encoding="utf-8", newline="\n") as f:
            json.dump(cur, f, indent=2)
            f.write("\n")
    return errs, warns, a, changed
