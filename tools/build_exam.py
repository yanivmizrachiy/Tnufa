# -*- coding: utf-8 -*-
"""Builds exam.pdf (A4) from the question source in this file.

Run:  python tools/build_exam.py
Needs: playwright (Chromium) and pymupdf. The answer key is deliberately not kept
in this public repository.
"""
import math, os
import fitz
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "exam.pdf")
TMP = os.path.join(ROOT, "tools", ".exam_print.html")

games = {0: 4, 1: 7, 2: 5, 3: 3, 4: 1}
oren = dict(walk=40, bus=30, bike=25, car=5)
brosh = dict(walk=30, bus=45, bike=15, car=10)

# ---------- palette ----------
NAVY, BLUE, G1, G2, G3 = "#161f31", "#15386e", "#5ca585", "#3c8468", "#276149"
PALE, PALE2, GRID, INK, MUTE = "#e6f1ec", "#cfe4da", "#cdd8d4", "#16202c", "#4f5f6b"
AMBER, YEL = "#c2641a", "#fbe7a6"


# ---------- svg helpers ----------
def svg(w, h, body, label):
    return ('<figure class="fig" style="max-width:%dpx"><svg viewBox="0 0 %d %d" role="img" aria-label="%s" '
            'xmlns="http://www.w3.org/2000/svg">%s</svg></figure>' % (w, w, h, label, body))


def t(x, y, s, size=14, a="middle", ltr=False, w=500, c=INK):
    return ('<text x="%.1f" y="%.1f" font-size="%s" font-weight="%d" text-anchor="%s" fill="%s" direction="%s">%s</text>'
            % (x, y, size, w, a, c, "ltr" if ltr else "rtl", s))


def line(x1, y1, x2, y2, c=INK, w=1.5, extra=""):
    return '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%s" stroke-linecap="round" %s/>' % (x1, y1, x2, y2, c, w, extra)


def head(x, y, ang, c=INK, s=8):
    """Filled arrow head with its tip at (x, y), pointing along ang (degrees, y down)."""
    a = math.radians(ang)
    p = [(x, y)]
    for d in (150, -150):
        b = a + math.radians(d)
        p.append((x + s * math.cos(b), y + s * math.sin(b)))
    return '<polygon points="%s" fill="%s"/>' % (" ".join("%.2f,%.2f" % q for q in p), c)


def arrow(x1, y1, x2, y2, c=INK, w=1.5):
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return line(x1, y1, x2, y2, c, w) + head(x2, y2, ang, c)


def circ(x, y, r, fill, stroke="none", sw=0):
    return '<circle cx="%.2f" cy="%.2f" r="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (x, y, r, fill, stroke, sw)


def rect(x, y, w, h, fill, stroke="none", sw=0, rx=0):
    return '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (x, y, w, h, rx, fill, stroke, sw)


def poly(pts, fill, stroke="none", sw=0, extra=""):
    return '<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" %s/>' % (
        " ".join("%.2f,%.2f" % p for p in pts), fill, stroke, sw, extra)


def arc(cx, cy, r, a1, a2, c=INK, w=1.3):
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    x1, y1 = p(a1); x2, y2 = p(a2)
    return '<path d="M%.2f %.2f A%s %s 0 0 1 %.2f %.2f" fill="none" stroke="%s" stroke-width="%s"/>' % (x1, y1, r, r, x2, y2, c, w)


class Plane:
    """Coordinate plane with one shared scale for grid, ticks, labels and marks."""

    def __init__(self, x1, y1, ux, uy, xlab=1, ylab=1, xgrid=1, ygrid=1, xt="x", yt="y", ml=46, mt=44, mr=64, mb=44):
        self.x1, self.y1, self.ux, self.uy = x1, y1, ux, uy
        self.ml, self.mt = ml, mt
        self.W = ml + x1 * ux + mr
        self.H = mt + y1 * uy + mb
        b = ""
        x = 0
        while x <= x1:
            b += line(self.sx(x), self.sy(0), self.sx(x), self.sy(y1), GRID, .9)
            x += xgrid
        y = 0
        while y <= y1:
            b += line(self.sx(0), self.sy(y), self.sx(x1), self.sy(y), GRID, .9)
            y += ygrid
        b += arrow(self.sx(0), self.sy(0), self.sx(x1) + 26, self.sy(0), INK, 1.7)
        b += arrow(self.sx(0), self.sy(0), self.sx(0), self.sy(y1) - 26, INK, 1.7)
        x = xlab
        while x <= x1:
            b += t(self.sx(x), self.sy(0) + 19, x, 13, ltr=True)
            x += xlab
        y = ylab
        while y <= y1:
            b += t(self.sx(0) - 9, self.sy(y) + 4.5, y, 13, "end", ltr=True)
            y += ylab
        b += t(self.sx(0) - 9, self.sy(0) + 19, 0, 13, "end", ltr=True)
        self.b = b
        self.xt, self.yt = xt, yt

    def sx(self, x): return self.ml + x * self.ux
    def sy(self, y): return self.mt + (self.y1 - y) * self.uy

    def path(self, pts, c=BLUE, w=2.6):
        return '<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"/>' % (
            " ".join("%.2f,%.2f" % (self.sx(a), self.sy(b)) for a, b in pts), c, w)

    def dot(self, x, y, c=INK, r=4.2):
        return circ(self.sx(x), self.sy(y), r, c, "#fff", 1.4)


# ---------- html helpers ----------
def m(s):
    return '<bdi class="math" dir="ltr">%s</bdi>' % s


def part(letter, html):
    return '<div class="part"><b class="pl">%s.</b><div class="pb">%s</div></div>' % (letter, html)


def opts(items, cols=1):
    letters = "אבגדהו"
    out = ""
    for i, it in enumerate(items):
        out += '<div class="opt"><span class="let">%s</span><span class="box"></span><span>%s</span></div>' % (letters[i], it)
    return '<div class="opts c%d">%s</div>' % (cols, out)


def yesno():
    return opts(["כן", "לא"], 2)


def work(h=112):
    return '<div class="work" style="height:%dpx"></div>' % h


def ans(s):
    return '<p class="ans">%s</p>' % s


BLANK = '<span class="blank"></span>'
BL_S = '<span class="blank s"></span>'


def q(n, html):
    return '<article class="q" id="q%d"><div class="qh"><span class="num">%d</span><div class="qb">%s</div></div></article>' % (n, n, html)


Q = []

# ---------- Q1 ----------
Q.append("""<p>פתרו את המשוואה שלפניכם: &nbsp; %s</p><p>הציגו את דרך הפתרון.</p>%s%s""" % (
    m("5y − 7 = 2y + 11"), work(140), ans('תשובה: &nbsp;<bdi dir="ltr" class="math">y = %s</bdi>' % BLANK)))

# ---------- Q2 ----------
p = Plane(7, 6, 44, 44)
b = p.b + t(p.sx(7) + 38, p.sy(0) + 5, "x", 15, ltr=True, w=600) + t(p.sx(0), p.sy(6) - 32, "y", 15, ltr=True, w=600)
for lab, (x, y) in (("M", (1, 2)), ("A", (5, 2))):
    b += p.dot(x, y, BLUE, 5) + t(p.sx(x) + 14, p.sy(y) - 10, lab, 16, ltr=True, w=700, c=BLUE)
