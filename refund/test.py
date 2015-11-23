#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: python
# @Date:   2015-11-23 15:18:54
# @Last Modified by:   python
# @Last Modified time: 2015-11-23 16:11:42
import web
from weixin import make_weixin_signatrue, make_xml_bunch, make_nonce_bunch

urls = (
    r'/test/xml/?', 'TestXML',
)

class TestXML:
    def GET(self):
        params = dict(
            appid='wxd930ea5d5a258f4f',
            mch_id='10000100',
            device_info='1000',
            body='test',
            nonce_str=make_nonce_bunch())
            
        signature = make_weixin_signatrue(
            mch_key = '192006250b4c09247ec02edce69f6a2d', # secret
            params=params,
            )

        xml = make_xml_bunch(params, sign=signature)
        web.header('content-type', 'text/xml')
        return xml

def main():
    app = web.application(urls, globals(), autoreload=True)
    app.run()

if __name__ == '__main__':
    main()
