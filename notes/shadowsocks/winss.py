#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-12-06 09:42:12
# @Last Modified by:   edward
# @Last Modified time: 2016-02-01 23:03:56
import urllib
import os
import sys
import re

class FreeSS:

    timeout = 600
    local_port = 1987
    urls = [
        # 'http://www.feixunvpn.com/page/testss.html',
        'https://www.freevpnss.org/'
    ]
    def __init__(self):
        for url in self.urls:
            resp = urllib.urlopen(url)
            if resp.code == 200:
                self.html = resp.read()
                break

    def get_params(self):
        _params = list(self._ext_params())
        if all(_params):
            _params.extend([self.local_port, self.timeout])
            return _params
        else:
            raise Exception('invalid parameter!')

    def _ext_params(self):
        pat_ip = re.compile(r'服务器地址：([\w\.]+)')
        pat_port = re.compile(r'端口：(\d+)')
        pat_passwd = re.compile(r'密.*码：(\d+)')
        pat_encrypt = re.compile(r'加密方式：([\w-]+)')
        html = self.html
        ip = pat_ip.search(html)
        port = pat_port.search(html)
        passwd = pat_passwd.search(html)
        encrypt = pat_encrypt.search(html)
        for i in (ip, port, passwd, encrypt):
            yield i.group(1) if i else i

if __name__ == '__main__':
    params = FreeSS().get_params()
    launch = 'sslocal -s %s -p %s -k %s -m %s -l %s -t %s' % tuple(params)
    os.system(launch)
