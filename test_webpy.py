#!/usr/bin/env python
# coding=utf-8
import web
from webutils import (
    resp_as_json,
    make_response,
    render_template,
    response_json)


# ==========
class Json:
    @resp_as_json
    def GET(self):
        return {'result': 'hello,yes'}
class Amaze:
    def GET(self):
        return render_template('amaze01.html')

class hello:

    def GET(self):
        return open("templates/ng01.html")
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
if __name__ == '__main__':
    web.application(
        (r"/?", "hello",
         r'/directive/01/?', 'Directive01',
         r'/canvas/(\d+)/?', 'Canvas01',
         r'/ionic/(\d+)/?', 'Ionic01',
         r'/amaze/?', 'Amaze',
         r'/json/?', 'Json',
        ),
        globals(), autoreload=True).run()
    # application = app.wsgifunc()
