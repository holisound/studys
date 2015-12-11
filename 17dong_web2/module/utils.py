#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-12-07 11:24:00
# @Last Modified by:   edward
# @Last Modified time: 2015-12-07 11:25:00
from hashlib import md5
from urllib import urlencode


def excludes(keys=(), values=()):
    def _decorator(f):
        def _func(params):
            _the_params = {
                k: v for (k, v) in params.items()
                if (k not in keys) and (v not in values)}
            return f(_the_params)
        return _func
    return _decorator


@excludes(keys=('sign', 'sign_type'), values=('',))
def link_params(params):
    return '&'.join('%s=%s' % (k, v) for (k, v) in sorted(params.items()))


@excludes(values=('',))
def urlencode_params(params):
    return urlencode(params)


def md5_sign(params, key):
    return md5(link_params(params) + key).hexdigest()