#!/usr/bin/env python
#-*-coding:utf-8-*-

import sys, os
abspath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(abspath)
os.chdir(abspath)

from module.mysqldb import DbHelper
import module.settings as Settings
import datetime

from time import gmtime, strftime
from datetime import timedelta
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

import tornado.ioloop, tornado.web, tornado.process, string
import web, uuid, re, time, random, cgi
import urllib, urllib2, urlparse, cookielib, hashlib, socket
import logging, httplib, json

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

def create_trade_no(user_id, product_id, scene_id, preorder_counts, preorder_counts_child):
        if product_id is None:
            product_id = 0

        if scene_id is None:
            scene_id = 0

        if preorder_counts is None:
            preorder_counts = 0

        if preorder_counts_child is None:
            preorder_counts_child = 0

        return "%sU%sP%sS%sO%sT%sR%s" % (strftime("%Y%m%d%H%M%S"), user_id, product_id, scene_id, preorder_counts, preorder_counts_child, random.randint(100, 999))

def createUsers():
    db = DbHelper()

    for i in range(100):
        username = "username_%04d" % i
        passwd = "this_is_password_%d" % i
        phonenumber = "1351111%04d" % i
        role = random.randint(1, 3)
        vendornames = {"vendor1" : "GB2014", "vendor2" : "WA52014", "vendor3" : "SLB2014", "vendor4" : "XH2014", "vendor5" : "WXTY2014", "vendor6" : "NMZ2014"}
        user_vendorname = None

        if role == 2:  # 供应商
            user_vendorname = vendornames["vendor%d" % random.randint(1, 6)]
        
        db.AddUser({"user_name" : username, "user_password" : passwd, "user_phonenumber" : phonenumber, "user_role" : role, "user_vendorname" : user_vendorname})
        print "Creating user %r" % i

    db.AddUser({"user_name" : "17dong", "user_password" : "17dong", "user_phonenumber" : "13133334444", "user_role" : 1, "user_vendorname" : "Name"})
    db.AddUser({"user_name" : "vendor", "user_password" : "vendor", "user_phonenumber" : "13133334444", "user_role" : 2, "user_vendorname" : "Name"})
    db.AddUser({"user_name" : "admin_17dong",  "user_password" : "admin", "user_phonenumber" : "13133334444", "user_role" : 3, "user_adminrole" : 1, "user_vendorname" : "Name"})
    db.AddUser({'user_name' : 'admin_siysl', 'user_role' : 4, 'user_adminrole' : 1, 'user_phonenumber' : '13800138000', 'user_nickname' : 'Willson', 'user_password' : 'admin', 'user_country_chs' : '中国', 'user_country_eng' : 'China' })

def createCategories():
    db = DbHelper()

    category_names = {
        "1" : ["足球", "蓝球", "羽毛球", "乒乓球", "游泳", "击剑", "射击", "骑马", "跆拳道"], 
        "2" : ["高端赛事观摩", "水下摄影", "瑞士滑雪", "马代水上冲浪"], 
        "3" : ["蓝球试听", "林丹试听", "李林试听", "李大试听", "王东试听"], 
        "4" : ["某某某活动", "李大叶活动", "大表哥活动", "其其林活动"], 
        "5" : ["体验课程", "实物礼品"],
        "6" : ["足球", "蓝球", "羽毛球", "游泳", "击剑" ], 
        "99": ["旅游专题", "体育专题", "培训专题", "系统文章"] }
    allparentcategories = db.QueryParentCategories(0, 0)
    for key, value in category_names.items():
        parent = key
        for onecategory in value:
            name = onecategory
            db.AddCategory({ "category_name" :  name, "category_parent" : int(parent) })
            # print "Creating category %r" % name

