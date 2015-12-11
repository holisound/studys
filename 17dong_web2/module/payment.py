#!/usr/bin/env python
#-*-coding:utf-8-*-

import module.settings as Settings
from module.alipay import Alipay

_ALIPAY = Settings.ALIPAY

def direct_payment(payment_type, trade_no, subject, total_fee, return_url, notify_url, showurl=None):
    '''Drop the payment request to its corresponding payment method.'''

    if payment_type == "alipay":
        return _alipay(trade_no, subject, total_fee, return_url, notify_url)
    if payment_type == "alipay_wap":
        return _alipay_wap(trade_no, subject, total_fee, return_url, notify_url, showurl)
    else:
        return None

def _alipay(trade_no, subject, total_fee, return_url, notify_url):
    alipay = Alipay(_ALIPAY.get('PID'), _ALIPAY.get('KEY'), _ALIPAY.get('EMAIL'))
    payment_url = alipay.create_direct_pay_by_user_url(
        out_trade_no=trade_no,
        subject=subject,
        total_fee=total_fee,
        return_url=return_url,
        notify_url=notify_url)

    return payment_url

def _alipay_wap(trade_no, subject, total_fee, return_url, notify_url, showurl):
    alipay = Alipay(_ALIPAY.get('PID'), _ALIPAY.get('KEY'), _ALIPAY.get('EMAIL'))

    total_fee = "%.2f" % float(total_fee)
    payment_url = alipay.create_wap_direct_pay_by_user_url(
        out_trade_no=trade_no,
        subject=subject,
        total_fee=total_fee,
        return_url=return_url,
        notify_url=notify_url,
        show_url=showurl)

    return payment_url
