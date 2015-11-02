#!/usr/bin/env python
# coding=utf-8
import os
import web
import json
from jinja2 import Environment, FileSystemLoader
from mydql import connect
from itertools import islice
urls = (r"/?", "hello",
        r'/register/?', 'Register',
        r'/upload/?', 'Upload',
        r'/data/?' , 'Data',
        r'/home/?', 'Home',
        )
app = web.application(urls, globals(), autoreload=True)
db = connect(host='localhost', db='QGYM', user='root', passwd='123123')

def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(__file__), 'templates')),
        extensions=extensions,
    )
    jinja_env.globals.update(globals)

    # jinja_env.update_template_context(context)
    return jinja_env.get_template(template_name).render(context)

class hello:

    def GET(self):
        # web.header('Content-Type','application/json')
        # return json.dumps({'greet': 'Hello,world!'})
        # You can use a relative path as template name, for example,
        # 'ldap/hello.html'.
        return open("templates/ng01.html")
class Home:
    def GET(self):
        dql = conn.dql()
        st = dql.set_main('student')
        st.sbirthday.date_format("%Y-%m-%d", "birth")
        return json.dumps({ "testdata":dql.query()})
class Data:
    def GET(self):
        # =====*frontend input*=====
        args = web.input(start=0, count=10)
        start, count = int(args.start), int(args.count)
        stop = start + count
        # =====*database query*=====
        dql = db.InitDQL()
        dql.set_main('order_table')
        # dql.set_main(courseview)
        # dql.inner_join('course_schedule_table', on="course_schedule_id=order_objectid")
        # dql.inner_join('gym_branch_table', on="course_schedule_gymbranchid=gym_branch_id")
        # dql.inner_join('course_table', on="course_id=course_schedule_courseid")
        # dql.inner_join('category_table', on="course_categoryid=category_id")
        db.GetField('order_table', 'order_date').DateFormat("%Y-%m-%d")
        db.GetField('order_table', 'order_begintime').DateFormat("%H:%i")
        db.GetField('order_table', 'order_endtime').DateFormat("%H:%i")
        db.GetField('order_table', 'order_datetime').DateFormat("%Y-%m-%d %H:%i")

        # dql.fields.order_date.
        # results = dql.query(where=dict(order_date='2015-12-22',order_type=2))
        print dql.get_dql()
        results = dql.queryset.sliceinto(start, stop)

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
if __name__ == '__main__':
    app.run()
    # application = app.wsgifunc()