Q.append("""<p>במערכת הצירים שלפניכם נתונות שתי נקודות: %s ו־%s.</p>
<p>יונתן מחפש נקודה %s, כך שהמשולש %s יהיה שווה־שוקיים.</p>%s%s%s""" % (
    m("A"), m("M"), m("P"), m("MAP"), svg(int(p.W), int(p.H), b, "מערכת צירים ובה הנקודות M ו-A"),
    part("א", "סמנו במערכת הצירים נקודה שיכולה להיות הנקודה %s, ורשמו את שיעוריה." % m("P") +
         ans('תשובה: &nbsp;<bdi dir="ltr" class="math">P ( %s , %s )</bdi>' % (BL_S, BL_S))),
    part("ב", "האם יש יותר מנקודה אחת שיכולה להיות הנקודה %s?" % m("P") + yesno() + "<p>נמקו את תשובתכם.</p>" + work(84))))


# ---------- Q3 ----------
def tag(cx, txt, cap, fill=PALE, ink=G3):
    return (poly([(cx - 62, 34), (cx + 44, 34), (cx + 62, 62), (cx + 44, 90), (cx - 62, 90)], fill, G3, 1.6) +
            circ(cx + 42, 62, 5, "#fff", G3, 1.4) + t(cx - 8, 71, txt, 22, w=700, c=ink) + t(cx, 114, cap, 13, c=MUTE))


b = tag(530, "150 ₪", "לפני הקיץ") + tag(310, "?", "אחרי ההתייקרות") + tag(90, "?", "בסוף הקיץ")
b += arrow(462, 62, 382, 62, AMBER, 2.2) + t(422, 50, "20%+", 14, w=700, c=AMBER, ltr=False)
b += arrow(242, 62, 162, 62, AMBER, 2.2) + t(202, 50, "20%−", 14, w=700, c=AMBER, ltr=False)
Q.append("""<p>מחיר כרטיס כניסה לפארק מים היה 150 שקלים.</p>
<p>בתחילת הקיץ התייקר הכרטיס ב־20%%. בסוף הקיץ הוזל המחיר החדש ב־20%%.</p>%s%s%s%s""" % (
    svg(620, 124, b, "שינויי מחיר הכרטיס"),
    part("א", "מה היה מחיר הכרטיס אחרי ההתייקרות?" + ans("תשובה: %s שקלים" % BLANK)),
    part("ב", "רוני אומר: &quot;התייקרות של 20%% והוזלה של 20%% מבטלות זו את זו, ולכן בסוף הקיץ המחיר חזר ל־150&nbsp;שקלים.&quot;<br>האם רוני צודק?" % () +
         yesno() + "<p>נמקו את תשובתכם בעזרת חישוב מתאים.</p>" + work(84)),
    part("ג", "בסוף הקיץ החליטה הנהלת הפארק להוזיל את המחיר בדיוק כך שיחזור ל־150 שקלים.<br>בכמה אחוזים היה צריך להוזיל את המחיר שאחרי ההתייקרות?" +
         opts(["בערך 12%", "בערך 17%", "בערך 20%", "בערך 30%"], 2))))


# ---------- Q4 ----------
def hexchain(n, rcx, cy, r=30):
    w = math.sqrt(3) * r
    edges, cells = {}, ""
    verts = set()
    for i in range(n):
        cx = rcx - i * w
        v = [(cx, cy - r), (cx + w / 2, cy - r / 2), (cx + w / 2, cy + r / 2), (cx, cy + r), (cx - w / 2, cy + r / 2), (cx - w / 2, cy - r / 2)]
        cells += poly(v, PALE)
        for j in range(6):
            a, c = v[j], v[(j + 1) % 6]
            k = tuple(sorted(((round(a[0], 1), round(a[1], 1)), (round(c[0], 1), round(c[1], 1)))))
            edges[k] = (a, c)
            verts.add((round(a[0], 1), round(a[1], 1)))
    out = cells
    for a, c in edges.values():
        out += line(a[0], a[1], c[0], c[1], BLUE, 3.6)
    for x, y in verts:
        out += circ(x, y, 3.1, G3)
    return out


b = hexchain(1, 556, 52) + t(556, 112, "צורה 1", 14, w=600)
b += hexchain(2, 438, 52) + t(412, 112, "צורה 2", 14, w=600)
b += hexchain(3, 240, 52) + t(188, 112, "צורה 3", 14, w=600)
tbl = """<div class="tw"><table class="t"><thead><tr><th>מספר הצורה</th><td>1</td><td>2</td><td>3</td><td>4</td><td>10</td></tr></thead>
<tbody><tr><th>מספר המוטות</th><td>6</td><td>11</td><td></td><td></td><td></td></tr></tbody></table></div>"""
Q.append("""<p>נועה בונה צורות של חלת דבש ממוטות זהים, לפי החוקיות המוצגת בסרטוט שלפניכם.</p>%s%s%s%s""" % (
    svg(620, 122, b, "שלוש צורות של משושים צמודים"),
    part("א", "השלימו את הטבלה." + tbl),
    part("ב", "נסמן ב־%s את מספר הצורה. איזה מהביטויים הבאים מבטא את מספר המוטות בצורה שמספרה %s?" % (m("n"), m("n")) +
         opts([m("6n"), m("5n + 1"), m("n + 5"), m("6n − 1")], 2)),
    part("ג", "לנועה יש בדיוק 100 מוטות. האם היא יכולה לבנות צורה אחת ולהשתמש בכל המוטות?" + yesno() + "<p>נמקו את תשובתכם.</p>" + work(84))))

# ---------- Q5 ----------
yT, yB, h1, h2 = 40, 220, 100, 80
Bx = 190
Ex, Ey = Bx + h1 / math.tan(math.radians(35)), yT + h1
Dx = Ex - h2 / math.tan(math.radians(50))
assert abs(Ey + h2 - yB) < 1e-9
b = line(120, yT, 560, yT, NAVY, 2.6) + line(120, yB, 560, yB, NAVY, 2.6)
b += head(452, yT, 0, NAVY, 10) + head(452, yB, 0, NAVY, 10)
b += line(Bx, yT, Ex, Ey, G3, 2.6) + line(Ex, Ey, Dx, yB, G3, 2.6)
b += arc(Bx, yT, 40, 0, 35) + t(Bx + 66 * math.cos(math.radians(17.5)), yT + 66 * math.sin(math.radians(17.5)) + 5, "35°", 15, ltr=True, w=600)
b += arc(Dx, yB, 40, -50, 0) + t(Dx + 66 * math.cos(math.radians(25)), yB - 66 * math.sin(math.radians(25)) + 5, "50°", 15, ltr=True, w=600)
b += arc(Ex, Ey, 26, 130, 215, AMBER, 1.8) + t(Ex - 44, Ey + 11, "?", 20, ltr=True, w=700, c=AMBER)
for lab, x, y, dx, dy in (("B", Bx, yT, 0, -13), ("A", 500, yT, 0, -13), ("D", Dx, yB, 0, 25), ("C", 500, yB, 0, 25), ("E", Ex, Ey, 18, 6)):
    b += circ(x, y, 3.8, NAVY) + t(x + dx, y + dy, lab, 16, ltr=True, w=700)
