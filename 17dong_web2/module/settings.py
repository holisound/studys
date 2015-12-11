#!/usr/bin/env python
#-*-coding:utf-8-*-

import socket
import MySQLdb.cursors
import os
##############################################################################################################

SERVER_HOST_NAME        = "17dong.com.cn"

WILLSON_HOST_NAME       = "Willsons-iMac.local"

DEBUG_APP               = True # False if socket.gethostname() == SERVER_HOST_NAME else True

COOKIE_SECRET           = "IEMavmTpSwyXz0+b1oOHSbmwLTjTzUlJuMeJNZpl7pQ="

COOKIE_SECRET_BACKEND   = "rikItUadQX28Y8JCvylPd+289Uit5EWkiaQwuYUjBww="

DB_NAME                 = "17DONG"

DB_USER                 = "root"

DB_PASSWORD             = "v28so709" if (socket.gethostname() == SERVER_HOST_NAME or socket.gethostname() == WILLSON_HOST_NAME) else "123123"

DB_ARRAYCURSOR          = MySQLdb.cursors.Cursor

DB_DICTCURSOR           = MySQLdb.cursors.DictCursor

DB_CURSORCLASS          = DB_DICTCURSOR  # DB_ARRAYCURSOR if socket.gethostname() == SERVER_HOST_NAME else DB_DICTCURSOR  # Cursor / DictCursor

RSS_FEED_COUNT          = 50

LIST_ITEM_PER_PAGE      = 10                     # 每页列表中显示的条目最大数

COMMENT_ITEM_PER_PAGE   = 5                      # 每页评论显示的条目最大数

INITIAL_PARENT_CATEGORY = { "1" : "体育培训", "2" : "体育旅游", "3" : "课程体验", "4" : "精彩活动", "5" : "积分商城", "6" : "私人教练", "99" : "文章" }

EMPP_URL                = "http://sms.51sxun.com/sms.aspx"

EMPP_POST_PARAM         = { "action" : "send", "userid" : "156", "account" : "yingku", "password" : "yingku123", "sendTime" : "", "extno" : "" }

FULL_PERMISSION         = '''{ "User1"       : "A,D,V,U", "User2"    : "A,D,V,U", "User3"    : "A,D,V,U", 
                               "Product1"    : "A,D,V,U", "Product2" : "A,D,V,U", "Product3" : "A,D,V,U", "Product4" : "A,D,V,U", "Product5" : "A,D,V,U", "Product6" : "A,D,V,U", "Product7" : "A,D,V,U", 
                               "Category"    : "A,D,V,U", 
                               "Article"     : "A,D,V,U", 
                               "Ads"         : "A,D,V,U", 
                               "Order"       : "A,D,V,U", 
                               "Comment"     : "A,D,V,U",
                               "Coupon"      : "A,D,V,U",
                               "Vote"        : "A,D,V,U",
                               "Swordfight"  : "A,D,V,U",
                               "Promotion"   : "A,D,V,U",
                               "Competition" : "A,D,V,U",
                               "Message"     : "A,D,V,U",
                               "Keyword"     : "A,D,V,U",
                               "Links"       : "A,D,V,U" }'''

ADMIN_PERMISSION        = '''{ "User1"       : "A,V", "User2"    : "A,V", "User3"    : "A,V", 
                               "Product1"    : "A,V", "Product2" : "A,V", "Product3" : "A,V", "Product4" : "A,V", "Product5" : "A,V", "Product6" : "A,V", "Product7" : "A,V", 
                               "Category"    : "A,V", 
                               "Article"     : "A,V", 
                               "Ads"         : "A,V", 
                               "Order"       : "A,V", 
                               "Comment"     : "A,V", 
                               "Coupon"      : "A,V",
                               "Vote"        : "A,V",
                               "Swordfight"  : "A,V",
                               "Promotion"   : "A,V",
                               "Competition" : "A,V",
                               "Message"     : "A,V",
                               "Keyword"     : "A,V",
                               "Links"       : "A,V" }'''

VENDOR_PERMISSION       = '''{ "Product1" : "A,D,V,U", "Product2" : "A,D,V,U", "Product3" : "A,D,V,U", "Product4" : "A,D,V,U", "Product5" : "A,D,V,U", "Product6" : "A,D,V,U", "Product7" : "A,D,V,U", 
                               "Order"    : "V,U",
                               "Comment"  : "V" }'''

##############################################################################################################

JPUSH = { 
    "app_key" : "611debcba0f2677b86910354",
    "master_secret" : "065c2e83ca110b22e42aa667"
    }

##############################################################################################################

