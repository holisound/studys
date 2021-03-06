#!/usr/bin/env python
# coding=utf-8
import web
import glob
import config
from webutils import (
    resp_with_json,
    make_thumbnail,
    Handler as _Handler,
    )
# ==========
class Handler(_Handler):
    templates_path = '../templates/'
# ==========
class Register(Handler):
    def GET(self):
        return self.render('reg.html', path=web.ctx.path)
    @resp_with_json
    def POST(self):
        params = self.get_input(
            username='',
            password=''
        )
        if params.username and params.password:
            return params
        else:
            return 0

class Json(Handler):
    @resp_with_json
    def GET(self):
        return {'result': 'hello,yes'}
    @resp_with_json
    def POST(self):
        return {'result': '2012-12-12 12:12'}

class hello(Handler):

    def GET(self):
	   return self.render('base.html', title="mytitle", body="<h1>Hello, world!</h1>")

# ==========
class Directive01(Handler):
    def GET(self):
        return self.render('directive01.html')

class Canvas01(Handler):
    def GET(self, mid):
        return self.render('canvas01.html', image_id=int(mid))

class Ionic01(Handler):
    def GET(self, theid):
        return self.render('ionic01.html')
class TestPost(Handler):
    def GET(self):
        return '<h1>test get</h1>'
    def POST(self):
        return '<h1>test post</h1>'

class Index(Handler):
    def GET(self):
        def glob_slide_image(slide_dir=config.UPLOAD_DIR):
            imgl = [e.split('/')[-1] for e in glob.glob(slide_dir + '*.jpg') if 'thumbnail' not in e]
            return imgl
        return self.render('index.html', slide_image_list=glob_slide_image())

class Upload(Handler):
    def GET(self):
        return self.render('upload.html')
    def POST(self):
        def save(fp):
            try:
                make_thumbnail(config.UPLOAD_DIR, fp.filename, fp.file)
            except Exception as e:
                return e
            else:
                return 0
        data = web.input(myfile={})
        fp = data.myfile
        if save(fp) == 0: 
            return self.render('upload.html', alert_msg="1")
        else:
            return self.render('upload.html', alert_msg="0")


class Signin(Handler):
    def GET(self):
        return self.render('signin.html')
    def POST(self):
        pass
class Register(Handler):
    def GET(self):
        return self.render('reg.html', path=web.ctx.path)
    def POST(self):
        params = p = web.input(
            username="",
            email="",
            password="",
            confirm=""
        )
        return '''
            username: %s
            email: %s
            password: %s
            confirm: %s
            ''' % (p.username, p.email, p.password, p.confirm)

class Angular(Handler):
    def GET(self, id):
        tplname = 'ng-test-%02d.html' % int(id)
        return self.render(tplname)

class NotFound(Handler):
    def GET(self):
        return self.render('error.html', status_code=404, desc="NOT FOUND")
class React(Handler):
    def GET(self, tid):
        tpl_name = 'react-%02d.html' % int(tid)
        return self.render(tpl_name, tpl_id=tid)
# ====================
urls = (
        r'/upload/?', 'Upload',
        r"/hello/?", "hello",
        r"/?", 'Index',
        r'/directive/01/?', 'Directive01',
        r'/canvas/(\d+)/?', 'Canvas01',
        r'/ionic/(\d+)/?', 'Ionic01',
        r'/amaze/?', 'Amaze',
        r'/json/?', 'Json',
        r'/post/?', 'TestPost',
        r'/signin/?', 'Signin',
        r'/reg/?', 'Register',
        r'/ng/(\d+)/?', 'Angular',
        r'/react/(\d+)/?', 'React',
        r'/notfound/?', 'NotFound',
    )
myApp = web.application(urls, globals()).wsgifunc()
# myApp = web.application(urls, globals())
# if __name__ == '__main__':
    
#     myApp.run()