Q.append("""<p>בסרטוט שלפניכם הישרים %s ו־%s מקבילים. הנקודה %s נמצאת בין שני הישרים.</p>
<p>נתון: %s, &nbsp; %s.</p>%s<p>מהו הגודל של הזווית %s? הציגו את דרך הפתרון.</p>%s%s""" % (
    m("AB"), m("CD"), m("E"), m("∢ABE = 35°"), m("∢CDE = 50°"), svg(620, 256, b, "שני ישרים מקבילים ונקודה E ביניהם"),
    m("BED"), work(145), ans('תשובה: &nbsp;<bdi dir="ltr" class="math">∢BED = %s°</bdi>' % BLANK)))

# ---------- Q6 ----------
b = ""
x0, base, dx, dy = 70, 222, 84, 23
for k, c in games.items():
    for i in range(c):
        b += circ(x0 + k * dx, base - 14 - i * dy, 9.5, G2)
    b += line(x0 + k * dx, base, x0 + k * dx, base + 6, INK, 1.4) + t(x0 + k * dx, base + 24, k, 14, ltr=True, w=600)
b += line(x0 - 34, base, x0 + 4 * dx + 34, base, INK, 1.7) + t(x0 + 2 * dx, base + 48, "מספר השערים במשחק", 14, w=600)
b += circ(396, 32, 9.5, G2) + t(382, 37, "= משחק אחד", 14, "start")
Q.append("""<p>קבוצת הכדורגל של בית הספר שיחקה בליגה העירונית.</p>
<p>בדיאגרמה שלפניכם כל נקודה מייצגת משחק אחד, ומיקומה מראה כמה שערים הבקיעה הקבוצה באותו משחק.</p>%s%s%s%s%s""" % (
    svg(490, 280, b, "דיאגרמת נקודות של מספר השערים במשחק"),
    part("א", "כמה משחקים שיחקה הקבוצה בסך הכול?" + ans("תשובה: %s משחקים" % BLANK)),
    part("ב", "מהו המספר הממוצע של שערים למשחק? הציגו את דרך הפתרון." + work(70) + ans("תשובה: %s שערים" % BLANK)),
    part("ג", "השלימו את החסר במשפט: &nbsp; השכיח של מספר השערים הוא %s, והחציון הוא %s." % (BL_S, BL_S)),
    part("ד", "כמה שערים צריכה הקבוצה להבקיע במשחק הבא, כדי שהממוצע של כל המשחקים יהיה בדיוק 2&nbsp;שערים למשחק? הציגו את דרך הפתרון." + work(84) + ans("תשובה: %s שערים" % BLANK))))

# ---------- Q7 ----------
b = circ(600, 62, 30, PALE, G3, 2) + t(600, 58, "מספר", 13, w=600, c=G3) + t(600, 74, "נכנס", 13, w=600, c=G3)
boxes = [(470, ["העלאה", "בריבוע"]), (320, ["חיסור", "9"]), (170, ["הוצאת", "שורש ריבועי"])]
for cx, lines_ in boxes:
    b += rect(cx - 60, 28, 120, 68, G3, rx=7)
    b += t(cx, 57, lines_[0], 15, w=600, c="#fff") + t(cx, 78, lines_[1], 15, w=600, c="#fff")
b += arrow(568, 62, 534, 62, INK, 2) + arrow(408, 62, 384, 62, INK, 2) + arrow(258, 62, 234, 62, INK, 2) + arrow(108, 62, 74, 62, INK, 2)
b += circ(40, 62, 30, PALE, G3, 2) + t(40, 67, "תוצאה", 13, w=600, c=G3)
Q.append("""<p>במכונת המספרים שלפניכם מכניסים מספר. המכונה מבצעת עליו שלוש פעולות לפי הסדר, ומציגה את התוצאה.</p>%s%s%s%s%s""" % (
    svg(640, 124, b, "שלבי מכונת המספרים"),
    part("א", "תמר הכניסה למכונה את המספר 5. מהי התוצאה שהציגה המכונה? הציגו את דרך הפתרון." + work(56) + ans("תשובה: %s" % BLANK)),
    part("ב", "ישנו מספר נוסף, שונה מ־5, שעבורו מציגה המכונה אותה תוצאה. מהו המספר הזה?" + ans("תשובה: %s" % BLANK)),
    part("ג", "סמנו את <b>כל המספרים</b> שעבורם המכונה מציגה את התוצאה 0." +
         opts([m("−9"), m("−3"), m("0"), m("3"), m("9")], 3)),
    part("ד", "יונתן הכניס למכונה את המספר 2, והמכונה הציגה הודעת שגיאה. הסבירו מדוע." + work(70))))

# ---------- Q8 ----------
p = Plane(20, 50, 25, 5.6, xlab=2, ylab=10, xgrid=2, ygrid=10, mr=44, mt=52, mb=62)
pts = [(0, 0), (4, 40), (10, 40), (12, 20), (16, 20), (20, 0)]
b = p.b + p.path(pts)
for a, c in pts[1:-1]:
    b += p.dot(a, c, BLUE, 3.8)
b += t(p.sx(0) - 34, p.sy(50) - 34, "גובה (במטרים)", 13, "end", w=600)
b += t(p.sx(10), p.sy(0) + 46, "זמן (בשניות)", 13, "middle", w=600)
dx0, dy0 = p.sx(18), p.sy(50) - 22
b += rect(dx0 - 16, dy0 - 5, 32, 10, NAVY, rx=4) + line(dx0 - 30, dy0 - 11, dx0 + 30, dy0 - 11, NAVY, 2)
b += line(dx0 - 24, dy0 - 11, dx0 - 14, dy0, NAVY, 2) + line(dx0 + 24, dy0 - 11, dx0 + 14, dy0, NAVY, 2)
b += line(dx0 - 26, dy0 - 11, dx0 - 26, dy0 - 15, NAVY, 2) + line(dx0 + 26, dy0 - 11, dx0 + 26, dy0 - 15, NAVY, 2)
b += line(dx0 - 36, dy0 - 15, dx0 - 16, dy0 - 15, AMBER, 2.4) + line(dx0 + 16, dy0 - 15, dx0 + 36, dy0 - 15, AMBER, 2.4)
Q.append("""<p>הגרף שלפניכם מתאר את הגובה של רחפן מעל הקרקע במהלך טיסה קצרה, כפונקציה של הזמן שעבר מרגע ההמראה.</p>%s%s%s%s%s""" % (
    svg(int(p.W), int(p.H), b, "גרף גובה הרחפן כפונקציה של הזמן"),
    part("א", "באיזה גובה היה הרחפן 2 שניות אחרי ההמראה?" + ans("תשובה: %s מטרים" % BLANK)),
    part("ב", "במשך כמה שניות בסך הכול הרחפן <b>לא</b> שינה את גובהו?" + ans("תשובה: %s שניות" % BLANK)),
    part("ג", "השלימו את החסר במשפט: &nbsp; הרחפן היה בגובה 30 מטרים כעבור %s שניות וכעבור <span style='white-space:nowrap'>%s שניות.</span>" % (BL_S, BL_S)),
    part("ד", "באיזה פרק זמן ירד הרחפן מהר יותר?" +
         opts(["בין השנייה ה־10 לשנייה ה־12", "בין השנייה ה־16 לשנייה ה־20"]) + "<p>נמקו את תשובתכם בעזרת חישוב מתאים.</p>" + work(70))))