def createProducts():
    db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)
    allvendors = db.QueryUsers(0, 0, 2)
    description = '''中俄在国际事务中协调配合更加密切

                    习近平指出，今年以来，我同你保持密切沟通，就发展中俄关系加强顶层设计和战略引领，栽培中俄友好合作常青树，我们收获了丰厚果实。双边贸易额和双向投资持续增长，东线天然气管道和东西两线增供原油等一批大项目合作取得重要进展，在国际事务中协调和配合更加密切有效。

                    普京表示，我完全赞同习近平主席对俄中关系的评价。我们都大力推动俄中全面战略协作伙伴关系发展，政治对话不断加深，能源合作进展顺利，经贸合作取得更多实际成果。

                    要求落实好共庆二战胜利70周年计划

                    两国元首一致认为，双方要如期推进东线天然气管道建设，尽快启动西线天然气项目，积极商谈油田大项目合作，探讨核电、水电合作新项目。双方还同意加强高铁、高技术、航天、金融等领域合作。

                    两国元首要求双方有关部门落实好《中俄共同举办庆祝第二次世界大战胜利70周年活动计划》，以此为重要契机，共同维护第二次世界大战胜利成果和战后国际秩序。

                    两国元首共同见证了一系列双边合作协议的签署，包括《关于通过中俄西线管道自俄罗斯联邦向中华人民共和国供应天然气领域合作的备忘录》、《中国石油天然气集团公司与俄罗斯天然气工业公司关于经中俄西线自俄罗斯向中国供应天然气的框架协议》。

                    又讯 据新华社电 俄罗斯、日本、越南、菲律宾、泰国、新加坡、巴布亚新几内亚、韩国、新西兰、澳大利亚、马来西亚、文莱等经济体领导人9日抵达北京，出席亚太经合组织领导人非正式会议。

                    他们是：俄罗斯总统普京、日本首相安倍晋三、越南国家主席张晋创、菲律宾总统阿基诺、泰国总理巴育、新加坡总理李显龙、巴布亚新几内亚总理奥尼尔、韩国总统朴槿惠、新西兰总理约翰·基、澳大利亚总理阿博特、马来西亚总理纳吉布、文莱苏丹哈桑纳尔。

                    焦点1会见梁振英

                    听取梁振英对香港当前形势和特区政府工作情况的汇报

                    习近平：支持港府维护法治权威

                    据新华社电 国家主席习近平9日上午在人民大会堂会见了来北京出席亚太经合组织第二十二次领导人非正式会议的香港特别行政区行政长官梁振英。

                    习近平听取了梁振英对香港当前形势和特区政府工作情况的汇报。习近平指出，十八届四中全会提出了全面推进依法治国总目标，强调依法保障“一国两制”实践，保持香港、澳门长期繁荣稳定，依法保护港澳同胞利益。这是我国推进国家治理体系和治理能力现代化迈出的重要一步，对全面准确贯彻“一国两制”方针和基本法、促进香港长治久安具有重要意义。中央政府充分肯定、全力支持行政长官和特区政府依法施政，特别是为维护法治权威、维护社会秩序所做的大量工作。

                    习近平强调，中央政府将继续坚定不移贯彻“一国两制”方针和基本法，坚定不移支持香港依法推进民主发展，坚定不移维护香港长期繁荣稳定。希望香港各界在行政长官梁振英和特区政府带领下，把握历史机遇，依法落实普选，共同谱写香港民主发展新篇章。

                    焦点2会见萧万长

                    习近平：尊重彼此社会制度选择

                    两岸关系遇到困难、阻力在所难免，越是这样越需要加强交流

                    据新华社电 中共中央总书记习近平9日在人民大会堂会见台湾两岸共同市场基金会荣誉董事长萧万长一行。

                    习近平指出，两岸双方在坚持“九二共识”、反对“台独”的共同政治基础上建立并持续增进互信，是确保两岸关系和平发展正确方向和良好势头的关键。由于两岸间存在一些差异等原因，两岸关系遇到一些困难和阻力在所难免。越是这样越需要加强交流、增进互信，保持良性互动、相向而行。要尊重彼此对发展道路和社会制度的选择。

                    习近平指出，两岸交流合作前景广阔。希望两岸双方共同努力，排除干扰，为扩大和深化两岸经济、文化、科技、教育等各领域交流合作采取更多积极措施。

                    萧万长表示，两岸共同开创的台海和平稳定发展大局得之不易，应该共同珍惜。应坚持巩固“九二共识”，加强两岸制度化经济合作，实现中华民族的繁荣昌盛。
    '''
    vendorids = { "vendor1_id" : allvendors[0][0], "vendor2_id" : allvendors[1][0], "vendor3_id" : allvendors[2][0], "vendor4_id" : allvendors[3][0], "vendor5_id" : allvendors[4][0] }
    productnames = {
        "name1" : "自道精舍咏春拳培训班", 
        "name2" : "2014单项夏令营：刘军足球夏令营", 
        "name3" : "2014协和运动夏令营", 
        "name4" : "2014单项夏令营：拼搏体育儿童暑假网球提高班" }
    prices= {"price1" : 1500.00, "price2" : 2400.00, "price3" : 1800, "price4" : 3600, "price5" : 5000, "price6" : 3000.00}
    status= {"status1" : 1, "status2" : 0}

    product_avatar = "ProductAvatar"
    product_area = "Shanghai"
    
    for product_type in range(1, 7):
        allitems = db.QueryCategories(0, 0, product_type)
        for item in allitems:
            index = 0
            for vendorinfo in allvendors:
                index += 1
                product_item = item[1]
                product_applicableage = random.randint(0, 5)
                product_price = prices["price%d" % random.randint(1, 6)]
                product_dividedrate = 0.3
                product_status = status["status%d" % random.randint(1, 2)]
                product_auditstatus = status["status%d" % random.randint(1, 2)]
                product_vendorid = vendorinfo[0]
                product_name = productnames["name%d" % random.randint(1, 4)]
                product_travelstartplace = str(random.randint(1000000, 9000000))
                product_travelendplace = str(random.randint(1000000, 9000000))
                product_traveldays = random.randint(10, 80)
                product_description = description
                product_paymentdescription = description
                product_precautions = description
                product_eventbegintime = None
                product_eventendtime = None
                product_availabletime = None
                product_couponwhenorder = None
                product_couponwhenactivate = None
                product_couponrestriction = None
                product_isrecommendedproduct = 0

                if product_type == 3:
                    product_eventbegintime = strftime("%Y-%m-%d")
                    product_eventendtime = strftime("%Y-%m-%d")
                    product_availabletime = strftime("%Y-%m-%d")
                    product_couponwhenorder = 50.0
                    product_couponwhenactivate = 50.0
                    product_couponrestriction = "No Limit"

                if product_type == 4:
                    product_eventbegintime = strftime("%Y-%m-%d")
                    product_eventendtime = strftime("%Y-%m-%d")
                    product_availabletime = strftime("%Y-%m-%d")

                if product_type == 5:
                    product_availabletime = strftime("%Y-%m-%d")

                if index % 2 == 0:
                    product_status = 1
                    product_auditstatus = 1

                if index % 4 == 0:
                    product_isrecommendedproduct = 1

                db.AddProduct({"product_vendorid" : product_vendorid, "product_name" : product_name, "product_type" : product_type, "product_avatar" : product_avatar, "product_area" : product_area, 
                    "product_applicableage" : product_applicableage, "product_item" : product_item, "product_price" : product_price, "product_dividedrate" : product_dividedrate, 
                    "product_status" : product_status, "product_auditstatus" : product_auditstatus, "product_travelstartplace" : product_travelstartplace, 
                    "product_travelendplace" : product_travelendplace, "product_traveldays" : product_traveldays, "product_eventbegintime" : product_eventbegintime, 
                    "product_eventendtime" : product_eventendtime, "product_availabletime" : product_availabletime, "product_couponwhenorder" : product_couponwhenorder, 
                    "product_couponwhenactivate" : product_couponwhenactivate, "product_couponrestriction" : product_couponrestriction, "product_description" : product_description,
                    "product_paymentdescription" : product_paymentdescription, "product_precautions" : product_precautions, "product_isrecommendedproduct" : product_isrecommendedproduct })
                print "Creating product ..."

