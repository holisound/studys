# !/usr/bin/env python
# coding=utf-8
import sys,time
sys.path.append('/home/edward/lib/')
class Base:
    def __init__(self, a, b):
        self.val = a + b


class Child(Base):

    def __init__(self, *args, **kwargs):
        # 当super不可用时
        apply(Base.__init__, (self,) + args, kwargs)


def untie(a,b):
    return a + b

if __name__ == '__main__':
# # apply()用来传递参数，从子类传递到基类
#     c = Child(123,b=1456)
#     print c.val
# # apply()用来解包参数
#     arg = (1,)
#     kwarg = {'b': 2}
#     try:
#         assert apply(untie, arg, kwarg) == untie(*arg, **kwarg)
#     except AssertionError:
#         print 'failed'
#     else:
#         print 'successed'
    ss = set()
    ll = list()
    a=time.clock()
    for i in xrange(10**7):
        ll.extend([i])
    b=time.clock()
    for i in xrange(10**7):
        ss.update({i})
    c=time.clock()
    print (b-a)
    print (c-b)
