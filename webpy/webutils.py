import web
import os, json
from jinja2 import Environment, FileSystemLoader

# 
def get_template_render(templates_dir="templates"):
    def render(template_name, **context):
        extensions = context.pop('extensions', [])
        globals = context.pop('globals', {})
        jinja_env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), templates_dir)),
            extensions=extensions,
        )
        jinja_env.globals.update(globals)

        # jinja_env.update_template_context(context)
        return jinja_env.get_template(template_name).render(context)
    return render

def make_response(to_response, content_type='text/html'):
    _filename = to_response;
    web.header('Content-Type', content_type)
    # 
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    # 
    filepath = os.path.join(templates_dir, _filename)
    if os.path.isfile(filepath):
        with open(filepath) as f:
            return f.read()
    else:
        return to_response
# 
def response_json(to_response):
    web.header('Content-Type', 'application/json')
    return json.dumps(to_response)

def resp_with_json(method):
    def fn(self, *args, **kw):
        web.header('Content-Type', 'application/json; charset=UTF-8')
        return json.dumps(method(self, *args, **kw))
    return fn
    
def getvariance(s):
    """
    s: str
    """
    ls = map(ord,s)
    _average = sum(ls)/float(ls.__len__())
    def fx(e):
        return (e - _average)**2
    return sum(map(fx, ls))/float(ls.__len__())

def main():
    print getvariance('ajax')
if __name__ == '__main__':
    main()