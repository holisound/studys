import web
import os, json
from jinja2 import Environment, FileSystemLoader
import datetime
from PIL import Image
# 
class Handler:
    templates_path = 'templates'
    def __init__(self):
        web.header('Content-Type', 'text/html; charset=UTF-8')
        self.input = None
        self.response = None

    def render(self, tpl, **kw):
        _render = get_template_render(self.templates_path)
        self.response =  _render(tpl, **kw)
        return self.response

    def get_input(self, **kw):
        self.input = web.input(**kw)
        return self.input

    def _dispatch(self, method, *args):
        tocall = getattr(self, method, None)
        if hasattr(tocall, '__call__'):
            return tocall(*args) or self.response
        else:
            raise web.nomethod()

    def GET(self, *args):
        return self._dispatch('get', *args)
    def POST(self, *args):
        return self._dispatch('post', *args)

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            ARGS = ('year', 'month', 'day', 'hour', 'minute',
                     'second', 'microsecond')
            return {'__type__': 'datetime.datetime',
                    'args': [getattr(obj, a) for a in ARGS]}
        elif isinstance(obj, datetime.date):
            ARGS = ('year', 'month', 'day')
            return {'__type__': 'datetime.date',
                    'args': [getattr(obj, a) for a in ARGS]}
        elif isinstance(obj, datetime.time):
            ARGS = ('hour', 'minute', 'second', 'microsecond')
            return {'__type__': 'datetime.time',
                    'args': [getattr(obj, a) for a in ARGS]}
        elif isinstance(obj, datetime.timedelta):
            ARGS = ('days', 'seconds', 'microseconds')
            return {'__type__': 'datetime.timedelta',
                    'args': [getattr(obj, a) for a in ARGS]}
        elif isinstance(obj, decimal.Decimal):
            return {'__type__': 'decimal.Decimal',
                    'args': [str(obj),]}
        else:
            return super().default(obj)

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
# 
def resp_with_json(method):
    def fn(self, *args, **kw):
        web.header('Content-Type', 'application/json; charset=UTF-8')
        return json.dumps(method(self, *args, **kw), cls=EnhancedJSONEncoder)
    return fn

def make_thumbnail(save_as, imgObj, width=640):
    # try:
    im = Image.open(imgObj)
    # im = Image.open(fileObj)
    w, h = im.size
    tw = width if w > width else w
    th = width/float(w)*h if w > width else h
    tsize = tw, th
    im.thumbnail(tsize, Image.ANTIALIAS)
    im.save(save_as, "JPEG")
    # 
    if w > h:
        thumbnail_w = 128;
        thumbnail_h = 128/float(w)*h
    else:
        thumbnail_h = 128;
        thumbnail_w = 128/float(h)*w

    save_as_thumbnail = '.thumbnail.'.join(save_as.split('.'))
    tsize = thumbnail_w, thumbnail_h
    im.thumbnail(tsize, Image.ANTIALIAS)
    im.save(save_as_thumbnail, "JPEG")
    # except IOError:
    #     print("cannot create thumbnail for", save_as)

def getvariance(s):
    """
    s: str
    """
    ls = map(ord,s)
    _average = sum(ls)/float(len(ls))
    def fx(e):
        return (e - _average)**2
    return sum(map(fx, ls))/float(len(ls))

def main():
    print getvariance('ajax')
if __name__ == '__main__':
    main()