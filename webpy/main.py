#!/usr/bin/env python
# coding=utf-8
import web
import glob
from webutils import (
    resp_with_json,
    make_response,
    make_thumbnail,
    get_template_render,
    Handler
    )
web.config.debug = True
# ==========
# ==========
render_template = get_template_render('../templates/')
# ==========
class Json(Handler):
    @resp_with_json
    def GET(self):
        return {'result': 'hello,yes'}
    @resp_with_json
    def POST(self):
        return {'result': '2012-12-12 12:12'}
class Amaze:
    def GET(self):
        return render_template('amaze01.html')

class hello(Handler):
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
class TestPost(Handler):
    def GET(self):
        return '<h1>test get</h1>'
    def POST(self):
        return '<h1>test post</h1>'

class Index(Handler):
    def GET(self):
        def glob_slide_image(slide_dir='/home/edward/data/www/static/uploads/slide/'):
            imgl = [e.split('/')[-1] for e in glob.glob(slide_dir + '*.jpg')]
            return imgl
        return render_template('index.html', slide_image_list=glob_slide_image())

class Upload(Handler):
    def GET(self):
        return render_template(
            'base.html',
            body='''
                <form method="post" action="/upload" enctype="multipart/form-data">
                    <input type="file" name="myfile"/>
                    <input type="submit" value="upload to server"/>
                <form/>
            ''')

    def POST(self):
        def save(fp, save_dir="/home/edward/data/www/static/uploads/slide/"):

            try:
                make_thumbnail(save_dir + fp.filename, fp.file)
            except Exception as e:
                return e
            else:
                return 0
        data = web.input(myfile={})
        fp = data.myfile
        if save(fp) == 0: # fp.filename, fp.read() gives name and contents of the file
            return render_template('index.html', alert_msg="1")
        else:
            return render_template('index.html', alert_msg="0")


class Signin(Handler):
    def GET(self):
        return render_template('signin.html')
    def POST(self):
        pass
# ====================
urls = (
        r'/upload/?', 'Upload',
        r"/hello/?", "hello",
        r"/?", Index,
        r'/directive/01/?', 'Directive01',
        r'/canvas/(\d+)/?', 'Canvas01',
        r'/ionic/(\d+)/?', 'Ionic01',
        r'/amaze/?', 'Amaze',
        r'/json/?', 'Json',
        r'/post/?', 'TestPost',
        r'/signin/?', 'Signin',
    )
myApp = web.application(urls, globals()).wsgifunc()
# app.run()