# ---------- Q9 ----------
p = Plane(5, 5, 46, 46)
b = p.b + t(p.sx(5) + 38, p.sy(0) + 5, "x", 15, ltr=True, w=600) + t(p.sx(0), p.sy(5) - 32, "y", 15, ltr=True, w=600)
b += p.path([(2 / 3, 0), (7 / 3, 5)], BLUE) + p.path([(0, 4), (4, 0)], G3)
b += p.dot(1.5, 2.5, NAVY, 5) + t(p.sx(1.5) + 18, p.sy(2.5) + 6, "P", 16, ltr=True, w=700)
for lab, x, y, c in (("a", 2.5, 4.5, BLUE), ("b", 3.5, 1.5, G3)):
    b += t(p.sx(x), p.sy(y) + 6, lab, 17, ltr=True, w=700, c=c)
Q.append("""<p>במערכת הצירים שלפניכם מסורטטים הישרים %s ו־%s, הנחתכים בנקודה %s.</p>
<p>משוואת הישר %s היא %s.</p>%s%s%s""" % (
    m("a"), m("b"), m("P"), m("a"), m("y = 3x − 2"), svg(int(p.W), int(p.H), b, "שני ישרים נחתכים במערכת צירים"),
    part("א", "איזו מהמשוואות הבאות היא משוואת הישר %s?" % m("b") +
         opts([m("y = x + 4"), m("y = −x − 4"), m("y = −x + 4"), m("y = 4x − 1")], 2)),
    part("ב", "מצאו את שיעורי הנקודה %s. הציגו את דרך הפתרון." % m("P") + work(145) +
         ans('תשובה: &nbsp;<bdi dir="ltr" class="math">P ( %s , %s )</bdi>' % (BL_S, BL_S)))))

# ---------- Q10 ----------
A_, B_, C_, D_, E_ = (180, 40), (60, 200), (360, 200), (132, 104), (252, 104)
assert math.dist(A_, D_) == 80 and math.dist(D_, B_) == 120 and D_[1] == E_[1] and E_[0] - D_[0] == 120
b = poly([D_, E_, C_, B_], PALE2) + poly([A_, D_, E_], PALE)
b += poly([A_, B_, C_], "none", NAVY, 2.2) + line(D_[0], D_[1], E_[0], E_[1], G3, 2.4)
b += head(198, 104, 0, G3, 9) + head(216, 200, 0, NAVY, 9)
for lab, pt, dx, dy in (("A", A_, 0, -10), ("B", B_, -14, 8), ("C", C_, 14, 8), ("D", D_, -14, 2), ("E", E_, 14, 2)):
    b += t(pt[0] + dx, pt[1] + dy, lab, 16, ltr=True, w=700)
b += t(127, 68, "4 ס״מ", 14, w=600) + t(58, 148, "6 ס״מ", 14, w=600) + t(192, 95, "6 ס״מ", 14, w=600)
b += t(210, 224, "?", 20, ltr=True, w=700, c=AMBER)
Q.append("""<p>במשולש %s הנקודה %s נמצאת על הצלע %s, והנקודה %s נמצאת על הצלע %s, כך ש־%s.</p>
<p>אורך הקטע %s הוא 4 ס״מ, אורך הקטע %s הוא 6 ס״מ, ואורך הקטע %s הוא 6 ס״מ.</p>%s%s%s""" % (
    m("ABC"), m("D"), m("AB"), m("E"), m("AC"), m("DE ∥ BC"), m("AD"), m("DB"), m("DE"),
    svg(420, 236, b, "משולש ובתוכו קטע המקביל לבסיס"),
    part("א", "הסבירו מדוע המשולשים %s ו־%s דומים." % (m("ADE"), m("ABC")) + work(97)),
    part("ב", "מהו האורך של הצלע %s? הציגו את דרך הפתרון." % m("BC") + work(97) + ans("תשובה: %s ס״מ" % BLANK))))

# ---------- Q11 ----------
b = line(24, 62, 616, 62, INK, 1.7) + head(24, 62, 180, INK, 9) + head(616, 62, 0, INK, 9)
for i in range(0, 9):
    x = 40 + i * 70
    b += line(x, 55, x, 69, INK, 1.4) + t(x, 90, i, 14, ltr=True, w=600)
for lab, v in (("A", 3.5), ("B", 4.5), ("C", 5.5), ("D", 6.5)):
    x = 40 + v * 70
    b += circ(x, 62, 5.5, BLUE, "#fff", 1.4) + t(x, 42, lab, 16, ltr=True, w=700, c=BLUE)
Q.append("""<p>על ישר המספרים שלפניכם מסומנות ארבע נקודות.</p>%s<p>איזו מהנקודות יכולה לייצג את המספר %s?</p>%s""" % (
    svg(640, 100, b, "ישר מספרים מ-0 עד 8 ועליו ארבע נקודות"), m("√30"),
    opts([m("A"), m("B"), m("C"), m("D")], 2)))

# ---------- Q12 ----------
def numline(at, right):
    u = 15
    cx = 120
    b = line(14, 24, 226, 24, INK, 1.4) + head(14, 24, 180, INK, 7) + head(226, 24, 0, INK, 7)
    for i in range(-6, 7):
        b += line(cx + i * u, 20, cx + i * u, 28, INK, 1)
    for v in sorted({0, at}):
        b += t(cx + v * u, 45, str(v).replace("-", "−"), 13, ltr=True, w=600)
    x = cx + at * u
    end = 222 if right else 18
    b += line(x, 24, end, 24, G3, 4)
    b += circ(x, 24, 5, "#fff", G3, 2.4)
    return '<svg class="nl" viewBox="0 0 240 52" role="img" aria-label="ישר מספרים">%s</svg>' % b


Q.append("""<p>נתון אי־השוויון: &nbsp; %s</p><p>איזה מהסרטוטים שלפניכם מציג את כל הפתרונות של אי־השוויון?</p>%s<p>הציגו את דרך הפתרון.</p>%s""" % (
    m("3 − 2x &gt; −5"), opts([numline(4, True), numline(-4, False), numline(4, False), numline(-4, True)], 2), work(97)))

# ---------- Q13 ----------
cats = [("ברגל", "walk"), ("באוטובוס", "bus"), ("באופניים", "bike"), ("ברכב פרטי", "car")]
X0, Y0, UH, bw = 62, 262, 4.2, 38
b = ""
for v in range(0, 51, 10):
    y = Y0 - v * UH
    b += line(X0, y, 610, y, GRID if v else INK, .9 if v else 1.6)
    b += t(X0 - 9, y + 4.5, "%d%%" % v, 13, "end", ltr=True)
slot = (610 - X0) / 4


def bar(x, v, c):
    h = v * UH; y = Y0 - h; r = 4
    return ('<path d="M%.1f %.1f V%.1f Q%.1f %.1f %.1f %.1f H%.1f Q%.1f %.1f %.1f %.1f V%.1f Z" fill="%s"/>' %
            (x, Y0, y + r, x, y, x + r, y, x + bw - r, x + bw, y, x + bw, y + r, Y0, c))


for i, (name, key) in enumerate(cats):
    c = 610 - slot * (i + .5)
    b += bar(c + 1, oren[key], "#2f6fd0") + bar(c - 1 - bw, brosh[key], "#20a070")
    b += t(c + 1 + bw / 2, Y0 - oren[key] * UH - 7, "%d%%" % oren[key], 13, w=600, ltr=True)
    b += t(c - 1 - bw / 2, Y0 - brosh[key] * UH - 7, "%d%%" % brosh[key], 13, w=600, ltr=True)
    b += t(c, Y0 + 24, name, 14, w=600)
