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
    # C at the center; A and E on one line through C, B and D on the other. Ratio CE:CA = 9:6.
    Cp = (250, 150)
    import math
    ang1, ang2 = math.radians(205), math.radians(335)       # directions to A and B (upper side)
    k = 1.5                                                # CE/CA = CD/CB
    rA, rB = 150, 110
    Ap = (Cp[0] + rA * math.cos(ang1), Cp[1] + rA * math.sin(ang1))
    Bp = (Cp[0] + rB * math.cos(ang2), Cp[1] + rB * math.sin(ang2))
    Ep = (Cp[0] - k * rA * math.cos(ang1), Cp[1] - k * rA * math.sin(ang1))
    Dp = (Cp[0] - k * rB * math.cos(ang2), Cp[1] - k * rB * math.sin(ang2))
    b = S.poly([Ap, Bp, Cp], S.PALE, S.NAVY, 2.2) + S.poly([Ep, Dp, Cp], S.PALE2, S.NAVY, 2.2)
    b += S.par_mark(Ap, Bp, 1, 7, S.BLUE) + S.par_mark(Dp, Ep, 1, 7, S.BLUE)
    for p in (Ap, Bp, Cp, Dp, Ep):
        b += S.dot(p)
    b += S.label(Ap, "A", -14, -6) + S.label(Bp, "B", 14, -6) + S.label(Cp, "C", 0, -12) + S.label(Dp, "D", -14, 12) + S.label(Ep, "E", 14, 12)
    # lengths
    b += S.t((Ap[0] + Cp[0]) / 2 - 14, (Ap[1] + Cp[1]) / 2 + 16, "6", 15, ltr=True, w=600)
    b += S.t((Ep[0] + Cp[0]) / 2 + 16, (Ep[1] + Cp[1]) / 2 - 6, "9", 15, ltr=True, w=600)
    b += S.t((Bp[0] + Cp[0]) / 2 + 14, (Bp[1] + Cp[1]) / 2 + 16, "4", 15, ltr=True, w=600)
    b += S.t((Dp[0] + Cp[0]) / 2 - 16, (Dp[1] + Cp[1]) / 2 - 6, "?", 18, ltr=True, w=700, c=S.AMBER)
    return S.svg(500, 330, b, "שני משולשים עם קודקוד משותף C, AB מקביל ל-DE", maxw=360)


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
        errors="13.5 (4·9/... התאמה שגויה) או 2.67 — התאמת קודקודים לא נכונה; 7 (4 + 3) — חשיבה חיבורית.",
    )
    return Question(
        n=14, domain="geometry", topic="דמיון משולשים", skill="זיהוי משולשים דומים (ז.ז.) בתצורת &quot;שעון חול&quot;; חישוב צלע מפרופורציה",
        claim="התלמיד מזהה דמיון דרך זוויות קודקודיות ומתחלפות, ומתאים קודקודים נכון בפרופורציה.",
        evidence="נימוק ז.ז. עם שני הזוגות; פרופורציה נכונה ו־6.",
        task="נימוק קצר; חישוב פרופורציוני עם התאמת קודקודים.",
        difficulty="mid", representations=["שרטוט → פרופורציה"], literacy=False, minutes=4,
        stem="<p>בסרטוט שלפניכם %s. הקטעים %s ו־%s נחתכים בנקודה %s.</p>%s" % (H.m("AB ∥ DE"), H.m("AE"), H.m("BD"), H.m("C"), figure()),
        parts=[a, b],
        reference="הקרוב ביותר: שאלה 10 במבחן התרגול הקודם (DE ∥ BC בתוך משולש). הבדלים: (1) תצורת שעון חול עם זוויות קודקודיות, לא משולש בתוך משולש; (2) הזוויות השוות אינן &quot;זווית משותפת&quot;; (3) ההתאמה בין הקודקודים הפוכה (A↔E, B↔D) ומחייבת זהירות; (4) יחס דמיון לא שלם (1.5).",
        accessibility="השרטוט מדויק ביחס 1.5; המספרים קטנים; חיצי הקבלה מסומנים.",
        notes="התאמת קודקודים בתצורה זו היא המכשול העיקרי; לתרגל כתיבת זוגות מתאימים לפני כתיבת פרופורציה.",
        check=check,
    )
