# -*- coding: utf-8 -*-
"""The 17 items, one file each. load() returns them in exam order."""
import importlib


def load():
    qs = []
    for n in range(1, 18):
        mod = importlib.import_module(".q%02d" % n, __name__)
        qq = mod.build()
        assert qq.n == n, (qq.n, n)
        qs.append(qq)
    return qs