b += rect(520, 12, 14, 14, "#2f6fd0", rx=3) + t(514, 24, "אורן", 14, "start", w=600)
b += rect(420, 12, 14, 14, "#20a070", rx=3) + t(414, 24, "ברוש", 14, "start", w=600)
Q.append("""<p>בשני בתי ספר נערך סקר: כיצד התלמידים מגיעים בדרך כלל לבית הספר?</p>
<p>בבית הספר &quot;אורן&quot; לומדים 400 תלמידים, ובבית הספר &quot;ברוש&quot; לומדים 900 תלמידים.</p>
<p>הדיאגרמה שלפניכם מציגה את תוצאות הסקר באחוזים.</p>%s%s%s%s""" % (
    svg(620, 300, b, "דיאגרמת עמודות: אופן ההגעה לבית הספר באחוזים בשני בתי ספר"),
    part("א", "כמה תלמידים מבית הספר &quot;אורן&quot; מגיעים לבית הספר על אופניים?" + ans("תשובה: %s תלמידים" % BLANK)),
    part("ב", "בעיתון המקומי נכתב: &quot;באורן יש יותר תלמידים שמגיעים על אופניים מאשר בברוש.&quot;<br>האם הטענה נכונה?" + yesno() + "<p>נמקו את תשובתכם בעזרת חישוב מתאים.</p>" + work(84)),
    part("ג", "מתוך כלל התלמידים בשני בתי הספר יחד, כמה אחוזים בערך מגיעים באוטובוס?" +
         opts(["בערך 30%", "בערך 37%", "בערך 40%", "בערך 75%"], 2) + "<p>הציגו את דרך הפתרון.</p>" + work(84))))

# ---------- Q14 ----------
Ax, Ay, Dy, half = 478, 44, 134, 110
b = poly([(Ax, Ay), (Ax - half, Dy), (Ax + half, Dy)], PALE, G3, 2)
b += line(Ax, Ay, Ax, Dy, BLUE, 1.8) + rect(Ax, Dy - 10, 10, 10, "none", INK, 1.1)
for sgn in (-1, 1):
    mx, my = Ax + sgn * half / 2, (Ay + Dy) / 2
    L_ = math.hypot(half, Dy - Ay); nx, ny = (Dy - Ay) / L_ * 6, sgn * half / L_ * -6
    b += line(mx - nx, my - ny, mx + nx, my + ny, INK, 1.8)
b += t(Ax, Ay - 9, "A", 16, ltr=True, w=700) + t(Ax + half + 13, Dy + 5, "B", 16, ltr=True, w=700)
b += t(Ax - half - 13, Dy + 5, "C", 16, ltr=True, w=700) + t(Ax, Dy + 19, "D", 16, ltr=True, w=700)
b += t(Ax, Dy + 42, "4 מטרים", 14, w=600) + t(Ax + 42, (Ay + Dy) / 2 + 22, "1.5 מטרים", 13, w=600)
b += line(Ax - half, Dy + 29, Ax - 36, Dy + 29, MUTE, 1) + line(Ax + 36, Dy + 29, Ax + half, Dy + 29, MUTE, 1)
b += line(Ax - half, Dy + 24, Ax - half, Dy + 34, MUTE, 1) + line(Ax + half, Dy + 24, Ax + half, Dy + 34, MUTE, 1)
b += t(Ax, Dy + 66, "חזית האוהל", 14, c=MUTE)
# 3-D tent to the left
Fa, Fb, Fc = (92, 112), (22, 170), (162, 170)
dpx, dpy = 100, -46
Ba, Bb, Bc = (Fa[0] + dpx, Fa[1] + dpy), (Fb[0] + dpx, Fb[1] + dpy), (Fc[0] + dpx, Fc[1] + dpy)
b += poly([Fa, Fc, Bc, Ba], PALE2, G3, 1.8)
b += line(Fb[0], Fb[1], Bb[0], Bb[1], G3, 1.1, 'stroke-dasharray="5 4"') + line(Ba[0], Ba[1], Bb[0], Bb[1], G3, 1.1, 'stroke-dasharray="5 4"') + line(Bb[0], Bb[1], Bc[0], Bc[1], G3, 1.1, 'stroke-dasharray="5 4"')
b += poly([Fa, Fb, Fc], PALE, G3, 2) + line(Fa[0], Fa[1], Fa[0], Fb[1], G3, 1.2)
b += t(Fc[0] + dpx / 2 + 34, Fc[1] + dpy / 2 + 14, "3 מטרים", 13, w=600)
b += t(130, Dy + 66, "האוהל", 14, c=MUTE)
Q.append("""<p>לפניכם סרטוט של אוהל. חזית האוהל היא משולש שווה־שוקיים %s (%s).</p>
<p>%s הוא הגובה לצלע %s. אורך הצלע %s הוא 4 מטרים, ואורך הגובה %s הוא 1.5 מטרים. אורך האוהל הוא 3 מטרים.</p>%s%s%s%s""" % (
    m("ABC"), m("AB = AC"), m("AD"), m("BC"), m("BC"), m("AD"), svg(620, 212, b, "אוהל וחזית האוהל בצורת משולש שווה-שוקיים"),
    part("א", "הוכיחו שהמשולשים %s ו־%s חופפים." % (m("ABD"), m("ACD")) + work(112)),
    part("ב", "מהו האורך של הצלע %s? הציגו את דרך הפתרון." % m("AB") + work(84) + ans("תשובה: %s מטרים" % BLANK)),
    part("ג", "כמה מטרים רבועים של בד דרושים לשני צידי הגג, לחזית האוהל ולגב האוהל? הציגו את דרך הפתרון." + work(98) + ans("תשובה: %s מ״ר" % BLANK))))

# ---------- Q15 ----------
xr, xm, xl, yt, ym, yb = 372, 222, 112, 42, 192, 258
b = rect(xm, yt, xr - xm, ym - yt, PALE2, NAVY, 1.8) + rect(xl, yt, xm - xl, ym - yt, PALE, NAVY, 1.8)
b += rect(xm, ym, xr - xm, yb - ym, PALE, NAVY, 1.8) + rect(xl, ym, xm - xl, yb - ym, "#fff", NAVY, 1.8)
b += t((xm + xr) / 2, (yt + ym) / 2 + 7, "x²", 21, ltr=True, w=600) + t((xl + xm) / 2, (yt + ym) / 2 + 7, "5x", 21, ltr=True, w=600)
b += t((xm + xr) / 2, (ym + yb) / 2 + 8, "?", 22, ltr=True, w=700, c=AMBER) + t((xl + xm) / 2, (ym + yb) / 2 + 8, "?", 22, ltr=True, w=700, c=AMBER)
b += t((xm + xr) / 2, yt - 10, "x", 17, ltr=True, w=600) + t((xl + xm) / 2, yt - 10, "5", 17, ltr=True, w=600)
b += t(xr + 16, (yt + ym) / 2 + 6, "x", 17, ltr=True, w=600) + t(xr + 16, (ym + yb) / 2 + 6, "3", 17, ltr=True, w=600)
Q.append("""<p>המלבן שלפניכם מחולק לארבעה מלבנים. אורכי הצלעות רשומים בסרטוט (%s מספר חיובי).</p>%s%s%s%s""" % (
    m("x"), svg(460, 274, b, "מלבן שצלעותיו x+5 ו-x+3 מחולק לארבעה חלקים"),
    part("א", "השלימו בסרטוט את השטחים החסרים: רשמו ביטוי מתאים במקום כל סימן שאלה."),
    part("ב", "איזה מהביטויים הבאים מבטא את השטח של המלבן הגדול?" +
         opts([m("x² + 15"), m("x² + 8x + 8"), m("x² + 8x + 15"), m("x² + 15x + 8")], 2)),
    part("ג", "נתון ריבוע שאורך צלעו %s.<br>נועה טוענת: &quot;לכל ערך חיובי של %s, השטח של הריבוע גדול ב־1 מהשטח של המלבן הגדול.&quot;<br>האם נועה צודקת?" % (m("x + 4"), m("x")) +
         yesno() + "<p>נמקו את תשובתכם בעזרת ביטויים אלגבריים.</p>" + work(112))))


