#!/usr/bin/env python
#-*-coding:utf-8-*-

# # # Author: Willson Zhang
# # # Date: Aug 10th, 2015
# # # Email: willson.zhang1220@gmail.com

import time, random, os, hashlib, MySQLdb, settings, socket
import json, re, uuid, logging, markdown, html5lib, cgi

from urllib import unquote
from urllib import quote
from html5lib import sanitizer
from crypter import Crypter
from datetime import timedelta
from monthdelta import MonthDelta
from time import gmtime, strftime
from MySQLdb.cursors import DictCursor
from collections import OrderedDict
from itertools import groupby
from transform import Transform
from datetime import datetime as DateTime
import shutil
import uuid
from mydql import WhereClause, DataBase
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

class WhereClause(WhereClause):
    def get_condition_sql(self):
        c = super(WhereClause, self).get_condition_sql()
        c = (' AND ' + c) if c else c
        return c

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
                user_name   VARCHAR(128) NOT NULL, \
                user_role   INTEGER NOT NULL, \
                user_adminrole  INTEGER, \
                user_phonenumber    VARCHAR(32) NOT NULL, \
                user_nickname   VARCHAR(32), \
                user_password   VARCHAR(128) NOT NULL, \
                user_email  VARCHAR(128), \
                user_gender INTEGER, \
                user_birthday   DATE, \
                user_height REAL, \
                user_weight REAL, \
                user_avatar VARCHAR(64), \
                user_qqopenid   VARCHAR(64), \
                user_wechatopenid   VARCHAR(64), \
                user_sinauid    VARCHAR(64), \
                user_huanchaouid    VARCHAR(64), \
                user_registertime   DATETIME NOT NULL DEFAULT NOW(), \
                deleteflag  INTEGER, \
                user_registersource INTEGER NOT NULL DEFAULT 1, \
                user_registerip VARCHAR(64), \
                user_permission VARCHAR(512), \
                user_star_people    TEXT, \
                user_star_gymbranch TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS user_data_table(\
                user_data_id    INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                user_data_userid    INTEGER, \
                user_data_categoryid    INTEGER, \
                user_data_duration  REAL, \
                user_data_calory    INTEGER, \
                user_data_source    INTEGER, \
                user_data_date  DATE) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS user_vipcard_table(\
                user_vipcard_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                user_vipcard_userid INTEGER, \
                user_vipcard_range  INTEGER, \
                user_vipcard_rangeid    VARCHAR(255), \
                user_vipcard_no VARCHAR(255), \
                user_vipcard_phonenumber    VARCHAR(64), \
                user_vipcard_name   VARCHAR(64), \
                user_vipcard_expiredate DATE, \
                user_vipcard_validtimes INTEGER, \
                user_vipcard_status INTEGER) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS gym_table(\
                gym_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                gym_name    VARCHAR(255), \
                gym_boss    VARCHAR(255)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS gym_branch_table(\
                gym_branch_id   INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                gym_branch_gymid    INTEGER, \
                gym_branch_name VARCHAR(255), \
                gym_branch_district VARCHAR(255), \
                gym_branch_businesscircle   VARCHAR(255), \
                gym_branch_address  VARCHAR(255), \
                gym_branch_phonenumber  VARCHAR(255)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS course_table(\
                course_id   INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                course_gymid  INTEGER, \
                course_categoryid   INTEGER, \
                course_name VARCHAR(255), \
                course_avatar   TEXT, \
                course_description  TEXT, \
                course_star_data    TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS course_schedule_table(\
                course_schedule_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                course_schedule_courseid    INTEGER, \
                course_schedule_teacherid   INTEGER, \
                course_schedule_gymbranchid INTEGER, \
                course_schedule_day INTEGER, \
                course_schedule_month   VARCHAR(16), \
                course_schedule_begintime   TIME, \
                course_schedule_endtime TIME, \
                course_schedule_stock   VARCHAR(255), \
                course_schedule_calory  INTEGER NOT NULL DEFAULT 0) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS teacher_table(\
                teacher_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                teacher_name    VARCHAR(255), \
                teacher_idcardno    VARCHAR(255), \
                teacher_gymid   INTEGER, \
                teacher_permitno    VARCHAR(255), \
                teacher_idcard_avatar   VARCHAR(32), \
                teacher_permit_avatar   VARCHAR(32), \
                teacher_avatar  TEXT, \
                teacher_description TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS private_teacher_table(\
                private_teacher_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                private_teacher_name    VARCHAR(255), \
                private_teacher_idcardno    VARCHAR(255), \
                private_teacher_gymbranchid INTEGER, \
                private_teacher_permitno    VARCHAR(255), \
                private_teacher_idcard_avatar   VARCHAR(32), \
                private_teacher_permit_avatar   VARCHAR(32), \
                private_teacher_avatar  TEXT, \
                private_teacher_description TEXT, \
                private_teacher_star_data   TEXT, \
                private_teacher_categoryid  INTEGER,\
                private_teacher_userid INT UNSIGNED NOT NULL) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS order_table(\
                order_id    INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                order_userid    INTEGER, \
                order_type  INTEGER, \
                order_objectid  INTEGER, \
                order_date  DATE, \
                order_begintime TIME, \
                order_endtime   TIME, \
                order_contact_name  VARCHAR(255), \
                order_contact_phonenumber   VARCHAR(64), \
                order_remark    VARCHAR(512), \
                order_status    INTEGER, \
                order_datetime  DATETIME) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS ads_table(\
                ads_id  INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                ads_auditstate  INTEGER, \
                ads_publisherid INTEGER, \
                ads_platform    INTEGER, \
                ads_position    INTEGER, \
                ads_avatar  VARCHAR(255), \
                ads_externalurl TEXT, \
                ads_sortweight  INTEGER, \
                ads_type    INTEGER, \
                ads_restriction TEXT) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS category_table(\
                category_id INTEGER UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                category_type   INTEGER, \
                category_name   VARCHAR(64), \
                category_description    TEXT, \
                category_sortweight TEXT, \
                category_avatar VARCHAR(64)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")

            cursor.execute("CREATE TABLE IF NOT EXISTS apiuuid_table(\
                apiuuid_id BIGINT(20) UNSIGNED PRIMARY KEY NOT NULL AUTO_INCREMENT, \
                apiuuid_value VARCHAR(48) UNIQUE NOT NULL, \
                INDEX(apiuuid_value)) \
                ENGINE = MyISAM DEFAULT CHARSET = utf8")
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS photo_table(\
                photo_id INT UNSIGNED KEY AUTO_INCREMENT,\
                photo_userid INT UNSIGNED NOT NULL,\
                photo_uuid VARCHAR(64) NOT NULL,\
                photo_uploadtime DATETIME NOT NULL DEFAULT NOW(),\
                photo_viewtimes INT UNSIGNED NOT NULL DEFAULT 0,\
                photo_stars TEXT,\
                photo_privacy INT UNSIGNED NOT NULL DEFAULT 0\
                )ENGINE=MyISAM DEFAULT CHARSET=UTF8'
            )
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS comment_table(\
                comment_id INT UNSIGNED KEY AUTO_INCREMENT,\
                comment_userid INT UNSIGNED NOT NULL,\
                comment_type INT UNSIGNED  NOT NULL,\
                comment_objectid INT UNSIGNED NOT NULL,\
                comment_content TEXT NOT NULL,\
                comment_postedtime DATETIME NOT NULL DEFAULT NOW(),\
                comment_parentid INT UNSIGNED\
                )ENGINE=MyISAM DEFAULT CHARSET=UTF8'
            )
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS relation_table(\
                relation_id INT UNSIGNED KEY AUTO_INCREMENT,\
                relation_main_userid INT UNSIGNED NOT NULL,\
                relation_sub_userid INT UNSIGNED NOT NULL,\
                relation_type INT UNSIGNED NOT NULL\
                )ENGINE=MyISAM DEFAULT CHARSET=UTF8'
            )
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

            #####################################################################################################################################
        else:
            self.db.select_db(settings.DB_NAME)
        cursor.close()

    def __del__(self):
        if self.db:
            self.db.close()

    @staticmethod
    def get_target_date(base):
        from datetime import timedelta
        return lambda d:base + timedelta(days=d)

    @staticmethod
    def get_filter_by_weekday(wd):
        return lambda d: True if wd == d.isoweekday() else False

    @staticmethod
    def get_filter_by_date(dd):
        return lambda d: True if dd == d else False

    @staticmethod
    def updatedCopyOfDict(dictObj, **kwargs):
    # 新建一个字典的副本，同时可以更新或者添加新的key-value
        copy = dictObj.copy()
        copy.update(kwargs)
        return copy

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

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_id = %s AND user_password = %s AND user_role != 1 LIMIT 1"
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

    def QueryUserInfo(self, userid):
        return self.QueryUserInfoById(userid)

    def QueryUserInfoById(self, userid):
        '''根据userid查询用户信息
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_id = %s LIMIT 1"
        param = [userid]
        cursor.execute(sql, param)

        result = cursor.fetchone()

        if result and result['user_registertime']:
            result['user_registertime'] = str(result['user_registertime'])

        if result and result['user_birthday']:
            result['user_birthday'] = str(result['user_birthday'])

        cursor.close()
        return result

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
            hashedpassword = result["user_password"]
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
            hashedpassword = result["user_password"]
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
            hashedpassword = result["user_password"]
            if cpt.ValidatePassword(passwd, hashedpassword):
                return 1
            else:
                return -1
        else:
            return -2

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

        if result and result['user_registertime']:
            result['user_registertime'] = str(result['user_registertime'])

        if result and result['user_birthday']:
            result['user_birthday'] = str(result['user_birthday'])

        cursor.close()
        return result

        
    def FuzzyQueryUserByHashed(self, hashed_stuff):
        sql = 'SELECT * FROM user_table WHERE md5(concat(user_name, user_password)) LIKE "%{}%"'.format(hashed_stuff)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        if result and result['user_registertime']:
            result['user_registertime'] = str(result['user_registertime'])

        if result and result['user_birthday']:
            result['user_birthday'] = str(result['user_birthday'])

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

        if result and result['user_registertime']:
            result['user_registertime'] = str(result['user_registertime'])

        if result and result['user_birthday']:
            result['user_birthday'] = str(result['user_birthday'])

        cursor.close()
        return result

    def QueryAllUserCount(self, userrole=0):
        ''' userrole: 0 - 全部用户， 1 - 前端用户， 2 - 供应商，3 - 管理员
        '''
        cursor = self.db.cursor()
        if userrole == 0:
            sql = "SELECT COUNT(*) AS COUNT FROM user_table WHERE deleteflag = 0"
        else:
            sql = "SELECT COUNT(*) AS COUNT FROM user_table WHERE deleteflag = 0 AND user_role = %s" % userrole
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        usercount = result["COUNT"] if result["COUNT"] is not None else 0

        return usercount

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
        return result["COUNT"] if result["COUNT"] is not None else 0

    def FuzzyQueryUser(self, userkey, startpos, count=settings.LIST_ITEM_PER_PAGE, userrole=0):
        cursor = self.db.cursor()
        userkey = userkey.replace("'", "''") if userkey else userkey
        if userrole == 0:
            sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND (user_name LIKE '%s%%' OR user_phonenumber LIKE '%s%%') ORDER BY user_id DESC LIMIT %s, %s" % (userkey, userkey, startpos, count)
        else:
            sql = "SELECT * FROM user_table WHERE deleteflag = 0 AND user_role = %s AND (user_name LIKE '%s%%' OR user_phonenumber LIKE '%s%%') ORDER BY user_id DESC LIMIT %s, %s" % (userrole, userkey, userkey, startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()

        for oneuser in result:
            if oneuser and oneuser['user_registertime']:
                oneuser['user_registertime'] = str(oneuser['user_registertime'])

            if oneuser and oneuser['user_birthday']:
                oneuser['user_birthday'] = str(oneuser['user_birthday'])

        cursor.close()
        return result

    def QueryUsers(self, startpos, count=settings.LIST_ITEM_PER_PAGE, userrole=0, **kwargs):
        cursor = self.db.cursor()
        sql = "SELECT * FROM user_table WHERE deleteflag = 0 "
        if userrole != 0:
            sql += " AND user_role = %s " % userrole
        sql += WhereClause(kwargs).get_condition_sql()
        sql += " ORDER BY user_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        
        cursor.execute(sql)
        result = cursor.fetchall()

        for oneuser in result:
            if oneuser and oneuser['user_registertime']:
                oneuser['user_registertime'] = str(oneuser['user_registertime'])

            if oneuser and oneuser['user_birthday']:
                oneuser['user_birthday'] = str(oneuser['user_birthday'])

        cursor.close()
        return result

    def SaveUser(self, obj, *args, **kwargs):
        '''Adds/Updates a user object.
        If obj['promotion_id'] is defined, perform an update operation.
        Otherwise, perform an insertion.

        Arguments:
            obj: An user object in the form of dictionary.

        Returns:
            0: Success
            1: Nothing to save
            2: Error
        '''
        if obj.has_key('user_password'):
            fields = ('user_id', 'user_name', 'user_role', 'user_adminrole', 'user_phonenumber', 'user_nickname', 'user_password', 'user_email', 'user_gender', 'user_birthday', 'user_height', 'user_weight', 'user_avatar', 'user_qqopenid', 'user_wechatopenid', 'user_sinauid', 'user_huanchaouid', 'user_registertime', 'deleteflag', 'user_registersource', 'user_registerip', 'user_permission', 'user_star_people', 'user_star_gymbranch', 'user_friends')
        else:
            fields = ('user_id', 'user_name', 'user_role', 'user_adminrole', 'user_phonenumber', 'user_nickname', 'user_email', 'user_gender', 'user_birthday', 'user_height', 'user_weight', 'user_avatar', 'user_qqopenid', 'user_wechatopenid', 'user_sinauid', 'user_huanchaouid', 'user_registertime', 'deleteflag', 'user_registersource', 'user_registerip', 'user_permission', 'user_star_people', 'user_star_gymbranch', 'user_friends')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        if obj.has_key('user_password'):
            cpt = Crypter()
            obj['user_password'] = cpt.EncryptPassword(obj['user_password'])

        if obj.has_key('user_birthday') and obj['user_birthday'] == '':
            del obj['user_birthday']

        user_id = obj.get("user_id", None)
        phonenumber = obj.get("user_phonenumber")
        password = obj.get("user_password")
        if user_id:
            # Update
            update_keys = [ k for k in obj if k != 'user_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update user_table set {updates} where user_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'user_id' ]
                params.append(user_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        elif phonenumber and password and len(obj) == 3:
            sql = 'UPDATE user_table SET user_password="%s" WHERE user_phonenumber=%s' % (password, phonenumber)
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            return 0
        else:
            # Add
            sql_tmpl = r"insert into user_table ({fields}) values ({values})"
            obj['user_registertime'] = datetime.datetime.now()
            obj['deleteflag'] = 0
            sql = sql_tmpl.format(
                fields=','.join(k for k in obj.keys()),
                values=','.join('%s' for _ in obj.keys())
            )
            params = [v for v in obj.values()]
            cursor = self.db.cursor()
            cursor.execute(sql, params)
            theid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return theid

    def SaveUserPoints(self, user_id, delta_points):
        sql = 'UPDATE user_table set user_points = user_points + %s where user_id = %s' 
        params = [delta_points, user_id]
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        self.db.commit()

    def DeleteUser(self, user_id, permant):
        cursor = self.db.cursor()
        if int(permant) == 0:
            sql = "UPDATE user_table SET deleteflag = 1 WHERE user_id = %s" % user_id
        else:
            sql = "DELETE FROM user_table WHERE user_id = %s" % user_id
        cursor.execute(sql)
        self.db.commit()

    def SearchPeopleByKeyword(self, keyword, search_range=0):
        sql = 'SELECT * FROM user_table WHERE user_role=1 AND (\
               user_huanchaouid LIKE "%{kwd}%" OR \
               user_phonenumber LIKE "%{kwd}%" OR \
               user_nickname LIKE "%{kwd}%")'.format(kwd=keyword)
        if int(search_range) == 1:
            sql += ' AND user_id NOT IN (SELECT coachauth_userid FROM coachauth_table WHERE coachauth_status=1) '
        elif int(search_range) == 2:
            sql += ' AND user_id IN (SELECT coachauth_userid FROM coachauth_table WHERE coachauth_status=1) '
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

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
            avt = result["user_avatar"]
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

    def GetUserAvatarPreview(self, userid):
        '''Get the user's preview avatar path.
        '''
        hascustomavatar = True
        userinfo = self.QueryUserInfoById(userid)
        if userinfo is None:
            return ('/static/img/avatar/user/default_avatar.jpeg', False)
        filedir = abspath
        avatarfile = '/static/img/avatar/user/L%s_%s.jpeg' % (userinfo["user_id"], self.GetUserAvatarUniqueString(userid))
        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/user/P%s_%s.jpeg' % (userinfo["user_id"], self.GetUserAvatarUniqueString(userid))
            outfile  = filedir + avatarfile
            if os.path.exists(outfile) == False:
                avatarfile = '/static/img/avatar/user/default_avatar.jpeg'
                hascustomavatar = False
        return (avatarfile, hascustomavatar)

    # ----------

    def QueryUserFans(self, user_id):
        '''查询用户的所有粉丝(user_id 列表)
        '''
        user_id = int(user_id)
        userfansidlist = []
        userinfo = self.QueryUserInfoById(user_id)
        if userinfo is not None:
            allusers = self.QueryUsers(0, 0, userrole=1)
            for oneuser in allusers:
                if self.IsPeopleFollowedByUser(user_id, oneuser['user_id']):
                    if oneuser['user_id'] not in userfansidlist:
                        userfansidlist.append(oneuser['user_id'])
        return userfansidlist

    def QueryUserFollowPeople(self, user_id):
        '''查询用户关注的所有人(user_id 列表 - string类型的ID)
        '''
        userinfo = self.QueryUserInfoById(user_id)
        if userinfo is None or userinfo['user_star_people'] is None or userinfo['user_star_people'] == "" or userinfo['user_star_people'] == "None":
            useridlist = []
        else:
            userfollowpeoplelist = json.loads(userinfo['user_star_people'])
            useridlist = []
            for the_id in userfollowpeoplelist:
                if int(the_id) not in useridlist:
                    useridlist.append(int(the_id))
        return useridlist

    def QueryUserFollowPeopleInfo(self, user_id):
        '''
           查询用户关注的所有人信息（userinfo 列表）
        '''
        userfollowpeoplelist = self.QueryUserFollowPeople(user_id)
        userfollowpeopleinfo = []
        for userid in userfollowpeoplelist:
            userinfo = self.QueryUserInfoById(userid)
            userfollowpeopleinfo.append(userinfo)
        return userfollowpeopleinfo

    def FollowPeople(self, user_id, targetuserid):
        '''关注某人
        '''
        userinfo = self.QueryUserInfoById(targetuserid)
        if userinfo is None:
            return

        userfollowpeoplelist = self.QueryUserFollowPeople(user_id)
        if targetuserid in userfollowpeoplelist:
            return
            
        userfollowpeoplelist.append(targetuserid)
        userfollowpeople_json = json.dumps(userfollowpeoplelist)

        cursor = self.db.cursor()

        sql   = "UPDATE user_table SET user_star_people = %s WHERE user_id = %s"
        param = (userfollowpeople_json, user_id)
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

        # relevantuserinfo = self.QueryUserInfoByName(username)
        # self.CreateNotification(self.NOTIFICATION_TYPE_FOLLOW_PEOPLE, targetuserid, relevantuserinfo[0], None, None, None, None)

    def UnfollowPeople(self, user_id, targetuserid):
        '''取消关注某人
        '''
        userinfo = self.QueryUserInfoById(targetuserid)
        if userinfo is None:
            return

        userfollowpeoplelist = self.QueryUserFollowPeople(user_id)
        if targetuserid not in userfollowpeoplelist:
            return
            
        userfollowpeoplelist.remove(targetuserid)
        userfollowpeople_json = json.dumps(userfollowpeoplelist)

        cursor = self.db.cursor()

        sql   = "UPDATE user_table SET user_star_people = %s WHERE user_id = %s"
        param = (userfollowpeople_json, user_id)
        cursor.execute(sql, param)

        self.db.commit()
        cursor.close()

    def IsPeopleFollowedByUser(self, peopleid, user_id):
        '''查询某人(peopleid) 是否被登录用户(user_id) 关注
        '''
        userfollowpeoplelist = self.QueryUserFollowPeople(user_id)

        if int(peopleid) in userfollowpeoplelist or str(peopleid) in userfollowpeoplelist:
            # if int(peopleid) == 23 and int(user_id) == 10:
            #     logging.debug("--- userfollowpeoplelist(user_id - %r): %r in %r" % (user_id, peopleid, userfollowpeoplelist))
            return True
        else:
            # if int(peopleid) == 23 and int(user_id) == 10:
            #     logging.debug("--- userfollowpeoplelist(user_id - %r): %r not in %r" % (user_id, peopleid, userfollowpeoplelist))
            return False

    # ----------
    def MakeFriends(self, user_id, targetuser_id):
        userinfo = self.QueryUserInfoById(user_id)
        if userinfo is None: return 0
        else:
            if userinfo['user_friends']:
               friends_list = json.loads(userinfo["user_friends"])
               if int(targetuser_id) in friends_list:
                    return 0
               else:
                    friends_list.append(int(targetuser_id))
            else:
                friends_list = [int(targetuser_id)]
            self.SaveUser(dict(
                user_id=user_id,
                user_friends=json.dumps(friends_list)
            ))
            return 1

    def QueryRelationInfo(self, uid1, uid2):
        sql = "SELECT * FROM relation_table WHERE \
        (relation_main_userid = %s AND relation_sub_userid = %s) OR\
        (relation_main_userid = %s AND relation_sub_userid = %s)"
        cursor = self.db.cursor()
        params = [uid1, uid2, uid2, uid1]
        cursor.execute(sql, params)
        result = cursor.fetchone()
        cursor.close()
        return result        


    def BuildRelations(self, user_id, targetuser_id, relation_type):
        users = self.QueryUsers(startpos=0, count=0, userrole=1, user_id__in=[int(user_id), int(targetuser_id)])
        if len(users) == 2:
            relationInfo = self.QueryRelationInfo(user_id, targetuser_id)
            if relationInfo is None:
                if int(relation_type) != 0:
                    self.SaveRelation(
                        relation_main_userid=user_id,
                        relation_sub_userid=targetuser_id,
                        relation_type=relation_type
                    )
                    return 1
                else:
                    return 0
            elif relationInfo['relation_type'] == 0 and int(relation_type) > 0 or \
                 relationInfo['relation_type'] > 0 and int(relation_type) == 0:
                self.SaveRelation(
                    relation_id=relationInfo['relation_id'],
                    relation_main_userid=user_id,
                    relation_sub_userid=targetuser_id,
                    relation_type=relation_type
                )
                return 1
            else:
                return 0
        else:
            return 0


    def QueryRelatedUsers(self, userid, startpos=0, count=settings.LIST_ITEM_PER_PAGE, relation_type=0):
        '''
        relation_type:
        1 - query user's friends refer to userid
        2 - for user which is a coach, query user's students; for user which is a student, query user's coaches
        '''
        sql = 'SELECT * FROM user_table LEFT JOIN coachauth_table ON coachauth_userid=user_id WHERE user_role=1 AND user_id IN \
            (SELECT relation_main_userid FROM relation_table WHERE relation_status=1 AND relation_sub_userid={userid} {relation_type}) \
            OR user_id IN\
            (SELECT relation_sub_userid FROM relation_table WHERE relation_status=1 AND relation_main_userid={userid} {relation_type})'\
            .format(userid=userid, relation_type=('' if relation_type == 0 else 'AND relation_type=%s' % relation_type))
        sql += " ORDER BY user_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        cursor = self.db.cursor()
        cursor.execute(sql)
        r = cursor.fetchall()
        return r
    def QueryRelations(self, userid, the_other_userid=0, rtype=0, **kwargs):
        if the_other_userid == 0:
            sql = "SELECT * FROM relation_table WHERE (relation_main_userid={userid} OR relation_sub_userid={userid})".format(userid=userid)
            sql += WhereClause(kwargs).get_condition_sql()
        else:
            sql = "SELECT * FROM relation_table WHERE (relation_main_userid={userid} AND relation_sub_userid={the_other_userid} OR \
                  relation_sub_userid={userid} AND relation_main_userid={the_other_userid})".format(userid=userid, the_other_userid=the_other_userid)
        if rtype != 0:
            sql += " AND relation_type=%s" % rtype
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryApplyMessages(self, user_id, rtype=0):
        '''
        user_id, current user id 
        '''
        sql = "SELECT * FROM relation_table \
            INNER JOIN user_table ON relation_main_userid=user_id \
            LEFT JOIN coachauth_table ON user_id=coachauth_userid \
            WHERE relation_sub_userid=%s AND relation_msg_delete=0 " % user_id
        if int(rtype) != 0:
            sql += " AND relation_type=%s" % rtype

        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    
    def SaveTable(self, tbname, **kwargs):
        tb_id = kwargs.pop('{}_id'.format(tbname), None)
        if tb_id and kwargs:
            temp = kwargs.copy()
            where_kw = {''.join(k.split('__where')):temp.pop(k) for k, v in kwargs.items() if '__where' in k}
            sql_tmpl = "UPDATE %s_table SET {updates} WHERE %s_id = {id}" % (tbname, tbname)
            sql_tmpl += WhereClause(where_kw).get_condition_sql()
            kwargs = temp
            updates = ','.join("{}=%s".format(k) for k in kwargs)
            sql = sql_tmpl.format(
                updates=updates,
                id='%s'
            )
            params = [ v for k, v in kwargs.items() ]
            params.append(tb_id)
            cursor = self.db.cursor()
            try:
                cursor.execute(sql, params)
            except:
                signal = False
            else:
                self.db.commit()
                signal = True
            finally:
                return signal
        elif kwargs:
            repeat = 1
            for v in kwargs.values():
                if isinstance(v, (tuple, list)):
                    repeat = len(v)
                    break
            slots = ",".join(["({})"] * repeat)

            # sql_tmpl = "INSERT INTO %s_table ({fields}) VALUES ({vals})" % tbname
            sql_tmpl = "INSERT INTO %s_table ({fields}) VALUES %s" % (tbname, slots)

            slots_vals = [','.join('%s' for _ in kwargs.keys())] * repeat
            sql = sql_tmpl.format(
                # vals=','.join('%s' for _ in kwargs.keys())
                *slots_vals,
                fields=','.join(k for k in kwargs.keys())
            )
            # params = [ v for v in kwargs.values() ]
            tmp = []
            for v in kwargs.values():
                if isinstance(v, (tuple, list)):
                    tmp.append(v)
                else:
                    tmp.append([v]*repeat)
            target_params = []
            for i in zip(*tmp):
                target_params.extend(i)

            cursor = self.db.cursor()
            cursor.execute(sql, target_params)
            theid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return theid
            
    def SavePhoto(self, auto_prefix=False, **kwargs):
        prefix = 'photo'
        if auto_prefix is True:
            kwargs = {'{}_{}'.format(prefix, k): v for k, v in kwargs.items()}
        return self.SaveTable(prefix, **kwargs)

    def SaveRelation(self, auto_prefix=True, **kwargs):
        prefix = 'relation'
        if auto_prefix is True:
            kwargs = {'{}_{}'.format(prefix, k): v for k, v in kwargs.items()}
        return self.SaveTable(prefix, **kwargs)

    def SaveCoachAuth(self, auto_prefix=False, **kwargs):
        prefix = 'coachauth'
        if auto_prefix is True:
            kwargs = {'{}_{}'.format(prefix, k): v for k, v in kwargs.items()}
        return self.SaveTable(prefix, **kwargs)

    def QueryCoachAuths(self, startpos=0, count=settings.LIST_ITEM_PER_PAGE, **kwargs):
        sql = 'SELECT * FROM coachauth_table WHERE 1=1 '
        sql += WhereClause(kwargs).get_condition_sql()
        sql += ' ORDER BY coachauth_id DESC'
        if count != 0:
            sql += ' LIMIT %s, %s' % (startpos, count)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result
    
    def IsCoach(self, uid):
        auths = self.QueryCoachAuths(count=0, coachauth_userid=uid, coachauth_status=1)
        return len(auths) > 0
        
    def QueryPhotoInfo(self, photo_id):
        # sql = 'SELECT * from photo_table AS pt INNER JOIN \
        #       (SELECT * from comment_table WHERE comment_type = 1)  AS ct ON photo_id=comment_objectid INNER JOIN\
        #       user_table AS ut ON user_id=comment_userid WHERE photo_id=%s'
        sql = 'SELECT * FROM photo_table WHERE photo_id=%s'
        cursor = self.db.cursor()
        cursor.execute(sql, [photo_id])
        return cursor.fetchone()

    def QueryPhotos(self, startpos=0, count=settings.LIST_ITEM_PER_PAGE, **kwargs):
        sql = 'SELECT * FROM photo_table WHERE 1=1 '
        sql += WhereClause(kwargs).get_condition_sql()
        if count != 0:
            sql += ' LIMIT %s, %s ' % (startpos, count)
        cursor = self.db.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def SaveComment(self, **kwargs):
        return self.SaveTable('comment', **kwargs)

    def QueryComments(self, startpos=0, count=settings.LIST_ITEM_PER_PAGE, **kwargs):
        sql = 'SELECT * FROM comment_table INNER JOIN user_table ON user_id=comment_userid AND 1=1 '
        sql += WhereClause(kwargs).get_condition_sql()
        sql += " ORDER BY comment_id DESC "
        if count != 0:
            sql += ' LIMIT %s, %s ' % (startpos, count)
        cursor = self.db.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def QueryCommentInfo(self, comment_id):
        sql = 'SELECT * FROM comment_table INNER JOIN user_table ON user_id=comment_userid WHERE comment_id=%s'
        cursor = self.db.cursor()
        cursor.execute(sql, [comment_id])
        result = cursor.fetchone()
        cursor.close()
        return result


    def SaveTask(self, auto_prefix=False, **kwargs):
        prefix = 'task'
        if auto_prefix is True:
            kwargs = {'{}_{}'.format(prefix, k): v for k, v in kwargs.items()}
        return self.SaveTable(prefix, **kwargs)

    def QueryTasks(self, startpos=0, count=settings.LIST_ITEM_PER_PAGE, daily=False, **kwargs):
        if daily:
            sql = 'SELECT * FROM task_table WHERE DATE_FORMAT(now(), "%Y%m%d") = DATE_FORMAT(task_finishtime, "%Y%m%d") AND 1=1 '
        else:
            sql = 'SELECT * FROM task_table WHERE 1=1 '

        sql += WhereClause(kwargs).get_condition_sql()
        if count != 0:
            sql += ' LIMIT %s, %s' % (startpos, count)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result


    def SaveEntry(self, auto_prefix=False, **kwargs):
        prefix = 'entry'
        if auto_prefix is True:
            kwargs = {'{}_{}'.format(prefix, k): v for k, v in kwargs.items()}
        return self.SaveTable(prefix, **kwargs)

    def QueryEntrys(self, startpos=0, count=settings.LIST_ITEM_PER_PAGE, **kwargs):
        sql = 'SELECT * FROM entry_table WHERE 1=1 '
        sql += WhereClause(kwargs).get_condition_sql()
        sql += ' ORDER BY entry_id DESC'
        if count != 0:
            sql += ' LIMIT %s, %s' % (startpos, count)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryEntryInfo(self, entry_id):
        cursor = self.db.cursor()
        sql = "SELECT * FROM entry_table WHERE entry_id = %s "
        cursor.execute(sql, [entry_id])
        r = cursor.fetchone()
        cursor.close()
        return r

    def SaveScheduleV2(self, auto_prefix=False, **kwargs):
        prefix = 'schedule'
        if auto_prefix is True:
            kwargs = {'{}_{}'.format(prefix, k): v for k, v in kwargs.items()}
        return self.SaveTable(prefix, **kwargs)

    def QueryScheduleV2(self, auto_prefix=False, vision=0, **kwargs):
        """
        vision: 0 show regular lessons, 1 show students' lessons
        """
        prefix = 'schedule'
        if auto_prefix is True:
            kwargs = {'{}_{}'.format(prefix, k): v for k, v in kwargs.items()}
        sql = "SELECT * FROM schedule_table "        
        if vision == 1:
            sql += 'INNER JOIN user_table ON schedule_student_userid=user_id '
        sql += "WHERE schedule_deleteflag=0 AND 1=1 "
        sql += WhereClause(kwargs).get_condition_sql()
        sql += ' ORDER BY {}_id DESC'.format(prefix)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def QueryFitnessData(self, **kwargs):
        sql = 'SELECT * FROM user_data_table \
            INNER JOIN category_table ON user_data_categoryid=category_id '
        sql += WhereClause(kwargs).get_condition_sql()
        cursor = self.db.cursor()
        cursor.execute(sql)
        r = cursor.fetchall()
        cursor.close()
        return r

    #####################################################################################################################################

    def QueryUserDataInfo(self, user_data_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM user_data_table WHERE user_data_id = %s LIMIT 1"
        param = [ user_data_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryUserData(self, startpos, count=settings.LIST_ITEM_PER_PAGE, user_id=0, month=0, date=0, source=0, **kwargs):
        cursor = self.db.cursor()
        sql = "SELECT * FROM user_data_table INNER JOIN user_table ON user_id=user_data_userid WHERE 1=1 "
        if user_id !=0:
            sql += " AND user_data_userid=%s " % user_id
        if month != 0:
            sql += ' AND DATE_FORMAT(user_data_date, "%s") = "%s"' % ('%Y%m', month) 
        if date != 0:
            sql += ' AND DATE_FORMAT(user_data_date, "%s") = "%s"' % ('%Y-%m-%d', date)
        if source != 0:
            sql += ' AND user_data_source = %s' % source
        sql += WhereClause(kwargs).get_condition_sql()
        sql += " ORDER BY user_data_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        cursor.execute(sql)
        result = cursor.fetchall()
        for r in result:
            r['user_data_date'] = str(r['user_data_date'])
        cursor.close()
        return result

    def SaveUserData(self, obj, *args, **kwargs):
        fields = ('user_data_id', 'user_data_userid', 'user_data_categoryid', 'user_data_duration', 'user_data_calory', 'user_data_source', 'user_data_date')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        user_data_id = obj.get("user_data_id", None)
        if user_data_id:
            # Update
            update_keys = [ k for k in obj if k != 'user_data_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update user_data_table set {updates} where user_data_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'user_data_id' ]
                params.append(user_data_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into user_data_table ({fields}) values ({values})"
            # obj['user_registertime'] = datetime.datetime.now()
            # obj['deleteflag'] = 0
            sql = sql_tmpl.format(
                fields=','.join(k for k in obj.keys()),
                values=','.join('%s' for _ in obj.keys())
            )
            params = [ v for v in obj.values() ]
            cursor = self.db.cursor()

            # logging.debug("--- sql: %r" % sql)
            # logging.debug("--- params: %r" % params)

            cursor.execute(sql, params)
            theid = cursor.lastrowid
            self.db.commit()
            cursor.close()
            return theid

    def DeleteUserData(self, user_data_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM user_data_table WHERE user_data_id = %s" % user_data_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def SaveUserDataV2(self, auto_prefix=False, **kwargs):
        prefix = 'user_data'
        if auto_prefix is True:
            kwargs = {'{}_{}'.format(prefix, k): v for k, v in kwargs.items()}
        return self.SaveTable(prefix, **kwargs)
    #####################################################################################################################################

    def QueryUservipcardInfo(self, user_vipcard_id=0, **kwargs):
        cursor = self.db.cursor()
        sql  = " SELECT * FROM user_vipcard_table WHERE 1=1 "
        if user_vipcard_id != 0:
            sql += ' AND user_vipcard_id = %s ' % user_vipcard_id
        sql += WhereClause(kwargs).get_condition_sql()
        cursor.execute(sql)
        result = cursor.fetchone()
        rangeid_list = json.loads(result['user_vipcard_rangeid']) if result and result['user_vipcard_rangeid'] else None
        if rangeid_list:
            if not isinstance(rangeid_list, (tuple, list)):
                rangeid_list = [rangeid_list]
            result['rangeid_list'] = rangeid_list

        cursor.close()
        return result

    def QueryUservipcard(self, startpos, count=settings.LIST_ITEM_PER_PAGE, user_id=0, **kwargs):
        user_vipcard_range = kwargs.pop("user_vipcard_range", None)
        cursor = self.db.cursor()
        sql = 'SELECT * FROM user_vipcard_table '
        if user_vipcard_range is None:
            sql += ' WHERE 1=1 '
        else:
            sql += ' WHERE user_vipcard_range=%s ' % user_vipcard_range

        if user_id != 0:
            sql += ' AND user_vipcard_userid=%s' % user_id
        sql += " ORDER BY user_vipcard_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        # ====================
        cursor.execute(sql)
        result = cursor.fetchall()

        for r in result:
            r['user_vipcard_expiredate'] = str(r['user_vipcard_expiredate'])
        # ====================
            rangeid_list = json.loads(r['user_vipcard_rangeid']) if r['user_vipcard_rangeid'] else None
            if r['user_vipcard_range'] == 0:
                r['gym_branch_list'] = self.QueryGymBranch(0, gym_id__in=rangeid_list)
            elif r['user_vipcard_range'] == 1:
                r['gym_branch_list'] = self.QueryGymBranch(0, gym_branch_id__in=rangeid_list)
        cursor.close()
        return result

    def SaveUservipcard(self, obj, *args, **kwargs):
        fields = ('user_vipcard_id', 'user_vipcard_userid', 'user_vipcard_range', 'user_vipcard_rangeid', 'user_vipcard_no', 'user_vipcard_phonenumber', 'user_vipcard_name', 'user_vipcard_expiredate', 'user_vipcard_validtimes', 'user_vipcard_status')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        user_vipcard_id = obj.get("user_vipcard_id", None)
        if user_vipcard_id:
            # Update
            update_keys = [ k for k in obj if k != 'user_vipcard_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update user_vipcard_table set {updates} where user_vipcard_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'user_vipcard_id' ]
                params.append(user_vipcard_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into user_vipcard_table ({fields}) values ({values})"
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

    def DeleteUservipcard(self, user_vipcard_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM user_vipcard_table WHERE user_vipcard_id = %s" % user_vipcard_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def QueryGymInfo(self, gym_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM gym_table WHERE gym_id = %s LIMIT 1"
        param = [ gym_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryGym(self, startpos, count=settings.LIST_ITEM_PER_PAGE):
        cursor = self.db.cursor()
        sql = "SELECT * FROM gym_table "
        sql += " ORDER BY gym_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SaveGym(self, obj, *args, **kwargs):
        fields = ('gym_id', 'gym_name', 'gym_boss')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        gym_id = obj.get("gym_id", None)
        if gym_id:
            # Update
            update_keys = [ k for k in obj if k != 'gym_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update gym_table set {updates} where gym_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'gym_id' ]
                params.append(gym_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into gym_table ({fields}) values ({values})"
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

    def DeleteGym(self, gym_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM gym_table WHERE gym_id = %s" % gym_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def QueryGymBranchInfo(self, gym_branch_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM gym_branch_table WHERE gym_branch_id = %s LIMIT 1"
        param = [ gym_branch_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryGymBranch(self, startpos, count=settings.LIST_ITEM_PER_PAGE, gym_id=0, **kwargs):
        cursor = self.db.cursor()
        sql = "SELECT * FROM gym_branch_table INNER JOIN gym_table ON gym_id=gym_branch_gymid WHERE 1 = 1 "
        if gym_id != 0:
            sql += " AND gym_branch_gymid = %s " % gym_id
        sql += WhereClause(kwargs).get_condition_sql()
        sql += " ORDER BY gym_branch_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def GetAllDistrictBusinessCircle(self, firstBC=0, districtname=None):
        if firstBC != 0:
            for k, v in settings.DISTRICT_BUSINESSCIRCLE.iteritems():
                return (k, v)
        elif districtname is not None:
            for k, v in settings.DISTRICT_BUSINESSCIRCLE.iteritems():
                if k == districtname:
                    return (k, v)
        else:
            return settings.DISTRICT_BUSINESSCIRCLE

    def SaveGymBranch(self, obj, *args, **kwargs):
        fields = ('gym_branch_id', 'gym_branch_gymid', 'gym_branch_name', 'gym_branch_district', 'gym_branch_businesscircle', 'gym_branch_address', 'gym_branch_phonenumber')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        gym_branch_id = obj.get("gym_branch_id", None)
        if gym_branch_id:
            # Update
            update_keys = [ k for k in obj if k != 'gym_branch_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update gym_branch_table set {updates} where gym_branch_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'gym_branch_id' ]
                params.append(gym_branch_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into gym_branch_table ({fields}) values ({values})"
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

    def DeleteGymBranch(self, gym_branch_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM gym_branch_table WHERE gym_branch_id = %s" % gym_branch_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def QueryCourseInfo(self, course_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM course_table WHERE course_id = %s LIMIT 1"
        param = [ course_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryCourse(self, startpos, count=settings.LIST_ITEM_PER_PAGE, category_id=0, gym_id=0):
        cursor = self.db.cursor()
        sql = "SELECT * FROM course_table WHERE 1 = 1 "
        if category_id != 0:
            sql += " AND course_categoryid = %s " % category_id
        if gym_id != 0:
            sql += " AND course_gymid = %s " % gym_id
        sql += " ORDER BY course_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SaveCourse(self, obj, *args, **kwargs):
        fields = ('course_id', 'course_gymid', 'course_categoryid', 'course_name', 'course_avatar', 'course_description', 'course_star_data')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        course_id = obj.get("course_id", None)
        if course_id:
            # Update
            update_keys = [ k for k in obj if k != 'course_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update course_table set {updates} where course_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'course_id' ]
                params.append(course_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into course_table ({fields}) values ({values})"
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

    def DeleteCourse(self, course_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM course_table WHERE course_id = %s" % course_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def GetCourseAvatarUniqueString(self, course_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM course_table WHERE course_id = %s LIMIT 1"
        param = [ course_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["course_avatar"]
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

    def GetCourseAvatarUniqueStrings(self, course_id):
        '''Gets the random generated unique strings for a product'''
        cursor = self.db.cursor()
        sql = "SELECT * FROM course_table WHERE course_id = %s LIMIT 1"
        param = [ course_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        
        if result is not None:
            if result["course_avatar"] and result["course_avatar"].startswith('['):
                try:
                    return json.loads(result["course_avatar"])
                except (TypeError, ValueError):
                    pass
            else:
                return [ result["course_avatar"] ]
        return []

    def GetCourseAvatarPreview(self, course_id):
        aps = course_id and self.GetCourseAvatarPreviews(course_id) or []
        i = 0
        avatarpreview = None
        hascustomavatar = False
        for avatar, uniquestring, iscustom in aps:
            if i == 0:
                avatarpreview = avatar
                hascustomavatar = iscustom
            else:
                break
            i = i + 1
        return (avatarpreview, hascustomavatar)

    def GetCourseAvatarPreviews(self, course_id):
        '''Get the all image avatar paths'''
        courseinfo = self.QueryCourseInfo(course_id)
        filedir = abspath
        avatars = self.GetCourseAvatarUniqueStrings(course_id)
        file_tmpl = '/static/img/avatar/course/%s.jpeg'

        for uniquestr in avatars:
            avatarfile = file_tmpl % ('P%s_%s' % (courseinfo["course_id"], uniquestr))
            outfile = filedir + avatarfile
            hascustomavatar = os.path.exists(outfile)
            yield (
                avatarfile, # if hascustomavatar else file_tmpl % 'default_avatar_product',
                uniquestr,
                hascustomavatar
            )

    #####################################################################################################################################

    def QueryScheduleInfoPlus(self, **kwargs):
        sql = ' SELECT course_schedule_id, course_schedule_courseid, course_schedule_teacherid, course_schedule_gymbranchid,  \
                       course_schedule_day, course_schedule_month, DATE_FORMAT(course_schedule_begintime, "%H:%i") AS course_schedule_begintime, \
                       DATE_FORMAT(course_schedule_endtime, "%H:%i") AS course_schedule_endtime, course_schedule_stock, course_schedule_calory FROM course_schedule_table WHERE 1 = 1 '
        sql += WhereClause(kwargs).get_condition_sql()
        sql += ' LIMIT 1'
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryScheduleInfo(self, course_schedule_id):
        sql = ' SELECT course_schedule_id, course_schedule_courseid, course_schedule_teacherid, course_schedule_gymbranchid,  \
                       course_schedule_day, course_schedule_month, DATE_FORMAT(course_schedule_begintime, "%H:%i") AS course_schedule_begintime, \
                       DATE_FORMAT(course_schedule_endtime, "%H:%i") AS course_schedule_endtime, course_schedule_stock, course_schedule_calory, c.* FROM course_schedule_table \
                INNER JOIN course_table AS c ON course_id=course_schedule_courseid '
        sql += ' WHERE course_schedule_id = %s LIMIT 1 ' % course_schedule_id
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()

        teacherinfo = self.QueryTeacherInfo(result['course_schedule_teacherid'])

        result['course_star_data'] = eval(result['course_star_data']) if result['course_star_data'] else []
        result['course_teacher_name'] = teacherinfo['teacher_name'] if teacherinfo else "N/A"
        result['course_schedule_stock'] = eval(str(result['course_schedule_stock']))

        return result

    def QueryScheduleTime(self, startpos, count=settings.LIST_ITEM_PER_PAGE, **kwargs):
        sql = " SELECT course_schedule_id, course_schedule_courseid, course_schedule_teacherid, \
            course_schedule_gymbranchid, course_schedule_day, course_schedule_month, \
            date_format(course_schedule_begintime, '%H:%i') as course_schedule_begintime, \
            date_format(course_schedule_endtime, '%H:%i') as course_schedule_endtime, \
            course_schedule_stock, course_schedule_calory FROM course_schedule_table WHERE 1=1 "
        sql += WhereClause(kwargs).get_condition_sql()
        if count !=0:
            sql += ' LIMIT %s, %s ' % (startpos, count)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result


    def QuerySchedule(self, startpos, count=settings.LIST_ITEM_PER_PAGE, copyschedule=1, **kwargs):
        ''' 
    		当以表的字段field_name作为筛选条件，e.g. WHERE course_schedule_id = 1234
    		可以这样调用该方法，e.g. QuerySchedule(..., course_schedule_id=1234)
			支持多个字段进行筛选。
			以及其包括运算符号：=, >, <, >=, <=, IN (在field_name紧跟'__'双下划线);
			e.g. QuerySchedule(..., course_schedule_begintime__gt='20:00') 等价于 'WHERE course_schedule_begintime>"20:00"'
        '''
        sql = "SELECT *, date_format(course_schedule_begintime, '%H:%i') as course_schedule_begintime, \
            date_format(course_schedule_endtime, '%H:%i') as course_schedule_endtime \
            FROM course_schedule_table \
            INNER JOIN course_table ON course_schedule_courseid=course_id \
            INNER JOIN gym_branch_table ON gym_branch_id=course_schedule_gymbranchid \
            INNER JOIN category_table ON category_id=course_categoryid \
            INNER JOIN gym_table ON gym_branch_gymid=gym_id \
            WHERE 1=1 "
        course_date = kwargs.pop('course_date', None) 
        gym_branch_list = kwargs.pop('gym_branch_list', None)
        sql += WhereClause(kwargs).get_condition_sql()
        sql += " ORDER BY course_schedule_id DESC "
        # return sql
        # ============================================
        if copyschedule == 1:
            cursor = self.db.cursor()

            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            if course_date:
                resultg = (r.update(course_date=course_date) or r for r in result)
            else:
                today_date_string = DateTime.strftime(DateTime.today(), "%Y-%m-%d")
                resultg = (self.updatedCopyOfDict(r, course_date=date) for r in result for date in self.getDateOfMonthByWeekday(
                            r['course_schedule_month'],
                            r['course_schedule_day']) if date >= today_date_string
                        )
                _result_list = list(resultg)
                _result_list.sort(key=lambda x: x['course_date'])
                resultg = iter(_result_list)
        # ============================================
            if count != 0:
                from itertools import islice
                result = []
                for r in islice(
                    resultg,
                    int(startpos),
                    int(count) + int(startpos)
                    ): result.append(r)
            elif count == 0:
                result = list(resultg)
        # ============================================
            for r in result:
                r['course_schedule_begintime'] = r.pop('.course_schedule_begintime',None)
                r['course_schedule_endtime'] = r.pop('.course_schedule_endtime',None)
                r['gym'] = '%s (%s)' % (r['gym_name'], r['gym_branch_name'])
                date_str = r['course_date']
                stock_dict = json.loads(r['course_schedule_stock'])
                r['course_schedule_stock'] = stock_dict[date_str]
                r['course_star_data'] = eval(r['course_star_data']) if r['course_star_data'] else []
                r['gym_branch_followed'] = False
                if gym_branch_list and r['gym_branch_id'] in gym_branch_list:
                    r['gym_branch_followed'] = True
        else:
            if count != 0:
                sql += ' LIMIT %s, %s ' % (startpos, count)

            cursor = self.db.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
        return result

    def QueryScheduleStock(self, course_schedule_id, date):
        ''' 查询一个团操排期的库存（名额）
            date - 日期, 格式 '2015-09-08'
        '''
        scheduleinfo = self.QueryScheduleInfo(course_schedule_id)
        course_schedule_stock = scheduleinfo['course_schedule_stock']
        return course_schedule_stock[date] if course_schedule_stock.has_key(date) else 0

    def SaveSchedule(self, obj, *args, **kwargs):
        fields = ('course_schedule_id', 'course_schedule_courseid', 'course_schedule_teacherid', 'course_schedule_gymbranchid', 'course_schedule_day', 'course_schedule_month', 'course_schedule_begintime', 'course_schedule_endtime', 'course_schedule_stock', 'course_schedule_calory')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        course_schedule_id = obj.get("course_schedule_id", None)
        if course_schedule_id:
            # Update
            update_keys = [ k for k in obj if k != 'course_schedule_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update course_schedule_table set {updates} where course_schedule_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'course_schedule_id' ]
                params.append(course_schedule_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into course_schedule_table ({fields}) values ({values})"
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

    def DeleteSchedule(self, course_schedule_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM course_schedule_table WHERE course_schedule_id = %s" % course_schedule_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def CopySchedule(self, oldscheduleid):
        cursor = self.db.cursor()
        cursor.execute( "INSERT INTO course_schedule_table SELECT "
                        " 0, course_schedule_courseid, course_schedule_teacherid, course_schedule_gymbranchid, course_schedule_day, course_schedule_month, course_schedule_begintime, "
                        " course_schedule_endtime, course_schedule_stock, course_schedule_calory FROM course_schedule_table WHERE course_schedule_id = %s" % oldscheduleid)
        scheduleid = cursor.lastrowid
        self.db.commit()
        cursor.close()

        # # 复制商品的场次信息
        # cursor = self.db.cursor()
        # sql = "insert into scene_table select %d, %d, scene_time1, scene_time2, scene_maxpeople, scene_fullprice, scene_childprice, scene_name, scene_locations, scene_timeperiod, scene_marketprice, scene_points, scene_promotionprice, scene_promotionbegintime, scene_promotionendtime, scene_description, deleteflag from scene_table where scene_productid = %d" % (0, productid, oldproductid)
        # cursor.execute(sql)
        # self.db.commit()
        # cursor.close()

        return scheduleid

    def GetCourseLocationList(self):
        sql = 'SELECT DISTINCT gbt.gym_branch_district, gbt.gym_branch_businesscircle FROM course_table AS c\
               INNER JOIN category_table AS cg ON cg.category_id=c.course_categoryid\
               INNER JOIN gym_branch_table AS gbt ON c.course_gymid=gbt.gym_branch_gymid\
               WHERE cg.category_type=1 '
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = { "不限" : [ "全部商圈" ] }
        for val in cursor.fetchall():
            key = val['gym_branch_district']
            result.setdefault(key, [])
            result.get(key).append(val['gym_branch_businesscircle'])
        cursor.close()

        return result
    #####################################################################################################################################

    def QueryTeacherInfo(self, teacher_id):
        cursor = self.db.cursor()
        sql   = "SELECT * FROM teacher_table \
                INNER JOIN gym_table ON teacher_gymid=gym_id \
                WHERE teacher_id = %s LIMIT 1"
        param = [ teacher_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryTeacher(self, startpos, count=settings.LIST_ITEM_PER_PAGE, gym_id=0, **kwargs):
        cursor = self.db.cursor()
        sql = "SELECT * FROM teacher_table AS tc "

        if kwargs.get('teacher_district') or kwargs.get('teacher_businesscircle'):
            sql += ' INNER JOIN gym_branch_table AS gbt ON gbt.gym_branch_gymid=tc.teacher_gymid'
        sql += " WHERE 1 = 1 "

        if gym_id != 0:
            sql += " AND tc.teacher_gymid  = %s " % gym_id

        if kwargs.get('course_name'):
            sql += ' AND cg.category_name = "%s" ' % kwargs['course_name']

        if kwargs.get('teacher_district'):
            sql += ' AND gbt.gym_branch_district = "%s" ' % kwargs['teacher_district']

        if kwargs.get('teacher_businesscircle'):
            sql += ' AND gbt.gym_branch_businesscircle = "%s" ' % kwargs['teacher_businesscircle']

        sql += " ORDER BY tc.teacher_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SaveTeacher(self, obj, *args, **kwargs):
        fields = ('teacher_id', 'teacher_name', 'teacher_idcardno', 'teacher_gymid', 'teacher_permitno', 'teacher_idcard_avatar', 'teacher_permit_avatar', 'teacher_avatar', 'teacher_description')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        teacher_id = obj.get("teacher_id", None)
        if teacher_id:
            # Update
            update_keys = [ k for k in obj if k != 'teacher_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update teacher_table set {updates} where teacher_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'teacher_id' ]
                params.append(teacher_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into teacher_table ({fields}) values ({values})"
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

    def DeleteTeacher(self, teacher_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM teacher_table WHERE teacher_id = %s" % teacher_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def QueryTypeList(self, category_type):
        cursor = self.db.cursor()
        sql = 'SELECT * FROM category_table WHERE category_type = %s' % category_type
        cursor.execute(sql)
        result = []
        for r in cursor.fetchall():
            result.append(r)
        cursor.close()
        return result

    def GetTeacherLocationList(self):
        sql = 'SELECT DISTINCT gbt.gym_branch_district, gbt.gym_branch_businesscircle FROM private_teacher_table AS pt '  
        sql += 'INNER JOIN gym_branch_table AS gbt ON pt.private_teacher_gymbranchid=gbt.gym_branch_id '
        sql += 'INNER JOIN category_table AS cg ON cg.category_id=pt.private_teacher_categoryid '
        sql += 'WHERE cg.category_type=2 '
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = { "不限" : [ "全部商圈" ] }
        for val in cursor.fetchall():
            key = val['gym_branch_district']
            result.setdefault(key, [])
            result.get(key).append(val['gym_branch_businesscircle'])
        cursor.close()
        return result

    def GetTeacherAvatarUniqueString(self, teacher_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM teacher_table WHERE teacher_id = %s LIMIT 1"
        param = [ teacher_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["teacher_avatar"]
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

    def GetTeacherAvatarUniqueStrings(self, teacher_id):
        '''Gets the random generated unique strings for a product'''
        cursor = self.db.cursor()
        sql = "SELECT * FROM teacher_table WHERE teacher_id = %s LIMIT 1"
        param = [ teacher_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        
        if result is not None:
            if result["teacher_avatar"] and result["teacher_avatar"].startswith('['):
                try:
                    return json.loads(result["teacher_avatar"])
                except (TypeError, ValueError):
                    pass
            else:
                return [ result["teacher_avatar"] ]
        return []

    def GetTeacherAvatarPreview(self, teacher_id):
        aps = teacher_id and self.GetTeacherAvatarPreviews(teacher_id) or []
        i = 0
        avatarpreview = None
        hascustomavatar = False
        for avatar, uniquestring, iscustom in aps:
            if i == 0:
                avatarpreview = avatar
                hascustomavatar = iscustom
            else:
                break
            i = i + 1
        return (avatarpreview, hascustomavatar)

    def GetTeacherAvatarPreviews(self, teacher_id):
        '''Get the all image avatar paths'''
        teacherinfo = self.QueryTeacherInfo(teacher_id)
        filedir = abspath
        avatars = self.GetTeacherAvatarUniqueStrings(teacher_id)
        file_tmpl = '/static/img/avatar/teacher/%s.jpeg'

        for uniquestr in avatars:
            avatarfile = file_tmpl % ('P%s_%s' % (teacherinfo["teacher_id"], uniquestr))
            outfile = filedir + avatarfile
            hascustomavatar = os.path.exists(outfile)
            yield (
                avatarfile, # if hascustomavatar else file_tmpl % 'default_avatar_product',
                uniquestr,
                hascustomavatar
            )

    # ------------

    def GetTeacherIDCardAvatarUniqueString(self, teacher_id):
        '''获取用户avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM teacher_table WHERE teacher_id = %s LIMIT 1"
        param = [teacher_id]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["teacher_idcard_avatar"]
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

    def GetTeacherIDCardAvatarPreview(self, teacher_id):
        '''Get the user's preview avatar path.
        '''
        hascustomavatar = True
        teacherinfo = self.QueryTeacherInfo(teacher_id)
        if teacherinfo is None:
            return ('/static/img/avatar/teacher/default_idcard_avatar.jpeg', False)
        filedir = abspath
        avatarfile = '/static/img/avatar/teacher/IDC%s_%s.jpeg' % (teacherinfo["teacher_id"], self.GetTeacherIDCardAvatarUniqueString(teacher_id))
        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/teacher/IDC%s_%s.jpeg' % (teacherinfo["teacher_id"], self.GetTeacherIDCardAvatarUniqueString(teacher_id))
            outfile  = filedir + avatarfile
            if os.path.exists(outfile) == False:
                avatarfile = '/static/img/avatar/teacher/default_idcard_avatar.jpeg'
                hascustomavatar = False
        return (avatarfile, hascustomavatar)

    # ------------

    def GetTeacherPermitAvatarUniqueString(self, teacher_id):
        '''获取用户avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM teacher_table WHERE teacher_id = %s LIMIT 1"
        param = [teacher_id]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["teacher_permit_avatar"]
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

    def GetTeacherPermitAvatarPreview(self, teacher_id):
        '''Get the teacher's preview avatar path.
        '''
        hascustomavatar = True
        teacherinfo = self.QueryTeacherInfo(teacher_id)
        if teacherinfo is None:
            return ('/static/img/avatar/teacher/default_permit_avatar.jpeg', False)
        filedir = abspath
        avatarfile = '/static/img/avatar/teacher/PMT%s_%s.jpeg' % (teacherinfo["teacher_id"], self.GetTeacherPermitAvatarUniqueString(teacher_id))
        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/teacher/PMT%s_%s.jpeg' % (teacherinfo["teacher_id"], self.GetTeacherPermitAvatarUniqueString(teacher_id))
            outfile  = filedir + avatarfile
            if os.path.exists(outfile) == False:
                avatarfile = '/static/img/avatar/teacher/default_permit_avatar.jpeg'
                hascustomavatar = False
        return (avatarfile, hascustomavatar)

    #####################################################################################################################################

    def QueryPrivateTeacherInfo(self, private_teacher_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM private_teacher_table WHERE private_teacher_id = %s LIMIT 1"
        param = [ private_teacher_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()

        if result:
            result['private_teacher_star_data'] = eval(result['private_teacher_star_data']) if result['private_teacher_star_data'] else []

        return result

    def QueryPrivateTeacher(self, startpos, count=settings.LIST_ITEM_PER_PAGE, **kwargs):
        cursor = self.db.cursor()
        sql = " SELECT * FROM private_teacher_table\
                INNER JOIN gym_branch_table ON gym_branch_id=private_teacher_gymbranchid\
                INNER JOIN category_table ON private_teacher_categoryid=category_id\
                WHERE 1=1 "
        sql += WhereClause(kwargs).get_condition_sql()

        sql += " ORDER BY private_teacher_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)

        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SavePrivateTeacher(self, obj, *args, **kwargs):
        fields = ( 'private_teacher_id', 'private_teacher_name', 'private_teacher_idcardno', 'private_teacher_gymbranchid', 'private_teacher_permitno', 'private_teacher_idcard_avatar', 'private_teacher_permit_avatar', 'private_teacher_avatar', 'private_teacher_description', 'private_teacher_star_data', 'private_teacher_categoryid' )
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        private_teacher_id = obj.get("private_teacher_id", None)
        if private_teacher_id:
            # Update
            update_keys = [ k for k in obj if k != 'private_teacher_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update private_teacher_table set {updates} where private_teacher_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'private_teacher_id' ]
                params.append(private_teacher_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into private_teacher_table  ({fields}) values ({values})"
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

    def DeletePrivateTeacher(self, private_teacher_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM private_teacher_table WHERE private_teacher_id = %s" % private_teacher_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def GetPrivateTeacherAvatarUniqueString(self, private_teacher_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM private_teacher_table WHERE private_teacher_id = %s LIMIT 1"
        param = [ private_teacher_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["private_teacher_avatar"]
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

    def GetPrivateTeacherAvatarUniqueStrings(self, private_teacher_id):
        '''Gets the random generated unique strings for a product'''
        cursor = self.db.cursor()
        sql = "SELECT * FROM private_teacher_table WHERE private_teacher_id = %s LIMIT 1"
        param = [ private_teacher_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        
        if result is not None:
            if result["private_teacher_avatar"] and result["private_teacher_avatar"].startswith('['):
                try:
                    return json.loads(result["private_teacher_avatar"])
                except (TypeError, ValueError):
                    pass
            else:
                return [ result["private_teacher_avatar"] ]
        return []

    def GetPrivateTeacherAvatarPreview(self, private_teacher_id):
        aps = private_teacher_id and self.GetPrivateTeacherAvatarPreviews(private_teacher_id) or []
        i = 0
        avatarpreview = None
        hascustomavatar = False
        for avatar, uniquestring, iscustom in aps:
            if i == 0:
                avatarpreview = avatar
                hascustomavatar = iscustom
            else:
                break
            i = i + 1
        return (avatarpreview, hascustomavatar)

    def GetPrivateTeacherAvatarPreviews(self, private_teacher_id):
        '''Get the all image avatar paths'''
        teacherinfo = self.QueryPrivateTeacherInfo(private_teacher_id)
        filedir = abspath
        avatars = self.GetPrivateTeacherAvatarUniqueStrings(private_teacher_id)
        file_tmpl = '/static/img/avatar/privateteacher/%s.jpeg'

        for uniquestr in avatars:
            avatarfile = file_tmpl % ('P%s_%s' % (teacherinfo["private_teacher_id"], uniquestr))
            outfile = filedir + avatarfile
            hascustomavatar = os.path.exists(outfile)
            yield (
                avatarfile, # if hascustomavatar else file_tmpl % 'default_avatar_product',
                uniquestr,
                hascustomavatar
            )

    # ------------

    def GetPrivateTeacherIDCardAvatarUniqueString(self, private_teacher_id):
        '''获取用户avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM private_teacher_table WHERE private_teacher_id = %s LIMIT 1"
        param = [private_teacher_id]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["private_teacher_idcard_avatar"]
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

    def GetPrivateTeacherIDCardAvatarPreview(self, private_teacher_id):
        '''Get the user's preview avatar path.
        '''
        hascustomavatar = True
        teacherinfo = self.QueryPrivateTeacherInfo(private_teacher_id)
        if teacherinfo is None:
            return ('/static/img/avatar/privateteacher/default_idcard_avatar.jpeg', False)
        filedir = abspath
        avatarfile = '/static/img/avatar/privateteacher/IDC%s_%s.jpeg' % (teacherinfo["private_teacher_id"], self.GetPrivateTeacherIDCardAvatarUniqueString(private_teacher_id))
        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/privateteacher/IDC%s_%s.jpeg' % (teacherinfo["private_teacher_id"], self.GetPrivateTeacherIDCardAvatarUniqueString(private_teacher_id))
            outfile  = filedir + avatarfile
            if os.path.exists(outfile) == False:
                avatarfile = '/static/img/avatar/privateteacher/default_idcard_avatar.jpeg'
                hascustomavatar = False
        return (avatarfile, hascustomavatar)

    # ------------

    def GetPrivateTeacherPermitAvatarUniqueString(self, private_teacher_id):
        '''获取用户avatar的10位随机字符串
        '''
        cursor = self.db.cursor()

        sql   = "SELECT * FROM private_teacher_table WHERE private_teacher_id = %s LIMIT 1"
        param = [private_teacher_id]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["private_teacher_permit_avatar"]
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

    def GetPrivateTeacherPermitAvatarPreview(self, private_teacher_id):
        '''Get the teacher's preview avatar path.
        '''
        hascustomavatar = True
        teacherinfo = self.QueryPrivateTeacherInfo(private_teacher_id)
        if teacherinfo is None:
            return ('/static/img/avatar/privateteacher/default_permit_avatar.jpeg', False)
        filedir = abspath
        avatarfile = '/static/img/avatar/privateteacher/PMT%s_%s.jpeg' % (teacherinfo["private_teacher_id"], self.GetPrivateTeacherPermitAvatarUniqueString(private_teacher_id))
        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/privateteacher/PMT%s_%s.jpeg' % (teacherinfo["private_teacher_id"], self.GetPrivateTeacherPermitAvatarUniqueString(private_teacher_id))
            outfile  = filedir + avatarfile
            if os.path.exists(outfile) == False:
                avatarfile = '/static/img/avatar/privateteacher/default_permit_avatar.jpeg'
                hascustomavatar = False
        return (avatarfile, hascustomavatar)

    #####################################################################################################################################

    def QueryOrderInfo(self, order_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM order_table WHERE order_id = %s LIMIT 1"
        param = [ order_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryOrder(self, startpos, count=settings.LIST_ITEM_PER_PAGE, **kwargs):
        order_type = kwargs.pop('order_type', None) 
        if order_type==1:
            sql = ' SELECT *, %s FROM course_schedule_table INNER JOIN (%s) AS order_table ON course_schedule_id=order_objectid \
                    INNER JOIN gym_branch_table ON course_schedule_gymbranchid=gym_branch_id \
                    INNER JOIN course_table ON course_schedule_courseid=course_id \
                    INNER JOIN category_table ON course_categoryid=category_id'
            params = ('DATE_FORMAT(course_schedule_begintime, "%H:%i") AS course_schedule_begintime, \
                       DATE_FORMAT(course_schedule_endtime, "%H:%i") AS course_schedule_endtime',
                       'SELECT * FROM order_table WHERE order_type=1')
        elif order_type==2:
            sql = ' SELECT * FROM private_teacher_table INNER JOIN (%s) AS order_table ON private_teacher_id=order_objectid \
                    INNER JOIN gym_branch_table ON private_teacher_gymbranchid=gym_branch_id\
                    INNER JOIN category_table ON private_teacher_categoryid=category_id'
            params = 'SELECT * FROM order_table WHERE order_type=2'
        else:
            sql = ' SELECT *, DATE_FORMAT(order_begintime, "%H:%i") AS order_begintime, DATE_FORMAT(order_endtime, "%H:%i") AS order_endtime FROM order_table '
        if order_type:
            sql = sql % params

        sql += ' WHERE 1=1 '
        sql += WhereClause(kwargs).get_condition_sql()
        sql += " ORDER BY order_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        cursor = self.db.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        for r in result:
            if order_type == 1:
                r['course_schedule_begintime'] = r.pop('.course_schedule_begintime')
                r['course_schedule_endtime'] = r.pop('.course_schedule_endtime')
            if order_type in (1, 2):
                gyminfo = self.QueryGymInfo(r['gym_branch_gymid'])
                r['gym_branch'] = '%s (%s)' % (gyminfo['gym_name'], r['gym_branch_name'])
            if order_type is None:
                r['order_begintime'] = r.pop('.order_begintime')
                r['order_endtime'] = r.pop('.order_endtime')

        cursor.close()

        return result

    def QueryOrderGymBranchID(self, order_id):
        orderinfo = self.QueryOrderInfo(order_id)
        if orderinfo['order_type'] == 1:
            # 团操排期ID
            scheduleinfo = self.QueryScheduleInfo(orderinfo['order_objectid'])
            return scheduleinfo['course_schedule_gymbranchid']
        elif orderinfo['order_type'] == 2:
            # 私教ID
            teacherinfo = self.QueryPrivateTeacherInfo(orderinfo['order_objectid'])
            if teacherinfo:
                return teacherinfo['private_teacher_gymbranchid']
            else:
                return 0

    def SaveOrder(self, obj, *args, **kwargs):
        fields = ('order_id', 'order_userid', 'order_type', 'order_objectid', 'order_date','order_begintime','order_endtime', 'order_contact_name', 'order_contact_phonenumber', 'order_remark', 'order_status', 'order_datetime')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        order_id = obj.get("order_id", None)
        if order_id:
            # Update
            update_keys = [ k for k in obj if k != 'order_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update order_table set {updates} where order_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'order_id' ]
                params.append(order_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into order_table ({fields}) values ({values})"
            obj['order_datetime'] = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
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

    def DeleteOrder(self, order_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM order_table WHERE order_id = %s" % order_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    #####################################################################################################################################

    def QueryAdsInfo(self, ads_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM ads_table WHERE ads_id = %s LIMIT 1"
        param = [ ads_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

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

    def QueryAds(self, startpos, count=settings.LIST_ITEM_PER_PAGE, ads_position=0, showAllAds=1):
        cursor = self.db.cursor()
        sql = "SELECT * FROM ads_table WHERE 1 = 1 "
        if ads_position != 0:
            sql += " AND ads_position = %s " % ads_position
        else:
            if showAllAds != 1:
                sql += " AND ads_position != 98 AND ads_position != 99 "

        sql += " ORDER BY ads_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SaveAds(self, obj, *args, **kwargs):
        fields = ('ads_id', 'ads_auditstate', 'ads_publisherid', 'ads_platform', 'ads_position', 'ads_avatar', 'ads_externalurl', 'ads_sortweight', 'ads_type', 'ads_restriction')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        ads_id = obj.get("ads_id", None)
        if ads_id:
            # Update
            update_keys = [ k for k in obj if k != 'ads_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update ads_table set {updates} where ads_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'ads_id' ]
                params.append(ads_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into ads_table ({fields}) values ({values})"
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

    def DeleteAds(self, ads_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM ads_table WHERE ads_id = %s" % ads_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def GetAdsAvatarUniqueString(self, ads_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM ads_table WHERE ads_id = %s LIMIT 1"
        param = [ ads_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["ads_avatar"]
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

    def GetAdsAvatarPreview(self, ads_id):
        hascustomavatar = True
        adsinfo = self.QueryAdsInfo(ads_id)
        if adsinfo is None:
            return ('/static/img/avatar/ads/default.jpeg', False)

        filedir = abspath
        avatarfile = '/static/img/avatar/ads/P%s_%s.jpeg' % (adsinfo["ads_id"], self.GetAdsAvatarUniqueString(ads_id))

        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/ads/default.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    #####################################################################################################################################

    def QueryCategoryInfo(self, category_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM category_table WHERE category_id = %s LIMIT 1"
        param = [ category_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        return result

    def QueryCategory(self, startpos, count=settings.LIST_ITEM_PER_PAGE, category_type=0, category_name=0):
        cursor = self.db.cursor()
        sql = "SELECT * FROM category_table WHERE 1 = 1 "
        if category_type != 0:
            sql += " AND category_type = %s " % category_type
        if category_name != 0:
            sql += " AND category_name = '%s' " % category_name
        sql += " ORDER BY category_id DESC "
        if count != 0:
            sql += " LIMIT %s, %s " % (startpos, count)
        
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def SaveCategory(self, obj, *args, **kwargs):
        fields = ('category_id', 'category_type', 'category_name', 'category_description', 'category_sortweight', 'category_avatar', 'category_calory_unit')
        obj = { k: v for k, v in obj.iteritems() if k in fields }

        category_id = obj.get("category_id", None)
        if category_id:
            # Update
            update_keys = [ k for k in obj if k != 'category_id' ]
            if update_keys:
                # Prepare for update
                sql_tmpl = r"update category_table set {updates} where category_id = {id}"
                updates = ','.join("{}=%s".format(k) for k in update_keys)
                sql = sql_tmpl.format(
                    updates=updates,
                    id='%s'
                )
                params = [ v for k, v in obj.items() if k != 'category_id' ]
                params.append(category_id)
                cursor = self.db.cursor()
                cursor.execute(sql, params)
                self.db.commit()
                return 0
            else:
                # Nothing to proceed
                return 1
        else:
            # Add
            sql_tmpl = r"insert into category_table ({fields}) values ({values})"
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
    def DeleteEntry(self, the_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM {tblname}_table WHERE {tblname}_id = {the_id} OR {tblname}_parentid = {the_id}".format(tblname='entry', the_id=the_id)
        cursor.execute(sql)
        self.db.commit()
        cursor.close() 
    def DeleteCategory(self, category_id):
        cursor = self.db.cursor()
        sql = "DELETE FROM category_table WHERE category_id = %s" % category_id
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def GetCategoryAvatarUniqueString(self, category_id):
        cursor = self.db.cursor()

        sql   = "SELECT * FROM category_table WHERE category_id = %s LIMIT 1"
        param = [ category_id ]
        cursor.execute(sql, param)

        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            ret = None
            avt = result["category_avatar"]
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

    def GetCategoryAvatarPreview(self, category_id):
        hascustomavatar = True
        categoryinfo = self.QueryCategoryInfo(category_id)
        if categoryinfo is None:
            return ('/static/img/avatar/category/default.jpeg', False)

        filedir = abspath
        avatarfile = '/static/img/avatar/category/P%s_%s.jpeg' % (categoryinfo["category_id"], self.GetCategoryAvatarUniqueString(category_id))

        outfile  = filedir + avatarfile
        if os.path.exists(outfile) == False:
            avatarfile = '/static/img/avatar/category/default.jpeg'
            hascustomavatar = False
        return (avatarfile, hascustomavatar)

    #####################################################################################################################################
    #####################################################################################################################################
    def getMonthWeekdayByDate(self, datestr):
        '''
            datestr e.g '2015-12-12'
        '''
        from datetime import datetime
        dateObj = datetime.strptime(datestr, '%Y-%m-%d').date()
        monthstr = datetime.strftime(dateObj, '%Y%m')
        weekday = dateObj.isoweekday()
        return monthstr, weekday
    def getDateOfMonthByWeekday(self, monthstr, weekday):
        '''
            monthstr e.g string "201502"
            weekday integer 1 ~ 7
            返回值格式： [ '2015-09-06', '2015-09-13', '2015-09-20', '2015-09-27' ]
        '''
        from datetime import datetime
        dateObj = datetime.strptime(monthstr, "%Y%m").date()
        t_day = self.get_target_date(dateObj)
        weekday_filter = self.get_filter_by_weekday(weekday)
        date_list = [t_day(i) for i in range(31) if t_day(0).month == t_day(i).month]
        mylist = filter(weekday_filter, date_list)
        return [ str(mydate) for mydate in mylist ]

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

    #####################################################################################################################################
    #####################################################################################################################################