def createScenes():
    db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)

    allproducts = db.QueryProducts(0, 0, 0, 0)
    scenenames = {"name1" : "外教班-16课时", 
                  "name2" : "外教班-32课时", 
                  "name3" : "外教班-48课时", 
                  "name4" : "中教班-16课时", 
                  "name5" : "中教班-32课时",
                  "name6" : "中教班-48课时"}
    locations =  {"location1" : "徐汇区", 
                  "location2" : "黄浦区", 
                  "location3" : "卢湾区", 
                  "location4" : "静安区", 
                  "location5" : "松江区", 
                  "location6" : "嘉定区" }
    timeperiods= {"period1" : "周一上午 8:00 - 10:00", 
                  "period2" : "周二下午 13:00 - 14:00", 
                  "period3" : "周三上午 10:00 - 12:00", 
                  "period4" : "周四下午 14:00 - 15:00", 
                  "period5" : "周五上午 7:00 - 9:00", 
                  "period6" : "周六下午 15:00 - 18:00", }

    for productinfo in allproducts:
        for i in range(5):
            scene_productid = productinfo[0]
            scene_time1 = "not defined"
            scene_time2 = "not defined"
            scene_maxpeople = random.randint(30, 90)
            scene_fullprice = float("%.2f" % random.uniform(7000.0, 9000.0))
            scene_childprice = float("%.2f" % random.uniform(6000.0, 7000.0))
            scene_name = scenenames["name%d" % random.randint(1, 6)]
            scene_locations = locations["location%d" % random.randint(1, 6)]
            scene_timeperiod = timeperiods["period%d" % random.randint(1, 6)]
            scene_marketprice = float("%.2f" % random.uniform(9000.0, 10000.0))
            scene_points = random.uniform(100.0, 300.0)
            scene_promotionprice = None
            scene_promotionbegintime = None
            scene_promotionendtime = None
            if scene_productid % 7 == 0:
                scene_promotionprice = random.uniform(5000.0, 6000.0)
                scene_promotionbegintime = strftime("%Y-%m-%d")
                scene_promotionendtime = strftime("%Y-%m-%d")
            scene_description = '''昨日是APEC调休放假第二天，机动车单双号限行，全天道路畅通。昨日，北京市交通委主任周正宇介绍了APEC期间北京交通服务保障情况。他表示，11月3日单双号限行以来，城市道路交通拥堵指数下降70%，单双号限行效果明显。目前，相关部门正在对限行后的交通和环保数据进行监测，此次限行结束后将发布相关报告。

据介绍，此次启动机动车单双号限行以来，城市道路交通拥堵指数降低了70%。公交客流增加了10%，地铁客流增加了5%。为应对公共交通客流增加，公交车增加了400辆，地铁也增加了班次。

周正宇介绍，放假首日，高速进出京客流为125万，相比较黄金周首日下降30%，属于完全畅通状态。周正宇表示，这种“完全畅通”状态将保持到12日。
            '''
            db.AddScene(sceneinfo={ "scene_productid" : scene_productid, "scene_time1" : scene_time1, "scene_time2" : scene_time2, "scene_maxpeople" : scene_maxpeople, "scene_fullprice" : scene_fullprice, 
                "scene_childprice" : scene_childprice, "scene_name" : scene_name, "scene_locations" : scene_locations, "scene_timeperiod" : scene_timeperiod, 
                "scene_marketprice" : scene_marketprice, "scene_points" : scene_points, "scene_promotionprice" : scene_promotionprice, 
                "scene_promotionbegintime" : scene_promotionbegintime, "scene_promotionendtime" : scene_promotionendtime, "scene_description" : scene_description })
            print "Creating scene ..."