# ---------- Q16 ----------
def pizza(cx, cy, r, lab):
    b = circ(cx, cy, r, "#dfae6a", "#a9742f", 1.4) + circ(cx, cy, r * .88, "#f6d98e")
    for rad, deg in [(.66, a) for a in (30, 70, 110, 150, 210, 250, 290, 330)] + [(.36, 90), (.36, 270)]:
        a = math.radians(deg)
        b += circ(cx + r * rad * math.cos(a), cy + r * rad * math.sin(a), r * .1, "#b4432b")
    b += line(cx - r, cy, cx + r, cy, NAVY, 1.8) + head(cx - r, cy, 180, NAVY, 8) + head(cx + r, cy, 0, NAVY, 8)
    b += rect(cx - 30, cy - 11, 60, 21, "#fff", rx=4) + t(cx, cy + 5, lab, 13, w=700, c=NAVY)
    return b


# drawn to scale: 6 px per cm
b = pizza(505, 100, 90, "30 ס״מ") + pizza(258, 100, 60, "20 ס״מ") + pizza(112, 100, 60, "20 ס״מ")
b += t(505, 216, "פיצה גדולה: 60 שקלים", 15, w=700, c=G3) + t(185, 216, "2 פיצות קטנות: 25 שקלים לכל פיצה", 15, w=700, c=G3)
Q.append("""<p>בפיצרייה אפשר להזמין פיצה גדולה אחת או שתי פיצות קטנות. כל הפיצות באותו עובי ועם אותן תוספות.</p>
<p>הקוטר של כל פיצה רשום בסרטוט שלפניכם. (בחישובים הניחו %s.)</p>%s%s%s%s""" % (
    '<bdi class="math" dir="ltr"><i style="font-family:serif">π</i> = 3.14</bdi>', svg(620, 226, b, "פיצה גדולה ושתי פיצות קטנות בקנה מידה אחיד"),
    part("א", "מהו השטח של הפיצה הגדולה, בסמ״ר? הציגו את דרך הפתרון." + work(70) + ans("תשובה: %s סמ״ר" % BLANK)),
    part("ב", "דני אומר: &quot;הקוטר של כל פיצה קטנה הוא 20 ס״מ, וביחד זה 40 ס״מ. לכן בשתי הפיצות הקטנות יש יותר פיצה מאשר בפיצה הגדולה.&quot;<br>האם דני צודק?" + yesno() + "<p>נמקו את תשובתכם בעזרת חישוב מתאים.</p>" + work(84)),
    part("ג", "באיזו אפשרות המחיר של סמ״ר פיצה נמוך יותר?" + opts(["פיצה גדולה אחת", "שתי פיצות קטנות"]) + "<p>הציגו את דרך הפתרון.</p>" + work(84))))

# ---------- Q17 ----------
p = Plane(12, 22, 38, 13, xlab=1, ylab=2, xgrid=1, ygrid=2, mr=44, mt=56, mb=62)
b = p.b + p.path([(0, 20), (10, 0)])
b += t(p.sx(4.5), p.sy(15) + 5, "נר א", 14, w=700, c=BLUE)
b += t(p.sx(0) - 34, p.sy(22) - 36, "גובה הנר (בס״מ)", 13, "end", w=600)
b += t(p.sx(6), p.sy(0) + 46, "זמן (בשעות)", 13, w=600)


def candle(cx, base, hcm, lab):
    h = hcm * 5
    out = rect(cx - 9, base - h, 18, h, "#f7f1e3", "#b9a77f", 1.3, 2)
    out += line(cx, base - h, cx, base - h - 6, INK, 1.2)
    out += '<path d="M%.1f %.1f q6 -9 0 -17 q-6 8 0 17z" fill="#e8912d"/>' % (cx, base - h - 5)
    out += line(cx - 15, base, cx + 15, base, INK, 1.3)
    out += t(cx, base + 20, lab, 17, w=600)
    return out


bc = candle(170, 136, 20, "נר א: 20 ס״מ") + candle(60, 136, 12, "נר ב: 12 ס״מ")
Q.append("""<div style="display:flex;gap:14px;align-items:flex-start"><div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:7px">
<p>שני נרות נדלקו באותו רגע, וכל אחד מהם נשרף בקצב קבוע.</p>
<p>נר א: הגובה ההתחלתי שלו 20 ס״מ, והוא מתקצר ב־2 ס״מ בכל שעה.</p>
<p>נר ב: הגובה ההתחלתי שלו 12 ס״מ, והוא מתקצר ב־1 ס״מ בכל שעה.</p></div><div style="flex:0 0 176px">%s</div></div>
<p>במערכת הצירים שלפניכם מסורטט הגרף של נר א.</p>%s%s%s%s%s""" % (
    svg(240, 162, bc, "שני נרות בגבהים 20 ו-12 סנטימטרים"),
    svg(int(p.W), int(p.H), b, "מערכת צירים ובה גרף גובה נר א"),
    part("א", "איזו מהמשוואות הבאות מתארת את הגרף של נר א? (%s — הזמן בשעות, %s — הגובה בס״מ)" % (m("x"), m("y")) +
         opts([m("y = 2x + 20"), m("y = 20 − 2x"), m("y = 20x − 2"), m("y = 2x − 20")], 2)),
    part("ב", "סרטטו באותה מערכת צירים את הגרף של נר ב."),
    part("ג", "כעבור כמה שעות יהיו שני הנרות באותו הגובה? מהו הגובה הזה? הציגו את דרך הפתרון." + work(98) +
         ans("כעבור %s שעות, בגובה %s ס״מ" % (BL_S, BL_S))),
    part("ד", "הנרות נדלקו בשעה 18:00. באיזו שעה כבה הנר הראשון, ואיזה מהנרות זה היה?" +
         ans("נר %s כבה בשעה %s" % (BL_S, BL_S)))))

# ---------- sub-part load: keep close to the reference exam (17 questions, about 35 items) ----------
DROP = {3: "ג", 6: "א", 7: "ב", 8: "א", 13: "א", 16: "א", 17: "ד"}
OPEN = '<div class="part"><b class="pl">'
HEB = "אבגדה"
for i, html_ in enumerate(Q):
    segs = html_.split(OPEN)
    kept = [x for x in segs[1:] if not x.startswith(DROP.get(i + 1, "#") + ".")]
    assert len(kept) == len(segs[1:]) - (1 if (i + 1) in DROP else 0), i + 1
    Q[i] = segs[0] + "".join(OPEN + HEB[j] + x[1:] for j, x in enumerate(kept))
ITEMS = sum(max(1, x.count(OPEN)) for x in Q)
assert ITEMS == 37, ITEMS

