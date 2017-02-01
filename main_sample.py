#!/usr/bin/env python
import logging
import sys
import uuid
from os import path

import tornado.web
from jinja2 import Environment, FileSystemLoader
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import options, define

import freess

reload(sys)
sys.setdefaultencoding("utf-8")
base_path = path.dirname(__file__)
logging.basicConfig(filename=path.join(base_path, 'log.txt'), level=logging.INFO)


class JinjaLoader(object):
    def __init__(self, template_path):
        self.template_path = template_path
        self.jinja_env = None
        self.template = None

    def generate(self, **context):
        if self.template is None:
            return
        template = self.template
        self.template = None
        return template.render(context)

    def load(self, template_name):
        if self.jinja_env is None:
            jinja_env = Environment(
                loader=FileSystemLoader(self.template_path),
                trim_blocks=True,
                extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols", ])
            self.jinja_env = jinja_env
        else:
            jinja_env = self.jinja_env
        self.template = jinja_env.get_template(template_name)
        return self


def add_url_prefix(handlers, url_prefix):
    ret = []
    for handler in handlers:
        tmp = list(handler)
        tmp[0] = url_prefix + tmp[0]
        ret.append(tuple(tmp))
    return ret


def main():
    define('port', default=8000, help="run on the port", type=int)
    define('debug', default=False, help='run in debug mode', type=bool)
    options.parse_command_line()

    settings = dict(
        template_loader=JinjaLoader(path.join(base_path, 'template')),
        static_path=path.join(base_path, 'static'),
        cookie_secret=uuid.uuid4().hex,
        login_url='/login',
        xsrf_cookies=False,
        debug=options.debug,
        gzip=False,
    )
    app = tornado.web.Application(**settings)
    app.add_handlers(".*", add_url_prefix(freess.handlers, '/spa'))
    server = HTTPServer(app)
    server.listen(options.port)
    IOLoop.current().start()


if __name__ == "__main__":
    main()
