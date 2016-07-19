#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-05-19 14:37:44
# @Last Modified by:   edward
# @Last Modified time: 2016-07-19 09:20:54
import tornado.web
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import options, define
# ====================
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
    define('port', default=8000, help="run on the port", type=int)
    define('debug', default=False, help='run in debug mode', type=bool)
    options.parse_command_line()
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
        debug=options.debug,
        gzip=True,
        )
    server = HTTPServer(app)
    server.listen(options.port)
    print 'tornado launched!'
    IOLoop.current().start()
if __name__ == "__main__":
    main()
