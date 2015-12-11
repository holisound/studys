#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-12-07 10:40:40
# @Last Modified by:   edward
# @Last Modified time: 2015-12-07 15:46:36
from .utils import md5_sign, urlencode_params

class Ebank:
    GATEWAY = 'https://mapi.alipay.com/gateway.do'
    DATA = dict(
        service='create_direct_pay_by_user',
        _input_charset='utf-8',
        sign_type='MD5',
        notify_url='http://www.17dong.com.cn/payment/notify/',
        return_url='http://www.17dong.com.cn/payment/return/',
        payment_type='1',
        defaultbank='ICBCBTB', 
    )
    def __init__(self):
        self.data = self.DATA.copy()

    def _assert_requirement(self):
        assert sorted(self.data.keys()) == sorted([
                'partner',
                'seller_email',
                'sign',
                'out_trade_no',
                'subject',
                'total_fee',
                # ==========
                '_input_charset',
                'notify_url',
                'service',
                'sign_type',
                'return_url',
                'payment_type',
                'defaultbank',

            ]) and all(self.data.values())

    def do_sign(self, key):
        self.data['sign'] = md5_sign(self.data, key)

    def set_many(self, **kw):
        return self.data.update(kw)

    def get_url(self):
        self._assert_requirement()
        return ''.join([self.GATEWAY, '?', urlencode_params(self.data)])

    def get_result(self):
        return requests.get(self.get_url()).text