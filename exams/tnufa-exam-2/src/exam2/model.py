# -*- coding: utf-8 -*-
"""Data model of one exam item. Every question file (questions/qNN.py) returns a Question.

The student text, the solution and the rubric of one question live together in one file,
so a change to the wording and a change to the key are made in the same place.
"""
from dataclasses import dataclass
from typing import Callable, List, Tuple

DOMAINS = ("numbers", "algebra", "geometry", "data")
DOMAIN_HE = {"numbers": "מספרי", "algebra": "אלגברי", "geometry": "גאומטרי", "data": "נתונים ואי־ודאות"}
THINKING = ("knowledge", "algorithmic", "process", "open")
THINKING_HE = {"knowledge": "ידע וזיהוי", "algorithmic": "חשיבה אלגוריתמית",
               "process": "חשיבה תהליכית", "open": "חיפוש פתוח / הנמקה / ביקורת"}
DIFFICULTY_HE = {"low": "נמוכה", "mid": "בינונית", "high": "גבוהה"}


@dataclass
class Part:
    letter: str                      # "א", "ב"... or "" when the question has one part
    points: int
    thinking: str                    # one of THINKING
    html: str                        # student-facing markup (text, options, work box, answer line)
    answer: str                      # short answer (HTML)
    solution: str                    # full solution for the teacher (HTML)
    rubric: List[Tuple[int, str]]    # [(points, criterion)] from full credit down to 0
    alternatives: str = ""           # other valid routes
    errors: str = ""                 # expected errors and what they diagnose
    carry: str = ""                  # follow-through rule when an earlier part is wrong
    reasoning_credit: bool = False   # points are given for the explanation / method itself

    def __post_init__(self):
        assert self.thinking in THINKING, self.thinking
        assert self.rubric and self.rubric[0][0] == self.points, (self.letter, self.points, self.rubric)
        assert self.rubric[-1][0] == 0, "rubric must end with the 0-point row"


@dataclass
class Question:
    n: int
    domain: str
    topic: str                       # short topic line (teacher table)
    skill: str                       # curriculum skill measured
    claim: str                       # Claim: what a correct answer lets us say about the student
    evidence: str                    # Evidence: what in the work counts as evidence
    task: str                        # Task model: what the student actually has to do
    difficulty: str                  # low / mid / high
    representations: List[str]       # representation transitions in the item
    literacy: bool                   # real-world modelling item (counts toward the ~25 literacy points)
    minutes: int                     # planned solving time
    stem: str                        # HTML before the parts (context, figure, givens)
    parts: List[Part]
    reference: str                   # nearest reference item and the structural differences from it
    accessibility: str               # reading load, figure, calculator notes
    notes: str                       # teaching notes after the exam
    check: Callable[[], None]        # asserts that recompute every value in the key
    depends: str = ""                # dependency between parts, if any
    critique: bool = False           # the item asks the student to judge a claim
    strategy: bool = False           # the student must choose a method with no fixed procedure

    def __post_init__(self):
        assert self.domain in DOMAINS, self.domain
        assert self.difficulty in DIFFICULTY_HE
        letters = [p.letter for p in self.parts]
        assert len(letters) == len(set(letters)), letters

    @property
    def points(self):
        return sum(p.points for p in self.parts)

    @property
    def student_html(self):
        """The whole question as the student sees it."""
        from . import html as H
        body = self.stem
        for p in self.parts:
            body += H.part(p.letter, p.html) if p.letter else p.html
        return H.q(self.n, body)
