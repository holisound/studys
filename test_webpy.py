import os
import web
import json
from jinja2 import Environment,FileSystemLoader

urls = ("/.*", "hello")
app = web.application(urls, globals(), autoreload=True)

def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    #jinja_env.update_template_context(context)
    return jinja_env.get_template(template_name).render(context)

class hello:
    def GET(self):
        # web.header('Content-Type','application/json')
        # return json.dumps({'greet': 'Hello,world!'})
        # You can use a relative path as template name, for example, 'ldap/hello.html'.
        return render_template('index.html', name='Edward',)
    def POST(self):
        return render_template('index.html', name='request with "post" method')

if __name__ == '__main__':
    app.run()
    # application = app.wsgifunc()