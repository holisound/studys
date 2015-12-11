# -*- coding: utf-8 -*-
import requests
from hashlib import md5
try:
    from .exceptions import MissingParameter
    from .exceptions import ParameterValueError
    from .exceptions import TokenAuthorizationError
except Exception:
    MissingParameter = ParameterValueError = TokenAuthorizationError = Exception
import six
import time
import urllib
try:
    from ordereddict import OrderedDict
except ImportError:
    from collections import OrderedDict

if six.PY3:
    from urllib.parse import parse_qs, urlparse, unquote
else:
    from urlparse import parse_qs, urlparse, unquote
from xml.etree import ElementTree

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from Crypto import Signature
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_v1_5_Cipher
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Util import number
from Crypto.Util._number_new import ceil_div
import Crypto
import base64
import binascii
import os

import logging
logging.basicConfig(filename = os.path.join(os.getcwd(), 'log.txt'), level = logging.DEBUG)

################################################################################################################################################

def encode_dict(params):
    return params
    # return {k:six.u(v).encode('utf-8') if isinstance(v, str) else v.encode('utf-8') if isinstance(v, six.string_types) else v for k, v in six.iteritems(params)}

_private_rsa_key = None
_public_rsa_key = None
_public_rsa_key_ali = None

def module_init():
    module_path = os.path.dirname(__file__)
    priv_path = os.path.abspath(os.path.join(module_path, "rsa_private_key.pem"))
    pub_path = os.path.abspath(os.path.join(module_path, "rsa_public_key.pem"))
    pub_path_ali = os.path.abspath(os.path.join(module_path, "rsa_public_key_ali.pem"))

    prik = open(priv_path, "r").read()
    pubk = open(pub_path, "r").read()
    pubk_ali = open(pub_path_ali, "r").read()
    return (prik, pubk, pubk_ali)

