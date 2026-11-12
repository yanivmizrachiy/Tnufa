# -*- coding: utf-8 -*-
"""Q14 — geometry: similar triangles in a bow-tie configuration (AB ∥ DE, AE and BD cross at C)."""
from fractions import Fraction as F
from ..model import Question, Part
from .. import html as H
from .. import svg as S

AC, CE, BC = 6, 9, 4


def check():
    assert F(BC) * CE / AC == 6


def figure():
    # C in the middle; A and E on one line through C, B and D on the other. CE:CA = CD:CB = 9:6 = 1.5,
    # so the drawing is to scale and AB is parallel to DE by construction.
    import math
    Cp = (250.0, 165.0)
    k = F(CE, AC)                                           # 3/2
    ang_a, ang_b = math.radians(212), math.radians(320)     # directions C→A (up-left) and C→B (up-right)
    rA, rB = 150.0, 150.0 * BC / AC                         # CB : CA = 4 : 6
    Ap = (Cp[0] + rA * math.cos(ang_a), Cp[1] + rA * math.sin(ang_a))
    Bp = (Cp[0] + rB * math.cos(ang_b), Cp[1] + rB * math.sin(ang_b))
    Ep = (Cp[0] - float(k) * rA * math.cos(ang_a), Cp[1] - float(k) * rA * math.sin(ang_a))
    Dp = (Cp[0] - float(k) * rB * math.cos(ang_b), Cp[1] - float(k) * rB * math.sin(ang_b))

    def pill(p, q, away, text, c=S.INK, bold=600, size=15):
        """Length label in a small white pill, set off the segment p-q on the side away from 'away'."""
        mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        if (away[0] - mx) * nx + (away[1] - my) * ny > 0:
            nx, ny = -nx, -ny
        x, y = mx + nx * 17, my + ny * 17
        w = 14 + 9 * len(text)
        return (S.rect(x - w / 2, y - 12, w, 24, "#fff", c, 1.2, rx=12) +
                S.t(x, y + 5.5, text, size, ltr=True, w=bold, c=c))

    b = S.poly([Ap, Bp, Cp], S.PALE, S.G3, 2.4)
    b += S.poly([Ep, Dp, Cp], "#e3eef8", S.BLUE, 2.4)
    b += S.par_mark(Ap, Bp, 1, 8, S.G3, 2) + S.par_mark(Dp, Ep, 1, 8, S.BLUE, 2)
    b += pill(Ap, Cp, Bp, "6") + pill(Bp, Cp, Ap, "4") + pill(Cp, Ep, Dp, "9") + pill(Cp, Dp, Ep, "?", c=S.AMBER, bold=800, size=16)
    for p in (Ap, Bp, Cp, Dp, Ep):
        b += S.circ(p[0], p[1], 4.2, "#fff", S.NAVY, 2)
    b += (S.label(Ap, "A", -16, -8, 18) + S.label(Bp, "B", 16, -8, 18) + S.label(Cp, "C", 0, -16, 18) +
          S.label(Dp, "D", -16, 20, 18) + S.label(Ep, "E", 16, 20, 18))
    return S.svg(560, 320, b, "שני משולשים ABC ו-EDC עם קודקוד משותף C; AB מקביל ל-DE; AC = 6, BC = 4, CE = 9, CD לא ידוע", maxw=430)


KEY = {   # answer key (מחוון תשובות): part → (answer, how)
    "א": ("דומים לפי ז.ז.", "%s, ולכן %s ו־%s (זוויות מתחלפות); וגם %s (זוויות קודקודיות)." % (
        H.m("AB ∥ DE"), H.m("∢BAC = ∢DEC"), H.m("∢ABC = ∢EDC"), H.m("∢ACB = ∢ECD"))),
    "ב": ("6 ס״מ", "%s, ולכן %s." % (H.m("CD : CB = CE : CA = 9 : 6"), H.m("CD = 4 · 1.5 = 6"))),
}