def createAds():
    db = DbHelper()

    for i in range(100):
        ads_publisher = "username_%04d" % random.randint(1, 100)
        ads_platform = random.randint(1, 3)
        ads_position = random.randint(1, 5)
        ads_avatar = "AdsAvatar"
        ads_externalproductid = random.randint(20, 50)
        ads_begintime = strftime("%Y-%m-%d %H:%M:%S")
        ads_endtime = strftime("%Y-%m-%d %H:%M:%S")
        ads_sortweight = random.randint(1, 100)
        ads_auditstate = 0
        ads_state = 0

        if i % 9 == 0:
            ads_auditstate = 1
            ads_state = 1

        db.AddAds({ "ads_publisher" : ads_publisher, "ads_platform" : ads_platform, "ads_position" : ads_position, "ads_avatar" : ads_avatar, 
            "ads_externalproductid" : ads_externalproductid, "ads_begintime" : ads_begintime, "ads_endtime" : ads_endtime, "ads_sortweight" : ads_sortweight,
            "ads_state" : ads_state, "ads_auditstate" : ads_auditstate })
        print "Creating ads %r" % i

def createArticles():
    db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)

    alltitles = { "title1" : "中国现有55种死刑罪多半为非暴力犯罪", 
                  "title2" : "2011年全球仅20国执行死刑", 
                  "title3" : "李嘉诚李兆基等富豪就占中表态", 
                  "title4" : "赴台交流大陆女生被台间谍威逼利诱策反", 
                  "title5" : "中办国办:历史建筑公园等下月起严禁设私人会所", 
                  "title6" : "立法机关拟出法律解释:父母姓外可选其他姓氏", 
                  "title7" : "中纪委:有领导干部坐公交打出租去参加宴请", 
                  "title8" : "江西厅官预感苏荣要出事 借口赝品向其妻讨名画", 
                  "title9" : "陆军六大集团军主官换人 空军空降兵15军换政委", 
                  "title10" : "最高检修订举报规定 首次明确举报人具体权利" }
    allparentcategories = db.QueryCategories(0, 0, 99)
    for i in range(100):
        articles_auditstate = random.randint(0, 1)
        articles_title = alltitles["title%d" % random.randint(1, 10)]
        articles_content = str(random.randint(10000, 99999))
        articles_publisher = str(random.randint(10000, 99999))
        articles_category = allparentcategories[random.randint(0, len(allparentcategories) - 1)][2]
        articles_avatar = "None"
        articles_externalurl = "None"
        articles_sortweight = random.randint(1, 100)
        articles_content = '''
            LAS VEGAS -- Automakers and equipment makers have incorporated rear-view cameras into rear-view mirrors, giving drivers a better view behind their cars, but App-Tronics takes the idea further with its SmartNav 5, bringing all the capabilities of a Windows CE computer into the mirror.

SmartNav 5 projects a 5-inch screen into the middle of its rear-view mirror. The projection is translucent, letting drivers focus on the mirror image instead of the screen if they so choose. The device features automatic day and night modes, changing the brightness so as not to interfere with the simple mirror projection.

The SmartNav 5 rear-view mirror casing includes a small computer running Windows CE, hosting a variety of useful driving apps. It runs iGo navigation software, giving drivers turn-by-turn route guidance. There is a video recorder tied to a front-facing camera, which works as an incident recorder in case of a crash, similar to current dash-mounted crash recorders. That recorder can also take input from a separate camera mounted on the rear of the car, the rear camera also serving as a live rear view for the driver when the car is in reverse.

App-Tronics even includes a Bluetooth phone connection, as the SmartNav 5 can be wired to the car's audio system. It shows performance gauges, such as a digital speedometer, but this data is derived from the GPS chip in the unit, rather than the car's own CAN bus system.

One of the more intriguing features requires an App-Tronics accessory radar detector mounted on the front of the car. SmartNav 5 shows an alert on its screen whenever the accessory detects police radar, and includes a live database of recorded speed traps.

The SmartNav5 not only includes a series of buttons along the lower bezel to bring up different features, but also incorporates a touchscreen so drivers can enter addresses for navigation. The full, icon-covered screen of the SmartNav 5 may seem like a safety hazard, but drivers can choose different themes that limit the display to as little as three icons.

App-Tronics offers the SmartNav 5 as a complete rear-view mirror replacement for cars, or as a clip-on device, covering the existing rear-view mirror. In either case, the device draws power from a wired 12-volt connection to the car.

The SmartNav 5 won the Best in Show award for Mobile Electronics at the 2014 SEMA aftermarket automotive show.
         '''

        db.AddArticle({ "articles_auditstate" : articles_auditstate, "articles_title" : articles_title, "articles_content" : articles_content,
                        "articles_publisher" : articles_publisher, "articles_category" : articles_category, "articles_avatar" : articles_avatar,
                        "articles_externalurl" : articles_externalurl, "articles_sortweight" : articles_sortweight, "articles_content" : articles_content })
        print "Creating article %r" % i

