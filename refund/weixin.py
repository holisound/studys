#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: python
# @Date:   2015-11-23 13:04:50
# @Last Modified by:   python
# @Last Modified time: 2015-11-23 18:23:53

from hashlib import md5
from xml.etree.ElementTree import Element, tostring, fromstring
import random


def prepare(f, *args, **kwargs):
    def _(params, **kws):
        mch_key = kws.pop('mch_key', None)
        p = params.copy()
        p.update(kws)
        nd = {k: v for k, v in p.items() if v != ''} # ignores empty string
        kv_pairs = sorted(nd.items(), key=lambda x:x[0]) # sorts by ascii 
        if mch_key is None:
            return f(kv_pairs)
        else:
            return f(mch_key, kv_pairs)
    return _        

@prepare
def make_weixin_signatrue(mch_key, params,**kws):
    """
    ====================================
    `weixin refund` signature algorithm
    ====================================
    *`mch_key`: str 
    *`params`: dict 
    """
    if hasattr(params, 'items'):
        params = params.items()
    stringA = '&'.join('%s=%s' % (k, v) for k, v in params) # concat
    stringSignTemp = stringA + '&key=' + mch_key # add key to it 
    signature = md5(stringSignTemp).hexdigest().upper() 
    return signature

@prepare
def make_xml_bunch(params, **kws):
    root = Element('xml')
    for k, v in params:
        child = Element(k)
        child.text = v
        root.append(child)
    return tostring(root)

def make_nonce_bunch(length=16):
    """
    length: int, the length of bunch expected, defaults to `16`, not more than `32`
    `nonce_bunch` algorithm to ensure the bunch is unpredictable
    """
    _num_range = []
    _num_range.extend(range(65, 91)) # A ~ Z (65-90) ascii
    _num_range.extend(range(97, 123)) # a ~ z (97-122) ascii
    _bunch_list = []
    while len(_bunch_list) < length:
        char = chr(random.choice(_num_range))
        _bunch_list.append(char)
    return ''.join(_bunch_list)
 
def xml_loads(xml_bunch):
    """
    xml_bunch: str ==> dict object
    >>> xml_loads("<xml><a>111</a><b>222</b></xml>")
    {'a': '111', 'b': '222'}
    """
    root = fromstring(xml_bunch)
    return {child.tag: child.text for child in root.getchildren()}

if __name__ == '__main__':
    import doctest
    doctest.testmod()
    params = dict(
        appid='wxd930ea5d5a258f4f',
        mch_id='10000100',
        device_info='1000',
        body='test',
        nonce_str='ibuaiVcKdpRxkhJA')
        
    signature = make_weixin_signatrue(
        mch_key = '192006250b4c09247ec02edce69f6a2d', # secret
        params=params,
        )

    print make_xml_bunch(params, sign=signature)

    print make_nonce_bunch()


