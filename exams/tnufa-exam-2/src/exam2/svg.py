# -*- coding: utf-8 -*-
"""Vector figure helpers. Every drawing in the exam is built from these, with real geometry
(coordinates are computed, never eyeballed), so a figure is exact and prints sharp."""
import math

# palette (shared with the booklet CSS)
NAVY, BLUE, G1, G2, G3 = "#161f31", "#15386e", "#5ca585", "#3c8468", "#276149"
PALE, PALE2, GRID, INK, MUTE = "#e6f1ec", "#cfe4da", "#cdd8d4", "#16202c", "#4f5f6b"
AMBER, YEL, TURQ = "#c2641a", "#fbe7a6", "#15bda9"


def svg(w, h, body, label, maxw=None):
    return ('<figure class="fig" style="max-width:%dpx"><svg viewBox="0 0 %d %d" role="img" aria-label="%s" '
            'xmlns="http://www.w3.org/2000/svg">%s</svg></figure>' % (maxw or w, w, h, label, body))


def t(x, y, s, size=14, a="middle", ltr=False, w=500, c=INK, extra=""):
    return ('<text x="%.1f" y="%.1f" font-size="%s" font-weight="%d" text-anchor="%s" fill="%s" direction="%s" %s>%s</text>'
            % (x, y, size, w, a, c, "ltr" if ltr else "rtl", extra, s))


def line(x1, y1, x2, y2, c=INK, w=1.5, extra=""):
    return ('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%s" stroke-linecap="round" %s/>'
            % (x1, y1, x2, y2, c, w, extra))


def head(x, y, ang, c=INK, s=8):
    """Filled arrow head with its tip at (x, y), pointing along ang (degrees, y down)."""
    a = math.radians(ang)
    p = [(x, y)]
    for d in (150, -150):
        b = a + math.radians(d)
        p.append((x + s * math.cos(b), y + s * math.sin(b)))
    return '<polygon points="%s" fill="%s"/>' % (" ".join("%.2f,%.2f" % q for q in p), c)


def arrow(x1, y1, x2, y2, c=INK, w=1.5, s=8):
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return line(x1, y1, x2, y2, c, w) + head(x2, y2, ang, c, s)


def circ(x, y, r, fill, stroke="none", sw=0.0):
    return '<circle cx="%.2f" cy="%.2f" r="%s" fill="%s" stroke="%s" stroke-width="%s"/>' % (x, y, r, fill, stroke, sw)


def rect(x, y, w, h, fill, stroke="none", sw=0.0, rx=0, extra=""):
    return '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%s" fill="%s" stroke="%s" stroke-width="%s" %s/>' % (
        x, y, w, h, rx, fill, stroke, sw, extra)


def poly(pts, fill, stroke="none", sw=0.0, extra=""):
    return '<polygon points="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" %s/>' % (
        " ".join("%.2f,%.2f" % p for p in pts), fill, stroke, sw, extra)


def path(d, fill="none", stroke=INK, w=1.5, extra=""):
    return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round" %s/>' % (
        d, fill, stroke, w, extra)


def arc(cx, cy, r, a1, a2, c=INK, w=1.3):
    """Arc from angle a1 to a2 (degrees, y down, clockwise positive)."""
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    x1, y1 = p(a1)
    x2, y2 = p(a2)
    large = 1 if (a2 - a1) % 360 > 180 else 0
    return '<path d="M%.2f %.2f A%s %s 0 %d 1 %.2f %.2f" fill="none" stroke="%s" stroke-width="%s"/>' % (
        x1, y1, r, r, large, x2, y2, c, w)


def angle_mark(v, p1, p2, r=24, c=INK, w=1.3, label="", lsize=14, lc=INK, lr=None):
    """Arc inside angle p1-v-p2 (the smaller one), with an optional label on the bisector."""
    a1 = math.degrees(math.atan2(p1[1] - v[1], p1[0] - v[0]))
    a2 = math.degrees(math.atan2(p2[1] - v[1], p2[0] - v[0]))
    d = (a2 - a1) % 360
    if d > 180:
        a1, a2 = a2, a1
        d = 360 - d
    out = arc(v[0], v[1], r, a1, a1 + d, c, w)
    if label:
        mid = math.radians(a1 + d / 2)
        R = lr or (r + 16)
        out += t(v[0] + R * math.cos(mid), v[1] + R * math.sin(mid) + 5, label, lsize, ltr=True, w=600, c=lc)
    return out


def right_mark(v, p1, p2, s=11, c=INK, w=1.3):
    """Small square marking a right angle at v between directions to p1 and p2."""
    u = (p1[0] - v[0], p1[1] - v[1])
    q = (p2[0] - v[0], p2[1] - v[1])
    ul, ql = math.hypot(*u), math.hypot(*q)
    ux, uy, qx, qy = u[0] / ul * s, u[1] / ul * s, q[0] / ql * s, q[1] / ql * s
    return path("M%.2f %.2f L%.2f %.2f L%.2f %.2f" % (v[0] + ux, v[1] + uy, v[0] + ux + qx, v[1] + uy + qy, v[0] + qx, v[1] + qy), stroke=c, w=w)


