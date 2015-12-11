#!/usr/bin/env python
#-*-coding:utf-8-*-

# # # Author: Willson Zhang
# # # Date: Sep 20th, 2014
# # # Email: willson.zhang1220@gmail.com

import time, random, os, hashlib, MySQLdb, settings, socket
import json, re, uuid, logging, markdown, html5lib, cgi, string

from urllib import unquote
from urllib import quote
from html5lib import sanitizer
from crypter import Crypter
from datetime import timedelta, datetime as DateTime
from monthdelta import MonthDelta
from time import gmtime, strftime
from MySQLdb.cursors import DictCursor
from collections import OrderedDict
from itertools import groupby
from transform import Transform

import shutil
import uuid

import sys
import datetime
import random
import PyRSS2Gen

abspath = sys.path[0]

if settings.DEBUG_APP:
    logging.basicConfig(filename = os.path.join(os.getcwd(), 'log.txt'), level = logging.DEBUG)

pyver = tuple(getattr(sys.version_info, m) for m in ['major', 'minor', 'micro'])

if pyver[0] >= 3:
    from io import StringIO
else:
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO


class DbHelper:
    '''The mysql database helper class for python, realized with MySQLdb.
    '''
    dbHost = "unset"
    dbUser = "unset"
    dbPasswd = "unset"
    db = None
    cursorclass = None

    def __init__(self, host="localhost", user=settings.DB_USER, passwd=settings.DB_PASSWORD, cursorclass=settings.DB_CURSORCLASS):
        '''Init mysql database:
           1) create database if not exists;
           2) create related tables if not exists;
        '''

        if self.db:
            return

        self.dbHost      = host
        self.dbUser      = user
        self.dbPasswd    = passwd
        self.cursorclass = cursorclass
        self.db = MySQLdb.Connect(host=self.dbHost, user=self.dbUser, passwd=self.dbPasswd, charset='utf8', cursorclass=self.cursorclass)
        cursor  = self.db.cursor()

        cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '%s'" % settings.DB_NAME)
        result = cursor.fetchone()
        if result is None:
            cursor.execute("CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci" % settings.DB_NAME)
            self.db.select_db(settings.DB_NAME)

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS user_table(\
                user_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                user_name VARCHAR(128) UNIQUE NOT NULL, \
                user_password VARCHAR(128) NOT NULL, \
                user_phonenumber VARCHAR(16) NOT NULL, \
                user_email VARCHAR(128), \
                user_nickname VARCHAR(32), \
                user_interest TEXT, \
                user_avatar VARCHAR(255), \
                user_gender VARCHAR(2), \
                user_age INTEGER, \
                user_address TEXT, \
                user_payment REAL, \
                user_points REAL, \
                user_qqtoken VARCHAR(64), \
                user_qqopenid VARCHAR(64), \
                user_sinatoken VARCHAR(64), \
                user_sinauid VARCHAR(64), \
                user_registertime DATETIME NOT NULL, \
                user_role INTEGER NOT NULL, \
                user_permission TEXT, \
                user_vendorname VARCHAR(255), \
                user_vendorleadername VARCHAR(128), \
                user_vendorleaderidcardno VARCHAR(64), \
                user_vendorcreditrating INTEGER, \
                user_emailpasskey VARCHAR(64), \
                user_vendorphonenumber VARCHAR(16), \
                user_vendoraddress TEXT, \
                user_vendorexperience INTEGER, \
                user_vendorcredit INTEGER NOT NULL DEFAULT 48, \
                user_vendorlicenseid VARCHAR(64), \
                user_vendorleaderphonenumber VARCHAR(16), \
                user_vendorbusinessscope VARCHAR(255), \
                user_vendordescription TEXT, \
                user_permissionstate INTEGER, \
                user_viplevel INTEGER, \
                user_vipexperience INTEGER, \
                user_birthday DATE, \
                user_adminrole INTEGER, \
                user_qietoken VARCHAR(64), \
                user_qieopenid VARCHAR(64), \
                deleteflag INTEGER, \
                user_registersource INTEGER NOT NULL DEFAULT 1, \
                user_registerip VARCHAR(64), \
                user_lastlogindatetime  DATETIME, \
                user_followcompetition  TEXT, \
                user_country_chs    VARCHAR(64), \
                user_country_eng    VARCHAR(64)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS useraddress_table(\
                useraddress_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                useraddress_userid INTEGER, \
                useraddress_recipients VARCHAR(255), \
                useraddress_address TEXT, \
                useraddress_phonenumber VARCHAR(128), \
                useraddress_zipcode VARCHAR(16)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS usertraveller_table(\
                usertraveller_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                usertraveller_userid INTEGER, \
                usertraveller_name VARCHAR(128), \
                usertraveller_type INTEGER, \
                usertraveller_idcardno VARCHAR(64)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS category_table(\
                category_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                category_name VARCHAR(128) NOT NULL, \
                category_description VARCHAR(128), \
                category_avatar VARCHAR(255), \
                category_parent INTEGER, \
                category_sortweight INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            for category_name, category_description in settings.INITIAL_PARENT_CATEGORY.items():
                self.AddCategory(categoryinfo={"category_name" : category_name, "category_description" : category_description, "category_parent" : 0 })

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS scene_table(\
                scene_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                scene_productid INTEGER NOT NULL, \
                scene_time1 VARCHAR(64), \
                scene_time2 VARCHAR(64), \
                scene_maxpeople INTEGER, \
                scene_fullprice REAL, \
                scene_childprice REAL, \
                scene_name VARCHAR(255), \
                scene_locations VARCHAR(255), \
                scene_timeperiod VARCHAR(255), \
                scene_marketprice REAL, \
                scene_points INTEGER, \
                scene_promotionprice REAL, \
                scene_promotionbegintime DATETIME, \
                scene_promotionendtime DATETIME, \
                scene_description TEXT, \
                deleteflag INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS comment_table(\
                comment_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                comment_userid INTEGER NOT NULL, \
                comment_productid INTEGER NOT NULL, \
                comment_content TEXT NOT NULL, \
                comment_time DATETIME NOT NULL, \
                comment_level INTEGER NOT NULL, \
                comment_score1 INTEGER, \
                comment_score2 INTEGER, \
                comment_score3 INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS product_table(\
                product_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                product_vendorid INTEGER NOT NULL, \
                product_name VARCHAR(255) NOT NULL, \
                product_availabletime DATETIME, \
                product_type INTEGER NOT NULL, \
                product_avatar VARCHAR(255), \
                product_area VARCHAR(32), \
                product_applicableage INTEGER, \
                product_item TEXT NOT NULL, \
                product_price REAL, \
                product_discounts REAL, \
                product_dividedrate REAL, \
                product_description TEXT, \
                product_status INTEGER, \
                product_maxdeductiblepoints REAL, \
                product_auditstatus INTEGER, \
                product_isadproduct INTEGER, \
                product_isrecommendedproduct INTEGER NOT NULL, \
                product_recommendbegintime DATETIME, \
                product_recommendendtime DATETIME, \
                product_allowviplevel INTEGER, \
                product_balancepaytime DATETIME, \
                product_paymentdescription TEXT, \
                product_precautions TEXT, \
                product_auditfailreason VARCHAR(255), \
                product_auditfaildescription VARCHAR(255), \
                product_sortweight INTEGER, \
                product_traveltype INTEGER, \
                product_travelstartplace VARCHAR(255), \
                product_travelendplace VARCHAR(255), \
                product_traveldays INTEGER, \
                product_eventbegintime DATE, \
                product_eventendtime DATE, \
                product_couponwhenorder REAL, \
                product_couponwhenactivate REAL, \
                product_couponrestriction TEXT, \
                deleteflag INTEGER, \
                product_inputuserid INTEGER NOT NULL DEFAULT 1, \
                product_inputtime DATETIME NOT NULL DEFAULT NOW(), \
                product_purchaselimit INTEGER, \
                product_parentitem VARCHAR(255)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS preorder_table(\
                preorder_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                preorder_userid INTEGER NOT NULL, \
                preorder_productid INTEGER NOT NULL, \
                preorder_vendorid INTEGER NOT NULL, \
                preorder_buytime DATETIME NOT NULL, \
                preorder_paytime DATETIME, \
                preorder_settletime DATETIME, \
                preorder_prepaid REAL NOT NULL, \
                preorder_counts INTEGER NOT NULL, \
                preorder_decuctamount REAL, \
                preorder_fullprice REAL NOT NULL, \
                preorder_sceneid INTEGER NOT NULL, \
                preorder_paymentstatus INTEGER NOT NULL, \
                preorder_joinstatus INTEGER NOT NULL, \
                preorder_refundstatus INTEGER, \
                preorder_appraisal TEXT, \
                preorder_paymentcode VARCHAR(64), \
                preorder_usedpoints REAL, \
                preorder_deliveryaddressid INTEGER, \
                preorder_deliverystatus INTEGER, \
                preorder_paymentcode_createtime DATETIME, \
                preorder_paymentcode_usetime DATETIME, \
                preorder_paymentcode_status INTEGER, \
                preorder_contacts VARCHAR(128), \
                preorder_contactsphonenumber VARCHAR(16), \
                preorder_travellerids TEXT, \
                preorder_invoicetype INTEGER, \
                preorder_invoiceheader VARCHAR(255), \
                preorder_coupondiscount REAL, \
                preorder_paymentmethod VARCHAR(128), \
                preorder_remarks TEXT, \
                preorder_outtradeno VARCHAR(255), \
                preorder_invoicedeliveryaddress VARCHAR(255), \
                deleteflag INTEGER, \
                preorder_notes TEXT,\
                preorder_outrefundno VARCHAR(64),\
                preorder_outrefundfee FLOAT(12,2), \
                preorder_tradeno    VARCHAR(128), \
                preorder_rewardpoints   INTEGER DEFAULT 0) \
                ENGINE = MyISAM AUTO_INCREMENT = 100000 DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS apiuuid_table(\
                apiuuid_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                apiuuid_value VARCHAR(48) UNIQUE NOT NULL, \
                INDEX(apiuuid_value)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS coupon_table(\
                coupon_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                coupon_userid INTEGER NOT NULL, \
                coupon_serialnumber VARCHAR(64) NOT NULL UNIQUE, \
                coupon_valid INTEGER NOT NULL, \
                coupon_amount REAL NOT NULL, \
                coupon_createtime DATETIME NOT NULL, \
                coupon_usetime DATETIME, \
                coupon_restrictions TEXT, \
                coupon_type INTEGER, \
                coupon_validtime DATETIME, \
                coupon_source BIGINT(20), \
                coupon_giftcode_deviceid VARCHAR(64) UNIQUE) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS complaints_table(\
                complaints_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                complaints_userid INTEGER, \
                complaints_orderid INTEGER, \
                complaints_reason VARCHAR(255), \
                complaints_description TEXT, \
                complaints_time DATETIME, \
                complaints_state INTEGER, \
                complaints_remarks TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS articles_table(\
                articles_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                articles_auditstate INTEGER, \
                articles_title VARCHAR(255), \
                articles_content TEXT, \
                articles_publisher VARCHAR(128), \
                articles_category VARCHAR(64), \
                articles_avatar VARCHAR(255), \
                articles_externalurl TEXT, \
                articles_externalproductid INTEGER, \
                articles_publishtime DATETIME, \
                articles_sortweight INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS ads_table(\
                ads_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                ads_auditstate INTEGER, \
                ads_state INTEGER, \
                ads_publisher VARCHAR(128), \
                ads_platform INTEGER, \
                ads_position INTEGER, \
                ads_avatar VARCHAR(255), \
                ads_externalurl TEXT, \
                ads_externalproductid INTEGER, \
                ads_begintime DATETIME, \
                ads_endtime DATETIME, \
                ads_sortweight INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS message_table(\
                message_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                message_type INTEGER, \
                message_state INTEGER, \
                message_title VARCHAR(255), \
                message_publisher VARCHAR(128), \
                message_externalurl TEXT, \
                message_externalproductid INTEGER, \
                message_sendtime DATETIME, \
                message_receiver TEXT, \
                message_content TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS searchkeyword_table(\
                searchkeyword_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                searchkeyword_text VARCHAR(255) UNIQUE NOT NULL, \
                searchkeyword_frequent INTEGER UNSIGNED, \
                searchkeyword_isrecommended INTEGER, \
                searchkeyword_sortweight INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS links_table(\
                links_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                links_show INTEGER, \
                links_name VARCHAR(255), \
                links_url VARCHAR(255), \
                links_sortweight INTEGER, \
                links_logourl VARCHAR(255)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS promotion_reward_record_table ( \
                promotion_reward_record_id bigint(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                user_id int(11) DEFAULT NULL, \
                promotion_id bigint(20) DEFAULT NULL, \
                promotion_reward_id bigint(20) DEFAULT NULL, \
                promotion_reward_record_time datetime DEFAULT NULL, \
                promotion_name varchar(255) DEFAULT NULL, \
                promotion_reward_type varchar(255) DEFAULT NULL, \
                promotion_reward_name varchar(255) DEFAULT NULL) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS promotion_reward_table ( \
                promotion_reward_id bigint(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                promotion_id bigint(20) NOT NULL, \
                promotion_reward_name varchar(255) DEFAULT NULL, \
                promotion_reward_type varchar(45) DEFAULT NULL, \
                promotion_reward_prompt varchar(255) DEFAULT NULL, \
                promotion_reward_probability int(11) DEFAULT NULL, \
                promotion_reward_max_per_user int(11) DEFAULT NULL, \
                promotion_reward_max_per_cycle int(11) DEFAULT NULL, \
                promotion_reward_cycle_period int(11) DEFAULT NULL, \
                promotion_reward_date_slot datetime DEFAULT NULL, \
                promotion_coupon_type INTEGER, \
                promotion_coupon_amount REAL, \
                promotion_coupon_restrictions TEXT, \
                promotion_coupon_validtime DATETIME) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS promotion_table ( \
                promotion_id bigint(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                promotion_name varchar(255) NOT NULL, \
                promotion_address varchar(255) DEFAULT NULL, \
                promotion_start_date datetime DEFAULT NULL, \
                promotion_end_date datetime DEFAULT NULL, \
                promotion_attendees int(11) DEFAULT '0', \
                promotion_status int(11) DEFAULT '0', \
                promotion_created_date datetime DEFAULT NULL, \
                promotion_last_modified_date datetime DEFAULT NULL, \
                promotion_last_modified_by int(11) DEFAULT NULL, \
                promotion_default_drawing_times_per_day int(11) NOT NULL DEFAULT '0', \
                promotion_max_drawing_times int(11)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS vote_table ( \
                vote_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                vote_name VARCHAR(255) NOT NULL, \
                vote_status INTEGER NOT NULL, \
                vote_begintime DATETIME NOT NULL, \
                vote_endtime DATETIME NOT NULL, \
                vote_permission INTEGER NOT NULL, \
                vote_countmode INTEGER NOT NULL, \
                vote_countwhenshare INTEGER, \
                vote_description TEXT, \
                vote_maxresult_count INTEGER UNSIGNED NOT NULL, \
                vote_reserve1 TEXT, \
                vote_reserve2 TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS vote_option_table ( \
                vote_option_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                vote_option_voteid BIGINT(20) UNSIGNED NOT NULL, \
                vote_option_title VARCHAR(255) NOT NULL, \
                vote_option_description TEXT, \
                vote_option_sortweight INTEGER, \
                vote_option_avatar VARCHAR(255), \
                vote_option_video TEXT, \
                vote_option_result TEXT, \
                vote_option_reserve1 TEXT, \
                vote_option_reserve2 TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            # CREATE TABLE IF NOT EXISTS vote_table (vote_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, vote_name VARCHAR(255) NOT NULL, vote_status INTEGER NOT NULL, vote_begintime DATETIME NOT NULL, vote_endtime DATETIME NOT NULL, vote_permission INTEGER NOT NULL, vote_countmode INTEGER NOT NULL, vote_countwhenshare INTEGER, vote_description TEXT, vote_maxresult_count INTEGER UNSIGNED NOT NULL, vote_reserve1 TEXT, vote_reserve2 TEXT) ENGINE = MyISAM DEFAULT CHARSET = utf8
            # CREATE TABLE IF NOT EXISTS vote_option_table (vote_option_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, vote_option_voteid BIGINT(20) UNSIGNED NOT NULL, vote_option_title VARCHAR(255) NOT NULL, vote_option_description TEXT, vote_option_sortweight INTEGER, vote_option_avatar VARCHAR(255), vote_option_video TEXT, vote_option_result TEXT, vote_option_reserve1 TEXT, vote_option_reserve2 TEXT) ENGINE = MyISAM DEFAULT CHARSET = utf8

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS temp1_table ( \
                temp1_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                temp1_name VARCHAR(512) NOT NULL, \
                temp1_phonenumber VARCHAR(512) NOT NULL, \
                temp1_email VARCHAR(512) NOT NULL, \
                temp1_reserve1 VARCHAR(512), \
                temp1_reserve2 VARCHAR(512), \
                temp1_reserve3 VARCHAR(512), \
                temp1_gender INTEGER NOT NULL DEFAULT 1, \
                temp1_age INTEGER NOT NULL DEFAULT 0, \
                temp1_competition_category INTEGER NOT NULL DEFAULT 1, \
                temp1_sword_category INTEGER NOT NULL DEFAULT 1, \
                temp1_team_number INTEGER NOT NULL DEFAULT 1, \
                temp1_type INTEGER NOT NULL DEFAULT 1) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS temp1_staff_table ( \
                temp1_staff_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                temp1_staff_extid INTEGER UNSIGNED NOT NULL, \
                temp1_staff_name VARCHAR(512) NOT NULL, \
                temp1_staff_age VARCHAR(512) NOT NULL, \
                temp1_staff_reserve1 VARCHAR(512), \
                temp1_staff_reserve2 VARCHAR(512), \
                temp1_staff_reserve3 VARCHAR(512), \
                temp1_staff_phonenumber VARCHAR(512) NOT NULL DEFAULT '0') \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            # CREATE TABLE IF NOT EXISTS temp1_table (temp1_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, temp1_name VARCHAR(512) NOT NULL, temp1_phonenumber VARCHAR(512) NOT NULL, temp1_email VARCHAR(512) NOT NULL, temp1_reserve1 VARCHAR(512), temp1_reserve2 VARCHAR(512), temp1_reserve3 VARCHAR(512)) ENGINE = MyISAM DEFAULT CHARSET = utf8
            # CREATE TABLE IF NOT EXISTS temp1_staff_table (temp1_staff_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, temp1_staff_extid INTEGER UNSIGNED NOT NULL, temp1_staff_name VARCHAR(512) NOT NULL, temp1_staff_age VARCHAR(512) NOT NULL, temp1_staff_reserve1 VARCHAR(512), temp1_staff_reserve2 VARCHAR(512), temp1_staff_reserve3 VARCHAR(512)) ENGINE = MyISAM DEFAULT CHARSET = utf8

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS competition_table ( \
                competition_id bigint(20) unsigned PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                competition_name varchar(255) NOT NULL, \
                competition_start_time datetime DEFAULT NULL, \
                competition_end_time datetime DEFAULT NULL, \
                competition_registration_start_time datetime DEFAULT NULL, \
                competition_registration_end_time datetime DEFAULT NULL, \
                competition_location varchar(255) DEFAULT NULL, \
                competition_registration_fee decimal(12,4) DEFAULT NULL, \
                competition_stock int(11) DEFAULT NULL, \
                competition_registration_limit int(11) DEFAULT NULL, \
                competition_registration_players_lower int(11) DEFAULT NULL, \
                competition_registration_players_upper int(11) DEFAULT NULL, \
                competition_created_date datetime DEFAULT NULL, \
                competition_intro longtext, \
                competition_mustknow longtext, \
                competition_prod_status tinyint(4) DEFAULT '1', \
                competition_images varchar(255) DEFAULT NULL, \
                competition_registration_form_id bigint(20) DEFAULT NULL, \
                competition_product_id int(11) DEFAULT NULL) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS competition_registration_form_table ( \
                competition_registration_form_id bigint(20) unsigned PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                user_id int(11) DEFAULT NULL, \
                competition_registration_form_name varchar(255) DEFAULT NULL) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS competition_registration_form_field_table ( \
                competition_registration_form_field_id bigint(20) unsigned PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                competition_registration_form_field_name varchar(45) DEFAULT NULL, \
                competition_registration_form_field_description varchar(255) DEFAULT NULL, \
                competition_registration_form_field_type varchar(45) DEFAULT NULL, \
                competition_registration_form_field_is_mandatory tinyint(1) DEFAULT NULL, \
                competition_registration_form_field_extra varchar(1024) DEFAULT NULL, \
                competition_registration_form_id bigint(20) DEFAULT NULL, \
                competition_registration_form_field_is_required tinyint(1) DEFAULT NULL, \
                competition_registration_form_field_index int(11) DEFAULT NULL) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS competition_registration_form_data_table ( \
                competition_registration_form_data_id bigint(20) unsigned PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                competition_registration_form_id bigint(20) unsigned DEFAULT NULL, \
                competition_registration_form_field_id bigint(20) unsigned DEFAULT NULL, \
                competition_registration_form_field_name varchar(45) DEFAULT NULL, \
                competition_registration_form_field_type varchar(45) DEFAULT NULL, \
                competition_registration_form_field_phone varchar(45) DEFAULT NULL, \
                competition_registration_form_field_email varchar(255) DEFAULT NULL, \
                competition_registration_form_field_image varchar(255) DEFAULT NULL, \
                competition_registration_form_field_digits varchar(255) DEFAULT NULL, \
                competition_registration_form_field_text varchar(16384) DEFAULT NULL, \
                competition_registration_form_field_radio varchar(255) DEFAULT NULL, \
                competition_registration_form_field_dropdown varchar(255) DEFAULT NULL, \
                competition_registration_form_user_id int(11) DEFAULT NULL, \
                competition_registration_form_registration_id bigint(20) DEFAULT NULL, \
                competition_id bigint(20) DEFAULT NULL, \
                competition_registration_form_player_number int(11) DEFAULT NULL, \
                competition_registration_form_field_index int(11) DEFAULT NULL) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")
				
            cursor.execute("CREATE TABLE IF NOT EXISTS competition_registration_table ( \
                competition_registration_id bigint(20) unsigned PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                competition_registration_order_id bigint(20) DEFAULT NULL, \
                user_id bigint(20) DEFAULT NULL, \
                competition_id bigint(20) DEFAULT NULL, \
                competition_registration_time datetime DEFAULT NULL) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS activity_table(\
                activity_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                activity_productid  INTEGER NOT NULL, \
                activity_name   VARCHAR(512) NOT NULL, \
                activity_status INTEGER NOT NULL, \
                activity_categoryid INTEGER, \
                activity_mark   INTEGER, \
                activity_price  REAL, \
                activity_begintime  DATETIME, \
                activity_endtime    DATETIME, \
                activity_sortweight INTEGER, \
                activity_avatar VARCHAR(512), \
                activity_description    TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS subject_table(\
                subject_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                subject_name    VARCHAR(512) NOT NULL, \
                subject_status  INTEGER, \
                subject_date    DATE, \
                subject_sortweight  INTEGER, \
                subject_avatar  VARCHAR(512)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS subject_object_table(\
                subject_object_id   INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                subject_object_subjectid    INTEGER, \
                subject_object_type INTEGER, \
                subject_object_objectid INTEGER, \
                subject_object_description  VARCHAR(512), \
                subject_object_sortweight   INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            # CREATE TABLE IF NOT EXISTS activity_table(activity_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, activity_productid  INTEGER NOT NULL, activity_name   VARCHAR(512) NOT NULL, activity_status INTEGER NOT NULL, activity_categoryid INTEGER, activity_mark   INTEGER, activity_price  REAL, activity_begintime  DATETIME, activity_endtime    DATETIME, activity_sortweight INTEGER, activity_avatar VARCHAR(512), activity_description    TEXT) ENGINE = MyISAM DEFAULT CHARSET = utf8;
            # CREATE TABLE IF NOT EXISTS subject_table(subject_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, subject_name    VARCHAR(512) NOT NULL, subject_status  INTEGER, subject_date    DATE, subject_sortweight  INTEGER, subject_avatar  VARCHAR(512)) ENGINE = MyISAM DEFAULT CHARSET = utf8;
            # CREATE TABLE IF NOT EXISTS subject_object_table(subject_object_id   INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, subject_object_subjectid    INTEGER, subject_object_type INTEGER, subject_object_objectid INTEGER, subject_object_description  VARCHAR(512), subject_object_sortweight   INTEGER) ENGINE = MyISAM DEFAULT CHARSET = utf8;

            #####################################################################################################################################

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_player_table(\
                player_id   INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                player_teamid   INTEGER UNSIGNED, \
                player_name_chs VARCHAR(128), \
                player_name_eng VARCHAR(128), \
                player_country_chs  VARCHAR(64), \
                player_country_eng  VARCHAR(64)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_team_table(\
                team_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                team_clubid INTEGER UNSIGNED, \
                team_name_chs   VARCHAR(256), \
                team_name_eng   VARCHAR(256), \
                team_firstcategoryid    INTEGER UNSIGNED, \
                team_secondcategoryid   INTEGER UNSIGNED) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_category_table(\
                category_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                category_level  INTEGER, \
                category_name_chs   VARCHAR(64), \
                category_name_eng   VARCHAR(64), \
                category_description_chs    TEXT, \
                category_description_eng    TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_club_table(\
                club_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                club_name_chs   VARCHAR(256), \
                club_name_eng   VARCHAR(256), \
                club_avatar VARCHAR(256), \
                club_location_chs   VARCHAR(256), \
                club_location_eng   VARCHAR(256), \
                club_description_chs    TEXT, \
                club_description_eng    TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_competition_table(\
                competition_id  BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                competition_mainteamid  INTEGER UNSIGNED, \
                competition_secondaryteamid INTEGER UNSIGNED, \
                competition_stadiumid   INTEGER UNSIGNED, \
                competition_time    DATETIME, \
                competition_mainteam_goal   TEXT, \
                competition_secondaryteam_goal  TEXT, \
                competition_mainteam_goal_count INTEGER NOT NULL DEFAULT 0, \
                competition_secondaryteam_goal_count    INTEGER NOT NULL DEFAULT 0, \
                competition_status  INTEGER UNSIGNED, \
				competition_event TEXT)\
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_stadium_table(\
                stadium_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                stadium_name_chs    VARCHAR(256), \
                stadium_name_eng    VARCHAR(256), \
                stadium_city_chs    VARCHAR(256), \
                stadium_city_eng    VARCHAR(256), \
                stadium_location    VARCHAR(255)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_article_table(\
                article_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                article_auditstate  INTEGER, \
                article_title_chs   VARCHAR(255), \
                article_title_eng   VARCHAR(255), \
                article_content_chs TEXT, \
                article_content_eng TEXT, \
                article_publisherid INTEGER, \
                article_categoryid  INTEGER, \
                article_avatar_chs  VARCHAR(255), \
                article_avatar_eng  VARCHAR(255), \
                article_externalurl TEXT, \
                article_createtime  DATETIME, \
                article_sortweight  INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_ads_table(\
                ads_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                ads_auditstate  INTEGER, \
                ads_publisherid INTEGER, \
                ads_platform    INTEGER, \
                ads_position    INTEGER, \
                ads_avatar  VARCHAR(255), \
                ads_externalurl TEXT, \
                ads_sortweight  INTEGER, \
                ads_categoryid  INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_links_table(\
                links_id    INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                links_show  INTEGER, \
                links_name  VARCHAR(255), \
                links_url   TEXT, \
                links_sortweight    INTEGER, \
                links_avatar    VARCHAR(255)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS siysl_image_table(\
                image_id    INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                image_title_chs VARCHAR(256), \
                image_title_eng VARCHAR(256), \
                image_categoryid    INTEGER, \
                image_avatar    TEXT, \
                image_sortweight    INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            # ALTER TABLE competition_registration_form_data_table CHANGE competition_registration_form_field_mobile_phone competition_registration_form_field_phone varchar(45)
            # ALTER TABLE tablename MODIFY columnname INTEGER;
            # alter table thread_table drop column thread_module;
            # alter table thread_table add column thread_moduleid integer not null default 1;
            # alter table comment_table drop column comment_module;
            # alter table comment_table add column comment_moduleid integer not null default 1;
            # alter table user_table add column user_receive_notifications varchar(256) default "[1, 2, 3, 4, 5]";
            # alter table module_table add index (module_category);
            # create table engine_test_table ( test_a integer, test_b varchar(12) ) engine = "MyISAM";
            # select * from thread_table where thread_lastupdatetime >= '2013-10-01 00:57:20';
            # select preorder_table.preorder_id, preorder_table.preorder_outtradeno, preorder_table.preorder_paymentstatus, user_table.user_name, product_table.product_name from 
            #    preorder_table left join product_table on preorder_table.preorder_productid = product_table.product_id left join user_table on preorder_table.preorder_userid = user_table.user_id 
            #    where preorder_table.deleteflag = 1 and preorder_table.preorder_paymentstatus = 1;
            # RENAME TABLE  `oldTableName` TO  `newTableName`

            #####################################################################################################################################

        else:
            self.db.select_db(settings.DB_NAME)
        cursor.close()

    def __del__(self):
        if self.db:
            self.db.close()

    def IsDbUseDictCursor(self):
        return self.cursorclass == MySQLdb.cursors.DictCursor

    def isdict(self):
        return self.IsDbUseDictCursor()

    def quote(self, argument):
        return quote(argument)

    def unquote(self, argument):
        return unquote(argument)

    def GetVersion(self):
        '''Get mysql database version.
        '''
        cursor = self.db.cursor()
        cursor.execute("SELECT VERSION()")
        data = cursor.fetchone()
        if __name__ == "__main__":
            print "Database version: %s" % data
        cursor.close()
        return "Database version: %s" % data

    def getDictValue(self, dictinfo, keyname, index):
        keyvalue = dictinfo[index] if not self.IsDbUseDictCursor() else dictinfo[keyname]
        keyvalue = keyvalue if keyvalue is not None else ""
        return keyvalue

    #####################################################################################################################################

    def AddUser(self, userinfo):
        '''新增用户
        '''
        cpt = Crypter()
        user_name = userinfo["user_name"]
        user_password = cpt.EncryptPassword(userinfo["user_password"])
        user_phonenumber = userinfo["user_phonenumber"]
        user_role = userinfo["user_role"]
        user_adminrole = userinfo["user_adminrole"] if userinfo.has_key("user_adminrole") else -1

        if user_name is None:
            return 0

        if len(user_name) < 2 or len(user_name) > 32:
            return 0

        if self.IsUserExist(user_name) == True:
            return 0

        if self.IsPhonenumberExist(user_phonenumber) == True and int(user_role) == 1 and user_phonenumber != "请绑定手机":
            return 0

        if userinfo.has_key("user_permission"):
            user_permission = userinfo["user_permission"]
        else:
            if user_role == 1:              # 前端用户，无权限
                user_permission = None
            elif user_role == 2:            # 供应商，供应商权限
                user_permission = settings.VENDOR_PERMISSION
            elif user_role == 3:
                if user_adminrole == 1:      # 超级管理员，所有权限
                    user_permission = settings.FULL_PERMISSION
                else:                       # 普通管理员，全部增加、查看权限
                    user_permission = settings.ADMIN_PERMISSION
            else:
                user_permission = None
        user_email = userinfo["user_email"] if userinfo.has_key("user_email") else None
        user_nickname = userinfo["user_nickname"] if userinfo.has_key("user_nickname") else None
        user_interest = userinfo["user_interest"] if userinfo.has_key("user_interest") else None
        user_avatar = userinfo["user_avatar"] if userinfo.has_key("user_avatar") else None
        user_gender = userinfo["user_gender"] if userinfo.has_key("user_gender") else None
        user_age = userinfo["user_age"] if userinfo.has_key("user_age") else None
        user_address = userinfo["user_address"] if userinfo.has_key("user_address") else None
        user_payment = userinfo["user_payment"] if userinfo.has_key("user_payment") else None
        user_points = userinfo["user_points"] if userinfo.has_key("user_points") else None
        user_qqtoken = userinfo["user_qqtoken"] if userinfo.has_key("user_qqtoken") else None
        user_qqopenid = userinfo["user_qqopenid"] if userinfo.has_key("user_qqopenid") else None
        user_sinatoken = userinfo["user_sinatoken"] if userinfo.has_key("user_sinatoken") else None
        user_sinauid = userinfo["user_sinauid"] if userinfo.has_key("user_sinauid") else None
        user_vendorname = userinfo["user_vendorname"] if userinfo.has_key("user_vendorname") else None
        user_vendorleadername = userinfo["user_vendorleadername"] if userinfo.has_key("user_vendorleadername") else None
        user_vendorleaderidcardno = userinfo["user_vendorleaderidcardno"] if userinfo.has_key("user_vendorleaderidcardno") else None
        user_vendorcreditrating = userinfo["user_vendorcreditrating"] if userinfo.has_key("user_vendorcreditrating") else 1
        user_registertime = strftime("%Y-%m-%d %H:%M:%S")
        user_emailpasskey = None
        user_vendorphonenumber = userinfo["user_vendorphonenumber"] if userinfo.has_key("user_vendorphonenumber") else None
        user_vendoraddress = userinfo["user_vendoraddress"] if userinfo.has_key("user_vendoraddress") else None
        user_vendorexperience = userinfo["user_vendorexperience"] if userinfo.has_key("user_vendorexperience") else 0
        user_vendorcredit = userinfo["user_vendorcredit"] if userinfo.has_key("user_vendorcredit") else 48
        user_vendorlicenseid = userinfo["user_vendorlicenseid"] if userinfo.has_key("user_vendorlicenseid") else None
        user_vendorleaderphonenumber = userinfo["user_vendorleaderphonenumber"] if userinfo.has_key("user_vendorleaderphonenumber") else None
        user_vendorbusinessscope = userinfo["user_vendorbusinessscope"] if userinfo.has_key("user_vendorbusinessscope") else None
        user_vendordescription = userinfo["user_vendordescription"] if userinfo.has_key("user_vendordescription") else None
        user_permissionstate = userinfo["user_permissionstate"] if userinfo.has_key("user_permissionstate") else 1
        user_viplevel = userinfo["user_viplevel"] if userinfo.has_key("user_viplevel") else 1
        user_vipexperience  = userinfo["user_vipexperience"] if userinfo.has_key("user_vipexperience") else 0
        user_birthday = userinfo["user_birthday"] if userinfo.has_key("user_birthday") else None
        user_qietoken = userinfo["user_qietoken"] if userinfo.has_key("user_qietoken") else None
        user_qieopenid = userinfo["user_qieopenid"] if userinfo.has_key("user_qieopenid") else None
        deleteflag = 0
        user_registersource = userinfo["user_registersource"] if userinfo.has_key("user_registersource") else 1
        user_registerip = userinfo["user_registerip"] if userinfo.has_key("user_registerip") else None
        user_lastlogindatetime = userinfo["user_lastlogindatetime"] if userinfo.has_key("user_lastlogindatetime") else None
        user_followcompetition = userinfo["user_followcompetition"] if userinfo.has_key("user_followcompetition") else None
        user_country_chs = userinfo["user_country_chs"] if userinfo.has_key("user_country_chs") else None
        user_country_eng = userinfo["user_country_eng"] if userinfo.has_key("user_country_eng") else None

        cursor = self.db.cursor()
        value = [ None, user_name, user_password, user_phonenumber, user_email, user_nickname, user_interest, user_avatar, user_gender, 
            user_age, user_address, user_payment, user_points, user_qqtoken, user_qqopenid, user_sinatoken, user_sinauid, user_role, user_permission, 
            user_vendorname, user_vendorleadername, user_vendorleaderidcardno, user_vendorcreditrating, user_registertime, user_emailpasskey, 
            user_vendorphonenumber, user_vendoraddress, user_vendorexperience, user_vendorcredit, user_vendorlicenseid, user_vendorleaderphonenumber, 
            user_vendorbusinessscope, user_vendordescription, user_permissionstate, user_viplevel, user_vipexperience, user_birthday, user_adminrole,
            user_qietoken, user_qieopenid, deleteflag, user_registersource, user_registerip, user_lastlogindatetime, user_followcompetition, user_country_chs, user_country_eng ]
        cursor.execute("INSERT INTO user_table (user_id, user_name, user_password, user_phonenumber, user_email, user_nickname, \
            user_interest, user_avatar, user_gender, user_age, user_address, user_payment, user_points, user_qqtoken, user_qqopenid, \
            user_sinatoken, user_sinauid, user_role, user_permission, user_vendorname, user_vendorleadername, user_vendorleaderidcardno, \
            user_vendorcreditrating, user_registertime, user_emailpasskey, user_vendorphonenumber, user_vendoraddress, user_vendorexperience, \
            user_vendorcredit, user_vendorlicenseid, user_vendorleaderphonenumber, user_vendorbusinessscope, user_vendordescription, \
            user_permissionstate, user_viplevel, user_vipexperience, user_birthday, user_adminrole, user_qietoken, user_qieopenid, deleteflag, \
            user_registersource, user_registerip, user_lastlogindatetime, user_followcompetition, user_country_chs, user_country_eng) \
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, \
                   %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        userid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return userid

    def CheckUser(self, username, passwd):
        '''Validate username & passwd.
        返回值: -2 - 无此帐户， -1 - 验证失败， 1 - 验证成功
        '''
        cpt = Crypter()
        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND (user_name = %s OR user_phonenumber = %s) AND user_role = 1 LIMIT 1"
        param = [username, username]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            hashedpassword = result[2] if not self.IsDbUseDictCursor() else result["user_password"]
            if cpt.ValidatePassword(passwd, hashedpassword):
                return 1
            else:
                return -1
        else:
            return -2

    def CheckUserByID(self, userid, passwd):
        '''Validate userid & passwd.
        返回值: -2 - 无此帐户， -1 - 验证失败， 1 - 验证成功
        '''
        cpt = Crypter()
        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_id = %s AND user_role = 1 LIMIT 1"
        param = [userid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            hashedpassword = result[2] if not self.IsDbUseDictCursor() else result["user_password"]
            if passwd == hashedpassword or cpt.ValidatePassword(passwd, hashedpassword):
                return 1
            else:
                return -1
        else:
            return -2

    def CheckUserBackend(self, username, passwd):
        cpt = Crypter()
        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_name = %s AND user_role != 1 LIMIT 1"
        param = [username]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            hashedpassword = result[2] if not self.IsDbUseDictCursor() else result["user_password"]
            if cpt.ValidatePassword(passwd, hashedpassword):
                return 1
            else:
                return -1
        else:
            return -2

    def QueryUserPermission(self, userid):
        userinfo = self.QueryUserInfoById(userid)
        user_permission = userinfo[19] if not self.IsDbUseDictCursor() else userinfo["user_permission"]
        return json.loads(user_permission)

    def CreateBatchNO(self):
        return self.CreateOutRefundNO()
        
    def CreateOutRefundNO(self):
        """
        批次号都必须保证唯一性。格式为：退款日期（8位）+流水号（3～24位）。
        不可重复，且退款日期必须是当天日期。流水号可以接受数字或英文字符，建议使用数字，但不可接受“000”
        """
        thedate = DateTime.strftime(datetime.date.today(), '%Y%m%d')
        random_range = range(random.randint(3, 24))
        get_thefollowno = lambda: ''.join(random.choice(string.digits) for i in random_range)
        outrefundno = thedate + get_thefollowno()
        while self.IsOutRefundNoExist(outrefundno) or outrefundno.endswith('000'):
            outrefundno = thedate + get_thefollowno()
        return outrefundno

    def MakeDetailData(self, preorder_id):
        """
        Method to make 'detail_data' for AlipayRefund
        2011011201037066^5.00^协商退款
        1. detail_data中的退款笔数总和要等于参数batch_num的值；
        2.“退款理由”长度不能大于256字节，“退款理由”中不能有“^”、“|”、“$”、“#”等影响detail_data格式的特殊字符；
        3. detail_data中退款总金额不能大于交易总金额；
        4. 一笔交易可以多次退款，退款次数最多不能超过99次，需要遵守多次退款的总金额不超过该笔交易付款金
        format: 2011011201037066^5.00^协商退款  outtradeno^outrefundfee^outrefundreason
        """
        preorderinfo = self.QueryPreorderInfo(preorder_id)
        if preorderinfo is not None:
            outtradeno = preorderinfo['preorder_outtradeno']
            outrefundfee = preorderinfo['preorder_outrefundfee']
            outrefundreason = preorderinfo['preorder_appraisal']
            return '^'.join(str(i) for i in [outtradeno, outrefundfee, outrefundreason])

    #####################################################################################################################################

    def QueryAllUserCount(self, userrole=0):
        ''' userrole: 0 - 全部用户， 1 - 前端用户， 2 - 供应商， 3 - 管理员
        '''
        cursor = self.db.cursor()
        if userrole == 0:
            sql = "SELECT COUNT(*) AS COUNT FROM user_table WHERE deleteflag = 0"
        else:
            sql = "SELECT COUNT(*) AS COUNT FROM user_table WHERE deleteflag = 0 AND user_role = %s" % userrole
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()

        if not self.IsDbUseDictCursor():
            usercount = result[0] if result[0] is not None else 0
        else:
            usercount = result["COUNT"] if result["COUNT"] is not None else 0

        return usercount

    def QueryVendorInfoByVendorName(self, vendorname):
        cursor = self.db.cursor()
        sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_vendorname = '%s' LIMIT 1" % vendorname
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryVendorsByProductType(self, producttype=0):
        '''查询能提供 product_type 类型商品的供应商
        '''
        cursor = self.db.cursor()
        if producttype == 0:
            sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_role = 2 AND user_id IN (SELECT DISTINCT product_vendorid FROM product_table WHERE deleteflag = 0 AND product_status = 1 AND product_auditstatus = 1) GROUP BY user_vendorname"
        else:
            sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_role = 2 AND user_id IN (SELECT DISTINCT product_vendorid FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_status = 1 AND product_auditstatus = 1) GROUP BY user_vendorname" % producttype
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryUsers(self, startpos, count=settings.LIST_ITEM_PER_PAGE, userrole=0):
        cursor = self.db.cursor()
        if count == 0:
            if userrole == 0:
                sql = "SELECT * FROM user_table WHERE deleteflag = 0 ORDER BY user_id DESC"
            else:
                sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_role = %s ORDER BY user_id DESC" % userrole
        else:
            if userrole == 0:
                sql = "SELECT * FROM user_table WHERE deleteflag = 0 ORDER BY user_id DESC LIMIT %s, %s" % (startpos, count)
            else:
                sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_role = %s ORDER BY user_id DESC LIMIT %s, %s" % (userrole, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def FuzzyQueryUser(self, userkey, startpos, count=settings.LIST_ITEM_PER_PAGE, userrole=0):
        cursor = self.db.cursor()
        userkey = userkey.replace("'", "''") if userkey else userkey
        if userrole == 0:
            sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND (user_name LIKE '%s%%' OR user_phonenumber LIKE '%s%%') ORDER BY user_id DESC LIMIT %s, %s" % (userkey, userkey, startpos, count)
        else:
            sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_role = %s AND (user_name LIKE '%s%%' OR user_phonenumber LIKE '%s%%') ORDER BY user_id DESC LIMIT %s, %s" % (userrole, userkey, userkey, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def FuzzyQueryUserCount(self, userkey, userrole=0):
        cursor = self.db.cursor()
        userkey = userkey.replace("'", "''") if userkey else userkey
        if userrole == 0:
            sql = "SELECT COUNT(*) AS COUNT FROM user_table WHERE deleteflag = 0 AND (user_name LIKE '%s%%' OR user_phonenumber LIKE '%s%%')" % (userkey, userkey)
        else:
            sql = "SELECT COUNT(*) AS COUNT FROM user_table WHERE deleteflag = 0 AND user_role = %s AND (user_name LIKE '%s%%' OR user_phonenumber LIKE '%s%%')" % (userrole, userkey, userkey)
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()

        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

        # SELECT * FROM table LIMIT 95,-1; // 检索记录行 96 - last.
        # SELECT * FROM articles WHERE category_id = 123 ORDER BY id LIMIT 10000, 10  
        # 分布查询优化，（page > 100时使用）
        # SELECT * FROM articles WHERE  id >= (SELECT id FROM articles  WHERE category_id = 123 ORDER BY id LIMIT 10000, 1) LIMIT 10

    #####################################################################################################################################

    def IsUserExist(self, username):
        '''查询用户是否存在
        '''
        if username is None:
            return False

        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE user_name = %s LIMIT 1"
        param = [username]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        return True if result else False

    def IsUserExistById(self, userid):
        '''查询用户是否存在
        '''
        try:
            userid = int(userid)
        except Exception, e:
            return False

        if not userid:
            return False

        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_id = %s AND user_role = 1 LIMIT 1"
        param = [userid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        return True if result else False

    def IsUserExistByIdBackend(self, userid, userpassword):
        '''查询后台用户是否存在
        '''
        try:
            userid = int(userid)
        except Exception, e:
            return False

        if not userid:
            return False

        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_id = %s AND user_password = %s AND ( user_role = 2 OR user_role = 3 ) LIMIT 1"
        param = [userid, userpassword]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        return True if result else False

    def IsPhonenumberExist(self, phonenumber):
        '''查询手机号是否存在
        '''
        if phonenumber is None:
            return False

        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_phonenumber = %s LIMIT 1"
        param = [phonenumber]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        return True if result else False

    #####################################################################################################################################

    def QueryUserInfoByName(self, username):
        '''根据username查询用户信息
        '''
        if username is None:
            return None

        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_name = %s LIMIT 1"
        param = [username]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryUserInfoByNameOrPhonenumber(self, username):
        '''根据username查询用户信息
        '''
        if username is None:
            return None

        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND (user_name = %s OR user_phonenumber = %s) LIMIT 1"
        param = [username, username]
        cursor.execute(sql, param)

        result = cursor.fetchone()

        if result is not None:
            if not self.IsDbUseDictCursor():
                result = list(result)
            else:
                result = dict(result)
            user_birthday = result[37] if not self.IsDbUseDictCursor() else result["user_birthday"]
            if user_birthday is None:
                if not self.IsDbUseDictCursor():
                    result[37] = "1970-01-01"
                else:
                    result["user_birthday"] = "1970-01-01"

        cursor.close()
        return result

    #####################################################################################################################################

    def QueryUserInfoById(self, userid):
        '''根据userid查询用户信息
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_id = %s LIMIT 1"
        param = [userid]
        cursor.execute(sql, param)

        result = cursor.fetchone()

        if result is not None:
            if not self.IsDbUseDictCursor():
                result = list(result)
            else:
                result = dict(result)
            user_birthday = result[37] if not self.IsDbUseDictCursor() else result["user_birthday"]
            if user_birthday is None:
                if not self.IsDbUseDictCursor():
                    result[37] = "1970-01-01"
                else:
                    result["user_birthday"] = "1970-01-01"

        cursor.close()
        return result

    def QueryUserInfoByOpenid(self, openid):
        '''根据微信OpenID查询用户信息
        '''
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM user_table WHERE deleteflag = 0 AND user_qqopenid = '%s'" % openid)
        result = cursor.fetchone()

        if result is not None:
            if not self.IsDbUseDictCursor():
                result = list(result)
            else:
                result = dict(result)
            user_birthday = result[37] if not self.IsDbUseDictCursor() else result["user_birthday"]
            if user_birthday is None:
                if not self.IsDbUseDictCursor():
                    result[37] = "1970-01-01"
                else:
                    result["user_birthday"] = "1970-01-01"

        cursor.close()
        return result

    def QueryUserInfoBySinaUID(self, sinauid):
        '''根据新浪UID查询用户信息
        '''
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM user_table WHERE deleteflag = 0 AND user_sinauid = '%s'" % sinauid)
        result = cursor.fetchone()

        if result is not None:
            if not self.IsDbUseDictCursor():
                result = list(result)
            else:
                result = dict(result)
            user_birthday = result[37] if not self.IsDbUseDictCursor() else result["user_birthday"]
            if user_birthday is None:
                if not self.IsDbUseDictCursor():
                    result[37] = "1970-01-01"
                else:
                    result["user_birthday"] = "1970-01-01"

        cursor.close()
        return result

    def QueryUserInfoByQieOpenID(self, openid):
        '''根据企鹅（QQ）OpenID查询用户信息
        '''
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM user_table WHERE deleteflag = 0 AND user_qieopenid = '%s'" % openid)
        result = cursor.fetchone()

        if result is not None:
            if not self.IsDbUseDictCursor():
                result = list(result)
            else:
                result = dict(result)
            user_birthday = result[37] if not self.IsDbUseDictCursor() else result["user_birthday"]
            if user_birthday is None:
                if not self.IsDbUseDictCursor():
                    result[37] = "1970-01-01"
                else:
                    result["user_birthday"] = "1970-01-01"

        cursor.close()
        return result

    #####################################################################################################################################

    def DeleteUserOldAvatar(self, userid):
        '''在更新用户的avatar之前先把老的用户头像删除掉
        '''
        (useravatar, hascustomavatar) = self.GetUserAvatarPreview(userid)
        if hascustomavatar:
            filedir = socket.gethostname() == settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp'
            infile = filedir + '/' + useravatar
            os.remove(infile)

    def UpdateUserPasswordByPhoneNumber(self, phonenumber, password):
        cursor = self.db.cursor()
        cpt = Crypter()
        user_password = cpt.EncryptPassword(password)
        sql = "UPDATE user_table SET user_password = %s WHERE deleteflag = 0 AND user_phonenumber = %s"
        param = [user_password, phonenumber]
        cursor.execute(sql, param)
        self.db.commit()
        cursor.close()

    def UpdateUserInfoById(self, userid, userinfo):
        user_id = userid
        cpt = Crypter()

        user_name = userinfo["user_name"] if userinfo.has_key("user_name") else None
        if userinfo.has_key("user_password") and userinfo["user_password"] is not None:
            user_password = cpt.EncryptPassword(userinfo["user_password"])
        else:
            user_password = None
        # user_password = cpt.EncryptPassword(userinfo["user_password"]) if userinfo.has_key("user_password") else None
        user_phonenumber = userinfo["user_phonenumber"] if userinfo.has_key("user_phonenumber") else None

        user_email = userinfo["user_email"] if userinfo.has_key("user_email") else None
        user_nickname = userinfo["user_nickname"] if userinfo.has_key("user_nickname") else None
        user_interest = userinfo["user_interest"] if userinfo.has_key("user_interest") else None
        user_avatar = userinfo["user_avatar"] if userinfo.has_key("user_avatar") else None
        user_gender = userinfo["user_gender"] if userinfo.has_key("user_gender") else None
        user_age = userinfo["user_age"] if userinfo.has_key("user_age") else None
        user_address = userinfo["user_address"] if userinfo.has_key("user_address") else None
        user_payment = userinfo["user_payment"] if userinfo.has_key("user_payment") else None
        user_points = userinfo["user_points"] if userinfo.has_key("user_points") else None
        user_qqtoken = userinfo["user_qqtoken"] if userinfo.has_key("user_qqtoken") else None
        user_qqopenid = userinfo["user_qqopenid"] if userinfo.has_key("user_qqopenid") else None
        user_sinatoken = userinfo["user_sinatoken"] if userinfo.has_key("user_sinatoken") else None
        user_sinauid = userinfo["user_sinauid"] if userinfo.has_key("user_sinauid") else None
        user_registertime = userinfo["user_registertime"] if userinfo.has_key("user_registertime") else None

        user_permission = userinfo["user_permission"] if userinfo.has_key("user_permission") else None
        user_vendorname = userinfo["user_vendorname"] if userinfo.has_key("user_vendorname") else None
        user_vendorleadername = userinfo["user_vendorleadername"] if userinfo.has_key("user_vendorleadername") else None
        user_vendorleaderidcardno = userinfo["user_vendorleaderidcardno"] if userinfo.has_key("user_vendorleaderidcardno") else None
        user_vendorcreditrating = userinfo["user_vendorcreditrating"] if userinfo.has_key("user_vendorcreditrating") else None
        user_emailpasskey = userinfo["user_emailpasskey"] if userinfo.has_key("user_emailpasskey") else None

        user_vendorphonenumber = userinfo["user_vendorphonenumber"] if userinfo.has_key("user_vendorphonenumber") else None
        user_vendoraddress = userinfo["user_vendoraddress"] if userinfo.has_key("user_vendoraddress") else None
        user_vendorexperience = userinfo["user_vendorexperience"] if userinfo.has_key("user_vendorexperience") else None
        user_vendorcredit = userinfo["user_vendorcredit"] if userinfo.has_key("user_vendorcredit") else None
        user_vendorlicenseid = userinfo["user_vendorlicenseid"] if userinfo.has_key("user_vendorlicenseid") else None
        user_vendorleaderphonenumber = userinfo["user_vendorleaderphonenumber"] if userinfo.has_key("user_vendorleaderphonenumber") else None
        user_vendorbusinessscope = userinfo["user_vendorbusinessscope"] if userinfo.has_key("user_vendorbusinessscope") else None
        user_vendordescription = userinfo["user_vendordescription"] if userinfo.has_key("user_vendordescription") else None
        user_permissionstate = userinfo["user_permissionstate"] if userinfo.has_key("user_permissionstate") else None
        user_viplevel = userinfo["user_viplevel"] if userinfo.has_key("user_viplevel") else None
        user_vipexperience  = userinfo["user_vipexperience"] if userinfo.has_key("user_vipexperience") else None
        user_birthday = userinfo["user_birthday"] if userinfo.has_key("user_birthday") else None
        user_adminrole = userinfo["user_adminrole"] if userinfo.has_key("user_adminrole") else None
        user_qietoken = userinfo["user_qietoken"] if userinfo.has_key("user_qietoken") else None
        user_qieopenid = userinfo["user_qieopenid"] if userinfo.has_key("user_qieopenid") else None
        deleteflag = userinfo["deleteflag"] if userinfo.has_key("deleteflag") else None
        user_registersource = userinfo["user_registersource"] if userinfo.has_key("user_registersource") else None
        user_registerip = userinfo["user_registerip"] if userinfo.has_key("user_registerip") else None
        user_lastlogindatetime = userinfo["user_lastlogindatetime"] if userinfo.has_key("user_lastlogindatetime") else None
        user_followcompetition = userinfo["user_followcompetition"] if userinfo.has_key("user_followcompetition") else None
        user_country_chs = userinfo["user_country_chs"] if userinfo.has_key("user_country_chs") else None
        user_country_eng = userinfo["user_country_eng"] if userinfo.has_key("user_country_eng") else None

        cursor = self.db.cursor()

        sql     = "UPDATE user_table SET "
        param   = []
        setted  = False
        if user_password is not None:
            sql += " user_password = %s "
            param.append(user_password)
            setted = True
        if user_name is not None:
            sql += (", user_name = %s " if setted else " user_name = %s ")
            param.append(user_name)
            setted = True
        if user_phonenumber is not None:
            sql += (", user_phonenumber = %s " if setted else " user_phonenumber = %s ")
            param.append(user_phonenumber)
            setted = True
        if user_email is not None:
            sql += (", user_email = %s " if setted else " user_email = %s ")
            param.append(user_email)
            setted = True
        if user_nickname is not None:
            sql += (", user_nickname = %s " if setted else " user_nickname = %s ")
            param.append(user_nickname)
            setted = True
        if user_interest is not None:
            sql += (", user_interest = %s " if setted else " user_interest = %s ")
            param.append(user_interest)
            setted = True
        if user_avatar is not None:
            sql += (", user_avatar = %s " if setted else " user_avatar = %s ")
            param.append(user_avatar)
            setted = True
            self.DeleteUserOldAvatar(user_id)
        if user_gender is not None:
            sql += (", user_gender = %s " if setted else " user_gender = %s ")
            param.append(user_gender)
            setted = True
        if user_age is not None:
            sql += (", user_age = %s " if setted else " user_age = %s ")
            param.append(user_age)
            setted = True
        if user_address is not None:
            sql += (", user_address = %s " if setted else " user_address = %s ")
            param.append(user_address)
            setted = True
        if user_payment is not None:
            sql += (", user_payment = %s " if setted else " user_payment = %s ")
            param.append(user_payment)
            setted = True
        if user_points is not None:
            user_points = float(user_points)
            user_points = user_points if user_points < 100000000 else 100000000
            sql += (", user_points = %s " if setted else " user_points = %s ")
            param.append(user_points)
            setted = True
        if user_qqtoken is not None:
            sql += (", user_qqtoken = %s " if setted else " user_qqtoken = %s ")
            param.append(user_qqtoken)
            setted = True
        if user_qqopenid is not None:
            sql += (", user_qqopenid = %s " if setted else " user_qqopenid = %s ")
            param.append(user_qqopenid)
            setted = True
        if user_sinatoken is not None:
            sql += (", user_sinatoken = %s " if setted else " user_sinatoken = %s ")
            param.append(user_sinatoken)
            setted = True
        if user_sinauid is not None:
            sql += (", user_sinauid = %s " if setted else " user_sinauid = %s ")
            param.append(user_sinauid)
            setted = True
        if user_registertime is not None:
            sql += (", user_registertime = %s " if setted else " user_registertime = %s ")
            param.append(user_registertime)
            setted = True
        if user_permission is not None:
            sql += (", user_permission = %s " if setted else " user_permission = %s ")
            param.append(user_permission)
            setted = True
        if user_vendorname is not None:
            sql += (", user_vendorname = %s " if setted else " user_vendorname = %s ")
            param.append(user_vendorname)
            setted = True
        if user_vendorleadername is not None:
            sql += (", user_vendorleadername = %s " if setted else " user_vendorleadername = %s ")
            param.append(user_vendorleadername)
            setted = True
        if user_vendorleaderidcardno is not None:
            sql += (", user_vendorleaderidcardno = %s " if setted else " user_vendorleaderidcardno = %s ")
            param.append(user_vendorleaderidcardno)
            setted = True
        if user_vendorcreditrating is not None:
            sql += (", user_vendorcreditrating = %s " if setted else " user_vendorcreditrating = %s ")
            param.append(user_vendorcreditrating)
            setted = True
        if user_emailpasskey is not None:
            sql += (", user_emailpasskey = %s " if setted else " user_emailpasskey = %s ")
            param.append(user_emailpasskey)
            setted = True
        if user_vendorphonenumber is not None:
            sql += (", user_vendorphonenumber = %s " if setted else " user_vendorphonenumber = %s ")
            param.append(user_vendorphonenumber)
            setted = True
        if user_vendoraddress is not None:
            sql += (", user_vendoraddress = %s " if setted else " user_vendoraddress = %s ")
            param.append(user_vendoraddress)
            setted = True
        if user_vendorexperience is not None:
            sql += (", user_vendorexperience = %s " if setted else " user_vendorexperience = %s ")
            param.append(user_vendorexperience)
            setted = True
        if user_vendorcredit is not None:
            sql += (", user_vendorcredit = %s " if setted else " user_vendorcredit = %s ")
            param.append(user_vendorcredit)
            setted = True
        if user_vendorlicenseid is not None:
            sql += (", user_vendorlicenseid = %s " if setted else " user_vendorlicenseid = %s ")
            param.append(user_vendorlicenseid)
            setted = True
        if user_vendorleaderphonenumber is not None:
            sql += (", user_vendorleaderphonenumber = %s " if setted else " user_vendorleaderphonenumber = %s ")
            param.append(user_vendorleaderphonenumber)
            setted = True
        if user_vendorbusinessscope is not None:
            sql += (", user_vendorbusinessscope = %s " if setted else " user_vendorbusinessscope = %s ")
            param.append(user_vendorbusinessscope)
            setted = True
        if user_vendordescription is not None:
            sql += (", user_vendordescription = %s " if setted else " user_vendordescription = %s ")
            param.append(user_vendordescription)
            setted = True
        if user_permissionstate is not None:
            sql += (", user_permissionstate = %s " if setted else " user_permissionstate = %s ")
            param.append(user_permissionstate)
            setted = True
        if user_viplevel is not None:
            sql += (", user_viplevel = %s " if setted else " user_viplevel = %s ")
            param.append(user_viplevel)
            setted = True
        if user_vipexperience is not None:
            sql += (", user_vipexperience = %s " if setted else " user_vipexperience = %s ")
            param.append(user_vipexperience)
            setted = True
        if user_birthday is not None:
            sql += (", user_birthday = %s " if setted else " user_birthday = %s ")
            param.append(user_birthday)
            setted = True
        if user_adminrole is not None:
            sql += (", user_adminrole = %s " if setted else " user_adminrole = %s ")
            param.append(user_adminrole)
            setted = True
        if user_qietoken is not None:
            sql += (", user_qietoken = %s " if setted else " user_qietoken = %s ")
            param.append(user_qietoken)
            setted = True
        if user_qieopenid is not None:
            sql += (", user_qieopenid = %s " if setted else " user_qieopenid = %s ")
            param.append(user_qieopenid)
            setted = True
        if deleteflag is not None:
            sql += (", deleteflag = %s " if setted else " deleteflag = %s ")
            param.append(deleteflag)
            setted = True
        if user_registersource is not None:
            sql += (", user_registersource = %s " if setted else " user_registersource = %s ")
            param.append(user_registersource)
            setted = True
        if user_registerip is not None:
            sql += (", user_registerip = %s " if setted else " user_registerip = %s ")
            param.append(user_registerip)
            setted = True
        if user_lastlogindatetime is not None:
            sql += (", user_lastlogindatetime = %s " if setted else " user_lastlogindatetime = %s ")
            param.append(user_lastlogindatetime)
            setted = True
        if user_followcompetition is not None:
            sql += (", user_followcompetition = %s " if setted else " user_followcompetition = %s ")
            param.append(user_followcompetition)
            setted = True
        if user_country_chs is not None:
            sql += (", user_country_chs = %s " if setted else " user_country_chs = %s ")
            param.append(user_country_chs)
            setted = True            
        if user_country_eng is not None:
            sql += (", user_country_eng = %s " if setted else " user_country_eng = %s ")
            param.append(user_country_eng)
            setted = True

        if setted:
            sql += " WHERE user_id = %s"
            param.append(user_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False
    
    #####################################################################################################################################

    def DeleteUserById(self, userid, permant=0):
        cursor = self.db.cursor()
        if int(permant) == 0:
            sql = "UPDATE user_table SET deleteflag = 1 WHERE user_id = %s" % userid
        else:
            sql = "DELETE FROM user_table WHERE user_id = %s" % userid
        cursor.execute(sql)
        self.db.commit()

        sql = "DELETE FROM comment_table WHERE comment_userid = %s" % userid
        cursor.execute(sql)
        self.db.commit()

        sql = "DELETE FROM coupon_table WHERE coupon_userid = %s" % userid
        cursor.execute(sql)
        self.db.commit()

        sql = "DELETE FROM complaints_table WHERE complaints_id = %s" % userid
        cursor.execute(sql)
        self.db.commit()

        if int(permant) == 0:
            sql = "UPDATE preorder_table SET deleteflag = 1 WHERE preorder_userid = %s" % userid
        else:
            sql = "DELETE FROM preorder_table WHERE preorder_userid = %s" % userid
        cursor.execute(sql)
        self.db.commit()

        sql = "DELETE FROM usertraveller_table WHERE usertraveller_userid = %s" % userid
        cursor.execute(sql)
        self.db.commit()

        sql = "DELETE FROM useraddress_table WHERE useraddress_userid = %s" % userid
        cursor.execute(sql)
        self.db.commit()

        sql = "DELETE FROM useraddress_table WHERE useraddress_userid = %s" % userid
        cursor.execute(sql)
        self.db.commit()

        cursor.close()

    #####################################################################################################################################

    def AddUserAddress(self, userid, addressinfo):
        useraddress_userid = userid
        useraddress_recipients = addressinfo["useraddress_recipients"]
        useraddress_address = addressinfo["useraddress_address"]
        useraddress_phonenumber = addressinfo["useraddress_phonenumber"]
        useraddress_zipcode = addressinfo["useraddress_zipcode"] if addressinfo.has_key("useraddress_zipcode") else None

        cursor = self.db.cursor()
        value = [None, useraddress_userid, useraddress_recipients, useraddress_address, useraddress_phonenumber, useraddress_zipcode]
        cursor.execute("INSERT INTO useraddress_table VALUES(%s, %s, %s, %s, %s, %s)", value)
        addressid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return addressid

    def QueryUserAllAddress(self, userid):
        cursor = self.db.cursor()
        sql = "SELECT * FROM useraddress_table WHERE useraddress_userid = %s ORDER BY useraddress_id ASC"
        param = [userid]
        cursor.execute(sql, param)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryAddressInfo(self, useraddressid):
        cursor = self.db.cursor()
        sql   = "SELECT * FROM useraddress_table WHERE useraddress_id = %s LIMIT 1"
        param = [useraddressid]
        cursor.execute(sql, param)
        result = cursor.fetchone()
        cursor.close()
        return result

    def UpdateUserAddress(self, addressid, addressinfo):
        useraddress_id = addressid

        useraddress_recipients = addressinfo["useraddress_recipients"] if addressinfo.has_key("useraddress_recipients") else None
        useraddress_address = addressinfo["useraddress_address"] if addressinfo.has_key("useraddress_address") else None
        useraddress_phonenumber = addressinfo["useraddress_phonenumber"] if addressinfo.has_key("useraddress_phonenumber") else None
        useraddress_zipcode = addressinfo["useraddress_zipcode"] if addressinfo.has_key("useraddress_zipcode") else None

        cursor = self.db.cursor()

        sql     = "UPDATE useraddress_table SET "
        param   = []
        setted  = False
        if useraddress_recipients is not None:
            sql += " useraddress_recipients = %s "
            param.append(useraddress_recipients)
            setted = True
        if useraddress_address is not None:
            sql += (", useraddress_address = %s " if setted else " useraddress_address = %s ")
            param.append(useraddress_address)
            setted = True
        if useraddress_phonenumber is not None:
            sql += (", useraddress_phonenumber = %s " if setted else " useraddress_phonenumber = %s ")
            param.append(useraddress_phonenumber)
            setted = True
        if useraddress_zipcode is not None:
            sql += (", useraddress_zipcode = %s " if setted else " useraddress_zipcode = %s ")
            param.append(useraddress_zipcode)
            setted = True
        if setted:
            sql += " WHERE useraddress_id = %s"
            param.append(useraddress_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    def DeleteUserAddress(self, addressid, userid=0):
        cursor = self.db.cursor()
        if userid == 0:
            sql = "DELETE FROM useraddress_table WHERE useraddress_id = %s" % addressid
        else:
            sql = "DELETE FROM useraddress_table WHERE useraddress_userid = %s" % userid
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddUserTraveller(self, userid, travellerinfo):
        usertraveller_userid = userid
        usertraveller_name = travellerinfo["usertraveller_name"]
        usertraveller_type = travellerinfo["usertraveller_type"]

        usertraveller_idcardno = travellerinfo["usertraveller_idcardno"] if travellerinfo.has_key("usertraveller_idcardno") else None

        cursor = self.db.cursor()
        value = [None, usertraveller_userid, usertraveller_name, usertraveller_type, usertraveller_idcardno]
        cursor.execute("INSERT INTO usertraveller_table VALUES(%s, %s, %s, %s, %s)", value)
        lastid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return lastid

    def QueryUserAllTraveller(self, userid):
        cursor = self.db.cursor()
        sql = "SELECT * FROM usertraveller_table WHERE usertraveller_userid = %s ORDER BY usertraveller_id ASC"
        param = [userid]
        cursor.execute(sql, param)
        result = cursor.fetchall()
        cursor.close()
        return result

    def UpdateUserTraveller(self, travellerid, travellerinfo):
        usertraveller_id = travellerid

        usertraveller_name = travellerinfo["usertraveller_name"] if travellerinfo.has_key("usertraveller_name") else None
        usertraveller_type = travellerinfo["usertraveller_type"] if travellerinfo.has_key("usertraveller_type") else None
        usertraveller_idcardno = travellerinfo["usertraveller_idcardno"] if travellerinfo.has_key("usertraveller_idcardno") else None

        cursor = self.db.cursor()

        sql     = "UPDATE usertraveller_table SET "
        param   = []
        setted  = False
        if usertraveller_name is not None:
            sql += " usertraveller_name = %s "
            param.append(usertraveller_name)
            setted = True
        if usertraveller_type is not None:
            sql += (", usertraveller_type = %s " if setted else " usertraveller_type = %s ")
            param.append(usertraveller_type)
            setted = True
        if usertraveller_idcardno is not None:
            sql += (", usertraveller_idcardno = %s " if setted else " usertraveller_idcardno = %s ")
            param.append(usertraveller_idcardno)
            setted = True
        if setted:
            sql += " WHERE usertraveller_id = %s"
            param.append(usertraveller_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    def DeleteUserTraveller(self, travellerid, userid=0):
        cursor = self.db.cursor()
        if userid == 0:
            sql = "DELETE FROM usertraveller_table WHERE usertraveller_id = %s" % travellerid
        else:
            sql = "DELETE FROM usertraveller_table WHERE usertraveller_userid = %s" % userid
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddCategory(self, categoryinfo):
        category_name = categoryinfo["category_name"] if categoryinfo.has_key("category_name") else None
        category_description = categoryinfo["category_description"] if categoryinfo.has_key("category_description") else None
        category_avatar = categoryinfo["category_avatar"] if categoryinfo.has_key("category_avatar") else None
        category_parent = categoryinfo["category_parent"] if categoryinfo.has_key("category_parent") else None
        category_sortweight = categoryinfo["category_sortweight"] if categoryinfo.has_key("category_sortweight") else None

        cursor = self.db.cursor()
        value = [None, category_name, category_description, category_avatar, category_parent, category_sortweight]
        cursor.execute("INSERT INTO category_table VALUES(%s, %s, %s, %s, %s, %s)", value)
        categoryid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return categoryid

    #####################################################################################################################################

    def QueryAllCategoryCount(self):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM category_table WHERE category_parent != 0"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryCategoriesList(self):
        '''获取体育培训类型产品的分类列表（包括父级分类与子分类）
        '''
        sql = 'SELECT DISTINCT gbt.product_parentitem, gbt.product_item FROM category_table AS c \
               INNER JOIN product_table AS gbt ON c.category_name = gbt.product_item \
               WHERE gbt.product_type = 1 '
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = { "不限" : [ "全部项目" ] }
        # result = {}
        for val in cursor.fetchall():
            key = val['product_parentitem']
            result.setdefault(key, [])
            result.get(key).append(val['product_item'])
        cursor.close()
        return result

    def QueryCategories(self, startpos, count=settings.LIST_ITEM_PER_PAGE, categoryparent=0, sort=0):
        '''sort: 0 - 按分类ID进行排序
                 1 - 按分类中的商品数量进行排序
                 2 - 按分类的权重进行排序
        '''
        if sort == 0:
            cursor = self.db.cursor()
            sql = "SELECT * FROM category_table WHERE 1 = 1 "
            if categoryparent != 0:
                sql += " AND category_parent = %s " % categoryparent
            else:
                sql += " AND category_parent != 0 "
            sql += " ORDER BY category_id DESC "
            if count != 0:
                sql += " LIMIT %s, %s " % (startpos, count)
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            return result
        elif sort == 1:
            allcategories = self.QueryCategories(0, 0, categoryparent)
            allcategories_new = []

            for categoryinfo in allcategories:
                productcountincategory = self.QueryProductCountInCategory(categoryinfo[1] if not self.IsDbUseDictCursor() else categoryinfo["category_name"], categoryparent=categoryparent)
                allcategories_new.append({ "CategoryInfo" : categoryinfo, "Count" : int(productcountincategory) })

            allcategories_sorted = sorted(allcategories_new, key = lambda x:x['Count'], reverse = True)
            allcategories_result = []

            for categorydict in allcategories_sorted:
                allcategories_result.append(categorydict["CategoryInfo"])

            if count != 0:
                return allcategories_result[startpos:startpos + count]
            else:
                return allcategories_result
        elif sort == 2:
            cursor = self.db.cursor()
            sql = "SELECT * FROM category_table WHERE 1 = 1 AND "
            if categoryparent != 0:
                sql += " category_parent = %s " % categoryparent
            else:
                sql += " category_parent != 0 "
            sql += " ORDER BY category_sortweight DESC "
            if count != 0:
                sql += " LIMIT %s, %s " % (startpos, count)
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            return result
        else:
            if not self.IsDbUseDictCursor():
                return list([])
            else:
                return dict({})

    def QueryProductCountInCategory(self, category, categoryparent):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0 AND product_item = '%s' AND product_type = %s AND product_status = 1 AND product_auditstatus = 1" % (category, categoryparent)
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryParentCategories(self, startpos, count=settings.LIST_ITEM_PER_PAGE):
        cursor = self.db.cursor()
        sql = "SELECT * FROM category_table WHERE category_parent = 0 ORDER BY category_name asc" if count == 0 else "SELECT * FROM category_table WHERE category_parent = 0 ORDER BY category_name asc LIMIT %s, %s" % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    #####################################################################################################################################

    def IsCategoryExist(self, categoryname):
        if categoryname is None:
            return False

        cursor = self.db.cursor()

        sql   = "SELECT * FROM category_table WHERE category_name = %s LIMIT 1"
        param = [categoryname]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        return True if result else False

    #####################################################################################################################################

    def QueryCategoryInfoByName(self, categoryname):
        if categoryname is None:
            return None

        cursor = self.db.cursor()

        sql   = "SELECT * FROM category_table WHERE category_name = %s AND category_parent != 0 LIMIT 1"
        param = [categoryname]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    #####################################################################################################################################

    def QueryCategoryInfoById(self, categoryid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM category_table WHERE category_id = %s AND category_parent != 0 LIMIT 1"
        param = [categoryid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryCategoryInfo(self, categoryid):
        return self.QueryCategoryInfoById(categoryid)

    #####################################################################################################################################

    def UpdateCategoryInfoByName(self, categoryname, categoryinfo):
        category_name = categoryname

        category_description = categoryinfo["category_description"] if categoryinfo.has_key("category_description") else None
        category_avatar = categoryinfo["category_avatar"] if categoryinfo.has_key("category_avatar") else None
        category_parent = categoryinfo["category_parent"] if categoryinfo.has_key("category_parent") else None
        category_sortweight = categoryinfo["category_sortweight"] if categoryinfo.has_key("category_sortweight") else None

        cursor = self.db.cursor()

        sql     = "UPDATE category_table SET "
        param   = []
        setted  = False
        if category_avatar is not None:
            sql += " category_avatar = %s "
            param.append(category_avatar)
            setted = True
        if category_parent is not None:
            sql += (", category_parent = %s " if setted else " category_parent = %s ")
            param.append(category_parent)
            setted = True
        if category_sortweight is not None:
            sql += (", category_sortweight = %s " if setted else " category_sortweight = %s ")
            param.append(category_sortweight)
            setted = True
        if category_description is not None:
            sql += (", category_description = %s " if setted else " category_description = %s ")
            param.append(category_description)
            setted = True
        if setted:
            sql += " WHERE category_name = %s AND category_parent != 0"
            param.append(category_name)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    #####################################################################################################################################

    def UpdateCategoryInfoById(self, categoryid, categoryinfo):
        category_id = categoryid

        category_description = categoryinfo["category_description"] if categoryinfo.has_key("category_description") else None
        category_name = categoryinfo["category_name"] if categoryinfo.has_key("category_name") else None
        category_avatar = categoryinfo["category_avatar"] if categoryinfo.has_key("category_avatar") else None
        category_parent = categoryinfo["category_parent"] if categoryinfo.has_key("category_parent") else None
        category_sortweight = categoryinfo["category_sortweight"] if categoryinfo.has_key("category_sortweight") else None

        cursor = self.db.cursor()

        sql     = "UPDATE category_table SET "
        param   = []
        setted  = False
        if category_name is not None:
            sql += " category_name = %s "
            param.append(category_name)
            setted = True
        if category_avatar is not None:
            sql += (", category_avatar = %s " if setted else " category_avatar = %s ")
            param.append(category_avatar)
            setted = True
        if category_parent is not None:
            sql += (", category_parent = %s " if setted else " category_parent = %s ")
            param.append(category_parent)
            setted = True
        if category_sortweight is not None:
            sql += (", category_sortweight = %s " if setted else " category_sortweight = %s ")
            param.append(category_sortweight)
            setted = True
        if category_description is not None:
            sql += (", category_description = %s " if setted else " category_description = %s ")
            param.append(category_description)
            setted = True
        if setted:
            sql += " WHERE category_id = %s AND category_parent != 0"
            param.append(category_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    #####################################################################################################################################

    def DeleteCategoryByName(self, categoryname):
        cursor = self.db.cursor()
        sql = "DELETE FROM category_table WHERE category_name = %s AND category_parent != 0"
        param = [categoryname]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def DeleteCategoryById(self, categoryid):
        cursor = self.db.cursor()
        sql = "DELETE FROM category_table WHERE category_id = %s AND category_parent != 0"
        param = [categoryid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddScene(self, sceneinfo):
        scene_productid = sceneinfo["scene_productid"]
        scene_time1 = sceneinfo["scene_time1"] if sceneinfo.has_key("scene_time1") else None
        scene_time2 = sceneinfo["scene_time2"] if sceneinfo.has_key("scene_time2") else None
        scene_maxpeople = sceneinfo["scene_maxpeople"] if sceneinfo.has_key("scene_maxpeople") else None
        scene_fullprice = sceneinfo["scene_fullprice"] if sceneinfo.has_key("scene_fullprice") else None

        scene_childprice = sceneinfo["scene_childprice"] if sceneinfo.has_key("scene_childprice") else None
        scene_name = sceneinfo["scene_name"] if sceneinfo.has_key("scene_name") else None
        scene_locations = sceneinfo["scene_locations"] if sceneinfo.has_key("scene_locations") else None
        scene_timeperiod = sceneinfo["scene_timeperiod"] if sceneinfo.has_key("scene_timeperiod") else None
        scene_marketprice = sceneinfo["scene_marketprice"] if sceneinfo.has_key("scene_marketprice") else None
        scene_points = sceneinfo["scene_points"] if sceneinfo.has_key("scene_points") else None
        scene_promotionprice = sceneinfo["scene_promotionprice"] if sceneinfo.has_key("scene_promotionprice") else None
        scene_promotionbegintime = sceneinfo["scene_promotionbegintime"] if sceneinfo.has_key("scene_promotionbegintime") else None
        scene_promotionendtime = sceneinfo["scene_promotionendtime"] if sceneinfo.has_key("scene_promotionendtime") else None
        scene_description = sceneinfo["scene_description"] if sceneinfo.has_key("scene_description") else None
        deleteflag = 0

        cursor = self.db.cursor()
        value = [None, scene_productid, scene_time1, scene_time2, scene_maxpeople, scene_fullprice, scene_childprice, 
            scene_name, scene_locations, scene_timeperiod, scene_marketprice, scene_points, scene_promotionprice, 
            scene_promotionbegintime, scene_promotionendtime, scene_description, deleteflag]
        cursor.execute("INSERT INTO scene_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        sceneid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return sceneid

    def QueryAllTravelDestinationlace(self):
        '''获取体育旅游所有目的地
        '''
        cursor = self.db.cursor()
        sql = "SELECT DISTINCT product_travelendplace FROM product_table WHERE deleteflag = 0 AND product_type = 2 AND product_travelendplace IS NOT NULL AND product_status = 1 AND product_auditstatus = 1 ORDER BY product_id DESC"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryAllTravelDays(self):
        '''获取体育旅游所有行程天数
        '''
        cursor = self.db.cursor()
        sql = "SELECT DISTINCT product_traveldays FROM product_table WHERE deleteflag = 0 AND product_type = 2 AND product_traveldays IS NOT NULL AND product_status = 1 AND product_auditstatus = 1 ORDER BY product_sortweight DESC"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryAllTeachingPlaces(self, producttype=0):
        '''获取所有体育培训的教学地点
        '''
        cursor = self.db.cursor()
        # 1, 3, 4, 6, 7
        if producttype == 0:
            sql = "SELECT DISTINCT scene_locations FROM scene_table WHERE deleteflag = 0 ORDER BY scene_locations ASC"
        elif producttype == 2 or producttype == 5:
            sql = "SELECT DISTINCT scene_locations FROM scene_table WHERE deleteflag = 0 AND scene_productid IN (SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_status = 1 AND product_auditstatus = 1) ORDER BY scene_locations ASC" % producttype
        elif producttype == 7:
            sql = "SELECT DISTINCT product_area FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_status = 1 AND product_auditstatus = 1" % producttype
        else:
            if not self.IsDbUseDictCursor():
                return [(u"黄浦区", ), (u"徐汇区", ), (u"长宁区", ), (u"静安区", ), (u"普陀区", ), (u"闸北区", ), (u"虹口区", ), (u"杨浦区", ), (u"宝山区", ), (u"闵行区", ), (u"嘉定区", ), (u"浦东新区", ), (u"松江区", ), (u"金山区", ), (u"青浦区", ), (u"南汇区", ), (u"奉贤区", ), (u"崇明县", )]
            else:
                return [{ "product_area" : u"黄浦区" }, { "product_area" : u"徐汇区" }, { "product_area" : u"长宁区" }, { "product_area" : u"静安区" }, { "product_area" : u"普陀区" }, { "product_area" : u"闸北区" }, { "product_area" : u"虹口区" }, { "product_area" : u"杨浦区" }, { "product_area" : u"宝山区" }, { "product_area" : u"闵行区" }, { "product_area" : u"嘉定区" }, { "product_area" : u"浦东新区" }, { "product_area" : u"松江区" }, { "product_area" : u"金山区" }, { "product_area" : u"青浦区" }, { "product_area" : u"南汇区" }, { "product_area" : u"奉贤区" }, { "product_area" : u"崇明县" }]
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryProductMarketPrice(self, productid, highprice=0, scenename=None, scenelocations=None, scenetimeperiod=None):
        '''获取商品的市场价（以所有场次中市场价最高的为准）
        '''
        cursor = self.db.cursor()
        if highprice == 0:
            sql = "SELECT MIN(scene_marketprice) AS PRICE FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
        else:
            sql = "SELECT MAX(scene_marketprice) AS PRICE FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid

        if scenename is not None:
            sql += " AND scene_name = '%s' " % scenename
        if scenelocations is not None:
            sql += " AND scene_locations = '%s' " % scenelocations
        if scenetimeperiod is not None:
            sql += " AND scene_timeperiod = '%s' " % scenetimeperiod

        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()

        if not self.IsDbUseDictCursor():
            price = result[0] if result[0] is not None else 0
        else:
            price = result["PRICE"] if result["PRICE"] is not None else 0

        return "%.2f" % price

    def QueryProduct17dongPrice(self, productid, highprice=0, scenename=None, scenelocations=None, scenetimeperiod=None):
        '''获取商品的一起动价（以所有场次中一起动价最低的为准）, highprice: 为 0 时查询最低价，为 1 时查询最高价
        '''
        cursor = self.db.cursor()
        if highprice == 0:
            sql = "SELECT MIN(scene_fullprice) AS PRICE FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
        else:
            sql = "SELECT MAX(scene_fullprice) AS PRICE FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
        
        if scenename is not None:
            sql += " AND scene_name = '%s' " % scenename
        if scenelocations is not None:
            sql += " AND scene_locations = '%s' " % scenelocations
        if scenetimeperiod is not None:
            sql += " AND scene_timeperiod = '%s' " % scenetimeperiod
            
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            price = result[0] if result[0] is not None else 0
        else:
            price = result["PRICE"] if result["PRICE"] is not None else 0
        return "%.2f" % price

    def QueryProduct17dongChildPrice(self, productid, highprice=0, scenename=None, scenetimeperiod=None):
        '''获取商品的一起动价（以所有场次中一起动价最低的为准）, highprice: 为 0 时查询最低价，为 1 时查询最高价
        '''
        cursor = self.db.cursor()
        if highprice == 0:
            sql = "SELECT MIN(scene_childprice) AS PRICE FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
            if scenename is not None:
                sql += " AND scene_name = '%s' " % scenename
            if scenetimeperiod is not None:
                sql += " AND scene_timeperiod = '%s' " % scenetimeperiod
        else:
            sql = "SELECT MAX(scene_childprice) AS PRICE FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
            if scenename is not None:
                sql += " AND scene_name = '%s' " % scenename
            if scenetimeperiod is not None:
                sql += " AND scene_timeperiod = '%s' " % scenetimeperiod
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            price = result[0] if result[0] is not None else 0
        else:
            price = result["PRICE"] if result["PRICE"] is not None else 0
        return "%.2f" % price

    def IsProductHasCoupon(self, productid):
        '''查询商品是否有优惠券奖励
        '''
        productinfo = self.QueryProductInfo(productid)
        coupon1 = productinfo[33] if not self.IsDbUseDictCursor() else productinfo["product_couponwhenorder"]

        if coupon1:
            return True
        else:
            return False

    def IsProductHasPromotion(self, productid):
        '''查询商品是否有特价优惠
        '''
        haspromotion = False
        allscenes = self.QueryProductScenes(productid)
        for onescene in allscenes:
            promotionprice = onescene[12] if not self.IsDbUseDictCursor() else onescene["scene_promotionprice"]
            if promotionprice is not None:
                try:
                    promotionprice = float(promotionprice)
                except Exception, e:
                    continue
                if promotionprice > 0:
                    haspromotion = True
                    break
        return haspromotion

    #####################################################################################################################################

    def QueryAllSceneCount(self):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM scene_table WHERE deleteflag = 0"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryScenes(self, startpos, count=settings.LIST_ITEM_PER_PAGE):
        cursor = self.db.cursor()
        sql = "SELECT * FROM scene_table WHERE deleteflag = 0 ORDER BY scene_id ASC" if count == 0 else "SELECT * FROM scene_table WHERE deleteflag = 0 ORDER BY scene_id ASC LIMIT %s, %s" % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    #####################################################################################################################################

    def QuerySceneInfo(self, sceneid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_id = %s LIMIT 1"
        param = [sceneid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryProductScenes(self, productid, distinctscenename=False, distinctscenelocation=False, distinctscenetimeperiod=False):
        cursor = self.db.cursor()
        if distinctscenename or distinctscenelocation or distinctscenetimeperiod:
            if distinctscenename:
                sql = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s GROUP BY scene_name ORDER BY scene_id ASC"
            elif distinctscenelocation:
                sql = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s GROUP BY scene_locations ORDER BY scene_id ASC"
            elif distinctscenetimeperiod:
                sql = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s GROUP BY scene_timeperiod ORDER BY scene_id ASC"
        else:
            sql = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s ORDER BY scene_id ASC"

        param = [productid]
        cursor.execute(sql, param)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryProductLocationsInScene(self, productid, scenename):
        '''获取商品场次的某个场次名称中的所有地点信息
        '''
        sql = "SELECT scene_locations FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s AND scene_name = '%s' GROUP BY scene_locations ORDER BY scene_id ASC" % (productid, scenename)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryProductTimeperiodsInScene(self, productid, scenename, scenelocation):
        '''获取商品场次的某个场次名称中的所有时间段信息
        '''
        productinfo = self.QueryProductInfo(productid)
        producttype = int(productinfo[4] if not self.IsDbUseDictCursor() else productinfo["product_type"])
        if producttype == 1 or producttype == 4 or producttype == 6 or producttype == 7:
            sql = "SELECT scene_timeperiod FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s AND scene_name = '%s' AND scene_locations = '%s' GROUP BY scene_timeperiod ORDER BY scene_id ASC" % (productid, scenename, scenelocation)
        elif producttype == 2:
            sql = "SELECT scene_timeperiod FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s AND scene_name = '%s' GROUP BY scene_timeperiod ORDER BY scene_id ASC" % (productid, scenename)
        elif producttype == 3:
            sql = "SELECT scene_timeperiod FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s AND scene_locations = '%s' GROUP BY scene_timeperiod ORDER BY scene_id ASC" % (productid, scenelocation)
        elif producttype == 5:
            sql = "SELECT scene_timeperiod FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def GetDefaultSceneFromScenes(self, productscenes):
        if productscenes is None:
            return [] if not self.IsDbUseDictCursor() else dict({})
        if len(productscenes) < 1:
            return [] if not self.IsDbUseDictCursor() else dict({})
        if len(productscenes) == 1:
            return productscenes[0]

        defaultscene = []
        for sceneinfo in productscenes:
            scene_time1 = sceneinfo[2] if not self.IsDbUseDictCursor() else sceneinfo["scene_time1"]
            if scene_time1 is not None and int(scene_time1) == 1:
                defaultscene = sceneinfo
                break
        defaultscene = productscenes[0] if len(defaultscene) < 1 else defaultscene
        return defaultscene

    def QueryProductOfScene(self, productid, scenename, scenelocation, scenetimeperiod):
        productinfo = self.QueryProductInfo(productid)
        producttype = int(productinfo[4] if not self.IsDbUseDictCursor() else productinfo["product_type"])
        if producttype == 1 or producttype == 4 or producttype == 6 or producttype == 7:
            sql = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
            if scenename is not None:
                sql += " AND scene_name = '%s' " % scenename
            if scenelocation is not None:
                sql += " AND scene_locations = '%s' " % scenelocation
            if scenetimeperiod is not None:
                sql += " AND scene_timeperiod = '%s' " % scenetimeperiod
            sql += " ORDER BY scene_id ASC "
        elif producttype == 2:
            sql = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
            if scenename is not None:
                sql += " AND scene_name = '%s' " % scenename
            if scenetimeperiod is not None:
                sql += " AND scene_timeperiod = '%s' " % scenetimeperiod
            sql += " ORDER BY scene_id ASC "
        elif producttype == 3:
            sql = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
            if scenelocation is not None:
                sql += " AND scene_locations = '%s' " % scenelocation
            if scenetimeperiod is not None:
                sql += " AND scene_timeperiod = '%s' " % scenetimeperiod
            sql += " ORDER BY scene_id ASC "
        elif producttype == 5:
            sql = "SELECT * FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryProductPrice(self, productid, scenename=None, scenelocation=None, scenetime=None, count=1, count1=1, count2=0):
        product_id = productid
        productinfo = self.QueryProductInfo(product_id)
        product_type = int(productinfo[4] if not self.IsDbUseDictCursor() else productinfo["product_type"])

        scene_name = scenename
        scene_locations = scenelocation
        scene_timeperiod = scenetime

        product17dongpricelow = self.QueryProduct17dongPrice(product_id, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)
        product17dongpricehigh = self.QueryProduct17dongPrice(product_id, highprice=1, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)

        marketpricelow = self.QueryProductMarketPrice(product_id, highprice=0, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)
        marketpricehigh = self.QueryProductMarketPrice(product_id, highprice=1, scenename=scene_name, scenelocations=scene_locations, scenetimeperiod=scene_timeperiod)

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
            product17dongchildpricelow  = self.QueryProduct17dongChildPrice(product_id, highprice=0, scenename=scene_name, scenetimeperiod=scene_timeperiod)
            product17dongchildpricehigh = self.QueryProduct17dongChildPrice(product_id, highprice=1, scenename=scene_name, scenetimeperiod=scene_timeperiod)

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

        if product_type == 3:
            if not self.IsDbUseDictCursor():
                singleprice = float(productinfo[9]) if productinfo[9] is not None else 0
            else:
                singleprice = float(productinfo["product_price"]) if productinfo["product_price"] is not None else 0
            totalprice = "¥ %.2f" % (count * singleprice)

        if product_type == 5:
            if not self.IsDbUseDictCursor():
                singleprice = float(productinfo[9]) if productinfo[9] is not None else 0
            else:
                singleprice = float(productinfo["product_price"]) if productinfo["product_price"] is not None else 0
            totalprice = "%.0f 分" % (count * singleprice)

        return (price, marketprice, totalprice, childprice)

    #####################################################################################################################################

    def UpdateSceneInfo(self, sceneid, sceneinfo):
        scene_id = sceneid

        scene_productid = sceneinfo["scene_productid"] if sceneinfo.has_key("scene_productid") else None
        scene_time1 = sceneinfo["scene_time1"] if sceneinfo.has_key("scene_time1") else None
        scene_time2 = sceneinfo["scene_time2"] if sceneinfo.has_key("scene_time2") else None
        scene_maxpeople = sceneinfo["scene_maxpeople"] if sceneinfo.has_key("scene_maxpeople") else None
        scene_fullprice = sceneinfo["scene_fullprice"] if sceneinfo.has_key("scene_fullprice") else None

        scene_childprice = sceneinfo["scene_childprice"] if sceneinfo.has_key("scene_childprice") else None
        scene_name = sceneinfo["scene_name"] if sceneinfo.has_key("scene_name") else None
        scene_locations = sceneinfo["scene_locations"] if sceneinfo.has_key("scene_locations") else None
        scene_timeperiod = sceneinfo["scene_timeperiod"] if sceneinfo.has_key("scene_timeperiod") else None
        scene_marketprice = sceneinfo["scene_marketprice"] if sceneinfo.has_key("scene_marketprice") else None
        scene_points = sceneinfo["scene_points"] if sceneinfo.has_key("scene_points") else None
        scene_promotionprice = sceneinfo["scene_promotionprice"] if sceneinfo.has_key("scene_promotionprice") else None
        scene_promotionbegintime = sceneinfo["scene_promotionbegintime"] if sceneinfo.has_key("scene_promotionbegintime") else None
        scene_promotionendtime = sceneinfo["scene_promotionendtime"] if sceneinfo.has_key("scene_promotionendtime") else None
        scene_description = sceneinfo["scene_description"] if sceneinfo.has_key("scene_description") else None
        deleteflag = sceneinfo["deleteflag"] if sceneinfo.has_key("deleteflag") else None

        cursor = self.db.cursor()

        sql     = "UPDATE scene_table SET "
        param   = []
        setted  = False
        if scene_productid is not None:
            sql += " scene_productid = %s "
            param.append(scene_productid)
            setted = True
        if scene_time1 is not None:
            sql += (", scene_time1 = %s " if setted else " scene_time1 = %s ")
            param.append(scene_time1)
            setted = True
        if scene_time2 is not None:
            sql += (", scene_time2 = %s " if setted else " scene_time2 = %s ")
            param.append(scene_time2)
            setted = True
        if scene_maxpeople is not None:
            sql += (", scene_maxpeople = %s " if setted else " scene_maxpeople = %s ")
            param.append(scene_maxpeople)
            setted = True
        if scene_fullprice is not None:
            sql += (", scene_fullprice = %s " if setted else " scene_fullprice = %s ")
            param.append(scene_fullprice)
            setted = True
        if scene_childprice is not None:
            sql += (", scene_childprice = %s " if setted else " scene_childprice = %s ")
            param.append(scene_childprice)
            setted = True
        if scene_name is not None:
            sql += (", scene_name = %s " if setted else " scene_name = %s ")
            param.append(scene_name)
            setted = True
        if scene_locations is not None:
            sql += (", scene_locations = %s " if setted else " scene_locations = %s ")
            param.append(scene_locations)
            setted = True
        if scene_timeperiod is not None:
            sql += (", scene_timeperiod = %s " if setted else " scene_timeperiod = %s ")
            param.append(scene_timeperiod)
            setted = True
        if scene_marketprice is not None:
            sql += (", scene_marketprice = %s " if setted else " scene_marketprice = %s ")
            param.append(scene_marketprice)
            setted = True
        if scene_points is not None:
            sql += (", scene_points = %s " if setted else " scene_points = %s ")
            param.append(scene_points)
            setted = True
        if scene_promotionprice is not None:
            sql += (", scene_promotionprice = %s " if setted else " scene_promotionprice = %s ")
            param.append(scene_promotionprice)
            setted = True
        if scene_promotionbegintime is not None:
            sql += (", scene_promotionbegintime = %s " if setted else " scene_promotionbegintime = %s ")
            param.append(scene_promotionbegintime)
            setted = True
        if scene_promotionendtime is not None:
            sql += (", scene_promotionendtime = %s " if setted else " scene_promotionendtime = %s ")
            param.append(scene_promotionendtime)
            setted = True
        if scene_description is not None:
            sql += (", scene_description = %s " if setted else " scene_description = %s ")
            param.append(scene_description)
            setted = True
        if deleteflag is not None:
            sql += (", deleteflag = %s " if setted else " deleteflag = %s ")
            param.append(deleteflag)
            setted = True

        if setted:
            sql += " WHERE scene_id = %s"
            param.append(scene_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    #####################################################################################################################################

    def DeleteScene(self, sceneid):
        cursor = self.db.cursor()
        sql = "UPDATE scene_table SET deleteflag = 1 WHERE scene_id = %s" % sceneid # "DELETE FROM scene_table WHERE scene_id = %s"
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def DeleteProductScenes(self, productid):
        '''删除商品的所有场次信息
        '''
        cursor = self.db.cursor()
        sql = "UPDATE scene_table SET deleteflag = 1 WHERE scene_productid = %s" % productid # "DELETE FROM scene_table WHERE scene_productid = %s" % productid
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddComment(self, commentinfo):
        comment_userid = commentinfo["comment_userid"]
        comment_productid = commentinfo["comment_productid"]
        comment_content = commentinfo["comment_content"]
        comment_level = commentinfo["comment_level"]
        comment_score1 = commentinfo["comment_score1"] if commentinfo.has_key("comment_score1") else None
        comment_score2 = commentinfo["comment_score2"] if commentinfo.has_key("comment_score2") else None
        comment_score3 = commentinfo["comment_score3"] if commentinfo.has_key("comment_score3") else None
        comment_time = strftime("%Y-%m-%d %H:%M:%S")

        try:
            # UCS-4
            highpoints = re.compile(u'[\U00010000-\U0010ffff]')
        except re.error:
            # UCS-2
            highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
        comment_content = highpoints.sub(u'\u25FD', comment_content)
        
        cursor = self.db.cursor()
        value = [None, comment_userid, comment_productid, comment_content, comment_time, comment_level, comment_score1, comment_score2, comment_score3]
        cursor.execute("INSERT INTO comment_table (comment_id, comment_userid, comment_productid, comment_content, comment_time, \
            comment_level, comment_score1, comment_score2, comment_score3) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        commentid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return commentid

    def GetProductCommentScore(self, productid):
        cursor = self.db.cursor()
        sql1 = "SELECT (SUM(comment_score1) + SUM(comment_score2) + SUM(comment_score3)) AS totalscore FROM comment_table WHERE comment_productid = %s" % productid
        cursor.execute(sql1)
        result = cursor.fetchone()
        if not self.IsDbUseDictCursor():
            totalscore = result[0] if result[0] is not None else 0
        else:
            totalscore = result["totalscore"] if result["totalscore"] is not None else 0

        sql2 = "SELECT COUNT(*) AS COUNT FROM comment_table WHERE comment_productid = %s" % productid
        cursor.execute(sql2)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            totalcount = result[0] if result[0] is not None else 0
        else:
            totalcount = result["COUNT"] if result["COUNT"] is not None else 0

        if totalcount and totalscore:
            totalscore = float(totalscore)
            totalcount = float(totalcount)
            return "%.0f" % (totalscore / totalcount / 3.0)
        else:
            return 0

    #####################################################################################################################################

    def QueryAllCommentCount(self, commentproductid=0, productvendorid=0):
        cursor = self.db.cursor()
        if commentproductid == 0:
            if productvendorid == 0:
                sql = "SELECT COUNT(*) AS COUNT FROM comment_table"
            else:
                sql = "SELECT COUNT(*) AS COUNT FROM comment_table WHERE comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s )" % productvendorid
        else:
            if productvendorid == 0:
                sql = "SELECT COUNT(*) AS COUNT FROM comment_table WHERE comment_productid = %d" % commentproductid
            else:
                sql = "SELECT COUNT(*) AS COUNT FROM comment_table WHERE comment_productid = %d AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s )" % (commentproductid, productvendorid)
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryComments(self, startpos, count=settings.LIST_ITEM_PER_PAGE, commentproductid=0, productvendorid=0, commentlevel=2):
        cursor = self.db.cursor()
        if count == 0:
            if commentproductid == 0:
                if productvendorid == 0:
                    if commentlevel == 2:
                        sql = "SELECT * FROM comment_table ORDER BY comment_time DESC"
                    else:
                        sql = "SELECT * FROM comment_table WHERE comment_level = %s ORDER BY comment_time DESC" % commentlevel
                else:
                    if commentlevel == 2:
                        sql = "SELECT * FROM comment_table WHERE comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_time DESC" % productvendorid
                    else:
                        sql = "SELECT * FROM comment_table WHERE comment_level = %s AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_time DESC" % (commentlevel, productvendorid)
            else:
                if productvendorid == 0:
                    if commentlevel == 2:
                        sql = "SELECT * FROM comment_table WHERE comment_productid = %d ORDER BY comment_time DESC" % commentproductid
                    else:
                        sql = "SELECT * FROM comment_table WHERE comment_level = %s AND comment_productid = %d ORDER BY comment_time DESC" % (commentlevel, commentproductid)
                else:
                    if commentlevel == 2:
                        sql = "SELECT * FROM comment_table WHERE comment_productid = %d AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_time DESC" % (commentproductid, productvendorid)
                    else:
                        sql = "SELECT * FROM comment_table WHERE comment_level = %s AND comment_productid = %d AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_time DESC" % (commentlevel, commentproductid, productvendorid)
        else:
            if commentproductid == 0:
                if productvendorid == 0:
                    if commentlevel == 2:
                        sql = "SELECT * FROM comment_table ORDER BY comment_time DESC LIMIT %s, %s" % (startpos, count)
                    else:
                        sql = "SELECT * FROM comment_table WHERE comment_level = %s ORDER BY comment_time DESC LIMIT %s, %s" % (commentlevel, startpos, count)
                else:
                    if commentlevel == 2:
                        sql = "SELECT * FROM comment_table WHERE comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_time DESC LIMIT %s, %s" % (productvendorid, startpos, count)
                    else:
                        sql = "SELECT * FROM comment_table WHERE comment_level = %s AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_time DESC LIMIT %s, %s" % (commentlevel, productvendorid, startpos, count)
            else:
                if productvendorid == 0:
                    if commentlevel == 2:
                        sql = "SELECT * FROM comment_table WHERE comment_productid = %d ORDER BY comment_time DESC LIMIT %s, %s" % (commentproductid, startpos, count)
                    else:                    
                        sql = "SELECT * FROM comment_table WHERE comment_level = %s AND comment_productid = %d ORDER BY comment_time DESC LIMIT %s, %s" % (commentlevel, commentproductid, startpos, count)
                else:
                    if commentlevel == 2:
                        sql = "SELECT * FROM comment_table WHERE comment_productid = %d AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_time DESC LIMIT %s, %s" % (commentproductid, productvendorid, startpos, count)
                    else:
                        sql = "SELECT * FROM comment_table WHERE comment_level = %s AND comment_productid = %d AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_time DESC LIMIT %s, %s" % (commentlevel, commentproductid, productvendorid, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def FuzzyQueryComments(self, commentkey, startpos, count=settings.LIST_ITEM_PER_PAGE, productvendorid=0):
        cursor = self.db.cursor()
        commentkey = commentkey.replace("'", "''") if commentkey else commentkey

        if productvendorid == 0:
            sql = "SELECT * FROM comment_table WHERE comment_content LIKE '%%%s%%' ORDER BY comment_id DESC LIMIT %s, %s" % (commentkey, startpos, count)
        else:
            sql = "SELECT * FROM comment_table WHERE comment_content LIKE '%%%s%%' AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s ) ORDER BY comment_id DESC LIMIT %s, %s" % (commentkey, productvendorid, startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def FuzzyQueryCommentCount(self, commentkey, productvendorid=0):
        cursor = self.db.cursor()
        commentkey = commentkey.replace("'", "''") if commentkey else commentkey

        if productvendorid == 0:
            sql = "SELECT COUNT(*) AS COUNT FROM comment_table WHERE comment_content LIKE '%%%s%%'" % commentkey
        else:
            sql = "SELECT COUNT(*) AS COUNT FROM comment_table WHERE comment_content LIKE '%%%s%%' AND comment_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_vendorid = %s )" % (commentkey, productvendorid)

        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    #####################################################################################################################################

    def QueryCommentInfo(self, commentid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM comment_table WHERE comment_id = %s LIMIT 1"
        param = [commentid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    #####################################################################################################################################

    def UpdateCommentInfo(self, commentid, commentinfo):
        comment_id = commentid

        comment_userid = commentinfo["comment_userid"] if commentinfo.has_key("comment_userid") else None
        comment_productid = commentinfo["comment_productid"] if commentinfo.has_key("comment_productid") else None
        comment_content = commentinfo["comment_content"] if commentinfo.has_key("comment_content") else None
        comment_time = commentinfo["comment_time"] if commentinfo.has_key("comment_time") else None
        comment_level = commentinfo["comment_level"] if commentinfo.has_key("comment_level") else None
        comment_score1 = commentinfo["comment_score1"] if commentinfo.has_key("comment_score1") else None
        comment_score2 = commentinfo["comment_score2"] if commentinfo.has_key("comment_score2") else None
        comment_score3 = commentinfo["comment_score3"] if commentinfo.has_key("comment_score3") else None

        cursor = self.db.cursor()

        sql     = "UPDATE comment_table SET "
        param   = []
        setted  = False
        if comment_userid is not None:
            sql += " comment_userid = %s "
            param.append(comment_userid)
            setted = True
        if comment_productid is not None:
            sql += (", comment_productid = %s " if setted else " comment_productid = %s ")
            param.append(comment_productid)
            setted = True
        if comment_content is not None:
            sql += (", comment_content = %s " if setted else " comment_content = %s ")
            param.append(comment_content)
            setted = True
        if comment_time is not None:
            sql += (", comment_time = %s " if setted else " comment_time = %s ")
            param.append(comment_time)
            setted = True
        if comment_level is not None:
            sql += (", comment_level = %s " if setted else " comment_level = %s ")
            param.append(comment_level)
            setted = True
        if comment_score1 is not None:
            sql += (", comment_score1 = %s " if setted else " comment_score1 = %s ")
            param.append(comment_score1)
            setted = True
        if comment_score2 is not None:
            sql += (", comment_score2 = %s " if setted else " comment_score2 = %s ")
            param.append(comment_score2)
            setted = True
        if comment_score3 is not None:
            sql += (", comment_score3 = %s " if setted else " comment_score3 = %s ")
            param.append(comment_score3)
            setted = True
        
        if setted:
            sql += " WHERE comment_id = %s"
            param.append(comment_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    #####################################################################################################################################

    def DeleteComment(self, commentid):
        cursor = self.db.cursor()
        sql = "DELETE FROM comment_table WHERE comment_id = %s"
        param = [commentid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    def DeleteCommentByProductId(self, productid):
        cursor = self.db.cursor()
        sql = "DELETE FROM comment_table WHERE comment_productid = %s"
        param = [productid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddProduct(self, productinfo):
        product_vendorid = productinfo["product_vendorid"]
        product_name = productinfo["product_name"]
        product_type = productinfo["product_type"]
        product_item = productinfo["product_item"]
        product_status = productinfo["product_status"]

        product_dividedrate = productinfo["product_dividedrate"] if productinfo.has_key("product_dividedrate") else 0
        product_price = productinfo["product_price"] if productinfo.has_key("product_price") else None
        product_area = productinfo["product_area"] if productinfo.has_key("product_area") else  None
        product_applicableage = productinfo["product_applicableage"] if productinfo.has_key("product_applicableage") else 0
        product_avatar = productinfo["product_avatar"] if productinfo.has_key("product_avatar") else None
        product_availabletime = productinfo["product_availabletime"] if productinfo.has_key("product_availabletime") else None
        product_discounts = 0 # productinfo["product_discounts"] if productinfo.has_key("product_discounts") else None
        product_description = productinfo["product_description"] if productinfo.has_key("product_description") else None
        product_maxdeductiblepoints = productinfo["product_maxdeductiblepoints"] if productinfo.has_key("product_maxdeductiblepoints") else None
        product_auditstatus = productinfo["product_auditstatus"] if productinfo.has_key("product_auditstatus") else None
        product_isadproduct = productinfo["product_isadproduct"] if productinfo.has_key("product_isadproduct") else 0
        product_isrecommendedproduct = productinfo["product_isrecommendedproduct"] if productinfo.has_key("product_isrecommendedproduct") else 0

        product_recommendbegintime = productinfo["product_recommendbegintime"] if productinfo.has_key("product_recommendbegintime") else None
        product_recommendendtime = productinfo["product_recommendendtime"] if productinfo.has_key("product_recommendendtime") else None
        product_allowviplevel = productinfo["product_allowviplevel"] if productinfo.has_key("product_allowviplevel") else None
        product_balancepaytime = productinfo["product_balancepaytime"] if productinfo.has_key("product_balancepaytime") else None
        product_paymentdescription = productinfo["product_paymentdescription"] if productinfo.has_key("product_paymentdescription") else None
        product_precautions = productinfo["product_precautions"] if productinfo.has_key("product_precautions") else None
        product_auditfailreason = productinfo["product_auditfailreason"] if productinfo.has_key("product_auditfailreason") else None
        product_auditfaildescription = productinfo["product_auditfaildescription"] if productinfo.has_key("product_auditfaildescription") else None
        product_sortweight = productinfo["product_sortweight"] if productinfo.has_key("product_sortweight") else 0
        product_traveltype = productinfo["product_traveltype"] if productinfo.has_key("product_traveltype") else None
        product_travelstartplace = productinfo["product_travelstartplace"] if productinfo.has_key("product_travelstartplace") else None
        product_travelendplace = productinfo["product_travelendplace"] if productinfo.has_key("product_travelendplace") else None
        product_traveldays = productinfo["product_traveldays"] if productinfo.has_key("product_traveldays") else None
        product_eventbegintime = productinfo["product_eventbegintime"] if productinfo.has_key("product_eventbegintime") else None
        product_eventendtime = productinfo["product_eventendtime"] if productinfo.has_key("product_eventendtime") else None
        product_couponwhenorder = productinfo["product_couponwhenorder"] if productinfo.has_key("product_couponwhenorder") else None
        product_couponwhenactivate = productinfo["product_couponwhenactivate"] if productinfo.has_key("product_couponwhenactivate") else None
        product_couponrestriction = productinfo["product_couponrestriction"] if productinfo.has_key("product_couponrestriction") else None
        deleteflag = 0
        product_inputuserid = productinfo["product_inputuserid"] if productinfo.has_key("product_inputuserid") else 0
        product_inputtime = strftime("%Y-%m-%d %H:%M:%S")
        product_purchaselimit = productinfo["product_purchaselimit"] if productinfo.has_key("product_purchaselimit") else None
        if product_purchaselimit == '':
            product_purchaselimit = None
        product_parentitem = productinfo["product_parentitem"] if productinfo.has_key("product_parentitem") else None

        cursor = self.db.cursor()
        value = [ None, product_vendorid, product_name, product_availabletime, product_type, product_avatar, product_area, 
            product_applicableage, product_item, product_price, product_discounts, product_dividedrate, product_description, 
            product_status, product_maxdeductiblepoints, product_auditstatus, product_isadproduct, product_isrecommendedproduct, 
            product_recommendbegintime, product_recommendendtime, product_allowviplevel, product_balancepaytime, 
            product_paymentdescription, product_precautions, product_auditfailreason, product_auditfaildescription, product_sortweight, 
            product_traveltype, product_travelstartplace, product_travelendplace, product_traveldays, product_eventbegintime, 
            product_eventendtime, product_couponwhenorder, product_couponwhenactivate, product_couponrestriction, deleteflag, product_inputuserid,
            product_inputtime, product_purchaselimit, product_parentitem ]
        cursor.execute("INSERT INTO product_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        productid = cursor.lastrowid
        self.db.commit()
        cursor.close()

        if product_type != 9:
            self.UpdateRssFeed(product_type)

        return productid

    def UpdateProductInputtime(self):
        allproducts = self.QueryProducts(startpos=0, count=0, producttype=0, frontend=0, productitem=None, productvendorid=0, orderby=0)
        for productinfo in allproducts:
            inputtime = productinfo["product_availabletime"]
            if inputtime is None:
                inputtime = strftime("%Y-%m-%d %H:%M:%S")
            self.UpdateProductInfo(productid=productinfo["product_id"], productinfo={ "product_inputtime" : inputtime })

    def CopyProduct(self, oldproductid, newproductname, inputuserid):
        cursor = self.db.cursor()
        
        # 复制商品表中的数据
        cursor.execute("INSERT INTO product_table SELECT "
            "0,                          product_vendorid,             product_name, "
            "product_availabletime,      product_type,                 product_avatar, "
            "product_area,               product_applicableage,        product_item, "
            "product_price,              product_discounts,            product_dividedrate, "
            "product_description,        product_status,               product_maxdeductiblepoints, "
            "product_auditstatus,        product_isadproduct,          product_isrecommendedproduct, "
            "product_recommendbegintime, product_recommendendtime,     product_allowviplevel, "
            "product_balancepaytime,     product_paymentdescription,   product_precautions, "
            "product_auditfailreason,    product_auditfaildescription, product_sortweight, "
            "product_traveltype,         product_travelstartplace,     product_travelendplace, "
            "product_traveldays,         product_eventbegintime,       product_eventendtime, "
            "product_couponwhenorder,    product_couponwhenactivate,   product_couponrestriction, "
            "deleteflag,                 product_inputuserid,          product_inputtime, "
            "product_purchaselimit,      product_parentitem"
            " FROM product_table WHERE product_id = %s" % oldproductid)
        productid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        self.UpdateProductInfo(productid=productid, productinfo=
            { "product_name" : newproductname, "product_status" : 0, "product_inputuserid" : inputuserid, "product_inputtime" : strftime("%Y-%m-%d %H:%M:%S") })

        # 复制商品的场次信息
        cursor = self.db.cursor()
        sql = "insert into scene_table select %d, %d, scene_time1, scene_time2, scene_maxpeople, scene_fullprice, scene_childprice, scene_name, scene_locations, scene_timeperiod, scene_marketprice, scene_points, scene_promotionprice, scene_promotionbegintime, scene_promotionendtime, scene_description, deleteflag from scene_table where scene_productid = %d" % (0, productid, oldproductid)
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

        # oldproductscenes = self.QueryProductScenes(oldproductid, distinctscenename=False, distinctscenelocation=False, distinctscenetimeperiod=False)
        # for sceneinfo in oldproductscenes:
        #     if not self.IsDbUseDictCursor():
        #         self.AddScene(sceneinfo={"scene_productid" : productid, 
        #                                  "scene_time1" : sceneinfo[2], 
        #                                  "scene_time2" : sceneinfo[3], 
        #                                  "scene_maxpeople" : sceneinfo[4], 
        #                                  "scene_fullprice" : sceneinfo[5], 
        #                                  "scene_childprice" : sceneinfo[6], 
        #                                  "scene_name" : sceneinfo[7], 
        #                                  "scene_locations" : sceneinfo[8], 
        #                                  "scene_timeperiod" : sceneinfo[9], 
        #                                  "scene_marketprice" : sceneinfo[10], 
        #                                  "scene_points" : sceneinfo[11], 
        #                                  "scene_promotionprice" : sceneinfo[12], 
        #                                  "scene_promotionbegintime" : sceneinfo[13], 
        #                                  "scene_promotionendtime" : sceneinfo[14], 
        #                                  "scene_description" : sceneinfo[15] })
        #     else:
        #         self.AddScene(sceneinfo={"scene_productid" : productid, 
        #                                  "scene_time1" : sceneinfo["scene_time1"], 
        #                                  "scene_time2" : sceneinfo["scene_time2"], 
        #                                  "scene_maxpeople" : sceneinfo["scene_maxpeople"], 
        #                                  "scene_fullprice" : sceneinfo["scene_fullprice"], 
        #                                  "scene_childprice" : sceneinfo["scene_childprice"], 
        #                                  "scene_name" : sceneinfo["scene_name"], 
        #                                  "scene_locations" : sceneinfo["scene_locations"], 
        #                                  "scene_timeperiod" : sceneinfo["scene_timeperiod"], 
        #                                  "scene_marketprice" : sceneinfo["scene_marketprice"], 
        #                                  "scene_points" : sceneinfo["scene_points"], 
        #                                  "scene_promotionprice" : sceneinfo["scene_promotionprice"], 
        #                                  "scene_promotionbegintime" : sceneinfo["scene_promotionbegintime"], 
        #                                  "scene_promotionendtime" : sceneinfo["scene_promotionendtime"], 
        #                                  "scene_description" : sceneinfo["scene_description"] })

        return productid

    def getUnicodeStr(self, originalstr):
        result = None
        if isinstance(originalstr, str):
            result = unicode(originalstr, "utf-8")
        elif isinstance(originalstr, unicode):
            result = originalstr
        else:
            result = None
        return result

    #####################################################################################################################################

    def IsVendorHasProduct(self, vendorid, productid):
        '''检测供应商是否拥有某件商品
        '''
        sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_id = %s AND product_vendorid = %s" % (productid, vendorid)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return True if result is not None else False

    def QueryAllProductCount(self, producttype=0, productvendorid=0):
        cursor = self.db.cursor()
        if producttype == 0:
            if productvendorid == 0:
                sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0"
            else:
                sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0 AND product_vendorid = %d" % productvendorid
        else:
            if productvendorid == 0:
                sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0 AND product_type = %s" % producttype
            else:
                sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_vendorid = %d" % (producttype, productvendorid)
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryUserBuyProductCounts(self, userid, productid):
        cursor = self.db.cursor()
        sql = "SELECT SUM(preorder_counts) AS COUNT FROM preorder_table WHERE preorder_paymentstatus = 1 AND preorder_userid = %s AND preorder_productid = %s" % (userid, productid)
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryProducts(self, startpos, count=settings.LIST_ITEM_PER_PAGE, producttype=0, frontend=0, productitem=None, productvendorid=0, orderby=0, startdate=None, enddate=None, sort=1, seckillproduct=0):
        '''查询商品
            startpos: 查询起始位置
            count: 查询数量
            producttype: 查询商品类型
            frontend: 是否只查询已上架的商品
            productitem: 查询商品子类别
            productvendorid: 查询某个供应商的商品
            orderby: 排序规则，0 - 按权重排序，1 - 按商品ID排序，2 - 按销量排序，3 - 按销售金额排序
            startdate & enddate: 查询某个录入时间段内的商品
            sort: 排序顺序，1 - 降序，0 - 升序
            seckillproduct: 是否查询秒杀商品，1 - 只查询秒杀商品，0 - 只查询非秒杀商品, -1 - 查询全部商品（包括秒杀商品和非秒杀商品）
        '''
        cursor = self.db.cursor()
        if orderby > 1:
            sql = "SELECT product_table.*, SUM(preorder_table.preorder_counts) AS totalsellcount, SUM(preorder_table.preorder_fullprice) AS totalsellmoney FROM product_table LEFT JOIN preorder_table ON (product_table.product_id = preorder_table.preorder_productid AND preorder_table.preorder_paymentstatus = 1) WHERE product_table.deleteflag = 0 "
        else:
            sql = "SELECT * FROM product_table WHERE deleteflag = 0 "
        setted  = False
        
        if producttype != 0:
            sql += " AND product_type = %s " % producttype
            setted = True

        if frontend != 0:
            sql += (" AND product_status = 1 AND product_auditstatus = 1 ")
            setted = True

        if productitem is not None:
            sql += (" AND product_item = '%s' " % productitem)
            setted = True

        if productvendorid != 0:
            sql += (" AND product_vendorid = %s " % productvendorid)
            setted = True

        if startdate is not None and enddate is not None:
            sql += (" AND product_inputtime < '%s' AND product_inputtime > '%s'" % (str(enddate), str(startdate)))

        if int(seckillproduct) == 1:
            sql += " AND product_recommendbegintime IS NOT NULL AND product_recommendendtime IS NOT NULL "
        elif int(seckillproduct) == 0:
            sql += " AND product_recommendbegintime IS NULL AND product_recommendendtime IS NULL "
        else:
            pass

        if orderby == 0:
            orderbyfield = " ORDER BY product_sortweight "

        elif orderby == 1:
            orderbyfield = " ORDER BY product_id "

        elif orderby == 2:
            orderbyfield = " GROUP BY product_table.product_id ORDER BY SUM(preorder_table.preorder_counts) "

        elif orderby == 3:
            orderbyfield = " GROUP BY product_table.product_id ORDER BY SUM(preorder_table.preorder_fullprice) "
            
        else:
            orderbyfield = " ORDER BY product_id "

        if sort == 1:
            sortfield = " DESC "
        else:
            sortfield = " ASC "

        sql += " %s %s " % (orderbyfield, sortfield)

        if count != 0:
            sql += " LIMIT %d, %d " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        #-----------------------------------------------------------------------
        if self.IsDbUseDictCursor():
            for productinfo in result:
                # productseckill: 是否秒杀商品, 1 / 是秒杀商品，0 / 不是秒杀商品
                if productinfo['product_recommendbegintime'] is not None and productinfo['product_recommendendtime'] is not None:
                    productseckill = 1
                else:
                    productseckill = 0
                productinfo["productseckill"] = productseckill

                # productseckillstatus: 秒杀商品当前状态，"notready" / 秒杀尚未开始，"underway" / 正在秒杀，"ended" / 秒杀结束, "illegal" / 非秒杀商品
                if productseckill == 1:
                    now = datetime.datetime.now()
                    now = str(now)
                    now = datetime.datetime(int(now[0:4]), int(now[5:7]), int(now[8:10]), int(now[11:13]), int(now[14:16]), int(now[17:19]))
                    if now < productinfo['product_recommendbegintime']:
                        productseckillstatus = "notready"
                    elif now < productinfo['product_recommendendtime']:
                        productseckillstatus = "underway"
                    else:
                        productseckillstatus = "ended"
                    productinfo['productseckillstatus'] = productseckillstatus
                else:
                    productinfo['productseckillstatus'] = "illegal"
        #-----------------------------------------------------------------------
        return result

    def QueryHotSellProducts(self, startpos, count=settings.LIST_ITEM_PER_PAGE, producttype=0):
        cursor = self.db.cursor()
        if count == 0:
            if producttype == 0:
                sql = "SELECT preorder_productid, COUNT(*) FROM preorder_table WHERE deleteflag = 0 AND preorder_productid IN (SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_status = 1 AND product_auditstatus = 1) GROUP BY preorder_productid ORDER BY COUNT(*) DESC"
            else:
                sql = "SELECT preorder_productid, COUNT(*) FROM preorder_table WHERE deleteflag = 0 AND preorder_productid IN (SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_status = 1 AND product_auditstatus = 1) GROUP BY preorder_productid ORDER BY COUNT(*) DESC" % producttype
        else:
            if producttype == 0:
                sql = "SELECT preorder_productid, COUNT(*) FROM preorder_table WHERE deleteflag = 0 AND preorder_productid IN (SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_status = 1 AND product_auditstatus = 1) GROUP BY preorder_productid ORDER BY COUNT(*) DESC LIMIT %s, %s" % (startpos, count)
            else:
                sql = "SELECT preorder_productid, COUNT(*) FROM preorder_table WHERE deleteflag = 0 AND preorder_productid IN (SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_status = 1 AND product_auditstatus = 1) GROUP BY preorder_productid ORDER BY COUNT(*) DESC LIMIT %s, %s" % (producttype, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

        allhotproducts = []
        for orderinfo in result:
            productinfo = self.QueryProductInfo(orderinfo[0] if not self.IsDbUseDictCursor() else orderinfo["preorder_productid"])
            allhotproducts.append(productinfo)
        return allhotproducts

    def SearchProducts(self, searchinfo, count=settings.LIST_ITEM_PER_PAGE, producttype=0):
        '''searchinfo字典中包括 "inputkey", "startposition", "price", "age" 参数
        '''
        inputkey = searchinfo["inputkey"]
        try:
            startposition = int(searchinfo["startposition"]) if searchinfo.has_key("startposition") else 0
            startposition = 0 if startposition is None else startposition
        except Exception, e:
            startposition = 0
        price = searchinfo["price"] if searchinfo.has_key("price") else None
        age = searchinfo["age"] if searchinfo.has_key("age") else None

        cursor = self.db.cursor()
        sql = "SELECT * FROM product_table WHERE deleteflag = 0"
        if producttype != 0:
            sql += " AND product_type = %s " % producttype
        sql += " AND product_name LIKE '%%%s%%' AND product_status = 1 AND product_auditstatus = 1 ORDER BY product_id DESC LIMIT %s, %s " % (inputkey, startposition, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        #-----------------------------------------------------------------------
        if self.IsDbUseDictCursor():
            for productinfo in result:
                # productseckill: 是否秒杀商品, 1 / 是秒杀商品，0 / 不是秒杀商品
                if productinfo['product_recommendbegintime'] is not None and productinfo['product_recommendendtime'] is not None:
                    productseckill = 1
                else:
                    productseckill = 0
                productinfo["productseckill"] = productseckill

                # productseckillstatus: 秒杀商品当前状态，"notready" / 秒杀尚未开始，"underway" / 正在秒杀，"ended" / 秒杀结束, "illegal" / 非秒杀商品
                if productseckill == 1:
                    now = datetime.datetime.now()
                    now = str(now)
                    now = datetime.datetime(int(now[0:4]), int(now[5:7]), int(now[8:10]), int(now[11:13]), int(now[14:16]), int(now[17:19]))
                    if now < productinfo['product_recommendbegintime']:
                        productseckillstatus = "notready"
                    elif now < productinfo['product_recommendendtime']:
                        productseckillstatus = "underway"
                    else:
                        productseckillstatus = "ended"
                    productinfo['productseckillstatus'] = productseckillstatus
                else:
                    productinfo['productseckillstatus'] = "illegal"
        #-----------------------------------------------------------------------
        return result

    def QueryFilteredProducts(self, trainingitem, trainingplace, trainingage, trainingvendor, startpos=0, count=settings.LIST_ITEM_PER_PAGE, producttype=1, sort=0, mylocation=(0,0), parentitem=None):
        '''根据培训项目、培训地点和培训年龄查询商品信息（仅限于 product_type 为 1, 6 和 7 的商品）
        '''
        if sort == 1:
            sql  = "SELECT product_table.* FROM product_table LEFT JOIN preorder_table ON product_table.product_id = preorder_table.preorder_productid WHERE product_table.deleteflag = 0 AND product_type = %s AND product_status = 1 AND product_auditstatus = 1 AND product_recommendbegintime IS NULL AND product_recommendendtime IS NULL " % producttype
        elif sort == 3:
            sql  = "SELECT product_table.* FROM product_table LEFT JOIN comment_table ON product_table.product_id = comment_table.comment_productid WHERE product_table.deleteflag = 0 AND product_type = %s AND product_status = 1 AND product_auditstatus = 1 AND product_recommendbegintime IS NULL AND product_recommendendtime IS NULL " % producttype
        else:
            sql  = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_status = 1 AND product_auditstatus = 1 AND product_recommendbegintime IS NULL AND product_recommendendtime IS NULL " % producttype

        if trainingitem is not None and len(str(trainingitem)) != 0:
            sql += " AND product_item = '%s' " % trainingitem

        if parentitem is not None:
            sql += " AND product_parentitem = '%s' " % parentitem

        if trainingplace is not None and trainingplace != "0":
            # sql += " AND product_id IN ( SELECT scene_productid FROM scene_table WHERE scene_locations = '%s' ) " % trainingplace
            sql += " AND product_area = '%s' " % trainingplace

        if trainingage is not None and trainingage != "0":
            sql += " AND (product_applicableage = %s or product_applicableage = 0) " % trainingage

        if producttype == 1 or producttype == 7:
            if trainingvendor is not None and len(str(trainingvendor)) != 0:
                sql += " AND product_vendorid IN ( SELECT user_id FROM user_table WHERE deleteflag = 0 AND user_vendorname = '%s' ) " % trainingvendor

        if producttype == 4:
            sql += " AND product_traveltype != 4 AND product_traveltype != 5 "

        if sort == 0:       # 默认排序
            sql += " ORDER BY product_sortweight DESC "
        elif sort == 1:     # 按销量
            sql += " GROUP BY product_table.product_id ORDER BY COUNT(*) DESC "
        elif sort == 2:     # 按时间
            sql += " ORDER BY product_availabletime DESC "
        elif sort == 3:     # 按评价
            sql += " GROUP BY product_table.product_id ORDER BY COUNT(*) DESC"

        if sort == 4:       # 按价格
            allproducts = self.QueryFilteredProducts(trainingitem, trainingplace, trainingage, trainingvendor, 0, 0, producttype)
            allproducts_new = []
            for productinfo in allproducts:
                minproductprice = self.QueryProductMinPrice(productinfo[0] if not self.IsDbUseDictCursor() else productinfo["product_id"])
                allproducts_new.append({ "ProductInfo" : productinfo, "MinPrice" : float(minproductprice) })
            allproducts_sorted = sorted(allproducts_new, key = lambda x:x['MinPrice'])
            allproducts_result = []
            for productdict in allproducts_sorted:
                allproducts_result.append(productdict["ProductInfo"])
            if count != 0:
                return allproducts_result[startpos:startpos + count]
            else:
                return allproducts_result
        elif sort == 5:     # 按距离
            if int(mylocation[0]) != 0 and int(mylocation[1]) != 0:
                # 当前位置可用，使用位置进行排序
                tf = Transform()
                allproducts = self.QueryFilteredProducts(trainingitem, trainingplace, trainingage, trainingvendor, 0, 0, producttype)
                allproducts_new = []
                for productinfo in allproducts:
                    product_auditfaildescription = productinfo[25] if not self.IsDbUseDictCursor() else productinfo["product_auditfaildescription"]
                    productlocation = json.loads(product_auditfaildescription) if product_auditfaildescription is not None else (0,0)
                    productlocation = (float(productlocation[0]), float(productlocation[1]))
                    if productlocation[0] == 0 and productlocation[1] == 0:
                        productdistance = 999999999
                    else:
                        productdistance = tf.distance(mylocation[0], mylocation[1], productlocation[0], productlocation[1])

                        # logging.debug("mylocation: %r, productlocation: %r, productdistance: %r" % (mylocation, productlocation, productdistance))

                    productinfo = list(productinfo) if not self.IsDbUseDictCursor() else dict(productinfo)
                    if not self.IsDbUseDictCursor():
                        productinfo.append(productdistance) # pop it when return to client
                    else:
                        productinfo["productdistance"] = productdistance
                    allproducts_new.append({ "ProductInfo" : productinfo, "Distance" : float(productdistance) })
                allproducts_sorted = sorted(allproducts_new, key = lambda x:x['Distance'])
                allproducts_result = []
                for productdict in allproducts_sorted:
                    allproducts_result.append(productdict["ProductInfo"])
                if count != 0:
                    return allproducts_result[startpos:startpos + count]
                else:
                    return allproducts_result
            else:
                # 当前位置不可用，使用默认排序
                return self.QueryFilteredProducts(trainingitem, trainingplace, trainingage, trainingvendor, startpos, count, producttype, sort=0, mylocation=(0,0))
        else:
            if count != 0:
                sql += " LIMIT %s, %s " % (startpos, count)

            cursor = self.db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            #-----------------------------------------------------------------------
            if self.IsDbUseDictCursor():
                for productinfo in result:
                    # productseckill: 是否秒杀商品, 1 / 是秒杀商品，0 / 不是秒杀商品
                    if productinfo['product_recommendbegintime'] is not None and productinfo['product_recommendendtime'] is not None:
                        productseckill = 1
                    else:
                        productseckill = 0
                    productinfo["productseckill"] = productseckill

                    # productseckillstatus: 秒杀商品当前状态，"notready" / 秒杀尚未开始，"underway" / 正在秒杀，"ended" / 秒杀结束, "illegal" / 非秒杀商品
                    if productseckill == 1:
                        now = datetime.datetime.now()
                        now = str(now)
                        now = datetime.datetime(int(now[0:4]), int(now[5:7]), int(now[8:10]), int(now[11:13]), int(now[14:16]), int(now[17:19]))
                        if now < productinfo['product_recommendbegintime']:
                            productseckillstatus = "notready"
                        elif now < productinfo['product_recommendendtime']:
                            productseckillstatus = "underway"
                        else:
                            productseckillstatus = "ended"
                        productinfo['productseckillstatus'] = productseckillstatus
                    else:
                        productinfo['productseckillstatus'] = "illegal"
            #-----------------------------------------------------------------------
            return result

    def QueryProductMinPrice(self, productid):
        cursor = self.db.cursor()
        sql = "SELECT MIN(scene_fullprice) AS PRICE FROM scene_table WHERE deleteflag = 0 AND scene_productid = %s" % productid
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            price = result[0] if result[0] is not None else 0
        else:
            price = result["PRICE"] if result["PRICE"] is not None else 0
        return "%.2f" % price

    def QueryTourismProducts(self, filters, startpos=0, count=settings.LIST_ITEM_PER_PAGE):
        '''查询体育旅游商品信息 filters["pstatplace"], filters["pdestplace"], filters["pitem"], filters["pdays"], filters["ptype"], filters["pvendor"]
        '''
        sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_type = 2 AND product_status = 1 AND product_auditstatus = 1 AND product_recommendbegintime IS NULL AND product_recommendendtime IS NULL "

        if filters.has_key("pstatplace") and filters["pstatplace"] is not None:
            sql += " AND product_travelstartplace = '%s' " % filters["pstatplace"]

        if filters.has_key("pdestplace") and filters["pdestplace"] is not None:
            sql += " AND product_travelendplace = '%s' " % filters["pdestplace"]

        if filters.has_key("pitem") and filters["pitem"] is not None:
            sql += " AND product_item = '%s' " % filters["pitem"]

        if filters.has_key("pdays") and filters["pdays"] is not None:
            sql += " AND product_traveldays = %s " % filters["pdays"]

        if filters.has_key("ptype") and filters["ptype"] is not None:
            sql += " AND product_traveltype = %s " % filters["ptype"]

        if filters.has_key("pvendor") and filters["pvendor"] is not None:
            sql += " AND product_vendorid IN ( SELECT user_id FROM user_table WHERE deleteflag = 0 AND user_vendorname = '%s' ) " % filters["pvendor"]

        sql += " ORDER BY product_sortweight DESC "

        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        #-----------------------------------------------------------------------
        if self.IsDbUseDictCursor():
            for productinfo in result:
                # productseckill: 是否秒杀商品, 1 / 是秒杀商品，0 / 不是秒杀商品
                if productinfo['product_recommendbegintime'] is not None and productinfo['product_recommendendtime'] is not None:
                    productseckill = 1
                else:
                    productseckill = 0
                productinfo["productseckill"] = productseckill

                # productseckillstatus: 秒杀商品当前状态，"notready" / 秒杀尚未开始，"underway" / 正在秒杀，"ended" / 秒杀结束, "illegal" / 非秒杀商品
                if productseckill == 1:
                    now = datetime.datetime.now()
                    now = str(now)
                    now = datetime.datetime(int(now[0:4]), int(now[5:7]), int(now[8:10]), int(now[11:13]), int(now[14:16]), int(now[17:19]))
                    if now < productinfo['product_recommendbegintime']:
                        productseckillstatus = "notready"
                    elif now < productinfo['product_recommendendtime']:
                        productseckillstatus = "underway"
                    else:
                        productseckillstatus = "ended"
                    productinfo['productseckillstatus'] = productseckillstatus
                else:
                    productinfo['productseckillstatus'] = "illegal"
        #-----------------------------------------------------------------------
        return result

    def QueryFreetrialProducts(self, filters, startpos=0, count=settings.LIST_ITEM_PER_PAGE):
        '''查询课程体验商品信息 filters["pitem"], filters["plocations"]
        '''
        sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_type = 3 AND product_status = 1 AND product_auditstatus = 1 AND product_recommendbegintime IS NULL AND product_recommendendtime IS NULL "

        if filters.has_key("pitem") and filters["pitem"] is not None:
            sql += " AND product_item = '%s' " % filters["pitem"]

        if filters.has_key("plocations") and filters["plocations"] is not None:
            # sql += " AND product_id IN ( SELECT scene_productid FROM scene_table WHERE scene_locations = '%s' ) " % filters["plocations"]
            sql += " AND product_area = '%s' " % filters["plocations"]

        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        #-----------------------------------------------------------------------
        if self.IsDbUseDictCursor():
            for productinfo in result:
                # productseckill: 是否秒杀商品, 1 / 是秒杀商品，0 / 不是秒杀商品
                if productinfo['product_recommendbegintime'] is not None and productinfo['product_recommendendtime'] is not None:
                    productseckill = 1
                else:
                    productseckill = 0
                productinfo["productseckill"] = productseckill

                # productseckillstatus: 秒杀商品当前状态，"notready" / 秒杀尚未开始，"underway" / 正在秒杀，"ended" / 秒杀结束, "illegal" / 非秒杀商品
                if productseckill == 1:
                    now = datetime.datetime.now()
                    now = str(now)
                    now = datetime.datetime(int(now[0:4]), int(now[5:7]), int(now[8:10]), int(now[11:13]), int(now[14:16]), int(now[17:19]))
                    if now < productinfo['product_recommendbegintime']:
                        productseckillstatus = "notready"
                    elif now < productinfo['product_recommendendtime']:
                        productseckillstatus = "underway"
                    else:
                        productseckillstatus = "ended"
                    productinfo['productseckillstatus'] = productseckillstatus
                else:
                    productinfo['productseckillstatus'] = "illegal"
        #-----------------------------------------------------------------------
        return result

    def FuzzyQueryProduct(self, productkey, startpos=0, count=settings.LIST_ITEM_PER_PAGE, producttype=0, frontend=0, productvendorid=0, seckillproduct=0):
        cursor = self.db.cursor()
        productkey = productkey.replace("'", "''") if productkey else productkey

        sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_name LIKE '%%%s%%'" % productkey
        if producttype != 0:
            sql += " AND product_type = %s " % producttype
        if frontend != 0:
            sql += " AND product_status = 1 AND product_auditstatus = 1 "
        if productvendorid != 0:
            sql += " AND product_vendorid = %s " % productvendorid
        
        if int(seckillproduct) == 1:
            sql += " AND product_recommendbegintime IS NOT NULL AND product_recommendendtime IS NOT NULL "
        elif int(seckillproduct) == 0:
            sql += " AND product_recommendbegintime IS NULL AND product_recommendendtime IS NULL "
        else:
            pass

        sql += " ORDER BY product_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
                    
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        #-----------------------------------------------------------------------
        if self.IsDbUseDictCursor():
            for productinfo in result:
                # productseckill: 是否秒杀商品, 1 / 是秒杀商品，0 / 不是秒杀商品
                if productinfo['product_recommendbegintime'] is not None and productinfo['product_recommendendtime'] is not None:
                    productseckill = 1
                else:
                    productseckill = 0
                productinfo["productseckill"] = productseckill

                # productseckillstatus: 秒杀商品当前状态，"notready" / 秒杀尚未开始，"underway" / 正在秒杀，"ended" / 秒杀结束, "illegal" / 非秒杀商品
                if productseckill == 1:
                    now = datetime.datetime.now()
                    now = str(now)
                    now = datetime.datetime(int(now[0:4]), int(now[5:7]), int(now[8:10]), int(now[11:13]), int(now[14:16]), int(now[17:19]))
                    if now < productinfo['product_recommendbegintime']:
                        productseckillstatus = "notready"
                    elif now < productinfo['product_recommendendtime']:
                        productseckillstatus = "underway"
                    else:
                        productseckillstatus = "ended"
                    productinfo['productseckillstatus'] = productseckillstatus
                else:
                    productinfo['productseckillstatus'] = "illegal"
        #-----------------------------------------------------------------------
        return result

    def FuzzyQueryProductCount(self, productkey, producttype=0, productvendorid=0):
        cursor = self.db.cursor()
        productkey = productkey.replace("'", "''") if productkey else productkey
        if producttype == 0:
            if productvendorid == 0:
                sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0 AND product_name LIKE '%%%s%%'" % productkey
            else:
                sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0 AND product_name LIKE '%%%s%%' AND product_vendorid = %d" % (productkey, productvendorid)
        else:
            if productvendorid == 0:
                sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_name LIKE '%%%s%%'" % (producttype, productkey)
            else:
                sql = "SELECT COUNT(*) AS COUNT FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_name LIKE '%%%s%%' AND product_vendorid = %s" % (producttype, productkey, productvendorid)
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryAllAdvertisedProduct(self, adsplatform=3, adsposition=1, startpos=0, count=0):
        '''根据发布平台和广告位置查询广告
            WEB ( 1 )
            手机端 ( 2 )
            全部 ( 3 )
        '''
        cursor = self.db.cursor()
        if adsplatform == 3:
            sql = "SELECT * FROM ads_table WHERE ads_auditstate = 1 AND ads_state = 1 AND ads_position = %s ORDER BY ads_sortweight DESC" % adsposition
            if count != 0:
                sql += " LIMIT %s, %s " % (startpos, count)
        else:
            sql = "SELECT * FROM ads_table WHERE ads_auditstate = 1 AND ads_state = 1 AND ads_platform IN (%s, 3) AND ads_position = %s ORDER BY ads_sortweight DESC" % (adsplatform, adsposition)
            if count != 0:
                sql += " LIMIT %s, %s " % (startpos, count)
        
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryAllRecommendedProduct(self, startpos=0, count=0, producttype=0, productitem=None):
        cursor = self.db.cursor()
        if count == 0:
            if producttype == 0:
                if productitem is None:
                    sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_isrecommendedproduct = 1 AND product_status = 1 AND product_auditstatus = 1 ORDER BY product_sortweight DESC"
                else:
                    sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_isrecommendedproduct = 1 AND product_status = 1 AND product_auditstatus = 1 AND product_item = '%s' ORDER BY product_sortweight DESC" % productitem
            else:
                if productitem is None:
                    sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_isrecommendedproduct = 1 AND product_status = 1 AND product_auditstatus = 1 ORDER BY product_sortweight DESC" % producttype
                else:
                    sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_isrecommendedproduct = 1 AND product_status = 1 AND product_auditstatus = 1 AND product_item = '%s' ORDER BY product_sortweight DESC" % (producttype, productitem)
        else:
            if producttype == 0:
                if productitem is None:
                    sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_isrecommendedproduct = 1 AND product_status = 1 AND product_auditstatus = 1 ORDER BY product_sortweight DESC LIMIT %s, %s" % (startpos, count)
                else:
                    sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_isrecommendedproduct = 1 AND product_status = 1 AND product_auditstatus = 1 AND product_item = '%s' ORDER BY product_sortweight DESC LIMIT %s, %s" % (productitem, startpos, count)
            else:
                if productitem is None:
                    sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_isrecommendedproduct = 1 AND product_status = 1 AND product_auditstatus = 1 ORDER BY product_sortweight DESC LIMIT %s, %s" % (producttype, startpos, count)
                else:
                    sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_type = %s AND product_isrecommendedproduct = 1 AND product_status = 1 AND product_auditstatus = 1 AND product_item = '%s' ORDER BY product_sortweight DESC LIMIT %s, %s" % (producttype, productitem, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        #-----------------------------------------------------------------------
        if self.IsDbUseDictCursor():
            for productinfo in result:
                # productseckill: 是否秒杀商品, 1 / 是秒杀商品，0 / 不是秒杀商品
                if productinfo['product_recommendbegintime'] is not None and productinfo['product_recommendendtime'] is not None:
                    productseckill = 1
                else:
                    productseckill = 0
                productinfo["productseckill"] = productseckill

                # productseckillstatus: 秒杀商品当前状态，"notready" / 秒杀尚未开始，"underway" / 正在秒杀，"ended" / 秒杀结束, "illegal" / 非秒杀商品
                if productseckill == 1:
                    now = datetime.datetime.now()
                    now = str(now)
                    now = datetime.datetime(int(now[0:4]), int(now[5:7]), int(now[8:10]), int(now[11:13]), int(now[14:16]), int(now[17:19]))
                    if now < productinfo['product_recommendbegintime']:
                        productseckillstatus = "notready"
                    elif now < productinfo['product_recommendendtime']:
                        productseckillstatus = "underway"
                    else:
                        productseckillstatus = "ended"
                    productinfo['productseckillstatus'] = productseckillstatus
                else:
                    productinfo['productseckillstatus'] = "illegal"
        #-----------------------------------------------------------------------
        return result

    #####################################################################################################################################

    def QueryProductPaymentProcess(self, productid):
        onserver = (socket.gethostname() == settings.SERVER_HOST_NAME)
        productinfo = self.QueryProductInfo(productid)
        product_type = int(productinfo[4] if not self.IsDbUseDictCursor() else productinfo["product_type"])

        if product_type == 1 or product_type == 7:
            # 体育培训
            articleinfo = self.QueryArticleInfo(articlesid=237 if onserver else 6)
        elif product_type == 2:
            # 体育旅游
            articleinfo = self.QueryArticleInfo(articlesid=238 if onserver else 7)
        elif product_type == 3:
            # 课程体验
            articleinfo = self.QueryArticleInfo(articlesid=237 if onserver else 3)
        elif product_type == 4:
            # 精彩活动
            articleinfo = self.QueryArticleInfo(articlesid=240 if onserver else 6)
        elif product_type == 5:
            # 积分商城
            articleinfo = self.QueryArticleInfo(articlesid=237 if onserver else 6)
        elif product_type == 6:
            # 私人教练
            articleinfo = self.QueryArticleInfo(articlesid=239 if onserver else 9)
        else:
            articleinfo = None

        if articleinfo is None:
            paymentprocess = None
        else:
            paymentprocess = articleinfo[3] if not self.IsDbUseDictCursor() else articleinfo["articles_content"]
        return paymentprocess

    def QueryProductInfo(self, productid):
        try:
            productid = int(productid)
        except Exception, e:
            return None

        cursor = self.db.cursor()
        sql   = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_id = %s LIMIT 1"
        param = [productid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        if result is None:
            return None

        # The avatars should be deserialized for templates to loop over.
        if not self.IsDbUseDictCursor():
            result = list(result)
            if result[5] and result[5].startswith('['):
                try:
                    result[5] = json.loads(result[5])
                except (TypeError, ValueError):
                    result[5] = []
            else:
                result[5] = [result[5]]
            result = tuple(result)
            return result
        else:
            result = dict(result)
            if result["product_avatar"] and result["product_avatar"].startswith('['):
                try:
                    result["product_avatar"] = json.loads(result["product_avatar"])
                except (TypeError, ValueError):
                    result["product_avatar"] = []
            else:
                result["product_avatar"] = [result["product_avatar"]]
            result = dict(result)

            #-----------------------------------------------------------------------
            # productseckill: 是否秒杀商品, 1 / 是秒杀商品，0 / 不是秒杀商品
            if self.IsDbUseDictCursor():
                productinfo = result
                if productinfo['product_recommendbegintime'] is not None and productinfo['product_recommendendtime'] is not None:
                    productseckill = 1
                else:
                    productseckill = 0
                productinfo["productseckill"] = productseckill

                # productseckillstatus: 秒杀商品当前状态，"notready" / 秒杀尚未开始，"underway" / 正在秒杀，"ended" / 秒杀结束, "illegal" / 非秒杀商品
                if productseckill == 1:
                    now = datetime.datetime.now()
                    now = str(now)
                    now = datetime.datetime(int(now[0:4]), int(now[5:7]), int(now[8:10]), int(now[11:13]), int(now[14:16]), int(now[17:19]))
                    if now < productinfo['product_recommendbegintime']:
                        productseckillstatus = "notready"
                    elif now < productinfo['product_recommendendtime']:
                        productseckillstatus = "underway"
                    else:
                        productseckillstatus = "ended"
                    productinfo['productseckillstatus'] = productseckillstatus
                else:
                    productinfo['productseckillstatus'] = "illegal"
                result = productinfo
            #-----------------------------------------------------------------------

            return result

    def QueryProductSellCount(self, productid):
        # '''查询商品的销量
        #     sort: 0 - 不排序，-1 从小到大排序， 1 从大到小排序
        # '''
        cursor = self.db.cursor()
        sql = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_productid = %s" % productid
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

        totalsellcount = 0
        for orderinfo in result:
            preorder_counts = int(orderinfo["preorder_counts"])
            totalsellcount += preorder_counts

        return totalsellcount

    def QueryProductSellMoney(self, productid):
        # '''查询商品的销售金额
        #     sort: 0 - 不排序，-1 从小到大排序， 1 从大到小排序
        # '''
        cursor = self.db.cursor()
        sql = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_productid = %s" % productid
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

        totalsellmoney = 0
        for orderinfo in result:
            preorder_fullprice = float(orderinfo["preorder_fullprice"])
            totalsellmoney += preorder_fullprice

        return totalsellmoney

    def QueryProductLocation(self, productid):
        # 获取商品的位置（经纬度信息）
        productinfo = self.QueryProductInfo(productid)

        # logging.debug("productinfo[25]: %r" % productinfo[25])

        if not self.IsDbUseDictCursor():
            product_auditfaildescription = json.loads(productinfo[25]) if productinfo[25] is not None else (0, 0)
        else:
            product_auditfaildescription = json.loads(productinfo["product_auditfaildescription"]) if productinfo["product_auditfaildescription"] is not None else (0, 0)
        return product_auditfaildescription

    #####################################################################################################################################

    def DeleteProductOldAvatar(self, productid, new_avatars):
        '''在更新商品的avatar之前先把老的商品图片删除掉
        '''
        new_avatars = json.loads(new_avatars)
        old_avatar_f_us_pairs = set((f, us) for f, us, _ in self.GetProductAvatarPreviews(productid))
        new_avatar_set = set(new_avatars)
        for f, us in old_avatar_f_us_pairs:
            if us not in new_avatar_set:
                filedir = abspath
                infile   = filedir + '/' + f
                os.remove(infile)

    def UpdateProductInfo(self, productid, productinfo):
        product_id = productid
        oldproductinfo = self.QueryProductInfo(productid)
        product_type = int(oldproductinfo[4] if not self.IsDbUseDictCursor() else oldproductinfo["product_type"])

        product_vendorid = productinfo["product_vendorid"] if productinfo.has_key("product_vendorid") else None
        product_name = productinfo["product_name"] if productinfo.has_key("product_name") else None
        product_availabletime = productinfo["product_availabletime"] if productinfo.has_key("product_availabletime") else None
        # product_type = productinfo["product_type"] if productinfo.has_key("product_type") else None
        product_avatar = productinfo["product_avatar"] if productinfo.has_key("product_avatar") else None
        product_area = productinfo["product_area"] if productinfo.has_key("product_area") else None
        product_applicableage = productinfo["product_applicableage"] if productinfo.has_key("product_applicableage") else None
        product_item = productinfo["product_item"] if productinfo.has_key("product_item") else None
        product_price = productinfo["product_price"] if productinfo.has_key("product_price") else None
        product_discounts = productinfo["product_discounts"] if productinfo.has_key("product_discounts") else None
        product_dividedrate = productinfo["product_dividedrate"] if productinfo.has_key("product_dividedrate") else None
        product_description = productinfo["product_description"] if productinfo.has_key("product_description") else None
        product_status = productinfo["product_status"] if productinfo.has_key("product_status") else None
        product_maxdeductiblepoints = productinfo["product_maxdeductiblepoints"] if productinfo.has_key("product_maxdeductiblepoints") else None
        product_auditstatus = productinfo["product_auditstatus"] if productinfo.has_key("product_auditstatus") else None
        product_isadproduct = productinfo["product_isadproduct"] if productinfo.has_key("product_isadproduct") else None
        product_isrecommendedproduct = productinfo["product_isrecommendedproduct"] if productinfo.has_key("product_isrecommendedproduct") else None

        product_recommendbegintime = productinfo["product_recommendbegintime"] if productinfo.has_key("product_recommendbegintime") else None
        product_recommendendtime = productinfo["product_recommendendtime"] if productinfo.has_key("product_recommendendtime") else None
        product_allowviplevel = productinfo["product_allowviplevel"] if productinfo.has_key("product_allowviplevel") else None
        product_balancepaytime = productinfo["product_balancepaytime"] if productinfo.has_key("product_balancepaytime") else None
        product_paymentdescription = productinfo["product_paymentdescription"] if productinfo.has_key("product_paymentdescription") else None
        product_precautions = productinfo["product_precautions"] if productinfo.has_key("product_precautions") else None
        product_auditfailreason = productinfo["product_auditfailreason"] if productinfo.has_key("product_auditfailreason") else None
        product_auditfaildescription = productinfo["product_auditfaildescription"] if productinfo.has_key("product_auditfaildescription") else None
        product_sortweight = productinfo["product_sortweight"] if productinfo.has_key("product_sortweight") else None
        product_traveltype = productinfo["product_traveltype"] if productinfo.has_key("product_traveltype") else None
        product_travelstartplace = productinfo["product_travelstartplace"] if productinfo.has_key("product_travelstartplace") else None
        product_travelendplace = productinfo["product_travelendplace"] if productinfo.has_key("product_travelendplace") else None
        product_traveldays = productinfo["product_traveldays"] if productinfo.has_key("product_traveldays") else None
        product_eventbegintime = productinfo["product_eventbegintime"] if productinfo.has_key("product_eventbegintime") else None
        product_eventendtime = productinfo["product_eventendtime"] if productinfo.has_key("product_eventendtime") else None
        product_couponwhenorder = productinfo["product_couponwhenorder"] if productinfo.has_key("product_couponwhenorder") else None
        product_couponwhenactivate = productinfo["product_couponwhenactivate"] if productinfo.has_key("product_couponwhenactivate") else None
        product_couponrestriction = productinfo["product_couponrestriction"] if productinfo.has_key("product_couponrestriction") else None
        deleteflag = productinfo["deleteflag"] if productinfo.has_key("deleteflag") else None
        product_inputuserid = productinfo["product_inputuserid"] if productinfo.has_key("product_inputuserid") else None
        product_inputtime = productinfo["product_inputtime"] if productinfo.has_key("product_inputtime") else None
        product_purchaselimit = productinfo["product_purchaselimit"] if productinfo.has_key("product_purchaselimit") else None
        product_parentitem = productinfo["product_parentitem"] if productinfo.has_key("product_parentitem") else None

        cursor = self.db.cursor()

        sql     = "UPDATE product_table SET "
        param   = []
        setted  = False
        if product_vendorid is not None:
            sql += " product_vendorid = %s "
            param.append(product_vendorid)
            setted = True
        if product_name is not None:
            sql += (", product_name = %s " if setted else " product_name = %s ")
            param.append(product_name)
            setted = True
        if product_availabletime is not None:
            sql += (", product_availabletime = %s " if setted else " product_availabletime = %s ")
            param.append(product_availabletime)
            setted = True
        # if product_type is not None:
        #     sql += (", product_type = %s " if setted else " product_type = %s ")
        #     param.append(product_type)
        #     setted = True
        if product_avatar is not None:
            sql += (", product_avatar = %s " if setted else " product_avatar = %s ")
            param.append(product_avatar)
            setted = True
            # self.DeleteProductOldAvatar(product_id)
        if product_area is not None:
            sql += (", product_area = %s " if setted else " product_area = %s ")
            param.append(product_area)
            setted = True
        if product_applicableage is not None:
            sql += (", product_applicableage = %s " if setted else " product_applicableage = %s ")
            param.append(product_applicableage)
            setted = True
        if product_item is not None:
            sql += (", product_item = %s " if setted else " product_item = %s ")
            param.append(product_item)
            setted = True
        if product_price is not None:
            sql += (", product_price = %s " if setted else " product_price = %s ")
            param.append(product_price)
            setted = True
        if product_discounts is not None:
            sql += (", product_discounts = %s " if setted else " product_discounts = %s ")
            param.append(product_discounts)
            setted = True
        if product_dividedrate is not None:
            sql += (", product_dividedrate = %s " if setted else " product_dividedrate = %s ")
            param.append(product_dividedrate)
            setted = True
        if product_description is not None:
            sql += (", product_description = %s " if setted else " product_description = %s ")
            param.append(product_description)
            setted = True
        if product_status is not None:
            sql += (", product_status = %s " if setted else " product_status = %s ")
            param.append(product_status)
            setted = True
        if product_maxdeductiblepoints is not None:
            product_maxdeductiblepoints = float(product_maxdeductiblepoints)
            product_maxdeductiblepoints = product_maxdeductiblepoints if product_maxdeductiblepoints < 100000000 else 100000000
            sql += (", product_maxdeductiblepoints = %s " if setted else " product_maxdeductiblepoints = %s ")
            param.append(product_maxdeductiblepoints)
            setted = True
        if product_auditstatus is not None:
            sql += (", product_auditstatus = %s " if setted else " product_auditstatus = %s ")
            param.append(product_auditstatus)
            setted = True
        if product_isadproduct is not None:
            sql += (", product_isadproduct = %s " if setted else " product_isadproduct = %s ")
            param.append(product_isadproduct)
            setted = True
        if product_isrecommendedproduct is not None:
            sql += (", product_isrecommendedproduct = %s " if setted else " product_isrecommendedproduct = %s ")
            param.append(product_isrecommendedproduct)
            setted = True
        if product_recommendbegintime is not None:
            if product_recommendbegintime != '':
                sql += (", product_recommendbegintime = %s " if setted else " product_recommendbegintime = %s ")
                param.append(product_recommendbegintime)
                setted = True
            else:
                sql += (", product_recommendbegintime = null " if setted else " product_recommendbegintime = null ")
                setted = True
        if product_recommendendtime is not None:
            if product_recommendendtime != '':
                sql += (", product_recommendendtime = %s " if setted else " product_recommendendtime = %s ")
                param.append(product_recommendendtime)
                setted = True
            else:
                sql += (", product_recommendendtime = null " if setted else " product_recommendendtime = null ")
                setted = True
        if product_allowviplevel is not None:
            sql += (", product_allowviplevel = %s " if setted else " product_allowviplevel = %s ")
            param.append(product_allowviplevel)
            setted = True
        if product_balancepaytime is not None:
            if product_balancepaytime != '':
                sql += (", product_balancepaytime = %s " if setted else " product_balancepaytime = %s ")
                param.append(product_balancepaytime)
                setted = True
            else:
                sql += (", product_balancepaytime = null " if setted else " product_balancepaytime = null ")
                setted = True
        if product_paymentdescription is not None:
            sql += (", product_paymentdescription = %s " if setted else " product_paymentdescription = %s ")
            param.append(product_paymentdescription)
            setted = True
        if product_precautions is not None:
            sql += (", product_precautions = %s " if setted else " product_precautions = %s ")
            param.append(product_precautions)
            setted = True
        if product_auditfailreason is not None:
            sql += (", product_auditfailreason = %s " if setted else " product_auditfailreason = %s ")
            param.append(product_auditfailreason)
            setted = True
        if product_auditfaildescription is not None:
            sql += (", product_auditfaildescription = %s " if setted else " product_auditfaildescription = %s ")
            param.append(product_auditfaildescription)
            setted = True
        if product_sortweight is not None:
            sql += (", product_sortweight = %s " if setted else " product_sortweight = %s ")
            param.append(product_sortweight)
            setted = True
        if product_traveltype is not None:
            sql += (", product_traveltype = %s " if setted else " product_traveltype = %s ")
            param.append(product_traveltype)
            setted = True
        if product_travelstartplace is not None:
            sql += (", product_travelstartplace = %s " if setted else " product_travelstartplace = %s ")
            param.append(product_travelstartplace)
            setted = True
        if product_travelendplace is not None:
            sql += (", product_travelendplace = %s " if setted else " product_travelendplace = %s ")
            param.append(product_travelendplace)
            setted = True
        if product_traveldays is not None:
            sql += (", product_traveldays = %s " if setted else " product_traveldays = %s ")
            param.append(product_traveldays)
            setted = True
        if product_eventbegintime is not None:
            sql += (", product_eventbegintime = %s " if setted else " product_eventbegintime = %s ")
            param.append(product_eventbegintime)
            setted = True
        if product_eventendtime is not None:
            sql += (", product_eventendtime = %s " if setted else " product_eventendtime = %s ")
            param.append(product_eventendtime)
            setted = True
        if product_couponwhenorder is not None:
            sql += (", product_couponwhenorder = %s " if setted else " product_couponwhenorder = %s ")
            param.append(product_couponwhenorder)
            setted = True
        if product_couponwhenactivate is not None:
            sql += (", product_couponwhenactivate = %s " if setted else " product_couponwhenactivate = %s ")
            param.append(product_couponwhenactivate)
            setted = True
        if product_couponrestriction is not None:
            sql += (", product_couponrestriction = %s " if setted else " product_couponrestriction = %s ")
            param.append(product_couponrestriction)
            setted = True
        if deleteflag is not None:
            sql += (", deleteflag = %s " if setted else " deleteflag = %s ")
            param.append(deleteflag)
            setted = True
        if product_inputuserid is not None:
            sql += (", product_inputuserid = %s " if setted else " product_inputuserid = %s ")
            param.append(product_inputuserid)
            setted = True
        if product_inputtime is not None:
            sql += (", product_inputtime = %s " if setted else " product_inputtime = %s ")
            param.append(product_inputtime)
            setted = True

        if product_purchaselimit is not None:
            if product_purchaselimit != '':
                sql += (", product_purchaselimit = %s " if setted else " product_purchaselimit = %s ")
                param.append(product_purchaselimit)
                setted = True
            else:
                sql += (", product_purchaselimit = null " if setted else " product_purchaselimit = null ")
                setted = True
                
        if product_parentitem is not None:
            sql += (", product_parentitem = %s " if setted else " product_parentitem = %s ")
            param.append(product_parentitem)
            setted = True

        if setted:
            sql += " WHERE product_id = %s"
            param.append(product_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()

            if product_type != 9:  # Ignore external products.
                self.UpdateRssFeed(product_type)

            return True
        else:
            return False

    #####################################################################################################################################

    def UpdateRssFeed(self, product_type):
        pass
        # # 更新 RSS Feed Begin ------>>>
        # productdesdict = { "1" : "体育培训", "2" : "体育旅游", "3" : "课程体验", "4" : "精彩活动", "5" : "积分商城", "6" : "私人教练", "7" : "热门专题" }
        # producturldict = { "1" : "training", "2" : "tourism", "3" : "freetrial", "4" : "activities", "5" : "mall", "6" : "privatecoach", "7" : "topics" }
        # category = productdesdict[str(product_type)]
        # if int(product_type) == 7:
        #     allproducts = self.QueryArticles(startpos=0, count=settings.RSS_FEED_COUNT, frontend=1)
        # else:
        #     allproducts = self.QueryProducts(startpos=0, count=settings.RSS_FEED_COUNT, producttype=product_type, frontend=1)
        # rss = PyRSS2Gen.RSS2(
        #     title = self.getUnicodeStr(u"一起动 - %s" % category),
        #     link = "http://www.17dong.com.cn/%s" % producturldict[str(product_type)],
        #     description = self.getUnicodeStr(u"一起动 \"%s\" 的最新产品" % category),
        #     lastBuildDate = datetime.datetime.now(),
        #     generator = None,
        #     docs = None,

        #     items = [
        #         PyRSS2Gen.RSSItem(
        #             title = self.getUnicodeStr(productinfo[2] if not self.IsDbUseDictCursor() else productinfo["product_name"]),  # 标题的下标都为 2
        #             link = "http://www.17dong.com.cn/topics/%s" % (productinfo[0] if not self.IsDbUseDictCursor() else productinfo["product_id"]) if int(product_type) == 7 else "http://www.17dong.com.cn/product/%s" % (productinfo[0] if not self.IsDbUseDictCursor() else productinfo["product_id"]),
        #             description = self.getUnicodeStr((productinfo[3] if not self.IsDbUseDictCursor() else productinfo["product_availabletime"]) if int(product_type) == 7 else (productinfo[12] if not self.IsDbUseDictCursor() else productinfo["product_description"])),
        #             guid = PyRSS2Gen.Guid("http://www.17dong.com.cn/topics/%s" % (productinfo[0] if not self.IsDbUseDictCursor() else productinfo["product_id"]) if int(product_type) == 7 else "http://www.17dong.com.cn/product/%s" % (productinfo[0] if not self.IsDbUseDictCursor() else productinfo["product_id"])),
        #             pubDate = strftime("%Y-%m-%d %H:%M:%S")
        #         )
        #         for productinfo in allproducts
        #     ]
        # )
        # filedir = abspath
        # rssfile = "%s/rss/%s.xml" % (filedir, producturldict[str(product_type)])
        # rss.write_xml(open(rssfile, "w"))
        # # 更新 RSS Feed End <<<-----

    def DeleteProduct(self, productid):
        cursor = self.db.cursor()
        sql = "UPDATE product_table SET deleteflag = 1 WHERE product_id = %s" % productid # "DELETE FROM product_table WHERE product_id = %s"
        cursor.execute(sql)

        self.db.commit()
        cursor.close()

        self.DeletePreorderByProductId(productid)
        self.DeleteCommentByProductId(productid)
        self.DeleteProductScenes(productid)
        self.DeleteSubjectObjectByObjectId(subject_object_type=1, subject_object_objectid=productid)

    #####################################################################################################################################

    def AddPreorder(self, preorderinfo, entity_type='product'):
        preorder_userid = preorderinfo["preorder_userid"]
        preorder_productid = preorderinfo["preorder_productid"]
        preorder_prepaid = preorderinfo["preorder_prepaid"]
        preorder_counts = preorderinfo["preorder_counts"]
        preorder_fullprice = preorderinfo["preorder_fullprice"]
        preorder_sceneid = preorderinfo["preorder_sceneid"]

        if entity_type == 'product':
            productinfo = self.QueryProductInfo(preorder_productid)
            preorder_vendorid = productinfo[1] if not self.IsDbUseDictCursor() else productinfo["product_vendorid"]
        else:
            preorder_vendorid = 0
        preorder_paymentstatus = preorderinfo["preorder_paymentstatus"] if preorderinfo.has_key("preorder_paymentstatus") else 0
        preorder_joinstatus = 0

        preorder_outrefundno = preorderinfo.pop('preorder_outrefundno', None)
        preorder_outrefundfee = preorderinfo.pop('preorder_outrefundfee', None)
        preorder_tradeno = preorderinfo.pop('preorder_tradeno', None)

        preorder_paytime = preorderinfo["preorder_paytime"] if preorderinfo.has_key("preorder_paytime") else None
        preorder_settletime = preorderinfo["preorder_settletime"] if preorderinfo.has_key("preorder_settletime") else None
        preorder_decuctamount = preorderinfo["preorder_decuctamount"] if preorderinfo.has_key("preorder_decuctamount") else None
        preorder_refundstatus = preorderinfo["preorder_refundstatus"] if preorderinfo.has_key("preorder_refundstatus") else 0
        preorder_appraisal = preorderinfo["preorder_appraisal"] if preorderinfo.has_key("preorder_appraisal") else None
        preorder_paymentcode = preorderinfo["preorder_paymentcode"] if preorderinfo.has_key("preorder_paymentcode") else None
        preorder_usedpoints = preorderinfo["preorder_usedpoints"] if preorderinfo.has_key("preorder_usedpoints") else None
        preorder_deliveryaddressid = preorderinfo["preorder_deliveryaddressid"] if preorderinfo.has_key("preorder_deliveryaddressid") else 0
        preorder_deliverystatus = preorderinfo["preorder_deliverystatus"] if preorderinfo.has_key("preorder_deliverystatus") else None
        preorder_buytime = strftime("%Y-%m-%d %H:%M:%S")

        preorder_paymentcode_createtime = preorderinfo["preorder_paymentcode_createtime"] if preorderinfo.has_key("preorder_paymentcode_createtime") else None
        preorder_paymentcode_usetime = preorderinfo["preorder_paymentcode_usetime"] if preorderinfo.has_key("preorder_paymentcode_usetime") else None
        preorder_paymentcode_status = preorderinfo["preorder_paymentcode_status"] if preorderinfo.has_key("preorder_paymentcode_status") else None
        preorder_contacts = preorderinfo["preorder_contacts"] if preorderinfo.has_key("preorder_contacts") else None
        preorder_contactsphonenumber = preorderinfo["preorder_contactsphonenumber"] if preorderinfo.has_key("preorder_contactsphonenumber") else None
        preorder_travellerids = preorderinfo["preorder_travellerids"] if preorderinfo.has_key("preorder_travellerids") else None
        preorder_invoicetype = preorderinfo["preorder_invoicetype"] if preorderinfo.has_key("preorder_invoicetype") else None
        preorder_invoiceheader = preorderinfo["preorder_invoiceheader"] if preorderinfo.has_key("preorder_invoiceheader") else None
        preorder_coupondiscount = preorderinfo["preorder_coupondiscount"] if preorderinfo.has_key("preorder_coupondiscount") else None
        preorder_paymentmethod = preorderinfo["preorder_paymentmethod"] if preorderinfo.has_key("preorder_paymentmethod") else None
        preorder_remarks = preorderinfo["preorder_remarks"] if preorderinfo.has_key("preorder_remarks") else None
        preorder_outtradeno = preorderinfo["preorder_outtradeno"] if preorderinfo.has_key("preorder_outtradeno") else None
        preorder_invoicedeliveryaddress = preorderinfo["preorder_invoicedeliveryaddress"] if preorderinfo.has_key("preorder_invoicedeliveryaddress") else None
        deleteflag = 0
        preorder_notes = preorderinfo["preorder_notes"] if preorderinfo.has_key("preorder_notes") else None
        preorder_rewardpoints = preorderinfo["preorder_rewardpoints"] if preorderinfo.has_key("preorder_rewardpoints") else 0

        cursor = self.db.cursor()
        value = [None, preorder_userid, preorder_productid, preorder_vendorid, preorder_paytime, preorder_settletime, preorder_prepaid, preorder_counts, 
            preorder_decuctamount, preorder_fullprice, preorder_sceneid, preorder_paymentstatus, preorder_joinstatus, preorder_refundstatus, 
            preorder_appraisal, preorder_paymentcode, preorder_usedpoints, preorder_deliveryaddressid, preorder_deliverystatus, preorder_buytime, 
            preorder_paymentcode_createtime, preorder_paymentcode_usetime, preorder_paymentcode_status, preorder_contacts, preorder_contactsphonenumber, 
            preorder_travellerids, preorder_invoicetype, preorder_invoiceheader, preorder_coupondiscount, preorder_paymentmethod, preorder_remarks, preorder_outtradeno,
            preorder_invoicedeliveryaddress, deleteflag, preorder_notes, preorder_outrefundno, preorder_outrefundfee, preorder_tradeno, preorder_rewardpoints]
        cursor.execute("INSERT INTO preorder_table (preorder_id, preorder_userid, preorder_productid, preorder_vendorid, preorder_paytime, \
            preorder_settletime, preorder_prepaid, preorder_counts, preorder_decuctamount, preorder_fullprice, preorder_sceneid, preorder_paymentstatus, \
            preorder_joinstatus, preorder_refundstatus, preorder_appraisal, preorder_paymentcode, preorder_usedpoints, preorder_deliveryaddressid, \
            preorder_deliverystatus, preorder_buytime, preorder_paymentcode_createtime, preorder_paymentcode_usetime, preorder_paymentcode_status, \
            preorder_contacts, preorder_contactsphonenumber, preorder_travellerids, preorder_invoicetype, preorder_invoiceheader, preorder_coupondiscount, \
            preorder_paymentmethod, preorder_remarks, preorder_outtradeno, preorder_invoicedeliveryaddress, deleteflag, preorder_notes, preorder_outrefundno, \
            preorder_outrefundfee, preorder_tradeno, preorder_rewardpoints) \
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, \
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        preorderid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return preorderid

    def GetPaymentMethodObject(self, preorderid):
        orderinfo = self.QueryPreorderInfo(preorderid)
        if not self.IsDbUseDictCursor():
            preorder_paymentmethod = orderinfo[29] if orderinfo[29] is not None else "{}"

            if orderinfo is not None:
                if orderinfo[29] is not None:
                    if orderinfo[29].startswith('{'):
                        try:
                            return json.loads(orderinfo[29])
                        except (TypeError, ValueError):
                            pass
                    else:
                        return { "S" : orderinfo[29], "P" : 0 }
            return { "S" : 0, "P" : 0 }
        else:
            preorder_paymentmethod = orderinfo["preorder_paymentmethod"] if orderinfo["preorder_paymentmethod"] is not None else "{}"

            if orderinfo is not None:
                if orderinfo["preorder_paymentmethod"] is not None:
                    if orderinfo["preorder_paymentmethod"].startswith('{'):
                        try:
                            return json.loads(orderinfo["preorder_paymentmethod"])
                        except (TypeError, ValueError):
                            pass
                    else:
                        return { "S" : orderinfo["preorder_paymentmethod"], "P" : 0 }
            return { "S" : 0, "P" : 0 }

    #####################################################################################################################################

    def QueryAllPreorderCount(self, productvendorid=0):
        cursor = self.db.cursor()
        if productvendorid == 0:
            sql = "SELECT COUNT(*) AS COUNT FROM preorder_table WHERE deleteflag = 0"
        else:
            sql = "SELECT COUNT(*) AS COUNT FROM preorder_table WHERE deleteflag = 0 AND preorder_vendorid = %s" % productvendorid
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryPreorders(self, startpos, count=settings.LIST_ITEM_PER_PAGE, productvendorid=0, userid=0, producttype=0, paymentstatus=-1, pricelow=None, pricehigh=None, startdate=None, enddate=None, refundstatus=-1, outrefundno=None):
        '''查询订单
            startpos: 查询起始位置
            count: 查询数量
            productvendorid: 查询某个供应商的订单
            userid: 查询某个用户的订单
            producttype: 查询某种商品类型的订单
            pricelow, pricehigh: 查询某个价格区间的订单
            startdate, enddate: 查询某个时间区间内成交的订单
        '''
        cursor = self.db.cursor()
        sql = "SELECT * FROM preorder_table WHERE deleteflag = 0 "
        if int(productvendorid) != 0:
            sql += " AND preorder_vendorid = %s " % productvendorid
        if int(userid) != 0:
            sql += " AND preorder_userid = %s " % userid
        if int(producttype) != 0:
            sql += " AND preorder_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_type = %s ) " % producttype
        else:
            sql += " AND preorder_productid IN ( SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_type != 5 ) "
        if int(paymentstatus) != -1:
            sql += " AND preorder_paymentstatus = %s " % paymentstatus
        if int(refundstatus) != -1:
            sql += " AND preorder_refundstatus = %s " % refundstatus
        if pricelow is not None and pricehigh is not None:
            if float(pricelow) == float(pricehigh):
                sql += " AND preorder_fullprice = %s " % float(pricehigh)
            else:
                sql += " AND preorder_fullprice < %s AND preorder_fullprice > %s " % (float(pricehigh), float(pricelow))
        if startdate is not None and enddate is not None:
            sql += " AND preorder_paytime < '%s' AND preorder_paytime > '%s'" % (str(enddate), str(startdate))
        if outrefundno is not None:
            sql += ' AND preorder_outrefundno = "%s"' % outrefundno
        sql += " ORDER BY preorder_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        # logging.debug("----- QueryPreorders: %r" % sql)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result
    def IsOutRefundNoExist(self, outrefundno):
        cursor = self.db.cursor()
        sql    = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_outrefundno = '%s' LIMIT 1" % outrefundno
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return True if result else False
        
    def IsOutTradeNOExist(self, outtradeno):
        cursor = self.db.cursor()
        sql    = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_outtradeno = '%s' LIMIT 1" % outtradeno
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return True if result else False

    def FuzzyQueryPreorders(self, orderkey, startpos, count=settings.LIST_ITEM_PER_PAGE, productvendorid=0):
        cursor = self.db.cursor()
        if count == 0:
            if productvendorid == 0:
                sql = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_outtradeno LIKE '%%%s%%' ORDER BY preorder_id DESC" % orderkey
            else:
                sql = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_outtradeno LIKE '%%%s%%' AND preorder_vendorid = %s ORDER BY preorder_id DESC" % (orderkey, productvendorid)
        else:
            if productvendorid == 0:
                sql = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_outtradeno LIKE '%%%s%%' ORDER BY preorder_id DESC LIMIT %s, %s" % (orderkey, startpos, count)
            else:
                sql = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_outtradeno LIKE '%%%s%%' AND preorder_vendorid = %s ORDER BY preorder_id DESC LIMIT %s, %s" % (orderkey, productvendorid, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def FuzzyQueryPreorderCount(self, orderkey, productvendorid=0):
        return len(self.FuzzyQueryPreorders(orderkey, 0, 0, productvendorid))

    #####################################################################################################################################

    # mysql> select preorder_productid, preorder_usedpoints from preorder_table where preorder_userid = 15 and preorder_usedpoints != 0;
    # mysql> select preorder_productid, preorder_rewardpoints from preorder_table where preorder_userid = 15 and preorder_rewardpoints != 0;
    # select preorder_productid, preorder_usedpoints, preorder_rewardpoints,  preorder_paytime from preorder_table where preorder_userid = 15 and ( preorder_usedpoints != 0 or preorder_rewardpoints != 0 ) and preorder_paymentstatus = 1 order by preorder_paytime desc ;

    def QueryUserPointsHistory(self, userid, reward=1):
        '''查询用户消耗积分的历史
            userid: 用户ID
            reward: 查询积分的类型，1 - 只查奖励的积分，0 - 只查消耗的积分
        '''
        cursor = self.db.cursor()
        if reward == 1:
            sql = "select preorder_productid, preorder_paytime, preorder_rewardpoints as points from preorder_table where preorder_userid = %s and preorder_rewardpoints != 0 and preorder_paymentstatus = 1 order by preorder_paytime desc" % userid
        else:
            sql = "select preorder_productid, preorder_paytime, -preorder_usedpoints  as points from preorder_table where preorder_userid = %s and preorder_usedpoints != 0 and preorder_paymentstatus = 1 order by preorder_paytime desc" % userid
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    #####################################################################################################################################

    def QueryPreorderInfo(self, preorderid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_id = %s LIMIT 1"
        param = [preorderid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    #####################################################################################################################################

    def QueryPreorderInfoByOutTradeNo(self, out_trade_no):
        cursor = self.db.cursor()
        sql   = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_outtradeno = '%s' LIMIT 1" % out_trade_no
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return result

    def UpdatePreorderInfo(self, preorderid, preorderinfo):
        preorder_id = preorderid

        preorder_userid = preorderinfo["preorder_userid"] if preorderinfo.has_key("preorder_userid") else None
        preorder_productid = preorderinfo["preorder_productid"] if preorderinfo.has_key("preorder_productid") else None
        preorder_vendorid = preorderinfo["preorder_vendorid"] if preorderinfo.has_key("preorder_vendorid") else None
        preorder_buytime = preorderinfo["preorder_buytime"] if preorderinfo.has_key("preorder_buytime") else None
        preorder_paytime = preorderinfo["preorder_paytime"] if preorderinfo.has_key("preorder_paytime") else None
        preorder_settletime = preorderinfo["preorder_settletime"] if preorderinfo.has_key("preorder_settletime") else None
        preorder_prepaid = preorderinfo["preorder_prepaid"] if preorderinfo.has_key("preorder_prepaid") else None
        preorder_counts = preorderinfo["preorder_counts"] if preorderinfo.has_key("preorder_counts") else None
        preorder_decuctamount = preorderinfo["preorder_decuctamount"] if preorderinfo.has_key("preorder_decuctamount") else None
        preorder_fullprice = preorderinfo["preorder_fullprice"] if preorderinfo.has_key("preorder_fullprice") else None
        preorder_sceneid = preorderinfo["preorder_sceneid"] if preorderinfo.has_key("preorder_sceneid") else None
        preorder_paymentstatus = preorderinfo["preorder_paymentstatus"] if preorderinfo.has_key("preorder_paymentstatus") else None
        preorder_joinstatus = preorderinfo["preorder_joinstatus"] if preorderinfo.has_key("preorder_joinstatus") else None
        preorder_refundstatus = preorderinfo["preorder_refundstatus"] if preorderinfo.has_key("preorder_refundstatus") else None
        preorder_appraisal = preorderinfo["preorder_appraisal"] if preorderinfo.has_key("preorder_appraisal") else None
        preorder_paymentcode = preorderinfo["preorder_paymentcode"] if preorderinfo.has_key("preorder_paymentcode") else None
        preorder_usedpoints = preorderinfo["preorder_usedpoints"] if preorderinfo.has_key("preorder_usedpoints") else None
        preorder_deliveryaddressid = preorderinfo["preorder_deliveryaddressid"] if preorderinfo.has_key("preorder_deliveryaddressid") else None
        preorder_deliverystatus = preorderinfo["preorder_deliverystatus"] if preorderinfo.has_key("preorder_deliverystatus") else None

        preorder_paymentcode_createtime = preorderinfo["preorder_paymentcode_createtime"] if preorderinfo.has_key("preorder_paymentcode_createtime") else None
        preorder_paymentcode_usetime = preorderinfo["preorder_paymentcode_usetime"] if preorderinfo.has_key("preorder_paymentcode_usetime") else None
        preorder_paymentcode_status = preorderinfo["preorder_paymentcode_status"] if preorderinfo.has_key("preorder_paymentcode_status") else None
        preorder_contacts = preorderinfo["preorder_contacts"] if preorderinfo.has_key("preorder_contacts") else None
        preorder_contactsphonenumber = preorderinfo["preorder_contactsphonenumber"] if preorderinfo.has_key("preorder_contactsphonenumber") else None
        preorder_travellerids = preorderinfo["preorder_travellerids"] if preorderinfo.has_key("preorder_travellerids") else None
        preorder_invoicetype = preorderinfo["preorder_invoicetype"] if preorderinfo.has_key("preorder_invoicetype") else None
        preorder_invoiceheader = preorderinfo["preorder_invoiceheader"] if preorderinfo.has_key("preorder_invoiceheader") else None
        preorder_coupondiscount = preorderinfo["preorder_coupondiscount"] if preorderinfo.has_key("preorder_coupondiscount") else None
        preorder_paymentmethod = preorderinfo["preorder_paymentmethod"] if preorderinfo.has_key("preorder_paymentmethod") else None
        preorder_remarks = preorderinfo["preorder_remarks"] if preorderinfo.has_key("preorder_remarks") else None
        preorder_outtradeno = preorderinfo["preorder_outtradeno"] if preorderinfo.has_key("preorder_outtradeno") else None
        preorder_invoicedeliveryaddress = preorderinfo["preorder_invoicedeliveryaddress"] if preorderinfo.has_key("preorder_invoicedeliveryaddress") else None
        deleteflag = preorderinfo["deleteflag"] if preorderinfo.has_key("deleteflag") else None
        preorder_notes = preorderinfo["preorder_notes"] if preorderinfo.has_key("preorder_notes") else None
        preorder_outrefundno = preorderinfo.pop('preorder_outrefundno', None)
        preorder_tradeno = preorderinfo.pop('preorder_tradeno', None)
        preorder_rewardpoints = preorderinfo.pop('preorder_rewardpoints', None)

        cursor = self.db.cursor()
        sql     = "UPDATE preorder_table SET "
        param   = []
        setted  = False
        if preorder_userid is not None:
            sql += " preorder_userid = %s "
            param.append(preorder_userid)
            setted = True
        if preorder_productid is not None:
            sql += (", preorder_productid = %s " if setted else " preorder_productid = %s ")
            param.append(preorder_productid)
            setted = True
        if preorder_vendorid is not None:
            sql += (", preorder_vendorid = %s " if setted else " preorder_vendorid = %s ")
            param.append(preorder_vendorid)
            setted = True
        if preorder_buytime is not None:
            sql += (", preorder_buytime = %s " if setted else " preorder_buytime = %s ")
            param.append(preorder_buytime)
            setted = True
        if preorder_paytime is not None:
            sql += (", preorder_paytime = %s " if setted else " preorder_paytime = %s ")
            param.append(preorder_paytime)
            setted = True
        if preorder_settletime is not None:
            sql += (", preorder_settletime = %s " if setted else " preorder_settletime = %s ")
            param.append(preorder_settletime)
            setted = True
        if preorder_prepaid is not None:
            sql += (", preorder_prepaid = %s " if setted else " preorder_prepaid = %s ")
            param.append(preorder_prepaid)
            setted = True
        if preorder_counts is not None:
            sql += (", preorder_counts = %s " if setted else " preorder_counts = %s ")
            param.append(preorder_counts)
            setted = True
        if preorder_decuctamount is not None:
            sql += (", preorder_decuctamount = %s " if setted else " preorder_decuctamount = %s ")
            param.append(preorder_decuctamount)
            setted = True
        if preorder_fullprice is not None:
            sql += (", preorder_fullprice = %s " if setted else " preorder_fullprice = %s ")
            param.append(preorder_fullprice)
            setted = True
        if preorder_sceneid is not None:
            sql += (", preorder_sceneid = %s " if setted else " preorder_sceneid = %s ")
            param.append(preorder_sceneid)
            setted = True
        if preorder_paymentstatus is not None:
            sql += (", preorder_paymentstatus = %s " if setted else " preorder_paymentstatus = %s ")
            param.append(preorder_paymentstatus)
            setted = True
        if preorder_joinstatus is not None:
            sql += (", preorder_joinstatus = %s " if setted else " preorder_joinstatus = %s ")
            param.append(preorder_joinstatus)
            setted = True
        if preorder_refundstatus is not None:
            sql += (", preorder_refundstatus = %s " if setted else " preorder_refundstatus = %s ")
            param.append(preorder_refundstatus)
            setted = True
        if preorder_appraisal is not None:
            sql += (", preorder_appraisal = %s " if setted else " preorder_appraisal = %s ")
            param.append(preorder_appraisal)
            setted = True
        if preorder_paymentcode is not None:
            sql += (", preorder_paymentcode = %s " if setted else " preorder_paymentcode = %s ")
            param.append(preorder_paymentcode)
            setted = True
        if preorder_usedpoints is not None:
            sql += (", preorder_usedpoints = %s " if setted else " preorder_usedpoints = %s ")
            param.append(preorder_usedpoints)
            setted = True
        if preorder_deliveryaddressid is not None:
            sql += (", preorder_deliveryaddressid = %s " if setted else " preorder_deliveryaddressid = %s ")
            param.append(preorder_deliveryaddressid)
            setted = True
        if preorder_deliverystatus is not None:
            sql += (", preorder_deliverystatus = %s " if setted else " preorder_deliverystatus = %s ")
            param.append(preorder_deliverystatus)
            setted = True
        if preorder_paymentcode_createtime is not None:
            sql += (", preorder_paymentcode_createtime = %s " if setted else " preorder_paymentcode_createtime = %s ")
            param.append(preorder_paymentcode_createtime)
            setted = True
        if preorder_paymentcode_usetime is not None:
            sql += (", preorder_paymentcode_usetime = %s " if setted else " preorder_paymentcode_usetime = %s ")
            param.append(preorder_paymentcode_usetime)
            setted = True
        if preorder_paymentcode_status is not None:
            sql += (", preorder_paymentcode_status = %s " if setted else " preorder_paymentcode_status = %s ")
            param.append(preorder_paymentcode_status)
            setted = True
        if preorder_contacts is not None:
            sql += (", preorder_contacts = %s " if setted else " preorder_contacts = %s ")
            param.append(preorder_contacts)
            setted = True
        if preorder_contactsphonenumber is not None:
            sql += (", preorder_contactsphonenumber = %s " if setted else " preorder_contactsphonenumber = %s ")
            param.append(preorder_contactsphonenumber)
            setted = True
        if preorder_travellerids is not None:
            sql += (", preorder_travellerids = %s " if setted else " preorder_travellerids = %s ")
            param.append(preorder_travellerids)
            setted = True
        if preorder_invoicetype is not None:
            sql += (", preorder_invoicetype = %s " if setted else " preorder_invoicetype = %s ")
            param.append(preorder_invoicetype)
            setted = True
        if preorder_invoiceheader is not None:
            sql += (", preorder_invoiceheader = %s " if setted else " preorder_invoiceheader = %s ")
            param.append(preorder_invoiceheader)
            setted = True
        if preorder_coupondiscount is not None:
            sql += (", preorder_coupondiscount = %s " if setted else " preorder_coupondiscount = %s ")
            param.append(preorder_coupondiscount)
            setted = True
        if preorder_paymentmethod is not None:
            sql += (", preorder_paymentmethod = %s " if setted else " preorder_paymentmethod = %s ")
            param.append(preorder_paymentmethod)
            setted = True
        if preorder_remarks is not None:
            sql += (", preorder_remarks = %s " if setted else " preorder_remarks = %s ")
            param.append(preorder_remarks)
            setted = True
        if preorder_outtradeno is not None:
            sql += (", preorder_outtradeno = %s " if setted else " preorder_outtradeno = %s ")
            param.append(preorder_outtradeno)
            setted = True
        if preorder_invoicedeliveryaddress is not None:
            sql += (", preorder_invoicedeliveryaddress = %s " if setted else " preorder_invoicedeliveryaddress = %s ")
            param.append(preorder_invoicedeliveryaddress)
            setted = True
        if deleteflag is not None:
            sql += (", deleteflag = %s " if setted else " deleteflag = %s ")
            param.append(deleteflag)
            setted = True
        if preorder_notes is not None:
            sql += (", preorder_notes = %s " if setted else " preorder_notes = %s ")
            param.append(preorder_notes)
            setted = True
        if preorder_outrefundno is not None:
            sql += (", preorder_outrefundno = %s " if setted else " preorder_outrefundno = %s ")
            param.append(preorder_outrefundno)
            setted = True
        if preorder_tradeno is not None:
            sql += (", preorder_tradeno = %s " if setted else " preorder_tradeno = %s ")
            param.append(preorder_tradeno)
            setted = True
        if preorder_rewardpoints is not None:
            sql += (", preorder_rewardpoints = %s " if setted else " preorder_rewardpoints = %s ")
            param.append(preorder_rewardpoints)
            setted = True
            
        if setted:
            sql += " WHERE preorder_id = %s"
            param.append(preorder_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    #####################################################################################################################################

    def DeletePreorder(self, preorderid):
        cursor = self.db.cursor()
        sql = "UPDATE preorder_table SET deleteflag = 1 WHERE preorder_id = %s" % preorderid # "DELETE FROM preorder_table WHERE preorder_id = %s"
        cursor.execute(sql)

        self.db.commit()
        cursor.close()

    def DeletePreorderByProductId(self, productid):
        cursor = self.db.cursor()
        sql = "UPDATE preorder_table SET deleteflag = 1 WHERE preorder_productid = %s" % productid # "DELETE FROM preorder_table WHERE preorder_productid = %s" % productid
        cursor.execute(sql)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def IsUniqueStringExistsInCoupon(self, uniquestr, coupontype):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM coupon_table WHERE coupon_type = %s AND coupon_serialnumber = %s LIMIT 1"
        param = [coupontype, uniquestr]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        return True if result else False

    def getuniquestring(self):
        mystr = hashlib.md5(str(time.time())).hexdigest().upper()
        randstr = ""
        for i in range(1, 11):
            randstr += mystr[random.randint(0, len(mystr) - 1)]

        # randstr = str(time.time()).replace(".", "")[6:]
        # while len(randstr) < 6:
        #     randstr += str(random.randint(1, 9))
        # randstr += str(random.randint(1000, 9999))

        return randstr

    def getuniquestringV2(self):
        return str(random.randrange(1000000000000000, 9999999999999999))

    def getuniquestringV3(self):
        cstr = "88%s" % str(random.randrange(100000, 999999))
        return cstr

    def IsDeviceIDExistInCoupon(self, deviceid):
        '''检测某个移动设备的 deviceid 是否已经注册过
        '''
        if deviceid is None:
            return False

        cursor = self.db.cursor()

        sql   = "SELECT * FROM coupon_table WHERE coupon_giftcode_deviceid = %s LIMIT 1"
        param = [deviceid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        return True if result else False

    def AddCoupon(self, couponinfo, couponvaliddays=30):
        '''couponvaliddays - 优惠券有效期，默认从当前日期开始的 30 天以内
        '''
        coupon_userid = couponinfo["coupon_userid"]
        coupon_amount = couponinfo["coupon_amount"]
        coupon_usetime = couponinfo["coupon_usetime"] if couponinfo.has_key("coupon_usetime") else None
        coupon_restrictions = couponinfo["coupon_restrictions"] if couponinfo.has_key("coupon_restrictions") else json.dumps({ "RestrictionType" : 0 })
        coupon_type = couponinfo["coupon_type"] if couponinfo.has_key("coupon_type") else 2
        coupon_type = int(coupon_type)
        
        coupon_valid = 1
        coupon_createtime = strftime("%Y-%m-%d %H:%M:%S")
        coupon_validtime = datetime.date.today() + timedelta(days=couponvaliddays)
        coupon_source = couponinfo["coupon_source"] if couponinfo.has_key("coupon_source") else 0
        coupon_giftcode_deviceid = couponinfo["coupon_giftcode_deviceid"] if couponinfo.has_key("coupon_giftcode_deviceid") else None

        if coupon_type == 1:
            # 抵扣券，16位数字，使用时需要手动输入
            coupon_serialnumber = self.getuniquestringV2()
            while self.IsUniqueStringExistsInCoupon(uniquestr=coupon_serialnumber, coupontype=coupon_type):
                coupon_serialnumber = self.getuniquestringV2()

            cursor = self.db.cursor()
            value = [None, coupon_userid, coupon_serialnumber, coupon_valid, coupon_amount, coupon_createtime, coupon_usetime, coupon_restrictions, coupon_type, coupon_validtime, coupon_source, coupon_giftcode_deviceid]
            cursor.execute("INSERT INTO coupon_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
            couponid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return couponid

        elif coupon_type == 2:
            # 优惠券, 10位字符
            coupon_serialnumber = self.getuniquestring()
            while self.IsUniqueStringExistsInCoupon(uniquestr=coupon_serialnumber, coupontype=coupon_type):
                coupon_serialnumber = self.getuniquestring()

            cursor = self.db.cursor()
            value = [None, coupon_userid, coupon_serialnumber, coupon_valid, coupon_amount, coupon_createtime, coupon_usetime, coupon_restrictions, coupon_type, coupon_validtime, coupon_source, coupon_giftcode_deviceid]
            cursor.execute("INSERT INTO coupon_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
            couponid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return couponid

        elif coupon_type == 3:
            # 兑奖券，8位数字
            coupon_serialnumber = self.getuniquestringV3()
            while self.IsUniqueStringExistsInCoupon(uniquestr=coupon_serialnumber, coupontype=coupon_type):
                coupon_serialnumber = self.getuniquestringV3()

            cursor = self.db.cursor()
            value = [None, coupon_userid, coupon_serialnumber, coupon_valid, coupon_amount, coupon_createtime, coupon_usetime, coupon_restrictions, coupon_type, coupon_validtime, coupon_source, coupon_giftcode_deviceid]
            cursor.execute("INSERT INTO coupon_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
            couponid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return couponid

        else:
            return 0

    #####################################################################################################################################

    def QueryAllCouponCount(self):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM coupon_table"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def QueryCoupons(self, startpos, count=settings.LIST_ITEM_PER_PAGE, userid=0, couponvalid=-1, couponexpired=-1, couponsource=-1):
        ''' couponvalid         - 优惠券是否有效
            couponexpired       - 优惠券是否过期
            couponsource        - 优惠券来源
                有效优惠券： QueryCoupons(0, count=0, userid=current_userid, couponvalid=1, couponexpired=0)
                无效优惠券： QueryCoupons(0, count=0, userid=current_userid, couponvalid=0, couponexpired=0)
                过期优惠券： QueryCoupons(0, count=0, userid=current_userid, couponvalid=-1, couponexpired=1)
            couponrestrictions  - 优惠券适用范围（字典类型，详细定义见字段表）
        '''
        # select count(*) from coupon_table where coupon_validtime = '2015-12-31 00:00:00';
        cursor = self.db.cursor()
        sql = "SELECT * FROM coupon_table "

        setted = False
        if userid != 0:
            sql += " WHERE coupon_userid = %s " % userid
            setted = True
        if couponvalid != -1:
            sql += " WHERE coupon_valid = %s " % couponvalid if setted == False else " AND coupon_valid = %s " % couponvalid
        if couponexpired != -1:
            if couponexpired == 0:
                sql += " WHERE coupon_validtime > NOW() " if setted == False else " AND coupon_validtime > NOW() "
            else:
                sql += " WHERE coupon_validtime < NOW() " if setted == False else " AND coupon_validtime < NOW() "
        if couponsource != -1:
            sql += " WHERE coupon_source = %s " % couponsource if setted == False else " AND coupon_source = %s " % couponsource

        # 不显示 5 万张 88 元的抵扣券
        sql += " WHERE NOT (coupon_validtime = '2015-12-31 00:00:00' AND coupon_amount = 88)" if setted == False else " AND NOT (coupon_validtime = '2015-12-31 00:00:00' AND coupon_amount = 88) "

        sql += " ORDER BY coupon_id DESC "

        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()

        if self.IsDbUseDictCursor():
            now = datetime.datetime.now()
            for couponinfo in result:
                if couponinfo["coupon_validtime"] > now:
                    couponinfo["coupon_status"] = 1
                else:
                    couponinfo["coupon_status"] = 0
            cursor.close()
            return result
        else:
            cursor.close()
            return result

    def ValidateProductCoupon(self, productid, couponid):
        ''' 检测某个优惠券是否适用于某个商品
              适用     - True
              不适用   - False
        '''
        productinfo = self.QueryProductInfo(productid)
        couponinfo  = self.QueryCouponInfo(couponid)

        if couponinfo is None or productinfo is None:
            return False
            
        if not self.IsDbUseDictCursor():
            restrictiondict = json.loads(couponinfo[7] if couponinfo[7] is not None else '''{ "RestrictionType" : 0 }''')
        else:
            try:
                restrictiondict = json.loads(couponinfo["coupon_restrictions"] if couponinfo["coupon_restrictions"] is not None else '''{ "RestrictionType" : 0 }''')
            except Exception, e:
                return False
        
        if not isinstance(restrictiondict, dict):
            restrictiondict = { "RestrictionType" : 0 }

        restricttype = int(restrictiondict["RestrictionType"] if restrictiondict.has_key("RestrictionType") else "0")
        if restricttype == 0:       # 不限
            return True
        elif restricttype == 1:     # 限制商品类型
            ProductType = restrictiondict["ProductType"] if restrictiondict.has_key("ProductType") else "(0)"
            ProductTypeList = ProductType # json.loads(ProductType)

            # logging.debug("restricttype: %r, ProductTypeList: %r" % (restricttype, ProductTypeList))

            if not self.IsDbUseDictCursor():
                return productinfo[4] in ProductTypeList
            else:
                try:
                    return productinfo["product_type"] in ProductTypeList
                except Exception, e:
                    return int(productinfo["product_type"]) == int(ProductTypeList)
        elif restricttype == 2:     # 限制商品项目
            ProductType = restrictiondict["ProductType"] if restrictiondict.has_key("ProductType") else "0"
            ProductItem = restrictiondict["ProductItem"] if restrictiondict.has_key("ProductItem") else "()"
            ProductItemList = ProductItem # json.loads(ProductItem)

            producttypevalid = False
            if type(ProductType) == tuple or type(ProductType) == list:
                producttypevalid = True if int(productinfo["product_type"]) in ProductType else False
            else:
                producttypevalid = True if int(productinfo["product_type"]) == int(ProductType) else False

            # logging.debug("restricttype: %r, ProductItemList: %r" % (restricttype, ProductItemList))
            
            if not self.IsDbUseDictCursor():
                return (int(productinfo[4]) == int(ProductType) and productinfo[8] in ProductItemList)
            else:
                return (producttypevalid == True and productinfo["product_item"] in ProductItemList)
        elif restricttype == 3:     # 限制商品供应商
            ProductVendorID = restrictiondict["ProductVendorID"] if restrictiondict.has_key("ProductVendorID") else "(0)"
            ProductVendorIDList = ProductVendorID # json.loads(ProductVendorID)

            # logging.debug("restricttype: %r, ProductVendorIDList: %r" % (restricttype, ProductVendorIDList))
            
            if not self.IsDbUseDictCursor():
                return productinfo[1] in ProductVendorIDList
            else:
                return productinfo["product_vendorid"] in ProductVendorIDList
        elif restricttype == 4:     # 限制商品ID
            ProductID = restrictiondict["ProductID"] if restrictiondict.has_key("ProductID") else (0)

            # logging.debug("ProductID: %r" % ProductID)

            ProductIDList = ProductID # json.loads(ProductID)

            # logging.debug("restricttype: %r, ProductIDList: %r" % (restricttype, ProductIDList))
            
            if not self.IsDbUseDictCursor():
                return productinfo[0] in ProductIDList
            else:
                return productinfo["product_id"] in ProductIDList
        else:
            return False

    def IsUserGetSpecificCoupon(self, userid, productid=None, activityid=None):
        ''' 查询用户是否领取某种类型的优惠券
              productid     - 商品ID
              activityid    - 活动ID
            productid 和 activityid 只能二选一，不可同时为 None，也不可同时有值
            返回值： True - 已领取， False - 未领取
        '''

        couponsource = None
        if productid is not None:
            couponsource = "1%s" % productid
        if activityid is not None:
            couponsource = "2%s" % activityid
        if couponsource is not None:
            cursor = self.db.cursor()
            sql   = "SELECT * FROM coupon_table WHERE coupon_userid = %s AND coupon_source = %s LIMIT 1"
            param = [userid, couponsource]
            cursor.execute(sql, param)
            result = cursor.fetchone()
            cursor.close()
            return True if result else False
        else:
            return False

    def GetCouponRestrictionDescription(self, couponid):
        ''' 获取优惠券适用范围的描述信息
        '''
        couponinfo = self.QueryCouponInfo(couponid)

        if not self.IsDbUseDictCursor():
            coupon_restrictions = couponinfo[7] if couponinfo[7] is not None else json.dumps({ "RestrictionType" : 0 })
        else:
            coupon_restrictions = couponinfo["coupon_restrictions"] if couponinfo["coupon_restrictions"] is not None else json.dumps({ "RestrictionType" : 0 })

        # logging.debug("couponid: %r, restriction: %r" % (couponid, coupon_restrictions))

        restrictiondict = json.loads(coupon_restrictions)
        
        if not isinstance(restrictiondict, dict):
            restrictiondict = { "RestrictionType" : 0 }

        restricttype = int(restrictiondict["RestrictionType"] if restrictiondict.has_key("RestrictionType") else 0)
        if restricttype == 0:
            return "不限"
        elif restricttype == 1:
            return "限定商品类型"
        elif restricttype == 2:
            return "限定商品项目"
        elif restricttype == 3:
            return "限定商品供应商"
        elif restricttype == 4:
            return "限定指定商品"

    def FuzzyQueryCoupon(self, couponkey, startpos, count=settings.LIST_ITEM_PER_PAGE, couponsource=-1):
        cursor = self.db.cursor()
        couponkey = couponkey.replace("'", "''") if couponkey else couponkey
        sql = "SELECT * FROM coupon_table WHERE (coupon_serialnumber LIKE '%%%s%%' OR coupon_id = '%s') " % (couponkey, couponkey)
        if couponsource != -1:
            sql += " AND coupon_source = %s " % couponsource
        sql += " ORDER BY coupon_id DESC"
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def FuzzyQueryCouponCount(self, couponkey, couponsource=-1):
        return len(self.FuzzyQueryCoupon(couponkey, startpos=0, count=0, couponsource=couponsource))

    #####################################################################################################################################

    def QueryCouponInfo(self, couponid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM coupon_table WHERE coupon_id = %s LIMIT 1"
        param = [couponid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryCouponInfoByCNO(self, cno):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM coupon_table WHERE coupon_serialnumber = '%s' LIMIT 1" % cno
        cursor.execute(sql)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryCouponInfoByDeviceID(self, deviceid):
        if deviceid is None:
            return None

        cursor = self.db.cursor()

        sql   = "SELECT * FROM coupon_table WHERE coupon_type = 3 AND coupon_giftcode_deviceid = '%s' LIMIT 1" % deviceid
        cursor.execute(sql)

        result = cursor.fetchone()
        cursor.close()
        return result

    #####################################################################################################################################

    def UpdateCouponInfo(self, couponid, couponinfo):
        coupon_id = couponid

        coupon_userid = couponinfo["coupon_userid"] if couponinfo.has_key("coupon_userid") else None
        coupon_serialnumber = couponinfo["coupon_serialnumber"] if couponinfo.has_key("coupon_serialnumber") else None
        coupon_valid = couponinfo["coupon_valid"] if couponinfo.has_key("coupon_valid") else None
        coupon_amount = couponinfo["coupon_amount"] if couponinfo.has_key("coupon_amount") else None
        coupon_createtime = couponinfo["coupon_createtime"] if couponinfo.has_key("coupon_createtime") else None
        coupon_usetime = couponinfo["coupon_usetime"] if couponinfo.has_key("coupon_usetime") else None
        coupon_restrictions = couponinfo["coupon_restrictions"] if couponinfo.has_key("coupon_restrictions") else None
        coupon_type = couponinfo["coupon_type"] if couponinfo.has_key("coupon_type") else None
        coupon_validtime = couponinfo["coupon_validtime"] if couponinfo.has_key("coupon_validtime") else None
        coupon_source = couponinfo["coupon_source"] if couponinfo.has_key("coupon_source") else 0 # 优惠券来源默认是 "注册赠送"
        coupon_giftcode_deviceid = couponinfo["coupon_giftcode_deviceid"] if couponinfo.has_key("coupon_giftcode_deviceid") else None

        cursor = self.db.cursor()

        sql     = "UPDATE coupon_table SET "
        param   = []
        setted  = False
        if coupon_userid is not None:
            sql += " coupon_userid = %s "
            param.append(coupon_userid)
            setted = True
        if coupon_serialnumber is not None:
            sql += (", coupon_serialnumber = %s " if setted else " coupon_serialnumber = %s ")
            param.append(coupon_serialnumber)
            setted = True
        if coupon_valid is not None:
            sql += (", coupon_valid = %s " if setted else " coupon_valid = %s ")
            param.append(coupon_valid)
            setted = True
        if coupon_amount is not None:
            sql += (", coupon_amount = %s " if setted else " coupon_amount = %s ")
            param.append(coupon_amount)
            setted = True
        if coupon_createtime is not None:
            sql += (", coupon_createtime = %s " if setted else " coupon_createtime = %s ")
            param.append(coupon_createtime)
            setted = True
        if coupon_usetime is not None:
            sql += (", coupon_usetime = %s " if setted else " coupon_usetime = %s ")
            param.append(coupon_usetime)
            setted = True
        if coupon_restrictions is not None:
            sql += (", coupon_restrictions = %s " if setted else " coupon_restrictions = %s ")
            param.append(coupon_restrictions)
            setted = True
        if coupon_type is not None:
            sql += (", coupon_type = %s " if setted else " coupon_type = %s ")
            param.append(coupon_type)
            setted = True
        if coupon_validtime is not None:
            sql += (", coupon_validtime = %s " if setted else " coupon_validtime = %s ")
            param.append(coupon_validtime)
            setted = True
        if coupon_source is not None:
            sql += (", coupon_source = %s " if setted else " coupon_source = %s ")
            param.append(coupon_source)
            setted = True
        if coupon_giftcode_deviceid is not None:
            sql += (", coupon_giftcode_deviceid = %s " if setted else " coupon_giftcode_deviceid = %s ")
            param.append(coupon_giftcode_deviceid)
            setted = True
        
        if setted:
            sql += " WHERE coupon_id = %s"
            param.append(coupon_id)

            cursor.execute(sql, param)

            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    #####################################################################################################################################

    def DeleteCoupon(self, couponid):
        cursor = self.db.cursor()
        sql = "DELETE FROM coupon_table WHERE coupon_id = %s"
        param = [couponid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def QueryAllAppDownloadCount(self, startdate, enddate):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM coupon_table WHERE coupon_type = 3 "
        if startdate == enddate:
            sql += " AND coupon_createtime = '%s' " % startdate
        else:
            sql += " AND coupon_createtime > '%s' AND coupon_createtime < '%s'" % (startdate, enddate)
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def AddComplaint(self, complaintinfo):
        complaints_userid = complaintinfo["complaints_userid"]
        complaints_reason = complaintinfo["complaints_reason"]
        complaints_description = complaintinfo["complaints_description"]
        complaints_time = strftime("%Y-%m-%d %H:%M:%S")
        complaints_state = 0
        complaints_orderid = complaintinfo["complaints_orderid"] if complaintinfo.has_key("complaints_orderid") else None
        complaints_remarks = complaintinfo["complaints_remarks"] if complaintinfo.has_key("complaints_remarks") else None

        cursor = self.db.cursor()
        value = [None, complaints_userid, complaints_orderid, complaints_reason, complaints_description, complaints_time, complaints_state, complaints_remarks]
        cursor.execute("INSERT INTO complaints_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", value)
        lastid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return lastid

    def QueryAllComplaintCount(self):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM complaints_table"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0
        
    def QueryComplaints(self, startpos, count=settings.LIST_ITEM_PER_PAGE):
        cursor = self.db.cursor()
        sql = "SELECT * FROM complaints_table ORDER BY complaints_id DESC" if count == 0 else "SELECT * FROM complaints_table ORDER BY complaints_id DESC LIMIT %s, %s" % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result
        
    def QueryComplaintInfo(self, complaintsid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM complaints_table WHERE complaints_id = %s LIMIT 1"
        param = [complaintsid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result
        
    def UpdateComplaintInfo(self, complaintsid, complaintinfo):
        complaints_id = complaintsid

        complaints_reason = complaintinfo["complaints_reason"] if complaintinfo.has_key("complaints_reason") else None
        complaints_description = complaintinfo["complaints_description"] if complaintinfo.has_key("complaints_description") else None
        complaints_state = complaintinfo["complaints_state"] if complaintinfo.has_key("complaints_state") else None
        complaints_orderid = complaintinfo["complaints_orderid"] if complaintinfo.has_key("complaints_orderid") else None
        complaints_remarks = complaintinfo["complaints_remarks"] if complaintinfo.has_key("complaints_remarks") else None

        cursor = self.db.cursor()

        sql     = "UPDATE complaints_table SET "
        param   = []
        setted  = False
        if complaints_reason is not None:
            sql += " complaints_reason = %s "
            param.append(complaints_reason)
            setted = True
        if complaints_description is not None:
            sql += (", complaints_description = %s " if setted else " complaints_description = %s ")
            param.append(complaints_description)
            setted = True
        if complaints_state is not None:
            sql += (", complaints_state = %s " if setted else " complaints_state = %s ")
            param.append(complaints_state)
            setted = True
        if complaints_orderid is not None:
            sql += (", complaints_orderid = %s " if setted else " complaints_orderid = %s ")
            param.append(complaints_orderid)
            setted = True
        if complaints_remarks is not None:
            sql += (", complaints_remarks = %s " if setted else " complaints_remarks = %s ")
            param.append(complaints_remarks)
            setted = True
        
        if setted:
            sql += " WHERE complaints_id = %s"
            param.append(complaints_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False
        
    def DeleteComplaint(self, complaintsid):
        cursor = self.db.cursor()
        sql = "DELETE FROM complaints_table WHERE complaints_id = %s"
        param = [complaintsid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()
    
    #####################################################################################################################################

    def AddArticle(self, articleinfo):
        articles_title = articleinfo["articles_title"]
        articles_auditstate = articleinfo["articles_auditstate"] if articleinfo.has_key("articles_auditstate") else 0
        articles_content = articleinfo["articles_content"] if articleinfo.has_key("articles_content") else None
        articles_publisher = articleinfo["articles_publisher"] if articleinfo.has_key("articles_publisher") else None
        articles_category = articleinfo["articles_category"] if articleinfo.has_key("articles_category") else None
        articles_avatar = articleinfo["articles_avatar"] if articleinfo.has_key("articles_avatar") else None
        articles_externalurl = articleinfo["articles_externalurl"] if articleinfo.has_key("articles_externalurl") else None
        articles_externalproductid = articleinfo["articles_externalproductid"] if articleinfo.has_key("articles_externalproductid") else None
        articles_sortweight = articleinfo["articles_sortweight"] if articleinfo.has_key("articles_sortweight") else None
        articles_publishtime = articleinfo["articles_publishtime"] if articleinfo.has_key("articles_publishtime") else strftime("%Y-%m-%d") # %H:%M:%S

        cursor = self.db.cursor()
        value = [None, articles_auditstate, articles_title, articles_content, articles_publisher, articles_category, articles_avatar, 
            articles_externalurl, articles_externalproductid, articles_publishtime, articles_sortweight]
        cursor.execute("INSERT INTO articles_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        lastid = cursor.lastrowid
        self.db.commit()
        cursor.close()

        self.UpdateRssFeed(product_type=7)

        return lastid
        
    def QueryAllArticleCount(self):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM articles_table"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0
        
    def QueryArticles(self, startpos, count=settings.LIST_ITEM_PER_PAGE, frontend=0, articlescategory=None):
        cursor = self.db.cursor()
        if count == 0:
            if frontend == 0:
                sql = "SELECT * FROM articles_table ORDER BY articles_id DESC"
            else:
                # 查询一起动前端热门专题
                if articlescategory is None:
                    sql = "SELECT * FROM articles_table WHERE articles_auditstate = 1 AND articles_category != '系统文章' AND articles_category != '校园足球联盟' ORDER BY articles_id DESC"
                # 查询前端某个分类的文章
                else:
                    sql = "SELECT * FROM articles_table WHERE articles_auditstate = 1 AND articles_category = '%s' ORDER BY articles_id DESC" % articlescategory
        else:
            if frontend == 0:
                sql = "SELECT * FROM articles_table ORDER BY articles_id DESC LIMIT %s, %s" % (startpos, count)
            else:
                # 分页查询一起动前端热门专题
                if articlescategory is None:
                    sql = "SELECT * FROM articles_table WHERE articles_auditstate = 1 AND articles_category != '系统文章' AND articles_category != '校园足球联盟' ORDER BY articles_id DESC LIMIT %s, %s" % (startpos, count)
                # 分页查询前端某个分类的文章
                else:
                    sql = "SELECT * FROM articles_table WHERE articles_auditstate = 1 AND articles_category = '%s' ORDER BY articles_id DESC LIMIT %s, %s" % (articlescategory, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result
        
    def QueryArticleInfo(self, articlesid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM articles_table WHERE articles_id = %s LIMIT 1"
        param = [articlesid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result
        
    def UpdateArticleInfo(self, articlesid, articleinfo):
        articles_id = articlesid

        articles_auditstate = articleinfo["articles_auditstate"] if articleinfo.has_key("articles_auditstate") else None
        articles_title = articleinfo["articles_title"] if articleinfo.has_key("articles_title") else None
        articles_content = articleinfo["articles_content"] if articleinfo.has_key("articles_content") else None
        articles_publisher = articleinfo["articles_publisher"] if articleinfo.has_key("articles_publisher") else None
        articles_category = articleinfo["articles_category"] if articleinfo.has_key("articles_category") else None
        articles_avatar = articleinfo["articles_avatar"] if articleinfo.has_key("articles_avatar") else None
        articles_externalurl = articleinfo["articles_externalurl"] if articleinfo.has_key("articles_externalurl") else None
        articles_externalproductid = articleinfo["articles_externalproductid"] if articleinfo.has_key("articles_externalproductid") else None
        articles_sortweight = articleinfo["articles_sortweight"] if articleinfo.has_key("articles_sortweight") else None
        articles_publishtime = articleinfo["articles_publishtime"] if articleinfo.has_key("articles_publishtime") else strftime("%Y-%m-%d") # %H:%M:%S

        cursor = self.db.cursor()

        sql     = "UPDATE articles_table SET "
        param   = []
        setted  = False
        if articles_auditstate is not None:
            sql += " articles_auditstate = %s "
            param.append(articles_auditstate)
            setted = True
        if articles_title is not None:
            sql += (", articles_title = %s " if setted else " articles_title = %s ")
            param.append(articles_title)
            setted = True
        if articles_content is not None:
            sql += (", articles_content = %s " if setted else " articles_content = %s ")
            param.append(articles_content)
            setted = True
        if articles_publisher is not None:
            sql += (", articles_publisher = %s " if setted else " articles_publisher = %s ")
            param.append(articles_publisher)
            setted = True
        if articles_category is not None:
            sql += (", articles_category = %s " if setted else " articles_category = %s ")
            param.append(articles_category)
            setted = True
        if articles_avatar is not None:
            sql += (", articles_avatar = %s " if setted else " articles_avatar = %s ")
            param.append(articles_avatar)
            setted = True
        if articles_externalurl is not None:
            sql += (", articles_externalurl = %s " if setted else " articles_externalurl = %s ")
            param.append(articles_externalurl)
            setted = True
        if articles_externalproductid is not None:
            sql += (", articles_externalproductid = %s " if setted else " articles_externalproductid = %s ")
            param.append(articles_externalproductid)
            setted = True
        if articles_publishtime is not None:
            sql += (", articles_publishtime = %s " if setted else " articles_publishtime = %s ")
            param.append(articles_publishtime)
            setted = True
        if articles_sortweight is not None:
            sql += (", articles_sortweight = %s " if setted else " articles_sortweight = %s ")
            param.append(articles_sortweight)
            setted = True
        if setted:
            sql += " WHERE articles_id = %s"
            param.append(articles_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()

            self.UpdateRssFeed(product_type=7)

            return True
        else:
            return False
        
    def DeleteArticle(self, articlesid):
        cursor = self.db.cursor()
        sql = "DELETE FROM articles_table WHERE articles_id = %s"
        param = [articlesid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddAds(self, adsinfo):
        ads_auditstate = adsinfo["ads_auditstate"] if adsinfo.has_key("ads_auditstate") else None
        ads_state = adsinfo["ads_state"] if adsinfo.has_key("ads_state") else None
        ads_platform = adsinfo["ads_platform"] if adsinfo.has_key("ads_platform") else None
        ads_publisher = adsinfo["ads_publisher"] if adsinfo.has_key("ads_publisher") else None
        ads_position = adsinfo["ads_position"] if adsinfo.has_key("ads_position") else None
        ads_avatar = adsinfo["ads_avatar"] if adsinfo.has_key("ads_avatar") else None
        ads_externalurl = adsinfo["ads_externalurl"] if adsinfo.has_key("ads_externalurl") else None
        ads_externalproductid = adsinfo["ads_externalproductid"] if adsinfo.has_key("ads_externalproductid") else None
        ads_begintime = adsinfo["ads_begintime"] if adsinfo.has_key("ads_begintime") else None
        ads_endtime = adsinfo["ads_endtime"] if adsinfo.has_key("ads_endtime") else None
        ads_sortweight = adsinfo["ads_sortweight"] if adsinfo.has_key("ads_sortweight") else None

        cursor = self.db.cursor()
        value = [None, ads_auditstate, ads_state, ads_publisher, ads_platform, ads_position, ads_avatar, ads_externalurl, 
            ads_externalproductid, ads_begintime, ads_endtime, ads_sortweight]
        cursor.execute("INSERT INTO ads_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        lastid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return lastid

    def QueryAllAdsCount(self):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM ads_table"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def FuzzyQueryAds(self, adskey, startpos, count=settings.LIST_ITEM_PER_PAGE, showAllAds=1):
        cursor = self.db.cursor()
        adskey = adskey.replace("'", "''") if adskey else adskey
        sql = "SELECT * FROM ads_table WHERE ads_publisher LIKE '%%%s%%'" % adskey
        if showAllAds == 0:
            sql += " AND ads_auditstate = 1 AND ads_state = 1 "
        sql += " ORDER BY ads_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (adskey, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def FuzzyQueryAdsCount(self, adskey):
        cursor = self.db.cursor()
        adskey = adskey.replace("'", "''") if adskey else adskey
        sql = "SELECT COUNT(*) AS COUNT FROM ads_table WHERE ads_publisher LIKE '%%%s%%'" % adskey
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0
        
    def QueryAds(self, startpos, count=settings.LIST_ITEM_PER_PAGE, showAllAds=1):
        cursor = self.db.cursor()
        sql = "SELECT * FROM ads_table"
        if showAllAds == 0:
            sql += " WHERE ads_auditstate = 1 AND ads_state = 1 "
        sql += " ORDER BY ads_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s" % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result
        
    def QueryAdsInfo(self, adsid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM ads_table WHERE ads_id = %s LIMIT 1"
        param = [adsid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def DeleteAdsOldAvatar(self, adsid):
        '''在更新广告的avatar之前先把老的广告图片删除掉
        '''
        (adsavatar, hascustomavatar) = self.GetAdsAvatarPreview(adsid)
        if hascustomavatar:
            filedir = socket.gethostname() == settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp'
            infile   = filedir + '/' + adsavatar
            os.remove(infile)
        
    def UpdateAdsInfo(self, adsid, adsinfo):
        ads_id = adsid

        ads_auditstate = adsinfo["ads_auditstate"] if adsinfo.has_key("ads_auditstate") else None
        ads_state = adsinfo["ads_state"] if adsinfo.has_key("ads_state") else None
        ads_platform = adsinfo["ads_platform"] if adsinfo.has_key("ads_platform") else None
        ads_publisher = adsinfo["ads_publisher"] if adsinfo.has_key("ads_publisher") else None
        ads_position = adsinfo["ads_position"] if adsinfo.has_key("ads_position") else None
        ads_avatar = adsinfo["ads_avatar"] if adsinfo.has_key("ads_avatar") else None
        ads_externalurl = adsinfo["ads_externalurl"] if adsinfo.has_key("ads_externalurl") else None
        ads_externalproductid = adsinfo["ads_externalproductid"] if adsinfo.has_key("ads_externalproductid") else None
        ads_begintime = adsinfo["ads_begintime"] if adsinfo.has_key("ads_begintime") else None
        ads_endtime = adsinfo["ads_endtime"] if adsinfo.has_key("ads_endtime") else None
        ads_sortweight = adsinfo["ads_sortweight"] if adsinfo.has_key("ads_sortweight") else None

        cursor = self.db.cursor()

        sql     = "UPDATE ads_table SET "
        param   = []
        setted  = False
        if ads_auditstate is not None:
            sql += " ads_auditstate = %s "
            param.append(ads_auditstate)
            setted = True
        if ads_state is not None:
            sql += (", ads_state = %s " if setted else " ads_state = %s ")
            param.append(ads_state)
            setted = True
        if ads_platform is not None:
            sql += (", ads_platform = %s " if setted else " ads_platform = %s ")
            param.append(ads_platform)
            setted = True
        if ads_publisher is not None:
            sql += (", ads_publisher = %s " if setted else " ads_publisher = %s ")
            param.append(ads_publisher)
            setted = True
        if ads_position is not None:
            sql += (", ads_position = %s " if setted else " ads_position = %s ")
            param.append(ads_position)
            setted = True
        if ads_avatar is not None:
            sql += (", ads_avatar = %s " if setted else " ads_avatar = %s ")
            param.append(ads_avatar)
            setted = True
            self.DeleteAdsOldAvatar(ads_id)
        if ads_externalurl is not None:
            sql += (", ads_externalurl = %s " if setted else " ads_externalurl = %s ")
            param.append(ads_externalurl)
            setted = True
        if ads_externalproductid is not None:
            sql += (", ads_externalproductid = %s " if setted else " ads_externalproductid = %s ")
            param.append(ads_externalproductid)
            setted = True
        if ads_begintime is not None:
            sql += (", ads_begintime = %s " if setted else " ads_begintime = %s ")
            param.append(ads_begintime)
            setted = True
        if ads_endtime is not None:
            sql += (", ads_endtime = %s " if setted else " ads_endtime = %s ")
            param.append(ads_endtime)
            setted = True
        if ads_sortweight is not None:
            sql += (", ads_sortweight = %s " if setted else " ads_sortweight = %s ")
            param.append(ads_sortweight)
            setted = True

        if setted:
            sql += " WHERE ads_id = %s"
            param.append(ads_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False
        
    def DeleteAds(self, adsid):
        cursor = self.db.cursor()
        sql = "DELETE FROM ads_table WHERE ads_id = %s"
        param = [adsid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddMessage(self, messageinfo):
        message_type = messageinfo["message_type"] if messageinfo.has_key("message_type") else None
        message_state = messageinfo["message_state"] if messageinfo.has_key("message_state") else None
        message_title = messageinfo["message_title"] if messageinfo.has_key("message_title") else None
        message_publisher = messageinfo["message_publisher"] if messageinfo.has_key("message_publisher") else None
        message_externalurl = messageinfo["message_externalurl"] if messageinfo.has_key("message_externalurl") else None
        message_externalproductid = messageinfo["message_externalproductid"] if messageinfo.has_key("message_externalproductid") else None
        message_sendtime = messageinfo["message_sendtime"] if messageinfo.has_key("message_sendtime") else None
        message_receiver = messageinfo["message_receiver"] if messageinfo.has_key("message_receiver") else None
        message_content = messageinfo["message_content"] if messageinfo.has_key("message_content") else None

        cursor = self.db.cursor()
        value = [None, message_type, message_state, message_title, message_publisher, message_externalurl, 
            message_externalproductid, message_sendtime, message_receiver, message_content]
        cursor.execute("INSERT INTO message_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        lastid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return lastid

    def QueryAllMessageCount(self):
        cursor = self.db.cursor()
        sql = "SELECT COUNT(*) AS COUNT FROM message_table"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def FuzzyQueryMessageCount(self, messagekey):
        cursor = self.db.cursor()
        messagekey = messagekey.replace("'", "''") if messagekey else messagekey
        sql = "SELECT COUNT(*) AS COUNT FROM message_table WHERE message_title LIKE '%%%s%%'" % messagekey
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            return result[0] if result[0] is not None else 0
        else:
            return result["COUNT"] if result["COUNT"] is not None else 0

    def FuzzyQueryMessage(self, messagekey, startpos, count=settings.LIST_ITEM_PER_PAGE):
        cursor = self.db.cursor()
        messagekey = messagekey.replace("'", "''") if messagekey else messagekey
        sql = "SELECT * FROM message_table WHERE message_title LIKE '%%%s%%' ORDER BY message_id DESC LIMIT %s, %s" % (messagekey, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result
        
    def QueryAllMessages(self, startpos, count=settings.LIST_ITEM_PER_PAGE, frontend=0, messagetype=0):
        cursor = self.db.cursor()
        sql = "SELECT * FROM message_table WHERE 1 = 1 "
        if frontend != 0:
            sql += " AND message_state = 1 "
        if messagetype != 0:
            sql += " AND message_type = %s " % messagetype
        sql += " ORDER BY message_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryMessages(self, userid=0, frontend=0, messagetype=0):
        allmessages = self.QueryAllMessages(0, 0, frontend, messagetype=messagetype)
        resultmessages = []
        for messageinfo in allmessages:
            message_receiver = messageinfo[8] if not self.IsDbUseDictCursor() else messageinfo["message_receiver"]
            message_receiver = json.loads(message_receiver) if message_receiver is not None else []
            if int(userid) in message_receiver:
                resultmessages.append(messageinfo)
        return resultmessages
        
    def QueryMessageInfo(self, messageid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM message_table WHERE message_id = %s LIMIT 1"
        param = [messageid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result
        
    def UpdateMessageInfo(self, messageid, messageinfo):
        message_id = messageid

        message_type = messageinfo["message_type"] if messageinfo.has_key("message_type") else None
        message_state = messageinfo["message_state"] if messageinfo.has_key("message_state") else None
        message_title = messageinfo["message_title"] if messageinfo.has_key("message_title") else None
        message_publisher = messageinfo["message_publisher"] if messageinfo.has_key("message_publisher") else None
        message_externalurl = messageinfo["message_externalurl"] if messageinfo.has_key("message_externalurl") else None
        message_externalproductid = messageinfo["message_externalproductid"] if messageinfo.has_key("message_externalproductid") else None
        message_sendtime = messageinfo["message_sendtime"] if messageinfo.has_key("message_sendtime") else None
        message_receiver = messageinfo["message_receiver"] if messageinfo.has_key("message_receiver") else None
        message_content = messageinfo["message_content"] if messageinfo.has_key("message_content") else None

        cursor = self.db.cursor()

        sql     = "UPDATE message_table SET "
        param   = []
        setted  = False
        if message_type is not None:
            sql += " message_type = %s "
            param.append(message_type)
            setted = True
        if message_state is not None:
            sql += (", message_state = %s " if setted else " message_state = %s ")
            param.append(message_state)
            setted = True
        if message_title is not None:
            sql += (", message_title = %s " if setted else " message_title = %s ")
            param.append(message_title)
            setted = True
        if message_publisher is not None:
            sql += (", message_publisher = %s " if setted else " message_publisher = %s ")
            param.append(message_publisher)
            setted = True
        if message_externalurl is not None:
            sql += (", message_externalurl = %s " if setted else " message_externalurl = %s ")
            param.append(message_externalurl)
            setted = True
        if message_externalproductid is not None:
            sql += (", message_externalproductid = %s " if setted else " message_externalproductid = %s ")
            param.append(message_externalproductid)
            setted = True
        if message_sendtime is not None:
            sql += (", message_sendtime = %s " if setted else " message_sendtime = %s ")
            param.append(message_sendtime)
            setted = True
        if message_receiver is not None:
            sql += (", message_receiver = %s " if setted else " message_receiver = %s ")
            param.append(message_receiver)
            setted = True
        if message_content is not None:
            sql += (", message_content = %s " if setted else " message_content = %s ")
            param.append(message_content)
            setted = True

        if setted:
            sql += " WHERE message_id = %s"
            param.append(message_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False
        
    def DeleteMessage(self, messageid):
        cursor = self.db.cursor()
        sql = "DELETE FROM message_table WHERE message_id = %s"
        param = [messageid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()
    
    #####################################################################################################################################

    def AddSearchkeyword(self, searchkeyword_text, sortweight=0):
        keywordinfo = self.QuerySearchkeywordInfoByKeywordText(searchkeyword_text)
        if keywordinfo is not None:
            searchkeyword_id = keywordinfo[0] if not self.IsDbUseDictCursor() else keywordinfo["searchkeyword_id"]
            searchkeyword_frequent = keywordinfo[2] if not self.IsDbUseDictCursor() else keywordinfo["searchkeyword_frequent"]

            searchkeyword_frequent = int(searchkeyword_frequent) + 1
            self.UpdateSearchkeywordInfo(searchkeyword_id, { "searchkeyword_frequent" : searchkeyword_frequent })
        else:
            searchkeyword_frequent = 1
            searchkeyword_isrecommended = 0
            searchkeyword_sortweight = sortweight

            try:
                cursor = self.db.cursor()
                value = [None, searchkeyword_text, searchkeyword_frequent, searchkeyword_isrecommended, searchkeyword_sortweight]
                cursor.execute("INSERT INTO searchkeyword_table VALUES(%s, %s, %s, %s, %s)", value)
                lastid = cursor.lastrowid
                self.db.commit()
                cursor.close()
                return lastid
            except Exception, e:
                return 0

    def UpdateSearchkeywordInfo(self, searchkeywordid, searchkeywordinfo):
        searchkeyword_id = searchkeywordid

        searchkeyword_text = searchkeywordinfo["searchkeyword_text"] if searchkeywordinfo.has_key("searchkeyword_text") else None
        searchkeyword_frequent = searchkeywordinfo["searchkeyword_frequent"] if searchkeywordinfo.has_key("searchkeyword_frequent") else None
        searchkeyword_isrecommended = searchkeywordinfo["searchkeyword_isrecommended"] if searchkeywordinfo.has_key("searchkeyword_isrecommended") else None
        searchkeyword_sortweight = searchkeywordinfo["searchkeyword_sortweight"] if searchkeywordinfo.has_key("searchkeyword_sortweight") else 0

        cursor = self.db.cursor()

        sql     = "UPDATE searchkeyword_table SET "
        param   = []
        setted  = False
        if searchkeyword_text is not None:
            sql += " searchkeyword_text = %s "
            param.append(searchkeyword_text)
            setted = True
        if searchkeyword_frequent is not None:
            sql += (", searchkeyword_frequent = %s " if setted else " searchkeyword_frequent = %s ")
            param.append(searchkeyword_frequent)
            setted = True
        if searchkeyword_isrecommended is not None:
            sql += (", searchkeyword_isrecommended = %s " if setted else " searchkeyword_isrecommended = %s ")
            param.append(searchkeyword_isrecommended)
            setted = True
        if searchkeyword_sortweight is not None:
            sql += (", searchkeyword_sortweight = %s " if setted else " searchkeyword_sortweight = %s ")
            param.append(searchkeyword_sortweight)
            setted = True
        
        if setted:
            sql += " WHERE searchkeyword_id = %s"
            param.append(searchkeyword_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    def QuerySearchkeywords(self, startpos, count=settings.LIST_ITEM_PER_PAGE, frontend=0):
        cursor = self.db.cursor()
        
        if frontend == 0:
            sql = "SELECT * FROM searchkeyword_table ORDER BY searchkeyword_frequent DESC"
        else:
            sql = "SELECT * FROM searchkeyword_table WHERE searchkeyword_isrecommended = 1 ORDER BY searchkeyword_sortweight DESC"
        
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QuerySearchkeywordInfo(self, searchkeywordid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM searchkeyword_table WHERE searchkeyword_id = %s LIMIT 1" % searchkeywordid
        cursor.execute(sql)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QuerySearchkeywordInfoByKeywordText(self, keywordtext):
        cursor = self.db.cursor()

        keywordtext = keywordtext.replace("'", "''") if keywordtext else keywordtext
        sql   = "SELECT * FROM searchkeyword_table WHERE searchkeyword_text = '%s' LIMIT 1" % keywordtext
        cursor.execute(sql)

        result = cursor.fetchone()
        cursor.close()
        return result

    def DeleteSearchkeyword(self, keywordid):
        cursor = self.db.cursor()
        sql = "DELETE FROM searchkeyword_table WHERE searchkeyword_id = %s"
        param = [keywordid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddLink(self, linkinfo):
        links_show = linkinfo["links_show"]
        links_name = linkinfo["links_name"]
        links_url = linkinfo["links_url"]

        links_sortweight = linkinfo["links_sortweight"] if linkinfo.has_key("links_sortweight") else None
        links_logourl = linkinfo["links_logourl"] if linkinfo.has_key("links_logourl") else None
        
        cursor = self.db.cursor()
        value = [ None, links_show, links_name, links_url, links_sortweight, links_logourl ]
        cursor.execute("INSERT INTO links_table (links_id, links_show, links_name, links_url, links_sortweight, links_logourl) VALUES(%s, %s, %s, %s, %s, %s)", value)
        linksid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return linksid

    def UpdateLinkInfo(self, linksid, linkinfo):
        links_id = linksid
        links_show = linkinfo["links_show"] if linkinfo.has_key("links_show") else None
        links_name = linkinfo["links_name"] if linkinfo.has_key("links_name") else None
        links_url = linkinfo["links_url"] if linkinfo.has_key("links_url") else None
        links_sortweight = linkinfo["links_sortweight"] if linkinfo.has_key("links_sortweight") else None
        links_logourl = linkinfo["links_logourl"] if linkinfo.has_key("links_logourl") else None

        cursor = self.db.cursor()
        sql     = "UPDATE links_table SET "
        param   = []
        setted  = False
        if links_show is not None:
            sql += " links_show = %s "
            param.append(links_show)
            setted = True
        if links_name is not None:
            sql += (", links_name = %s " if setted else " links_name = %s ")
            param.append(links_name)
            setted = True
        if links_url is not None:
            sql += (", links_url = %s " if setted else " links_url = %s ")
            param.append(links_url)
            setted = True
        if links_sortweight is not None:
            sql += (", links_sortweight = %s " if setted else " links_sortweight = %s ")
            param.append(links_sortweight)
            setted = True
        if links_logourl is not None:
            sql += (", links_logourl = %s " if setted else " links_logourl = %s ")
            param.append(links_logourl)
            setted = True
        if setted:
            sql += " WHERE links_id = %s"
            param.append(links_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    def QueryLinks(self, startpos, count=settings.LIST_ITEM_PER_PAGE, frontend=0):
        cursor = self.db.cursor()
        
        if frontend == 0:
            sql = "SELECT * FROM links_table ORDER BY links_sortweight DESC"
        else:
            sql = "SELECT * FROM links_table WHERE links_show = 1 ORDER BY links_sortweight DESC"
        
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryLinkInfo(self, linksid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM links_table WHERE links_id = %s LIMIT 1"
        param = [linksid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def DeleteLink(self, linksid):
        cursor = self.db.cursor()
        sql = "DELETE FROM links_table WHERE links_id = %s"
        param = [linksid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    #####################################################################################################################################

    def GegeratePageIndicator(self, totalcount, pageindex, urlprefix, countperpage=settings.LIST_ITEM_PER_PAGE, align=-1):
        # m <= 9:                  < 1 2 3 4 5 6 7 8 9 >
        # m > 9:
        #     (1 <= n <= 6):       < 1 2 3 4 5 6 7 ... m-1 m >
        #     (n > 6):
        #         (n >= m - 3):    < 1 2 ... m-6 m-5 m-4 m-3 m-2 m-1 m >
        #         (n < m - 3 ):    < 1 2 ... n-4 n-3 n-2 n-1 n ... m-1 m >
        # urlprefix = "/?category=$currentcategoryidentifier"
        # align: -1 - 左
        #         0 - 中
        #         1 - 右
        htmlText = ""
        if totalcount > countperpage:
            pagecount = totalcount % countperpage == 0 and (totalcount / countperpage) or (totalcount / countperpage + 1)
            prevpage = pageindex - 1
            nextpage = pageindex + 1
            htmlText += '''<div class="fr_pagination '''
            if align == -1:
                htmlText += "tall"
            if align == 0:
                htmlText += "talc"
            if align == 1:
                htmlText += "talr"
            htmlText += '''" style="line-height: 50px;">'''
                ########################################### m <= 9: < 1 2 3 4 5 6 7 8 9 > ###########################################
            if pagecount <= 9:
                for page in range(pagecount):
                    indicator = page + 1
                    if indicator == pageindex:
                        if indicator == 1:
                            htmlText += '''<span class="disabled previous_page">上一页</span>
                                           <em class="current">%s</em>''' % indicator
                        elif indicator == pagecount:
                            htmlText += '''<em class="current">%s</em>
                                           <span class="disabled next_page">下一页</span>''' % indicator
                        else:
                            htmlText += '''<em class="current">%s</em>''' % indicator
                    else:
                        if indicator == 1:
                            htmlText += '''<a href="%sp=%s" rel="previous" class="previous_page">上一页</a>
                                           <a href="%sp=%s">%s</a>''' % (urlprefix, prevpage, urlprefix, indicator, indicator)
                        elif indicator == pagecount:
                            htmlText += '''<a href="%sp=%s">%s</a>
                                           <a href="%sp=%s" rel="next" class="next_page">下一页</a>''' % (urlprefix, indicator, indicator, urlprefix, nextpage)
                        else:
                            htmlText += '''<a href="%sp=%s">%s</a>''' % (urlprefix, indicator, indicator)
            else:
                #################################### (1 <= n <= 6): < 1 2 3 4 5 6 7 ... m-1 m > #####################################
                if 1 <= pageindex and pageindex <= 6:
                    for page in range(7):
                        indicator = page + 1
                        if indicator == pageindex:
                            if indicator == 1:
                                htmlText += '''<span class="disabled previous_page">上一页</span>
                                               <em class="current">%s</em>''' % indicator
                            else:
                                htmlText += '''<em class="current">%s</em>''' % indicator
                        else:
                            if indicator == 1:
                                htmlText += '''<a href="%sp=%s" rel="previous" class="previous_page">上一页</a>
                                               <a href="%sp=%s">%s</a>''' % (urlprefix, prevpage, urlprefix, indicator, indicator)
                            else:
                                htmlText += '''<a href="%sp=%s">%s</a>''' % (urlprefix, indicator, indicator)
                    htmlText += '''<span class="gap">…</span>'''
                    for page in range(pagecount - 1, pagecount + 1):
                        indicator = page
                        if indicator == pagecount - 1:
                            htmlText += '''<a href="%sp=%s">%s</a>''' % (urlprefix, indicator, indicator)
                        else:
                            htmlText += '''<a href="%sp=%s">%s</a>
                                           <a href="%sp=%s" rel="next" class="next_page">下一页</a>''' % (urlprefix, indicator, indicator, urlprefix, nextpage)
                else:
                    ############################### (n >= m - 3): < 1 2 ... m-6 m-5 m-4 m-3 m-2 m-1 m > #################################
                    if pageindex >= pagecount - 3:
                        for page in range(1, 3):
                            indicator = page
                            if indicator == 1:
                                htmlText += '''<a href="%sp=%s" rel="previous" class="previous_page">上一页</a>
                                               <a href="%sp=%s">%s</a>''' % (urlprefix, prevpage, urlprefix, indicator, indicator)
                            else:
                                htmlText += '''<a href="%sp=%s">%s</a>''' % (urlprefix, indicator, indicator)
                        htmlText += '''<span class="gap">…</span>'''
                        for page in range(pagecount - 6, pagecount + 1):
                            indicator = page
                            if indicator == pageindex:
                                if indicator == pagecount:
                                    htmlText += '''<em class="current">%s</em>
                                                   <span class="disabled next_page">下一页</span>''' % indicator
                                else:
                                    htmlText += '''<em class="current">%s</em>''' % indicator
                            else:
                                if indicator == pagecount:
                                    htmlText += '''<a href="%sp=%s">%s</a>
                                                   <a href="%sp=%s" rel="next" class="next_page">下一页</a>''' % (urlprefix, indicator, indicator, urlprefix, nextpage)
                                else:
                                    htmlText += '''<a href="%sp=%s">%s</a>''' % (urlprefix, indicator, indicator)
                        ############################### (n < m - 3): < 1 2 ... n-4 n-3 n-2 n-1 n ... m-1 m > ################################ -->
                    elif pageindex < pagecount - 3:
                        for page in range(1, 3):
                            indicator = page
                            if indicator == 1:
                                htmlText += '''<a href="%sp=%s" rel="previous" class="previous_page">上一页</a>
                                               <a href="%sp=%s">%s</a>''' % (urlprefix, prevpage, urlprefix, indicator, indicator)
                            else:
                                htmlText += '''<a href="%sp=%s">%s</a>''' % (urlprefix, indicator, indicator)
                        htmlText += '''<span class="gap">…</span>'''
                        for page in range(pageindex - 2, pageindex + 3):
                            indicator = page
                            if indicator == pageindex:
                                htmlText += '''<em class="current">%s</em>''' % indicator
                            else:
                                htmlText += '''<a href="%sp=%s">%s</a>''' % (urlprefix, indicator, indicator)
                        if pageindex + 2 != pagecount - 2:
                            htmlText += '''<span class="gap">…</span>'''
                        for page in range(pagecount - 1, pagecount + 1):
                            indicator = page
                            if indicator == pagecount - 1:
                                htmlText += '''<a href="%sp=%s">%s</a>''' % (urlprefix, indicator, indicator)
                            else:
                                htmlText += '''<a href="%sp=%s">%s</a>
                                               <a href="%sp=%s" rel="next" class="next_page">下一页</a>''' % (urlprefix, indicator, indicator, urlprefix, nextpage)
            htmlText += '''</div>'''
        return htmlText


    def GegerateProductCommentPageIndicatorJS(self, totalcount, pageindex, countperpage, productid):
        # m <= 9:                  < 1 2 3 4 5 6 7 8 9 >
        # m > 9:
        #     (1 <= n <= 6):       < 1 2 3 4 5 6 7 ... m-1 m >
        #     (n > 6):
        #         (n >= m - 3):    < 1 2 ... m-6 m-5 m-4 m-3 m-2 m-1 m >
        #         (n < m - 3 ):    < 1 2 ... n-4 n-3 n-2 n-1 n ... m-1 m >
        # urlprefix = "/?category=$currentcategoryidentifier"
        htmlText = ""
        if totalcount > countperpage:
            pagecount = totalcount % countperpage == 0 and (totalcount / countperpage) or (totalcount / countperpage + 1)
            prevpage = pageindex - 1
            nextpage = pageindex + 1
            htmlText += '''<div class="fr_pagination talr" style="line-height: 50px;">'''
                ########################################### m <= 9: < 1 2 3 4 5 6 7 8 9 > ###########################################
            if pagecount <= 9:
                for page in range(pagecount):
                    indicator = page + 1
                    if indicator == pageindex:
                        if indicator == 1:
                            htmlText += '''<span class="disabled previous_page">上一页</span>
                                           <em class="current">%s</em>''' % indicator
                        elif indicator == pagecount:
                            htmlText += '''<em class="current">%s</em>
                                           <span class="disabled next_page">下一页</span>''' % indicator
                        else:
                            htmlText += '''<em class="current">%s</em>''' % indicator
                    else:
                        if indicator == 1:
                            htmlText += '''<a href="javascript:void(0);" rel="previous" class="india previous_page">上一页</a>
                                           <a href="javascript:void(0);" class="india">%s</a>''' % indicator
                        elif indicator == pagecount:
                            htmlText += '''<a href="javascript:void(0);" class="india">%s</a>
                                           <a href="javascript:void(0);" rel="next" class="india next_page">下一页</a>''' % indicator
                        else:
                            htmlText += '''<a href="javascript:void(0);" class="india">%s</a>''' % indicator
            else:
                #################################### (1 <= n <= 6): < 1 2 3 4 5 6 7 ... m-1 m > #####################################
                if 1 <= pageindex and pageindex <= 6:
                    for page in range(7):
                        indicator = page + 1
                        if indicator == pageindex:
                            if indicator == 1:
                                htmlText += '''<span class="disabled previous_page">上一页</span>
                                               <em class="current">%s</em>''' % indicator
                            else:
                                htmlText += '''<em class="current">%s</em>''' % indicator
                        else:
                            if indicator == 1:
                                htmlText += '''<a href="javascript:void(0);" rel="previous" class="previous_page india">上一页</a>
                                               <a href="javascript:void(0);" class="india">%s</a>''' % indicator
                            else:
                                htmlText += '''<a href="javascript:void(0);" class="india">%s</a>''' % indicator
                    htmlText += '''<span class="gap">…</span>'''
                    for page in range(pagecount - 1, pagecount + 1):
                        indicator = page
                        if indicator == pagecount - 1:
                            htmlText += '''<a href="javascript:void(0);" class="india">%s</a>''' % indicator
                        else:
                            htmlText += '''<a href="javascript:void(0);" class="india">%s</a>
                                           <a href="javascript:void(0);" rel="next" class="india next_page">下一页</a>''' % indicator
                else:
                    ############################### (n >= m - 3): < 1 2 ... m-6 m-5 m-4 m-3 m-2 m-1 m > #################################
                    if pageindex >= pagecount - 3:
                        for page in range(1, 3):
                            indicator = page
                            if indicator == 1:
                                htmlText += '''<a href="javascript:void(0);" rel="previous" class="india previous_page">上一页</a>
                                               <a href="javascript:void(0);" class="india">%s</a>''' % indicator
                            else:
                                htmlText += '''<a href="javascript:void(0);" class="india">%s</a>''' % indicator
                        htmlText += '''<span class="gap">…</span>'''
                        for page in range(pagecount - 6, pagecount + 1):
                            indicator = page
                            if indicator == pageindex:
                                if indicator == pagecount:
                                    htmlText += '''<em class="current">%s</em>
                                                   <span class="disabled next_page">下一页</span>''' % indicator
                                else:
                                    htmlText += '''<em class="current">%s</em>''' % indicator
                            else:
                                if indicator == pagecount:
                                    htmlText += '''<a href="javascript:void(0);" class="india">%s</a>
                                                   <a href="javascript:void(0);" rel="next" class="next_page india">下一页</a>''' % indicator
                                else:
                                    htmlText += '''<a href="javascript:void(0);" class="india">%s</a>''' % indicator
                        ############################### (n < m - 3): < 1 2 ... n-4 n-3 n-2 n-1 n ... m-1 m > ################################ -->
                    elif pageindex < pagecount - 3:
                        for page in range(1, 3):
                            indicator = page
                            if indicator == 1:
                                htmlText += '''<a href="javascript:void(0);" rel="previous" class="previous_page india">上一页</a>
                                               <a href="javascript:void(0);" class="india">%s</a>''' % indicator
                            else:
                                htmlText += '''<a href="javascript:void(0);" class="india">%s</a>''' % indicator
                        htmlText += '''<span class="gap">…</span>'''
                        for page in range(pageindex - 2, pageindex + 3):
                            indicator = page
                            if indicator == pageindex:
                                htmlText += '''<em class="current">%s</em>''' % indicator
                            else:
                                htmlText += '''<a href="javascript:void(0);" class="india">%s</a>''' % indicator
                        if pageindex + 2 != pagecount - 2:
                            htmlText += '''<span class="gap">…</span>'''
                        for page in range(pagecount - 1, pagecount + 1):
                            indicator = page
                            if indicator == pagecount - 1:
                                htmlText += '''<a href="javascript:void(0);" class="india">%s</a>''' % indicator
                            else:
                                htmlText += '''<a href="javascript:void(0);" class="india">%s</a>
                                               <a href="javascript:void(0);" rel="next" class="next_page india">下一页</a>''' % indicator
            htmlText += '''</div>'''
            htmlText += '''
                            <script type="text/javascript">
                                $(".india").click(function() {
                                    var pi = $(this).html();
                                    $.ajax({
                                        type : "get",
                                        url : "/product/getcomment",
                                        data : { "index" : pi, "curindex" : %s, "id" : %s, "t" : Math.round(Math.random(0) * 100000) },
                                        dataType : "html",
                                        contentType: "application/x-www-form-urlencoded; charset=utf-8",
                                        async : true,
                                        success : function(data) {
                                            $("#commentContainer").html(data);
                                        }, 
                                        error : function(){
                                            
                                        }
                                    });
                                });
                            </script>
                        ''' % (pageindex, productid)
        return htmlText

    #####################################################################################################################################

    def CalculateAPIToken(self, xsrf):
        s  = xsrf
        s0 = s.replace("-", "")
        s1 = hashlib.sha256(s0).hexdigest().upper()
        s2 = hashlib.md5(s1).hexdigest().upper()
        s3 = hashlib.md5(s2).hexdigest().upper()
        s4 = hashlib.md5(s3).hexdigest().upper()
        s5 = s4[::-1]
        s6 = hashlib.md5(s5).hexdigest().upper()
        s7 = hashlib.sha256(s6).hexdigest().upper()
        return s7

    def AddValidUUID(self, uuid):
        cursor = self.db.cursor()
        sql    = "INSERT INTO apiuuid_table VALUES(%s, %s)"
        value  = [None, uuid]
        cursor.execute(sql, value)
        self.db.commit()
        cursor.close()

    def IsUUIDExist(self, uuid):
        cursor = self.db.cursor()
        sql    = "SELECT * FROM apiuuid_table WHERE apiuuid_value = %s LIMIT 1"
        param  = [uuid]
        cursor.execute(sql, param)
        result = cursor.fetchone()
        cursor.close()
        return True if result else False

    #####################################################################################################################################

    def AddVote(self, voteinfo):
        vote_name = voteinfo["vote_name"]
        vote_status = voteinfo["vote_status"]
        vote_begintime = voteinfo["vote_begintime"]
        vote_endtime = voteinfo["vote_endtime"]
        vote_permission = voteinfo["vote_permission"]
        vote_countmode = voteinfo["vote_countmode"]
        vote_maxresult_count = voteinfo["vote_maxresult_count"]

        vote_countwhenshare = voteinfo["vote_countwhenshare"] if voteinfo.has_key("vote_countwhenshare") else None
        vote_description = voteinfo["vote_description"] if voteinfo.has_key("vote_description") else None
        vote_reserve1 = voteinfo["vote_reserve1"] if voteinfo.has_key("vote_reserve1") else None
        vote_reserve2 = voteinfo["vote_reserve2"] if voteinfo.has_key("vote_reserve2") else None

        cursor = self.db.cursor()
        value = [ None, vote_name, vote_status, vote_begintime, vote_endtime, vote_permission, vote_countmode, vote_countwhenshare, vote_description, vote_maxresult_count, vote_reserve1, vote_reserve2 ]
        cursor.execute("INSERT INTO vote_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        voteid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return voteid

    def QueryAllUserVotes(self, userid):
        '''查询用户参与过的所有投票信息
        '''
        allvotes = self.QueryVotes(0, 0, frontend=1)
        alluservotes = list([])
        for voteinfo in allvotes:
            if not self.IsDbUseDictCursor():
                vote_reserve2 = json.loads(voteinfo[11]) if voteinfo[11] is not None else dict({})
            else:
                vote_reserve2 = json.loads(voteinfo["vote_reserve2"]) if voteinfo["vote_reserve2"] is not None and len(voteinfo["vote_reserve2"]) > 0 else dict({})

            if vote_reserve2.has_key(str(userid)):
                alluservotes.append(voteinfo)
        return alluservotes

    def QueryVotes(self, startpos, count=settings.LIST_ITEM_PER_PAGE, frontend=0):
        cursor = self.db.cursor()
        sql = "SELECT * FROM vote_table "

        if frontend != 0:
            sql += " WHERE vote_status = 1 "

        sql += " ORDER BY vote_id DESC "

        if count != 0:
            sql += " LIMIT %d, %d " % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryVoteInfo(self, voteid):
        cursor = self.db.cursor()

        sql    = "SELECT * FROM vote_table WHERE vote_id = %s LIMIT 1"
        param  = [voteid]
        cursor.execute(sql, param)
        result = cursor.fetchone()
        cursor.close()
        return result

    def UpdateVoteInfo(self, voteid, voteinfo):
        vote_id = voteid
        vote_name = voteinfo["vote_name"] if voteinfo.has_key("vote_name") else None
        vote_status = voteinfo["vote_status"] if voteinfo.has_key("vote_status") else None
        vote_begintime = voteinfo["vote_begintime"] if voteinfo.has_key("vote_begintime") else None
        vote_endtime = voteinfo["vote_endtime"] if voteinfo.has_key("vote_endtime") else None
        vote_permission = voteinfo["vote_permission"] if voteinfo.has_key("vote_permission") else None
        vote_countmode = voteinfo["vote_countmode"] if voteinfo.has_key("vote_countmode") else None
        vote_countwhenshare = voteinfo["vote_countwhenshare"] if voteinfo.has_key("vote_countwhenshare") else None
        vote_description = voteinfo["vote_description"] if voteinfo.has_key("vote_description") else None
        vote_maxresult_count = voteinfo["vote_maxresult_count"] if voteinfo.has_key("vote_maxresult_count") else None
        vote_reserve1 = voteinfo["vote_reserve1"] if voteinfo.has_key("vote_reserve1") else None
        vote_reserve2 = voteinfo["vote_reserve2"] if voteinfo.has_key("vote_reserve2") else None

        cursor = self.db.cursor()

        sql     = "UPDATE vote_table SET "
        param   = []
        setted  = False
        if vote_name is not None:
            sql += " vote_name = %s "
            param.append(vote_name)
            setted = True
        if vote_status is not None:
            sql += (", vote_status = %s " if setted else " vote_status = %s ")
            param.append(vote_status)
            setted = True
        if vote_begintime is not None:
            sql += (", vote_begintime = %s " if setted else " vote_begintime = %s ")
            param.append(vote_begintime)
            setted = True
        if vote_endtime is not None:
            sql += (", vote_endtime = %s " if setted else " vote_endtime = %s ")
            param.append(vote_endtime)
            setted = True
        if vote_permission is not None:
            sql += (", vote_permission = %s " if setted else " vote_permission = %s ")
            param.append(vote_permission)
            setted = True
        if vote_countmode is not None:
            sql += (", vote_countmode = %s " if setted else " vote_countmode = %s ")
            param.append(vote_countmode)
            setted = True
        if vote_countwhenshare is not None:
            sql += (", vote_countwhenshare = %s " if setted else " vote_countwhenshare = %s ")
            param.append(vote_countwhenshare)
            setted = True
        if vote_description is not None:
            sql += (", vote_description = %s " if setted else " vote_description = %s ")
            param.append(vote_description)
            setted = True
        if vote_maxresult_count is not None:
            sql += (", vote_maxresult_count = %s " if setted else " vote_maxresult_count = %s ")
            param.append(vote_maxresult_count)
            setted = True
        if vote_reserve1 is not None:
            sql += (", vote_reserve1 = %s " if setted else " vote_reserve1 = %s ")
            param.append(vote_reserve1)
            setted = True
        if vote_reserve2 is not None:
            sql += (", vote_reserve2 = %s " if setted else " vote_reserve2 = %s ")
            param.append(vote_reserve2)
            setted = True

        if setted:
            sql += " WHERE vote_id = %s"
            param.append(vote_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    def DeleteVote(self, voteid):
        cursor = self.db.cursor()
        sql = "DELETE FROM vote_table WHERE vote_id = %s"
        param = [voteid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

        self.DeleteVoteOptionByVoteId(voteid)

    def DeleteVoteOptionByVoteId(self, voteid):
        cursor = self.db.cursor()
        sql = "DELETE FROM vote_option_table WHERE vote_option_voteid = %s"
        param = [voteid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    def GetVoteAvatarPreview(self, voteid):
        hascustomavatar = True

        voteinfo = self.QueryVoteInfo(voteid)
        if voteinfo is None:
            return '/static/img/avatar/vote/default_vote.jpeg'
        filedir = socket.gethostname() == settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp'
        avatarfile = '/static/img/avatar/vote/C%s_%s.jpeg' % (voteinfo[0] if not self.IsDbUseDictCursor() else voteinfo["vote_id"], self.GetVoteAvatarUniqueString(voteid))

        # logging.debug("vote avatarfile is: %r" % avatarfile)

        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/vote/default_vote.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    def GetVoteAvatarUniqueString(self, voteid):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM vote_table WHERE vote_id = %s LIMIT 1"
        param = [voteid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result[10] if not self.IsDbUseDictCursor() else result["vote_reserve1"]
            if avt is None:
                ret = None
            elif len(avt) < 1:
                ret = None
            elif avt == "None" or avt == "NULL":
                ret = None
            else:
                ret = avt
            return ret
        else:
            return None

    #####################################################################################################################################

    def AddVoteOption(self, voteoptioninfo):
        vote_option_voteid = voteoptioninfo["vote_option_voteid"]
        vote_option_title = voteoptioninfo["vote_option_title"]

        vote_option_description = voteoptioninfo["vote_option_description"] if voteoptioninfo.has_key("vote_option_description") else None
        vote_option_sortweight = voteoptioninfo["vote_option_sortweight"] if voteoptioninfo.has_key("vote_option_sortweight") else None
        vote_option_avatar = voteoptioninfo["vote_option_avatar"] if voteoptioninfo.has_key("vote_option_avatar") else None
        vote_option_video = voteoptioninfo["vote_option_video"] if voteoptioninfo.has_key("vote_option_video") else None
        vote_option_result = voteoptioninfo["vote_option_result"] if voteoptioninfo.has_key("vote_option_result") else None
        vote_option_reserve1 = voteoptioninfo["vote_option_reserve1"] if voteoptioninfo.has_key("vote_option_reserve1") else None
        vote_option_reserve2 = voteoptioninfo["vote_option_reserve2"] if voteoptioninfo.has_key("vote_option_reserve2") else None

        cursor = self.db.cursor()
        value = [ None, vote_option_voteid, vote_option_title, vote_option_description, vote_option_sortweight, vote_option_avatar, vote_option_video, vote_option_result, vote_option_reserve1, vote_option_reserve2 ]
        cursor.execute("INSERT INTO vote_option_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        voteoptionid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return voteoptionid

    def QueryVoteOptions(self, voteid, startpos, count=settings.LIST_ITEM_PER_PAGE, status=2):
        '''status: 1 - 上架, 0 - 审核中, -1 - 下架, 2 - 不限
        '''
        cursor = self.db.cursor()
        if status == 2:
            sql = "SELECT * FROM vote_option_table WHERE vote_option_voteid = %s ORDER BY vote_option_sortweight DESC " % voteid
        else:
            sql = "SELECT * FROM vote_option_table WHERE vote_option_voteid = %s AND vote_option_reserve2 = %s ORDER BY vote_option_sortweight DESC " % (voteid, status)
        
        if count != 0:
            sql += " LIMIT %d, %d " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryVoteOptionInfo(self, voteoptionid):
        cursor = self.db.cursor()

        sql    = "SELECT * FROM vote_option_table WHERE vote_option_id = %s LIMIT 1"
        param  = [voteoptionid]
        cursor.execute(sql, param)
        result = cursor.fetchone()
        cursor.close()
        return result

    def UpdateVoteOptionInfo(self, voteoptionid, voteoptioninfo):
        vote_option_id = voteoptionid

        vote_option_voteid = voteoptioninfo["vote_option_voteid"] if voteoptioninfo.has_key("vote_option_voteid") else None
        vote_option_title = voteoptioninfo["vote_option_title"] if voteoptioninfo.has_key("vote_option_title") else None
        vote_option_description = voteoptioninfo["vote_option_description"] if voteoptioninfo.has_key("vote_option_description") else None
        vote_option_sortweight = voteoptioninfo["vote_option_sortweight"] if voteoptioninfo.has_key("vote_option_sortweight") else None
        vote_option_avatar = voteoptioninfo["vote_option_avatar"] if voteoptioninfo.has_key("vote_option_avatar") else None
        vote_option_video = voteoptioninfo["vote_option_video"] if voteoptioninfo.has_key("vote_option_video") else None
        vote_option_result = voteoptioninfo["vote_option_result"] if voteoptioninfo.has_key("vote_option_result") else None
        vote_option_reserve1 = voteoptioninfo["vote_option_reserve1"] if voteoptioninfo.has_key("vote_option_reserve1") else None
        vote_option_reserve2 = voteoptioninfo["vote_option_reserve2"] if voteoptioninfo.has_key("vote_option_reserve2") else None

        cursor = self.db.cursor()

        sql     = "UPDATE vote_option_table SET "
        param   = []
        setted  = False
        if vote_option_voteid is not None:
            sql += " vote_option_voteid = %s "
            param.append(vote_option_voteid)
            setted = True
        if vote_option_title is not None:
            sql += (", vote_option_title = %s " if setted else " vote_option_title = %s ")
            param.append(vote_option_title)
            setted = True
        if vote_option_description is not None:
            sql += (", vote_option_description = %s " if setted else " vote_option_description = %s ")
            param.append(vote_option_description)
            setted = True
        if vote_option_sortweight is not None:
            sql += (", vote_option_sortweight = %s " if setted else " vote_option_sortweight = %s ")
            param.append(vote_option_sortweight)
            setted = True
        if vote_option_avatar is not None:
            sql += (", vote_option_avatar = %s " if setted else " vote_option_avatar = %s ")
            param.append(vote_option_avatar)
            setted = True
        if vote_option_video is not None:
            sql += (", vote_option_video = %s " if setted else " vote_option_video = %s ")
            param.append(vote_option_video)
            setted = True
        if vote_option_result is not None:
            sql += (", vote_option_result = %s " if setted else " vote_option_result = %s ")
            param.append(vote_option_result)
            setted = True
        if vote_option_reserve1 is not None:
            sql += (", vote_option_reserve1 = %s " if setted else " vote_option_reserve1 = %s ")
            param.append(vote_option_reserve1)
            setted = True
        if vote_option_reserve2 is not None:
            sql += (", vote_option_reserve2 = %s " if setted else " vote_option_reserve2 = %s ")
            param.append(vote_option_reserve2)
            setted = True
        
        if setted:
            sql += " WHERE vote_option_id = %s"
            param.append(vote_option_id)

            cursor.execute(sql, param)
            self.db.commit()
            cursor.close()
            return True
        else:
            return False

    def DeleteVoteOption(self, voteoptionid):
        cursor = self.db.cursor()
        sql = "DELETE FROM vote_option_table WHERE vote_option_id = %s"
        param = [voteoptionid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    def VoteForOption(self, userid, voteoptionid):
        '''用户对某个投票选项进行投票，返回值：
             1 - 投票成功
             2 - 您已经投票过了，无法再次投票
             3 - 您今天已经投票过了，请明天再来投票
             4 - 投票已结束，无法进行投票
        '''
        # 获取用户最近一次的投票时间
        oldvoteoptioninfo = self.QueryVoteOptionInfo(voteoptionid=voteoptionid)
        voteid = oldvoteoptioninfo[1] if not self.IsDbUseDictCursor() else oldvoteoptioninfo["vote_option_voteid"]
        voteinfo = self.QueryVoteInfo(voteid)
        vote_reserve2 = voteinfo[11] if not self.IsDbUseDictCursor() else voteinfo["vote_reserve2"]
        userlastvotetime = None

        # vote_maxresult_count = voteinfo[9] if not self.IsDbUseDictCursor() else voteinfo["vote_maxresult_count"]
        # voteuservotecount = self.QueryVoteTimesForVote(voteid=voteid, userid=userid)
        # if int(voteuservotecount) > int(vote_maxresult_count):
        #     # 用户对整个投票的投票次数大于后台设置的次数
        #     logging.debug("此投票最多允许投 %s 次，用户已经投票 %s 次，无法进行投票")
        #     return 5

        if vote_reserve2 is not None and len(vote_reserve2) > 0:
            vote_reserve2 = json.loads(vote_reserve2)
        else:
            vote_reserve2 = dict({})
        if vote_reserve2.has_key(str(userid)):
            userlastvotetime = vote_reserve2[str(userid)]
            if type(userlastvotetime) == dict:
                userlastvotetime = userlastvotetime[str(voteoptionid)] if userlastvotetime.has_key(str(voteoptionid)) else "1970-01-01 12:00:00"
            else:
                userlastvotetime = "1970-01-01 12:00:00"

        vote_endtime = voteinfo[4] if not self.IsDbUseDictCursor() else voteinfo["vote_endtime"]
        vote_endtime = str(vote_endtime) if vote_endtime is not None else "1970-01-01 12:01:01"
        vote_endtime = vote_endtime if len(vote_endtime) == len("1970-01-01 12:01:01") else "1970-01-01 12:01:01"

        # 检测当前时间是否处于投票时间之内
        present = datetime.datetime.now()
        votetime = datetime.datetime(int(vote_endtime[0:4]), int(vote_endtime[5:7]), int(vote_endtime[8:10]), int(vote_endtime[11:13]), int(vote_endtime[14:16]), int(vote_endtime[17:19]))
        if votetime < present:
            return 4

        # 根据投票频率设置判断用户是否有权限进行投票
        vote_countmode = int(voteinfo[6] if not self.IsDbUseDictCursor() else voteinfo["vote_countmode"])  # "永远只可投一次 - 0, 每天只可投一次 - 1" （"投一次"是针对某一个投票选项而言，而不是整个投票）
        if vote_countmode == 0:
            if self.IsUserVotedVoteOption(userid, voteoptionid):
                # 对此投票选项已经投过票
                # 用户已经投票，且永久只可投一次
                logging.debug("用户已经投票，且对某个投票选项永久只可投一次")

                return 2
            else:
                # 对此投票选项没有投过票
                # 用户没有投过票，且永久只可投一次
                logging.debug("用户没有投过票，且对某个投票选项永久只可投一次")

                self.vote(userid, vote_reserve2, voteinfo, oldvoteoptioninfo)
                return 1
        elif vote_countmode == 1:
            if self.IsUserVotedVoteOption(userid, voteoptionid):
                # 用户已经投票，但每天都可投一次
                currentdatetime = strftime("%Y-%m-%d %H:%M:%S")
                if userlastvotetime[0:10] == currentdatetime[0:10]:
                    # 当天已投票，不可再次投票
                    logging.debug("当天已投票，对某个投票选项不可再次投票")

                    return 3
                else:
                    # 最后一次投票日期与当天不是同一天，可以投票
                    logging.debug("最后一次投票日期与当天不是同一天，对某个投票选项可以投票")
                    
                    self.vote(userid, vote_reserve2, voteinfo, oldvoteoptioninfo)
                    return 1
            else:
                # 用户没有投过票，但每天都可投一次
                logging.debug("用户没有投过票，但对某个投票选项每天都可投一次")

                self.vote(userid, vote_reserve2, voteinfo, oldvoteoptioninfo)
                return 1

    def vote(self, userid, vote_reserve2, voteinfo, oldvoteoptioninfo):
        voteoptionid = oldvoteoptioninfo[0] if not self.IsDbUseDictCursor() else oldvoteoptioninfo["vote_option_id"]
        voteresult = oldvoteoptioninfo[7] if not self.IsDbUseDictCursor() else oldvoteoptioninfo["vote_option_result"]
        if voteresult is None or len(voteresult) < 1:
            voteresult = "[]"
        voteresultlist = json.loads(voteresult)
        voteresultlist = list(voteresultlist)
        # if userid not in voteresultlist:
        voteresultlist.append(userid)
        voteresult = json.dumps(voteresultlist)
        self.UpdateVoteOptionInfo(voteoptionid=voteoptionid, voteoptioninfo={ "vote_option_result" : voteresult })

        uservoteresult = vote_reserve2[str(userid)] if vote_reserve2.has_key(str(userid)) else {}
        if type(uservoteresult) == dict:
            uservoteresult[str(voteoptionid)] = strftime("%Y-%m-%d %H:%M:%S")
            vote_reserve2[str(userid)] = uservoteresult
        else:
            vote_reserve2[str(userid)] = { str(voteoptionid) : "1970-01-01 12:00:00" }

        self.UpdateVoteInfo(voteid=voteinfo[0] if not self.IsDbUseDictCursor() else voteinfo["vote_id"], voteinfo={ "vote_reserve2" : json.dumps(vote_reserve2) })

    def QueryVoteTimesForVote(self, voteid, userid=0):
        '''查询某个投票的总投票次数, userid 为 0 时查询全部，不为 0 时只查询某个用户对某个投票的投票次数
        '''
        allvoteoptions = self.QueryVoteOptions(voteid, 0, 0)
        totalcount = 0
        for voteoptioninfo in allvoteoptions:
            totalcount += self.QueryVoteTimesForVoteOption(voteoptioninfo[0] if not self.IsDbUseDictCursor() else voteoptioninfo["vote_option_id"], userid=userid)
        return totalcount

    def QueryVoteTimesForVoteOption(self, voteoptionid, userid=0):
        '''查询某个投票选项的总投票次数, userid 为 0 时查询全部，不为 0 时只查询某个用户对某个投票选项的投票次数
        '''
        voteoptioninfo = self.QueryVoteOptionInfo(voteoptionid)
        if not self.IsDbUseDictCursor():
            try:
                vote_option_result = json.loads(voteoptioninfo[7]) if voteoptioninfo[7] is not None else []
            except Exception, e:
                vote_option_result = list([])
        else:
            vote_option_result = json.loads(voteoptioninfo["vote_option_result"]) if voteoptioninfo["vote_option_result"] is not None and len(voteoptioninfo["vote_option_result"]) > 0 else []

        if userid == 0:
            return len(vote_option_result)
        else:
            totaltimes = 0
            for item in vote_option_result:
                if str(item) == str(userid):
                    totaltimes += 1
            return totaltimes

    def IsUserVotedVote(self, userid, voteid):
        '''用户是否对某个投票进行过投票
        '''
        userinfo = self.QueryUserInfoById(userid)
        voteinfo = self.QueryVoteInfo(voteid)

        if userinfo is None or voteinfo is None:
            return False

        allvoteoptions = self.QueryVoteOptions(voteid, 0, 0)
        for voteoptioninfo in allvoteoptions:
            if not self.IsDbUseDictCursor():
                vote_option_result = json.loads(voteoptioninfo[7]) if voteoptioninfo[7] is not None else []
            else:
                vote_option_result = json.loads(voteoptioninfo["vote_option_result"]) if voteoptioninfo["vote_option_result"] is not None and len(voteoptioninfo["vote_option_result"]) > 0 else []
            vote_option_result = list(vote_option_result)
            if userid in vote_option_result:
                return True
        return False

    def IsUserVotedVoteOption(self, userid, voteoptionid):
        '''用户是否对某个投票选项进行过投票
        '''
        voteoptioninfo = self.QueryVoteOptionInfo(voteoptionid)
        if not self.IsDbUseDictCursor():
            vote_option_result = json.loads(voteoptioninfo[7]) if voteoptioninfo[7] is not None else []
        else:
            vote_option_result = json.loads(voteoptioninfo["vote_option_result"]) if voteoptioninfo["vote_option_result"] is not None and len(voteoptioninfo["vote_option_result"]) > 0 else []
        vote_option_result = list(vote_option_result)
        userid = "%s" % userid

        if userid in vote_option_result or int(userid) in vote_option_result:
            return True
        return False

    def GetVoteOptionPreviews(self, voteoptionid):
        voteoptioninfo = self.QueryVoteOptionInfo(voteoptionid)
        filedir = abspath
        avatars = self.GetVoteOptionAvatarUniqueStrings(voteoptionid)
        file_tmpl = '/static/img/avatar/vote/%s.jpeg'

        for uniquestr in avatars:
            if not self.IsDbUseDictCursor():
                avatarfile = file_tmpl % ('P%s_%s' % (voteoptioninfo[0], uniquestr))
            else:
                avatarfile = file_tmpl % ('P%s_%s' % (voteoptioninfo["vote_option_id"], uniquestr))
            outfile = filedir + avatarfile
            hascustomavatar = os.path.exists(outfile)
            yield (
                avatarfile, # if hascustomavatar else file_tmpl % 'default_avatar_product',
                uniquestr,
                hascustomavatar
            )

    def GetVoteOptionPreviewsV2(self, voteoptionid):
        voteoptioninfo = self.QueryVoteOptionInfo(voteoptionid)
        filedir = abspath
        avatars = self.GetVoteOptionAvatarUniqueStrings(voteoptionid)
        file_tmpl = '/static/img/avatar/vote/%s.jpeg'
        resultlist = []

        for uniquestr in avatars:
            if not self.IsDbUseDictCursor():
                avatarfile = file_tmpl % ('P%s_%s' % (voteoptioninfo[0], uniquestr))
            else:
                avatarfile = file_tmpl % ('P%s_%s' % (voteoptioninfo["vote_option_id"], uniquestr))
            outfile = filedir + avatarfile
            hascustomavatar = os.path.exists(outfile)
            resultlist.append((avatarfile, uniquestr, hascustomavatar))

        return resultlist

    def GetVoteOptionAvatarUniqueStrings(self, voteoptionid):
        cursor = self.db.cursor()
        sql = "SELECT * FROM vote_option_table WHERE vote_option_id = %s LIMIT 1"
        param = [voteoptionid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            if result is not None:
                if result[5] is not None:
                    if result[5].startswith('['):
                        try:
                            return json.loads(result[5])
                        except (TypeError, ValueError):
                            pass
                    else:
                        return [result[5]]
        else:
            if result is not None:
                if result["vote_option_avatar"] is not None:
                    if result["vote_option_avatar"].startswith('['):
                        try:
                            return json.loads(result["vote_option_avatar"])
                        except (TypeError, ValueError):
                            pass
                    else:
                        return [result["vote_option_avatar"]]
        return []

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def QueryRegisterCounts(self, registersource=0, startdate=None, enddate=None, stateunit=1):
        '''查询注册量， registersource: 0 - 全部，1 - 网站，2 - iOS客户端，3 - Android客户端
                       startdate: 统计起始日期
                       enddate: 统计结束日期
                       stateunit: 统计单位，1 - 日，2 - 周，3 - 月
           返回结果：stateunit 为 1 时返回字典，格式： { "20120230" : 39, ... } ( "年+月+日" : 注册人数 )
                    stateunit 为 2 时返回字典，格式： { "201451" : 39, ... } ( "年+周序数" : 注册人数 )
                    stateunit 为 3 时返回字典，格式： { "201402" : 39, ... } ( "年+月" : 注册人数 )
        '''
        registersource = int(registersource)
        stateunit = int(stateunit)
        if startdate is None or enddate is None:
            enddate = datetime.datetime.now()
            startdate = enddate - timedelta(days=30)
        startdate = str(startdate)
        enddate = str(enddate)

        startdate = datetime.datetime(int(startdate[0:4]), int(startdate[5:7]), int(startdate[8:10]), int(startdate[11:13]), int(startdate[14:16]), int(startdate[17:19]))
        enddate = datetime.datetime(int(enddate[0:4]), int(enddate[5:7]), int(enddate[8:10]), int(enddate[11:13]), int(enddate[14:16]), int(enddate[17:19]))

        sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_registertime < '%s' AND user_registertime > '%s'" % (str(enddate), str(startdate))
        if registersource != 0:
            sql += " AND user_registersource = %s " % registersource

        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

        resultdict = {}
        if stateunit == 1:
            for single_date in self.daterange(datetime.date(startdate.year, startdate.month, startdate.day), datetime.date(enddate.year, enddate.month, enddate.day)):
                registercount = 0
                for userinfo in result:
                    user_registertime = userinfo["user_registertime"]
                    if single_date.strftime("%Y%m%d") == user_registertime.strftime("%Y%m%d"):
                        registercount += 1
                resultdict[single_date.strftime("%Y%m%d")] = registercount
        elif stateunit == 2:
            if len(result) > 0:
                for userinfo in result:
                    user_registertime = userinfo["user_registertime"]
                    userkey = "%04d%02d" % (user_registertime.year, user_registertime.isocalendar()[1])
                    if resultdict.has_key(userkey):
                        resultdict[userkey] += 1
                    else:
                        resultdict[userkey] = 1
                # resultdict = sorted(resultdict.items())
            else:
                for single_date in self.daterange(datetime.date(startdate.year, startdate.month, startdate.day), datetime.date(enddate.year, enddate.month, enddate.day)):
                    userkey = "%04d%02d" % (single_date.year, single_date.isocalendar()[1])
                    resultdict[userkey] = 0
        elif stateunit == 3:
            if len(result) > 0:
                for userinfo in result:
                    user_registertime = userinfo["user_registertime"]
                    userkey = "%04d%02d" % (user_registertime.year, user_registertime.month)
                    if resultdict.has_key(userkey):
                        resultdict[userkey] += 1
                    else:
                        resultdict[userkey] = 1
                # resultdict = sorted(resultdict.items())
            else:
                for single_date in self.daterange(datetime.date(startdate.year, startdate.month, startdate.day), datetime.date(enddate.year, enddate.month, enddate.day)):
                    userkey = "%04d%02d" % (single_date.year, single_date.month)
                    resultdict[userkey] = 0
        return resultdict

    def QueryIncome(self, registersource=0, startdate=None, enddate=None, stateunit=1, statedata=1, producttype=0):
        '''查询注册量， registersource: 0 - 全部，1 - 网站，2 - iOS客户端，3 - Android客户端
                       startdate: 统计起始日期
                       enddate: 统计结束日期
                       stateunit: 统计单位，1 - 日，2 - 周，3 - 月
                       statedata: 统计数据，1 - 付费人数，2 - 销量，3 - 消费金额，4 - ARPU值
                       producttype: 统计商品类型，全部 - 0，体育培训 - 1, 体育旅游 - 2, 课程体检 - 3, 精彩活动 - 4, 积分商城 - 5, 私人教练 - 6, 冬夏令营 - 7
           返回结果：stateunit 为 1 时返回字典，格式： { "20120230" : 39, ... } ( "年+月+日" : 注册人数 )
                    stateunit 为 2 时返回字典，格式： { "201451" : 39, ... } ( "年+周序数" : 注册人数 )
                    stateunit 为 3 时返回字典，格式： { "201402" : 39, ... } ( "年+月" : 注册人数 )
        '''
        registersource = int(registersource)
        statedata = int(statedata)
        stateunit = int(stateunit)
        producttype = int(producttype)
        if startdate is None or enddate is None:
            enddate = datetime.datetime.now()
            startdate = enddate - timedelta(days=30)
        startdate = str(startdate)
        enddate = str(enddate)

        startdate = datetime.datetime(int(startdate[0:4]), int(startdate[5:7]), int(startdate[8:10]), int(startdate[11:13]), int(startdate[14:16]), int(startdate[17:19]))
        enddate = datetime.datetime(int(enddate[0:4]), int(enddate[5:7]), int(enddate[8:10]), int(enddate[11:13]), int(enddate[14:16]), int(enddate[17:19]))

        sql = "SELECT * FROM preorder_table WHERE deleteflag = 0 AND preorder_paymentstatus = 1 AND preorder_paytime < '%s' AND preorder_paytime > '%s'" % (str(enddate), str(startdate))
        if registersource != 0:
            clause = '''%%"P": %s%%''' % (registersource - 1)

            sql = "%s AND preorder_paymentmethod LIKE '%s' " % (sql, clause)

        if producttype != 0:
            sql = "%s AND preorder_productid IN (SELECT product_id FROM product_table WHERE deleteflag = 0 AND product_type = %s) " % (sql, producttype)

        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

        resultdict = {}
        if stateunit == 1:
            for single_date in self.daterange(datetime.date(startdate.year, startdate.month, startdate.day), datetime.date(enddate.year, enddate.month, enddate.day)):
                registercount = 0
                for orderinfo in result:
                    unit = 1
                    if statedata == 1:
                        unit = 1
                    elif statedata == 2:
                        unit = int(orderinfo["preorder_counts"])
                    elif statedata == 3:
                        unit = float("{0:.2f}".format(float(orderinfo["preorder_fullprice"])))
                    elif statedata == 4:
                        unit = 0 if int(orderinfo["preorder_counts"]) == 0 else float("%.2f" % (float(orderinfo["preorder_fullprice"]) / int(orderinfo["preorder_counts"])))
                    else:
                        unit = 1

                    preorder_paytime = orderinfo["preorder_paytime"]
                    if single_date.strftime("%Y%m%d") == preorder_paytime.strftime("%Y%m%d"):
                        registercount += unit
                resultdict[single_date.strftime("%Y%m%d")] = registercount
        elif stateunit == 2:
            if len(result) > 0:
                for orderinfo in result:
                    unit = 1
                    if statedata == 1:
                        unit = 1
                    elif statedata == 2:
                        unit = int(orderinfo["preorder_counts"])
                    elif statedata == 3:
                        unit = float("{0:.2f}".format(float(orderinfo["preorder_fullprice"])))
                    elif statedata == 4:
                        unit = 0 if int(orderinfo["preorder_counts"]) == 0 else float("%.2f" % (float(orderinfo["preorder_fullprice"]) / int(orderinfo["preorder_counts"])))
                    else:
                        unit = 1

                    preorder_paytime = orderinfo["preorder_paytime"]
                    userkey = "%04d%02d" % (preorder_paytime.year, preorder_paytime.isocalendar()[1])
                    if resultdict.has_key(userkey):
                        resultdict[userkey] += unit
                    else:
                        resultdict[userkey] = unit
                # resultdict = sorted(resultdict.items())
            else:
                for single_date in self.daterange(datetime.date(startdate.year, startdate.month, startdate.day), datetime.date(enddate.year, enddate.month, enddate.day)):
                    userkey = "%04d%02d" % (single_date.year, single_date.isocalendar()[1])
                    resultdict[userkey] = 0
        elif stateunit == 3:
            if len(result) > 0:
                for orderinfo in result:
                    unit = 1
                    if statedata == 1:
                        unit = 1
                    elif statedata == 2:
                        unit = int(orderinfo["preorder_counts"])
                    elif statedata == 3:
                        unit = float("{0:.2f}".format(float(orderinfo["preorder_fullprice"])))
                    elif statedata == 4:
                        unit = 0 if int(orderinfo["preorder_counts"]) == 0 else float("%.2f" % (float(orderinfo["preorder_fullprice"]) / int(orderinfo["preorder_counts"])))
                    else:
                        unit = 1

                    preorder_paytime = orderinfo["preorder_paytime"]
                    userkey = "%04d%02d" % (preorder_paytime.year, preorder_paytime.month)
                    if resultdict.has_key(userkey):
                        resultdict[userkey] += unit
                    else:
                        resultdict[userkey] = unit
                # resultdict = sorted(resultdict.items())
            else:
                for single_date in self.daterange(datetime.date(startdate.year, startdate.month, startdate.day), datetime.date(enddate.year, enddate.month, enddate.day)):
                    userkey = "%04d%02d" % (single_date.year, single_date.month)
                    resultdict[userkey] = 0
        return resultdict

    def QueryProductsData(self, startdate=None, enddate=None, statedata=1, producttype=0):
        '''statedata: 统计数据，1 - 区域，2 - 类型，3 - 供应商，4 - 录入人
        '''
        statedata = int(statedata)
        producttype = int(producttype)
        if startdate is None or enddate is None:
            enddate = datetime.datetime.now()
            startdate = enddate - timedelta(days=30)
        startdate = str(startdate)
        enddate = str(enddate)
        startdate = datetime.datetime(int(startdate[0:4]), int(startdate[5:7]), int(startdate[8:10]), int(startdate[11:13]), int(startdate[14:16]), int(startdate[17:19]))
        enddate = datetime.datetime(int(enddate[0:4]), int(enddate[5:7]), int(enddate[8:10]), int(enddate[11:13]), int(enddate[14:16]), int(enddate[17:19]))

        sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_inputtime < '%s' AND product_inputtime > '%s'" % (str(enddate), str(startdate))
        if producttype != 0:
            sql += " AND product_type = %s " % producttype
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()

        resultdict = {}
        for productinfo in result:
            thedata = None
            if statedata == 1:
                thedata = productinfo["product_area"]
            elif statedata == 2:
                thedata = productinfo["product_item"]
            elif statedata == 3:
                thedata = productinfo["product_vendorid"]
                vendorinfo = self.QueryUserInfoById(thedata)
                thedata = vendorinfo["user_vendorname"] if vendorinfo is not None else None
            elif statedata == 4:
                thedata = productinfo["product_inputuserid"]
                admininfo = self.QueryUserInfoById(thedata)
                thedata = admininfo["user_nickname"] if admininfo is not None else None
            else:
                thedata = None

            if thedata is None:
                continue
            
            if resultdict.has_key(thedata):
                resultdict[thedata] += 1
            else:
                resultdict[thedata] = 1
        return resultdict

    #####################################################################################################################################

    def AddSwordfight(self, swordfightinfo):
        temp1_name = swordfightinfo["temp1_name"]
        temp1_phonenumber = swordfightinfo["temp1_phonenumber"]
        temp1_email = swordfightinfo["temp1_email"]
        temp1_reserve1 = swordfightinfo["temp1_reserve1"] if swordfightinfo.has_key("temp1_reserve1") else None
        temp1_reserve2 = swordfightinfo["temp1_reserve2"] if swordfightinfo.has_key("temp1_reserve2") else None
        temp1_reserve3 = swordfightinfo["temp1_reserve3"] if swordfightinfo.has_key("temp1_reserve3") else None

        temp1_gender = swordfightinfo["temp1_gender"]
        temp1_age = swordfightinfo["temp1_age"]
        temp1_competition_category = swordfightinfo["temp1_competition_category"]
        temp1_sword_category = swordfightinfo["temp1_sword_category"]
        temp1_team_number = swordfightinfo["temp1_team_number"]
        temp1_type = swordfightinfo["temp1_type"]

        cursor = self.db.cursor()
        value = [ None, temp1_name, temp1_phonenumber, temp1_email, temp1_reserve1, temp1_reserve2, temp1_reserve3, temp1_gender, 
            temp1_age, temp1_competition_category, temp1_sword_category, temp1_team_number, temp1_type ]
        cursor.execute("INSERT INTO temp1_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", value)
        theid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return theid

    def QuerySwordfights(self, startpos, count=settings.LIST_ITEM_PER_PAGE):
        cursor = self.db.cursor()
        if count == 0:
            sql = "SELECT * FROM temp1_table ORDER BY temp1_id DESC"
        else:
            sql = "SELECT * FROM temp1_table ORDER BY temp1_id DESC LIMIT %d, %d" % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QuerySwordfightInfo(self, theid):
        cursor = self.db.cursor()

        sql    = "SELECT * FROM temp1_table WHERE temp1_id = %s LIMIT 1"
        param  = [theid]
        cursor.execute(sql, param)
        result = cursor.fetchone()
        cursor.close()
        return result

    def UpdateSwordfightInfo(self, theid, swordfightinfo):
        pass

    def DeleteSwordfight(self, theid):
        cursor = self.db.cursor()
        sql = "DELETE FROM temp1_table WHERE temp1_id = %s"
        param = [theid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

        self.DeleteSwordfightStaffById(theid)

    def DeleteSwordfightStaffById(self, theid):
        cursor = self.db.cursor()
        sql = "DELETE FROM temp1_staff_table WHERE temp1_staff_extid = %s"
        param = [theid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def AddSwordfightStaff(self, swordfightstaffinfo):
        temp1_staff_extid = swordfightstaffinfo["temp1_staff_extid"]
        temp1_staff_name = swordfightstaffinfo["temp1_staff_name"]
        temp1_staff_age = swordfightstaffinfo["temp1_staff_age"]
        temp1_staff_reserve1 = swordfightstaffinfo["temp1_staff_reserve1"] if swordfightstaffinfo.has_key("temp1_staff_reserve1") else None
        temp1_staff_reserve2 = swordfightstaffinfo["temp1_staff_reserve2"] if swordfightstaffinfo.has_key("temp1_staff_reserve2") else None
        temp1_staff_reserve3 = swordfightstaffinfo["temp1_staff_reserve3"] if swordfightstaffinfo.has_key("temp1_staff_reserve3") else None
        temp1_staff_phonenumber = swordfightstaffinfo["temp1_staff_phonenumber"]

        cursor = self.db.cursor()
        value = [ None, temp1_staff_extid, temp1_staff_name, temp1_staff_age, temp1_staff_reserve1, temp1_staff_reserve2, temp1_staff_reserve3, temp1_staff_phonenumber ]
        cursor.execute("INSERT INTO temp1_staff_table VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", value)
        theid = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return theid

    def QuerySwordfightStaffs(self, swordfightid, startpos, count=settings.LIST_ITEM_PER_PAGE):
        cursor = self.db.cursor()
        if count == 0:
            sql = "SELECT * FROM temp1_staff_table WHERE temp1_staff_extid = %s ORDER BY temp1_staff_id DESC" % swordfightid
        else:
            sql = "SELECT * FROM temp1_staff_table WHERE temp1_staff_extid = %s ORDER BY temp1_staff_id DESC LIMIT %d, %d" % (swordfightid, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QuerySwordfightStaffInfo(self, swordfightstaffid):
        cursor = self.db.cursor()
        sql    = "SELECT * FROM temp1_staff_table WHERE temp1_staff_id = %s LIMIT 1"
        param  = [swordfightstaffid]
        cursor.execute(sql, param)
        result = cursor.fetchone()
        cursor.close()
        return result

    def UpdateSwordfightStaffInfo(self, swordfightid, swordfightstaffinfo):
        pass

    def DeleteSwordfightStaff(self, swordfightstaffid):
        cursor = self.db.cursor()
        sql = "DELETE FROM temp1_staff_table WHERE temp1_staff_id = %s"
        param = [swordfightstaffid]
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def QueryCompetitionProducts(self, startpos, count=settings.LIST_ITEM_PER_PAGE, frontend=0):
        # 获取常规比赛报名的商品列表
        cursor = self.db.cursor()
        sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_type = 4 AND product_traveltype = 5 "
        
        if frontend != 0:
            sql += " AND product_status = 1 AND product_auditstatus = 1 "

        sql += " ORDER BY product_sortweight DESC "

        if count != 0:
            sql += " LIMIT %d, %d " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    #####################################################################################################################################

    def GetUserAvatarUniqueString(self, userid):
        '''获取用户avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_id = %s LIMIT 1"
        param = [userid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result[7] if not self.IsDbUseDictCursor() else result["user_avatar"]
            if avt is None:
                ret = None
            elif len(avt) < 1:
                ret = None
            elif avt == "None" or avt == "NULL":
                ret = None
            else:
                ret = avt
            return ret
        else:
            return None

    def GetArticleAvatarUniqueString(self, articlesid):
        '''获取广告avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM articles_table WHERE articles_id = %s LIMIT 1"
        param = [articlesid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result[6] if not self.IsDbUseDictCursor() else result["articles_avatar"]
            if avt is None:
                ret = None
            elif len(avt) < 1:
                ret = None
            elif avt == "None" or avt == "NULL":
                ret = None
            else:
                ret = avt
            return ret
        else:
            return None

    def GetCategoryAvatarUniqueString(self, categoryid):
        '''获取广告avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM category_table WHERE category_id = %s LIMIT 1"
        param = [ categoryid ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result[6] if not self.IsDbUseDictCursor() else result["category_avatar"]
            if avt is None:
                ret = None
            elif len(avt) < 1:
                ret = None
            elif avt == "None" or avt == "NULL":
                ret = None
            else:
                ret = avt
            return ret
        else:
            return None

    def GetAdsAvatarUniqueString(self, adsid):
        '''获取广告avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM ads_table WHERE ads_id = %s LIMIT 1"
        param = [adsid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result[6] if not self.IsDbUseDictCursor() else result["ads_avatar"]
            if avt is None:
                ret = None
            elif len(avt) < 1:
                ret = None
            elif avt == "None" or avt == "NULL":
                ret = None
            else:
                ret = avt
            return ret
        else:
            return None

    def GetProductAvatarUniqueString(self, productid):
        '''获取商品avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_id = %s LIMIT 1"
        param = [productid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result[5] if not self.IsDbUseDictCursor() else result["product_avatar"]
            if avt and avt.startswith('['):
                try:
                    avt_json = json.loads(avt)
                    return avt_json[0]  # Defaults to the first avatar
                except (TypeError, ValueError):                
                    if avt is None:
                        ret = None
                    elif len(avt) < 1:
                        ret = None
                    elif avt == "None" or avt == "NULL":
                        ret = None
                    else:
                        ret = avt
                    try:
                        a = int(avt)
                    except Exception, e:
                        ret = None
                    return ret
                except IndexError:
                    return None
            else:
                return avt
        else:
            return None

    def GetProductAvatarUniqueStrings(self, productid):
        '''Gets the random generated unique strings for a product'''
        cursor = self.db.cursor()
        sql = "SELECT * FROM product_table WHERE deleteflag = 0 AND product_id = %s LIMIT 1"
        param = [productid]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if not self.IsDbUseDictCursor():
            if result is not None:
                if result[5] and result[5].startswith('['):
                    try:
                        return json.loads(result[5])
                    except (TypeError, ValueError):
                        pass
                else:
                    return [result[5]]
        else:
            if result is not None:
                if result["product_avatar"] and result["product_avatar"].startswith('['):
                    try:
                        return json.loads(result["product_avatar"])
                    except (TypeError, ValueError):
                        pass
                else:
                    return [result["product_avatar"]]
        return []

    def GetUserAvatarPreview(self, userid):
        '''Get the user's preview avatar path.
        '''
        hascustomavatar = True
        userinfo = self.QueryUserInfoById(userid)
        if userinfo is None:
            return '/static/img/avatar/user/default_avatar.jpeg'
        filedir = abspath
        avatarfile = '/static/img/avatar/user/L%s_%s.jpeg' % (userinfo[0] if not self.IsDbUseDictCursor() else userinfo["user_id"], self.GetUserAvatarUniqueString(userid))
        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/user/P%s_%s.jpeg' % (userinfo[0] if not self.IsDbUseDictCursor() else userinfo["user_id"], self.GetUserAvatarUniqueString(userid))
            outfile  = filedir + avatarfile
            if os.path.exists(outfile) == False:
                avatarfile = '/static/img/avatar/user/default_avatar.jpeg'
                hascustomavatar = False
        return (avatarfile, hascustomavatar)

    def GetProductAvatarPreview(self, productid):
        '''Get the user's preview avatar path.
        '''
        hascustomavatar = True
        productinfo = self.QueryProductInfo(productid)
        if productinfo is None:
            return ('/static/img/avatar/product/default_avatar_product.jpeg', False)
        if not self.IsDbUseDictCursor():
            if not productinfo[5]:
                return ('/static/img/avatar/product/default_avatar_product.jpeg', False)
        else:
            if not productinfo["product_avatar"]:
                return ('/static/img/avatar/product/default_avatar_product.jpeg', False)

        if settings.DEBUG_APP == True:
            return ('/static/img/avatar/product/default_avatar_product.jpeg', False)
        filedir = abspath
        avatarfile = '/static/img/avatar/product/P%s_%s.jpeg' % (productid, self.GetProductAvatarUniqueString(productid))
        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            # avatarfile = '/static/img/avatar/product/default_avatar_product.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    def GetProductAvatarPreviews(self, productid):
        '''Get the all product avatar paths'''
        productinfo = self.QueryProductInfo(productid)
        filedir = abspath
        avatars = self.GetProductAvatarUniqueStrings(productid)
        file_tmpl = '/static/img/avatar/product/%s.jpeg'

        for uniquestr in avatars:
            avatarfile = file_tmpl % ('P%s_%s' % (productinfo[0] if not self.IsDbUseDictCursor() else productinfo["product_id"], uniquestr))
            outfile = filedir + avatarfile
            hascustomavatar = os.path.exists(outfile)
            yield (
                avatarfile, # if hascustomavatar else file_tmpl % 'default_avatar_product',
                uniquestr,
                hascustomavatar
            )

    def GetAdsAvatarPreview(self, adsid):
        '''Get the user's preview avatar path.
        '''
        hascustomavatar = True
        adsinfo = self.QueryAdsInfo(adsid)
        if adsinfo is None:
            return '/static/img/avatar/ads/default.jpeg'
        filedir = socket.gethostname() == settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp'
        avatarfile = '/static/img/avatar/ads/P%s_%s.jpeg' % (adsinfo[0] if not self.IsDbUseDictCursor() else adsinfo["ads_id"], self.GetAdsAvatarUniqueString(adsid))

        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarposition = adsinfo[5] if not self.IsDbUseDictCursor() else adsinfo["ads_position"]
            if avatarposition == 2 or avatarposition == 3: # 广告位在首页中部或者底部时使用水平的默认广告图
                avatarfile = '/static/img/avatar/ads/default.jpeg'
            else:
                avatarfile = '/static/img/avatar/ads/default.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    def GetArticleAvatarPreview(self, articlesid):
        '''Get the user's preview avatar path.
        '''
        hascustomavatar = True
        articleinfo = self.QueryArticleInfo(articlesid)
        if articleinfo is None:
            return '/static/img/avatar/article/default.jpeg'
        filedir = socket.gethostname() == settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp'
        avatarfile = '/static/img/avatar/article/P%s_%s.jpeg' % (articleinfo[0] if not self.IsDbUseDictCursor() else articleinfo["articles_id"], self.GetArticleAvatarUniqueString(articlesid))

        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/article/default.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    def GetCategoryAvatarPreview(self, categoryid):
        '''Get the user's preview avatar path.
        '''
        hascustomavatar = True
        categoryinfo = self.QueryCategoryInfo(categoryid)
        if categoryinfo is None:
            return '/static/img/avatar/category/default.jpeg'
        # filedir = socket.gethostname() == settings.SERVER_HOST_NAME and '/home/zhangxh/fivestarcamp' or '/Library/WebServer/Documents/fivestarcamp'
        filedir = abspath
        avatarfile = '/static/img/avatar/category/%s' % self.GetCategoryAvatarUniqueString(categoryid)

        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/category/default.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    #########################################################################################################################################################
    #########################################################################################################################################################
    # -- Promotion --

    def GetPromotion(self, promotion_id, *args, **kwargs):
        ''' Returns a single promotion object'''

        try:
            sql = "select * from promotion_table where promotion_id = %s"
            cursor = self.db.cursor(cursorclass=DictCursor)
            params = [promotion_id]
            cursor.execute(sql, params)
            promotion = cursor.fetchone()
            now = datetime.datetime.now()
            try:
                if now < promotion['promotion_start_date']:
                    promotion['promotion_status'] = -1
                elif now < promotion['promotion_end_date']:
                    promotion['promotion_status'] = 0
                else:
                    promotion['promotion_status'] = 1
            except TypeError:
                promotion['promotion_status'] = -1
            return promotion
        except Exception as e:
            logging.error(e.message)

    def GetPromotionCount(self, *args, **kwargs):
        '''Return the number of promotions (or those that satisfy the filter if given).

        Keyword arguments:
            page: If given, filters the result by the page number.
            name: If given, filters the result by the name.
            date: If given, filters the result by the date.

        Returns:
            int -- the count number.
        '''
        now = datetime.datetime.now()
        name = kwargs.get('name', None)
        status = kwargs.get('status', None)

        sql_io = StringIO()
        params = []
        sql_io.write("select count(1) as count from promotion_table where 1=1")
        if name:
            sql_io.write(
                " and promotion_name like %s"
            )
            params.append("%" + name + "%")
        if status is not None:
            if status == 0:
                sql_io.write(
                    " and %s between promotion_start_date and promotion_end_date"
                )
            elif status == -1:
                sql_io.write(
                    " and promotion_start_date > %s"
                )
            else:
                sql_io.write(
                    " and promotion_end_date < %s"
                )
            params.append(now)
        try:
            cursor = self.db.cursor()
            cursor.execute(sql_io.getvalue(), params)
            count = cursor.fetchone()
            if not self.IsDbUseDictCursor():
                return count[0] if count else 0
            else:
                return count["count"] if count else 0
        except Exception as e:
            logging.error(e.message)
    
    def GetPromotions(self, *args, **kwargs):
        '''Returns a list of promotion rows.

        Keyword arguments:
            page: If given, filters the result by the page number.
            name: If given, filters the result by the name.
            date: If given, filters the result by the date.
        '''
        now = datetime.datetime.now()
        page = kwargs.get('page', None)
        name = kwargs.get('name', None)
        status = kwargs.get('status', None)

        sql_io = StringIO()
        params = []
        sql_io.write("select * from promotion_table where 1=1")
        if name:
            sql_io.write(
                " and promotion_name like %s"
            )
            params.append("%" + name + "%")
        if status is not None:
            if status == 0:
                sql_io.write(
                    " and %s between promotion_start_date and promotion_end_date"
                )
            elif status == -1:
                sql_io.write(
                    " and promotion_start_date > %s"
                )
            else:
                sql_io.write(
                    " and promotion_end_date < %s"
                )
            params.append(now)

        sql_io.write(" order by (case when promotion_start_date > %s then -1 when promotion_end_date > %s then 0 else 1 end)")
        params.extend([now]*2)

        if page:
            page_size = settings.LIST_ITEM_PER_PAGE
            sql_io.write(
                " limit {offset}, {count}".format(
                    offset=page_size * (page - 1),
                    count=page_size
                )
            )

        try:
            cursor = self.db.cursor(cursorclass=DictCursor)
            cursor.execute(sql_io.getvalue(), params)
            promotions = cursor.fetchall()
            now = datetime.datetime.now()

            for promotion in promotions:
                try:
                    if now < promotion['promotion_start_date']:
                        promotion['promotion_status'] = -1
                    elif now < promotion['promotion_end_date']:
                        promotion['promotion_status'] = 0
                    else:
                        promotion['promotion_status'] = 1
                except TypeError:
                    promotion['promotion_status'] = -1
            return promotions
        except Exception as e:
            logging.error(e.message)

    def ExportPromotion(self, promotion_id, *args, **kwargs):
        promotion = self.GetPromotion(promotion_id)
        sql = "select prr.*, u.user_name from promotion_reward_record_table prr left join user_table u on prr.user_id = u.user_id where prr.promotion_id = %s and prr.promotion_reward_type not in ('nothing', 'recommendation') order by prr.promotion_reward_record_time desc"
        try:
            cursor = self.db.cursor(cursorclass=DictCursor)
            params = [promotion_id]
            cursor.execute(sql, params)
            records = cursor.fetchall()
            for record in records:
                record['promotion_name'] = promotion['promotion_name']
            reward_type_mapping = {
                'nothing': '未中奖',
                'gift': '实物奖品',
                'recommendation': '商品推荐',
                'coupon': '优惠券',
            }
            fields = ['奖品编号','用户编号','用户名','活动编号','活动名称','获奖时间','奖品类别','奖品名称',]
            prepared_list = [
                OrderedDict({
                    '奖品编号': item['promotion_reward_id'],
                    '用户编号': item['user_id'],
                    '用户名': item['user_name'],
                    '活动编号': item['promotion_id'],
                    '活动名称': item['promotion_name'],
                    '获奖时间': item['promotion_reward_record_time'],
                    '奖品类别': reward_type_mapping.get(item['promotion_reward_type']),
                    '奖品名称': item['promotion_reward_name']
                }) for item in records
            ]
            import csv
            from io import BytesIO
            bio = BytesIO()
            writer = csv.DictWriter(bio, fieldnames=fields)
            writer.writeheader()
            for record in prepared_list:
                writer.writerow(record)
            bio.seek(0)
            return bio
        except Exception as e:
            logging.error(e.message)

    def SavePromotion(self, obj, *args, **kwargs):
        '''Adds/Updates a promotion object.
        If obj['promotion_id'] is defined, perform an update operation.
        Otherwise, perform an insertion.

        Arguments:
            obj: A promotion object in the form of dictionary.

        Returns:
            0: Success
            1: Nothing to save
            2: Error
        '''
        now = datetime.datetime.now()
        fields = ('promotion_id', 'promotion_name', 'promotion_address', 'promotion_start_date', 'promotion_end_date', 'promotion_default_drawing_times_per_day', 'promotion_max_drawing_times')
        obj = {k: v for k, v in obj.iteritems() if k in fields}
        if obj['promotion_max_drawing_times'] == '':
            obj['promotion_max_drawing_times'] = 0

        promotion_id = obj.get("promotion_id", None)
        # try:
        if promotion_id:
            # Update
            update_keys = [k for k in obj if k != 'promotion_id']
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update promotion_table set {updates} where promotion_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [v for k, v in obj.items() if k != 'promotion_id']
                params.append(promotion_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into promotion_table ({fields}) values ({values})"
            obj['promotion_created_date'] = now
            sql = sql_tmpl.format(
                fields=','.join(k for k in obj.keys()),
                values=','.join('%s' for _ in obj.keys())
            )
            params = [v for v in obj.values()]
            cursor = self.db.cursor()
            cursor.execute(sql, params)
            self.db.commit()
            return 0
        # except Exception as e:
        #     logging.error(e.message)
        #     return 2

    def DeletePromotion(self, promotion_id, *args, **kwargs):
        '''Deletes a promotion by id.

        Arguments:
        promotion_id: The id of the promotion to delete.
        '''
        try:
            sql = "delete from promotion_table where promotion_id = %s"
            cursor = self.db.cursor()
            params = [promotion_id]
            cursor.execute(sql, promotion_id)
            self.db.commit()
        except Exception as e:
            logging.error(e.message)
            return 2

    def GetPromotionReward(self, promotion_reward_id, *args, **kwargs):
        '''Returns the reward by promotion_reward_id.

        Arguments:
        promotion_reward_id: The id of the promotion reward.
        '''
        try:
            sql = "select * from promotion_reward_table where promotion_reward_id = %s"
            cursor = self.db.cursor(cursorclass=DictCursor)
            params = [promotion_reward_id]
            cursor.execute(sql, params)
            promotion_reward = cursor.fetchone()
            return promotion_reward
        except Exception as e:
            logging.error(e.message)

    def GetPromotionRewards(self, promotion_id, *args, **kwargs):
        '''Returns the rewards set for a promotion.

        Arguments:
        promotion_id: The id of the promotion
        '''
        try:
            exclude_nothing = kwargs.get('exclude_nothing', None)
            sql = "select pr.*, count(prr.promotion_reward_id) as promotion_reward_drawn from promotion_reward_table pr left join promotion_reward_record_table prr on pr.promotion_reward_id = prr.promotion_reward_id where pr.promotion_id = %s{exclude_nothing} and pr.promotion_reward_type is not NULL group by pr.promotion_reward_id".format(
                exclude_nothing=(exclude_nothing and " and pr.promotion_reward_type != 'nothing'" or '')
            )
            cursor = self.db.cursor(cursorclass=DictCursor)
            params = [promotion_id]
            cursor.execute(sql, params)
            promotion_rewards = cursor.fetchall()
            return promotion_rewards
        except Exception as e:
            logging.error(e.message)

    def SavePromotionReward(self, obj, *args, **kwargs):  # 
        '''Adds/Updates a promotion reward.
        If promotion_reward['promotion_reward_id'] is set, perform an update operation.
        Otherwise, perform an insertion.
p
        Arguments:
        obj: A promotion reward object in the form of dictionary.

        Returns:
        0: Success
        1: Nothing to update
        2: Error
        3: Promotion does not exist.
        '''

        fields = (
            'promotion_reward_id', 'promotion_id', 'promotion_reward_name',
            'promotion_reward_type', 'promotion_reward_prompt', 'promotion_reward_probability',
            'promotion_reward_max_per_user', 'promotion_reward_max_per_cycle' , 
            'promotion_coupon_type', 'promotion_coupon_amount', 'promotion_coupon_restrictions', 'promotion_coupon_validtime'
        ) #, 'promotion_reward_cycle_period','promotion_reward_date_slot' )

        obj = {k: v for k, v in obj.iteritems() if k in fields}

        if obj["promotion_reward_type"] != 'coupon':
            fields = (
                'promotion_reward_id', 'promotion_id', 'promotion_reward_name',
                'promotion_reward_type', 'promotion_reward_prompt', 'promotion_reward_probability',
                'promotion_reward_max_per_user', 'promotion_reward_max_per_cycle'
            ) #, 'promotion_reward_cycle_period','promotion_reward_date_slot' )
            obj.pop('promotion_coupon_type')
            obj.pop('promotion_coupon_amount')
            obj.pop('promotion_coupon_restrictions')
            obj.pop('promotion_coupon_validtime')
        # else:
        #     restrictions = cgi.escape(obj['promotion_coupon_restrictions'])
        #     obj['promotion_coupon_restrictions'] = restrictions

        #     logging.debug("coupon_restrictions: %s" % obj['promotion_coupon_restrictions'])

        promotion_id = obj.get('promotion_id', None)
        promotion = self.GetPromotion(promotion_id)
        if not promotion:
            return 3

        promotion_reward_id = obj.get("promotion_reward_id", None)
        # try:
        if promotion_reward_id:
            # Update
            update_keys = [k for k in obj if k != 'promotion_reward_id']
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update promotion_reward_table set {updates} where promotion_reward_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [v for k, v in obj.items() if k != 'promotion_reward_id']
                params.append(promotion_reward_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)

                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into promotion_reward_table ({fields}) values ({values})"
            sql = sql_tmpl.format(
                fields=','.join(k for k in obj.keys()),
                values=','.join('%s' for _ in obj.keys())
            )
            params = [v for v in obj.values()]
            cursor = self.db.cursor()

            cursor.execute(sql, params)
            self.db.commit()
            return 0
        # except Exception as e:
        #     logging.error(e.message)
        #     return 2
			
    def _GetPromotionDrawTimesToday(self, promotion_id, user_id=0):
        now = datetime.datetime.now()
        start = datetime.datetime(now.year, now.month, now.day)
        end = start + datetime.timedelta(1)  # One day afterwards.
        sql = "select count(1) as count from promotion_reward_record_table where promotion_id = %s and promotion_reward_record_time between %s and %s"
        params = [promotion_id, start, end]
        
        if user_id != 0:
            sql += " and user_id = %s "
            params.append(user_id)

        cursor = self.db.cursor()
        cursor.execute(sql, params)
        count = cursor.fetchone()
        if not self.IsDbUseDictCursor():
            return count[0] if count else 0
        else:
            return count["count"] if count else 0

    def _GetPromotionDrawTimes(self, promotion_id, user_id=0):
        sql = "select count(1) as count from promotion_reward_record_table where promotion_id = %s"
        params = [promotion_id]
        
        if user_id != 0:
            sql += " and user_id = %s "
            params.append(user_id)

        cursor = self.db.cursor()
        cursor.execute(sql, params)
        count = cursor.fetchone()
        if not self.IsDbUseDictCursor():
            return count[0] if count else 0
        else:
            return count["count"] if count else 0

    def GetPromotionRewardDrawTimes(self, promotion_id):
        sql = "select count(1) as count from promotion_reward_record_table where promotion_id = %s"
        cursor = self.db.cursor()
        params = [promotion_id]
        cursor.execute(sql, params)
        count = cursor.fetchone()
        if not self.IsDbUseDictCursor():
            return count[0] if count else 0
        else:
            return count["count"] if count else 0

    def GetPromotionRewardRecords(self, promotion_id):
        sql = "select * from promotion_reward_record_table where promotion_id = %s" % promotion_id
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def _GetUserPromotionRewardDrawTimes(self, user_id, promotion_reward_id):
        sql = "select count(1) as count from promotion_reward_record_table where promotion_reward_id = %s and user_id = %s"
        cursor = self.db.cursor()
        params = [promotion_reward_id, user_id]
        cursor.execute(sql, params)
        count = cursor.fetchone()
        if not self.IsDbUseDictCursor():
            return count[0] if count else 0
        else:
            return count["count"] if count else 0

    def GetUserPromotionRewardDrawRecords(self, promotion_id, user_id, excludenothing=0):
        sql = "select * from promotion_reward_record_table where promotion_id = %s and user_id = %s"
        if excludenothing == 1:
            sql += " and promotion_reward_type != 'nothing' "
        cursor = self.db.cursor()
        params = [promotion_id, user_id]
        cursor.execute(sql, params)
        result = cursor.fetchall()
        cursor.close()
        return result

    # def _UpdatePromotionRewardDateSlot(self, promotion_reward_id):
    #     now = datetime.datetime.now()
    #     sql = "select promotion_reward_date_slot, promotion_reward_cycle_period from promotion_reward_table where promotion_reward_id = %s"
    #     cursor = self.db.cursor(cursorclass=DictCursor)
    #     params = [promotion_reward_id]
    #     cursor.execute(sql, params)
    #     data = cursor.fetchone()
    #     start = data['promotion_reward_date_slot'] or now
    #     cycle_period = data['promotion_reward_cycle_period']
    #     time_delta = datetime.timedelta(cycle_period)
    #     while start < now - time_delta:
    #         start += time_delta
    #     sql = "update promotion_reward_table set promotion_reward_date_slot = %s where promotion_reward_id = %s"
    #     params = [start, promotion_reward_id]
    #     cursor.execute(sql, params)
    #     self.db.commit()
    #     return (start, cycle_period)

    # def _GetRewardDrawnTimesWithinPeriod(self, promotion_reward_id, start, end):
    #     sql = "select count(1) as count from promotion_reward_record_table where promotion_reward_id = %s and promotion_reward_record_time between %s and %s"
    #     params = [promotion_reward_id, start, end]
    #     cursor = self.db.cursor()
    #     cursor.execute(sql, params)
    #     count = cursor.fetchone()
    #     if not self.IsDbUseDictCursor():
    #         return count[0] if count else 0
    #     else:
    #         return count["count"] if count else 0

    def _GetRewardDrawnTimes(self, promotion_reward_id):
        sql = "select count(1) as count from promotion_reward_record_table where promotion_reward_id = %s"
        params = [promotion_reward_id]
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        count = cursor.fetchone()
        if not self.IsDbUseDictCursor():
            return count[0] if count else 0
        else:
            return count["count"] if count else 0

    def _RecordPromotionRewardDrawing(self, user_id, promotion, promotion_reward):
        now = datetime.datetime.now()
        sql = "insert into promotion_reward_record_table (user_id, promotion_id, promotion_reward_id, promotion_reward_record_time, promotion_name, promotion_reward_type, promotion_reward_name) values (%s, %s, %s, %s, %s, %s, %s)"
        params = [user_id, promotion['promotion_id'], promotion_reward['promotion_reward_id'], now, promotion['promotion_name'], promotion_reward['promotion_reward_type'], promotion_reward['promotion_reward_name']]
        try:
            cursor = self.db.cursor()
            cursor.execute(sql, params)
            self.db.commit()
        except Exception as e:
            print(e)
            logging.error(e)

    # def _TryIncrementPromotionAttendees(self, user_id, promotion_id):
    #     sql = "select count(1) as count from promotion_reward_record_table where promotion_id = %s and user_id = %s"
    #     params = [promotion_id, user_id]
    #     try:
    #         cursor = self.db.cursor()
    #         cursor.execute(sql, params)
    #         count = cursor.fetchone()
    #         if not self.IsDbUseDictCursor():
    #             count = count[0] if count else 0
    #         else:
    #             count = count["count"] if count else 0
    #         if count == 0:
    #             sql = "update promotion_table set promotion_attendees = if(promotion_attendees is NULL, 1, promotion_attendees + 1) where promotion_id = %s"
    #             params = [promotion_id]
    #             cursor = self.db.cursor()
    #             cursor.execute(sql, params)
    #             self.db.commit()
    #     except Exception as e:
    #         print(e)
    #         logging.error(e)

    def WeightedChoice(self, choices):
        '''加权随机
            choices: 参数列表，格式：[("iPhone 6 Plus", 1), ("A box of Chocolate", 10), ("A Pencil", 33), ("Free Course of Training", 10), ("iPod Touch", 6), ("Thank you!", 40)]
        '''
        total = sum(w for c, w in choices)
        r = random.uniform(0, total)
        upto = 0
        for c, w in choices:
            if upto + w >= r:
                return c
            upto += w
        assert False, "Shouldn't get here"

    def TestWeightedChoice(self):
        total = 0
        maxcount = 500000
        for i in range(maxcount):
            ret = self.WeightedChoice([("iPhone 6 Plus", 100), ("A box of Chocolate", 1000), ("A Pencil", 3300), ("Free Course of Training", 1000), ("iPod Touch", 600), ("Thank you!", 4000)])
            if ret == "iPhone 6 Plus":
                total += 1
                print "I got iPhone 6 Plus!"
        print "The iPhone 6 Plus probability is: %.2f%%" % (float(float(total) / float(maxcount)) * 100)

    # def _WeighedChoice(self, choices):
    #     '''Pick a weighed random choice by probability.
    #     Arguments:
    #         choices: a list of 2-tuples of choice and weight, e.g.
    #                  [('a', 1), ('b', 2), ('c', 3)]
    #     '''
    #     total = sum(w for c, w in choices)
    #     r = random.uniform(0, total)
    #     upto = 0
    #     for c, w in choices:
    #         if upto + w >= r:
    #             return c
    #         upto += w
    #     assert False, "Shouldn't get here"

    def PromotionDraw(self, promotion_id, user_id, *args, **kwargs):
        '''User draws from rewards. Returns a result.
            Arguments:
                promotion_id: The id of the promotion
                user_id: The user id of promotion draw
            kwargs:
                trypromotiondraw: 1 / 0     - Try promotion draw, does not perform the drawing operation.

            Returns:
                A 4-key dict:
                {"result": result, "reward_type": reward_type, "reward_name": reward_name, "reward_prompt": reward_prompt}
                if the drawing is successful;
                or a 2-key dict:
                {"result": result, "messsage": message}
                if the drawing fails.

                Where result is:
                 2 -- Try Promotion Draw Success ( The user can perform a drawing operation. )
                 1 -- Successful
                 0 -- Got a reward which exceeded max drawing time
                -1 -- Not found
                -2 -- Promotion not in active period.
                -3 -- Drawing times exceeded.
                -4 -- No rewards.
                -5 -- Total promotion drawing times exceeded
        '''
        def _tuple_to_dict(*result):
            if result is None:
                return None
            if result[0] == 1:
                obj = { k: v for k, v in result[1].iteritems() }
                obj["result"] = str(1)
                return obj
                # return {"result": str(1), "reward_type": result[1], "reward_name": result[2], "reward_prompt": result[3]}
            else:
                return {"result": str(result[0]), "message": result[1]}

        db = DbHelper()
        promotion = db.GetPromotion(promotion_id)
        if not promotion:
            return _tuple_to_dict(-1, "Not found")
        if promotion['promotion_status'] != 0:
            return _tuple_to_dict(-2, "Not in active period")

        drawn_today = self._GetPromotionDrawTimesToday(promotion_id, user_id)
        if drawn_today >= promotion['promotion_default_drawing_times_per_day'] or 0:
            return _tuple_to_dict(-3, "Promotion drawing times for today exceeded")

        if promotion['promotion_max_drawing_times'] != 0 and promotion['promotion_max_drawing_times'] is not None:
            drawn_total = self._GetPromotionDrawTimes(promotion_id, user_id)
            if drawn_total >= promotion['promotion_max_drawing_times']:
                return _tuple_to_dict(-5, "Total promotion drawing times exceeded")

        rewards = db.GetPromotionRewards(promotion_id)
        choices = [(k, k['promotion_reward_probability']) for k in rewards]
        if not choices:
            return _tuple_to_dict(-4, 'No available rewards')

        # Max per cycle drawing limit.
        # Update the date_slot first.
        for idx in range(len(choices) - 1, -1, -1):
            choice = choices[idx][0]
            # date_slot, cycle_period = self._UpdatePromotionRewardDateSlot(choice['promotion_reward_id'])
            # start, end = date_slot, date_slot + datetime.timedelta(cycle_period)
            mpc = choice['promotion_reward_max_per_cycle']
            if mpc > 0:
                # dr = self._GetRewardDrawnTimesWithinPeriod(choice['promotion_reward_id'], start, end)
                dr = self._GetRewardDrawnTimes(choice['promotion_reward_id'])
                if dr >= mpc:
                    # return (-3, "Reward cycle max drawing times exceeded")
                    del choices[idx]
        if not choices:
            return _tuple_to_dict(-4, 'No available rewards')

        if kwargs['trypromotiondraw'] == 1:
            return _tuple_to_dict(2, 'Try promotion draw success')
        else:
            choice = self.WeightedChoice(choices)
            
            # Max per user drawing limit.
            mpu = choice['promotion_reward_max_per_user']
            if mpu > 0:
                user_drawing_count = self._GetUserPromotionRewardDrawTimes(
                    user_id, choice['promotion_reward_id']
                )
                if user_drawing_count >= mpu:
                    return _tuple_to_dict(0, "Reward user max drawing times exceeded")

            # Record it!
            # self._TryIncrementPromotionAttendees(user_id, promotion_id)
            self._RecordPromotionRewardDrawing(user_id, promotion, choice)

            # if user got a 'coupon', generate a coupon for him / her
            if choice['promotion_reward_type'] == 'coupon':
                coupon_validtime = str(choice['promotion_coupon_validtime'])
                coupon_type = choice['promotion_coupon_type']
                coupon_amount = choice['promotion_coupon_amount']
                coupon_restrictions = choice['promotion_coupon_restrictions']

                validdays = datetime.date(int(coupon_validtime[0:4]), int(coupon_validtime[5:7]), int(coupon_validtime[8:10])) - datetime.date.today()
                validdays = validdays.days

                self.AddCoupon({ "coupon_userid" : user_id, "coupon_amount" : coupon_amount, "coupon_restrictions" : coupon_restrictions, 
                    "coupon_source" : 9, "coupon_type" : coupon_type }, couponvaliddays=validdays)

            return _tuple_to_dict(1, choice)
            # return _tuple_to_dict(1, choice['promotion_reward_type'], choice['promotion_reward_name'], choice['promotion_reward_prompt'])

    def DeletePromotionReward(self, promotion_reward_id, *args, **kwargs):
        '''Deletes a promotion reward by id.

        Arguments:
        promotion_reward_id: The id of the promotion reward to delete.
        '''
        try:
            sql = "delete from promotion_reward_table where promotion_reward_id = %s"
            cursor = self.db.cursor()
            params = [promotion_reward_id]
            cursor.execute(sql, params)
            self.db.commit()
        except Exception as e:
            logging.error(e.message)
            return 2

    def GenerateRandomProductRecommendation(self, product_type):
        '''Generates a random product recommendation based on the product_type.

        Arguments:
        product_type: An integer representing the product type. (See the doc for further details.)

        Returns:
        A 2-tuple (product_id, product_name)
        '''
        sql = "select product_id, product_name from product_table where deleteflag = 0 AND product_type = %s order by rand() limit 1"
        cursor = self.db.cursor(cursorclass=DictCursor)
        params = [product_type]
        cursor.execute(sql, params)
        row = cursor.fetchone()
        if not row:
            return (0, None)
        else:
            return (row['product_id'], row['product_name'])

    def GetProductName(self, product_id):
        '''Gets product name by product id.

        Arguments:
        product_id:

        Returns:
        string -- product name
        '''
        sql = "select product_name from product_table where deleteflag = 0 AND product_id = %s" % product_id
        cursor = self.db.cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        if self.IsDbUseDictCursor():
            return row['product_name'] if row else None
        else:
            if self.IsDbUseDictCursor():
                return row['product_name'] if row else None
            else:
                return row[0] if row else None

    #####################################################################################################################################

    def QueryActivityInfo(self, activity_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM activity_table WHERE activity_id = %s LIMIT 1"
        param = [ activity_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryActivity(self, startpos, count=settings.LIST_ITEM_PER_PAGE, couldbuy=-1, sort=1, categoryid=0):
        # couldbuy: 活动对应商品是否可以购买，1，可以购买，0，不可以购买, -1 ，包括全部可买与不可买
        # sort: 排序方式，1 - 智能排序（权重），2 - 价格排序，3 - 时间排序
        cursor = self.db.cursor()
        sql = "SELECT * FROM activity_table WHERE 1 = 1 "
        if couldbuy == 1:
            sql += " AND activity_productid != 0 "
        elif couldbuy == 0:
            sql += " AND activity_productid = 0 "

        if categoryid != 0:
            sql += " AND activity_categoryid = %s " % categoryid
        
        if sort == 1:
            sql += " ORDER BY activity_sortweight DESC "
        elif sort == 2:
            sql += " ORDER BY activity_price DESC "
        elif sort == 3:
            sql += " ORDER BY activity_begintime DESC "
        else:
            sql += " ORDER BY activity_id DESC "
        
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SaveActivity(self, obj, *args, **kwargs):
        fields = ('activity_id', 'activity_productid', 'activity_name', 'activity_status', 'activity_categoryid', 'activity_mark', 'activity_price', 'activity_begintime', 'activity_endtime', 'activity_sortweight', 'activity_avatar', 'activity_description')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        activity_id = obj.get("activity_id", None)
        if activity_id:
            # Update
            update_keys = [ k for k in obj if k != 'activity_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update activity_table set {updates} where activity_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'activity_id' ]
                params.append(activity_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into activity_table ({fields}) values ({values})"
            # obj['user_registertime'] = datetime.datetime.now()
            # obj['deleteflag'] = 0
            sql = sql_tmpl.format(
                fields=','.join(k for k in obj.keys()),
                values=','.join('%s' for _ in obj.keys())
            )
            params = [ v for v in obj.values() ]
            cursor = self.db.cursor()
            cursor.execute(sql, params)
            theid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return theid

    def DeleteActivity(self, activity_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM activity_table WHERE activity_id = %s" % activity_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

        self.DeleteSubjectObjectByObjectId(subject_object_type=2, subject_object_objectid=activity_id)

    def GetActivityAvatarUniqueString(self, activity_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM activity_table WHERE activity_id = %s LIMIT 1"
        param = [ activity_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["activity_avatar"]
            if avt is None:
                ret = None
            elif len(avt) < 1:
                ret = None
            elif avt == "None" or avt == "NULL":
                ret = None
            else:
                ret = avt
            return ret
        else:
            return None

    def GetActivityAvatarPreview(self, activity_id):
        hascustomavatar = True
        activityinfo = self.QueryActivityInfo(activity_id)
        if activityinfo is None:
            return ('/static/img/avatar/activity/default.jpeg', False)

        filedir = abspath
        avatarfile = '/static/img/avatar/activity/P%s_%s.jpeg' % (activityinfo["activity_id"], self.GetActivityAvatarUniqueString(activity_id))

        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/activity/default.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    #########################################################################################################################################################

    def QuerySubjectInfo(self, subject_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM subject_table WHERE subject_id = %s LIMIT 1"
        param = [ subject_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QuerySubject(self, startpos, count=settings.LIST_ITEM_PER_PAGE):
        cursor = self.db.cursor()
        sql = "SELECT * FROM subject_table WHERE 1 = 1 "
        sql += " ORDER BY subject_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SaveSubject(self, obj, *args, **kwargs):
        fields = ('subject_id', 'subject_name', 'subject_status', 'subject_date', 'subject_sortweight', 'subject_avatar')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        subject_id = obj.get("subject_id", None)
        if subject_id:
            # Update
            update_keys = [ k for k in obj if k != 'subject_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update subject_table set {updates} where subject_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'subject_id' ]
                params.append(subject_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into subject_table ({fields}) values ({values})"
            # obj['user_registertime'] = datetime.datetime.now()
            # obj['deleteflag'] = 0
            sql = sql_tmpl.format(
                fields=','.join(k for k in obj.keys()),
                values=','.join('%s' for _ in obj.keys())
            )
            params = [ v for v in obj.values() ]
            cursor = self.db.cursor()
            cursor.execute(sql, params)
            theid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return theid

    def DeleteSubject(self, subject_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM subject_table WHERE subject_id = %s" % subject_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

        self.DeleteSubjectObjectBySubjectId(subject_id)

    def GetSubjectAvatarUniqueString(self, subject_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM subject_table WHERE subject_id = %s LIMIT 1"
        param = [ subject_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["subject_avatar"]
            if avt is None:
                ret = None
            elif len(avt) < 1:
                ret = None
            elif avt == "None" or avt == "NULL":
                ret = None
            else:
                ret = avt
            return ret
        else:
            return None

    def GetSubjectAvatarPreview(self, subject_id):
        hascustomavatar = True
        subjectinfo = self.QuerySubjectInfo(subject_id)
        if subjectinfo is None:
            return ('/static/img/avatar/subject/default.jpeg', False)

        filedir = abspath
        avatarfile = '/static/img/avatar/subject/P%s_%s.jpeg' % (subjectinfo["subject_id"], self.GetSubjectAvatarUniqueString(subject_id))

        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/subject/default.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    #########################################################################################################################################################

    def QuerySubjectObjectInfo(self, subject_object_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM subject_object_table WHERE subject_object_id = %s LIMIT 1"
        param = [ subject_object_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QuerySubjectObject(self, startpos, count=settings.LIST_ITEM_PER_PAGE, subject_id=0, frontend=0):
        cursor = self.db.cursor()
        sql = "SELECT * FROM subject_object_table WHERE 1 = 1 "
        if subject_id != 0:
            sql += " AND subject_object_subjectid = %s " % subject_id
        if frontend != 0:
            sql += " AND ((subject_object_objectid IN ( SELECT product_id FROM product_table WHERE product_status = 1 AND product_auditstatus = 1 ) AND subject_object_type = 1) OR (subject_object_objectid IN ( SELECT activity_id FROM activity_table WHERE activity_status = 1 ) AND subject_object_type = 2)) "
        sql += " ORDER BY subject_object_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SaveSubjectObject(self, obj, *args, **kwargs):
        fields = ('subject_object_id', 'subject_object_subjectid', 'subject_object_type', 'subject_object_objectid', 'subject_object_description', 'subject_object_sortweight')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        subject_object_id = obj.get("subject_object_id", None)
        if subject_object_id:
            # Update
            update_keys = [ k for k in obj if k != 'subject_object_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update subject_object_table set {updates} where subject_object_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'subject_object_id' ]
                params.append(subject_object_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into subject_object_table ({fields}) values ({values})"
            # obj['user_registertime'] = datetime.datetime.now()
            # obj['deleteflag'] = 0
            sql = sql_tmpl.format(
                fields=','.join(k for k in obj.keys()),
                values=','.join('%s' for _ in obj.keys())
            )
            params = [ v for v in obj.values() ]
            cursor = self.db.cursor()
            cursor.execute(sql, params)
            theid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return theid

    def DeleteSubjectObject(self, subject_object_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM subject_object_table WHERE subject_object_id = %s" % subject_object_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def DeleteSubjectObjectByObjectId(self, subject_object_type, subject_object_objectid):
        cursor = self.db.cursor()
        sql = "DELETE FROM subject_object_table WHERE subject_object_type = %s AND subject_object_objectid = %s" % (subject_object_type, subject_object_objectid)
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def DeleteSubjectObjectBySubjectId(self, subject_object_subjectid):
        cursor = self.db.cursor()
        sql = "DELETE FROM subject_object_table WHERE subject_object_subjectid = %s" % subject_object_subjectid
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    #########################################################################################################################################################

    def GetCompetition(self, competition_id, *args, **kwargs):
        '''Returns a single competition object'''
        try:
            sql = "select * from competition_table where competition_id = %s"
            cursor = self.db.cursor(cursorclass=DictCursor)
            params = [competition_id]
            cursor.execute(sql, params)
            competition = cursor.fetchone()
            now = datetime.datetime.now()
            try:
                if now < competition['competition_start_time']:
                    competition['competition_status'] = -1
                elif now < competition['competition_end_time']:
                    competition['competition_status'] = 0
                else:
                    competition['competition_status'] = 1
            except TypeError:
                competition['competition_status'] = -1
            # registered_count
            # sql = "select count(1) from competition_registration_table where competition_id = %s"
            sql = "select * from competition_registration_form_data_table fd where competition_id = %s group by fd.competition_registration_form_registration_id"
            cursor.execute(sql, [competition_id])
            rows = cursor.fetchall()
            competition['competition_registered_count'] = len(rows)

            return competition
        except Exception as e:
            logging.error(e.message)

    def GetCompetitionByProductId(self, product_id):
        '''Returns a single competition object by its product_id'''
        try:
            productinfo = self.QueryProductInfo(product_id)
            competition_id = productinfo[30] if not self.IsDbUseDictCursor() else productinfo["product_traveldays"]

            product_eventbegintime = str(productinfo[31] if not self.IsDbUseDictCursor() else productinfo["product_eventbegintime"])
            product_eventendtime = str(productinfo[32] if not self.IsDbUseDictCursor() else productinfo["product_eventendtime"])
            product_eventbegintime = datetime.datetime(int(product_eventbegintime[0:4]), int(product_eventbegintime[5:7]), int(product_eventbegintime[8:10]), 0, 0, 0)
            product_eventendtime = datetime.datetime(int(product_eventendtime[0:4]), int(product_eventendtime[5:7]), int(product_eventendtime[8:10]), 0, 0, 0)

            if not competition_id:
                return None
            sql = "select * from competition_table where competition_id = %s"
            cursor = self.db.cursor(cursorclass=DictCursor)
            params = [competition_id]
            cursor.execute(sql, params)
            competition = cursor.fetchone()
            now = datetime.datetime.now()
            try:
                if now < product_eventbegintime:
                    competition['competition_status'] = -1
                elif now < product_eventendtime:
                    competition['competition_status'] = 0
                else:
                    competition['competition_status'] = 1
            except TypeError:
                competition['competition_status'] = -1

            return competition
        except Exception as e:
            logging.error(e.message)

    def GetCompetitions(self, *args, **kwargs):
        '''Returns a list of competition rows.

        Keyword arguments:
            page: If given, filters the result by page number.
            name: If given, filters the result by name.
            prod_status: If given, filters the result by production status.
            status: If given, filters the result by competition status.
        '''
        now = datetime.datetime.now()
        page = kwargs.get('page', None)
        name = kwargs.get('name', None)
        prod_status = kwargs.get('prod_status', None)
        status = kwargs.get('status', None)
        startpos = kwargs.get("startpos", None)
        count = kwargs.get("count", settings.LIST_ITEM_PER_PAGE)

        sql_io = StringIO()
        params = []
        sql_io.write("select c.*, count(fd.competition_registration_form_registration_id) as competition_registered_count from competition_table as c")
        sql_io.write(" left join (select * from competition_registration_form_data_table _fd group by _fd.competition_registration_form_registration_id) fd on c.competition_id = fd.competition_id")
        sql_io.write(" where 1=1")
        if name:
            sql_io.write(
                " and competition_name like %s"
            )
            params.append("%" + name + "%")
        if prod_status is not None:
            sql_io.write(" and competition_prod_status = %s")
            params.append(prod_status)

        if status is not None:
            if status == 0:
                sql_io.write(
                    " and %s between competition_start_time and competition_end_time"
                )
            elif status == -1:
                sql_io.write(
                    " and competition_start_time > %s"
                )
            else:
                sql_io.write(
                    " and competition_end_time < %s"
                )
            params.append(now)
        sql_io.write(" group by c.competition_id")
        sql_io.write(" order by (case when competition_start_time > %s then -1 when competition_end_time > %s then 0 else 1 end)")
        params.extend([now]*2)

        if startpos is not None:
            if count != 0:
                sql_io.write(" LIMIT %d, %d " % (startpos, count))
        else:
            if page:
                page_size = settings.LIST_ITEM_PER_PAGE
                sql_io.write(
                    " limit {offset}, {count}".format(
                        offset=page_size * (page - 1),
                        count=page_size
                    )
                )

        try:
            cursor = self.db.cursor(cursorclass=DictCursor)
            cursor.execute(sql_io.getvalue(), params)
            competitions = cursor.fetchall()
            now = datetime.datetime.now()

            for competition in competitions:
                try:
                    if now < competition['competition_start_time']:
                        competition['competition_status'] = -1
                    elif now < competition['competition_end_time']:
                        competition['competition_status'] = 0
                    else:
                        competition['competition_status'] = 1
                except TypeError:
                    competition['competition_status'] = -1
            return competitions
        except Exception as e:
            logging.error(e.message)

    
    def GetCompetitionCount(self, *args, **kwargs):
        '''Return the number of competitions (or those that satisfy the filter if given).

        Keyword arguments:
            page: If given, filters the result by page number.
            name: If given, filters the result by name.
            prod_status: If given, filters the result by production status.
            status: If given, filters the result by status.

        Returns:
            int -- the count number.
        '''
        now = datetime.datetime.now()
        name = kwargs.get('name', None)
        prod_status = kwargs.get('prod_status', None)
        status = kwargs.get('status', None)

        sql_io = StringIO()
        params = []
        sql_io.write("select count(1) as count from competition_table where 1=1")
        if name:
            sql_io.write(
                " and competition_name like %s"
            )
            params.append("%" + name + "%")
        if prod_status is not None:
            sql_io.write(
                " and competition_prod_status = %s"
            )
            params.append(prod_status)
        if status is not None:
            if status == 0:
                sql_io.write(
                    " and %s between competition_start_time and competition_end_time"
                )
            elif status == -1:
                sql_io.write(
                    " and competition_start_time > %s"
                )
            else:
                sql_io.write(
                    " and competition_end_time < %s"
                )
            params.append(now)
        try:
            cursor = self.db.cursor()
            cursor.execute(sql_io.getvalue(), params)
            count = cursor.fetchone()
            if not self.IsDbUseDictCursor():
                return count[0] if count else 0
            else:
                return count["count"] if count else 0
        except Exception as e:
            logging.error(e.message)


    def SaveCompetition(self, obj, *args, **kwargs):
        '''Adds/Updates a competition object.
        If obj['competition_id'] is defined, perform an update operation.
        Otherwise, perform an insertion.

        P.S. Each competition has a bound product. Saving a competition will also save its corresponding product.

        Arguments:
            obj: A competition object in the form of dictionary.

        Returns:
            0: Success
            1: Nothing to save
            2: Error
        '''
        now = datetime.datetime.now()
        fields = ('competition_id', 'competition_name', 'competition_registration_start_time', 'competition_registration_end_time', 'competition_start_time', 'competition_end_time', 'competition_location', 'competition_registration_fee', 'competition_stock', 'competition_registration_players_lower', 'competition_registration_players_upper', 'competition_intro', 'competition_mustknow', 'competition_prod_status', 'competition_registration_form_id')
        images = obj.pop('competition_images', [])
        obj = {k: v for k, v in obj.iteritems() if k in fields}

        competition_id = obj.get("competition_id", None)
        # try:
        if competition_id:
            # Update
            competition = self.GetCompetition(competition_id)
            product_id = competition['competition_product_id']
            product = {
                'product_vendorid': 0,
                'product_name': obj['competition_name'],
                'product_type': 9,  # External product types.
                'product_item': '比赛报名',
                'product_status': 1
            }
            if not product_id:
                self.AddProduct(product)
            else:
                self.UpdateProductInfo(product_id, product)
            
            update_keys = [k for k in obj if k != 'competition_id']
            if update_keys:
                # Prepare for update
                update_keys.append('competition_product_id')
                sql_tmpl = r"update competition_table set {updates} where competition_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [v for k, v in obj.items() if k != 'competition_id']
                params.append(product_id)
                params.append(competition_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)

                self.db.commit()
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            product = {
                'product_vendorid': 0,
                'product_name': obj['competition_name'],
                'product_type': 9,
                'product_item': '比赛报名',
                'product_status': 1
            }

            product_id = self.AddProduct(product)

            sql_tmpl = r"insert into competition_table ({fields}) values ({values})"
            obj['competition_created_date'] = now
            fields = [k for k in obj.keys()]
            fields.append('competition_product_id')
            values = ['%s'] * len(obj.keys())
            values.append('%s')
            sql = sql_tmpl.format(
                fields=','.join(fields),
                values=','.join(values),
            )
            params = [v for v in obj.values()] + [product_id]
            cursor = self.db.cursor()
            cursor.execute(sql, params)
            self.db.commit()
            competition_id = cursor.lastrowid

        basedir = os.path.join(abspath, 'static/img/avatar')
        tempdir = os.path.join(basedir, 'temp')
        realdir = os.path.join(basedir, 'competition')
        new_images_json = []
        for image in images:
            if image.startswith('NEW'):
                _, uniquestring, img_partial_name = image.split(':')
                # Move the temporary file to a permanent product image file.
                new_unique_string = self.getuniquestring()
                outfile  = 'C%s_%s.jpeg' % (competition_id, new_unique_string)
                os.rename(
                    os.path.join(tempdir, img_partial_name),
                    os.path.join(realdir, outfile)
                )
                new_images_json.append(new_unique_string)
            else:
                new_images_json.append(image)
        sql = r"update competition_table set competition_images = %s where competition_id = %s"
        images = json.dumps(new_images_json)
        cursor.execute(sql, [images, competition_id])
        self.db.commit()

        return 0
        # except Exception as e:
        #     logging.error(e.message)
        #     return 2

    def DeleteCompetition(self, competition_id):
        competition = self.GetCompetition(competition_id)
        cursor = self.db.cursor()
        sql = "delete from competition_registration_form_data_table where competition_id = %s"
        cursor.execute(sql, [competition_id])
        sql = "delete from competition_registration_table where competition_id = %s"
        cursor.execute(sql, [competition_id])
        sql = "delete from competition_table where competition_id = %s"
        cursor = self.db.cursor()
        cursor.execute(sql, [competition_id])
        self.db.commit()
        return 0

    def GetUserDefinedCompetitionRegistrationForms(self, user_id):
        sql = "select * from competition_registration_form_table"
        cursor = self.db.cursor(cursorclass=DictCursor)
        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows

    def GetCompetitionRegistrationForms(self):
        sql = "select * from competition_registration_form_table"
        cursor = self.db.cursor(cursorclass=DictCursor)
        cursor.execute(sql)
        rows = cursor.fetchall()
        return rows        

    def SaveCompetitionRegistrationForm(self, user_id, obj):
        # try:
        # Step 1: insert into competition_registration_form_table
        obj = obj.get('form')
        if not obj:
            return (0, None)
        
        form_obj = {
            'competition_registration_form_id': obj.get('id'),
            'competition_registration_form_name': obj.get('name'),
            'user_id': user_id
        }
        competition_registration_form_id = form_obj['competition_registration_form_id']
        if competition_registration_form_id:
            update_keys = [k for k in form_obj if k != 'competition_registration_form_id']
            sql_tmpl = r"update competition_registration_form_table set {updates} where competition_registration_form_id = %s"
            updates = ','.join("{}=%s".format(k) for k in update_keys)
            sql = sql_tmpl.format(
                updates=update,
            )
            params = [v for k, v in form_obj.items() if k != 'competition_registration_form_id']
            params.append(competition_registration_form_id)
            cursor = self.db.cursor()
            cursor.execute(sql, params)
        else:
            sql_tmpl = r"insert into competition_registration_form_table ({fields}) values ({values})"
            sql = sql_tmpl.format(
                fields=','.join(k for k in form_obj.keys()),
                values=','.join('%s' for _ in form_obj.keys())
            )
            params = [v for v in form_obj.values()]
            cursor = self.db.cursor()
            cursor.execute(sql, params)
            

        # Step 2: insert into competition_registration_form_field_table
        # Get the last inserted id first.
        competition_registration_form_id = cursor.lastrowid
        if 'fields' in obj.keys():
            fields = obj.get('fields', [])
            existing_ids = [field.get('field_id') for field in fields if field.get('field_id')]
            if existing_ids:
                sql_tmpl = r"delete from competition_registration_form_field_table where competition_registration_form_field_id in ({ids})"
                sql = sql_tmpl.format(ids=','.join(existing_ids))
                cursor.execute(sql)

            # Lemme try to perform an upsert.
            for idx, field in enumerate(fields):
                field_obj = OrderedDict({
                    'competition_registration_form_field_name': field.get('name'),
                    'competition_registration_form_field_description': field.get('description'),
                    'competition_registration_form_field_type': field.get('type'),
                    'competition_registration_form_field_is_mandatory': field.get('mandatory', False),
                    'competition_registration_form_field_is_required': field.get('required', False),
                    'competition_registration_form_field_extra': field.get('extra'),
                    'competition_registration_form_field_index': idx,
                    'competition_registration_form_field_id': field.get('field_id'),
                    'competition_registration_form_id': competition_registration_form_id
                })
                update_keys = [k for k in field_obj if k not in ('competition_registration_form_field_id',)]
                sql_tmpl = r"insert into competition_registration_form_field_table ({fields}) values ({values}) on duplicate key update {updates}"
                sql = sql_tmpl.format(
                    fields=','.join(k for k in field_obj.keys()),
                    values=','.join('%s' for _ in field_obj.keys()),
                    updates=','.join("{}=%s".format(k) for k in update_keys)
                )
                params = list(field_obj.values()) + [v for k, v in field_obj.items() if k in update_keys]
                cursor.execute(sql, params)

        self.db.commit()
        return (1, {
            'id': competition_registration_form_id,
            'name': form_obj['competition_registration_form_name']
        })
        # except Exception as e:
        #     logging.error(e.message)
        #     return (2, None)

    def GetCompetitionRegistrationForm(self, registration_form_id):
        try:
            cursor = self.db.cursor(cursorclass=DictCursor)
            sql = "select * from competition_registration_form_table where competition_registration_form_id = %s"
            params = [registration_form_id]
            cursor.execute(sql, params)
            registration_form = cursor.fetchone()
            if not registration_form:
                return (-1, 'not found')
            sql = "select * from competition_registration_form_field_table where competition_registration_form_id = %s"
            params = [registration_form_id]
            cursor.execute(sql, params)
            registration_form_fields = cursor.fetchall()
            return (1, registration_form, registration_form_fields)
        except Exception as e:
            logging.error(e.message)
            return (2, 'unknown error')

    def GetCompetitionRegistrationFormByCompetitionId(self, competition_id):
        '''Returns a competition registration form with its field definitions.

        Arguments:
        user_id: xxx
        registration_form_id: xxx


        Returns:
        A 3-tuple (1, registration_form_info, field_info_list) on success,
        or 2-tuple (error_code, message) on error
        '''
        try:
            cursor = self.db.cursor(cursorclass=DictCursor)
            sql = "select competition_registration_form_id from competition_table where competition_id = %s"
            params = [competition_id]
            cursor.execute(sql, params)
            row = cursor.fetchone()
            if not row:
                return (-1, 'not found')
            registration_form_id = row['competition_registration_form_id']
            sql = "select * from competition_registration_form_table where competition_registration_form_id = %s"
            params = [registration_form_id]
            cursor.execute(sql, params)
            registration_form = cursor.fetchone()
            if not registration_form:
                return (-1, 'not found')
            sql = "select * from competition_registration_form_field_table where competition_registration_form_id = %s"
            params = [registration_form_id]
            cursor.execute(sql, params)
            registration_form_fields = cursor.fetchall()
            return (1, registration_form, registration_form_fields)
        except Exception as e:
            logging.error(e.message)
            return (2, 'unknown error')

    def DeleteCompetitionRegistrationForm(self, registration_form_id):
        sql = 'delete from competition_registration_form_table where competition_registration_form_id = %s'
        cursor = self.db.cursor()
        cursor.execute(sql, [registration_form_id])
        self.db.commit()
        return 1

    def CompetitionRegister(self, user_id, competition_id, player_forms):
        playerempty = True
        for player in player_forms:
            if len(player) != 0:
                playerempty = False
                break
        if playerempty:
            return (0, 0)

        # try:
        now = datetime.datetime.now()
        cursor = self.db.cursor()
        sql = '''insert into competition_registration_table (user_id, competition_id, competition_registration_time) values (%s, %s, %s)'''
        cursor.execute(sql, [user_id, competition_id, now])
        registration_id = cursor.lastrowid
        result = self.GetCompetitionRegistrationFormByCompetitionId(competition_id)
        if result[0] != 1:
            return (0, 'not found')
        form_info, field_info_list = result[1:]
        registration_form_id = form_info['competition_registration_form_id']
        field_info = {
            fi['competition_registration_form_field_name']: fi
            for fi in field_info_list
        }

        filedir = os.path.join(abspath, 'static/img/upload/competition/')
        tempfiledir = os.path.join(abspath, 'static/img/avatar/temp/')
        for idx, player in enumerate(player_forms, 1):
            for field, value in [(k, v) for k, v in player.items() if not k.startswith('_')]:
                sql_tmpl = "insert into competition_registration_form_data_table (competition_registration_form_id, competition_registration_form_field_name, competition_registration_form_field_type, competition_registration_form_field_{t}, competition_registration_form_user_id, competition_registration_form_registration_id, competition_id, competition_registration_form_player_number, competition_registration_form_field_index) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                t = field_info[field].get('competition_registration_form_field_type', 'text')
                sql = sql_tmpl.format(t=t)
                if t == 'image':
                    try:
                        filename = 'R%s_%s_%s.jpeg' % (registration_id, idx, field)
                        outfile  = filedir + filename
                        shutil.move(tempfiledir + player[field], outfile)
                        os.chmod(outfile, 0777)
                        value = filename
                    except Exception, e:
                        value = "default.jpeg"
                params = [
                    registration_form_id, field, t, value, user_id, registration_id, competition_id, idx, field_info[field].get('competition_registration_form_field_index')
                ]
                cursor.execute(sql, params)
        self.db.commit()

        competition = self.GetCompetition(competition_id)
        return (1, registration_id)
        # except Exception as e:
        #     logging.error(e.message)
        #     return (0, 'error')

    def GetCompetitionImageUniqueStrings(self, competition_id):
        '''Gets the random generated unique string for a competition.'''
        cursor = self.db.cursor(cursorclass=DictCursor)
        sql = "SELECT * FROM competition_table WHERE competition_id = %s LIMIT 1"
        param = [competition_id]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        if result is not None:
            if result['competition_images']:
                try:
                    return json.loads(result['competition_images'])
                except (TypeError, ValueError):
                    pass
        return []                    

    def GetCompetitionImagePreviews(self, competition_id):
        '''Get the all product avatar paths'''
        competition = self.GetCompetition(competition_id)
        filedir = abspath  # This is a global variable.
        images = self.GetCompetitionImageUniqueStrings(competition_id)
        file_tmpl = '/static/img/avatar/competition/%s.jpeg'

        for uniquestr in images:
            imagefile = file_tmpl % ('C%s_%s' % (competition['competition_id'], uniquestr))
            outfile = filedir + imagefile
            hascustomavatar = os.path.exists(outfile)
            yield (
                imagefile, # if hascustomavatar else file_tmpl % 'default_avatar_product',
                uniquestr,
                hascustomavatar
            )

    def GetCompetitionImagePreview(self, competition_id):
        previews = self.GetCompetitionImagePreviews(competition_id)
        return next(previews, None)

    def GetMyCompetitionRegistrations(self, user_id):
        sql = "select * from competition_registration_form_data_table where competition_registration_form_user_id = %s"
        cursor = self.db.cursor(cursorclass=DictCursor)
        cursor.execute(sql, [user_id])
        rows = cursor.fetchall()
        return rows

    def GetCompetitionRegistrations(self, competition_id, *args, **kwargs):
        '''
        Keyword arguments:
            page: xxx
            startpos: xxx
            count: xxx
        '''
        page = kwargs.get('page', None)
        startpos = kwargs.get('startpos', None)
        count = kwargs.get('count', None)
        sql_io = StringIO()
        sql_io.write("select r.*, o.preorder_id, o.preorder_paymentstatus, count(fd.competition_registration_form_player_number) as player_count from competition_registration_table r")
        sql_io.write(" left join (select * from competition_registration_form_data_table where competition_id = %s group by competition_registration_form_registration_id, competition_registration_form_player_number) fd on r.competition_registration_id = fd.competition_registration_form_registration_id")
        sql_io.write(" left join preorder_table o on r.competition_registration_order_id = o.preorder_id")
        sql_io.write(" where r.competition_id = %s")
        sql_io.write(" group by fd.competition_registration_form_registration_id")
        sql_io.write(" order by r.competition_registration_id desc")
        if startpos is not None:
            if count != 0:
                sql_io.write(" LIMIT %d, %d " % (startpos, count))
        else:
            if page:
                page_size = settings.LIST_ITEM_PER_PAGE
                sql_io.write(
                    " limit {offset}, {count}".format(
                        offset=page_size * (page - 1),
                        count=page_size
                    )
                )

        cursor = self.db.cursor(cursorclass=DictCursor)
        cursor.execute(sql_io.getvalue(), [competition_id] * 2)
        rows = cursor.fetchall()
        return rows

    
    def GetCompetitionRegistrationCount(self, competition_id, *args, **kwargs):
        sql_io = StringIO()
        sql_io.write("select count(1) as count from (select r.*, o.preorder_id, o.preorder_paymentstatus, count(fd.competition_registration_form_player_number) as player_count from competition_registration_table r")
        sql_io.write(" left join (select * from competition_registration_form_data_table where competition_id = %s group by competition_registration_form_registration_id, competition_registration_form_player_number) fd on r.competition_registration_id = fd.competition_registration_form_registration_id")
        sql_io.write(" left join preorder_table o on r.competition_registration_order_id = o.preorder_id")
        sql_io.write(" where r.competition_id = %s")
        sql_io.write(" group by fd.competition_registration_form_registration_id")
        sql_io.write(" order by r.competition_registration_id asc) regs")

        cursor = self.db.cursor()
        cursor.execute(sql_io.getvalue(), [competition_id] * 2)
        count = cursor.fetchone()
        if not self.IsDbUseDictCursor():
            count = count[0] if count else 0
        else:
            count = count["count"] if count else 0
        return count

    def GetCompetitionRegistration(self, competition_id, registration_id):
        sql = "select * from competition_registration_form_data_table where competition_id = %s and competition_registration_form_registration_id = %s order by competition_registration_form_player_number, competition_registration_form_data_id"
        cursor = self.db.cursor(cursorclass=DictCursor)
        cursor.execute(sql, [competition_id, registration_id])
        rows = cursor.fetchall()
        rows = groupby(rows, key=lambda r: r['competition_registration_form_player_number'])
        ret = []
        for row in rows:
            elem = (row[0], list(row[1]))
            ret.append(elem)
        return ret

    def DeleteCompetitionRegistration(self, competition_id, registration_id):
        sql1 = "delete from competition_registration_form_data_table where competition_registration_form_registration_id = %s" % registration_id
        sql2 = "delete from competition_registration_table where competition_registration_id = %s" % registration_id

        cursor = self.db.cursor()
        cursor.execute(sql1)
        cursor.execute(sql2)

        self.db.commit()
        cursor.close()

    def UpdateCompetitionRegistrationOrderNo(self, registration_id, orderid):
        sql = "update competition_registration_table set competition_registration_order_id = %s where competition_registration_id = %s"
        cursor = self.db.cursor(cursorclass=DictCursor)
        cursor.execute(sql, [orderid, registration_id])
        self.db.commit()

    def GetCompetitionRegisteredPlayerCountInProduct(self, product_id):
        product = self.QueryProductInfo(product_id)
        sql_io = StringIO()
        sql_io.write("select count(1) as count from (select 1 from preorder_table o")
        sql_io.write(" left join competition_registration_table r on o.preorder_id = r.competition_registration_order_id")
        sql_io.write(" left join competition_registration_form_data_table fd on r.competition_registration_id = fd.competition_registration_form_registration_id")
        sql_io.write(" where o.preorder_productid = %s and o.preorder_paymentstatus = 1")
        sql_io.write(" group by fd.competition_registration_form_registration_id, fd.competition_registration_form_player_number) _")
        
        cursor = self.db.cursor()
        cursor.execute(sql_io.getvalue(), [product_id])
        count = cursor.fetchone()
        if count:
            count = count[0] if not self.IsDbUseDictCursor() else count["count"]
        return count

    #####################################################################################################################################
