#!/usr/bin/env python
#-*-coding:utf-8-*-

# # # Author: Willson Zhang
# # # Date: Sep 9th, 2015
# # # Email: willson.zhang1220@gmail.com

import sys, os
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
os.chdir(abspath)

from module.mysqldb import DbHelper
import module.settings as Settings
import Image, ImageOps
import shutil
import datetime
import requests
import decimal
import xlwt
from copy import deepcopy
from module.snownlp import SnowNLP
from module import qr, date_stuff
from time import gmtime, strftime
from datetime import timedelta
from urllib import unquote
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from datetime import datetime as DateTime
from wheezy.captcha.image import captcha
from wheezy.captcha.image import background
from wheezy.captcha.image import curve
from wheezy.captcha.image import noise
from wheezy.captcha.image import smooth
from wheezy.captcha.image import text
from wheezy.captcha.image import offset
from wheezy.captcha.image import rotate
from wheezy.captcha.image import warp
from tornado.httpserver import HTTPServer
from tornado.netutil import bind_sockets
from tornado.httpclient import HTTPResponse

import jpush as jpush
import tornado.ioloop, tornado.web, tornado.process, string
import web, uuid, re, time, random, cgi
import urllib, urllib2, urlparse, cookielib, hashlib, socket
import logging, httplib, json
from module import env
from module import watermark
from operator import itemgetter
from itertools import islice, groupby
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

if Settings.DEBUG_APP:
    logging.basicConfig(filename = os.path.join(os.getcwd(), 'log.txt'), level = logging.DEBUG)

web.config.debug = False
if True:
    web.config.smtp_server = 'smtp.gmail.com'
    web.config.smtp_port = 587
    web.config.smtp_username = 'viroyal1220@gmail.com'
    web.config.smtp_password = 'viroyal1220'
    web.config.smtp_starttls = True

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
############################################################################################################################################################################################

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
        db = DbHelper()
        if db.IsUserExistByIdBackend(user_id, user_password) == False:
            self.setcurrentuser(None)
            user_id = None
        return user_id

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
        return jinja_env.get_template(template_name).render(context)

class BaseHandler(tornado.web.RequestHandler, TemplateRedering):
    '''基础Handler，所有Tornado的Handler为了使用Jinja2模板引擎必须以此类为基类
    '''
    # def write_error(self, status_code, **kwargs):
    #     return self.renderJinjaTemplate("error.html", errorcode=status_code, user=self.getcurrentuser(), db=DbHelper())
    def get_argument(self, *args, **kwargs):
        v = super(BaseHandler, self).get_argument(*args, **kwargs)
        if isinstance(v, basestring) and len(v) == 0:
            raise tornado.web.MissingArgumentError(args[0])
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
        })
        onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
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
    def handle_photos_upload(self, photo_dict, width=640, save_dir=Settings.UPLOAD_DIR):
        im = Image.open(StringIO(photo_dict['body']))
        img_uuid = uuid.uuid4().hex + '.' + im.format.lower()
        save_to_path = os.path.join(
            save_dir,
            img_uuid,
        )
        with open(save_to_path + '.tmp', 'wb') as out_f:
            out_f.write(photo_dict['body'])
        os.rename(save_to_path + '.tmp', save_to_path)
        if os.path.exists(save_to_path):
            return 0, img_uuid
        return 1, None

class XsrfBaseHandler(BaseHandler):
    def check_xsrf_cookie(self):
        # xsrf -> Delete Dash -> SHA256 -> MD5 x 3 -> Reverse -> MD5 -> SHA256 -> token
        params = (self.get_argument("xsrf", None) or self.get_argument("token", None))
        if not params:
            raise tornado.web.HTTPError(403, "'xsrf' and 'token' argument missing from POST")

        db = DbHelper()
        xsrf  = self.get_argument("xsrf")
        token = self.get_argument("token")
        s7    = db.CalculateAPIToken(xsrf)

        if s7 != token:
            raise tornado.web.HTTPError(403, "XSRF argument does not match POST argument")
        else:
            if db.IsUUIDExist(xsrf) == True:
                raise tornado.web.HTTPError(403, "XSRF argument expired")
            else:
                db.AddValidUUID(xsrf)

    def handle_daily_task(self, uid, task_type):
        DAILY_POINTS_MAP = {
            1: 100,
        }
        db = DbHelper()
        if len(db.QueryTasks(daily=True, task_type=task_type)) == 0:
            # daily points task
            db.SaveTask(
                auto_prefix=True,
                userid=uid,
                type=task_type,
            )
            db.SaveUserPoints(uid, DAILY_POINTS_MAP[task_type])

############################################################################################################################################################################################

def IsArgumentEmpty(handler, argkey):
    argvalue = handler.get_argument(argkey, None)
    ret = False
    if argvalue is None:
        ret = True
    else:
        if len(str(argvalue)) == 0:
            ret = True
        else:
            ret = False
    return ret

def GetArgumentValue(handler, argkey, escapehtml=1, default=None):
    if escapehtml == 1:
        return default if IsArgumentEmpty(handler, argkey) else cgi.escape(handler.get_argument(argkey))
    else:
        return default if IsArgumentEmpty(handler, argkey) else handler.get_argument(argkey)

def getuniquestring():
    randstr = str(time.time()).replace(".", "")[4:]
    while len(randstr) < 8:
        randstr += "0"
    randstr += str(random.randint(10, 99))
    return randstr

def postHttp(posturl, postdatadict):
    url = posturl
    payload = postdatadict
    headers = {'content-type': 'application/json'}

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response

def check_avatar_image_ratio(width, height):
    ratio = 1.5
    error = 0.1
    if abs(float(width) / height - ratio) - error > 0:
        return False
    return True

check_image_ratio = check_avatar_image_ratio

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

class EnhancedJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, object_hook=self.object_hook,
                         **kwargs)
    def object_hook(self, d): 
        if '__type__' not in d:
            return d
        o = sys.modules[__name__]
        for e in d['__type__'].split('.'):
            o = getattr(o, e)
        args, kwargs = d.get('args', ()), d.get('kwargs', {})
        return o(*args, **kwargs)

############################################################################################################################################################################################

class Captcha(BaseHandler):
    def get(self):
        captcha_image = captcha(drawings=[
            background(),
            text(fonts=[
                'fonts/CourierNew-Bold.ttf',
                'fonts/LiberationMono-Bold.ttf'],
                drawings=[
                    warp(),
                    rotate(),
                    offset()
                ]),
            curve(),
            noise(),
            smooth()
        ])
        chars = random.sample(string.uppercase + string.digits, 4)
        image = captcha_image(chars)
        self.set_secure_cookie("QGYMCAPTCHABE", ''.join(chars), expires_days=1)

        out = StringIO()
        image.save(out, "JPEG", quality=100)
        self.set_header('Content-Type','image/jpeg')
        self.write(out.getvalue())

class CaptchaCheck(BaseHandler):
    def post(self):
        captcha = GetArgumentValue(self, "captcha")
        correctVal = self.get_secure_cookie("QGYMCAPTCHABE")
        iscaptcharight = (captcha.upper() == correctVal)
        return self.write("1" if iscaptcharight else "0")

class CKEditImageUpload(BaseHandler):
    def post(self):
        if not self.request.files.has_key('upload'):
            return

        uploadedfile = self.request.files['upload'][0]
        original_fname = uploadedfile['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = getuniquestring()
        filename = fname + extension

        filedir             = os.path.join(abspath, 'static/img/upload')
        infile              = filedir + '/' + filename
        infile_preview      = '/static/img/upload/P%s.jpeg' % fname

        # filedir             = "static/img/upload"
        # infile              = filedir + '/' + filename # infile就是用户上传的原始照片
        # infile_preview      = filedir + '/P%s.jpeg' % fname

        localfile           = infile # os.path.join(abspath, infile)
        localfile_preview   = os.path.join(abspath, 'static/img/upload/P%s.jpeg' % fname) # os.path.join(abspath, infile_preview)

        # 自动保存用户上传的照片文件
        output_file = open(localfile, 'w')
        output_file.write(uploadedfile['body'])
        output_file.close()

        # 将 infile 保存为 jpeg 格式的图片，最大宽度为 900
        im = Image.open(localfile)
        im_width = im.size[0]
        im_height = im.size[1]
        avatar_size = (im_width, im_height)
        if im_width > 900:
            avatar_size = (900, int(im_height * (900.0 / im_width)))

        method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
        # formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5,0.5))

        method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
        formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5,0.5))
        formatted_im.save(localfile_preview, "JPEG", quality=100)
        watermark.watermark(localfile_preview, watermark.MARKIMAGE, watermark.POSITION[4], opacity=0.7).save(localfile_preview, quality=90)
        
        os.remove(localfile)

        # 向 CKEditor 编辑器返回图片链接
        # serveraddress = self.request.headers.get("Host")
        serveraddress = self.request.headers.get("Host")
        # serveraddress = "www.17dong.com.cn" if socket.gethostname() == Settings.SERVER_HOST_NAME else "192.168.1.99"
        url = "http://%s%s" % (serveraddress, infile_preview)
        self.write("""
            <script type='text/javascript'>
                window.parent.CKEDITOR.tools.callFunction(%s, '%s');
            </script>""" % (self.get_argument('CKEditorFuncNum'), url))

    def check_xsrf_cookie(self):
        pass

    def GetImagePixelSize(self, imagefilepath):
        imout = Image.open(imagefilepath)
        newsize = imout.size
        return newsize

############################################################################################################################################################################################

class AdminLogin(BaseHandler):
    def get(self):
        login_type = self.get_argument("type", None)
        # 退出登录
        if login_type and login_type == "logout":
            db = DbHelper()
            user_id = self.current_user
            userinfo = db.QueryUserInfoById(user_id)
            user_name = userinfo["user_name"]
            username = user_name if userinfo is not None else ""

            self.setcurrentuser(None)
            return self.renderJinjaTemplate("backend/admin_login.html", verifyResponse={
                "inputusernameempty" : False, "inputpasswordempty" : False, "isCaptchaValid" : True, "checkuserstatus" : 1, "username" : username}, 
                next=self.get_argument("next", "/"))
        # 登录
        else:
            user_id = self.current_user
            if user_id:
                return self.redirect("/")
            else:
                return self.renderJinjaTemplate("backend/admin_login.html", verifyResponse={
                    "inputusernameempty" : False, "inputpasswordempty" : False, "isCaptchaValid" : True, "checkuserstatus" : 1, "username" : ""}, 
                    next=self.get_argument("next", "/"))

    def post(self):
        username = cgi.escape(self.get_argument("inputUserName"))
        passwd = cgi.escape(self.get_argument("inputPassword"))
        captcha = self.get_argument("inputCaptcha")
        inputusernameempty = False
        inputpasswordempty = False
        if (username is None) or (username == ""):
            inputusernameempty = True
        if (passwd is None) or (passwd == ""):
            inputpasswordempty = True
        db = DbHelper()
        checkuserstatus = db.CheckUserBackend(username, passwd)

        isCaptchaValid = self.isValidCaptcha(captcha)

        if (inputusernameempty == True) or (inputpasswordempty == True) or (checkuserstatus < 0) or (isCaptchaValid == False):
            # 登录失败
            return self.renderJinjaTemplate("backend/admin_login.html", verifyResponse={
                "inputusernameempty" : inputusernameempty, "inputpasswordempty" : inputpasswordempty, "isCaptchaValid" : isCaptchaValid, "checkuserstatus" : checkuserstatus, "username" : username}, 
                next=self.get_argument("next", "/"))
        else:
            # 登录成功
            userinfo = db.QueryUserInfoByName(username)
            self.setcurrentuser(userinfo["user_id"], userpassword=userinfo["user_password"])
            return self.redirect(self.get_argument("next", "/"))

    def isValidCaptcha(self, captcha):
        if not captcha:
            return False
        correctVal = self.get_secure_cookie("QGYMCAPTCHABE")
        return captcha.upper() == correctVal

class AdminUser(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        # 分页显示用户信息
        inputname = self.get_argument("inputname", None)
        user_role = int(self.get_argument("user_role", 1))

        # 权限检测
        # if CheckUserPermission(self, "User%d" % user_role, "V") == False:
        #     return self.send_error(403)

        db = DbHelper()
        alluserscount = db.QueryAllUserCount(user_role) if inputname is None else db.FuzzyQueryUserCount(inputname, user_role)
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1

        allusers = db.QueryUsers((pageindex - 1) * Settings.LIST_ITEM_PER_PAGE, userrole=user_role) if inputname is None else db.FuzzyQueryUser(inputname, (pageindex - 1) * Settings.LIST_ITEM_PER_PAGE, userrole=user_role)
        return self.renderJinjaTemplate("backend/admin_user.html", allusers=allusers, inputname=inputname, 
            pageindex=pageindex, LIST_ITEM_PER_PAGE=Settings.LIST_ITEM_PER_PAGE, alluserscount=alluserscount, userrole=user_role)

    @tornado.web.authenticated
    def post(self):
        '''处理查询用户的请求
        '''
        username = cgi.escape(self.get_argument("inputUsername"))
        user_role = int(self.get_argument("user_role", 1))

        # 权限检测
        # if CheckUserPermission(self, "User%d" % user_role, "V") == False:
        #     return self.send_error(403)

        redirecturl = "/user?"
        paramdict = { "user_role" : user_role, "inputname" : username }
        redirecturl = "%s%s" % (redirecturl, urllib.urlencode(paramdict))

        return self.redirect(redirecturl)

class AdminUserAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        # 权限检测
        # if CheckUserPermission(self, "User%d" % user_role, "A") == False:
        #     return self.send_error(403)
        return self.renderJinjaTemplate("backend/admin_user_add.html", userrole=int(self.get_argument("user_role", 1)))

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }
        obj['user_registerip'] = self.request.remote_ip
        db = DbHelper()
        user_id = db.SaveUser(obj)

        # 添加图片信息 ##########################
        if self.request.files.has_key('user_avatar'):
            uploadedfile = self.request.files['user_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/user')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SaveUser({ "user_id" : user_id, "user_avatar" : getuniquestring() })
            outfile  = filedir + '/P%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #########################################

        return self.redirect("/user?user_role=%d" % int(self.get_argument("user_role", 1)))

class AdminUserDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        user_id = cgi.escape(self.get_argument("uid"))
        permant = self.get_argument("permant", "0")
        try:
            user_id = int(user_id)
            permant = int(permant)
        except Exception, e:
            user_id = None
            permant = 0
        if user_id:
            db = DbHelper()
            db.DeleteUser(user_id, permant)
            return self.write("Success")
        else:
            return self.write("Fail")

class AdminUserEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryUserInfoById(the_id)
        return self.renderJinjaTemplate("backend/admin_user_edit.html", objectinfo=objectinfo)

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        if int(self.get_argument("updatePasword")) == 1:
            obj['user_password'] = cgi.escape(self.get_argument("user_password"))
        else:
            if obj.has_key('user_password'):
                obj.pop('user_password')

        if not self.request.files.has_key('user_avatar'):
            obj.pop('user_avatar')

        db = DbHelper()
        db.SaveUser(obj)

        # 添加图片信息 ##########################
        user_id = obj['user_id']
        if self.request.files.has_key('user_avatar'):
            uploadedfile = self.request.files['user_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/user')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SaveUser({ "user_id" : user_id, "user_avatar" : getuniquestring() })
            outfile  = filedir + '/P%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #########################################

        return self.redirect("/user?user_role=%d" % int(self.get_argument("user_role", 1)))

class AdminUserVipcard(BaseHandler):

    @tornado.web.authenticated
    def get(self, user_id):
        return self.renderJinjaTemplate("backend/admin_uservipcard.html", user_id=user_id)

class AdminUserVipcardAdd(BaseHandler):
    @tornado.web.authenticated
    def get(self, user_id):
        return self.renderJinjaTemplate("backend/admin_uservipcard_add.html", user_id=user_id)
    @tornado.web.authenticated
    def post(self, user_id):
        db = DbHelper()
        user_vipcard_range= int(GetArgumentValue(self, "vipcard_range"))
        vipcard_data = dict(
            user_vipcard_userid=user_id,
            user_vipcard_range=user_vipcard_range,
            user_vipcard_no=GetArgumentValue(self, "vipcard_number"),
            user_vipcard_phonenumber=GetArgumentValue(self, "phone_number"),
            user_vipcard_name=GetArgumentValue(self, "vipcard_username"),
            user_vipcard_expiredate=GetArgumentValue(self, "vipcard_exp"),
            user_vipcard_validtimes=GetArgumentValue(self, "vipcard_validtimes"),
            user_vipcard_status=GetArgumentValue(self, "vipcard_status"),
        )
        if user_vipcard_range == 0:
            vipcard_data['user_vipcard_rangeid'] = json.dumps([int(GetArgumentValue(self, "gym_select"))])
        elif user_vipcard_range == 1:
            vipcard_data['user_vipcard_rangeid'] = json.dumps(sorted(int(i) for i in self.get_arguments("gymbranch_select")))

        db.SaveUservipcard(vipcard_data)
        return self.redirect('/user/%s/vipcard' % user_id)

class AdminUserVipcardEdit(BaseHandler):
    @tornado.web.authenticated
    def get(self, user_id):
        return self.renderJinjaTemplate("backend/admin_uservipcard_edit.html", vipcard_id=GetArgumentValue(self, "id"), user_id=user_id)
    @tornado.web.authenticated
    def post(self,user_id):
        db = DbHelper()
        user_vipcard_range= int(GetArgumentValue(self, "vipcard_range"))
        vipcard_data = dict(
            user_vipcard_id=GetArgumentValue(self, "id"),
            user_vipcard_userid=user_id,
            user_vipcard_range=user_vipcard_range,
            user_vipcard_no=GetArgumentValue(self, "vipcard_number"),
            user_vipcard_phonenumber=GetArgumentValue(self, "phone_number"),
            user_vipcard_name=GetArgumentValue(self, "vipcard_username"),
            user_vipcard_expiredate=GetArgumentValue(self, "vipcard_exp"),
            user_vipcard_validtimes=GetArgumentValue(self, "vipcard_validtimes"),
            user_vipcard_status=GetArgumentValue(self, "vipcard_status"),
        )
        if user_vipcard_range == 0:
              vipcard_data['user_vipcard_rangeid'] = json.dumps([int(GetArgumentValue(self, "gym_select"))])
        elif user_vipcard_range == 1:
              vipcard_data['user_vipcard_rangeid'] = json.dumps(sorted(int(i) for i in self.get_arguments("gymbranch_select")))

        db.SaveUservipcard(vipcard_data)
        return self.redirect('/user/%s/vipcard' % user_id)