def tick(p1, p2, n=1, s=6, c=INK, w=1.6, gap=5):
    """n short strokes across the midpoint of segment p1-p2 (equal-length marks)."""
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L            # along
    nx, ny = -uy, ux                   # normal
    out = ""
    for i in range(n):
        off = (i - (n - 1) / 2) * gap
        cx, cy = mx + ux * off, my + uy * off
        out += line(cx - nx * s, cy - ny * s, cx + nx * s, cy + ny * s, c, w)
    return out


def par_mark(p1, p2, n=1, s=6, c=INK, w=1.5, gap=6):
    """n small chevrons at the midpoint of p1-p2, pointing from p1 to p2 (parallel marks)."""
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    out = ""
    for i in range(n):
        off = (i - (n - 1) / 2) * gap
        cx, cy = mx + ux * off, my + uy * off
        out += path("M%.2f %.2f L%.2f %.2f L%.2f %.2f" % (cx - ux * s + nx * s, cy - uy * s + ny * s, cx, cy,
                                                         cx - ux * s - nx * s, cy - uy * s - ny * s), stroke=c, w=w)
    return out


def label(p, s, dx=0, dy=0, size=16, c=INK, w=700):
    return t(p[0] + dx, p[1] + dy, s, size, ltr=True, w=w, c=c)


def dot(p, r=3.6, c=NAVY):
    return circ(p[0], p[1], r, c)


class Plane:
    """Coordinate plane with one shared scale; supports negative ranges. Units are grid units."""

    def __init__(self, xmin, xmax, ymin, ymax, u=32, xlab=1, ylab=1, ml=30, mt=30, mr=40, mb=34, labels=True):
        self.xmin, self.xmax, self.ymin, self.ymax, self.u = xmin, xmax, ymin, ymax, u
        self.ml, self.mt = ml, mt
        self.W = ml + (xmax - xmin) * u + mr
        self.H = mt + (ymax - ymin) * u + mb
        b = ""
        for x in range(xmin, xmax + 1):
            b += line(self.sx(x), self.sy(ymin), self.sx(x), self.sy(ymax), GRID, .9)
        for y in range(ymin, ymax + 1):
            b += line(self.sx(xmin), self.sy(y), self.sx(xmax), self.sy(y), GRID, .9)
        b += arrow(self.sx(xmin) - 6, self.sy(0), self.sx(xmax) + 22, self.sy(0), INK, 1.7)
        b += arrow(self.sx(0), self.sy(ymin) + 6, self.sx(0), self.sy(ymax) - 22, INK, 1.7)
        if labels:
            for x in range(xmin, xmax + 1):
                if x % xlab == 0 and x != 0:
                    b += line(self.sx(x), self.sy(0) - 3, self.sx(x), self.sy(0) + 3, INK, 1.2)
                    b += t(self.sx(x), self.sy(0) + 17, str(x).replace("-", "−"), 12, ltr=True)
            for y in range(ymin, ymax + 1):
                if y % ylab == 0 and y != 0:
                    b += line(self.sx(0) - 3, self.sy(y), self.sx(0) + 3, self.sy(y), INK, 1.2)
                    b += t(self.sx(0) - 7, self.sy(y) + 4.3, str(y).replace("-", "−"), 12, "end", ltr=True)
            b += t(self.sx(0) - 7, self.sy(0) + 17, "0", 12, "end", ltr=True)
        b += t(self.sx(xmax) + 24, self.sy(0) + 5, "x", 15, ltr=True, w=600)
        b += t(self.sx(0) + 10, self.sy(ymax) - 20, "y", 15, ltr=True, w=600, a="start")
        self.b = b

    def sx(self, x):
        return self.ml + (x - self.xmin) * self.u

    def sy(self, y):
        return self.mt + (self.ymax - y) * self.u

    def pt(self, x, y):
        return (self.sx(x), self.sy(y))

    def line_through(self, m, k, c=BLUE, w=2.4, pad=0.6):
        """Draw y = m x + k across the visible rectangle, slightly past the grid."""
        pts = []
        for x in (self.xmin - pad, self.xmax + pad):
            pts.append((x, m * x + k))
        # clip to vertical range
        out = []
        for x, y in pts:
            out.append((x, y))
        (x1, y1), (x2, y2) = out
        ylo, yhi = self.ymin - pad, self.ymax + pad

        def clipx(y):
            return (y - k) / m if m else None
        if y1 < ylo:
            x1, y1 = clipx(ylo), ylo
        if y1 > yhi:
            x1, y1 = clipx(yhi), yhi
        if y2 < ylo:
            x2, y2 = clipx(ylo), ylo
        if y2 > yhi:
            x2, y2 = clipx(yhi), yhi
        return '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (
            self.sx(x1), self.sy(y1), self.sx(x2), self.sy(y2), c, w)

    def mark(self, x, y, c=NAVY, r=4):
        return circ(self.sx(x), self.sy(y), r, c, "#fff", 1.3)
