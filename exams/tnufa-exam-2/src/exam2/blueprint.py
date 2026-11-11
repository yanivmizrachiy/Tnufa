# -*- coding: utf-8 -*-
"""The locked plan the items are checked against (SOURCE_OF_TRUTH.md §3)."""

PLAN = {
    "questions": 17,
    "points": 100,
    "minutes_total": 90,
    "minutes_solving": 80,
    "domains": {"numbers": 15, "algebra": 40, "geometry": 30, "data": 15},
    "thinking": {"knowledge": 10, "algorithmic": 28, "process": 42, "open": 20},
    "literacy": 25,                 # approximate target, inside the 100
    "min_representation_transitions": 7,
    "min_reasoning_questions": 4,
    "min_critique_questions": 1,
    "min_strategy_questions": 1,
}


def actual(qs):
    from collections import Counter
    dom, th = Counter(), Counter()
    reps = 0
    for q in qs:
        dom[q.domain] += q.points
        reps += len(q.representations)
        for p in q.parts:
            th[p.thinking] += p.points
    return {
        "questions": len(qs),
        "points": sum(q.points for q in qs),
        "items": sum(len(q.parts) for q in qs),
        "minutes_solving": sum(q.minutes for q in qs),
        "domains": dict(dom),
        "thinking": dict(th),
        "literacy": sum(q.points for q in qs if q.literacy),
        "representation_transitions": reps,
        "reasoning_questions": sum(1 for q in qs if any(p.reasoning_credit for p in q.parts)),
        "critique_questions": sum(1 for q in qs if q.critique),
        "strategy_questions": sum(1 for q in qs if q.strategy),
    }


def blueprint(qs):
    from .model import DOMAIN_HE, THINKING_HE, DIFFICULTY_HE
    rows = []
    for q in qs:
        rows.append({
            "n": q.n, "domain": q.domain, "domain_he": DOMAIN_HE[q.domain], "topic": q.topic, "skill": q.skill,
            "claim": q.claim, "evidence": q.evidence, "task": q.task, "difficulty": q.difficulty,
            "difficulty_he": DIFFICULTY_HE[q.difficulty], "representations": q.representations,
            "literacy": q.literacy, "critique": q.critique, "strategy": q.strategy, "minutes": q.minutes,
            "points": q.points, "depends": q.depends, "figure": "<figure" in q.stem or any("<figure" in p.html for p in q.parts),
            "accessibility": q.accessibility, "reference": q.reference,
            "parts": [{"letter": p.letter, "points": p.points, "thinking": p.thinking, "thinking_he": THINKING_HE[p.thinking],
                       "reasoning_credit": p.reasoning_credit, "carry": bool(p.carry)} for p in q.parts],
        })
    return {"plan": PLAN, "actual": actual(qs), "questions": rows}
