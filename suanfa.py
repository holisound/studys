#!/usr/bin/env python
#coding=utf-8
import time
from functools import reduce
def reduce_func(x,y):
    """
    [x1,x2,x3...xn] => [x1,x1+x2,x1+x2+x3,...,x1+x2+x3...+xn]
    :param x:
    :param y:
    :return: list
    """
    if isinstance(x, (list,)):
        return x + [x[-1] + y]
    else:
        return [x, x+y]

def compare_exec(fns=[], *args, **kwargs):
    def timeit(fn):
        start = time.clock()
        fn(*args, **kwargs)
        end = time.clock()
        return '%.4f' % (end - start)
    if not isinstance(fns, list):
        fns = [fns]
    r = map(timeit, fns)
    print r
    return r


def get_id_validate_number(id17):
    weight = (7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2)
    assert len(weight) == 17
    validate = ('1','0','X','9','8','7','6','5','4','3','2')
    remain = sum( int(i) * int(w) for i, w, in zip(id17, weight)) % 11
    assert 0 <= remain <= 10
    return validate[remain]



if __name__ == '__main__':
    # ls = range(10**5)
    # compare_exec([
    #     lambda : reduce(reduce_func, ls),
        # lambda :[reduce(lambda x,y:x+y, ls[:i]) for i in range(1, len(ls))],
        # lambda :[sum(ls[:i]) for i in range(1, len(ls))]
    # ])
    print get_id_validate_number('53010219200508011')