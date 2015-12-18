#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-11-29 21:13:29
# @Last Modified by:   edward
# @Last Modified time: 2015-12-18 14:48:12
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

# ====================

class Refund:
    GATEWAY = 'https://mapi.alipay.com/gateway.do'
    DATA = dict(
        service='refund_fastpay_by_platform_pwd',
        _input_charset='utf-8',
        sign_type='MD5',
        notify_url='http://www.17dong.com.cn',
    )
    def __init__(self):
        self.data = self.DATA.copy()

    def _assert_requirement(self):
        assert sorted(self.data.keys()) == sorted([
                '_input_charset',
                'batch_no',
                'batch_num',
                'detail_data',
                'notify_url',
                'partner',
                'refund_date',
                'seller_email',
                'service',
                'sign',
                'sign_type',
            ]) and all(self.data.values())

    def set_many(self, **kw):
        self.data.update(kw)

    def do_sign(self, key):
        self.data['sign'] = md5_sign(self.data, key)

    def get_url(self):
        self._assert_requirement()
        return ''.join([self.GATEWAY, '?', urlencode_params(self.data)])
