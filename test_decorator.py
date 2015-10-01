# coding=utf-8
# 主题:测试python装饰器的一些特性


def dec2(f,s=''):
    print s
    print 'dec2'
    return lambda x: 'Bye, %s' % x


def dec(f):
    print 'inside dec'
    print f('call')
    return lambda x: 'Hello, %s' % x


@dec2
@dec
def greet_dec(s):
    return "hi, %s with decorator." % s


def greet(s):
    return 'hi, %s without decorator.' % s
# 什么装饰器decorator(@dec)?(对lambda并不适用)
# 它运用了一种优雅的语法,但说到底是还是一个函数
# <--使用装饰器-->
>>> @dec
... def greet_dec(s):
... return "hi, %s with decorator." % s
...
inside dec
hi, call with decorator.
# 居然输出了内容？很显然，装饰器被调用了。
# 在调用greet_dec之前, 也就是在给greet_dec声明@dec的时候。装饰器就已经起作用了。
>>> greet_dec('Edward')
'Hello, Edward'
# 解释器没有像之前那样输出内容,说明@dec并没有再次被调用。
# 在调用greet_dec之后，@dec并没被调用，那么@dec到底怎么起作用的呢？
# 假设@dec的确接受了greet_dec作为参数并被解释器所调用，那么@dec作为一个函数它的返回结果去哪了呢？
# 有一种可能性是，@dec仅仅在加载脚本的时候才起作用，而@dec改变的不是别的而是greet_dec的命名空间所指向的函数对象。
# 而@dec恰恰是通过返回一个callable()的对象来替换原来greet_dec的命名空间所指向的函数对象。
# 这下就应该能解释的通，为什么@dec没有被调用，但是仍然改变了greet_dec的输出结果了吧？
# 包裹函数的最内层的@dec优先被执行
# 在有多个@dec的情况下，最外层的@dec返回callable()对象将作为greet_dec函数的替代品
# 值得注意的是,多个@dec之间是相互独立的, 它们的执行结果是互不影响的
# 它们的共同点是, 它们都接收一个叫做greet的函数作为参数



