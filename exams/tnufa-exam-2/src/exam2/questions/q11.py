# -*- coding: utf-8 -*-
"""Q11 — geometry: angles in a triangle with a bisector, and a parallel through a vertex."""
import math
from ..model import Question, Part
from .. import html as H
from .. import svg as S

ANG_A, ANG_ABD = 50, 35


def check():
    B = 2 * ANG_ABD
    C = 180 - ANG_A - B
    assert B == 70 and C == 60


def figure():
    # real geometry: B at origin, C on the right, A found from the angles at B (70°) and C (60°)
    Bp = (110, 300)
    Cp = (300, 300)
    angB, angC = math.radians(2 * ANG_ABD), math.radians(180 - ANG_A - 2 * ANG_ABD)
    BC = Cp[0] - Bp[0]
    # law of sines: AB / sin C = BC / sin A
    AB = BC * math.sin(angC) / math.sin(math.radians(ANG_A))
    Ap = (Bp[0] + AB * math.cos(angB), Bp[1] - AB * math.sin(angB))
    # D on AC where BD bisects angle B: direction at 35° from BC
    half = math.radians(ANG_ABD)
    # intersect ray from B at angle 'half' with segment AC
    dx, dy = math.cos(half), -math.sin(half)
    ax, ay = Ap
    cx, cy = Cp
    # solve B + s*(dx,dy) = A + u*(C-A)
    ex, ey = cx - ax, cy - ay
    det = dx * (-ey) - dy * (-ex)
    s = ((ax - Bp[0]) * (-ey) - (ay - Bp[1]) * (-ex)) / det
    Dp = (Bp[0] + s * dx, Bp[1] + s * dy)
    # E: through C, parallel to AB, on the side below BC (alternate angle to angle ABC)
    ux, uy = (Bp[0] - Ap[0]), (Bp[1] - Ap[1])
    L = math.hypot(ux, uy)
    Ep = (Cp[0] + ux / L * 95, Cp[1] + uy / L * 95)
    b = S.poly([Ap, Bp, Cp], S.PALE, S.NAVY, 2.2)
    b += S.line(Bp[0], Bp[1], Dp[0], Dp[1], S.G3, 2)
    b += S.line(Cp[0], Cp[1], Ep[0], Ep[1], S.BLUE, 2, 'stroke-dasharray="7 5"')
    b += S.angle_mark(Ap, Bp, Cp, 24, label="50°", lr=40)
    b += S.angle_mark(Bp, Ap, Dp, 30, c=S.G3, label="35°", lc=S.G3, lr=54) + S.angle_mark(Bp, Ap, Dp, 36, c=S.G3)
    b += S.angle_mark(Bp, Dp, Cp, 42, c=S.G3) + S.angle_mark(Bp, Dp, Cp, 48, c=S.G3)
    b += S.par_mark(Ap, Bp, 1, 7, S.BLUE) + S.par_mark(Cp, Ep, 1, 7, S.BLUE)
    b += S.dot(Ap) + S.dot(Bp) + S.dot(Cp) + S.dot(Dp) + S.dot(Ep)
    b += S.label(Ap, "A", 0, -12) + S.label(Bp, "B", -16, 8) + S.label(Cp, "C", 16, 4) + S.label(Dp, "D", 14, -4) + S.label(Ep, "E", 14, 10)
    return S.svg(440, 410, b, "משולש ABC, חוצה הזווית BD, וישר דרך C המקביל ל-AB", maxw=330)


KEY = {   # answer key (מחוון תשובות): part → (answer, how)
    "א": (H.m("∢ACB = 60°"), "%s (BD חוצה זווית), ולפי סכום הזוויות במשולש %s." % (H.m("∢ABC = 2 · 35° = 70°"), H.m("180° − 50° − 70° = 60°"))),
    "ב": (H.m("∢BCE = 70°"), "%s, ולכן %s (זוויות מתחלפות)." % (H.m("CE ∥ AB"), H.m("∢BCE = ∢ABC = 70°"))),
}


