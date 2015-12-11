#!/usr/bin/env python
#-*-coding:utf-8-*-

######################################################################################################################
#    Reference  Alipay Dualfun API
#    Author     Willson
#    Email      willson.zhang1220@gmail.com
#    Date       2013-08-03 00:44
######################################################################################################################

import os
import urllib
import urllib2
import hashlib
import settings
import logging
import requests

try:
    from ordereddict import OrderedDict as orderdict
except ImportError:
    from collections import OrderedDict as orderdict

if settings.DEBUG_APP:
    logging.basicConfig(filename = os.path.join(os.getcwd(), 'log.txt'), level = logging.DEBUG)

######################################################################################################################

def signParam(adict):
    newdict = {}
    for i in adict:
        if (i == "sign") or (adict[i] == ""):
            continue
        else:
            newdict[i] = adict[i]
    newdict = orderdict(sorted(newdict.items()))

    signstring = ""
    for k in newdict:
        v = newdict[k]
        if v != '':
            signstring += '%s=%s&' % (k, v)
    signstring += ("key=%s" % settings.LIANLIANPAY["key"])
    # signstring = signstring[:-1] + settings.LIANLIANPAY["key"]

    # logging.debug("---------------------------------- signstring: %r" % signstring)

    m = hashlib.md5(signstring)
    m.digest()
    md5signstr = m.hexdigest()

    # logging.debug("---------------------------------- md5signstr: %r" % md5signstr)

    return md5signstr

def create_payment(parameter):
    # logging.debug("---------------------------------- parameter: %r" % parameter)

    signstr = signParam(parameter)
    parameter['sign'] = signstr
    parameter['sign_type'] = settings.LIANLIANPAY["sign_type"]

    # logging.debug("---------------------------------- parameter: %r" % parameter)

    sHtml  = "<form id='llpaysubmit' name='llpaysubmit' action='%s' method='post'>" % settings.LIANLIANPAY["llpay_gateway_new"]
    if parameter.has_key("version") and parameter["version"] is not None:
        sHtml += "<input type='hidden' name='version' value='%s'/>" % parameter["version"]
    if parameter.has_key("oid_partner") and parameter["oid_partner"] is not None:
        sHtml += "<input type='hidden' name='oid_partner' value='%s'/>" % parameter["oid_partner"]
    if parameter.has_key("user_id") and parameter["user_id"] is not None:
        sHtml += "<input type='hidden' name='user_id' value='%s'/>" % parameter["user_id"]
    if parameter.has_key("timestamp") and parameter["timestamp"] is not None:
        sHtml += "<input type='hidden' name='timestamp' value='%s'/>" % parameter["timestamp"]
    if parameter.has_key("sign_type") and parameter["sign_type"] is not None:
        sHtml += "<input type='hidden' name='sign_type' value='%s'/>" % parameter["sign_type"]
    if parameter.has_key("sign") and parameter["sign"] is not None:
        sHtml += "<input type='hidden' name='sign' value='%s'/>" % parameter["sign"]
    if parameter.has_key("busi_partner") and parameter["busi_partner"] is not None:
        sHtml += "<input type='hidden' name='busi_partner' value='%s'/>" % parameter["busi_partner"]
    if parameter.has_key("no_order") and parameter["no_order"] is not None:
        sHtml += "<input type='hidden' name='no_order' value='%s'/>" % parameter["no_order"]
    if parameter.has_key("dt_order") and parameter["dt_order"] is not None:
        sHtml += "<input type='hidden' name='dt_order' value='%s'/>" % parameter["dt_order"]
    if parameter.has_key("name_goods") and parameter["name_goods"] is not None:
        sHtml += "<input type='hidden' name='name_goods' value='%s'/>" % parameter["name_goods"]
    if parameter.has_key("info_order") and parameter["info_order"] is not None:
        sHtml += "<input type='hidden' name='info_order' value='%s'/>" % parameter["info_order"]
    if parameter.has_key("money_order") and parameter["money_order"] is not None:
        sHtml += "<input type='hidden' name='money_order' value='%s'/>" % parameter["money_order"]
    if parameter.has_key("notify_url") and parameter["notify_url"] is not None:
        sHtml += "<input type='hidden' name='notify_url' value='%s'/>" % parameter["notify_url"]
    if parameter.has_key("url_return") and parameter["url_return"] is not None:
        sHtml += "<input type='hidden' name='url_return' value='%s'/>" % parameter["url_return"]
    if parameter.has_key("userreq_ip") and parameter["userreq_ip"] is not None:
        sHtml += "<input type='hidden' name='userreq_ip' value='%s'/>" % parameter["userreq_ip"]
    if parameter.has_key("url_order") and parameter["url_order"] is not None:
        sHtml += "<input type='hidden' name='url_order' value='%s'/>" % parameter["url_order"]
    if parameter.has_key("valid_order") and parameter["valid_order"] is not None:
        sHtml += "<input type='hidden' name='valid_order' value='%s'/>" % parameter["valid_order"]
    if parameter.has_key("bank_code") and parameter["bank_code"] is not None:
        sHtml += "<input type='hidden' name='bank_code' value='%s'/>" % parameter["bank_code"]
    if parameter.has_key("pay_type") and parameter["pay_type"] is not None:
        sHtml += "<input type='hidden' name='pay_type' value='%s'/>" % parameter["pay_type"]
    if parameter.has_key("no_agree") and parameter["no_agree"] is not None:
        sHtml += "<input type='hidden' name='no_agree' value='%s'/>" % parameter["no_agree"]
    if parameter.has_key("shareing_data") and parameter["shareing_data"] is not None:
        sHtml += "<input type='hidden' name='shareing_data' value='%s'/>" % parameter["shareing_data"]
    if parameter.has_key("risk_item") and parameter["risk_item"] is not None:
        sHtml += "<input type='hidden' name='risk_item' value='%s'/>" % parameter["risk_item"]
    if parameter.has_key("id_type") and parameter["id_type"] is not None:
        sHtml += "<input type='hidden' name='id_type' value='%s'/>" % parameter["id_type"]
    if parameter.has_key("id_no") and parameter["id_no"] is not None:
        sHtml += "<input type='hidden' name='id_no' value='%s'/>" % parameter["id_no"]
    if parameter.has_key("acct_name") and parameter["acct_name"] is not None:
        sHtml += "<input type='hidden' name='acct_name' value='%s'/>" % parameter["acct_name"]
    if parameter.has_key("flag_modify") and parameter["flag_modify"] is not None:
        sHtml += "<input type='hidden' name='flag_modify' value='%s'/>" % parameter["flag_modify"]
    if parameter.has_key("card_no") and parameter["card_no"] is not None:
        sHtml += "<input type='hidden' name='card_no' value='%s'/>" % parameter["card_no"]
    if parameter.has_key("back_url") and parameter["back_url"] is not None:
        sHtml += "<input type='hidden' name='back_url' value='%s'/>" % parameter["back_url"]
    sHtml += "<input type='submit' value='' style='display: none;'></form>"
    sHtml += "<script>document.forms['llpaysubmit'].submit();</script>"

    # logging.debug("---------------------------------- sHtml: %r" % sHtml)

    return sHtml

########################################################################################################################
