# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-05-17 10:13:14
# @Last Modified by:   edward
# @Last Modified time: 2016-06-13 16:32:54


import sys, os
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
os.chdir(abspath)

# from module.mysqldb import DbHelper
# import module.settings as Settings
import datetime
import decimal
from copy import deepcopy
from time import gmtime, strftime
from datetime import timedelta
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from tornado.web import RequestHandler, MissingArgumentError
import web, uuid, re, time, random, cgi
import urllib, urllib2, urlparse, cookielib, hashlib, socket
import logging, httplib, json
# from module import env
from operator import itemgetter
from itertools import islice, groupby
from PIL import Image
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

# if Settings.DEBUG_APP:
#     logging.basicConfig(filename = os.path.join(os.getcwd(), 'log.txt'), level = logging.DEBUG)

# ====================
def safe_int(s):
    try:
        s = int(s)
    except (ValueError, TypeError):
        pass
    return s
def json_safe_loads(jsonstr, **kwargs):

    if isinstance(jsonstr, basestring):
        try:
            pyObj = json.loads(jsonstr, **kwargs)
        except ValueError:
            return None
        else:
            if isinstance(pyObj, dict):
                pyObj = { k: safe_int(v) for k, v in pyObj.iteritems() }
            elif isinstance(pyObj, list):
                pyObj = [ safe_int(i) for i in pyObj ]
            return pyObj
    else:
        return jsonstr
def get_target_date(base):
    from datetime import timedelta
    return lambda d:base + timedelta(days=d)
def get_filter_by_weekday(wd):
    return lambda d: True if wd == d.isoweekday() else False
def get_filter_by_date(dd):
    return lambda d: True if dd == d else False
def updatedCopyOfDict(dictObj, **kwargs):
    # 新建一个字典的副本，同时可以更新或者添加新的key-value
    copy = dictObj.copy()
    copy.update(kwargs)
    return copy
def get_minute_duration(start, end):
    """
    start = '12:00(:00)', end = '13:01(:00)'
    get_duration( start, end ) --> 61 min
    """
    start = start if start.count(':') == 1 else start[:-3]
    end = end if end.count(':') == 1 else end[:-3]
    end, start = (end, start) if end > start else (start, end)
    duration_in_second = (datetime.datetime.strptime(end, '%H:%M') - datetime.datetime.strptime(start, '%H:%M')).seconds
    return duration_in_second/60
def sortit(iterable, key=None, reverse=False):
    return tuple(sorted(iterable, key=key, reverse=reverse))

def pick_out_of_dict(dictObj, keysets):
    return {k: v for k, v in dictObj.items() if k in keysets}

