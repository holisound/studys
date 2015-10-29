#!/usr/bin/env python
import os
import web
import json
from jinja2 import Environment, FileSystemLoader
from mydql import connect
urls = (r"/?", "hello",
        r'/register/?', 'Register',
        r'/upload/?', 'Upload',
        r'/data/?' , 'Data',
        )
app = web.application(urls, globals(), autoreload=True)


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

def mydql():
    return connect(host="localhost", db="QGYM", user="root", passwd="123123")

class hello:

    def GET(self):
        # web.header('Content-Type','application/json')
        # return json.dumps({'greet': 'Hello,world!'})
        # You can use a relative path as template name, for example,
        # 'ldap/hello.html'.
        return open("templates/ng01.html")

class Data:
    def GET(self):
        dql = mydql()
        dql.set_main('order_table')
        # dql.fields.order_date.
        dql.fieldstore.order_date.date_format("%Y-%m-%d")
        dql.fieldstore.order_begintime.date_format("%H:%i")
        dql.fieldstore.order_endtime.date_format("%H:%i")
        results = dql.query(where=dict(order_date='2015-10-07'))
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
