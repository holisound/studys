#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-11-29 21:13:29
# @Last Modified by:   edward
# @Last Modified time: 2015-12-10 16:17:58
from .utils import md5_sign, urlencode_params
    
class Refund:
    GATEWAY = 'https://mapi.alipay.com/gateway.do'
    DATA = dict(
        service='refund_fastpay_by_platform_pwd',
        _input_charset='utf-8',
        sign_type='MD5',
        notify_url='http://www.17dong.com.cn/alipay/batchrefund/notify/',
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

    def do_sign(self, key):
        self.data['sign'] = md5_sign(self.data, key)

    def get_url(self):
        self._assert_requirement()
        return ''.join([self.GATEWAY, '?', urlencode_params(self.data)])