############################################################################################################################################################################################
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
class TemplateRedering:
    '''使用Jinja2生成模板
    '''
    def dbhelper(self):
        return DbHelper()

    def calcPageSpentTime(self):
        return '%.2f ms' % (self.request.request_time() * 1000.0)

    def getcurrentuser(self):
        user_id = self.get_secure_cookie("QGYMAUTHIDBE")
        user_password = self.get_secure_cookie("QGYMAUTHIDPWD")
        if self.db.IsUserExistByIdBackend(user_id, user_password) == False:
            self.setcurrentuser(None)
            user_id = None
        return user_id and int(user_id)

    def setcurrentuser(self, userid, userpassword=None):
        if userid is not None:
            # 0.001 day = 1.44 min
            self.set_secure_cookie("QGYMAUTHIDBE", str(userid), expires_days=7)
            self.set_secure_cookie("QGYMAUTHIDPWD", str(userpassword), expires_days=7)
            self.set_secure_cookie("QGYMAUTHLOGINTIME", strftime("%Y-%m-%d %H:%M:%S"), expires_days=7)
        else:
            self.clear_cookie("QGYMAUTHIDBE")
            self.clear_cookie("QGYMAUTHIDPWD")
            self.clear_cookie("QGYMAUTHLOGINTIME")

    def datetimespec(self):
        startyear = 2013
        currentyear = int(strftime("%Y-%m-%d %H:%M:%S")[0:4])
        if currentyear == startyear:
            return "%d" % startyear
        else:
            return "%d - %d" % (startyear, currentyear)

    def fromsource(self):
        # 请求此 url 的来源，可取值： "web", "app", "ios" 和 "android" ( "app" 包括 "ios" 和 "android" )
        fs = self.get_secure_cookie("fromsource")
        
        if fs == "web":
            self.clear_cookie("fromsource")

        if fs is None:
            fromsource = self.get_argument("urlrequestfrom", "web")
            if fromsource != "web":
                self.set_secure_cookie("fromsource", fromsource, expires_days=1)
        else:
            fromsource = fs
        return fromsource

    def getlogindatetime(self):
        logindatetime = self.get_secure_cookie("QGYMAUTHLOGINTIME")
        if logindatetime is None:
            return "未知"
        else:
            return logindatetime

    def listitemperpage(self):
        return Settings.LIST_ITEM_PER_PAGE

    def getpermission(self):
        user_id = self.getcurrentuser()
        if user_id:
            db = DbHelper()
            current_userinfo = db.QueryUserInfoById(user_id)
            user_permission = current_userinfo["user_permission"]
            if user_permission is not None:
                return json.loads(user_permission)
            else:
                return None
        else:
            return None

    def format_timestamp(self, timestamp, f='%Y-%m-%d %H:%M'):
        dateObj = datetime.datetime.fromtimestamp(float(timestamp))
        return datetime.datetime.strftime(dateObj,f)

    def render_Jinja_Template(self, template_name, **context):
        globals = context.pop('globals', {})
        jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'template/jinja2')),
            trim_blocks=True,
            extensions=["jinja2.ext.do","jinja2.ext.loopcontrols",])
        jinja_env.globals.update(globals)
        jinja_env.globals.update(json_safe_loads=json_safe_loads)
        jinja_env.globals.update(dbhelper=self.dbhelper)
        jinja_env.globals.update(currentuser=self.getcurrentuser)
        jinja_env.globals.update(getlogindatetime=self.getlogindatetime)
        jinja_env.globals.update(listitemperpage=self.listitemperpage)
        jinja_env.globals.update(calcPageSpentTime=self.calcPageSpentTime)
        jinja_env.globals.update(datetimespec=self.datetimespec)
        jinja_env.globals.update(getpermission=self.getpermission)
        jinja_env.globals.update(request_uri=self.request.uri)
        jinja_env.globals.update(format_timestamp=self.format_timestamp)
        return jinja_env.get_template(template_name).render(context)

