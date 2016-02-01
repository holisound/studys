#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-12-06 09:42:12
# @Last Modified by:   edward
# @Last Modified time: 2016-02-01 22:58:31
import requests
from scrapy.selector import Selector
import os
import sys
# url = 'http://www.feixunvpn.com/page/testss.html'
url = 'https://www.freevpnss.org/'
body = requests.get(url, verify=False).content
#_xpath = '//div[@class="testvpnitem"]'
_xpath = '//div[@class="panel-body"]'
testvpnitems = Selector(text=body).xpath(_xpath).extract()
vpndetials = testvpnitems[3]
port, = Selector(text=vpndetials).re(u'端口：(\d+)')
#passwd, = Selector(text=vpndetials).re(u'密码：(\d+)')
passwd, = Selector(text=vpndetials).re(u'码：(\d+)')
# ip, encrpyt = Selector(text=vpndetials).xpath('//span/text()').extract()
print vpndetials
ip, = Selector(text=vpndetials).re(u'服务器地址：([\w\.]+)')
encrpyt, = Selector(text=vpndetials).re(u'加密方式：([\w-]+)')
local_port = 1987
timeout = 600
print ip
print encrpyt
# 
params = (ip, port, passwd, encrpyt, local_port, sys.argv[1], timeout)
launch = 'sslocal -s %s -p %s -k %s -m %s -l %s -d %s -t %s' % params
os.system(launch)
