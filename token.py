#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-11-10 16:26:05
# @Last Modified by:   python
# @Last Modified time: 2015-11-10 18:28:06
__metaclass__ = type
import random

def sortit(iterable, key=None, reverse=False, reverse_key=None, conv=iter):
    """
    An alternative to 'sorted' which returns a sorted-iterator instead of a list.
    if 'reverse' is True, 'reverse_key' will be ignored.
    """
    if (reverse is False) and hasattr(reverse_key, '__call__'):
        _rev = reverse_key()
    else:
        _rev = reverse
    return conv(sorted(iterable, key=key, reverse=_rev))

def reverse(iterable, key=None):
    _it = iterable
    return sorted(iterable, key=key)
    
def token_formula(n):
    """
    n: 'str' or iterable contains 'str' objects
    """
    if hasattr(n, '__iter__'): 
        ls = n
    else:
        ls = [n]
    



# ==========
class Token:

    def __init__(self, *args):
        """
        args expects to collect 'str' object
        """
        self._init_token(*args)

    @property
    def value(self):
        return self.get_value()

    def get_value(self):
        return self._value

    def _init_token(self, *args):
        self._value = None
        if len(args) == 0:
            return
        elif len(args) == 1:

        else:
            pass


class AccessToken(Token):
    pass

class RefreshToken(Token):
    pass