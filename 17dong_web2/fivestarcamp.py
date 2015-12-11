#!/usr/bin/env python
#-*-coding:utf-8-*-

# # # Author: Willson Zhang
# # # Date: Sep 20th, 2014
# # # Email: willson.zhang1220@gmail.com

import sys, os
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
os.chdir(abspath)

from module.mysqldb import DbHelper
import module.settings as Settings
import module.lianlianpay as LLPay
import Image, ImageOps
import shutil
import datetime
import requests
import decimal
import re
import base64
from itertools import groupby

import M2Crypto
from M2Crypto import BIO, RSA, EVP
from time import gmtime, strftime
from datetime import timedelta, datetime as DateTime
from urllib import unquote
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

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
from module import wzhifuSDK, refundnotify, ebank

import tornado.ioloop, tornado.web, tornado.process, string
import web, uuid, re, time, random, cgi
import urllib, urllib2, urlparse, cookielib, hashlib, socket
import logging, httplib, json

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

try:
    from ordereddict import OrderedDict as orderdict
except:
    from collections import OrderedDict as orderdict

from module.payment import direct_payment
from module.alipay import Alipay

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

if Settings.DEBUG_APP:
    logging.basicConfig(filename = os.path.join(os.getcwd(), 'log.txt'), level = logging.DEBUG)

web.config.debug = False
# if socket.gethostname() != Settings.SERVER_HOST_NAME:
if True:
    web.config.smtp_server = 'smtp.ym.163.com'
    web.config.smtp_port = 25
    web.config.smtp_username = 'no-reply@17dong.com.cn'
    web.config.smtp_password = 'incool-no-reply'
    web.config.smtp_starttls = True

############################################################################################################################################################################################

class TemplateRedering:
    '''使用Jinja2生成模板
    '''
    def dbhelper(self):
        return DbHelper()

    def calcPageSpentTime(self):
        return '%.2f ms' % (self.request.request_time() * 1000.0)

    def getcurrentuser(self):
        user_id = self.get_secure_cookie("AUTHID")
        db = DbHelper()
        if db.IsUserExistById(user_id) == False:
            self.setcurrentuser(None)
            user_id = None
        return user_id

    def setcurrentuser(self, userid, autologin=False):
        if userid is not None:
            if autologin == True:
                self.set_secure_cookie("AUTHID", str(userid), expires_days=3)
            else:
                self.set_secure_cookie("AUTHID", str(userid), expires_days=None)
        else:
            self.clear_cookie("AUTHID")

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

    def filter_dateformat(self, date):
        return date.strftime('%Y-%m-%d')

    def filter_price(self, price):
        if price:
            return "￥{price:.2f}".format(price=price)

    def filter_list(self, iterable):
        return list(iterable)

    def listitemperpage(self):
        return Settings.LIST_ITEM_PER_PAGE

    def render_Jinja_Template(self, template_name, **context):
        globals = context.pop('globals', {})
        jinja_env = Environment(
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'template/jinja2')), 
            trim_blocks=True,
            extensions=["jinja2.ext.do","jinja2.ext.loopcontrols",])
        jinja_env.globals.update(globals)
        jinja_env.globals.update(dbhelper=self.dbhelper)
        jinja_env.globals.update(currentuser=self.getcurrentuser)
        jinja_env.globals.update(listitemperpage=self.listitemperpage)
        jinja_env.globals.update(calcPageSpentTime=self.calcPageSpentTime)
        jinja_env.globals.update(datetimespec=self.datetimespec)
        jinja_env.globals.update(fromsource=self.fromsource)
        jinja_env.filters['dateformat'] = self.filter_dateformat
        jinja_env.filters['price'] = self.filter_price
        jinja_env.filters['list'] = self.filter_list
        return jinja_env.get_template(template_name).render(context)

class BaseHandler(tornado.web.RequestHandler, TemplateRedering):
    '''基础Handler，所有Tornado的Handler为了使用Jinja2模板引擎必须以此类为基类
    '''
    # def write_error(self, status_code, **kwargs):
    #     return self.renderJinjaTemplate("error.html", errorcode=status_code, user=self.getcurrentuser(), db=DbHelper())
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
        })
        onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
        old_template_name = template_name
        if self.is_mobile():
            if template_name.endswith(".html"):
                template_name = "%smobile.html" % template_name[:-4]
            else:
                template_name = template_name

            templatefile = os.path.join(abspath, 'template/jinja2/%s' % template_name)
            # logging.debug("templatefile: %r" % templatefile)
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

        # logging.debug("check_xsrf_cookie: xsrf = %r, token = %r, s7 = %r" % (xsrf, token, s7))

        if s7 != token:
            # logging.debug("check_xsrf_cookie: XSRF argument does not match POST argument")

            raise tornado.web.HTTPError(403, "XSRF argument does not match POST argument")
        else:
            if db.IsUUIDExist(xsrf) == True:
                # logging.debug("check_xsrf_cookie: XSRF argument expired")

                raise tornado.web.HTTPError(403, "XSRF argument expired")
            else:
                # logging.debug("check_xsrf_cookie: XSRF check success")
                
                db.AddValidUUID(xsrf)

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
            # if str(argvalue) == "null" or str(argvalue) == "nil":
            #     ret = True
            # else:
            #     ret = False
            ret = False
    return ret

def GetArgumentValue(handler, argkey, escapehtml=1):
    if escapehtml == 1:
        return None if IsArgumentEmpty(handler, argkey) else cgi.escape(handler.get_argument(argkey))
    else:
        return None if IsArgumentEmpty(handler, argkey) else handler.get_argument(argkey)

def GetApiVersion(handler):
    webpath  = handler.request.path
    elements = webpath.split("/")
    version = elements[2]
    if version.startswith('v'):
        version = version[1:]
        try:
            version = float(version)
        except Exception, e:
            version = None
        return str(version) if version is not None else None
    else:
        return None

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

class Xsrf(BaseHandler):
    def get(self):
        onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
        if not onserver:
            db = DbHelper()
            xsrf  = getuniquestring()
            token = db.CalculateAPIToken(xsrf)
            return self.write("xsrf: %s, token: %s" % (xsrf, token))
        else:
            return self.send_error(404)

class Index(BaseHandler):
    '''首页'''
    def get(self):
        return self.renderJinjaTemplate("frontend/index.html")

class Search(BaseHandler):
    def post(self):
        '''响应前端用户搜索
        '''
        try:
            product_type = int(self.get_argument("type", 0))
        except Exception, e:
            product_type = None

        if product_type is not None:
            db = DbHelper()
            # 首页左侧边栏查询
            if product_type == 1:
                trainingitem = cgi.escape(self.get_argument("trainingitem"))
                trainingplace = cgi.escape(self.get_argument("trainingplace"))
                trainingage = cgi.escape(self.get_argument("trainingage"))

                redirecturl = "/training?"
                paramdict = { "item" : trainingitem, "location" : trainingplace, "age" : trainingage }
                redirecturl = "%s%s" % (redirecturl, urllib.urlencode(paramdict))
                return self.redirect(redirecturl)
            elif product_type == 2:
                travelitem = GetArgumentValue(self, "travelitem")
                travelplace = GetArgumentValue(self, "travelplace")

                redirecturl = "/tourism?"
                paramdict = {}
                if travelplace == "0":
                    paramdict["pitem"] = travelitem
                else:
                    paramdict["pitem"] = travelitem
                    paramdict["pdestplace"] = travelplace
                redirecturl = "%s%s" % (redirecturl, urllib.urlencode(paramdict))
                return self.redirect(redirecturl)
            # 首页顶部商品搜索
            elif product_type == 0:
                inputProductKey = cgi.escape(self.get_argument("inputProductKey", None))
                if inputProductKey is None or len(inputProductKey) == 0:
                    allwords = db.QuerySearchkeywords(startpos=0, count=0, frontend=0)
                    if len(allwords) > 0:
                        watermarkword = allwords[0][1] if not db.IsDbUseDictCursor() else allwords[0]["searchkeyword_text"]
                        redirecturl = "/search?"
                        paramdict = { "type" : 0, "inputkey" : watermarkword }
                        redirecturl = "%s%s" % (redirecturl, urllib.urlencode(paramdict))
                        return self.redirect(redirecturl)
                    else:
                        return self.redirect("/")
                else:
                    db.AddSearchkeyword(inputProductKey)
                    redirecturl = "/search?"
                    paramdict = { "type" : 0, "inputkey" : inputProductKey }
                    if IsArgumentEmpty(self, "user_vendorname") == False:
                        vendor = GetArgumentValue(self, "user_vendorname")
                        paramdict["vendor"] = vendor
                    redirecturl = "%s%s" % (redirecturl, urllib.urlencode(paramdict))

                    return self.redirect(redirecturl)
        else:
            return self.send_error(403)

    def get(self):
        try:
            product_type = int(self.get_argument("type", 0))
        except Exception, e:
            product_type = None

        if product_type is not None:
            if product_type == 0:
                pageindex = 1
                if self.get_argument("p", None):
                    try:
                        pageindex = int(self.get_argument("p"))
                    except Exception, e:
                        pageindex = 1
                vendor = GetArgumentValue(self, "vendor")
                inputProductKey = GetArgumentValue(self, "inputkey")

                return self.renderJinjaTemplate("frontend/f1_search.html", pageindex=pageindex, filters={ "vendor" : vendor }, inputProductKey=inputProductKey)

############################################################################################################################################################################################

class About(BaseHandler):
    '''关于我们'''
    def get(self):
        return self.renderJinjaTemplate("frontend/about.html")

class Cooperation(BaseHandler):
    '''商务合作'''
    def get(self):
        return self.renderJinjaTemplate("frontend/cooperation.html")

class Contact(BaseHandler):
    '''联系我们'''
    def get(self):
        return self.renderJinjaTemplate("frontend/contact.html")

class Faq(BaseHandler):
    '''常见问题'''
    def get(self):
        return self.renderJinjaTemplate("frontend/faq.html")

############################################################################################################################################################################################

class Wintercamp(BaseHandler):
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        item = GetArgumentValue(self, "item")
        location = GetArgumentValue(self, "location")
        age = GetArgumentValue(self, "age")

        if str(location) == "0":
            location = None
        if str(age) == "0":
            age = None

        vendor = GetArgumentValue(self, "vendor")
        sort = self.get_argument("sort", 0)

        return self.renderJinjaTemplate("frontend/f1_wintercamp.html", 
            pageindex=pageindex, 
            filters={ "item" : item, "location" : location, "age" : age, "vendor" : vendor, "sort" : sort })

    def post(self):
        redirecturl = "/wintercamp"

        paramdict = {}
        setted = False
        if IsArgumentEmpty(self, "product_item") == False:
            item = GetArgumentValue(self, "product_item")
            paramdict["item"] = item
            setted = True
        if IsArgumentEmpty(self, "scene_locations") == False:
            location = GetArgumentValue(self, "scene_locations")
            paramdict["location"] = location
            setted = True
        if IsArgumentEmpty(self, "product_applicableage") == False:
            age = GetArgumentValue(self, "product_applicableage")
            paramdict["age"] = age
            setted = True
        if IsArgumentEmpty(self, "user_vendorname") == False:
            vendor = GetArgumentValue(self, "user_vendorname")
            paramdict["vendor"] = vendor
            setted = True
        if IsArgumentEmpty(self, "sort") == False:
            sort = GetArgumentValue(self, "sort")
            paramdict["sort"] = sort
            setted = True

        if setted:
            redirecturl += "?%s" % urllib.urlencode(paramdict)
        
        return self.redirect(redirecturl)

class SummercampIndex(BaseHandler):
    def get(self):
        if self.is_mobile():
            return self.redirect("/summercamp")
        else:
            return self.renderJinjaTemplate("frontend/f1_summercamp_index.html")

class SummercampList(BaseHandler):
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        try:
            item = GetArgumentValue(self, "item")
        except Exception, e:
            item = None
        
        location = GetArgumentValue(self, "location")
        age = GetArgumentValue(self, "age")

        if str(location) == "0":
            location = None
        if str(age) == "0":
            age = None

        vendor = GetArgumentValue(self, "vendor")
        sort = self.get_argument("sort", 0)

        return self.renderJinjaTemplate("frontend/f1_training.html", 
            producttype=7,
            pageindex=pageindex, 
            filters={ "item" : item, "location" : location, "age" : age, "vendor" : vendor, "sort" : sort })

    def post(self):
        redirecturl = "/summercamp"

        paramdict = {}
        setted = False
        if IsArgumentEmpty(self, "product_item") == False:
            item = GetArgumentValue(self, "product_item")
            paramdict["item"] = item
            setted = True
        if IsArgumentEmpty(self, "scene_locations") == False:
            location = GetArgumentValue(self, "scene_locations")
            paramdict["location"] = location
            setted = True
        if IsArgumentEmpty(self, "product_applicableage") == False:
            age = GetArgumentValue(self, "product_applicableage")
            paramdict["age"] = age
            setted = True
        if IsArgumentEmpty(self, "user_vendorname") == False:
            vendor = GetArgumentValue(self, "user_vendorname")
            paramdict["vendor"] = vendor
            setted = True
        if IsArgumentEmpty(self, "sort") == False:
            sort = GetArgumentValue(self, "sort")
            paramdict["sort"] = sort
            setted = True

        if setted:
            redirecturl += "?%s" % urllib.urlencode(paramdict)
        
        return self.redirect(redirecturl)

class Training(BaseHandler):
    '''体育培训'''
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        item = GetArgumentValue(self, "item")
        location = GetArgumentValue(self, "location")
        age = GetArgumentValue(self, "age")

        if str(location) == "0":
            location = None
        if str(age) == "0":
            age = None

        vendor = GetArgumentValue(self, "vendor")
        sort = self.get_argument("sort", 0)

        return self.renderJinjaTemplate("frontend/f1_training.html", 
            producttype=1,
            pageindex=pageindex, 
            filters={ "item" : item, "location" : location, "age" : age, "vendor" : vendor, "sort" : sort })

    def post(self):
        redirecturl = "/training"

        paramdict = {}
        setted = False
        if IsArgumentEmpty(self, "product_item") == False:
            item = GetArgumentValue(self, "product_item")
            # addedurl = "?item=%s" % item
            # redirecturl += addedurl
            paramdict["item"] = item
            setted = True
        if IsArgumentEmpty(self, "scene_locations") == False:
            location = GetArgumentValue(self, "scene_locations")
            # addedurl = "?location=%s" % location if setted == False else "&location=%s" % location
            # redirecturl += addedurl
            paramdict["location"] = location
            setted = True
        if IsArgumentEmpty(self, "product_applicableage") == False:
            age = GetArgumentValue(self, "product_applicableage")
            # addedurl = "?age=%s" % age if setted == False else "&age=%s" % age
            # redirecturl += addedurl
            paramdict["age"] = age
            setted = True
        if IsArgumentEmpty(self, "user_vendorname") == False:
            vendor = GetArgumentValue(self, "user_vendorname")
            # addedurl = "?vendor=%s" % vendor if setted == False else "&vendor=%s" % vendor
            # redirecturl += addedurl
            paramdict["vendor"] = vendor
            setted = True
        if IsArgumentEmpty(self, "sort") == False:
            sort = GetArgumentValue(self, "sort")
            paramdict["sort"] = sort
            setted = True

        if setted:
            redirecturl += "?%s" % urllib.urlencode(paramdict)
        
        return self.redirect(redirecturl)

class PrivateCoach(BaseHandler):

    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        item = GetArgumentValue(self, "item")
        location = GetArgumentValue(self, "location")
        age = GetArgumentValue(self, "age")

        if str(location) == "0":
            location = None
        if str(age) == "0":
            age = None
        sort = self.get_argument("sort", 0)

        return self.renderJinjaTemplate("frontend/f1_training.html", 
            producttype=6,
            pageindex=pageindex, 
            filters={ "item" : item, "location" : location, "age" : age, "vendor" : None, "sort" : sort })

    def post(self):
        redirecturl = "/privatecoach"

        paramdict = {}
        setted = False
        if IsArgumentEmpty(self, "product_item") == False:
            item = GetArgumentValue(self, "product_item")
            # addedurl = "?item=%s" % item
            # redirecturl += addedurl
            paramdict["item"] = item
            setted = True
        if IsArgumentEmpty(self, "scene_locations") == False:
            location = GetArgumentValue(self, "scene_locations")
            # addedurl = "?location=%s" % location if setted == False else "&location=%s" % location
            # redirecturl += addedurl
            paramdict["location"] = location
            setted = True
        if IsArgumentEmpty(self, "product_applicableage") == False:
            age = GetArgumentValue(self, "product_applicableage")
            # addedurl = "?age=%s" % age if setted == False else "&age=%s" % age
            # redirecturl += addedurl
            paramdict["age"] = age
            setted = True
        if IsArgumentEmpty(self, "sort") == False:
            sort = GetArgumentValue(self, "sort")
            paramdict["sort"] = sort
            setted = True

        if setted:
            redirecturl += "?%s" % urllib.urlencode(paramdict)
        
        return self.redirect(redirecturl)

############################################################################################################################################################################################

class Tourism(BaseHandler):
    '''体育旅游'''
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1

        pstatplace = GetArgumentValue(self, "pstatplace")
        pdestplace = GetArgumentValue(self, "pdestplace")
        pitem = GetArgumentValue(self, "pitem")
        pdays = GetArgumentValue(self, "pdays")
        ptype = GetArgumentValue(self, "ptype")
        pvendor = GetArgumentValue(self, "pvendor")
        return self.renderJinjaTemplate("frontend/f1_tourism.html", 
            producttype=2,
            pageindex=pageindex, 
            filters={ "pstatplace" : pstatplace, "pdestplace" : pdestplace, "pitem" : pitem, "pdays" : pdays, "ptype" : ptype, "pvendor" : pvendor })

    def post(self):
        redirecturl = "/tourism"

        paramdict = {}
        setted = False
        if IsArgumentEmpty(self, "product_travelstartplace") == False:
            pstatplace = GetArgumentValue(self, "product_travelstartplace")
            # addedurl = "?pstatplace=%s" % pstatplace
            # redirecturl += addedurl
            paramdict["pstatplace"] = pstatplace
            setted = True
        if IsArgumentEmpty(self, "product_travelendplace") == False:
            pdestplace = GetArgumentValue(self, "product_travelendplace")
            # addedurl = "?pdestplace=%s" % pdestplace if setted == False else "&pdestplace=%s" % pdestplace
            # redirecturl += addedurl
            paramdict["pdestplace"] = pdestplace
            setted = True
        if IsArgumentEmpty(self, "product_item") == False:
            pitem = GetArgumentValue(self, "product_item")
            # addedurl = "?pitem=%s" % pitem if setted == False else "&pitem=%s" % pitem
            # redirecturl += addedurl
            paramdict["pitem"] = pitem
            setted = True
        if IsArgumentEmpty(self, "product_traveldays") == False:
            pdays = GetArgumentValue(self, "product_traveldays")
            # addedurl = "?pdays=%s" % pdays if setted == False else "&pdays=%s" % pdays
            # redirecturl += addedurl
            paramdict["pdays"] = pdays
            setted = True
        if IsArgumentEmpty(self, "product_type") == False:
            ptype = GetArgumentValue(self, "product_type")
            # addedurl = "?ptype=%s" % ptype if setted == False else "&ptype=%s" % ptype
            # redirecturl += addedurl
            paramdict["ptype"] = ptype
            setted = True
        if IsArgumentEmpty(self, "user_vendorname") == False:
            pvendor = GetArgumentValue(self, "user_vendorname")
            # addedurl = "?pvendor=%s" % pvendor if setted == False else "&pvendor=%s" % pvendor
            # redirecturl += addedurl
            paramdict["pvendor"] = pvendor
            setted = True

        if setted:
            redirecturl += "?%s" % urllib.urlencode(paramdict)
        
        return self.redirect(redirecturl)

############################################################################################################################################################################################

class Freetrial(BaseHandler):
    '''课程体验'''
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1

        pitem = GetArgumentValue(self, "pitem")
        plocations = GetArgumentValue(self, "plocations")
        return self.renderJinjaTemplate("frontend/f1_freetrial.html", pageindex=pageindex, filters={ "pitem" : pitem, "plocations" : plocations })

    def post(self):
        redirecturl = "/freetrial"

        paramdict = {}
        setted = False
        if IsArgumentEmpty(self, "product_item") == False:
            pitem = GetArgumentValue(self, "product_item")
            # addedurl = "?pitem=%s" % pitem if setted == False else "&pitem=%s" % pitem
            # redirecturl += addedurl
            paramdict["pitem"] = pitem
            setted = True
        if IsArgumentEmpty(self, "scene_locations") == False:
            plocations = GetArgumentValue(self, "scene_locations")
            # addedurl = "?plocations=%s" % plocations if setted == False else "&plocations=%s" % plocations
            # redirecturl += addedurl
            paramdict["plocations"] = plocations
            setted = True

        if setted:
            redirecturl += "?%s" % urllib.urlencode(paramdict)
        
        return self.redirect(redirecturl)

############################################################################################################################################################################################

class Activities(BaseHandler):
    '''精彩活动'''
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1

        pitem = GetArgumentValue(self, "pitem")
        plocations = GetArgumentValue(self, "plocations")
        return self.renderJinjaTemplate("frontend/f1_activities.html",
            producttype=4,
            pageindex=pageindex, 
            filters={ "pitem" : pitem, "plocations" : plocations })

    def post(self):
        redirecturl = "/activities"

        paramdict = {}
        setted = False
        if IsArgumentEmpty(self, "product_item") == False:
            pitem = GetArgumentValue(self, "product_item")
            # addedurl = "?pitem=%s" % pitem if setted == False else "&pitem=%s" % pitem
            # redirecturl += addedurl
            paramdict["pitem"] = pitem
            setted = True
        if IsArgumentEmpty(self, "scene_locations") == False:
            plocations = GetArgumentValue(self, "scene_locations")
            # addedurl = "?plocations=%s" % plocations if setted == False else "&plocations=%s" % plocations
            # redirecturl += addedurl
            paramdict["plocations"] = plocations
            setted = True

        if setted:
            redirecturl += "?%s" % urllib.urlencode(paramdict)
        
        return self.redirect(redirecturl)

############################################################################################################################################################################################

class Topics(BaseHandler):
    '''热门专题'''
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        return self.renderJinjaTemplate("frontend/f1_topics.html", 
            pageindex=pageindex)

class TopicsDetail(BaseHandler):
    '''专题详情'''
    def get(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 3:
            try:
                articles_id = int(elements[2])
            except Exception, e:
                articles_id = None
        else:
            articles_id = None

        db = DbHelper()
        articleinfo = db.QueryArticleInfo(articles_id)
        articles_auditstate = int(articleinfo[1] if not db.IsDbUseDictCursor() else articleinfo["articles_auditstate"])
        if articles_auditstate != 1:
            return self.send_error(404)
        else:
            return self.renderJinjaTemplate("frontend/f1_topics_detail.html", articles_id=articles_id)

############################################################################################################################################################################################

class Mall(BaseHandler):
    '''积分商城'''
    def get(self):
        return self.renderJinjaTemplate("frontend/f1_mall.html")

############################################################################################################################################################################################

class FindpasswordSendSmsCode(BaseHandler):
    def post(self):
        verifyCode = getuniquestring()[3:9]

        url = Settings.EMPP_URL
        phonenumber = self.get_argument("phonenumber", None)
        message = "您的验证码为：%s，切勿告知他人，请在页面中输入以完成验证！" % verifyCode

        if phonenumber:
            db = DbHelper()
            if db.IsPhonenumberExist(phonenumber) == False:
                return self.write("0")
            else:
                postparam = Settings.EMPP_POST_PARAM
                postparam["mobile"] = phonenumber
                postparam["content"] = message
                response = requests.post(url, postparam)

                if response.status_code == 200:
                    self.set_secure_cookie("SMSCODE", verifyCode, expires_days=0.1)
                    return self.write("1")
                else:
                    return self.write("-1")
        else:
            return self.write("-2")

class RegistrationSendSmsCode(BaseHandler):
    def post(self):
        '''  1：发送成功
             0：手机号码已经被注册
            -1：发送失败
            -2：手机号码为空
            -3：手机号码格式不正确
        '''
        verifyCode = getuniquestring()[3:9]

        url = Settings.EMPP_URL
        phonenumber = self.get_argument("phonenumber", None)
        message = "欢迎使用一起动，您的验证码为：%s，请尽快使用，动起来，让生活更精彩！" % verifyCode

        if phonenumber:
            db = DbHelper()
            if db.IsPhonenumberExist(phonenumber):
                return self.write("0")
            else:
                if re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
                    postparam = Settings.EMPP_POST_PARAM
                    postparam["mobile"] = phonenumber
                    postparam["content"] = message
                    response = requests.post(url, postparam)

                    if response.status_code == 200:
                        self.set_secure_cookie("SMSCODE", verifyCode, expires_days=0.1)
                        return self.write("1")
                    else:
                        return self.write("-1")
                else:
                    return self.write("-3")
        else:
            return self.write("-2")

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
        self.set_secure_cookie("CAPTCHA", ''.join(chars), expires_days=0.1)

        out = StringIO()
        image.save(out, "JPEG", quality=75)
        self.set_header('Content-Type','image/jpeg')
        self.write(out.getvalue())

class Registration(BaseHandler):
    def get(self):
        if self.get_current_user() is not None:
            return self.redirect("/account")
        else:
            return self.renderJinjaTemplate("frontend/registration.html", randstr=str(random.randint(1000, 9999)), verifyResponse={ "isPhoneNumberValid" : True, 
                    "isSmscodeValid" : True, "isUsernameValid" : True, "isPasswordValid" : True, "isCaptchaValid" : True, "user_name" : "", "user_phonenumber" : "" })

    def post(self):
        user_phonenumber = self.get_argument("inputPhoneNumber", None)
        smscode = self.get_argument("inputVerifyCode", None)
        if not self.is_mobile():
            user_name = self.get_argument("inputUserName", None)
            user_password = self.get_argument("inputPassword", None)
            user_password_confirm = self.get_argument("inputPasswordConfirm", None)
            captcha = self.get_argument("inputCaptcha", None)
        
        # 校验输入参数格式
        isPhoneNumberValid = self.isValudPhonenumber(user_phonenumber)
        isSmscodeValid = self.isValidSmsVerifyCode(smscode)
        if not self.is_mobile():
            isUsernameValid = self.isValidUsername(user_name)
            isPasswordValid = self.isValidPassword(user_password, user_password_confirm)
            isCaptchaValid = self.isValidCaptcha(captcha)

        db = DbHelper()
        if not self.is_mobile():
            # 新建用户
            if isPhoneNumberValid == 1 and isSmscodeValid and isUsernameValid == 1 and isPasswordValid == 1 and isCaptchaValid:
                user_id = db.AddUser({ "user_name" : user_name, "user_nickname" : user_name, "user_password" : user_password, 
                    "user_phonenumber" : user_phonenumber, "user_role" : 1, "user_registersource" : 1, "user_registerip" : self.request.remote_ip })
                if user_id != 0:
                    # 注册成功，赠送 100 元优惠券
                    # restriction = json.dumps({ "RestrictionType" : 1, "ProductType" : (1, 2, 6, 7) })
                    # db.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : 50, "coupon_source" : 0, "coupon_restrictions" : restriction }, couponvaliddays=30)

                    #########################################################################################################
                    # 推送相关通知信息
                    message_title = '''欢迎注册成为一起动会员'''
                    message_content = '''恭喜您已经成为一起动会员，最好的产品、最低的市场价尽在一起动！赶快去个人中心完善你的资料，让我们更了解你吧！'''

                    # 向用户发送站内信
                    db.AddMessage(messageinfo={ "message_type" : 2, "message_state" : 1, "message_title" : message_title, "message_publisher" : "系统", 
                        "message_externalurl" : "", "message_externalproductid" : 0, "message_sendtime" : strftime("%Y-%m-%d"), 
                        "message_receiver" : json.dumps([user_id]), "message_content" : message_content })

                    # 向用户发送手机短信
                    url = Settings.EMPP_URL
                    phonenumber = user_phonenumber
                    if re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
                        postparam = Settings.EMPP_POST_PARAM
                        postparam["mobile"]  = phonenumber
                        postparam["content"] = message_content
                        requests.post(url, postparam)
                    #########################################################################################################

                    self.setcurrentuser(user_id)
                    return self.redirect("/registration/success")
                else:
                    return self.send_error(403)
            else:
                return self.renderJinjaTemplate("frontend/registration.html", randstr=str(random.randint(1000, 9999)), verifyResponse={ "isPhoneNumberValid" : isPhoneNumberValid, 
                    "isSmscodeValid" : isSmscodeValid, "isUsernameValid" : isUsernameValid, "isPasswordValid" : isPasswordValid, "isCaptchaValid" : isCaptchaValid, 
                    "user_name" : user_name, "user_phonenumber" : user_phonenumber })
        else:
            if isPhoneNumberValid == 1 and isSmscodeValid:
                return self.redirect("/registration/step2?mobilePhone=%s" % user_phonenumber)
            else:
                return self.renderJinjaTemplate("frontend/registration.html", randstr=str(random.randint(1000, 9999)), verifyResponse={ "isPhoneNumberValid" : isPhoneNumberValid, 
                    "isSmscodeValid" : isSmscodeValid, "user_phonenumber" : user_phonenumber })

    def isValidPassword(self, password1, password2):
        ''' -1, 密码为空
            -2, 密码不一致
            -3, 密码长度不合法（应为 6 - 32 位）
            1,  密码合法
        '''
        if IsArgumentEmpty(self, "inputPassword") or IsArgumentEmpty(self, "inputPasswordConfirm"):
            return -1
        else:
            if password1 != password2:
                return -2
            else:
                if len(password1) < 6 or len(password1) > 32:
                    return -3
                else:
                    return 1

    def isValidUsername(self, username):
        ''' -1, 用户名为空
            -2, 用户名已存在
            -3, 用户名长度不合法（应为 2 - 32 位）
            1,  用户名合法
        '''
        db = DbHelper()
        if IsArgumentEmpty(self, "inputUserName"):
            return -1
        else:
            if db.IsUserExist(username):
                return -2
            else:
                if len(username) < 2 or len(username) > 32:
                    return -3
                else:
                    return 1

    def isValudPhonenumber(self, phonenumber):
        ''' -1, 手机号码格式不正确
            -2, 手机号码已经被注册
            1, 手机号码合法
        '''
        if re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
            db = DbHelper()
            if db.IsPhonenumberExist(phonenumber) == True:
                return -2
            else:
                return 1
        else:
            return -1

    def isValidCaptcha(self, captcha):
        if not captcha:
            return False
        correctVal = self.get_secure_cookie("CAPTCHA")
        return captcha.upper() == correctVal

    def isValidSmsVerifyCode(self, smscode):
        if not smscode:
            return False
        correctVal = self.get_secure_cookie("SMSCODE")
        return smscode == correctVal

class RegistrationStep2(BaseHandler):

    def get(self):
        referer = self.request.headers.get('Referer')
        if referer is not None:
            if "/registration" in referer:
                mobilePhone = GetArgumentValue(self, "mobilePhone")
                return self.renderJinjaTemplate("frontend/registration_step2.html", mobilePhone=mobilePhone, 
                    verifyResponse={ "isUsernameValid" : True, "isPasswordValid" : True, "user_name" : "" })
            else:
                return self.send_error(403)
        else:
            return self.send_error(403)

    def post(self):
        user_phonenumber = self.get_argument("inputPhoneNumber", None)
        user_name = self.get_argument("inputUserName", None)
        user_password = self.get_argument("inputPassword", None)
        user_password_confirm = self.get_argument("inputPasswordConfirm", None)
        
        # 校验输入参数格式
        isUsernameValid = self.isValidUsername(user_name)
        isPasswordValid = self.isValidPassword(user_password, user_password_confirm)

        db = DbHelper()
        # 新建用户
        if isUsernameValid == 1 and isPasswordValid == 1:
            user_id = db.AddUser({ "user_name" : user_name, "user_nickname" : user_name, "user_password" : user_password, 
                "user_phonenumber" : user_phonenumber, "user_role" : 1, "user_registersource" : 1, "user_registerip" : self.request.remote_ip })
            if user_id != 0:
                # 注册成功，赠送 100 元优惠券
                # restriction = json.dumps({ "RestrictionType" : 1, "ProductType" : (1, 2, 6, 7) })
                # db.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : 50, "coupon_source" : 0, "coupon_restrictions" : restriction }, couponvaliddays=30)

                #########################################################################################################
                # 推送相关通知信息
                message_title = '''欢迎注册成为一起动会员'''
                message_content = '''恭喜您已经成为一起动会员，最好的产品、最低的市场价尽在一起动！赶快去个人中心完善你的资料，让我们更了解你吧！'''

                # 向用户发送站内信
                db.AddMessage(messageinfo={ "message_type" : 2, "message_state" : 1, "message_title" : message_title, "message_publisher" : "系统", 
                    "message_externalurl" : "", "message_externalproductid" : 0, "message_sendtime" : strftime("%Y-%m-%d"), 
                    "message_receiver" : json.dumps([user_id]), "message_content" : message_content })

                # 向用户发送手机短信
                url = Settings.EMPP_URL
                phonenumber = user_phonenumber
                if re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
                    postparam = Settings.EMPP_POST_PARAM
                    postparam["mobile"]  = phonenumber
                    postparam["content"] = message_content
                    requests.post(url, postparam)
                #########################################################################################################

                self.setcurrentuser(user_id)
                return self.redirect("/account")
            else:
                return self.send_error(403)
        else:
            return self.renderJinjaTemplate("frontend/registration_step2.html", mobilePhone=user_phonenumber, 
                verifyResponse={ "isUsernameValid" : isUsernameValid, "isPasswordValid" : isPasswordValid, "user_name" : user_name })

    def isValidPassword(self, password1, password2):
        ''' -1, 密码为空
            -2, 密码不一致
            -3, 密码长度不合法（应为 6 - 32 位）
            1,  密码合法
        '''
        if IsArgumentEmpty(self, "inputPassword") or IsArgumentEmpty(self, "inputPasswordConfirm"):
            return -1
        else:
            if password1 != password2:
                return -2
            else:
                if len(password1) < 6 or len(password1) > 32:
                    return -3
                else:
                    return 1

    def isValidUsername(self, username):
        ''' -1, 用户名为空
            -2, 用户名已存在
            -3, 用户名长度不合法（应为 2 - 32 位）
            1,  用户名合法
        '''
        db = DbHelper()
        if IsArgumentEmpty(self, "inputUserName"):
            return -1
        else:
            if db.IsUserExist(username):
                return -2
            else:
                if len(username) < 2 or len(username) > 32:
                    return -3
                else:
                    return 1

class RegistrationSuccess(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        referer = self.request.headers.get('Referer')
        if referer is not None:
            if "/registration" in referer:
                user_id = self.current_user
                db = DbHelper()
                userinfo = db.QueryUserInfoById(user_id)
                return self.renderJinjaTemplate("frontend/registsuccess.html", username=userinfo[1] if not db.IsDbUseDictCursor() else userinfo["user_name"])
            else:
                return self.send_error(403)
        else:
            return self.send_error(403)

class AjaxLogin(XsrfBaseHandler):
    ''' APP 的 WebView 通过 AJAX 模拟登录状态
        返回值: -2 - 无此帐户， -1 - 验证失败， 1 - 登录成功
    '''
    def post(self):
        userid = GetArgumentValue(self, "UID")
        password = GetArgumentValue(self, "UserPassword")
        db = DbHelper()
        checkuserstatus = db.CheckUserByID(userid, password)
        if checkuserstatus == 1:
            self.setcurrentuser(userid)

        # logging.debug("AjaxLogin checkuserstatus: %r" % checkuserstatus)

        resultlist = { "result" : checkuserstatus }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class Login(BaseHandler):
    def get(self):
        login_type = self.get_argument("type", None)
        # 退出登录
        if login_type and login_type == "logout":
            db = DbHelper()
            user_id = self.current_user
            userinfo = db.QueryUserInfoById(user_id)

            if not db.IsDbUseDictCursor():
                username = userinfo[1] if userinfo is not None else ""
            else:
                username = userinfo["user_name"] if userinfo is not None else ""
            self.setcurrentuser(None)
            return self.renderJinjaTemplate("frontend/login.html", verifyResponse={"inputfieldempty" : False, "checkuserstatus" : 1, "username" : username}, next=self.get_argument("next", "/"))
        # 登录
        else:
            user_id = self.current_user
            if user_id:
                return self.redirect("/")
            else:
                # onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
                # if onserver:
                #     if self.is_mobile():
                #         return self.renderJinjaTemplateV2("frontend/login.mobile.html", verifyResponse={"inputfieldempty" : False, "checkuserstatus" : 1, "username" : ""}, next=self.get_argument("next", "/"))
                #     else:
                #         return self.renderJinjaTemplateV2("frontend/login.html", verifyResponse={"inputfieldempty" : False, "checkuserstatus" : 1, "username" : ""}, next=self.get_argument("next", "/"))
                # else:
                return self.renderJinjaTemplate("frontend/login.html", verifyResponse={"inputfieldempty" : False, "checkuserstatus" : 1, "username" : ""}, next=self.get_argument("next", "/"))

    def post(self):
        inputAutoLogin = GetArgumentValue(self, "inputAutoLogin")
        if inputAutoLogin is not None and inputAutoLogin == "on":
            autologin = True
        else:
            autologin = False
        # return self.write("autologin: %r" % autologin)

        username = cgi.escape(self.get_argument("inputUserName"))
        passwd = cgi.escape(self.get_argument("inputPassword"))
        inputfieldempty = False
        if (username is None) or (username == "") or (passwd is None) or (passwd == ""):
            inputfieldempty = True
        db = DbHelper()
        checkuserstatus = db.CheckUser(username, passwd)

        if (inputfieldempty == True) or (checkuserstatus < 0):
            return self.renderJinjaTemplate("frontend/login.html", verifyResponse={"inputfieldempty" : inputfieldempty, "checkuserstatus" : checkuserstatus, "username" : username}, next=self.get_argument("next", "/"))
        else:
            userinfo = db.QueryUserInfoByNameOrPhonenumber(username)
            self.setcurrentuser(userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"], autologin=autologin)
            return self.redirect(self.get_argument("next", "/"))

class SinaLogin(BaseHandler):
    def get(self):
        # 1. https://api.weibo.com/oauth2/authorize?client_id=683589198&response_type=code&redirect_uri=linkvpn.cc/sinalogin
        app_id = "1278737315"
        app_secret = "f7391a91c59748f9ead090668326c458"

        my_url = urllib.quote("17dong.com.cn/sinalogin")
        # Step1：获取Authorization Code
        if IsArgumentEmpty(self, "code"):
            # Check if the user denied access.
            if IsArgumentEmpty(self, "error") == False:
                return self.redirect("/login")
            else:
                url = "https://api.weibo.com/oauth2/authorize?client_id=%s&response_type=code&redirect_uri=%s" % (app_id, my_url)
                return self.redirect(url)
        # User grant the access.
        if IsArgumentEmpty(self, "code") == False:
            code = GetArgumentValue(self, "code")
            # Step2：通过Authorization Code获取Access Token
            datadict = {"client_id" : app_id, "client_secret" : app_secret, "grant_type" : "authorization_code", "code" : code, "redirect_uri" : my_url}
            token_url = "https://api.weibo.com/oauth2/access_token"
            result = json.loads(self.GetPostResponse(token_url, datadict))
            access_token = ""
            sina_uid = ""
            try:
                access_token = result["access_token"]
                sina_uid = result["uid"]
            except Exception, e:
                return self.send_error(500)
            # Step3：使用Access Token和uid来获取用户信息
            usershow_url = "https://api.weibo.com/2/users/show.json?access_token=%s&uid=%s" % (access_token, sina_uid)
            result = json.loads(self.GetUrlResponse(usershow_url))
            if result.has_key("error_code"):
                return self.send_error(500)
            avatar = result["profile_image_url"]
            nickname = result["screen_name"]
            # Check this uid if registered or not
            db = DbHelper()
            userinfo = db.QueryUserInfoBySinaUID(sina_uid)
            if userinfo is not None:       # user already registered, redirect to account page
                # ALTER TABLE user_table ADD sina_access_token varchar(64) default 'None';
                # ALTER TABLE user_table ADD sina_uid varchar(64) default 'None';
                userid = userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"]
                # update access token if nessesary
                user_sinatoken = userinfo[15] if not db.IsDbUseDictCursor() else userinfo["user_sinatoken"]
                if user_sinatoken is not None and user_sinatoken != "None" and user_sinatoken != access_token:
                    db.UpdateUserInfoById(userid, { "user_sinatoken" : access_token })
                # set session and cookie data
                self.setcurrentuser(userid, autologin=True)

                return self.redirect(self.get_argument("next", "/"))
            else:
                # return render.sinalogin(currentuser(),
                #     {"avatar" : avatar, "name" : nickname, "access_token" : access_token, "sinauid" : sina_uid},
                #     {"verifyusernameok" : True, "usernameisvalid" : True, "verifyemailok" : True, "isemailexist" : False})

                # Param is right, add user to database.
                # randstr = str(time.time()).replace(".", "")[4:]
                # while len(randstr) < 8:
                #     randstr += "0"
                # randstr += str(random.randint(10, 99))
                # username = "17dong_%s" % randstr

                while db.IsUserExist(nickname):
                    randstr = str(time.time()).replace(".", "")[-3:]
                    nickname = "%s%s" % (result["screen_name"], randstr)
                username = nickname

                passwd = str(random.randint(100000, 999999))
                phonenumber = "请绑定手机"

                user_id = db.AddUser({ "user_name" : username, "user_password" : passwd, "user_phonenumber" : phonenumber, "user_role" : 1, 
                    "user_nickname" : nickname,  "user_sinatoken" : access_token, "user_sinauid" : sina_uid, "user_registersource" : 1, "user_registerip" : self.request.remote_ip })
                if user_id != 0:
                    # 注册成功，赠送 100 元优惠券
                    # restriction = json.dumps({ "RestrictionType" : 1, "ProductType" : (1, 2, 6, 7) })
                    # db.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : 50, "coupon_source" : 0, "coupon_restrictions" : restriction }, couponvaliddays=30)

                    # 更新用户头像为 QQ 的头像 #########################################################
                    db.UpdateUserInfoById(user_id, { "user_avatar" : getuniquestring() })
                    outfile  = os.path.join(abspath, 'static/img/avatar/user/P%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id)))

                    imgresponse = requests.get(avatar, stream=True)
                    with open(outfile, 'wb') as out_file:   # 'img.png'
                        shutil.copyfileobj(imgresponse.raw, out_file)
                    del imgresponse
                    #################################################################################

                    self.setcurrentuser(user_id)
                    return self.redirect(self.get_argument("next", "/"))
                else:
                    return self.send_error(403)
                # ---------------------------------------
        else:
            return self.send_error(403)

    def GetPostResponse(self, url, datadict):
        data_urlencode = urllib.urlencode(datadict)
        req = urllib2.Request(url, data_urlencode)
        res_data = urllib2.urlopen(req)
        res = res_data.read()
        return res

    def GetUrlResponse(self, url, https=True):
        conn = httplib.HTTPSConnection("api.weibo.com")
        conn.request(method="GET", url=url)
        response = conn.getresponse()
        res = response.read()
        return res

class QQLogin(BaseHandler):
    def get(self):
        '''Handle QQ user login request.
        '''
        app_id = "101176445"
        app_secret = "73b85fe7c06ce1bd9e273d3bfc56fd78"
        my_url = urllib.quote("17dong.com.cn/qqlogin")
        next_url = self.get_argument("next", "/")

        # Step1：获取Authorization Code
        if IsArgumentEmpty(self, "code"):
            m = hashlib.md5(str(uuid.uuid4()))
            m.digest()
            state = m.hexdigest()
            self.set_secure_cookie("QLS", state)
            url = "https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=%s&redirect_uri=%s&scope=get_user_info&state=%s&next=%s" % (app_id, my_url, state, next_url)
            return self.redirect(url)
        if IsArgumentEmpty(self, "code") == False:
            code = GetArgumentValue(self, "code")
            returnstate = GetArgumentValue(self, "state")
            qqloginstate = self.get_secure_cookie("QLS")
            next_url = self.get_argument("next", "/")
            # TODO: 跨域 cookie 不通导致 QQ 登录异常
            if True == True:
                # Step2：通过Authorization Code获取Access Token
                token_url = "https://graph.qq.com/oauth2.0/token?grant_type=authorization_code&client_id=%s&client_secret=%s&code=%s&state=%s&redirect_uri=%s" % (app_id, app_secret, code, returnstate, my_url)
                result = dict(urlparse.parse_qsl(self.GetUrlResponse(token_url)))
                access_token = ""
                try:
                    access_token = result["access_token"]
                except Exception, e:
                    return self.send_error(403)
                # Step3：使用Access Token来获取用户的OpenID
                openid_url = "https://graph.qq.com/oauth2.0/me?access_token=%s" % access_token
                result = self.GetUrlResponse(openid_url)
                result = result[result.find("(") + 1 : result.find(")")]
                resultdict = json.loads(result)
                if resultdict.has_key("error"):
                    return self.send_error(403)
                openid = resultdict["openid"]
                # Check this openid if registered or not
                db = DbHelper()
                userinfo = db.QueryUserInfoByQieOpenID(openid)
                if userinfo is not None:       # user already registered, redirect to account page
                    userid = userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"]
                    # update access token if nessesary
                    user_qqtoken = userinfo[38] if not db.IsDbUseDictCursor() else userinfo["user_qietoken"]
                    if user_qqtoken is not None and user_qqtoken != access_token:
                        db.UpdateUserInfoById(userid, { "user_qietoken" : access_token })
                    # set session and cookie data
                    self.setcurrentuser(userid, autologin=True)

                    return self.redirect(next_url)

                # Step4：使用Access Token以及OpenID来访问和修改用户数据
                login_url = "https://graph.qq.com/user/get_user_info?access_token=%s&oauth_consumer_key=%s&openid=%s" % (access_token, app_id, openid)
                result = self.GetUrlResponse(login_url)
                resultdict = json.loads(result)
                if resultdict["ret"] == 0:
                    # ALTER TABLE user_table ADD access_token varchar(64) default 'None';
                    # ALTER TABLE user_table ADD openid varchar(64) default 'None';
                    # return render.qqlogin(currentuser(),
                    #     {"avatar" : resultdict["figureurl_qq_1"], "name" : resultdict["nickname"], "access_token" : access_token, "openid" : openid},
                    #     {"verifyusernameok" : True, "usernameisvalid" : True, "verifyemailok" : True, "isemailexist" : False})
                    # Param is right, add user to database.

                    nickname = resultdict["nickname"]
                    avatar = resultdict["figureurl_qq_1"]

                    while db.IsUserExist(nickname):
                        randstr = str(time.time()).replace(".", "")[-3:]
                        nickname = "%s%s" % (resultdict["nickname"], randstr)
                    username = nickname
                    passwd = str(random.randint(100000, 999999))
                    phonenumber = "请绑定手机"
                    
                    user_id = db.AddUser({ "user_name" : username, "user_password" : passwd, "user_phonenumber" : phonenumber, "user_role" : 1, 
                        "user_nickname" : nickname,  "user_qietoken" : access_token, "user_qieopenid" : openid, "user_registersource" : 1, "user_registerip" : self.request.remote_ip })
                    if user_id != 0:
                        # 注册成功，赠送 100 元优惠券
                        # restriction = json.dumps({ "RestrictionType" : 1, "ProductType" : (1, 2, 6, 7) })
                        # db.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : 50, "coupon_source" : 0, "coupon_restrictions" : restriction }, couponvaliddays=30)

                        # 更新用户头像为 QQ 的头像 #########################################################
                        db.UpdateUserInfoById(user_id, { "user_avatar" : getuniquestring() })
                        outfile  = os.path.join(abspath, 'static/img/avatar/user/P%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id)))

                        imgresponse = requests.get(avatar, stream=True)
                        with open(outfile, 'wb') as out_file:   # 'img.png'
                            shutil.copyfileobj(imgresponse.raw, out_file)
                        del imgresponse
                        #################################################################################

                        self.setcurrentuser(user_id)
                        return self.redirect(next_url)
                    else:
                        return self.send_error(403)
                    # ---------------------------------------
                else:
                    return self.send_error(403)
            else:
                return self.send_error(403)

    def GetUrlResponse(self, url, https=True):
        conn = httplib.HTTPSConnection("graph.qq.com")
        conn.request(method="GET", url=url)
        response = conn.getresponse()
        res = response.read()
        return res

class WechatLogin(BaseHandler):
    def get(self):
        # 1. https://open.weixin.qq.com/connect/qrconnect?appid=wxdf05016e6aa2a3b2&redirect_uri=http%3A%2F%2Fwww.17dong.com.cn%2Fwechatlogin&response_type=code&scope=snsapi_login&state=STATE#wechat_redirect
        my_url = urllib.quote("http://www.17dong.com.cn/wechatlogin")
        # Step1：获取Authorization Code
        if IsArgumentEmpty(self, "state"):
            url = "https://open.weixin.qq.com/connect/qrconnect?appid=%s&redirect_uri=%s&response_type=code&scope=snsapi_login&state=%s#wechat_redirect" % (Settings.WX_LOGIN_APPID, my_url, getuniquestring())
            return self.redirect(url)
        else:
            # Check if the user denied access.
            if IsArgumentEmpty(self, "code"):
                return self.redirect("/login")
        # User grant the access.
        if IsArgumentEmpty(self, "state") == False and IsArgumentEmpty(self, "code") == False:
            code = GetArgumentValue(self, "code")
            # Step2：通过Authorization Code获取Access Token
            # https://api.weixin.qq.com/sns/oauth2/access_token?appid=wxdf05016e6aa2a3b2&secret=2ff425a3148dd96cae7f19072ddf215c&code=%s&grant_type=authorization_code
            login_url = "https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code" % (Settings.WX_LOGIN_APPID, Settings.WX_LOGIN_APPSECRET, code)
            result = self.GetUrlResponse(login_url)
            resultdict = json.loads(result)
            try:
                access_token = resultdict["access_token"]
                refresh_token = resultdict["refresh_token"]
                wechatopenid = resultdict["openid"]
            except Exception, e:
                return self.send_error(500)

            # 检测 access_token 是否有效
            # https://api.weixin.qq.com/sns/auth?access_token=ACCESS_TOKEN&openid=OPENID
            accesstoken_url = "https://api.weixin.qq.com/sns/auth?access_token=%s&openid=%s" % (access_token, wechatopenid)
            result = self.GetUrlResponse(accesstoken_url)
            resultdict = json.loads(result)
            if int(resultdict["errcode"]) != 0:
                # https://api.weixin.qq.com/sns/oauth2/refresh_token?appid=APPID&grant_type=refresh_token&refresh_token=REFRESH_TOKEN
                refreshtoken_url = "https://api.weixin.qq.com/sns/oauth2/refresh_token?appid=%s&grant_type=refresh_token&refresh_token=%s" % (wechatopenid, refresh_token)
                result = self.GetUrlResponse(refreshtoken_url)
                resultdict = json.loads(result)
                try:
                    access_token = resultdict["access_token"]
                    refresh_token = resultdict["refresh_token"]
                    wechatopenid = resultdict["openid"]
                except Exception, e:
                    return self.send_error(500)

            # Step3：使用Access Token和uid来获取用户信息
            # https://api.weixin.qq.com/sns/userinfo?access_token=ACCESS_TOKEN&openid=OPENID&lang=zh_CN
            usershow_url = "https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%s&lang=zh_CN" % (access_token, wechatopenid)
            result = json.loads(self.GetUrlResponse(usershow_url))
            if result.has_key("errcode"):
                return self.send_error(500)

            avatar = result["headimgurl"]
            nickname = result["nickname"]
            wechatunionid = result["unionid"]

            logging.debug("--- WechatLogin wechatunionid: %r" % wechatunionid)

            # Check this uid if registered or not
            db = DbHelper()
            userinfo = db.QueryUserInfoByOpenid(wechatunionid)
            if userinfo is not None:       # user already registered, redirect to account page
                # ALTER TABLE user_table ADD sina_access_token varchar(64) default 'None';
                # ALTER TABLE user_table ADD sina_uid varchar(64) default 'None';
                userid = userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"]
                # # update access token if nessesary
                # user_qqtoken = userinfo[13] if not db.IsDbUseDictCursor() else userinfo["user_qqtoken"]
                # if user_qqtoken is not None and user_qqtoken != "None" and user_qqtoken != access_token:
                #     db.UpdateUserInfoById(userid, { "user_qqtoken" : access_token })
                # set session and cookie data
                self.setcurrentuser(userid, autologin=True)

                return self.redirect(self.get_argument("next", "/"))
            else:
                # return render.sinalogin(currentuser(),
                #     {"avatar" : avatar, "name" : nickname, "access_token" : access_token, "sinauid" : sina_uid},
                #     {"verifyusernameok" : True, "usernameisvalid" : True, "verifyemailok" : True, "isemailexist" : False})

                # Param is right, add user to database.
                # randstr = str(time.time()).replace(".", "")[4:]
                # while len(randstr) < 8:
                #     randstr += "0"
                # randstr += str(random.randint(10, 99))
                # username = "17dong_%s" % randstr

                while db.IsUserExist(nickname):
                    randstr = str(time.time()).replace(".", "")[-3:]
                    nickname = "%s%s" % (result["nickname"], randstr)
                username = nickname

                passwd = str(random.randint(100000, 999999))
                phonenumber = "请绑定手机"

                wechatuserinfo = { "user_name" : username, "user_password" : passwd, "user_phonenumber" : phonenumber, "user_role" : 1, 
                    "user_nickname" : nickname, "user_qqopenid" : wechatunionid, "user_registersource" : 1, "user_registerip" : self.request.remote_ip }

                # logging.debug("---------- wechatuserinfo: %r" % wechatuserinfo)

                user_id = db.AddUser(wechatuserinfo)
                if user_id != 0:
                    # 注册成功，赠送 100 元优惠券
                    # restriction = json.dumps({ "RestrictionType" : 1, "ProductType" : (1, 2, 6, 7) })
                    # db.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : 50, "coupon_source" : 0, "coupon_restrictions" : restriction }, couponvaliddays=30)

                    # 更新用户头像为 QQ 的头像 #########################################################
                    db.UpdateUserInfoById(user_id, { "user_avatar" : getuniquestring() })
                    outfile  = os.path.join(abspath, 'static/img/avatar/user/P%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id)))

                    imgresponse = requests.get(avatar, stream=True)
                    with open(outfile, 'wb') as out_file:   # 'img.png'
                        shutil.copyfileobj(imgresponse.raw, out_file)
                    del imgresponse
                    #################################################################################

                    self.setcurrentuser(user_id)
                    return self.redirect(self.get_argument("next", "/"))
                else:
                    return self.send_error(403)
                # ---------------------------------------
        else:
            return self.redirect("/login")

    def GetPostResponse(self, url, datadict):
        data_urlencode = urllib.urlencode(datadict)
        req = urllib2.Request(url, data_urlencode)
        res_data = urllib2.urlopen(req)
        res = res_data.read()
        return res

    def GetUrlResponse(self, url, https=True):
        conn = httplib.HTTPSConnection("api.weixin.qq.com")
        conn.request(method="GET", url=url)
        response = conn.getresponse()
        res = response.read()
        return res

class Account(BaseHandler):
    
    @tornado.web.authenticated
    def get(self):
        updateresult = GetArgumentValue(self, "updatesuccess")
        if updateresult is not None:
            if int(updateresult) == 1:
                return self.renderJinjaTemplate("frontend/account/account_base.html", user_id=self.current_user,
                    verifyResponse={ "updatesuccess" : 1 })
            elif int(updateresult) == 0:
                return self.renderJinjaTemplate("frontend/account/account_base.html", user_id=self.current_user,
                    verifyResponse={ "updatesuccess" : 0 })
            else:
                return self.renderJinjaTemplate("frontend/account/account_base.html", user_id=self.current_user,
                    verifyResponse={  })
        else:
            return self.renderJinjaTemplate("frontend/account/account_base.html", user_id=self.current_user,
                verifyResponse={  })

    @tornado.web.authenticated
    def post(self):
        user_id = self.current_user
        db = DbHelper()

        # 获取性别等信息
        user_gender = self.get_argument("user_gender", "M")
        user_nickname = self.get_argument("user_nickname", "")
        user_birthday = GetArgumentValue(self, "user_birthday")
        user_address = self.get_argument("user_address", "")

        # 获取兴趣爱好
        user_interest = self.get_argument("userInterest", "")
        if user_interest is not None:
            interests = user_interest.split(",")
            for i in interests:
                if i is None or i == "":
                    interests.remove(i)
            user_interest = ",".join(interests)
        else:
            user_interest = None
        db.UpdateUserInfoById(user_id, { "user_gender" : user_gender, "user_nickname" : user_nickname, 
            "user_birthday" : user_birthday, "user_address" : user_address, "user_interest" : user_interest })

        # 获取收货信息
        db.DeleteUserAddress(addressid=0, userid=user_id)
        useraddress_count = int(self.get_argument("userAddressCounter"))
        for i in range(useraddress_count):
            if GetArgumentValue(self, "input_useraddress_recipients%d" % i):
                useraddress_recipients = GetArgumentValue(self, "input_useraddress_recipients%d" % i)
                useraddress_phonenumber = GetArgumentValue(self, "input_useraddress_phonenumber%d" % i)
                useraddress_address = GetArgumentValue(self, "input_useraddress_address%d" % i)
                useraddress_zipcode = GetArgumentValue(self, "input_useraddress_zipcode%d" % i)

                useraddressinfo = { "useraddress_recipients" : useraddress_recipients, "useraddress_address" : useraddress_address, 
                    "useraddress_phonenumber" : useraddress_phonenumber, "useraddress_zipcode" : useraddress_zipcode }
                # 增加的 UserAddress，加入
                db.AddUserAddress(user_id, useraddressinfo)

        # 获取游客信息
        db.DeleteUserTraveller(travellerid=0, userid=user_id)
        usertraveller_count = int(self.get_argument("userTravellerCounter"))
        for i in range(usertraveller_count):
            if GetArgumentValue(self, "input_usertraveller_name%d" % i):
                usertraveller_name = GetArgumentValue(self, "input_usertraveller_name%d" % i)
                usertraveller_idcardno = GetArgumentValue(self, "input_usertraveller_idcardno%d" % i)
                usertraveller_type = GetArgumentValue(self, "input_usertraveller_type%d" % i)

                usertravellerinfo = { "usertraveller_name" : usertraveller_name, "usertraveller_type" : usertraveller_type, 
                    "usertraveller_idcardno" : usertraveller_idcardno }
                db.AddUserTraveller(user_id, usertravellerinfo)
        return self.redirect("/account?updatesuccess=1")
        # return self.renderJinjaTemplate("frontend/account/account_base.html", user_id=self.current_user)

class AccountEmailConfirm(BaseHandler):
    '''确认用户电子邮件地址
    '''
    def get(self):
        user_emailpasskey = self.get_argument("passkey", None)
        user_email = self.get_argument("email", None)
        user_id = self.get_argument("uid", None)
        if user_emailpasskey is None or user_email is None or user_id is None:
            return self.send_error(403)
        else:
            # 检验 user_id 与 user_emailpasskey 是否一致
            db = DbHelper()
            userinfo = db.QueryUserInfoById(user_id)
            if userinfo:
                emailpasskey = userinfo[24] if not db.IsDbUseDictCursor() else userinfo["user_emailpasskey"]
                if emailpasskey == user_emailpasskey:
                    # 更新 user_email
                    db.UpdateUserInfoById(user_id, { "user_email" : user_email })

                    # 显示绑定成功页面
                    return self.renderJinjaTemplate("frontend/account/account_email_confirm.html", userid=user_id, useremail=user_email)
                else:
                    return self.send_error(300)
            else:
                return self.send_error(403)

class AccountOrder(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        ''' 0 - 未完成订单
            1 - 已完成订单
            2 - 所有订单
        '''
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1

        ordertype = GetArgumentValue(self, "type")
        ordertype = 2 if ordertype is None else int(ordertype)

        updatesuccess = GetArgumentValue(self, "updatesuccess")
        if updatesuccess is not None:
            if str(updatesuccess) == "1":
                updatesuccess = 1
            else:
                updatesuccess = 0

        return self.renderJinjaTemplate("frontend/account/account_order.html", pageindex=pageindex, updatesuccess=updatesuccess, type=ordertype)

class AccountOrderRefund(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        preorder_id = GetArgumentValue(self, "oid")
        if preorder_id is not None:
            db = DbHelper()
            orderinfo = db.QueryPreorderInfo(preorder_id)
            order_paymentstatus = int(orderinfo[12] if not db.IsDbUseDictCursor() else orderinfo["preorder_paymentstatus"])
            if order_paymentstatus == 1:
                return self.renderJinjaTemplate("frontend/account/account_order_refund.html", preorder_id=preorder_id)
            else:
                return self.send_error(403)
        else:
            return self.send_error(403)

    def post(self):
        preorder_id = GetArgumentValue(self, "oid")
        if preorder_id is not None:
            db = DbHelper()
            orderinfo = db.QueryPreorderInfo(preorder_id)
            order_paymentstatus = int(orderinfo[12] if not db.IsDbUseDictCursor() else orderinfo["preorder_paymentstatus"])
            if order_paymentstatus == 1:
                refundReason = GetArgumentValue(self, "refundReason")
                db.UpdatePreorderInfo(preorder_id, { "preorder_appraisal" : refundReason, "preorder_refundstatus" : 2 })

                return self.redirect("/account/order")
            else:
                return self.send_error(403)
        else:
            return self.send_error(403)

class AccountInfo(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        return self.renderJinjaTemplate("frontend/account/account_info.html", pageindex=pageindex)
    
class AccountIntegration(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        return self.renderJinjaTemplate("frontend/account/account_integration.html", pageindex=pageindex)
    
class AccountCoupon(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("frontend/account/account_coupon.html")
    
class AccountFavorite(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("frontend/account/account_favorite.html")
    
class AccountReport(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        return self.renderJinjaTemplate("frontend/account/account_report.html")

class AccountAddressAdd(BaseHandler):

    def post(self):
        # 'uid' : uid, 'name' : name, 'phone' : phone, 'address' : address, 'zipcode' : zipcode
        uid = GetArgumentValue(self, "uid")
        name = GetArgumentValue(self, "name")
        phone = GetArgumentValue(self, "phone")
        address = GetArgumentValue(self, "address")
        zipcode = GetArgumentValue(self, "zipcode")

        if name is None and phone is None and address is None and zipcode is None:
            return self.write("")

        db = DbHelper()
        useraddress_id = db.AddUserAddress(uid, { "useraddress_recipients" : name, "useraddress_phonenumber" : phone, "useraddress_address" : address, "useraddress_zipcode" : zipcode })

        htmlstr = '''
            <div class="clearfix w990 f14 c8">
                <label class="w678 radio-inline"><input type="radio" name="user_gender" id="inlineRadio1" value="%s">&nbsp;
                    %s, %s, %s, %s
                </label>
            </div>''' % (useraddress_id, name, phone, address, zipcode)

        return self.write(htmlstr)

class ProductDetail(BaseHandler):
    def get(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 3:
            try:
                product_id = int(elements[2])
            except Exception, e:
                product_id = None
        else:
            product_id = None

        if product_id:
            db = DbHelper()
            productinfo = db.QueryProductInfo(product_id)
            if productinfo:
                product_type = productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"]
            else:
                return self.send_error(404)

            if product_type == 5:
                return self.send_error(404)

            product_status = int(productinfo[13] if not db.IsDbUseDictCursor() else productinfo["product_status"])
            product_auditstatus = int(productinfo[15] if not db.IsDbUseDictCursor() else productinfo["product_auditstatus"])
            if product_status == 0 or product_auditstatus == 0:
                # 如果商品未上架或者未审核通过，则禁止查看其详情
                return self.renderJinjaTemplate("frontend/f1_detail.html", productid=product_id, name=None, location=None, time=None, productoffstate=1)
            else:
                name = GetArgumentValue(self, "name")
                location = GetArgumentValue(self, "location")
                time = GetArgumentValue(self, "time")

                name = None if name == "undefined" else name
                location = None if location == "undefined" else location
                time = None if time == "undefined" else time

                # 如果商品对应的场次不存在，则跳转到默认详情页面
                allscenes = db.QueryProductOfScene(product_id, name, location, time)
                if len(allscenes) > 0:
                    return self.renderJinjaTemplate("frontend/f1_detail.html", productid=product_id, name=name, location=location, time=time, productoffstate=0)
                else:
                    return self.redirect("/product/%s" % product_id)
        else:
            return self.send_error(403)

class ProductOrder(BaseHandler):

    @tornado.web.authenticated
    def get(self, pid):
        product_id = pid # self.get_argument("pid", None)
        scene_id = self.get_argument("sid", None)
        preorder_counts = self.get_argument("ct", None)
        preorder_counts_child = self.get_argument("ctc", None)

        db = DbHelper()
        productinfo = db.QueryProductInfo(product_id)
        if not db.IsDbUseDictCursor():
            product_traveltype = productinfo[27] if productinfo[27] is not None else ""
        else:
            product_traveltype = productinfo["product_traveltype"] if productinfo["product_traveltype"] is not None else ""
        product_type = productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"]
        if int(product_type) == 2 and int(product_traveltype) == 0:
            preorder_counts = 1
        if int(product_type) == 4 and int(product_traveltype) == 4:
            preorder_counts = 1
        if int(product_type) == 4 and int(product_traveltype) == 5:
            preorder_counts = 1

        return self.renderJinjaTemplate("frontend/f1_order.html", 
            product_id=product_id, 
            scene_id=scene_id, 
            preorder_counts=preorder_counts, 
            preorder_counts_child=preorder_counts_child, 
            errormsg=None)

    def post(self, pid):
        product_id = pid # self.get_argument("pid", None)
        scene_id = self.get_argument("scene_id", None)
        preorder_counts = self.get_argument("buy-num", None)
        preorder_counts_elder = self.get_argument("buy-num-1", None)
        preorder_counts_child = self.get_argument("buy-num-2", None)

        if preorder_counts is None:
            preorder_counts = preorder_counts_elder

        current_userid = self.current_user
        if current_userid is None:
            urlparam = { "pid" : product_id, "sid" : scene_id }

            if preorder_counts is not None:
                urlparam["ct"] = preorder_counts
            if preorder_counts_elder is not None:
                urlparam["cte"] = preorder_counts_elder
            if preorder_counts_child is not None:
                urlparam["ctc"] = preorder_counts_child

            urlpostfix = "/product/%s/order?%s" % (product_id, urllib.urlencode(urlparam))
            urlpostfix = urllib.quote(urlpostfix)

            redirecturl = "/login?next=%s" % urlpostfix
            return self.redirect(redirecturl)

        db = DbHelper()
        productinfo = db.QueryProductInfo(product_id)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

        redirecturl = "/product/%s/order?" % product_id
        paramdict = { "pid" : product_id }
        if scene_id is not None:
            paramdict["sid"] = scene_id
        if preorder_counts is not None:
            paramdict["ct"] = preorder_counts
        if preorder_counts_child is not None:
            paramdict["ctc"] = preorder_counts_child
        redirecturl = "%s%s" % (redirecturl, urllib.urlencode(paramdict))
        return self.redirect(redirecturl)

class ProductOrderStep2(BaseHandler):

    @tornado.web.authenticated
    def get(self, product_id):
        sid = GetArgumentValue(self, "sid")
        count = GetArgumentValue(self, "count")
        errormsg = None
        return self.renderJinjaTemplate("frontend/f1_order_step2.html", product_id=product_id, scene_id=sid, count=count, errormsg=errormsg)

class ProductComment(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 3:
            try:
                product_id = int(elements[2])
            except Exception, e:
                product_id = None
        else:
            product_id = None
        preorder_id = GetArgumentValue(self, "oid")

        db = DbHelper()
        orderinfo = db.QueryPreorderInfo(preorder_id)

        preorder_joinstatus = int(orderinfo[13] if not db.IsDbUseDictCursor() else orderinfo["preorder_joinstatus"])
        if preorder_joinstatus == 0:
            return self.renderJinjaTemplate("frontend/account/account_order_comment.html", product_id=product_id, preorder_id=preorder_id, isCommentContentValid=True)
        else:
            return self.send_error(403)

    @tornado.web.authenticated
    def post(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 3:
            try:
                product_id = int(elements[2])
            except Exception, e:
                product_id = None
        else:
            product_id = None
        preorder_id = GetArgumentValue(self, "oid")

        comment_level = GetArgumentValue(self, "comment_level")
        comment_score1 = GetArgumentValue(self, "comment_score1")
        comment_score2 = GetArgumentValue(self, "comment_score2")
        comment_score3 = GetArgumentValue(self, "comment_score3")
        comment_content = cgi.escape(self.get_argument("comment_content", ""))

        comment_score1 = 1 if comment_score1 is None else int(comment_score1) + 1
        comment_score2 = 1 if comment_score2 is None else int(comment_score2) + 1
        comment_score3 = 1 if comment_score3 is None else int(comment_score3) + 1

        isCommentContentValid = True
        if len(comment_content) < 10:
            isCommentContentValid = False

        if isCommentContentValid == False:
            return self.renderJinjaTemplate("frontend/account/account_order_comment.html", product_id=product_id, preorder_id=preorder_id, isCommentContentValid=False)
        else:
            db = DbHelper()
            orderinfo = db.QueryPreorderInfo(preorder_id)
            preorder_joinstatus = int(orderinfo[13] if not db.IsDbUseDictCursor() else orderinfo["preorder_joinstatus"])
            if preorder_joinstatus == 0:
                db.AddComment({ "comment_userid" : self.current_user, 
                    "comment_productid" : product_id, 
                    "comment_content" : comment_content, 
                    "comment_level" : comment_level, 
                    "comment_score1" : comment_score1, 
                    "comment_score2" : comment_score2, 
                    "comment_score3" : comment_score3 })

                userinfo = db.QueryUserInfoById(self.current_user)
                if not db.IsDbUseDictCursor():
                    user_points = 0 if userinfo[12] is None else int(userinfo[12])
                    user_points = user_points + 50
                else:
                    user_points = 0 if userinfo["user_points"] is None else int(userinfo["user_points"])
                    user_points = user_points + 50
                db.UpdateUserInfoById(self.current_user, { "user_points" : user_points })

                db.UpdatePreorderInfo(preorder_id, { "preorder_joinstatus" : 1 })

                return self.redirect("/account/order?updatesuccess=1")
            else:
                return self.send_error(403)

class AccountAvatar(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        user_id = self.current_user
        db = DbHelper()
        userinfo = db.QueryUserInfoById(user_id)

        # 获取用户预览大图的文件路径，如果尚未上传大图则使用系统默认大图
        filedir = socket.gethostname() == Settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp'
        if db.GetUserAvatarUniqueString(user_id) is None:
            db.UpdateUserInfoById(user_id, { "user_avatar" : getuniquestring() })
        avatarfile = '/static/img/avatar/user/P%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))
        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False or os.path.getsize(outfile) == 0:
            avatarfile = '/static/img/avatar/user/default_avatar.jpeg'
            outfile  = filedir + avatarfile

        verifyResponse = {"avatarsizeok" : True}
        return self.renderJinjaTemplate("frontend/account/account_avatar.html", 
            avatarfile=avatarfile, 
            ImagePixelSize=self.GetImagePixelSize(outfile), 
            verifyResponse=verifyResponse)

    @tornado.web.authenticated
    def post(self):
        AVATAR_MAXWIDTH  = 300
        AVATAR_MAXHEIGHT = 300

        db = DbHelper()
        user_id = self.current_user

        if not self.request.files.has_key('useravatar'):
            return

        uploadedfile = self.request.files['useravatar'][0]
        original_fname = uploadedfile['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        filename = fname + extension

        filedir = socket.gethostname() == Settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp/static/img/avatar/user' or '/Library/WebServer/Documents/fivestarcamp/static/img/avatar/user'
        # infile就是用户上传的原始照片
        infile   = filedir + '/' + filename
        # 将用户上传的原始照片进行剪裁压缩处理, 这里分两步处理，outfile_temp是通过file input控件自动上传后，处理过的预览大图，outfile是用户点击保存头像后将outfile_temp重命名的预览大图
        outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))

        # 自动保存用户上传的照片文件
        output_file = open(infile, 'w')
        output_file.write(uploadedfile['body'])
        output_file.close()

        # 检查用户上传照片的大小，小于300x300则不接受
        infilepixelsize = self.GetImagePixelSize(infile)
        if infilepixelsize[0] < 300 or infilepixelsize[1] < 300:
            os.remove(infile)
            serverdir = socket.gethostname() == Settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp'
            (useravatarpreview, hascustomavatar) = db.GetUserAvatarPreview(user_id)
            useravatarpreviewpath = serverdir + "/" + useravatarpreview
            verifyResponse = {"avatarsizeok" : False}
            return self.renderJinjaTemplate("frontend/account/account_avatar.html", 
                    avatarfile=useravatarpreview, ImagePixelSize=self.GetImagePixelSize(useravatarpreviewpath), verifyResponse=verifyResponse)

        # 对上传的原始照片文件进行剪裁，宽度固定为240px, 高度可变
        avatar_size = (300, AVATAR_MAXHEIGHT)
        im = Image.open(infile)
        im_width = im.size[0]
        im_height = im.size[1]
        if im_width == im_height:
            avatar_size = (300, 300)
        elif im_width < im_height:
            avatar_size = (300, im_height if im_height < AVATAR_MAXHEIGHT else AVATAR_MAXHEIGHT)
        else:
            avatar_size = (300, int(im_height * (300.0 / im_width)))

        # 将用户上传的原始照片文件infile经处理保存为outfile_temp
        formatted_im = ImageOps.fit(im, avatar_size, Image.ANTIALIAS, centering = (0.5,0.5))
        formatted_im.save(outfile_temp, "JPEG")
        avatarfile = '/static/img/avatar/user/P%s_%s_temp.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))

        # 为了节约服务器空间，删除用户上传的原始照片文件
        os.remove(infile)

        # 使用outfile_temp重新生成页面
        verifyResponse = {"avatarsizeok" : True}
        return self.renderJinjaTemplate("frontend/account/account_avatar.html", 
                    avatarfile=avatarfile, ImagePixelSize=self.GetImagePixelSize(outfile_temp), verifyResponse=verifyResponse)

    def GetImagePixelSize(self, imagefilepath):
        imout = Image.open(imagefilepath)
        newsize = imout.size
        return newsize

class AccountAvatarUpdate(BaseHandler):

    @tornado.web.authenticated
    def post(self):
        AVATAR_MAXWIDTH  = 300
        AVATAR_MAXHEIGHT = 300

        db = DbHelper()
        user_id = self.current_user

        # 将用户选择的照片文件上传到服务器
        filedir = socket.gethostname() == Settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp/static/img/avatar/user' or '/Library/WebServer/Documents/fivestarcamp/static/img/avatar/user'

        outfile  = filedir + '/P%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))
        outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))

        x1 = 0
        y1 = 0
        x2 = 100
        y2 = 100
        try:
            # 获取用户通过javascript在预览图上勾选的图像坐标数据
            x1 = int(self.get_argument("x1", x1))
            y1 = int(self.get_argument("y1", y1))
            x2 = int(self.get_argument("x2", x2))
            y2 = int(self.get_argument("y2", y2))
        except Exception, e:
            pass

        avatar_large =   filedir + '/L%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))

        # 将预览大图outfile_temp正式命名为outfile (outfile在用户个人资料中显示)
        if os.path.exists(outfile_temp) == True:
            outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))
            if os.path.exists(outfile) == True:
                os.remove(outfile)
            if os.path.exists(avatar_large) == True:
                os.remove(avatar_large)
            
            db.UpdateUserInfoById(user_id, { "user_avatar" : getuniquestring() })
            outfile  = filedir + '/P%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))
            shutil.move(outfile_temp, outfile)

        # 保存用户头像时规格， large(100x100)
        avatar_large =   filedir + '/L%s_%s.jpeg' % (user_id, db.GetUserAvatarUniqueString(user_id))

        # 如果用户没用通过file input控件上传照片，则使用缺省照片作为预览大图
        if os.path.exists(outfile) == False:
            outfile = filedir + '/default_avatar.jpeg'
        # 通过Python的PIL库对预览大图根据用户手选的坐标进行裁剪，裁剪的结果为一个正方形的不定大小照片
        img = Image.open(outfile)
        img.crop((x1, y1, x2, y2)).save(avatar_large)

        # 将上一步中正方形不定大小照片通过PIL库保存为100x100像素的用户大头像
        size = 100, 100
        im = Image.open(avatar_large)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(avatar_large, "JPEG")
        
        # 返回到用户profile页面
        return self.redirect("/account?updatesuccess=1")

    def GetImagePixelSize(self, imagefilepath):
        imout = Image.open(imagefilepath)
        newsize = imout.size
        return newsize

class AccountChangephonenumber(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/account/account_changephonenumber.html")

class ProductGetvpdetail(BaseHandler):
    def get(self):
        db = DbHelper()
        visitedProductIds = self.get_argument("vp")
        visitedProductIds.replace("undefined", "")
        visitedProductIdsList = visitedProductIds.split(",")

        htmlstr = ""
        for i in range(len(visitedProductIdsList)):
            if i > 2:
                break
            product_id = visitedProductIdsList[i]
            productinfo = db.QueryProductInfo(product_id)
            if productinfo is None:
                continue

            productavatar = db.GetProductAvatarPreview(product_id)[0]
            product17dongprice = db.QueryProduct17dongPrice(product_id)

            htmlstr += '''
                <li>
                    <div class="record_images fl">
                        <a href="/product/%s"><img src="%s"></a>
                    </div>
                    <div class="clearfix fl lh20 w126">
                        <a href="/product/%s"><p class="f14">%s</p></a>
                    </div>
                </li>
            ''' % (product_id, productavatar, product_id, productinfo[2] if not db.IsDbUseDictCursor() else productinfo["product_name"])
        return self.write(htmlstr)

class CouponInfo(BaseHandler):

    def post(self):
        db = DbHelper()
        cno = GetArgumentValue(self, "cno")

        couponinfo = db.QueryCouponInfoByCNO(cno) # QueryCouponInfo(cid)
        coupon_amount = "%.2f" % (couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"])

        return self.write(str(coupon_amount))

class FindPassword(BaseHandler):

    def get(self):
        return self.renderJinjaTemplate("frontend/findpassword.html", step=1, verifyResponse={})

    def post(self):
        step = GetArgumentValue(self, "step")
        step = int(step) if step is not None else 1
        if step == 1:
            user_phonenumber = GetArgumentValue(self, "inputUserName")
            captcha = GetArgumentValue(self, "inputCaptcha")

            isUsernameValid = self.isValidUsername(user_phonenumber)
            isCaptchaValid = self.isValidCaptcha(captcha)

            if isUsernameValid != 1 or isCaptchaValid == False:
                return self.renderJinjaTemplate("frontend/findpassword.html", step=1, verifyResponse={ 
                    "isUsernameValid" : isUsernameValid, "isCaptchaValid" : isCaptchaValid, "user_phonenumber" : user_phonenumber })
            else:
                return self.renderJinjaTemplate("frontend/findpassword.html", step=2, verifyResponse={ "phonenumber" : user_phonenumber })

        elif step == 2:
            smscode = GetArgumentValue(self, "inputVerifyCode")
            phonenumber = GetArgumentValue(self, "phonenumber")
            isSmscodeValid = self.isValidSmsVerifyCode(smscode)

            if isSmscodeValid == False:
                return self.renderJinjaTemplate("frontend/findpassword.html", step=2, verifyResponse={
                    "isSmscodeValid" : isSmscodeValid, "phonenumber" : phonenumber })
            else:
                self.set_secure_cookie("USERPHONE", phonenumber, expires_days=0.1)
                return self.renderJinjaTemplate("frontend/findpassword.html", step=3, verifyResponse={ "phonenumber" : phonenumber })

        elif step == 3:
            inputPassword = GetArgumentValue(self, "inputPassword")
            inputPasswordConfirm = GetArgumentValue(self, "inputPasswordConfirm")
            isPasswordValid = self.isValidPassword(inputPassword, inputPasswordConfirm)

            if isPasswordValid != 1:
                return self.renderJinjaTemplate("frontend/findpassword.html", step=3, verifyResponse={
                    "isPasswordValid" : isPasswordValid })
            else:
                db = DbHelper()
                phonenumber = self.get_secure_cookie("USERPHONE")
                db.UpdateUserPasswordByPhoneNumber(phonenumber, inputPassword)
                self.clear_cookie("USERPHONE")
                return self.renderJinjaTemplate("frontend/findpassword.html", step=4, verifyResponse={ "phonenumber" : phonenumber })

        elif step == 4:
            return self.redirect("/login")

    def isValidCaptcha(self, captcha):
        if not captcha:
            return False
        correctVal = self.get_secure_cookie("CAPTCHA")
        return captcha.upper() == correctVal

    def isValidUsername(self, username):
        ''' -1, 用户名为空
            -2, 用户名不存在
            1,  用户名合法
        '''
        db = DbHelper()
        if IsArgumentEmpty(self, "inputUserName"):
            return -1
        else:
            if db.IsPhonenumberExist(username) == False:
                return -2
            else:
                return 1

    def isValidSmsVerifyCode(self, smscode):
        if not smscode:
            return False
        correctVal = self.get_secure_cookie("SMSCODE")
        return smscode == correctVal

    def isValidPassword(self, password1, password2):
        ''' -1, 密码为空
            -2, 密码不一致
            1,  密码合法
        '''
        if IsArgumentEmpty(self, "inputPassword") or IsArgumentEmpty(self, "inputPasswordConfirm"):
            return -1
        else:
            if password1 != password2:
                return -2
            else:
                return 1

class Report(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/report.html")

class ProductGetcomment(BaseHandler):
    def get(self):
        db = DbHelper()
        curindex = int(self.get_argument("curindex"))
        pageindex = self.get_argument("index", 1)
        if str(pageindex) == "上一页":
            pageindex = curindex - 1
        elif str(pageindex) == "下一页":
            pageindex = curindex + 1
        else:
            pageindex = int(pageindex)
        product_id = int(self.get_argument("id"))

        commentitemperpage = Settings.COMMENT_ITEM_PER_PAGE
        totalcount = db.QueryAllCommentCount(product_id)
        startpos = (pageindex - 1) * commentitemperpage
        productcomments = db.QueryComments(startpos, commentitemperpage, product_id)

        htmlstr = ""
        for i in range(len(productcomments)):
            index = i + 1
            commentinfo = productcomments[i]
            commentuserinfo = db.QueryUserInfoById(commentinfo[1] if not db.IsDbUseDictCursor() else commentinfo["comment_userid"])
            commentuseravatar = db.GetUserAvatarPreview(commentuserinfo[0] if not db.IsDbUseDictCursor() else commentuserinfo["user_id"])[0]
            commentcontent = commentinfo[3] if not db.IsDbUseDictCursor() else commentinfo["comment_content"]
            comment_time = commentinfo[4] if not db.IsDbUseDictCursor() else commentinfo["comment_time"]
            commentdatetime = comment_time.strftime("%Y-%m-%d %H:%M:%S") if comment_time is not None else ""
            comment_score1 = commentinfo[6] if not db.IsDbUseDictCursor() else commentinfo["comment_score1"]
            score1 = int(comment_score1) if comment_score1 is not None else 0
            commentscore = score1
            if commentscore == 0:
                starpoint = "nostar"
            elif commentscore == 1:
                starpoint = "onestar"
            elif commentscore == 2:
                starpoint = "twostar"
            elif commentscore == 3:
                starpoint = "threestar"
            elif commentscore == 4:
                starpoint = "fourstar"
            elif commentscore == 5:
                starpoint = "fivestar"

            commentname = commentuserinfo[1] if not db.IsDbUseDictCursor() else commentuserinfo["user_name"]
            htmlstr += '''
            <div class="w948 clearfix">
                <div class="fl mt5 mr13">
                    <img width="50px" src="''' + commentuseravatar + '''" alt="avatar">
                </div>
                <div class="fl w880">
                    <div class="clearfix">
                        <span class="fb f14 corange">''' + commentname + '''</span>
                        <span class="dib fr">
                            <ul class="rating ''' + starpoint + '''">
                                <li class="one">1</li>
                                <li class="two">2</li>
                                <li class="three">3</li>
                                <li class="four">4</li>
                                <li class="five">5</li>
                            </ul>
                        </span>
                    </div>
                    <p><span class="c8">''' + commentcontent + '''</span></p>
                    <p class="mt5"><span class="c8">''' + commentdatetime + '''</span></p>
                </div>
            </div>'''
            if index != len(productcomments):
                htmlstr += '''<hr>'''

        paginationHtmlText = db.GegerateProductCommentPageIndicatorJS(totalcount, pageindex, commentitemperpage, product_id)
        htmlstr += paginationHtmlText
        self.write(htmlstr)

class ProductGetscenelocation(BaseHandler):
    def get(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 3:
            try:
                product_id = int(elements[2])
            except Exception, e:
                product_id = None
        else:
            product_id = None
        scene_name = self.get_argument("name", None)

        db = DbHelper()
        productinfo = db.QueryProductInfo(product_id)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

        if product_type == 1 or product_type == 4 or product_type == 6 or product_type == 7:
            alllocations = db.QueryProductLocationsInScene(product_id, scene_name)
            htmlstr = "<ul class='choose fl'>"
            for onlocation in alllocations:
                htmlstr += '''
                            <li class="scenelocations"><a class="label alocation" href="javascript:void(0);" onclick="slocation(this)">%s</a></li>''' % onlocation
            htmlstr += "</ul>"
            self.write(htmlstr)
        elif product_type == 2:
            alltimeperiods = db.QueryProductTimeperiodsInScene(product_id, scene_name, None)

            htmlstr = "<ul class='choose fl'>"
            for timeperiod in alltimeperiods:
                htmlstr += '''
                            <li class="scenetimeperiod"><a class="label atimeperiod" href="javascript:void(0);" onclick="stimeperiod(this)">%s</a></li>''' % timeperiod
            htmlstr += "</ul>"

            return self.write(htmlstr)

class ProductGetscenetimeperiod(BaseHandler):
    def get(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 3:
            try:
                product_id = int(elements[2])
            except Exception, e:
                product_id = None
        else:
            product_id = None
        scene_name = self.get_argument("name", None)
        scene_locations = self.get_argument("location", None)

        db = DbHelper()
        productinfo = db.QueryProductInfo(product_id)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

        if product_type == 1 or product_type == 4 or product_type == 6 or product_type == 7:
            alltimeperiods = db.QueryProductTimeperiodsInScene(product_id, scene_name, scene_locations)
            htmlstr = "<ul class='choose fl'>"
            for timeperiod in alltimeperiods:
                htmlstr += '''
                            <li class="scenetimeperiod"><a class="label atimeperiod" href="javascript:void(0);" onclick="stimeperiod(this)">%s</a></li>''' % timeperiod
            htmlstr += "</ul>"
        elif product_type == 3:
            alltimeperiods = db.QueryProductTimeperiodsInScene(product_id, scene_name, scene_locations)
            htmlstr = "<ul class='choose fl'>"
            for timeperiod in alltimeperiods:
                htmlstr += '''
                            <li class="scenetimeperiod"><a class="label atimeperiod" href="javascript:void(0);" onclick="stimeperiod(this)">%s</a></li>''' % timeperiod
            htmlstr += "</ul>"
        self.write(htmlstr)

class ProductGetscene(BaseHandler):
    def get(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 3:
            try:
                product_id = int(elements[2])
            except Exception, e:
                product_id = None
        else:
            product_id = None
        scene_name = self.get_argument("name", None)
        scene_locations = self.get_argument("location", None)
        scene_timeperiod = self.get_argument("time", None)

        db = DbHelper()
        productinfo = db.QueryProductInfo(product_id)
        if productinfo is not None:
            product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])
            if product_type == 1 or product_type == 4 or product_type == 6 or product_type == 7:
                allscenes = db.QueryProductOfScene(product_id, scene_name, scene_locations, scene_timeperiod)
                if len(allscenes) > 0:
                    thescene = allscenes[0]

                    sceneid = thescene[0] if not db.IsDbUseDictCursor() else thescene["scene_id"]
                    scenemaxpeople = thescene[4] if not db.IsDbUseDictCursor() else thescene["scene_maxpeople"]
                    scenemaxpeople = scenemaxpeople if scenemaxpeople is not None else 0

                    htmlstr = '''<input type="hidden" id="scene_id" name="scene_id" value="%s">
                                 <input type="hidden" id="scene_maxpeople" name="scene_maxpeople" value="%s">
                              ''' % (sceneid, scenemaxpeople)
                else:
                    htmlstr = '''<input type="hidden" id="scene_id" name="scene_id" value="0">
                                 <input type="hidden" id="scene_maxpeople" name="scene_maxpeople" value="0">'''
                self.write(htmlstr)
            elif product_type == 3:
                allscenes = db.QueryProductOfScene(product_id, scene_name, scene_locations, scene_timeperiod)
                if len(allscenes) > 0:
                    thescene = allscenes[0]
                    sceneid = thescene[0] if not db.IsDbUseDictCursor() else thescene["scene_id"]
                    htmlstr = '''<input type="hidden" id="scene_id" name="scene_id" value="%s">
                              ''' % sceneid
                    self.write(htmlstr)
                else:
                    self.write('''<input type="hidden" id="scene_id" name="scene_id" value="0">''')
            elif product_type == 2:
                allscenes = db.QueryProductOfScene(product_id, scene_name, None, scene_timeperiod)
                if len(allscenes) > 0:
                    thescene = allscenes[0]
                    sceneid = thescene[0] if not db.IsDbUseDictCursor() else thescene["scene_id"]
                    scenefullprice = thescene[5] if not db.IsDbUseDictCursor() else thescene["scene_fullprice"]
                    scenechildprice = thescene[6] if not db.IsDbUseDictCursor() else thescene["scene_childprice"]
                    scenefullprice = scenefullprice if scenefullprice is not None else "¥ 0.00"
                    scenechildprice = scenechildprice if scenechildprice is not None else "¥ 0.00"

                    scontainer = '''<input type="hidden" id="scene_id" name="scene_id" value="%s">
                              ''' % sceneid
                    pricefull = "¥ %.2f" % scenefullprice
                    pricechild = "¥ %.2f" % scenechildprice
                    
                    resultlist = { "scontainer" : scontainer, "pricefull" : pricefull, "pricechild" : pricechild }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
                else:
                    resultlist = { "scontainer" : '''<input type="hidden" id="scene_id" name="scene_id" value="0">''', "pricefull" : 0, "pricechild" : 0 }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
        else:
            self.set_header('Content-Type','application/json')
            self.write("Fail")

class ProductGetprice(BaseHandler):
    def get(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 3:
            try:
                product_id = int(elements[2])
            except Exception, e:
                product_id = None
        else:
            product_id = None
        db = DbHelper()
        productinfo = db.QueryProductInfo(product_id)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

        scene_name = self.get_argument("name", None)
        scene_locations = self.get_argument("location", None)
        scene_timeperiod = self.get_argument("time", None)
        count = int(self.get_argument("count", "1"))

        product17dongpricelow = db.QueryProduct17dongPrice(product_id, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)
        product17dongpricehigh = db.QueryProduct17dongPrice(product_id, highprice=1, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)

        marketpricelow = db.QueryProductMarketPrice(product_id, highprice=0, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)
        marketpricehigh = db.QueryProductMarketPrice(product_id, highprice=1, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)

        if product17dongpricelow == product17dongpricehigh:
            price = "¥ %.2f" % float(product17dongpricelow)
            totalprice = "¥ %.2f" % (float(product17dongpricelow) * count)
        else:
            price = "¥ %.2f - ¥ %.2f" % ( float(product17dongpricelow), float(product17dongpricehigh) )
            totalprice = "¥ %.2f - ¥ %.2f" % ( (float(product17dongpricelow) * count), (float(product17dongpricehigh) * count) )

        if marketpricelow == marketpricehigh:
            marketprice = "¥ %.2f" % float(marketpricelow)
        else:
            marketprice = "¥ %.2f - ¥ %.2f" % ( float(marketpricelow), float(marketpricehigh) )

        if product_type == 2:
            count1 = int(self.get_argument("count1", "1"))
            count2 = int(self.get_argument("count2", "0"))
            product17dongchildpricelow  = db.QueryProduct17dongChildPrice(product_id, highprice=0, scenename=scene_name, scenetimeperiod=scene_timeperiod)
            product17dongchildpricehigh = db.QueryProduct17dongChildPrice(product_id, highprice=1, scenename=scene_name, scenetimeperiod=scene_timeperiod)

            # 体育旅游计算总价时需要加上儿童价
            if product17dongchildpricelow == product17dongchildpricehigh:
                childprice = "¥ %.2f" % float(product17dongchildpricelow)
                if product17dongpricelow == product17dongpricehigh:
                    totalprice = "¥ %.2f" % (float(product17dongpricelow) * count1 + float(product17dongchildpricelow) * count2)
                else:
                    totalprice = "¥ %.2f - ¥ %.2f" % ( float(product17dongpricelow) * count1 + float(product17dongchildpricelow) * count2, float(product17dongpricehigh) * count1 + float(product17dongchildpricelow) * count2 )
            else:
                childprice = "¥ %.2f - ¥ %.2f" % ( float(product17dongchildpricelow), float(product17dongchildpricehigh) )
                totalprice = "¥ %.2f - ¥ %.2f" % ( float(product17dongpricelow) * count1 + float(product17dongchildpricelow) * count2, float(product17dongpricehigh) * count1 + float(product17dongchildpricehigh) * count2 )
        else:
            childprice = ""

        productprice = productinfo[9] if not db.IsDbUseDictCursor() else productinfo["product_price"]

        if product_type == 3:
            singleprice = float(productprice) if productprice is not None else 0
            totalprice = "¥ %.2f" % (count * singleprice)

        if product_type == 5:
            singleprice = float(productprice) if productprice is not None else 0
            totalprice = "%.0f 分" % (count * singleprice)

        resultlist = { "pricespan" : price, "marketpricespan" : marketprice, "totalpricespan" : totalprice, "childpricespan" : childprice }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        return self.write(jsonstr)

class ProductShowInfo(BaseHandler):
    def get(self, product_id):
        name = GetArgumentValue(self, "name")
        if name == "description" or name == "price" or name == "teachlocation" or name == "paymentprocess":
            return self.renderJinjaTemplate("frontend/productshowinfo.html", productid=product_id, name=name)
        else:
            return self.send_error(404)

class ProductGetCoupon(BaseHandler):
    @tornado.web.authenticated
    def get(self, product_id):
        return self.renderJinjaTemplate("frontend/productgetcoupon.html", productid=product_id)

class ProductCouponUserDraw(BaseHandler):
    def post(self, product_id):
        user_id = GetArgumentValue(self, "UID")
        product_id = GetArgumentValue(self, "PID")

        db = DbHelper(cursorclass=Settings.DB_DICTCURSOR)
        producthascoupon = db.IsProductHasCoupon(product_id)
        if producthascoupon:
            productinfo = db.QueryProductInfo(product_id)
            if not db.IsDbUseDictCursor():
                product_coupons = float(productinfo[33]) if productinfo[33] is not None else 0
            else:
                product_coupons = float(productinfo["product_couponwhenorder"]) if productinfo["product_couponwhenorder"] is not None else 0
            if product_coupons > 0:
                userhasgetcoupon = db.IsUserGetSpecificCoupon(userid=user_id, productid=product_id, activityid=None)
                if userhasgetcoupon:
                    resultlist = { "result" : "0" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)
                else:
                    restriction = json.dumps({ "RestrictionType" : 4, "ProductID" : (int(product_id),) })
                    couponsource = int("1%s" % int(product_id))
                    if not db.IsDbUseDictCursor():
                        validdays = int(productinfo[34]) if productinfo[34] is not None else 30
                    else:
                        validdays = int(productinfo["product_couponwhenactivate"]) if productinfo["product_couponwhenactivate"] is not None else 30
                    validdays = validdays if validdays > 0 else 30
                    db.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : product_coupons, "coupon_restrictions" : restriction, "coupon_source" : couponsource }, couponvaliddays=validdays)

                    resultlist = { "result" : "1" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)
            else:
                resultlist = { "result" : "-1" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
        else:
            resultlist = { "result" : "-2" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)

class AutocompleteSearchKeywords(BaseHandler):
    def get(self):
        callback = self.get_argument("callback", None)
        if callback is not None:
            db = DbHelper()
            inputkey = GetArgumentValue(self, "q")
            
            resultlist = []
            allproducts = db.FuzzyQueryProduct(inputkey, 0, 8, producttype=0, frontend=1, productvendorid=0)
            for productinfo in allproducts:
                resultlist.append(productinfo[2] if not db.IsDbUseDictCursor() else productinfo["product_name"])
            
            jsonstr = "%s(%s)" % (callback, json.dumps(resultlist, cls=EnhancedJSONEncoder))
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)

class Agreement(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/agreement.html")

class AccountCouponDelete(BaseHandler):
    def post(self):
        coupon_id = cgi.escape(self.get_argument("cid"))
        current_userid = self.current_user
        try:
            coupon_id = int(coupon_id)
        except Exception, e:
            coupon_id = None
        if coupon_id:
            db = DbHelper()
            couponinfo = db.QueryCouponInfo(coupon_id)

            couponuserid = couponinfo[1] if not db.IsDbUseDictCursor() else couponinfo["coupon_userid"]

            if int(couponuserid) == int(current_userid):
                db.DeleteCoupon(coupon_id)
                return self.write("Success")
            else:
                return self.write("Fail")
        else:
            return self.write("Fail")

class AccountUpdatePhonenumber(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        db = DbHelper()
        current_userid = self.current_user
        userinfo = db.QueryUserInfoById(current_userid)
        user_phonenumber = userinfo[3] if not db.IsDbUseDictCursor() else userinfo["user_phonenumber"]

        # 直接填写手机号码
        if self.isPhonenumberOK(user_phonenumber) != 1:
            return self.renderJinjaTemplate("frontend/account/account_updatephone.html", step=1, updatephonenumber=False, 
                verifyResponse={ "isSmscodeValid" : True, "isPhoneNumberValid" : 1, "user_phonenumber" : "" })
        # 修改绑定手机号码
        else:
            return self.renderJinjaTemplate("frontend/account/account_updatephone.html", step=1, updatephonenumber=True, 
                verifyResponse={ "isSmscodeValid" : True, "isPhoneNumberValid" : 1, "user_phonenumber" : user_phonenumber })

    def post(self):
        db = DbHelper()
        current_userid = self.current_user
        userinfo = db.QueryUserInfoById(current_userid)
        user_phonenumber = userinfo[3] if not db.IsDbUseDictCursor() else userinfo["user_phonenumber"]
        updatephonenumber = False if self.isPhonenumberOK(user_phonenumber) != 1 else True

        if updatephonenumber == True:
            step = GetArgumentValue(self, "step")
            step = int(step) if step is not None else 1
            if step == 1:
                user_phonenumber = GetArgumentValue(self, "inputPhoneNumber")
                inputVerifyCode = GetArgumentValue(self, "inputVerifyCode")

                isPhoneNumberValid = self.isPhonenumberValid(user_phonenumber)
                isSmscodeValid = self.isValidSmsVerifyCode(inputVerifyCode)

                if isPhoneNumberValid != 1 or isSmscodeValid == False:
                    return self.renderJinjaTemplate("frontend/account/account_updatephone.html", step=1, updatephonenumber=updatephonenumber, 
                        verifyResponse={ "isSmscodeValid" : isSmscodeValid, "isPhoneNumberValid" : isPhoneNumberValid, "user_phonenumber" : user_phonenumber })
                else:
                    return self.renderJinjaTemplate("frontend/account/account_updatephone.html", step=2, updatephonenumber=updatephonenumber, 
                        verifyResponse={ "isSmscodeValid" : True, "isPhoneNumberValid" : 1, "user_phonenumber" : "" })
            elif step == 2:
                user_phonenumber = GetArgumentValue(self, "inputPhoneNumber")
                inputVerifyCode = GetArgumentValue(self, "inputVerifyCode")

                isPhoneNumberValid = self.isPhonenumberValid(user_phonenumber, step=2)
                isSmscodeValid = self.isValidSmsVerifyCode(inputVerifyCode)

                if isPhoneNumberValid != 1 or isSmscodeValid == False:
                    return self.renderJinjaTemplate("frontend/account/account_updatephone.html", step=2, updatephonenumber=updatephonenumber, 
                        verifyResponse={ "isSmscodeValid" : isSmscodeValid, "isPhoneNumberValid" : isPhoneNumberValid, "user_phonenumber" : user_phonenumber })
                else:
                    db.UpdateUserInfoById(current_userid, { "user_phonenumber" : user_phonenumber })
                    return self.renderJinjaTemplate("frontend/account/account_updatephone.html", step=3, updatephonenumber=updatephonenumber, 
                        verifyResponse={ "isSmscodeValid" : True, "isPhoneNumberValid" : 1, "user_phonenumber" : user_phonenumber })
        else:
            user_phonenumber = GetArgumentValue(self, "inputPhoneNumber")
            inputVerifyCode = GetArgumentValue(self, "inputVerifyCode")

            isPhoneNumberValid = self.isPhonenumberOK(user_phonenumber)
            isSmscodeValid = self.isValidSmsVerifyCode(inputVerifyCode)

            if isPhoneNumberValid != 1 or isSmscodeValid == False:
                return self.renderJinjaTemplate("frontend/account/account_updatephone.html", step=1, updatephonenumber=False, 
                    verifyResponse={ "isSmscodeValid" : isSmscodeValid, "isPhoneNumberValid" : isPhoneNumberValid, "user_phonenumber" : user_phonenumber })
            else:
                db.UpdateUserInfoById(current_userid, { "user_phonenumber" : user_phonenumber })
                return self.redirect("/account?updatesuccess=1")

    def isPhonenumberOK(self, phonenumber):
        ''' -1, 手机号码格式不正确
            -2, 手机号码为空
             1, 手机号码合法
        '''
        if phonenumber is None:
            return -2
        elif re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
            return 1
        else:
            return -1

    def isPhonenumberValid(self, phonenumber, step=1):
        ''' -1, 手机号码格式不正确
            -2, 手机号码为空
             0, 手机号码不存在
             1, 手机号码合法
        '''
        if phonenumber is None:
            return -2
        elif re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
            db = DbHelper()
            if step == 1:
                if db.IsPhonenumberExist(phonenumber):
                    return 1
                else:
                    return 0
            else:
                if db.IsPhonenumberExist(phonenumber) == False:
                    return 1
                else:
                    return 0
        else:
            return -1

    def isValidSmsVerifyCode(self, smscode):
        if not smscode:
            return False
        correctVal = self.get_secure_cookie("SMSCODE")
        return smscode == correctVal

class AccountUpdateEmail(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/account/account_updateemail.html")
    
class AccountUpdatePassword(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/account/account_updatepassword.html")
    
class ProductOrderUpdate(BaseHandler):
    def post(self):
        '''修改订单状态
            因素：成人数量、儿童数量、发票、积分、优惠券
        '''
        product_id = GetArgumentValue(self, "pid")
        product_sceneid = GetArgumentValue(self, "sid")
        counts = GetArgumentValue(self, "counts")
        counts_child = GetArgumentValue(self, "counts_child")

        needinvoice = self.get_argument("needinvoice", "0")
        usepointcount = self.get_argument("usepointcount", "0")
        usecouponno = GetArgumentValue(self, "usecouponno")
        c2password = GetArgumentValue(self, "c2password")
        upt = GetArgumentValue(self, "upt")
        upt = int(upt)

        db = DbHelper()
        current_userid = self.current_user
        userinfo = db.QueryUserInfoById(current_userid)

        productinfo = db.QueryProductInfo(product_id)
        sceneinfo = db.QuerySceneInfo(product_sceneid)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])
        product_price = productinfo[9] if not db.IsDbUseDictCursor() else productinfo["product_price"]
        product_maxdeductiblepoints = productinfo[14] if not db.IsDbUseDictCursor() else productinfo["product_maxdeductiblepoints"]

        product_price = 0.0
        invoicedelivery_price = 0.0
        discount_price = 0.0
        final_price = product_price
        used_points = 0
        coupon_discount = 0
        c2discount = 0

        if product_type == 3:
            if product_price is not None and int(product_price) == 0:
                product3needpayment = False
            else:
                product3needpayment = True
        else:
            product3needpayment = False

        if counts:
            if product_type == 1 or product_type == 2 or product_type == 4 or product_type == 6 or product_type == 7:
                price = sceneinfo[5] if not db.IsDbUseDictCursor() else sceneinfo["scene_fullprice"]
            elif product_type == 5 or product3needpayment == True:
                price = product_price

            final_price = float(price) * int(counts)
            product_price = float(price) * int(counts)

        if counts_child and product_type == 2:
            if sceneinfo is not None:
                price_child = sceneinfo[6] if not db.IsDbUseDictCursor() else sceneinfo["scene_childprice"]
                final_price += float(price_child) * int(counts_child)
                product_price += float(price_child) * int(counts_child)

        if needinvoice is not None:
            if int(needinvoice) == 1:
                final_price += 10.0
                invoicedelivery_price = 10.0
            else:
                invoicedelivery_price = 0.0

        # 积分判断逻辑 ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # if upt == 1:
        try:
            usepointcount = int(usepointcount)
        except Exception, e:
            self.set_status(503, "503")
            return self.finish()
        if usepointcount is not None and int(usepointcount) > 0:
            used_points = int(usepointcount)
            final_price -= (int(usepointcount) / 100.0)
            discount_price = (int(usepointcount) / 100.0)

            maxusablepoint = int(product_maxdeductiblepoints) if product_maxdeductiblepoints is not None else 0
            if not db.IsDbUseDictCursor():
                maxuserpoint = int(userinfo[12]) if userinfo[12] is not None else 0
            else:
                maxuserpoint = int(userinfo["user_points"]) if userinfo["user_points"] is not None else 0
            if int(usepointcount) > int(maxusablepoint):
                errormsg = "%s" % maxusablepoint
                self.set_status(501, errormsg)
                return self.finish()
            if int(usepointcount) > int(maxuserpoint):
                self.set_status(502, "502")
                return self.finish()

        # 优惠券判断逻辑 ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        if usecouponno is not None:
            if str(usecouponno) == "0":
                pass
            else:
                couponinfo = db.QueryCouponInfoByCNO(usecouponno)
                coupon_discount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]
                coupon_amount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]
                final_price -= float(coupon_amount)
                discount_price += float(coupon_amount)

        # 抵扣券判断逻辑 ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////

        # if upt == 2:
        try:
            c2password = int(c2password)
        except Exception, e:
            self.set_status(510, "510")
            return self.finish()
        if c2password is not None and int(c2password) > 0:
            if db.IsUniqueStringExistsInCoupon(uniquestr=c2password, coupontype=1):
                couponinfo = db.QueryCouponInfoByCNO(cno=c2password)
                coupon_valid = couponinfo[3] if not db.IsDbUseDictCursor() else couponinfo["coupon_valid"]
                if int(coupon_valid) == 1:
                    # allcoupons = db.QueryCoupons(0, count=0, userid=current_userid, couponvalid=1, couponexpired=0, couponsource=-1)
                    coupon_validtime = couponinfo[9] if not db.IsDbUseDictCursor() else couponinfo["coupon_validtime"]
                    coupon_validtime = str(coupon_validtime)
                    validdays = datetime.date(int(coupon_validtime[0:4]), int(coupon_validtime[5:7]), int(coupon_validtime[8:10])) - datetime.date.today()
                    validdays = validdays.days
                    if validdays >= 0:
                        if db.ValidateProductCoupon(productid=product_id, couponid=couponinfo[0] if not db.IsDbUseDictCursor() else couponinfo["coupon_id"]):
                            c2discount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]
                            final_price -= float(c2discount)
                            discount_price += float(c2discount)
                        else:
                            self.set_status(514, "514")
                            return self.finish()
                    else:
                        self.set_status(513, "513")
                        return self.finish()
                else:
                    self.set_status(512, "512")
                    return self.finish()
            else:
                self.set_status(511, "511")
                return self.finish()

        # 返回 josn 数据 ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        
        product_price = "%.2f" % product_price
        invoicedelivery_price = "%.2f" % invoicedelivery_price
        discount_price = "%.2f" % discount_price
        final_price = 0 if final_price < 0 else final_price
        final_price = "%.2f" % final_price

        resultlist = { "ProductPrice" : product_price, "InvoiceDeliveryPrice" : invoicedelivery_price, "DiscountPrice" : discount_price, 
                       "FinalPrice" : final_price, "UsedPoints" : used_points, "CouponDiscount" : coupon_discount, "C2Discount" : c2discount }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        return self.write(jsonstr)

class SendSmsCodeRegistration(BaseHandler):
    def post(self):
        '''  1：发送成功
             0：手机号码已经被注册
            -1：发送失败
            -2：手机号码为空
            -3：手机号码格式不正确
        '''
        phonenumber = GetArgumentValue(self, "mobilePhone")
        verifyCode = getuniquestring()[3:9]

        url = Settings.EMPP_URL
        message = "欢迎使用一起动，您的验证码为：%s，请尽快使用，动起来，让生活更精彩！" % verifyCode

        if phonenumber:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            if db.IsPhonenumberExist(phonenumber):
                resultlist = { "result" : "0", "errormsg" : "手机号码已经被注册" }
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
                        resultlist = { "result" : "-1", "errormsg" : "发送验证验失败" }
                        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                        self.set_header('Content-Type','application/json')
                        self.write(jsonstr)
                else:
                    resultlist = { "result" : "-3", "errormsg" : "手机号码格式不正确" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
        else:
            resultlist = { "result" : "-2", "errormsg" : "手机号码为空，请输入手机号码" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class UserOrderList(BaseHandler):
    def post(self):
        user_id = GetArgumentValue(self, "UID")
        startposition = self.get_argument("startposition", 0)
        count = self.get_argument("count", Settings.LIST_ITEM_PER_PAGE)
        ordertype = self.get_argument("type", 2)
        ordertype = int(ordertype)

        logging.debug("UID: %r, startposition: %r, count: %r, type: %r" % (user_id, startposition, count, ordertype))

        db = DbHelper(cursorclass=Settings.DB_DICTCURSOR)
        paymentstatus = -1 if ordertype == 2 or ordertype == 5 else ordertype
        producttype   =  5 if ordertype == 5 else 0
        alluserorders = db.QueryPreorders(startposition, count, productvendorid=0, userid=user_id, producttype=producttype, paymentstatus=paymentstatus)

        allupdatedorders = []
        for orderinfo in alluserorders:
            if not db.IsDbUseDictCursor():
                orderinfo = list(orderinfo)
                avatarpreview = db.GetProductAvatarPreview(orderinfo[2])[0]
                serveraddress = self.request.headers.get("Host")
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                productinfo = db.QueryProductInfo(orderinfo[2])
                productname = productinfo[2]
                orderinfo.append(avatarurl)
                orderinfo.append(productname)
                allupdatedorders.append(orderinfo)
            else:
                orderinfo = dict(orderinfo)
                avatarpreview = db.GetProductAvatarPreview(orderinfo["preorder_productid"])[0]
                serveraddress = self.request.headers.get("Host")
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                productinfo = db.QueryProductInfo(orderinfo["preorder_productid"])
                productname = productinfo["product_name"]
                orderinfo["avatarurl"] = avatarurl
                orderinfo["productname"] = productname
                orderinfo["preorder_buytime"] = str(orderinfo["preorder_buytime"])
                allupdatedorders.append(orderinfo)

        resultlist = { "result" : "1", "OrderList" : allupdatedorders }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class AppInstall(BaseHandler):
    def get(self):
        if self.is_ios():
            app = GetArgumentValue(self, "app")
            if app is None:
                return self.write('')
            else:
                return self.renderJinjaTemplateV2("frontend/appinstall.html", app=app)
        else:
            return self.write("请用 iPhone 手机的 Safari 浏览器打开此链接。")

class AppDownload(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/appdownload.html")

class AppDownloadMobile1(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/app_download.html")

class AppDownloadMobile2(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/app_download_apk.html")

class VersionIOS(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("static/app/version.plist").read())

class VersionAndroid(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("static/app/version.xml").read())

class WapVersion(BaseHandler):
    def get(self):
        # return self.renderJinjaTemplate("frontend/wap/index.html")
        return self.redirect("/", permanent=True)

class SpecialTopicWinterCamp(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/wintercamp/index.html")

class SpecialTopicRegister(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/register/index.html")

class SpecialTopicValentine(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/valentine/index.html")

class SpecialTopicSwordfight(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/swordfight/index.html")

class SpecialTopicLandingPageBaseketball(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/landingpage/basketball/index.html")

class SpecialTopicSummerCampV2(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/summercamp/v2/index.html")

class SpecialTopicSummerCampV3(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/summercamp/v3/index.html")

class SpecialTopicLandingPageFootball(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/landingpage/football/index.html")

class SpecialTopicLandingPageSwim(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/landingpage/swim/index.html")

class SpecialTopicSummerCamp(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/summercamp/index.html")

class SpecialTopicVoteFamily(BaseHandler):
    def get(self):
        # onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
        # if onserver:
        #     if self.is_mobile():
        #         return self.renderJinjaTemplateV2("special_topic/vote/family/index.mobile.html")
        #     else:
        #         return self.renderJinjaTemplateV2("special_topic/vote/family/index.html")
        # else:
        return self.renderJinjaTemplate("special_topic/vote/family/index.html")

class SpecialTopicVoteFamilyList(BaseHandler):
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        db = DbHelper()
        onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
        serveraddress = self.request.headers.get("Host")
        thevoteid = 7 if not onserver else 12
        allvoteoption = db.QueryVoteOptions(voteid=thevoteid, startpos=(pageindex - 1) * 8, count=8, status=1)
        allvoteoptioncount = len(db.QueryVoteOptions(voteid=thevoteid, startpos=0, count=0, status=1))

        # if onserver:
        #     if self.is_mobile():
        #         return self.renderJinjaTemplateV2("special_topic/vote/family/votelist.mobile.html", pageindex=pageindex, allvoteoption=allvoteoption, allvoteoptioncount=allvoteoptioncount, serveraddress=serveraddress)
        #     else:
        #         return self.renderJinjaTemplateV2("special_topic/vote/family/votelist.html", pageindex=pageindex, allvoteoption=allvoteoption, allvoteoptioncount=allvoteoptioncount, serveraddress=serveraddress)
        # else:
        return self.renderJinjaTemplate("special_topic/vote/family/votelist.html", pageindex=pageindex, allvoteoption=allvoteoption, allvoteoptioncount=allvoteoptioncount, serveraddress=serveraddress)

    def post(self):
        '''
             0 - 投票失败
             1 - 投票成功
             2 - 您已经投票过了，无法再次投票
             3 - 您今天已经投票过了，请明天再来投票
             4 - 投票已结束，无法进行投票
        '''
        uid = self.get_argument("uid")
        optid = self.get_argument("optid")
        current_userid = self.current_user

        if str(uid) == str(current_userid):
            db = DbHelper()
            ret = db.VoteForOption(userid=int(current_userid), voteoptionid=optid)
        else:
            ret = 0
        
        resultlist = { "ret" : ret }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        return self.write(jsonstr)

class SpecialTopicDance(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/dance/index.html")

class SpecialTopicActivity(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/activity/index.html")

class SpecialTopicLotterydraw(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/lotterydraw/index.html")

class SpecialTopicLotterydrawDraw(BaseHandler):
    def post(self, promotion_id):
        '''返回抽奖结果 （ 0 - 7），对应抽奖页面：http://www.17dong.com.cn/special_topic/lotterydraw
        '''
        trypromotiondraw = int(self.get_argument('trypromotiondraw', 0))

        db = DbHelper()
        rewardids       = [1, 5, 6, 2, 7, 4, 3, 8]
        frontendindexes = [0, 1, 2, 7, 3, 6, 5, 4]
        rewards = []
        for i in range(len(rewardids)):
            rewards.append((frontendindexes[i], db.GetPromotionReward(promotion_reward_id=rewardids[i])))

        userid = self.get_argument("uid", None)
        if userid:
            choice = db.PromotionDraw(promotion_id=promotion_id, user_id=userid, trypromotiondraw=trypromotiondraw)

            # logging.debug("PromotionDraw: %r" % json.dumps(choice, cls=EnhancedJSONEncoder))

            if int(choice["result"]) == 1:
                choiceindex = None
                for i in range(len(rewards)):
                    rewardinfo = rewards[i][1]
                    if rewardinfo is not None and int(rewardinfo['promotion_reward_id']) == int(choice['promotion_reward_id']):
                        choiceindex = rewards[i][0]
                        break

                if choiceindex is not None:
                    resultlist = { "result" : "1", "choiceindex" : choiceindex }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
                else:
                    resultlist = { "result" : "-9", "message" : "PromotionDraw failed." }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
            else:
                resultlist = { "result" : choice["result"], "message" : choice["message"] }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            resultlist = { "result" : "-9", "message" : "User not logged in." }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class SpecialTopicLotterydrawQuerystate(BaseHandler):
    def post(self, promotion_id):
        '''查询用户的中奖信息，对应抽奖页面：http://www.17dong.com.cn/special_topic/lotterydraw
        '''
        db = DbHelper()
        userid = self.get_argument("uid", None)
        if userid:
            userdrawrecords = db.GetUserPromotionRewardDrawRecords(promotion_id, userid, excludenothing=1)
            rewardnames = []
            for recordinfo in userdrawrecords:
                rewardinfo = db.GetPromotionReward(recordinfo['promotion_reward_id'])
                rewardnames.append(rewardinfo['promotion_reward_name'])

            resultlist = { "result" : "1", "rewardnames" : rewardnames }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            resultlist = { "result" : "-9", "message" : "User not logged in." }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class SpecialTopicLotterydrawV2(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/lotterydraw_v2/index.html")

    def post(self):
        current_userid = self.current_user
        if current_userid is None:
            resultlist = { "result" : -1 }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)
        else:
            # 活动名称          活动ID   金额   限制条件    有效期
            # ----------------------------------------------------------------------
            # 霸道红包网球券     4        100   1, 网球     2015-12-31
            # 霸道红包击剑券     5        100   1, 击剑     2015-12-31
            # 霸道红包游泳券     6        50    1, 游泳     2015-12-31
            # 霸道红包篮球券     7        50    1, 篮球     2015-12-31
            # 霸道红包足球券     8        50    1, 足球     2015-12-31
            # 霸道红包舞蹈券     9        50    1, 舞蹈     2015-12-31
            # 霸道红包轮滑券     10       50    1, 轮滑     2015-12-31
            # 霸道红包跆拳道券   11       50    1, 跆拳道   2015-12-31

            db = DbHelper()
            try:
                activityid = int(GetArgumentValue(self, "t"))
            except Exception, e:
                activityid = 0
            userhasgetcoupon = db.IsUserGetSpecificCoupon(userid=current_userid, productid=None, activityid=activityid)
            if userhasgetcoupon:
                resultlist = { "result" : 0 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
            else:
                if activityid == 4:
                    item = list()
                    tp = "网球"
                    item.append(tp)
                    couponvalue = 100
                elif activityid == 5:
                    item = list()
                    tp = "击剑"
                    item.append(tp)
                    couponvalue = 100
                elif activityid == 6:
                    item = list()
                    tp = "游泳"
                    item.append(tp)
                    couponvalue = 50
                elif activityid == 7:
                    item = list()
                    tp = "篮球"
                    item.append(tp)
                    couponvalue = 50
                elif activityid == 8:
                    item = list()
                    tp = "足球"
                    item.append(tp)
                    couponvalue = 50
                elif activityid == 9:
                    item = list()
                    tp = "舞蹈"
                    item.append(tp)
                    couponvalue = 50
                elif activityid == 10:
                    item = list()
                    tp = "轮滑"
                    item.append(tp)
                    couponvalue = 50
                elif activityid == 11:
                    item = list()
                    tp = "跆拳道"
                    item.append(tp)
                    couponvalue = 50
                else:
                    resultlist = { "result" : 0 }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)

                restriction = json.dumps({ "RestrictionType" : 2, "ProductType": 1, "ProductItem" : item })
                couponsource = int("2%s" % activityid)
                validdays = datetime.date(2015, 12, 31) - datetime.date.today()
                validdays = validdays.days
                db.AddCoupon(couponinfo={ "coupon_userid" : current_userid, "coupon_amount" : couponvalue, "coupon_restrictions" : restriction, "coupon_source" : couponsource }, couponvaliddays=validdays)
                
                resultlist = { "result" : 1 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

class SpecialTopicLotterydrawDrawV2(BaseHandler):
    def post(self, promotion_id):
        '''返回抽奖结果 （ 0 - 7），对应抽奖页面：http://www.17dong.com.cn/special_topic/lotterydraw/v2
        '''
        trypromotiondraw = int(self.get_argument('trypromotiondraw', 0))

        db = DbHelper()
        rewardids       = [14, 11, 17, 16, 13, 12, 10, 15]
        frontendindexes = [0,   1,  2,  7,  3,  6,  5,  4]
        rewards = []
        for i in range(len(rewardids)):
            rewards.append((frontendindexes[i], db.GetPromotionReward(promotion_reward_id=rewardids[i])))

        userid = self.get_argument("uid", None)
        if userid:
            choice = db.PromotionDraw(promotion_id=promotion_id, user_id=userid, trypromotiondraw=trypromotiondraw)

            # logging.debug("PromotionDraw: %r" % json.dumps(choice, cls=EnhancedJSONEncoder))

            if int(choice["result"]) == 1:
                choiceindex = None
                for i in range(len(rewards)):
                    rewardinfo = rewards[i][1]
                    if rewardinfo is not None and int(rewardinfo['promotion_reward_id']) == int(choice['promotion_reward_id']):
                        choiceindex = rewards[i][0]
                        break

                if choiceindex is not None:
                    resultlist = { "result" : "1", "choiceindex" : choiceindex }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
                else:
                    resultlist = { "result" : "-9", "message" : "PromotionDraw failed." }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
            else:
                resultlist = { "result" : choice["result"], "message" : choice["message"] }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            resultlist = { "result" : "-9", "message" : "User not logged in." }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class SpecialTopicBaymax(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/baymax/index.html")

class SpecialTopicQmengqinzileyuan(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/qmengqinzileyuan/index.html")

class SpecialTopicQmengqinzileyuanV2(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/qmengqinzileyuan_v2/index.html")

class SpecialTopicPhotograph(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/photograph/index.html")

class SpecialBreakfast(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/breakfast/index.html")

class SpecialBreakfastDraw(BaseHandler):
    def post(self, promotion_id):
        '''返回抽奖结果 （1 - 4），对应抽奖页面：http://www.17dong.com.cn/special_topic/breakfast
        '''
        trypromotiondraw = int(self.get_argument('trypromotiondraw', 0))

        db = DbHelper()
        rewardids       = [18, 19, 21, 20]
        frontendindexes = [1,   2,  3,  4]
        rewards = []
        for i in range(len(rewardids)):
            rewards.append((frontendindexes[i], db.GetPromotionReward(promotion_reward_id=rewardids[i])))

        userid = self.get_argument("uid", None)
        if userid:
            choice = db.PromotionDraw(promotion_id=promotion_id, user_id=userid, trypromotiondraw=trypromotiondraw)

            # logging.debug("PromotionDraw: %r" % json.dumps(choice, cls=EnhancedJSONEncoder))

            if int(choice["result"]) == 1:
                choiceindex = None
                for i in range(len(rewards)):
                    rewardinfo = rewards[i][1]
                    if rewardinfo is not None and int(rewardinfo['promotion_reward_id']) == int(choice['promotion_reward_id']):
                        choiceindex = rewards[i][0]
                        break

                if choiceindex is not None:
                    resultlist = { "result" : "1", "choiceindex" : choiceindex }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
                else:
                    resultlist = { "result" : "-9", "message" : "PromotionDraw failed." }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
            else:
                resultlist = { "result" : choice["result"], "message" : choice["message"] }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            resultlist = { "result" : "-9", "message" : "User not logged in." }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class SpecialBreakfastQuerystate(BaseHandler):
    def post(self, promotion_id):
        '''查询用户的中奖信息，对应抽奖页面：http://www.17dong.com.cn/special_topic/breakfast
        '''
        db = DbHelper()
        userid = self.get_argument("uid", None)
        if userid:
            userdrawrecords = db.GetUserPromotionRewardDrawRecords(promotion_id, userid, excludenothing=1)
            rewardnames = []
            for recordinfo in userdrawrecords:
                rewardinfo = db.GetPromotionReward(recordinfo['promotion_reward_id'])
                rewardnames.append(rewardinfo['promotion_reward_name'])

            if len(rewardnames) > 0:
                resultlist = { "result" : "1", "rewardnames" : rewardnames }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            resultlist = { "result" : "-9", "message" : "User not logged in." }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class SpecialBreakfastMob(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/breakfastmob/index.html")

class SpecialTopicKaixue(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/kaixue/index.html")

class SpecialTopicFreeSports(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/freesports/index.html")

class SpecialTopicTeacherday(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/teacherday/index.html")

    def post(self):
        '''
             0 - 投票失败
             1 - 投票成功
             2 - 您已经投票过了，无法再次投票
             3 - 您今天已经投票过了，请明天再来投票
             4 - 投票已结束，无法进行投票
        '''
        uid = self.get_argument("uid")
        optid = self.get_argument("optid")
        current_userid = self.current_user

        if str(uid) == str(current_userid):
            db = DbHelper()
            ret = db.VoteForOption(userid=int(current_userid), voteoptionid=optid)
        else:
            ret = 0
        
        resultlist = { "ret" : ret }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        return self.write(jsonstr)

class SpecialTopicTeacherdayMob(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/teacherdaymob/index.html")

    def post(self):
        '''返回抽奖结果 （ 0 - 7），对应抽奖页面：http://www.17dong.com.cn/special_topic/lotterydraw
        '''
        promotion_id = 4
        trypromotiondraw = int(self.get_argument('trypromotiondraw', 0))

        db = DbHelper()
        rewardids       = [22, 23, 24, 25, 26]
        frontendindexes = [ 0,  1,  2,  3,  4]
        rewards = []
        for i in range(len(rewardids)):
            rewards.append((frontendindexes[i], db.GetPromotionReward(promotion_reward_id=rewardids[i])))

        userid = self.get_argument("uid", None)
        if userid:
            choice = db.PromotionDraw(promotion_id=promotion_id, user_id=userid, trypromotiondraw=trypromotiondraw)

            # logging.debug("PromotionDraw: %r" % json.dumps(choice, cls=EnhancedJSONEncoder))

            if int(choice["result"]) == 1:
                choiceindex = None
                for i in range(len(rewards)):
                    rewardinfo = rewards[i][1]
                    if rewardinfo is not None and int(rewardinfo['promotion_reward_id']) == int(choice['promotion_reward_id']):
                        choiceindex = rewards[i][0]
                        break

                if choiceindex is not None:
                    resultlist = { "result" : "1", "choiceindex" : choiceindex }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
                else:
                    resultlist = { "result" : "-9", "message" : "PromotionDraw failed." }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
            else:
                resultlist = { "result" : choice["result"], "message" : choice["message"] }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            resultlist = { "result" : "-9", "message" : "User not logged in." }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class SpecialTopicExam(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/exam/index.html")

class SpecialTopicRexueFootball(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/rexuefootball/index.html")

class SpecialTopicNationalDay2015(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/nationalday2015/index.html")

    def post(self):
        current_userid = self.current_user
        if current_userid is None:
            resultlist = { "result" : -1 }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)
        else:
            # 活动名称          活动ID   金额   限制条件    有效期
            # ----------------------------------------------------------------------
            # 国庆节30元优惠券   12       30    1, 游泳   2015-10-31
            # 国庆节60元优惠券   13       60    1, 足球   2015-10-31
            # 国庆节10元优惠券   14       10    4, 周末去哪   2015-10-31

            db = DbHelper()
            try:
                activityid = int(GetArgumentValue(self, "t"))
            except Exception, e:
                activityid = 0
            userhasgetcoupon = db.IsUserGetSpecificCoupon(userid=current_userid, productid=None, activityid=activityid)
            if userhasgetcoupon:
                resultlist = { "result" : 0 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
            else:
                if activityid == 12:
                    item = list()
                    tp = "游泳"
                    item.append(tp)
                    couponvalue = 30
                    restriction = json.dumps({ "RestrictionType" : 2, "ProductType": 1, "ProductItem" : item })
                elif activityid == 13:
                    item = list()
                    tp = "足球"
                    item.append(tp)
                    couponvalue = 60
                    restriction = json.dumps({ "RestrictionType" : 2, "ProductType": 1, "ProductItem" : item })
                elif activityid == 14:
                    couponvalue = 10
                    restriction = json.dumps({ "RestrictionType" : 1, "ProductType": 4 })
                else:
                    resultlist = { "result" : 0 }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)

                couponsource = int("2%s" % activityid)
                validdays = datetime.date(2015, 10, 31) - datetime.date.today()
                validdays = validdays.days
                db.AddCoupon(couponinfo={ "coupon_userid" : current_userid, 
                    "coupon_amount" : couponvalue, 
                    "coupon_restrictions" : restriction, 
                    "coupon_source" : couponsource }, 
                    couponvaliddays=validdays)
                
                resultlist = { "result" : 1 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

class SpecialTopicLandingPageBaseketballV2(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/landingpage/basketball/v2/index.html")

class SpecialTopicLandingPageBadminton(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/landingpage/badminton/index.html")

class SpecialTopicGifts(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/gifts/index.mobile.html", promotion_id=5)

class SpecialTopicGiftsDraw(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        '''返回抽奖结果 （ 0 - 6），对应抽奖页面：http://www.17dong.com.cn/special_topic/gifts
            1.11种体育项目12课时随意组合！500元礼包1折抢 
            2.100元斯马特卡
            3.价值1999元的齿科体检
            4.5元好剧优惠券
            5.1米大熊免费送
            6.100元电话卡
            7. 酸奶机
        '''
        trypromotiondraw = int(self.get_argument('trypromotiondraw', 0))

        db = DbHelper()
        rewardids       = [28, 29, 30, 34, 31, 33, 32]
        frontendindexes = [0, 1, 2, 3, 4, 5, 6]
        rewards = []
        for i in range(len(rewardids)):
            rewards.append((frontendindexes[i], db.GetPromotionReward(promotion_reward_id=rewardids[i])))
        userid = self.get_argument("uid", None) or self.get_current_user()
        if userid:
            choice = db.PromotionDraw(promotion_id=5, user_id=userid, trypromotiondraw=trypromotiondraw)

            # logging.debug("PromotionDraw: %r" % json.dumps(choice, cls=EnhancedJSONEncoder))

            if int(choice["result"]) == 1:
                choiceindex = None
                for i in range(len(rewards)):
                    rewardinfo = rewards[i][1]
                    if rewardinfo is not None and int(rewardinfo['promotion_reward_id']) == int(choice['promotion_reward_id']):
                        choiceindex = rewards[i][0]
                        break

                if choiceindex is not None:
                    resultlist = { "result" : "1", "choiceindex" : choiceindex }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
                else:
                    resultlist = { "result" : "-9", "message" : "PromotionDraw failed." }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
            else:
                resultlist = { "result" : choice["result"], "message" : choice["message"] }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            resultlist = { "result" : "-9", "message" : "User not logged in." }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class SpecialTopicGiftsQuerystate(BaseHandler):
    def post(self, promotion_id):
        '''查询用户的中奖信息，对应抽奖页面：http://www.17dong.com.cn/special_topic/gifts
        '''
        db = DbHelper()
        userid = self.get_argument("uid", None) or self.get_current_user()
        if userid:
            userdrawrecords = db.GetUserPromotionRewardDrawRecords(promotion_id, userid, excludenothing=1)
            rewardnames = []
            for recordinfo in userdrawrecords:
                rewardinfo = db.GetPromotionReward(recordinfo['promotion_reward_id'])
                rewardnames.append(rewardinfo['promotion_reward_name'])

            if len(rewardnames) > 0:
                resultlist = { "result" : "1", "rewardnames" : rewardnames }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            resultlist = { "result" : "-9", "message" : "User not logged in." }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class SpecialTopicVoteRevenge(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/vote/revenge/index.html")

class SpecialTopicVoteRevengeList(BaseHandler):
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        db = DbHelper()
        onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
        serveraddress = self.request.headers.get("Host")
        thevoteid = 6 if not onserver else 11
        allvoteoption = db.QueryVoteOptions(voteid=thevoteid, startpos=(pageindex - 1) * 8, count=8, status=1)
        allvoteoptioncount = len(db.QueryVoteOptions(voteid=thevoteid, startpos=0, count=0, status=1))
        return self.renderJinjaTemplate("special_topic/vote/revenge/votelist.html", pageindex=pageindex, allvoteoption=allvoteoption, allvoteoptioncount=allvoteoptioncount, serveraddress=serveraddress)

    def post(self):
        '''
             0 - 投票失败
             1 - 投票成功
             2 - 您已经投票过了，无法再次投票
             3 - 您今天已经投票过了，请明天再来投票
             4 - 投票已结束，无法进行投票
        '''
        uid = self.get_argument("uid")
        optid = self.get_argument("optid")
        current_userid = self.current_user

        if str(uid) == str(current_userid):
            db = DbHelper()
            ret = db.VoteForOption(userid=int(current_userid), voteoptionid=optid)
        else:
            ret = 0
        
        resultlist = { "ret" : ret }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        return self.write(jsonstr)

class SpecialTopicVoteTraining(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("special_topic/vote/training/index.html")

    def post(self):
        '''
             0 - 投票失败
             1 - 投票成功
             2 - 您已经投票过了，无法再次投票
             3 - 您今天已经投票过了，请明天再来投票
             4 - 投票已结束，无法进行投票
        '''
        uid = self.get_argument("uid")
        optid = self.get_argument("optid")
        current_userid = self.current_user

        if str(uid) == str(current_userid):
            db = DbHelper()
            ret = db.VoteForOption(userid=int(current_userid), voteoptionid=optid)
        else:
            ret = 0
        
        resultlist = { "ret" : ret }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        return self.write(jsonstr)

class SpecialTopicValentineGetCoupon(BaseHandler):
    # @tornado.web.authenticated
    def post(self):
        current_userid = self.current_user
        if current_userid is None:
            resultlist = { "result" : -1 }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)
        else:
            db = DbHelper()
            userhasgetcoupon = db.IsUserGetSpecificCoupon(userid=current_userid, productid=None, activityid=1)  # 情人节领取优惠券的活动ID为1
            if userhasgetcoupon:
                # return self.write("对不起，你已领取过此次活动的优惠券，无法再次领取！")
                resultlist = { "result" : 0 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
            else:
                restriction = json.dumps({ "RestrictionType" : 4, "ProductID" : (194, 195, 196, 197, 198, 199, 259, 260, 261, 262) })
                activityid = 1
                couponsource = int("2%s" % activityid)
                validdays = datetime.date(2015, 3, 15) - datetime.date.today()
                validdays = validdays.days
                db.AddCoupon(couponinfo={ "coupon_userid" : current_userid, "coupon_amount" : 200, "coupon_restrictions" : restriction, "coupon_source" : couponsource }, couponvaliddays=validdays)
                
                resultlist = { "result" : 1 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

class SpecialTopicSummerCampGetCoupon(BaseHandler):
    def post(self):
        current_userid = self.current_user
        if current_userid is None:
            resultlist = { "result" : -1 }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)
        else:
            # 夏令营领取国外营优惠券活动ID为 2
            # 夏令营领取国内营优惠券活动ID为 3
            coupontype = GetArgumentValue(self, "t")
            activityid = int(coupontype) + 1

            db = DbHelper()
            userhasgetcoupon = db.IsUserGetSpecificCoupon(userid=current_userid, productid=None, activityid=activityid)
            if userhasgetcoupon:
                resultlist = { "result" : 0 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
            else:
                if activityid == 2:
                    item = list()
                    tp = "国外营"
                    item.append(tp)
                    couponvalue = 500
                else:
                    item = list()
                    tp = "国内营"
                    item.append(tp)
                    couponvalue = 200

                restriction = json.dumps({ "RestrictionType" : 2, "ProductType": 7, "ProductItem" : item })
                couponsource = int("2%s" % activityid)
                validdays = datetime.date(2015, 8, 31) - datetime.date.today()
                validdays = validdays.days
                db.AddCoupon(couponinfo={ "coupon_userid" : current_userid, "coupon_amount" : couponvalue, "coupon_restrictions" : restriction, "coupon_source" : couponsource }, couponvaliddays=validdays)
                
                resultlist = { "result" : 1 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

############################################################################################################################################################################################
############################################################################################################################################################################################

class CampusFootball(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("campusfootball/index.html")

class CampusFootballNews(BaseHandler):
    def get(self):
        webpath  = self.request.path
        elements = webpath.split("/")
        if len(elements) >= 4:
            try:
                articles_id = int(elements[3])
            except Exception, e:
                articles_id = None
        else:
            articles_id = None

        if articles_id:
            return self.renderJinjaTemplate("campusfootball/news_detail.html", articles_id=articles_id)
        else:
            return self.send_error(404)

class SpecialTopicSummerCampV2GetCoupon(BaseHandler):
    def post(self):
        current_userid = self.current_user
        if current_userid is None:
            resultlist = { "result" : -1 }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)
        else:
            # 夏令营领取国外营优惠券活动ID为 2 (夏令营V2 和活动ID也为2)
            coupontype = GetArgumentValue(self, "t")
            activityid = int(coupontype) + 1

            db = DbHelper()
            userhasgetcoupon = db.IsUserGetSpecificCoupon(userid=current_userid, productid=None, activityid=activityid)
            if userhasgetcoupon:
                resultlist = { "result" : 0 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
            else:
                if activityid == 2:
                    item = list()
                    tp = "国外营"
                    item.append(tp)
                    couponvalue = 500
                    
                restriction = json.dumps({ "RestrictionType" : 2, "ProductType": 7, "ProductItem" : item })
                couponsource = int("2%s" % activityid)
                validdays = datetime.date(2015, 8, 31) - datetime.date.today()
                validdays = validdays.days
                db.AddCoupon(couponinfo={ "coupon_userid" : current_userid, "coupon_amount" : couponvalue, "coupon_restrictions" : restriction, "coupon_source" : couponsource }, couponvaliddays=validdays)
                
                resultlist = { "result" : 1 }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

############################################################################################################################################################################################
############################################################################################################################################################################################

class CKEditImageUpload(BaseHandler):
    def post(self):
        if not self.request.files.has_key('upload'):
            return

        uploadedfile = self.request.files['upload'][0]
        original_fname = uploadedfile['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = getuniquestring()
        filename = fname + extension

        filedir             = "/static/img/upload"
        infile              = filedir + '/' + filename # infile就是用户上传的原始照片
        infile_preview      = filedir + '/P%s.jpeg' % fname
        localfile           = (socket.gethostname() == Settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp') + infile
        localfile_preview   = (socket.gethostname() == Settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp') + infile_preview

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

        formatted_im = ImageOps.fit(im, avatar_size, Image.ANTIALIAS, centering = (0.5,0.5))
        formatted_im.save(localfile_preview, "JPEG")
        os.remove(localfile)

        # 向 CKEditor 编辑器返回图片链接
        url = infile_preview
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

class AccountOrderDelete(BaseHandler):

    def post(self):
        current_userid = self.current_user
        user_id = GetArgumentValue(self, "uid")
        preorder_id = GetArgumentValue(self, "oid")

        # 权限检测
        if user_id is None or current_userid is None:
            return self.send_error(300)
        else:
            if str(current_userid) != str(user_id):
                return self.send_error(300)
            else:
                db = DbHelper()
                db.DeletePreorder(preorder_id)
                return self.write("success")

class AccountInfoDelete(BaseHandler):

    def post(self):
        current_userid = self.current_user
        user_id = GetArgumentValue(self, "uid")
        message_id = GetArgumentValue(self, "mid")

        # 权限检测
        if user_id is None or current_userid is None:
            return self.send_error(300)
        else:
            if str(current_userid) != str(user_id):
                return self.send_error(300)
            else:
                db = DbHelper()
                db.DeleteMessage(message_id)
                return self.write("success")

def UpdateOrderStatusWhenPaymentSuccess(handler, orderinfo):
    if orderinfo is None:
        return

    if type(orderinfo) == dict:
        db = DbHelper(cursorclass=Settings.DB_DICTCURSOR)
    elif type(orderinfo) == tuple or type(orderinfo) == list:
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)
    else:
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)

    preorder_id = orderinfo[0] if not db.IsDbUseDictCursor() else orderinfo["preorder_id"]
    preorder_userid = orderinfo[1] if not db.IsDbUseDictCursor() else orderinfo["preorder_userid"]
    preorder_productid = orderinfo[2] if not db.IsDbUseDictCursor() else orderinfo["preorder_productid"]
    preorder_paytime = orderinfo[5] if not db.IsDbUseDictCursor() else orderinfo["preorder_paytime"]
    preorder_counts = orderinfo[8] if not db.IsDbUseDictCursor() else orderinfo["preorder_counts"]
    preorder_fullprice = orderinfo[10] if not db.IsDbUseDictCursor() else orderinfo["preorder_fullprice"]
    preorder_sceneid = orderinfo[11] if not db.IsDbUseDictCursor() else orderinfo["preorder_sceneid"]
    preorder_usedpoints = orderinfo[17] if not db.IsDbUseDictCursor() else orderinfo["preorder_usedpoints"]
    preorder_contactsphonenumber = orderinfo[24] if not db.IsDbUseDictCursor() else orderinfo["preorder_contactsphonenumber"]
    preorder_travellerids = orderinfo[25] if not db.IsDbUseDictCursor() else orderinfo["preorder_travellerids"]
    preorder_remarks = orderinfo[30] if not db.IsDbUseDictCursor() else orderinfo["preorder_remarks"]
    preorder_tradeno = orderinfo[37] if not db.IsDbUseDictCursor() else (orderinfo['preorder_tradeno'] if orderinfo.has_key('preorder_tradeno') else None)

    productinfo = db.QueryProductInfo(preorder_productid)
    
    # 更新订单状态
    db.UpdatePreorderInfo(preorder_id, { "preorder_paymentstatus" : 1, "preorder_paytime" : strftime("%Y-%m-%d %H:%M:%S"), "preorder_tradeno" : preorder_tradeno })

    # 如果使用了优惠券，更新优惠券状态
    if preorder_remarks is not None:
        couponinfo = db.QueryCouponInfoByCNO(preorder_remarks)
        if couponinfo is not None:
            if not db.IsDbUseDictCursor():
                db.UpdateCouponInfo(couponinfo[0], { "coupon_valid" : 0, "coupon_source" : couponinfo[10] })
            else:
                db.UpdateCouponInfo(couponinfo["coupon_id"], { "coupon_valid" : 0, "coupon_source" : couponinfo["coupon_source"] })

    # 如果使用了抵扣券，更新抵扣券状态
    if preorder_travellerids is not None:
        couponinfo = db.QueryCouponInfoByCNO(preorder_travellerids)
        if couponinfo is not None:
            if not db.IsDbUseDictCursor():
                db.UpdateCouponInfo(couponinfo[0], { "coupon_valid" : 0, "coupon_source" : couponinfo[10] })
            else:
                db.UpdateCouponInfo(couponinfo["coupon_id"], { "coupon_valid" : 0, "coupon_source" : couponinfo["coupon_source"] })

    # 如果使用了积分，更新用户积分数
    order_userid = preorder_userid
    order_userinfo = db.QueryUserInfoById(order_userid)
    userpoints = order_userinfo[12] if not db.IsDbUseDictCursor() else order_userinfo["user_points"]
    if preorder_usedpoints is not None and float(preorder_usedpoints) > 0:
        if userpoints is not None and float(userpoints) > 0:
            user_points = float(userpoints) - float(preorder_usedpoints)
            if user_points < 0:
                user_points = 0
            db.UpdateUserInfoById(order_userid, { "user_points" : user_points })

    # 如果此订单有赠送积分，更新用户积分数
    scene_points = 0
    order_productsceneid = preorder_sceneid
    order_productsceneinfo = db.QuerySceneInfo(order_productsceneid)
    scenepoints = order_productsceneinfo[11] if not db.IsDbUseDictCursor() else order_productsceneinfo["scene_points"]
    if order_productsceneinfo is not None:
        scene_points = int(scenepoints) if scenepoints is not None else 0
        if scene_points > 0:
            order_userinfo = db.QueryUserInfoById(order_userid)
            order_userpoints  = int(userpoints) if userpoints is not None else 0
            order_userpoints += int(scene_points) * int(preorder_counts)
            db.UpdateUserInfoById(order_userid, { "user_points" : order_userpoints })
            db.UpdatePreorderInfo(preorder_id, { "preorder_rewardpoints" : scene_points })

    #########################################################################################################
    # 推送相关通知信息
    fullprice = float(preorder_fullprice)
    if fullprice > 0:
        product_name = productinfo[2] if not db.IsDbUseDictCursor() else productinfo["product_name"]
        message_title = '''购买"%s"产品成功''' % product_name
        if scene_points > 0:
            # 有积分赠送
            message_content = '''感谢您购买一起动的"%s"产品，您已经获得 %s 积分，请尽快跟我们的客服确认订单后续事宜。[客服电话400-601-9917]''' % (product_name, scene_points)
        else:
            # 无积分赠送
            message_content = '''感谢您购买一起动的"%s"产品，如有任何疑问请咨询客服。[客服电话：400-601-9917]''' % product_name

        # 向用户发送站内信
        db.AddMessage(messageinfo={ "message_type" : 2, "message_state" : 1, "message_title" : message_title, "message_publisher" : "系统", 
            "message_externalurl" : "", "message_externalproductid" : 0, "message_sendtime" : strftime("%Y-%m-%d"), 
            "message_receiver" : json.dumps([orderinfo[1] if not db.IsDbUseDictCursor() else orderinfo["preorder_userid"]]), "message_content" : message_content })

        # 向用户发送手机短信
        url = Settings.EMPP_URL
        userinfo = db.QueryUserInfoById(preorder_userid)
        UserPhonenumber = userinfo[3] if not db.IsDbUseDictCursor() else userinfo["user_phonenumber"]
        if not db.IsDbUseDictCursor():
            phonenumber = UserPhonenumber
        else:
            phonenumber = userinfo["user_phonenumber"] if userinfo["user_phonenumber"] is not None else preorder_contactsphonenumber
        if re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
            postparam = Settings.EMPP_POST_PARAM
            postparam["mobile"]  = phonenumber
            postparam["content"] = message_content
            requests.post(url, postparam)
    #########################################################################################################
    
    # # 如果此订单有赠送优惠券，对用户发放优惠券
    # order_productid = orderinfo[2]
    # order_productinfo = db.QueryProductInfo(order_productid)
    # if order_productinfo is not None:
    #     product_coupons = float(order_productinfo[33]) if order_productinfo[33] is not None else 0
    #     if product_coupons > 0:
    #         db.AddCoupon({ "coupon_userid" : order_userid, "coupon_amount" : product_coupons, "coupon_source" : 9 })

    # 更新商品库存
    preorder_counts = 0 if preorder_counts is None else preorder_counts
    sceneinfo = db.QuerySceneInfo(preorder_sceneid)
    if sceneinfo is not None:
        scene_maxpeople = sceneinfo[4] if not db.IsDbUseDictCursor() else sceneinfo["scene_maxpeople"]
        scene_maxpeople = int(scene_maxpeople) - int(preorder_counts)
        scene_maxpeople = 0 if scene_maxpeople < 0 else scene_maxpeople
        db.UpdateSceneInfo(preorder_sceneid, sceneinfo={ "scene_maxpeople" : scene_maxpeople })

def CalculateProductPrice(BaseHandler, productid, sceneid, counts, counts_child, needinvoice, usepointcount, usecouponno, c2discountno):
    db = DbHelper()
    productinfo = db.QueryProductInfo(productid)
    sceneinfo = db.QuerySceneInfo(sceneid)
    product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

    if product_type == 3:
        productprice = productinfo[9] if not db.IsDbUseDictCursor() else productinfo["product_price"]
        if productprice is not None and int(productprice) == 0:
            product3needpayment = False
        else:
            product3needpayment = True
    else:
        product3needpayment = False

    # --------------
    final_price = 0.0

    # 根据购买数量计算价格
    if counts:
        if sceneinfo is not None:
            if product_type == 1 or product_type == 2 or product_type == 4 or product_type == 6 or product_type == 7:
                price = sceneinfo[5] if not db.IsDbUseDictCursor() else sceneinfo["scene_fullprice"]
            else:
                price = 0
        else:
            if product3needpayment == True or product_type == 5:
                price = productinfo[9] if not db.IsDbUseDictCursor() else productinfo["product_price"]
            else:
                price = 0
        final_price = float(price) * int(counts)

    if counts_child and product_type == 2:
        if sceneinfo is not None:
            price_child = sceneinfo[6] if not db.IsDbUseDictCursor() else sceneinfo["scene_childprice"]
            final_price += float(price_child) * int(counts_child)

    # 是否需要发票
    if needinvoice is not None:
        if int(needinvoice) == 1:
            final_price += 10.0

    # 是否使用积分
    if usepointcount is not None and int(usepointcount) > 0:
        final_price -= (int(usepointcount) / 100.0)

    # 是否使用优惠券
    if usecouponno is not None:
        if str(usecouponno) == "0":
            pass
        else:
            couponinfo = db.QueryCouponInfoByCNO(usecouponno)
            if couponinfo is not None:
                coupon_discount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]
                coupon_amount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]
                final_price -= float(coupon_amount)

    # 是否使用抵扣券
    if c2discountno is not None:
        if str(c2discountno) == "0":
            pass
        else:
            couponinfo = db.QueryCouponInfoByCNO(c2discountno)
            if couponinfo is not None:
                c2discount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]
                final_price -= float(c2discount)

    final_price = 0 if final_price < 0 else final_price
    return final_price
    # --------------

############################################################################################################################################################################################
############################################################################################################################################################################################

class LLPayment(BaseHandler):
    def initialize(self):
        serveraddress = self.request.headers.get("Host")
        self.url_root = "http://%s" % serveraddress

    def get(self):
        return self.renderJinjaTemplate("frontend/lianlianpayment.html")

    def post(self):
        user_id = GetArgumentValue(self, "user_id")
        busi_partner = GetArgumentValue(self, "busi_partner")
        no_order = GetArgumentValue(self, "no_order")
        money_order = GetArgumentValue(self, "money_order")
        name_goods = GetArgumentValue(self, "name_goods")
        url_order = GetArgumentValue(self, "url_order")
        info_order = GetArgumentValue(self, "info_order")
        bank_code = GetArgumentValue(self, "bank_code")
        pay_type = GetArgumentValue(self, "pay_type")
        card_no = GetArgumentValue(self, "card_no")
        acct_name = GetArgumentValue(self, "acct_name")
        id_no = GetArgumentValue(self, "id_no")
        no_agree = GetArgumentValue(self, "no_agree")
        flag_modify = GetArgumentValue(self, "flag_modify")
        risk_item = GetArgumentValue(self, "risk_item")
        shareing_data = GetArgumentValue(self, "shareing_data")
        back_url = GetArgumentValue(self, "back_url")
        valid_order = GetArgumentValue(self, "valid_order")
        notify_url = "%s/payment/llpay/notify" % self.url_root
        return_url = "%s/payment/llpay/return" % self.url_root

        parameter = {
            "version" : Settings.LIANLIANPAY["version"],
            "oid_partner" : Settings.LIANLIANPAY["oid_partner"],
            "sign_type" : Settings.LIANLIANPAY["sign_type"],
            "id_type" : Settings.LIANLIANPAY["id_type"],
            "valid_order" : Settings.LIANLIANPAY["valid_order"],
            "timestamp" : strftime("%Y%m%d%H%M%S"),
            "dt_order" :  strftime("%Y%m%d%H%M%S"),
        }
        if user_id is not None:
            parameter["user_id"] = user_id
        if busi_partner is not None:
            parameter["busi_partner"] = busi_partner
        if no_order is not None:
            parameter["no_order"] = no_order
        if name_goods is not None:
            parameter["name_goods"] = name_goods
        if info_order is not None:
            parameter["info_order"] = info_order
        if money_order is not None:
            parameter["money_order"] = money_order
        if notify_url is not None:
            parameter["notify_url"] = notify_url
        if return_url is not None:
            parameter["url_return"] = return_url
        if url_order is not None:
            parameter["url_order"] = url_order
        if bank_code is not None:
            parameter["bank_code"] = bank_code
        if pay_type is not None:
            parameter["pay_type"] = pay_type
        if no_agree is not None:
            parameter["no_agree"] = no_agree
        if shareing_data is not None:
            parameter["shareing_data"] = shareing_data
        if risk_item is not None:
            parameter["risk_item"] = risk_item
        if id_no is not None:
            parameter["id_no"] = id_no
        if acct_name is not None:
            parameter["acct_name"] = acct_name
        if flag_modify is not None:
            parameter["flag_modify"] = flag_modify
        if card_no is not None:
            parameter["card_no"] = card_no
        if back_url is not None:
            parameter["back_url"] = back_url

        sHtml = LLPay.create_payment(parameter)

        return self.write(sHtml)

class LLPaymentReturn(BaseHandler):
    def post(self):
        if self.verifyReturn() == True:
            # oid_partner = GetArgumentValue(self, "oid_partner")
            no_order = GetArgumentValue(self, "no_order")
            # oid_paybill = GetArgumentValue(self, "oid_paybill")
            # money_order = GetArgumentValue(self, "money_order")
            result_pay = GetArgumentValue(self, "result_pay")
            out_trade_no = no_order

            db = DbHelper()
            orderinfo = db.QueryPreorderInfoByOutTradeNo(out_trade_no)
            if result_pay == 'SUCCESS':
                paymentstatus = int(orderinfo[12]) if orderinfo is not None else 0
                if paymentstatus == 0:
                    UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)
                
                product_id = orderinfo[2]
                productinfo = db.QueryProductInfo(product_id)
                product_type = productinfo[4]
                return self.redirect('/payment/success?type=%s' % product_type)
            else:
                return self.redirect('/payment/error')
        else:
            return self.send_error(500)

    def verifyReturn(self):
        oid_partner = GetArgumentValue(self, "oid_partner")
        sign_type = GetArgumentValue(self, "sign_type")
        dt_order = GetArgumentValue(self, "dt_order")
        no_order = GetArgumentValue(self, "no_order")
        oid_paybill = GetArgumentValue(self, "oid_paybill")
        money_order = GetArgumentValue(self, "money_order")
        result_pay = GetArgumentValue(self, "result_pay")
        settle_date = GetArgumentValue(self, "settle_date")
        info_order = GetArgumentValue(self, "info_order")
        pay_type = GetArgumentValue(self, "pay_type")
        bank_code = GetArgumentValue(self, "bank_code")

        adict = {}

        if oid_partner is not None:
            adict["oid_partner"] = oid_partner
        if sign_type is not None:
            adict["sign_type"] = sign_type
        if dt_order is not None:
            adict["dt_order"] = dt_order
        if no_order is not None:
            adict["no_order"] = no_order
        if oid_paybill is not None:
            adict["oid_paybill"] = oid_paybill
        if money_order is not None:
            adict["money_order"] = money_order
        if result_pay is not None:
            adict["result_pay"] = result_pay
        if settle_date is not None:
            adict["settle_date"] = settle_date
        if info_order is not None:
            adict["info_order"] = info_order
        if pay_type is not None:
            adict["pay_type"] = pay_type
        if bank_code is not None:
            adict["bank_code"] = bank_code

        # logging.debug("---------------------------------- [LLPaymentReturn] adict: %r" % adict)

        sign = GetArgumentValue(self, "sign")

        # logging.debug("---------------------------------- [LLPaymentReturn] sign: %r" % sign)

        if GetArgumentValue(self, "oid_partner") != Settings.LIANLIANPAY["oid_partner"]:
            return False
        signstr = LLPay.signParam(adict)

        # logging.debug("---------------------------------- [LLPaymentReturn] signstr: %r" % signstr)

        return signstr == sign

    def check_xsrf_cookie(self):
        pass

class LLPaymentNotify(BaseHandler):
    def post(self):
        if self.verifyNotify() == True:
            db = DbHelper()
            inputstr = self.request.body
            jsondict = json.loads(inputstr)

            # oid_partner = jsondict["oid_partner"] if jsondict.has_key("oid_partner") else None
            no_order = jsondict["no_order"] if jsondict.has_key("no_order") else None
            # oid_paybill = jsondict["oid_paybill"] if jsondict.has_key("oid_paybill") else None
            # money_order = jsondict["money_order"] if jsondict.has_key("money_order") else None
            result_pay = jsondict["result_pay"] if jsondict.has_key("result_pay") else None
            out_trade_no = no_order
            orderinfo = db.QueryPreorderInfoByOutTradeNo(out_trade_no)
            if result_pay == 'SUCCESS':
                paymentstatus = int(orderinfo[12]) if orderinfo is not None else 0
                if paymentstatus == 0:
                    UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)

                logging.debug("---------------------------------- [LLPaymentNotify] Payment success!")

                return self.write("{'ret_code':'0000','ret_msg':'交易成功'}")
            else:
                return self.write("{'ret_code':'9999','ret_msg':'交易失败'}")
        else:
            return self.write("{'ret_code':'9999','ret_msg':'验证失败'}")

    def verifyNotify(self):
        inputstr = self.request.body

        logging.debug("---------------------------------- [LLPaymentNotify] inputstr: %r" % inputstr)

        jsondict = json.loads(inputstr)

        logging.debug("---------------------------------- [LLPaymentNotify] jsondict: %r" % jsondict)

        oid_partner = jsondict["oid_partner"] if jsondict.has_key("oid_partner") else None
        sign_type = jsondict["sign_type"] if jsondict.has_key("sign_type") else None
        dt_order = jsondict["dt_order"] if jsondict.has_key("dt_order") else None
        no_order = jsondict["no_order"] if jsondict.has_key("no_order") else None
        oid_paybill = jsondict["oid_paybill"] if jsondict.has_key("oid_paybill") else None
        money_order = jsondict["money_order"] if jsondict.has_key("money_order") else None
        result_pay = jsondict["result_pay"] if jsondict.has_key("result_pay") else None
        settle_date = jsondict["settle_date"] if jsondict.has_key("settle_date") else None
        info_order = jsondict["info_order"] if jsondict.has_key("info_order") else None
        pay_type = jsondict["pay_type"] if jsondict.has_key("pay_type") else None
        bank_code = jsondict["bank_code"] if jsondict.has_key("bank_code") else None

        adict = {}

        if oid_partner is not None:
            adict["oid_partner"] = oid_partner
        if sign_type is not None:
            adict["sign_type"] = sign_type
        if dt_order is not None:
            adict["dt_order"] = dt_order
        if no_order is not None:
            adict["no_order"] = no_order
        if oid_paybill is not None:
            adict["oid_paybill"] = oid_paybill
        if money_order is not None:
            adict["money_order"] = money_order
        if result_pay is not None:
            adict["result_pay"] = result_pay
        if settle_date is not None:
            adict["settle_date"] = settle_date
        if info_order is not None:
            adict["info_order"] = info_order
        if pay_type is not None:
            adict["pay_type"] = pay_type
        if bank_code is not None:
            adict["bank_code"] = bank_code

        logging.debug("---------------------------------- [LLPaymentNotify] adict: %r" % adict)

        sign = jsondict["sign"] if jsondict.has_key("sign") else None

        logging.debug("---------------------------------- [LLPaymentNotify] sign: %r" % sign)

        if oid_partner != Settings.LIANLIANPAY["oid_partner"]:
            return False
        signstr = LLPay.signParam(adict)

        logging.debug("---------------------------------- [LLPaymentNotify] signstr: %r" % signstr)

        return signstr == sign

    def check_xsrf_cookie(self):
        pass

def create_trade_no(user_id, product_type, product_id):
    # 订单号生成规则：商品类型（1位）+ 商品ID末3位（不足3位前缀补0）+ 用户ID末3位（不足3位前缀补0）+ 用户已下单此类型商品数量末3位（不足3位前缀补0）
    #               如有重复，则在末尾再加1位随机数（001 - 999）
    # 订单号位数：    10位 或者 13位
    db = DbHelper()
    alluserorders = db.QueryPreorders(startpos=0, count=0, productvendorid=0, userid=user_id, producttype=product_type, paymentstatus=-1)
    alluserorderscount = int(len(alluserorders) + 1) if alluserorders is not None else 1
    outtradeno = "%01d%03d%03d%03d" % (int(product_type), int(str(product_id)[-3:]), int(str(user_id)[-3:]), int(str(alluserorderscount)[-3:]))

    while db.IsOutTradeNOExist(outtradeno):
        outtradeno = "%s%03d" % (outtradeno, int(random.randint(1, 999)))

    return outtradeno

def create_competition_trade_no(user_id, competition_id):
    # 订单号生成规则：9+比赛ID（不足3位前缀补0）+用户ID末3位（不足3位前缀补0）+用户已下单此比赛数量末3位（不足3位前缀补0）
    # 如有重复，在末尾再加1位随机数（001-999）
    # 订单号位数：10位或13位
    db = DbHelper()
    registration_form_data = db.GetMyRegistrations(user_id)
    groups = groupby(sorted(
        d['competition_registration_form_registration_id']
        for d in registration_form_data
    ))
    num = len(list(groups)) + 1
    outtradeno = "%01d%03d%03d%03d" % (
        9, int(str(competition_id)[-3:]), int(str(user_id)[-3:]), int(str(num)[-3:])
    )
    while db.IsOutTradeNOExist(outtradeno):
        outtradeno = "%s%03d" % (outtradeno, int(random.randint(1, 999)))
    return outtradeno
    
class PaymentHandler(BaseHandler):
    
    def initialize(self):
        serveraddress = self.request.headers.get("Host")
        self.url_root = "http://%s" % serveraddress

    @tornado.web.authenticated
    def post(self):
        product_id = GetArgumentValue(self, "product_id")
        product_sceneid = GetArgumentValue(self, "scene_id")
        counts = GetArgumentValue(self, "preorder_counts")
        counts_child = GetArgumentValue(self, "preorder_counts_child")
        needinvoice = self.get_argument("needinvoice", "0")
        usepointcount = self.get_argument("pointdiscount", "0")
        usecouponno = GetArgumentValue(self, "coupondiscount")
        c2discountno = GetArgumentValue(self, "c2discountno")
        totalprice = GetArgumentValue(self, "totalprice")
        totalprice = 0 if totalprice is None else totalprice
        preorder_contacts = GetArgumentValue(self, "preorder_contacts")
        preorder_contactsphonenumber = GetArgumentValue(self, "preorder_contactsphonenumber")
        preorder_invoicetype = GetArgumentValue(self, "invoicetype")
        preorder_invoiceheader = GetArgumentValue(self, "preorder_invoiceheader")
        preorder_notes = GetArgumentValue(self, "preorder_notes")
        preorder_deliveryaddressid = GetArgumentValue(self, "preorder_deliveryaddressid")
        preorder_invoicedeliveryaddress = GetArgumentValue(self, "preorder_invoicedeliveryaddress")
        paymentmethod_s = pmd_s = self.get_argument('_s') # 区分支付类型 alipy "0" ebank "1"
        if int(needinvoice) == 0:
            preorder_invoicetype = 0
        try:
            counts = int(counts)
        except Exception, e:
            counts = 1

        db = DbHelper()
        productinfo = db.QueryProductInfo(product_id)

        # -------------------------------------------------------------------------
        # 优惠券抵扣
        coupondiscount = None
        if usecouponno is not None:
            if str(usecouponno) != "0":
                couponinfo = db.QueryCouponInfoByCNO(usecouponno)
                coupondiscount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]

        # -------------------------------------------------------------------------
        # 抵扣券抵扣
        c2discount = None
        if c2discountno is not None:
            if str(c2discountno) != "0":
                couponinfo = db.QueryCouponInfoByCNO(c2discountno)
                c2discount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]

        # -------------------------------------------------------------------------
        # 积分抵扣
        pointdiscount = None
        if usepointcount is not None:
            pointdiscount = float(usepointcount) / 100.0

        preorder_vendorid = productinfo[1] if not db.IsDbUseDictCursor() else productinfo["product_vendorid"]
        preorder_decuctamount = pointdiscount
        preorder_coupondiscount = coupondiscount
        preorder_usedpoints = float(pointdiscount) * 100 if pointdiscount is not None else pointdiscount
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

        # -------------------------------------------------------------------------
        # 创建订单号
        trade_no = create_trade_no(self.current_user, product_type, product_id)
        if not db.IsDbUseDictCursor():
            product_name = productinfo[2] if productinfo[2] is not None else ""
        else:
            product_name = productinfo["product_name"] if productinfo["product_name"] is not None else ""
        sceneinfo = db.QuerySceneInfo(product_sceneid)

        # -------------------------------------------------------------------------
        # 是否为需要付费的课程体验商品
        if product_type == 3:
            productprice = productinfo[9] if not db.IsDbUseDictCursor() else productinfo["product_price"]
            if productprice is not None and int(productprice) == 0:
                product3needpayment = False
            else:
                product3needpayment = True
        else:
            product3needpayment = False

        # -------------------------------------------------------------------------
        # 是否为需要付费的精彩活动商品
        if product_type == 4:
            if sceneinfo is not None:
                if float(sceneinfo[5] if not db.IsDbUseDictCursor() else sceneinfo["scene_fullprice"]) > 0:
                    product4needpayment = True
                else:
                    product4needpayment = False
            else:
                product4needpayment = False
        else:
            product4needpayment = False

        # -------------------------------------------------------------------------
        # 限购商品处理流程
        product_purchaselimit = productinfo[39] if not db.IsDbUseDictCursor() else productinfo["product_purchaselimit"]
        userbuyproductcounts  = db.QueryUserBuyProductCounts(self.current_user, product_id)
        # logging.debug("product_purchaselimit: %r, userbuyproductcounts: %r" % (product_purchaselimit, userbuyproductcounts))
        if product_purchaselimit is not None and int(product_purchaselimit) > 0 and int(userbuyproductcounts) + int(counts) > int(product_purchaselimit):
            errormsg = "非常抱歉，此商品每人限购 %s 份，您已购买 %s 份，本次无法购买 %s 份。" % (product_purchaselimit, userbuyproductcounts, counts)
            return self.renderJinjaTemplate("frontend/f1_order.html", 
                product_id=product_id, 
                scene_id=product_sceneid, 
                preorder_counts=counts, 
                preorder_counts_child=0, 
                errormsg=errormsg)

        # -------------------------------------------------------------------------
        # 商品库存检测
        instock = (sceneinfo[4] if sceneinfo is not none else 0) if not db.isdict() else sceneinfo["scene_maxpeople"]
        if instock is not None:
            if counts > instock:
                errormsg = "非常抱歉，此商品对应场次的库存为 %s，您本次无法购买 %s 份。" % (instock, counts)
                return self.renderJinjaTemplate("frontend/f1_order.html", 
                    product_id=product_id, 
                    scene_id=product_sceneid, 
                    preorder_counts=counts, 
                    preorder_counts_child=0, 
                    errormsg=errormsg)

        # -------------------------------------------------------------------------
        # 秒杀商品有效性检测
        isseckillproduct = True if productinfo['productseckill'] == 1 else False
        seckillproductstatus = productinfo['productseckillstatus']
        if isseckillproduct == True:
            if seckillproductstatus != "underway":
                errormsg = "非常抱歉，此商品不在秒杀期内，您本次无法购买。"
                return self.renderJinjaTemplate("frontend/f1_order.html", 
                    product_id=product_id, 
                    scene_id=product_sceneid, 
                    preorder_counts=counts, 
                    preorder_counts_child=0, 
                    errormsg=errormsg)

        # -------------------------------------------------------------------------
        # 联系人信息检测
        if preorder_contacts is None or preorder_contactsphonenumber is None:
            errormsg = "非常抱歉，无法提交订单，请填写订单联系人信息。"
            if self.is_mobile():
                return self.renderJinjaTemplate("frontend/f1_order_step2.html", product_id=product_id, scene_id=product_sceneid, count=counts, errormsg=errormsg)
            else:
                return self.renderJinjaTemplate("frontend/f1_order.html", 
                        product_id=product_id, 
                        scene_id=product_sceneid, 
                        preorder_counts=counts, 
                        preorder_counts_child=0, 
                        errormsg=errormsg)

        # -------------------------------------------------------------------------

        # 需要付费的订单处理流程
        # if product_type == 1 or product_type == 2 or product_type == 6 or product_type == 7 or product3needpayment == True or product4needpayment == True:
        if product_type != 5: # 非积分商城商品订单处理流程（包括付费与免费商品）
            final_price = CalculateProductPrice(self, product_id, product_sceneid, counts, counts_child, needinvoice, usepointcount, usecouponno, c2discountno)
            final_price = float("%.2f" % final_price)

            total_fee = final_price

            new_preorderinfo = {
                'preorder_fullprice' : total_fee,
                'preorder_prepaid': total_fee,
                'preorder_userid': self.current_user,
                'preorder_outtradeno': trade_no,
                'preorder_counts': counts,
                'preorder_sceneid': product_sceneid,
                'preorder_productid': product_id, 

                'preorder_contacts' : preorder_contacts,
                'preorder_contactsphonenumber' : preorder_contactsphonenumber,
                'preorder_invoicetype' : preorder_invoicetype, 
                'preorder_invoiceheader' : preorder_invoiceheader,
                'preorder_notes' : preorder_notes,
                'preorder_deliveryaddressid' : preorder_deliveryaddressid,

                'preorder_vendorid' : preorder_vendorid,
                'preorder_decuctamount' : preorder_decuctamount,
                'preorder_coupondiscount' : preorder_coupondiscount,
                'preorder_usedpoints' : preorder_usedpoints,

                'preorder_remarks' : usecouponno,
                'preorder_travellerids' : c2discountno,
                'preorder_prepaid' : totalprice,
                'preorder_invoicedeliveryaddress' : preorder_invoicedeliveryaddress
            }
            if counts_child is not None:
                new_preorderinfo["preorder_counts"] = int(counts) + int(counts_child)
            self.set_secure_cookie('outtradeno', trade_no, expires_days=0.1)
            # ====================
            _pmd_s = int(pmd_s)
            if _pmd_s == 0:
                paymentobj = { "S" : 0, "P" : 0 }   # 网站，支付宝
                new_preorderinfo["preorder_paymentmethod"] = json.dumps(paymentobj)      # 支付宝支付
                orderid = db.AddPreorder(new_preorderinfo)

                ######################################################################
                # 静安击剑报名处理流程
                if product_type == 4 and int(productinfo[27] if not db.IsDbUseDictCursor() else productinfo["product_traveltype"]) == 4:
                    swordtype = int(sceneinfo[3])
                    temp1_name = GetArgumentValue(self, "temp1_name")
                    temp1_age = GetArgumentValue(self, "temp1_age")
                    temp1_age = 0 if temp1_age is None else temp1_age
                    temp1_age = 120 if int(temp1_age) > 120 else temp1_age
                    temp1_phonenumber = GetArgumentValue(self, "temp1_phonenumber")
                    temp1_email = GetArgumentValue(self, "temp1_email")
                    temp1_gender = GetArgumentValue(self, "temp1_gender")
                    temp1_competition_category = GetArgumentValue(self, "temp1_competition_category")
                    temp1_sword_category = GetArgumentValue(self, "temp1_sword_category")
                    temp1_team_number = GetArgumentValue(self, "temp1_team_number")
                    temp1_team_number = 0 if temp1_team_number is None else temp1_team_number
                    temp1_reserve1 = orderid
                    temp1_id = db.AddSwordfight(swordfightinfo={ "temp1_name" : temp1_name, "temp1_age" : temp1_age, "temp1_phonenumber" : temp1_phonenumber,
                            "temp1_email" : temp1_email, "temp1_gender" : temp1_gender, "temp1_competition_category" : temp1_competition_category, 
                            "temp1_sword_category" : temp1_sword_category, "temp1_team_number" : temp1_team_number, "temp1_reserve1" : temp1_reserve1,
                            "temp1_type" : swordtype })
                    if swordtype == 1:
                        # 单人报名
                        pass
                    elif swordtype == 2:
                        # 团队报名
                        all_temp1_staff_name = self.get_arguments("temp1_staff_name")
                        all_temp1_staff_age = self.get_arguments("temp1_staff_age")
                        all_temp1_staff_phonenumber = self.get_arguments("temp1_staff_phonenumber")
                        for i in range(len(all_temp1_staff_name)):
                            temp1_staff_name = all_temp1_staff_name[i]
                            temp1_staff_age = all_temp1_staff_age[i]
                            temp1_staff_phonenumber = all_temp1_staff_phonenumber[i]
                            temp1_staff_extid = temp1_id

                            db.AddSwordfightStaff(swordfightstaffinfo={ "temp1_staff_extid" : temp1_staff_extid, "temp1_staff_name" : temp1_staff_name, "temp1_staff_age" : temp1_staff_age,
                                "temp1_staff_phonenumber" : temp1_staff_phonenumber })
                # 常规比赛报名处理流程
                elif product_type == 4 and int(productinfo[27] if not db.IsDbUseDictCursor() else productinfo["product_traveltype"]) == 5:
                    registration_id = GetArgumentValue(self, 'registration_id')
                    db.UpdateCompetitionRegistrationOrderNo(registration_id, orderid)
                ######################################################################

                if float(total_fee) == 0:
                    orderinfo = db.QueryPreorderInfo(orderid)
                    paymentstatus = int(orderinfo[12] if not db.IsDbUseDictCursor() else orderinfo["preorder_paymentstatus"])
                    if paymentstatus == 0:
                        UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)
                    return self.redirect('/payment/success?type=%s' % product_type)
                else:
                    if self.is_mobile():
                        url = direct_payment('alipay_wap', trade_no, product_name, total_fee, "%s/payment/return" % self.url_root, "%s/payment/notify" % self.url_root, "%s/product/%s" % (self.url_root, product_id))
                    else:
                        url = direct_payment('alipay', trade_no, product_name, total_fee, "%s/payment/return" % self.url_root, "%s/payment/notify" % self.url_root)

                    logging.debug("-----alipay url: %s" % url)

                    return self.redirect(url)
            elif _pmd_s == 1:
                paymentobj = { "S" : 1, "P" : 0 }   # 网站，网银
                new_preorderinfo["preorder_paymentmethod"] = json.dumps(paymentobj)      # 网银支付（连连支付）
                oid = db.AddPreorder(new_preorderinfo)
                return self.redirect('/payment/ebank?oid=%s' % oid)
            #     user_id = self.current_user
            #     userinfo = db.QueryUserInfoById(user_id)
            #     user_registertime = str(userinfo[17] if not db.IsDbUseDictCursor() else userinfo["user_registertime"])
            #     dt = datetime.datetime.strptime(user_registertime, "%Y-%m-%d %H:%M:%S")
            #     user_registertime = dt.strftime("%Y%m%d%H%M%S")

            #     busi_partner = 101001   # 虚拟类 - 101001，实物类 - 109001
            #     no_order = trade_no
            #     money_order = total_fee
            #     name_goods = product_name
            #     url_order = preorder_deliveryaddressid
            #     info_order = product_name
            #     bank_code = None
            #     pay_type = None
            #     card_no = None
            #     acct_name = preorder_contacts
            #     id_no = None
            #     no_agree = None
            #     flag_modify = None
            #     risk_item = '''{ "frms_ware_category" : "1005", "user_info_mercht_userno" : "%s", "user_info_dt_register" : "%s" }''' % (user_id, user_registertime)
            #     shareing_data = None
            #     back_url = None
            #     valid_order = 15        # 订单有效期，15min
            #     notify_url = "%s/payment/llpay/notify" % self.url_root
            #     return_url = "%s/payment/llpay/return" % self.url_root

            #     parameter = {
            #         "version" : Settings.LIANLIANPAY["version"],
            #         "oid_partner" : Settings.LIANLIANPAY["oid_partner"],
            #         "sign_type" : Settings.LIANLIANPAY["sign_type"],
            #         "id_type" : Settings.LIANLIANPAY["id_type"],
            #         "valid_order" : Settings.LIANLIANPAY["valid_order"],
            #         "timestamp" : strftime("%Y%m%d%H%M%S"),
            #         "dt_order" :  strftime("%Y%m%d%H%M%S"),
            #     }
            #     if user_id is not None:
            #         parameter["user_id"] = user_id
            #     if busi_partner is not None:
            #         parameter["busi_partner"] = busi_partner
            #     if no_order is not None:
            #         parameter["no_order"] = no_order
            #     if name_goods is not None:
            #         parameter["name_goods"] = name_goods
            #     if info_order is not None:
            #         parameter["info_order"] = info_order
            #     if money_order is not None:
            #         parameter["money_order"] = money_order
            #     if notify_url is not None:
            #         parameter["notify_url"] = notify_url
            #     if return_url is not None:
            #         parameter["url_return"] = return_url
            #     if url_order is not None:
            #         parameter["url_order"] = url_order
            #     if bank_code is not None:
            #         parameter["bank_code"] = bank_code
            #     if pay_type is not None:
            #         parameter["pay_type"] = pay_type
            #     if no_agree is not None:
            #         parameter["no_agree"] = no_agree
            #     if shareing_data is not None:
            #         parameter["shareing_data"] = shareing_data
            #     if risk_item is not None:
            #         parameter["risk_item"] = risk_item
            #     if id_no is not None:
            #         parameter["id_no"] = id_no
            #     if acct_name is not None:
            #         parameter["acct_name"] = acct_name
            #     if flag_modify is not None:
            #         parameter["flag_modify"] = flag_modify
            #     if card_no is not None:
            #         parameter["card_no"] = card_no
            #     if back_url is not None:
            #         parameter["back_url"] = back_url

            #     sHtml = LLPay.create_payment(parameter)
            #     return self.write(sHtml)
        # 无需付费的订单处理流程
        # elif (product_type == 3 and product3needpayment == False) or (product_type == 4 and product4needpayment == False) or product_type == 5:
        # 积分商城订单处理流程
        else: # product_type == 5
            new_preorderinfo = {
                'preorder_fullprice' : 0,
                'preorder_prepaid': 0,
                'preorder_userid': self.current_user,
                'preorder_outtradeno': trade_no,
                'preorder_counts': counts,
                'preorder_sceneid': product_sceneid,
                'preorder_productid': product_id,

                'preorder_contacts' : preorder_contacts,
                'preorder_contactsphonenumber' : preorder_contactsphonenumber,
                'preorder_invoicetype' : preorder_invoicetype, 
                'preorder_invoiceheader' : preorder_invoiceheader,
                'preorder_notes' : preorder_notes,
                'preorder_deliveryaddressid' : preorder_deliveryaddressid,

                'preorder_vendorid' : preorder_vendorid,
                'preorder_decuctamount' : preorder_decuctamount,
                'preorder_coupondiscount' : preorder_coupondiscount,
                'preorder_usedpoints' : preorder_usedpoints,
                'preorder_paymentstatus' : 1
            }
            if product_type == 5:
                new_preorderinfo["preorder_usedpoints"] = float(productinfo[9] if not db.IsDbUseDictCursor() else productinfo["product_price"]) * int(counts)
                new_preorderinfo["preorder_sceneid"] = 0

                current_userinfo = db.QueryUserInfoById(self.current_user)
                current_userpoints = float(current_userinfo[12] if not db.IsDbUseDictCursor() else current_userinfo["user_points"])
                # 积分数量不够，返回错误
                if new_preorderinfo["preorder_usedpoints"] > current_userpoints:
                    errormsg = "需要 %s 积分，您的积分数量为 %s 分，无法购买此商品！" % (int(float(new_preorderinfo["preorder_usedpoints"])), int(float(current_userpoints)))
                    return self.renderJinjaTemplate("frontend/f1_order.html", 
                        product_id=product_id, 
                        scene_id=0, 
                        preorder_counts=counts, 
                        preorder_counts_child=0, 
                        errormsg=errormsg)
            order_id = db.AddPreorder(new_preorderinfo)
            if product_type == 5 and order_id != 0:
                orderinfo = db.QueryPreorderInfo(order_id)
                UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)
            
            return self.redirect('/payment/success?type=%s' % product_type)

############################################################################################################################################################################################
############################################################################################################################################################################################

class ApiPaymentHandler(BaseHandler):
    # 客户端向微信申请预付款ID (prepay_id)
    def get(self):
        tool = GetArgumentValue(self, "tool")
        platform = GetArgumentValue(self, "plat")
        order_no = GetArgumentValue(self, "order_no")
        product_name = GetArgumentValue(self, "product_name")
        order_price = GetArgumentValue(self, "order_price")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        orderinfo = db.QueryPreorderInfoByOutTradeNo(order_no)
        if orderinfo is not None:
            couponinfo = db.QueryCouponInfoByCNO(orderinfo[30] if not db.IsDbUseDictCursor() else orderinfo["preorder_remarks"])
            couponinfo2 = db.QueryCouponInfoByCNO(orderinfo[25] if not db.IsDbUseDictCursor() else orderinfo["preorder_travellerids"])
            productinfo = db.QueryProductInfo(orderinfo[2] if not db.IsDbUseDictCursor() else orderinfo["preorder_productid"])
            product_type = productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"]
            counts = orderinfo[8] if not db.IsDbUseDictCursor() else orderinfo["preorder_counts"]
            try:
                counts = int(counts)
            except Exception, e:
                counts = 1

            # -------------------------------------------------------------------------
            # 订单中使用的优惠券无效
            if couponinfo is not None and int(couponinfo[3] if not db.IsDbUseDictCursor() else couponinfo["coupon_valid"]) == 0:
                logging.debug("您的订单中使用了无效的优惠券，无法进行支付")

                resultlist = { "retcode" : 1, "errormsg" : "您的订单中使用了无效的优惠券，无法进行支付" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 订单中使用的抵扣券无效
            if couponinfo2 is not None and int(couponinfo2[3] if not db.IsDbUseDictCursor() else couponinfo2["coupon_valid"]) == 0:
                logging.debug("您的订单中使用了无效的抵扣券，无法进行支付")

                resultlist = { "retcode" : 1, "errormsg" : "您的订单中使用了无效的抵扣券，无法进行支付" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
            
            # -------------------------------------------------------------------------
            # 常规比赛报名已过期
            if int(product_type) == 4:
                if int(productinfo[27] if not db.IsDbUseDictCursor() else productinfo["product_traveltype"]) == 5:
                    competition_status = -1

                    now = datetime.date.today()
                    begintime = productinfo[31] if not db.IsDbUseDictCursor() else productinfo["product_eventbegintime"]
                    endtime = productinfo[32] if not db.IsDbUseDictCursor() else productinfo["product_eventendtime"]
                    
                    now = datetime.datetime.strptime(str(now), "%Y-%m-%d") 
                    begintime = datetime.datetime.strptime(str(begintime), "%Y-%m-%d")
                    endtime = datetime.datetime.strptime(str(endtime), "%Y-%m-%d")

                    try:
                        if now < begintime:
                            competition_status = -1
                        elif now < endtime:
                            competition_status = 0
                        else:
                            competition_status = 1
                    except TypeError:
                        competition_status = -1

                    if competition_status != 0:
                        logging.debug("活动结束，您购买的比赛报名商品无法支付")

                        resultlist = { "retcode" : 1, "errormsg" : "活动结束，您购买的比赛报名商品无法支付" }
                        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                        self.set_header('Content-Type','application/json')
                        return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 限购商品处理流程
            product_purchaselimit = productinfo[39] if not db.IsDbUseDictCursor() else productinfo["product_purchaselimit"]
            preorder_userid = orderinfo[1] if not db.IsDbUseDictCursor() else orderinfo["preorder_userid"]
            preorder_productid = orderinfo[2] if not db.IsDbUseDictCursor() else orderinfo["preorder_productid"]
            userbuyproductcounts  = db.QueryUserBuyProductCounts(preorder_userid, preorder_productid)
            if product_purchaselimit is not None and int(product_purchaselimit) > 0 and int(userbuyproductcounts) + int(counts) > int(product_purchaselimit):
                errormsg = "非常抱歉，此商品每人限购 %s 份，您已购买 %s 份，本次无法购买 %s 份。" % (product_purchaselimit, userbuyproductcounts, counts)
                resultlist = { "retcode" : 1, "errormsg" : errormsg }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 商品库存检测
            preorder_sceneid = orderinfo[11] if not db.IsDbUseDictCursor() else orderinfo["preorder_sceneid"]
            sceneinfo = db.QuerySceneInfo(preorder_sceneid)
            instock = (sceneinfo[4] if sceneinfo is not none else 0) if not db.isdict() else sceneinfo["scene_maxpeople"]
            if instock is not None:
                if counts > int(instock):
                    errormsg = "非常抱歉，此商品对应场次的库存为 %s，您本次无法购买 %s 份。" % (instock, counts)
                    resultlist = { "retcode" : 1, "errormsg" : errormsg }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 秒杀商品有效性检测
            isseckillproduct = True if productinfo['productseckill'] == 1 else False
            seckillproductstatus = productinfo['productseckillstatus']
            if isseckillproduct == True:
                if seckillproductstatus != "underway":
                    errormsg = "非常抱歉，此商品不在秒杀期内，您本次无法购买。"
                    resultlist = { "retcode" : 1, "errormsg" : errormsg }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 联系人信息检测
            preorder_contacts = db.getDictValue(orderinfo, "preorder_contacts", 23)
            preorder_contactsphonenumber = db.getDictValue(orderinfo, "preorder_contactsphonenumber", 24)
            if preorder_contacts == "" or preorder_contactsphonenumber == "":
                errormsg = "非常抱歉，无法提交订单，请填写订单联系人信息。"
                resultlist = { "retcode" : 1, "errormsg" : errormsg }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 修改支付方式与支付工具
            if platform == "iOS":
                if tool == "wechat":
                    paymentobj = { "S" : 3, "P" : 1 }   # iOS, 微信
                elif tool == "alipay":
                    paymentobj = { "S" : 0, "P" : 1 }   # iOS, 支付宝
                else:
                    paymentobj = { "S" : 3, "P" : 1 }   # iOS, 微信
            elif platform == "Android":
                if tool == "wechat":
                    paymentobj = { "S" : 3, "P" : 2 }   # Android, 微信
                elif tool == "alipay":
                    paymentobj = { "S" : 0, "P" : 2 }   # Android, 支付宝
                else:
                    paymentobj = { "S" : 3, "P" : 2 }   # Android, 微信
            else:
                paymentobj = { "S" : 0, "P" : 2 }       # Android, 支付宝
            orderid = orderinfo[0] if not db.IsDbUseDictCursor() else orderinfo["preorder_id"]
            preorder_paymentmethod = json.dumps(paymentobj)
            db.UpdatePreorderInfo(orderid, { "preorder_paymentmethod" : preorder_paymentmethod })

            # logging.debug("platform: %r order_no: %r product_name: %r order_price: %r" % (platform, order_no, product_name, order_price))

            if tool == "wechat":
                # 向微信请求预付款ID (prepay_id)
                out_trade_no = order_no
                body = product_name
                total_fee = order_price
                notify_url = Settings.WX_NOTIFY_URL
                trade_type = "APP"

                unifiedorder = wzhifuSDK.UnifiedOrder_pub()
                unifiedorder.setParameter("out_trade_no", out_trade_no)
                unifiedorder.setParameter("body", body)
                unifiedorder.setParameter("total_fee", total_fee)
                unifiedorder.setParameter("notify_url", notify_url)
                unifiedorder.setParameter("trade_type", trade_type)

                result = unifiedorder.getResult()

                # logging.debug("result: %r" % result)

                if result["return_code"] == "SUCCESS":
                    if result["result_code"] == "SUCCESS":
                        # 预支付成功
                        timestamp = int(time.time())
                        m = hashlib.md5(str(timestamp))
                        m.digest()
                        noncestr = m.hexdigest().upper()

                        signParams = { "appid" : Settings.WX_APPID, "noncestr" : noncestr, "package" : "Sign=WXPay", "partnerid" : Settings.WX_MCHID, "timestamp" : timestamp, "prepayid" : result["prepay_id"] }
                        resultlist = { "retcode" : 0, "tool" : "wechat", "timestamp" : signParams["timestamp"], "appid" : signParams["appid"], "partnerid" : signParams["partnerid"], 
                            "prepayid" : signParams["prepayid"], "noncestr" : signParams["noncestr"], "package" : signParams["package"], "sign" : unifiedorder.getSign(signParams) }
                        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                        self.set_header('Content-Type','application/json')
                        return self.write(jsonstr)
                    else:
                        # 预支付失败
                        logging.debug("微信服务器返回错误的结果码，支付失败")

                        resultlist = { "retcode" : 1, "errormsg" : "微信服务器返回错误的结果码，支付失败" }
                        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                        self.set_header('Content-Type','application/json')
                        return self.write(jsonstr)
                else:
                    logging.debug("微信服务器返回错误的返回码，支付失败")

                    # 预支付失败
                    resultlist = { "retcode" : 1, "errormsg" : "微信服务器返回错误的返回码，支付失败" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)
            else:
                resultlist = { "retcode" : 0, "tool" : "alipay" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
        else:
            logging.debug("无法获取订单信息，支付失败")

            # 预支付失败
            resultlist = { "retcode" : 1, "errormsg" : "无法获取订单信息，支付失败" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)

class ApiPaymentWechatNotifyHandler(BaseHandler):
    def post(self):
        notify = wzhifuSDK.Notify_pub()
        xml = self.request.body
        
        logging.debug("---------------------------------- [API_WechatPaymentNotify] body: %r" % xml)

        notify.saveData(xml)
        checksign = notify.checkSign()

        logging.debug("---------------------------------- [API_WechatPaymentNotify] checksign: %r" % checksign)

        data = notify.getData()

        if data["return_code"] == "SUCCESS" and checksign == True:
            logging.debug("---------------------------------- [API_WechatPaymentNotify] check sign data scuccess, data: %r" % data)

            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            out_trade_no = data["out_trade_no"]
            total_fee = float(int(data["total_fee"]) / 100.0)
            preorder_tradeno = data['transaction_id']
            orderinfo = db.QueryPreorderInfoByOutTradeNo(out_trade_no)
            orderinfo = list(orderinfo) if not db.IsDbUseDictCursor() else dict(orderinfo)

            if orderinfo is None:

                # 通知微信支付失败
                notify.setReturnParameter("return_code", "FAIL")
                notify.setReturnParameter("return_msg", "order does not exist")
                returnxml = notify.returnXml()
                self.set_header('Content-Type','application/xml')
                self.write(returnxml)
            else:
                full_price = orderinfo[10] if not db.IsDbUseDictCursor() else orderinfo["preorder_fullprice"]

                logging.debug("---------------------------------- [API_WechatPaymentNotify] total_fee: %s, full_price: %s" % (total_fee, full_price))

                if float(total_fee) != float(full_price):

                    # 通知微信支付失败
                    notify.setReturnParameter("return_code", "FAIL")
                    notify.setReturnParameter("return_msg", "order price & product price not equal")
                    returnxml = notify.returnXml()
                    self.set_header('Content-Type','application/xml')
                    self.write(returnxml)
                else:
                    logging.debug("---------------------------------- [API_WechatPaymentNotify] out_trade_no: %s" % out_trade_no)

                    paymentstatus = int(orderinfo[12] if not db.IsDbUseDictCursor() else orderinfo['preorder_paymentstatus']) if orderinfo is not None else 0

                    if paymentstatus == 0:

                        logging.debug("---------------------------------- [API_WechatPaymentNotify] Update order status as paid!")

                        if db.IsDbUseDictCursor():
                            orderinfo['preorder_tradeno'] = preorder_tradeno
                        else:
                            orderinfo[37] = preorder_tradeno

                        UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)

                    logging.debug("---------------------------------- [API_WechatPaymentNotify] Payment success!")

                    # 通知微信支付成功
                    notify.setReturnParameter("return_code", "SUCCESS")
                    notify.setReturnParameter("return_msg", "OK")
                    returnxml = notify.returnXml()
                    self.set_header('Content-Type','application/xml')
                    self.write(returnxml)
        else:
            # 通知微信支付失败
            notify.setReturnParameter("return_code", "FAIL")
            notify.setReturnParameter("return_msg", "check sign data failed or return code is not SUCCESS")
            returnxml = notify.returnXml()
            self.set_header('Content-Type','application/xml')
            self.write(returnxml)

    def check_xsrf_cookie(self):
        pass

############################################################################################################################################################################################
############################################################################################################################################################################################

class PaymentReturnHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        '''Renders the payment success page.'''

        # 返回结果合法性校验
        paramdict = {k:''.join(v) for k,v in self.request.arguments.iteritems()}
        alipay = Alipay(Settings.ALIPAY.get('PID'), Settings.ALIPAY.get('KEY'), Settings.ALIPAY.get('EMAIL'))
        result = alipay.verify_notify(**paramdict)

        # return self.write("result:%r<br><br>paramdict: %r" % (result, paramdict))

        if result != True:
            return self.redirect('/payment/error')

        # 获取支付状态
        is_success = self.get_argument('is_success')
        if not is_success == 'T':
            return self.send_error(500)
        else:
            db = DbHelper()
            trade_no = self.get_argument('trade_no')
            out_trade_no = self.get_argument('out_trade_no')
            trade_status = self.get_argument('trade_status')

            orderinfo = db.QueryPreorderInfoByOutTradeNo(out_trade_no)
            orderinfo['preorder_tradeno'] = trade_no
            # db.UpdatePreorderInfo({ 'preorder_id' : orderinfo['preorder_id'], 'preorder_tradeno' : trade_no })

            if trade_status in ['TRADE_FINISHED', 'TRADE_SUCCESS']:
                if not db.IsDbUseDictCursor():
                    paymentstatus = int(orderinfo[12]) if orderinfo is not None else 0
                else:
                    paymentstatus = int(orderinfo["preorder_paymentstatus"]) if orderinfo is not None else 0
                if paymentstatus == 0:
                    UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)

                product_id = orderinfo[2] if not db.IsDbUseDictCursor() else orderinfo["preorder_productid"]
				
                productinfo = db.QueryProductInfo(product_id)
                product_type = productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"]
                self.redirect('/payment/success?type=%s' % product_type)
            else:
                self.redirect('/payment/error')

class PaymentNotifyHandler(BaseHandler):
    pass
    
    def post(self):
        # 返回结果合法性校验
        paramdict = {k:''.join(v) for k,v in self.request.arguments.iteritems()}
        alipay = Alipay(Settings.ALIPAY.get('PID'), Settings.ALIPAY.get('KEY'), Settings.ALIPAY.get('EMAIL'))
        result = alipay.verify_notify(**paramdict)

        logging.debug("---------------------------------- [PaymentNotifyHandler] verifyNotify: %r" % result)

        if result != True:
            return self.write("fail")

        # 获取支付状态
        db = DbHelper()
        trade_no = self.get_argument('trade_no')
        out_trade_no = self.get_argument('out_trade_no')
        trade_status = self.get_argument('trade_status')
        total_fee = self.get_argument('total_fee', '0')

        orderinfo = db.QueryPreorderInfoByOutTradeNo(out_trade_no)

        if orderinfo is None:
            return self.write("fail")
        else:
            orderinfo['preorder_tradeno'] = trade_no

            full_price = orderinfo[10] if not db.IsDbUseDictCursor() else orderinfo["preorder_fullprice"]

            logging.debug("---------------------------------- [AlipayPaymentNotify] total_fee: %s, full_price: %s" % (total_fee, full_price))

            if float(total_fee) != float(full_price):

                return self.write("fail")

            logging.debug("---------------------------------- [AlipayPaymentNotify] out_trade_no: %s" % out_trade_no)
            
            if trade_status in ['TRADE_FINISHED', 'TRADE_SUCCESS']:
                if not db.IsDbUseDictCursor():
                    paymentstatus = int(orderinfo[12]) if orderinfo is not None else 0
                else:
                    paymentstatus = int(orderinfo["preorder_paymentstatus"]) if orderinfo is not None else 0
                if paymentstatus == 0:

                    logging.debug("---------------------------------- [AlipayPaymentNotify] Update order status as paid!")

                    UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)

                logging.debug("---------------------------------- [AlipayPaymentNotify] Payment success!")

                return self.write("success")
            else:

                logging.debug("---------------------------------- [AlipayPaymentNotify] Payment failed!")

                return self.write("fail")

    def check_xsrf_cookie(self):
        pass

class ApiPaymentNotifyHandler(BaseHandler):
    def post(self):
        paramdict = {k:''.join(v) for k,v in self.request.arguments.iteritems()}

        verify_result = self.verifyNotify(paramdict)

        logging.debug("---------------------------------- [API_PaymentNotifyHandler] Verify result: %r" % verify_result)

        if verify_result:
            # 获取支付状态
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            trade_no = self.get_argument('trade_no')
            out_trade_no = self.get_argument('out_trade_no')
            trade_status = self.get_argument('trade_status')
            total_fee = self.get_argument('total_fee', '0')

            orderinfo = db.QueryPreorderInfoByOutTradeNo(out_trade_no)

            if orderinfo is None:
                return self.write("fail")
            else:
                orderinfo['preorder_tradeno'] = trade_no

                full_price = orderinfo[10] if not db.IsDbUseDictCursor() else orderinfo["preorder_fullprice"]

                logging.debug("---------------------------------- [API_PaymentNotifyHandler] total_fee: %s, full_price: %s" % (total_fee, full_price))

                if float(total_fee) != float(full_price):

                    return self.write("fail")

                logging.debug("---------------------------------- [API_PaymentNotifyHandler] out_trade_no: %s, trade_status: %s" % (out_trade_no, trade_status))

                if trade_status in ['TRADE_FINISHED', 'TRADE_SUCCESS']:
                    if not db.IsDbUseDictCursor():
                        paymentstatus = int(orderinfo[12]) if orderinfo is not None else 0
                    else:
                        paymentstatus = int(orderinfo["preorder_paymentstatus"]) if orderinfo is not None else 0
                    if paymentstatus == 0:

                        logging.debug("---------------------------------- [API_PaymentNotifyHandler] Update order status as paid!")

                        UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)

                    logging.debug("---------------------------------- [API_PaymentNotifyHandler] Payment success!")

                    return self.write("success")
        else:
            logging.debug("---------------------------------- [API_PaymentNotifyHandler] Payment failed!")

            return self.write("fail")

    def verifyNotify(self, paramdict):
        if not paramdict:
            return False
        else:
            return self.getSignVeryfy(paramdict, paramdict["sign"])

    def getSignVeryfy(self, paramdict, sign):
        '''
           获取返回时的签名验证结果
           para_temp 通知返回来的参数数组
           sign 返回的签名结果
           签名验证结果
        '''
        newdict = {}
        for i in paramdict:
            if (i == "sign") or (i == "sign_type") or (paramdict[i] == ""):
                continue
            else:
                newdict[i] = paramdict[i]
        newdict = orderdict(sorted(newdict.items()))

        signstring = ""
        for k in newdict:
            v = newdict[k]
            signstring += '%s=%s&' % (k, v)
        signstring = signstring[:-1]

        # 对签名进行 RSA 验证
        issigned = self.rsaVerify(signstring, sign)

        logging.debug("---------------------------------- [API_PaymentNotifyHandler] issigned: %r" % issigned)

        responseTxt = 'false'
        if paramdict.has_key("notify_id"):
            responseTxt = self.verifyResponse(paramdict)

        logging.debug("---------------------------------- [API_PaymentNotifyHandler] responseTxt: %r" % responseTxt)

        if issigned and responseTxt == 'true':
            return True
        else:
            return False

    def rsaVerify(self, data, sign):
        verifydata = self.verifydata(data, sign)

        logging.debug("---------------------------------- [API_PaymentNotifyHandler] verifydata: %s" % verifydata)

        return verifydata == 1

    def verifydata(self, data, sign):
        pem = Settings.ALIPAY["ALIPAY_PUBLIC_KEY"]
        key = M2Crypto.RSA.load_pub_key_bio(M2Crypto.BIO.MemoryBuffer(pem))
        m = M2Crypto.EVP.MessageDigest('sha1')
        m.update(data)
        digest = m.final()
        signature = key.verify(digest, base64.decodestring(sign), "sha1")
        return signature

    def signdata(self, data):
        pem = Settings.ALIPAY["RSA_PRIVATE_KEY"]
        key = M2Crypto.RSA.load_key_string(pem)
        m = M2Crypto.EVP.MessageDigest('sha1')
        m.update(data)
        digest = m.final()
        signature = key.sign(digest, "sha1")
        return signature

    def verifyResponse(self, adict):
        responseTxt = "false"
        notify_id = adict["notify_id"]
        if notify_id != "" :
            veryfy_url = Settings.ALIPAY["ALIPAY_TRANSPORT"] == "https" and Settings.ALIPAY["ALIPAY_HTTPS_VERIFY_URL"] or Settings.ALIPAY["ALIPAY_HTTP_VERIFY_URL"]
            veryfy_url += "partner=" + Settings.ALIPAY["PID"] + "&notify_id=" + notify_id
            open = urllib2.urlopen(veryfy_url, timeout=120000)
            responseTxt = open.read()
        return responseTxt

    def check_xsrf_cookie(self):
        pass

class PaymentCompleteHandler(BaseHandler):

    @tornado.web.authenticated
    def get(self):
        db = DbHelper()
        trade_no = self.get_secure_cookie('outtradeno')
        orderinfo = db.QueryPreorderInfoByOutTradeNo(trade_no)
        paymentstatus = int(orderinfo[12] if not db.IsDbUseDictCursor() else orderinfo["preorder_paymentstatus"]) if orderinfo is not None else 0
        if paymentstatus == 1:
            product_id = orderinfo[2] if not db.IsDbUseDictCursor() else orderinfo["preorder_productid"]
            productinfo = db.QueryProductInfo(product_id)
            product_type = productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"]
            return self.redirect('/payment/success?type=%s' % product_type)
        else:
            return self.redirect('/payment/error')

class PaymentSuccessHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self):
        product_type = GetArgumentValue(self, "type")
        return self.renderJinjaTemplate('frontend/payment_success.html', product_type=product_type)

class PaymentErrorHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self):
        self.renderJinjaTemplate('frontend/payment_failure.html')

class PaymentEbank(BaseHandler):
    """
    don't use this api directly, but via 'PaymentHandler'
    """
    def check_xsrf_cookie(self):pass

    @tornado.web.authenticated
    def get(self):
        order_id = self.get_argument('oid', None)
        self.renderJinjaTemplate('frontend/test_ebank.html', order_id=order_id)

    @tornado.web.authenticated
    def post(self):
        order_id = self.get_argument('oid', None)
        bankcode = self.get_argument('bank_code', None)
        if order_id is None: self.send_error(403)
        db = DbHelper(cursorclass=Settings.DB_DICTCURSOR)
        oinfo = db.QueryPreorderInfo(order_id)
        if oinfo is None: 
            self.send_error(403)
        else:
            outtradeno = oinfo['preorder_outtradeno']
            fullprice = oinfo['preorder_fullprice']
            _pid = oinfo['preorder_productid']
            _pinfo = db.QueryProductInfo(_pid)
            pname = _pinfo['product_name']
        # ===============
        eb = ebank.Ebank()
        eb.set_many(
            partner=Settings.ALIPAY['PID'],
            seller_email=Settings.ALIPAY['EMAIL'],
            out_trade_no=outtradeno,
            subject=pname,
            total_fee=fullprice,
        )
        if bankcode:
            eb.set_many(defaultbank=bankcode)

        eb.do_sign(Settings.ALIPAY['KEY'])
        return self.redirect(eb.get_url())

# =======================================================
class CompetitionList(BaseHandler):
    
    def get(self):
        pageindex = 1
        if self.get_argument("p", None):
            try:
                pageindex = int(self.get_argument("p"))
            except Exception, e:
                pageindex = 1
        return self.renderJinjaTemplate("frontend/competition_list.html", pageindex=pageindex)

class CompetitionDetail(BaseHandler):

    def get(self, product_id):
        db = DbHelper()
        productinfo = db.QueryProductInfo(product_id)
        if productinfo:
            product_type = productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"]
        else:
            return self.send_error(404)

        # 如果商品未上架或者未审核通过，则禁止查看其详情
        product_status = int(productinfo[13] if not db.IsDbUseDictCursor() else productinfo["product_status"])
        product_auditstatus = int(productinfo[15] if not db.IsDbUseDictCursor() else productinfo["product_auditstatus"])
        if product_status == 0 or product_auditstatus == 0:
            return self.send_error(404)
        else:
            return self.renderJinjaTemplate("frontend/f1_detail.html", productid=product_id, name=None, location=None, time=None, productoffstate=0)

class CompetitionRegister(BaseHandler):
    def check_xsrf_cookie(self):
        pass

    @tornado.web.authenticated
    def get(self, competition_id):
        db = DbHelper()
        competition = db.GetCompetition(competition_id)
        res = db.GetCompetitionRegistrationForm(competition_id)
        if res[0] != 1:
            return self.send_error(500)
        self.renderJinjaTemplate(
            'frontend/competition_register.html',
            competition=competition,
            form_info=res[1],
            field_info=res[2]
        )

    @tornado.web.authenticated
    def post(self, competition_id):
        '''Process "AJAX" registration request'''
        jsondata = self.request.body
        try:
            jsondict = json.loads(jsondata)
        except ValueError as e:
            return self.write_error(400)

        try:
            user_id = jsondict["UID"]
            players = jsondict["players"]
        except KeyError as e:
            return self.write_error(400)

        db = DbHelper()
        competition = db.GetCompetition(competition_id)
        if not competition:
            return self.send_error(404)
        obj = players
        result = db.CompetitionRegister(self.current_user, competition_id, obj)

        if result[0] == 1:
            registration_fee = competition['competition_registration_fee'] or 0

        jsonstr = json.dumps(result, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)


class CompetitionRegistrationUploadImage(BaseHandler):
    def post(self):
        '''Used for iframe upload'''
        files = self.request.files
        if not files:
            return self.write(0)
        uploadedfile = self.request.files['files[]'][0]
        original_fname = uploadedfile['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        fname = "%s%s" % (fname, getuniquestring())
        filename = fname + extension

        # Please never do this again.
        # filedir = socket.gethostname() == Settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp/static/img/image/product' or '/Library/WebServer/Documents/fivestarcamp/static/img/image/product'

        filedir = os.path.join(abspath, 'static/img/avatar/temp')
        if not os.path.exists(filedir):
            os.mkdir(filedir)

        infile   = filedir + '/' + filename # infile就是用户上传的原始照片

        # 自动保存用户上传的照片文件
        output_file = open(infile, 'w')
        output_file.write(uploadedfile['body'])
        output_file.close()
        result = 0
        path = '/static/img/avatar/temp/%s' % filename
        return self.write(json.dumps((fname, filename)))

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

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        checkuserstatus = db.CheckUser(username, password)
        if checkuserstatus < 0:
            # -2 - 无此帐户， -1 - 验证失败， 1 - 验证成功
            resultlist = { "result" : str(checkuserstatus) }

            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            userinfo = db.QueryUserInfoByNameOrPhonenumber(username)
            useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"])[0])
            resultlist = { "result" : "1", "UserInfo" : userinfo, "UserAvatar" : useravatarurl }

            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiUserCheckState(XsrfBaseHandler):
    def post(self):
        serveraddress = self.request.headers.get("Host")
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)
        userid = jsondict["UID"]
        password = jsondict["UserPassword"]
        devicetoken = jsondict["DeviceToken"] if jsondict.has_key("DeviceToken") else None

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        checkuserstatus = db.CheckUserByID(userid, password)

        # 先判读某个 deviceid 是否有注册过（即一个 deviceid 是否生成过 type 为 3 的兑奖券）如果没有注册过则注册 deviceid
        if db.IsDeviceIDExistInCoupon(deviceid=devicetoken) == False and devicetoken is not None:
            db.AddCoupon({ "coupon_userid" : 0, "coupon_type" : 3, "coupon_amount" : 0, "coupon_source" : 9, "coupon_giftcode_deviceid" : devicetoken }, couponvaliddays=99999)

        # 判断此 deviceid 对应的兑奖券是否已经兑换过礼品
        giftcode = 0
        couponinfo = db.QueryCouponInfoByDeviceID(devicetoken)
        if couponinfo is not None:
            # 如果没有兑换过则返回真实的 "GiftCode" 号码
            coupon_valid = couponinfo[3] if not db.IsDbUseDictCursor() else couponinfo["coupon_valid"]
            if coupon_valid == 1:
                giftcode = couponinfo[2] if not db.IsDbUseDictCursor() else couponinfo["coupon_serialnumber"]

            # 如果已经兑换过则返回 0 的 "GiftCode"
            else:
                giftcode = 0
        else:
            giftcode = 0

        if int(checkuserstatus) < 0:
            resultlist = { "result" : "0", "GiftCode" : giftcode }

            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            userinfo = db.QueryUserInfoById(userid)
            useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"])[0])
            if not db.IsDbUseDictCursor():
                userinfo = list(userinfo)
                userinfo[7] = useravatarurl
            else:
                userinfo["user_avatar"] = useravatarurl
            resultlist = { "result" : "1", "UserInfo" : userinfo, "GiftCode" : giftcode }

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
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        serveraddress = self.request.headers.get("Host")
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)
        user_phonenumber = jsondict["UserPhonenumber"] if jsondict.has_key("UserPhonenumber") else None

        user_name = GetArgumentValue(self, "UserName")
        user_password = GetArgumentValue(self, "UserPassword")
        user_nickname = GetArgumentValue(self, "UserNickName") if IsArgumentEmpty(self, "UserNickName") == False else user_name

        # 第三方注册用户，保存用户的 openid
        if IsArgumentEmpty(self, "WeChatOpenID") == False:
            user_qqopenid = GetArgumentValue(self, "WeChatOpenID")

            logging.debug("--- ApiUserRegister wechatunionid: %r" % user_qqopenid)

            user_qieopenid = None
            user_sinauid = None
            user_vendorcreditrating = 1

            while db.IsUserExist(user_name):
                randstr = str(time.time()).replace(".", "")[-3:]
                user_name = "%s%s" % (user_name, randstr)
        elif IsArgumentEmpty(self, "QQOpenID") == False:
            user_qqopenid = None
            user_qieopenid = GetArgumentValue(self, "QQOpenID")
            user_sinauid = None
            user_vendorcreditrating = 2

            while db.IsUserExist(user_name):
                randstr = str(time.time()).replace(".", "")[-3:]
                user_name = "%s%s" % (user_name, randstr)
        elif IsArgumentEmpty(self, "SinaUID") == False:
            user_qqopenid = None
            user_qieopenid = None
            user_sinauid = GetArgumentValue(self, "SinaUID")
            user_vendorcreditrating = 3

            while db.IsUserExist(user_name):
                randstr = str(time.time()).replace(".", "")[-3:]
                user_name = "%s%s" % (user_name, randstr)
        else:
            user_qqopenid = None
            user_qieopenid = None
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
            return self.write(jsonstr)

        if passwordret != 1:
            jsonstr = json.dumps({ "result" : "%s" % passwordret }, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)

        registersource = 2 if self.is_ios() else 3
        user_id = db.AddUser({"user_name" : user_name, "user_nickname" : user_nickname, "user_password" : user_password, "user_phonenumber" : user_phonenumber, 
            "user_role" : 1, "user_vendorcreditrating" : user_vendorcreditrating, "user_qqopenid" : user_qqopenid, "user_qieopenid" : user_qieopenid, 
            "user_sinauid" : user_sinauid, "user_registersource" : registersource, "user_registerip" : self.request.remote_ip})
        if user_id != 0:
            # 注册成功，赠送优惠券
            restriction = json.dumps({ "RestrictionType" : 1, "ProductType" : (1, 2, 6, 7) })
            db.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : 20, "coupon_source" : 0, "coupon_restrictions" : restriction }, couponvaliddays=30)

            #########################################################################################################
            # 推送相关通知信息
            message_title = '''欢迎注册成为一起动会员'''
            message_content = '''恭喜您已经成为一起动会员，最好的产品、最低的市场价尽在一起动！赶快去个人中心完善你的资料，让我们更了解你吧！'''

            # 向用户发送站内信
            db.AddMessage(messageinfo={ "message_type" : 2, "message_state" : 1, "message_title" : message_title, "message_publisher" : "系统", 
                "message_externalurl" : "", "message_externalproductid" : 0, "message_sendtime" : strftime("%Y-%m-%d"), 
                "message_receiver" : json.dumps([user_id]), "message_content" : message_content })

            # 向用户发送手机短信
            url = Settings.EMPP_URL
            phonenumber = user_phonenumber
            if re.match('^(0|86|17951)?(1[0-9][0-9]|15[012356789]|17[678]|18[0-9]|14[57])[0-9]{8}$', phonenumber):
                postparam = Settings.EMPP_POST_PARAM
                postparam["mobile"]  = phonenumber
                postparam["content"] = message_content
                requests.post(url, postparam)
            #########################################################################################################

            userinfo = db.QueryUserInfoById(user_id)
            useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(user_id)[0])
            jsonstr = json.dumps({ "result" : "1", "UserInfo" : userinfo, "UserAvatar" : useravatarurl }, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            jsonstr = json.dumps({"result" : "0"}, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

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
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
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

class ApiUserQueryInfo(XsrfBaseHandler):
    def post(self):
        serveraddress = self.request.headers.get("Host")
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"] if jsondict.has_key("UID") else None
        user_qqopenid = jsondict["openid"] if jsondict.has_key("openid") else None
        user_qieopenid = jsondict["qieopenid"] if jsondict.has_key("qieopenid") else None
        user_sinauid = jsondict["sinauid"] if jsondict.has_key("sinauid") else None

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        errormsg = None
        if user_id:
            userinfo = db.QueryUserInfoById(user_id)
            if userinfo:
                useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"])[0])
            else:
                errormsg = "userinfo is None"
        elif user_qqopenid:
            userinfo = db.QueryUserInfoByOpenid(user_qqopenid)
            if userinfo:
                useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"])[0])
            else:
                errormsg = "userinfo is None"
        elif user_qieopenid:
            userinfo = db.QueryUserInfoByQieOpenID(user_qieopenid)
            if userinfo:
                useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"])[0])
            else:
                errormsg = "userinfo is None"
        elif user_sinauid:
            userinfo = db.QueryUserInfoBySinaUID(user_sinauid)
            if userinfo:
                useravatarurl = "http://%s%s" % (serveraddress, db.GetUserAvatarPreview(userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"])[0])
            else:
                errormsg = "userinfo is None"
        else:
            errormsg = "user id is None"

        if errormsg:
            jsonstr = json.dumps({"result" : 0}, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            userinfo['user_avatar'] = useravatarurl
            current_user_id = userinfo['user_id']
            userorders = db.QueryPreorders(startpos=0, count=0, userid=current_user_id)
            usercoupons = db.QueryCoupons(startpos=0, count=0, userid=current_user_id)
            userpoints = int(userinfo['user_points'] if userinfo['user_points'] else 0)

            userinfo['user_order_count'] = len(userorders) if userorders else 0     # 订单数
            userinfo['user_coupon_count'] = len(usercoupons) if usercoupons else 0  # 优惠券数
            userinfo['user_points_count'] = userpoints                              # 积分数

            jsonstr = json.dumps({ "result" : 1, "UserInfo" : userinfo, "UserAvatar" : useravatarurl }, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiUserAvatarUpload(XsrfBaseHandler):
    def post(self):
        AVATAR_MAXWIDTH  = 300
        AVATAR_MAXHEIGHT = 300
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        # username = self.current_user
        user_id = cgi.escape(self.get_argument("uid"))
        userinfo = db.QueryUserInfoById(user_id)
        theuserid = userinfo[0] if not db.IsDbUseDictCursor() else userinfo["user_id"]

        if not self.request.files.has_key('myfile'):
            return

        uploadedfile = self.request.files['myfile'][0]
        original_fname = uploadedfile['filename']
        extension = os.path.splitext(original_fname)[1]
        fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
        filename = fname + extension

        filedir = socket.gethostname() == Settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp/static/img/avatar/user' or '/Library/WebServer/Documents/fivestarcamp/static/img/avatar/user'
        infile   = filedir + '/' + filename # infile就是用户上传的原始照片
        outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id)) # 将用户上传的原始照片进行剪裁压缩处理, 这里分两步处理，outfile_temp是通过file input控件自动上传后，处理过的预览大图，outfile是用户点击保存头像后将outfile_temp重命名的预览大图

        # 自动保存用户上传的照片文件
        output_file = open(infile, 'w')
        output_file.write(uploadedfile['body'])
        output_file.close()

        # 对上传的原始照片文件进行剪裁，宽度固定为240px, 高度可变
        avatar_size = (300, AVATAR_MAXHEIGHT)
        im = Image.open(infile)
        im_width = im.size[0]
        im_height = im.size[1]
        if im_width == im_height:
            avatar_size = (300, 300)
        elif im_width < im_height:
            avatar_size = (300, im_height if im_height < AVATAR_MAXHEIGHT else AVATAR_MAXHEIGHT)
        else:
            avatar_size = (300, int(im_height * (300.0 / im_width)))

        # 将用户上传的原始照片文件infile经处理保存为outfile_temp
        formatted_im = ImageOps.fit(im, avatar_size, Image.ANTIALIAS, centering = (0.5,0.5))
        formatted_im.save(outfile_temp, "JPEG")
        avatarfile = '/static/img/avatar/user/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 为了节约服务器空间，删除用户上传的原始照片文件
        os.remove(infile)

        # 将用户选择的照片文件上传到服务器
        outfile  = filedir + '/P%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
        # outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        x1 = 0
        y1 = 0
        x2 = 100
        y2 = 100
        try:
            # 获取用户通过javascript在预览图上勾选的图像坐标数据
            x1 = int(self.get_argument("x1", x1))
            y1 = int(self.get_argument("y1", y1))
            x2 = int(self.get_argument("x2", x2))
            y2 = int(self.get_argument("y2", y2))
        except Exception, e:
            pass

        avatar_large =   filedir + '/L%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
        avatar_normal =  filedir + '/N%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
        avatar_small =   filedir + '/S%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 将预览大图outfile_temp正式命名为outfile (outfile在用户个人资料中显示)
        if os.path.exists(outfile_temp) == True:
            outfile_temp  = filedir + '/P%s_%s_temp.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
            if os.path.exists(outfile) == True:
                os.remove(outfile)
            if os.path.exists(avatar_large) == True:
                os.remove(avatar_large)
            if os.path.exists(avatar_normal) == True:
                os.remove(avatar_normal)
            if os.path.exists(avatar_small) == True:
                os.remove(avatar_small)
            # db.SetUserAvatar(user_id, getuniquestring())
            db.UpdateUserInfoById(user_id, { "user_avatar" : getuniquestring() })
            outfile  = filedir + '/P%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
            shutil.move(outfile_temp, outfile)

        # 保存用户头像时有三咱规格， large(100x100), normal(50x50)和small(25x25)
        avatar_large =   filedir + '/L%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
        avatar_normal =  filedir + '/N%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))
        avatar_small =   filedir + '/S%s_%s.jpeg' % (theuserid, db.GetUserAvatarUniqueString(user_id))

        # 如果用户没用通过file input控件上传照片，则使用缺省照片作为预览大图
        if os.path.exists(outfile) == False:
            outfile = filedir + '/default_avatar.jpeg'
        # # 通过Python的PIL库对预览大图根据用户手选的坐标进行裁剪，裁剪的结果为一个正方形的不定大小照片
        # img = Image.open(outfile)
        # img.crop((x1, y1, x2, y2)).save(avatar_large)

        # 将上一步中正方形不定大小照片通过PIL库保存为100x100像素的用户大头像
        size = 100, 100
        im = Image.open(outfile)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(avatar_large, "JPEG")
        # 将上一步中正方形不定大小照片通过PIL库保存为50x50像素的用户中头像
        size = 50, 50
        im = Image.open(avatar_large)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(avatar_normal, "JPEG")
        # 将上一步中正方形不定大小照片通过PIL库保存为25x25像素的用户小头像
        size = 25, 25
        im = Image.open(avatar_large)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(avatar_small, "JPEG")

        resultlist = { "result" : "1" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

    def GetImagePixelSize(self, imagefilepath):
        imout = Image.open(imagefilepath)
        newsize = imout.size
        return newsize

class ApiUserNicknameUpdate(XsrfBaseHandler):
    '''更新用户呢称
    '''
    def post(self):
        errormsg = None
        # try:
            # jsondata = self.request.headers.get("json", None)
            # jsondict = json.loads(jsondata)
            # user_id = jsondict["UID"]
            # user_nickname = jsondict["UserNickname"]
        # except Exception, e:
        #     errormsg = "argument error"

        user_id = GetArgumentValue(self, "UID")
        user_nickname = GetArgumentValue(self, "UserNickname")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        try:
            db.UpdateUserInfoById(int(user_id), { "user_nickname" : user_nickname })
        except Exception, e:
            errormsg = "update user info error"

        if errormsg is not None:
            self.raiseError(errormsg)
        else:
            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        
    def raiseError(self, errormsg):
        resultlist = { "result" : "0" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserPhonenumberUpdate(XsrfBaseHandler):
    '''更新用户手机号
    '''
    def post(self):
        errormsg = None
        try:
            jsondata = self.request.headers.get("json", None)
            jsondict = json.loads(jsondata)
            user_id = jsondict["UID"]
            user_phonenumber = jsondict["UserPhonenumber"]
        except Exception, e:
            errormsg = "argument error"

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        try:
            db.UpdateUserInfoById(int(user_id), { "user_phonenumber" : user_phonenumber })
        except Exception, e:
            errormsg = "update user info error"

        if errormsg is not None:
            self.raiseError(errormsg)
        else:
            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        
    def raiseError(self, errormsg):
        resultlist = { "result" : "0" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserEmailVerify(XsrfBaseHandler):
    '''验证用户邮箱，调用此接口会向用户输入的Email地址中发送一封校验邮件，用户点击邮件中的链接后完成邮件绑定操作
    '''
    def post(self):
        fromaddress = "no-reply@17dong.com.cn"
        toaddress = None

        errormsg = None
        try:
            jsondata = self.request.headers.get("json", None)
            jsondict = json.loads(jsondata)
            toaddress = jsondict["UserEmail"]
            user_id = int(jsondict["UID"])
        except Exception, e:
            errormsg = "argument error"

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        try:
            userinfo = db.QueryUserInfoById(user_id)
            user_name = userinfo[1] if not db.IsDbUseDictCursor() else userinfo["user_name"]
            user_emailpasskey = str(uuid.uuid4())
            confirm_url_prefix = socket.gethostname() == Settings.SERVER_HOST_NAME and "http://www.17dong.com.cn" or "http://192.168.1.99"
            confirm_url = "%s/account/email/confirm?passkey=%s&email=%s&uid=%d" % (confirm_url_prefix, user_emailpasskey, toaddress, user_id)

        except Exception, e:
            errormsg = "query user info error"

        if errormsg is not None:
            self.raiseError(errormsg)
        else:
            try:
                subject = "[一起动] 请确认您的邮箱地址"
                message = ''' 
                            %s 用户，您好！<br>
                            要完成电子邮件地址的绑定，您必须点击下方确认您的邮箱地址。<br><br>
                            <a href="%s">确认电子邮件地址</a><br><br>
                            谢谢！<br>
                            一起动团队<br>''' % (user_name, confirm_url)
                web.sendmail(fromaddress, toaddress, subject, message, headers = {'Content-Type' : 'text/html;charset=utf-8'})

                db.UpdateUserInfoById(user_id, { "user_emailpasskey" : user_emailpasskey })
                resultlist = { "result" : "1" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            except Exception, e:
                self.raiseError("send email error")

    def raiseError(self, errormsg):
        resultlist = { "result" : "0" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserPasswordReset(XsrfBaseHandler):
    def post(self):
        '''  1, 重置成功
             3, 密码长度不合法（应为 6 - 32 位）
             4, 密码格式不正确（不能包含空格）
        '''
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_phonenumber = jsondict["UserPhonenumber"]
        user_password = jsondict["NewPassword"]

        passwordret = self.isValidPassword(user_password)

        if passwordret != 1:
            jsonstr = json.dumps({ "result" : "%s" % passwordret }, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)
        else:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            db.UpdateUserPasswordByPhoneNumber(user_phonenumber, user_password)

            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

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

class ApiUserPasswordUpdate(XsrfBaseHandler):
    def post(self):
        errormsg = None
        try:
            jsondata = self.request.headers.get("json", None)
            jsondict = json.loads(jsondata)
            user_id = jsondict["UID"]
            user_password_old = jsondict["OldPassword"]
            user_password = jsondict["NewPassword"]
        except Exception, e:
            errormsg = "argument error"

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        userinfo = db.QueryUserInfoById(int(user_id))

        if db.CheckUser(userinfo[1] if not db.IsDbUseDictCursor() else userinfo["user_name"], user_password_old) != 1:
            resultlist = { "result" : "2" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)

        passwordret = self.isValidPassword(user_password)
        if passwordret != 1:
            resultlist = { "result" : "%s" % passwordret }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)
        else:
            try:
                db.UpdateUserInfoById(int(user_id), { "user_password" : user_password })
            except Exception, e:
                errormsg = "update user info error"

            if errormsg is not None:
                self.raiseError(errormsg)
            else:
                resultlist = { "result" : "1" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        
    def raiseError(self, errormsg):
        resultlist = { "result" : "0" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

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

class ApiUserAddressAdd(XsrfBaseHandler):
    def post(self):
        errormsg = None

        user_id = GetArgumentValue(self, "UID")
        useraddress_recipients = GetArgumentValue(self, "AddressName")
        useraddress_phonenumber = GetArgumentValue(self, "AddressPhonenumber")
        useraddress_address = GetArgumentValue(self, "AddressDetail")
        useraddress_zipcode = GetArgumentValue(self, "AddressZipcode")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        db.AddUserAddress(int(user_id), { "useraddress_recipients" : useraddress_recipients, "useraddress_phonenumber" : useraddress_phonenumber,
            "useraddress_address" : useraddress_address, "useraddress_zipcode" : useraddress_zipcode })
        
        resultlist = { "result" : "1" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)
        
    def raiseError(self, errormsg):
        resultlist = { "result" : "0" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

    def check_xsrf_cookie(self):
        pass

class ApiUserTravellerAdd(XsrfBaseHandler):
    def post(self):
        errormsg = None

        # jsondata = self.request.headers.get("json", None)
        # jsondict = json.loads(jsondata)

        user_id = GetArgumentValue(self, "UID")
        usertraveller_name = GetArgumentValue(self, "TravellerName")
        usertraveller_idcardno = GetArgumentValue(self, "TravellerIDcardno")
        usertraveller_type = GetArgumentValue(self, "TravellerType")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        try:
            db.AddUserTraveller(int(user_id), { "usertraveller_name" : usertraveller_name, "usertraveller_idcardno" : usertraveller_idcardno, "usertraveller_type" : usertraveller_type })
        except Exception, e:
            errormsg = "update user info error"

        if errormsg is not None:
            self.raiseError(errormsg)
        else:
            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        
    def raiseError(self, errormsg):
        resultlist = { "result" : "0" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserTravellerDelete(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)
        
        user_id = jsondict["UID"]
        usertraveller_id = jsondict["UserTravellerID"]

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        db.DeleteUserTraveller(usertraveller_id)

        resultlist = { "result" : "1" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserBaseinfoUpdate(XsrfBaseHandler):
    def post(self):
        errormsg = None
        # try:
        # jsondata = self.request.headers.get("json", None)
        # jsondict = json.loads(jsondata)
        user_id = GetArgumentValue(self, "UID")
        user_gender = GetArgumentValue(self, "UserGender")
        user_birthday = GetArgumentValue(self, "UserBirthday")
        user_address = GetArgumentValue(self, "UserAddress")
        user_points = GetArgumentValue(self, "UserPoints")

        # user_interest = GetArgumentValue(self, "UserInterest")
        # 获取兴趣爱好
        user_interest = self.get_argument("UserInterest", "")
        if user_interest is not None:
            interests = user_interest.split(",")
            for i in interests:
                if i is None or i == "":
                    interests.remove(i)
            user_interest = ",".join(interests)
        else:
            user_interest = None

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        try:
            userinfodict = {}
            if user_gender is not None:
                userinfodict["user_gender"] = user_gender
            if user_birthday is not None:
                userinfodict["user_birthday"] = user_birthday
            if user_address is not None:
                userinfodict["user_address"] = user_address
            if user_interest is not None:
                userinfodict["user_interest"] = user_interest
            if user_points is not None:
                userinfodict["user_points"] = user_points
            db.UpdateUserInfoById(int(user_id), userinfodict)
        except Exception, e:
            errormsg = "update user info error"

        if errormsg is not None:
            self.raiseError(errormsg)
        else:
            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        
    def raiseError(self, errormsg):
        resultlist = { "result" : "0" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiProductAdvertised(BaseHandler):
    ''' 获取所有广告商品, 参数 type 定义：
           0  - 首页顶部轮播广告
           50 - 大 Banner 广告
           51 - 小 Banner 广告
    '''
    def get(self):
        # db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        # adstype = GetArgumentValue(self, "type")
        # if adstype == "rbads":
        #     startposition = int(self.get_argument("startposition", 0))
        #     count = GetArgumentValue(self, "count")
        #     count = int(count) if count is not None else int(Settings.LIST_ITEM_PER_PAGE)

        #     # --------------------------------------------------------------------------------------------
        #     # APP RB 广告位
        #     updatedads_23 = self.getAds(adsposition=23, startposition=startposition, count=count)
        #     # --------------------------------------------------------------------------------------------

        #     resultlist = { "result" : "1", "RB" : updatedads_23 }
        #     jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        #     self.set_header('Content-Type','application/json')
        #     self.write(jsonstr)
        # else:
        #     # --------------------------------------------------------------------------------------------
        #     # 顶部轮播广告位
        #     updatedads = self.getAds(adsposition=1)

        #     # --------------------------------------------------------------------------------------------
        #     # APP 大 Banner 广告位
        #     updatedads_2 = self.getAds(adsposition=4)

        #     # --------------------------------------------------------------------------------------------
        #     # APP 小 Banner 广告位
        #     updatedads_3 = self.getAds(adsposition=5)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R1_1 广告位
        #     updatedads_12 = self.getAds(adsposition=12)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R1_2 广告位
        #     updatedads_13 = self.getAds(adsposition=13)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R1_3 广告位
        #     updatedads_14 = self.getAds(adsposition=14)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R2_1 广告位
        #     updatedads_15 = self.getAds(adsposition=15)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R2_2 广告位
        #     updatedads_16 = self.getAds(adsposition=16)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R3_1 广告位
        #     updatedads_17 = self.getAds(adsposition=17)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R3_2 广告位
        #     updatedads_18 = self.getAds(adsposition=18)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R3_3 广告位
        #     updatedads_19 = self.getAds(adsposition=19)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R4_1 广告位
        #     updatedads_20 = self.getAds(adsposition=20)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R4_2 广告位
        #     updatedads_21 = self.getAds(adsposition=21)

        #     # --------------------------------------------------------------------------------------------
        #     # APP R4_3 广告位
        #     updatedads_22 = self.getAds(adsposition=22)

        #     # --------------------------------------------------------------------------------------------
        #     # APP RB 广告位
        #     updatedads_23 = self.getAds(adsposition=23, startposition=0, count=5)

        #     # --------------------------------------------------------------------------------------------

        #     resultlist = { "result" : "1", "AllAdvertisedProduct" : updatedads, "BigAdsInfo" : updatedads_2, "SmallAdsInfo" : updatedads_3, 
        #         "R1_1" : updatedads_12, "R1_2" : updatedads_13, "R1_3" : updatedads_14, 
        #         "R2_1" : updatedads_15, "R2_2" : updatedads_16, 
        #         "R3_1" : updatedads_17, "R3_2" : updatedads_18, "R3_3" : updatedads_19, 
        #         "R4_1" : updatedads_20, "R4_2" : updatedads_21, "R4_3" : updatedads_22, 
        #         "RB" : updatedads_23 }
        #     jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            jsonstr = {"SmallAdsInfo": [{"ads_position": 5, "ads_platform": 2, "ads_sortweight": 51, "ads_id": 13, "ads_state": 1, "ads_endtime": {"args": [2015, 2, 4, 11, 51, 21, 0], "__type__": "datetime.datetime"}, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P13_2193729920.jpeg", "ads_externalurl": "http://17dong.com.cn/product/2017", "ads_begintime": {"args": [2015, 2, 4, 11, 51, 20, 0], "__type__": "datetime.datetime"}, "adstarget": "product", "ads_externalproductid": "2017", "ads_publisher": "Willson", "productid": "2017"}], "R3_1": [{"ads_position": 17, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 56, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P56_3146519414.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u6e38\u6cf3", "productfilter": {"sort": "0", "item": "\u6e38\u6cf3", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "BigAdsInfo": [{"ads_position": 4, "ads_platform": 3, "ads_sortweight": 1, "ads_id": 95, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P95_4505549373.jpeg", "ads_externalurl": "http://www.17dong.com.cn/product/1755", "ads_begintime": None, "adstarget": "product", "ads_externalproductid": "1755", "ads_publisher": "vivian", "productid": "1755"}], "R3_3": [{"ads_position": 19, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 58, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P58_4728653791.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7bee\u7403", "productfilter": {"sort": "0", "item": "\u7bee\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R1_2": [{"ads_position": 13, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 52, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P52_9438849779.jpeg", "ads_externalurl": "http://www.17dong.com.cn/product/1503", "ads_begintime": None, "adstarget": "product", "ads_externalproductid": "1503", "ads_publisher": "Willson", "productid": "1503"}], "R1_3": [{"ads_position": 14, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 53, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P53_9439289816.jpeg", "ads_externalurl": "http://www.17dong.com.cn/product/1301", "ads_begintime": None, "adstarget": "product", "ads_externalproductid": "1301", "ads_publisher": "Willson", "productid": "1301"}], "R1_1": [{"ads_position": 12, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 51, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P51_9438388977.jpeg", "ads_externalurl": "http://www.17dong.com.cn/product/1510", "ads_begintime": None, "adstarget": "product", "ads_externalproductid": "1510", "ads_publisher": "Willson", "productid": "1510"}], "R2_1": [{"ads_position": 15, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 54, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P54_7065015451.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u8db3\u7403", "productfilter": {"sort": "0", "item": "\u8db3\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R2_2": [{"ads_position": 16, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 55, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P55_7050394159.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7bee\u7403", "productfilter": {"sort": "0", "item": "\u7bee\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R3_2": [{"ads_position": 18, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 57, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P57_3146694782.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u8db3\u7403", "productfilter": {"sort": "0", "item": "\u8db3\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "AllAdvertisedProduct": [{"ads_position": 1, "ads_platform": 2, "ads_sortweight": 999, "ads_id": 85, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P85_8155279659.jpeg", "ads_externalurl": "http://www.17dong.com.cn/special_topic/gifts?urlrequestfrom=app", "specialtopicurl": "http://www.17dong.com.cn/special_topic/gifts?urlrequestfrom=app", "ads_begintime": None, "adstarget": "specialtopic", "ads_externalproductid": None, "ads_publisher": "vivian"}, {"ads_position": 1, "ads_platform": 3, "ads_sortweight": 999, "ads_id": 93, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P93_3884070544.jpeg", "ads_externalurl": "http://www.17dong.com.cn/special_topic/exam?urlrequestfrom=app", "specialtopicurl": "http://www.17dong.com.cn/special_topic/exam?urlrequestfrom=app", "ads_begintime": None, "adstarget": "specialtopic", "ads_externalproductid": None, "ads_publisher": "vivian"}, {"ads_position": 1, "ads_platform": 3, "ads_sortweight": 900, "ads_id": 87, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P87_9851381872.jpeg", "ads_externalurl": "http://17dong.com.cn/special_topic/kaixue?urlrequestfrom=app", "specialtopicurl": "http://17dong.com.cn/special_topic/kaixue?urlrequestfrom=app", "ads_begintime": None, "adstarget": "specialtopic", "ads_externalproductid": None, "ads_publisher": "vivian"}], "result": "1", "RB": [{"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 62, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P62_7050898921.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7f51\u7403", "productfilter": {"sort": "0", "item": "\u7f51\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}, {"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 63, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P63_7051109328.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7fbd\u6bdb\u7403", "productfilter": {"sort": "0", "item": "\u7fbd\u6bdb\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}, {"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 64, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P64_7051326468.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u821e\u8e48", "productfilter": {"sort": "0", "item": "\u821e\u8e48", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}, {"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 65, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P65_7051927930.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7a7a\u624b\u9053", "productfilter": {"sort": "0", "item": "\u7a7a\u624b\u9053", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}, {"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 66, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P66_7052295917.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u8dc6\u62f3\u9053", "productfilter": {"sort": "0", "item": "\u8dc6\u62f3\u9053", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R4_3": [{"ads_position": 22, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 61, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P61_4726853486.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u821e\u8e48", "productfilter": {"sort": "0", "item": "\u821e\u8e48", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R4_2": [{"ads_position": 21, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 60, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P60_3147742676.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u51fb\u5251", "productfilter": {"sort": "0", "item": "\u51fb\u5251", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R4_1": [{"ads_position": 20, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 59, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P59_3147478989.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7f51\u7403", "productfilter": {"sort": "0", "item": "\u7f51\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}]}
            jsonstr = json.dumps(jsonstr)
            self.write(jsonstr)

    def getAds(self, adsposition, startposition=0, count=0):
        db = DbHelper()
        serveraddress = self.request.headers.get("Host")
        allads = db.QueryAllAdvertisedProduct(adsplatform=2, adsposition=adsposition, startpos=startposition, count=count)
        alladsupdated = []
        for adsinfo in allads:
            if not db.IsDbUseDictCursor():
                adsinfo = list(adsinfo)
                (avatarpreview, hascustom) = db.GetAdsAvatarPreview(adsinfo[0])
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                adsinfo[6] = avatarurl
            else:
                adsinfo = dict(adsinfo)
                (avatarpreview, hascustom) = db.GetAdsAvatarPreview(adsinfo["ads_id"])
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                adsinfo["ads_avatar"] = avatarurl
                self.processAdsAvatarUrl(adsinfo)
            alladsupdated.append(adsinfo)
        return alladsupdated

    def processAdsAvatarUrl(self, adsinfo):
        '''根据 ads_externalurl 更新 adsinfo 信息，以统一 APP 和网站对广告的跳转逻辑
        '''
        # http://www.17dong.com.cn/product/830
        # http://www.17dong.com.cn/training?sort=0&item=%E8%B6%B3%E7%90%83&age=3&vendor=%E4%B8%9C%E4%BA%9A%E4%BD%93%E8%82%B2&location=%E5%BE%90%E6%B1%87%E5%8C%BA
        # http://www.17dong.com.cn/summercamp?sort=0&item=%E5%9B%BD%E5%86%85%E8%90%A5&age=3&vendor=%E5%A5%A5%E4%BD%93360&location=%E4%B8%8A%E6%B5%B7
        # http://www.17dong.com.cn/wintercamp?sort=0&item=%E5%9B%BD%E5%86%85%E8%90%A5&age=3&vendor=%E5%A5%A5%E4%BD%93360&location=%E4%B8%8A%E6%B5%B7
        # http://www.17dong.com.cn/privatecoach?sort=0&item=%E7%BD%91%E7%90%83&age=4&location=%E9%95%BF%E5%AE%81%E5%8C%BA
        # http://www.17dong.com.cn/tourism?pitem=%E8%B5%9B%E8%BD%A6%E6%97%85%E6%B8%B8&pvendor=%E7%82%8E%E5%B0%94%E4%BD%93%E8%82%B2&ptype=2&pdestplace=%E6%B5%B7%E5%A4%96
        # http://www.17dong.com.cn/activities?pitem=%E8%BF%90%E5%8A%A8%E5%91%A8%E6%9C%AB&plocations=%E9%9D%99%E5%AE%89%E5%8C%BA
        # http://www.17dong.com.cn/topics/103
        # http://www.17dong.com.cn/special_topic/swordfight

        ads_externalurl = adsinfo['ads_externalurl']
        slashparts = ads_externalurl.split('/')

        # logging.debug("slashparts: %r" % json.dumps(slashparts))

        try:
            if slashparts[3] == "product":
                adsinfo['adstarget'] = 'product'
                adsinfo['productid'] = slashparts[4]
                adsinfo['ads_externalproductid'] = slashparts[4]
            elif slashparts[3].startswith("training"):
                adsinfo['adstarget'] = 'productlist'
                self.processUrlParts(slashparts, adsinfo, 1)
                # logging.debug("adsinfo: %r" % adsinfo)
            elif slashparts[3].startswith("summercamp"):
                adsinfo['adstarget'] = 'productlist'
                self.processUrlParts(slashparts, adsinfo, 7)
            elif slashparts[3].startswith("wintercamp"):
                adsinfo['adstarget'] = 'productlist'
                self.processUrlParts(slashparts, adsinfo, 7)
            elif slashparts[3].startswith("privatecoach"):
                adsinfo['adstarget'] = 'productlist'
                self.processUrlParts(slashparts, adsinfo, 6)
            elif slashparts[3].startswith("tourism"):
                adsinfo['adstarget'] = 'productlist'
                self.processUrlParts(slashparts, adsinfo, 2)
            elif slashparts[3].startswith("activities"):
                adsinfo['adstarget'] = 'productlist'
                self.processUrlParts(slashparts, adsinfo, 4)
            elif slashparts[3] == "topics":
                adsinfo['adstarget'] = 'topic'
                adsinfo['topicid'] = slashparts[4]
            elif slashparts[3] == "special_topic":
                adsinfo['adstarget'] = 'specialtopic'

                parsed = urlparse.urlparse(adsinfo['ads_externalurl'])
                if urlparse.parse_qs(parsed.query):
                    adsinfo['ads_externalurl'] = "%s&urlrequestfrom=app" % adsinfo['ads_externalurl']
                else:
                    adsinfo['ads_externalurl'] = "%s?urlrequestfrom=app" % adsinfo['ads_externalurl']
                adsinfo['specialtopicurl'] = adsinfo['ads_externalurl']
        except Exception, e:
            pass

    def processUrlParts(self, slashparts, adsinfo, producttype):
        subparts = slashparts[3].split('?')

        # logging.debug("subparts: %s" % subparts)

        if len(subparts) > 1:
            subsubparts = subparts[1].split('&amp;')

            # logging.debug("subsubparts: %s" % subsubparts)

            filterdict = { "producttype" : producttype }
            for onepart in subsubparts:
                suboneparts = onepart.split('=')
                filterdict[suboneparts[0]] = suboneparts[1] # unquote(suboneparts[1])
            adsinfo['productfilter'] = filterdict

            # logging.debug("adsinfo['productfilter']: %s" % adsinfo['productfilter'])
            
        else:
            adsinfo['productfilter'] = { "producttype" : 1, "item" : '', "age" : '', "vendor" : '', "location" : '' }

class ApiProductRecommended(BaseHandler):
    '''获取所有推荐商品
    '''
    def get(self):
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        startposition = int(self.get_argument("startposition", 0))
        count = GetArgumentValue(self, "count")
        count = int(count) if count is not None else int(Settings.LIST_ITEM_PER_PAGE)

        allproducts = db.QueryAllRecommendedProduct(startpos=startposition, count=count, producttype=0, productitem=None)
        serveraddress = self.request.headers.get("Host")

        updatedproducts = []
        for productinfo in allproducts:
            productinfo = list(productinfo) if not db.IsDbUseDictCursor() else dict(productinfo)
            (avatarpreview, hascustom) = db.GetProductAvatarPreview(productinfo[0] if not db.IsDbUseDictCursor() else productinfo["product_id"])
            avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
            if not db.IsDbUseDictCursor():
                productinfo[5] = avatarurl
            else:
                productinfo["product_avatar"] = avatarurl

            productid = productinfo[0] if not db.IsDbUseDictCursor() else productinfo["product_id"]
            productmarketprice = db.QueryProductMarketPrice(productid)
            product17dongprice = db.QueryProduct17dongPrice(productid)
            producthascoupon = db.IsProductHasCoupon(productid)
            producthaspromotion = db.IsProductHasPromotion(productid)
            productpoints = db.GetProductCommentScore(productid)
            # All product avatars
            productavatars = db.GetProductAvatarPreviews(productid)
            productavatars = [("http://%s%s" % (serveraddress, a[0])) for a in productavatars]

            if not db.IsDbUseDictCursor():
                productinfo.append(productmarketprice)
                productinfo.append(product17dongprice)
                productinfo.append(producthascoupon)
                productinfo.append(producthaspromotion)
                productinfo.append(productpoints)
                productinfo.append(productavatars)
            else:
                productinfo["productmarketprice"] = productmarketprice
                productinfo["product17dongprice"] = product17dongprice
                productinfo["producthascoupon"] = producthascoupon
                productinfo["producthaspromotion"] = producthaspromotion
                productinfo["productpoints"] = productpoints
                productinfo["productavatars"] = productavatars
            updatedproducts.append(productinfo)
        
        resultlist = { "result" : "1", "AllRecommendedProduct" : updatedproducts }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiProductRelatedProducts(BaseHandler):
    def get(self):
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        product_id   = self.get_argument("PID", None)
        oldproductinfo  = db.QueryProductInfo(product_id)
        if oldproductinfo is None:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            product_type = oldproductinfo[4] if not db.IsDbUseDictCursor() else oldproductinfo["product_type"]
            product_item = oldproductinfo[8] if not db.IsDbUseDictCursor() else oldproductinfo["product_item"]

            allproducts = db.QueryProducts(startpos=0, count=5, producttype=product_type, frontend=1, productitem=product_item, productvendorid=0, orderby=0)
            serveraddress = self.request.headers.get("Host")
            updatedproducts = []
            for productinfo in allproducts:

                productid = productinfo[0] if not db.IsDbUseDictCursor() else productinfo["product_id"]

                if int(product_id) == int(productid):
                    continue

                if not db.IsDbUseDictCursor():
                    productinfo = list(productinfo)
                    (avatarpreview, hascustom) = db.GetProductAvatarPreview(productid)
                    avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                    productinfo[5] = avatarurl
                else:
                    productinfo = dict(productinfo)
                    (avatarpreview, hascustom) = db.GetProductAvatarPreview(productid)
                    avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                    productinfo["product_avatar"] = avatarurl

                productmarketprice = db.QueryProductMarketPrice(productid)
                product17dongprice = db.QueryProduct17dongPrice(productid)
                producthascoupon = db.IsProductHasCoupon(productid)
                producthaspromotion = db.IsProductHasPromotion(productid)
                productpoints = db.GetProductCommentScore(productid)
                # All product avatars
                productavatars = db.GetProductAvatarPreviews(productid)
                productavatars = [("http://%s%s" % (serveraddress, a[0])) for a in productavatars]

                if not db.IsDbUseDictCursor():
                    productinfo.append(productmarketprice)
                    productinfo.append(product17dongprice)
                    productinfo.append(producthascoupon)
                    productinfo.append(producthaspromotion)
                    productinfo.append(productpoints)
                    productinfo.append(productavatars)
                else:
                    productinfo["productmarketprice"] = productmarketprice
                    productinfo["product17dongprice"] = product17dongprice
                    productinfo["producthascoupon"] = producthascoupon
                    productinfo["producthaspromotion"] = producthaspromotion
                    productinfo["productpoints"] = productpoints
                    productinfo["productavatars"] = productavatars
                updatedproducts.append(productinfo)
            
            resultlist = { "result" : "1", "AllRelatedProduct" : updatedproducts }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiVendorList(BaseHandler):
    def get(self):
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allvendors = db.QueryUsers(startpos=0, count=0, userrole=2)
        
        resultlist = { "result" : "1", "AllVendors" : allvendors }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiProductSearch(BaseHandler):
    '''搜索商品
    '''
    def get(self):
        inputkey = self.get_argument("inputkey", None)
        if inputkey is None:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            startposition = int(self.get_argument("startposition", 0))
            count = GetArgumentValue(self, "count")
            count = int(count) if count is not None else int(Settings.LIST_ITEM_PER_PAGE)
            producttype = int(self.get_argument("type", 0))
            vendorid = GetArgumentValue(self, "vendorid")
            vendorid = int(vendorid) if vendorid is not None else 0

            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            db.AddSearchkeyword(inputkey)
            allproducts = db.FuzzyQueryProduct(inputkey, startpos=startposition, count=count, producttype=producttype, frontend=1, productvendorid=vendorid)
            serveraddress = self.request.headers.get("Host")
            updatedproducts = []

            for productinfo in allproducts:
                productid = productinfo[0] if not db.IsDbUseDictCursor() else productinfo["product_id"]

                if not db.IsDbUseDictCursor():
                    productinfo = list(productinfo)
                    (avatarpreview, hascustom) = db.GetProductAvatarPreview(productid)
                    avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                    productinfo[5] = avatarurl
                else:
                    productinfo = dict(productinfo)
                    (avatarpreview, hascustom) = db.GetProductAvatarPreview(productid)
                    avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                    productinfo["product_avatar"] = avatarurl

                productmarketprice = db.QueryProductMarketPrice(productid)
                product17dongprice = db.QueryProduct17dongPrice(productid)
                producthascoupon = db.IsProductHasCoupon(productid)
                producthaspromotion = db.IsProductHasPromotion(productid)
                productpoints = db.GetProductCommentScore(productid)
                # All product avatars
                productavatars = db.GetProductAvatarPreviews(productid)
                productavatars = [("http://%s%s" % (serveraddress, a[0])) for a in productavatars]

                if not db.IsDbUseDictCursor():
                    productinfo.append(productmarketprice)
                    productinfo.append(product17dongprice)
                    productinfo.append(producthascoupon)
                    productinfo.append(producthaspromotion)
                    productinfo.append(productpoints)
                    productinfo.append(productavatars)
                else:
                    productinfo["productmarketprice"] = productmarketprice
                    productinfo["product17dongprice"] = product17dongprice
                    productinfo["producthascoupon"] = producthascoupon
                    productinfo["producthaspromotion"] = producthaspromotion
                    productinfo["productpoints"] = productpoints
                    productinfo["productavatars"] = productavatars
                updatedproducts.append(productinfo)

            resultlist = { "result" : "1", "SearchedProduct" : updatedproducts }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiProductSearchDetail(BaseHandler):
    '''查询某个商品的详细信息
    '''
    def get(self):
        '''查询商品详细信息
        '''
        product_id = self.get_argument("pid", None)
        if product_id is None:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            productinfo = db.QueryProductInfo(product_id)

            productid = productinfo[0] if not db.IsDbUseDictCursor() else productinfo["product_id"]

            if not db.IsDbUseDictCursor():
                productinfo = list(productinfo)
                serveraddress = self.request.headers.get("Host")
                (avatarpreview, hascustom) = db.GetProductAvatarPreview(productid)
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                productinfo[5] = avatarurl
            else:
                productinfo = dict(productinfo)
                serveraddress = self.request.headers.get("Host")
                (avatarpreview, hascustom) = db.GetProductAvatarPreview(productid)
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                productinfo["product_avatar"] = avatarurl

            productmarketprice = db.QueryProductMarketPrice(productid)
            product17dongprice = db.QueryProduct17dongPrice(productid)
            producthascoupon = db.IsProductHasCoupon(productid)
            producthaspromotion = db.IsProductHasPromotion(productid)
            productpoints = db.GetProductCommentScore(productid)
            # All product avatars
            productavatars = db.GetProductAvatarPreviews(productid)
            productavatars = [("http://%s%s" % (serveraddress, a[0])) for a in productavatars]
            defaultsceneinfo = db.GetDefaultSceneFromScenes(productscenes=db.QueryProductOfScene(product_id, None, None, None))
            
            if not db.IsDbUseDictCursor():
                productinfo.append(productmarketprice)
                productinfo.append(product17dongprice)
                productinfo.append(producthascoupon)
                productinfo.append(producthaspromotion)
                productinfo.append(productpoints)
                productinfo.append(productavatars)
                productinfo.append(defaultsceneinfo)
            else:
                productinfo["productmarketprice"] = productmarketprice
                productinfo["product17dongprice"] = product17dongprice
                productinfo["producthascoupon"] = producthascoupon
                productinfo["producthaspromotion"] = producthaspromotion
                productinfo["productpoints"] = productpoints
                productinfo["productavatars"] = productavatars
                productinfo["defaultsceneinfo"] = defaultsceneinfo

            resultlist = { "result" : "1", "SearchedProductDetail" : productinfo }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiProductList(BaseHandler):
    '''分页获取所需要的商品
    '''
    def get(self):
        # if GetApiVersion(self) is None:
        #     return self.write("No version")
        # else:
        #     return self.write(GetApiVersion(self))

        startposition = int(self.get_argument("startposition", 0))
        count = int(self.get_argument("count", Settings.LIST_ITEM_PER_PAGE))
        producttype = int(self.get_argument("type", 0))
        sort = int(self.get_argument("sort", 0))
        mylocation = (0, 0)
        if sort == 5:
            if IsArgumentEmpty(self, "mylocation"):
                mylocation = "0,0"
            else:
                mylocation = self.get_argument("mylocation", "0,0")
            (lat, lng) = mylocation.split(',')
            mylocation = (float(lat.strip()), float(lng.strip()))

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        if producttype == 1 or producttype == 6 or producttype == 7:
            item = GetArgumentValue(self, "item")
            parentitem = GetArgumentValue(self, "parentitem")
            location = GetArgumentValue(self, "location")
            age = GetArgumentValue(self, "age")
            vendor = GetArgumentValue(self, "vendor")
            allproducts = db.QueryFilteredProducts(trainingitem=item, trainingplace=location, trainingage=age, trainingvendor=vendor, startpos=startposition, count=count, producttype=producttype, sort=sort, mylocation=mylocation, parentitem=parentitem)
        elif producttype == 2:
            pdestplace = GetArgumentValue(self, "pdestplace")
            pitem = GetArgumentValue(self, "pitem")
            ptype = GetArgumentValue(self, "ptype")
            pvendor = GetArgumentValue(self, "pvendor")
            allproducts = db.QueryTourismProducts(filters={"pdestplace" : pdestplace, "pitem" : pitem, "ptype" : ptype, "pvendor" : pvendor}, startpos=startposition, count=count)
        elif producttype == 3:
            pitem = GetArgumentValue(self, "pitem")
            plocations = GetArgumentValue(self, "plocations")
            allproducts = db.QueryFreetrialProducts(filters={"pitem" : pitem, "plocations" : plocations}, startpos=startposition, count=count)
        elif producttype == 4:
            pitem = GetArgumentValue(self, "pitem")
            plocations = GetArgumentValue(self, "plocations")
            allproducts = db.QueryFilteredProducts(trainingitem=pitem, trainingplace=plocations, trainingage=None, trainingvendor=None, startpos=startposition, count=count, producttype=4, sort=sort, mylocation=mylocation)
        else:
            allproducts = db.QueryProducts(startposition, count, producttype, frontend=1)

        serveraddress = self.request.headers.get("Host")
        updatedproducts = []
        for productinfo in allproducts:
            if not db.IsDbUseDictCursor():
                productinfo = list(productinfo)
                (avatarpreview, hascustom) = db.GetProductAvatarPreview(productinfo[0])
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                productinfo[5] = avatarurl
            else:
                productinfo = dict(productinfo)
                (avatarpreview, hascustom) = db.GetProductAvatarPreview(productinfo["product_id"])
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                productinfo["product_avatar"] = avatarurl
            
            productid = productinfo[0] if not db.IsDbUseDictCursor() else productinfo["product_id"]
            productmarketprice = db.QueryProductMarketPrice(productid)
            product17dongprice = db.QueryProduct17dongPrice(productid)
            producthascoupon = db.IsProductHasCoupon(productid)
            producthaspromotion = db.IsProductHasPromotion(productid)
            productpoints = db.GetProductCommentScore(productid)
            # All product avatars
            productavatars = db.GetProductAvatarPreviews(productid)
            productavatars = [("http://%s%s" % (serveraddress, a[0])) for a in productavatars]
            if sort == 5:
                if int(mylocation[0]) == 0 and int(mylocation[1]) == 0:
                    productdistance = 999999999
                else:
                    if not db.IsDbUseDictCursor():
                        productdistance = productinfo.pop()
                    else:
                        productdistance = productinfo["productdistance"]
            else:
                productdistance = 999999999

            if not db.IsDbUseDictCursor():
                productinfo.append(productmarketprice)
                productinfo.append(product17dongprice)
                productinfo.append(producthascoupon)
                productinfo.append(producthaspromotion)
                productinfo.append(productpoints)
                productinfo.append(productavatars)
                productinfo.append(productdistance)
            else:
                productinfo["productmarketprice"] = productmarketprice
                productinfo["product17dongprice"] = product17dongprice
                productinfo["producthascoupon"] = producthascoupon
                productinfo["producthaspromotion"] = producthaspromotion
                productinfo["productpoints"] = productpoints
                productinfo["productavatars"] = productavatars
                productinfo["productdistance"] = productdistance
            updatedproducts.append(productinfo)

        resultlist = { "result" : "1", "ProductList" : updatedproducts }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiProductFilterList(BaseHandler):
    def get(self):
        product_type = int(self.get_argument("type"))
        filtername = self.get_argument("filtername")
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)

        if product_type == 1 or product_type == 6 or product_type == 7:
            if filtername == "subitem":            # 培训项目
                allitems = db.QueryCategoriesList()
            elif filtername == "item":            # 培训项目
                allitems = db.QueryCategories(startpos=0, count=0, categoryparent=product_type, sort=2)
            elif filtername == "location":      # 培训地点
                allitems = db.QueryAllTeachingPlaces(producttype=product_type)
            elif filtername == "age":           # 适应年龄段
                allitems = ["1", "2", "3", "4", "5"]
            elif filtername == "vendor":        # 供应商
                allitems = db.QueryVendorsByProductType(producttype=product_type)
            else:
                allitems = []
            resultlist = { "result" : "1", "FilterItems" : allitems }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        elif product_type == 2:
            if filtername == "pdestplace":      # 目的地
                allitems = db.QueryAllTravelDestinationlace()
            elif filtername == "pitem":         # 旅游主题
                allitems = db.QueryCategories(0, 0, 2, sort=2)
            elif filtername == "ptype":         # 旅游类型
                allitems = ["0", "1", "2", "3"]
            elif filtername == "pvendor":       # 供应商
                allitems = db.QueryVendorsByProductType(producttype=2)
            else:
                allitems = []
            resultlist = { "result" : "1", "FilterItems" : allitems }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        elif product_type == 3:
            if filtername == "pitem":           # 体验项目
                allitems = db.QueryCategories(0, 0, 3, sort=2)
            elif filtername == "plocations":    # 体验地点
                allitems = db.QueryAllTeachingPlaces(3)
            else:
                allitems = []
            resultlist = { "result" : "1", "FilterItems" : allitems }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        elif product_type == 4:
            if filtername == "pitem":           # 活动项目
                allitems = db.QueryCategories(startpos=0, count=0, categoryparent=4, sort=2)
            elif filtername == "plocations":    # 活动地点
                allitems = db.QueryAllTeachingPlaces(producttype=4)
            else:
                allitems = []
            resultlist = { "result" : "1", "FilterItems" : allitems }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiProductSceneList(BaseHandler):
    '''获取商品的所有场次信息
    '''
    def get(self):
        product_id = self.get_argument("pid", None)
        if product_id is None:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            allscenes = db.QueryProductScenes(product_id)

            resultlist = { "result" : "1", "ProductSceneList" : allscenes }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiProductSceneListAll(BaseHandler):
    def get(self):
        productid = GetArgumentValue(self, "PID")
        name      = GetArgumentValue(self, "SceneName")
        location  = GetArgumentValue(self, "SceneLocation")
        time      = GetArgumentValue(self, "SceneTimeperiod")

        # -----------------------------------------------------------------
        # remove ZERO-WIDTH SPACE (ZWSP)
        if name is not None:
            name = name.replace('\xe2\x80\x8e', '')

        if location is not None:
            location = location.replace('\xe2\x80\x8e', '')

        if time is not None:
            time = time.replace('\xe2\x80\x8e', '')
        # -----------------------------------------------------------------

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        productinfo  = db.QueryProductInfo(productid)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])
        allproductscenebyname       = db.QueryProductScenes(productid, distinctscenename=True)
        allproductscenebylocation   = db.QueryProductScenes(productid, distinctscenelocation=True)
        allproductscenebytimeperiod = db.QueryProductScenes(productid, distinctscenetimeperiod=True)

        productscenes = db.QueryProductOfScene(productid, None, None, None)
        defaultsceneinfo = db.GetDefaultSceneFromScenes(productscenes=productscenes)
        if name is not None or location is not None or time is not None:
            current_scene_name = name
            current_scene_location = location
            current_scene_time = time

            allscenes = db.QueryProductOfScene(productid, name, location, time)
            if len(allscenes) > 0:
                thescene = allscenes[0]
                if current_scene_location is None:
                    current_scene_location = thescene[8] if not db.IsDbUseDictCursor() else thescene["scene_locations"]
                if current_scene_time is None:
                    current_scene_time = thescene[9] if not db.IsDbUseDictCursor() else thescene["scene_timeperiod"]
            else:
                current_scene_location = None
                current_scene_time = None
        else:
            if not db.IsDbUseDictCursor():
                current_scene_name = defaultsceneinfo[7] if len(defaultsceneinfo) > 0 else None
                current_scene_location = defaultsceneinfo[8] if len(defaultsceneinfo) > 0 else None
                current_scene_time = defaultsceneinfo[9] if len(defaultsceneinfo) > 0 else None
            else:
                current_scene_name = defaultsceneinfo["scene_name"] if len(defaultsceneinfo) > 0 else None
                current_scene_location = defaultsceneinfo["scene_locations"] if len(defaultsceneinfo) > 0 else None
                current_scene_time = defaultsceneinfo["scene_timeperiod"] if len(defaultsceneinfo) > 0 else None
        alllocationsofname = db.QueryProductLocationsInScene(productid, current_scene_name)
        alltimeperiodsofname = db.QueryProductTimeperiodsInScene(productid, current_scene_name, current_scene_location)

        # (price, marketprice, totalprice, childprice) = db.QueryProductPrice(productid=productid, scenename=current_scene_name, scenelocation=current_scene_location, scenetime=current_scene_time, count=1, count1=1, count2=0)
        allscenes = db.QueryProductOfScene(productid, current_scene_name, current_scene_location, current_scene_time)
        if allscenes is not None and len(allscenes) > 0:
            currentscene = allscenes[0]
        else:
            currentscene = None

        activescenename = None
        activescenelocation = None
        activescenetime = None
        allnames     = []
        alllocations = []
        alltimes     = []

        if product_type != 3 and product_type != 5:
            for sceneinfo in allproductscenebyname:
                scene_name = sceneinfo[7] if not db.IsDbUseDictCursor() else sceneinfo["scene_name"]
                allnames.append(scene_name)
                if current_scene_name == scene_name:
                    activescenename = scene_name

        if product_type != 2 and product_type != 5:
            for sceneinfo in allproductscenebylocation:
                scene_location = sceneinfo[8] if not db.IsDbUseDictCursor() else sceneinfo["scene_locations"]
                locationisin = []
                for onelocationinfo in alllocationsofname:
                    scenelocations = onelocationinfo[0] if not db.IsDbUseDictCursor() else onelocationinfo["scene_locations"]
                    if scenelocations == scene_location:
                        locationisin.append(scenelocations)
                        break
                if len(locationisin) > 0:
                    alllocations.append(scene_location)
                if current_scene_location == scene_location:
                    activescenelocation = scene_location

        if product_type != 5:
            for sceneinfo in allproductscenebytimeperiod:
                scene_timeperiod = sceneinfo[9] if not db.IsDbUseDictCursor() else sceneinfo["scene_timeperiod"]
                timeperiodisin = []
                for ontimeperiodinfo in alltimeperiodsofname:
                    scenetimeperiod = ontimeperiodinfo[0] if not db.IsDbUseDictCursor() else ontimeperiodinfo["scene_timeperiod"]
                    if scenetimeperiod == scene_timeperiod:
                        timeperiodisin.append(scenetimeperiod)
                        break
                if len(timeperiodisin) > 0:
                    alltimes.append(scene_timeperiod)
                if current_scene_time == scene_timeperiod:
                    activescenetime = scene_timeperiod

        resultlist = { "result" : "1", "SceneNames" : allnames, "SceneLocations" : alllocations, "SceneTimeperiods" : alltimes, "DefaultScene" : currentscene }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiCommentList(XsrfBaseHandler):
    def get(self):
        startposition = GetArgumentValue(self, "startposition")
        count = GetArgumentValue(self, "count")
        productid = GetArgumentValue(self, "productid")
        vendorid = GetArgumentValue(self, "vendorid")
        commentlevel = GetArgumentValue(self, "commentlevel")

        startposition = int(startposition) if startposition else 0
        count = int(count) if count else Settings.LIST_ITEM_PER_PAGE
        productid = int(productid) if productid else 0
        vendorid = int(vendorid) if vendorid else 0
        commentlevel = int(commentlevel) if commentlevel is not None else 2

        if productid == 0:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            allcomments = db.QueryComments(startposition, count=count, commentproductid=productid, productvendorid=vendorid, commentlevel=commentlevel)
            serveraddress = self.request.headers.get("Host")

            score1 = 0
            score2 = 0
            score3 = 0
            goodcomments = 0
            moderatecomments = 0
            poolcomments = 0
            updatedcomments = []
            for commentinfo in allcomments:
                commentinfo = list(commentinfo) if not db.IsDbUseDictCursor() else dict(commentinfo)

                commentuserinfo = db.QueryUserInfoById(commentinfo[1] if not db.IsDbUseDictCursor() else commentinfo["comment_userid"])
                commentuseravatar = db.GetUserAvatarPreview(commentuserinfo[0] if not db.IsDbUseDictCursor() else commentuserinfo["user_id"])[0]
                commentuseravatar = "http://%s%s" % (serveraddress, commentuseravatar)
                commentusername = commentuserinfo[1] if not db.IsDbUseDictCursor() else commentuserinfo["user_name"]

                if not db.IsDbUseDictCursor():
                    commentinfo.append(commentusername)
                    commentinfo.append(commentuseravatar)
                else:
                    commentinfo["commentusername"] = commentusername
                    commentinfo["commentuseravatar"] = commentuseravatar

                updatedcomments.append(commentinfo)

                comment_level = int(commentinfo[5] if not db.IsDbUseDictCursor() else commentinfo["comment_level"])
                if comment_level == 1:
                    goodcomments += 1
                elif comment_level == 0:
                    moderatecomments += 1
                elif comment_level == -1:
                    poolcomments += 1

                score1 += commentinfo[6] if not db.IsDbUseDictCursor() else commentinfo["comment_score1"]
                score2 += commentinfo[7] if not db.IsDbUseDictCursor() else commentinfo["comment_score2"]
                score3 += commentinfo[8] if not db.IsDbUseDictCursor() else commentinfo["comment_score3"]

            if len(allcomments) > 0:
                score1 = "%.2f" % (float(score1) / float(len(allcomments)))
                score2 = "%.2f" % (float(score2) / float(len(allcomments)))
                score3 = "%.2f" % (float(score3) / float(len(allcomments)))
            else:
                score1 = 0
                score2 = 0
                score3 = 0

            resultlist = { "result" : "1", "CommentList" : updatedcomments, 
                "Good" : goodcomments, "Moderate" : moderatecomments, "Pool" : poolcomments,
                "Score1" : score1, "Score2" : score2, "Score3" : score3 }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiCommentAdd(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)

        jsondict = json.loads(jsondata)
        user_id = jsondict["UID"] if jsondict.has_key("UID") else 0
        product_id = jsondict["PID"] if jsondict.has_key("PID") else 0
        order_id = jsondict["OID"] if jsondict.has_key("OID") else 0

        if int(user_id) == 0 or int(product_id) == 0 or int(order_id) == 0:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            comment_level = jsondict["CommentLevel"]
            comment_score1 = jsondict["CommentScore1"]
            comment_score2 = jsondict["CommentScore2"]
            comment_score3 = jsondict["CommentScore3"]
            comment_content = GetArgumentValue(self, "CommentContent")

            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            orderinfo = db.QueryPreorderInfo(order_id)
            if int(orderinfo[13] if not db.IsDbUseDictCursor() else orderinfo["preorder_joinstatus"]) == 0:
                comment_id = db.AddComment(commentinfo={ 
                    "comment_userid" : user_id,
                    "comment_productid" : product_id, 
                    "comment_content" : comment_content, 
                    "comment_level" : comment_level, 
                    "comment_score1" : comment_score1, 
                    "comment_score2" : comment_score2, 
                    "comment_score3" : comment_score3
                })

                # 赠送积分
                userinfo = db.QueryUserInfoById(user_id)
                if not db.IsDbUseDictCursor():
                    user_points = 0 if userinfo[12] is None else int(userinfo[12])
                else:
                    user_points = 0 if userinfo["user_points"] is None else int(userinfo["user_points"])
                user_points = user_points + 50
                db.UpdateUserInfoById(user_id, { "user_points" : user_points })

                # 更新订单状态 -> 已评价
                db.UpdatePreorderInfo(order_id, { "preorder_joinstatus" : 1 })

                resultlist = { "result" : "1", "CommentID" : comment_id }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)

class ApiOrderAdd(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        userid = jsondict["preorder_userid"] if jsondict.has_key("preorder_userid") else 0
        productid = jsondict["preorder_productid"] if jsondict.has_key("preorder_productid") else 0

        preorder_contacts = GetArgumentValue(self, "preorder_contacts")
        preorder_contactsphonenumber = GetArgumentValue(self, "preorder_contactsphonenumber")
        preorder_appraisal = GetArgumentValue(self, "preorder_appraisal")
        preorder_invoiceheader = GetArgumentValue(self, "preorder_invoiceheader")
        preorder_notes = GetArgumentValue(self, 'preorder_notes')
        preorder_deliveryaddressid = jsondict["preorder_deliveryaddressid"] if jsondict.has_key("preorder_deliveryaddressid") else None

        if int(userid) == 0 or int(productid) == 0:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            productinfo = db.QueryProductInfo(productid)
            product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

            preorder_outtradeno = create_trade_no(jsondict["preorder_userid"], product_type, jsondict["preorder_productid"])
            jsondict["preorder_outtradeno"] = preorder_outtradeno
            jsondict["preorder_contacts"] = preorder_contacts
            jsondict["preorder_contactsphonenumber"] = preorder_contactsphonenumber
            jsondict["preorder_appraisal"] = preorder_appraisal
            jsondict["preorder_invoiceheader"] = preorder_invoiceheader
            jsondict['preorder_notes'] = preorder_notes
            jsondict["preorder_deliveryaddressid"] = 0 if preorder_deliveryaddressid is None or preorder_deliveryaddressid == "" else preorder_deliveryaddressid

            useragent = self.request.headers["User-Agent"]
            if useragent == "iOS":
                paymentobj = { "S" : 0, "P" : 1 }   # iOS, 支付宝
            elif useragent == "Android":
                paymentobj = { "S" : 0, "P" : 2 }   # Android, 支付宝
            else:
                paymentobj = { "S" : 0, "P" : 1 }   # iOS, 支付宝
            jsondict["preorder_paymentmethod"] = json.dumps(paymentobj)

            preorder_id = db.AddPreorder(preorderinfo=jsondict)
            orderinfo = db.QueryPreorderInfo(preorder_id)
            if product_type == 5:
                UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)

            resultlist = { "result" : "1", "OrderInfo" : orderinfo }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
            
    def raiseError(self, errormsg):
        resultlist = { "result" : "0" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiOrderQuery(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        preorder_id = jsondict["OID"] if jsondict.has_key("OID") else None
        preorder_outtradeno = jsondict["OutTradeNo"] if jsondict.has_key("OutTradeNo") else None

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        if preorder_id is not None:
            orderinfo = db.QueryPreorderInfo(preorder_id)
        elif preorder_outtradeno is not None:
            orderinfo = db.QueryPreorderInfoByOutTradeNo(preorder_outtradeno)
        else:
            orderinfo = None

        if orderinfo is None:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            resultlist = { "result" : "1", "OrderInfo" : orderinfo }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiOrderQueryFinalPrice(BaseHandler):
    def get(self):
        product_id = GetArgumentValue(self, "PID")
        scene_id = GetArgumentValue(self, "SID")

        try:
            preorder_counts = int(self.get_argument("Counts", 1))
        except Exception, e:
            preorder_counts = 1
        try:
            preorder_counts_child = int(self.get_argument("CountsChild", 0))
        except Exception, e:
            preorder_counts_child = 0
        try:
            needinvoice = int(self.get_argument("NeedInvoice", 0))
        except Exception, e:
            needinvoice = 0

        usepointcount = self.get_argument("UsePointCount", 0)
        usepointcount = int(float(usepointcount))
        usecouponno = GetArgumentValue(self, "UseCouponNO")
        c2discountno = GetArgumentValue(self, "C2DiscountNO")

        final_price = CalculateProductPrice(self, product_id, scene_id, preorder_counts, preorder_counts_child, needinvoice, usepointcount, usecouponno, c2discountno)
        final_price = float("%.2f" % final_price)

        resultlist = { "result" : "1", "FinalPrice" : final_price }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiC2DiscountValidate(XsrfBaseHandler):
    def post(self):
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)

        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)
        c2password = jsondict["C2DiscountNO"] # GetArgumentValue(self, "C2DiscountNO")
        product_id = jsondict["PID"] # GetArgumentValue(self, "PID")

        try:
            c2password = int(c2password)
        except Exception, e:
            resultlist = { "result" : "-1", "errormsg" : "请输入正确格式的抵扣券密码" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)

        if c2password is not None and int(c2password) > 0:
            if db.IsUniqueStringExistsInCoupon(uniquestr=c2password, coupontype=1):
                couponinfo = db.QueryCouponInfoByCNO(cno=c2password)
                coupon_valid = couponinfo[3] if not db.IsDbUseDictCursor() else couponinfo["coupon_valid"]
                if int(coupon_valid) == 1:
                    coupon_validtime = couponinfo[9] if not db.IsDbUseDictCursor() else couponinfo["coupon_validtime"]
                    coupon_validtime = str(coupon_validtime)
                    validdays = datetime.date(int(coupon_validtime[0:4]), int(coupon_validtime[5:7]), int(coupon_validtime[8:10])) - datetime.date.today()
                    validdays = validdays.days
                    if validdays >= 0:
                        if db.ValidateProductCoupon(productid=product_id, couponid=couponinfo[0] if not db.IsDbUseDictCursor() else couponinfo["coupon_id"]):
                            discountamount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]
                            discountamount = "%.2f" % float(discountamount)
                            resultlist = { "result" : "1", "DiscountAmount" : discountamount }
                            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                            self.set_header('Content-Type','application/json')
                            return self.write(jsonstr)
                        else:
                            resultlist = { "result" : "-5", "errormsg" : "您的抵扣券无法使用于此商品" }
                            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                            self.set_header('Content-Type','application/json')
                            return self.write(jsonstr)
                    else:
                        resultlist = { "result" : "-4", "errormsg" : "抵扣券已过期" }
                        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                        self.set_header('Content-Type','application/json')
                        return self.write(jsonstr)
                else:
                    resultlist = { "result" : "-3", "errormsg" : "抵扣券已被使用" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)
            else:
                resultlist = { "result" : "-2", "errormsg" : "您输入的抵扣券密码不正确" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

class ProductC2DiscountValidate(BaseHandler):
    def post(self, product_id):
        db = DbHelper(cursorclass=Settings.DB_DICTCURSOR)
        c2password = GetArgumentValue(self, "C2DiscountNO")

        try:
            c2password = int(c2password)
        except Exception, e:
            resultlist = { "result" : "-1", "errormsg" : "请输入正确格式的抵扣券密码" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)

        if c2password is not None and int(c2password) > 0:
            if db.IsUniqueStringExistsInCoupon(uniquestr=c2password, coupontype=1):
                couponinfo = db.QueryCouponInfoByCNO(cno=c2password)
                coupon_valid = couponinfo[3] if not db.IsDbUseDictCursor() else couponinfo["coupon_valid"]
                if int(coupon_valid) == 1:
                    coupon_validtime = couponinfo[9] if not db.IsDbUseDictCursor() else couponinfo["coupon_validtime"]
                    coupon_validtime = str(coupon_validtime)
                    validdays = datetime.date(int(coupon_validtime[0:4]), int(coupon_validtime[5:7]), int(coupon_validtime[8:10])) - datetime.date.today()
                    validdays = validdays.days
                    if validdays >= 0:
                        if db.ValidateProductCoupon(productid=product_id, couponid=couponinfo[0] if not db.IsDbUseDictCursor() else couponinfo["coupon_id"]):
                            discountamount = couponinfo[4] if not db.IsDbUseDictCursor() else couponinfo["coupon_amount"]
                            discountamount = "%.2f" % float(discountamount)
                            resultlist = { "result" : "1", "DiscountAmount" : discountamount }
                            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                            self.set_header('Content-Type','application/json')
                            return self.write(jsonstr)
                        else:
                            resultlist = { "result" : "-5", "errormsg" : "您的抵扣券无法使用于此商品" }
                            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                            self.set_header('Content-Type','application/json')
                            return self.write(jsonstr)
                    else:
                        resultlist = { "result" : "-4", "errormsg" : "抵扣券已过期" }
                        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                        self.set_header('Content-Type','application/json')
                        return self.write(jsonstr)
                else:
                    resultlist = { "result" : "-3", "errormsg" : "抵扣券已被使用" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)
            else:
                resultlist = { "result" : "-2", "errormsg" : "您输入的抵扣券密码不正确" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

class ApiProductSceneNameList(BaseHandler):
    def get(self):
        product_id = GetArgumentValue(self, "PID")
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allproductscenebyname = db.QueryProductScenes(product_id, distinctscenename=True)

        allscenenames = []
        for sceneinfo in allproductscenebyname:
            allscenenames.append(sceneinfo[7] if not db.IsDbUseDictCursor() else sceneinfo["scene_name"])

        resultlist = { "result" : "1", "SceneNameList" : allscenenames }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiProductSceneLocationList(BaseHandler):
    def get(self):
        product_id = GetArgumentValue(self, "PID")
        scene_name = GetArgumentValue(self, "SceneName")
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        productinfo = db.QueryProductInfo(product_id)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

        if product_type == 1 or product_type == 4 or product_type == 6 or product_type == 7:
            alllocations = db.QueryProductLocationsInScene(product_id, scene_name)
            
            resultlist = { "result" : "1", "SceneLocationList" : alllocations }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        elif product_type == 3:
            allscenes = db.QueryProductScenes(product_id, distinctscenelocation=True)
            alllocations = []
            for sceneinfo in allscenes:
                alllocations.append(sceneinfo[8] if not db.IsDbUseDictCursor() else sceneinfo["scene_locations"])

            resultlist = { "result" : "1", "SceneLocationList" : alllocations }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
    
class ApiProductSceneTimeperiodList(BaseHandler):
    def get(self):
        product_id = GetArgumentValue(self, "PID")
        scene_name = GetArgumentValue(self, "SceneName")
        scene_locations = GetArgumentValue(self, "SceneLocation")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        productinfo = db.QueryProductInfo(product_id)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

        if product_type == 1 or product_type == 3 or product_type == 4 or product_type == 6 or product_type == 7:
            alltimeperiods = db.QueryProductTimeperiodsInScene(product_id, scene_name, scene_locations)
            
            resultlist = { "result" : "1", "SceneTimeperiodList" : alltimeperiods }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        elif product_type == 2:
            alltimeperiods = db.QueryProductTimeperiodsInScene(product_id, scene_name, None)

            resultlist = { "result" : "1", "SceneTimeperiodList" : alltimeperiods }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
    
class ApiProductSceneQuery(BaseHandler):
    def get(self):
        product_id = GetArgumentValue(self, "PID")
        scene_name = GetArgumentValue(self, "SceneName")
        scene_locations = GetArgumentValue(self, "SceneLocation")
        scene_timeperiod = GetArgumentValue(self, "SceneTimeperiod")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        productinfo = db.QueryProductInfo(product_id)
        product_type = int(productinfo[4] if not db.IsDbUseDictCursor() else productinfo["product_type"])

        if product_type == 1 or product_type == 3 or product_type == 4 or product_type == 6 or product_type == 7:
            allscenes = db.QueryProductOfScene(product_id, scene_name, scene_locations, scene_timeperiod)
            if allscenes is not None and len(allscenes) > 0:
                thescene = allscenes[0]

                resultlist = { "result" : "1", "SceneInfo" : thescene }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        elif product_type == 2:
            allscenes = db.QueryProductOfScene(product_id, scene_name, None, scene_timeperiod)
            if len(allscenes):
                thescene = allscenes[0]
                resultlist = { "result" : "1", "SceneInfo" : thescene }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)

class ApiProductSceneQueryPrice(BaseHandler):
    def get(self):
        product_id = GetArgumentValue(self, "PID")
        scene_name = GetArgumentValue(self, "SceneName")
        scene_locations = GetArgumentValue(self, "SceneLocation")
        scene_timeperiod = GetArgumentValue(self, "SceneTimeperiod")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        product17dongpricelow = db.QueryProduct17dongPrice(product_id, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)
        product17dongpricehigh = db.QueryProduct17dongPrice(product_id, highprice=1, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)
        if product17dongpricelow == product17dongpricehigh:
            if product17dongpricelow is None:
                htmlstr = "¥ 0.00"
            else:
                htmlstr = "¥ %.2f" % float(product17dongpricelow)
        else:
            htmlstr = "¥ %.2f - ¥ %.2f" % ( float(product17dongpricelow), float(product17dongpricehigh) )

        resultlist = { "result" : "1", "ProductPrice" : htmlstr }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserAddressList(BaseHandler):
    def get(self):
        user_id = GetArgumentValue(self, "UID")
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        alluseraddress = db.QueryUserAllAddress(user_id)

        resultlist = { "result" : "1", "AllUserAddress" : alluseraddress }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserAddressQueryInfo(BaseHandler):
    def get(self):
        useraddress_id = GetArgumentValue(self, "AddressID")
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        useraddressinfo = db.QueryAddressInfo(useraddressid=useraddress_id)
        useraddressinfo = [] if useraddressinfo is None else useraddressinfo

        resultlist = { "result" : "1", "AddressInfo" : useraddressinfo }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserTravellerList(BaseHandler):
    def get(self):
        user_id = GetArgumentValue(self, "UID")
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allusertraveller = db.QueryUserAllTraveller(user_id)

        resultlist = { "result" : "1", "AllUserTraveller" : allusertraveller }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiTopicList(BaseHandler):
    def get(self):
        startposition = self.get_argument("startposition", 0)
        count = self.get_argument("count", Settings.LIST_ITEM_PER_PAGE)
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allarticles = db.QueryArticles(startposition, count, frontend=1)

        allupdatedarticles = []
        for articleinfo in allarticles:
            articleinfo = list(articleinfo) if not db.IsDbUseDictCursor() else dict(articleinfo)
            avatarpreview = db.GetArticleAvatarPreview(articleinfo[0] if not db.IsDbUseDictCursor() else articleinfo["articles_id"])[0]
            serveraddress = self.request.headers.get("Host")
            avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
            if not db.IsDbUseDictCursor():
                articleinfo[6] = avatarurl
            else:
                articleinfo["articles_avatar"] = avatarurl
            allupdatedarticles.append(articleinfo)

        resultlist = { "result" : "1", "TopicList" : allupdatedarticles }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiTopicDetail(BaseHandler):
    def get(self):
        topicid = GetArgumentValue(self, "topicid")
        db = DbHelper()
        articleinfo = db.QueryArticleInfo(topicid)

        avatarpreview = db.GetArticleAvatarPreview(articleinfo[0] if not db.IsDbUseDictCursor() else articleinfo["articles_id"])[0]
        serveraddress = self.request.headers.get("Host")
        avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
        if not db.IsDbUseDictCursor():
            articleinfo[6] = avatarurl
        else:
            articleinfo["articles_avatar"] = avatarurl

        resultlist = { "result" : "1", "TopicDetail" : articleinfo }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

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
        message = "欢迎使用一起动，您的验证码为：%s，请尽快使用，动起来，让生活更精彩！" % verifyCode

        if phonenumber:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
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

                        logging.debug("---ApiSendSmsCodeRegistration: %r" % verifyCode)

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
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
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

                    logging.debug("---ApiSendSmsCodeFindpassword: %r" % verifyCode)

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

class ApiCouponUpdate(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        coupon_id = jsondict["CouponID"]
        coupon_valid = jsondict["CouponValid"]
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        couponinfo = db.QueryCouponInfo(coupon_id)
        db.UpdateCouponInfo(coupon_id, { "coupon_valid" : coupon_valid, "coupon_source" : couponinfo[10] if not db.IsDbUseDictCursor() else couponinfo["coupon_source"] })

        resultlist = { "result" : "1" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiCouponList(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        startposition = jsondict["startposition"] if jsondict.has_key("startposition") else 0
        count = jsondict["count"] if jsondict.has_key("count") else Settings.LIST_ITEM_PER_PAGE
        coupontype = jsondict["type"] if jsondict.has_key("type") else 0
        coupontype = int(coupontype)

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        # 全部
        if coupontype == 0:
            updatedcoupons = db.QueryCoupons(startpos=startposition, count=count, userid=user_id, couponvalid=-1, couponexpired=-1)
        # 未使用
        elif coupontype == 1:
            allcoupons = db.QueryCoupons(startpos=startposition, count=count, userid=user_id, couponvalid=1, couponexpired=0)

            updatedcoupons = []
            product_id = jsondict["PID"] if jsondict.has_key("PID") else 0
            if product_id != 0:
                for couponinfo in allcoupons:
                    if db.ValidateProductCoupon(productid=product_id, couponid=couponinfo[0] if not db.IsDbUseDictCursor() else couponinfo["coupon_id"]):
                        updatedcoupons.append(couponinfo)
            else:
                updatedcoupons = allcoupons
        # 已使用
        elif coupontype == 2:
            updatedcoupons = db.QueryCoupons(startpos=startposition, count=count, userid=user_id, couponvalid=0, couponexpired=0)
        # 已过期
        elif coupontype == 3:
            updatedcoupons = db.QueryCoupons(startpos=startposition, count=count, userid=user_id, couponvalid=-1, couponexpired=1)
        else:
            updatedcoupons = None

        if updatedcoupons is None:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            newupdatedcoupons = []
            for couponinfo in updatedcoupons:
                if not db.IsDbUseDictCursor():
                    couponinfo = list(couponinfo)
                    couponinfo[7] = db.GetCouponRestrictionDescription(couponid=couponinfo[0])
                    newupdatedcoupons.append(couponinfo)
                else:
                    couponinfo = dict(couponinfo)
                    couponinfo["coupon_restrictions"] = db.GetCouponRestrictionDescription(couponid=couponinfo[0] if not db.IsDbUseDictCursor() else couponinfo["coupon_id"])
                    newupdatedcoupons.append(couponinfo)

            resultlist = { "result" : "1", "AllCoupons" : newupdatedcoupons }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiCouponUserDraw(XsrfBaseHandler):
    def post(self):
        '''用户主动领取某个商品的优惠券
        '''
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        product_id = jsondict["PID"]

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        producthascoupon = db.IsProductHasCoupon(product_id)
        if producthascoupon:
            productinfo = db.QueryProductInfo(product_id)
            if not db.IsDbUseDictCursor():
                product_coupons = float(productinfo[33]) if productinfo[33] is not None else 0
            else:
                product_coupons = float(productinfo["product_couponwhenorder"]) if productinfo["product_couponwhenorder"] is not None else 0
            if product_coupons > 0:
                userhasgetcoupon = db.IsUserGetSpecificCoupon(userid=user_id, productid=product_id, activityid=None)
                if userhasgetcoupon:
                    resultlist = { "result" : "0" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)
                else:
                    restriction = json.dumps({ "RestrictionType" : 4, "ProductID" : (int(product_id),) })
                    couponsource = int("1%s" % int(product_id))
                    if not db.IsDbUseDictCursor():
                        validdays = int(productinfo[34]) if productinfo[34] is not None else 30
                    else:
                        validdays = int(productinfo["product_couponwhenactivate"]) if productinfo["product_couponwhenactivate"] is not None else 30
                    validdays = validdays if validdays > 0 else 30
                    db.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : product_coupons, "coupon_restrictions" : restriction, "coupon_source" : couponsource }, couponvaliddays=validdays)

                    resultlist = { "result" : "1" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)
            else:
                resultlist = { "result" : "-1" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
        else:
            resultlist = { "result" : "-2" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)

class ApiCouponUserDrawDetect(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        product_id = jsondict["PID"]

        if int(user_id) == 0:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            return self.write(jsonstr)
        else:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            userhasgetcoupon = db.IsUserGetSpecificCoupon(userid=user_id, productid=product_id, activityid=None)
            if userhasgetcoupon:
                resultlist = { "result" : "1" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)
            else:
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

class ApiProductPaymentProcess(BaseHandler):
    def get(self):
        product_type = GetArgumentValue(self, "ProductType")
        product_type = int(product_type) if product_type is not None else 0
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)

        onserver = (socket.gethostname() == Settings.SERVER_HOST_NAME)
        if product_type == 1 or product_type == 7:
            # 体育培训
            articleinfo = db.QueryArticleInfo(articlesid=237 if onserver else 6)
        elif product_type == 2:
            # 体育旅游
            articleinfo = db.QueryArticleInfo(articlesid=238 if onserver else 7)
        elif product_type == 3:
            # 课程体验
            articleinfo = db.QueryArticleInfo(articlesid=237 if onserver else 3)
        elif product_type == 4:
            # 精彩活动
            articleinfo = db.QueryArticleInfo(articlesid=240 if onserver else 6)
        elif product_type == 5:
            # 积分商城
            articleinfo = db.QueryArticleInfo(articlesid=237 if onserver else 6)
        elif product_type == 6:
            # 私人教练
            articleinfo = db.QueryArticleInfo(articlesid=239 if onserver else 9)
        else:
            articleinfo = None

        if articleinfo is None:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            paymentprocess = articleinfo[3] if not db.IsDbUseDictCursor() else articleinfo["articles_content"]

            resultlist = { "result" : "1", "PaymentProcess" : paymentprocess }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiUserOrderList(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        startposition = jsondict["startposition"] if jsondict.has_key("startposition") else 0
        count = jsondict["count"] if jsondict.has_key("count") else Settings.LIST_ITEM_PER_PAGE
        ordertype = jsondict["type"] if jsondict.has_key("type") else 2
        ordertype = int(ordertype)

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        paymentstatus = -1 if ordertype == 2 or ordertype == 5 else ordertype
        producttype   =  5 if ordertype == 5 else 0
        alluserorders = db.QueryPreorders(startposition, count, productvendorid=0, userid=user_id, producttype=producttype, paymentstatus=paymentstatus)

        allupdatedorders = []
        for orderinfo in alluserorders:
            if not db.IsDbUseDictCursor():
                orderinfo = list(orderinfo)
                avatarpreview = db.GetProductAvatarPreview(orderinfo[2])[0]
                serveraddress = self.request.headers.get("Host")
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                productinfo = db.QueryProductInfo(orderinfo[2])
                productname = productinfo[2]
                orderinfo.append(avatarurl)
                orderinfo.append(productname)
                allupdatedorders.append(orderinfo)
            else:
                orderinfo = dict(orderinfo)
                avatarpreview = db.GetProductAvatarPreview(orderinfo["preorder_productid"])[0]
                serveraddress = self.request.headers.get("Host")
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                productinfo = db.QueryProductInfo(orderinfo["preorder_productid"])
                productname = productinfo["product_name"]
                orderinfo["avatarurl"] = avatarurl
                orderinfo["productname"] = productname
                allupdatedorders.append(orderinfo)

        resultlist = { "result" : "1", "OrderList" : allupdatedorders }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiProductWintercampList(BaseHandler):
    def get(self):
        startposition = int(self.get_argument("startposition", 0))
        count = int(self.get_argument("count", Settings.LIST_ITEM_PER_PAGE))
        sort = int(self.get_argument("sort", 0))

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allproducts = db.QueryFilteredProducts(trainingitem=None, trainingplace=None, trainingage=None, trainingvendor=None, 
            startpos=startposition, count=count, producttype=7, sort=sort)

        serveraddress = self.request.headers.get("Host")
        updatedproducts = []
        for oneproduct in allproducts:
            productid = oneproduct[0] if not db.IsDbUseDictCursor() else oneproduct["product_id"]
            if not db.IsDbUseDictCursor():
                oneproduct = list(oneproduct)
                (avatarpreview, hascustom) = db.GetProductAvatarPreview(oneproduct[0])
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                oneproduct[5] = avatarurl
            else:
                oneproduct = dict(oneproduct)
                (avatarpreview, hascustom) = db.GetProductAvatarPreview(oneproduct["product_id"])
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                oneproduct["product_avatar"] = avatarurl
            
            productmarketprice = db.QueryProductMarketPrice(productid)
            product17dongprice = db.QueryProduct17dongPrice(productid)
            producthascoupon = db.IsProductHasCoupon(productid)
            producthaspromotion = db.IsProductHasPromotion(productid)
            productpoints = db.GetProductCommentScore(productid)
            # All product avatars
            productavatars = db.GetProductAvatarPreviews(productid)
            productavatars = [("http://%s%s" % (serveraddress, a[0])) for a in productavatars]

            if not db.IsDbUseDictCursor():
                oneproduct.append(productmarketprice)
                oneproduct.append(product17dongprice)
                oneproduct.append(producthascoupon)
                oneproduct.append(producthaspromotion)
                oneproduct.append(productpoints)
                oneproduct.append(productavatars)
            else:
                oneproduct["productmarketprice"] = productmarketprice
                oneproduct["product17dongprice"] = product17dongprice
                oneproduct["producthascoupon"] = producthascoupon
                oneproduct["producthaspromotion"] = producthaspromotion
                oneproduct["productpoints"] = productpoints
                oneproduct["productavatars"] = productavatars
            updatedproducts.append(oneproduct)

        resultlist = { "result" : "1", "ProductList" : updatedproducts }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiOrderFinish(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        OutTradeNO = jsondict["OutTradeNO"]
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        orderinfo = db.QueryPreorderInfoByOutTradeNo(OutTradeNO)
        if orderinfo is None:
            resultlist = { "result" : "0", "errormsg" : "订单不存在" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            productinfo = db.QueryProductInfo(orderinfo[2] if not db.IsDbUseDictCursor() else orderinfo["preorder_productid"])
            counts = orderinfo[8] if not db.IsDbUseDictCursor() else orderinfo["preorder_counts"]
            try:
                counts = int(counts)
            except Exception, e:
                counts = 1

            # -------------------------------------------------------------------------
            # 限购商品处理流程
            product_purchaselimit = productinfo[39] if not db.IsDbUseDictCursor() else productinfo["product_purchaselimit"]
            preorder_userid = orderinfo[1] if not db.IsDbUseDictCursor() else orderinfo["preorder_userid"]
            preorder_productid = orderinfo[2] if not db.IsDbUseDictCursor() else orderinfo["preorder_productid"]
            userbuyproductcounts  = db.QueryUserBuyProductCounts(preorder_userid, preorder_productid)
            if product_purchaselimit is not None and int(product_purchaselimit) > 0 and int(userbuyproductcounts) + int(counts) > int(product_purchaselimit):
                errormsg = "非常抱歉，此商品每人限购 %s 份，您已购买 %s 份，本次无法购买 %s 份。" % (product_purchaselimit, userbuyproductcounts, counts)
                resultlist = { "result" : "0", "errormsg" : errormsg }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 商品库存检测
            preorder_sceneid = orderinfo[11] if not db.IsDbUseDictCursor() else orderinfo["preorder_sceneid"]
            sceneinfo = db.QuerySceneInfo(preorder_sceneid)
            instock = (sceneinfo[4] if sceneinfo is not None else 0) if not db.isdict() else sceneinfo["scene_maxpeople"]
            if instock is not None:
                if counts > int(instock):
                    errormsg = "非常抱歉，此商品对应场次的库存为 %s，您本次无法购买 %s 份。" % (instock, counts)
                    resultlist = { "result" : "0", "errormsg" : errormsg }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 秒杀商品有效性检测
            isseckillproduct = True if productinfo['productseckill'] == 1 else False
            seckillproductstatus = productinfo['productseckillstatus']
            if isseckillproduct == True:
                if seckillproductstatus != "underway":
                    errormsg = "非常抱歉，此商品不在秒杀期内，您本次无法购买。"
                    resultlist = { "result" : "0", "errormsg" : errormsg }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    return self.write(jsonstr)

            # -------------------------------------------------------------------------
            # 联系人信息检测
            preorder_contacts = db.getDictValue(orderinfo, "preorder_contacts", 23)
            preorder_contactsphonenumber = db.getDictValue(orderinfo, "preorder_contactsphonenumber", 24)
            if preorder_contacts == "" or preorder_contactsphonenumber == "":
                errormsg = "非常抱歉，无法提交订单，请填写订单联系人信息。"
                resultlist = { "result" : "0", "errormsg" : errormsg }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                return self.write(jsonstr)

            # -------------------------------------------------------------------------

            preorder_fullprice = int(orderinfo[10] if not db.IsDbUseDictCursor() else orderinfo["preorder_fullprice"])
            if preorder_fullprice != 0:
                resultlist = { "result" : "0", "errormsg" : "订单价格不为0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                paymentstatus = int(orderinfo[12] if not db.IsDbUseDictCursor() else orderinfo["preorder_paymentstatus"])
                if paymentstatus == 0:
                    UpdateOrderStatusWhenPaymentSuccess(self, orderinfo)

                    resultlist = { "result" : "1" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)
                else:
                    resultlist = { "result" : "0", "errormsg" : "订单已完成，无法重复创建订单" }
                    jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                    self.set_header('Content-Type','application/json')
                    self.write(jsonstr)

class ApiSearchkeywordsList(BaseHandler):
    def get(self):
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allsearchkeyword = db.QuerySearchkeywords(startpos=0, count=10, frontend=1)

        resultlist = { "result" : "1", "KeywordList" : allsearchkeyword }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiVoteDetail(BaseHandler):
    def get(self):
        voteid = int(self.get_argument("VID", 0))
        user_id = int(self.get_argument("UID", 0))
        serveraddress = self.request.headers.get("Host")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        onevote = db.QueryVoteInfo(voteid)
        onevote = list(onevote) if not db.IsDbUseDictCursor() else dict(onevote)
        (avatarpreview, hascustom) = db.GetVoteAvatarPreview(onevote[0] if not db.IsDbUseDictCursor() else onevote["vote_id"])
        avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
        if notdb.IsDbUseDictCursor():
            onevote[10] = avatarurl
        else:
            onevote["vote_reserve1"] = avatarurl

        useralreadyvoted = 1 if db.IsUserVotedVote(user_id, onevote[0] if not db.IsDbUseDictCursor() else onevote["vote_id"]) else 0
        totalvotetimes = db.QueryVoteTimesForVote(voteid=onevote[0] if not db.IsDbUseDictCursor() else onevote["vote_id"])
        onevote.append(useralreadyvoted)
        onevote.append(totalvotetimes)

        resultlist = { "result" : "1", "VoteDetail" : onevote }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiVoteList(BaseHandler):
    def get(self):
        startposition = int(self.get_argument("startposition", 0))
        count = int(self.get_argument("count", Settings.LIST_ITEM_PER_PAGE))
        user_id = int(self.get_argument("UID", 0))

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allvote = db.QueryVotes(startpos=startposition, count=count, frontend=1)

        serveraddress = self.request.headers.get("Host")
        updatedvotes = []
        for onevote in allvote:
            if not db.IsDbUseDictCursor():
                onevote = list(onevote)
                (avatarpreview, hascustom) = db.GetVoteAvatarPreview(onevote[0])
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                onevote[10] = avatarurl
            else:
                onevote = dict(onevote)
                (avatarpreview, hascustom) = db.GetVoteAvatarPreview(onevote["vote_id"])
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                onevote["vote_reserve1"] = avatarurl

            voteid = onevote[0] if not db.IsDbUseDictCursor() else onevote["vote_id"]
            useralreadyvoted = 1 if db.IsUserVotedVote(user_id, voteid) else 0
            totalvotetimes = db.QueryVoteTimesForVote(voteid=voteid)

            if not db.IsDbUseDictCursor():
                onevote.append(useralreadyvoted)
                onevote.append(totalvotetimes)
            else:
                onevote["useralreadyvoted"] = useralreadyvoted
                onevote["totalvotetimes"] = totalvotetimes

            updatedvotes.append(onevote)

        resultlist = { "result" : "1", "VoteList" : updatedvotes }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserVoteList(BaseHandler):
    def get(self):
        if IsArgumentEmpty(self, "UID"):
            user_id = 0
        else:
            user_id = int(self.get_argument("UID", 0))
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allvote = db.QueryAllUserVotes(userid=user_id)

        serveraddress = self.request.headers.get("Host")
        updatedvotes = []
        for onevote in allvote:
            voteid = onevote[0] if not db.IsDbUseDictCursor() else onevote["vote_id"]

            if not db.IsDbUseDictCursor():
                onevote = list(onevote)
                (avatarpreview, hascustom) = db.GetVoteAvatarPreview(voteid)
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                onevote[10] = avatarurl
            else:
                onevote = dict(onevote)
                (avatarpreview, hascustom) = db.GetVoteAvatarPreview(voteid)
                avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
                onevote["vote_reserve1"] = avatarurl

            useralreadyvoted = 1 if db.IsUserVotedVote(user_id, voteid) else 0
            totalvotetimes = db.QueryVoteTimesForVote(voteid=voteid)

            if not db.IsDbUseDictCursor():
                onevote.append(useralreadyvoted)
                onevote.append(totalvotetimes)
            else:
                onevote["useralreadyvoted"] = useralreadyvoted
                onevote["totalvotetimes"] = totalvotetimes

            updatedvotes.append(onevote)

        resultlist = { "result" : "1", "AllUserVotes" : updatedvotes }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiVoteOptionDetail(BaseHandler):
    def get(self):
        user_id = int(self.get_argument("UID", 0))
        voteoptionid = int(self.get_argument("VoptID", 0))

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        onevoteoption = db.QueryVoteOptionInfo(voteoptionid=voteoptionid)
        onevoteoption = list(onevoteoption) if not db.IsDbUseDictCursor() else dict(onevoteoption)

        voteoptionid = onevoteoption[0] if not db.IsDbUseDictCursor() else onevoteoption["vote_option_id"]
        serveraddress = self.request.headers.get("Host")
        aps = db.GetVoteOptionPreviews(voteoptionid)
        avatarlist = []
        for avatar, uniquestring, iscustom in aps:
            avatarurl = "http://%s%s" % (serveraddress, avatar)
            avatarlist.append(avatarurl)
        if not db.IsDbUseDictCursor():
            onevoteoption[5] = avatarlist
        else:
            onevoteoption["vote_option_avatar"] = avatarlist

        useralreadyvoted = 1 if db.IsUserVotedVoteOption(user_id, voteoptionid) else 0
        totalvotetimes = db.QueryVoteTimesForVoteOption(voteoptionid)

        if not db.IsDbUseDictCursor():
            onevoteoption.append(useralreadyvoted)
            onevoteoption.append(totalvotetimes)
        else:
            onevoteoption["useralreadyvoted"] = useralreadyvoted
            onevoteoption["totalvotetimes"] = totalvotetimes

        resultlist = { "result" : "1", "VoteOptionDetail" : onevoteoption }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)
    
class ApiVoteOptionList(BaseHandler):
    def get(self):
        vote_id = int(self.get_argument("VID", 0))
        startposition = int(self.get_argument("startposition", 0))
        count = int(self.get_argument("count", Settings.LIST_ITEM_PER_PAGE))
        if IsArgumentEmpty(self, "UID"):
            user_id = 0
        else:
            user_id = int(self.get_argument("UID", 0))

        if vote_id == 0:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            allvoteoption = db.QueryVoteOptions(voteid=vote_id, startpos=startposition, count=count, status=1)

            serveraddress = self.request.headers.get("Host")
            updatedvoteoptions = []
            for onevoteoption in allvoteoption:
                onevoteoption = list(onevoteoption) if not db.IsDbUseDictCursor() else dict(onevoteoption)
                avatarlist = []

                voteoptionid = onevoteoption[0] if not db.IsDbUseDictCursor() else onevoteoption["vote_option_id"]
                aps = db.GetVoteOptionPreviews(voteoptionid)
                for avatar, uniquestring, iscustom in aps:
                    avatarurl = "http://%s%s" % (serveraddress, avatar)
                    avatarlist.append(avatarurl)
                if not db.IsDbUseDictCursor():
                    onevoteoption[5] = avatarlist
                else:
                    onevoteoption["vote_option_avatar"] = avatarlist

                useralreadyvoted = 1 if db.IsUserVotedVoteOption(user_id, voteoptionid) else 0
                totalvotetimes = db.QueryVoteTimesForVoteOption(voteoptionid)

                if not db.IsDbUseDictCursor():
                    onevoteoption.append(useralreadyvoted)
                    onevoteoption.append(totalvotetimes)
                else:
                    onevoteoption["useralreadyvoted"] = useralreadyvoted
                    onevoteoption["totalvotetimes"] = totalvotetimes

                updatedvoteoptions.append(onevoteoption)

            resultlist = { "result" : "1", "VoteOptionList" : updatedvoteoptions }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiVoteOptionVote(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        voteoptionid = jsondict["VoteOptionID"]
        voteoptionidlist = json.loads(voteoptionid)
        
        haserror = False
        try:
            user_id = int(user_id)
        except Exception, e:
            haserror = True

        if haserror == True:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            ret = db.VoteForOption(userid=user_id, voteoptionid=voteoptionidlist[0])
            resultlist = { "result" : "%s" % ret }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiVoteOptionUpload(XsrfBaseHandler):
    def post(self):
        ''' 个人用户提交投票选项信息
        '''
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        user_id = self.get_argument("UID")
        vote_id = self.get_argument("VoteID")
        voteoption_title = self.get_argument("VoteOptionTitle")
        voteoption_description = self.get_argument("VoteOptionDescription")

        logging.debug("ApiVoteOptionUpload: UID: %r, vote_id: %r, voteoption_title: %r, voteoption_description: %r" % (user_id, vote_id, voteoption_title, voteoption_description))

        voteoption_id = db.AddVoteOption(voteoptioninfo={ "vote_option_voteid" : vote_id, "vote_option_title" : voteoption_title, "vote_option_description" : voteoption_description, 
            "vote_option_sortweight" : 0, "vote_option_video" : None, "vote_option_reserve1" : user_id, "vote_option_reserve2" : 0 })

        # 保存图片信息
        if self.request.files.has_key('myfile'):
            voteoption_avatar = []
            # 包含图片信息
            uploadedfiles = self.request.files['myfile']

            logging.debug("uploadedfiles count: %r" % len(uploadedfiles))

            for i in range(len(uploadedfiles)):
                # ////////////////
                uploadedfile = uploadedfiles[i]
                original_fname = uploadedfile['filename']
                extension = os.path.splitext(original_fname)[1]
                fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
                fname = "%s%s" % (fname, getuniquestring())
                filename = fname + extension

                filedir = os.path.join(abspath, 'static/img/avatar/temp')
                infile = filedir + '/' + filename # infile就是用户上传的原始照片

                # 自动保存用户上传的照片文件
                output_file = open(infile, 'w')
                output_file.write(uploadedfile['body'])
                output_file.close()

                # 将 infile 保存为 jpeg 格式的商品图片
                im = Image.open(infile)
                maxwidth = 600
                avatar_size = (maxwidth if im.size[0] > maxwidth else im.size[0], maxwidth * im.size[1] / im.size[0] if im.size[0] > maxwidth else im.size[1])
                
                new_unique_string = getuniquestring()
                votedir = os.path.join(abspath, 'static/img/avatar/vote')
                outfile = votedir + '/P%s_%s.jpeg' % (voteoption_id, new_unique_string)

                method = Image.NEAREST if im.size == avatar_size else Image.ANTIALIAS
                formatted_im = ImageOps.fit(im, avatar_size, method = method, centering = (0.5,0.5))
                formatted_im.save(outfile, "JPEG", quality=100)

                # 删除用户上传的原始文件infile
                os.remove(infile)

                voteoption_avatar.append(new_unique_string)
                # ////////////////
            db.UpdateVoteOptionInfo(voteoptionid=voteoption_id, voteoptioninfo={"vote_option_avatar" : json.dumps(voteoption_avatar)})

        resultlist = { "result" : "1" }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiMessageList(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)

        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        startposition = jsondict["startposition"] if jsondict.has_key("startposition") else 0
        count = 0 #jsondict["count"] if jsondict.has_key("count") else Settings.LIST_ITEM_PER_PAGE
        messagetype = jsondict['type'] if jsondict.has_key("type") else 0
        
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        if startposition == 0:
            allmessages = db.QueryMessages(userid=user_id, frontend=1, messagetype=messagetype)
        else:
            allmessages = []

        resultlist = { "result" : "1", "MessageList" : allmessages }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiMessageDetail(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        message_id = jsondict["MessageID"]
        
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        messageinfo = db.QueryMessageInfo(messageid=message_id)

        resultlist = { "result" : "1", "MessageDetail" : messageinfo }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiDeleteCoupon(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        coupon_id = jsondict["CouponID"]

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)

        couponinfo = db.QueryCouponInfo(coupon_id)
        if int(user_id) == int(couponinfo[1] if not db.IsDbUseDictCursor() else couponinfo["coupon_userid"]):
            db.DeleteCoupon(coupon_id)

            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiDeleteMessage(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        message_id = jsondict["MessageID"]

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)

        userhasmessage = False
        msgs = db.QueryMessages(userid=user_id, frontend=1)
        for messageinfo in msgs:
            if int(message_id) == int(messageinfo[0] if not db.IsDbUseDictCursor() else messageinfo["message_id"]):
                userhasmessage = True
                break

        if userhasmessage:
            db.DeleteMessage(message_id)

            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
    
class ApiDeleteOrder(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        order_id = jsondict["OrderID"]

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)

        orderinfo = db.QueryPreorderInfo(order_id)
        if int(user_id) == int(orderinfo[1] if not db.IsDbUseDictCursor() else orderinfo["preorder_userid"]):
            db.DeletePreorder(order_id)

            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
    
class ApiOrderRefund(XsrfBaseHandler):
    def post(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        preorder_id = jsondict["OrderID"]
        refundReason = GetArgumentValue(self, "refundReason")

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        orderinfo = db.QueryPreorderInfo(preorder_id)
        order_paymentstatus = int(orderinfo[12] if not db.IsDbUseDictCursor() else orderinfo["preorder_paymentstatus"])
        if order_paymentstatus == 1:
            db.UpdatePreorderInfo(preorder_id, { "preorder_appraisal" : refundReason, "preorder_refundstatus" : 2 })

            resultlist = { "result" : "1" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class AlipayBatchrefund(XsrfBaseHandler):

    def response(self, res):
        jsonstr = json.dumps(res, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        return self.write(jsonstr)

    def check_xsrf_cookie(self):
        pass

    @staticmethod
    def extract_params(dictobj, keys=[]):
        return [dictobj.get(k) for k in keys]

    @staticmethod
    def make_detail_data(outtradeno, outrefundfee, outrefundreason):
        """
        Method to make 'detail_data' for AlipayRefund
        2011011201037066^5.00^协商退款
        1. detail_data中的退款笔数总和要等于参数batch_num的值；
        2.“退款理由”长度不能大于256字节，“退款理由”中不能有“^”、“|”、“$”、“#”等影响detail_data格式的特殊字符；
        3. detail_data中退款总金额不能大于交易总金额；
        4. 一笔交易可以多次退款，退款次数最多不能超过99次，需要遵守多次退款的总金额不超过该笔交易付款金
        format: 2011011201037066^5.00^协商退款  outtradeno^outrefundfee^outrefundreason
        """
        return '^'.join(str(i) for i in [outtradeno, outrefundfee, outrefundreason])

    def make_data_set(self, order_list):
        _set = set()
        params = ['preorder_fullprice', 'out_refund_fee', 'preorder_tradeno','out_refund_reason']
        for (fullprice, orf, tradeno, reason) in [self.extract_params(r, params) for r in order_list]:
            orf = orf if (0 < orf < fullprice) else fullprice
            _set.add(self.make_detail_data(tradeno, orf, reason))
        return '#'.join(_set)
        # return ('2015112721001004760297869589' + '^' + '0.01' + '^' + 'reason').decode('utf-8')

    def post(self):
        """
        HTTP 头：{"json" : [
                  { "UID" : xxx, "OrderID" : xxx, "Fee":xx  },
                  { "UID" : xxx, "OrderID" : xxx, "Fee":xx  }]
                }
        "UID"      - 用户ID，必选
        "OrderID"      - 订单ID，必选
        "Fee"       - 退款金额, 可选, 默认为支付金额
        POST 链接参数： 
        "refundReason" - 退款原因，可选
        """
        jsondata = self.request.headers.get("json", None)
        refundReason = GetArgumentValue(self, "refundReason")
        if jsondata is None:
            self.send_error(404)
        else:
            refund_list = json.loads(jsondata)
        # ==========
        refund_values = []
        for r in refund_list:
            ls = []
            ls.append(r['UID'])
            ls.append(r['OrderID'])
            ls.append(r.pop('Fee', None) or None)
            refund_values.append(tuple(ls))

        # ==========
        # validate 
        db = DbHelper(cursorclass=Settings.DB_DICTCURSOR)
        alipay_order_list = []
        for uid, orderid, fee in refund_values:
            orderinfo = db.QueryPreorderInfo(orderid)
            if orderinfo is None:
                return self.response({'result':0, 'msg':'invalid orderid %r' % orderid})
            elif orderinfo['preorder_userid'] != int(uid): 
                # check if uid match orderinfo 
                return self.response({'result':0, 'msg':'uid does not match %r' % orderid})
            elif orderinfo['preorder_paymentstatus'] != 1:
                # check paymentstatus 
                return self.response({'result':0, 'msg':'unpaid order %r' % orderid})
            elif orderinfo['preorder_refundstatus'] in (1, 2):
                # if encounters refunded, refunding order then skip
                continue
            else:
                ppd = orderinfo['preorder_paymentmethod']
                payby_dict = json.loads(ppd or '{"S":0,"P":0}')
                orderinfo['S'], orderinfo['P'] = int(payby_dict['S']), int(payby_dict['P'])
                orderinfo['out_refund_fee'] = fee
                orderinfo['out_refund_reason'] = refundReason or 'none-reason'
                # ==================================================
                # P: web 0 ios 1 android 2
                # S: 支付宝 - 0 网银 - 1 快捷支付 - 2 微信 -3
                # ==================================================
                if orderinfo['S'] == 0 and orderinfo not in alipay_order_list:
                    alipay_order_list.append(orderinfo)
        # ==============================
        # web, alipay
        # PS: Remote Api Async Response
        # ==============================
        batchNum = len(alipay_order_list)
        batchNO = db.CreateBatchNO()
        if batchNum > 0:
            refund = refundnotify.Refund()
            refund.data.update(dict(
                partner=Settings.ALIPAY['PID'],
                seller_email=Settings.ALIPAY['EMAIL'],
                # seller_user_id
                refund_date=DateTime.strftime(DateTime.now(),'%Y-%m-%d %H:%M:%S'),
                batch_no=batchNO,
                batch_num=batchNum,
                detail_data=self.make_data_set(alipay_order_list)
            ))
            refund.do_sign(Settings.ALIPAY['KEY'])
            for o in alipay_order_list:
                theid = o['preorder_id']
                db.UpdatePreorderInfo(theid, {"preorder_outrefundno": batchNO, "preorder_appraisal" : refundReason})
            self.redirect(refund.get_url())
        else:
            self.send_error(404)

class ApiAlipayBatchrefundQuery(XsrfBaseHandler):
    pass

class AlipayBatchrefundNotify(XsrfBaseHandler):

    def post(self):
        if len(self.request.arguments) > 0:
            notifyId = self.get_argument('notify_id', None) or None
            logging.info('====================[notify_id]=%r' % notifyId)
            if notifyId is not None:
                veryfy_url = Settings.ALIPAY["ALIPAY_TRANSPORT"] == "https" and Settings.ALIPAY["ALIPAY_HTTPS_VERIFY_URL"] or Settings.ALIPAY["ALIPAY_HTTP_VERIFY_URL"]
                veryfy_url += "partner=" + Settings.ALIPAY["PID"] + "&notify_id=" + notifyId
                logging.info('====================[veryfy_url]=%r' % veryfy_url)
                response = urllib2.urlopen(veryfy_url, timeout=120000)
                responseTxt = response.read()
                logging.info('====================[responseTxt]=%r' % responseTxt)
                # responseTxt = 'true'
                if responseTxt == 'true':
                    db = DbHelper()
                    batchNO = self.get_argument('batch_no', 0)

                    logging.info('====================[batchNO]=%r' % batchNO)

                    successNum = self.get_argument('success_num', 0)
                    
                    logging.info('====================[successNum]=%r' % successNum)

                    preorders = db.QueryPreorders(0, 0, outrefundno=batchNO)

                    logging.info('====================[preorders]=%r' % preorders)
                    
                    length = len(preorders)

                    if length > 0:
                        for o in preorders:
                            theid = o['preorder_id']
                            db.UpdatePreorderInfo(theid, {'preorder_refundstatus': 1})
                        else:
                            self.write('success')
                    elif length == 0:
                        self.write('fail: no preorder matching the batch_no')
                else:
                    self.write('fail: verify notify is false')
            else:
                self.write('fail: missing notifyid')
        else:
            self.write('fail: no arguments')


    def check_xsrf_cookie(self):
        pass

class ApiWeixinBatchrefund(XsrfBaseHandler):
    '''
    批量申请退款接口,指:
    提交退款申请,无法获悉退款金额是否到帐,
    是否到账通过请求[退款查询接口]查询,同时更新相应批次订单的退款状态
    '''
    def response(self, res):
        jsonstr = json.dumps(res, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        return self.write(jsonstr)
    def check_xsrf_cookie(self):
        pass

    def post(self):
        jsondata = self.request.headers.get("json", None)
        refundReason = GetArgumentValue(self, "refundReason")
        if jsondata is None:
            self.send_error(403)
        else:
            refund_list = json.loads(jsondata)
        refund_values = []
        for r in refund_list:
            ls = []
            ls.append(r['UID'])
            ls.append(r['OrderID'])
            ls.append(r.pop('Fee', None) or None)
            refund_values.append(tuple(ls))
        # ==========
        # validate 
        db = DbHelper(cursorclass=Settings.DB_DICTCURSOR)
        weixin_order_list = []
        for uid, orderid, fee in refund_values:
            orderinfo = db.QueryPreorderInfo(orderid)
            if orderinfo is None:
                return self.response({'result':0, 'msg':'invalid orderid %r' % orderid})
            elif orderinfo['preorder_userid'] != int(uid): 
                # check if uid match orderinfo 
                return self.response({'result':0, 'msg':'uid does not match %r' % orderid})
            elif orderinfo['preorder_paymentstatus'] != 1:
                # check paymentstatus 
                return self.response({'result':0, 'msg':'unpaid order %r' % orderid})
            elif orderinfo['preorder_refundstatus'] in (1, 2):
                # if encounters refunded, refunding order then skip
                continue
            else:
                ppd = orderinfo['preorder_paymentmethod']
                payby_dict = json.loads(ppd or '{"S":3,"P":0}')
                orderinfo['S'], orderinfo['P'] = int(payby_dict['S']), int(payby_dict['P'])
                orderinfo['out_refund_fee'] = fee
                # ==================================================
                # P: web 0 ios 1 android 2
                # S: 支付宝 - 0 网银 - 1 快捷支付 - 2 微信 -3
                # ==================================================
                if orderinfo['S'] == 3 and orderinfo not in weixin_order_list:
                    weixin_order_list.append(orderinfo)
        # ==========================================================================================
        # web weixin
        # the remote api unsupports to [Batch Refund]
        # if have many orders to refund , requests the remote api by 'one-refund one-calling'
        # api required parameters:
        #   "out_trade_no", "out_refund_no", "total_fee", "refund_f
        # ==========================================================================================
        weixin_response_list = []
        for o in weixin_order_list:
            theid = o['preorder_id']
            fullprice  = o['preorder_fullprice']
            # fullprice = 0.01
            orf = o['out_refund_fee']
            otn  = o['preorder_outtradeno']
            # otn = '1970015012'

            outrefundno = o['preorder_outrefundno']
            out_refund_no = db.CreateOutRefundNO() # !!! unique outrefund number
            total_fee = int(fullprice*100) # converts from 'yuan' to 'fen'
            refund_fee = orf if (0 < orf < total_fee) else total_fee # defaults to total_fee
            refundClient = wzhifuSDK.Refund_pub()
            refundClient.setParameter('out_trade_no', str(otn))
            refundClient.setParameter('out_refund_no', outrefundno or out_refund_no)
            refundClient.setParameter('total_fee', str(total_fee))
            refundClient.setParameter('refund_fee', str(refund_fee))
            refundClient.setParameter('op_user_id', Settings.WX_MCHID)
            response = refundClient.getResult()
            if outrefundno is None:
                db.UpdatePreorderInfo(theid, {"preorder_outrefundno": out_refund_no, "preorder_appraisal" : refundReason})
            if response['return_code'] == 'SUCCESS' and response['result_code'] == 'SUCCESS':
                db.UpdatePreorderInfo(theid, {"preorder_refundstatus":2})          
            response['order_id'] = theid
            weixin_response_list.append(response)  
        self.response({'result':1, 'response_list': weixin_response_list})
        # "cash_refund_fee": "1",
        # "coupon_refund_fee": "0",
        # "cash_fee": "1",
        # "refund_id": "2006880303201511300089556816",
        # "coupon_refund_count": "0",
        # "refund_channel": null,
        # "nonce_str": "VNgA75OCxAn455fr",
        # "return_code": "SUCCESS",
        # "return_msg": "OK",
        # "sign": "EA557F5871C0A5CDA94F83154CFF8376",
        # "mch_id": "1237581002",
        # "out_trade_no": "1970015012",
        # "transaction_id": "1006880303201511301835441843",
        # "total_fee": "1",
        # "appid": "wx75e720a9c37aa258",
        # "out_refund_no": "20151130433",
        # "refund_fee": "1",
        # "result_code": "SUCCESS"


class ApiWeixinRefundquery(XsrfBaseHandler):
    def check_xsrf_cookie(self):
        pass
    def post(self):
        refund_id = GetArgumentValue(self,'refund_id')
        order_id = GetArgumentValue(self,'order_id')
        if order_id is None:
            raise tornado.web.HTTPError(403)
        else:
            refundqueryClient = wzhifuSDK.RefundQuery_pub()    
            db = DbHelper()
            if refund_id is None:
                orderinfo = db.QueryPreorderInfo(order_id)
                if orderinfo is None:
                    return self.write('no such order_id %r' % order_id)
                elif not orderinfo['preorder_outrefundno']:
                    return self.write('preorder of id %r without out_trade_no' % order_id)
                else:
                    refundqueryClient.setParameter('out_refund_no', orderinfo['preorder_outrefundno'])
            else:
                refundqueryClient.setParameter('refund_id', refund_id)
            result = refundqueryClient.getResult()
            if result['return_code'] == 'SUCCESS' and result["result_code"]=='SUCCESS' and result['refund_status_0']=='SUCCESS':
                db.UpdatePreorderInfo(order_id,{"preorder_refundstatus":1})

            response = {'result':1, 'refund_details':result}
            # "total_fee": "1",
            # "refund_id_0": "2006880303201511300089556816",
            # "refund_status_0": "PROCESSING",
            # "refund_channel_0": "ORIGINAL",
            # "nonce_str": "14KX9CukcuL7mLeu",
            # "refund_fee_0": "1",
            # "return_msg": "OK",
            # "return_code": "SUCCESS",
            # "mch_id": "1237581002",
            # "out_trade_no": "1970015012",
            # "transaction_id": "1006880303201511301835441843",
            # "refund_count": "1",
            # "appid": "wx75e720a9c37aa258",
            # "out_refund_no_0": "20151130433",
            # "cash_fee": "1",
            # "refund_fee": "1",
            # "result_code": "SUCCESS",
            # "sign": "0BFB0938A150D7F14ED0028F6288C1FD"                

        jsonstr = json.dumps(response, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)            


############################################################################################################################################################################################

class ApiPromotionDraw(BaseHandler):
    def get(self):
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)

        user_id = jsondict["UID"]
        promotion_id = jsondict["promotion_id"]
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        result = db.PromotionDraw(promotion_id, user_id)
        jsonstr = json.dumps(result, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type', 'application/json')
        self.write(jsonstr)

class ApiCompetitionList(BaseHandler):
    def get(self):
        startposition = int(self.get_argument("startposition", 0))
        count = int(self.get_argument("count", Settings.LIST_ITEM_PER_PAGE))
        
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        allproducts = db.QueryCompetitionProducts(startpos=startposition, count=count, frontend=1)

        serveraddress = self.request.headers.get("Host")
        updatedproducts = []
        for oneproduct in allproducts:
            oneproduct = list(oneproduct) if not db.IsDbUseDictCursor() else dict(oneproduct)
            productid = oneproduct[0] if not db.IsDbUseDictCursor() else oneproduct["product_id"]

            (avatarpreview, hascustom) = db.GetProductAvatarPreview(productid)
            avatarurl = "http://%s%s" % (serveraddress, avatarpreview)
            if not db.IsDbUseDictCursor():
                oneproduct[5] = avatarurl
            else:
                oneproduct["product_avatar"] = avatarurl
            
            productmarketprice = db.QueryProductMarketPrice(productid)
            product17dongprice = db.QueryProduct17dongPrice(productid)
            producthascoupon = db.IsProductHasCoupon(productid)
            producthaspromotion = db.IsProductHasPromotion(productid)
            productpoints = db.GetProductCommentScore(productid)
            # All product avatars
            productavatars = db.GetProductAvatarPreviews(productid)
            productavatars = [("http://%s%s" % (serveraddress, a[0])) for a in productavatars]
            productplayscount = db.GetCompetitionRegisteredPlayerCountInProduct(productid)
            # competitioninfo = db.GetCompetitionByProductId(productid)

            product_eventbegintime = str(oneproduct[31] if not db.IsDbUseDictCursor() else oneproduct["product_eventbegintime"])
            product_eventendtime = str(oneproduct[32] if not db.IsDbUseDictCursor() else oneproduct["product_eventendtime"])
            product_eventbegintime = datetime.datetime(int(product_eventbegintime[0:4]), int(product_eventbegintime[5:7]), int(product_eventbegintime[8:10]), 0, 0, 0)
            product_eventendtime = datetime.datetime(int(product_eventendtime[0:4]), int(product_eventendtime[5:7]), int(product_eventendtime[8:10]), 0, 0, 0)
            
            competition_status = -1
            now = datetime.datetime.now()
            try:
                if now < product_eventbegintime:
                    competition_status = -1
                elif now < product_eventendtime:
                    competition_status = 0
                else:
                    competition_status = 1
            except TypeError:
                competition_status = -1

            if not db.IsDbUseDictCursor():
                oneproduct.append(productmarketprice)
                oneproduct.append(product17dongprice)
                oneproduct.append(producthascoupon)
                oneproduct.append(producthaspromotion)
                oneproduct.append(productpoints)
                oneproduct.append(productavatars)
                oneproduct.append(productplayscount)
            else:
                oneproduct["productmarketprice"] = productmarketprice
                oneproduct["product17dongprice"] = product17dongprice
                oneproduct["producthascoupon"] = producthascoupon
                oneproduct["producthaspromotion"] = producthaspromotion
                oneproduct["productpoints"] = productpoints
                oneproduct["productavatars"] = productavatars
                oneproduct["productplayscount"] = productplayscount
                oneproduct["competition_status"] = competition_status
            updatedproducts.append(oneproduct)

        resultlist = { "result" : "1", "CompetitionList" : updatedproducts }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiCompetitionDetail(BaseHandler):
    def get(self):
        product_id = GetArgumentValue(self, "PID")
        if product_id:
            db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
            productinfo = db.QueryProductInfo(product_id)
            competition_id = productinfo[30] if not db.IsDbUseDictCursor() else productinfo["product_traveldays"]
            competitioninfo = db.GetCompetition(competition_id=competition_id)

            resultlist = { "result" : "1", "CompetitionDetail" : competitioninfo }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)
        else:
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiCompetitionRegistrationForm(BaseHandler):
    def get(self):
        '''Gets the competition registration form definition by product id.

        Returns:
        {"result": 1, "form_info": form_info, "field_list": field_list} on success.
        {"result": 0} on not found.
        {"result": -1, "message": errormsg} on other errors.
        '''
        # jsondata = self.request.headers.get("json", None)
        # jsondict = json.loads(jsondata)
        # product_id = jsondict["product_id"]

        product_id = GetArgumentValue(self, "PID")
        self.set_header('Content-Type', 'application/json')
        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        competition = db.GetCompetitionByProductId(product_id)
        if not competition:
            jsonobj = {"result": 0}
        else:
            competition_id = competition['competition_id']
            result = db.GetCompetitionRegistrationFormByCompetitionId(competition_id)
            if result[0] == 1:
                field_list= result[2]
                normalized_field_list = []
                for field in field_list:
                    field_item = {
                        'name': field['competition_registration_form_field_name'],
                        'type': field['competition_registration_form_field_type'],
                        'is_required': bool(field['competition_registration_form_field_is_required']),
                        'is_mandatory': bool(field['competition_registration_form_field_is_mandatory']),
                        'description': field['competition_registration_form_field_description'] or '',
                        'index': field['competition_registration_form_field_index'],
                        'extra': field['competition_registration_form_field_extra'] or '',
                    }
                    normalized_field_list.append(field_item)
                jsonobj = {'result': 1, 'field_list': normalized_field_list}
            else:
                jsonobj = {'result': 2, 'message': result[1]}

        jsonstr = json.dumps(jsonobj, cls=EnhancedJSONEncoder)
        return self.write(jsonstr)

class ApiCompetitionRegister(XsrfBaseHandler):
    def post(self):
        ''' 客户端提交报名数据信息：
            数据格式：[ {"姓名" : "张三", "性别" : "男", "年龄" : "25", "个人照片" : "myphoto.png"}, 
                       {"姓名" : "张六", "性别" : "女", "年龄" : "22", "个人照片" : "minicoper.jpeg"} ]
        '''
        AVATAR_MAXWIDTH  = 300
        AVATAR_MAXHEIGHT = 300

        db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR if GetApiVersion(self) is None else Settings.DB_DICTCURSOR)
        user_id = self.get_argument("UID")
        product_id = self.get_argument("PID")
        players = self.get_argument("players")
        orderid = self.get_argument("OrderID")
        playersArr = json.loads(players)
        playersImageKeyname = self.get_argument("playersImageKeyname")
        playersImageKeynameArr = json.loads(playersImageKeyname)
        
        # logging.debug("ApiCompetitionRegister: UID: %r, PID: %r, players: %r" % (user_id, product_id, players))

        productinfo = db.QueryProductInfo(product_id)
        competition_id = productinfo[30] if not db.IsDbUseDictCursor() else productinfo["product_traveldays"]

        # logging.debug("playersArr: %r" % playersArr)
        # logging.debug("playersImageKeynameArr: %r" % playersImageKeynameArr)

        # 保存图片信息
        if self.request.files.has_key('myfile'):
            # 包含图片信息
            uploadedfiles = self.request.files['myfile']

            # logging.debug("uploadedfiles length: %r" % len(uploadedfiles))
            # logging.debug("playersImageKeynameArr length: %r" % len(playersImageKeynameArr))

            for i in range(len(uploadedfiles)):
                uploadedfile = uploadedfiles[i]
                original_fname = uploadedfile['filename']
                extension = os.path.splitext(original_fname)[1]
                fname = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(6))
                filename = fname + extension

                filedir = os.path.join(abspath, 'static/img/avatar/temp')
                infile   = filedir + '/' + filename # infile就是用户上传的原始照片

                # 自动保存用户上传的照片文件
                output_file = open(infile, 'w')
                output_file.write(uploadedfile['body'])
                output_file.close()

                playersArr[i][playersImageKeynameArr[i]] = filename

        # 保存报名信息
        ret = db.CompetitionRegister(user_id, competition_id, playersArr)
        db.UpdateCompetitionRegistrationOrderNo(ret[1], orderid)

        resultlist = { "result" : "%s" % ret[0] }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

    def GetImagePixelSize(self, imagefilepath):
        imout = Image.open(imagefilepath)
        newsize = imout.size
        return newsize

class ApiActivityList(BaseHandler):
    def get(self):
        startposition = int(self.get_argument("startposition", 0))
        count = int(self.get_argument("count", 10))
        sort = int(self.get_argument("sort", 1))
        category_id = int(self.get_argument("category_id", 0))
        serveraddress = self.request.headers.get("Host")

        db = DbHelper()
        allactivity = db.QueryActivity(startpos=startposition, count=count, couldbuy=-1, sort=sort, categoryid=category_id)

        for activityinfo in allactivity:
            activityinfo['activity_begintime'] = str(activityinfo['activity_begintime'])
            activityinfo['activity_endtime'] = str(activityinfo['activity_endtime'])
            activityinfo['activity_avatar'] = "http://%s%s" % (serveraddress, db.GetActivityAvatarPreview(activityinfo['activity_id'])[0])

        resultlist = { "result" : "1", "ActivityList" : allactivity }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiActivityCategoryList(BaseHandler):
    def get(self):
        serveraddress = self.request.headers.get("Host")

        db = DbHelper()
        allcategory = db.QueryCategories(0, 0, categoryparent=98)

        # for categoryinfo in allcategory:
        #     categoryinfo[''] = "http://%s%s" % (serveraddress, db.GetActivityAvatarPreview(activityinfo['activity_id'])[0])

        resultlist = { "result" : "1", "ActivityCategoryList" : allcategory }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiActivityDetail(BaseHandler):
    def get(self):
        activity_id = int(self.get_argument("activity_id", 0))
        serveraddress = self.request.headers.get("Host")

        db = DbHelper()
        activityinfo = db.QueryActivityInfo(activity_id)

        activityinfo['activity_begintime'] = str(activityinfo['activity_begintime'])
        activityinfo['activity_endtime'] = str(activityinfo['activity_endtime'])
        activityinfo['activity_avatar'] = "http://%s%s" % (serveraddress, db.GetActivityAvatarPreview(activityinfo['activity_id'])[0])

        resultlist = { "result" : "1", "ActivityDetail" : activityinfo }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)
    
class ApiSubjectList(BaseHandler):
    def get(self):
        startposition = int(self.get_argument("startposition", 0))
        count = int(self.get_argument("count", 10))
        serveraddress = self.request.headers.get("Host")

        db = DbHelper()
        allsubject = db.QuerySubject(startpos=startposition, count=count)

        for subjectinfo in allsubject:
            subjectinfo['subject_date'] = str(subjectinfo['subject_date'])
            subjectinfo['subject_avatar'] = "http://%s%s" % (serveraddress, db.GetSubjectAvatarPreview(subjectinfo['subject_id'])[0])

        resultlist = { "result" : "1", "SubjectList" : allsubject }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)
    
class ApiSubjectDetail(BaseHandler):
    def get(self):
        subject_id = int(self.get_argument("subject_id", 0))
        serveraddress = self.request.headers.get("Host")

        db = DbHelper()
        subjectinfo = db.QuerySubjectInfo(subject_id)

        subjectinfo['subject_date'] = str(subjectinfo['subject_date'])
        subjectinfo['subject_avatar'] = "http://%s%s" % (serveraddress, db.GetSubjectAvatarPreview(subjectinfo['subject_id'])[0])

        subjectobjects = db.QuerySubjectObject(startpos=0, count=0, subject_id=subjectinfo['subject_id'], frontend=1)
        for subjectobjectinfo in subjectobjects:
            if subjectobjectinfo['subject_object_type'] == 1:
                # 对象为商品
                product_id = subjectobjectinfo['subject_object_objectid']
                subjectobjectinfo['subject_object_avatar'] = "http://%s%s" % (serveraddress, db.GetProductAvatarPreview(subjectobjectinfo['subject_object_objectid'])[0])
                subjectobjectinfo['subject_object_name'] = db.GetProductName(product_id)
                subjectobjectinfo['subject_object_price'] = float(db.QueryProduct17dongPrice(product_id))
            elif subjectobjectinfo['subject_object_type'] == 2:
                # 对象为活动
                activityinfo = db.QueryActivityInfo(subjectobjectinfo['subject_object_objectid'])
                subjectobjectinfo['subject_object_avatar'] = "http://%s%s" % (serveraddress, db.GetActivityAvatarPreview(subjectobjectinfo['subject_object_objectid'])[0])
                subjectobjectinfo['subject_object_name'] = activityinfo['activity_name']
                subjectobjectinfo['subject_object_price'] = float("%.2f" % float(activityinfo['activity_price']))

        resultlist = { "result" : "1", "SubjectDetail" : subjectinfo, "SubjectObjectList" : subjectobjects }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiUserPointsList(XsrfBaseHandler):
    def post(self):
        # user_id = GetArgumentValue(self, 'user_id')
        jsondata = self.request.headers.get("json", None)
        jsondict = json.loads(jsondata)
        user_id = jsondict["user_id"]

        db = DbHelper()
        userinfo = db.QueryUserInfoById(user_id)
        totalpoints = userinfo['user_points'] if userinfo['user_points'] else 0

        userpoints_reward = db.QueryUserPointsHistory(user_id, reward=1)
        userpoints_used = db.QueryUserPointsHistory(user_id, reward=0)

        userpoints = list(userpoints_reward)
        userpoints.extend(userpoints_used)
        userpoints_sorted = sorted(userpoints, key = lambda dct: (dct['preorder_paytime']), reverse=True)

        for pointsinfo in userpoints_sorted:
            pointsinfo['preorder_paytime'] = str(pointsinfo['preorder_paytime'])
            pointsinfo['preorder_points_description'] = "购买商品抵用积分" if pointsinfo['points'] < 0 else "购买商品奖励积分"

        resultlist = { "result" : "1", "UserPoints" : totalpoints, "UserPointsList" : userpoints_sorted }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ApiIndexIconList(BaseHandler):
    def get(self):
        db = DbHelper()
        serveraddress = self.request.headers.get("Host")
        # subjectinfo['subject_avatar'] = "http://%s%s" % (serveraddress, db.GetSubjectAvatarPreview(subjectinfo['subject_id'])[0])

        # 104, 105, 106, 107
        # app_index_icon1 = db.QueryCategoryInfo(104)
        # app_index_icon2 = db.QueryCategoryInfo(105)
        # app_index_icon3 = db.QueryCategoryInfo(106)
        # app_index_icon4 = db.QueryCategoryInfo(107)

        appindexiconlist = list()
        appindexiconlist.append("http://%s%s" % (serveraddress, '/static/img/mobile/nav_1.png'))
        appindexiconlist.append("http://%s%s" % (serveraddress, '/static/img/mobile/nav_2.png'))
        appindexiconlist.append("http://%s%s" % (serveraddress, '/static/img/mobile/nav_3.png'))
        appindexiconlist.append("http://%s%s" % (serveraddress, '/static/img/mobile/nav_4.png'))
        # appindexiconlist.append("http://%s%s" % (serveraddress, db.GetCategoryAvatarPreview(app_index_icon2['category_id'])[0]))
        # appindexiconlist.append("http://%s%s" % (serveraddress, db.GetCategoryAvatarPreview(app_index_icon3['category_id'])[0]))
        # appindexiconlist.append("http://%s%s" % (serveraddress, db.GetCategoryAvatarPreview(app_index_icon4['category_id'])[0]))

        resultlist = { "result" : "1", "AppIndexIconList" : appindexiconlist }
        jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

############################################################################################################################################################################################
############################################################################################################################################################################################
    
class ApiAdsMachineExchangeValidate(BaseHandler):
    def get(self):
        # "secret" - 用户在礼品机上输入的兑换密码
        # "machineid" – 礼品机编号，按我司购买此礼品机的台数序号而定，如购买的第一台则编号为 “1”, 购买的第二台则编号为 “2”。

        # 成功: { "result" : "1" }
        # 失败: { "result" : "0" }

        secret = GetArgumentValue(self, "secret")
        machineid = GetArgumentValue(self, "machineid")
        db = DbHelper()
        couponinfo = db.QueryCouponInfoByCNO(secret)
        if couponinfo is not None:
            coupon_valid = int(couponinfo["coupon_valid"])
            coupon_type = int(couponinfo["coupon_type"])
            if coupon_valid == 1 and coupon_type == 3:
                # 兑奖券有效
                # db.UpdateCouponInfo(couponid=couponinfo["coupon_id"], couponinfo={ "coupon_valid" : 0 })

                resultlist = { "result" : "1" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                # 兑奖券已经使用
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            # 优惠券不存在
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

class ApiAdsMachineExchangeNotify(BaseHandler):
    def post(self):
        # "secret" - 用户在礼品机上输入的兑换密码
        # "machineid" – 礼品机编号，按我司购买此礼品机的台数序号而定，如购买的第一台则编号为 “1”, 购买的第二台则编号为 “2”。
        # "status" - 礼品机出货状态，"success" / "fail"

        # 成功: { "result" : "1" }  （成功接收通知）
        # 失败: { "result" : "0" }  （数据异常）

        secret = GetArgumentValue(self, "secret")
        machineid = GetArgumentValue(self, "machineid")
        status = GetArgumentValue(self, "status")

        db = DbHelper()
        couponinfo = db.QueryCouponInfoByCNO(secret)
        if couponinfo is not None:
            coupon_valid = int(couponinfo["coupon_valid"])
            coupon_type = int(couponinfo["coupon_type"])
            if coupon_valid == 1 and coupon_type == 3 and status == "success":
                # 兑奖券有效
                db.UpdateCouponInfo(couponid=couponinfo["coupon_id"], couponinfo={ "coupon_valid" : 0 })

                resultlist = { "result" : "1" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
            else:
                # 兑奖券已经使用
                resultlist = { "result" : "0" }
                jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
                self.set_header('Content-Type','application/json')
                self.write(jsonstr)
        else:
            # 优惠券不存在
            resultlist = { "result" : "0" }
            jsonstr = json.dumps(resultlist, cls=EnhancedJSONEncoder)
            self.set_header('Content-Type','application/json')
            self.write(jsonstr)

    def check_xsrf_cookie(self):
        pass

class AdsMachineGiftPreview(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/adsmachine_giftpreview.html")

class AdsMachineAddress(BaseHandler):
    def get(self):
        return self.renderJinjaTemplate("frontend/adsmachine_address.html")

############################################################################################################################################################################################
############################################################################################################################################################################################

class Sitemap(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("sitemap.xml").read())

class SitemapTraining(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("rss/training.xml").read())

class SitemapTourism(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("rss/tourism.xml").read())

class SitemapFreetrial(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("rss/freetrial.xml").read())

class SitemapActivities(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("rss/activities.xml").read())

class SitemapMall(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("rss/mall.xml").read())

class SitemapPrivatecoach(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("rss/privatecoach.xml").read())

class SitemapTopics(BaseHandler):
    def get(self):
        self.set_header('Content-Type', 'text/xml')
        self.write(open("rss/topics.xml").read())

class Mobile2(BaseHandler):
    def get(self):
        response = self.renderJinjaTemplate('frontend/index.mobile2.html')
############################################################################################################################################################################################
############################################################################################################################################################################################

def main():
    settings = {
        "cookie_secret": Settings.COOKIE_SECRET,
        "login_url": "/login",
        "xsrf_cookies": True,
        "debug": Settings.DEBUG_APP,
        "gzip": True,
        'static_path': os.path.join(os.path.dirname(__file__), 'static'),
    }
    application = tornado.web.Application(
        [
    ############################################ Front End ######################################

        (r'/xsrf/?', Xsrf),
        (r'/?', Index),
        (r'/search/?', Search),
        (r'/about/?', About),
        (r'/cooperation/?', Cooperation),
        (r'/contact/?', Contact),
        (r'/faq/?', Faq),
        (r'/training/?', Training), 
        (r'/privatecoach/?', PrivateCoach),
        (r'/tourism/?', Tourism), 
        (r'/freetrial/?', Freetrial), 
        (r'/activities/?', Activities), 
        (r'/topics/?', Topics), 
        (r'/topics/\d{1,}/?', TopicsDetail), 
        (r'/mall/?', Mall), 
        (r'/registration/?', Registration), 
        (r'/registration/step2/?', RegistrationStep2), 
        (r'/registration/success?', RegistrationSuccess), 
        (r'/sendsmscode/?', RegistrationSendSmsCode), 
        (r'/sendsmscode/findpassword/?', FindpasswordSendSmsCode), 
        (r'/captcha/?\d{0,}', Captcha),
        (r'/ajax/login/?', AjaxLogin), 
        (r'/login/?', Login), 
        (r'/sinalogin/?', SinaLogin), 
        (r'/qqlogin/?', QQLogin), 
        (r'/wechatlogin/?', WechatLogin), 
        (r'/account/?', Account), 
        (r'/account/email/confirm/?', AccountEmailConfirm), 
        (r'/account/order/?', AccountOrder), 
        (r'/account/order/refund/?', AccountOrderRefund), 
        (r'/account/order/delete/?', AccountOrderDelete), 
        (r'/account/info/?', AccountInfo), 
        (r'/account/info/delete/?', AccountInfoDelete), 
        (r'/account/integration/?', AccountIntegration), 
        (r'/account/coupon/?', AccountCoupon), 
        (r'/account/favorite/?', AccountFavorite), 
        (r'/account/report/?', AccountReport), 
        (r'/account/address/add/?', AccountAddressAdd), 
        (r'/product/\d{1,}/?', ProductDetail), 
        (r'/product/(\d+)/order/?', ProductOrder), 
        (r'/product/(\d+)/order/step2/?', ProductOrderStep2), 
        (r'/product/\d{1,}/comment/?', ProductComment), 
        (r'/account/avatar/?', AccountAvatar), 
        (r'/account/avatar/update/?', AccountAvatarUpdate), 
        (r'/account/changephonenumber/?', AccountChangephonenumber), 
        (r'/product/getcomment/?', ProductGetcomment), 
        (r'/product/\d{1,}/getscenelocation/?', ProductGetscenelocation), 
        (r'/product/\d{1,}/getscenetimeperiod/?', ProductGetscenetimeperiod), 
        (r'/product/\d{1,}/getscene/?', ProductGetscene), 
        (r'/product/\d{1,}/getprice/?', ProductGetprice), 
        (r'/product/(\d+)/show/?', ProductShowInfo),
        (r'/product/(\d+)/getcoupon/?', ProductGetCoupon),
        (r'/product/(\d+)/coupon/userdraw/?', ProductCouponUserDraw),
        (r'/product/(\d+)/c2discount/validate/?', ProductC2DiscountValidate),
        (r'/product/getvpdetail/?', ProductGetvpdetail), 
        (r'/ckedit/image/upload/?', CKEditImageUpload),
        (r'/coupon/info/?', CouponInfo),
        (r'/findpassword/?', FindPassword),
        (r'/report/?', Report),
        (r'/agreement/?', Agreement),
        (r'/account/coupon/delete/?', AccountCouponDelete),
        (r'/account/updatephonenumber/?', AccountUpdatePhonenumber),
        (r'/account/updateemail/?', AccountUpdateEmail),
        (r'/account/updatepassword/?', AccountUpdatePassword),
        (r'/product/order/update/?', ProductOrderUpdate),
        (r'/app/install/?', AppInstall),
        (r'/app/?', AppDownload),
        (r'/app/download/mobile/1/?', AppDownloadMobile1),
        (r'/app/download/mobile/2/?', AppDownloadMobile2),
        (r'/version.plist', VersionIOS),
        (r'/version.xml', VersionAndroid),
        (r'/wap/?', WapVersion),
        (r'/sendsmscode/registration/?', SendSmsCodeRegistration),
        (r'/user/order/list/?', UserOrderList),

        (r'/special_topic/wintercamp/?', SpecialTopicWinterCamp),
        (r'/special_topic/register/?', SpecialTopicRegister),
        (r'/special_topic/valentine/?', SpecialTopicValentine),
        (r'/special_topic/valentine/getcoupon/?', SpecialTopicValentineGetCoupon),
        (r'/special_topic/swordfight/?', SpecialTopicSwordfight),
        (r'/special_topic/summercamp/?', SpecialTopicSummerCamp),
        (r'/special_topic/summercamp/getcoupon/?', SpecialTopicSummerCampGetCoupon),
        (r'/special_topic/landingpage/basketball/?', SpecialTopicLandingPageBaseketball),
        (r'/special_topic/landingpage/football/?', SpecialTopicLandingPageFootball),
        (r'/special_topic/landingpage/swim/?', SpecialTopicLandingPageSwim),
        (r'/special_topic/summercamp/v2/?', SpecialTopicSummerCampV2),
        (r'/special_topic/summercamp/v2/getcoupon/?', SpecialTopicSummerCampV2GetCoupon),
        (r'/special_topic/summercamp/v3/?', SpecialTopicSummerCampV3),
        (r'/special_topic/vote/family/?', SpecialTopicVoteFamily),
        (r'/special_topic/vote/family/list/?', SpecialTopicVoteFamilyList),
        (r'/special_topic/vote/revenge/?', SpecialTopicVoteRevenge),
        (r'/special_topic/vote/revenge/list?', SpecialTopicVoteRevengeList),
        (r'/special_topic/vote/training/?', SpecialTopicVoteTraining),
        (r'/special_topic/dance/?', SpecialTopicDance),
        (r'/special_topic/activity/?', SpecialTopicActivity),
        (r'/special_topic/lotterydraw/?', SpecialTopicLotterydraw),
        (r'/special_topic/lotterydraw/(\d+)/draw/?', SpecialTopicLotterydrawDraw),
        (r'/special_topic/lotterydraw/(\d+)/querystate/?', SpecialTopicLotterydrawQuerystate),
        (r'/special_topic/lotterydraw/v2/?', SpecialTopicLotterydrawV2),
        (r'/special_topic/lotterydraw/v2/(\d+)/draw/?', SpecialTopicLotterydrawDrawV2),
        (r'/special_topic/baymax/?', SpecialTopicBaymax),
        (r'/special_topic/qmengqinzileyuan/?', SpecialTopicQmengqinzileyuan),
        (r'/special_topic/qmengqinzileyuan/v2/?', SpecialTopicQmengqinzileyuanV2),
        (r'/special_topic/photograph/?', SpecialTopicPhotograph),
        (r'/special_topic/breakfast/?', SpecialBreakfast),
        (r'/special_topic/breakfast/(\d+)/draw/?', SpecialBreakfastDraw),
        (r'/special_topic/breakfast/(\d+)/querystate/?', SpecialBreakfastQuerystate),
        (r'/special_topic/breakfastmob/?', SpecialBreakfastMob),
        (r'/special_topic/kaixue/?', SpecialTopicKaixue),
        (r'/special_topic/freesports/?', SpecialTopicFreeSports),
        (r'/special_topic/teacherday/?', SpecialTopicTeacherday),
        (r'/special_topic/teacherdaymob/?', SpecialTopicTeacherdayMob),
        (r'/special_topic/exam/?', SpecialTopicExam),
        (r'/special_topic/rexuefootball/?', SpecialTopicRexueFootball),
        (r'/special_topic/nationalday2015/?', SpecialTopicNationalDay2015),
        (r'/special_topic/landingpage/basketball/v2/?', SpecialTopicLandingPageBaseketballV2),
        (r'/special_topic/landingpage/badminton/?', SpecialTopicLandingPageBadminton),
        (r'/special_topic/gifts/?', SpecialTopicGifts),
        (r'/special_topic/gifts/draw/?', SpecialTopicGiftsDraw),
        (r'/special_topic/gifts/(\d+)/querystate/?', SpecialTopicGiftsQuerystate),

        (r'/wintercamp/?', Wintercamp),
        (r'/summercamp/index/?', SummercampIndex),
        (r'/summercamp/?', SummercampList),
        (r'/competition/?', CompetitionList),
        (r'/competition/(\d+)/?', CompetitionDetail),
        (r'/competition/(\d+)/register/?', CompetitionRegister),
        (r'/competition/registration/upload', CompetitionRegistrationUploadImage),
        (r'/search/keywords/?', AutocompleteSearchKeywords),

    #############################################################################################

        (r'/campusfootball/?', CampusFootball),
        (r'/campusfootball/news/\d{1,}/?', CampusFootballNews),
        
    ############################################ LianLianPay ####################################
        
        (r'/payment/?', PaymentHandler),
        (r'/payment/return/?', PaymentReturnHandler),
        (r'/payment/notify/?', PaymentNotifyHandler),
        (r'/payment/llpay/return/?', LLPaymentReturn),
        (r'/payment/llpay/notify/?', LLPaymentNotify),
        (r'/payment/success/?', PaymentSuccessHandler),
        (r'/payment/error/?', PaymentErrorHandler),
        (r'/payment/complete/?', PaymentCompleteHandler),
        (r'/payment/ebank/?', PaymentEbank),
        
    ############################################ API ############################################

        (r'/api/v[\w.]*/?payment/wechat/?\b|/payment/wechat/?', ApiPaymentHandler),
        (r'/api/v[\w.]*/?payment/wechat/notify/?\b|/api/payment/wechat/notify/?', ApiPaymentWechatNotifyHandler),
        (r'/api/v[\w.]*/?payment/notify/?\b|/api/payment/notify/?', ApiPaymentNotifyHandler),
        (r'/api/v[\w.]*/?user/login/?\b|/api/user/login/?', ApiUserLogin),
        (r'/api/v[\w.]*/?user/checkstate/?\b|/api/user/checkstate/?', ApiUserCheckState),
        (r'/api/v[\w.]*/?user/register/?\b|/api/user/register/?', ApiUserRegister),
        (r'/api/v[\w.]*/?user/queryinfo/?\b|/api/user/queryinfo/?', ApiUserQueryInfo),
        (r'/api/v[\w.]*/?user/avatar/upload/?\b|/api/user/avatar/upload/?', ApiUserAvatarUpload),
        (r'/api/v[\w.]*/?user/nickname/update/?\b|/api/user/nickname/update/?', ApiUserNicknameUpdate),
        (r'/api/v[\w.]*/?user/phonenumber/update/?\b|/api/user/phonenumber/update/?', ApiUserPhonenumberUpdate),
        (r'/api/v[\w.]*/?user/email/verify/?\b|/api/user/email/verify/?', ApiUserEmailVerify),
        (r'/api/v[\w.]*/?user/password/reset/?\b|/api/user/password/reset/?', ApiUserPasswordReset),
        (r'/api/v[\w.]*/?user/password/update/?\b|/api/user/password/update/?', ApiUserPasswordUpdate),
        (r'/api/v[\w.]*/?user/address/add/?\b|/api/user/address/add/?', ApiUserAddressAdd),
        (r'/api/v[\w.]*/?user/traveller/add/?\b|/api/user/traveller/add/?', ApiUserTravellerAdd),
        (r'/api/v[\w.]*/?user/traveller/delete/?\b|/api/user/traveller/delete/?', ApiUserTravellerDelete),
        (r'/api/v[\w.]*/?user/baseinfo/update/?\b|/api/user/baseinfo/update/?', ApiUserBaseinfoUpdate),
        (r'/api/v[\w.]*/?product/advertised/?\b|/api/product/advertised/?', ApiProductAdvertised),
        (r'/api/v[\w.]*/?product/recommended/?\b|/api/product/recommended/?', ApiProductRecommended),
        (r'/api/v[\w.]*/?product/relatedproducts/?\b|/api/product/relatedproducts/?', ApiProductRelatedProducts),
        (r'/api/v[\w.]*/?vendor/list/?\b|/api/vendor/list/?', ApiVendorList),
        (r'/api/v[\w.]*/?product/search/?\b|/api/product/search/?', ApiProductSearch),
        (r'/api/v[\w.]*/?product/searchdetail/?\b|/api/product/searchdetail/?', ApiProductSearchDetail),
        (r'/api/v[\w.]*/?product/list/?\b|/api/product/list/?', ApiProductList),
        (r'/api/v[\w.]*/?product/filter/list/?\b|/api/product/filter/list/?', ApiProductFilterList),
        (r'/api/v[\w.]*/?product/scene/list/?\b|/api/product/scene/list/?', ApiProductSceneList),
        (r'/api/v[\w.]*/?comment/list/?\b|/api/comment/list/?', ApiCommentList),
        (r'/api/v[\w.]*/?comment/add/?\b|/api/comment/add/?', ApiCommentAdd),
        (r'/api/v[\w.]*/?order/add/?\b|/api/order/add/?', ApiOrderAdd),
        (r'/api/v[\w.]*/?order/query/?\b|/api/order/query/?', ApiOrderQuery),
        (r'/api/v[\w.]*/?order/finalprice/query/?\b|/api/order/finalprice/query/?', ApiOrderQueryFinalPrice),
        (r'/api/v[\w.]*/?c2discount/validate/?\b|/api/c2discount/validate/?', ApiC2DiscountValidate),
        (r'/api/v[\w.]*/?product/scene/name/list/?\b|/api/product/scene/name/list/?', ApiProductSceneNameList),
        (r'/api/v[\w.]*/?product/scene/location/list/?\b|/api/product/scene/location/list/?', ApiProductSceneLocationList),
        (r'/api/v[\w.]*/?product/scene/timeperiod/list/?\b|/api/product/scene/timeperiod/list/?', ApiProductSceneTimeperiodList),
        (r'/api/v[\w.]*/?product/scene/query/?\b|/api/product/scene/query/?', ApiProductSceneQuery),
        (r'/api/v[\w.]*/?product/scene/queryprice/?\b|/api/product/scene/queryprice/?', ApiProductSceneQueryPrice),
        (r'/api/v[\w.]*/?product/scene/listall/?\b|/api/product/scene/listall/?', ApiProductSceneListAll),
        (r'/api/v[\w.]*/?user/address/list/?\b|/api/user/address/list/?', ApiUserAddressList),
        (r'/api/v[\w.]*/?user/address/queryinfo/?\b|/api/user/address/queryinfo/?', ApiUserAddressQueryInfo),
        (r'/api/v[\w.]*/?user/traveller/list/?\b|/api/user/traveller/list/?', ApiUserTravellerList),
        (r'/api/v[\w.]*/?topic/list/?\b|/api/topic/list/?', ApiTopicList),
        (r'/api/v[\w.]*/?topic/detail/?\b|/api/topic/detail/?', ApiTopicDetail),
        (r'/api/v[\w.]*/?sendsmscode/registration/?\b|/api/sendsmscode/registration/?', ApiSendSmsCodeRegistration),
        (r'/api/v[\w.]*/?sendsmscode/findpassword/?\b|/api/sendsmscode/findpassword/?', ApiSendSmsCodeFindpassword),
        (r'/api/v[\w.]*/?coupon/update/?\b|/api/coupon/update/?', ApiCouponUpdate),
        (r'/api/v[\w.]*/?coupon/list/?\b|/api/coupon/list/?', ApiCouponList),
        (r'/api/v[\w.]*/?coupon/userdraw/detect/?\b|/api/coupon/userdraw/detect/?', ApiCouponUserDrawDetect),
        (r'/api/v[\w.]*/?coupon/userdraw/?\b|/api/coupon/userdraw/?', ApiCouponUserDraw),
        (r'/api/v[\w.]*/?product/payment/process/?\b|/api/product/payment/process/?', ApiProductPaymentProcess),
        (r'/api/v[\w.]*/?user/order/list/?\b|/api/user/order/list/?', ApiUserOrderList),
        (r'/api/v[\w.]*/?product/wintercamp/list/?\b|/api/product/wintercamp/list/?', ApiProductWintercampList),
        (r'/api/v[\w.]*/?order/finish/?\b|/api/order/finish/?', ApiOrderFinish),
        (r'/api/v[\w.]*/?searchkeywords/list/?\b|/api/searchkeywords/list/?', ApiSearchkeywordsList),
        (r'/api/v[\w.]*/?vote/list/?\b|/api/vote/list/?', ApiVoteList),
        (r'/api/v[\w.]*/?user/vote/list/?\b|/api/user/vote/list/?', ApiUserVoteList),
        (r'/api/v[\w.]*/?vote/detail/?\b|/api/vote/detail/?', ApiVoteDetail),
        (r'/api/v[\w.]*/?vote/option/list/?\b|/api/vote/option/list/?', ApiVoteOptionList),
        (r'/api/v[\w.]*/?vote/option/detail/?\b|/api/vote/option/detail/?', ApiVoteOptionDetail),
        (r'/api/v[\w.]*/?vote/option/vote/?\b|/api/vote/option/vote/?', ApiVoteOptionVote),
        (r'/api/v[\w.]*/?vote/option/upload/?\b|/api/vote/option/upload/?', ApiVoteOptionUpload),
        (r'/api/v[\w.]*/?message/list/?\b|/api/message/list/?', ApiMessageList),
        (r'/api/v[\w.]*/?message/detail/?\b|/api/message/detail/?', ApiMessageDetail),
        (r'/api/v[\w.]*/?coupon/delete/?\b|/api/coupon/delete/?', ApiDeleteCoupon),
        (r'/api/v[\w.]*/?message/delete/?\b|/api/message/delete/?', ApiDeleteMessage),
        (r'/api/v[\w.]*/?order/delete/?\b|/api/order/delete/?', ApiDeleteOrder),
        (r'/api/v[\w.]*/?order/refund/?\b|/api/order/refund/?', ApiOrderRefund),
        (r'/api/v[\w.]*/?promotion/draw/?\b|/api/promotion/draw/?', ApiPromotionDraw),
        (r'/api/v[\w.]*/?competition/list/?\b|/api/competition/list/?', ApiCompetitionList),
        (r'/api/v[\w.]*/?competition/registration-form/?\b|/api/competition/registration-form/?', ApiCompetitionRegistrationForm),
        (r'/api/v[\w.]*/?competition/register/?\b|/api/competition/register/?', ApiCompetitionRegister),
        (r'/api/v[\w.]*/?competition/detail/?\b|/api/competition/detail/?', ApiCompetitionDetail),

        (r'/alipay/batchrefund/?', AlipayBatchrefund),
        (r'/alipay/batchrefund/notify/?', AlipayBatchrefundNotify),
        (r'/api/v[\w.]*/weixin/batchrefund/?', ApiWeixinBatchrefund),
        (r'/api/v[\w.]*/weixin/refundquery/?', ApiWeixinRefundquery),
        (r'/api/v[\w.]*/?activity/list/?', ApiActivityList),
        (r'/api/v[\w.]*/?activity/category/list/?', ApiActivityCategoryList),
        (r'/api/v[\w.]*/?activity/detail/?', ApiActivityDetail),
        (r'/api/v[\w.]*/?subject/list/?', ApiSubjectList),
        (r'/api/v[\w.]*/?subject/detail/?', ApiSubjectDetail),
        (r'/api/v[\w.]*/?user/points/list/?', ApiUserPointsList),
        (r'/api/v[\w.]*/?index/icon/list/?', ApiIndexIconList),

    #############################################################################################

        (r'/api/adsmachine/exchange/validate/?', ApiAdsMachineExchangeValidate),
        (r'/api/adsmachine/exchange/notify/?', ApiAdsMachineExchangeNotify),
        (r'/adsmachine/giftpreview/?', AdsMachineGiftPreview),
        (r'/adsmachine/address/?', AdsMachineAddress),

    #############################################################################################

        (r'/sitemap.xml', Sitemap),
        (r'/rss/training.xml', SitemapTraining),
        (r'/rss/tourism.xml', SitemapTourism),
        (r'/rss/freetrial.xml', SitemapFreetrial),
        (r'/rss/activities.xml', SitemapActivities),
        (r'/rss/mall.xml', SitemapMall),
        (r'/rss/privatecoach.xml', SitemapPrivatecoach),
        (r'/rss/topics.xml', SitemapTopics),
        (r'/mobile2/?', Mobile2),

    #############################################################################################

        ], **settings)

    if len(sys.argv) > 1:
        port = int(sys.argv[1].split('=')[1])
    else:
        port = 8888
    # application.listen(port)
    # tornado.ioloop.IOLoop.instance().start()

    sockets = bind_sockets(port)
    # tornado.process.fork_processes(0)
    server = HTTPServer(application, xheaders=True)
    server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

############################################################################################################################################################################################