# ---------- print layout ----------
CSS = """
/* A4 sheets: content column, then the shared footer. Grid paper fills spare room. */
:root{--ink:#16202c;--mute:#4f5f6b;--navy:#15386e;--g3:#276149;--line:#cdd8d4;--foot:92px}
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
@page{size:A4;margin:0}
html,body{margin:0;padding:0;background:#fff}
body{color:var(--ink);font-family:"Heebo",Arial,sans-serif;font-size:14.8px;line-height:1.55}
.page{position:relative;width:210mm;height:297mm;overflow:hidden;break-after:page;display:flex;flex-direction:column;
  padding:34px 60px var(--foot)}
.page:last-child{break-after:auto}
.content{flex:1 1 auto;min-height:0;display:flex;flex-direction:column}
.foot{position:absolute;inset-inline:0;bottom:0;height:var(--foot);background:#fff}
.foot .rule{position:absolute;top:0;inset-inline:0;height:2.5px;background:var(--navy)}
.foot .row{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:12px;padding-top:3px}
.foot img{width:40px;height:40px;border-radius:50%}
.foot .lines{display:flex;flex-direction:column;text-align:center;line-height:1.3}
.foot b{font-weight:800;font-size:12.5px;color:#122f4c}
.foot span{font-size:11px;color:#3a5168}
.q{padding-block:14px 16px;border-top:1.5px solid var(--line)}
.q:first-child{border-top:0;padding-top:0}
.qh{display:flex;gap:12px;align-items:flex-start}
.num{flex:0 0 auto;width:36px;height:36px;border-radius:50%;background:var(--g3);color:#fff;font-weight:700;font-size:18px;
  display:flex;align-items:center;justify-content:center;font-variant-numeric:tabular-nums}
.qb{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:7px;padding-top:5px}
.qb p{margin:0}
.fig{margin:4px auto;width:100%}
.fig svg{display:block;width:100%;height:auto;font-family:"Heebo",Arial,sans-serif}
.part{display:flex;gap:8px;margin-top:5px}
.pl{flex:0 0 16px;font-weight:800}
.pb{flex:1 1 auto;min-width:0}
.pb>p,.pb>.opts,.pb>.work,.pb>.ans,.pb>.fig,.pb>.tw{margin-top:7px;margin-bottom:0}
.math{font-family:Arial,"Heebo",sans-serif;white-space:nowrap;unicode-bidi:isolate}
.opts{display:grid;gap:7px 22px;margin-block:3px}
.opts.c2{grid-template-columns:repeat(2,minmax(0,1fr))}
.opts.c3{grid-template-columns:repeat(3,minmax(0,1fr))}
.opt{display:flex;align-items:center;gap:8px;min-width:0}
.opt>span:last-child{flex:1 1 auto;min-width:0}
.let{font-size:11px;color:var(--mute);width:10px;flex:0 0 auto}
.box{flex:0 0 auto;width:16px;height:16px;border:1.3px solid #6d7a84;border-radius:3px;background:#fff}
.sys{display:inline-block;font-family:Arial,"Heebo",sans-serif;border-inline-start:2px solid var(--ink);padding-inline-start:8px;line-height:1.4;text-align:left}
.nl{display:block;width:100%;max-width:240px;height:auto;font-family:"Heebo",Arial,sans-serif}
.work,.fill{position:relative;overflow:hidden}
.work svg,.fill svg{position:absolute;inset:0;display:block}
.fill{flex:1 1 auto;min-height:0;margin-top:6px;margin-bottom:10px}
.ans{font-weight:500}
.blank{display:inline-block;position:relative;width:97px;height:25px;margin-inline:3px;vertical-align:middle}
.blank svg{position:absolute;inset:0;display:block}
.blank.s{width:61px}
.tw{overflow:hidden}
.t{border-collapse:collapse;width:100%;font-size:14px;text-align:center}
.t th{background:var(--g3);color:#fff;font-weight:600;padding:6px 10px;border:1px solid var(--g3);white-space:nowrap}
.t td{border:1px solid #6d7a84;padding:6px 10px;min-width:50px;height:34px;font-variant-numeric:tabular-nums}
.intro{color:#2b4080;display:flex;flex-direction:column;flex:1 1 auto}
.intro .meta{color:#111111;text-align:right;margin:0 0 16px;padding:0 0 10px;font-size:15px;font-weight:600;line-height:1.5;border-bottom:1px solid #d4dce2}
.intro h2{font-family:"Rubik","Heebo",sans-serif;font-weight:700;color:#2d4799;font-size:22.5px;text-align:center;margin:28px 0 12px}
.intro p.l{margin:0 0 13px}
.intro .luck{font-family:"Rubik","Heebo",sans-serif;font-weight:700;color:#2d4799;font-size:24px;text-align:center;margin-top:44px}
.draft{font-family:"Rubik","Heebo",sans-serif;font-weight:700;color:#1d4ed8;font-size:18.5px;text-align:center;margin:0}
"""

GRID_JS = """
/* Notebook windows: even squares, soft frame, a pencil tab, and a small green cross every five squares. */
const S = 18, IN = 3;
const pencil = (cx, cy) => `<g transform="translate(${cx} ${cy}) rotate(135)"><rect x="-8.2" y="-2.3" width="3" height="4.6" rx="0.8" fill="#cfe4da"/><rect x="-4.6" y="-2.3" width="8.6" height="4.6" fill="#fff"/><polygon points="4.4,-2.3 8.4,0 4.4,2.3" fill="#fff"/></g>`;
document.querySelectorAll('.work,.fill').forEach((el, n) => {
  const w = Math.floor(el.clientWidth), h = Math.floor(el.clientHeight);
  const cols = Math.floor((w - 2 * IN) / S), rows = Math.floor((h - 2 * IN) / S);
  const W = cols * S, H = rows * S, x0 = Math.floor((w - W) / 2), y0 = IN, xr = x0 + W, R = 11, id = 'win' + n;
  let g = '';
  for (let i = 1; i < cols; i++) g += `<line x1="${x0 + i * S}" y1="${y0}" x2="${x0 + i * S}" y2="${y0 + H}"/>`;
  for (let j = 1; j < rows; j++) g += `<line x1="${x0}" y1="${y0 + j * S}" x2="${xr}" y2="${y0 + j * S}"/>`;
  let c = '';
  for (let i = 5; i < cols; i += 5) for (let j = 5; j < rows; j += 5) {
    const x = xr - i * S, y = y0 + j * S;
    c += `<path d="M${x - 3.5} ${y}H${x + 3.5}M${x} ${y - 3.5}V${y + 3.5}"/>`;
  }
  const tab = `<path d="M${xr - 38} ${y0}H${xr - R}A${R} ${R} 0 0 1 ${xr} ${y0 + R}V${y0 + 27}H${xr - 30}A8 8 0 0 1 ${xr - 38} ${y0 + 19}Z" fill="#276149"/>` + pencil(xr - 19, y0 + 13.5);
  el.insertAdjacentHTML('afterbegin', `<svg width="${w}" height="${h}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
    <defs><clipPath id="${id}"><rect x="${x0}" y="${y0}" width="${W}" height="${H}" rx="${R}"/></clipPath></defs>
    <rect x="${x0}" y="${y0}" width="${W}" height="${H}" rx="${R}" fill="#f8fbfa" stroke="#cfe4da" stroke-width="5"/>
    <g clip-path="url(#${id})"><g stroke="#bcd2e4" stroke-width="0.65">${g}</g><g stroke="#5ca585" stroke-width="1" fill="none">${c}</g>${tab}</g>
    <rect x="${x0}" y="${y0}" width="${W}" height="${H}" rx="${R}" fill="none" stroke="#276149" stroke-width="1.3"/></svg>`);
});
document.querySelectorAll('.blank').forEach(el => {
  const W = el.clientWidth - 1, H = el.clientHeight - 1, s = 12;
  let g = '';
  for (let x = s; x < W; x += s) g += `<line x1="${x + 0.5}" y1="0.5" x2="${x + 0.5}" y2="${H + 0.5}"/>`;
  for (let y = s; y < H; y += s) g += `<line x1="0.5" y1="${y + 0.5}" x2="${W + 0.5}" y2="${y + 0.5}"/>`;
  el.innerHTML = `<svg width="${W + 1}" height="${H + 1}" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><rect x="0.5" y="0.5" width="${W}" height="${H}" rx="4" fill="#f8fbfa"/><g stroke="#bcd2e4" stroke-width="0.6">${g}</g><rect x="0.5" y="0.5" width="${W}" height="${H}" rx="4" fill="none" stroke="#276149" stroke-width="1.1"/></svg>`;
});
"""

