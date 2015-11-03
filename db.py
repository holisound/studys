#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-11-02 16:51:33
# @Last Modified by:   edward
# @Last Modified time: 2015-11-03 15:13:37
from mydql import connect

_db = connect(host='localhost', db='QGYM', user='root', passwd='123123')
_db.GetField('order_table', 'order_date').DateFormat("%Y-%m-%d")
_db.GetField('order_table', 'order_begintime').DateFormat("%H:%i")
_db.GetField('order_table', 'order_endtime').DateFormat("%H:%i")
_db.GetField('order_table', 'order_datetime').DateFormat("%H:%i")
# _db.GetField('course_schedule_table', 'course_schedule_begintime').DateFormat("%H:%i")
# _db.GetField('course_schedule_table', 'course_schedule_endtime').DateFormat("%H:%i")
# _db = connect(host='localhost', db='db',user='root', passwd='123123')
# _db.GetField('student', 'sbirthday').DateFormat("%Y-%m-%d")


def mydql():
    return _db.dql()
