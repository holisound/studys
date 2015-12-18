#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-11-29 22:49:59
# @Last Modified by:   edward
# @Last Modified time: 2015-12-18 14:51:04
from refundnotify import Refund
refund = Refund()
refund.set_many(
    partner='ppps',
    seller_email='only@win5.com.cn',
    # seller_user_id
    refund_date='2011-01-01 01:01',
    batch_no=9999,
    batch_num=50,
    detail_data='12345^3.33^no reason'
)
refund.do_sign('secret')
print refund.get_url()
# print refund.get_result()