_private_rsa_key, _public_rsa_key, _public_rsa_key_ali = module_init()
_public_rsa_key_ali = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnxj/9qwVfgoUh/y2W89L6BkRA
FljhNhgPdyPuBV64bfQNN1PjbCzkIM6qRdKBoLPXmKKMiFYnkd6rAoprih3/PrQE
B/VsW8OoM8fxn67UDYuyBTqA23MML9q1+ilIZwBC2AQ2UBVOrFXfFl75p6/B5Ksi
NG9zpgmLCUYuLkxpLQIDAQAB
-----END PUBLIC KEY-----'''

def stringToBase64(s):
    return base64.encodestring(s).replace("\n", "")

def base64ToString(s):
    try:
        return base64.decodestring(s)
    except binascii.Error, e:
        raise SyntaxError(e)
    except binascii.Incomplete, e:
        raise SyntaxError(e)

################################################################################################################################################

class Alipay(object):
    GATEWAY_URL = 'https://mapi.alipay.com/gateway.do'
    
    NOTIFY_GATEWAY_URL = 'https://mapi.alipay.com/gateway.do?service=notify_verify&partner=%s&notify_id=%s'

    def __init__(self, pid, key, seller_email):
        self.key = key
        self.pid = pid
        self.default_params = {'_input_charset': 'utf-8',
                               'partner': pid,
                               'seller_email': seller_email,
                               'payment_type': '1'}

    def _generate_md5_sign(self, params):
        src = '&'.join(['%s=%s' % (key, value) for key,
                        value in sorted(params.items())]) + self.key
        return md5(src.encode('utf-8')).hexdigest()

    def _generate_rsa_sign(self, params):
        src = '&'.join(['%s=%s' % (key, value) for key,
                        value in sorted(params.items())])
        return self.rsa_sign(src.encode('utf-8'))

    def rsa_sign(self, msg):
        key = RSA.importKey(_private_rsa_key)
        h = SHA.new(msg)
        signer = PKCS1_v1_5.new(key)
        signature = signer.sign(h)
        signature = stringToBase64(signature)
        return signature

    def check_with_rsa(self, msg, signature):
        signature = base64ToString(signature)
        key = RSA.importKey(_public_rsa_key)
        h = SHA.new(msg)
        verifier = PKCS1_v1_5.new(key)
        return verifier.verify(h, signature)

    def check_with_rsa_ali(self, msg, signature):
        signature = base64ToString(signature)
        key = RSA.importKey(_public_rsa_key_ali)
        h = SHA.new(msg)
        verifier = PKCS1_v1_5.new(key)
        return verifier.verify(h, signature)

    def _check_params(self, params, names):
        if not all(k in params for k in names):
            raise MissingParameter('missing parameters')
        return

    def getSignTuple(self):
        return ('sign_type', 'MD5', 'MD5')

    def getSignTupleForWAP(self):
        return ('sign_type', 'RSA', 'RSA')
    
    def signKey(self, signtype):
        return False

    def _build_url(self, service, **kw):
        params = self.default_params.copy()
        params['service'] = service
        if service == "alipay.wap.create.direct.pay.by.user":
            params.pop('seller_email', None)
            params['seller_id'] = params['partner']
            signkey, signvalue, signdescription = self.getSignTupleForWAP()
        else:
            signkey, signvalue, signdescription = self.getSignTuple()
        params.update(kw)
        signmethod = getattr(self, '_generate_%s_sign' %(signdescription.lower()))
        if signmethod == None:
            raise NotImplementedError("This type '%s' of sign is not implemented yet." %(signdescription))
        if self.signKey(signvalue):
            params.update({signkey: signvalue})
        params.update({signkey: signvalue, 'sign': signmethod(params)})

        if service == "alipay.wap.create.direct.pay.by.user":
            params = sorted(params.iteritems(), key=lambda d:d[0])

        return '%s?%s' % (self.GATEWAY_URL, urlencode(encode_dict(params)))

    def create_direct_pay_by_user_url(self, **kw):
        '''即时到帐'''
        self._check_params(kw, ['out_trade_no', 'subject'])

        if not kw.get('total_fee') and \
           not (kw.get('price') and kw.get('quantity')):
            raise ParameterValueError('total_fee or (price && quantiry)\
             must have one')

        url = self._build_url('create_direct_pay_by_user', **kw)
        return url

    def create_wap_direct_pay_by_user_url(self, **kw):
        '''Wap即时到帐'''
        self._check_params(kw, ['out_trade_no', 'subject'])

        if not kw.get('total_fee') and \
           not (kw.get('price') and kw.get('quantity')):
            raise ParameterValueError('total_fee or (price && quantiry)\
             must have one')

        url = self._build_url('alipay.wap.create.direct.pay.by.user', **kw)
        return url

    def create_partner_trade_by_buyer_url(self, **kw):
        '''担保交易'''
        names = ['out_trade_no', 'subject', 'logistics_type',
                 'logistics_fee', 'logistics_payment', 'price', 'quantity']
        self._check_params(kw, names)
        url = self._build_url('create_partner_trade_by_buyer', **kw)
        return url

    def trade_create_by_buyer_url(self, **kw):
        '''标准双接口'''
        names = ['out_trade_no', 'subject', 'logistics_type',
                 'logistics_fee', 'logistics_payment', 'price', 'quantity']
        self._check_params(kw, names)

        url = self._build_url('trade_create_by_buyer', **kw)
        return url
    
    def getSignMethod(self, **kw):
        signkey, signvalue, signdescription = self.getSignTuple()
        signmethod = getattr(self, '_generate_%s_sign' %(signdescription.lower()))
        if signmethod == None:
            raise NotImplementedError("This type '%s' of sign is not implemented yet." %(signdescription))
        return signmethod

    def getSignMethodWAP(self, **kw):
        signkey, signvalue, signdescription = self.getSignTupleForWAP()
        signmethod = getattr(self, '_generate_%s_sign' %(signdescription.lower()))
        if signmethod == None:
            raise NotImplementedError("This type '%s' of sign is not implemented yet." %(signdescription))
        return signmethod

    def verify_notify(self, **kw):
        sign = kw.pop('sign')
        try:
            signtype = kw.pop('sign_type')
        except KeyError:
            signtype = "MD5"

        if signtype == "RSA":
            msg = '&'.join(['%s=%s' % (key, value) for key, value in sorted(kw.items())])
            msg = msg.encode('utf-8')
            signature = sign
            if self.check_with_rsa_ali(msg, signature):
                return self.checkNotifyRemotely(**kw)
            else:
                return False
        else:
            signmethod = self.getSignMethod(**kw)
            if signmethod(kw) == sign:
                return self.checkNotifyRemotely(**kw)
            else:
                return False
        
    def checkNotifyRemotely(self, **kw):
        return requests.get(self.NOTIFY_GATEWAY_URL % (self.pid, kw['notify_id']), headers={'connection': 'close'}).text == 'true'

################################################################################################################################################

'''Wap支付接口'''
class WapAlipay(Alipay):
    GATEWAY_URL = 'http://wappaygw.alipay.com/service/rest.htm'
    TOKEN_ROOT_NODE = 'direct_trade_create_req'
    AUTH_ROOT_NODE = 'auth_and_execute_req'
    _xmlnode = '<%s>%s</%s>'

    def __init__(self, pid, key, seller_email):
        super(WapAlipay, self).__init__(pid, key, seller_email)
        self.seller_email = seller_email
        self.default_params = {'format': 'xml',
                               'v': '2.0',
                               'partner': pid,
                               '_input_charset': 'utf-8',
                               }
    
    def create_direct_pay_token_url(self, **kw):
        '''即时到帐token'''
        names = ['subject', 'out_trade_no', 'total_fee', 'seller_account_name',
                 'call_back_url', ]
        self._check_params(kw, names)
        req_data = ''.join([self._xmlnode % (key, value, key) for (key, value) in six.iteritems(kw)])
        req_data = self._xmlnode %(self.TOKEN_ROOT_NODE, req_data, self.TOKEN_ROOT_NODE)
        if '&' in req_data:
            raise ParameterValueError('character \'&\' is not allowed.')
        params = {'req_data': req_data, 'req_id': time.time()}
        url = self._build_url('alipay.wap.trade.create.direct', **params)
        return url
    
    def create_direct_pay_by_user_url(self, **kw):
        '''即时到帐'''
        if 'token' not in kw:
            url = self.create_direct_pay_token_url(**kw)
            alipayres = requests.post(url, headers={'connection': 'close'}).text
            params = parse_qs(urlparse(alipayres).path, keep_blank_values=True)
            if 'res_data' in params:
                tree = ElementTree.ElementTree(ElementTree.fromstring(unquote(params['res_data'][0])))
                token = tree.find("request_token").text
            else:
                raise TokenAuthorizationError(unquote(params['res_error'][0]))
        else:
            token = kw['token']
        params = {'req_data': self._xmlnode %(self.AUTH_ROOT_NODE, (self._xmlnode %('request_token', token,'request_token')) , self.AUTH_ROOT_NODE)}
        url = self._build_url('alipay.wap.auth.authAndExecute', **params)
        return url
    
    def getSignTuple(self):
        return ('sec_id', 'MD5', 'MD5')
        
    def trade_create_by_buyer_url(self, **kw):
        raise NotImplementedError("This type of pay is not supported in wap.")
    
    def create_partner_trade_by_buyer_url(self, **kw):
        raise NotImplementedError("This type of pay is not supported in wap.")
    
    def signKey(self):
        return True
    
    def checkNotifyRemotely(self, **kw):
        if 'notify_data' in kw:
            notifydata = unquote(kw['notify_data'])
            notifydata = six.u(notifydata).encode('utf-8') if isinstance(notifydata, str) else notifydata.encode('utf-8') if isinstance(notifydata, six.string_types) else notifydata
            tree = ElementTree.ElementTree(ElementTree.fromstring(notifydata))
            return super(WapAlipay, self).checkNotifyRemotely(**{'notify_id': tree.find("notify_id").text})
        return True
    
    def _generate_md5_notify_sign(self, kw):
        newpara = OrderedDict()
        newpara['service'] = kw['service']
        newpara['v'] = kw['v']
        newpara['sec_id'] = kw['sec_id']
        newpara['notify_data'] = kw['notify_data']
        src = '&'.join(['%s=%s' % (key, value) for key,
                        value in newpara.items()]) + self.key
        return md5(src.encode('utf-8')).hexdigest()
    
    def getSignMethod(self, **kw):
        if 'notify_data' in kw:
            signkey, signvalue, signdescription = self.getSignTuple()
            signmethod = getattr(self, '_generate_%s_notify_sign' %(signdescription.lower()))
            if signmethod == None:
                raise NotImplementedError("This type '%s' of sign is not implemented yet." %(signdescription))
            return signmethod
        return super(WapAlipay, self).getSignMethod(**kw)

def includeme(config):
    settings = config.registry.settings
    config.registry['alipay'] = Alipay(
        pid=settings.get('alipay.pid'),
        key=settings.get('alipay.key'),
        seller_email=settings.get('alipay.seller_email'))

################################################################################################################################################

class Refund:
    """
    service 接口名称    String  接口名称。   不可空 refund_fastpay_by_platform_pwd
    partner 合作者身份ID String(16)  签约的支付宝账号对应的支付宝唯一用户号。以2088开头的16位纯数字组成。   不可空 2088101008267254
    _input_charset  参数编码字符集 String  商户网站使用的编码格式，如utf-8、gbk、gb2312等。 不可空 GBK
    sign_type   签名方式    String  DSA、RSA、MD5三个值可选，必须大写。  不可空 MD5
    sign    签名  String  请参见签名。  不可空 tphoyf4aoio5e6zxoaydjevem2c1s1zo
    notify_url  服务器异步通知页面路径 String(200) 支付宝服务器主动通知商户网站里指定的页面http路径。 可空    
    seller_email    卖家支付宝账号 String  如果卖家Id已填，则此字段可为空。   不可空 Jier1105@alitest.com
    seller_user_id  卖家用户ID  String  卖家支付宝账号对应的支付宝唯一用户号。以2088开头的纯16位数字。登录时，。   不可空 2088101008267254
    refund_date 退款请求时间  String  退款请求的当前时间。格式为：yyyy-MM-dd hh:mm:ss。  不可空 2011-01-12 11:21:00
    batch_no    退款批次号   String  每进行一次即时到账批量退款，都需要提供一个批次号，通过该批次号可以查询这一批次的退款交易记录，对于每一个合作伙伴，传递的每一个批次号都必须保证唯一性。格式为：退款日期（8位）+流水号（3～24位）。不可重复，且退款日期必须是当天日期。流水号可以接受数字或英文字符，建议使用数字，但不可接受“000”。  不可空 201101120001
    batch_num   总笔数 String  即参数detail_data的值中，“#”字符出现的数量加1，最大支持1000笔（即“#”字符出现的最大数量为999个）。   不可空 1
    detail_data 单笔数据集   String  退款请求的明细数据。格式详情参见下面的“单笔数据集参数说明”。 不可空 2011011201037066^5.00^协商退款
    单笔数据集参数说明
    单笔数据集格式为：第一笔交易退款数据集#第二笔交易退款数据集#第三笔交易退款数据集…#第N笔交易退款数据集；
    交易退款数据集的格式为：原付款支付宝交易号^退款总金额^退款理由；
    不支持退分润功能。
    单笔数据集（detail_data）注意事项
    detail_data中的退款笔数总和要等于参数batch_num的值；
    “退款理由”长度不能大于256字节，“退款理由”中不能有“^”、“|”、“$”、“#”等影响detail_data格式的特殊字符；
    detail_data中退款总金额不能大于交易总金额；
    一笔交易可以多次退款，退款次数最多不能超过99次，需要遵守多次退款的总金额不超过该笔交易付款金额的原则。
    """
    refund_fastpay_by_platform_pwd_service = 'refund_fastpay_by_platform_pwd'
    refund_fastpay_by_platform_pwd_partner = '' #
    refund_fastpay_by_platform_pwd__input_charset = 'utf-8'
    refund_fastpay_by_platform_pwd_sign_type = 'MD5' #
    refund_fastpay_by_platform_pwd_notify_url = 'http://test'
    refund_fastpay_by_platform_pwd_seller_email = '' 
    # refund_fastpay_by_platform_pwd_seller_user_id = '' 
    refund_fastpay_by_platform_pwd_refund_date = ''
    refund_fastpay_by_platform_pwd_batch_no = ''
    refund_fastpay_by_platform_pwd_batch_num = ''
    refund_fastpay_by_platform_pwd_key = '' #
    refund_fastpay_by_platform_pwd_reason = "" #
    gateway = 'https://mapi.alipay.com/gateway.do'

    def __init__(self, refund_list):
        self.refund_list = refund_list

    def assert_hash_params(self):
        assert self.attr('key')
        requires = ['service', 'partner', '_input_charset', 
                    'notify_url', 'seller_email',
                    'refund_date', 'batch_no', 'batch_num']
        for x,y in zip(sorted(self.hash_params),sorted(requires)) :
            if x != y:
                raise Exception('%r != %r' % (x,y))
    @property
    def sign(self):
        self.assert_hash_params()
        signature = self._generate_md5_sign(self.hash_params)
        return signature

    def group(self):
        return '&'.join('%s=%s' % (k,v) for (k,v) in sorted(self.hash_params.items()))
    
    def _generate_md5_sign(self, params):
        src = '&'.join(['%s=%s' % (key, value) for key,
                        value in sorted(params.items())]) + self.attr('key')
        return md5(src.encode('utf-8')).hexdigest()

    def attr(self, name, value=None):
        if value is None:
             return getattr(self, 'refund_fastpay_by_platform_pwd_%s' % name, None)
        else:
            setattr(self,'refund_fastpay_by_platform_pwd_%s' % name, value)


    @property
    def param_names(self):
        return tuple(i[31:] for i in dir(self) if str(i).startswith('refund_fastpay_by_platform_pwd'))

    @property
    def param_dict(self):
        d = {}
        for name in self.param_names:
            attr = self.attr(name)
            if bool(attr):
                d[name] = attr
        return d

    @property
    def hash_params(self):
        return {k:v for k,v in self.param_dict.items() if k not in ('sign_type', 'sign','key','reason')}

    def get_url(self):
        params = self.hash_params
        params['sign'] = self.sign
        params['sign_type'] = self.attr('sign_type')
        params['detail_data'] = self.detail_data_set
        return '%s?%s' % (self.gateway, urlencode(params))


    @staticmethod
    def make_detail_data(outtradeno, outrefundfee, outrefundreason):
        """
        Method to make 'detail_data' for AlipayRefund
        2011011201037066^5.00^协商退款
        1. detail_data中的退款笔数总和要等于参数batch_num的值；
        2.“退款理由”长度不能大于256字节，“退款理由”中不能有“^”、“|”、“$”、“#”等影响detail_data格式的特殊字符；
        3. detail_data中退款总金额不能大于交易总金额；
        4. 一笔交易可以多次退款，退款次数最多不能超过99次，需要遵守多次退款的总金额不超过该笔交易付款金
        format: 2011011201037066^5.00^协商退款  outtradeno^outrefundfee^outrefundreason
        """
        return '^'.join(str(i) for i in [outtradeno, outrefundfee, outrefundreason])

    @staticmethod
    def extract_params(dictobj, keys=[]):

        return [dictobj.get(k) for k in keys]

    @property
    def detail_data_set(self):
        """
        fullprice preorder_fullprice
        orf out_refund_fee
        otn preorder_outtradeno
        reason 
        """
        _set = set()
        params = ['preorder_fullprice', 'out_refund_fee', 'preorder_outtradeno']
        for (fullprice, orf, otn) in [self.extract_params(r, params) for r in self.refund_list]:
            orf = orf if (0 < orf < fullprice) else fullprice
            _set.add(self.make_detail_data(otn, orf, self.attr('reason')))
        return '#'.join(_set)