def build():
    a = Part(
        "א", 2, "knowledge",
        "הסבירו מדוע המשולשים %s ו־%s דומים." % (H.m("ABC"), H.m("EDC")) + H.work(84),
        "דומים לפי ז.ז.",
        "%s (זוויות קודקודיות). %s (זוויות מתחלפות בין המקבילים %s ו־%s). שתי זוויות שוות בהתאמה, ולכן המשולשים דומים לפי ז.ז." % (
            H.m("∢ACB = ∢ECD"), H.m("∢BAC = ∢DEC"), H.m("AB"), H.m("DE")),
        [(2, "שני זוגות זוויות שוות עם נימוק (קודקודיות; מתחלפות) ומשפט דמיון ז.ז."),
         (1, "זוג אחד מנומק, או שני זוגות ללא נימוק."),
         (0, "כל אפשרות אחרת.")],
        errors="&quot;כי הם נראים אותו דבר&quot; — ללא נימוק; שימוש ביחס צלעות (זה מה שצריך להוכיח, לא נתון).",
        reasoning_credit=True,
    )
    b = Part(
        "ב", 3, "algorithmic",
        "נתון: %s ס״מ, %s ס״מ, %s ס״מ. מהו האורך של הקטע %s? הציגו את דרך הפתרון." % (
            H.m("AC = 6"), H.m("CE = 9"), H.m("BC = 4"), H.m("CD")) + H.work(96) + H.ans("תשובה: %s ס״מ" % H.BLANK),
        "6 ס״מ",
        "במשולשים דומים צלעות מתאימות פרופורציוניות: %s, כלומר %s, ולכן %s ס״מ." % (
            H.m(H.frac("CD", "CB") + " = " + H.frac("CE", "CA")), H.m(H.frac("CD", "4") + " = " + H.frac("9", "6")), H.m("CD = 6")),
        [(3, "6 עם פרופורציה נכונה (התאמת קודקודים נכונה)."),
         (2, "פרופורציה נכונה עם טעות חישוב, או יחס דמיון 1.5 ללא השלמה."),
         (1, "פרופורציה עם התאמה שגויה (למשל %s), או 6 ללא דרך." % H.m("CD/6 = 9/4")),
         (0, "כל אפשרות אחרת.")],
        alternatives="יחס הדמיון %s ולכן %s." % (H.m("9 : 6 = 1.5"), H.m("CD = 4 · 1.5 = 6")),
        errors="13.5 (%s) או 2.67 (%s) — התאמת קודקודים לא נכונה; 7 (%s) — חשיבה חיבורית (הוספת 3 במקום כפל ב־1.5)." % (
            H.m("CD = 9 · 6 : 4"), H.m("CD = 4 · 6 : 9"), H.m("4 + 3")),
    )
    return Question(
        n=14, domain="geometry", topic="דמיון משולשים", skill="זיהוי משולשים דומים (ז.ז.) בתצורת &quot;שעון חול&quot;; חישוב צלע מפרופורציה",
        claim="התלמיד מזהה דמיון דרך זוויות קודקודיות ומתחלפות, ומתאים קודקודים נכון בפרופורציה.",
        evidence="נימוק ז.ז. עם שני הזוגות; פרופורציה נכונה ו־6.",
        task="נימוק קצר; חישוב פרופורציוני עם התאמת קודקודים.",
        difficulty="mid", representations=["סרטוט → פרופורציה"], literacy=False, minutes=4,
        stem="<p>בסרטוט שלפניכם %s. הקטעים %s ו־%s נחתכים בנקודה %s.</p>%s" % (H.m("AB ∥ DE"), H.m("AE"), H.m("BD"), H.m("C"), figure()),
        parts=[a, b],
        reference="הקרוב ביותר: שאלה 10 במבחן התרגול הקודם (DE ∥ BC בתוך משולש). הבדלים: (1) תצורת שעון חול עם זוויות קודקודיות, לא משולש בתוך משולש; (2) הזוויות השוות אינן &quot;זווית משותפת&quot;; (3) ההתאמה בין הקודקודים הפוכה (A↔E, B↔D) ומחייבת זהירות; (4) יחס דמיון לא שלם (1.5).",
        accessibility="הסרטוט מדויק ביחס 1.5; המספרים קטנים; חיצי הקבלה מסומנים.",
        notes="התאמת קודקודים בתצורה זו היא המכשול העיקרי; לתרגל כתיבת זוגות מתאימים לפני כתיבת פרופורציה.",
        check=check,
    )
