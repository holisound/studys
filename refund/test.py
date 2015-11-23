#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: python
# @Date:   2015-11-23 15:18:54
# @Last Modified by:   python
# @Last Modified time: 2015-11-23 19:01:39
import web
from weixin import make_weixin_signatrue, make_xml_bunch, make_nonce_bunch, xml_loads
web.config.debug = True

urls = (
    r'/handle/xml/?', 'HandleXML',
)

class HandleXML:
    def POST(self):
        print web.ctx
        params = xml_loads(web.data())
            
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