class AdminUserVipcardDelete(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        db = DbHelper()
        db.DeleteUservipcard(GetArgumentValue(self, "the_id"))

class AdminUserData(BaseHandler):

    @tornado.web.authenticated
    def get(self, user_id):
        return self.renderJinjaTemplate("backend/admin_userdata.html", user_id=user_id, pageindex=int(self.get_argument("p", 1)))

class AdminUserDataAdd(BaseHandler):
    @tornado.web.authenticated
    def get(self, user_id):
        return self.renderJinjaTemplate("backend/admin_userdata_add.html", user_id=user_id)

    @tornado.web.authenticated
    def post(self, user_id):
        db = DbHelper()
        userdata_data = dict(
            user_data_userid=user_id,
            user_data_categoryid=GetArgumentValue(self, "category_id"),
            user_data_date=GetArgumentValue(self, "date"),
            user_data_duration=GetArgumentValue(self, "duration"),
            user_data_source=GetArgumentValue(self, "source"),
            user_data_calory=GetArgumentValue(self, "calory"),
        )
        db.SaveUserData(userdata_data)
        return self.redirect("/user/%s/data" % user_id)

class AdminUserDataEdit(BaseHandler):
    @tornado.web.authenticated
    def get(self, user_id):
        return self.renderJinjaTemplate("backend/admin_userdata_edit.html", user_id=user_id, userdata_id=GetArgumentValue(self, "id"))
    def post(self, user_id):
        db = DbHelper()
        userdata_data = dict(
            user_data_id=GetArgumentValue(self, "id"),
            user_data_userid=user_id,
            user_data_categoryid=GetArgumentValue(self, "category_id"),
            user_data_date=GetArgumentValue(self, "date"),
            user_data_duration=GetArgumentValue(self, "duration"),
            user_data_source=GetArgumentValue(self, "source"),
            user_data_calory=GetArgumentValue(self, "calory"),
        )
        db.SaveUserData(userdata_data)
        return self.redirect("/user/%s/data" % user_id)

class AdminUserDataDelete(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        db = DbHelper()
        db.DeleteUserData(GetArgumentValue(self, 'the_id'))
class AdminAds(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_ads.html", pageindex=int(self.get_argument("p", 1)))

class AdminAdsAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_ads_add.html")

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }
        obj['ads_publisherid'] = self.getcurrentuser()

        db = DbHelper()
        ads_id = db.SaveAds(obj)

        # 添加图片信息 ##########################
        if self.request.files.has_key('ads_avatar'):
            uploadedfile = self.request.files['ads_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/ads')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SaveAds({ "ads_id" : ads_id, "ads_avatar" : getuniquestring() })
            outfile  = filedir + '/P%s_%s.jpeg' % (ads_id, db.GetAdsAvatarUniqueString(ads_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #########################################

        return self.redirect("/ads")

class AdminAdsDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteAds(the_id)
        return self.write("Success")

class AdminAdsEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryAdsInfo(the_id)
        return self.renderJinjaTemplate("backend/admin_ads_edit.html", objectinfo=objectinfo)

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }
        obj['ads_publisherid'] = self.getcurrentuser()

        if not self.request.files.has_key('ads_avatar'):
            obj.pop('ads_avatar')

        db = DbHelper()
        db.SaveAds(obj)

        # 添加图片信息 ##########################
        ads_id = obj['ads_id']
        if self.request.files.has_key('ads_avatar'):
            uploadedfile = self.request.files['ads_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/ads')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SaveAds({ "ads_id" : ads_id, "ads_avatar" : getuniquestring() })
            outfile  = filedir + '/P%s_%s.jpeg' % (ads_id, db.GetAdsAvatarUniqueString(ads_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #########################################

        return self.redirect("/ads")

class AdminCategory(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_category.html", pageindex=int(self.get_argument("p", 1)))
    
class AdminCategoryAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_category_add.html")

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }
        obj.pop('_xsrf', None)
        db = DbHelper()
        if "category_avatar" in self.request.files:
            _, uuid = self.handle_photos_upload(self.request.files['category_avatar'][0])
            obj['category_avatar'] = uuid
        db.SaveCategory(obj)
        # 添加图片信息 ##########################
        # if self.request.files.has_key('category_avatar'):
        #     uploadedfile = self.request.files['category_avatar'][0]
        #     original_fname = uploadedfile['filename']
        #     extension = os.path.splitext(original_fname)[1]
        #     fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        #     fname = "%s%s" % (fname, getuniquestring())
        #     filename = fname + extension

        #     filedir = os.path.join(abspath, 'static/img/avatar/category')
        #     infile   = filedir + '/' + filename # infile就是用户上传的原始照片

        #     # 自动保存用户上传的照片文件
        #     output_file = open(infile, 'w')
        #     output_file.write(uploadedfile['body'])
        #     output_file.close()

        #     # 将 infile 保存为 jpeg 格式的商品图片
        #     im = Image.open(infile)
        #     avatar_size = (im.size[0], im.size[1])
        #     db.SaveCategory({ "category_id" : category_id, "category_avatar" : getuniquestring() })
        #     outfile  = filedir + '/P%s_%s.jpeg' % (category_id, db.GetCategoryAvatarUniqueString(category_id))

        #     method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
        #     formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
        #     formatted_im.save(outfile, "JPEG", quality=100)

        #     # 删除用户上传的原始文件infile
        #     os.remove(infile)
        # #########################################

        return self.redirect("/category")

class AdminCategoryDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteCategory(the_id)
        return self.write("Success")

class AdminCategoryEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryCategoryInfo(the_id)
        return self.renderJinjaTemplate("backend/admin_category_edit.html", objectinfo=objectinfo)

    @tornado.web.authenticated
    def post(self):
        # obj = { k: self.get_argument(k) for k in self.request.arguments }

        # if not self.request.files.has_key('category_avatar'):
        #     obj.pop('category_avatar')

        # db = DbHelper()
        # db.SaveCategory(obj)
        obj = { k: self.get_argument(k) for k in self.request.arguments }
        obj.pop('_xsrf', None)
        db = DbHelper()
        if "category_avatar" in self.request.files:
            _, uuid = self.handle_photos_upload(self.request.files['category_avatar'][0])
            obj['category_avatar'] = uuid
        else:
            obj.pop('category_avatar')
        db.SaveCategory(obj)
        # # 添加图片信息 ##########################
        # category_id = obj['category_id']
        # if self.request.files.has_key('category_avatar'):
        #     uploadedfile = self.request.files['category_avatar'][0]
        #     original_fname = uploadedfile['filename']
        #     extension = os.path.splitext(original_fname)[1]
        #     fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        #     fname = "%s%s" % (fname, getuniquestring())
        #     filename = fname + extension

        #     filedir = os.path.join(abspath, 'static/img/avatar/category')
        #     infile   = filedir + '/' + filename # infile就是用户上传的原始照片

        #     # 自动保存用户上传的照片文件
        #     output_file = open(infile, 'w')
        #     output_file.write(uploadedfile['body'])
        #     output_file.close()

        #     # 将 infile 保存为 jpeg 格式的商品图片
        #     im = Image.open(infile)
        #     avatar_size = (im.size[0], im.size[1])
        #     db.SaveCategory({ "category_id" : category_id, "category_avatar" : getuniquestring() })
        #     outfile  = filedir + '/P%s_%s.jpeg' % (category_id, db.GetCategoryAvatarUniqueString(category_id))

        #     method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
        #     formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
        #     formatted_im.save(outfile, "JPEG", quality=100)

        #     # 删除用户上传的原始文件infile
        #     os.remove(infile)
        # #########################################

        return self.redirect("/category")

class AdminGym(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_gym.html", pageindex=int(self.get_argument("p", 1)))

class AdminGymAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_gym_add.html")

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        db = DbHelper()
        db.SaveGym(obj)

        return self.redirect("/gym")
    
class AdminGymDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteGym(the_id)
        return self.write("Success")
    
class AdminGymEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryGymInfo(the_id)
        return self.renderJinjaTemplate("backend/admin_gym_edit.html", objectinfo=objectinfo)

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        db = DbHelper()
        db.SaveGym(obj)

        return self.redirect("/gym")

class AdminGymBranch(BaseHandler):

    @tornado.web.authenticated
    def get(self, gym_id):
        return self.renderJinjaTemplate("backend/admin_gymbranch.html", gym_id=gym_id)

class AdminGymBranchEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self, gym_branch_id):
        return self.renderJinjaTemplate("backend/admin_gymbranch_edit.html", gym_branch_id=gym_branch_id)

    @tornado.web.authenticated
    def post(self, gym_branch_id):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        db = DbHelper()
        db.SaveGymBranch(obj)

        gym_id = GetArgumentValue(self, "gym_branch_gymid")
        return self.redirect("/gym/%s/branch" % gym_id)

class AdminGymBranchAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self, gym_id):
        return self.renderJinjaTemplate("backend/admin_gymbranch_add.html", gym_id=gym_id)

    @tornado.web.authenticated
    def post(self, gym_id):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        db = DbHelper()
        gym_branch_id = db.SaveGymBranch(obj)

        gym_id = GetArgumentValue(self, "gym_branch_gymid")
        return self.redirect("/gym/%s/branch" % gym_id)

class AdminGymBranchDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self, gym_branch_id):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteGymBranch(the_id)
        return self.write("Success")
    
class AdminCourse(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_course.html", pageindex=int(self.get_argument("p", 1)))
    
class AdminCourseAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_course_add.html")

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        db = DbHelper()
        course_id = db.SaveCourse(obj)

        # 添加商品图片信息 ##########################
        avatars = self.get_arguments('avatars')
        basedir = os.path.join(abspath, 'static/img/avatar')
        tempdir = os.path.join(basedir, 'temp')
        realdir = os.path.join(basedir, 'course')
        new_avatars_json = []
        for avatar in avatars:
            if avatar.startswith('NEW'):
                _, uniquestring, img_partial_name = avatar.split(':')
                # Move the temporary file to a permanent product avatar file.
                new_unique_string = getuniquestring()
                outfile  = 'P%s_%s.jpeg' % (course_id, new_unique_string)
                os.rename(
                    os.path.join(tempdir, img_partial_name),
                    os.path.join(realdir, outfile)
                )
                new_avatars_json.append(new_unique_string)
            else:
                new_avatars_json.append(avatar)
                
        db.SaveCourse({ "course_id" : course_id, "course_avatar" : json.dumps(new_avatars_json) })
        #########################################

        return self.redirect("/course")
    
class AdminCourseDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteCourse(the_id)
        return self.write("Success")
    
class AdminCourseEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryCourseInfo(the_id)
        return self.renderJinjaTemplate("backend/admin_course_edit.html", objectinfo=objectinfo)

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        db = DbHelper()
        db.SaveCourse(obj)

        # 添加商品图片信息 ##########################
        course_id = obj['course_id']
        avatars = self.get_arguments('avatars')
        basedir = os.path.join(abspath, 'static/img/avatar')
        tempdir = os.path.join(basedir, 'temp')
        realdir = os.path.join(basedir, 'course')
        new_avatars_json = []
        for avatar in avatars:
            if avatar.startswith('NEW'):
                _, uniquestring, img_partial_name = avatar.split(':')
                # Move the temporary file to a permanent product avatar file.
                new_unique_string = getuniquestring()
                outfile  = 'P%s_%s.jpeg' % (course_id, new_unique_string)
                os.rename(
                    os.path.join(tempdir, img_partial_name),
                    os.path.join(realdir, outfile)
                )
                new_avatars_json.append(new_unique_string)
            else:
                new_avatars_json.append(avatar)

        db.SaveCourse({ "course_id" : course_id, "course_avatar" : json.dumps(new_avatars_json) })
        #########################################
        
        return self.redirect("/course")

class AdminSchedule(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_schedule.html", pageindex=int(self.get_argument("p", 1)))
    
class AdminScheduleAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_schedule_add.html")

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        schedule_date =  self.get_arguments('schedule_date')
        schedule_stock =  self.get_arguments('schedule_stock')

        # logging.debug("--- schedule_date: %r" % schedule_date)
        # logging.debug("--- schedule_stock: %r" % schedule_stock)

        course_schedule_stock = {}
        for i in range(len(schedule_date)):
            course_schedule_stock[str(schedule_date[i])] = int(schedule_stock[i])
        obj['course_schedule_stock'] = json.dumps(course_schedule_stock)

        db = DbHelper()
        db.SaveSchedule(obj)

        return self.redirect("/schedule")
    
class AdminScheduleDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteSchedule(the_id)
        return self.write("Success")
    
class AdminScheduleCopy(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.CopySchedule(the_id)
        return self.write("Success")

class AdminScheduleEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryScheduleInfo(the_id)
        return self.renderJinjaTemplate("backend/admin_schedule_edit.html", objectinfo=objectinfo)

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        schedule_date =  self.get_arguments('schedule_date')
        schedule_stock =  self.get_arguments('schedule_stock')

        # logging.debug("--- schedule_date: %r" % schedule_date)
        # logging.debug("--- schedule_stock: %r" % schedule_stock)

        course_schedule_stock = {}
        for i in range(len(schedule_date)):
            course_schedule_stock[str(schedule_date[i])] = int(schedule_stock[i])
        obj['course_schedule_stock'] = json.dumps(course_schedule_stock)

        db = DbHelper()
        db.SaveSchedule(obj)

        return self.redirect("/schedule")

class AdminTeacher(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_teacher.html", pageindex=int(self.get_argument("p", 1)))
    
class AdminTeacherAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_teacher_add.html")

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        db = DbHelper()
        teacher_id = db.SaveTeacher(obj)

        # 添加商品图片信息 ##########################
        avatars = self.get_arguments('avatars')
        basedir = os.path.join(abspath, 'static/img/avatar')
        tempdir = os.path.join(basedir, 'temp')
        realdir = os.path.join(basedir, 'teacher')
        new_avatars_json = []
        for avatar in avatars:
            if avatar.startswith('NEW'):
                _, uniquestring, img_partial_name = avatar.split(':')
                # Move the temporary file to a permanent product avatar file.
                new_unique_string = getuniquestring()
                outfile  = 'P%s_%s.jpeg' % (teacher_id, new_unique_string)
                os.rename(
                    os.path.join(tempdir, img_partial_name),
                    os.path.join(realdir, outfile)
                )
                new_avatars_json.append(new_unique_string)
            else:
                new_avatars_json.append(avatar)
                
        db.SaveTeacher({ "teacher_id" : teacher_id, "teacher_avatar" : json.dumps(new_avatars_json) })
        #########################################
        # 添加图片信息 ############################
        if self.request.files.has_key('teacher_idcard_avatar'):
            uploadedfile = self.request.files['teacher_idcard_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/teacher')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SaveTeacher({ "teacher_id" : teacher_id, "teacher_idcard_avatar" : getuniquestring() })
            outfile  = filedir + '/IDC%s_%s.jpeg' % (teacher_id, db.GetTeacherIDCardAvatarUniqueString(teacher_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        ###########################################
        # 添加图片信息 ##############################
        if self.request.files.has_key('teacher_permit_avatar'):
            uploadedfile = self.request.files['teacher_permit_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/teacher')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SaveTeacher({ "teacher_id" : teacher_id, "teacher_permit_avatar" : getuniquestring() })
            outfile  = filedir + '/PMT%s_%s.jpeg' % (teacher_id, db.GetTeacherPermitAvatarUniqueString(teacher_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #############################################

        return self.redirect("/teacher")
    
class AdminTeacherDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteTeacher(the_id)
        return self.write("Success")
    
class AdminTeacherEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryTeacherInfo(the_id)
        return self.renderJinjaTemplate("backend/admin_teacher_edit.html", objectinfo=objectinfo)

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        # if not self.request.files.has_key('teacher_idcard_avatar'):
        #     obj.pop('teacher_idcard_avatar')
        # if not self.request.files.has_key('teacher_permit_avatar'):
        #     obj.pop('teacher_permit_avatar')

        db = DbHelper()
        db.SaveTeacher(obj)

        # 添加商品图片信息 ##########################
        teacher_id = obj['teacher_id']
        avatars = self.get_arguments('avatars')
        basedir = os.path.join(abspath, 'static/img/avatar')
        tempdir = os.path.join(basedir, 'temp')
        realdir = os.path.join(basedir, 'teacher')
        new_avatars_json = []
        for avatar in avatars:
            if avatar.startswith('NEW'):
                _, uniquestring, img_partial_name = avatar.split(':')
                # Move the temporary file to a permanent product avatar file.
                new_unique_string = getuniquestring()
                outfile  = 'P%s_%s.jpeg' % (teacher_id, new_unique_string)
                os.rename(
                    os.path.join(tempdir, img_partial_name),
                    os.path.join(realdir, outfile)
                )
                new_avatars_json.append(new_unique_string)
            else:
                new_avatars_json.append(avatar)

        db.SaveTeacher({ "teacher_id" : teacher_id, "teacher_avatar" : json.dumps(new_avatars_json) })
        #########################################
        # 添加图片信息 ############################
        if self.request.files.has_key('teacher_idcard_avatar'):
            uploadedfile = self.request.files['teacher_idcard_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/teacher')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SaveTeacher({ "teacher_id" : teacher_id, "teacher_idcard_avatar" : getuniquestring() })
            outfile  = filedir + '/IDC%s_%s.jpeg' % (teacher_id, db.GetTeacherIDCardAvatarUniqueString(teacher_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #########################################
        # 添加图片信息 ############################
        if self.request.files.has_key('teacher_permit_avatar'):
            uploadedfile = self.request.files['teacher_permit_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/teacher')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SaveTeacher({ "teacher_id" : teacher_id, "teacher_permit_avatar" : getuniquestring() })
            outfile  = filedir + '/PMT%s_%s.jpeg' % (teacher_id, db.GetTeacherPermitAvatarUniqueString(teacher_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #########################################

        return self.redirect("/teacher")

class AdminImageUpload(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        '''Used for iframe upload'''
        files = self.request.files['product_avatar']
        if not files:
            return self.write(0)
        uploadedfile = self.request.files['product_avatar'][0]
        original_fname = uploadedfile['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        fname = "%s%s" % (fname, getuniquestring())
        filename = fname + extension

        filedir = os.path.join(abspath, 'static/img/avatar/temp')
        if not os.path.exists(filedir):
            os.mkdir(filedir)

        infile   = filedir + '/' + filename # infile就是用户上传的原始照片

        # 自动保存用户上传的照片文件
        output_file = open(infile, 'w')
        output_file.write(uploadedfile['body'])
        output_file.close()

        # 将 infile 保存为 jpeg 格式的商品图片
        # 对上传的原始照片文件进行剪裁，宽度固定为448px, 高度可变
        max_width = 1280
        # avatar_size = (avatarwidth, AVATAR_MAXHEIGHT)
        avatar_size = (1280, 853)
        im = Image.open(infile)
        im_width = im.size[0]
        im_height = im.size[1]

        # if not check_avatar_image_ratio(im_width, im_height):
            # os.remove(infile)
            # result = 1  # Image size incorrect.
        # else:

        shrink_ratio = float(min(max_width, im_width)) / im_width
        final_size = int(im_width * shrink_ratio), int(im_height * shrink_ratio)

        method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
        formatted_im = ImageOps.fit(im, final_size, method = method, centering = (0.5, 0.5))
        formatted_im.save(infile, "JPEG", quality=100)
        # watermark.watermark(infile, watermark.MARKIMAGE, watermark.POSITION[4], opacity=0.7).save(infile, quality=90)
        result = 0

        path = '/static/img/avatar/temp/%s' % filename
        return self.write("<script type='text/javascript'>window.top.window.stopUpload(%s, '%s', '%s');</script>" % (result, fname, filename))

class AdminOrder(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_order.html", pageindex=int(self.get_argument("p", 1)))
    
class AdminOrderAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        pass
    
class AdminOrderDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteOrder(the_id)
        return self.write("Success")
    
class AdminOrderEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        pass

############################################################################################################################################################################################

class AdminPrivateTeacher(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_private_teacher.html", pageindex=int(self.get_argument("p", 1)))

class AdminPrivateTeacherAdd(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_private_teacher_add.html")

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        db = DbHelper()
        private_teacher_id = db.SavePrivateTeacher(obj)

        # 添加商品图片信息 ##########################
        avatars = self.get_arguments('avatars')
        basedir = os.path.join(abspath, 'static/img/avatar')
        tempdir = os.path.join(basedir, 'temp')
        realdir = os.path.join(basedir, 'privateteacher')
        new_avatars_json = []
        for avatar in avatars:
            if avatar.startswith('NEW'):
                _, uniquestring, img_partial_name = avatar.split(':')
                # Move the temporary file to a permanent product avatar file.
                new_unique_string = getuniquestring()
                outfile  = 'P%s_%s.jpeg' % (private_teacher_id, new_unique_string)
                os.rename(
                    os.path.join(tempdir, img_partial_name),
                    os.path.join(realdir, outfile)
                )
                new_avatars_json.append(new_unique_string)
            else:
                new_avatars_json.append(avatar)
                
        db.SavePrivateTeacher({ "private_teacher_id" : private_teacher_id, "private_teacher_avatar" : json.dumps(new_avatars_json) })
        #########################################
        # 添加图片信息 ############################
        if self.request.files.has_key('private_teacher_idcard_avatar'):
            uploadedfile = self.request.files['private_teacher_idcard_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/privateteacher')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SavePrivateTeacher({ "private_teacher_id" : private_teacher_id, "private_teacher_idcard_avatar" : getuniquestring() })
            outfile  = filedir + '/IDC%s_%s.jpeg' % (private_teacher_id, db.GetPrivateTeacherIDCardAvatarUniqueString(private_teacher_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        ###########################################
        # 添加图片信息 ##############################
        if self.request.files.has_key('private_teacher_permit_avatar'):
            uploadedfile = self.request.files['private_teacher_permit_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/privateteacher')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SavePrivateTeacher({ "private_teacher_id" : private_teacher_id, "private_teacher_permit_avatar" : getuniquestring() })
            outfile  = filedir + '/PMT%s_%s.jpeg' % (private_teacher_id, db.GetPrivateTeacherPermitAvatarUniqueString(private_teacher_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #############################################

        return self.redirect("/privateteacher")

class AdminPrivateTeacherDelete(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeletePrivateTeacher(the_id)
        return self.write("Success")

class AdminPrivateTeacherEdit(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryPrivateTeacherInfo(the_id)
        return self.renderJinjaTemplate("backend/admin_private_teacher_edit.html", objectinfo=objectinfo)

    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }

        # if not self.request.files.has_key('private_teacher_idcard_avatar'):
        #     obj.pop('private_teacher_idcard_avatar')
        # if not self.request.files.has_key('private_teacher_permit_avatar'):
        #     obj.pop('private_teacher_permit_avatar')

        db = DbHelper()
        db.SavePrivateTeacher(obj)

        # 添加商品图片信息 ##########################
        private_teacher_id = obj['private_teacher_id']
        avatars = self.get_arguments('avatars')
        basedir = os.path.join(abspath, 'static/img/avatar')
        tempdir = os.path.join(basedir, 'temp')
        realdir = os.path.join(basedir, 'privateteacher')
        new_avatars_json = []
        for avatar in avatars:
            if avatar.startswith('NEW'):
                _, uniquestring, img_partial_name = avatar.split(':')
                # Move the temporary file to a permanent product avatar file.
                new_unique_string = getuniquestring()
                outfile  = 'P%s_%s.jpeg' % (private_teacher_id, new_unique_string)
                os.rename(
                    os.path.join(tempdir, img_partial_name),
                    os.path.join(realdir, outfile)
                )
                new_avatars_json.append(new_unique_string)
            else:
                new_avatars_json.append(avatar)

        db.SavePrivateTeacher({ "private_teacher_id" : private_teacher_id, "private_teacher_avatar" : json.dumps(new_avatars_json) })
        #########################################
        # 添加图片信息 ############################
        if self.request.files.has_key('private_teacher_idcard_avatar'):
            uploadedfile = self.request.files['private_teacher_idcard_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/privateteacher')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SavePrivateTeacher({ "private_teacher_id" : private_teacher_id, "private_teacher_idcard_avatar" : getuniquestring() })
            outfile  = filedir + '/IDC%s_%s.jpeg' % (private_teacher_id, db.GetPrivateTeacherIDCardAvatarUniqueString(private_teacher_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #########################################
        # 添加图片信息 ############################
        if self.request.files.has_key('private_teacher_permit_avatar'):
            uploadedfile = self.request.files['private_teacher_permit_avatar'][0]
            original_fname = uploadedfile['filename']
            extension = os.path.splitext(original_fname)[1]
            fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
            fname = "%s%s" % (fname, getuniquestring())
            filename = fname + extension

            filedir = os.path.join(abspath, 'static/img/avatar/privateteacher')
            infile   = filedir + '/' + filename # infile就是用户上传的原始照片

            # 自动保存用户上传的照片文件
            output_file = open(infile, 'w')
            output_file.write(uploadedfile['body'])
            output_file.close()

            # 将 infile 保存为 jpeg 格式的商品图片
            im = Image.open(infile)
            avatar_size = (im.size[0], im.size[1])
            db.SavePrivateTeacher({ "private_teacher_id" : private_teacher_id, "private_teacher_permit_avatar" : getuniquestring() })
            outfile  = filedir + '/PMT%s_%s.jpeg' % (private_teacher_id, db.GetPrivateTeacherPermitAvatarUniqueString(private_teacher_id))

            method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
            formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5, 0.5))
            formatted_im.save(outfile, "JPEG", quality=100)

            # 删除用户上传的原始文件infile
            os.remove(infile)
        #########################################

        return self.redirect("/privateteacher")
    
class AdminPushNotification(BaseHandler):

    def string_width(self, text):
        import unicodedata
        s = 0
        for ch in text:
            if isinstance(ch, unicode):
                if unicodedata.east_asian_width(ch) != 'Na':
                    s += 3
                else:
                    s += 1
            else:
                s += 1
        return s

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("backend/admin_pushnotification.html", verifyResponse={ "isNotifContentValid" : True, "isNotifObjectValid" : True }, notif_object="1,2,3")

    def post(self):
        notif_title = GetArgumentValue(self, "notif_title")
        notif_content = GetArgumentValue(self, "notif_content")
        notif_object = GetArgumentValue(self, "notif_object")

        isNotifContentValid = True if notif_content is not None else False
        if isNotifContentValid:
            isNotifContentValid = False if self.string_width(notif_content) > 180 else True
            # return self.write("%s" % self.string_width(notif_content))
        isNotifObjectValid = True if notif_object is not None else False

        if isNotifContentValid == False or isNotifObjectValid == False:
            return self.renderJinjaTemplate("backend/admin_pushnotification.html", verifyResponse={ "isNotifContentValid" : isNotifContentValid, 
                "isNotifObjectValid" : isNotifObjectValid, "PushSuccess" : False }, notif_object=notif_object if notif_object is not None else "")
        else:
            _jpush = jpush.JPush(Settings.JPUSH["app_key"], Settings.JPUSH["master_secret"])
            push = _jpush.create_push()
            push.options = { "apns_production" : False }
            push.audience = jpush.all_
            # iOS & Android
            if "1" in notif_object and "2" in notif_object:
                if notif_title is not None:
                    push.notification = jpush.notification(
                        android=jpush.android(alert=notif_content, title=notif_title), 
                        ios=jpush.ios(alert=notif_content))
                else:
                    push.notification = jpush.notification(
                        android=jpush.android(alert=notif_content), 
                        ios=jpush.ios(alert=notif_content))
                push.platform = jpush.all_
                try:
                    push.send()
                except Exception, e:
                    return self.renderJinjaTemplate("backend/admin_pushnotification.html", verifyResponse={ "isNotifContentValid" : True, 
                        "isNotifObjectValid" : True, "PushSuccess" : False }, notif_object=notif_object if notif_object is not None else "")
            # iOS
            elif "1" in notif_object and "2" not in notif_object:
                push.notification = jpush.notification(ios=jpush.ios(alert=notif_content))
                push.platform = jpush.platform('ios')
                try:
                    push.send()
                except Exception, e:
                    return self.renderJinjaTemplate("backend/admin_pushnotification.html", verifyResponse={ "isNotifContentValid" : True, 
                        "isNotifObjectValid" : True, "PushSuccess" : False }, notif_object=notif_object if notif_object is not None else "")
            # Android
            elif "1" not in notif_object and "2" in notif_object:
                if notif_title is not None:
                    push.notification = jpush.notification(android=jpush.android(alert=notif_content, title=notif_title))
                else:
                    push.notification = jpush.notification(android=jpush.android(alert=notif_content))
                push.platform = jpush.platform('android')
                try:
                    push.send()
                except Exception, e:
                    return self.renderJinjaTemplate("backend/admin_pushnotification.html", verifyResponse={ "isNotifContentValid" : True, 
                        "isNotifObjectValid" : True, "PushSuccess" : False }, notif_object=notif_object if notif_object is not None else "")
            
            return self.renderJinjaTemplate("backend/admin_pushnotification.html", verifyResponse={ "isNotifContentValid" : True, 
                "isNotifObjectValid" : True, "PushSuccess" : True }, notif_object=notif_object if notif_object is not None else "")


class AdminCoachAuth(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.renderJinjaTemplate('backend/admin_coachauth.html', pageindex=int(self.get_argument("p", 1)))
    @tornado.web.authenticated
    def post(self):
        auth_id = self.get_argument('authid')
        auth = self.get_argument('auth')
        msg = self.get_argument('msg')
        if auth in ("1", "-1"):
            db = DbHelper()
            db.SaveCoachAuth(
                auto_prefix=True,
                id=auth_id,
                status=1 if auth == "1" else 2,
                message=msg,
            )
        self.redirect('/coachauth')

class AdminEntry(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.renderJinjaTemplate('backend/admin_entry.html', pageindex=int(self.get_argument("p", 1)))

class AdminEntryAdd(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        entry_parentid = self.get_argument('pid', -1)
        db = DbHelper()
        entry_info = db.QueryEntryInfo(entry_id=entry_parentid)
        self.renderJinjaTemplate(
            'backend/admin_entry_add.html',
            parent_entry=entry_info, )
    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }
        obj.pop('_xsrf', None)
        db = DbHelper()
        if "entry_image" in self.request.files:
            _, uuid = self.handle_photos_upload(self.request.files['entry_image'][0])
            obj['entry_image'] = uuid
        db.SaveEntry(**obj)
        return self.redirect("/entry")

class AdminEntryEdit(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        the_id = self.get_argument("id", None)
        db = DbHelper()
        objectinfo = db.QueryEntryInfo(the_id)
        self.renderJinjaTemplate('backend/admin_entry_edit.html', objectinfo=objectinfo)
    @tornado.web.authenticated
    def post(self):
        obj = { k: self.get_argument(k) for k in self.request.arguments }
        obj.pop('_xsrf', None)
        db = DbHelper()
        if "entry_image" in self.request.files:
            files = self.request.files['entry_image'][0]            
            _, uuid = self.handle_photos_upload(files)
            obj['entry_image'] = uuid
        else:
            obj.pop('entry_image')
        db.SaveEntry(**obj)
        return self.redirect("/entry")


class AdminEntryDelete(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        the_id = self.get_argument("the_id")
        db = DbHelper()
        db.DeleteEntry(the_id)
        return self.write("Success")
############################################################################################################################################################################################
############################################################################################################################################################################################

class ApiUserLogin(XsrfBaseHandler):
    def post(self):
        serveraddress = self.request.headers.get("Host")

        username = GetArgumentValue(self, "UserName")
        password = GetArgumentValue(self, "UserPassword")

        if username is None or password is None:
            jsondata = self.request.headers.get("json", None)
            jsondict = json.loads(jsondata)
            username = jsondict["UserName"] if jsondict.has_key("UserName") else None
            password = jsondict["UserPassword"] if jsondict.has_key("UserPassword") else None

        db = DbHelper()
        checkuserstatus = db.CheckUser(username, password)

        # logging.debug("username: %r, password: %r, checkuserstatus: %r" % (username, password, checkuserstatus))

        if checkuserstatus < 0:
            # -2 - 无此帐户， -1 - 验证失败， 1 - 验证成功
            resultlist = { "result" : str(checkuserstatus) }

            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            userinfo = db.QueryUserInfoByNameOrPhonenumber(username)
            userinfo['user_qrcodelink'] = 'http://%s/api/v2.0/df/' % serveraddress + qr.encrypt(userinfo["user_name"] + userinfo["user_password"])
            userinfo['user_iscoach'] = db.IsCoach(userinfo['user_id'])
            useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(userinfo["user_id"])[0])
            resultlist = { "result" : "1", "UserInfo" : userinfo, "UserAvatar" : useravatarurl }

            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiUserCheckState(XsrfBaseHandler):
    def post(self):
        serveraddress = self.request.headers.get("Host")

        userid = GetArgumentValue(self, "UID")
        password = GetArgumentValue(self, "UserPassword")
        devicetoken = GetArgumentValue(self, "DeviceToken")

        if userid is None or password is None or devicetoken is None:
            jsondata = self.request.headers.get("json", None)
            jsondict = json.loads(jsondata)

            userid = jsondict["UID"]
            password = jsondict["UserPassword"]
            devicetoken = jsondict["DeviceToken"] if jsondict.has_key("DeviceToken") else None

        db = DbHelper()
        checkuserstatus = db.CheckUserByID(userid, password)

        # # 先判读某个 deviceid 是否有注册过（即一个 deviceid 是否生成过 type 为 3 的兑奖券）如果没有注册过则注册 deviceid
        # if db.IsDeviceIDExistInCoupon(deviceid=devicetoken) == False and devicetoken is not None:
        #     db.AddCoupon({ "coupon_userid" : 0, "coupon_type" : 3, "coupon_amount" : 0, "coupon_source" : 9, "coupon_giftcode_deviceid" : devicetoken }, couponvaliddays=99999)

        # # 判断此 deviceid 对应的兑奖券是否已经兑换过礼品
        # giftcode = 0
        # couponinfo = db.QueryCouponInfoByDeviceID(devicetoken)
        # if couponinfo is not None:
        #     # 如果没有兑换过则返回真实的 "GiftCode" 号码
        #     coupon_valid = couponinfo[3] if not db.IsDbUseDictCursor() else couponinfo["coupon_valid"]
        #     if coupon_valid == 1:
        #         giftcode = couponinfo[2] if not db.IsDbUseDictCursor() else couponinfo["coupon_serialnumber"]

        #     # 如果已经兑换过则返回 0 的 "GiftCode"
        #     else:
        #         giftcode = 0
        # else:
        #     giftcode = 0

        if int(checkuserstatus) < 0:
            resultlist = { "result" : "0" }

            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            userinfo = db.QueryUserInfoById(userid)
            useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(userinfo["user_id"])[0])
            userinfo["user_avatar"] = useravatarurl
            resultlist = { "result" : "1", "UserInfo" : userinfo }

            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiUserRegister(XsrfBaseHandler):
    def post(self):
        ''' -1, 用户名为空
            -2, 用户名已存在
            -3, 用户名长度不合法（应为 2 - 32 位）
             0, 注册失败
             1, 注册成功
             3, 密码长度不合法（应为 6 - 32 位）
             4, 密码格式不正确（不能包含空格）
        '''
        db = DbHelper()
        serveraddress = self.request.headers.get("Host")

        # user_id = cgi.escape(self.get_argument("uid"))
        user_name = GetArgumentValue(self, "UserName")
        user_phonenumber = GetArgumentValue(self, "UserPhonenumber")
        user_password = GetArgumentValue(self, "UserPassword")
        user_gender = GetArgumentValue(self, "UserGender")
        user_height = GetArgumentValue(self, "UserHeight")
        user_weight = GetArgumentValue(self, "UserWeight")
        user_nickname = GetArgumentValue(self, "UserNickName") if IsArgumentEmpty(self, "UserNickName") == False else user_name

        # logging.debug("--- user_name: %r, user_phonenumber: %r, user_password: %r, user_gender: %r, user_height: %r, user_weight: %r, user_nickname: %r" % (user_name, user_phonenumber, user_password, user_gender, user_height, user_weight, user_nickname))

        # 第三方注册用户，保存用户的 openid
        if IsArgumentEmpty(self, "WeChatOpenID") == False:
            user_wechatopenid = GetArgumentValue(self, "WeChatOpenID")

            # logging.debug("--- ApiUserRegister wechatunionid: %r" % user_wechatopenid)

            user_qqopenid = None
            user_sinauid = None
            user_vendorcreditrating = 1

            while db.IsUserExist(user_name):
                randstr = str(time.time()).replace(".", "")[-3:]
                user_name = "%s%s" % (user_name, randstr)
        elif IsArgumentEmpty(self, "QQOpenID") == False:
            user_wechatopenid = None
            user_qqopenid = GetArgumentValue(self, "QQOpenID")
            user_sinauid = None
            user_vendorcreditrating = 2

            while db.IsUserExist(user_name):
                randstr = str(time.time()).replace(".", "")[-3:]
                user_name = "%s%s" % (user_name, randstr)
        elif IsArgumentEmpty(self, "SinaUID") == False:
            user_wechatopenid = None
            user_qqopenid = None
            user_sinauid = GetArgumentValue(self, "SinaUID")
            user_vendorcreditrating = 3

            while db.IsUserExist(user_name):
                randstr = str(time.time()).replace(".", "")[-3:]
                user_name = "%s%s" % (user_name, randstr)
        else:
            user_wechatopenid = None
            user_qqopenid = None
            user_sinauid = None
            user_vendorcreditrating = 0

        if user_name is None or user_password is None:
            user_name = jsondict["UserName"] if jsondict.has_key("UserName") else None
            user_password = jsondict["UserPassword"] if jsondict.has_key("UserPassword") else None

        usernameret = self.isValidUsername(user_name)
        passwordret = self.isValidPassword(user_password)

        if usernameret != 1:
            jsonstr = json.dumps({ "result" : "%s" % usernameret }, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')

            # logging.debug("--- result: %r" % usernameret)

            return self.write(jsonstr)

        if passwordret != 1:
            jsonstr = json.dumps({ "result" : "%s" % passwordret }, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')

            # logging.debug("--- result: %r" % passwordret)

            return self.write(jsonstr)

        registersource = 2 if self.is_ios() else 3
        user_id = db.SaveUser({"user_name" : user_name, 
                "user_nickname" : user_nickname, 
                "user_password" : user_password, 
                "user_phonenumber" : user_phonenumber, 
                "user_role" : 1, 
                "user_wechatopenid" : user_wechatopenid, 
                "user_qqopenid" : user_qqopenid, 
                "user_sinauid" : user_sinauid, 
                "user_registersource" : registersource, 
                "user_gender" : user_gender,
                "user_height" : user_height,
                "user_weight" : user_weight,
                "user_registerip" : self.request.remote_ip})
        if user_id != 0:
            self.uploadUserAvatar(user_id)
            userinfo = db.QueryUserInfoById(user_id)
            useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(user_id)[0])

            # logging.debug("--- result: 1")

            resultlist = { "result" : "1", "UserInfo" : userinfo, "UserAvatar" : useravatarurl }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            # logging.debug("--- result: 0")

            jsonstr = json.dumps({"result" : "0"}, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

    def uploadUserAvatar(self, user_id):
        AVATAR_MAXWIDTH  = 300
        AVATAR_MAXHEIGHT = 300
        db = DbHelper()

        # user_id = cgi.escape(self.get_argument("uid"))
        userinfo = db.QueryUserInfoById(user_id)
        theuserid = user_id

        if not self.request.files.has_key('myfile'):
            return

        uploadedfile = self.request.files['myfile'][0]
        original_fname = uploadedfile['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        filename = fname + extension

        filedir = os.path.join(abspath, 'static/img/avatar/user')
        infile   = filedir + '/' + filename # infile就是用户上传的原始照片
        outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 自动保存用户上传的照片文件
        output_file = open(infile, 'w')
        output_file.write(uploadedfile['body'])
        output_file.close()

        # 对上传的原始照片文件进行剪裁，宽度固定为240px, 高度可变
        # avatar_size = (AVATAR_MAXWIDTH, AVATAR_MAXHEIGHT)
        im = Image.open(infile)
        # im_width = im.size[0]
        # im_height = im.size[1]
        # if im_width == im_height:
        #     avatar_size = (AVATAR_MAXWIDTH, AVATAR_MAXHEIGHT)
        # elif im_width < im_height:
        #     avatar_size = (AVATAR_MAXWIDTH, im_height if im_height < AVATAR_MAXHEIGHT else AVATAR_MAXHEIGHT)
        # else:
        #     avatar_size = (AVATAR_MAXWIDTH, int(im_height * (float(AVATAR_MAXHEIGHT) / im_width)))
        avatar_size = im.size

        # 将用户上传的原始照片文件infile经处理保存为outfile_temp
        formatted_im = ImageOps.fit(im, avatar_size, Image.ANTIALIAS, centering = (0.5, 0.5))
        formatted_im.save(outfile_temp, "JPEG")
        avatarfile = '/static/img/avatar/user/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 为了节约服务器空间，删除用户上传的原始照片文件
        os.remove(infile)

        # 将用户选择的照片文件上传到服务器
        outfile  = filedir + '/P%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
        # outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        avatar_large =   filedir + '/L%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 将预览大图outfile_temp正式命名为outfile (outfile在用户个人资料中显示)
        if os.path.exists(outfile_temp) == True:
            outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
            if os.path.exists(outfile) == True:
                os.remove(outfile)
            if os.path.exists(avatar_large) == True:
                os.remove(avatar_large)
            db.SaveUser({ "user_id" : user_id, "user_avatar" : getuniquestring() })
            outfile  = filedir + '/P%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
            shutil.move(outfile_temp, outfile)

        # 保存用户头像时有三咱规格， large(100x100), normal(50x50)和small(25x25)
        avatar_large = filedir + '/L%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 如果用户没用通过file input控件上传照片，则使用缺省照片作为预览大图
        if os.path.exists(outfile) == False:
            outfile = filedir + '/default_avatar.jpeg'

        # 将上一步中正方形不定大小照片通过PIL库保存为100x100像素的用户大头像
        # size = 100, 100
        size = avatar_size
        im = Image.open(outfile)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(avatar_large, "JPEG")

        # resultlist = { "result" : "1" }
        # jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        # self.set_header('Content-Type','application/json')
        # self.write(jsonstr)

    def GetImagePixelSize(self, imagefilepath):
        imout = Image.open(imagefilepath)
        newsize = imout.size
        return newsize

    def isValidPassword(self, password1):
        ''' 4, 密码格式不正确（不能包含空格）
            3, 密码长度不合法（应为 6 - 32 位）
            1, 密码合法
        '''
        if password1 is None or (' ' in password1):
            return 4
        if len(password1) < 6 or len(password1) > 32:
            return 3
        else:
            return 1

    def isValidUsername(self, username):
        ''' -1, 用户名为空
            -2, 用户名已存在
            -3, 用户名长度不合法（应为 2 - 32 位）
            1,  用户名合法
        '''
        db = DbHelper()
        if self.isstringempty(username):
            return -1
        else:
            if db.IsUserExist(username):
                return -2
            else:
                if len(username) < 2 or len(username) > 32:
                    return -3
                else:
                    return 1

    def isstringempty(self, strval):
        argvalue = strval
        ret = False
        if argvalue is None:
            ret = True
        else:
            if len(str(argvalue)) == 0:
                ret = True
            else:
                ret = False
        return ret

class ApiSendSmsCodeRegistration(XsrfBaseHandler):
    def post(self):
        '''  1：发送成功
             0：手机号码已经被注册
            -1：发送失败
            -2：手机号码为空
            -3：手机号码格式不正确
        '''
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)
        phonenumber = jsondict["mobilePhone"]
        verifyCode = getuniquestring()[3:9]

        url = Settings.EMPP_URL
        message = "欢迎使用趣健身，您的验证码为：%s，请尽快使用，动起来，让生活更精彩！" % verifyCode

        # logging.debug("--- verifyCode: %r" % verifyCode)

        if phonenumber:
            db = DbHelper()
            if db.IsPhonenumberExist(phonenumber):
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                if re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
                    postparam = Settings.EMPP_POST_PARAM
                    postparam["mobile"] = phonenumber
                    postparam["content"] = message
                    response = requests.post(url, postparam)

                    if response.status_code == 200:
                        self.set_secure_cookie("SMSCODE", verifyCode, expires_days=0.1)

                        resultlist = { "result" : "1", "VerifyCode" : verifyCode }
                        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                        self.set_header('Content-Type','application/json')
                        self.write(jsonstr)
                    else:
                        resultlist = { "result" : "-1" }
                        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                        self.set_header('Content-Type','application/json')
                        self.write(jsonstr)
                else:
                    resultlist = { "result" : "-3" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
        else:
            resultlist = { "result" : "-2" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiSendSmsCodeFindpassword(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)
        phonenumber = jsondict["mobilePhone"]
        verifyCode = getuniquestring()[3:9]

        url = Settings.EMPP_URL
        message = "您的验证码为：%s，切勿告知他人，请在页面中输入以完成验证！" % verifyCode

        if phonenumber:
            db = DbHelper()
            if db.IsPhonenumberExist(phonenumber) == False:
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                postparam = Settings.EMPP_POST_PARAM
                postparam["mobile"] = phonenumber
                postparam["content"] = message
                response = requests.post(url, postparam)

                if response.status_code == 200:
                    self.set_secure_cookie("SMSCODE", verifyCode, expires_days=0.1)

                    resultlist = { "result" : "1", "VerifyCode" : verifyCode }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
                else:
                    resultlist = { "result" : "-1" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
        else:
            resultlist = { "result" : "-2" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiAdsList(BaseHandler):
    def get(self):
        db = DbHelper()
        adslist = db.QueryAds(0, showAllAds=0)

        serveraddress = self.request.headers.get("Host")
        for adsinfo in adslist:
            adsinfo['ads_avatar'] = 'http://%s%s' % (serveraddress, db.GetAdsAvatarPreview(adsinfo['ads_id'])[0])
            adsinfo['ads_restriction'] = adsinfo and json_safe_loads(adsinfo['ads_restriction']) or []

        resultlist = { "result" : 1, "AdsList" : adslist }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiCourseList(BaseHandler):
    def get(self):
        db = DbHelper()
        course_list = db.QueryCourse(0, 0)
        resultlist = { "result" : 1, "CourseList" : course_list }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiCourseCategoryList(BaseHandler):

    def get(self):
        db = DbHelper()
        course_category_list = db.QueryCategory(0, 5, category_type=1)

        serveraddress = self.request.headers.get("Host")

        courseadsinfo = db.QueryAds(0, 0, ads_position=98)
        if courseadsinfo and len(courseadsinfo) > 0:
            course_avatar = 'http://%s%s' % (serveraddress, db.GetAdsAvatarPreview(courseadsinfo[0]['ads_id'])[0])
        else:
            course_avatar = 'http://%s%s' % (serveraddress, db.GetAdsAvatarPreview(0)[0])

        for categoryinfo in course_category_list:
            categoryinfo['category_avatar'] = 'http://%s%s' % (serveraddress, db.GetCategoryAvatarPreview(categoryinfo['category_id'])[0])

        resultlist = {'result': 1, 'CourseCategoryList': course_category_list, 'CourseAvatar' : course_avatar}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiTeacherCategoryList(BaseHandler):
    def get(self):
        db = DbHelper()
        teacher_category_list = db.QueryCategory(0, 5, category_type=2)

        serveraddress = self.request.headers.get("Host")
        teacheradsinfo = db.QueryAds(0, 0, ads_position=99)
        if teacheradsinfo and len(teacheradsinfo) > 0:
            teacher_avatar = 'http://%s%s' % (serveraddress, db.GetAdsAvatarPreview(teacheradsinfo[0]['ads_id'])[0])
        else:
            teacher_avatar = 'http://%s%s' % (serveraddress, db.GetAdsAvatarPreview(0)[0])

        for categoryinfo in teacher_category_list:
            categoryinfo['category_avatar'] = 'http://%s%s' % (serveraddress, db.GetCategoryAvatarPreview(categoryinfo['category_id'])[0])

        resultlist = {'result': 1, 'TeacherCategoryList': teacher_category_list, 'TeacherAvatar' : teacher_avatar}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCourseScheduleList(BaseHandler):
    def get(self):
        startpos = int(GetArgumentValue(self, 'startposition') or 0)
        count = int(GetArgumentValue(self, 'count') or 20)
        user_id = GetArgumentValue(self, 'user_id')

        # ====================
        data = {}
        data['course_date'] = GetArgumentValue(self, 'course_date')
        data['course_schedule_begintime__gte'] = GetArgumentValue(self, 'course_starttime')
        data['course_schedule_endtime__lte'] = GetArgumentValue(self, 'course_endtime')
        data['category_name'] = GetArgumentValue(self, 'course_type')
        data['gym_branch_businesscircle'] = GetArgumentValue(self, 'course_businesscircle')
        data['gym_branch_district'] = GetArgumentValue(self, 'course_district')
        data['gym_branch_id'] = GetArgumentValue(self, 'gym_branch_id')
        data['course_schedule_courseid'] = GetArgumentValue(self, 'course_id')
        data['course_schedule_id'] = GetArgumentValue(self, 'course_schedule_id')
        copyschedule = GetArgumentValue(self, 'copyschedule') or 1
        db = DbHelper()
        if data['course_date']:
            datestr = data.get('course_date')
            data['course_schedule_month'], data['course_schedule_day'] = db.getMonthWeekdayByDate(datestr)
        if user_id:
            star_jsonstr = db.QueryUserInfoById(user_id)['user_star_gymbranch']
            if star_jsonstr:
                gym_branch_list = json.loads(star_jsonstr)
                data['gym_branch_list'] = gym_branch_list

            
        course_list = db.QuerySchedule(startpos, count, copyschedule, **data)
        # return self.write(json.dumps(course_list))
        serveraddress = self.request.headers.get("Host")
        for courseinfo in course_list:
            avatar_list = []
            for avatar in json.loads(courseinfo['course_avatar']):
                avatar_list.append('http://%s%s' % (serveraddress, "/static/img/avatar/course/P%s_%s.jpeg" % (courseinfo['course_id'], avatar)))
            courseinfo['course_avatar'] = avatar_list

            teacherinfo = db.QueryTeacherInfo(courseinfo['course_schedule_teacherid'])
            courseinfo['course_teacher_name'] = teacherinfo and teacherinfo['teacher_name'] or None

            # ====================
            courseinfo['user_ordered'] = False
            courseinfo['stock_remains'] = courseinfo['course_schedule_stock']
            if user_id:
                order_query_conditions = dict(
                    order_date=courseinfo['course_date'],
                    order_userid=user_id,
                    order_objectid=courseinfo['course_schedule_id'],
                    order_type=1,
                    order_status=1)
                order_list = db.QueryOrder(0, **order_query_conditions)
                length = len(order_list)
                if length != 0:
                    courseinfo['user_ordered'] = True
            # ====================

        # course_list = sorted(course_list, key = lambda dct: (dct['course_date']), reverse=False)

        resultlist = {'result': 1, 'CourseScheduleList': course_list}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)


class ApiCourseTimeList(BaseHandler):
    def get(self):
        db = DbHelper()
        time_span_f = '%s - %s' 
        # ===============
        # month-span e.g. today is '2015-9-30' --> ('201509', '201510')
        t_day = get_target_date(datetime.date.today())
        # get dateObj within 7 days from now
        date_list = [str(t_day(i)) for i in xrange(7)]
        montstr_tpl = tuple(set(map(
                                    lambda x:db.getMonthWeekdayByDate(x)[0],
                                    (date_list[0],date_list[-1])
                                    )))
        # ===============
        # make container out of date object
        course_time_ori = [ { "不限" : [ "全部时间段" ] } ]
        course_time = [{}.fromkeys([str(date)], []) for date in date_list]
        course_time_ori.extend(course_time)
        course_time = course_time_ori
        # query schedule object accroding to month-span (this month and next if needed)
        schedule_list = db.QueryScheduleTime(0,0, course_schedule_month__in=montstr_tpl)
        # ===============
        for s in schedule_list:
            s_date_list = db.getDateOfMonthByWeekday(s['course_schedule_month'], s['course_schedule_day'])
            date_set = set(s_date_list) & set(date_list)
            if date_set:
                date_key = list(date_set)[0]
                # get time-span
                begin = str(s['course_schedule_begintime'])
                end = str(s['course_schedule_endtime'])
                time_span = time_span_f % (begin, end)
                for c_dict in course_time:
                    time_list = c_dict.get(date_key)
                    if time_list is None: continue # 
                    if time_span not in time_list:
                        time_list.append(time_span)
                        time_list.sort()
                        break
            else:
                continue
        resultlist = {'result': 1, 'CourseTime': course_time}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCourseTypeList(BaseHandler):
    def get(self):
        db = DbHelper()
        type_list = db.QueryTypeList(1)
    
        resultlist = {'result': 1, 'TypeList': type_list}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCourseLocationList(BaseHandler):
    def get(self):
        db = DbHelper()
        location_list = db.GetCourseLocationList()

        resultlist = {'result': 1, 'Location': location_list}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiPrivateteacherList(BaseHandler):
    def get(self):
        startpos = GetArgumentValue(self,'startposition') or 0
        count = GetArgumentValue(self,'count') or 20
        user_id = GetArgumentValue(self, 'user_id')
        data = {}
        data['gym_branch_district'] = GetArgumentValue(self, 'teacher_district')
        data['gym_branch_businesscircle'] = GetArgumentValue(self, 'teacher_businesscircle')
        data['category_name'] = GetArgumentValue(self, 'teacher_type')

        db = DbHelper()
        teacher_list = db.QueryPrivateTeacher(startpos, count, **data)
        serveraddress = self.request.headers.get("Host")
        for r in teacher_list:
            avatar_list = []
            for avatar in json.loads(r['private_teacher_avatar']):
                avatar_list.append('http://%s%s' % (serveraddress, "/static/img/avatar/privateteacher/P%s_%s.jpeg" % (r['private_teacher_id'], avatar)))
            r['private_teacher_avatar'] = avatar_list

            # ====================
            r['user_ordered_privateteacher'] = False
            if user_id:
                order_query_conditions = dict(
                    order_userid=user_id,
                    order_objectid=r['private_teacher_id'],
                    order_type=2,
                    order_status=1,
                )
                order_list = db.QueryOrder(0, **order_query_conditions)
                if len(order_list) != 0:
                    r['user_ordered_privateteacher'] = True
            # ====================

        resultlist = {'result': 1, 'PrivateTeacherList': teacher_list}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiPrivateteacherTypeList(BaseHandler):
    def get(self):
        db = DbHelper()
        teacher_type_list = db.QueryTypeList(2)

        resultlist = {'result': 1, 'TypeList': teacher_type_list}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiPrivateteacherLocationList(BaseHandler):
    def get(self):
        db = DbHelper()
        teacher_location_list = db.GetTeacherLocationList()
        
        resultlist = {'result': 1, 'Location': teacher_location_list}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCourseScheduleDetail(BaseHandler):
    def get(self):
        course_scheduleid = GetArgumentValue(self, 'course_schedule_id')
        user_id = GetArgumentValue(self, 'user_id')
        course_date = GetArgumentValue(self, 'course_date')

        db = DbHelper()
        host = self.request.headers.get('host')
        course_detail = db.QueryScheduleInfo(course_scheduleid)
        # ====================
        course_detail['user_ordered'] = False
        course_detail['stock_remains'] = -1
        course_detail['gymbranch_followed'] = False
        if user_id:
            user = db.QueryUserInfo(user_id)
            star_gymbranch_list = user and json_safe_loads(user['user_star_gymbranch']) or []
            if int(course_detail['course_schedule_gymbranchid']) in star_gymbranch_list or str(course_detail['course_schedule_gymbranchid']) in star_gymbranch_list:
                course_detail['gymbranch_followed'] = True
        if course_date:
            course_detail['stock_remains'] = course_detail['course_schedule_stock'][course_date]   
            if user_id:
                order_query_conditions = dict(
                    order_date=course_date,
                    order_userid=user_id,
                    order_objectid=course_scheduleid,
                    order_type=1,
                    order_status=1)
                order_list = db.QueryOrder(0,**order_query_conditions)
                length = len(order_list)
                if length != 0:
                    course_detail['user_ordered'] = True
        # ====================
        course_detail['user_star'] = False 
        if course_detail['course_star_data'] and user_id:
            for ud in course_detail['course_star_data']:
                if str(user_id) in ud:
                    course_detail['user_star'] = True
                    break
                else:
                    continue

        serveraddress = self.request.headers.get("Host")
        avatar_list = []
        for avatar in json.loads(course_detail['course_avatar']):
            avatar_list.append('http://%s%s' % (serveraddress, "/static/img/avatar/course/P%s_%s.jpeg" % (course_detail['course_id'], avatar)))
        course_detail['course_avatar'] = avatar_list

        resultlist = {'result': 1, 'CourseScheduleDetail': course_detail}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiPrivateteacherDetail(BaseHandler):
    def get(self):
        private_teacher_id = GetArgumentValue(self, 'private_teacher_id')
        user_id = GetArgumentValue(self, 'user_id')
        host = self.request.headers.get('host')
        db = DbHelper()
        teacher_detail = db.QueryPrivateTeacherInfo(private_teacher_id)
        star_jsonstr = teacher_detail['private_teacher_star_data']
        # ====================
        teacher_detail['user_ordered_privateteacher'] = False
        if user_id:
            order_query_conditions = dict(
                order_userid=user_id,
                order_objectid=private_teacher_id,
                order_type=2,
                order_status=1,
            )
            order_list = db.QueryOrder(0,**order_query_conditions)
            if len(order_list) != 0:
                teacher_detail['user_ordered_privateteacher'] = True
        # ====================
        teacher_detail['user_star'] = False
        if star_jsonstr and user_id:
            star_list = star_jsonstr # json.loads(star_jsonstr)
            for ud in star_list:
                if str(user_id) in ud:
                    teacher_detail['user_star'] = True
                    break
                else:
                    continue
            
        avatar_list = []
        aps = private_teacher_id and db.GetPrivateTeacherAvatarPreviews(private_teacher_id) or []
        for avatar, uniquestring, iscustom in aps:
            avatar_list.append('http://%s%s' % (host, avatar))

        teacher_detail['private_teacher_avatar'] = avatar_list
        teacher_detail['private_teacher_permit_avatar'] = 'http://%s%s' % (host, db.GetTeacherPermitAvatarPreview(private_teacher_id)[0])
        teacher_detail['private_teacher_idcard_avatar'] = 'http://%s%s' % (host, db.GetTeacherIDCardAvatarPreview(private_teacher_id)[0])

        gymbranchinfo = db.QueryGymBranchInfo(teacher_detail['private_teacher_gymbranchid'])
        gyminfo = db.QueryGymInfo(gymbranchinfo['gym_branch_gymid'])
        teacher_detail['private_teacher_gym'] = '%s (%s)' % (gyminfo['gym_name'], gymbranchinfo['gym_branch_name'])
        teacher_detail['private_teacher_gymbranchaddress'] = gymbranchinfo['gym_branch_address']
        teacher_detail['private_teacher_gymbranchphonenumber'] = gymbranchinfo['gym_branch_phonenumber']

        teacher_detail['gym_branch_id'] = gymbranchinfo['gym_branch_id']
        teacher_detail['gymbranch_followed'] = False
        if user_id:
            user = db.QueryUserInfo(user_id)
            star_gymbranch_list = user and json_safe_loads(user['user_star_gymbranch']) or []
            if int(teacher_detail['private_teacher_gymbranchid']) in star_gymbranch_list or str(teacher_detail['private_teacher_gymbranchid']) in star_gymbranch_list:
                teacher_detail['gymbranch_followed'] = True
        
        resultlist = {'result': 1, 'PrivateTeacherDetail': teacher_detail}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCourseScheduleOrder(XsrfBaseHandler):

    def post(self):
        # header
        jsondict = json.loads(self.request.headers.get('json'))
        userid =jsondict['order_userid'] = jsondict.pop('user_id')
        jsondict['order_objectid'] = jsondict.pop('course_schedule_id')
        jsondict['order_type'] = 1 # 团操
        data = jsondict
        db = DbHelper()
        # verify if order exists which statisfying the conditions deriving from data
        order_list= db.QueryOrder(0, **data)
        scheduleObj = db.QueryScheduleInfoPlus(course_schedule_id=data['order_objectid'])
        stock_dict = json.loads(scheduleObj['course_schedule_stock'])
        length = len(order_list)
        response = {'result': 0 ,'errormsg':'order already exists'}
        # check if 'order_date' of postdata is proper
        if stock_dict[data['order_date']] <= 0:
            response['errormsg'] = 'stock is empty'
            jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type', 'application/json')
            return self.write(jsonstr)
        stock_dict[data['order_date']] = stock_dict[data['order_date']] - 1 # minus one 

        stock_json = json.dumps(stock_dict)
        # =====================
        data['order_status'] = 1
        data['order_contact_name'] = GetArgumentValue(self,'order_contact_name')
        data['order_contact_phonenumber'] = GetArgumentValue(self, 'order_contact_phonenumber')
        data['order_remark'] = GetArgumentValue(self, 'order_remark')
        # =====================
        if length == 0:
            # new order
                db.SaveOrder(data)
                db.SaveSchedule({
                    'course_schedule_id': scheduleObj['course_schedule_id'],
                    'course_schedule_stock': stock_json 
                })
                # ====================
                course_categoryid = db.QueryCourseInfo(scheduleObj['course_schedule_courseid'])['course_categoryid']
                duration = get_minute_duration(scheduleObj['course_schedule_begintime'], scheduleObj['course_schedule_endtime'])
                userdata_detail = { 
                    "user_data_categoryid" : course_categoryid,
                    "user_data_duration" : duration,
                    "user_data_calory" : scheduleObj['course_schedule_calory'],
                    "user_data_userid" : userid,
                    "user_data_date" : data['order_date'],
                    "user_data_source" : 1,
                }
                db.SaveUserData(userdata_detail)
                # ====================
                response = {'result': 1 }

        elif length == 1:
            # 恢复订单 order_status 2 --> 1，部分可修改字段
            orderObj = order_list[0]
            if orderObj['order_status'] == 2:
                db.SaveOrder({
                    'order_id':orderObj['order_id'],
                    'order_contact_name': data['order_contact_name'],
                    'order_contact_phonenumber': data['order_contact_phonenumber'],
                    'order_remark': data['order_remark'],
                    'order_status': 1,
                })
                db.SaveSchedule({
                    'course_schedule_id':scheduleObj['course_schedule_id'],
                    'course_schedule_stock': stock_json
                })
                response = {'result': 1 }
        else:
            pass

        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiPrivateteacherOrder(XsrfBaseHandler):

    def post(self):
        jsondict = json.loads(self.request.headers.get('json'))
        jsondict['order_objectid'] = jsondict.pop('private_teacher_id')
        jsondict['order_userid'] = jsondict.pop('user_id')

        data = jsondict
        data['order_type'] = 2
        # =================
        db = DbHelper()
        order_list = db.QueryOrder(0, **data)
        length = len(order_list)
        response = {'result': 0 }
        # =================
        data['order_status'] = 1
        data['order_contact_name'] = GetArgumentValue(self,'order_contact_name')
        data['order_contact_phonenumber'] = GetArgumentValue(self, 'order_contact_phonenumber')
        data['order_remark'] = GetArgumentValue(self, 'order_remark')

        if length == 0:
            # new order
            # logging.debug("--- data: %r" % data)

            db.SaveOrder(data)
            response = {'result': 1 }
        elif length == 1:
            # restore order
            orderObj = order_list[0]
            if orderObj['order_status'] == 2:
                db.SaveOrder({
                    'order_id':orderObj['order_id'],
                    'order_contact_name': data['order_contact_name'],
                    'order_contact_phonenumber': data['order_contact_phonenumber'],
                    'order_remark': data['order_remark'],
                    'order_status': 1,
                })
                response = {'result': 1 }
        else:
            pass

        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiOrderCancel(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get('json')
        jsondict = json.loads(jsondata)
        user_id = jsondict.pop('user_id')
        jsondict['order_status'] = 2 # cancel
        db = DbHelper()
        order_info = db.QueryOrderInfo(jsondict['order_id'])
        if order_info and order_info['order_userid'] == int(user_id):
            if order_info['order_status'] == 1:
                db_signal = db.SaveOrder(jsondict)
                if order_info['order_type'] == 1:       
                    course_schedule_id = order_info['order_objectid']
                    scheduleObj = db.QueryScheduleInfo(course_schedule_id)
                    stockdict = json_safe_loads(scheduleObj['course_schedule_stock'])
                    date_key = str(order_info['order_date'])
                    stockdict[date_key] += 1
                    db_signal = db.SaveSchedule({
                        'course_schedule_stock': json.dumps(stockdict),
                        'course_schedule_id': course_schedule_id,
                        })
                response = {'result': 1} # if (db_signal==0 or db_signal > 1) else 0
        else:
            response = {'result': 0}
        
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiOrderDelete(XsrfBaseHandler):
    def post(self):
        jsonObj = json.loads(self.request.headers.get('json'))
        user_id = jsonObj['user_id']
        order_id = jsonObj['order_id']
        db = DbHelper()
        orderObj = db.QueryOrderInfo(order_id)
        response = {'result': 0}
        if orderObj and orderObj['order_userid'] == int(user_id):
            if orderObj['order_type'] == 1:
                scheduleObj = db.QueryScheduleInfo(orderObj['order_objectid'])
                date_key = str(orderObj['order_date'])
                stock = scheduleObj['course_schedule_stock']
                stock[date_key] = stock[date_key] + 1
                db.SaveSchedule(dict(
                    course_schedule_id=scheduleObj['course_schedule_id'],
                    course_schedule_stock=json.dumps(stock)
                ))
            db.DeleteOrder(order_id)
            response['result'] = 1
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserDetail(XsrfBaseHandler):
    def post(self):
        db = DbHelper()
        user_id = GetArgumentValue(self, "user_id")
        if user_id is None:
            jsondata = self.request.headers.get('json')
            jsondict = json.loads(jsondata)
            user_id = jsondict['user_id']
        userinfo = db.QueryUserInfo(user_id)
        host = self.request.headers.get('host')

        userinfo['user_avatar'] = 'http://%s%s' % (host, db.GetUserAvatarPreview(user_id)[0])
        userinfo['user_fans_count'] = len(db.QueryUserFans(user_id))
        userinfo['user_star_count'] = len(db.QueryUserFollowPeople(user_id))
        userinfo['user_star_gymbranch'] = eval(userinfo['user_star_gymbranch']) if userinfo['user_star_gymbranch'] else []

        star_people_list = userinfo and json_safe_loads(userinfo['user_star_people']) or []
        userinfo['user_star_people'] = star_people_list

        response = { 'result': 1, "UserInfo" : userinfo }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserDetailV2(XsrfBaseHandler):
    def post(self):
        db = DbHelper()
        user_id_list = GetArgumentValue(self, "user_id_list")
        current_user_id = GetArgumentValue(self, "user_id")
        if user_id_list is None:
            jsondata = self.request.headers.get('json')
            jsondict = json.loads(jsondata)
            user_id_list = str(jsondict['user_id_list']).split(',')
            current_user_id = jsondict['user_id']

        # logging.debug("--- user_id: %r, user_id_list: %r" % (current_user_id, user_id_list))

        host = self.request.headers.get('host')
        userinfolist = []
        for user_id in user_id_list:
            user_id = str(user_id).strip()
            userinfo = db.QueryUserInfo(user_id)
            
            if userinfo is None:
                continue

            if userinfo['user_role'] != 1:
                continue

            userinfo['user_avatar'] = 'http://%s%s' % (host, db.GetUserAvatarPreview(user_id)[0])
            userinfo['user_fans_count'] = len(db.QueryUserFans(user_id))
            userinfo['user_star_count'] = len(db.QueryUserFollowPeople(user_id))
            userinfo['user_star_gymbranch'] = eval(userinfo['user_star_gymbranch']) if userinfo['user_star_gymbranch'] else []
            userinfo['user_star'] = db.IsPeopleFollowedByUser(user_id, current_user_id)

            star_people_list = userinfo and json_safe_loads(userinfo['user_star_people']) or []
            userinfo['user_star_people'] = star_people_list
            userinfolist.append(userinfo)

        response = { 'result': 1, "UserInfoList" : userinfolist }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserOrderList(XsrfBaseHandler):
    def post(self):
        # logging.debug("--- json: %r" % self.request.headers.get('json'))

        db = DbHelper()
        jsondict = json.loads(self.request.headers.get('json') or GetArgumentValue(self, 'json'))
        startpos = int(jsondict.pop('startposition', 0))
        count = int(jsondict.pop('count', 0))
        order_type = int(jsondict.pop('type', 0))
        days = int(jsondict.pop('days', 0))
        if jsondict.has_key('user_id'):
            jsondict['order_userid'] = jsondict.pop('user_id')
        else:
            jsondict['order_userid'] = 0
        course_data = jsondict.copy()
        teacher_data = jsondict.copy()
        # ==============
        teacher_data.pop('month', None)
        teacher_data.pop('date', None)
        teacher_data['order_type'] = 2
        # ==============
        date = course_data.pop('date', '')
        course_data['order_date'] = date if len(date.strip()) > 0 else None

        if course_data['order_date'] is None:
            month = course_data.pop('month', '')
            course_data['course_schedule_month'] = month if len(date.strip()) > 0 else None
        else:
            course_data.pop('month', None)
        course_data['order_type'] = 1

        the_status = jsondict['status'] if jsondict.has_key('status') else None
        the_status = None if the_status == "" else the_status
        if the_status is not None and int(the_status) != 0:
            course_data['order_status'] = the_status
        course_data.pop('status', None)
        teacher_data.pop('status', None)

        # ==============
        if order_type == 0:
            course_order = list(db.QueryOrder(0, 0, **course_data))
            teacher_order = db.QueryOrder(0, 0, **teacher_data)
            allorder = course_order.extend(teacher_order) or course_order
        elif order_type == 1:
            allorder = list(db.QueryOrder(0, 0, **course_data))
        elif order_type == 2:
            allorder = list(db.QueryOrder(0, 0, **teacher_data))
        allorder.sort(key=lambda d:d['order_id'])
        # ==============
        if days != 0:
            def get_filter(days):
                def _filter(o):
                    today = DateTime.today().date()
                    odate = o['order_datetime'].date()
                    span = today - odate
                    return (span.days < days)
                return _filter
            f = get_filter(days)
            allorder = filter(f, allorder)
        elif count != 0:
            order_list = []
            for order in islice(allorder, startpos, (startpos + count)):
                order_list.append(order)
            allorder = order_list
        # ==============
        for orderinfo in allorder:
            orderinfo['order_begintime'] = str(orderinfo['order_begintime'])
            orderinfo['order_endtime'] = str(orderinfo['order_endtime'])
            orderinfo['order_date'] = str(orderinfo['order_date'])
            if orderinfo['order_type'] == 1:
                course_id = orderinfo['order_objectid']
                courseinfo = db.QueryCourseInfo(course_id)
                orderinfo.update(courseinfo or {})
                
                datedelta = datetime.datetime(int(str(orderinfo['order_date'])[0:4]), int(str(orderinfo['order_date'])[5:7]), int(str(orderinfo['order_date'])[8:10]), 0, 0, 0) - datetime.datetime.now()
                
                # logging.debug("--- datedelta: %r, order_date: %r" % (datedelta, orderinfo['order_date']))

                orderinfo['order_completed'] = True if datedelta.days < -1 else False
            elif orderinfo['order_type'] == 2:
                teacher_id = orderinfo['order_objectid']
                teacherinfo = db.QueryTeacherInfo(teacher_id)
                orderinfo.update(teacherinfo or {})

        response = { 'result': 1, "UserOrderList" : allorder }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserDataList(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get('json') or GetArgumentValue(self, "json")
        jsondict = json.loads(jsondata)
        # json of headers
        user_id = jsondict.get('user_id')
        startpos = jsondict.get('startposition', 0)
        count = int(jsondict.get('count', 10))
        month = jsondict.get('month', 0)
        date = jsondict.get('date', 0)
        source = jsondict.get('src', 0)
        # =============================
        if str(date).strip() == '':
            date = 0
        if date == 0:
            if str(month).strip() == '':
                month = 0
            # if month != 0:
            #     month = month if len(month.strip()) > 0 else 0
        else:
            month = 0

        # ============================
        db = DbHelper()
        user_data_list = db.QueryUserData(startpos, count, user_id, month, date, source)
        user_data_list = sorted(user_data_list, key = lambda dct: (dct['user_data_date']), reverse=False)

        for userdatainfo in user_data_list:
            userdatainfo['user_data_categoryname'] = db.QueryCategoryInfo(userdatainfo['user_data_categoryid'])['category_name']

        response = { 'result':1, 'UserDataList' : user_data_list }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserDataListV2(XsrfBaseHandler):
    def post(self):
        jsonObj = json_safe_loads(self.request.headers['json'])
        user_id = jsonObj['user_id']
        # startdate = jsonObj.pop('startdate', None)
        days = jsonObj.pop('days', None)
        source = jsonObj.pop('src', 0)
        # ====================
        db = DbHelper()
        todaydateObj = DateTime.today().date()
        enddate = str(todaydateObj)
        pastdateObj = days and ( todaydateObj - datetime.timedelta(days=int(days)-1) )
        startdate = pastdateObj and str(pastdateObj)
        
        # ====================
        # startdateObj = startdate and DateTime.strptime(startdate, '%Y-%m-%d').date()
        # enddateObj = startdateObj and (startdateObj + datetime.timedelta(days=int(days)-1))
        # enddate = enddateObj and DateTime.strftime(enddateObj, '%Y-%m-%d')
        #
        result_list = []
        if days: 
            td = get_target_date(todaydateObj)
            start = - (int(days) - 1)
            for d in xrange( start, 1 ):
                result_list.append( { str( td(d) ): [0, 0] } )
        # 
        userdata_tpl = db.QueryUserData(0, 0, user_id=user_id, user_data_date__gte=startdate, user_data_date__lte=enddate, source=source)
        # ====================
        def groupby2(iterObj, key):
            _dict = {}
            for i in iterObj:
                k = key(i)
                _dict.setdefault(k, [])
                _dict[k].append(i)
            return _dict.iteritems()

        for date, items in groupby2( userdata_tpl, key=itemgetter('user_data_date') ):
            items = list(items)
            calory_gross = sum( i['user_data_calory'] for i in items )
            duration_gross = sum( i['user_data_duration'] for i in items )
            for r in result_list:
                if date in r:
                    r[date] = [ calory_gross, int(duration_gross)]
                    break
                else:
                    continue
            else:
                result_list.append({ date: [ calory_gross, int(duration_gross)] })
                    
        result_list.sort(key=lambda x:x.keys()[0])
        # ====================
        response = { 'result': 1, "UserDataListV2" : result_list }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserVipcardList(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get('json') or GetArgumentValue(self, "json")
        jsondict = json.loads(jsondata)
        # json of headers
        user_id = jsondict.get('user_id')
        startpos = jsondict.get('startposition', 0)
        count = jsondict.get('count', 10)

        db = DbHelper()
        user_vipcard_list = db.QueryUservipcard(startpos, count, user_id)

        response = {'result':1, 'UserVipcardList': user_vipcard_list}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserVipcardAdd(XsrfBaseHandler):
    def post(self):
        jsonObj = json_safe_loads(self.request.headers['json'])
        jsonObj['user_vipcard_userid'] = jsonObj.pop('user_id')
        jsonObj['user_vipcard_rangeid'] = json.dumps([jsonObj.pop('gymid')])
        jsonObj['user_vipcard_no'] = jsonObj.pop('vipcardno')
        jsonObj['user_vipcard_name'] = GetArgumentValue(self, 'vipcardname') or jsonObj.pop('vipcardname')
        jsonObj['user_vipcard_phonenumber'] = jsonObj.pop('phonenumber')
        jsonObj['user_vipcard_status'] = 1
        data = jsonObj
        db = DbHelper()
        if db.QueryUservipcardInfo(**data) is None:
            db.SaveUservipcard(data)
            response = {'result': 1 }
        else:
            response = {'result': 0 }

        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserVipcardDelete(XsrfBaseHandler):
    def post(self):
        jsonObj = json_safe_loads(self.request.headers['json'])
        user_id = jsonObj['user_id']
        vipcardid = jsonObj['vipcardid']
        db = DbHelper()
        if db.QueryUservipcardInfo(vipcardid, user_vipcard_userid=user_id) is None:
            response = { 'result': 0 }
        else:
            db.DeleteUservipcard(vipcardid)
            response = { 'result': 1 }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserVipcardUnbind(XsrfBaseHandler):
    def post(self):
        jsonObj = json_safe_loads(self.request.headers['json'])
        user_id = jsonObj['user_id']
        userpassword = str(jsonObj['userpassword'])
        vipcardid = jsonObj['vipcardid']
        phonenumber = jsonObj['phonenumber']
        # ====================
        db = DbHelper()
        user = db.QueryUserInfo(user_id)
        response = { 'result': 0}
        if db.CheckUserByID(user_id, userpassword) == 1:
                vipcard = db.QueryUservipcardInfo(
                    vipcardid, 
                    user_vipcard_status=1,
                    user_vipcard_userid=user_id,
                    user_vipcard_phonenumber=phonenumber)
                if vipcard is not None:
                    db.SaveUservipcard(dict(
                        user_vipcard_id=vipcardid,
                        user_vipcard_status=0,
                    ))
                    response = { 'result': 1 }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserUpdate(XsrfBaseHandler):
    def post(self):
        user_id = GetArgumentValue(self, 'user_id')
        user_password = GetArgumentValue(self, 'password')
        user_phonenumber = GetArgumentValue(self, 'phonenumber')
        user_gender = GetArgumentValue(self, 'gender')
        user_birthday = GetArgumentValue(self, 'birthday')
        user_height = GetArgumentValue(self, 'height')
        user_weight = GetArgumentValue(self, 'weight')
        user_nickname = GetArgumentValue(self, 'nickname')

        # data = { 'user_' + key: value for key, value in jsondict.items() if not str(key).startswith('user_') }
        # data['user_id'] = user_id
        # GetArgumentValue(self, 'nickname') and data.setdefault('user_nickname', GetArgumentValue(self, 'nickname'))

        data = { 'user_id' : user_id }
        if user_password:
            data['user_password'] = user_password
        if user_phonenumber:
            data['user_phonenumber'] = user_phonenumber
        if user_gender:
            data['user_gender'] = user_gender
        if user_birthday:
            data['user_birthday'] = user_birthday
        if user_height:
            data['user_height'] = user_height
        if user_weight:
            data['user_weight'] = user_weight
        if user_nickname:
            data['user_nickname'] = user_nickname

        db = DbHelper()

        db_signal = db.SaveUser(data)

        self.uploadUserAvatar(user_id)

        response = { 'result': 1 }

        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

    def uploadUserAvatar(self, user_id):
        if not self.request.files.has_key('myfile'):
            return

        AVATAR_MAXWIDTH  = 300
        AVATAR_MAXHEIGHT = 300
        db = DbHelper()

        # user_id = cgi.escape(self.get_argument("uid"))
        userinfo = db.QueryUserInfoById(user_id)
        theuserid = user_id

        uploadedfile = self.request.files['myfile'][0]
        original_fname = uploadedfile['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        filename = fname + extension

        filedir = os.path.join(abspath, 'static/img/avatar/user')
        infile   = filedir + '/' + filename # infile就是用户上传的原始照片
        outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 自动保存用户上传的照片文件
        output_file = open(infile, 'w')
        output_file.write(uploadedfile['body'])
        output_file.close()

        # 对上传的原始照片文件进行剪裁，宽度固定为240px, 高度可变
        # avatar_size = (AVATAR_MAXWIDTH, AVATAR_MAXHEIGHT)
        im = Image.open(infile)
        # im_width = im.size[0]
        # im_height = im.size[1]
        # if im_width == im_height:
        #     avatar_size = (AVATAR_MAXWIDTH, AVATAR_MAXHEIGHT)
        # elif im_width < im_height:
        #     avatar_size = (AVATAR_MAXWIDTH, im_height if im_height < AVATAR_MAXHEIGHT else AVATAR_MAXHEIGHT)
        # else:
        #     avatar_size = (AVATAR_MAXWIDTH, int(im_height * (float(AVATAR_MAXHEIGHT) / im_width)))
        avatar_size = im.size

        # 将用户上传的原始照片文件infile经处理保存为outfile_temp
        formatted_im = ImageOps.fit(im, avatar_size, Image.ANTIALIAS, centering = (0.5, 0.5))
        formatted_im.save(outfile_temp, "JPEG")
        avatarfile = '/static/img/avatar/user/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 为了节约服务器空间，删除用户上传的原始照片文件
        os.remove(infile)

        # 将用户选择的照片文件上传到服务器
        outfile  = filedir + '/P%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
        # outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        avatar_large =   filedir + '/L%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 将预览大图outfile_temp正式命名为outfile (outfile在用户个人资料中显示)
        if os.path.exists(outfile_temp) == True:
            outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
            if os.path.exists(outfile) == True:
                os.remove(outfile)
            if os.path.exists(avatar_large) == True:
                os.remove(avatar_large)
            db.SaveUser({ "user_id" : user_id, "user_avatar" : getuniquestring() })
            outfile  = filedir + '/P%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
            shutil.move(outfile_temp, outfile)

        # 保存用户头像时有三咱规格， large(100x100), normal(50x50)和small(25x25)
        avatar_large = filedir + '/L%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 如果用户没用通过file input控件上传照片，则使用缺省照片作为预览大图
        if os.path.exists(outfile) == False:
            outfile = filedir + '/default_avatar.jpeg'

        # 将上一步中正方形不定大小照片通过PIL库保存为100x100像素的用户大头像
        # size = 100, 100
        size = avatar_size
        im = Image.open(outfile)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(avatar_large, "JPEG")

        # resultlist = { "result" : "1" }
        # jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        # self.set_header('Content-Type','application/json')
        # self.write(jsonstr)

    def GetImagePixelSize(self, imagefilepath):
        imout = Image.open(imagefilepath)
        newsize = imout.size
        return newsize

class ApiDataTypeList(BaseHandler):
    def get(self):
        db = DbHelper()
        data_type_list = db.QueryTypeList(1)        
        response = {'result': 1, 'DataTypeList': data_type_list}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserDataAdd(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get('json') or GetArgumentValue(self, "json")

        # logging.debug("--- jsondata: %r" % jsondata)

        jsondict = json.loads(jsondata)

        # logging.debug("--- jsondict: %r" % jsondict)

        categoryid_list = eval(jsondict["user_data_categoryid"])
        duration_list = eval(jsondict["user_data_duration"])
        calory_list = eval(jsondict["user_data_calory"])
        date_list = eval(jsondict["user_data_date"])
        userid = jsondict.pop('user_id')
        # =============================
        db = DbHelper()
        for i in range(len(categoryid_list)):
            db.SaveUserData({ 
                "user_data_categoryid" : categoryid_list[i],
                "user_data_duration" : duration_list[i],
                "user_data_calory" : calory_list[i],
                "user_data_userid" : userid,
                "user_data_date" : date_list[i],
                "user_data_source" : 1 })

        response = { 'result': 1 }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserDataDelete(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get('json')
        jsondict = json.loads(jsondata)
        user_id = jsondict['user_id']
        user_data_id = jsondict['user_data_id']

        db = DbHelper()
        userdatainfo = db.QueryUserDataInfo(user_data_id)
        if int(user_id) != userdatainfo['user_data_userid']:
            response = { 'result': 0 }
            jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type', 'application/json')
            self.write(jsonstr)
        else:
            db.DeleteUserData(user_data_id)

            response = { 'result': 1 }
            jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type', 'application/json')
            self.write(jsonstr)

class ApiGymBranchList(BaseHandler):
    def get(self):
        db = DbHelper()
        gym_id = GetArgumentValue(self, 'gym_id') or 0
        allgymbranch = db.QueryGymBranch(0, 0, gym_id=gym_id)

        response = { 'result': 1, "AllGymBranch" : allgymbranch }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

        
class ApiDistrictBussinesscircle(BaseHandler):
    def get(self):
        response = { 'result': 1, "DistrictBusinessCircle" : Settings.DISTRICT_BUSINESSCIRCLE }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiGymList(BaseHandler):
    def get(self):
        db = DbHelper()
        gym_list = db.QueryGym(0,0)
        response = { 'result': 1, "GymList" : gym_list }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiGymBranchCourseList(BaseHandler):
    def get(self):
        db = DbHelper()
        gym_id = GetArgumentValue(self, "gym_id")
        allgymcourse = db.QueryCourse(0, 0, gym_id=gym_id)

        response = { 'result': 1, "AllGymBranchCourse" : allgymcourse }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiGymBranchTeacherList(BaseHandler):
    def get(self):
        db = DbHelper()
        gym_id = GetArgumentValue(self, "gym_id")
        allgymteacher = db.QueryTeacher(0, 0, gym_id=gym_id)

        response = { 'result': 1, "AllGymBranchTeacher" : allgymteacher }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCourseStar(XsrfBaseHandler):
    def post(self):
        jsondict = json.loads(self.request.headers.get('json'))
        course_id = jsondict['course_id']
        user_id = jsondict['user_id']
        db = DbHelper()
        courseObj = db.QueryCourseInfo(course_id)
        star_date = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
        if courseObj['course_star_data']:
            star_list = json.loads(courseObj['course_star_data'])
            get_key = lambda d: d.keys()[0]
            if str(user_id) not in map(get_key, star_list):
                star_list.append({user_id: star_date})
        else:
            star_list = [{user_id: star_date}]
        star_json = json.dumps(star_list)
        db.SaveCourse({
            'course_id': course_id,
            'course_star_data': star_json
            })
        response = {'result': 1 , 'CourseStarCount': len(star_list)}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCourseScheduleStockList(BaseHandler):
    def get(self):
        db = DbHelper()
        month = GetArgumentValue(self, "month")
        day = GetArgumentValue(self, "day")
        thedays = db.getDateOfMonthByWeekday(str(month), int(day))

        response = { 'result': 1, "TheDays" : thedays }

        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiTeacherStar(XsrfBaseHandler):
    def post(self):
        jsondict = json.loads(self.request.headers.get('json'))
        teacher_id = jsondict['teacher_id']
        user_id = jsondict['user_id']
        db = DbHelper()
        teacherObj = db.QueryPrivateTeacherInfo(teacher_id)
        star_date = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
        if teacherObj['private_teacher_star_data']:
            star_list = teacherObj['private_teacher_star_data'] # json.loads(teacherObj['private_teacher_star_data'])
            get_key = lambda d: d.keys()[0]
            if str(user_id) not in map(get_key, star_list):
                star_list.append({user_id: star_date})
        else:
            star_list = [{user_id: star_date}]
        star_json = json.dumps(star_list)
        db.SavePrivateTeacher({
            'private_teacher_id': teacher_id,
            'private_teacher_star_data': star_json
            })
        response = {'result': 1, 'TeacherStarCount': len(star_list) }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserStar(XsrfBaseHandler):
    def post(self):
        jsondict = json.loads(self.request.headers.get('json'))
        user_id = jsondict['user_id']
        user_id_2 = jsondict['user_id_2']

        db = DbHelper()
        db.FollowPeople(user_id, user_id_2)
        response = { 'result': 1 }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiGymbranchFollow(XsrfBaseHandler):
    def post(self):
        jsondict = json.loads(self.request.headers['json'])
        user_id = jsondict['user_id']
        gym_branch_id = int(jsondict['gym_branch_id'])

        db = DbHelper()
        star_list = db.QueryUserInfo(user_id)['user_star_gymbranch']
        json_list = json.loads(star_list) if star_list else star_list
        if json_list:
            if gym_branch_id not in json_list:
                json_list.append(gym_branch_id)
                json_list.sort()
        else:
            json_list = [gym_branch_id]

        db.SaveUser({
            'user_id': user_id,
            'user_star_gymbranch': json.dumps(json_list)
        })
        response = {'result': 1 }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiGymbranchUnfollow(XsrfBaseHandler):
    def post(self):
        jsondict = json.loads(self.request.headers['json'])
        user_id = jsondict['user_id']
        gym_branch_id = int(jsondict['gym_branch_id'])
        db = DbHelper()
        star_list = db.QueryUserInfo(user_id)['user_star_gymbranch']
        json_list = json.loads(star_list) if star_list else star_list
        if json_list:
            if gym_branch_id in json_list:
                json_list.remove(gym_branch_id)
                db.SaveUser({
                   'user_id': user_id,
                   'user_star_gymbranch': json.dumps(json_list)
                })

        response = {'result': 1 }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiTalentFitnessmanList(BaseHandler):
    def get(self):
        startpos = int(GetArgumentValue(self, 'startposition') or 0)
        count = int(GetArgumentValue(self, 'count') or 20)
        user_id = GetArgumentValue(self, 'user_id')
        sort = int(GetArgumentValue(self, 'sort') or 0)
        # ====================
        db = DbHelper()
        # from module.mysqldb import mydql
        # querys = mydql().setmain('user_data_table', 'ud')\
        #         .inner_join('user_table', on='user_id=user_data_userid', alias='u')\
        #         .query(excludes=['u.user_registertime','ud.user_data_date', 'u.user_birthday']).groupby('user_id')
        # return self.write({'data': querys})
        userdata_tpl = db.QueryUserData(0, 0)
        userid_tpl = tuple(set(ud['user_data_userid'] for ud in userdata_tpl))
        if len(userid_tpl) > 0:
            user_tpl = db.QueryUsers(0, 0, userrole=1, user_id__in=userid_tpl)
        else:
            user_tpl = db.QueryUsers(0, 0, userrole=1)
        viewer = db.QueryUserInfo(user_id) # backend support None
        star_people_list = viewer and json_safe_loads(viewer['user_star_people']) or []
        host = self.request.headers['host']

        user_tpl_new = []
        for user in user_tpl:
            if safe_int(user_id) == user['user_id']:
                continue
            user.pop('user_password')
            user.pop('user_registertime')
            user.pop('user_birthday')
            # 
            userid = user['user_id']
            user['user_duration_gross'] = sum( ud['user_data_duration'] for ud in userdata_tpl if ud['user_data_userid'] == userid )
            user['user_calory_gross'] = sum( ud['user_data_calory'] for ud in userdata_tpl if ud['user_data_userid'] == userid )
            # 
            user['user_avatar'] = 'http://%s%s' % (host, db.GetUserAvatarPreview(userid)[0])
            user['user_stared'] = False
            if user['user_id'] in star_people_list:
                user['user_stared'] = True
            user['user_fans_count'] = len(db.QueryUserFans(userid)) if userid else 0
            user['user_star_count'] = len(db.QueryUserFollowPeople(userid)) if userid else 0
            user_tpl_new.append(user)
        # 
        if sort == 0:
            user_tpl_new = sortit(user_tpl_new, key=itemgetter('user_calory_gross'), reverse=True)
        elif sort == 1:
            user_tpl_new = sortit(user_tpl_new, key=itemgetter('user_fans_count'), reverse=True)
                        
        result_list = [ r for r in islice(user_tpl_new, 0, 100) ] # if count != 0 else user_tpl_new
        # ====================
        response = {'result': 1 , 'TalentFitnessmanList':result_list}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiTalentPrivateteacherList(BaseHandler):
    def get(self):
        startpos = int(GetArgumentValue(self, 'startposition') or 0)
        count = int(GetArgumentValue(self, 'count') or 20)
        user_id = GetArgumentValue(self, 'user_id')
        # ==============================
        db = DbHelper()
        def _access_stardata(o):
            return json_safe_loads(o['private_teacher_star_data'])
        def _sort_key(o):
            return len(_access_stardata(o) or '')
        privateteacher_tpl = sortit(db.QueryPrivateTeacher(0, 0), key=_sort_key, reverse=True)
        viewer = db.QueryUserInfo(user_id)
        host = self.request.headers['host']
        for r in privateteacher_tpl:
            avatar_list = []
            for avatar in json.loads(r['private_teacher_avatar']):
                avatar_list.append('http://%s%s' % (host, "/static/img/avatar/privateteacher/P%s_%s.jpeg" % (r['private_teacher_id'], avatar)))
            r['private_teacher_avatar'] = avatar_list[0] if len(avatar_list) > 0 else 'http://%s%s' % (host, db.GetPrivateTeacherAvatarPreview(0)[0])
            # 
            r['user_stared'] = False
            r['private_teacher_star_data'] = json_safe_loads(r['private_teacher_star_data'])
            stardata_list = viewer and _access_stardata(r) or []
            for stardata in stardata_list:
                if user_id in stardata:
                    r['user_stared'] = True
                    break
                else:
                    continue
        result_list = [ r for r in islice(privateteacher_tpl, 0, 100) ] # if count != 0 else privateteacher_tpl
        # ==============================
        response = {'result': 1 , 'TalentPrivateteacherList':result_list}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserFansList(BaseHandler):
    def get(self):
        user_id = GetArgumentValue(self, "user_id")
        db = DbHelper()
        userlist = db.QueryUserFans(user_id)
        host = self.request.headers['host']
        
        users = []
        for user_id in userlist:
            userinfo = db.QueryUserInfo(user_id)
            if userinfo:
                userinfo['user_avatar'] = 'http://%s%s' % (host, db.GetUserAvatarPreview(userinfo['user_id'])[0])
                userinfo['user_fans_count'] = len(db.QueryUserFans(userinfo['user_id'])) if userinfo['user_id'] else 0
                userinfo['user_star_count'] = len(db.QueryUserFollowPeople(userinfo['user_id'])) if userinfo['user_id'] else 0
                users.append(userinfo)

        response = { 'result': 1 , 'UserFansList' : users }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserAttentionList(BaseHandler):
    def get(self):
        user_id = GetArgumentValue(self, "user_id")
        db = DbHelper()
        userlist = db.QueryUserFollowPeople(user_id)
        host = self.request.headers['host']

        users = []
        for user_id in userlist:
            userinfo = db.QueryUserInfo(user_id)
            if userinfo:
                userinfo['user_avatar'] = 'http://%s%s' % (host, db.GetUserAvatarPreview(userinfo['user_id'])[0])
                userinfo['user_fans_count'] = len(db.QueryUserFans(userinfo['user_id'])) if userinfo['user_id'] else 0
                userinfo['user_star_count'] = len(db.QueryUserFollowPeople(userinfo['user_id'])) if userinfo['user_id'] else 0
                users.append(userinfo)

        response = { 'result': 1 , 'UserAttentionList' : users }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCourseTeacherDetail(BaseHandler):
    def get(self):
        db = DbHelper()
        course_teacher_id = GetArgumentValue(self, 'teacher_id') or 0
        teacherinfo = db.QueryTeacherInfo(teacher_id=course_teacher_id)
        if teacherinfo is None:
            response = {'result':0}
        else:
            host = self.request.host
            al = []

            for avatar in db.GetTeacherAvatarPreviews(course_teacher_id):
                al.append(('http://%s%s'%(host, avatar[0])))
            teacherinfo['teacher_avatar']  = al
            teacherinfo['teacher_permit_avatar'] = ('http://%s%s' % (host, db.GetTeacherPermitAvatarPreview(course_teacher_id)[0]))
            teacherinfo['teacher_idcard_avatar'] = ('http://%s%s' % (host, db.GetTeacherIDCardAvatarPreview(course_teacher_id)[0]))
            response = { 'result': 1 , 'CourseTeacherDetail' : teacherinfo }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserRelationsApply(XsrfBaseHandler):
    def post(self):
        user_id = self.get_argument('u1')
        user_id_2 = self.get_argument('u2')
        rtype = self.get_argument("type")
        msg = self.get_argument('msg', None)
        db = DbHelper()
        signal = 0
        rels = db.QueryRelations(user_id, the_other_userid=user_id_2, rtype=rtype)
        if len(rels) == 0:
            signal = db.SaveRelation(
                auto_prefix=True,
                main_userid=user_id,
                sub_userid=user_id_2,
                type=rtype,
                message=msg,
            )
        else:
            pass
        response = { 'result': signal }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserRelationsConfirm(XsrfBaseHandler):
    def post(self):
        rid = self.get_argument('rel')
        uid = self.get_argument('u1')
        uid2 = self.get_argument('u2')
        db = DbHelper()
        signal = db.SaveRelation(
            auto_prefix=True,
            id=rid,
            status=1,
            _where_sub_userid=uid,
            _where_main_userid=uid2,
        )
        response = {"result": signal and 1 or 0}
        self.write(response)

class ApiUserRelationsDel(XsrfBaseHandler):
    def post(self):
        uid = self.get_argument('uid')
        relation_id = self.get_argument('rid')
        db = DbHelper()
        signal = db.SaveRelation(
            auto_prefix=True,
            id=relation_id,
            _where_sub_userid=uid,
            msg_delete=1,
        )
        response = {'result': signal and 1 or 0}
        self.write(response)

class ApiUserRelationsList(BaseHandler):
    def get(self):
        user_id = self.get_argument("uid")
        rtype = self.get_argument("type", "0") # relation_type: 0 all, 1 friends, 2 coach and student
        st = self.get_argument('status', "0") # 0 successfully-built relations, 1 all relations 
        db = DbHelper()
        # ====================
        rels = db.QueryRelations(user_id, rtype=(rtype if rtype in ("1", "2") else 0))
        relations_counts = len(rels)
        rel_new_apply = filter(lambda x:x['relation_status'] == 0 and x['relation_msg_delete'] == 0, rels)
        relations_tpl = db.QueryRelatedUsers(user_id, 0, 0, 
            relation_type=(rtype if rtype in ("1", "2") else 0),
            all_relations=(1 if st == '1' else 0))
        if st == '1':
            relations_built = db.QueryRelatedUsers(user_id, 0, 0, 
                relation_type=(rtype if rtype in ("1", "2") else 0))
            relations_bulit_userids = map(lambda x: x['user_id'], relations_built)
        has_new_friends = len(rel_new_apply) > 0
        is_coach = db.IsCoach(user_id)
        # ====================
        UserRelations = {}
        def sort_func(o):
            # sorted by initial letter
            s = SnowNLP(o['user_nickname'])
            return ''.join(s.pinyin)

        def get_rel_built_filter(uid1, uid2):
            'uid1 current user id, uid2 the opposite user id'
            uid1 = int(uid1)
            uid2 = int(uid2)
            def fn(o):
                main, sub = o['relation_main_userid'], o['relation_sub_userid']
                return (main, sub) == (uid2, uid1)
            return fn 

        for r in relations_tpl:
            ruid = r['user_id']
            # ====================
            if st == '1': # show all message of applying for building relations
                rel_filter = get_rel_built_filter(user_id, ruid)
                rel_ls = filter(rel_filter, rels)
                if len(rel_ls)== 0 or rel_ls[0]["relation_msg_delete"] == 1: 
                    r['show'] = False
                    continue
                else:
                    the_rel = rel_ls[0]
                    r['show'] = True
                    r["relation_message"] = the_rel['relation_message']
                    r["relation_id"] = the_rel['relation_id']
                    r['relation_built'] = ruid in relations_bulit_userids
            r['user_avatar'] = self.get_absurl(db.GetUserAvatarPreview(ruid)[0])
            r['user_iscoach'] = r['coachauth_userid'] is not None and r['coachauth_status'] == 1
            # ====================

            if r['user_iscoach'] and rtype == '0':
                initial = "@coaches"
            else:
                snlp = SnowNLP(r['user_nickname'])
                initial = snlp.pinyin[0][0].upper()

            if initial in UserRelations:
                UserRelations[initial].append(r)
            else:
                UserRelations[initial] = [r]

            if rtype == '2' and is_coach:
                # is coach
                # how many lessons already had for each students ?
                s = db.QueryScheduleV2(
                    auto_prefix=True,
                    coach_userid=user_id,
                    student_userid=r['user_id'],
                    status=1, # finished lesson
                )
                r['have_lessons_amount'] = len(s)
            elif rtype == '2':
                # is student
                # 本月上课次数
                s = db.QueryScheduleV2(
                    auto_prefix=True,
                    coach_userid=r['user_id'],
                    student_userid=user_id,
                    status__in=[0, 1],
                )
                # ====================
                did_s = filter(lambda x: x['schedule_status'] == 1, s)
                r['has_new_lessons'] = len(did_s) < len(s)
                s = did_s
                r['have_lessons'] = len(s)
                # ====================
                def fn(x):
                    now = datetime.date.today()
                    ds = date_stuff.DateScope(x['schedule_lessontime'].split(' ')[0])
                    return (ds.year, ds.month) == (now.year, now.month)
                s = filter(fn, s)
                r['have_lessons_thismonth'] = len(s)
                # ====================
                fdl = db.QueryFitnessData(
                    user_data_scheduleid__in=map(lambda x:x['schedule_id'], s)
                )
                calory_consume_thismonth = 0
                for fd in fdl:
                    calory_unit = fd['category_calory_unit']
                    if fd['category_type'] == 3:
                        calory_consume_thismonth += calory_unit * fd['user_data_duration']
                    elif fd['category_type'] == 4:
                        for kgreps in json.loads(fd['user_data_kgreps']):
                            calory_consume_thismonth += calory_unit * eval(kgreps)
                r['calory_consume_thismonth'] = calory_consume_thismonth
        if st == '1':
            relations_tpl = filter(lambda x:x['show'], relations_tpl)
        UserRelationsList = []
        for key in UserRelations:
            UserRelations[key].sort(key=sort_func)
            UserRelationsList.append({'initial_letter':key, 'relations': UserRelations[key]})
        UserRelationsList.sort(key=itemgetter('initial_letter'))
        if st == '1':
            UserRelationsList = reduce(lambda x, y: x + y, map(lambda x: x['relations'], UserRelationsList))

        # 
        response = {"result":1, "UserRelationsList": UserRelationsList, 
                    # "type": int(rtype),
                    'amount': len(UserRelationsList),
                    'has_new_friends': has_new_friends,
                    }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserRelations(BaseHandler):
    def get(self):
        user_id = self.get_argument('uid')
        rtype = self.get_argument('type', '0')
        db = DbHelper()
        # ====================
        rels_new_apply = db.QueryRelations(
            user_id,
            rtype=(2 if rtype == '1' else 0),
            relation_status=0,
            relation_msg_delete=0
            )
        related_users = db.QueryRelatedUsers(user_id, count=0, relation_type=(2 if rtype == '1' else 0))
        is_coach = db.IsCoach(user_id)
        # ====================
        UserRelations = {}
        def sort_func(o):
            # sorted by initial letter
            s = SnowNLP(o['user_nickname'])
            return ''.join(s.pinyin)
        for r in related_users:
            r['user_avatar'] = self.get_absurl(db.GetUserAvatarPreview(r["user_id"])[0])
            if r['coachauth_status'] == 1 and rtype == '0':
                initial = "@coaches"
            else:
                snlp = SnowNLP(r['user_nickname'])
                initial = snlp.pinyin[0][0].upper()

            if initial in UserRelations:
                UserRelations[initial].append(r)
            else:
                UserRelations[initial] = [r]

            if rtype == '2' and is_coach:
                # is coach
                # how many lessons already had for each students ?
                s = db.QueryScheduleV2(
                    auto_prefix=True,
                    coach_userid=user_id,
                    student_userid=r['user_id'],
                    status=1, # finished lesson
                )
                r['have_lessons_amount'] = len(s)
            elif rtype == '2':
                # is student
                # 本月上课次数
                s = db.QueryScheduleV2(
                    auto_prefix=True,
                    coach_userid=r['user_id'],
                    student_userid=user_id,
                    status__in=[0, 1],
                )
                # ====================
                did_s = filter(lambda x: x['schedule_status'] == 1, s)
                r['has_new_lessons'] = len(did_s) < len(s)
                s = did_s
                r['have_lessons'] = len(s)
                # ====================
                def fn(x):
                    now = datetime.date.today()
                    ds = date_stuff.DateScope(x['schedule_lessontime'].split(' ')[0])
                    return (ds.year, ds.month) == (now.year, now.month)
                s = filter(fn, s)
                r['have_lessons_thismonth'] = len(s)
                # ====================
                fdl = db.QueryFitnessData(
                    user_data_scheduleid__in=map(lambda x:x['schedule_id'], s)
                )
                calory_consume_thismonth = 0
                for fd in fdl:
                    calory_unit = fd['category_calory_unit']
                    if fd['category_type'] == 3:
                        calory_consume_thismonth += calory_unit * fd['user_data_duration']
                    elif fd['category_type'] == 4:
                        for kgreps in json.loads(fd['user_data_kgreps']):
                            calory_consume_thismonth += calory_unit * eval(kgreps)
                r['calory_consume_thismonth'] = calory_consume_thismonth
        UserRelationsArray = []
        for key in UserRelations:
            UserRelations[key].sort(key=sort_func)
            UserRelationsArray.append({'initial_letter':key, 'relations': UserRelations[key]})
        UserRelationsArray.sort(key=itemgetter('initial_letter'))
        # 
        response = {"result":1, "UserRelations": UserRelationsArray, 
                    'amount': len(UserRelationsArray),
                    'has_new_apply': len(rels_new_apply) > 0 }
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserApplyMessages(BaseHandler):
    def get(self):
        uid = self.get_argument('uid')
        rtype = self.get_argument('type', '0')
        db = DbHelper()
        msgs = db.QueryApplyMessages(uid, 2 if rtype == '1' else 0)
        for r in msgs:
            r['user_avatar'] = self.get_absurl(db.GetUserAvatarPreview(r['user_id'])[0])
        response = {"result": 1, "Messages": msgs}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)


class ApiUserPhotosUpload(XsrfBaseHandler):

    def post(self):
        uid = self.get_argument('uid')
        upload_key = 'photos'
        # logging.debug('=====================%s===============' % repr(self.request.files.keys()))
        if upload_key in self.request.files:
            db = DbHelper()
            response = {'result': 1, 'uploaded_amount': 0}
            uuid_array = []
            for photo in self.request.files[upload_key]:
                signal, uuid = self.handle_photos_upload(photo)
                if signal == 0:
                    uuid_array.append(uuid)
                    response['uploaded_amount'] += 1
            db.SavePhoto(
                auto_prefix=True,
                userid=uid,
                uuid=uuid_array
            )
            self.handle_daily_task(uid, task_type=1)
        else:
            response = {'result': 0}
        self.write(response)


class ApiUserPhotos(BaseHandler):
    def get(self):
        uid1 = self.get_argument('uid1')
        uid2 = self.get_argument('uid2')
        startpos = self.get_argument('startpos', 0)
        count = self.get_argument('count', 10)
        startpos = int(startpos)
        count = int(count)
        sortby = self.get_argument('sortby', 0)
        host = self.request.host
        db = DbHelper()
        if uid1 == uid2: 
            photos = db.QueryPhotos(0, 0, photo_userid=uid2)
        else:
            photos = db.QueryPhotos(0, 0, photo_userid=uid2, photo_privacy=0)
        temp = []
        for p in photos:
            if not os.path.isfile(os.path.join(Settings.UPLOAD_DIR, p['photo_uuid'])):
                continue
            p['photo_uploaddate'] = str(p['photo_uploadtime'])[:10]
            photo_url = urlparse.urljoin(
                'http://%s' % host,
                Settings.UPLOAD_URL + p['photo_uuid']
            )
            p['photo_thumbnail'] = photo_url
            p['photo_source'] =photo_url
            temp.append(p)
        photos = temp
        # sort by viewtimes or stars or dated-group ?
        if sortby == 0:
            UserPhotosList = photos
        else:
            UserPhotosList = list(photos)
            if sortby == '1': # viewtimes
                UserPhotosList.sort(key=lambda x:x['photo_viewtimes'], reverse=True)
            elif sortby == '2': # stars
                def sort_by(o):
                    stars = o['photo_stars'] and json.loads(o['photo_stars']) or []
                    return len(stars)
                UserPhotosList.sort(key=sort_by, reverse=True)
            elif sortby == '3': # dated-group
                UserPhotosList.sort(key=itemgetter('photo_uploadtime'), reverse=True)
                temp = []
                for key, items in groupby(UserPhotosList, key=itemgetter('photo_uploaddate')):
                    temp.append({'date':key, 'photos': list(items)})
                UserPhotosList = temp
        if count != 0:
            UserPhotosList = UserPhotosList[startpos: (startpos + count)]

        response = {"result":1, "UserPhotosList": UserPhotosList, "amount": len(UserPhotosList)}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiPhotoComments(BaseHandler):
    def get(self):
        pid = self.get_argument('pid')
        startpos = self.get_argument('startpos', 0)
        count = self.get_argument('count', 10)
        db = DbHelper()
        comments = db.QueryComments(startpos, count, comment_objectid=pid, comment_type=1)
        for c in comments:
            cc = c.copy()
            for key in cc:
                if key.startswith('comment') or key in ('user_avatar', 'user_nickname'):
                    continue
                else:
                    c.pop(key)
            # 
            c['comment_postedtime'] = str(c['comment_postedtime'])
            # 
            if c['comment_parentid']:
                c['parent_comment'] = db.QueryCommentInfo(c['comment_parentid'])

        response = {"result":1, "PhotoComments":comments}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiPhotoDetail(XsrfBaseHandler):
    def post(self):
        uid = self.get_argument('uid') #viewer
        pid = self.get_argument('pid')
        db = DbHelper()
        photoInfo = db.QueryPhotoInfo(pid)
        if photoInfo is None:
            response = {'result': 0}
        elif photoInfo['photo_privacy'] == 1 and photoInfo['photo_userid'] != int(uid):
            response = {'result': -1} # 用户隐私设置，您没有权限使用该资源
        else:
            # if the photo is stared?
            stars = photoInfo['photo_stars'] and json.loads(photoInfo['photo_stars']) or []
            photoInfo['photo_is_stared'] = True if int(uid) in stars else False
            # how many users stared?
            photoInfo['photo_stared_amount'] = len(stars)
            # count each api-visit and record backend
            # photo absurl
            db.SavePhoto(photo_id=pid, photo_viewtimes=photoInfo['photo_viewtimes'] + 1)
            response = {"result":1, "PhotoDetail": photoInfo}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)


class ApiUserPhotoStar(XsrfBaseHandler):
    def post(self):
        uid = self.get_argument('uid')
        pid = self.get_argument('pid')
        db = DbHelper()
        photoInfo = db.QueryPhotoInfo(pid)
        if photoInfo is None:
            response = {'result':0}
        elif photoInfo['photo_privacy'] == 1 and photoInfo['photo_userid'] != int(uid):
            response = {'result': -1} # 用户隐私设置，您没有权限使用该资源
        else:
            stars = photoInfo['photo_stars'] and json.loads(photoInfo['photo_stars']) or []
            if int(uid) not in stars:
                stars.append(int(uid))
                db.SavePhoto(photo_id=pid, photo_stars=json.dumps(stars))
            response = {'result': 1}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserComment(XsrfBaseHandler):
    def post(self):
        uid = self.get_argument('uid') # user id
        oid = self.get_argument('oid') # comment_objectid
        msg = self.get_argument('msg') # comment_content
        pid = self.get_argument('pid', None) # comment_parentid
        ctype = self.get_argument('type')
        db = DbHelper()
        if len(msg.strip()) == 0:
            response = {"result":0}
        else:
            db.SaveComment(
                comment_userid=uid,
                comment_objectid=oid,
                comment_parentid=pid,
                comment_content=msg,
                comment_type=ctype)
            response = {"result": 1}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)


class ApiUserDailyTasks(BaseHandler):
    def get(self):
        resp_tasks = [
            dict(taskname="上传照片", taskpoints=100, is_finished=False),
            dict(taskname="私人训练", taskpoints=200, is_finished=False),
            dict(taskname="私教训练", taskpoints=200, is_finished=False),
            dict(taskname="添加好友", taskpoints=300, is_finished=False),
        ]
        uid = self.get_argument('uid')
        db = DbHelper()
        tasks = db.QueryTasks(
            daily=True,
            task_userid=uid
        )
        for task in tasks:
            pos = task['task_type'] - 1
            resp_tasks[pos]['is_finished'] = True
        response = dict(
            result=1,
            tasks=resp_tasks,
        )
        self.write(response)

class ApiCoachAuth(XsrfBaseHandler):
    def post(self):
        usid = self.get_argument('uid')
        name = self.get_argument('name')
        idno = self.get_argument('idno')
        orgn = self.get_argument('orgn')
        wkno = self.get_argument('wkno', None)
        # return self.write(repr(self.request.files))
        ls = []
        for k in ('idcard', 'qualify'):
            if k in self.request.files:
                ls.extend(map(self.handle_photos_upload, self.request.files[k][:4])) # maxlength: 4
        # 
        for idx, val in enumerate(ls):
            if val[0] == 1:
                response = {"result": 0}
                if idx == 0:
                    response['msg'] = 'failed to upload idcard snapshot'
                else:
                    response['msg'] = 'failed to upload qualifications'
                break
        else:
            db = DbHelper()
            auths = db.QueryCoachAuths(count=0, coachauth_userid=usid)
            params = dict(
                auto_prefix=True,
                name=name,
                idcardno=idno,
                org=orgn,
                permitno=wkno,
                snapshot=ls[0][1],
                qualifications=json.dumps([i[1] for i in ls[1:]])
            )
            if len(auths) > 0:
                params['id'] = auths[0]['coachauth_id']
            else:
                params['userid'] = usid

            db.SaveCoachAuth(**params)
            response = {'result': 1}
        self.write(response)


class ApiCoachEntryList(BaseHandler):
    def get(self):
        uid = self.get_argument('uid')
        entry_type = self.get_argument('type', 0)
        entry_type = 0
        if entry_type == 0: # index
            db = DbHelper()
            auth_array = db.QueryCoachAuths(
                coachauth_userid=uid,
                count=0,
            )
            entry_array = list(db.QueryEntrys(entry_type=entry_type, count=0))
            entry_array.sort(key=itemgetter('entry_sortweight'), reverse=True)
            for entry in entry_array:
                entry['entry_image'] = self.get_absurl(Settings.UPLOAD_URL + entry['entry_image'])
            is_auth_array = filter(lambda x: x["coachauth_status"] == 1, auth_array)        
            response = dict(
                result = 1,
                is_auth = len(is_auth_array) > 0,
                organ= is_auth_array[0]['coachauth_org'] if len(is_auth_array) > 0 else '',
                entrys = entry_array,
                auth_records=auth_array
            )
        elif entry_type == 1: # add-data
            db = DbHelper()
            all_entrys = db.QueryEntrys(count=0, entry_type__in=(1,2))
            all_super_entrys = []
            for e in all_entrys:
                e['entry_image'] = self.get_absurl(Settings.UPLOAD_URL + e['entry_image'])
                if e['entry_type'] == 1:
                    for i in all_super_entrys:
                        if i['parent_id'] == e['entry_id']:
                            i['parent_entry'] = e
                            break
                    else:
                        all_super_entrys.append({
                            'parent_id': e['entry_parentid'],
                            'parent_entry': e,
                            'sub_entrys': []
                            })
                elif e['entry_type'] == 2:
                    for i in all_super_entrys:
                        if i['parent_id'] == e['entry_parentid']:
                            i['sub_entrys'].append(e)
                            i['sub_entrys'].sort(key=itemgetter('entry_sortweight'), reverse=True)
                            break
                    else:
                        all_super_entrys.append({
                            'parent_id': e['entry_parentid'],
                            'parent_entry': None,
                            'sub_entrys': [e]
                        })


            response = {'result':1, 'entrys': all_super_entrys}




        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCoachLessonList(BaseHandler):
    def get(self):
        status = self.get_argument('status', "0")
        coach_id = self.get_argument('coach_id')
        db = DbHelper()
        response = {'result': 0}
        params = dict(
            auto_prefix=True,
            coach_userid=coach_id            
        )
        if status == '0': #all
            params['vision'] = 1
        elif status == '1':#未开始
            params['status'] = 0
            params['vision'] = 1
        elif status == "2": #已结束
            params['status'] = 1
            params['vision'] = 1
        elif status == '3':
            params['status'] = 99
        schedules = db.QueryScheduleV2(**params)
        if status in ("0", "1", "2"):
            for s in schedules:
                 s['user_avatar'] = self.get_absurl(db.GetUserAvatarPreview(s["user_id"])[0])
        if len(schedules) > 0:
            response = {'result':1, 'CoachLessonList': schedules}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)


class ApiSearchPeople(BaseHandler):
    def get(self):
        # search people by:
        # user_nickname
        # user_phonenumber,
        # user_huanchaouid,
        keyword = self.get_argument('kwd', None)
        search_range = self.get_argument('range', "0")
        if keyword is None or len(keyword.strip()) == 0:
            response = {"result": 0}
        else:
            db = DbHelper()
            people = db.SearchPeopleByKeyword(keyword, search_range=int(search_range))
            def handle(o):
                if keyword in o['user_nickname']:
                    o['title'] = o['user_nickname']
                    return 1
                elif keyword in o['user_phonenumber']:
                    o['title'] = o['user_phonenumber']
                    return 2
                elif keyword in o['user_huanchaouid']:
                    o['title'] = o['user_huanchaouid']
                    return 3
            SearchPeople = list(people)
            SearchPeople.sort(key=handle)
            response = {"result":1, "SearchPeople": SearchPeople}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)


class ApiDetectFriends(BaseHandler):
    def get(self, secret):
        hashed_stuff = qr.decrypt(secret)
        response = {"result":0}
        if hashed_stuff:       
            db = DbHelper()
            userInfo = db.FuzzyQueryUserByHashed(hashed_stuff)
            if userInfo:
                userInfo["user_avatar"] = "http://%s%s" % (self.request.host, db.GetUserAvatarPreview(userInfo["user_id"])[0])
                # user_iscoach?
                userInfo["user_iscoach"] = db.IsCoach(userInfo['user_id'])
                response = {"result":1, "UserInfo": userInfo}
                # already bulid relations?
        self.write(response)


class ApiResource(BaseHandler):
    def get(self):
        key = self.get_argument('key', None)
        if key is None:
            response = {"result": 0}
        elif key == 'coach':
            resource_list =[
                self.get_absurl('static/img/coach_entry.png')
            ]
            response = {"result": 1, "ResourceList": resource_list}
        self.write(response)

class ApiScheduleCreate(XsrfBaseHandler):
    def post(self):
        # jsondict = json.loads(self.request.headers['json'])
        jsondict = self.request.arguments
        sorted_keys = sorted(jsondict.keys())
        create_schedule_params = None
        signal = 0
        if sorted_keys == ['coach_id', "student_id", "time"]:
            create_schedule_params = dict(
                schedule_coach_userid=jsondict['coach_id'],
                schedule_student_userid=jsondict['student_id'],
                schedule_lessontime=jsondict['time'],
            )
        elif sorted_keys == ['coach_id', 'regular']:
            create_schedule_params = dict(
                      schedule_coach_userid=jsondict['coach_id'],
                      schedule_name=jsondict['regular'],
                      schedule_status=99 # regular-used lesson
                  )
        if create_schedule_params:
            db = DbHelper()
            signal = db.SaveScheduleV2(**create_schedule_params)
        response = {'result': signal and 1 or 0 , 'lesson_id': signal}
        self.write(response)

class ApiScheduleFinish(XsrfBaseHandler):
    def post(self):
        coach_id = self.get_argument('coach_id')
        schedule_id = self.get_argument('lesson_id')
        db = DbHelper()
        signal = db.SaveScheduleV2(
            auto_prefix=True,
            id=schedule_id,
            status=1,
            _where_status=0,
            _where_coach_userid=coach_id,
        )
        response = {'result': signal and 1 or 0}
        self.write(response)


class ApiScheduleCancel(XsrfBaseHandler):
    def post(self):
        uid = self.get_argument('uid')
        sid = self.get_argument('sid')
        db = DbHelper()
        params = dict(
            auto_prefix=True,
            id=sid,
            status=2,
            _where_status=0,
        )
        if db.IsCoach(uid):
            params['_where_coach_userid'] = uid
        else:
            params['_where_student_userid'] = uid

        signal = db.SaveScheduleV2(**params)
        response = {'result': signal and 1 or 0}
        self.write(response)

class ApiScheduleDel(XsrfBaseHandler):
    def post(self):
        uid = self.get_argument('uid')
        sid = self.get_argument('sid')
        db = DbHelper()
        signal = 0
        if db.IsCoach(uid): # user is a coach
            """
            regular schedules can be delete by coach
            """
            signal = db.SaveScheduleV2(
                auto_prefix=True,
                id=sid,
                deleteflag=1,
                _where_coach_userid=uid,
                _where_status=99,
            )
        else:
            """
            canceled schedules can be deleted by student
            """
            signal = db.SaveScheduleV2(
                auto_prefix=True,
                id=sid,
                deleteflag=1,
                _where_student_userid=uid,
                _where_status=2
            )
        response = {"result": signal and 1 or 0}
        self.write(response)

class ApiScheduleMod(XsrfBaseHandler):
    def post(self):
        coach_id = self.get_argument('coach_id')
        schedule_id = self.get_argument('sid')
        regular_name = self.get_argument('rname')
        db = DbHelper()
        # a regular schedule's schedule_name can be modified by the coach who created it
        signal = db.SaveScheduleV2(
            auto_prefix=True,
            id=schedule_id,
            name=regular_name,
            _where_coach_userid=coach_id,
            _where_status=99,
        )
        response = {"result": signal and 1 or 0}
        self.write(response)


class ApiFitnessCategoryList(BaseHandler):
    def get(self):
        ctype = self.get_argument('type')
        db = DbHelper()
        entrys = db.QueryEntrys(count=0, entry_type=ctype)
        if len(entrys) > 0:
            avatar_url = self.get_absurl(Settings.UPLOAD_URL + entrys[0]['entry_image'])
        else:
            avatar_url = self.get_absurl('/static/img/avatar/ads/default.jpeg')
        category_list = db.QueryCategory(0, category_type={'1':3, '2':4}[ctype])
        category_list = list(category_list)
        category_list.sort(key=itemgetter('category_sortweight'), reverse=True)
        for c in category_list:
            c['category_avatar'] = self.get_absurl(Settings.UPLOAD_URL + c['category_avatar'])
        resultlist = {'result': 1, 'FitnessCategoryList': category_list, 'CategoryAvatar' : avatar_url}
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiFitnessDataAdd(XsrfBaseHandler):
    def post(self):
        student_id = self.get_argument('student_id')
        lesson_id = self.get_argument('lesson_id')
        array = json.loads(self.request.headers['json'])
        db = DbHelper()
        response = {'result': 0}
        for a in array:
            fitness_data_params = dict(
                auto_prefix=True,
                categoryid=a['categoryid'],
                scheduleid=lesson_id,
                userid=student_id,
                source=2 # by coach
            )
            if 'duration' in a:
                fitness_data_params['duration'] = a['duration']
            elif 'kg*reps' in a:
                fitness_data_params['kgreps'] = map(json.dumps, a['kg*reps'])
            if db.SaveUserDataV2(**fitness_data_params) > 0:
                response = {'result':1}
        self.write(response)


class ApiFitnessDataMod(XsrfBaseHandler):
    def post(self):
        # coach_id = self.get_argument('coach_id')
        schedule_id = self.get_argument('lesson_id')
        data_ls = json.loads(self.request.headers['json'])
        response = {"result": 1}
        db = DbHelper()
        for data in data_ls:
            params = dict(
                auto_prefix=True,
                id=data['data_id'],
                _where_scheduleid=schedule_id,
            )
            sorted_keys = sorted(data.keys())
            if sorted_keys == ['data_id', 'duration']:
                params['duration'] = data['duration']

            elif sorted_keys == ['data_id', 'kg*reps']:
                params['kgreps'] = json.dumps(data['kg*reps'])

            db.SaveUserDataV2(**params)
        self.write(response)


class ApiScheduleFitnessData(BaseHandler):
    def get(self):
        sid = self.get_argument('sid')
        db = DbHelper()
        fds = db.QueryFitnessData(user_data_scheduleid=sid)
        calory_gross = 0
        fd_3_ls = [ fd for fd in fds if fd['category_type'] == 3]
        fd_4_ls = [ fd for fd in fds if fd['category_type'] == 4]
        for fd in fd_3_ls:
            # 心肺耐力训练
            calory_unit = fd['category_calory_unit']
            duration = fd['user_data_duration']
            calory_gross += calory_unit * duration
            fd['calorys'] = calory_unit * duration
            fd['hours'] = int(duration/60.0)
            fd['minutes'] = int(duration%60)
        temp = []
        for fd in fd_4_ls:            
            # 力量训练
            dt = {}
            calory_unit = fd['category_calory_unit']
            for key in json.loads(fd['user_data_kgreps']):
                calory_gross += calory_unit * eval(key)
                if key in dt:
                    dt[key]['groups'] += 1
                else:
                    kgs, reps = map(int, key.split('*'))
                    dt[key] = dict(
                        groups=1,
                        kgs=kgs,
                        reps=reps,
                    )
            for to_emerge_dt in dt.values():
                fdcopy = deepcopy(fd)
                fdcopy['calorys'] = reduce(lambda x,y: x*y, to_emerge_dt.values()) * calory_unit
                fdcopy.update(to_emerge_dt)
                temp.append(fdcopy)
            

            # calory_gross += calory_unit * eval(fd['user_data_kgreps'])
        fds = temp
        fds.extend(fd_3_ls)
        fds.sort(key=itemgetter('user_data_id'), reverse=True)

        response = {'result':1, 'FitnessDataList':fds, 'calory_gross': calory_gross}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiUserFitnessData(BaseHandler):
    def get_calory_gross(self, sid):
        db = DbHelper()
        fds = db.QueryFitnessData(user_data_scheduleid=sid)
        calory_gross = 0
        fd_3_ls = [ fd for fd in fds if fd['category_type'] == 3]
        fd_4_ls = [ fd for fd in fds if fd['category_type'] == 4]
        for fd in fd_3_ls:
            # 心肺耐力训练
            calory_unit = fd['category_calory_unit']
            duration = fd['user_data_duration']
            calory_gross += calory_unit * duration
        for fd in fd_4_ls:            
            # 力量训练
            calory_unit = fd['category_calory_unit']
            for key in json.loads(fd['user_data_kgreps']):
                calory_gross += calory_unit * eval(key)
        return calory_gross

    def get(self):
        coach_id = self.get_argument('cid')
        student_id = self.get_argument('sid')
        span = self.get_argument('span', "0")

        db = DbHelper()
        ss = db.QueryScheduleV2(
            auto_prefix=True,
            coach_userid=coach_id,
            student_userid=student_id,
            )
        ds = date_stuff.DateScope()
        filter_fn = None
        if span == '1':
            filter_fn = ds.filter_of_lastdays(7, key=lambda x:x['schedule_lessontime'].split()[0])
        elif span == '2':
            filter_fn = ds.filter_of_lastdays(30, key=lambda x:x['schedule_lessontime'].split()[0])
        def fn(x):
            x['calory_gross'] = self.get_calory_gross(x['schedule_id'])
            return x
        tss = map(fn, filter(filter_fn, ss))
        response = {'result':1 , "FitnessData": tss}
        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)
############################################################################################################################################################################################
############################################################################################################################################################################################

def main():
    settings = {
        "cookie_secret": Settings.COOKIE_SECRET_BACKEND,
        "login_url": "/login",
        "xsrf_cookies": False,
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        # "debug": Settings.DEBUG_APP,
        "debug": False if len(sys.argv) > 1 else True,
        "gzip": True,
    }
    application = tornado.web.Application(
        [
    ############################################ Back End #######################################

        (r'/captcha/?\d{0,}', Captcha),
        (r'/checkcaptcha/?', CaptchaCheck),
        (r'/ckedit/image/upload/?', CKEditImageUpload),
        (r'/?', AdminUser),
        (r'/login?', AdminLogin),
        (r'/user/?', AdminUser),
        (r'/user/add/?', AdminUserAdd),
        (r'/user/delete/?', AdminUserDelete),
        (r'/user/edit/?', AdminUserEdit),

        (r'/user/(\d+)/vipcard/?', AdminUserVipcard),
        (r'/user/(\d+)/vipcard/add/?', AdminUserVipcardAdd),
        (r'/user/(\d+)/vipcard/edit/?', AdminUserVipcardEdit),
        (r'/user/vipcard/delete/?', AdminUserVipcardDelete),
        (r'/user/(\d+)/data/?', AdminUserData),
        (r'/user/(\d+)/data/add/?', AdminUserDataAdd),
        (r'/user/(\d+)/data/edit/?', AdminUserDataEdit),
        (r'/user/data/delete/?', AdminUserDataDelete),
        

        (r'/ads/?', AdminAds),
        (r'/ads/add/?', AdminAdsAdd),
        (r'/ads/delete/?', AdminAdsDelete),
        (r'/ads/edit/?', AdminAdsEdit),
        (r'/category/?', AdminCategory),
        (r'/category/add/?', AdminCategoryAdd),
        (r'/category/delete/?', AdminCategoryDelete),
        (r'/category/edit/?', AdminCategoryEdit),

        (r'/gym/?', AdminGym),
        (r'/gym/add/?', AdminGymAdd),
        (r'/gym/delete/?', AdminGymDelete),
        (r'/gym/edit/?', AdminGymEdit),

        (r'/gym/(\d+)/branch/?', AdminGymBranch),
        (r'/gym/(\d+)/branch/edit/?', AdminGymBranchEdit),
        (r'/gym/(\d+)/branch/add/?', AdminGymBranchAdd),
        (r'/gym/(\d+)/branch/delete/?', AdminGymBranchDelete),

        (r'/course/?', AdminCourse),
        (r'/course/add/?', AdminCourseAdd),
        (r'/course/delete/?', AdminCourseDelete),
        (r'/course/edit/?', AdminCourseEdit),

        (r'/schedule/?', AdminSchedule),
        (r'/schedule/add/?', AdminScheduleAdd),
        (r'/schedule/delete/?', AdminScheduleDelete),
        (r'/schedule/copy/?', AdminScheduleCopy),
        (r'/schedule/edit/?', AdminScheduleEdit),

        (r'/teacher/?', AdminTeacher),
        (r'/teacher/add/?', AdminTeacherAdd),
        (r'/teacher/delete/?', AdminTeacherDelete),
        (r'/teacher/edit/?', AdminTeacherEdit),
        (r'/image/upload/?', AdminImageUpload),

        (r'/order/?', AdminOrder),
        (r'/order/add/?', AdminOrderAdd),
        (r'/order/delete/?', AdminOrderDelete),
        (r'/order/edit/?', AdminOrderEdit),

        (r'/privateteacher/?', AdminPrivateTeacher),
        (r'/privateteacher/add/?', AdminPrivateTeacherAdd),
        (r'/privateteacher/delete/?', AdminPrivateTeacherDelete),
        (r'/privateteacher/edit/?', AdminPrivateTeacherEdit),
        (r'/push/?', AdminPushNotification),
        (r'/coachauth/?', AdminCoachAuth),
        (r'/entry/?', AdminEntry),
        (r'/entry/add/?', AdminEntryAdd),
        (r'/entry/edit/?', AdminEntryEdit),
        (r'/entry/delete/?', AdminEntryDelete),

    #############################################################################################

        (r'/api/v[\w.]*/?user/login/?', ApiUserLogin),
        (r'/api/v[\w.]*/?user/checkstate/?', ApiUserCheckState),
        (r'/api/v[\w.]*/?user/register/?', ApiUserRegister),
        (r'/api/v[\w.]*/?sendsmscode/registration/?', ApiSendSmsCodeRegistration),
        (r'/api/v[\w.]*/?sendsmscode/findpassword/?', ApiSendSmsCodeFindpassword),
        (r'/api/v[\w.]*/?ads/list/?', ApiAdsList),
        (r'/api/v[\w.]*/?course/list/?', ApiCourseList),
        (r'/api/v[\w.]*/?course/category/list/?', ApiCourseCategoryList), 
        (r'/api/v[\w.]*/?teacher/category/list/?', ApiTeacherCategoryList), 
        (r'/api/v[\w.]*/?course/schedule/list/?', ApiCourseScheduleList), 
        (r'/api/v[\w.]*/?course/time/list/?', ApiCourseTimeList), 
        (r'/api/v[\w.]*/?course/type/list/?', ApiCourseTypeList), 
        (r'/api/v[\w.]*/?course/location/list/?', ApiCourseLocationList), 
        (r'/api/v[\w.]*/?privateteacher/list/?', ApiPrivateteacherList), 
        (r'/api/v[\w.]*/?privateteacher/type/list/?', ApiPrivateteacherTypeList), 
        (r'/api/v[\w.]*/?privateteacher/location/list/?', ApiPrivateteacherLocationList), 
        (r'/api/v[\w.]*/?course/schedule/detail/?', ApiCourseScheduleDetail), 
        (r'/api/v[\w.]*/?privateteacher/detail/?', ApiPrivateteacherDetail), 
        (r'/api/v[\w.]*/?course/teacher/detail/?', ApiCourseTeacherDetail), 
        (r'/api/v[\w.]*/?course/schedule/order/?', ApiCourseScheduleOrder), 
        (r'/api/v[\w.]*/?privateteacher/order/?', ApiPrivateteacherOrder), 
        (r'/api/v[\w.]*/?order/cancel/?', ApiOrderCancel), 
        (r'/api/v[\w.]*/?order/delete/?', ApiOrderDelete), 

        (r'/api/v[\w.]*/?user/detail/?', ApiUserDetail), 
        (r'/api/v[\w.]*/?user/detail/v2/?', ApiUserDetailV2), 
        (r'/api/v[\w.]*/?user/order/list/?', ApiUserOrderList), 
        (r'/api/v[\w.]*/?user/data/list/?', ApiUserDataList), 
        (r'/api/v[\w.]*/?user/data/list/v2/?', ApiUserDataListV2), 
        (r'/api/v[\w.]*/?user/vipcard/list/?', ApiUserVipcardList), 
        (r'/api/v[\w.]*/?user/vipcard/add/?', ApiUserVipcardAdd), 
        (r'/api/v[\w.]*/?user/vipcard/delete/?', ApiUserVipcardDelete), 
        (r'/api/v[\w.]*/?user/vipcard/unbind/?', ApiUserVipcardUnbind), 
        (r'/api/v[\w.]*/?user/update/?', ApiUserUpdate), 
        (r'/api/v[\w.]*/?data/type/list/?', ApiDataTypeList), 
        (r'/api/v[\w.]*/?user/data/add/?', ApiUserDataAdd), 
        (r'/api/v[\w.]*/?user/data/delete/?', ApiUserDataDelete), 
        (r'/api/v[\w.]*/?gymbranch/list/?', ApiGymBranchList), 
        (r'/api/v[\w.]*/?district/businesscircle/list/?', ApiDistrictBussinesscircle), 
        (r'/api/v[\w.]*/?gym/list/?', ApiGymList), 
        (r'/api/v[\w.]*/?gym/course/list/?', ApiGymBranchCourseList), 
        (r'/api/v[\w.]*/?gym/teacher/list/?', ApiGymBranchTeacherList), 
        (r'/api/v[\w.]*/?data/type/list/?', ApiDataTypeList), 
        (r'/api/v[\w.]*/?course/schedule/stock/list/?', ApiCourseScheduleStockList), 
        (r'/api/v[\w.]*/?user/data/add/?', ApiUserDataAdd),
        (r'/api/v[\w.]*/?course/star/?', ApiCourseStar),
        (r'/api/v[\w.]*/?teacher/star/?', ApiTeacherStar),
        (r'/api/v[\w.]*/?user/star/?', ApiUserStar),
        (r'/api/v[\w.]*/?gymbranch/follow/?', ApiGymbranchFollow),
        (r'/api/v[\w.]*/?gymbranch/unfollow/?', ApiGymbranchUnfollow),
        (r'/api/v[\w.]*/?talent/fitnessman/list/?', ApiTalentFitnessmanList),
        (r'/api/v[\w.]*/?talent/privateteacher/list/?', ApiTalentPrivateteacherList),
        (r'/api/v[\w.]*/?user/fans/list/?', ApiUserFansList),
        (r'/api/v[\w.]*/?user/attention/list/?', ApiUserAttentionList),
        (r'/api/v[\w.]*/?user/relations/apply/?', ApiUserRelationsApply),
        (r'/api/v[\w.]*/?user/relations/confirm/?', ApiUserRelationsConfirm),
        (r'/api/v[\w.]*/?user/relations/del/?', ApiUserRelationsDel),
        (r'/api/v[\w.]*/?user/relations/list/?', ApiUserRelationsList),
        (r'/api/v[\w.]*/?user/relations/?', ApiUserRelations),
        (r'/api/v[\w.]*/?user/apply/messages/?', ApiUserApplyMessages),
        (r'/api/v[\w.]*/?user/photos/?', ApiUserPhotos),
        (r'/api/v[\w.]*/?user/photos/upload/?', ApiUserPhotosUpload),
        (r'/api/v[\w.]*/?user/photo/star/?', ApiUserPhotoStar),
        (r'/api/v[\w.]*/?user/comment/?', ApiUserComment),
        (r'/api/v[\w.]*/?user/daily/tasks/?', ApiUserDailyTasks),
        (r'/api/v[\w.]*/?photo/detail/?', ApiPhotoDetail),
        (r'/api/v[\w.]*/?photo/comments/?', ApiPhotoComments),
        (r'/api/v[\w.]*/?coach/auth/?', ApiCoachAuth),
        (r'/api/v[\w.]*/?coach/entry/list?', ApiCoachEntryList),
        (r'/api/v[\w.]*/?coach/lesson/list?', ApiCoachLessonList),
        (r'/api/v[\w.]*/?search/people/?', ApiSearchPeople),
        (r'/api/v[\w.]*/?resource/?', ApiResource),
        (r'/api/v[\w.]*/?fitness/category/list/?', ApiFitnessCategoryList),
        (r'/api/v[\w.]*/?fitness/data/add/?', ApiFitnessDataAdd),
        (r'/api/v[\w.]*/?fitness/data/mod/?', ApiFitnessDataMod),
        (r'/api/v[\w.]*/?schedule/create/?', ApiScheduleCreate),
        (r'/api/v[\w.]*/?schedule/finish/?', ApiScheduleFinish),
        (r'/api/v[\w.]*/?schedule/cancel/?', ApiScheduleCancel),
        (r'/api/v[\w.]*/?schedule/del/?', ApiScheduleDel),
        (r'/api/v[\w.]*/?schedule/mod/?', ApiScheduleMod),
        (r'/api/v[\w.]*/?schedule/fitness/data/?', ApiScheduleFitnessData),
        (r'/api/v[\w.]*/?user/fitness/data/?', ApiUserFitnessData),
        (r'/api/v[\w.]*/?df/([^/]{1,})', ApiDetectFriends),

    #############################################################################################

        ], **settings)

    if len(sys.argv) > 1:
        port = int(sys.argv[1].split('=')[1])
    else:
        port = 9999

    sockets = bind_sockets(port)
    server = HTTPServer(application, xheaders=True)
    server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

############################################################################################################################################################################################
