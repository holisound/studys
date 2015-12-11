#!/usr/bin/env python
#-*-coding:utf-8-*-

import os
import MySQLdb
import glob
import time

from time import gmtime, strftime
from datetime import timedelta, datetime

# cmd       = "/home/zhangxh/.dropbox-dist/dropbox &"
# os.system(cmd)

#####################################################################################################################

todaytime           = strftime("%Y-%m-%d %H:%M:%S")
datestr             = "%s%s%s" % (todaytime[0:4], todaytime[5:7], todaytime[8:10])
sqlpath             = "/home/zhangxh/17dong_web/backup/17dong_web_%s.sql.gz" % datestr
tarpath             = "/home/zhangxh/17dong_web/backup/"

#####################################################################################################################

cmd = "find /home/zhangxh/17dong_web/static/img/avatar -name \"*_temp.jpeg\" | xargs rm -fr"
os.system(cmd)

#####################################################################################################################

cmd       = "mysqldump -uroot -pv28so709 17DONG | gzip > %s" % sqlpath
os.system(cmd)

#####################################################################################################################

cmd = "cp -fr /home/zhangxh/17dong_web/static/img/avatar/* /home/zhangxh/17dong_web/backup/image/avatar/"
os.system(cmd)

cmd = "cp -fr /home/zhangxh/17dong_web/static/img/upload/* /home/zhangxh/17dong_web/backup/image/upload/"
os.system(cmd)

#####################################################################################################################

# cmd       = "rm -fr %s" % sqlpath
# os.system(cmd)

#####################################################################################################################

search_dir = tarpath
files = filter(os.path.isfile, glob.glob(search_dir + "17dong_web*.sql.gz"))
files.sort(key=lambda x: os.path.getmtime(x))
bakfiles = files[-10:]
for onefile in files:
    if onefile not in bakfiles:
        os.remove(onefile)

#####################################################################################################################