ALIPAY = {
    'PID'                     : '2088711406433982',
    'KEY'                     : '2ej4rmp4ipznr872960ks2gu6gfjpl2l',
    'EMAIL'                   : 'only@win5.com.cn', 

    'RSA_PRIVATE_KEY'        : '''-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQDAsLrFHrklol9FEpnPcDJbDqygupPl7wpW4TiaZ9pFrxN9FKty
x+s3riL72odREnW9NwlnqZBFfjHNxDJ8QJHzRclOiYAFvqJ0oVPYgYa2lsqBNwJf
zBXJZDtwxQAGC+zM/IY1bb5w1fPJcvdTKJR+q5bE/L6Lp4lND1ABXRBTBwIDAQAB
AoGAAhTmr6J5VZK/fLuKtdb8dEdgTgw19NH0RqQAPIrKrN4LU9qZT5AhVmSnNBlU
ROfyJa0miNwoFtgaKaLo+Lap3PYje7nRl9+LIpg9B3A/6UrCaJLmEpOMNMtIxsge
V14aIgbhEMxC2ocRIjGLg+Wz2Aoz2GF+zzNyG3SjAIDuFgECQQDgXtT0ZvZCGWKb
ipuy2K48ZM8wIU0D51rPjoNpgEvIFmUbDRnlUeWajmZ/r4Uptb3bifwMIpTKJLSX
OC420bJBAkEA29qdRRKp1R63IWcBC6ki3h8RAweXQhzz0777f0BGZgG/vaSdOQCB
3A+Y8TdfomYT9bItsrW/FsXllCGJaUkjRwJAbNMyQPSrnrXHUR/yktVr9RkEMRkF
zM3rCt7ZuFMk7oCGO4+oLsUBM2y8JFRSpz9iPdh4ar5fIoiZGvuB1s7wwQJAH7K4
ZCIZvHGOQ9GfE/hR36apBD/O7ihQe2IYzrMMs15jL8uRI4vQLVNOYND0B+0hyZXk
AtUzdOwZeq8PKc/ytwJBAKXyYQ6wrF1MIMGu4X/O0tYVzH/h6e8nBub5pOGyw1hZ
7b8Edzc3qdSIOJ/Sd/rdAzR9UFfRu6O6YRbYHsvvQvY=
-----END RSA PRIVATE KEY-----''',

    'ALIPAY_PUBLIC_KEY'      : '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnxj/9qwVfgoUh/y2W89L6BkRA
FljhNhgPdyPuBV64bfQNN1PjbCzkIM6qRdKBoLPXmKKMiFYnkd6rAoprih3/PrQE
B/VsW8OoM8fxn67UDYuyBTqA23MML9q1+ilIZwBC2AQ2UBVOrFXfFl75p6/B5Ksi
NG9zpgmLCUYuLkxpLQIDAQAB
-----END PUBLIC KEY-----''',

    'ALIPAY_TRANSPORT'        : 'http',
    'ALIPAY_GATEWAY'          : 'https://mapi.alipay.com/gateway.do?',
    'ALIPAY_HTTPS_VERIFY_URL' : 'https://mapi.alipay.com/gateway.do?service=notify_verify&',
    'ALIPAY_HTTP_VERIFY_URL'  : 'http://notify.alipay.com/trade/notify_query.do?',
    }

##############################################################################################################

LIANLIANPAY = {
    "oid_partner" : "201412151000133502",
    "key" : "201412151000133502_5975751363",

    "version" : "1.0",
    "userreq_ip" : "10.10.246.110",
    "id_type" : "0",
    "sign_type" : "MD5",
    "valid_order" : "30",
    "input_charset" : "utf-8",
    "transport" : "http",
    "llpay_gateway_new" : "https://yintong.com.cn/payment/bankgateway.htm",
    }

##############################################################################################################
# 微信支付

#=======【基本信息设置】=====================================
#微信公众号身份的唯一标识。审核通过后，在微信发送的邮件中查看
WX_APPID = "wx75e720a9c37aa258"
#JSAPI接口中获取openid，审核后在公众平台开启开发模式后可查看
WX_APPSECRET = "aed80adf8eb3b5169b6cb4121058e68f"

#受理商ID，身份标识
WX_MCHID = "1237581002"
#商户支付密钥Key。审核通过后，在微信发送的邮件中查看
WX_KEY = "iTCkH65rtkztlPP5GlBGABRgjHImrZrF"


#=======【异步通知url设置】===================================
#异步通知url，商户根据实际开发过程设定
WX_NOTIFY_URL = "http://www.17dong.com.cn/api/payment/wechat/notify"

#=======【JSAPI路径设置】===================================
#获取access_token过程中的跳转uri，通过跳转将code传入jsapi支付页面
WX_JS_API_CALL_URL = "http://******.com/pay/?showwxpaytitle=1"

#=======【证书路径设置】=====================================
#证书路径,注意应该填写绝对路径

WX_SSLCERT_PATH = os.path.join(os.path.dirname(__file__), 'wechat_cert/apiclient_cert.pem')
WX_SSLKEY_PATH = os.path.join(os.path.dirname(__file__), 'wechat_cert/apiclient_key.pem')

#=======【curl超时设置】===================================
WX_CURL_TIMEOUT = 30

#=======【HTTP客户端设置】===================================
WX_HTTP_CLIENT = "URLLIB"  # ("URLLIB", "CURL")

##############################################################################################################
# 微信登录

WX_LOGIN_APPID = "wxdf05016e6aa2a3b2"
WX_LOGIN_APPSECRET = "2ff425a3148dd96cae7f19072ddf215c"
##############################################################################################################