def createOrders():
    db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)
    allfrontendusers = db.QueryUsers(0, 0, 1)
    allvendorusers = db.QueryUsers(0, 0, 2)
    allproducts = db.QueryProducts(0, 0)

    prices= {"price1" : 1500.00, "price2" : 2400.00, "price3" : 1800, "price4" : 3600, "price5" : 5000, "price6" : 3000.00}
    prepaids = {"price1" : 500.00, "price2" : 400.00, "price3" : 800, "price4" : 600, "price5" : 500, "price6" : 300.00}
    productcounts = {"count1" : 3, "count2" : 33, "count3" : 23, "count4" : 87, "count5" : 5, "count6" : 9}

    for userinfo in allfrontendusers:
        for i in range(10):
            preorder_userid = userinfo[0]
            preorder_productid = allproducts[random.randint(1, len(allproducts) - 1)][0]
            productinfo = db.QueryProductInfo(preorder_productid)
            preorder_vendorid = productinfo[1]
            preorder_prepaid = prepaids["price%d" % random.randint(1, 6)]
            preorder_counts = productcounts["count%d" % random.randint(1, 6)]
            preorder_fullprice = prices["price%d" % random.randint(1, 6)]
            productscenes = db.QueryProductScenes(preorder_productid)
            # if len(productscenes) > 1:
            preorder_sceneid = random.randint(1, 10)
            preorder_outtradeno = create_trade_no(preorder_userid, preorder_productid, preorder_sceneid, preorder_counts, 0)
            # else:
            #     preorder_sceneid = 1
            pps = random.randint(0,1)
            prs = random.randint(0,2) if pps else 0
            poe = preorder_fullprice * 0.1 * random.randint(1,10) if prs else None
            db.AddPreorder({ "preorder_userid" : preorder_userid, "preorder_productid" : preorder_productid, 
                "preorder_prepaid" : preorder_prepaid, "preorder_counts" : preorder_counts, 
                "preorder_fullprice" : preorder_fullprice, "preorder_sceneid" : preorder_sceneid, 
                "preorder_paymentstatus": pps,
                "preorder_refundstatus": prs,
                "preorder_outrefundno": db.CreateOutRefundNO() if prs else None,
                "preorder_outrefundfee": poe,
                "preorder_appraisal": "I don't like it" if prs else None,
                "preorder_outtradeno" : preorder_outtradeno })
            print "Creating order  ..."

