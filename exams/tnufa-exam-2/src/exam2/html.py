# -*- coding: utf-8 -*-
"""Markup helpers for the item text: math isolation, option lists, writing windows, answer lines."""

LETTERS = "אבגדהו"


def m(s):
    """Math run, isolated left-to-right inside Hebrew text."""
    return '<bdi class="math" dir="ltr">%s</bdi>' % s


def frac(num, den):
    """Stacked fraction (inline)."""
    return '<span class="frac"><span class="fn">%s</span><span class="fd">%s</span></span>' % (num, den)


def root(n):
    """Square root drawn as a sign joined to the bar over the radicand."""
    return ('<span class="rad" role="img" aria-label="שורש של %s"><svg viewBox="0 0 13 24" preserveAspectRatio="none" aria-hidden="true">'
            '<path d="M0.6 14.2 L3.4 12.6 L7 22.6 L12.2 0.75 H13" fill="none" stroke="#16202c" stroke-width="1.5" stroke-linejoin="miter"/></svg>'
            '<span class="rc">%s</span></span>' % (n, n))


def sup(base, e):
    return '%s<sup>%s</sup>' % (base, e)


def part(letter, html):
    return '<div class="part"><b class="pl">%s.</b><div class="pb">%s</div></div>' % (letter, html)


def opts(items, cols=1):
    out = ""
    for i, it in enumerate(items):
        out += '<div class="opt"><span class="let">%s</span><span class="box"></span><span>%s</span></div>' % (LETTERS[i], it)
    return '<div class="opts c%d">%s</div>' % (cols, out)


def yesno():
    return opts(["כן", "לא"], 2)


def work(h=112):
    """Squared writing window; its height is a hint, the fitter raises it when the sheet has room."""
    return '<div class="work" style="height:%dpx"></div>' % h


def ans(s):
    return '<p class="ans">%s</p>' % s


BLANK = '<span class="blank"></span>'
BL_S = '<span class="blank s"></span>'


def answer_line(label, unit=""):
    return ans("תשובה: %s%s" % (BLANK if not label else label, (" " + unit) if unit else ""))


def table(head_cells, rows, cls="t"):
    th = "".join("<th>%s</th>" % c for c in head_cells)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return '<div class="tw"><table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (cls, th, body)


def kv_table(rows):
    """Two-row table where the first cell of each row is a header (row-oriented data)."""
    body = "".join('<tr><th class="rh">%s</th>%s</tr>' % (r[0], "".join("<td>%s</td>" % c for c in r[1:])) for r in rows)
    return '<div class="tw"><table class="t"><tbody>%s</tbody></table></div>' % body


def system(eqs):
    return '<span class="sys">%s</span>' % "<br>".join(eqs)


def q(n, html):
    return '<article class="q" id="q%d"><div class="qh"><span class="num">%d</span><div class="qb">%s</div></div></article>' % (n, n, html)


def note(s):
    return '<p class="note">%s</p>' % s
