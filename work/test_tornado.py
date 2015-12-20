    # coding=utf=8
# tornado模板
# {% apply function %} content {% end %}
# {% raw content %} 不转义 字符串
# {% escape content %} 转义 字符串
# {% module xsrf_form_html() %}
# set_cookie,get_cookie,get_current_user,current_user
# set_secure_cookie, get_secure_cookie, 
# xsrf_cookies
# templates
# {{ static_url('css/style.css') }}
# import tornado.autoreload
from tornado.web import (
    RequestHandler, Application, url, HTTPError,authenticated)
from tornado.ioloop import IOLoop
from tornado.options import define
import tornado
import os
import json
import requests

class Handler(RequestHandler):
    def get_argument_into(self, *args, **kwargs):
        into = kwargs.pop('into', None)
        r = self.get_argument(*args,**kwargs)
        if into is not None:
            r = into(r)
        return r
class ApiIndexIconList(Handler):
    def get(self):
        jsonstr = requests.get('http://www.17dong.com.cn/api/v2.0/index/icon/list/').text
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class OtherHtmlHandler(RequestHandler):

    def get_current_user(self):
        return self.get_secure_cookie('user')

    def get(self):
        if self.current_user:
            self.write("hello, I am %s." % self.current_user)
        else:
            self.redirect("/")

class LoginHandler(RequestHandler):

    def get(self):
        self.write("<form method='post'><input type='text' name='user'>\
            <input type='submit'></form>")

    def post(self):
        # 使用cookie来存储用户信息
        self.set_secure_cookie('user', self.get_argument('user', None), expires_days=None)
        self.write("登陆成功")
        
        
class ApiProductFilterList(RequestHandler):
    def get(self):
        product_type = int(self.get_argument("type"))
        filtername = self.get_argument("filtername")

        if filtername == 'item':
            resultlist = {
                    "FilterItems":[
                    {
                    "category_parent": 7,
                    "category_sortweight": None,
                    "category_avatar": "",
                    "category_description": "",
                    "category_id": 76,
                    "category_name": "国内营"
                    },
                    {
                    "category_parent": 7,
                    "category_sortweight": None,
                    "category_avatar": "",
                    "category_description": "",
                    "category_id": 77,
                    "category_name": "国外营"
                    }
                    ],
                    "result": "1"
                    }
        elif filtername == 'location':
            resultlist = {
            "FilterItems":[
            {
            "product_area": "美国"
            },
            {
            "product_area": "上海"
            },
            {
            "product_area": "英国"
            },
            {
            "product_area": "西班牙"
            },
            {
            "product_area": "澳大利亚"
            },
            {
            "product_area": "周边"
            },
            {
            "product_area": "外省市"
            },
            {
            "product_area": "日本"
            },
            {
            "product_area": "安吉"
            },
            {
            "product_area": "海外"
            },
            {
            "product_area": "葡萄牙"
            },
            {
            "product_area": "成都"
            },
            {
            "product_area": "广西"
            },
            {
            "product_area": "云南"
            },
            {
            "product_area": "张家口"
            }
            ],
            "result": "1"
            }
        jsonstr = json.dumps(resultlist)
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class HomeHandler(RequestHandler):


    # 自定义过滤器
    def test_string(self, msg):
        return 'test string %s' % msg

    def get(self):
        self.ui['test_function'] = self.test_string
        self.write(open('templates/index.mobile2.html').read())

class ProductList(RequestHandler):
    def get(self):
        self.write(open('templates/f1_camp.mobile.html').read())
class ProductList2(RequestHandler):
    def get(self):
        self.write(open('templates/camp.html').read())

class MainHanlder(RequestHandler):
    def get(self):
        items = ["Item 1","Item 2","Item 3",]
        self.render('tmp.html', title='My Title', items=items)

class TestData(Handler):
    def get(self):
        start = self.get_argument_into('startpos', 0, into=int)
        stop = start + self.get_argument_into('count', 10, into=int)
        dql = mydql()
        dql.setmain('student')
        # dql.setmain('order_table')
        results = dql.query(where={'DATE_FORMAT(sbirthday, "%Y-%m-%d")__gte':'1985-01-01'}).orderby('sbirthday', desc=True).slice(start, stop)
        self.write({'testdata': results})

