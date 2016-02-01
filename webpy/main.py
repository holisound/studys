#!/usr/bin/env python
# coding=utf-8
import web
from webutils import (
    resp_with_json,
    make_response,
    get_template_render,
    response_json)

# ==========
# ==========
render_template = get_template_render('../templates/')
# ==========
class Json:
    @resp_with_json
    def GET(self):
        return {'result': 'hello,yes'}
    @resp_with_json
    def POST(self):
        return {'result': 'greet via post'}
class Amaze:
    def GET(self):
        return render_template('amaze01.html')

class hello:
    def GET(self):
		return render_template('base.html', title="mytitle", body="<h1>Hello, world!</h1>")
# ==========
class Directive01:
    def GET(self):
        return make_response('directive01.html', 'text/html')

class Canvas01:
    def GET(self, mid):
        return render_template('canvas01.html', image_id=int(mid))

class Ionic01:
    def GET(self, theid):
        return render_template('ionic01.html')
# ====================
urls = (
        r"/?", "hello",
        r'/directive/01/?', 'Directive01',
        r'/canvas/(\d+)/?', 'Canvas01',
        r'/ionic/(\d+)/?', 'Ionic01',
        r'/amaze/?', 'Amaze',
        r'/json/?', 'Json',
    )
app = web.application(urls, globals())
application = app.wsgifunc()
# app.run()
