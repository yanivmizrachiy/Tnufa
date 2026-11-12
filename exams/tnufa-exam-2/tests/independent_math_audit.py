# -*- coding: utf-8 -*-
"""Independent, deterministic exam-key audit. No use of each question's check() function.

Runs on every build before PDF publication. Expected final answers and scores are
a fixed review baseline; numerical relationships are independently recomputed below.
"""
import html
import math
import re
import statistics
from fractions import Fraction

EXPECTED = [
    [("א", 2, "13"), ("ב", 2, "לא")],
    [("א", 3, "120"), ("ב", 3, "מרוכז פחות")],
    [("", 5, "120")],
    [("", 5, "−5")],
    [("א", 2, "4x"), ("ב", 4, "הוכחה")],
    [("", 5, "13")],
    [("א", 1, "140"), ("ב", 2, "6x"), ("ג", 2, "60"), ("ד", 3, "8")],
    [("א", 4, "x = 5"), ("ב", 2, "כן")],
    [("א", 3, "x ≥ 4"), ("ב", 1, "ג, ד, ה")],
    [("א", 1, "a"), ("ב", 2, "y = x"), ("ג", 1, "y = x"), ("ד", 2, "לא")],
    [("א", 3, "60°"), ("ב", 3, "70°")],
    [("א", 1, "∢ABC"), ("ב", 4, "הוכחה"), ("ג", 2, "AD = AE")],
    [("א", 3, "100"), ("ב", 2, "כן"), ("ג", 2, "60")],
    [("א", 2, "דומים"), ("ב", 3, "6")],
    [("א", 2, "5"), ("ב", 3, "פי 4")],
    [("א", 1, "25"), ("ב", 1, "2"), ("ג", 2, "2"), ("ד", 2, "2.24"), ("ה", 2, "לא")],
    [("א", 2, "48"), ("ב", 2, "45%"), ("ג", 3, "16")],
]


def _plain(text):
    return html.unescape(re.sub(r"<[^>]*>", "", text)).replace("\u200e", "").replace("\u200f", "")


def verify(qs):
    assert len(qs) == len(EXPECTED) == 17
    assert sum(map(len, EXPECTED)) == 41, "the current exam has 41 subparts"
    total = 0
    for index, (q, expected_parts) in enumerate(zip(qs, EXPECTED), 1):
        assert q.n == index
        assert len(q.parts) == len(expected_parts), (index, len(q.parts), len(expected_parts))
        for p, (letter, points, token) in zip(q.parts, expected_parts):
            assert p.letter == letter and p.points == points, (index, letter, points)
            assert token in _plain(p.key), (index, letter, token, _plain(p.key))
            assert p.rubric and p.rubric[0][0] == points and p.rubric[-1][0] == 0
            levels = [level for level, _ in p.rubric]
            assert all(isinstance(level, int) and 0 <= level <= points for level in levels)
            assert levels == sorted(set(levels), reverse=True), (index, letter, levels)
            assert all(isinstance(label, str) and label.strip() for _, label in p.rubric)
            assert p.how.strip() and p.solution.strip()
            total += points
    assert total == 100, total

    # Numerical results recomputed from independently stated exam conditions.
    assert 3 ** 2 + math.isqrt(16) == 13 and 2 ** 5 != 5 ** 2                  # Q1
    assert 600 * Fraction(1, 5) == 120 and Fraction(200, 1100) < Fraction(1, 5) # Q2
    assert Fraction(90, 1) / Fraction(75, 100) == 120                           # Q3
    assert 3 * (-5 - 4) == 7 * -5 + 8                                           # Q4
    assert all((2*x-3)**2 - 4*x*(x-3) == 9 for x in range(-10, 11))             # Q5
    assert Fraction(13+2, 3) - Fraction(13-1, 4) == 2                          # Q6
    assert [80 + 6*n for n in (10, 20, 50)] == [140, 200, 380]                 # Q7
    assert Fraction(440-80, 6) == 60 and Fraction(80+6*40, 40) == 8
    assert (2*5+1 == 11 and 5-1 == 4 and 2*5-9 == 1)                          # Q8
    assert all((2*x+6 <= 5*x-6) == (x>=4) for x in range(-20, 21))             # Q9
    a, b, c, d = (lambda x: -2*x+4), (lambda x: x-3), (lambda x: -x+2), (lambda x: x+2)
    assert a(0)==4 and a(2)==c(2)==0 and b(2)!=0 and d(0)==2 and d(1)-d(0)==1 # Q10
    assert 180-50-2*35==60 and 2*35==70                                       # Q11
    # Representative construction with AB=AC, BD=CE gives AD=AE.             # Q12
    A, D, E = (0, 6), (-2, 0), (2, 0)
    assert math.dist(A, D)==math.dist(A, E)
    assert math.hypot(80, 60)==100 and 100 / Fraction(5, 2)==40              # Q13
    assert math.isqrt(65**2-25**2)==60
    assert Fraction(4*9, 6)==6                                                # Q14
    assert 2*(5+8)==26 and (10*16)==4*(5*8)                                   # Q15
    freq = {0:2, 1:5, 2:8, 3:6, 4:3, 5:1}
    vals = sorted(v for k, count in freq.items() for v in [k]*count)
    assert len(vals)==25 and sum(vals)==56 and statistics.mode(vals)==2       # Q16
    assert statistics.median(vals)==2 and Fraction(sum(vals),25)==Fraction(56,25)
    assert sum(c for k,c in freq.items() if k>2)==10
    assert Fraction(240*20,100)==48 and round(100*Fraction(120,264))==45      # Q17
    assert Fraction(48+16,240+16)==Fraction(1,4)
    return total


if __name__ == "__main__":
    from pathlib import Path
    import sys
    base = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(base / "src"))
    from exam2 import questions
    print("independent math + scoring audit: %d points, 41 parts, 17 questions" % verify(questions.load()))