class BaseHandler(RequestHandler, TemplateRedering):
    '''基础Handler，所有Tornado的Handler为了使用Jinja2模板引擎必须以此类为基类
    '''
    # def write_error(self, status_code, **kwargs):
    #     return self.renderJinjaTemplate("error.html", errorcode=status_code, user=self.getcurrentuser(), db=DbHelper())
    def get(self):
        self.write('test get ' + getattr(self, "url_pattern", "unknown path"))
    def post(self):
        self.write('test post' + getattr(self, "url_pattern", "unknown path"))
    @property
    def config(self):
        return self.application.config
    @property
    def db(self):
        return getattr(self.application, 'db', None)
    
    def get_argument(self, *args, **kwargs):
        v = super(BaseHandler, self).get_argument(*args, **kwargs)
        if isinstance(v, basestring) and len(v.strip()) == 0 and len(args) == 0:
            raise MissingArgumentError(args[0])
        return v

    def is_mobile(self):
        mobile = re.compile(r"iPod|iPad|iPhone|Android|Opera Mini|BlackBerry|webOS|UCWEB|Blazer|PSP")
        try:
            useragent = self.request.headers["User-Agent"]
        except Exception, e:
            useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        return mobile.search(useragent)

    def is_ios(self):
        mobile = re.compile(r"iPod|iPad|iPhone")
        try:
            useragent = self.request.headers["User-Agent"]
        except Exception, e:
            useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        return mobile.search(useragent)

    def is_android(self):
        mobile = re.compile(r"Android")
        try:
            useragent = self.request.headers["User-Agent"]
        except Exception, e:
            useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        return mobile.search(useragent)

    def get_current_user(self):
        return self.getcurrentuser()

    def renderJinjaTemplate(self, template_name, **context):
        fs = self.fromsource()

        context.update({
            'settings': self.settings,
            'request': self.request,
            'xsrf_token': self.xsrf_token,
            'xsrf_form_html': self.xsrf_form_html,
            "absurl": self.get_absurl,
            "mysqldb": self.db,
        })
        # onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
        old_template_name = template_name
        if self.is_mobile():
            if template_name.endswith(".html"):
                template_name = "%smobile.html" % template_name[:-4]
            else:
                template_name = template_name

            templatefile = os.path.join(abspath, 'template/jinja2/%s' % template_name)
            if os.path.exists(templatefile):
                content = self.render_Jinja_Template(template_name, **context)
            else:
                content = self.render_Jinja_Template(old_template_name, **context)
        else:
            content = self.render_Jinja_Template(template_name, **context)
        self.write(content)

    def renderJinjaTemplateV2(self, template_name, **context):
        context.update({
            'settings': self.settings,
            'request': self.request,
            'xsrf_token': self.xsrf_token,
            'xsrf_form_html': self.xsrf_form_html,
        })
        content = self.render_Jinja_Template(template_name, **context)
        self.write(content)

    def get_absurl(self, relative_path):
        host = self.request.host
        host = host.split(':')[0] if ':' in host else host
        return urlparse.urljoin(
            "http://%s" % host,
            relative_path)
    # def handle_photos_upload(self, photo_dict, width=640, save_dir=Settings.UPLOAD_DIR):
    #     im = Image.open(StringIO(photo_dict['body']))
    #     img_uuid = uuid.uuid4().hex + '.' + im.format.lower()
    #     date_str = str(datetime.datetime.today().date())
    #     date_dir = os.path.join(
    #         save_dir,
    #         date_str,
    #     )
    #     if not os.path.isdir(date_dir):
    #         os.makedirs(date_dir)
    #     save_to_path = os.path.join(
    #         date_dir,
    #         img_uuid,
    #     )
    #     with open(save_to_path + '.tmp', 'wb') as out_f:
    #         out_f.write(photo_dict['body'])
    #     os.rename(save_to_path + '.tmp', save_to_path)
    #     if os.path.exists(save_to_path):
    #         return 0, date_str + '/' + img_uuid
    #     return 1, None

    @property
    def valid_arguments(self):
        r = {}
        for k, v in self.request.arguments.items():
            if k.startswith('_'): continue
            v = [ i for i in v if len(i) > 0]
            if len(v) == 0:
                continue
            elif len(v) == 1:
                tv = v[0]
            else:
                tv = v
            r[k] = tv
        return r
    def write_json(self, obj):
        self.set_header('content-type', 'application/json')
        jsonstr = json.dumps(obj, cls=EnhancedJSONEncoder)
        self.write(jsonstr)

def fetch_handlers(ctx, base_handler, url_prefix=None):
    _handlers_array = {
        k:v for k,v  in ctx.items() if v in base_handler.__subclasses__()
    }
    handlers = []
    for k, v in _handlers_array.items():
        url_pattern = getattr(v, "url_pattern", [])
        if not isinstance(url_pattern, (list, tuple)):
            url_pattern = [url_pattern]
        url_name = getattr(v, "name", None)
        url_prefix_ = getattr(v, "url_prefix", None) or url_prefix
        # print url_prefix
        for up in url_pattern:

            handlers.append(
                (
                    up if url_prefix_ is None else (url_prefix_ + up),
                    v
                )
            )
    return handlers