def build():
    a = Part(
        "א", 3, "process",
        "מהו הגודל של הזווית %s? הציגו את דרך הפתרון." % H.m("ACB") + H.work(84) +
        H.ans('תשובה: &nbsp;<bdi dir="ltr" class="math">∢ACB = %s°</bdi>' % H.BLANK),
        H.m("∢ACB = 60°"),
        "%s חוצה את הזווית %s, ולכן %s. סכום הזוויות במשולש: %s." % (
            H.m("BD"), H.m("ABC"), H.m("∢ABC = 2·35° = 70°"), H.m("∢ACB = 180° − 50° − 70° = 60°")),
        [(3, "60° עם נימוק: חוצה זווית → 70°, סכום זוויות → 60°."),
         (2, "70° נכון ואז טעות חישוב, או 60° עם נימוק חלקי (ללא אזכור חוצה הזווית)."),
         (1, "זיהוי %s בלבד, או 60° ללא דרך." % H.m("∢ABC = 70°")),
         (0, "כל אפשרות אחרת.")],
        errors="95° (180 − 50 − 35) — התעלמות מכך ש־BD חוצה זווית; 130° — שימוש ב־50° כזווית חיצונית.",
        reasoning_credit=True,
    )
    b = Part(
        "ב", 3, "process",
        "דרך הקודקוד %s עובר הקטע %s, המקביל לצלע %s (ראו סרטוט). מהו הגודל של הזווית %s? נמקו את תשובתכם." % (
            H.m("C"), H.m("CE"), H.m("AB"), H.m("BCE")) + H.work(84) +
        H.ans('תשובה: &nbsp;<bdi dir="ltr" class="math">∢BCE = %s°</bdi>' % H.BLANK),
        H.m("∢BCE = 70°"),
        "%s, והישר %s חותך את שני המקבילים. הזוויות %s ו־%s הן זוויות מתחלפות, ולכן %s." % (
            H.m("AB ∥ CE"), H.m("BC"), H.m("ABC"), H.m("BCE"), H.m("∢BCE = ∢ABC = 70°")),
        [(3, "70° עם נימוק של זוויות מתחלפות בין מקבילים (או נימוק תקף אחר)."),
         (2, "70° עם נימוק חלקי (&quot;כי מקבילים&quot; בלי לציין איזה זוג זוויות)."),
         (1, "70° ללא נימוק."),
         (0, "כל אפשרות אחרת.")],
        alternatives="דרך זוויות חד־צדדיות: %s, ולכן %s." % (H.m("∢ACE = 180° − 50° = 130°"), H.m("∢BCE = 130° − 60° = 70°")),
        carry="אם בסעיף א נמצא ערך שגוי ל־∢ABC והוא הועתק כאן עם נימוק נכון של זוויות מתחלפות — ניקוד מלא לסעיף ב.",
        errors="110° — זוויות חד־צדדיות במקום מתחלפות; 60° — בלבול עם הזווית ACB.",
        reasoning_credit=True,
    )
    return Question(
        n=11, domain="geometry", topic="זוויות במשולש ובין מקבילים", skill="חוצה זווית; סכום זוויות; זוויות מתחלפות",
        claim="התלמיד משתמש בהגדרת חוצה זווית ובסכום זוויות, ומזהה זוויות מתחלפות בין מקבילים.",
        evidence="60° ו־70° עם נימוקים המציינים את המשפט/ההגדרה.",
        task="חישוב מנומק בשני שלבים; זיהוי זוג זוויות מתאים בתצורת מקבילים.",
        difficulty="mid", representations=["סרטוט → חישוב מנומק"], literacy=False, minutes=5,
        stem="<p>במשולש %s נתון: %s. הקטע %s הוא חוצה הזווית %s, ו־%s.</p>%s" % (
            H.m("ABC"), H.m("∢BAC = 50°"), H.m("BD"), H.m("ABC"), H.m("∢ABD = 35°"), figure()),
        parts=[a, b],
        reference="הקרוב ביותר: שאלה 7 במבחן הרשמי (משולש שווה־שוקיים KLM עם מקביל, 16°) ושאלה 5 במבחן התרגול הקודם (נקודה בין שני מקבילים). הבדלים: (1) משולש כללי עם חוצה זווית, לא שווה־שוקיים ולא גובה; (2) המקביל יוצא מקודקוד ונדרשת זווית מתחלפת, לא הסבר שוויון α ו־β; (3) סעיף ב נשען על ∢ABC מסעיף א; (4) אין נקודה בין מקבילים ואין זווית ישרה.",
        accessibility="הסרטוט מדויק גאומטרית ומסומנות בו הזוויות הנתונות בלבד; המקביל מסומן בקו מקווקו וחיצי הקבלה.",
        notes="בסעיף ב רצוי להרגיל לציין &quot;זוויות מתחלפות בין מקבילים&quot; כנימוק מלא, כנדרש במחוון הרשמי.",
        check=check,
    )
