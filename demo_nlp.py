#!/usr/bin/env python
# coding=utf-8
import os
import re
from functools import  partial
from hashlib import md5
# def match_one(s, length=1):

def static_url_maker(debug=False):
    def static_url(filepath):
        prefix, filename = os.path.split(filepath)
        def minify(filename, debug=False):
            if '.' in filename and '.min.' not in filename and not debug:
                filename = filename.replace('.', '.min.')
            return filename
        url = os.path.join('static', prefix, minify(filename, debug))
        return url
    return static_url


class YukiNLP:

    def __init__(self, raw):
        self.raw = raw

    @staticmethod
    def get_unicode_one(chr, hex=False):
        text = repr(chr)
        # print text
        pattern = re.compile(r'\\u([0-9a-z]{4})')
        r = pattern.findall(text) or ['0']
        if not hex:
            r = map(lambda x: int(x, base=16), r)
        return r[0]

    def get_unicode_all(self, hex=False):
        _get_unicode_one = partial(self.get_unicode_one, hex=hex)
        r = tuple(map(_get_unicode_one, self.raw))
        return r

def expose(s, length=1, step=1):
    def gen():
        start, stop = 0, length
        t = s[start : stop]
        while len(t) == length:
            yield t
            start += step
            stop += step
            t = s[start : stop]

    return gen()


def words_count(s):
    pass

if __name__ == '__main__':
    # import config
    # files = ['angular.js', 'bootstrap.css', 'abc.min.css', 'css/abc.css']
    # static_url = static_url_maker(config.DEBUG)
    # print map(static_url, files)
    print YukiNLP.get_unicode_one(u'当地的和的风俗的aa',hex=True)
    words = u'你好,世界！'
    s = YukiNLP(words)
    print s.get_unicode_all()
    u"""
    1. 通过爬虫进行海量raw-data采集
    2. 中文字符从unicode数值上是线性关系(encoding:utf-8),计算相邻字符间的unicode差值(from data-analyze)
    a and b
    b and c
    a and c
    chr1 chr2 chr1u chr2u dvalue
    a    b    1111   2222  -1111
    b    a    2222   1111
    对大量自然语言文本进行分析之后，所得到的频次
    """
    words = u'我是一个中国人'
    hashed =  md5('hello,world').hexdigest().upper()
    # 遍历 for
    # 不使用遍历
    # 'set' version
    print tuple(expose(hashed, 2, 2))
    def words_count(text, to_match=None):
        def counter(word):
            return word, text.count(word)
        print text
        return dict(map(counter, to_match or cut_into_words(text, 2, 10)))
    # don't use 'set' which puts long-text into single character
    # sometimes need to count that not single character but words
    def cut_into_words(text, unit_length=1, step=1):
        return set(expose(text, unit_length, step))

    print words_count(hashed)

    # for i in tuple(expose(words,length=5)):
    #     print i