def createComments():
    db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)
    allfrontendusers = db.QueryUsers(0, 0, 1)
    allproducts = db.QueryProducts(0, 0)
    allcommentcontents = {
        "comment1" : "商品不错，客服态度'好得不得了'啊。", 
        "comment2" : "下次再来买。", 
        "comment3" : "快递很及时，下次还来买。", 
        "comment4" : "老师态度很差，以后不来了。", 
        "comment5" : "培训效果不明显，再也不来了。", 
        "comment6" : "商品质量不错，就是有些旧。" }

    for productinfo in allproducts:
        for userinfo in allfrontendusers:
            comment_userid = userinfo[0]
            comment_productid = productinfo[0]
            comment_content = allcommentcontents["comment%d" % random.randint(1, 6)]
            comment_level = random.randint(-1, 1)
            comment_score = random.randint(1, 5)

            db.AddComment({ "comment_userid" : comment_userid, "comment_productid" : comment_productid, 
                "comment_content" : comment_content, "comment_level" : comment_level, "comment_score" : comment_score })
            print "Creating comment ..."

def createCoupons():
    db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)
    allfrontendusers = db.QueryUsers(0, 0, 1)

    for i in range(100):
        coupon_userid = allfrontendusers[random.randint(1, 15)][0]
        coupon_amount = random.randint(1000, 9999)

        coupon_restrictions = ""
        coupon_validtime = strftime("%Y-%m-%d %H:%M:%S")

        db.AddCoupon({ "coupon_userid" : coupon_userid, "coupon_amount" : coupon_amount, "coupon_restrictions" : coupon_restrictions, "coupon_validtime" : coupon_validtime })
        print "Creating coupon %r" % i

