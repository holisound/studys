#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-12-06 09:42:12
# @Last Modified by:   edward
# @Last Modified time: 2015-12-06 10:43:12
import requests
from scrapy.selector import Selector
import os
url = 'http://www.feixunvpn.com/page/testss.html'
body = requests.get(url).content
_xpath = '//div[@class="testvpnitem"]'
testvpnitems = Selector(text=body).xpath(_xpath).extract()
vpndetials = testvpnitems[-1]
# 
# 服务器IP：45.32.69.222
# 端口：8501
# 密码：727394
# 加密方式：aes-256-cfb
# print vpndetials.encode('utf-8')
port, = Selector(text=vpndetials).re(u'端口：(\d+)')
passwd, = Selector(text=vpndetials).re(u'密码：(\d+)')
ip, encrpyt = Selector(text=vpndetials).xpath('//span/text()').extract()
local_port = 1987
timeout = 600
# 
params = (ip, port, passwd, encrpyt, local_port, timeout)
launch = 'sslocal -s %s -p %s -k %s -m %s -l %s -d restart -t %s' % params
os.system(launch)