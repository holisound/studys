import web
import os
from jinja2 import Environment, FileSystemLoader

# 
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

def make_response(to_response, content_type):
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