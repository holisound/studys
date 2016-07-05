#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-05-19 14:37:44
# @Last Modified by:   edward
# @Last Modified time: 2016-07-05 14:45:54
import tornado.web
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
# ====================
import sys
import os
# ====================

import config
# from app_handlers import handlers
# from db import DataBase
# from module.mysqldb import DbHelper
# from admin import handlers as admin_handlers
from test import handlers as test_handlers
# ====================


def main():
    # =====
    global_scope = globals()
    handlers = []
    for key in global_scope:
        if key.endswith('_handlers'):
            handlers.extend(global_scope[key])

    # =====
    class Main(tornado.web.Application):
        def __init__(self, *args, **kwargs):
            super(Main, self).__init__(*args, **kwargs)
            self.config = config
        @property
        def db(self):
            return DbHelper()
    app = Main(
        handlers, 
        cookie_secret='config.COOKIE_SECRET',
        login_url='/login',
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        xsrf_cookies=True,
        debug=False if len(sys.argv) > 1 else True,
        gzip=True,
        )

    if len(sys.argv) > 1:
        port = int(sys.argv[1].split('=')[1])
    else:
        port = 9999

    server = HTTPServer(app)
    server.listen(port)
    print 'tornado launched!'
    IOLoop.current().start()
if __name__ == "__main__":
    main()