FOOT = ('<div class="foot"><span class="rule"></span><div class="row"><img src="../assets/logo.svg" alt="">'
        '<div class="lines"><b>יניב רז — מדריך מחוזי חט״ב בעיר ירושלים</b>'
        '<span>הדרכה במחוז ירושלים והעיר ירושלים — מנח״י, בהובלת איילת קריספין</span></div></div></div>')

INTRO = """<div class="intro">
<p class="meta">זמן: 90 דקות | מותר להשתמש במחשבון ובסרגל</p>
<h2>אז מה צריך לעשות?</h2>
<p class="l">יש לפתור את המבחן ברצינות.</p>
<p class="l">המבחן נועד לאפשר לנו במערכת החינוך להבין במה הצלחנו ובמה אנחנו צריכים להשתפר.</p>
<p class="l">לכתוב רק בעט כחול, בעט שחור או בעיפרון.</p>
<p class="l">בשאלות שבהן יש לבחור תשובה, יש לסמן X במשבצת שליד התשובה שלדעתך היא הנכונה.</p>
<h2>ומה אפשר לעשות?</h2>
<p class="l">אפשר להיעזר במחשבון ובסרגל.</p>
<p class="l">אפשר להיעזר בדפי הטיוטה המצורפים בסוף המבחן (דפים אלה לא ייבדקו).</p>
<p class="l">אפשר לבקש מהמשגיחים עוד זמן.</p>
<p class="l" style="margin-top:24px">שימו לב, הסרטוטים במבחן מוקטנים.</p>
<p class="luck">בהצלחה!</p>
</div>"""

HEAD = ('<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><title>מבחן במתמטיקה לכיתה ט׳</title>'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;500;600;700;800&family=Rubik:wght@700&display=swap">'
        '<style>' + CSS + '</style></head><body>')


def sheet(inner):
    return '<section class="page"><div class="content">%s</div>%s</section>' % (inner, FOOT)


def write(html_):
    with open(TMP, "w", encoding="utf-8") as f:
        f.write(html_)


# Answer boxes: whole grid cells; spare room on a sheet raises the smallest box first, up to a cap.
FIT_JS = """
document.querySelectorAll('.page').forEach(pg => {
  const c = pg.querySelector('.content'), boxes = [...c.querySelectorAll('.work')];
  if (!boxes.length) return;
  const S = 18, CAP = 18;
  const hs = boxes.map(b => Math.floor((b.offsetHeight - 6) / S));
  boxes.forEach((b, i) => { b.style.height = hs[i] * S + 6 + 'px'; });
  let spare = c.getBoundingClientRect().bottom - c.lastElementChild.getBoundingClientRect().bottom;
  while (spare >= S) {
    const low = Math.min(...hs);
    if (low >= CAP) break;
    const i = hs.indexOf(low);
    hs[i]++; spare -= S;
    boxes[i].style.height = hs[i] * S + 6 + 'px';
  }
});
"""

with sync_playwright() as p:
    br = p.chromium.launch(headless=True, timeout=60000)
    try:
        pg = br.new_page(viewport={"width": 794, "height": 1123})
        pg.set_default_timeout(60000)
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.emulate_media(media="print")
        uri = "file:///" + TMP.replace("\\", "/")

        # 1. measure every question at the final column width
        write(HEAD + sheet("".join(q(i + 1, s) for i, s in enumerate(Q))).replace('class="page"', 'class="page" style="height:auto;overflow:visible"') + "</body></html>")
        pg.goto(uri, wait_until="networkidle")
        pg.evaluate("document.fonts.ready.then(()=>1)")
        heights = pg.evaluate("[...document.querySelectorAll('.q')].map(e => e.getBoundingClientRect().height)")
        avail = pg.evaluate("""() => { const c = document.createElement('section'); c.className='page';
            c.innerHTML='<div class="content"></div>'; document.body.append(c);
            const h = c.querySelector('.content').getBoundingClientRect().height; c.remove(); return h; }""")
        print("sheet content height: %.0f" % avail)
        print("question heights:", [round(h) for h in heights])
        too_tall = [i + 1 for i, h in enumerate(heights) if h > avail]
        assert not too_tall, "questions taller than one sheet: %s" % too_tall

        # 2. greedy pagination: a question is never split across sheets
        sheets, cur, used = [], [], 0.0
        for i, h in enumerate(heights):
            if cur and used + h > avail:
                sheets.append(cur); cur, used = [], 0.0
            cur.append(i); used += h
        sheets.append(cur)
        print("sheets:", [[i + 1 for i in s] for s in sheets])

        # 3. final document: instructions, question sheets, two draft sheets
        body = sheet(INTRO)
        for s in sheets:
            body += sheet("".join(q(i + 1, Q[i]) for i in s))
        for n in (1, 2):
            body += sheet('<h2 class="draft">דף טיוטה %d — לא ייבדק</h2><div class="fill" style="margin-top:10px"></div>' % n)
        write(HEAD + body + "</body></html>")
        pg.goto(uri, wait_until="networkidle")
        pg.evaluate("document.fonts.ready.then(()=>1)")
        pg.evaluate(FIT_JS)
        pg.evaluate(GRID_JS)
        over = pg.evaluate("""[...document.querySelectorAll('.content')].map((c,i)=>[i+1,c.scrollHeight-c.clientHeight,c.scrollWidth-c.clientWidth]).filter(a=>a[1]>1||a[2]>1)""")
        assert not over, "overflowing sheets: %s" % over
        assert pg.evaluate("document.fonts.check('15px Heebo') && document.fonts.check('700 22px Rubik')"), "fonts did not load"
        assert not errs, errs
        raw = PDF + ".raw"
        pg.pdf(path=raw, prefer_css_page_size=True, print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        expected = len(sheets) + 3
    finally:
        br.close()
        if os.path.exists(TMP):
            os.remove(TMP)

doc = fitz.open(raw)
assert doc.page_count == expected, (doc.page_count, expected)
doc.set_metadata({"title": "מבחן במתמטיקה לכיתה ט׳", "author": "יניב רז", "subject": "לקראת תנופה"})
doc.save(PDF, garbage=4, deflate=True)
doc.close()
os.remove(raw)
print("wrote exam.pdf: %d pages, %d KB" % (expected, os.path.getsize(PDF) // 1024))
