#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2015-11-02 16:51:33
# @Last Modified by:   edward
# @Last Modified time: 2015-11-02 22:58:32
from mydql import connect


def init():
    # db = connect(host='localhost', db='QGYM', user='root', passwd='123123')
    # db.GetField('course_schedule_table', 'course_schedule_begintime').DateFormat("%H:%i")
    # db.GetField('course_schedule_table', 'course_schedule_endtime').DateFormat("%H:%i")
    # db.GetField('order_table', 'order_date').DateFormat("%Y-%m-%d")
    # db.GetField('order_table', 'order_begintime').DateFormat("%H:%i")
    # db.GetField('order_table', 'order_endtime').DateFormat("%H:%i")
    db = connect(host='localhost', db='db',user='root', passwd='123123')
    db.GetField('student', 'sbirthday').DateFormat("%Y-%m-%d")
    return db
