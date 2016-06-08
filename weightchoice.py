#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-12-09 10:08:59
# @Last Modified by:   edward
# @Last Modified time: 2016-06-08 09:44:23
import random

class T:
    def WeightedChoice(self, choices):
        '''加权随机
            choices: 参数列表，格式：[("iPhone 6 Plus", 1), ("A box of Chocolate", 10), ("A Pencil", 33), ("Free Course of Training", 10), ("iPod Touch", 6), ("Thank you!", 40)]
        '''
        total = sum(w for c, w in choices)
        r = random.uniform(0, total)
        upto = 0
        for c, w in choices:
            if upto + w >= r:
                return c
            upto += w
        assert False, "Shouldn't get here"

    def TestWeightedChoice(self, price_pool, price_name):
        total = 0
        maxcount = 500000
        for i in range(maxcount):
            ret = self.WeightedChoice(price_pool)
            if ret == price_name:
                total += 1
        print "The %s probability is: %.2f%%" % (price_name, float(float(total) / float(maxcount)) * 100)

def main():
    PRIZE = [("iPhone 6 Plus", 100), ("A box of Chocolate", 1000), ("A Pencil", 3300), ("Free Course of Training", 1000), ("iPod Touch", 600), ("Thank you!", 4000)]
    t = T()
    t.TestWeightedChoice(PRIZE, PRIZE[0][0])
if __name__ == '__main__':
    main()