class ApiProductAdvertised(Handler):
    ''' 获取所有广告商品, 参数 type 定义：
           0  - 首页顶部轮播广告
           50 - 大 Banner 广告
           51 - 小 Banner 广告
    '''
    def get(self):
        self.set_header('Content-Type','application/json')
        jsonstr = {"SmallAdsInfo": [{"ads_position": 5, "ads_platform": 2, "ads_sortweight": 51, "ads_id": 13, "ads_state": 1, "ads_endtime": {"args": [2015, 2, 4, 11, 51, 21, 0], "__type__": "datetime.datetime"}, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P13_2193729920.jpeg", "ads_externalurl": "http://17dong.com.cn/product/2017", "ads_begintime": {"args": [2015, 2, 4, 11, 51, 20, 0], "__type__": "datetime.datetime"}, "adstarget": "product", "ads_externalproductid": "2017", "ads_publisher": "Willson", "productid": "2017"}], "R3_1": [{"ads_position": 17, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 56, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P56_3146519414.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u6e38\u6cf3", "productfilter": {"sort": "0", "item": "\u6e38\u6cf3", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "BigAdsInfo": [{"ads_position": 4, "ads_platform": 3, "ads_sortweight": 1, "ads_id": 95, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P95_4505549373.jpeg", "ads_externalurl": "http://www.17dong.com.cn/product/1755", "ads_begintime": None, "adstarget": "product", "ads_externalproductid": "1755", "ads_publisher": "vivian", "productid": "1755"}], "R3_3": [{"ads_position": 19, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 58, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P58_4728653791.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7bee\u7403", "productfilter": {"sort": "0", "item": "\u7bee\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R1_2": [{"ads_position": 13, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 52, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P52_9438849779.jpeg", "ads_externalurl": "http://www.17dong.com.cn/product/1503", "ads_begintime": None, "adstarget": "product", "ads_externalproductid": "1503", "ads_publisher": "Willson", "productid": "1503"}], "R1_3": [{"ads_position": 14, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 53, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P53_9439289816.jpeg", "ads_externalurl": "http://www.17dong.com.cn/product/1301", "ads_begintime": None, "adstarget": "product", "ads_externalproductid": "1301", "ads_publisher": "Willson", "productid": "1301"}], "R1_1": [{"ads_position": 12, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 51, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P51_9438388977.jpeg", "ads_externalurl": "http://www.17dong.com.cn/product/1510", "ads_begintime": None, "adstarget": "product", "ads_externalproductid": "1510", "ads_publisher": "Willson", "productid": "1510"}], "R2_1": [{"ads_position": 15, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 54, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P54_7065015451.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u8db3\u7403", "productfilter": {"sort": "0", "item": "\u8db3\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R2_2": [{"ads_position": 16, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 55, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P55_7050394159.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7bee\u7403", "productfilter": {"sort": "0", "item": "\u7bee\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R3_2": [{"ads_position": 18, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 57, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P57_3146694782.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u8db3\u7403", "productfilter": {"sort": "0", "item": "\u8db3\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "AllAdvertisedProduct": [{"ads_position": 1, "ads_platform": 2, "ads_sortweight": 999, "ads_id": 85, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P85_8155279659.jpeg", "ads_externalurl": "http://www.17dong.com.cn/special_topic/gifts?urlrequestfrom=app", "specialtopicurl": "http://www.17dong.com.cn/special_topic/gifts?urlrequestfrom=app", "ads_begintime": None, "adstarget": "specialtopic", "ads_externalproductid": None, "ads_publisher": "vivian"}, {"ads_position": 1, "ads_platform": 3, "ads_sortweight": 999, "ads_id": 93, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P93_3884070544.jpeg", "ads_externalurl": "http://www.17dong.com.cn/special_topic/exam?urlrequestfrom=app", "specialtopicurl": "http://www.17dong.com.cn/special_topic/exam?urlrequestfrom=app", "ads_begintime": None, "adstarget": "specialtopic", "ads_externalproductid": None, "ads_publisher": "vivian"}, {"ads_position": 1, "ads_platform": 3, "ads_sortweight": 900, "ads_id": 87, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P87_9851381872.jpeg", "ads_externalurl": "http://17dong.com.cn/special_topic/kaixue?urlrequestfrom=app", "specialtopicurl": "http://17dong.com.cn/special_topic/kaixue?urlrequestfrom=app", "ads_begintime": None, "adstarget": "specialtopic", "ads_externalproductid": None, "ads_publisher": "vivian"}], "result": "1", "RB": [{"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 62, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P62_7050898921.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7f51\u7403", "productfilter": {"sort": "0", "item": "\u7f51\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}, {"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 63, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P63_7051109328.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7fbd\u6bdb\u7403", "productfilter": {"sort": "0", "item": "\u7fbd\u6bdb\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}, {"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 64, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P64_7051326468.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u821e\u8e48", "productfilter": {"sort": "0", "item": "\u821e\u8e48", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}, {"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 65, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P65_7051927930.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7a7a\u624b\u9053", "productfilter": {"sort": "0", "item": "\u7a7a\u624b\u9053", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}, {"ads_position": 23, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 66, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P66_7052295917.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u8dc6\u62f3\u9053", "productfilter": {"sort": "0", "item": "\u8dc6\u62f3\u9053", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R4_3": [{"ads_position": 22, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 61, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P61_4726853486.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u821e\u8e48", "productfilter": {"sort": "0", "item": "\u821e\u8e48", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R4_2": [{"ads_position": 21, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 60, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P60_3147742676.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u51fb\u5251", "productfilter": {"sort": "0", "item": "\u51fb\u5251", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}], "R4_1": [{"ads_position": 20, "ads_platform": 2, "ads_sortweight": 1, "ads_id": 59, "ads_state": 1, "ads_endtime": None, "ads_auditstate": 1, "ads_avatar": "http://17dong.com.cn/static/img/avatar/ads/P59_3147478989.jpeg", "ads_externalurl": "http://17dong.com.cn/training?sort=0&amp;item=\u7f51\u7403", "productfilter": {"sort": "0", "item": "\u7f51\u7403", "producttype": 1}, "ads_begintime": None, "adstarget": "productlist", "ads_externalproductid": None, "ads_publisher": "Willson"}]}
        jsonstr = json.dumps(jsonstr)
        self.write(jsonstr)


class ApiProductWintercampList(Handler):
    def get(self):

        jsonstr = open('wintercamp.json').read()
        self.set_header('Content-Type','application/json')
        self.write(jsonstr)

class ProductOrder(Handler):
    def get(self):
        # self.write(open('templates/order2.html').read())
        self.write(open('templates/product_order_layout.html').read())

class ApiProductSearchDetail(Handler):
    def get(self):
        pid = self.get_argument('pid')
        resp = requests.get('http://www.17dong.com.cn/api/v2.0/product/searchdetail',
            params={'pid': pid})
        self.set_header('content-type','application/json')
        self.write(resp.text)

class TemplateHandler(Handler):
    def get(self, name):
        try:
            f = open('templates/'+ name + '.html')
        except Exception:
            self.send_error(404)
        else:
            self.write(f.read())
# tornado资源配置
settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'static_path': os.path.join(os.path.dirname(__file__),'static'),
    'login_url': '/login',
    'autoreload': True,
    'debug': True,
    'cookie_secret': 'abcdefg',
}

Application([
    (r'/?', HomeHandler),
    (r'/templates/([\w_]+)/?', TemplateHandler),
    (r'/product/2020/order/?', ProductOrder),
    (r'/product/list?', ProductList),
    (r'/product/list2?', ProductList2),
    (r'/login/?', LoginHandler),
    (r'/other/?', OtherHtmlHandler),
    (r'/main/?', MainHanlder),
    (r'/data/?', TestData),
    (r'/api/v[\w.]*/?product/advertised/?', ApiProductAdvertised),
    (r'/api/v[\w.]*/?index/icon/list/?', ApiIndexIconList),
    (r'/api/v[\w.]*/?product/filter/list/?\b|/api/product/filter/list/?', ApiProductFilterList),
    (r'/api/v[\w.]*/?product/wintercamp/list/?\b|/api/product/wintercamp/list/?', ApiProductWintercampList),
    (r'/api/v2.0/product/searchdetail/?',ApiProductSearchDetail),

    ], default_host="0.0.0.0", **settings).listen(8888)

IOLoop.current().start()