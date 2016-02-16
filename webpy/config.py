#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: edward
# @Date:   2016-02-11 16:03:58
# @Last Modified by:   python
# @Last Modified time: 2016-02-16 14:50:47
import os
if os.getlogin() == 'edward':
  UPLOAD_DIR = "/home/edward/data/www/static/uploads/slide/"
else:
  UPLOAD_DIR = '/home/python/nginx/static/uploads/slide/'