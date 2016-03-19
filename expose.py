#!/usr/bin/env python
#coding=utf-8


def expose(s, initial_length=1, step=1, expand=False, forward=False, max_length=None):
    def gen():
        start, stop = 0, initial_length
        s_length = len(s)
        if max_length is None or max_length > s_length:
            _max_length = s_length
        t = s[: stop]
        if expand:
            while stop < _max_length:
                while stop < _max_length:
                    yield t
                    stop += step
                    t = s[start: stop]
                if forward:
                    start += step
                    stop = start
            yield t[-1] if forward else t
        else:
            while stop < _max_length + 1:
                yield t
                start += step
                stop += step
                t = s[start : stop]

    return gen()

def test():
    sample01 = u"我的python世界"
    sample02 = u"我是一个pythoner"
    word_max_length = 10
    for i in tuple(expose(sample01, 1, expand=True)):
        print i
    for i in tuple(expose(sample02, 2,2, expand=False)):
        print i

if __name__ == "__main__":
    test()
