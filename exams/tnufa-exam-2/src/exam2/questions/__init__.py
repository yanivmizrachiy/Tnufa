# -*- coding: utf-8 -*-
"""The 17 items, one file each (text, figure, answer, rubric and the answer-key row KEY). load() returns them in exam order."""
import importlib


def load():
    qs = []
    for n in range(1, 18):
        mod = importlib.import_module(".q%02d" % n, __name__)
        qq = mod.build()
        assert qq.n == n, (qq.n, n)
        # the answer key lives in the same file as the question (single source): KEY[letter] = (answer, how)
        key = mod.KEY
        assert set(key) == {p.letter for p in qq.parts}, ("q%d: KEY letters" % n, sorted(key), [p.letter for p in qq.parts])
        for p in qq.parts:
            p.key, p.how = key[p.letter]
        qs.append(qq)
    return qs
