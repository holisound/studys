#!/usr/bin/env python
# coding=utf-8
import os
import web
import json
from itertools import islice
from webutils import make_response, render_template


# ==========
class hello:

    def GET(self):
        # 
        # web.header('Content-Type','application/json')
        # return json.dumps({'greet': 'Hello,world!'})
        # You can use a relative path as template name, for example,
        # 'ldap/hello.html'.
        return open("templates/ng01.html")
class Home:
    def GET(self):
        return '<h1>Hello, I am at home.</h1>'
# ==========

class Data:
    def GET(self):
        # =====*frontend input*=====
        args = web.input(start=0, count=10)
        start, count = int(args.start), int(args.count)
        stop = start + count
        # =====*database query*=====
        dql = DB.dql()
        dql.setmain('order_table')
        # print dql.fields
        # dql.inner_join('course_schedule_table', on='course_id=course_schedule_courseid')
        # dql.inner_join('gym_branch_table', on="course_schedule_gymbranchid=gym_branch_id")
        # dql.inner_join('category_table', on="course_categoryid=category_id")

        # results = dql.query().all()
        # results = dql.queryset.orderby('order_date').values('order_date', distinct=True)
        results = dql.query(distinct=True, fields=['order_date']).all()

        # for r in results:
        #     r['course_schedule_stock'] = json.loads(r["course_schedule_stock"])
        # results = tuple( r for r in islice(results,1,15))
        web.header('Content-Type', 'application/json')
        return json.dumps({'result':1, 'testdata': results})

class Register:

    def POST(self):
        data = web.input(username=None,
                         password=None,
                         verifycode=None)
        return data.verifycode


class Upload:

    def POST(self):
        data = web.input(myfile={})
        with open(data.myfile.filename, 'wb') as f:
            f.write(data.myfile.value)
        callback = open(data.myfile.filename).read()
        return callback

class Directive01:
    def GET(self):
        return make_response('directive01.html', 'text/html')

class Canvas01:
    def GET(self, mid):
        return render_template('canvas01.html', image_id=mid)

class Ionic01:
    def GET(self, theid):
        return render_template('ionic01.html')
if __name__ == '__main__':
    web.application(
        (r"/?", "hello",
         r'/register/?', 'Register',
         r'/upload/?', 'Upload',
         r'/data/?' , 'Data',
         r'/home/?', 'Home',
         r'/directive/01/?', 'Directive01',
         r'/canvas/(\d+)/?', 'Canvas01',
         r'/ionic/(\d+)/?', 'Ionic01',
        ),
        globals(), autoreload=True).run()
    # application = app.wsgifunc()