def createMessages():
    db = DbHelper(cursorclass=Settings.DB_ARRAYCURSOR)
    allfrontendusers = db.QueryUsers(0, 0, 1)

    alltitles = { "title1" : "阿里双十一13小时31分交易额突破362亿 超去年全天总额", 
                  "title2" : "俄罗斯货币贬值引来旅游人士购买iPhone 6", 
                  "title3" : "适度玩动作游戏可提高图案区别能力", 
                  "title4" : "LG新增第二条OLED屏幕生产线 总出货量是此前四倍", 
                  "title5" : "微软：Cortana 将很快登陆其他操作系统平台", 
                  "title6" : "[组图]《轩辕剑6外传》再曝神秘女角色：季阳", 
                  "title7" : "累觉不爱了就与机器人Carl Sagan谈心吧", 
                  "title8" : "鸿海10月营收同比涨22% 受益苹果订单带动", 
                  "title9" : "只有6%的人从事儿时梦想的职业", 
                  "title10": "腾讯QQ v6.5.12968 正式版官方更新" }
    allcontents={ "content1" : "昨日，腾讯发布了QQ6.5正式版的v12968维护更新，6.5版主要新增“我的手机页”，电脑手机无缝对接；群资料卡，全新换装。广大QQ爱好者迷们赶快尝鲜使用试试吧！QQ V6.5 版本特性",
                  "content2" : "据国外媒体报道，微软公司近日举行了新闻发布会，宣布其人力资源执行总裁Lisa Brummel即将于年底退休，她的继承人Kathleen Hogan将在11月28日开始接替她的位置。Lisa Brummel，于2005年5月成为微软人力资源部门总监，已经任职长达25年。她也是微软高层领导团队中的三位女性主管这一，此前她也是继任前CEO鲍尔默的继任人选之一。",
                  "content3" : "据路透社报道，两位知情人士透露，苹果在向企业发起迄今最有侵略性的攻势，调派专门的销售团队跟花旗集团等潜在客户展开洽谈，同时与十多家应用开发商进行合作。分析称，该公司想要通过扩大其在企业市场的触角来抵消增长日渐减速（iPad尤其明显，其销量已连续三个季度出现下降）带来的不良影响。",
                  "content4" : "据彭博社报道，在会见了小米CEO雷军、联想CEO杨元庆后，黑莓CEO程守宗表示，有意通过合作在中国实现扩张。程守宗昨天在参加APEC CEO峰会时接受采访时称，黑莓的优势在于安全、加密和隐私，而这些正是中国非常需要的。黑莓可能有机会在技术授权、分销或制造领域达成合作。",
                  "content5" : "周二中美就信息技术贸易协议(ITA)扩大范围达成一致，ITA将取消高科技产品的关税。白宫在一封电邮中表示，协议达成将有利于美国科技产品的出口。据外媒报道，周二中美就信息技术贸易协议(ITA)扩大范围达成一致，ITA将取消高科技产品的关税。白宫在一封电邮中表示，协议达成将有利于美国科技产品的出口。",
                  "content6" : "援引诺基亚官方博客消息首款微软品牌Lumia 535正式发布，该机配备分辨率为960*540的5.0英寸屏幕，1.2GHz的高通骁龙200四核处理器（MSM8212），500万的前置定焦摄像头和500万后置摄像头，1GB内存和8GB的内置储存，支持最高128GB的MicroSD卡扩展。Lumia 535双卡双待在各地区存在差异，目前预计税前售价约为110欧。",
                  "content7" : "今年8月，我们曾介绍一款可助大麻哈鱼轻松飞越大坝的“大炮”。提出这款产品的则是一家名为Whooshh Innovations的公司。说实在的，相信大部分人多多少少都动过“这是一款多么奇葩的产品”的想法。而现在，囧·奥利鹅决定将它的奇葩彻底放大。",
                  "content8" : "江南公安分局西关派出所民警接到报警：一名网吧老板称，有一名块头很大的男子在网吧闹事。民警立刻赶到了现场。民警果然看到一个背影高大肥胖的男子正在网吧里和老板吵架。民警上前劝阻，仔细一看，这不是一名成年男子，分明还是个孩子。网吧老板无奈地说，闹事的男孩一定要在网吧上网，但根据规定到网吧上网必须提供身份证，可是男孩却说没有。网管不让他上网，男孩居然一把推开了网管。",
                  "content9" : "从昨天下午6点开始，吴丽珍要作为客服，上班到今天凌晨3点。因为今天是“双十一”。 刚过完20岁生日的吴丽珍，是浙江工商大学会计专业大二学生。两周前，她在一家兼职网站，看到了XX电商的招聘信息，然后去参加了面试和培训。",
                  "content10": "“一部价值千元的手机，现金500元”，这就是打工仔许龙(化名)深夜入户抢劫的全部“战利”所得。但他如何都未想到，自己的无知不但被判处罚金一万元，更换来了十年六个月的牢狱之灾。11日，河南省郑州市二七区法院公布了这起入户抢劫案的判决。被告人许龙以暴力、胁迫方法入户强行劫取他人财物，依法被处有期徒刑十年零六个月，并处罚金人民币一万元，剥夺政治权利一年。" }
    for userinfo in allfrontendusers:
        for i in range(50):
            msgreceiver = []
            for i in range(10):
                msgreceiver.append(str(allfrontendusers[random.randint(1, len(allfrontendusers) - 1)][0]))

            message_type = random.randint(1, 2)
            message_state = random.randint(0, 1)
            message_title = alltitles["title%d" % random.randint(1, 10)]
            message_publisher = "一起动"
            message_externalurl = "None"
            message_externalproductid = 0
            message_sendtime = strftime("%Y-%m-%d")
            message_receiver = json.dumps(msgreceiver)
            message_content = allcontents["content%d" % random.randint(1, 10)]

            db.AddMessage({ "message_type" : message_type, "message_state" : message_state, "message_title" : message_title,
                "message_publisher" : message_publisher, "message_externalurl" : message_externalurl, "message_externalproductid" : message_externalproductid,
                "message_sendtime" : message_sendtime, "message_receiver" : message_receiver, "message_content" : message_content })
            print "Creating message ..."

def createSearchKeywords():
    db = DbHelper()
    allkeywords = { "key1" : "蓝球", "key2" : "足球", "key3" : "乒乓球", "key4" : "飞行球", "key5" : "羽毛球", 
        "key6" : "跆拳道", "key7" : "摔跤", "key8" : "柔道", "key9" : "击倒", "key10" : "游泳" }

    for i in range(100):
        db.AddSearchkeyword(allkeywords["key%d" % random.randint(1, 10)])

        print "Creating search keyword ..."

def initDatabase():
    createUsers()
    createCategories()
    createProducts()
    createScenes()
    createAds()
    createArticles()
    createOrders()
    createComments()
    createCoupons()
    createMessages()
    createSearchKeywords()

    print "initDatabase Done."

def main():
    initDatabase()

if __name__ == "__main__":
    main()

############################################################################################################################################################################################
